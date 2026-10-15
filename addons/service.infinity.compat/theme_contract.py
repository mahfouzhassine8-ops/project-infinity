# SPDX-License-Identifier: GPL-2.0-or-later
"""Infinity Skin Theme Contract.

Native bridge v5 publishes raw Android theme facts as Infinity.NativeSystemTheme.
This service resolves user policy into the effective skin theme and publishes a complete
palette/state snapshot before advancing ThemeRevision.
"""
from __future__ import annotations

import json
from pathlib import Path
import time

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

TAG = '[InfinityThemeContract] '
THEME_CONTRACT = '1.1'

PALETTES = {
    'light': {
        'Background': 'FFF8FBFF',
        'Surface': 'FFF8FBFF',
        'SurfaceElevated': 'FFFFFFFF',
        'TextPrimary': 'FF111821',
        'TextSecondary': 'FF334252',
        'Border': 'FFAAB9C5',
        'Focus': 'FF0A8FFF',
        'Accent': 'FF0A8FFF',
        'Danger': 'FFD93025',
        'Scrim': '33000000',
    },
    'dark': {
        'Background': 'FF000000',
        'Surface': 'FF101820',
        'SurfaceElevated': 'FF18232E',
        'TextPrimary': 'FFF5F7FA',
        'TextSecondary': 'FF8FA5B8',
        'Border': 'FF303B46',
        'Focus': 'FF19BFFF',
        'Accent': 'FF0A8FFF',
        'Danger': 'FFFF5252',
        'Scrim': 'CC000000',
    },
    'OLED': {
        'Background': 'FF000000',
        'Surface': 'FF050505',
        'SurfaceElevated': 'FF101010',
        'TextPrimary': 'FFFFFFFF',
        'TextSecondary': 'FFB7C0C8',
        'Border': 'FF2A2A2A',
        'Focus': 'FF19BFFF',
        'Accent': 'FF0A8FFF',
        'Danger': 'FFFF5252',
        'Scrim': 'E6000000',
    },
}


def _home():
    return xbmcgui.Window(10000)


def _set(name: str, value) -> None:
    try:
        _home().setProperty(name, str(value))
    except Exception:
        pass


def _addon_value(addon, key, default):
    try:
        value = addon.getSetting(key)
        return value if value != '' else default
    except Exception:
        return default


def _addon_bool(addon, key, default=True):
    try:
        value = addon.getSetting(key)
        return default if value == '' else value.lower() == 'true'
    except Exception:
        return default


def _read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default


