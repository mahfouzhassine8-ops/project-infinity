"""Run only inside isolated Linux Kodi fixture. Not Android acceptance."""
import json
from pathlib import Path
import sys
import time
import traceback
import xbmc
import xbmcgui

OUT = Path('/tmp/infinity-kodi-renderer/evidence')
OUT.mkdir(exist_ok=True)
sys.dont_write_bytecode = True
if xbmcgui.Window(10000).getProperty('QA.LoadingProbeStarted') == 'true':
    raise SystemExit
xbmcgui.Window(10000).setProperty('QA.LoadingProbeStarted','true')
sys.path.insert(0, '/workspace/project-infinity/repairs/infinity-2103436-end-to-end-loading/overlay/script.infinity.commandcenter')
import action_loading as loading

result = {'platform':'Debian Kodi21.2 fixture, not signed APK', 'checks':[]}

def require(name, value):
    result['checks'].append({'name':name, 'passed':bool(value)})
    assert value, name

def capture(name):
    # Screenshot builtin queues against the current rendered frame; give Kodi
    # a rendering turn after property changes. This is fixture capture settling,
    # never a production delay or a navigation timing measurement.
    xbmc.sleep(350)
    xbmc.executebuiltin('TakeScreenshot('+str(OUT/(name+'.png'))+')')
    xbmc.sleep(350)

try:
    # Finite fixture settling only; no production timer or readiness assertion.
    xbmc.sleep(1000)
    result['startup_ids'] = [xbmcgui.getCurrentWindowId(), xbmcgui.getCurrentWindowDialogId()]
    monitor = loading.make_monitor(xbmc, xbmcgui)
    notification_states=[]
    original_notification=type(monitor).onNotification
    def record_notification(self,sender,method,data):
        original_notification(self,sender,method,data)
        if sender==loading.SENDER:
            try:notification_states.append(json.loads(data).get('state'))
            except (TypeError,ValueError):pass
    type(monitor).onNotification=record_notification
    home = xbmcgui.Window(10000)
    monitor.tick()
    capture('00-idle')
    for name, window in [('home',10000), ('custom',11190)]:
        if window != 10000:
            xbmc.executebuiltin('ActivateWindow(11190)')
            xbmc.sleep(350)
        monitor.tick()
        ctx = loading._context(xbmc, xbmcgui)
        result[name+'_context'] = ctx
        require(name+'_native_window',ctx['window']==window)
        require(name+'_registered_existing_border',ctx['framed'])
        with loading.preparation('fixture:'+name):
            for _ in range(3):
                xbmc.sleep(250); monitor.tick()
            token = home.getProperty(loading.PREFIX+'Token')
            require(name+'_selected_active',home.getProperty(loading.PREFIX+'Active')=='true')
            require(name+'_local_token',bool(token) and xbmcgui.Window(window).getProperty(loading.PREFIX+'OwnerToken')==token)
            require(name+'_native_condition',xbmc.getCondVisibility('String.IsEqual(Window.Property(Infinity.Loading.OwnerToken),Window(Home).Property(Infinity.Loading.Token))'))
            capture('10-'+name+'-selected')
            home.setProperty('Infinity.OptionalMotionAllowed','false')
            capture('11-'+name+'-reduced-motion')
            home.clearProperty('Infinity.OptionalMotionAllowed')
        xbmc.sleep(250); monitor.tick()
        require(name+'_terminal_cleared',home.getProperty(loading.PREFIX+'Active')=='false' and not xbmcgui.Window(window).getProperty(loading.PREFIX+'OwnerToken'))
        capture('12-'+name+'-completed')
    xbmc.executebuiltin('ActivateWindow(Home)'); xbmc.sleep(350); monitor.tick()
    with loading.preparation('fixture:background',background=True):
        for _ in range(3): xbmc.sleep(250); monitor.tick()
        require('background_global',home.getProperty(loading.PREFIX+'Global')=='true')
        capture('20-background')
    xbmc.sleep(250); monitor.tick()
    require('background_terminal',home.getProperty(loading.PREFIX+'Global')=='false')
    capture('21-background-completed')
    # Actual Kodi control activation, XML action/dispatch notifications and the
    # original RunScript handler. The finite worker is explicitly a QA fixture.
    require('xml_original_addon_guard_enabled',xbmc.getCondVisibility('System.AddonIsEnabled(script.infinity.commandcenter)'))
    for attempt in ('complete','back'):
        xbmc.executebuiltin('ActivateWindow(11190)'); xbmc.sleep(350); monitor.tick()
        xbmc.executebuiltin('Action(Select)')
        seen=False
        for _ in range(8):
            xbmc.sleep(150); monitor.tick()
            if home.getProperty(loading.PREFIX+'Active')=='true':seen=True;break
        require('native_click_'+attempt+'_pending',seen)
        if attempt=='back':
            xbmc.executebuiltin('Action(Back)'); xbmc.sleep(350); monitor.tick()
            require('native_back_changed_window',xbmcgui.getCurrentWindowId()!=11190)
            require('native_back_cleared_selected',home.getProperty(loading.PREFIX+'Active')=='false')
        for _ in range(16): xbmc.sleep(150); monitor.tick()
        require('native_click_'+attempt+'_cleared',home.getProperty(loading.PREFIX+'Active')=='false')
    calls=[json.loads(line) for line in (OUT/'click-trace.jsonl').read_text().splitlines()]
    require('one_original_invocation_per_click',sum(v['state']=='invoked' for v in calls)==2)
    require('both_handlers_completed',sum(v['state']=='completed' for v in calls)==2)
    result['native_notification_states']=notification_states
    require('two_xml_start_notifications',notification_states.count('action')==2)
    require('two_xml_dispatch_notifications',notification_states.count('dispatched')==2)
    result['fixture_trace']=calls
    result['status']='PASS_NATIVE_STATE_AND_CAPTURE; VISUAL_PIXEL_REVIEW_SEPARATE'
except BaseException:
    result['status']='FAIL'; result['error']=traceback.format_exc()
finally:
    (OUT/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
