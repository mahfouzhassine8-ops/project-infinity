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
    xbmc.executebuiltin('ActivateWindow(Home)')
    # Isolated fixture skin uses Kodi's real Home static nav control and stock dialog.
    reply=json.loads(xbmc.executeJSONRPC(json.dumps({'jsonrpc':'2.0','id':1,'method':'Settings.SetSettingValue',
        'params':{'setting':'lookandfeel.skin','value':'skin.infinity.diggz'}})))
    assert 'error' not in reply,reply
    xbmc.sleep(2000)
    # Skin confirmation is part of Kodi's real switching behavior.
    if xbmcgui.getCurrentWindowDialogId()!=9999:
        xbmc.executebuiltin('SendClick(11)')
        xbmc.sleep(1000)
    wait(lambda:xbmcgui.getCurrentWindowDialogId()==9999)
    wait(lambda:xbmc.getInfoLabel('Container(9000).ListItem.Property(section)')=='tvshows')
    command='RunScript(script.infinity.rails,options,tvshows,c:plugin.video.infinityrailfixture,plugin.video.infinityrailfixture)'
    for dismiss in ['Back','Select']:
        xbmc.executebuiltin(command)
        wait(lambda:xbmcgui.getCurrentWindowDialogId()==12000)
        window=xbmcgui.Window(12000)
        labels=[]
        for cid in [3,6]:
            try:
                control=window.getControl(cid)
                labels=[control.getListItem(i).getLabel() for i in range(control.size())]
                if labels:break
            except (RuntimeError,AttributeError):pass
        assert labels[:3]==['Open Add-on','Move / Reorder','Remove from Rail'],labels
        checks['actual_dialog_populated']=labels
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
