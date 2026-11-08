"""Disposable Android-only observer and fixed GUI actions; never packaged.

Provider Search always runs unmodified publisher add-ons through Infinity.
The separate local-clip directory is for Info/Play/Trailer controls only.
"""
import hashlib,json,os,sys,time
from pathlib import Path
from urllib.parse import parse_qs
import xbmc,xbmcaddon,xbmcgui,xbmcplugin,xbmcvfs

CC='script.infinity.commandcenter'
QA='script.infinity.finalreleaseqa'
PROVIDERS=['plugin.video.watchnixtoons2','plugin.video.umbrella']
CLIP='special://profile/infinity-final-qa.mp4'

def rpc(method,params=None):
    request=dict(jsonrpc='2.0',id=464,method=method)
    if params is not None:request['params']=params
    result=json.loads(xbmc.executeJSONRPC(json.dumps(request)))
    if 'error' in result:raise RuntimeError(method+': '+json.dumps(result['error']))
    return result.get('result')

def until(fn,description,seconds=90):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if xbmc.Monitor().abortRequested():raise RuntimeError('Application ended during '+description)
        value=fn()
        if value:return value
        xbmc.sleep(100)
    raise RuntimeError('Timed out: '+description)

def snapshot():
    labels=['Container.FolderPath','Container.NumItems','System.CurrentControl','System.CurrentWindow','System.AddonVersion('+CC+')','System.AddonVersion(skin.infinity.diggz)']
    result=dict(pid=os.getpid(),window=xbmcgui.getCurrentWindowId(),dialog=xbmcgui.getCurrentWindowDialogId(),skin=xbmc.getSkinDir(),labels={n:xbmc.getInfoLabel(n) for n in labels})
    count=int(xbmc.getInfoLabel('Container.NumItems') or 0)
    if 0<=count<=200:
        result['rows']=[dict(index=i,label=xbmc.getInfoLabel('Container.ListItemAbsolute(%d).Label'%i),provider=xbmc.getInfoLabel('Container.ListItemAbsolute(%d).Property(Infinity.Search.Provider)'%i),file=xbmc.getInfoLabel('Container.ListItemAbsolute(%d).FileNameAndPath'%i)) for i in range(count+1)]
    result['components']={aid:xbmcaddon.Addon(aid).getAddonInfo('version') for aid in (CC,'skin.infinity.diggz')}
    controller=Path(xbmcvfs.translatePath(xbmcaddon.Addon(CC).getAddonInfo('path')))
    result['controller_files']={n:hashlib.sha256((controller/n).read_bytes()).hexdigest() for n in ('infinity_search.py','plugin.py','addon.xml','INFINITY-MODULES.v1','INFINITY-MODULES.v1.sig')}
    result['controller_path']=str(controller)
    home=xbmcgui.Window(10000)
    result['appearance_observation']=dict(home_properties={n:home.getProperty(n) for n in ('Infinity.SystemTheme','Infinity.NativeSystemTheme')},labels={n:xbmc.getInfoLabel(n) for n in ('Skin.String(Infinity.DarkAppearance)','Skin.CurrentColourTheme','Skin.CurrentTheme','$VAR[InfinityPaletteCardSurface]','$VAR[InfinityBoardBackground]','$VAR[InfinityCollectiveTextPrimary]')})
    return result

