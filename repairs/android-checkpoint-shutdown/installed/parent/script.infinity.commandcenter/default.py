# SPDX-License-Identifier: GPL-2.0-or-later
from __future__ import annotations

from pathlib import Path
import json
import sys
import time

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

from common import (addon, addon_profile, addon_set_setting, create_restore_point, disable_addon,
                    jsonrpc, list_restore_points, read_json, restore_point, mark_known_good,
                    restore_known_good, self_heal_ui, ui_health, refresh_runtime_state,
                    skin_baseline_integrity)
from view_mode import resolve_effective_view_mode

TITLE = 'Infinity Command Center'
ADDON = xbmcaddon.Addon()
ICON = xbmcvfs.translatePath(ADDON.getAddonInfo('icon')) if ADDON.getAddonInfo('icon') else xbmcgui.NOTIFICATION_INFO


def notify(text):
    xbmcgui.Dialog().notification('Infinity', text, ICON, 3500)




def _read_refresh_state() -> tuple[str, str]:
    try:
        refresh = xbmcaddon.Addon('service.infinity.refresh')
        mode = (refresh.getSetting('mode') or 'auto').strip().lower()
        cap = (refresh.getSetting('max_hz') or 'auto').strip().lower()
    except Exception:
        return 'auto', 'auto'
    if mode not in ('auto', 'performance', 'balanced', 'system', 'off'):
        mode = 'auto'
    if cap not in ('auto', '60', '90', '120', 'highest'):
        cap = 'auto'
    if mode == 'performance':
        cap = 'highest'
    elif mode == 'balanced' and cap in ('auto', 'highest'):
        cap = '90'
    return mode, cap


def _publish_refresh_state(mode: str | None = None, cap: str | None = None) -> tuple[str, str]:
    actual_mode, actual_cap = _read_refresh_state()
    if mode is not None and actual_mode != mode:
        xbmc.log('[InfinityCommandCenter] refresh readback mismatch: wanted mode=' + mode + ' got=' + actual_mode, xbmc.LOGWARNING)
    if cap is not None and actual_cap != cap:
        xbmc.log('[InfinityCommandCenter] refresh readback mismatch: wanted cap=' + cap + ' got=' + actual_cap, xbmc.LOGWARNING)
    home = xbmcgui.Window(10000)
    home.setProperty('Infinity.RefreshUserMode', actual_mode)
    home.setProperty('Infinity.RefreshMaxHz', actual_cap)
    home.setProperty('Infinity.RefreshPending', 'false')
    home.setProperty('Infinity.RefreshSelectionConfirmed', 'true')
    xbmc.executebuiltin('Skin.SetString(Infinity.PerformanceMode,' + actual_mode + ')')
    xbmc.executebuiltin('Skin.SetString(Infinity.RefreshCap,' + actual_cap + ')')
    return actual_mode, actual_cap


def set_refresh_mode(mode: str, quiet: bool = True) -> bool:
    mode = (mode or '').strip().lower()
    presets = {
        'auto': ('auto', 'auto'),
        'performance': ('performance', 'highest'),
        'balanced': ('balanced', '90'),
        'system': ('system', 'auto'),
    }
    if mode not in presets:
        return False
    real_mode, cap = presets[mode]
    home = xbmcgui.Window(10000)
    home.setProperty('Infinity.RefreshPending', 'true')
    ok1 = addon_set_setting('service.infinity.refresh', 'mode', real_mode)
    ok2 = addon_set_setting('service.infinity.refresh', 'max_hz', cap)
    if ok1 and ok2:
        xbmc.sleep(80)
        actual_mode, actual_cap = _publish_refresh_state(real_mode, cap)
        confirmed = actual_mode == real_mode and actual_cap == cap
        home.setProperty('Infinity.RefreshSelectionConfirmed', 'true' if confirmed else 'false')
        if confirmed:
            if not quiet:
                notify('Performance mode: ' + mode.title())
            return True
    home.setProperty('Infinity.RefreshPending', 'false')
    home.setProperty('Infinity.RefreshSelectionConfirmed', 'false')
    if not quiet:
        xbmcgui.Dialog().ok(TITLE, 'Infinity Refresh service did not confirm the requested mode.')
    return False


