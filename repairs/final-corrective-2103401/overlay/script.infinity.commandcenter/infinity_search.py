"""On-demand Infinity Search using verified, enabled providers' own interfaces.

No provider imports, edits, invented results, account access or persistent cache.
Search All requires the matched native bounded-result protocol. It has one
foreground request at a time and preserves provider invoker/writer accounting.
"""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
import threading
import time
from urllib.parse import urlencode, urlsplit, quote
import uuid
import xml.etree.ElementTree as ET

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

CC='script.infinity.commandcenter'
PROPERTIES=['title','year','plot','genre','art','uniqueid','season','episode','showtitle','playcount','runtime','mpaa','rating','thumbnail']
MAX_RESULTS=40
MAX_PROVIDERS=8
SEREN_PROOF={'addon.xml': '0843bed5a84fd706a0e59a1036114365efb51b20ee3366bf09b6236b985c7a22', 'seren.py': '515f177f58fe40da7bb2ff64c9f9625aa760c99350470389d97fea82dfbe5320', 'resources/lib/modules/router.py': 'cd96ae0e41952dae82e01e39e5cf2337dd85dc2fb1be597108f6545a7f094d90', 'resources/lib/modules/globals.py': 'ab943ec1dddb26e8172f46b2f4f446a06efdc0c9b9d9adc6a22e689798b623b8', 'resources/lib/common/tools.py': '558f5a58f2eefb0ab920db3b9b5961eb10203144e96a55a162711d59b5ee35cb', 'resources/lib/gui/movieMenus.py': 'a3bcdb8ff489bee4ffb3858c47ca660bd0781edd144758ca7b869a02988a02e7', 'resources/lib/gui/tvshowMenus.py': '721ad77ccd318fd6ce52975e75d5ae3c2c81c918f4ac06005acb82798f0b8839'}
HISTORY_KEY="infinity_search_history_v1"
HISTORY_LIMIT=50


def rpc(method, params):
    return json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params))))


def _read(root,name):
    path=root/name
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('source unavailable')
    with path.open('rb') as stream:raw=stream.read(512*1024+1)
    if len(raw)>512*1024:raise ValueError('source limit')
    return raw,ast.parse(raw.decode('utf-8-sig'))


def _branch(tree,variable,value):
    for node in ast.walk(tree):
        if not isinstance(node,ast.If):continue
        compare=node.test
        if isinstance(compare,ast.Compare) and len(compare.ops)==1 and isinstance(compare.ops[0],ast.Eq):
            left=compare.left
            left_name=left.id if isinstance(left,ast.Name) else left.attr if isinstance(left,ast.Attribute) else ''
            if left_name==variable and any(isinstance(c,ast.Constant) and c.value==value for c in compare.comparators):
                yield node


def _getter(tree,variable,key):
    for node in ast.walk(tree):
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==variable for t in node.targets):
            call=node.value
            if isinstance(call,ast.Call) and isinstance(call.func,ast.Attribute) and call.func.attr=='get' and call.args and isinstance(call.args[0],ast.Constant) and call.args[0].value==key:
                return True
    return False


def _forwarded(branch,method,argument):
    return any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr==method and
               n.args and isinstance(n.args[0],ast.Name) and n.args[0].id==argument
               for statement in branch.body for n in ast.walk(statement))


