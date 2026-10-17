"""Read-only presentation publisher; one stat per second, no per-poster disk I/O."""
import json
from pathlib import Path

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

from bridge_state import snapshot

PROPERTY = "Infinity.ResumeHub.PresentationSnapshot"


def status(home, value):
    if home.getProperty("Infinity.WatchedBridge.Status") != value:
        home.setProperty("Infinity.WatchedBridge.Status", value)


def run():
    monitor = xbmc.Monitor()
    home = xbmcgui.Window(10000)
    signature = None
    while not monitor.abortRequested():
        if xbmc.getInfoLabel("Window(Home).Property(Infinity.ResumeHub.BridgeVersion)") == "1":
            try:
                profile = Path(xbmcvfs.translatePath("special://profile/"))
                addon = xbmcaddon.Addon("script.infinity.commandcenter")
                file = Path(xbmcvfs.translatePath(addon.getAddonInfo("profile"))) / "continue-watching.json"
                stat = file.stat()
                current = (str(profile), stat.st_mtime_ns, stat.st_size, stat.st_ino)
                if current != signature or not home.getProperty(PROPERTY):
                    if stat.st_size > 8 * 1024 * 1024:
                        raise ValueError("Progress file exceeds presentation read limit")
                    data = json.loads(file.read_text(encoding="utf-8"))
                    value = snapshot(data, profile)
                    if home.getProperty(PROPERTY) != value:
                        home.setProperty(PROPERTY, value)
                        xbmc.executebuiltin("InfinityResumeHubUpdate")
                    signature = current
                    status(home, "Local watched badges ready")
            except (OSError, ValueError, RuntimeError, AttributeError):
                # Withhold stale derived state; never repair or rewrite the source.
                value = snapshot({"schema": 2}, xbmcvfs.translatePath("special://profile/"))
                if home.getProperty(PROPERTY) != value:
                    home.setProperty(PROPERTY, value)
                    xbmc.executebuiltin("InfinityResumeHubUpdate")
                signature = None
                status(home, "Local watched state unavailable; existing provider badges remain")
        else:
            status(home, "Existing provider badges; local badge bridge unavailable")
        if monitor.waitForAbort(1.0):
            break


if __name__ == "__main__":
    run()
