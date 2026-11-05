"""Finite native Info invocation on synthetic content; no playback/shutdown."""
import json,time,traceback
from pathlib import Path
import xbmc,xbmcgui
BASE=Path(QA_PATH)
C=json.loads((BASE/'config.json').read_text());OUT=Path(C['output'])
R={'platform':'upstream Linux Kodi with explicit responsive projection','Android':'NOT_RUN','Fold':'NOT_RUN','info_sha256':C['info_sha256'],'checks':[]}
def wait(p,seconds=20):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if p():return True
        xbmc.sleep(100)
    return False
def check(name,value):
    R['checks'].append({'name':name,'passed':bool(value)})
    if not value:raise RuntimeError(name)
def shot(name):
    xbmc.sleep(500);xbmc.executebuiltin('TakeScreenshot(%s)'%(OUT/(name+'.png')))
    check(name+'-capture',wait(lambda:(OUT/(name+'.png')).exists(),5))
try:
    check('skin-ready',wait(lambda:xbmc.getInfoLabel('Skin.CurrentTheme')!='' and xbmcgui.getCurrentWindowId()!=10099,35))
    for notice in range(3):
        if xbmcgui.getCurrentWindowDialogId()==9999:break
        heading=xbmc.getInfoLabel('Control.GetLabel(1)')
        R.setdefault('fixture_startup_dialogs',[]).append({'id':xbmcgui.getCurrentWindowDialogId(),'heading':heading})
        if xbmcgui.getCurrentWindowDialogId()!=10100 or heading!='Disabled add-ons':
            shot('unexpected-fixture-notice');raise RuntimeError('Unknown fixture notice; not dismissed')
        xbmc.executebuiltin('Action(Select)');xbmc.sleep(700)
    check('fixture-modal-dismissed',xbmcgui.getCurrentWindowDialogId()==9999)
    xbmc.sleep(1500)
    home=xbmcgui.Window(10000);home.setProperty('Infinity.SystemTheme','dark')
    home.setProperty('Infinity.OptionalMotionAllowed','false')
    xbmc.executebuiltin('ActivateWindow(Videos,plugin://plugin.video.infinitybrowserqa/?kind=movies)')
    check('synthetic-directory',wait(lambda:xbmc.getInfoLabel('Container.Content')=='movies' and not xbmc.getCondVisibility('Container.IsUpdating')))
    xbmc.executebuiltin('Container.SetViewMode(50)');xbmc.executebuiltin('SetFocus(50,1,absolute)')
    check('selected-movie',wait(lambda:xbmc.getInfoLabel('Container(50).ListItem.Label').startswith('Media 01')))
    xbmc.executebuiltin('Action(Info)')
    check('native-info-open',wait(lambda:xbmcgui.getCurrentWindowDialogId()==12003))
    shot('info-dark')
    home.setProperty('Infinity.SystemTheme','light');shot('info-light')
    # Button ID10 collision is independently retained as FAIL. Test native Back separately.
    R['skin_back_button']='FAIL_PREEXISTING_ID10_GET_THUMB_COLLISION_NOT_REPAIRED'
    xbmc.executebuiltin('Action(Back)')
    check('back-restores-browser',wait(lambda:xbmcgui.getCurrentWindowDialogId()==9999 and xbmcgui.getCurrentWindowId()==10025))
    check('same-selected-movie',xbmc.getInfoLabel('Container(50).ListItem.Label').startswith('Media 01'))
    R['status']='PASS_INFO_OPEN_THEME_AND_NATIVE_BACK_ONLY'
    R['overall_Info_acceptance']='NOT_ACCEPTED_BACK_BUTTON_FAILURE_AND_REMAINING_VISUAL_POLISH'
except Exception:
    R['status']='FAIL';R['error']=traceback.format_exc()
finally:(OUT/'RESULT.json').write_text(json.dumps(R,indent=2)+'\n')
