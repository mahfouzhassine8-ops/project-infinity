# SPDX-License-Identifier: GPL-2.0-or-later
from __future__ import annotations


def _norm(value: str) -> str:
    return (value or '').strip().lower().replace('_', '-').replace(' ', '-')


def _num(value: str):
    try:
        return float(str(value).strip())
    except Exception:
        return None


def resolve_effective_view_mode(
    selected: str,
    layout: str = '',
    device: str = '',
    orientation: str = '',
    width_dp: str = '',
    height_dp: str = '',
    screen_w: str = '',
    screen_h: str = '',
):
    """Return (effective_mode, reason) for Infinity's locked adaptive Auto contract.

    Manual Cinema/Compact/Two-Pane are hard overrides. Auto follows the device/layout
    contract used by the accepted C30.5/C34 runtime integration:
      cover/front or compact -> compact
      TV or expanded landscape -> cinema
      expanded portrait/square -> twopane
      otherwise -> balanced auto

    The dimension fallback is deliberately conservative and exists only for builds that
    publish incomplete/renamed native facts during fold/rotation transitions.
    """
    selected = _norm(selected)
    if selected == 'normal':
        selected = 'auto'
    if selected in ('cinema', 'compact', 'twopane'):
        return selected, 'manual-' + selected
    if selected != 'auto':
        selected = 'auto'

    layout = _norm(layout)
    device = _norm(device)
    orientation = _norm(orientation)

    compact_layouts = {'compact', 'narrow', 'cover', 'front', 'phone', 'handset'}
    expanded_layouts = {'expanded', 'inner', 'large', 'tablet', 'wide', 'fold-inner'}
    cover_devices = {
        'cover/front', 'front/cover', 'cover', 'front', 'cover-front', 'front-cover',
        'fold-cover', 'outer', 'outer-screen', 'phone', 'handset'
    }
    tv_devices = {'tv', 'television', 'android-tv'}

    if layout in compact_layouts or device in cover_devices:
        return 'compact', 'auto-cover-or-compact'
    if device in tv_devices:
        return 'cinema', 'auto-tv'
    if layout in expanded_layouts:
        if orientation == 'landscape':
            return 'cinema', 'auto-expanded-landscape'
        if orientation in ('portrait', 'square'):
            return 'twopane', 'auto-expanded-' + orientation

    # Conservative fallback for newer native/property vocabularies. Prefer dp facts,
    # then Kodi's actual screen dimensions. This keeps Fold cover/inner behavior stable
    # if device/layout strings are temporarily unknown during a transition.
    w = _num(width_dp)
    h = _num(height_dp)
    source = 'dp'
    if not w or not h:
        w = _num(screen_w)
        h = _num(screen_h)
        source = 'screen'
    if w and h and w > 0 and h > 0:
        small = min(w, h)
        large = max(w, h)
        ratio = large / small
        if orientation == 'landscape' and small >= 1400:
            return 'cinema', 'auto-' + source + '-inner-landscape'
        if orientation in ('portrait', 'square') and small >= 1400 and ratio < 1.55:
            return 'twopane', 'auto-' + source + '-inner-' + orientation
        if h > w and (ratio >= 1.55 or small < 1400):
            return 'compact', 'auto-' + source + '-narrow-portrait'
        if w > h and ratio >= 1.45:
            return 'cinema', 'auto-' + source + '-wide-landscape'

    return 'auto', 'auto-balanced-fallback'