def recipe(root,media):
    """Check the actual installed router and its receiving search method."""
    root=Path(root).resolve();pins={}
    def source(name):
        raw,tree=_read(root,name);pins[name]=hashlib.sha256(raw).hexdigest();return tree
    # Umbrella-style term endpoints accept the supplied name without opening
    # another keyboard. Never assume movieSearch itself accepts a query.
    try:
        router=source('resources/lib/modules/router.py')
        endpoint='movieSearchterm' if media=='movie' else 'tvSearchterm'
        menus=source('resources/lib/menus/'+('movies.py' if media=='movie' else 'tvshows.py'))
        if (_getter(router,'name','name') and any(_forwarded(b,'search_term','name') for b in _branch(router,'action',endpoint)) and
                any(isinstance(n,ast.FunctionDef) and n.name=='search_term' and len(n.args.args)>=2 for n in ast.walk(menus))):
            return dict(params={'action':endpoint},query_key='name',pins=pins,
                        history={'action':'movieSearch' if media=='movie' else 'tvSearch'})
    except (OSError,ValueError,SyntaxError,UnicodeError):pass
    pins={}
    # Exact reviewed Seren 4.3.214 router, globals decoder, query receivers and
    # entrypoint. Its manifest/service fingerprints match the user's Fold.
    # Do not infer support merely from a method named movies_search.
    try:
        verified={}
        for name,pin in SEREN_PROOF.items():
            path=root/name
            if path.is_symlink() or not path.is_file() or path.stat().st_size>512*1024:
                raise ValueError('Seren source unavailable')
            raw=path.read_bytes()
            if hashlib.sha256(raw).hexdigest()!=pin:raise ValueError('Seren source changed')
            verified[name]=pin
        endpoint='moviesSearch' if media=='movie' else 'showsSearch'
        return dict(params={'action':endpoint},query_key='action_args',query_codec='seren_json',
                    pins=verified,history={'action':'moviesSearchHistory' if media=='movie' else 'showsSearchHistory'})
    except (OSError,ValueError):pass
    pins={}
    # POV/Fen-family dispatch is verified from its real route table or branch,
    # followed by the selected movie/TV query receiver, without executing it.
    for entry in ('resources/lib/modules/entry.py','resources/lib/modules/router.py','resources/lib/pov.py','default.py'):
        try:
            router=source(entry)
            mode='build_movie_list' if media=='movie' else 'build_tvshow_list'
            endpoint='tmdb_movies_search' if media=='movie' else 'tmdb_tv_search'
            menu_path='resources/lib/menus/'+('movies.py' if media=='movie' else 'tvshows.py')
            menus=source(menu_path)
            route=False
            for n in ast.walk(router):
                if isinstance(n,ast.Dict):
                    for key,value in zip(n.keys,n.values):
                        if isinstance(key,ast.Constant) and key.value==mode and isinstance(value,ast.Lambda):
                            route=any(isinstance(x,ast.Constant) and x.value==('menus.movies' if media=='movie' else 'menus.tvshows') for x in ast.walk(value))
                elif isinstance(n,ast.If) and any(True for _ in _branch(ast.Module(body=[n],type_ignores=[]),'mode',mode)):
                    route=route or any(isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr in ('run','get') for x in ast.walk(n))
            receivers=list(_branch(menus,'action',endpoint))
            query=any(isinstance(n,ast.Constant) and n.value=='query' for branch in receivers for statement in branch.body for n in ast.walk(statement))
            if route and receivers and query:
                history=source('resources/lib/menus/history.py')
                history_ok=any(isinstance(n,ast.Subscript) and isinstance(n.value,ast.Name) and n.value.id=='params' and
                               isinstance(n.slice,ast.Constant) and n.slice.value=='action'
                               for n in ast.walk(history))
                if not history_ok:continue
                return dict(params={'mode':mode,'action':endpoint},query_key='query',pins=pins,
                            history={'mode':'search_history','action':'movie' if media=='movie' else 'tvshow'})
        except (OSError,ValueError,SyntaxError,UnicodeError):continue
    return None


def providers(media):
    result=rpc('Addons.GetAddons',dict(type='xbmc.addon.video',enabled=True,properties=['name','path','version']))
    rows=result.get('result',{}).get('addons') or []
    priority={'plugin.video.umbrella':0,'plugin.video.pov':1,'plugin.video.seren':2}
    rows=sorted(rows,key=lambda row:priority.get(row.get('addonid'),3))[:MAX_PROVIDERS]
    ready,unsupported=[],[]
    for row in rows:
        aid=row.get('addonid','')
        if not aid.startswith('plugin.video.') or not all(c.isalnum() or c in '._-' for c in aid):continue
        try:
            addon=xbmcaddon.Addon(aid)
            root=Path(xbmcvfs.translatePath(addon.getAddonInfo('path'))).resolve()
            with (root/'addon.xml').open('rb') as stream:raw=stream.read(131073)
            if len(raw)>131072 or b'<!DOCTYPE' in raw:raise ValueError('manifest limit')
            manifest=ET.fromstring(raw)
            if manifest.get('id')!=aid or manifest.find('extension[@point="xbmc.python.pluginsource"]') is None:
                raise ValueError('not a Python video provider')
            contract=recipe(root,media)
            if contract:
                contract['pins']['addon.xml']=hashlib.sha256(raw).hexdigest()
                ready.append(dict(id=aid,name=row.get('name') or aid,root=str(root),contract=contract))
            else:unsupported.append(row.get('name') or aid)
        except (OSError,ValueError,RuntimeError,ET.ParseError):unsupported.append(row.get('name') or aid)
    return ready,unsupported


