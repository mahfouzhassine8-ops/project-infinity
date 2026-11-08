"""Disposable real Kodi observer. No provider code replacement or callback mock."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

CC='script.infinity.commandcenter'
QA='script.infinity.finalreleaseqa'
PROVIDERS=('plugin.video.pov','plugin.video.umbrella')
EVENTS=None
BOOTSTRAP_SHA256='75821ef1dc3a42d1b5029f7d296f628fc19c3fea54c619b7a93acd1fb395576f'
BOOTSTRAP_MANIFEST=None


class ActualPlayerEvents(xbmc.Player):
    """Evidence subscriber only: genuine SDK callbacks; no control or progress writes."""
    def __init__(self):
        super().__init__()
        self.events=[]
    def record(self,name):
        self.events.append(dict(event=name,monotonic=time.monotonic()))
        self.events[:]=self.events[-64:]
    def onPlayBackStarted(self):self.record('Started')
    def onAVStarted(self):self.record('AVStarted')
    def onPlayBackStopped(self):self.record('Stopped')
    def onPlayBackEnded(self):self.record('Ended')
    def onPlayBackError(self):self.record('Error')


def rpc(method,params=None):
    request=dict(jsonrpc='2.0',id=468,method=method)
    if params is not None:request['params']=params
    value=json.loads(xbmc.executeJSONRPC(json.dumps(request)))
    if 'error' in value:raise RuntimeError(method+': '+json.dumps(value['error']))
    return value.get('result')


def until(fn,label,seconds=90):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if xbmc.Monitor().abortRequested():raise RuntimeError('Process ended during '+label)
        value=fn()
        if value:return value
        xbmc.sleep(100)
    raise RuntimeError('Timed out: '+label)


def authenticated_bootstrap(root):
    """Run the exact existing entry bootstrap before importing any owned helper."""
    global BOOTSTRAP_MANIFEST
    entry=root/'default.py'
    with entry.open('rb') as stream:source=stream.read(4*1024*1024+1)
    begin=b'# INFINITY_AUTHENTICATED_MODULE_BOOTSTRAP_V1\n'
    end=b'# END_INFINITY_AUTHENTICATED_MODULE_BOOTSTRAP_V1\n'
    assert len(source)<=4*1024*1024 and source.count(begin)==1 and source.count(end)==1
    block=begin+source.split(begin,1)[1].split(end,1)[0]+end
    assert hashlib.sha256(block).hexdigest()==BOOTSTRAP_SHA256,'EXACT_EXISTING_AUTHENTICATED_ENTRY_BOOTSTRAP_REQUIRED'
    # The unmodified entry bootstrap pins module_contract.py, filters owned import
    # paths, and performs the existing real native signature/source handshake.
    namespace={'__name__':'infinity_disposable_qa_bootstrap','__file__':__file__}
    exec(compile(block,str(entry),'exec',dont_inherit=True),namespace)
    contract=namespace['_infinity_contract']
    assert contract.source(CC+'/default.py')==source,'ACTUAL_INSTALLED_ENTRY_SOURCE_MUST_MATCH_NATIVE_AUTHENTICATED_MANIFEST'
    BOOTSTRAP_MANIFEST=contract.identity.manifest_sha256


def controller():
    root=Path(xbmcvfs.translatePath(xbmcaddon.Addon(CC).getAddonInfo('path')))
    authenticated_bootstrap(root)
    if str(root) not in sys.path:sys.path.insert(0,str(root))
    helper=root/'infinity_modules/uirepair'
    assert (helper/'controller_access.py').is_file(),'AUTHENTICATED_CONTROLLER_ACCESS_REQUIRED'
    if str(helper) not in sys.path:sys.path.insert(0,str(helper))
    from controller_access import load
    return load()


def identity():
    plugin=controller()
    root=Path(xbmcvfs.translatePath(xbmcaddon.Addon(CC).getAddonInfo('path')))
    files={}
    for line in (root/'INFINITY-MODULES.v1').read_text().splitlines():
        fields=line.split('\t')
        if fields[0]=='file':
            path=root.parent/fields[2]
            assert path.resolve().is_relative_to(root.parent.resolve())
            files[fields[2]]=hashlib.sha256(path.read_bytes()).hexdigest()
    pins=json.loads((Path(__file__).parent/'producer-pins.json').read_text())
    actual={}
    for aid,contract in pins.items():
        addon=xbmcaddon.Addon(aid);source=Path(xbmcvfs.translatePath(addon.getAddonInfo('path')))
        observed={name:hashlib.sha256((source/name).read_bytes()).hexdigest() for name in contract['files']}
        assert addon.getAddonInfo('version')==contract['version'] and observed==contract['files']
        actual[aid]=dict(version=addon.getAddonInfo('version'),files=observed,path=str(source))
    return dict(pid=os.getpid(),module_files=files,module_count=len(files),producer_sources=actual,
                controller_path=str(root),loaded_controller=str(plugin.__file__),Python_optimization=sys.flags.optimize,
                observer_bootstrap=dict(entry='default.py',bootstrap_sha256=BOOTSTRAP_SHA256,native_manifest_sha256=BOOTSTRAP_MANIFEST,helper_loader=type(sys.modules['controller_access'].__loader__).__name__),
                cc_version=xbmcaddon.Addon(CC).getAddonInfo('version'),skin=xbmc.getSkinDir())


def state():
    plugin=controller();data=plugin.hub.load_view(plugin.PROFILE)
    result=dict(data=data,progress_shows=plugin.hub.progress_shows(data),next_episodes=plugin.hub.next_episodes(data))
    return result


def snapshot():
    count=int(xbmc.getInfoLabel('Container.NumItems') or 0)
    assert 0<=count<=1000,'BOUNDED_ACTUAL_DIRECTORY_REQUIRED'
    rows=[]
    for i in range(count+1):
        prefix='Container.ListItemAbsolute(%d).'%i
        row=dict(index=i,label=xbmc.getInfoLabel(prefix+'Label'),file=xbmc.getInfoLabel(prefix+'FileNameAndPath'))
        for key in ('Infinity.ResumeHub.Key','Infinity.Selection.Snapshot','Infinity.Watchlist.Child'):
            row[key]=xbmc.getInfoLabel(prefix+'Property('+key+')')
        rows.append(row)
    menus={}
    for control in (50,450,1000):
        n=int(xbmc.getInfoLabel('Container(%d).NumItems'%control) or 0)
        if 0<n<=100:
            menus[str(control)]=[xbmc.getInfoLabel('Container(%d).ListItemAbsolute(%d).Label'%(control,i)) for i in range(n+1)]
    return dict(pid=os.getpid(),window=xbmcgui.getCurrentWindowId(),dialog=xbmcgui.getCurrentWindowDialogId(),
                folder=xbmc.getInfoLabel('Container.FolderPath'),rows=rows,menus=menus,
                dialog_xml=(xbmcgui.Window(xbmcgui.getCurrentWindowDialogId()).getProperty('xmlfile') if xbmcgui.getCurrentWindowDialogId() not in (0,-1,9999) else ''),
                heading=xbmc.getInfoLabel('Control.GetLabel(1)'),
                body=xbmc.getInfoLabel('Control.GetLabel(9)'),skin=xbmc.getSkinDir())


def focus(request):
    expected=request['file'];index=request['index']
    assert expected.startswith(('plugin://script.infinity.commandcenter/','plugin://plugin.video.pov/'))
    assert type(index) is int and 0<=index<=1000
    xbmc.executebuiltin('Container.SetViewMode(50)',True)
    xbmc.executebuiltin('SetFocus(50,%d,absolute)'%index,True)
    assert xbmc.getInfoLabel('Container(50).ListItem.FileNameAndPath')==expected,'LIVE_NATIVE_LISTITEM_PATH_REQUIRED'
    return expected


def action(request):
    kind=request['action']
    if kind=='events':return list(EVENTS.events)
    if kind=='identity':return identity()
    if kind=='state':return state()
    if kind=='snapshot':return snapshot()
    if kind=='configure':
        assert request['base']=='http://10.0.2.2:'+str(request['port'])
        addon=xbmcaddon.Addon('plugin.video.pov')
        values={'provider.aiostreams':'true','aio.instance':'1','aio.custom_url':request['base'],
                'aio.username':'fixture','aio.password':'fixture','auto_play_movie':'true','auto_play_episode':'true',
                'auto_resume_movie':'0','auto_resume_episode':'0','autoplay_next_episode':'false','autoscrape_next_episode':'false'}
        for key,value in values.items():addon.setSetting(key,value)
        assert all(addon.getSetting(k)==v for k,v in values.items())
        return dict(disposable_profile_only=True,synthetic_AIO_credentials=True,provider_source_modified=False,settings=values)
    if kind=='provider-start-new':
        dialog=xbmcgui.getCurrentWindowDialogId()
        assert dialog not in (0,-1,9999)
        window=xbmcgui.Window(dialog)
        addon=xbmcaddon.Addon('plugin.video.pov')
        assert Path(window.getProperty('xmlfile')).name=='progress_media.xml'
        assert window.getProperty('tikiskins.source_progress.buttons')=='true'
        assert window.getProperty('tikiskins.source_progress.false_button')==addon.getLocalizedString(32833)
        assert xbmc.getInfoLabel('Control.GetLabel(11)')==addon.getLocalizedString(32833)
        xbmc.executebuiltin('SendClick(%d,11)'%dialog)
        return dict(actual_provider_start_from_beginning=True,provider_bookmark_edited_by_harness=False)
    if kind=='initialize':
        import android_runtime_checks as ui
        result={}
        ui.complete_first_use(xbmcgui.Window(10000),result,lambda stage:None,providers=list(PROVIDERS))
        return dict(status='ACTUAL_SELECTED_PROVIDER_FIRST_USE',details=result)
    if kind=='watchlist':
        route='plugin://script.infinity.commandcenter/?action=library&bucket=watchlist'
        rpc('GUI.ActivateWindow',dict(window='videos',parameters=[route,'return']))
        until(lambda:xbmc.getInfoLabel('Container.FolderPath')==route and int(xbmc.getInfoLabel('Container.NumItems') or 0)>=2,'actual Watchlist directory',90)
        return snapshot()
    if kind=='click':
        expected=focus(request);rpc('Input.Select')
        return dict(status='ACTUAL_NATIVE_SELECTED_ITEM_CLICK',file=expected,live_ListItem_read=True)
    if kind=='popup-open':
        focus(request);rpc('Input.ContextMenu')
        until(lambda:xbmcgui.getCurrentWindowDialogId() not in (0,-1,9999),'actual native context menu',10)
        return snapshot()
    if kind=='menu-select':
        control=request['control'];index=request['index'];label=request['label']
        assert control in (50,450,1000) and type(index) is int and 0<=index<=100
        assert xbmcgui.getCurrentWindowDialogId() not in (0,-1,9999)
        xbmc.executebuiltin('SetFocus(%d,%d,absolute)'%(control,index),True)
        assert xbmc.getInfoLabel('Container(%d).ListItem.Label'%control)==label,'LIVE_NATIVE_MENU_LABEL_REQUIRED'
        rpc('Input.Select');return dict(selected_actual_label=label)
    raise ValueError('UNSELECTED_QA_ACTION: '+str(kind))


def serve():
    global EVENTS
    EVENTS=ActualPlayerEvents()
    root=Path(xbmcvfs.translatePath(xbmcaddon.Addon(QA).getAddonInfo('profile')));root.mkdir(parents=True,exist_ok=True)
    pid=os.getpid();last=0;monitor=xbmc.Monitor()
    (root/'ready.json').write_text(json.dumps(dict(pid=pid,qa=QA)))
    while not monitor.waitForAbort(.15):
        try:
            raw=(root/'request.json').read_text()
            if len(raw.encode('utf-8'))>65536:raise ValueError('BOUNDED_QA_REQUEST_REQUIRED')
            request=json.loads(raw)
        except (OSError,ValueError):continue
        if request.get('pid')!=pid or type(request.get('sequence')) is not int or request['sequence']<=last:continue
        last=request['sequence'];reply=dict(pid=pid,sequence=last,passed=False)
        try:reply.update(passed=True,result=action(request))
        except BaseException as error:reply.update(error=repr(error),traceback=traceback.format_exc())
        payload=json.dumps(reply,indent=2)
        if len(payload.encode('utf-8'))>2*1024*1024:
            payload=json.dumps(dict(pid=pid,sequence=last,passed=False,error='BOUNDED_2MIB_QA_REPLY_EXCEEDED'))
        pending=root/'reply.pending';pending.write_text(payload);pending.replace(root/'reply.json')


if __name__=='__main__':serve()
