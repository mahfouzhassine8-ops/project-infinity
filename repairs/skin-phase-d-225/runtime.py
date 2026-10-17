"""Real Kodi skin screenshots, bounded GUI loops and control geometry receipts."""
import json,sys,time,traceback,threading
from pathlib import Path
import xbmc,xbmcgui,xbmcvfs
profile=Path(xbmcvfs.translatePath('special://profile/'));config=json.loads((profile/'phase-d-config.json').read_text())
output=profile/'phase-d-results';output.mkdir(exist_ok=True)
report=dict(config=config,passed=False,physical_fold=False,renderer='stock Kodi with exact production unified XML; manifest projects the existing Android logical viewport; companion services unavailable',screens=[])
if sys.argv[-1]=='bootstrap':
 response=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method='Addons.SetAddonEnabled',params=dict(addonid='skin.infinity.phased',enabled=True)))))
 (profile/'phase-d-bootstrap.json').write_text(json.dumps(response));xbmc.executebuiltin('Quit()');raise SystemExit

def capture(name,ids=()):
 xbmc.sleep(500)
 w=xbmcgui.getCurrentWindowId();d=xbmcgui.getCurrentWindowDialogId();window=xbmcgui.Window(d if d not in (0,9999) else w)
 result=dict(name=name,window=w,dialog=d,focus=window.getFocusId(),controls=[])
 for id in ids:
  try:
   c=window.getControl(id);result['controls'].append(dict(id=id,position=c.getPosition(),width=c.getWidth(),height=c.getHeight()))
  except Exception as ex:result['controls'].append(dict(id=id,error=str(ex)))
 path=output/(name+'.png');xbmc.executebuiltin(f'TakeScreenshot({path},sync)',True)
 result['screenshot']=path.name;result['screenshot_present']=path.exists();report['screens'].append(result)

def close():
 xbmc.executebuiltin('Dialog.Close(all,true)',True);xbmc.executebuiltin('ActivateWindow(home)',True);xbmc.sleep(150)
try:
 assert xbmc.getSkinDir()==config.get('skin_id','skin.infinity.phased'),xbmc.getSkinDir()
 home=xbmcgui.Window(10000)
 for key,value in {'Infinity.OptionalMotionAllowed':'false','Infinity.MotionModeEffective':'off','Infinity.BootStage':'ready','Infinity.SystemTheme':'dark','Infinity.NativeSystemTheme':'dark','Infinity.BrowseTitle':'All Add-ons','Infinity.BrowseSubtitle':'Installed and available add-ons','Infinity.HealthOrb.State':'ready'}.items():home.setProperty(key,value)
 xbmc.executebuiltin('Skin.SetString(Infinity.VisualMode,normal)',True)
 xbmc.executebuiltin('Skin.SetString(Infinity.HomeView,normal)',True)
 for theme in ('light','dark','OLED'):
  home.setProperty('Infinity.SystemTheme',theme);home.setProperty('Infinity.NativeSystemTheme',theme)
  for screen,action,ids in [
   ('home','home',(9000,)),('browse','1193',(10,12,50)),('settings','settings',(9000,)),
   ('settings-category','playersettings',(3,5,60,20)),('command','1194',(1194888,1194101)),
   ('health','1188',(1188000,1188199)),('system','1191',(1191888,1191199)),
   ('navigation','1198',(1198899,1198999)),('audio','1195',(5101,5102,5103,5199)),
   ('speed','1196',(5201,5202,5203,5299)),('display','1197',(5390,5301,263)),
   ('palette','1190',(119000,119001,119002)),('addons','addonbrowser',(50,9096))]:
   # A modal ActivateWindow with wait=True blocks this test script until it closes.
   # Queue the normal GUI action so the harness can inspect and dismiss the dialog.
   close();xbmc.executebuiltin('ActivateWindow('+action+')');capture(theme.lower()+'-'+screen,ids)
   if screen=='settings-category':assert xbmcgui.getCurrentWindowId()!=10000,'PlayerSettings route did not open'
   (output/'progress.json').write_text(json.dumps(report,indent=2))
  close()
  worker=threading.Thread(target=lambda:xbmcgui.Dialog().select('Choose Your Experience / Resume Hub',['Infinity Home','Cobra','Resume Hub','Watchlist','Collection']))
  worker.start();xbmc.sleep(350);capture(theme.lower()+'-select',(3,));xbmc.executebuiltin('Action(Back)',True);worker.join(3)
  assert not worker.is_alive(),'Select dialog retained a test worker'
 # Repeated real custom dialog lifecycle with focus/Back: no service or install actions.
 cycles=[]
 for i in range(12):
  for id,control in [(1195,5101),(1196,5202),(1194,1194101),(1188,1188101),(1198,1198101)]:
   close();xbmc.executebuiltin('ActivateWindow('+str(id)+')');xbmc.sleep(350)
   d=xbmcgui.getCurrentWindowDialogId();assert d==id+10000,(id,d)
   xbmc.executebuiltin('SetFocus('+str(control)+')',True);xbmc.executebuiltin('Action(Back)',True);xbmc.sleep(75)
   after=xbmcgui.getCurrentWindowDialogId();assert after in (0,9999),(id,after)
   cycles.append(dict(window=id,opened=d,closed=after))
 report.update(passed=True,cycles=cycles,kodi_version=xbmc.getInfoLabel('System.BuildVersion'))
except Exception:report['failure']=traceback.format_exc()
finally:
 (output/'result.json').write_text(json.dumps(report,indent=2)+'\n')
 if not config.get('android'):xbmc.executebuiltin('Quit()')
