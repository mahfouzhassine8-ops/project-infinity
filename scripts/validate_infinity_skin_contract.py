#!/usr/bin/env python3
"""Static/matrix gate for Infinity native-responsive skin/theme contract.

This validates source contracts only. It does not claim real Fold, touch, rendering,
refresh-rate, or player behavior until an on-device run supplies evidence.
"""
from __future__ import annotations

import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
COMPAT = ROOT / 'addons/service.infinity.compat'
SKIN_API = json.loads((COMPAT / 'resources/skin-api.json').read_text(encoding='utf-8'))
CAPS = json.loads((COMPAT / 'resources/capabilities.json').read_text(encoding='utf-8'))
THEME_SRC = (COMPAT / 'theme_contract.py').read_text(encoding='utf-8')
LAYOUT_SRC = (COMPAT / 'layout_service.py').read_text(encoding='utf-8')
COMPAT_SRC = (COMPAT / 'service.py').read_text(encoding='utf-8')
OSD_PATH = COMPAT / 'resources/xml/VideoOSD.xml'
PANEL_PATH = COMPAT / 'resources/xml/Custom_1197_InfinityPlayerPanel.xml'
OSD_SRC = OSD_PATH.read_text(encoding='utf-8')
PANEL_SRC = PANEL_PATH.read_text(encoding='utf-8')

REQUIRED_PROPERTIES = {
    'Infinity.NativeSystemTheme', 'Infinity.NativeDeviceMode', 'Infinity.NativeLayout',
    'Infinity.NativeWidthDp', 'Infinity.NativeHeightDp', 'Infinity.NativeDisplayRevision',
    'Infinity.NativeReady', 'Infinity.SystemTheme', 'Infinity.ThemeRevision',
    'Infinity.DeviceMode', 'Infinity.Orientation', 'Infinity.Layout', 'Infinity.PaneMode',
    'Infinity.WindowWidth', 'Infinity.WindowHeight', 'Infinity.WindowWidthDp',
    'Infinity.WindowHeightDp', 'Infinity.DensityDpi', 'Infinity.AspectClass',
    'Infinity.SafeInsetTop', 'Infinity.SafeInsetBottom', 'Infinity.SafeInsetLeft',
    'Infinity.SafeInsetRight', 'Infinity.TouchClass', 'Infinity.DisplaySource',
    'Infinity.MotionPolicy', 'Infinity.RefreshPolicy', 'Infinity.PowerPolicy',
    'Infinity.ProtectedPlayerUI'
}
REQUIRED_TOKENS = {
    'Infinity.Palette.Background', 'Infinity.Palette.Surface',
    'Infinity.Palette.SurfaceElevated', 'Infinity.Palette.TextPrimary',
    'Infinity.Palette.TextSecondary', 'Infinity.Palette.Border',
    'Infinity.Palette.Focus', 'Infinity.Palette.Accent',
    'Infinity.Palette.Danger', 'Infinity.Palette.Scrim'
}


def classify(width_dp: int, height_dp: int, fold=False, tv=False):
    ratio = max(width_dp, height_dp) / float(min(width_dp, height_dp))
    layout = 'compact' if width_dp < 600 else 'medium' if width_dp < 840 else 'expanded'
    if tv:
        device = 'tv'
    elif (fold or ratio <= 1.60) and width_dp >= 600:
        device = 'inner/large'
    elif fold:
        device = 'cover/front'
    elif width_dp >= 600:
        device = 'tablet'
    else:
        device = 'phone'
    orientation = 'landscape' if width_dp > height_dp else 'portrait' if height_dp > width_dp else 'square'
    touch = 'compact' if layout == 'compact' else 'large-display' if layout == 'expanded' else 'normal'
    pane = 'pane' if width_dp >= 600 and device in ('inner/large', 'tablet') else 'overlay'
    return device, layout, orientation, touch, pane


