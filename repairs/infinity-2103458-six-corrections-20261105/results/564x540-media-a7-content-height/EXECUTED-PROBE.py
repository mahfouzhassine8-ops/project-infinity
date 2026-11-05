"""Bounded common browser/Info rendering; no play/stop or real provider calls."""
import json,time,traceback
from pathlib import Path
import xbmc,xbmcgui
from candidate_media_view import publish_browser_genres
BASE=Path(QA_PATH);C=json.loads((BASE/'config.json').read_text());OUT=Path(C['output'])
R={'platform':'upstream Linux Kodi; explicit responsive projection','Android':'NOT_RUN','physical_Fold':'NOT_RUN','source_hashes':C['media_sources'],'checks':[],'observations':[]}
def wait(p,seconds=16):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  if p():return True
  xbmc.sleep(100)
 return False
def check(name,ok):
 R['checks'].append({'name':name,'passed':bool(ok)})
 if not ok:raise RuntimeError(name)
def shot(name):
 xbmc.sleep(500);xbmc.executebuiltin('TakeScreenshot(%s)'%(OUT/(name+'.png')))
 check(name+'-capture',wait(lambda:(OUT/(name+'.png')).exists(),5))
try:
 check('skin-ready',wait(lambda:xbmc.getInfoLabel('Skin.CurrentTheme')!='' and xbmcgui.getCurrentWindowId()!=10099,35))
 for _ in range(3):
  if xbmcgui.getCurrentWindowDialogId()==9999:break
  check('known-fixture-notice',xbmcgui.getCurrentWindowDialogId()==10100 and xbmc.getInfoLabel('Control.GetLabel(1)')=='Disabled add-ons')
  xbmc.executebuiltin('Action(Select)');xbmc.sleep(700)
 xbmc.sleep(1500);home=xbmcgui.Window(10000)
 home.setProperty('Infinity.OptionalMotionAllowed','false')
 xbmc.executebuiltin('Skin.SetString(Infinity.HomeView,auto)');xbmc.executebuiltin('Skin.Reset(Enable.SlimList)')
 for kind in ('movies','tvshows','seasons','episodes'):
  xbmc.executebuiltin('ActivateWindow(Videos,plugin://plugin.video.infinitybrowserqa/?kind='+kind+')')
  check(kind+'-directory',wait(lambda:xbmc.getInfoLabel('Container.Content')==kind and not xbmc.getCondVisibility('Container.IsUpdating')))
  xbmc.executebuiltin('Container.SetViewMode(50)');xbmc.executebuiltin('SetFocus(50,1,absolute)')
  check(kind+'-selection',wait(lambda:xbmc.getInfoLabel('Container(50).ListItem.Label').startswith('Media 01')))
  publish_browser_genres(xbmc,xbmcgui)
  R['observations'].append({'kind':kind,'DBType':xbmc.getInfoLabel('Container(50).ListItem.DBType'),'plot_present':bool(xbmc.getInfoLabel('Container(50).ListItem.Plot')),'thumb_present':bool(xbmc.getInfoLabel('Container(50).ListItem.Art(thumb)')),'poster_present':bool(xbmc.getInfoLabel('Container(50).ListItem.Art(poster)')),'season_poster_present':bool(xbmc.getInfoLabel('Container(50).ListItem.Art(season.poster)'))})
  for theme in ('dark','light'):
   home.setProperty('Infinity.SystemTheme',theme);shot(kind+'-list-'+theme)
  R['known_behavior_failures']=['action-Up points to nonfocusable textbox98064','Info Back10/native GetThumb conflict; proposal not applied']
  if xbmc.getCondVisibility('Container(98060).HasNext'):
   xbmc.executebuiltin('SetFocus(98066)')
   check(kind+'-existing-scrollbar-focus',wait(lambda:xbmcgui.Window(10025).getFocusId()==98066))
   xbmc.executebuiltin('Action(Down)')
   check(kind+'-existing-scrollbar-moves',wait(lambda:xbmc.getCondVisibility('Container(98060).HasPrevious')))
   for step in range(20):
    if xbmcgui.Window(10025).getFocusId()!=98066:break
    xbmc.executebuiltin('Action(Down)');xbmc.sleep(160)
   R['observations'].append({'kind':kind,'endpoint_HasNext':xbmc.getCondVisibility('Container(98060).HasNext'),'endpoint_focus':xbmcgui.Window(10025).getFocusId(),'endpoint_visual_check':'PENDING_SCREENSHOT_REVIEW'})
   check(kind+'-scroll-preserves-item',xbmc.getInfoLabel('Container(50).ListItem.Label').startswith('Media 01'))
   shot(kind+'-details-scrollbar-light')
  else:R['observations'].append({'kind':kind,'detail_scrolling':'not_needed'})
  xbmc.executebuiltin('SetFocus(50,1,absolute)')
  if kind in ('movies','tvshows','episodes'):
   xbmc.executebuiltin('Action(Info)');check(kind+'-native-info',wait(lambda:xbmcgui.getCurrentWindowDialogId()==12003))
   for theme in ('dark','light'):
    home.setProperty('Infinity.SystemTheme',theme);shot(kind+'-info-'+theme)
   xbmc.executebuiltin('SetFocus(5)');xbmc.executebuiltin('Action(Select)')
   check(kind+'-cast-visible',wait(lambda:xbmc.getCondVisibility('Control.IsVisible(50)')))
   R['observations'].append({'kind':kind,'cast_count':xbmc.getInfoLabel('Container(50).NumItems')})
   shot(kind+'-cast-light')
   xbmc.executebuiltin('Action(Back)');check(kind+'-native-back',wait(lambda:xbmcgui.getCurrentWindowDialogId()==9999 and xbmcgui.getCurrentWindowId()==10025))
   check(kind+'-selection-restored',xbmc.getInfoLabel('Container(50).ListItem.Label').startswith('Media 01'))
 R['status']='PASS_SELECTED_SYNTHETIC_CONTENT_RENDER_AND_NATIVE_BACK'
 R['visual_acceptance']='PENDING_IMAGE_REVIEW_NOT_PHYSICAL_ACCEPTANCE'
except Exception:
 R['status']='FAIL';R['error']=traceback.format_exc()
finally:(OUT/'RESULT.json').write_text(json.dumps(R,indent=2)+'\n')