def set_refresh_cap(cap: str, quiet: bool = True) -> bool:
    cap = (cap or '').strip().lower()
    if cap not in ('auto', '60', '90', '120', 'highest'):
        return False
    home = xbmcgui.Window(10000)
    home.setProperty('Infinity.RefreshPending', 'true')
    ok1 = addon_set_setting('service.infinity.refresh', 'mode', 'auto')
    ok2 = addon_set_setting('service.infinity.refresh', 'max_hz', cap)
    if ok1 and ok2:
        xbmc.sleep(80)
        actual_mode, actual_cap = _publish_refresh_state('auto', cap)
        confirmed = actual_mode == 'auto' and actual_cap == cap
        home.setProperty('Infinity.RefreshSelectionConfirmed', 'true' if confirmed else 'false')
        if confirmed:
            if not quiet:
                notify('Refresh cap: ' + ('Highest' if cap == 'highest' else cap.upper()))
            return True
    home.setProperty('Infinity.RefreshPending', 'false')
    home.setProperty('Infinity.RefreshSelectionConfirmed', 'false')
    if not quiet:
        xbmcgui.Dialog().ok(TITLE, 'Infinity Refresh service did not confirm the requested cap.')
    return False



def runtime_sync(quiet: bool = False):
    actual_mode, actual_cap = _publish_refresh_state()
    try:
        snap = refresh_runtime_state()
        runtime = snap.get('runtime', {})
        home = xbmcgui.Window(10000)
        # Service normally owns the richer runtime publication; direct sync makes the
        # most important proof visible immediately if the service is still starting.
        for key, prop in (
            ('requested_hz', 'Infinity.RefreshRequestedHz'),
            ('active_hz', 'Infinity.RefreshActiveHz'),
            ('status', 'Infinity.RefreshStatus'),
            ('granted', 'Infinity.RefreshGranted'),
            ('battery_saver', 'Infinity.RefreshBatterySaver'),
            ('thermal_limited', 'Infinity.RefreshThermalLimited'),
            ('hook_active', 'Infinity.RefreshHookActive'),
        ):
            if key in runtime:
                home.setProperty(prop, runtime.get(key, ''))
        if not quiet:
            status = runtime.get('status') or 'runtime proof pending'
            active = runtime.get('active_hz') or '—'
            notify(actual_mode.title() + ' • ' + active + ' Hz • ' + status)
    except Exception:
        if not quiet:
            notify(actual_mode.title() + ' • refresh owner synchronized')


def baseline_check(quiet: bool = False):
    state = skin_baseline_integrity()
    home = xbmcgui.Window(10000)
    home.setProperty('Infinity.BaselineIntegrityStatus', state.get('status', 'unavailable'))
    home.setProperty('Infinity.BaselineCheckedFiles', str(state.get('checked', 0)))
    home.setProperty('Infinity.BaselineMismatchCount', str(len(state.get('mismatches', []))))
    home.setProperty('Infinity.BaselineMismatchFiles', ', '.join(state.get('mismatches', [])[:8]))
    if not quiet:
        if state.get('status') == 'ok':
            notify('Locked UI baseline verified')
        elif state.get('status') == 'mismatch':
            xbmcgui.Dialog().ok(TITLE, 'Protected UI mismatch detected.\n\n' + '\n'.join(state.get('mismatches', [])[:8]) + '\n\nNo files were changed automatically.')
        else:
            xbmcgui.Dialog().ok(TITLE, 'Protected baseline manifest is unavailable. No files were changed.')


def open_support_exporter():
    try:
        xbmcaddon.Addon('script.infinity.support')
        xbmc.executebuiltin('RunAddon(script.infinity.support)')
    except Exception:
        xbmcgui.Dialog().ok(TITLE, 'Infinity Support Exporter is not installed.')

