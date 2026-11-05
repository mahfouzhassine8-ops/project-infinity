"""Changed-control dispatch only, synthetic data and trailer receiver; no playback."""
import json, time, traceback
from pathlib import Path
import xbmc, xbmcgui
BASE = Path(QA_PATH)
C = json.loads((BASE/'config.json').read_text())
OUT = Path(C['output'])
R = dict(platform='upstream Linux Kodi with disclosed responsive projection',
         Android='NOT_RUN', Fold='NOT_RUN', source_hashes=C['media_sources'],
         trailer='Synthetic receiver: dispatch only, not actual bridge playback', checks=[])
def wait(p, seconds=12):
    until = time.monotonic()+seconds
    while time.monotonic()<until:
        if p(): return True
        xbmc.sleep(100)
    return False
def check(name, ok):
    R['checks'].append(dict(name=name, passed=bool(ok)))
    if not ok: raise RuntimeError(name)
def focus(cid):
    xbmc.executebuiltin('SetFocus(%d)' % cid, True)
    check('focus-'+str(cid), wait(lambda: xbmcgui.Window(xbmcgui.getCurrentWindowDialogId()
          if xbmcgui.getCurrentWindowDialogId()!=9999 else 10025).getFocusId()==cid))
try:
    check('skin-ready', wait(lambda: xbmc.getInfoLabel('Skin.CurrentTheme')!='' and xbmcgui.getCurrentWindowId()!=10099,35))
    for _ in range(3):
        if xbmcgui.getCurrentWindowDialogId()==9999: break
        check('known-fixture-notice', xbmcgui.getCurrentWindowDialogId()==10100 and xbmc.getInfoLabel('Control.GetLabel(1)')=='Disabled add-ons')
        xbmc.executebuiltin('Action(Select)',True); xbmc.sleep(700)
    home=xbmcgui.Window(10000)
    home.setProperty('Infinity.OptionalMotionAllowed','false')
    xbmc.executebuiltin('Skin.SetString(Infinity.HomeView,auto)')
    xbmc.executebuiltin('Skin.Reset(Enable.SlimList)')
    xbmc.executebuiltin('ActivateWindow(Videos,plugin://plugin.video.infinitybrowserqa/?kind=movies)')
    check('synthetic-movies',wait(lambda:xbmc.getInfoLabel('Container.Content')=='movies' and not xbmc.getCondVisibility('Container.IsUpdating')))
    xbmc.executebuiltin('Container.SetViewMode(50)',True)
    for theme in ('dark','light'):
        home.setProperty('Infinity.SystemTheme',theme)
        for row in (1,2):
            xbmc.executebuiltin('SetFocus(50,%d,absolute)'%row,True)
            check(theme+'-selected-'+str(row),wait(lambda:xbmc.getInfoLabel('Container(50).ListItem.Label').startswith('Media %02d'%row)))
            xbmc.sleep(600)
            # Total details extent includes art and metadata, not just synopsis.
            # Record the real condition; report a missing branch as NOT RUN.
            expected=98066 if xbmc.getCondVisibility('Control.IsVisible(98066)') else 50
            R.setdefault('observed_Up_branches',[]).append(dict(theme=theme,row=row,target=expected))
            for cid in (98070,98071,98072):
                focus(cid)
                xbmc.executebuiltin('Action(Up)',True)
                check(theme+'-Up-'+str(cid)+'-'+str(row),wait(lambda:xbmcgui.Window(10025).getFocusId()==expected))
                check('item-preserved',xbmc.getInfoLabel('Container(50).ListItem.Label').startswith('Media %02d'%row))
        xbmc.executebuiltin('SetFocus(50,1,absolute)',True)
        xbmc.executebuiltin('Action(Info)',True)
        check(theme+'-native-info',wait(lambda:xbmcgui.getCurrentWindowDialogId()==12003))
        focus(9012)
        home.clearProperty('Infinity.QA.TrailerCount')
        xbmc.executebuiltin('Action(Select)',True)
        check(theme+'-bridge-dispatch',wait(lambda:home.getProperty('Infinity.QA.TrailerCount')=='1'))
        xbmc.sleep(300)
        check(theme+'-no-extras-or-duplicate',xbmcgui.getCurrentWindowDialogId()==12003 and home.getProperty('Infinity.QA.TrailerCount')=='1')
        check('no-playback',not xbmc.getCondVisibility('Player.HasMedia'))
        focus(9011)
        xbmc.executebuiltin('Action(Select)',True)
        check(theme+'-Back-control-restores-browser',wait(lambda:xbmcgui.getCurrentWindowDialogId()==9999 and xbmcgui.getCurrentWindowId()==10025))
        check(theme+'-Back-selection',xbmc.getInfoLabel('Container(50).ListItem.Label').startswith('Media 01'))
    R['fallback_execution']='PASS' if any(x['target']==50 for x in R['observed_Up_branches']) else 'NOT_RUN_NO_ONE_PAGE_CASE'
    R['scrollbar_execution']='PASS' if any(x['target']==98066 for x in R['observed_Up_branches']) else 'NOT_RUN_NO_OVERFLOW_CASE'
    R['status']='PASS_CHANGED_CONTROL_DISPATCH_ONLY'
except Exception:
    R['status']='FAIL'; R['error']=traceback.format_exc()
finally:
    (OUT/'RESULT.json').write_text(json.dumps(R,indent=2)+'\n')
