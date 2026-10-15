# SPDX-License-Identifier: GPL-2.0-or-later
"""Infinity responsive display-state contract.

Bridge v5 is the preferred source of truth. It publishes Android window semantics in dp
and device/layout classes through native Window(Home) properties. Kodi GUI labels are
used only as diagnostics/fallbacks; authored skin-canvas dimensions never override v5.
"""
from __future__ import annotations

import re
import xbmc
import xbmcgui

TAG = '[InfinityLayout] '
LAYOUT_API = '1.2'
VALID_DEVICE_MODES = {'cover/front', 'inner/large', 'phone', 'tablet', 'tv', 'unknown'}
VALID_LAYOUTS = {'compact', 'medium', 'expanded', 'unknown'}


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


def _prop_int(home, name: str) -> int:
    try:
        raw = home.getProperty(name).strip()
        return max(0, int(raw)) if raw else 0
    except Exception:
        return 0


def _prop_bool(home, name: str) -> bool:
    try:
        return home.getProperty(name).strip().lower() == 'true'
    except Exception:
        return False


def _screen_size():
    """Diagnostic/fallback pixel size; never used to override native v5 classes."""
    width = _number('System.ScreenWidth')
    height = _number('System.ScreenHeight')
    if width > 0 and height > 0:
        return width, height, 'kodi-screen-labels'
    try:
        mode = xbmc.getInfoLabel('System.ScreenMode')
        match = re.search(r'(\d{2,5})\s*[xX]\s*(\d{2,5})', mode or '')
        if match:
            return int(match.group(1)), int(match.group(2)), 'kodi-screen-mode'
    except Exception:
        pass
    try:
        window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
        width, height = int(window.getWidth()), int(window.getHeight())
        if width > 0 and height > 0:
            return width, height, 'kodi-canvas-fallback'
    except Exception:
        pass
    return 0, 0, 'unknown'


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


def _native_v5_state():
    home = _home()
    try:
        bridge = int(home.getProperty('Infinity.BridgeVersion') or '0')
    except Exception:
        bridge = 0
    if bridge < 5 or not _prop_bool(home, 'Infinity.NativeReady'):
        return None

    device = (home.getProperty('Infinity.NativeDeviceMode') or 'unknown').strip().lower()
    layout = (home.getProperty('Infinity.NativeLayout') or 'unknown').strip().lower()
    if device not in VALID_DEVICE_MODES or layout not in VALID_LAYOUTS:
        return None
    width_dp = _prop_int(home, 'Infinity.NativeWidthDp')
    height_dp = _prop_int(home, 'Infinity.NativeHeightDp')
    if width_dp <= 0 or height_dp <= 0:
        return None

    # A Fold cover stays compact when rotated even if its horizontal width exceeds 840dp.
    if device == 'cover/front':
        layout = 'compact'

    orientation = (home.getProperty('Infinity.NativeOrientation') or '').strip().lower()
    if orientation not in ('portrait', 'landscape', 'square'):
        orientation = 'landscape' if width_dp > height_dp else 'portrait' if height_dp > width_dp else 'square'
    touch = (home.getProperty('Infinity.NativeTouchClass') or '').strip().lower()
    if device == 'cover/front':
        touch = 'compact'
    elif touch not in ('compact', 'normal', 'large-display'):
        touch = 'compact' if layout == 'compact' else 'large-display' if layout == 'expanded' else 'normal'

    px_w, px_h, px_source = _screen_size()
    density_dpi = round(px_w * 160.0 / width_dp) if px_w > 0 and width_dp > 0 else 0
    revision = _prop_int(home, 'Infinity.NativeDisplayRevision')
    pip = _prop_bool(home, 'Infinity.NativePiP')
    multi = _prop_bool(home, 'Infinity.NativeMultiWindow')
    fold_hint = _prop_bool(home, 'Infinity.NativeFoldHint')
    pane = (not pip and width_dp >= 600 and device in ('inner/large', 'tablet'))
    return {
        'api': LAYOUT_API,
        'width': px_w,
        'height': px_h,
        'width_dp': width_dp,
        'height_dp': height_dp,
        'density_dpi': density_dpi,
        'aspect_class': _aspect_class(width_dp, height_dp),
        'orientation': orientation,
        'layout': layout,
        'device_mode': device,
        'touch_class': touch,
        'pane_mode': 'pane' if pane else 'overlay',
        'pip': pip,
        'multiwindow': multi,
        'fold_hint': fold_hint,
        'revision': revision,
        'source': 'native-v5',
        'pixel_source': px_source,
        'inset_top': 0,
        'inset_bottom': 0,
        'inset_left': 0,
        'inset_right': 0,
        'insets_source': 'kodi-safe-area',
    }


