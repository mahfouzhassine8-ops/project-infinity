"""Bounded native icon-surface observations for the unchanged signed431 APK.

Only normal Settings App Info, Home/All Apps, system uiMode and read-only shell
diagnostics are used. No settings action/icon is tapped; no package, alias,
component, database, permission or private application data is changed. Native
frames are evidence to inspect, never an inferred icon-rendering PASS.
"""
import argparse
import json
import re
import subprocess
import time
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path

PACKAGE = 'com.projectinfinity.kodi'
COBRA = PACKAGE+'/.InfinityLiveActivity'
VERSION = 2103431


def _bounds(node):
    values = tuple(map(int, re.findall(r'-?\d+', node.get('bounds', ''))))
    return values if len(values) == 4 and values[2] > values[0] and values[3] > values[1] else None


def _labels(nodes, package):
    return [n.get('text') or n.get('content-desc') for n in nodes
            if n.get('package') == package and (n.get('text') or n.get('content-desc'))]


def _item(node):
    return {key: node.get(key) for key in
            ('text', 'content-desc', 'resource-id', 'class', 'package', 'bounds', 'clickable')}


def drawer_state(nodes, launcher):
    """Explicit native drawer IDs/role only; predicted Home icons do not count."""
    own = [n for n in nodes if n.get('package') == launcher and _bounds(n)]
    drawer = [n for n in own if re.search(
        r':id/(?:apps_view|apps_list_view|all_apps|all_apps_container|apps_recycler_view|all_apps_header)$',
        n.get('resource-id', '')) or re.fullmatch(r'Apps list|All apps list', n.get('content-desc', ''), re.I)]
    workspace = [n for n in own if re.search(r':id/(?:workspace|hotseat)$', n.get('resource-id', ''))]
    if drawer:
        return 'NATIVE_ALL_APPS', drawer
    if workspace:
        return 'NATIVE_WORKSPACE', workspace
    return 'UNOBSERVED_NATIVE_LAUNCHER_STATE', []