def _atomic_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name('.' + path.name + '.tmp')
    tmp.write_text(json.dumps(data, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)


def _bridge_version(home) -> int:
    try:
        return int(home.getProperty('Infinity.BridgeVersion') or '0')
    except Exception:
        return 0


def _native_system_theme(home) -> str:
    # Bridge v5 separates raw host truth from the effective skin output.
    if _bridge_version(home) >= 5:
        value = (home.getProperty('Infinity.NativeSystemTheme') or '').strip()
    else:
        value = (home.getProperty('Infinity.SystemTheme') or '').strip()
    if value.lower() == 'light':
        return 'light'
    if value.lower() == 'dark':
        return 'dark'
    if value.upper() == 'OLED':
        return 'OLED'
    return 'dark'


def _effective_theme(addon, home) -> str:
    policy = _addon_value(addon, 'theme_mode', 'system').strip()
    if policy == 'light':
        return 'light'
    if policy == 'dark':
        return 'dark'
    if policy.lower() == 'oled':
        return 'OLED'
    return _native_system_theme(home)


def _refresh_state():
    mode = 'auto'
    video_policy = 'match_video'
    respect_battery = True
    thermal = True
    override_battery = False
    try:
        refresh = xbmcaddon.Addon('service.infinity.refresh')
        mode = _addon_value(refresh, 'mode', 'auto').strip().lower()
        video_policy = _addon_value(refresh, 'video_policy', 'match_video').strip().lower()
        respect_battery = _addon_bool(refresh, 'respect_battery_saver', True)
        thermal = _addon_bool(refresh, 'thermal_protection', True)
        override_battery = _addon_bool(refresh, 'performance_override_battery', False)
    except Exception:
        pass

    if mode in ('performance', 'high_refresh'):
        refresh_policy = 'high-refresh'
    elif video_policy == 'match_video' and mode not in ('off', 'system'):
        refresh_policy = 'video-match'
    else:
        refresh_policy = 'normal'

    return mode, refresh_policy, respect_battery, thermal, override_battery


def _policies(addon):
    mode, refresh_policy, respect_battery, thermal, override_battery = _refresh_state()
    safe = _addon_value(addon, 'compat_mode', 'auto').strip().lower() == 'safe'

    if safe:
        motion = 'reduced'
    elif mode in ('performance', 'high_refresh'):
        motion = 'performance'
    else:
        motion = 'normal'

    if thermal and respect_battery and not override_battery:
        power = 'battery+thermal-protected'
    elif thermal:
        power = 'thermal-protected'
    elif respect_battery and not override_battery:
        power = 'battery-aware'
    else:
        power = 'unrestricted'
    return motion, refresh_policy, power


def _revision(profile: Path, signature: str) -> int:
    path = profile / 'theme-revision.json'
    data = _read_json(path, {'revision': 0, 'signature': ''})
    revision = int(data.get('revision', 0))
    if data.get('signature', '') != signature:
        revision += 1
        _atomic_json(path, {
            'revision': revision,
            'signature': signature,
            'timestamp': int(time.time()),
        })
    return revision


def publish(addon, profile: Path, force=False):
    home = _home()
    theme = _effective_theme(addon, home)
    palette = PALETTES[theme]
    motion, refresh_policy, power = _policies(addon)

    display_sig = home.getProperty('Infinity.DisplaySignature')
    signature = '|'.join([
        theme, motion, refresh_policy, power, display_sig,
        json.dumps(palette, sort_keys=True),
    ])
    revision = _revision(profile, signature)

    state_signature = str(revision) + '|' + signature
    if not force and home.getProperty('Infinity.ThemeContractSignature') == state_signature:
        return False

    _set('Infinity.ThemeReady', 'false')
    _set('Infinity.ThemeContract', THEME_CONTRACT)
    _set('Infinity.Theme', theme)
    # Backward-compatible effective output. Raw Android truth remains NativeSystemTheme.
    _set('Infinity.SystemTheme', theme)
    _set('Infinity.MotionPolicy', motion)
    _set('Infinity.RefreshPolicy', refresh_policy)
    _set('Infinity.PowerPolicy', power)
    for token, value in palette.items():
        _set('Infinity.Palette.' + token, value)

    # Commit markers are deliberately last so a new revision is a complete snapshot.
    _set('Infinity.ThemeContractSignature', state_signature)
    _set('Infinity.ThemeRevision', revision)
    _set('Infinity.ThemeReady', 'true')

    xbmc.log(
        TAG + 'theme=' + theme + ' revision=' + str(revision) +
        ' motion=' + motion + ' refresh=' + refresh_policy + ' power=' + power,
        xbmc.LOGINFO,
    )
    return True


class ThemeMonitor(xbmc.Monitor):
    def __init__(self, addon, profile):
        super().__init__()
        self.addon = addon
        self.profile = profile

    def onSettingsChanged(self):
        publish(self.addon, self.profile, force=True)

    def onNotification(self, sender, method, data):
        publish(self.addon, self.profile)

    def onScreensaverDeactivated(self):
        publish(self.addon, self.profile, force=True)

    def onDPMSDeactivated(self):
        publish(self.addon, self.profile, force=True)


if __name__ == '__main__':
    addon = xbmcaddon.Addon()
    profile = Path(xbmcvfs.translatePath(addon.getAddonInfo('profile')))
    monitor = ThemeMonitor(addon, profile)
    xbmc.log(TAG + 'Skin Theme Contract ' + THEME_CONTRACT + ' event service started', xbmc.LOGINFO)
    publish(addon, profile, force=True)
    monitor.waitForAbort()
