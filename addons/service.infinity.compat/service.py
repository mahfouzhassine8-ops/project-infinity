"""Infinity/Diggz boundary service.

Diggz/Xenon keeps Home. This service only owns: VideoOSD, seek overlay, Infinity lock,
Infinity color theme selection, and an optional Infinity System fontset. It never edits
shortcuts, Home.xml, widgets, menus, sources, accounts or add-on settings.
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


def apply_guard(addon_root: Path, backup_root: Path):
    if xbmc.getSkinDir() != SKIN_ID:
        return
    try:
        skin = xbmcaddon.Addon(SKIN_ID)
        skin_root = Path(xbmcvfs.translatePath(skin.getAddonInfo('path')))
    except Exception as error:
        log('Cannot resolve Xenon path: ' + type(error).__name__, xbmc.LOGWARNING)
        return
    if not skin_root.is_dir():
        log('Xenon path is not writable/visible as a directory', xbmc.LOGWARNING)
        return

    try:
        result = ensure_player_files(skin_root, addon_root, backup_root)
        theme_changes = ensure_theme_files(skin_root, addon_root)
        font_changed = ensure_system_fontset(skin_root, backup_root)
        if result['changed']:
            log('Reasserted protected player files: ' + ', '.join(result['changed']))
        if theme_changes:
            log('Installed Infinity Xenon themes: ' + ', '.join(theme_changes))
        if font_changed:
            log('Added Infinity System fontset without selecting it automatically')
    except Exception as error:
        log('Guard file update failed: ' + type(error).__name__, xbmc.LOGERROR)
        return

    estuary_settings = Path(xbmcvfs.translatePath('special://profile/addon_data/skin.estuary/settings.xml'))
    policy = parse_estuary_policy(estuary_settings)
    system_theme = xbmc.getInfoLabel('Window(Home).Property(Infinity.SystemTheme)')
    wanted = resolve_theme(policy, system_theme)
    if wanted:
        current = get_setting('lookandfeel.skincolors')
        if current != wanted and set_setting('lookandfeel.skincolors', wanted):
            log('Applied Infinity theme policy to Xenon: ' + wanted)
            xbmc.executebuiltin('ReloadSkin()')


def main():
    monitor = xbmc.Monitor()
    addon_root = Path(xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('path')))
    profile = Path(xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('profile')))
    backup_root = profile / 'xenon-backup'
    last = 0.0
    while not monitor.abortRequested():
        now = time.monotonic()
        if now - last >= 10.0:
            apply_guard(addon_root, backup_root)
            last = now
        if monitor.waitForAbort(1.0):
            break


if __name__ == '__main__':
    main()