def direct_command(argv) -> bool:
    if len(argv) < 2:
        return False
    action = argv[1].strip().lower()
    value = argv[2].strip().lower() if len(argv) >= 3 else ''
    if action in ('palette', 'palette-search', 'palette-run', 'resume-hub',
                  'restore-session', 'retry-playback', 'ambient-home', 'forget-source', 'remove-resume'):
        return experience_command(action, value)
    if action == 'refresh-mode':
        set_refresh_mode(value, quiet=True); return True
    if action == 'refresh-cap':
        set_refresh_cap(value, quiet=True); return True
    if action == 'view-mode':
        requested = (value or '').strip().lower()
        if requested in ('wide', 'wide-pane'):
            requested = 'twopane'
        if requested in ('follow', 'adaptive'):
            requested = 'auto'
        if requested not in ('normal', 'auto', 'cinema', 'compact', 'twopane'):
            return True

        home = xbmcgui.Window(10000)
        # H3 contract: Normal is a real presentation state, not an alias for AUTO.
        # HomeView stays 'auto' only as a legacy compatibility value; VisualMode and
        # EffectiveViewMode carry the explicit Normal intent. AUTO remains adaptive.
        if requested == 'normal':
            visual = 'normal'
            mode = 'auto'
            effective, reason = 'normal', 'explicit-normal-local'
        elif requested == 'auto':
            visual = 'follow'
            mode = 'auto'
            device = (home.getProperty('Infinity.NativeDeviceMode') or home.getProperty('Infinity.DeviceMode') or '').strip().lower()
            layout = (home.getProperty('Infinity.NativeLayout') or home.getProperty('Infinity.Layout') or '').strip().lower()
            orientation = (home.getProperty('Infinity.NativeOrientation') or home.getProperty('Infinity.Orientation') or '').strip().lower()
            width_dp = home.getProperty('Infinity.NativeWidthDp') or ''
            height_dp = home.getProperty('Infinity.NativeHeightDp') or ''
            screen_w = str(xbmc.getInfoLabel('System.ScreenWidth') or '').strip()
            screen_h = str(xbmc.getInfoLabel('System.ScreenHeight') or '').strip()
            effective, reason = resolve_effective_view_mode(
                mode, layout, device, orientation, width_dp, height_dp, screen_w, screen_h
            )
        else:
            visual = requested
            mode = requested
            effective, reason = requested, 'manual-' + requested

        xbmc.executebuiltin('Skin.SetString(Infinity.VisualMode,%s)' % visual)
        xbmc.executebuiltin('Skin.SetString(Infinity.HomeView,%s)' % mode)

        # Retire H1/H2's Normal-return latch. It is precisely what conflated Normal
        # with literal AUTO and caused the reported mode-switch lockout.
        for prop in (
            'Infinity.ViewMode.NormalReturnLatch',
            'Infinity.ViewMode.NormalReturnReason',
            'Infinity.ViewMode.NormalReturnBaselineCaptured',
            'Infinity.ViewMode.NormalReturnBaselineDevice',
            'Infinity.ViewMode.NormalReturnBaselineLayout',
            'Infinity.ViewMode.NormalReturnBaselineOrientation',
            'Infinity.ViewMode.NormalReturnBaselineWidthDp',
            'Infinity.ViewMode.NormalReturnBaselineHeightDp',
            'Infinity.ViewMode.NormalReturnBaselineScreenWidth',
            'Infinity.ViewMode.NormalReturnBaselineScreenHeight',
        ):
            home.clearProperty(prop)

        home.setProperty('Infinity.ViewMode.Requested', requested)
        home.setProperty('Infinity.ViewMode.Effective', effective)
        home.setProperty('Infinity.EffectiveViewMode', effective)
        home.setProperty('Infinity.EffectivePaneMode', 'two-pane' if effective == 'twopane' else 'single-pane')
        home.setProperty('Infinity.ViewMode.PolicyReason', reason)
        return True
    if action == 'runtime-sync':
        runtime_sync(quiet=(value == 'true')); return True
    if action == 'baseline-check':
        baseline_check(quiet=(value == 'true')); return True
    commands = {
        'mark-good': mark_good,
        'restore-good': restore_good,
        'create-restore': lambda: notify('Restore point saved: ' + create_restore_point('manual').name),
        'restore-menu': restore_menu,
        'self-heal': self_heal,
        'protected-zip': prepare_zip_install,
        'crash-recovery': quarantine_menu,
        'performance': performance_mode,
        'adaptive-refresh': auto_refresh,
        'safe-mode': safe_mode,
        'compat-auto': normal_mode,
        'health-center': open_health_center,
        'runtime': system_info,
        'support-exporter': open_support_exporter,
        'reload-skin': lambda: xbmc.executebuiltin('ReloadSkin()'),
        'settings': lambda: xbmc.executebuiltin('Addon.OpenSettings(script.infinity.commandcenter)'),
    }
    fn = commands.get(action)
    if fn is None:
        return False
    try:
        fn()
    except Exception as error:
        xbmcgui.Dialog().ok(TITLE, 'Command failed: ' + type(error).__name__)
    return True


