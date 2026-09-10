"""Infinity compatibility/capability service.

Kodi and third-party skins keep ownership of Home, widgets and navigation. Infinity owns
only explicitly protected capabilities such as player UI, theme bridging and diagnostics.
Routine policy changes live here so the native engine can remain stable.
"""
from pathlib import Path
import json
import time

import xbmc
import xbmcaddon
import xbmcvfs

from compat_runtime import (SKIN_ID, ensure_player_files, ensure_system_fontset,
                            ensure_theme_files, parse_estuary_policy, resolve_theme,
                            setting_rpc)

TAG = '[InfinityCompat] '
HOOK_API = '1.0'


def log(message, level=xbmc.LOGINFO):
    xbmc.log(TAG + message, level)


def get_setting(setting):
    try:
        reply = json.loads(xbmc.executeJSONRPC(setting_rpc('Settings.GetSettingValue', setting)))
        return reply.get('result', {}).get('value', '')
    except Exception:
        return ''


def set_setting(setting, value):
    try:
        reply = json.loads(xbmc.executeJSONRPC(setting_rpc('Settings.SetSettingValue', setting, value)))
        return 'error' not in reply
    except Exception:
        return False


def addon_value(addon, key, default):
    try:
        value = addon.getSetting(key)
        return value if value != '' else default
    except Exception:
        return default


def addon_bool(addon, key, default=True):
    try:
        value = addon.getSetting(key)
        if value == '':
            return default
        return value.lower() == 'true'
    except Exception:
        return default


def write_state(profile: Path, addon, mode: str, status: str, extra=None):
    if not addon_bool(addon, 'health_breadcrumbs', True):
        return
    data = {
        'schema': 1,
        'hook_api': HOOK_API,
        'infinity_release': '1.0.8 Candidate 1',
        'service': 'service.infinity.compat',
        'mode': mode,
        'status': status,
        'active_skin': xbmc.getSkinDir(),
        'protect_player_ui': addon_bool(addon, 'protect_player_ui', True),
        'follow_infinity_theme': addon_bool(addon, 'follow_infinity_theme', True),
        'allow_system_font': addon_bool(addon, 'allow_system_font', True),
        'timestamp': int(time.time()),
    }
    if extra:
        data.update(extra)
    profile.mkdir(parents=True, exist_ok=True)
    target = profile / 'health-state.json'
    tmp = profile / '.health-state.tmp'
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    tmp.replace(target)


def apply_guard(addon_root: Path, profile: Path, backup_root: Path, addon):
    mode = addon_value(addon, 'compat_mode', 'auto').strip().lower()
    if mode not in ('auto', 'protected', 'system', 'safe'):
        mode = 'auto'

    # System Default and Safe Mode deliberately make no skin-file changes.
    if mode in ('system', 'safe'):
        write_state(profile, addon, mode, 'yielding_to_system')
        return

    if xbmc.getSkinDir() != SKIN_ID:
        write_state(profile, addon, mode, 'inactive_skin')
        return

    try:
        skin = xbmcaddon.Addon(SKIN_ID)
        skin_root = Path(xbmcvfs.translatePath(skin.getAddonInfo('path')))
    except Exception as error:
        log('Cannot resolve Xenon path: ' + type(error).__name__, xbmc.LOGWARNING)
        write_state(profile, addon, mode, 'skin_resolution_failed', {'error': type(error).__name__})
        return
    if not skin_root.is_dir():
        log('Xenon path is not writable/visible as a directory', xbmc.LOGWARNING)
        write_state(profile, addon, mode, 'skin_path_unavailable')
        return

    changes = []
    try:
        if addon_bool(addon, 'protect_player_ui', True):
            result = ensure_player_files(skin_root, addon_root, backup_root)
            if result['changed']:
                changes.extend(result['changed'])
                log('Reasserted protected player files: ' + ', '.join(result['changed']))

        if addon_bool(addon, 'follow_infinity_theme', True):
            theme_changes = ensure_theme_files(skin_root, addon_root)
            if theme_changes:
                changes.extend(theme_changes)
                log('Installed Infinity Xenon themes: ' + ', '.join(theme_changes))

        if addon_bool(addon, 'allow_system_font', True):
            if ensure_system_fontset(skin_root, backup_root):
                changes.append('Infinity System fontset')
                log('Added Infinity System fontset without selecting it automatically')
    except Exception as error:
        log('Guard file update failed: ' + type(error).__name__, xbmc.LOGERROR)
        write_state(profile, addon, mode, 'guard_update_failed', {'error': type(error).__name__})
        return

    if addon_bool(addon, 'follow_infinity_theme', True):
        estuary_settings = Path(xbmcvfs.translatePath('special://profile/addon_data/skin.estuary/settings.xml'))
        policy = parse_estuary_policy(estuary_settings)
        system_theme = xbmc.getInfoLabel('Window(Home).Property(Infinity.SystemTheme)')
        wanted = resolve_theme(policy, system_theme)
        if wanted:
            current = get_setting('lookandfeel.skincolors')
            if current != wanted and set_setting('lookandfeel.skincolors', wanted):
                changes.append('theme=' + wanted)
                log('Applied Infinity theme policy to Xenon: ' + wanted)
                xbmc.executebuiltin('ReloadSkin()')

    write_state(profile, addon, mode, 'active', {'changes': changes})


def main():
    monitor = xbmc.Monitor()
    addon = xbmcaddon.Addon()
    addon_root = Path(xbmcvfs.translatePath(addon.getAddonInfo('path')))
    profile = Path(xbmcvfs.translatePath(addon.getAddonInfo('profile')))
    backup_root = profile / 'xenon-backup'
    last = 0.0
    log('Infinity Hook API ' + HOOK_API + ' compatibility service started')
    while not monitor.abortRequested():
        now = time.monotonic()
        if now - last >= 10.0:
            apply_guard(addon_root, profile, backup_root, addon)
            last = now
        if monitor.waitForAbort(1.0):
            break


if __name__ == '__main__':
    main()
