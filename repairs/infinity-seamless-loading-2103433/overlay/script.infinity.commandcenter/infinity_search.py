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
PROPERTIES=['title','year','plot','genre','art','uniqueid','season','episode','showtitle','playcount','runtime','mpaa','rating','thumbnail','trailer','premiered']
MAX_RESULTS=40
MAX_ACTIVE_CONSUMERS=1
HISTORY_KEY="infinity_search_history_v1"
HISTORY_LIMIT=50


def rpc(method, params):
    return json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params))))


def providers(media, force=False, provider_id=None):
    """Shared operation-specific inventory; no independent Search allowlist."""
    from provider_inventory import eligible
    return eligible(media, operation='search', force=force, provider_id=provider_id)


def route(provider,query=None,history=False):
    contract=provider['contract'];root=Path(provider['root'])
    if not xbmc.getCondVisibility('System.AddonIsEnabled('+provider['id']+')'):
        raise RuntimeError('Provider is unavailable or disabled.')
    from provider_capabilities import verify_dependencies
    from provider_inventory import _resolve_search_dependency
    verify_dependencies(contract, _resolve_search_dependency)
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


class _VisibleCancellation:
    # Check foreground Search dismissal during the real native consumer wait.
    # A cancelled native lease must not be abandoned; _leased_directory waits
    # for the original owned invoker to exit before clearing the cancel token.
    def __init__(self, cancel, progress):
        self.cancel, self.progress = cancel, progress
    def iscanceled(self):
        if self.cancel.iscanceled():
            return True
        if self.progress is not None and self.progress.iscanceled():
            self.cancel.cancel()
            return True
        return False


def _native_search_admission():
    """One foreground plugin.video RPC across all Python subinterpreters in Kodi.

    An abstract Linux Unix socket provides an atomic cross-interpreter lock
    without a lockfile, profile write, global property race, or external app.
    Its descriptor stays owned until the original JSON-RPC thread exits.
    """
    import errno
    import os
    import socket
    owner = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        owner.bind('\0infinity-search-native-rpc-v1-' + str(os.getpid()))
    except OSError as failure:
        owner.close()
        if failure.errno == errno.EADDRINUSE:
            return None
        raise RuntimeError('Infinity Search native admission is unavailable') from failure
    return owner


def _leased_directory(path,home,progress=None):
    """Keep the original native lease and the actual RPC worker's capacity.

    A failing consumer callback must not release capacity while native work
    remains alive. Only its real RPC worker retires an admission after start;
    this invoker retains ownership of its request/cancel/result token cleanup.
    """
    admission = _native_search_admission() if path.startswith('plugin://plugin.video.') else False
    if admission is None:
        return 'busy', {'error': {'message': 'A previous Infinity Search is still active'}}
    worker=None
    keys=[]
    cancel_sent=False
    try:
        token=uuid.uuid4().hex
        keys=['Infinity.Search.'+part+token for part in ('Request.','Cancel.','Result.')]
        output=[]
        def request():
            try:
                try:output.append(rpc('Files.GetDirectory',dict(directory=path+'|infinity_search='+token,media='video',
                                    properties=PROPERTIES,limits={'start':0,'end':MAX_RESULTS})))
                except (ValueError,RuntimeError):output.append({'error':{'message':'provider_failed'}})
            finally:
                # The worker owns capacity even if its submitting interpreter's
                # GUI callback, cancellation check or token cleanup raises.
                if admission:
                    admission.close()
        worker=threading.Thread(target=request,name='InfinitySearchResult')
        monitor=xbmc.Monitor()
        home.setProperty(keys[0],hashlib.sha256(path.encode('utf-8')).hexdigest())
        worker.start()
        while worker.is_alive():
            if not cancel_sent and (monitor.abortRequested() or (progress is not None and progress.iscanceled())):
                home.setProperty(keys[1],'1')
                cancel_sent=True
            worker.join(.05)
        status=home.getProperty(keys[2])
        return status,output[0] if output else {'error':{}}
    finally:
        try:
            if worker is not None and worker.ident is not None and worker.is_alive():
                # On exceptional consumer exit, request native cancellation once
                # and retain this original worker until it actually retires.
                # Never force-kill a provider or clear its live request token.
                if not cancel_sent:
                    try:
                        home.setProperty(keys[1],'1')
                    except Exception:
                        pass  # The existing native lease still owns retirement.
                worker.join()
            cleanup_error=None
            for key in keys:
                try:
                    home.clearProperty(key)
                except Exception as error:
                    if cleanup_error is None:
                        cleanup_error=error
            if cleanup_error is not None:
                raise cleanup_error
        finally:
            # No worker was launched: this invoker still owns the descriptor.
            # A started worker closes it itself, including exceptional RPC exit.
            if admission and (worker is None or worker.ident is None):
                admission.close()


