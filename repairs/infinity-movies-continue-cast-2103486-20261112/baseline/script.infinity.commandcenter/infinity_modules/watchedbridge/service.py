"""Read-only presentation publisher; one stat per second, no per-poster disk I/O."""
import json
from pathlib import Path

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

from .bridge_state import snapshot
from . import provider_contracts as contracts

PROPERTY = "Infinity.ResumeHub.PresentationSnapshot"


def status(home, value):
    if home.getProperty("Infinity.WatchedBridge.Status") != value:
        home.setProperty("Infinity.WatchedBridge.Status", value)






class Publisher:
    def __init__(self):
        self.home = xbmcgui.Window(10000)
        self.signature, self.verified = None, {}
        self.next_check = self.next_publish = self.next_tick = 0.0

    def tick(self, now):
        if now < self.next_tick:
            return
        self.next_tick = now + 1.0
        if xbmc.getInfoLabel('Window(Home).Property(Infinity.ResumeHub.BridgeVersion)') == '1':
            try:
                import time
                if time.monotonic() >= self.next_check:
                    current_contracts = {}
                    for addon_id in contracts.CATALOG:
                        try:
                            addon_root = xbmcvfs.translatePath(xbmcaddon.Addon(addon_id).getAddonInfo('path'))
                            proof = contracts.verify(addon_id, addon_root)
                            if proof:
                                current_contracts[addon_id] = proof
                        except RuntimeError:
                            pass
                    if current_contracts != self.verified:
                        self.signature = None
                    self.verified = current_contracts
                    self.next_check = time.monotonic() + 30.0
                profile = Path(xbmcvfs.translatePath('special://profile/'))
                addon = xbmcaddon.Addon('script.infinity.commandcenter')
                file = Path(xbmcvfs.translatePath(addon.getAddonInfo('profile'))) / 'continue-watching.json'
                stat = file.stat()
                current = (str(profile), stat.st_mtime_ns, stat.st_size, stat.st_ino)
                refresh_due = time.monotonic() >= self.next_publish
                if current != self.signature or not self.home.getProperty(PROPERTY) or refresh_due:
                    if stat.st_size > 8 * 1024 * 1024:
                        raise ValueError('Progress file exceeds presentation read limit')
                    data = json.loads(file.read_text(encoding='utf-8'))
                    value = snapshot(data, profile, self.verified)
                    changed = self.home.getProperty(PROPERTY) != value
                    if changed:
                        self.home.setProperty(PROPERTY, value)
                    if changed or refresh_due:
                        xbmc.executebuiltin('InfinityResumeHubUpdate()')
                        self.next_publish = time.monotonic() + 30.0
                    self.signature = current
                    names = ['Umbrella' if name.endswith('umbrella') else 'POV' for name in sorted(self.verified)]
                    status(self.home, 'Local badges ready; episode adapters: ' + ', '.join(names) if names else 'Local movie badges ready; no verified episode add-on adapter')
            except (OSError, ValueError, RuntimeError, AttributeError):
                value = snapshot({'schema': 2}, xbmcvfs.translatePath('special://profile/'))
                if self.home.getProperty(PROPERTY) != value:
                    self.home.setProperty(PROPERTY, value)
                    xbmc.executebuiltin('InfinityResumeHubUpdate()')
                self.signature = None
                status(self.home, 'Local watched state unavailable; existing provider badges remain')
        else:
            status(self.home, 'Existing provider badges; local badge bridge unavailable')