def experience_command(action, value=''):
    from experience import COMMANDS
    home = xbmcgui.Window(10000)
    if action == 'palette':
        home.setProperty('Infinity.Palette.Query', '')
        home.setProperty('Infinity.Palette.Revision', str(time.time()))
        xbmc.executebuiltin('ActivateWindow(1190)')
    elif action == 'palette-search':
        query = xbmcgui.Dialog().input('Search Infinity commands', home.getProperty('Infinity.Palette.Query'))
        home.setProperty('Infinity.Palette.Query', query.strip()[:120])
        home.setProperty('Infinity.Palette.Revision', str(time.time()))
        xbmc.executebuiltin('Container.Refresh')
    elif action == 'palette-run':
        if value not in {row[0] for row in COMMANDS}:
            return True
        xbmc.executebuiltin('Dialog.Close(1190)')
        if value.startswith('view-'):
            direct_command(['default.py', 'view-mode', value[5:]])
        else:
            direct_command(['default.py', value])
    elif action == 'resume-hub':
        xbmc.executebuiltin('Dialog.Close(1190)')
        xbmc.executebuiltin('ActivateWindow(Videos,plugin://script.infinity.commandcenter/?action=resume,return)')
    elif action == 'ambient-home':
        modes = ('off', 'subtle', 'immersive')
        current = addon().getSetting('ambient_home') or 'subtle'
        home.setProperty('Infinity.Select.Compact', 'true')
        try:
            choice = xbmcgui.Dialog().select('Infinity Ambient Home', ['Off', 'Subtle', 'Immersive'],
                                             preselect=modes.index(current) if current in modes else 1)
        finally:
            home.clearProperty('Infinity.Select.Compact')
        if choice >= 0:
            addon().setSetting('ambient_home', modes[choice])
            home.setProperty('Infinity.AmbientHome.Mode', modes[choice])
    elif action == 'remove-resume':
        import re
        if re.fullmatch(r'[a-f0-9]{64}', value):
            home.setProperty('Infinity.Experience.Command', 'remove:' + value)
    else:
        if action == 'retry-playback' and home.getProperty('Infinity.Recovery.Available') != 'true':
            notify('No recoverable playback failure is waiting.')
        elif action == 'forget-source' and home.getProperty('Infinity.SourceMemory.Status') != 'remembered':
            notify('No current title source preference is selected.')
        else:
            home.setProperty('Infinity.Experience.Command', action)
    return True

def open_health_center():
    for addon_id in ('script.kodihealthcenter','script.infinity.support'):
        try:
            xbmcaddon.Addon(addon_id)
            xbmc.executebuiltin('RunAddon(' + addon_id + ')')
            return
        except Exception:
            pass
    xbmcgui.Dialog().ok(TITLE, 'Kodi Health Center is not installed.')


def prepare_zip_install():
    try:
        point = create_restore_point('pre-zip-install')
    except Exception as error:
        xbmcgui.Dialog().ok(TITLE, 'Could not create the pre-install restore point: ' + type(error).__name__)
        return
    notify('Pre-install restore point created')
    xbmcgui.Dialog().ok(
        'Protected ZIP Install',
        'Safety snapshot created:\n\n' + point.name +
        '\n\nKodi will open the Add-ons browser. Choose Install from zip file normally. Health Center 2.5 will record the add-on change after installation.'
    )
    xbmc.executebuiltin('ActivateWindow(AddonBrowser)')