def route(provider,query=None,history=False):
    contract=provider['contract'];root=Path(provider['root'])
    if not xbmc.getCondVisibility('System.AddonIsEnabled('+provider['id']+')'):
        raise RuntimeError('Provider is unavailable or disabled.')
    for name,pin in contract['pins'].items():
        p=root/name
        if p.is_symlink() or not p.is_file() or p.stat().st_size>512*1024:
            raise RuntimeError('Provider changed. Reopen Infinity Search to verify its interface.')
        with p.open('rb') as stream:raw=stream.read(512*1024+1)
        if hashlib.sha256(raw).hexdigest()!=pin:
            raise RuntimeError('Provider changed. Reopen Infinity Search to verify its interface.')
    params=dict(contract['history'] if history else contract['params'])
    if query is not None and not history:
        if not isinstance(query,str) or not query.strip() or len(query)>160:
            raise ValueError('Enter a search query')
        # Seren's globals parse URL parameters then its helper unquotes and
        # JSON-decodes action_args. Preserve literal %, quotes, null and numbers.
        params[contract['query_key']]=(quote(json.dumps(query,ensure_ascii=True),safe='')
            if contract.get('query_codec')=='seren_json' else query)
    return 'plugin://'+provider['id']+'/?'+urlencode(params)


def _leased_directory(path,home,progress=None):
    token=uuid.uuid4().hex
    home.setProperty('Infinity.Search.Request.'+token,hashlib.sha256(path.encode('utf-8')).hexdigest())
    output=[]
    def request():
        try:output.append(rpc('Files.GetDirectory',dict(directory=path+'|infinity_search='+token,media='video',
                            properties=PROPERTIES,limits={'start':0,'end':MAX_RESULTS})))
        except (ValueError,RuntimeError):output.append({'error':{'message':'provider_failed'}})
    worker=threading.Thread(target=request,name='InfinitySearchResult');worker.start()
    monitor=xbmc.Monitor()
    while worker.is_alive():
        if monitor.abortRequested() or (progress is not None and progress.iscanceled()):
            home.setProperty('Infinity.Search.Cancel.'+token,'1')
        worker.join(.05)
    status=home.getProperty('Infinity.Search.Result.'+token)
    for key in ('Request.','Cancel.','Result.'):home.clearProperty('Infinity.Search.'+key+token)
    answer=output[0] if output else {'error':{}}
    return status,answer


def search_all(handle,media,query):
    if media not in ('movie','tv') or not isinstance(query,str) or not query.strip() or len(query)>160:return
    home=xbmcgui.Window(10000)
    # Harmless first-party probe: older engines do not publish the protocol.
    # Never give a provider the private protocol option on an unsupported APK.
    if home.getProperty('Infinity.Search.Protocol')!='1':
        _leased_directory('plugin://'+CC+'/?action=search-probe',home)
    if home.getProperty('Infinity.Search.Protocol')!='1':
        xbmcgui.Dialog().ok('Infinity Search','Search All requires the matching 2103394 APK. Provider search remains available.')
        return
    ready,unsupported=providers(media);progress=xbmcgui.DialogProgress();progress.create('Infinity Search','Searching compatible providers')
    xbmcplugin.setPluginCategory(handle,'Infinity Search — '+('Movies' if media=='movie' else 'TV Shows'))
    xbmcplugin.setContent(handle,'movies' if media=='movie' else 'tvshows')
    try:
        for position,provider in enumerate(ready):
            if progress.iscanceled() or xbmc.Monitor().abortRequested():break
            progress.update(int(position*100/max(1,len(ready))),provider['name'])
            try:path=route(provider,query)
            except RuntimeError:continue
            signature=hashlib.sha256((str(xbmcvfs.translatePath('special://profile'))+path+json.dumps(provider['contract']['pins'],sort_keys=True)).encode()).hexdigest()
            cache_key='Infinity.Search.Cache.'+provider['id']
            try:cache=json.loads(home.getProperty(cache_key) or '{}')
            except ValueError:cache={}
            if cache.get('signature')==signature and 0<=time.monotonic()-cache.get('at',0)<300:
                answer=cache['answer'];status='completed'
            else:
                status,answer=_leased_directory(path,home,progress)
                if status=='completed' and 'error' not in answer:
                    cache=json.dumps(dict(signature=signature,at=time.monotonic(),answer=answer))
                    if len(cache)<300000:home.setProperty(cache_key,cache)
            rows=answer.get('result',{}).get('files') or []
            heading=xbmcgui.ListItem(provider['name']+' — '+(str(len(rows))+' results' if status=='completed' else status or 'unavailable'))
            heading.setProperty('IsPlayable','false')
            # Opening the original provider group retains all of its own
            # context actions and search history. No actions are fabricated.
            xbmcplugin.addDirectoryItem(handle,path,heading,isFolder=True)
            for row in rows[:MAX_RESULTS]:
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
                item.addContextMenuItems([('Open in '+provider['name'],'ActivateWindow(Videos,"'+path+'",return)')])
                xbmcplugin.addDirectoryItem(handle,target,item,isFolder=row.get('filetype')=='directory')
        for name in unsupported:
            item=xbmcgui.ListItem(name+' — supplied-query search interface not verified')
            item.setProperty('IsPlayable','false');xbmcplugin.addDirectoryItem(handle,'',item,isFolder=False)
    finally:progress.close()