def _query_cache_entries(raw, now):
    """A few recent responses, within the original per-provider byte/age caps."""
    import math
    if not isinstance(raw, str) or not raw or len(raw) >= 300000 or not raw.isascii():
        return []
    try:
        value = json.loads(raw)
    except (ValueError, TypeError):
        return []
    if not isinstance(value, dict):
        return []
    if value.get('schema') == 2:
        rows = value.get('entries')
        if not isinstance(rows, list) or len(rows) > 4:
            return []
    elif 'schema' not in value:
        rows = [value]  # Read the already valid previous one-query format.
    else:
        return []
    result = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            return []
        signature, stamp, answer = row.get('signature'), row.get('at'), row.get('answer')
        if (not isinstance(signature, str) or len(signature) != 64 or
                any(ch not in '0123456789abcdef' for ch in signature) or signature in seen or
                type(stamp) not in (int, float) or not math.isfinite(stamp) or
                not isinstance(answer, dict) or 'error' in answer):
            return []
        seen.add(signature)
        if 0 <= now - stamp < 300:
            result.append(dict(signature=signature, at=stamp, answer=answer))
    return result


def _remember_query_answer(home, key, entries, signature, answer, now):
    """No persistent cache, extra memory budget, or renewed TTL on cache hits."""
    fresh = dict(signature=signature, at=now, answer=answer)
    rows = [fresh] + [row for row in entries if row['signature'] != signature]
    rows = rows[:4]
    while rows:
        raw = json.dumps(dict(schema=2, entries=rows), separators=(',', ':'))
        if len(raw) < 300000:
            home.setProperty(key, raw)
            return True
        rows.pop()
    # An oversized new response must not destroy other usable cached queries.
    return False


def _query_file_stamp(path):
    """Advisory invalidation only; unreadable/linked state disables reuse."""
    import stat
    try:
        value = path.lstat()
    except FileNotFoundError:
        return ('absent',)
    except OSError:
        return None
    if not stat.S_ISREG(value.st_mode):
        return None
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)


def _query_signature(provider, path, home):
    """Bind answers to their actual route, dependencies and current UI state.

    These stamps never grant a capability. route() must still verify enabled
    sources and raw dependency pins before and after every hit or native call.
    No persistent cache or extension of the original byte/age caps is involved.
    """
    profile = Path(xbmcvfs.translatePath('special://profile')).resolve()
    addon = xbmcaddon.Addon(CC)
    progress = Path(xbmcvfs.translatePath(addon.getAddonInfo('profile'))).resolve()
    dependencies = provider['contract'].get('dependencies', [])
    paths = [progress / 'continue-watching.json', Path(provider['root']) / 'addon.xml',
             profile / 'addon_data' / provider['id'] / 'settings.xml']
    for dependency in dependencies:
        paths.extend((Path(dependency['root']) / 'addon.xml',
                      profile / 'addon_data' / dependency['id'] / 'settings.xml'))
    stamps = [_query_file_stamp(file) for file in paths]
    if any(stamp is None for stamp in stamps):
        return None
    revisions = [home.getProperty(name) for name in (
        'Infinity.ContinueWatchingRevision', 'Infinity.ProviderInventory.Revision',
        'Infinity.ResumeHub.PresentationSnapshot', 'widgetreload', 'widgetreload2',
        'widgetreload-movies', 'widgetreload-tvshows')]
    identity = [str(profile), str(progress), addon.getAddonInfo('version'), path,
                provider['root'], provider['contract'], stamps, revisions]
    return hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()


