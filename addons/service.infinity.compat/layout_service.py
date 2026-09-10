# SPDX-License-Identifier: GPL-2.0-or-later
"""Infinity responsive display-state contract.

Infinity is the single source of truth for skin-visible geometry. This service publishes
actual current Kodi GUI dimensions and responsive classes on startup and on Kodi events;
it intentionally has no polling loop.
"""
from __future__ import annotations

import re
import xbmc
import xbmcgui

TAG = '[InfinityLayout] '
LAYOUT_API = '1.1'
VALID_DEVICE_MODES = {'cover/front', 'inner/large', 'phone', 'tablet'}


def _home():
    return xbmcgui.Window(10000)


def _set(name: str, value) -> None:
    try:
        _home().setProperty(name, str(value))
    except Exception:
        pass


def _number(label: str) -> int:
    try:
        raw = xbmc.getInfoLabel(label).strip()
        match = re.search(r'(\d+)', raw.replace(',', ''))
        return int(match.group(1)) if match else 0
    except Exception:
        return 0


def _current_gui_size():
    """Read the active Kodi GUI window first, with system labels only as fallbacks."""
    try:
        window_id = xbmcgui.getCurrentWindowId()
        window = xbmcgui.Window(window_id)
        width = int(window.getWidth())
        height = int(window.getHeight())
        if width > 0 and height > 0:
            return width, height
    except Exception:
        pass

    width = _number('System.ScreenWidth')
    height = _number('System.ScreenHeight')
    if width > 0 and height > 0:
        return width, height

    try:
        mode = xbmc.getInfoLabel('System.ScreenMode')
        match = re.search(r'(\d{2,5})\s*[xX]\s*(\d{2,5})', mode or '')
        if match:
            return int(match.group(1)), int(match.group(2))
    except Exception:
        pass
    return 0, 0


def _aspect_class(width: int, height: int) -> str:
    if width <= 0 or height <= 0:
        return 'unknown'
    ratio = width / float(height)
    if ratio < 0.82:
        return 'portrait'
    if ratio < 1.22:
        return 'square-ish'
    if ratio < 2.0:
        return 'standard-landscape'
    return 'ultrawide'


def _bridge_device_mode() -> str:
    """Prefer an Android/host bridge classification when available."""
    home = _home()
    for key in ('Infinity.NativeDeviceMode', 'Infinity.AndroidDeviceMode'):
        try:
            value = home.getProperty(key).strip().lower()
            if value in VALID_DEVICE_MODES:
                return value
        except Exception:
            pass
    return ''


def _classes(width: int, height: int):
    if width <= 0 or height <= 0:
        return 'unknown', 'unknown', 'unknown', 'unknown'

    orientation = 'landscape' if width > height else 'portrait' if height > width else 'square'
    short_edge = min(width, height)
    long_edge = max(width, height)
    ratio = long_edge / float(short_edge)

    if short_edge < 720:
        layout = 'compact'
    elif short_edge < 1200:
        layout = 'medium'
    else:
        layout = 'expanded'

    native_mode = _bridge_device_mode()
    if native_mode:
        device = native_mode
    elif short_edge < 720 and ratio >= 1.75:
        device = 'cover/front'
    elif ratio >= 1.8:
        device = 'phone'
    elif layout == 'expanded' and ratio <= 1.5:
        device = 'inner/large'
    elif layout == 'expanded':
        device = 'tablet'
    else:
        device = 'phone'

    touch = 'compact' if layout == 'compact' else 'large-display' if layout == 'expanded' else 'normal'
    return layout, orientation, device, touch


def _existing_inset(name: str) -> int:
    """Preserve any inset supplied by the Android bridge; otherwise Kodi GUI is the safe area."""
    try:
        value = _home().getProperty(name).strip()
        return max(0, int(value)) if value else 0
    except Exception:
        return 0


def snapshot():
    width, height = _current_gui_size()
    layout, orientation, device, touch = _classes(width, height)
    short_edge = min(width, height) if width > 0 and height > 0 else 0
    long_edge = max(width, height) if width > 0 and height > 0 else 0
    aspect = round(width / float(height), 4) if width > 0 and height > 0 else 0.0
    return {
        'api': LAYOUT_API,
        'width': width,
        'height': height,
        'short_edge': short_edge,
        'long_edge': long_edge,
        'aspect': aspect,
        'aspect_class': _aspect_class(width, height),
        'orientation': orientation,
        'layout': layout,
        'device_mode': device,
        'touch_class': touch,
        'inset_top': _existing_inset('Infinity.SafeInsetTop'),
        'inset_bottom': _existing_inset('Infinity.SafeInsetBottom'),
        'inset_left': _existing_inset('Infinity.SafeInsetLeft'),
        'inset_right': _existing_inset('Infinity.SafeInsetRight'),
    }


def publish(force=False) -> bool:
    state = snapshot()
    signature = '|'.join(str(state[k]) for k in (
        'width', 'height', 'orientation', 'device_mode', 'layout', 'aspect_class',
        'inset_top', 'inset_bottom', 'inset_left', 'inset_right'
    ))
    home = _home()
    if not force and home.getProperty('Infinity.DisplaySignature') == signature:
        return False

    values = {
        'Infinity.LayoutAPI': state['api'],
        'Infinity.WindowWidth': state['width'],
        'Infinity.WindowHeight': state['height'],
        'Infinity.Orientation': state['orientation'],
        'Infinity.DeviceMode': state['device_mode'],
        'Infinity.AspectClass': state['aspect_class'],
        'Infinity.TouchClass': state['touch_class'],
        'Infinity.SafeInsetTop': state['inset_top'],
        'Infinity.SafeInsetBottom': state['inset_bottom'],
        'Infinity.SafeInsetLeft': state['inset_left'],
        'Infinity.SafeInsetRight': state['inset_right'],
        'Infinity.Layout': state['layout'],
        'Infinity.LayoutWidth': state['width'],
        'Infinity.LayoutHeight': state['height'],
        'Infinity.LayoutShortEdge': state['short_edge'],
        'Infinity.LayoutLongEdge': state['long_edge'],
        'Infinity.LayoutAspect': state['aspect'],
        'Infinity.LayoutReady': str(state['width'] > 0 and state['height'] > 0).lower(),
        'Infinity.DisplaySignature': signature,
    }
    for key, value in values.items():
        _set(key, value)

    xbmc.log(
        TAG + 'device=' + state['device_mode'] + ' layout=' + state['layout'] +
        ' orientation=' + state['orientation'] + ' size=' +
        str(state['width']) + 'x' + str(state['height']), xbmc.LOGINFO,
    )
    return True


class DisplayMonitor(xbmc.Monitor):
    def onNotification(self, sender, method, data):
        publish()

    def onSettingsChanged(self):
        publish(force=True)

    def onScreensaverDeactivated(self):
        publish(force=True)

    def onDPMSDeactivated(self):
        publish(force=True)


if __name__ == '__main__':
    monitor = DisplayMonitor()
    xbmc.log(TAG + 'Adaptive Layout API ' + LAYOUT_API + ' event service started', xbmc.LOGINFO)
    publish(force=True)
    monitor.waitForAbort()