def mark_good():
    if xbmc.getSkinDir() != 'skin.infinity.diggz':
        xbmcgui.Dialog().ok(TITLE, 'Switch to the Infinity skin before marking Last Known Good. Recovery can still be run later from another skin.')
        return
    try:
        point = mark_known_good()
        notify('Last Known Good saved')
        xbmcgui.Dialog().ok(TITLE, 'Current Infinity configuration and critical UI files are now marked Last Known Good.\n\n' + point.name)
    except Exception as error:
        xbmcgui.Dialog().ok(TITLE, 'Could not mark Last Known Good: ' + type(error).__name__)


def restore_good():
    if not xbmcgui.Dialog().yesno(TITLE, 'Restore the Last Known Good Infinity configuration?', 'A new safety snapshot will be made before the restore.'):
        return
    ok, message = restore_known_good()
    xbmcgui.Dialog().ok(TITLE, message)
    if ok and xbmcgui.Dialog().yesno(TITLE, 'Reload the skin now?'):
        xbmc.executebuiltin('ReloadSkin()')


def self_heal():
    state = ui_health()
    if state.get('healthy'):
        ok, message = self_heal_ui()
        xbmcgui.Dialog().ok('Infinity UI Self-Heal', message)
        return
    detail='\n'.join('• '+x for x in state.get('issues',[])[:8])
    if not xbmcgui.Dialog().yesno('Infinity UI Self-Heal','Critical UI validation found problems:\n\n'+detail+'\n\nRestore known-good critical UI files if available?'):
        return
    ok, message = self_heal_ui()
    xbmcgui.Dialog().ok('Infinity UI Self-Heal', message)
    if ok:
        xbmc.executebuiltin('ReloadSkin()')

def performance_mode():
    set_refresh_mode('performance', quiet=False)


def auto_refresh():
    set_refresh_mode('auto', quiet=False)


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
    labels = []
    for path in points:
        labels.append(path.name.replace('Infinity-Restore-', '').replace('.zip', ''))
    index = xbmcgui.Dialog().select('Restore Point', labels)
    if index < 0:
        return
    chosen = points[index]
    if not xbmcgui.Dialog().yesno(TITLE, 'Restore this configuration snapshot?', chosen.name,
                                  'A safety snapshot of the current setup will be created first.'):
        return
    ok, message = restore_point(chosen)
    xbmcgui.Dialog().ok(TITLE, message)
    if ok and xbmcgui.Dialog().yesno(TITLE, 'Reload the skin now to apply restored UI settings?'):
        xbmc.executebuiltin('ReloadSkin()')