def open_search(media='movie'):
    if xbmc.getSkinDir()!='skin.infinity.diggz' or media not in ('movie','tv'):return
    ready,unsupported=providers(media)
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
                         description='Search '+('movies' if media=='movie' else 'TV shows')+' · select, then press Search',
                         icon=xbmcvfs.translatePath(icon)))
    # Availability is explicit for compatible examples, with no invented route.
    expected={'plugin.video.umbrella':'Umbrella','plugin.video.pov':'POV','plugin.video.seren':'Seren',
              'plugin.video.fenlight':'Fen Light','plugin.video.themoviedb.helper':'TMDb Helper'}
    for aid,name in expected.items():
        if aid not in {p['id'] for p in ready}:
            enabled=xbmc.getCondVisibility('System.AddonIsEnabled('+aid+')')
            rows.append(dict(id=aid,name=name,available=False,icon='',
                       description='Search interface not verified' if enabled else 'Not installed or disabled'))
    current='';selected='all';view='search'
    while not xbmc.Monitor().abortRequested():
        try:history_rows=shared_history()
        except (OSError,ValueError,RuntimeError) as error:
            from infinity_trakt import notice
            notice(str(error),'Infinity Search');return
        heading='Infinity.Search.2103395:'+json.dumps(dict(token=token,theme=theme,
            media='Movies' if media=='movie' else 'TV Shows',providers=rows[:24],
            shared_history=history_rows,selected=selected,initial_view=view),separators=(',',':'))
        keyboard=xbmc.Keyboard(current,heading,False)
        keyboard.doModal()
        if not keyboard.isConfirmed():return
        try:choice=json.loads(keyboard.getText())
        except (ValueError,TypeError):return
        if not isinstance(choice,dict) or choice.get('token')!=token:return
        query=choice.get('query');aid=choice.get('provider')
        if not isinstance(query,str) or len(query)>160:return
        if choice.get('operation')=='clear-history' and choice.get('confirmed') is True:
            shared_history(clear=True)
            current=query;selected=aid;view='history';continue
        legacy_history=choice.get('history') is True
        if not query.strip() and not legacy_history:return
        query=query.strip()
        if aid=='all' and not legacy_history:
            if not ready:return
            # Revalidate every admitted interface at submission, never on tap.
            for provider in ready:route(provider,query)
            target='plugin://'+CC+'/?'+urlencode(dict(action='search-all',media=media,query=query))
            provider_name='Search All'
        else:
            provider=next((p for p in ready if p['id']==aid),None)
            if provider is None:return
            target=route(provider,query,history=legacy_history);provider_name=provider['name']
        xbmc.executebuiltin('ActivateWindow(Videos,"'+target+'",return)',True)
        if not legacy_history:shared_history(query=query,media=media,provider=aid,name=provider_name)
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
            if not isinstance(row,dict) or set(row)!={'query','media','provider','name','at'} or not isinstance(row['query'],str) or not 1<=len(row['query'])<=160 or row['media'] not in ('movie','tv') or not isinstance(row['provider'],str) or len(row['provider'])>110 or not isinstance(row['name'],str) or len(row['name'])>100 or type(row['at']) is not int or not 0<=row['at']<=4102444800:
                raise RuntimeError('The saved search history is incompatible. Existing records were retained.')
        if clear:
            if history:value[HISTORY_KEY]=[];atomic_json(path,value)
            return []
        if query is not None:
            if not isinstance(query,str) or not query.strip() or len(query)>160 or media not in ('movie','tv') or not isinstance(provider,str) or len(provider)>110 or not isinstance(name,str):
                raise ValueError('Invalid submitted search')
            row=dict(query=query.strip(),media=media,provider=provider,name=name[:100],at=int(time.time()))
            history=[row]+[r for r in history if (r['query'].casefold(),r['media'])!=(row['query'].casefold(),media)]
            value[HISTORY_KEY]=history[:HISTORY_LIMIT];atomic_json(path,value)
        return history[:HISTORY_LIMIT]
