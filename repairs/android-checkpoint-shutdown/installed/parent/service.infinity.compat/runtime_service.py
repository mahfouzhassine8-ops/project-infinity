# SPDX-License-Identifier: GPL-2.0-or-later
from __future__ import annotations
from pathlib import Path
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

from compat_runtime import publish_runtime_status
import layout_service
import theme_contract

TAG='[InfinityCompat] '

class RuntimeMonitor(xbmc.Monitor):
    def __init__(self, addon, profile):
        super().__init__()
        self.addon=addon
        self.profile=profile

    def publish_all(self, force=False):
        publish_runtime_status()
        try:
            layout_service.publish(force=force)
            xbmcgui.Window(10000).setProperty('Infinity.LayoutServiceReady','true')
        except Exception as e:
            xbmcgui.Window(10000).setProperty('Infinity.LayoutServiceReady','false')
            xbmc.log(TAG+'layout publish failed: '+type(e).__name__,xbmc.LOGWARNING)
        try:
            theme_contract.publish(self.addon,self.profile,force=force)
            xbmcgui.Window(10000).setProperty('Infinity.ThemeServiceReady','true')
        except Exception as e:
            xbmcgui.Window(10000).setProperty('Infinity.ThemeServiceReady','false')
            xbmc.log(TAG+'theme publish failed: '+type(e).__name__,xbmc.LOGWARNING)

    def onSettingsChanged(self):
        self.publish_all(force=True)
    def onNotification(self,sender,method,data):
        self.publish_all(force=False)
    def onScreensaverDeactivated(self):
        self.publish_all(force=True)
    def onDPMSDeactivated(self):
        self.publish_all(force=True)

def main():
    addon=xbmcaddon.Addon()
    profile=Path(xbmcvfs.translatePath(addon.getAddonInfo('profile')))
    profile.mkdir(parents=True,exist_ok=True)
    mon=RuntimeMonitor(addon,profile)
    xbmc.log(TAG+'dual-skin clean-core runtime coordinator 0.8.1 started',xbmc.LOGINFO)
    mon.publish_all(force=True)
    while not mon.abortRequested():
        if mon.waitForAbort(2.0):
            break
        mon.publish_all(force=False)

if __name__=='__main__':
    main()
