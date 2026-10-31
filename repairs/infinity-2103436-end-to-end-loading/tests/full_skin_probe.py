"""Actual full-skin native busy/progress presentation. Linux only."""
import json
from pathlib import Path
import time
import traceback
import xbmc
import xbmcgui

OUT=Path('/tmp/infinity-full-skin-evidence');OUT.mkdir(exist_ok=True)
result={'platform':'Upstream Linux Kodi21.2 full Infinity skin; no production providers/services','checks':[]}
def check(name,ok):
    result['checks'].append(dict(name=name,passed=bool(ok)))
    if not ok:raise RuntimeError(name)
def shot(name):
    xbmc.sleep(450);xbmc.executebuiltin('TakeScreenshot('+str(OUT/(name+'.png'))+')');xbmc.sleep(300)
try:
    home=xbmcgui.Window(10000)
    home.setProperty('Infinity.Continuity.Observer','active')
    home.setProperty('Infinity.NativeAmbient.WriterLifecycle','running-optional')
    home.setProperty('Infinity.OptionalMotionAllowed','true')
    xbmc.sleep(2000)
    xbmc.executebuiltin('ActivateWindow(Home)');xbmc.sleep(1000)
    check('actual_skin',xbmc.getSkinDir()=='skin.infinity.diggz')
    for label,wid in [('home',10000),('videos',10025),('settings',10004)]:
        xbmc.executebuiltin('ActivateWindow('+str(wid)+')');xbmc.sleep(700)
        check(label+'_active',xbmcgui.getCurrentWindowId()==wid)
        shot(label+'-idle')
        started=time.monotonic()
        xbmc.executebuiltin('ActivateWindow(Videos,plugin://plugin.video.loadingqa/?case='+label+')')
        for _ in range(30):
            if xbmc.getCondVisibility('Window.IsActive(busydialog) | Window.IsActive(busydialognocancel)'):break
            xbmc.sleep(100)
        check(label+'_native_busy',xbmc.getCondVisibility('Window.IsActive(busydialog) | Window.IsActive(busydialognocancel)'))
        result[label+'_busy_base_window']=xbmcgui.getCurrentWindowId()
        # Deliberately retain a matching foreground observer token underneath
        # the native modal: it must not suppress the native drawer projection.
        active=xbmcgui.Window(xbmcgui.getCurrentWindowId())
        home.setProperty('Infinity.Loading.Active','true')
        home.setProperty('Infinity.Loading.Token','qa-overlap')
        active.setProperty('Infinity.Loading.OwnerToken','qa-overlap')
        shot(label+'-busy')
        home.clearProperty('Infinity.Loading.Active')
        home.clearProperty('Infinity.Loading.Token')
        active.clearProperty('Infinity.Loading.OwnerToken')
        for _ in range(60):
            if not xbmc.getCondVisibility('Window.IsActive(busydialog) | Window.IsActive(busydialognocancel)'):break
            xbmc.sleep(100)
        check(label+'_busy_closed',not xbmc.getCondVisibility('Window.IsActive(busydialog) | Window.IsActive(busydialognocancel)'))
        check(label+'_destination_ready',xbmcgui.getCurrentWindowId()==10025 and xbmc.getInfoLabel('Container.NumItems')=='1')
        shot(label+'-completed')
        result[label+'_fixture_busy_seconds']=time.monotonic()-started
    # Required native progress remains its original dialog, including cancellation.
    progress=xbmcgui.DialogProgress();progress.create('Required native progress','QA progress contract')
    progress.update(25,'QA progress contract');shot('native-progress')
    check('native_progress_visible',xbmc.getCondVisibility('Window.IsActive(progressdialog)'))
    progress.close();xbmc.sleep(300)
    check('native_progress_closed',not xbmc.getCondVisibility('Window.IsActive(progressdialog)'))
    result['status']='PASS_NATIVE_LIFETIMES; FULL_SKIN_VISUAL_REVIEW_SEPARATE'
except BaseException:
    result['status']='FAIL';result['error']=traceback.format_exc()
finally:
    (OUT/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
