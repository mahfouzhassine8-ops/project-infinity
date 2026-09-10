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
STABLE_SECONDS = 120
WINDOW_SECONDS = 15 * 60


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


def addon_int(addon, key, default):
    try:
        value = addon.getSetting(key)
        return int(value) if value != '' else default
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
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    tmp.replace(path)


def register_start(profile: Path, addon):
    """Track repeated unclean service starts without pretending they are proven native crashes."""
    marker = profile / 'startup-marker.json'
    history = profile / 'startup-history.json'
    now = int(time.time())
    data = _read_json(history, {'unclean_starts': [], 'auto_safe_activations': 0})
    starts = [int(x) for x in data.get('unclean_starts', []) if now - int(x) <= WINDOW_SECONDS]

    if marker.exists():
        prior = _read_json(marker, {})
        prior_ts = int(prior.get('timestamp', now))
        if now - prior_ts <= WINDOW_SECONDS:
            starts.append(now)

    data['unclean_starts'] = starts[-10:]
    data['last_start'] = now
    _atomic_json(history, data)
    _atomic_json(marker, {'timestamp': now, 'hook_api': HOOK_API})

    threshold = max(2, min(5, addon_int(addon, 'safe_mode_threshold', 3)))
    if addon_bool(addon, 'auto_safe_mode', True) and len(starts) >= threshold:
        if addon_value(addon, 'compat_mode', 'auto').strip().lower() != 'safe':
            addon.setSetting('compat_mode', 'safe')
            data['auto_safe_activations'] = int(data.get('auto_safe_activations', 0)) + 1
            data['last_auto_safe'] = now
            _atomic_json(history, data)
            log('Automatic Safe Mode activated after repeated unclean starts', xbmc.LOGWARNING)
        return True, len(starts), threshold
    return False, len(starts), threshold


def mark_stable(profile: Path):
    marker = profile / 'startup-marker.json'
    history = profile / 'startup-history.json'
    data = _read_json(history, {'unclean_starts': []})
    data['unclean_starts'] = []
    data['last_stable'] = int(time.time())
    _atomic_json(history, data)
    try:
        marker.unlink()
    except FileNotFoundError:
        pass


def write_state(profile: Path, addon, mode: str, status: str, extra=None):
    if not addon_bool(addon, 'health_breadcrumbs', True):
        return
    history = _read_json(profile / 'startup-history.json', {})
    data = {
        'schema': 2,
        'hook_api': HOOK_API,
        'infinity_release': '1.0.8 Candidate 1',
        'service': 'service.infinity.compat',
        'mode': mode,
        'status': status,
        'active_skin': xbmc.getSkinDir(),
        'protect_player_ui': addon_bool(addon, 'protect_player_ui', True),
        'follow_infinity_theme': addon_bool(addon, 'follow_infinity_theme', True),
        'allow_system_font': addon_bool(addon, 'allow_system_font', True),
        'auto_safe_mode': addon_bool(addon, 'auto_safe_mode', True),
        'unclean_starts_recent': len(history.get('unclean_starts', [])),
        'auto_safe_activations': int(history.get('auto_safe_activations', 0)),
        'timestamp': int(time.time()),
    }
    if extra:
        data.update(extra)
    _atomic_json(profile / 'health-state.json', data)


def apply_guard(addon_root: Path, profile: Path, backup_root: Path, addon):
    mode = addon_value(addon, 'compat_mode', 'auto').strip().lower()
    if mode not in ('auto', 'protected', 'system', 'safe'):
        mode = 'auto'

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
    started = time.monotonic()
    stable_marked = False
    auto_safe, count, threshold = register_start(profile, addon)
    log('Infinity Hook API ' + HOOK_API + ' compatibility service started')
    write_state(profile, addon, addon_value(addon, 'compat_mode', 'auto'), 'started', {
        'auto_safe_triggered_this_start': auto_safe,
        'unclean_start_count': count,
        'safe_mode_threshold': threshold,
    })
    last = 0.0
    while not monitor.abortRequested():
        now = time.monotonic()
        if not stable_marked and now - started >= STABLE_SECONDS:
            mark_stable(profile)
            stable_marked = True
            write_state(profile, addon, addon_value(addon, 'compat_mode', 'auto'), 'stable')
        if now - last >= 10.0:
            apply_guard(addon_root, profile, backup_root, addon)
            last = now
        if monitor.waitForAbort(1.0):
            break

    # A normal Kodi/service shutdown should not count as an unclean start next time.
    try:
        (profile / 'startup-marker.json').unlink()
    except FileNotFoundError:
        pass
    write_state(profile, addon, addon_value(addon, 'compat_mode', 'auto'), 'stopped_cleanly')


if __name__ == '__main__':
    main()
