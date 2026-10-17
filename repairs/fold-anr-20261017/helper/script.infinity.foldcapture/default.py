# SPDX-License-Identifier: GPL-2.0-or-later
"""User-started only. This add-on has no service or scheduled work."""
from pathlib import Path
import time

import xbmcaddon
import xbmcgui
import xbmcvfs

import capture


def main():
    addon = xbmcaddon.Addon()
    dialog = xbmcgui.Dialog()
    choice = dialog.select("Infinity Fold Freeze Capture", [
        "Arm capture for two hours", "Export current and previous capture", "Cancel"])
    if choice == 0:
        try:
            capture.arm_exact_library(capture.find_exact_native())
            dialog.ok("Capture armed for two hours",
                      "Use other apps, return to Infinity, dismiss the screensaver and reproduce the freeze. "
                      "If Android stops Infinity, reopen it once and export the capture from this helper. "
                      "Also keep the normal Android diagnostic ZIP from the same attempt.")
        except (OSError, RuntimeError, AttributeError, ValueError) as error:
            dialog.ok("Capture not armed", str(error))
    elif choice == 1:
        profile = Path(xbmcvfs.translatePath(addon.getAddonInfo("profile")))
        target = profile / ("Infinity-Fold-Lock-Capture-" + time.strftime("%Y%m%d-%H%M%S") + ".zip")
        versions = {}
        for addon_id in ("skin.infinity.diggz", "script.infinity.commandcenter", "script.infinity.rails"):
            try:
                versions[addon_id] = xbmcaddon.Addon(addon_id).getAddonInfo("version")
            except RuntimeError:
                versions[addon_id] = "unavailable"
        try:
            capture.collect(target, xbmcvfs.translatePath("special://temp/"), versions)
        except (OSError, RuntimeError, ValueError) as error:
            dialog.ok("Capture unavailable", str(error))
            return
        folder = dialog.browse(3, "Choose a folder for the capture", "files")
        if folder:
            destination = folder.rstrip("/\\") + "/" + target.name
            if xbmcvfs.copy(str(target), destination):
                dialog.ok("Capture exported", destination)
            else:
                dialog.ok("Export failed", "The capture remains saved at " + str(target))
        else:
            dialog.ok("Capture saved", str(target))


if __name__ == "__main__":
    main()
