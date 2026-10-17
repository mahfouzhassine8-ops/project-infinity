import xbmc
import xbmcgui


def main():
    dialog = xbmcgui.Dialog()
    status = xbmcgui.Window(10000).getProperty("Infinity.WatchedBridge.Status") or "Waiting for local watched state"
    choice = dialog.select("Infinity Watched and Lists", ["Open Resume Hub", "Compatibility and status"])
    if choice == 0:
        xbmc.executebuiltin("ActivateWindow(Videos,plugin://script.infinity.commandcenter/?action=resume,return)")
    elif choice == 1:
        dialog.ok("Watched integration", status + ". Use Infinity: Watched and Lists in a movie or episode context menu. Reliable metadata is required. Anime absolute numbering is not guessed, and provider-native watched actions do not synchronize unless a supported callback is available.")


if __name__ == "__main__":
    main()
