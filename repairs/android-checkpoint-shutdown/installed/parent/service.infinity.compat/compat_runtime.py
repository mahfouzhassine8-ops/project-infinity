# SPDX-License-Identifier: GPL-2.0-or-later
from __future__ import annotations
import xbmc
import xbmcaddon
import xbmcgui

SUPPORTED_SKINS = ('skin.infinity.diggz', 'skin.infinity')
PRIMARY_SKIN_ID = 'skin.infinity.diggz'
API_VERSION = '0.8.1'

def publish_runtime_status():
    home = xbmcgui.Window(10000)
    active = xbmc.getSkinDir()
    addon = xbmcaddon.Addon()
    mode = (addon.getSetting('compat_mode') or 'auto').strip().lower()
    ready = active in SUPPORTED_SKINS
    target = active if ready else PRIMARY_SKIN_ID
    values = {
        'Infinity.CompatAPI': API_VERSION,
        'Infinity.CompatTargetSkin': target,
        'Infinity.CompatSupportedSkins': ','.join(SUPPORTED_SKINS),
        'Infinity.CompatMode': mode,
        'Infinity.CompatServiceReady': 'true',
        'Infinity.CompatStatus': 'ready' if ready else 'standby',
        'Infinity.SkinAPI': '1.1',
        'Infinity.SkinOwner': active,
    }
    for key, value in values.items():
        try: home.setProperty(key, str(value))
        except Exception: pass
    return ready
