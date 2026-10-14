"""Executed INSIDE real Kodi, in a disposable CI profile; never shipped."""
import json
from pathlib import Path
import sys
import time
import traceback
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

out=Path(xbmcvfs.translatePath('special://profile/rail-smoke-result.json'))
checks={}

def wait(predicate, seconds=20):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if predicate():return
        xbmc.sleep(100)
    raise AssertionError('Timed out waiting for actual Kodi state')

def enable(aid):
    reply=json.loads(xbmc.executeJSONRPC(json.dumps({'jsonrpc':'2.0','id':1,
      'method':'Addons.SetAddonEnabled','params':{'addonid':aid,'enabled':True}})))
    assert 'error' not in reply,reply

try:
    xbmc.executebuiltin('UpdateLocalAddons')
    xbmc.sleep(2000)
    for aid in ['script.infinity.rails','plugin.video.infinityrailfixture','skin.infinity.diggz']:enable(aid)
    addon=xbmcaddon.Addon('script.infinity.rails')
    sys.path.insert(0,str(Path(xbmcvfs.translatePath(addon.getAddonInfo('path')))/'resources'))
    from lib.store import Store
    from lib import runtime
    profile=Path(xbmcvfs.translatePath(addon.getAddonInfo('profile')))
    Store(profile).add('plugin.video.infinityrailfixture',['tvshows'],{'movies':[],'tvshows':[]})
    # Close only disposable first-run welcome dialogs. No skin switch is needed:
    # setup installed the fixture Home into this runner's stock Estuary skin.
    checks['startup_dialogs']=[]
    for attempt in range(6):
        dialog=xbmcgui.getCurrentWindowDialogId()
        if dialog==9999:break
        labels={}
        for cid in [1,2,3,9,10,11]:
            labels[str(cid)]=xbmc.getInfoLabel('Control.GetLabel('+str(cid)+')')
        checks['startup_dialogs'].append({'id':dialog,'labels':labels})
        assert dialog==10100,checks['startup_dialogs']
        xbmc.executebuiltin('SendClick(10100,10)')
        xbmc.sleep(500)
    xbmc.executebuiltin('ActivateWindow(Home)')
    xbmc.sleep(500)
    wait(lambda:xbmcgui.getCurrentWindowDialogId()==9999)
    wait(lambda:xbmc.getInfoLabel('Container(9000).ListItem.Property(section)')=='tvshows')
    command='RunScript(script.infinity.rails,options,tvshows,c:plugin.video.infinityrailfixture,plugin.video.infinityrailfixture)'
    for dismiss in ['Back','Select']:
        xbmc.executebuiltin(command)
        wait(lambda:xbmcgui.getCurrentWindowDialogId()==12000)
        labels=[]
        for cid in [3,6]:
            count=xbmc.getInfoLabel('Container('+str(cid)+').NumItems')
            if count.isdigit() and int(count)>0:
                labels=[xbmc.getInfoLabel('Container('+str(cid)+').ListItemAbsolute('+str(i)+').Label') for i in range(int(count))]
                break
        assert labels[:3]==['Open Add-on','Move / Reorder','Remove from Rail'],labels
        checks['actual_dialog_populated']=labels
        xbmc.sleep(400)
        xbmc.executebuiltin('TakeScreenshot(special://profile/rail-options.png)')
        xbmc.executebuiltin('Action('+dismiss+')')
        wait(lambda:xbmcgui.getCurrentWindowDialogId()!=12000)
        if dismiss=='Back':
            wait(lambda:xbmcgui.Window(10000).getProperty('Infinity.Rails.OptionsActive')=='')
            checks['back_dismisses_and_clears_guard']=True
        else:
            wait(lambda:Path(xbmcvfs.translatePath('special://profile/rail-fixture-launched.txt')).exists())
            checks['open_action_runs_real_plugin']=True
    # The plugin directory emitted by Rails itself retains the launch URI and opt-in.
    xbmc.executebuiltin('ActivateWindow(Home)')
    xbmc.sleep(300)
    checks['kodi_version']=xbmc.getInfoLabel('System.BuildVersion')
    checks['passed']=True
except Exception:
    checks.update(passed=False,error=traceback.format_exc())
finally:
    checks.update(physical_fold_accepted=False,native_android_hold_injected=False,
                  scope='Real Kodi scripting, context callback, populated stock DialogSelect, Back and plugin launch; fixture Home skin')
    out.write_text(json.dumps(checks,indent=2)+'\n')
    xbmc.executebuiltin('Quit')
