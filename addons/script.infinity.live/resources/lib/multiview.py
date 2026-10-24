"""Infinity Live 2-up Multi-View request + UI integration.

The normal Kodi application player is intentionally single-owner. Multi-View
therefore hands two user-selected live URLs to Infinity's Android-side overlay
controller rather than creating competing xbmc.Player instances.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from urllib.parse import parse_qsl, quote

PACKAGE = "com.projectinfinity.kodi"
MAIN_CLASS = PACKAGE + ".Main"
SCHEME = "infinity-multiview"
BUTTON_ORDER = ["GUIDE", "FAVORITE", "FULL SCREEN", "MULTI-VIEW", "SOURCES", "REFRESH", "EXIT"]


def _split_kodi_url(url: str):
    base, sep, tail = (url or "").partition("|")
    headers = {}
    if sep:
        for key, value in parse_qsl(tail, keep_blank_values=True):
            if key:
                headers[key] = value
    return base, headers


def _channel_headers(channel):
    url, headers = _split_kodi_url(getattr(channel, "url", ""))
    props = getattr(channel, "properties", {}) or {}
    aliases = {
        "vlc.http-user-agent": "User-Agent",
        "http-user-agent": "User-Agent",
        "user-agent": "User-Agent",
        "vlc.http-referrer": "Referer",
        "vlc.http-referer": "Referer",
        "http-referrer": "Referer",
        "http-referer": "Referer",
        "referer": "Referer",
        "origin": "Origin",
        "http-origin": "Origin",
    }
    normalized = {str(k).lower(): str(v) for k, v in props.items() if v is not None}
    for source_key, target_key in aliases.items():
        value = normalized.get(source_key)
        if value and target_key not in headers:
            headers[target_key] = value
    return url, headers


def channel_payload(channel):
    url, headers = _channel_headers(channel)
    return {
        "name": getattr(channel, "name", "Live channel") or "Live channel",
        "group": getattr(channel, "group", "") or "",
        "logo": getattr(channel, "logo", "") or "",
        "url": url,
        "headers": headers,
    }


def build_request(primary, secondary):
    left = channel_payload(primary)
    right = channel_payload(secondary)
    if not left["url"] or not right["url"]:
        raise ValueError("Both Multi-View channels need a playable URL")
    if left["url"] == right["url"]:
        raise ValueError("Choose two different channels for Multi-View")
    return {
        "schema": 1,
        "mode": "split2",
        "audio_tile": 0,
        "created_epoch": int(time.time()),
        "channels": [left, right],
    }


def _cleanup_requests(profile_dir):
    try:
        for name in os.listdir(profile_dir):
            if not name.startswith("multiview-request-") or not name.endswith(".json"):
                continue
            path = os.path.join(profile_dir, name)
            try:
                if time.time() - os.path.getmtime(path) > 300:
                    os.remove(path)
            except OSError:
                pass
    except OSError:
        pass


def write_request(profile_dir, request):
    os.makedirs(profile_dir, exist_ok=True)
    _cleanup_requests(profile_dir)
    path = os.path.join(profile_dir, "multiview-request-" + uuid.uuid4().hex + ".json")
    temp = path + ".tmp"
    with open(temp, "w", encoding="utf-8") as handle:
        json.dump(request, handle, separators=(",", ":"), ensure_ascii=False)
        handle.flush()
        try:
            os.fsync(handle.fileno())
        except OSError:
            pass
    try:
        os.chmod(temp, 0o600)
    except OSError:
        pass
    os.replace(temp, path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return path


def launch_command(request_path):
    # Only the ephemeral request *path* travels through Kodi's logged Android
    # launcher builtin. Stream URLs/credentials stay inside the request file.
    data_uri = SCHEME + "://open?path=" + quote(request_path, safe="")
    return "StartAndroidActivity({0},,,{1},,,,,{2})".format(PACKAGE, data_uri, MAIN_CLASS)


def _guide_title(window, channel):
    guide = window.catalog.guides.get(channel.stable_key())
    if guide and guide.current:
        return guide.current.title
    return channel.group or "Live"


def choose_partner(window, primary):
    import xbmcgui

    candidates = [c for c in window.catalog.channels if c.stable_key() != primary.stable_key()]
    if not candidates:
        xbmcgui.Dialog().notification("Infinity Multi-View", "Add at least two live channels first", window.addon_path.rstrip("/") + "/resources/icon.png", 2500, False)
        return None
    labels = ["{}  •  {}".format(c.name, _guide_title(window, c)) for c in candidates]
    index = xbmcgui.Dialog().select("Choose second live channel", labels, preselect=0)
    return candidates[index] if 0 <= index < len(candidates) else None


def launch_from_window(window):
    import xbmc
    import xbmcgui

    if not xbmc.getCondVisibility("System.Platform.Android"):
        xbmcgui.Dialog().ok("Infinity Multi-View", "Multi-View Candidate 1 currently requires the Infinity Android APK.")
        return False

    primary = window._selected_channel()
    if primary is None:
        xbmcgui.Dialog().notification("Infinity Multi-View", "Select a live channel first", window.addon_path.rstrip("/") + "/resources/icon.png", 2200, False)
        return False
    secondary = choose_partner(window, primary)
    if secondary is None:
        return False

    try:
        request = build_request(primary, secondary)
        request_path = write_request(window.store.profile_dir, request)
    except Exception as exc:
        xbmcgui.Dialog().ok("Infinity Multi-View", "Could not prepare Multi-View: {}".format(exc))
        return False

    # Release Kodi's accepted single-player preview before asking Android for
    # two decoder surfaces. This prevents an accidental three-decoder workload.
    try:
        if window.player.isPlaying():
            window.player.stop()
            monitor = xbmc.Monitor()
            for _ in range(20):
                if not window.player.isPlaying() or monitor.abortRequested():
                    break
                monitor.waitForAbort(0.05)
    except Exception:
        pass

    try:
        xbmc.executebuiltin(launch_command(request_path))
        window.status_label.setLabel("MULTI-VIEW  •  {} + {}  •  OK switches audio".format(primary.name, secondary.name))
        return True
    except Exception as exc:
        try:
            os.remove(request_path)
        except OSError:
            pass
        xbmcgui.Dialog().ok("Infinity Multi-View", "Could not open Multi-View: {}".format(exc))
        return False


def _install_button(window):
    import xbmcgui

    if "MULTI-VIEW" in window.buttons:
        return
    w, h = xbmcgui.getScreenWidth(), xbmcgui.getScreenHeight()
    margin = max(18, int(min(w, h) * 0.025))
    footer_h = max(54, int(h * 0.072))
    gap = max(6, int(margin * 0.35))
    available = w - margin * 2
    button_w = int((available - gap * (len(BUTTON_ORDER) - 1)) / len(BUTTON_ORDER))
    y = h - margin - footer_h

    for index, label in enumerate(BUTTON_ORDER):
        x = margin + index * (button_w + gap)
        if label == "MULTI-VIEW":
            control = xbmcgui.ControlButton(
                x, y, button_w, footer_h, label,
                window.textures["focus"], window.textures["panel"],
                alignment=6, font="font13", textColor=window.theme["text"], focusedColor="FFFFFFFF",
            )
            window.addControl(control)
            window.buttons[label] = control
        else:
            control = window.buttons[label]
            control.setPosition(x, y)
            control.setWidth(button_w)
            control.setHeight(footer_h)


def install_multiview_hooks():
    from .ui import InfinityLiveWindow

    if getattr(InfinityLiveWindow, "_infinity_multiview_contract", False):
        return

    original_build = InfinityLiveWindow._build
    original_control = InfinityLiveWindow.onControl

    def build(self):
        original_build(self)
        _install_button(self)

    def on_control(self, control):
        if control == self.buttons.get("MULTI-VIEW"):
            launch_from_window(self)
            return
        original_control(self, control)

    InfinityLiveWindow._build = build
    InfinityLiveWindow.onControl = on_control
    InfinityLiveWindow._infinity_multiview_contract = True