def _fallback_state():
    width, height, source = _screen_size()
    if width <= 0 or height <= 0:
        return {
            'api': LAYOUT_API, 'width': 0, 'height': 0, 'width_dp': 0, 'height_dp': 0,
            'density_dpi': 0, 'aspect_class': 'unknown', 'orientation': 'unknown',
            'layout': 'unknown', 'device_mode': 'unknown', 'touch_class': 'unknown',
            'pane_mode': 'overlay', 'pip': False, 'multiwindow': False, 'fold_hint': False,
            'revision': 0, 'source': source, 'pixel_source': source,
            'inset_top': 0, 'inset_bottom': 0, 'inset_left': 0, 'inset_right': 0,
            'insets_source': 'unknown',
        }
    orientation = 'landscape' if width > height else 'portrait' if height > width else 'square'
    short_edge = min(width, height)
    layout = 'compact' if short_edge < 720 else 'medium' if short_edge < 1200 else 'expanded'
    # Legacy fallback is deliberately conservative: it does not claim Fold cover/inner identity.
    device = 'tablet' if layout == 'expanded' else 'phone'
    touch = 'compact' if layout == 'compact' else 'large-display' if layout == 'expanded' else 'normal'
    return {
        'api': LAYOUT_API, 'width': width, 'height': height, 'width_dp': 0, 'height_dp': 0,
        'density_dpi': 0, 'aspect_class': _aspect_class(width, height),
        'orientation': orientation, 'layout': layout, 'device_mode': device,
        'touch_class': touch, 'pane_mode': 'pane' if device == 'tablet' else 'overlay',
        'pip': False, 'multiwindow': False, 'fold_hint': False, 'revision': 0,
        'source': source, 'pixel_source': source,
        'inset_top': 0, 'inset_bottom': 0, 'inset_left': 0, 'inset_right': 0,
        'insets_source': 'unknown',
    }


def snapshot():
    return _native_v5_state() or _fallback_state()


def publish(force=False) -> bool:
    state = snapshot()
    signature = '|'.join(str(state[k]) for k in (
        'source', 'revision', 'width_dp', 'height_dp', 'orientation', 'device_mode',
        'layout', 'aspect_class', 'pane_mode', 'pip', 'multiwindow',
    ))
    home = _home()
    if not force and home.getProperty('Infinity.DisplaySignature') == signature:
        return False

    values = {
        'Infinity.LayoutAPI': state['api'],
        'Infinity.WindowWidth': state['width'],
        'Infinity.WindowHeight': state['height'],
        'Infinity.WindowWidthDp': state['width_dp'],
        'Infinity.WindowHeightDp': state['height_dp'],
        'Infinity.DensityDpi': state['density_dpi'],
        'Infinity.Orientation': state['orientation'],
        'Infinity.DeviceMode': state['device_mode'],
        'Infinity.AspectClass': state['aspect_class'],
        'Infinity.TouchClass': state['touch_class'],
        'Infinity.Layout': state['layout'],
        'Infinity.PaneMode': state['pane_mode'],
        'Infinity.IsPiP': str(state['pip']).lower(),
        'Infinity.IsMultiWindow': str(state['multiwindow']).lower(),
        'Infinity.FoldHint': str(state['fold_hint']).lower(),
        'Infinity.SafeInsetTop': state['inset_top'],
        'Infinity.SafeInsetBottom': state['inset_bottom'],
        'Infinity.SafeInsetLeft': state['inset_left'],
        'Infinity.SafeInsetRight': state['inset_right'],
        'Infinity.InsetsSource': state['insets_source'],
        'Infinity.DisplaySource': state['source'],
        'Infinity.PixelSource': state['pixel_source'],
        'Infinity.DisplayRevision': state['revision'],
        'Infinity.LayoutReady': str(state['device_mode'] != 'unknown').lower(),
        'Infinity.DisplaySignature': signature,
    }
    for key, value in values.items():
        _set(key, value)

    xbmc.log(
        TAG + 'source=' + state['source'] + ' device=' + state['device_mode'] +
        ' layout=' + state['layout'] + ' pane=' + state['pane_mode'] +
        ' orientation=' + state['orientation'] + ' dp=' +
        str(state['width_dp']) + 'x' + str(state['height_dp']) +
        ' revision=' + str(state['revision']), xbmc.LOGINFO,
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
