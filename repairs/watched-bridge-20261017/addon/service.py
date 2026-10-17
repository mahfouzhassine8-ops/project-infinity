"""Read-only presentation publisher; one stat per second, no per-poster disk I/O."""
import json
from pathlib import Path

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

from bridge_state import snapshot
import provider_contracts as contracts

PROPERTY = "Infinity.ResumeHub.PresentationSnapshot"


def status(home, value):
    if home.getProperty("Infinity.WatchedBridge.Status") != value:
        home.setProperty("Infinity.WatchedBridge.Status", value)


def run():
    monitor = xbmc.Monitor()
    home = xbmcgui.Window(10000)
    signature = None
    verified = {}
    next_check = 0
    while not monitor.abortRequested():
        if xbmc.getInfoLabel("Window(Home).Property(Infinity.ResumeHub.BridgeVersion)") == "1":
            try:
                import time
                if time.monotonic() >= next_check:
                    current_contracts = {}
                    for addon_id in contracts.CATALOG:
                        try:
                            addon_root = xbmcvfs.translatePath(xbmcaddon.Addon(addon_id).getAddonInfo("path"))
                            proof = contracts.verify(addon_id, addon_root)
                            if proof:
                                current_contracts[addon_id] = proof
                        except RuntimeError:
                            pass
                    if current_contracts != verified:
                        signature = None
                    verified = current_contracts
                    next_check = time.monotonic() + 30.0
                profile = Path(xbmcvfs.translatePath("special://profile/"))
                addon = xbmcaddon.Addon("script.infinity.commandcenter")
                file = Path(xbmcvfs.translatePath(addon.getAddonInfo("profile"))) / "continue-watching.json"
                stat = file.stat()
                current = (str(profile), stat.st_mtime_ns, stat.st_size, stat.st_ino)
                if current != signature or not home.getProperty(PROPERTY):
                    if stat.st_size > 8 * 1024 * 1024:
                        raise ValueError("Progress file exceeds presentation read limit")
                    data = json.loads(file.read_text(encoding="utf-8"))
                    value = snapshot(data, profile, verified)
                    if home.getProperty(PROPERTY) != value:
                        home.setProperty(PROPERTY, value)
                        xbmc.executebuiltin("InfinityResumeHubUpdate()")
                    signature = current
                    names = ["Umbrella" if name.endswith("umbrella") else "POV" for name in sorted(verified)]
                    status(home, "Local badges ready; episode adapters: " + ", ".join(names) if names else
                           "Local movie badges ready; no verified episode add-on adapter")
            except (OSError, ValueError, RuntimeError, AttributeError):
                # Withhold stale derived state; never repair or rewrite the source.
                value = snapshot({"schema": 2}, xbmcvfs.translatePath("special://profile/"))
                if home.getProperty(PROPERTY) != value:
                    home.setProperty(PROPERTY, value)
                    xbmc.executebuiltin("InfinityResumeHubUpdate()")
                signature = None
                status(home, "Local watched state unavailable; existing provider badges remain")
        else:
            status(home, "Existing provider badges; local badge bridge unavailable")
        if monitor.waitForAbort(1.0):
            break


if __name__ == "__main__":
    run()
