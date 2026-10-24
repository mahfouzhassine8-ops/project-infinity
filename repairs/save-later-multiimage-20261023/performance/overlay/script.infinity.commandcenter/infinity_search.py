"""On-demand Infinity Search using verified, enabled providers' own interfaces.

No provider imports, edits, invented results, account access or persistent cache.
Search uses the matched native provider-lease protocol. Each foreground Search
has one active result consumer and preserves provider invoker/writer ownership.
The native deadline does not prove a bound on work before native lease entry.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import threading
import time
from urllib.parse import urlencode, urlsplit, quote
import uuid

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

CC='script.infinity.commandcenter'
PROPERTIES=['title','year','plot','genre','art','uniqueid','season','episode','showtitle','playcount','runtime','mpaa','rating','thumbnail']
MAX_RESULTS=40
MAX_ACTIVE_CONSUMERS=1
HISTORY_KEY="infinity_search_history_v1"
HISTORY_LIMIT=50


def rpc(method, params):
    return json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params))))


def providers(media, force=False):
    """Shared operation-specific inventory; no independent Search allowlist."""
    from provider_inventory import eligible
    return eligible(media, operation='search', force=force)


def route(provider,query=None,history=False):
    contract=provider['contract'];root=Path(provider['root'])
    if not xbmc.getCondVisibility('System.AddonIsEnabled('+provider['id']+')'):
        raise RuntimeError('Provider is unavailable or disabled.')
    for name,pin in contract['pins'].items():
        p=root/name
        if (Path(name).is_absolute() or '..' in Path(name).parts or
                not p.resolve().is_relative_to(root.resolve()) or
                any(part.is_symlink() for part in (p, *p.parents) if part != root.parent) or
                not p.is_file() or p.stat().st_size>512*1024):
            raise RuntimeError('Provider changed. Reopen Infinity Search to verify its interface.')
        with p.open('rb') as stream:raw=stream.read(512*1024+1)
        if hashlib.sha256(raw).hexdigest()!=pin:
            raise RuntimeError('Provider changed. Reopen Infinity Search to verify its interface.')
    if history and 'history' not in contract:
        raise RuntimeError('Provider history is not a verified capability.')
    params=dict(contract['history'] if history else contract['params'])
    if query is not None and not history:
        if not isinstance(query,str) or not query.strip() or len(query)>160:
            raise ValueError('Enter a search query')
        # Seren's globals parse URL parameters then its helper unquotes and
        # JSON-decodes action_args. Preserve literal %, quotes, null and numbers.
        params[contract['query_key']]=(quote(json.dumps(query,ensure_ascii=True),safe='')
            if contract.get('query_codec')=='seren_json' else query)
    if contract.get('query_codec')=='path_component' and not history:
        prefix=contract.get('path_prefix','')
        if not prefix or any(c not in 'abcdefghijklmnopqrstuvwxyz_/' for c in prefix):
            raise RuntimeError('Provider path search contract is invalid.')
        return 'plugin://'+provider['id']+'/'+prefix+quote(query,safe='')
    return 'plugin://'+provider['id']+'/?'+urlencode(params)


class _Cancellation:
    def __init__(self): self.event=threading.Event()
    def iscanceled(self): return self.event.is_set()
    def cancel(self): self.event.set()


def _leased_directory(path,home,progress=None):
    """Keep the native 20-second consumer lease and original invoker owner.

    Cancellation never kills a provider or fabricates completion. The original
    native lease retains a timed-out invocation until its real thread retires.
    """
    token=uuid.uuid4().hex
    keys=['Infinity.Search.'+part+token for part in ('Request.','Cancel.','Result.')]
    output=[]
    def request():
        try:output.append(rpc('Files.GetDirectory',dict(directory=path+'|infinity_search='+token,media='video',
                            properties=PROPERTIES,limits={'start':0,'end':MAX_RESULTS})))
        except (ValueError,RuntimeError):output.append({'error':{'message':'provider_failed'}})
    worker=threading.Thread(target=request,name='InfinitySearchResult')
    monitor=xbmc.Monitor()
    try:
        home.setProperty(keys[0],hashlib.sha256(path.encode('utf-8')).hexdigest())
        worker.start()
        while worker.is_alive():
            if monitor.abortRequested() or (progress is not None and progress.iscanceled()):
                home.setProperty(keys[1],'1')
            worker.join(.05)
        status=home.getProperty(keys[2])
        return status,output[0] if output else {'error':{}}
    finally:
        # No orphan request/cancel/result state survives a completed consumer.
        # Never clear the native cancellation property before the consumer exits.
        for key in keys:home.clearProperty(key)


def _provider_result(provider,query,home,cancel):
    try:
        if cancel.iscanceled():return provider,'cancelled',{},''
        path=route(provider,query)
        signature=hashlib.sha256((str(xbmcvfs.translatePath('special://profile'))+path+json.dumps(provider['contract']['pins'],sort_keys=True)).encode()).hexdigest()
        cache_key='Infinity.Search.Cache.'+provider['id']
        try:cache=json.loads(home.getProperty(cache_key) or '{}')
        except (ValueError,TypeError):cache={}
        if (cache.get('signature')==signature and isinstance(cache.get('at'),(int,float))
                and 0<=time.monotonic()-cache['at']<300):
            answer=cache['answer'];status='completed'
        else:
            status,answer=_leased_directory(path,home,cancel)
            if status=='completed' and 'error' not in answer and not cancel.iscanceled():
                cache=json.dumps(dict(signature=signature,at=time.monotonic(),answer=answer))
                if len(cache)<300000:home.setProperty(cache_key,cache)
        # Reject update/disable/removal that raced with the directory request.
        route(provider,query)
        if cancel.iscanceled():return provider,'cancelled',{},path
        return provider,status,answer,path
    except (OSError,ValueError,RuntimeError,KeyError,TypeError):
        return provider,'unavailable',{},''


def _bounded_results(ready,query,home,cancel,progress):
    """One active consumer; native globally caps living providers at three."""
    import queue
    pending=iter(enumerate(ready));active={};completed=queue.Queue(maxsize=MAX_ACTIVE_CONSUMERS);finished=0
    monitor=xbmc.Monitor()
    def launch(index,provider):
        def work():
            try:result=_provider_result(provider,query,home,cancel)
            except Exception:result=(provider,'unavailable',{},'')
            completed.put((index,result))
        worker=threading.Thread(target=work,name='InfinitySearchProvider')
        active[index]=worker;worker.start()
    try:
        for _ in range(min(MAX_ACTIVE_CONSUMERS,len(ready))):launch(*next(pending))
        while active:
            if monitor.abortRequested() or progress.iscanceled():cancel.cancel()
            try:index,result=completed.get(timeout=.05)
            except queue.Empty:continue
            active.pop(index).join()
            finished+=1
            progress.update(int(finished*100/max(1,len(ready))),result[0]['name'])
            yield result
            if not cancel.iscanceled():
                try:launch(*next(pending))
                except StopIteration:pass
    finally:
        cancel.cancel()
        for worker in active.values():worker.join()


def _publish_result(handle,provider,status,answer,path):
    rows=answer.get('result',{}).get('files') or []
    if not isinstance(rows,list):rows=[];status='invalid_result'
    heading=xbmcgui.ListItem(provider['name']+' — '+(str(len(rows))+' results' if status=='completed' else status or 'unavailable'))
    heading.setProperty('IsPlayable','false')
    heading.setProperty('Infinity.Search.Provider',provider['id'])
    xbmcplugin.addDirectoryItem(handle,path,heading,isFolder=bool(path))
    if status!='completed':return
    for row in rows[:MAX_RESULTS]:
        if not isinstance(row,dict):continue
        target=row.get('file','')
        if not isinstance(target,str) or not target.startswith(('plugin://'+provider['id']+'/', 'videodb://')):continue
        item=xbmcgui.ListItem(row.get('label') or row.get('title') or '',path=target,offscreen=True)
        info={key:row[key] for key in ('title','year','plot','genre','season','episode','playcount','runtime','mpaa','rating') if key in row}
        kind=row.get('type')
        if kind in ('movie','tvshow','season','episode'):info['mediatype']=kind
        if 'showtitle' in row:info['tvshowtitle']=row['showtitle']
        item.setInfo('video',info)
        if isinstance(row.get('uniqueid'),dict):item.setUniqueIDs(row['uniqueid'])
        if isinstance(row.get('art'),dict):item.setArt(row['art'])
        item.setProperty('Infinity.Search.Provider',provider['id'])
        # Original destination and identity survive aggregation untouched.
        item.addContextMenuItems([('Open in '+provider['name'],'ActivateWindow(Videos,"'+path+'",return)')])
        xbmcplugin.addDirectoryItem(handle,target,item,isFolder=row.get('filetype')=='directory')


def _search_results(handle,media,query,provider_id=None):
    if media not in ('movie','tv','anime','cartoon') or not isinstance(query,str) or not query.strip() or len(query)>160:return
    home=xbmcgui.Window(10000)
    if home.getProperty('Infinity.Search.Protocol')!='1':
        _leased_directory('plugin://'+CC+'/?action=search-probe',home)
    if home.getProperty('Infinity.Search.Protocol')!='1':
        xbmcgui.Dialog().ok('Infinity Search','Search requires the matching Infinity APK.')
        return
    try:ready,unsupported=providers(media,force=True)
    except (OSError,ValueError,RuntimeError) as error:
        xbmcgui.Dialog().ok('Infinity Search',str(error));return
    if provider_id is not None:
        ready=[provider for provider in ready if provider['id']==provider_id]
        unsupported=[]
        if not ready:
            xbmcgui.Dialog().ok('Infinity Search','The selected provider is disabled or its search interface changed. Reopen Search to select an available provider.')
            return
    progress=xbmcgui.DialogProgress();progress.create('Infinity Search','Searching compatible providers')
    cancel=_Cancellation()
    labels={'movie':'Movies','tv':'TV Shows','anime':'Anime','cartoon':'Cartoons'}
    xbmcplugin.setPluginCategory(handle,'Infinity Search — '+labels[media])
    xbmcplugin.setContent(handle,'movies' if media=='movie' else 'tvshows' if media=='tv' else 'videos')
    results=_bounded_results(ready,query,home,cancel,progress)
    try:
        for provider,status,answer,path in results:
            if cancel.iscanceled():break
            _publish_result(handle,provider,status,answer,path)
    finally:
        cancel.cancel();results.close();progress.close()


def search_all(handle,media,query):
    return _search_results(handle,media,query)


def search_provider(handle,media,query,provider_id):
    return _search_results(handle,media,query,provider_id=provider_id)


def open_search(media='movie'):
    try:return _open_search(media)
    except (OSError,ValueError,RuntimeError) as error:
        xbmcgui.Dialog().ok('Infinity Search',str(error))


def _open_search(media='movie'):
    if xbmc.getSkinDir()!='skin.infinity.diggz' or media not in ('movie','tv','anime','cartoon'):return
    ready,unsupported=providers(media,force=True)
    home=xbmcgui.Window(10000)
    theme=home.getProperty('Infinity.SystemTheme') or home.getProperty('Infinity.NativeSystemTheme')
    theme='light' if theme.lower() in ('light','light pearl') else 'oled' if theme.lower()=='oled' else 'dark'
    if theme=='dark' and xbmc.getInfoLabel('Skin.String(Infinity.DarkAppearance)')=='oled':theme='oled'
    token=uuid.uuid4().hex
    rows=[]
    for provider in ready:
        try:icon=xbmcaddon.Addon(provider['id']).getAddonInfo('icon')
        except RuntimeError:icon=''
        rows.append(dict(id=provider['id'],name=provider['name'],available=True,
                         description=(provider.get('category_scope') or 'Search '+{'movie':'movies','tv':'TV shows','anime':'anime','cartoon':'cartoons'}[media])+' · select, then press Search',
                         icon=xbmcvfs.translatePath(icon)))
    for provider in unsupported:
        rows.append(dict(id=provider['id'],name=provider['name'],available=False,icon=provider['icon'],
                         description='Disabled' if not provider['enabled'] else 'Search interface not verified for this category'))
    current='';selected='all';view='search';restore_selection=True
    while not xbmc.Monitor().abortRequested():
        try:history_rows=shared_history()
        except (OSError,ValueError,RuntimeError) as error:
            from infinity_trakt import notice
            notice(str(error),'Infinity Search');return
        if restore_selection:
            eligible_ids={p['id'] for p in ready}|{'all'}
            previous=next((row['provider'] for row in history_rows if row['media']==media),None)
            if previous in eligible_ids:selected=previous
            restore_selection=False
        heading='Infinity.Search.2103395:'+json.dumps(dict(token=token,theme=theme,
            media={'movie':'Movies','tv':'TV Shows','anime':'Anime','cartoon':'Cartoons'}[media],providers=rows,
            shared_history=history_rows,selected=selected,initial_view=view),separators=(',',':'))
        if len(heading)>1024*1024:
            raise RuntimeError('The installed provider inventory exceeds the Search window size limit. No providers were silently omitted.')
        keyboard=xbmc.Keyboard(current,heading,False)
        keyboard.doModal()
        if not keyboard.isConfirmed():return
        try:choice=json.loads(keyboard.getText())
        except (ValueError,TypeError):return
        if not isinstance(choice,dict) or choice.get('token')!=token:return
        query=choice.get('query');aid=choice.get('provider')
        if not isinstance(query,str) or len(query)>160:return
        if choice.get('operation')=='clear-history' and choice.get('confirmed') is True:
            try:shared_history(clear=True)
            except (OSError,ValueError,RuntimeError) as error:
                from infinity_trakt import notice
                notice(str(error),'Infinity Search');return
            current=query;selected=aid;view='history';continue
        legacy_history=choice.get('history') is True
        if not query.strip() and not legacy_history:return
        query=query.strip()
        ready,unsupported=providers(media,force=True)
        if aid=='all' and not legacy_history:
            if not ready:return
            # Each bounded request revalidates its own source independently.
            target='plugin://'+CC+'/?'+urlencode(dict(action='search-all',media=media,query=query))
            provider_name='Search All'
        else:
            provider=next((p for p in ready if p['id']==aid),None)
            if provider is None:return
            # This dispatch reaches only our first-party results handler. It
            # force-discovers and validates the selected provider immediately
            # before execution; avoid a redundant full source read here.
            target=('plugin://'+CC+'/?'+urlencode(dict(action='search-provider',media=media,query=query,provider=aid))
                    if not legacy_history else route(provider,query,history=True))
            provider_name=provider['name']
        # Commit the existing history writer before posting asynchronous GUI
        # activation. An admission/write failure cannot leave a dispatched page
        # waiting on the submitting invoker's persistence transaction.
        if not legacy_history:shared_history(query=query,media=media,provider=aid,name=provider_name)
        xbmc.executebuiltin('ActivateWindow(Videos,"'+target+'",return)')
        return


def shared_history(query=None,media=None,provider=None,name=None,clear=False):
    """One independent namespace in the existing mandatory checkpointed store.

    Read/modify only this key under the original serialized writer lease. Keep
    raw unrelated fields byte-for-byte in value, including intentionally empty
    progress; never normalize, migrate, restore or query any provider history.
    """
    from common import addon_profile,persistence_scope,read_json,atomic_json
    path=addon_profile()/'continue-watching.json'
    with persistence_scope():
        if path.is_symlink() or (path.exists() and path.stat().st_size>8*1024*1024):
            raise RuntimeError('The saved search history cannot be read safely. Existing records were retained.')
        # read_json's generic fallback is not used for malformed existing data.
        if path.exists():
            value=json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(value,dict) or type(value.get('schema')) is not int or value.get('schema') not in (1,2):
                raise RuntimeError('The local state schema is unsupported. Existing records were retained.')
        else:value={'schema':2,'items':{}}
        # Read through the existing participant as well to verify its persisted proof.
        value=read_json(path,value)
        history=value.get(HISTORY_KEY,[])
        if not isinstance(history,list) or len(history)>HISTORY_LIMIT:
            raise RuntimeError('The saved search history is incompatible. Existing records were retained.')
        for row in history:
            if not isinstance(row,dict) or set(row)!={'query','media','provider','name','at'} or not isinstance(row['query'],str) or not 1<=len(row['query'])<=160 or row['media'] not in ('movie','tv','anime','cartoon') or not isinstance(row['provider'],str) or len(row['provider'])>110 or not isinstance(row['name'],str) or len(row['name'])>100 or type(row['at']) is not int or not 0<=row['at']<=4102444800:
                raise RuntimeError('The saved search history is incompatible. Existing records were retained.')
        if clear:
            if history:value[HISTORY_KEY]=[];atomic_json(path,value)
            return []
        if query is not None:
            if not isinstance(query,str) or not query.strip() or len(query)>160 or media not in ('movie','tv','anime','cartoon') or not isinstance(provider,str) or len(provider)>110 or not isinstance(name,str):
                raise ValueError('Invalid submitted search')
            row=dict(query=query.strip(),media=media,provider=provider,name=name[:100],at=int(time.time()))
            history=[row]+[r for r in history if (r['query'].casefold(),r['media'])!=(row['query'].casefold(),media)]
            value[HISTORY_KEY]=history[:HISTORY_LIMIT];atomic_json(path,value)
        return history[:HISTORY_LIMIT]
