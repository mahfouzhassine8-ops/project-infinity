#!/usr/bin/env python3
"""Non-invasive Galaxy Fold Infinity process-exit recorder for use on a Mac.

This tool only reads Android state and continuously saves bounded logcat output
locally. It NEVER launches, kills, force-stops, installs, alters app settings,
clears logcat, or uploads files. A missing PID alone is NOT labelled a crash.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading
import time

PACKAGE = 'com.projectinfinity.kodi'
ENGINE = PACKAGE + ':kodi'
ALLOWED_READS = (
    ('get-state',),
    ('shell', 'pidof', ENGINE),
    ('shell', 'dumpsys', 'activity', 'exit-info', PACKAGE),
    ('shell', 'dumpsys', 'dropbox', '--print', 'data_app_native_crash'),
    ('shell', 'dumpsys', 'dropbox', '--print', 'SYSTEM_TOMBSTONE'),
    ('shell', 'getprop', 'ro.product.model'),
    ('shell', 'getprop', 'ro.build.fingerprint'),
    ('shell', 'getprop', 'ro.build.version.release'),
    ('shell', 'getprop', 'ro.build.version.sdk'),
    ('shell', 'getprop', 'ro.build.version.oneui'),
    ('shell', 'dumpsys', 'package', PACKAGE),
    ('logcat', '-b', 'crash', '-d', '-v', 'threadtime'),
)


def now():
    return datetime.now(timezone.utc).isoformat()


def command(adb, serial, args, limit=2_000_000):
    if tuple(args) not in ALLOWED_READS:
        raise ValueError('Refused non-read-only ADB operation: ' + repr(args))
    try:
        p = subprocess.run([adb, '-s', serial, *args], capture_output=True,
                           timeout=25)
        return {'returncode': p.returncode,
                'stdout': p.stdout[:limit].decode('utf-8', 'replace'),
                'stderr': p.stderr[:4096].decode('utf-8', 'replace'),
                'truncated': len(p.stdout) > limit}
    except subprocess.TimeoutExpired as exc:
        return {'returncode': None, 'timed_out': True,
                'stderr': 'ADB read timed out; no change made'}


def current_pid(adb, serial):
    p = command(adb, serial, ('shell', 'pidof', ENGINE))
    if p['returncode'] == 0 and re.fullmatch(r'\s*\d+(?:\s+\d+)*\s*', p['stdout']):
        return int(p['stdout'].split()[0]), 'observed'
    # pidof exit=1 also occurs on disconnection. Confirm transport separately.
    state = command(adb, serial, ('get-state',))
    if state['returncode'] != 0 or state['stdout'].strip() != 'device':
        return None, 'adb_unavailable'
    return None, 'not_running'


def observe_transition(previous, missing, pid, state):
    """Return (active_pid, missing_samples, event, departed_pid).

    PID replacement can happen faster than a polling interval. Retain the
    previous PID for exit-info collection even if a new engine is already live.
    Neither disappearance nor replacement alone proves a native crash.
    """
    if state == 'observed':
        if previous is None:
            return pid, 0, 'engine_observed', None
        if pid != previous:
            return pid, 0, 'engine_pid_replaced', previous
        return previous, 0, None, None
    if state == 'not_running' and previous is not None:
        if missing + 1 >= 2:
            return None, 0, 'engine_no_longer_observed', previous
        return previous, missing + 1, None, None
    return previous, 0 if state == 'adb_unavailable' else missing, None, None


class RingLog:
    """Retain the newest four 16-MiB logcat segments without unbounded growth."""
    def __init__(self, folder, segment_bytes=16*1024*1024, max_files=4):
        self.folder = Path(folder)
        self.segment_bytes = segment_bytes
        self.max_files = max_files
        self.index = 0
        self.written = 0
        self.stream = (self.folder / 'logcat-0.txt').open('wb')

    def write(self, data):
        while data:
            if self.written >= self.segment_bytes:
                self.stream.close()
                self.index += 1
                old = self.index - self.max_files
                if old >= 0:
                    (self.folder / ('logcat-' + str(old) + '.txt')).unlink(missing_ok=True)
                self.written = 0
                self.stream = (self.folder / ('logcat-' + str(self.index) + '.txt')).open('wb')
            take = min(len(data), self.segment_bytes - self.written)
            self.stream.write(data[:take])
            self.written += take
            data = data[take:]

    def close(self):
        self.stream.close()


def capture_exit(adb, serial, folder, previous_pid, event_index):
    path = folder / ('exit-' + str(event_index).zfill(3))
    path.mkdir(mode=0o700)
    snapshot = {'timestamp_utc': now(), 'observed_prior_pid': previous_pid,
                'classification': 'unknown_until_exit_metadata_is_examined',
                'user_data_changed': False, 'crash_proven': False}
    for label, args in (
        ('exit-info', ('shell', 'dumpsys', 'activity', 'exit-info', PACKAGE)),
        ('logcat-crash', ('logcat', '-b', 'crash', '-d', '-v', 'threadtime')),
        ('native-dropbox', ('shell', 'dumpsys', 'dropbox', '--print', 'data_app_native_crash')),
        ('tombstone-dropbox', ('shell', 'dumpsys', 'dropbox', '--print', 'SYSTEM_TOMBSTONE'))):
        result = command(adb, serial, args)
        (path / (label + '.json')).write_text(json.dumps(result, indent=2))
        snapshot[label + '_retrieved'] = result['returncode'] == 0
    (path / 'SUMMARY.json').write_text(json.dumps(snapshot, indent=2))
    return path


def connected_serial(adb, requested):
    p = subprocess.run([adb, 'devices'], capture_output=True, text=True, timeout=20, check=True)
    valid = [line.split()[0] for line in p.stdout.splitlines()[1:]
             if len(line.split()) == 2 and line.split()[1] == 'device']
    if requested and requested in valid:
        return requested
    if not requested and len(valid) == 1:
        return valid[0]
    raise RuntimeError('Connect and authorize one Fold (or specify --serial from adb devices).')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True, help='New private directory on your Mac')
    p.add_argument('--serial', help='Optional ADB serial for multiple attached devices')
    p.add_argument('--hours', type=float, default=2, help='Observation limit, default 2 hours; no app control')
    args = p.parse_args()
    if not (0 < args.hours <= 24):
        p.error('--hours must be between 0 and 24')
    adb = shutil.which('adb')
    if not adb:
        p.error('Install Android platform-tools on the Mac so adb is available.')
    serial = connected_serial(adb, args.serial)
    os.umask(0o077)
    args.out.mkdir(mode=0o700, parents=True, exist_ok=False)
    folder = args.out
    meta = {'started_utc': now(), 'package': PACKAGE, 'process': ENGINE,
            'scope': 'read-only continuous diagnostics; no install, force-stop, data wipe or upload',
            'serial_sha256_only': None}
    # Device serial is deliberately omitted from saved reports.
    for key, prop in [('model', 'ro.product.model'), ('fingerprint', 'ro.build.fingerprint'),
                      ('android_release', 'ro.build.version.release'),
                      ('sdk', 'ro.build.version.sdk'), ('oneui', 'ro.build.version.oneui')]:
        meta[key] = command(adb, serial, ('shell', 'getprop', prop))
    meta['package_details'] = command(adb, serial, ('shell', 'dumpsys', 'package', PACKAGE))
    (folder / 'DEVICE.json').write_text(json.dumps(meta, indent=2))
    ring = RingLog(folder)
    # Read-only logcat stream, never 'logcat -c'. Logs may include sensitive data.
    log = subprocess.Popen([adb, '-s', serial, 'logcat', '-b', 'main', '-b', 'system',
                            '-b', 'crash', '-v', 'threadtime', '-T', '1'],
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    def consume():
        try:
            while True:
                chunk = log.stdout.read(8192)
                if not chunk: break
                ring.write(chunk)
        finally:
            ring.close()
    reader = threading.Thread(target=consume, daemon=True)
    reader.start()
    print('Watching Infinity without controlling it. Use your Fold normally; Ctrl+C stops.')
    previously_running = None
    missing = 0
    events = []
    end = time.monotonic() + args.hours * 3600
    try:
        while time.monotonic() < end:
            pid, state = current_pid(adb, serial)
            previously_running, missing, event, departed = observe_transition(
                previously_running, missing, pid, state)
            if event:
                record = {'time_utc': now(), 'event': event, 'cause': 'unknown'}
                if previously_running is not None: record['pid'] = previously_running
                if departed is not None: record['prior_pid'] = departed
                events.append(record)
            if departed is not None:
                capture_exit(adb, serial, folder, departed, len(events))
            (folder / 'TIMELINE.json').write_text(json.dumps(events, indent=2))
            time.sleep(3)
    except KeyboardInterrupt:
        pass
    finally:
        log.terminate()  # Only the local ADB logcat process, never Infinity.
        try: log.wait(timeout=5)
        except subprocess.TimeoutExpired: log.kill(); log.wait()
        reader.join(timeout=5)
        (folder / 'TIMELINE.json').write_text(json.dumps(events, indent=2))
    print('Capture ended. Keep the folder private and review it before sharing.')


if __name__ == '__main__': main()
