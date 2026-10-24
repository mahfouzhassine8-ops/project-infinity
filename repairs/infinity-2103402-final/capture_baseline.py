"""Read existing Android evidence without installing or controlling Infinity.

Run on a computer already connected to the Fold through authorized ADB.
Output is private diagnostic data: nothing is uploaded or committed by this tool.
No root, app launch, force-stop, log clearing, settings writes or APK operations.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import threading
import time
from zipfile import ZipFile, BadZipFile

PACKAGE = 'com.projectinfinity.kodi'
LIMIT = 8 * 1024 * 1024
BUGREPORT_LIMIT = 256 * 1024 * 1024


def capture(argv, destination, timeout=30, limit=LIMIT, watched=None,
            watched_limit=BUGREPORT_LIMIT):
    """Bound stdout, elapsed time and a bugreport written by the ADB client.

Only this host-side command is terminated on timeout. Never signal the app.
Retain partial output and record its limitations instead of claiming success.
"""
    start = time.monotonic()
    status = {'status': 'unavailable', 'bytes': 0, 'returncode': None}
    with Path(destination).open('xb') as output:
        try:
            proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    stdin=subprocess.DEVNULL)
        except OSError as error:
            status['error_type'] = type(error).__name__
            return status
        overflow = threading.Event()
        reader_error = []
        def read():
            try:
                while True:
                    block = proc.stdout.read1(8192)
                    if not block: break
                    room = limit - status['bytes']
                    output.write(block[:max(0, room)])
                    status['bytes'] += min(len(block), max(0, room))
                    if len(block) > room:
                        overflow.set()
                        break
            except OSError as error:
                reader_error.append(type(error).__name__)
                overflow.set()
        reader = threading.Thread(target=read, daemon=True)
        reader.start()
        reason = None
        try:
            while proc.poll() is None:
                if overflow.is_set(): reason = 'output_limit_or_read_failure'; break
                if time.monotonic() - start > timeout: reason = 'timeout'; break
                if watched is not None and watched.exists() and watched.stat().st_size > watched_limit:
                    reason = 'bugreport_size_limit'; break
                time.sleep(.05)
        finally:
            if proc.poll() is None:
                proc.kill()
            proc.wait()
            reader.join(timeout=5)
            proc.stdout.close()
        status['returncode'] = proc.returncode
        status['duration_ms'] = round((time.monotonic() - start) * 1000)
        if reader_error: status['error_type'] = reader_error[0]
        if reader.is_alive():
            raise RuntimeError('Host evidence reader did not finish; output cannot be claimed complete')
        status['status'] = (reason or ('output_limit_or_read_failure' if overflow.is_set() else
                            'command_failed' if proc.returncode else
                            'collected' if status['bytes'] else 'empty'))
    status['sha256'] = hashlib.sha256(Path(destination).read_bytes()).hexdigest()
    return status


def commands():
    # Fixed read-only commands; no shell strings or device mutation arguments.
    return [
        ('device-api.txt', ['shell', 'getprop', 'ro.build.version.sdk']),
        ('device-build.txt', ['shell', 'getprop', 'ro.build.fingerprint']),
        ('device-time.txt', ['shell', 'date', '+%Y-%m-%dT%H:%M:%S%z']),
        ('package.txt', ['shell', 'dumpsys', 'package', PACKAGE]),
        ('kodi-pid.txt', ['shell', 'pidof', PACKAGE + ':kodi']),
        ('exit-info.txt', ['shell', 'dumpsys', 'activity', 'exit-info', PACKAGE]),
        ('crash-logcat.txt', ['logcat', '-d', '-b', 'crash', '-v', 'threadtime']),
        ('recent-logcat.txt', ['logcat', '-d', '-b', 'main', '-b', 'system', '-b', 'events',
                              '-t', '20000', '-v', 'threadtime']),
        ('native-dropbox.txt', ['shell', 'dumpsys', 'dropbox', '--print', 'data_app_native_crash']),
        ('anr-dropbox.txt', ['shell', 'dumpsys', 'dropbox', '--print', 'data_app_anr']),
        ('memory.txt', ['shell', 'dumpsys', 'meminfo', PACKAGE]),
        ('existing-bugreports.txt', ['shell', 'ls', '/bugreports/']),
    ]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--adb', default='adb')
    parser.add_argument('--serial', required=True, help='An already authorized ADB device serial')
    parser.add_argument('--output', required=True, type=Path, help='A NEW private output directory')
    parser.add_argument('--bugreport', action='store_true', help='Also request the OS bugreport; may take several minutes')
    args = parser.parse_args(argv)
    if not re.fullmatch(r'[A-Za-z0-9_.:-]{1,160}', args.serial):
        parser.error('Invalid ADB serial')
    adb = shutil.which(args.adb)
    if not adb: parser.error('ADB is not available on this computer')
    args.output.mkdir(mode=0o700, parents=True, exist_ok=False)
    base = [adb, '-s', args.serial]
    manifest = {'schema': 1, 'captured_utc': datetime.now(timezone.utc).isoformat(),
                'expected_package': PACKAGE, 'expected_version_code': 2103401,
                'expected_api': 37, 'apk_installed': False, 'app_controlled': False,
                'native_fault_attributed': False, 'files': {},
                'privacy': 'Private OS logs may include other apps and personal data. No automatic upload.'}
    receipt = args.output / 'capture-manifest.json'
    def save():
        partial = receipt.with_suffix('.partial')
        partial.write_text(json.dumps(manifest, indent=2) + '\n')
        partial.replace(receipt)
    save()
    for name, command in commands():
        manifest['files'][name] = capture(base + command, args.output / name)
        save()
    package = (args.output / 'package.txt').read_text(errors='replace')
    api = (args.output / 'device-api.txt').read_text(errors='replace').strip()
    version = re.search(r'\bversionCode=(\d+)\b', package)
    manifest['observed_api'] = api if api.isdigit() else None
    manifest['observed_version_code'] = int(version[1]) if version else None
    manifest['baseline_identity_status'] = ('version_and_api_match_not_signer_proof'
        if api == '37' and version and version[1] == '2103401' else 'UNVERIFIED_OR_DIFFERENT_BASELINE')
    save()
    if args.bugreport:
        destination = args.output / 'android-bugreport.zip'
        status = capture(base + ['bugreport', str(destination)], args.output / 'bugreport-command.txt',
                         timeout=300, watched=destination)
        manifest['files']['bugreport-command.txt'] = status
        report = {'status': 'unavailable', 'available': False}
        if destination.is_file():
            report['bytes'] = destination.stat().st_size
            digest = hashlib.sha256()
            with destination.open('rb') as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b''): digest.update(block)
            report['sha256'] = digest.hexdigest()
            if status['status'] == 'collected' and report['bytes'] <= BUGREPORT_LIMIT:
                try:
                    with ZipFile(destination) as archive:
                        # Validate inventory without extracting private or unbounded files.
                        if not any(n.startswith('bugreport') and n.endswith('.txt') for n in archive.namelist()):
                            raise BadZipFile('No main report')
                    report.update(status='collected_archive_not_yet_analyzed', available=True)
                except (OSError, BadZipFile):
                    report['status'] = 'invalid_or_partial_archive'
            else: report['status'] = 'partial_or_limited_archive'
        manifest['files']['android-bugreport.zip'] = report
        save()
    print('Private evidence captured to ' + str(args.output) + '; see capture-manifest.json for omissions.')


if __name__ == '__main__':
    main()
