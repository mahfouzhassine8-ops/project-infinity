#!/usr/bin/env python3
"""Static/matrix gate for Infinity Skin Theme Contract.

This validates the upper-layer contract and representative responsive/theme states without
pretending to replace real on-device fold/rotation/OSD testing.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPAT = ROOT / 'addons/service.infinity.compat'
SKIN_API = json.loads((COMPAT / 'resources/skin-api.json').read_text(encoding='utf-8'))
CAPS = json.loads((COMPAT / 'resources/capabilities.json').read_text(encoding='utf-8'))
THEME_SRC = (COMPAT / 'theme_contract.py').read_text(encoding='utf-8')
LAYOUT_SRC = (COMPAT / 'layout_service.py').read_text(encoding='utf-8')
COMPAT_SRC = (COMPAT / 'service.py').read_text(encoding='utf-8')

REQUIRED_PROPERTIES = {
    'Infinity.SystemTheme', 'Infinity.ThemeRevision', 'Infinity.DeviceMode',
    'Infinity.Orientation', 'Infinity.WindowWidth', 'Infinity.WindowHeight',
    'Infinity.AspectClass', 'Infinity.SafeInsetTop', 'Infinity.SafeInsetBottom',
    'Infinity.SafeInsetLeft', 'Infinity.SafeInsetRight', 'Infinity.TouchClass',
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


def classify(width: int, height: int):
    short_edge = min(width, height)
    long_edge = max(width, height)
    ratio = long_edge / float(short_edge)
    orientation = 'landscape' if width > height else 'portrait' if height > width else 'square'
    if short_edge < 720:
        layout = 'compact'
    elif short_edge < 1200:
        layout = 'medium'
    else:
        layout = 'expanded'
    if short_edge < 720 and ratio >= 1.75:
        device = 'cover/front'
    elif short_edge >= 1200:
        device = 'inner/large'
    elif short_edge >= 900:
        device = 'tablet'
    else:
        device = 'phone'
    touch = 'compact' if layout == 'compact' else 'large-display' if layout == 'expanded' else 'normal'
    return device, orientation, touch


def main():
    props = set(SKIN_API['properties'])
    tokens = set(SKIN_API['palette_tokens'])
    assert REQUIRED_PROPERTIES <= props, sorted(REQUIRED_PROPERTIES - props)
    assert REQUIRED_TOKENS <= tokens, sorted(REQUIRED_TOKENS - tokens)
    assert set(SKIN_API['theme_values']) == {'light', 'dark', 'OLED'}
    assert CAPS['capabilities']['protected_player_ui'] is True
    assert CAPS['capabilities']['palette_tokens'] is True
    assert CAPS['capabilities']['responsive_display_state'] is True
    assert CAPS['capabilities']['event_driven_theme_updates'] is True
    assert CAPS['capabilities']['event_driven_layout_updates'] is True

    # No normal-theme/orientation forced ReloadSkin, and no geometry polling loop.
    assert 'ReloadSkin()' not in COMPAT_SRC
    assert 'while not monitor.abortRequested()' not in LAYOUT_SRC
    assert 'monitor.waitForAbort()' in LAYOUT_SRC
    assert 'monitor.waitForAbort()' in THEME_SRC

    for token in REQUIRED_TOKENS:
        bare = token.split('.')[-1]
        assert bare in THEME_SRC, bare

    matrix = [
        ('cover portrait', 540, 1280, 'cover/front', 'portrait', 'compact'),
        ('cover landscape', 1280, 540, 'cover/front', 'landscape', 'compact'),
        ('inner portrait', 1200, 1600, 'inner/large', 'portrait', 'large-display'),
        ('inner landscape', 1600, 1200, 'inner/large', 'landscape', 'large-display'),
        ('large-display landscape', 2560, 1600, 'inner/large', 'landscape', 'large-display'),
        ('phone portrait', 1080, 2400, 'tablet', 'portrait', 'normal'),
    ]
    for name, width, height, expected_device, expected_orientation, expected_touch in matrix:
        device, orientation, touch = classify(width, height)
        assert device == expected_device, (name, device, expected_device)
        assert orientation == expected_orientation, (name, orientation, expected_orientation)
        assert touch == expected_touch, (name, touch, expected_touch)

    for theme in ('light', 'dark', 'OLED'):
        assert repr(theme) in THEME_SRC or ("'" + theme + "'") in THEME_SRC

    player = SKIN_API['player_contract']
    assert player['owner'] == 'Infinity'
    assert player['replaceable_by_skin'] is False

    # Contract surfaces used across Home/widgets/menus/Add-ons/ZIP/settings/dialogs/power/weather/
    # notifications/player are intentionally global Window(Home) properties, not screen-specific state.
    print('Infinity Skin Theme Contract static + representative state matrix PASS')
    print('Real-device visual gate still required for fold/unfold, cutouts, player OSD and Kodi screens.')


if __name__ == '__main__':
    main()
