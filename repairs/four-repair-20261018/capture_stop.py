#!/usr/bin/env python3
"""Private ADB capture for Stop, background return, screensaver and Fold paths.

No installation, process termination, data clearing, settings changes, or
upload. Keep output private: logcat/bugreports can contain personal data.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

PACKAGE = 'com.projectinfinity.kodi'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--path', choices=['A', 'B', 'background', 'screensaver', 'fold'], required=True)
    parser.add_argument('--serial', help='ADB serial, required when multiple devices are connected')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--bugreport', action='store_true', help='Also collect a private Android bugreport after reproduction')
    parser.add_argument('--native-snapshot', action='store_true',
                        help='After reproduction only, request debuggerd -b for a still-live engine; may briefly pause threads and may be denied')
    args = parser.parse_args()
    if not shutil.which('adb'):
        parser.error('Android platform-tools adb is not on PATH.')
    os.umask(0o077)
    args.out.mkdir(parents=True, exist_ok=False, mode=0o700)
    devices = subprocess.check_output(['adb', 'devices'], text=True)
    available = [line.split()[0] for line in devices.splitlines()[1:]
                 if len(line.split()) == 2 and line.split()[1] == 'device']
    if args.serial:
        if args.serial not in available:
            parser.error('Selected device is not connected and authorized.')
        serial = args.serial
    elif len(available) == 1:
        serial = available[0]
    else:
        parser.error('Connect exactly one authorized device or use --serial.')
    command = ['adb', '-s', serial]
    def run(*values, timeout=30):
        try:
            result = subprocess.run(command + list(values), capture_output=True,
                                    text=True, timeout=timeout)
            return dict(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)
        except subprocess.TimeoutExpired as error:
            def decoded(value):
                return value.decode(errors='replace') if isinstance(value, bytes) else value or ''
            return dict(returncode=None, stdout=decoded(error.stdout),
                        stderr=decoded(error.stderr), timed_out=True)
    package = run('shell', 'dumpsys', 'package', PACKAGE)
    if 'versionCode=' not in package.get('stdout', ''):
        parser.error('Infinity is not installed on the selected device.')
    (args.out / 'package-before.json').write_text(json.dumps(package, indent=2))
    firmware = {name: run('shell', 'getprop', name) for name in (
        'ro.product.manufacturer', 'ro.product.model', 'ro.build.fingerprint',
        'ro.build.version.release', 'ro.build.version.sdk', 'ro.build.version.oneui',
        'ro.build.version.security_patch', 'ro.product.cpu.abilist')}
    (args.out / 'firmware.json').write_text(json.dumps(firmware, indent=2))
    events = []
    def mark(stage):
        row = dict(stage=stage, path=args.path,
                   host_utc=datetime.now(timezone.utc).isoformat(),
                   host_monotonic=time.monotonic(),
                   device_clock=run('shell', 'date', '+%s.%N'),
                   processes=run('shell', 'ps', '-A'))
        events.append(row)
        (args.out / 'timeline.json').write_text(json.dumps(events, indent=2))
        # A neutral marker only. Never log a video title/provider URL.
        run('shell', 'log', '-t', 'InfinityStopCapture', args.path + ':' + stage)
    def snapshot(label):
        for filename, values in (
            ('exit-info', ('shell', 'dumpsys', 'activity', 'exit-info', PACKAGE)),
            ('activities', ('shell', 'dumpsys', 'activity', 'activities')),
            ('window', ('shell', 'dumpsys', 'window', 'windows')),
            ('media-session', ('shell', 'dumpsys', 'media_session')),
            ('power', ('shell', 'dumpsys', 'power')),
            ('dream', ('shell', 'dumpsys', 'dreams')),
            ('device-state', ('shell', 'dumpsys', 'device_state')),
            ('display', ('shell', 'dumpsys', 'display')),
            ('threads', ('shell', 'ps', '-A', '-T')),
        ):
            (args.out / (label + '-' + filename + '.json')).write_text(json.dumps(run(*values), indent=2))
    log = (args.out / 'logcat-all.txt').open('w')
    live = subprocess.Popen(command + ['logcat', '-b', 'all', '-v', 'threadtime', '-T', '1'],
                            stdout=log, stderr=subprocess.STDOUT)
    try:
        mark('capture-started'); snapshot('before')
        if args.path in ('A', 'B'):
            print('Capture is running. Start a video in Infinity normally.')
            input('While the video is playing, press Enter here immediately BEFORE you press Stop: ')
            mark('before-stop')
            outcome = input('Press Stop. When choices return press Enter; if the app exits first, type exit and Enter: ').strip().casefold()
            mark('exit-before-choices' if outcome == 'exit' else 'choices-returned')
            if args.path == 'B' and outcome != 'exit':
                input('Now use Back/Home on the Fold. Press Enter here when Home appears or the app exits: ')
                mark('after-back-home')
            elif outcome != 'exit':
                print('Remain on movie choices; do not navigate Home for path A.')
        elif args.path == 'background':
            input('Use the usual playing or idle state. Press Enter immediately BEFORE leaving Infinity via Home/Recents: ')
            mark('before-background')
            input('Leave Infinity normally; press Enter once it is in the background: ')
            mark('background-entered'); snapshot('background')
            input('Keep the usual conditions for 5/20/45/90 minutes (separate captures). Press Enter immediately BEFORE returning, or now if a failure occurs: ')
            mark('before-foreground-return')
            input('Return to Infinity. Press Enter when it responds, freezes or exits: ')
            mark('after-foreground-return')
        elif args.path == 'screensaver':
            input('Allow the existing screensaver to activate normally; press Enter when it is visible: ')
            mark('screensaver-visible'); snapshot('screensaver')
            input('Press Enter immediately BEFORE dismissing the screensaver normally: ')
            mark('before-screensaver-dismissal')
            input('Dismiss it. Press Enter when Infinity responds, freezes or exits: ')
            mark('after-screensaver-dismissal')
        else:
            input('Use the usual playing or idle state. Press Enter immediately BEFORE folding/unfolding or rotating: ')
            mark('before-fold-transition')
            input('Perform ONE recorded transition. Press Enter when Infinity responds, freezes or exits: ')
            mark('after-fold-transition')
        input('Wait for the failure (or at least 30 seconds). Press Enter to finish this capture: ')
        mark('reproduction-ended'); snapshot('after')
        if args.native_snapshot:
            processes = run('shell', 'ps', '-A', '-o', 'PID,NAME')
            (args.out / 'native-snapshot-processes.json').write_text(json.dumps(processes, indent=2))
            for line in processes.get('stdout', '').splitlines():
                fields = line.split()
                if len(fields) == 2 and fields[0].isdigit() and fields[1] == PACKAGE + ':kodi':
                    result = run('shell', 'debuggerd', '-b', fields[0])
                    (args.out / ('native-snapshot-' + fields[0] + '.json')).write_text(json.dumps(result, indent=2))
        (args.out / 'tombstone-pull-result.json').write_text(json.dumps(
            run('pull', '/data/tombstones', str(args.out / 'tombstones')), indent=2))
        for name, values in (
            ('crash-buffer', ('logcat', '-b', 'crash', '-d', '-v', 'threadtime')),
            ('native-tombstone-dropbox', ('shell', 'dumpsys', 'dropbox', '--print', 'SYSTEM_TOMBSTONE')),
            ('native-crash-dropbox', ('shell', 'dumpsys', 'dropbox', '--print', 'data_app_native_crash')),
        ):
            (args.out / (name + '.json')).write_text(json.dumps(run(*values), indent=2))
        if args.bugreport:
            print('Collecting the Android bugreport into this private folder.')
            result = run('bugreport', str(args.out / 'android-bugreport.zip'), timeout=300)
            (args.out / 'bugreport-result.json').write_text(json.dumps(result, indent=2))
    finally:
        live.terminate()
        try: live.wait(timeout=5)
        except subprocess.TimeoutExpired: live.kill(); live.wait()
        log.close()
    print('Capture saved to ' + str(args.out.resolve()))
    print('Immediately export Infinity Diagnostics using its existing UI. Keep both outputs private.')
    print('No backtrace is promised: Samsung/Android may restrict crash records. Preserve any permission errors.')

if __name__ == '__main__':
    main()