def _provider_result(provider,query,home,cancel,progress=None):
    try:
        if cancel.iscanceled():return provider,'cancelled',{},''
        path=route(provider,query)
        signature=_query_signature(provider,path,home)
        cache_key='Infinity.Search.Cache.'+provider['id']
        cache=_query_cache_entries(home.getProperty(cache_key),time.monotonic())
        hit=next((row for row in cache if signature is not None and row['signature']==signature),None)
        if hit is not None:
            answer=hit['answer'];status='completed'
        else:
            status,answer=_leased_directory(path,home,_VisibleCancellation(cancel,progress))
        # Reject update/disable/removal that raced with the directory request.
        route(provider,query)
        if cancel.iscanceled():return provider,'cancelled',{},path
        if _query_signature(provider,path,home) != signature:
            return provider,'state_changed',{},path
        if hit is None and signature is not None and status=='completed' and 'error' not in answer:
            _remember_query_answer(home,cache_key,cache,signature,answer,time.monotonic())
        return provider,status,answer,path
    except (OSError,ValueError,RuntimeError,KeyError,TypeError):
        return provider,'unavailable',{},''


def _bounded_results(ready,query,home,cancel,progress):
    """Single consumer, one worker per native RPC, and no nested provider threads.

    MAX_ACTIVE_CONSUMERS has already been 1; the former extra wrapper thread
    was redundant. Keep the same provider order, native lease and caching.
    The progress cancellation is observed during _leased_directory's wait,
    not just between providers, while its real RPC owner retires normally.
    """
    monitor=xbmc.Monitor()
    try:
        for index,provider in enumerate(ready):
            if monitor.abortRequested() or progress.iscanceled() or cancel.iscanceled():
                cancel.cancel();break
            try:
                result=_provider_result(provider,query,home,cancel,progress)
            except Exception:
                result=(provider,'unavailable',{},'')
            if monitor.abortRequested() or progress.iscanceled() or cancel.iscanceled():
                cancel.cancel();break
            progress.update(int((index+1)*100/max(1,len(ready))),result[0]['name'])
            yield result
            if result[1] == 'busy':
                break  # Never hammer other providers while another Search is working.
    finally:
        cancel.cancel()

def _publish_result(handle,provider,status,answer,path):
    rows=answer.get('result',{}).get('files') or []
    if not isinstance(rows,list):rows=[];status='invalid_result'
    heading=xbmcgui.ListItem(provider['name']+' — '+(str(len(rows))+' results' if status=='completed' else
        'State changed; search again' if status=='state_changed' else status or 'unavailable'))
    heading.setProperty('IsPlayable','false')
    heading.setProperty('Infinity.Search.Provider',provider['id'])
    xbmcplugin.addDirectoryItem(handle,path,heading,isFolder=bool(path))
    if status!='completed':return
    for row in rows[:MAX_RESULTS]:
        if not isinstance(row,dict):continue
        target=row.get('file','')
        if not isinstance(target,str) or not target.startswith(('plugin://'+provider['id']+'/', 'videodb://')):continue
        item=xbmcgui.ListItem(row.get('label') or row.get('title') or '',path=target,offscreen=True)
        info={key:row[key] for key in ('title','year','plot','genre','season','episode','playcount','runtime','mpaa','rating','premiered') if key in row}
        from title_metadata import trailer_route
        trailer = trailer_route(row.get('trailer'))
        if trailer:info['trailer'] = trailer
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
    try:ready,unsupported=providers(media,force=True,provider_id=provider_id)
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
    from action_loading import preparation
    with preparation('search-prepare:'+media):
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
        try:
            keyboard.doModal()
            accepted=keyboard.isConfirmed()
            submitted=keyboard.getText() if accepted else ''
        finally:
            # Release the native IME/dialog owner before validating providers,
            # writing history, or activating a different Kodi window. Retaining
            # this wrapper through ActivateWindow overlapped two GUI lifetimes.
            del keyboard
        if not accepted:return
        try:choice=json.loads(submitted)
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
        ready,unsupported=providers(media,force=True,provider_id=None if aid=='all' else aid)
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