def quarantine_menu():
    khc = Path(xbmcvfs.translatePath('special://profile/addon_data/script.kodihealthcenter/health-bridge.json'))
    bridge = read_json(khc, {})
    suspects = []
    source = 'Infinity fallback correlation'
    if isinstance(bridge, dict) and bridge.get('correlated_changes'):
        suspects = bridge.get('correlated_changes', [])
        source = 'Kodi Health Center ' + str(bridge.get('version',''))
    if not suspects:
        path = addon_profile() / 'guardian-state.json'
        state = read_json(path, {})
        suspects = state.get('suspects', [])
    if not suspects:
        xbmcgui.Dialog().ok(TITLE, 'No recently changed add-ons are currently correlated with an unclean Infinity start.', 'Correlation is never treated as proof of cause.')
        return
    labels = [item.get('name') or item.get('addon_id', 'Unknown') for item in suspects]
    index = xbmcgui.Dialog().select('Crash Recovery — ' + source, labels)
    if index < 0:
        return
    item = suspects[index]
    addon_id = item.get('addon_id', '')
    if not addon_id:
        return
    detail = 'Changed about ' + str(item.get('minutes_before_start', '?')) + ' min before the unclean start.'
    if xbmcgui.Dialog().yesno('Disable correlated add-on?', addon_id, detail, 'Timing evidence only. Kodi Health Center does not claim this caused the crash. You can re-enable it later.'):
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
        '',
        'Boot stage: ' + (home.getProperty('Infinity.BootStage') or '?'),
        'Widget scheduler: ' + (home.getProperty('Infinity.WidgetLoadPolicy') or '?'),
        'Primary widgets ready: ' + (home.getProperty('Infinity.WidgetPrimaryReady') or '?'),
        'Secondary widgets ready: ' + (home.getProperty('Infinity.WidgetSecondaryReady') or '?'),
        'High-refresh UI: ' + (home.getProperty('Infinity.HighRefreshUI') or '?'),
        'UI frame budget: ' + (home.getProperty('Infinity.UIFrameBudgetMs') or '?') + ' ms',
        'Startup watchdog: ' + (home.getProperty('Infinity.StartupWatchdog.Status') or '?'),
        'UI health: ' + (home.getProperty('Infinity.UIHealth.Status') or '?'),
        'UI health issues: ' + (home.getProperty('Infinity.UIHealth.IssueCount') or '0'),
        '',
        'Effective view: ' + (home.getProperty('Infinity.EffectiveViewMode') or '?'),
        'Effective display: ' + (home.getProperty('Infinity.RuntimeDisplayProfile') or '?'),
        'Refresh requested: ' + (home.getProperty('Infinity.RefreshRequestedLabel') or '?'),
        'Refresh active: ' + (home.getProperty('Infinity.RefreshActiveLabel') or '?'),
        'Refresh status: ' + (home.getProperty('Infinity.RefreshStatus') or '?'),
        'Refresh granted: ' + (home.getProperty('Infinity.RefreshGranted') or '?'),
        'Battery saver: ' + (home.getProperty('Infinity.RefreshBatterySaver') or '?'),
        'Thermal limited: ' + (home.getProperty('Infinity.RefreshThermalLimited') or '?'),
        'Motion user/effective: ' + (home.getProperty('Infinity.MotionModeUser') or '?') + ' / ' + (home.getProperty('Infinity.MotionModeEffective') or '?'),
        'Baseline integrity: ' + (home.getProperty('Infinity.BaselineIntegrityStatus') or '?') + ' (' + (home.getProperty('Infinity.BaselineCheckedFiles') or '0') + ' files)',
    ]
    xbmcgui.Dialog().textviewer('Infinity Runtime State', '\n'.join(lines), usemono=True)


def main():
    try:
        # Candidate 34 Change 01: do not probe one hard-coded resolution directory.
        # Kodi resolves window 1194 from the active skin/profile.
        if xbmc.getSkinDir() == 'skin.infinity.diggz':
            xbmc.executebuiltin('ActivateWindow(1194)')
            return
    except Exception:
        pass
    items = [
        'Mark Current Setup — Last Known Good',
        'Restore Last Known Good',
        'Create Restore Point',
        'Restore Point…',
        'Infinity UI Self-Heal',
        'Protected Install from ZIP',
        'Crash Recovery / Quarantine',
        'Performance Mode',
        'Adaptive Refresh',
        'Infinity Safe Mode',
        'Compatibility: Auto',
        'Kodi Health Center',
        'Runtime / Stability Inspector',
        'Reload Skin',
        'Settings',
    ]
    while True:
        choice = xbmcgui.Dialog().select(TITLE, items)
        if choice < 0:
            return
        if choice == 0: mark_good()
        elif choice == 1: restore_good()
        elif choice == 2:
            try:
                point = create_restore_point('manual'); notify('Restore point saved: ' + point.name)
            except Exception as error:
                xbmcgui.Dialog().ok(TITLE, 'Could not create restore point: ' + type(error).__name__)
        elif choice == 3: restore_menu()
        elif choice == 4: self_heal()
        elif choice == 5: prepare_zip_install()
        elif choice == 6: quarantine_menu()
        elif choice == 7: performance_mode()
        elif choice == 8: auto_refresh()
        elif choice == 9: safe_mode()
        elif choice == 10: normal_mode()
        elif choice == 11: open_health_center()
        elif choice == 12: system_info()
        elif choice == 13: xbmc.executebuiltin('ReloadSkin()')
        elif choice == 14: xbmc.executebuiltin('Addon.OpenSettings(script.infinity.commandcenter)')


if __name__ == '__main__':
    if not direct_command(sys.argv):
        main()