def observe(out: Path, apk_sha256: str, version_code: int):
    out.mkdir(parents=True, exist_ok=False)
    report = {'scope': 'UNCHANGED_SIGNED431_NORMAL_SETTINGS_AND_NATIVE_ALL_APPS_ICON_SURFACES',
              'receipt_apk_sha256': apk_sha256, 'versionCode': version_code,
              'APK_binding': 'Parent signature/hash/install probe binds the exact signed APK',
              'Infinity': 'NOT_LAUNCHED', 'shutdown': 'NOT_RUN',
              'physical_Samsung': 'NOT_RUN', 'appearance': 'NOT_ASSERTED; INSPECT_NATIVE_FRAMES',
              'operations': [], 'modes': {}, 'errors': []}
    original_mode = None
    welcome_guard = False

    def command(*args, check=True):
        try:
            result = subprocess.run(['adb', *args], capture_output=True, text=True, timeout=30)
            row = {'stdout': result.stdout, 'stderr': result.stderr, 'returncode': result.returncode}
        except subprocess.TimeoutExpired:
            row = {'stdout': '', 'stderr': 'ADB30s operation timeout', 'returncode': 124}
        report['operations'].append({'adb': list(args), 'returncode': row['returncode']})
        if check and row['returncode']:
            raise RuntimeError('ADB operation failed '+repr(args[:3])+': '+row['stderr'][-500:])
        return row

    def text(*args, check=True):
        return command(*args, check=check)['stdout']

    def capture(folder, name):
        folder.mkdir(parents=True, exist_ok=True)
        dump = command('shell', 'uiautomator', 'dump', '/sdcard/infinity-icon-surface-qa.xml', check=False)
        raw = text('shell', 'cat', '/sdcard/infinity-icon-surface-qa.xml', check=False)
        (folder/(name+'.xml')).write_text(raw)
        screenshot = subprocess.run(['adb', 'exec-out', 'screencap', '-p'], capture_output=True, timeout=20)
        report['operations'].append({'adb': ['exec-out', 'screencap', '-p'], 'returncode': screenshot.returncode})
        (folder/(name+'.png')).write_bytes(screenshot.stdout)
        try:
            nodes = list(ET.fromstring(raw).iter('node'))
            parse_error = None
        except ET.ParseError as exc:
            nodes = []
            parse_error = str(exc)
        details = {'XML': name+'.xml', 'PNG': name+'.png', 'dump_returncode': dump['returncode'],
                   'screenshot_returncode': screenshot.returncode, 'XML_parse_error': parse_error,
                   'packages': sorted({n.get('package', '') for n in nodes})}
        if screenshot.returncode or not screenshot.stdout.startswith(b'\x89PNG\r\n\x1a\n'):
            raise RuntimeError('Native screenshot was not captured: '+name)
        return nodes, details

    def state_poll(folder, name, predicate):
        captures = []
        for attempt in range(1, 4):
            nodes, details = capture(folder, name+'-'+str(attempt))
            captures.append(details)
            if predicate(nodes):
                return nodes, captures, True
            if attempt != 3:
                time.sleep(.5)
        return nodes, captures, False

    def empty_cobra(nodes):
        return any(n.get('package') == PACKAGE and re.search(
            r'ADD TV SOURCE|Add a TV source', n.get('text', '')+n.get('content-desc', ''), re.I)
                   for n in nodes)

    def header_candidates(nodes, settings):
        images = [n for n in nodes if n.get('package') == settings and _bounds(n) and
                  ('ImageView' in n.get('class', '') or re.search(
                      r':id/(?:entity_header_icon|app_icon|app_detail_icon|application_icon|app_snippet_icon)$',
                      n.get('resource-id', '')))]
        return [_item(n) for n in images]

    def launcher_items(nodes, launcher, state):
        # A predicted Home item is deliberately excluded even if its label
        # happens to be Infinity. Only actual native All Apps is classified.
        if state != 'NATIVE_ALL_APPS':
            return []
        return [_item(n) for n in nodes if n.get('package') == launcher and _bounds(n) and
                (n.get('text', '').strip() == 'Infinity' or n.get('content-desc', '').strip() == 'Infinity') and
                not n.get('content-desc', '').startswith('Predicted app:')]

    try:
        if version_code != VERSION or re.fullmatch(r'[0-9a-f]{64}', apk_sha256) is None:
            raise RuntimeError('Exact final431 receipt required')
        serial = text('get-serialno').strip()
        sdk = text('shell', 'getprop', 'ro.build.version.sdk').strip()
        qemu = text('shell', 'getprop', 'ro.kernel.qemu').strip()
        if not (serial.startswith('emulator-') and sdk == '37' and qemu == '1'):
            raise RuntimeError('Disposable API37 emulator required')
        report.update(serial=serial, sdk=sdk)
        package = text('shell', 'dumpsys', 'package', PACKAGE)
        (out/'installed-package.txt').write_text(package)
        if re.search(r'\bversionCode='+str(VERSION)+r'\b', package) is None:
            raise RuntimeError('Installed package is not431')
        _, report['initial_Cobra_frames'], welcome_guard = state_poll(out, 'initial-Cobra-welcome', empty_cobra)
        if not welcome_guard:
            raise RuntimeError('Empty Cobra welcome required before sources/playback')
        raw_mode = text('shell', 'cmd', 'uimode', 'night', check=False)
        (out/'initial-night-mode.txt').write_text(raw_mode)
        found = re.search(r'Night mode:\s*(no|yes|auto|custom)\b', raw_mode, re.I)
        if found and found.group(1).lower() in ('no', 'yes'):
            original_mode = found.group(1).lower()
        home = text('shell', 'cmd', 'package', 'resolve-activity', '--brief', '-a',
                    'android.intent.action.MAIN', '-c', 'android.intent.category.HOME')
        (out/'HOME-component.txt').write_text(home)
        components = re.findall(r'([A-Za-z0-9_.]+)/(\S+)', home)
        if not components:
            raise RuntimeError('Native HOME component not resolved')
        launcher = components[-1][0]
        report['launcher_package'] = launcher
        raw_settings = text('shell', 'cmd', 'package', 'resolve-activity', '--brief', '-a',
                            'android.settings.APPLICATION_DETAILS_SETTINGS', '-d', 'package:'+PACKAGE)
        (out/'AppInfo-component.txt').write_text(raw_settings)
        settings_components = re.findall(r'([A-Za-z0-9_.]+)/(\S+)', raw_settings)
        if not settings_components:
            raise RuntimeError('Normal Settings App Info component not resolved')
        settings = settings_components[-1][0]
        report['settings_package'] = settings
        wm = text('shell', 'wm', 'size')
        (out/'display-size.txt').write_text(wm)
        sizes = re.findall(r'(\d+)x(\d+)', wm)
        if not sizes:
            raise RuntimeError('Actual display size missing')
        width, height = map(int, sizes[-1])
        report['display'] = [width, height]

        for mode, name in (('no', 'light'), ('yes', 'dark')):
            folder = out/name
            folder.mkdir()
            state = {'requested_night_mode': mode, 'appearance': 'UNVERIFIED_NATIVE_FRAMES',
                     'AppInfo': {}, 'AllApps': {}}
            report['modes'][mode] = state
            try:
                state['set_night_mode'] = command('shell', 'cmd', 'uimode', 'night', mode)
                state['actual_uimode'] = text('shell', 'cmd', 'uimode', 'night')
                state['configuration'] = text('shell', 'am', 'get-config', check=False)
                # Full ResolveInfo.dump preserves both ActivityInfo and
                # ApplicationInfo icon fields. It does not launch the icon.
                (folder/'launcher-ActivityInfo-ApplicationInfo.txt').write_text(text(
                    'shell', 'cmd', 'package', 'resolve-activity', '-a', 'android.intent.action.MAIN',
                    '-c', 'android.intent.category.LAUNCHER', '-p', PACKAGE, check=False))
                (folder/'AppInfo-launch.txt').write_text(text('shell', 'am', 'start', '-W', '-a',
                    'android.settings.APPLICATION_DETAILS_SETTINGS', '-d', 'package:'+PACKAGE))
                def info_ready(nodes):
                    return any(n.get('package') == settings and n.get('text', '').strip() == 'Infinity'
                               and _bounds(n) for n in nodes)
                nodes, frames, observed = state_poll(folder, 'Settings-AppInfo', info_ready)
                state['AppInfo'].update(frames=frames, native_Settings_Infinity_heading_observed=observed,
                                        native_icon_candidates=header_candidates(nodes, settings),
                                        labels=_labels(nodes, settings))

                text('shell', 'input', 'keyevent', 'KEYCODE_HOME')
                nodes, frames, home_observed = state_poll(folder, 'Home-before-AllApps',
                    lambda ns: drawer_state(ns, launcher)[0] == 'NATIVE_WORKSPACE')
                state['AllApps']['home_frames'] = frames
                state['AllApps']['native_workspace_observed_before_AllApps'] = home_observed
                if home_observed:
                    text('shell', 'input', 'keyevent', '284')  # KEYCODE_ALL_APPS
                    nodes, frames, all_apps = state_poll(folder, 'AllApps-key',
                        lambda ns: drawer_state(ns, launcher)[0] == 'NATIVE_ALL_APPS')
                    state['AllApps']['key_frames'] = frames
                    kind, markers = drawer_state(nodes, launcher)
                    # A single supported upward swipe is justified only by
                    # actual workspace IDs. Start in the blank middle, never
                    # the Google hotseat/search target at90% screen height.
                    if kind == 'NATIVE_WORKSPACE':
                        state['AllApps']['workspace_swipe'] = [width//2, height//2, width//2, height//6, 450]
                        text('shell', 'input', 'swipe', str(width//2), str(height//2),
                             str(width//2), str(height//6), '450')
                        nodes, frames, all_apps = state_poll(folder, 'AllApps-workspace-swipe',
                            lambda ns: drawer_state(ns, launcher)[0] == 'NATIVE_ALL_APPS')
                        state['AllApps']['swipe_frames'] = frames
                        kind, markers = drawer_state(nodes, launcher)
                    state['AllApps'].update(native_state=kind, state_markers=[_item(n) for n in markers],
                                            native_Infinity_items=launcher_items(nodes, launcher, kind),
                                            labels=_labels(nodes, launcher))
                else:
                    state['AllApps'].update(native_state='UNOBSERVED_HOME; NO_BLIND_DRAWER_GESTURE',
                                            native_Infinity_items=[])
                state['status'] = ('CAPTURED_NATIVE_SURFACES_APPEARANCE_REQUIRES_REVIEW'
                    if observed and state['AllApps'].get('native_state') == 'NATIVE_ALL_APPS' and
                       state['AllApps'].get('native_Infinity_items') else 'PARTIAL_NATIVE_SURFACE_OBSERVATION')
            except Exception as exc:
                state['status'] = 'FAIL_AT_RECORDED_NATIVE_SURFACE_OPERATION'
                state['error'] = str(exc)
                report['errors'].append(name+': '+str(exc))
                (folder/'ERROR.txt').write_text(traceback.format_exc())
        report['status'] = ('CAPTURED_BOTH_MODES_NATIVE_APPEARANCE_UNVERIFIED'
            if len(report['modes']) == 2 and all(m.get('status') == 'CAPTURED_NATIVE_SURFACES_APPEARANCE_REQUIRES_REVIEW'
                for m in report['modes'].values()) else 'PARTIAL_OR_FAILED_NATIVE_SURFACE_OBSERVATION')
    except Exception as exc:
        report['status'] = 'FAIL_AT_ICON_SURFACE_GUARD'
        report['errors'].append(str(exc))
        (out/'ERROR.txt').write_text(traceback.format_exc())
    finally:
        if original_mode:
            report['restore_initial_mode'] = command('shell', 'cmd', 'uimode', 'night', original_mode, check=False)
        if welcome_guard:
            report['return_Cobra'] = command('shell', 'am', 'start', '-W', '-n', COBRA, check=False)
            try:
                _, frames, ready = state_poll(out, 'returned-Cobra-welcome', empty_cobra)
                report['returned_Cobra_frames'] = frames
                report['safe_empty_Cobra_for_independent_buttons'] = ready
            except Exception as exc:
                report['safe_empty_Cobra_for_independent_buttons'] = False
                report['errors'].append('Return observation: '+str(exc))
        else:
            report['return_Cobra'] = 'NOT_RUN; initial welcome guard failed'
        report['logcat_capture'] = command('logcat', '-d', '-v', 'threadtime', check=False)
        (out/'logcat.txt').write_text(report['logcat_capture'].pop('stdout'))
        (out/'OUTCOME.json').write_text(json.dumps(report, indent=2)+'\n')
    if report['errors']:
        raise RuntimeError('Native icon surface probe failed: '+'; '.join(report['errors']))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--apk-sha256', required=True)
    parser.add_argument('--version-code', type=int, required=True)
    args = parser.parse_args()
    observe(args.out, args.apk_sha256, args.version_code)