def action(request,root):
    kind=request['action']
    if kind=='snapshot':
        result=snapshot()
        if request.get('full') is True:
            controller=Path(result['controller_path'])
            result['module_files']={}
            for line in (controller/'INFINITY-MODULES.v1').read_text().splitlines():
                row=line.split('\t')
                if row[0]=='file':
                    path=controller.parent/row[2]
                    assert path.resolve().is_relative_to(controller.parent.resolve())
                    result['module_files'][row[2]]=hashlib.sha256(path.read_bytes()).hexdigest()
            skin=Path(xbmcvfs.translatePath(xbmcaddon.Addon('skin.infinity.diggz').getAddonInfo('path')))
            result['skin_path']=str(skin)
            result['skin_files']={n:hashlib.sha256((skin/n).read_bytes()).hexdigest() for n in ('addon.xml','infinity-skin.json','Infinity-Protected-Manifest.json','unified/DialogVideoInfo.xml','unified/Includes_InfinityMediaLists.xml')}
        return result
    if kind=='first-use':
        import android_runtime_checks as ui
        result={}
        ui.complete_first_use(xbmcgui.Window(10000),result,lambda stage:(root/'FIRST-USE.json').write_text(json.dumps(result,indent=2)),providers=PROVIDERS)
        for aid in PROVIDERS:assert ui.first_provider_home(aid,result,lambda stage:None,providers=PROVIDERS)
        return dict(status='PASS_UNMODIFIED_TWO_PROVIDER_INITIALIZATION',details=result)
    if kind=='home':
        rpc('GUI.ActivateWindow',dict(window='home'));until(lambda:xbmcgui.getCurrentWindowId()==10000,'Home')
        return snapshot()
    if kind=='search':
        assert xbmc.getSkinDir()=='skin.infinity.diggz'
        media=request.get('media','movie');assert media in ('movie','tv')
        xbmc.executebuiltin('RunScript(script.infinity.commandcenter,universal-search,'+media+')')
        return dict(status='ORIGINAL_HOME_SEARCH_DISPATCHED',pid=os.getpid())
    if kind=='select-row':
        index=request['index'];count=int(xbmc.getInfoLabel('Container.NumItems') or 0)
        assert type(index) is int and 0<=index<=count<=200
        expected=request['file'];assert expected.startswith(tuple('plugin://'+p+'/' for p in PROVIDERS))
        xbmc.executebuiltin('Container.SetViewMode(50)',True)
        xbmc.executebuiltin('SetFocus(50,%d,absolute)'%index,True)
        assert xbmc.getInfoLabel('Container(50).ListItem.FileNameAndPath')==expected
        rpc('Input.Select')
        until(lambda:xbmc.getInfoLabel('Container.FolderPath').rstrip('/')==expected.rstrip('/'),'original provider heading route',120)
        return snapshot()
    if kind=='downloads':
        xbmc.executebuiltin('RunScript(script.infinity.commandcenter,downloads)')
        until(lambda:xbmcgui.getCurrentWindowId()==10025,'native Videos Files')
        xbmc.sleep(1000);return snapshot()
    if kind=='info':
        target='plugin://plugin.video.infinity.finalreleaseqaclip/?action=clip-list'
        xbmc.executebuiltin('ActivateWindow(Videos,"'+target+'",return)')
        until(lambda:xbmc.getInfoLabel('Container.FolderPath')==target and int(xbmc.getInfoLabel('Container.NumItems') or 0)>0,'generated local-clip list')
        xbmc.executebuiltin('Container.SetViewMode(50)',True)
        count=int(xbmc.getInfoLabel('Container(50).NumItems') or 0)
        for i in range(count):
            xbmc.executebuiltin('SetFocus(50,%d,absolute)'%i,True)
            if xbmc.getInfoLabel('Container(50).ListItem.Label')=='QA generated gray clip':break
        else:raise RuntimeError('Generated clip row absent')
        rpc('Input.Info');until(lambda:xbmc.getCondVisibility('Window.IsActive(videoinfo)'),'actual native Info')
        result=snapshot();result['Info_labels']={str(i):xbmc.getInfoLabel('Control.GetLabel(%d)'%i) for i in (8,9012,9011,106)}
        return result
    if kind=='info-click':
        control=request['control'];assert control in (8,9012)
        assert xbmc.getCondVisibility('Window.IsActive(videoinfo)')
        expected='PLAY' if control==8 else 'TRAILER'
        assert xbmc.getInfoLabel('Control.GetLabel(%d)'%control)==expected
        xbmc.executebuiltin('SendClick(12003,%d)'%control)
        until(lambda:xbmc.Player().isPlayingVideo(),'actual '+expected+' starts generated clip',45)
        active=rpc('Player.GetActivePlayers');player=next(p['playerid'] for p in active if p['type']=='video')
        item=rpc('Player.GetItem',dict(playerid=player,properties=['file','title']))
        assert item['item']['file'] in (CLIP,xbmcvfs.translatePath(CLIP)),item
        before=rpc('Player.GetProperties',dict(playerid=player,properties=['time','speed']))
        def advanced():
            value=rpc('Player.GetProperties',dict(playerid=player,properties=['time','speed']))
            return value if value['speed']==1 and value['time']!=before['time'] else None
        after=until(advanced,'actual local video time advances',10)
        rpc('Player.Stop',dict(playerid=player))
        until(lambda:not xbmc.Player().isPlayingVideo(),'selected clip Stop')
        return dict(status='PASS_ACTUAL_INFO_CONTROL_AND_LOCAL_VIDEO',control=control,item=item,before=before,after=after,content='Generated gray clip; no authenticated provider playback claim')
    if kind=='watched':
        import android_runtime_checks as ui
        helper=Path(xbmcvfs.translatePath(xbmcaddon.Addon('script.infinity.uirepair').getAddonInfo('path')))
        sys.path.insert(0,str(helper));from controller_access import load
        plugin=load();hub=plugin.hub;profile=plugin.PROFILE
        before=hub.load_view(profile);key='a'*64
        assert key in before['items'] and not before.get('watched')
        results=[]
        for label,present in [('Mark Watched',True),('Mark Unwatched',False)]:
            xbmc.executebuiltin('RunPlugin(plugin://script.infinity.commandcenter/?action=item-menu&bucket=continue&key='+key+')')
            ui.until(lambda:xbmc.getCondVisibility('System.HasActiveModalDialog') and xbmc.getInfoLabel('Window(%d).Property(Infinity.UI.Popup)'%xbmcgui.getCurrentWindowDialogId())=='1','actual watched popup')
            ui.select_native_item(50,lambda:xbmc.getInfoLabel('Container(50).ListItem.Label')==label,label)
            ui.until(lambda:bool(hub.load_view(profile)['watched'])==present,'actual '+label)
            results.append(dict(action=label,status='PASS_ACTUAL_NATIVE_POPUP_AND_PERSISTENCE'))
        after=hub.load_view(profile)
        for bucket in ('sources','navigation_recovery','lists','watchlist','collection'):assert after[bucket]==before[bucket],bucket
        return dict(cases=results,unrelated_buckets_preserved=True)
    raise ValueError('Unselected QA action')

