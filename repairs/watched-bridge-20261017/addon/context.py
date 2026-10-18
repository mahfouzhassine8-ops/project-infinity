"""Explicit local menu actions; native/provider context entries remain intact."""
from pathlib import Path
import sys
from urllib.parse import urlsplit

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

import controller
from bridge_state import identity, lookup, records
import provider_contracts as contracts

FOLDER_PROVIDERS = frozenset(("plugin.video.umbrella", "plugin.video.pov", "plugin.video.otaku", "plugin.video.watchnixtoons2"))


class TitleView:
    def __init__(self, item):
        self.item = item
    def isFolder(self):
        return False
    def __getattr__(self, name):
        return getattr(self.item, name)


def selected(modules, item, verify_provider=None):
    if item is None:
        return None
    candidate = item
    if item.isFolder():
        # Known provider title folders may resolve into source choices. Keep
        # tvshow/season/navigation rows excluded by the controller's typed ingress.
        if urlsplit(item.getPath()).netloc not in FOLDER_PROVIDERS:
            return None
        candidate = TitleView(item)
    entry = modules["context"].selected_entry(candidate)
    if entry and entry.get("media") == "tv":
        addon_id = contracts.provider(entry)
        if addon_id:
            if verify_provider is None:
                def verify_provider(name):
                    try:
                        addon = xbmcaddon.Addon(name)
                        return contracts.verify(name, xbmcvfs.translatePath(addon.getAddonInfo("path")))
                    except RuntimeError:
                        return None
            proof = verify_provider(addon_id)
            if not contracts.reviewed(addon_id, proof):
                return None
            entry[contracts.ENTRY_PROOF] = proof
            # These producers put series IDs in generic episode fields. A
            # coincident native episode ID cannot authorize library mutation.
            entry["dbid"] = -1
        if not contracts.canonical(entry, identity(entry), entry.get(contracts.ENTRY_PROOF)):
            return None
    return entry


def menu_intent(data, key, local_state, displayed_watched):
    """Capture the exact intent shown by the existing provider context menu.

    This is a read-only snapshot; the controller checks relevant state again
    inside the original Command Center writer lease before any mutation.
    """
    return dict(key=key, local_watched=local_state,
                displayed_watched=bool(displayed_watched),
                watchlist=key in data["watchlist"],
                collection=key in data["collection"])


def main():
    dialog = xbmcgui.Dialog()
    try:
        addon = xbmcaddon.Addon("script.infinity.commandcenter")
        modules = controller.load(xbmcvfs.translatePath(addon.getAddonInfo("path")))
        entry = selected(modules, getattr(sys, "listitem", None))
        if not entry:
            dialog.ok("Metadata unavailable", "This row lacks a verified movie or episode identity, or this add-on's episode numbering is not yet supported. No watched or list state was changed.")
            return
        profile = Path(xbmcvfs.translatePath(addon.getAddonInfo("profile")))
        hub = modules["resume_hub"]
        data = hub.load_view(profile)
        key = hub.compatible_key(data, entry)
        local_state = lookup(records(data), contracts.canonical(entry, identity(entry), entry.get(contracts.ENTRY_PROOF)))
        tag = getattr(sys, "listitem").getVideoInfoTag()
        native_watched = getattr(tag, "getPlayCount", lambda: 0)() > 0
        watched = local_state == "true" or (native_watched and local_state != "false")
        intent = menu_intent(data, key, local_state, watched)
        rows = [("Mark Unwatched" if watched else "Mark Watched", "mark-unwatched" if watched else "mark-watched"),
                ("Remove from Watchlist" if key in data["watchlist"] else "Add to Watchlist", "toggle-watchlist"),
                ("Remove from Collection" if key in data["collection"] else "Add to Collection", "toggle-collection"),
                ("Open Resume Hub", "view")]
        choice = dialog.select("Infinity: Watched and Lists", [label for label, _ in rows])
        if not 0 <= choice < len(rows):
            return
        action = rows[choice][1]
        if action == "view":
            modules["context"].view_hub()
        else:
            if controller.apply(modules, profile, entry, action, intent=intent):
                xbmc.executebuiltin("Container.Refresh")
            else:
                dialog.ok("No change applied", "This title's local state was unchanged. Its identity may need a compatibility check; no unrelated record was modified.")
    except (controller.UnsupportedController, OSError, ValueError, RuntimeError) as error:
        dialog.ok("Action not completed", str(error))


if __name__ == "__main__":
    main()
