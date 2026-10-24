import json
import os
import time
import urllib.parse
import uuid

import xbmc
import xbmcaddon
import xbmcgui

from .catalog import load_catalog
from .sources import add_source_dialog, manage_sources_dialog
from .storage import SourceStore
from .ui import InfinityLiveWindow
from .multiview import channel_payload, launch_command, write_request


class InfinityPlayer(xbmc.Player):
    pass


def _stream_url(channel):
    url = channel.url
    headers = []
    user_agent = channel.properties.get("vlc.http-user-agent")
    referer = channel.properties.get("vlc.http-referrer") or channel.properties.get("vlc.http-referer")
    if user_agent:
        headers.append("User-Agent=" + urllib.parse.quote_plus(user_agent))
    if referer:
        headers.append("Referer=" + urllib.parse.quote_plus(referer))
    if headers and "|" not in url:
        url += "|" + "&".join(headers)
    return url


def _play_channel(player, channel, state):
    """Android Live TV is owned by Media3/ExoPlayer; Kodi player remains fallback off Android."""
    if xbmc.getCondVisibility("System.Platform.Android"):
        try:
            payload = channel_payload(channel)
            if not payload.get("url"):
                raise ValueError("Channel has no playable URL")
            request = {
                "schema": 1,
                "mode": "single",
                "audio_tile": 0,
                "created_epoch": int(time.time()),
                "channels": [payload],
            }
            request_path = write_request(SourceStore().profile_dir, request)
            if player.isPlaying():
                player.stop()
            xbmc.executebuiltin(launch_command(request_path))
            state["owned_playback"] = False
            state["channel_key"] = channel.stable_key()
            state["exo_live"] = True
            return
        except Exception as exc:
            xbmcgui.Dialog().notification("Infinity Live", "ExoPlayer launch failed: {}".format(exc), xbmcgui.NOTIFICATION_ERROR, 3500)
            return

    item = xbmcgui.ListItem(label=channel.name, path=channel.url)
    item.setInfo("video", {"title": channel.name, "genre": channel.group or "Live TV"})
    if channel.logo:
        item.setArt({"thumb": channel.logo, "icon": channel.logo})
    for key, value in channel.properties.items():
        if key.startswith("vlc."):
            continue
        try:
            item.setProperty(key, value)
        except Exception:
            pass
    player.play(_stream_url(channel), item)
    state["owned_playback"] = True
    state["channel_key"] = channel.stable_key()


def _load_with_progress(store, force=False):
    source = store.active()
    if not source:
        return None
    progress = xbmcgui.DialogProgress()
    progress.create("Infinity Live", "Loading channels and guide…")
    try:
        catalog = load_catalog(source, store.profile_dir, force=force)
        progress.update(100, f"{len(catalog.channels)} channels ready")
        xbmc.sleep(120)
        return catalog
    finally:
        progress.close()


def _fullscreen_roundtrip(player):
    if not player.isPlayingVideo():
        return
    xbmc.executebuiltin("ActivateWindow(fullscreenvideo)")
    monitor = xbmc.Monitor()
    entered = False
    for _ in range(40):
        if monitor.abortRequested():
            return
        if xbmcgui.getCurrentWindowId() == 12005:
            entered = True
            break
        monitor.waitForAbort(0.05)
    if not entered:
        return
    while not monitor.abortRequested() and xbmcgui.getCurrentWindowId() == 12005:
        monitor.waitForAbort(0.15)


def run():
    addon = xbmcaddon.Addon("script.infinity.live")
    addon_path = addon.getAddonInfo("path")
    store = SourceStore()
    dialog = xbmcgui.Dialog()

    if not store.sources():
        if not dialog.yesno("Infinity Live", "Add your first Live TV source?\n\nInfinity Live supports user-authorized M3U/M3U8 + XMLTV and Xtream-style logins."):
            return
        if not add_source_dialog(store):
            return

    player = InfinityPlayer()
    state = {"owned_playback": False, "channel_key": "", "exo_live": False}
    force = False
    catalog = None

    while True:
        try:
            catalog = _load_with_progress(store, force=force)
            force = False
        except Exception as exc:
            choice = dialog.select("Infinity Live", ["Try again", "Manage sources", "Exit"], preselect=0)
            if choice == 1:
                manage_sources_dialog(store)
                force = True
                continue
            if choice == 0:
                force = True
                continue
            dialog.notification("Infinity Live", str(exc), addon_path.rstrip("/") + "/resources/icon.png", 3500, False)
            break
        if not catalog:
            break

        window = InfinityLiveWindow(
            addon_path,
            catalog,
            store,
            player,
            lambda channel: _play_channel(player, channel, state),
        )
        window.doModal()
        outcome = window.outcome
        del window

        if outcome == "fullscreen":
            _fullscreen_roundtrip(player)
            continue
        if outcome == "sources":
            if manage_sources_dialog(store):
                force = True
            continue
        if outcome == "refresh":
            force = True
            continue
        break

    if state.get("owned_playback") and player.isPlaying():
        player.stop()