def plugin_directory():
    handle=int(sys.argv[1]);assert parse_qs(sys.argv[2].lstrip('?'))=={'action':['clip-list']}
    item=xbmcgui.ListItem('QA generated gray clip',path=CLIP)
    item.setInfo('video',dict(title='QA generated gray clip',mediatype='movie',plot='Generated test media for Info controls only.',year=1999,trailer=CLIP,duration=180))
    item.setProperty('IsPlayable','true')
    xbmcplugin.addDirectoryItem(handle,CLIP,item,isFolder=False)
    xbmcplugin.setContent(handle,'movies');xbmcplugin.endOfDirectory(handle,cacheToDisc=False)

def serve():
    root=Path(xbmcvfs.translatePath(xbmcaddon.Addon(QA).getAddonInfo('profile')));root.mkdir(parents=True,exist_ok=True)
    pid=os.getpid();last=0;monitor=xbmc.Monitor()
    (root/'ready.json').write_text(json.dumps(dict(pid=pid,qa=QA)))
    while not monitor.waitForAbort(.15):
        try:request=json.loads((root/'request.json').read_text())
        except (OSError,ValueError):continue
        if request.get('pid')!=pid or type(request.get('sequence')) is not int or request['sequence']<=last:continue
        last=request['sequence'];reply=dict(pid=pid,sequence=last,action=request.get('action'),passed=False)
        try:reply.update(passed=True,result=action(request,root))
        except BaseException as error:reply.update(passed=False,error=type(error).__name__+': '+str(error),traceback=__import__('traceback').format_exc())
        pending=root/'reply.pending';pending.write_text(json.dumps(reply,indent=2));pending.replace(root/'reply.json')

if len(sys.argv)>1 and sys.argv[1].lstrip('-').isdigit():plugin_directory()
else:serve()
