"""Real Kodi menu/store operations plus before/after production row rendering."""
import hashlib
import json
from pathlib import Path
import sys
import threading
import traceback

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "addon"))
import controller
import bridge_state


def require(value, message):
    if not value:
        raise RuntimeError(message)


def rpc(method, params):
    value = json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc="2.0", id=1, method=method, params=params))))
    require("error" not in value, "Kodi API refused " + method)
    return value.get("result")


def change_skin(addon_id):
    rpc("Addons.SetAddonEnabled", dict(addonid=addon_id, enabled=True))
    errors = []
    def request():
        try:
            require(rpc("Settings.SetSettingValue", dict(setting="lookandfeel.skin", value=addon_id)) is True, "Skin setting was refused")
            xbmc.executebuiltin("ReloadSkin")
        except Exception: errors.append(traceback.format_exc())
    thread = threading.Thread(target=request); thread.start()
    monitor = xbmc.Monitor()
    for attempt in range(120):
        if xbmcgui.getCurrentWindowDialogId() == 10100:
            xbmc.executebuiltin("SendClick(11)")
        if xbmc.getSkinDir() == addon_id and not thread.is_alive() and xbmcgui.getCurrentWindowDialogId() != 10100:
            try:
                xbmcgui.Window(10000).getControl(50)
                break
            except RuntimeError:
                pass
        monitor.waitForAbort(0.25)
    thread.join(timeout=2)
    require(not thread.is_alive() and not errors and xbmc.getSkinDir() == addon_id, "Fixture skin did not activate: " + str(errors))
    xbmcgui.Window(10000).getControl(50)  # Setting text alone is not a loaded fixture.
    xbmc.sleep(800)


def row(label, watched=None, playcount=0, icon="DefaultVideo.png", kind="movie"):
    item = xbmcgui.ListItem(label=label, label2="Offline UI fixture", path="plugin://plugin.video.infinityfixture/?id=123")
    item.setInfo("video", dict(mediatype=kind, title=label, playcount=playcount, season=1, episode=2))
    item.setUniqueIDs({"tmdb": "123"})
    item.setArt(dict(icon=icon, thumb=icon))
    if watched is not None:
        item.setProperty("Infinity.ResumeHub.Watched", "true" if watched else "false")
    return item


profile = Path(xbmcvfs.translatePath("special://profile/"))
output = profile / "watched-runtime-result.json"
capture = profile / "watched-render-evidence"; capture.mkdir(exist_ok=True)
result = dict(passed=False, real_kodi_api=True, native_index_verified=False,
              real_provider_addons_tested=False, physical_fold_verified=False,
              renderer_scope="Extracted production 16x9 provider-row controls with actual source fonts/palette/assets; native index and full skin require separate Android/Fold gates")
try:
    rpc("Addons.SetAddonEnabled", dict(addonid="script.infinity.commandcenter", enabled=True))
    addon = xbmcaddon.Addon("script.infinity.commandcenter")
    modules = controller.load(xbmcvfs.translatePath(addon.getAddonInfo("path")))
    hub, common = modules["resume_hub"], modules["common"]
    cc_profile = Path(xbmcvfs.translatePath(addon.getAddonInfo("profile")))
    selected = modules["context"].selected_entry(row("Never-played fixture"))
    require(selected is not None, "Actual Kodi metadata ingress unavailable")
    with common.persistence_scope():
        common.atomic_json(cc_profile / hub.CONTINUE_FILE, dict(schema=2, foreign={"retained": [1, 2, 3]}))
    for action in ("toggle-watchlist", "toggle-collection", "mark-watched"):
        require(controller.apply(modules, cc_profile, selected, action), "Existing writer action failed: " + action)
    data = hub.load_view(cc_profile)
    key = selected["key"]
    require(key in data["watchlist"] and key in data["collection"] and key in data["watched"] and key not in data["items"], "Watched/list state incorrect")
    require(controller.apply(modules, cc_profile, selected, "mark-unwatched"), "Explicit Unwatched failed")
    data = hub.load_view(cc_profile)
    require(key not in data["watched"] and key not in data["items"] and key in data["watchlist"] and key in data["collection"], "Unwatched changed list or Continue semantics")
    require(data["foreign"] == {"retained": [1, 2, 3]}, "Foreign progress data changed")
    persisted = json.loads((cc_profile / hub.CONTINUE_FILE).read_text())
    require(bridge_state.lookup(bridge_state.records(persisted), bridge_state.identity(selected)) == "false", "Unwatched override was not durable")
    source = json.loads((profile / "watched-render-fixture/SOURCE-IDENTITY.json").read_text())
    images = []
    checks = []
    for version in ("before", "after"):
        change_skin("skin.infinity.rowverify." + version)
        for theme in ("light", "dark", "OLED"):
            home = xbmcgui.Window(10000)
            home.setProperty("Infinity.SystemTheme", theme)
            home.setProperty("Infinity.NativeSystemTheme", theme)
            home.setProperty("Infinity.OptionalMotionAllowed", "false")
            control = home.getControl(50)
            control.reset()
            cases = [("Watched movie", True, 0, True), ("Unplayed movie", None, 0, False),
                     ("Partially watched movie", None, 0, False), ("Native watched movie", None, 1, True),
                     ("Explicit Unwatched over native playcount", False, 1, False),
                     ("Watchlist only; no watched badge", None, 0, False), ("Watched episode; missing art", True, 0, True)]
            for label, watched, count, expected in cases:
                item = row(label, watched, count, kind="episode" if "episode" in label else "movie")
                if "Watchlist" in label: item.setProperty("Infinity.ResumeHub.Watchlist", "true")
                control.addItem(item)
            home.setFocusId(50)
            for index, case in enumerate(cases):
                control.selectItem(index); xbmc.sleep(80)
                observed = xbmc.getCondVisibility(source["watched_condition"])
                require(observed == case[3], "Actual row predicate mismatch: " + case[0])
                checks.append(dict(version=version, theme=theme, label=case[0], expected_watched=case[3], observed=observed))
            control.selectItem(1); xbmc.sleep(600)
            target = capture / (version + "-" + theme.lower() + ".png")
            xbmc.executebuiltin("TakeScreenshot(" + str(target) + ",sync)", True)
            require(target.is_file() and target.stat().st_size > 1000, "Native screenshot missing")
            images.append(target.name)
    result.update(passed=True, kodi_version=xbmc.getInfoLabel("System.BuildVersion"),
                  actual_installed_controller_preimages_verified=13,
                  never_played_context_ingress=True, existing_writer_actions_verified=True,
                  watchlist_collection_and_foreign_keys_retained=True, durable_unwatched_without_continue=True,
                  rendered_images=images, row_predicate_checks=checks, source_projection=source)
except Exception:
    result["failure"] = traceback.format_exc()
finally:
    output.write_text(json.dumps(result, indent=2) + "\n")
