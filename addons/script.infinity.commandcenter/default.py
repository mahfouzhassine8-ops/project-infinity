# SPDX-License-Identifier: GPL-2.0-or-later
from __future__ import annotations

import xbmc
import xbmcaddon
import xbmcgui

from common import (addon_profile, addon_set_setting, create_restore_point, disable_addon,
                    list_restore_points, read_json, restore_point)

TITLE = 'Infinity Command Center'


def notify(text):
    xbmcgui.Dialog().notification('Infinity', text, xbmcgui.NOTIFICATION_INFO, 3500)


def open_health_center():
    try:
        xbmcaddon.Addon('script.infinity.support')
        xbmc.executebuiltin('RunAddon(script.infinity.support)')
    except Exception:
        xbmcgui.Dialog().ok(TITLE, 'Infinity Health Center is not installed.')


def performance_mode():
    if addon_set_setting('service.infinity.refresh', 'mode', 'performance'):
        notify('Performance Mode enabled')
    else:
        xbmcgui.Dialog().ok(TITLE, 'Infinity Refresh service is unavailable.')


def auto_refresh():
    if addon_set_setting('service.infinity.refresh', 'mode', 'auto'):
        notify('Adaptive refresh restored')
    else:
        xbmcgui.Dialog().ok(TITLE, 'Infinity Refresh service is unavailable.')


def safe_mode():
    if addon_set_setting('service.infinity.compat', 'compat_mode', 'safe'):
        notify('Infinity Safe Mode enabled')
    else:
        xbmcgui.Dialog().ok(TITLE, 'Infinity Compatibility Guard is unavailable.')


def normal_mode():
    if addon_set_setting('service.infinity.compat', 'compat_mode', 'auto'):
        notify('Infinity compatibility returned to Auto')
    else:
        xbmcgui.Dialog().ok(TITLE, 'Infinity Compatibility Guard is unavailable.')


def restore_menu():
    points = list_restore_points()
    if not points:
        xbmcgui.Dialog().ok(TITLE, 'No Infinity restore points exist yet.')
        return
    labels = [path.name.replace('Infinity-Restore-', '').replace('.zip', '') for path in points]
    index = xbmcgui.Dialog().select('Restore Point', labels)
    if index < 0:
        return
    chosen = points[index]
    if not xbmcgui.Dialog().yesno(
        TITLE,
        'Restore this configuration snapshot?',
        chosen.name,
        'A safety snapshot of the current setup will be created first.'
    ):
        return
    ok, message = restore_point(chosen)
    xbmcgui.Dialog().ok(TITLE, message)
    if ok and xbmcgui.Dialog().yesno(TITLE, 'Reload the skin now to apply restored UI settings?'):
        xbmc.executebuiltin('ReloadSkin()')


def quarantine_menu():
    state = read_json(addon_profile() / 'guardian-state.json', {})
    suspects = state.get('suspects', [])
    if not suspects:
        xbmcgui.Dialog().ok(
            TITLE,
            'No recently changed add-ons are currently correlated with an unclean Infinity start.',
            'Crash Quarantine never treats correlation as proof of cause.'
        )
        return
    labels = [item.get('name') or item.get('addon_id', 'Unknown') for item in suspects]
    index = xbmcgui.Dialog().select('Crash Quarantine — correlated changes', labels)
    if index < 0:
        return
    item = suspects[index]
    addon_id = item.get('addon_id', '')
    if not addon_id:
        return
    detail = 'Modified ' + str(item.get('minutes_before_start', '?')) + ' min before the unclean start.'
    if xbmcgui.Dialog().yesno(
        'Disable suspect add-on?',
        addon_id,
        detail,
        'This is a correlation only. You can re-enable it later.'
    ):
        if disable_addon(addon_id):
            notify('Disabled ' + addon_id)
        else:
            xbmcgui.Dialog().ok(TITLE, 'Kodi could not disable ' + addon_id + '.')


def system_info():
    home = xbmcgui.Window(10000)
    lines = [
        'Theme: ' + (home.getProperty('Infinity.Theme') or '?'),
        'Theme revision: ' + (home.getProperty('Infinity.ThemeRevision') or '?'),
        'Device: ' + (home.getProperty('Infinity.DeviceMode') or '?'),
        'Orientation: ' + (home.getProperty('Infinity.Orientation') or '?'),
        'Window: ' + (home.getProperty('Infinity.WindowWidth') or '?') + ' × ' + (home.getProperty('Infinity.WindowHeight') or '?'),
        'Layout: ' + (home.getProperty('Infinity.Layout') or '?'),
        'Touch: ' + (home.getProperty('Infinity.TouchClass') or '?'),
        'Motion: ' + (home.getProperty('Infinity.MotionPolicy') or '?'),
        'Refresh: ' + (home.getProperty('Infinity.RefreshPolicy') or '?'),
        'Power: ' + (home.getProperty('Infinity.PowerPolicy') or '?'),
    ]
    xbmcgui.Dialog().textviewer('Infinity Runtime State', '\n'.join(lines), usemono=True)


def main():
    items = [
        'Create Restore Point',
        'Restore Working Setup',
        'Crash Quarantine',
        'Performance Mode',
        'Adaptive Refresh',
        'Infinity Safe Mode',
        'Compatibility: Auto',
        'Health Center',
        'Runtime / Skin Inspector',
        'Reload Skin',
        'Settings',
    ]
    while True:
        choice = xbmcgui.Dialog().select(TITLE, items)
        if choice < 0:
            return
        if choice == 0:
            try:
                point = create_restore_point('manual')
                notify('Restore point saved: ' + point.name)
            except Exception as error:
                xbmcgui.Dialog().ok(TITLE, 'Could not create restore point: ' + type(error).__name__)
        elif choice == 1:
            restore_menu()
        elif choice == 2:
            quarantine_menu()
        elif choice == 3:
            performance_mode()
        elif choice == 4:
            auto_refresh()
        elif choice == 5:
            safe_mode()
        elif choice == 6:
            normal_mode()
        elif choice == 7:
            open_health_center()
        elif choice == 8:
            system_info()
        elif choice == 9:
            xbmc.executebuiltin('ReloadSkin()')
        elif choice == 10:
            xbmc.executebuiltin('Addon.OpenSettings(script.infinity.commandcenter)')


if __name__ == '__main__':
    main()