def main():
    props = set(SKIN_API['properties'])
    tokens = set(SKIN_API['palette_tokens'])
    assert SKIN_API['layout_api'] == '1.2'
    assert SKIN_API['theme_contract'] == '1.1'
    assert REQUIRED_PROPERTIES <= props, sorted(REQUIRED_PROPERTIES - props)
    assert REQUIRED_TOKENS <= tokens, sorted(REQUIRED_TOKENS - tokens)
    assert set(SKIN_API['theme_values']) == {'light', 'dark', 'OLED'}
    for flag in ('protected_player_ui', 'protected_player_panel', 'palette_tokens',
                 'responsive_display_state', 'native_responsive_bridge_v5',
                 'native_dp_window_classes', 'pane_mode',
                 'event_driven_theme_updates', 'event_driven_layout_updates'):
        assert CAPS['capabilities'][flag] is True, flag

    assert 'ReloadSkin()' not in COMPAT_SRC
    assert 'while not monitor.abortRequested()' not in LAYOUT_SRC
    assert 'monitor.waitForAbort()' in LAYOUT_SRC
    assert 'monitor.waitForAbort()' in THEME_SRC
    assert "bridge < 5" not in LAYOUT_SRC
    assert "bridge < 5 or not _prop_bool(home, 'Infinity.NativeReady')" in LAYOUT_SRC
    assert "'source': 'native-v5'" in LAYOUT_SRC
    assert "'Infinity.PaneMode'" in LAYOUT_SRC
    assert "performance_override_battery" in THEME_SRC
    assert "performance_ignore_battery_saver" not in THEME_SRC
    assert "Infinity.NativeSystemTheme" in THEME_SRC
    assert THEME_SRC.index("Infinity.Palette.' + token") < THEME_SRC.index("Infinity.ThemeRevision")

    matrix = [
        ('cover portrait', 412, 915, True, 'cover/front', 'compact', 'portrait', 'compact', 'overlay'),
        ('cover landscape', 915, 412, True, 'inner/large', 'expanded', 'landscape', 'large-display', 'pane'),
        ('inner portrait', 673, 790, True, 'inner/large', 'medium', 'portrait', 'normal', 'pane'),
        ('inner landscape', 790, 673, True, 'inner/large', 'medium', 'landscape', 'normal', 'pane'),
        ('large tablet', 900, 600, False, 'inner/large', 'expanded', 'landscape', 'large-display', 'pane'),
        ('phone portrait', 412, 915, False, 'phone', 'compact', 'portrait', 'compact', 'overlay'),
    ]
    for row in matrix:
        name, w, h, fold, dev, lay, orient, touch, pane = row
        actual = classify(w, h, fold)
        expected = (dev, lay, orient, touch, pane)
        assert actual == expected, (name, actual, expected)

    for theme in ('light', 'dark', 'OLED'):
        assert "'" + theme + "'" in THEME_SRC

    player = SKIN_API['player_contract']
    assert player['owner'] == 'Infinity'
    assert player['replaceable_by_skin'] is False
    assert player['panel_window'] == 1197

    ET.parse(OSD_PATH)
    ET.parse(PANEL_PATH)
    for needle in ('Infinity.Palette.Scrim','Infinity.Palette.TextPrimary',
                   'Infinity.Palette.TextSecondary','Infinity.Palette.Focus',
                   'Infinity.Palette.Accent','Infinity.Orientation',
                   'ActivateWindow(osdsubtitlesettings)','ActivateWindow(osdaudiosettings)',
                   'PlayerControl(Play)','ActivateWindow(1199)','ActivateWindow(1197)'):
        assert needle in OSD_SRC, needle
    for needle in ('Chapters / Bookmarks','Subtitles','Audio','Video Settings',
                   'Playback Speed +','Playback Speed -','Related / Cast &amp; Crew',
                   'Close Player','Infinity.RefreshPolicy'):
        assert needle in PANEL_SRC, needle
    assert '<control type="videowindow"' not in OSD_SRC.lower()
    assert '<control type="videowindow"' not in PANEL_SRC.lower()

    print('Infinity Responsive Bridge v5 skin/theme contract matrix PASS')
    print('Real-device gate remains required for fold/unfold, OSD geometry, touch and cutouts.')


if __name__ == '__main__':
    main()
