import xbmc
import xbmcgui
from recovery import OTAKU, RecoveryError, disabled, enable


def restore(addon_id):
    result = enable(xbmc.executeJSONRPC, addon_id)
    state = result["state"]
    if state == "not-installed":
        xbmcgui.Dialog().ok("Installation not found", "Kodi does not list this add-on as installed. Open the native Add-on Manager to check its installation and repository.")
    elif state == "already-enabled":
        xbmcgui.Dialog().ok("Already enabled", result["name"] + " is enabled. If a custom rail hides it, open Infinity Add-on Rails to restore its card. Other grids may use their own filters.")
    else:
        xbmc.executebuiltin("Container.Refresh")
        xbmcgui.Dialog().ok("Add-on enabled", result["name"] + " is enabled through Kodi. Its existing settings and data were not reset. Return to Video Sources; use Infinity Add-on Rails if a custom card is hidden.")


def main():
    dialog = xbmcgui.Dialog()
    choice = dialog.select("Infinity Add-on Recovery", ["Restore Otaku", "Disabled add-ons", "Open native Add-on Manager", "Open Infinity Add-on Rails"])
    try:
        if choice == 0:
            restore(OTAKU)
        elif choice == 1:
            rows = disabled(xbmc.executeJSONRPC)
            if not rows:
                dialog.ok("No disabled add-ons", "Kodi reports no disabled installations. Missing cards may be hidden or filtered; use the relevant rail or the native Add-on Manager.")
                return
            selected = dialog.select("Enable an installed add-on", [item["name"] + " · " + item["version"] for item in rows])
            if 0 <= selected < len(rows):
                restore(rows[selected]["addonid"])
        elif choice == 2:
            xbmc.executebuiltin("ActivateWindow(AddonBrowser,addons://user/,return)")
        elif choice == 3:
            if xbmc.getCondVisibility("System.HasAddon(script.infinity.rails)"):
                xbmc.executebuiltin("RunScript(script.infinity.rails)")
            else:
                dialog.ok("Rails unavailable", "Open the native Add-on Manager to check Infinity Add-on Rails.")
    except RecoveryError as error:
        dialog.ok("Recovery not completed", str(error))


if __name__ == "__main__":
    main()
