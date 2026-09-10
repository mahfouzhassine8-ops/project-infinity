# SPDX-License-Identifier: GPL-2.0-or-later
"""Infinity Adaptive Layout API 1.0.

Publishes Kodi-reported usable screen geometry as stable Window(Home) properties so
Infinity-aware skins can implement responsive compact/medium/expanded layouts without
device-specific Python glue.
"""
from __future__ import annotations

import re
import time

import xbmc
import xbmcgui

TAG = '[InfinityLayout] '
LAYOUT_API = '1.0'


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


def _screen_size():
    """Return Kodi-reported screen width/height, with ScreenMode as a fallback."""
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


def _classify(width: int, height: int):
    if width <= 0 or height <= 0:
        return 'unknown', 'unknown', 'unknown', 0.0, 0

    orientation = 'landscape' if width > height else ('portrait' if height > width else 'square')
    short_edge = min(width, height)
    long_edge = max(width, height)
    aspect = round(width / float(height), 4)

    # Geometry classes intentionally use reported pixels rather than device models.
    # A cover/phone-style surface normally lands in compact; unfolded/tablet surfaces
    # naturally graduate to medium or expanded as their usable short edge grows.
    if short_edge < 720:
        layout = 'compact'
    elif short_edge < 1200:
        layout = 'medium'
    else:
        layout = 'expanded'

    if layout == 'compact':
        display = 'cover_or_phone'
    elif layout == 'medium':
        display = 'large_phone_or_tablet'
    else:
        display = 'large_or_unfolded'

    return layout, orientation, display, aspect, short_edge


def snapshot():
    width, height = _screen_size()
    layout, orientation, display, aspect, short_edge = _classify(width, height)
    long_edge = max(width, height) if width > 0 and height > 0 else 0
    return {
        'api': LAYOUT_API,
        'width': width,
        'height': height,
        'short_edge': short_edge,
        'long_edge': long_edge,
        'aspect': aspect,
        'orientation': orientation,
        'layout': layout,
        'display_class': display,
    }


def publish(state) -> None:
    _set('Infinity.LayoutAPI', state['api'])
    _set('Infinity.LayoutWidth', state['width'])
    _set('Infinity.LayoutHeight', state['height'])
    _set('Infinity.LayoutShortEdge', state['short_edge'])
    _set('Infinity.LayoutLongEdge', state['long_edge'])
    _set('Infinity.LayoutAspect', state['aspect'])
    _set('Infinity.Orientation', state['orientation'])
    _set('Infinity.Layout', state['layout'])
    _set('Infinity.DisplayClass', state['display_class'])
    _set('Infinity.LayoutReady', str(state['width'] > 0 and state['height'] > 0).lower())


if __name__ == '__main__':
    monitor = xbmc.Monitor()
    previous = None
    xbmc.log(TAG + 'Adaptive Layout API ' + LAYOUT_API + ' started', xbmc.LOGINFO)
    while not monitor.abortRequested():
        current = snapshot()
        signature = (
            current['width'], current['height'], current['orientation'],
            current['layout'], current['display_class']
        )
        if signature != previous:
            publish(current)
            previous = signature
            xbmc.log(
                TAG + 'layout=' + current['layout'] +
                ' orientation=' + current['orientation'] +
                ' size=' + str(current['width']) + 'x' + str(current['height']),
                xbmc.LOGINFO,
            )
        if monitor.waitForAbort(1.0):
            break
