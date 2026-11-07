"""Exact parent authentication and one disposable Android target qualification.

No signing, application modification, reset, Close, or repeated installation.
The Android result is about CI feasibility, never final candidate acceptance.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
APK_SHA = 'a24ffafd056db23aa9d433552e17d4362cc9dbc9dd568b086d84cabadae8c619'
CERT = 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
ENGINE = 'fadfb1a08e3d125958a77d393c1d66453ec3e9c91aac3349ec5806c67c17694d'
PACKAGE = 'com.projectinfinity.kodi'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(out, name, value):
    (out / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def run(args, timeout=40):
    return subprocess.run([str(x) for x in args], capture_output=True,
                          text=True, timeout=timeout, check=False)


def verify(apk, sdk, out):
    assert sha(apk) == APK_SHA, 'EXACT_SIGNED_2103462_PARENT_REQUIRED'
    assert apk.stat().st_size == 778732223
    signer = run(['java', '-jar', sdk / 'lib/apksigner.jar', 'verify',
                  '--verbose', '--print-certs', apk], timeout=120)
    (out / 'PARENT-SIGNATURE.txt').write_text(signer.stdout + signer.stderr)
    assert signer.returncode == 0
    assert re.findall(r'certificate SHA-256 digest: ([0-9a-f]+)', signer.stdout) == [CERT]
    assert 'Number of signers: 1' in signer.stdout
    for scheme in ('v1', 'v2', 'v3'):
        assert re.search(r'Verified using ' + scheme + r' scheme .*: true', signer.stdout)
    badging = run([sdk / 'aapt', 'dump', 'badging', apk])
    assert badging.returncode == 0
    (out / 'PARENT-BADGING.txt').write_text(badging.stdout)
    assert "name='" + PACKAGE + "' versionCode='2103462'" in badging.stdout
    with ZipFile(apk) as archive:
        names = archive.namelist()
        assert len(names) == len(set(names))
        assert all(not n.startswith('/') and '..' not in Path(n).parts for n in names)
        with archive.open('lib/arm64-v8a/libkodi.so') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == ENGINE
        abis = sorted({n.split('/')[1] for n in names if n.startswith('lib/') and n.endswith('.so')})
        assert abis == ['arm64-v8a']
    report = dict(status='PASS_EXACT_SIGNED_2103462_PARENT_AUTHENTICATED',
                  apk_sha256=APK_SHA, apk_bytes=apk.stat().st_size,
                  package=PACKAGE, versionCode=2103462, certificate_sha256=CERT,
                  native_sha256=ENGINE, native_ABIs=abis, signatures=['v1', 'v2', 'v3'],
                  successor_APK_created=False, Android='NOT_RUN', Fold='NOT_RUN')
    save(out, 'PARENT-AUTHENTICATION.json', report)
    print(json.dumps(report, sort_keys=True))


def android(apk, sdk, out):
    verify(apk, sdk, out)
    adb = Path(os.environ['ANDROID_HOME']) / 'platform-tools/adb'
    devices = run([adb, 'devices'])
    serials = re.findall(r'^(emulator-\d+)\s+device$', devices.stdout, re.M)
    assert len(serials) == 1, 'EXACTLY_ONE_DISPOSABLE_EMULATOR_REQUIRED'
    serial = serials[0]

    def shell(*args, timeout=40):
        return run([adb, '-s', serial, 'shell', *args], timeout=timeout)

    assert shell('getprop', 'ro.kernel.qemu').stdout.strip() == '1'
    assert not shell('pm', 'list', 'packages', PACKAGE).stdout.strip(), 'FRESH_TARGET_REQUIRED'
    props = {name: shell('getprop', name).stdout.strip() for name in (
        'ro.build.version.sdk', 'ro.build.fingerprint', 'ro.product.cpu.abilist',
        'ro.dalvik.vm.native.bridge', 'ro.enable.native.bridge.exec',
        'ro.product.cpu.abilist64', 'ro.product.cpu.abilist32')}
    props['page_size'] = shell('getconf', 'PAGESIZE').stdout.strip()
    props['emulator_serial'] = serial
    save(out, 'ANDROID-TARGET.json', props)
    assert props['ro.build.version.sdk'] == '37', 'ANDROID17_REQUIRED'
    expected = json.loads((HERE / 'SCOPE.json').read_text()).get('expected_target')
    if expected:
        assert props['page_size'] == expected['page_size'], 'EXACT_SELECTED_STOCK_PAGE_SIZE_REQUIRED'
    report = dict(status='BLOCKED_TARGET_NOT_QUALIFIED', parent_apk_sha256=APK_SHA,
                  candidate_runtime='NOT_RUN', Fold='NOT_RUN', shutdown='NOT_RUN',
                  settings_reset=False, OS_compatibility_overrides=False,
                  installed_user_device=False, attempts=1)
    try:
        installed = run([adb, '-s', serial, 'install', '--no-streaming', apk], timeout=240)
        (out / 'INSTALL.txt').write_text(installed.stdout + installed.stderr)
        report['install_exit'] = installed.returncode
        if installed.returncode != 0 or 'Success' not in installed.stdout:
            report['blocker'] = (installed.stdout + installed.stderr).strip()[-3000:]
            raise RuntimeError('EXACT_ARM64_PARENT_INSTALL_FAILED')
        # One original native entry, no replacement or test DEX/native library.
        launched = shell('am', 'start', '-W', '-n', PACKAGE + '/.Main', timeout=90)
        (out / 'LAUNCH.txt').write_text(launched.stdout + launched.stderr)
        report['launch_exit'] = launched.returncode
        if launched.returncode or 'Error:' in launched.stdout + launched.stderr or 'Exception' in launched.stdout + launched.stderr:
            report['blocker'] = (launched.stdout + launched.stderr).strip()[-3000:]
            raise RuntimeError('ORIGINAL_NATIVE_ENTRY_LAUNCH_FAILED')
        # Read-only observation. This is neither a Close nor a reopen cycle.
        deadline = time.monotonic() + 60
        live = []
        while time.monotonic() < deadline:
            pid = shell('pidof', PACKAGE).stdout.strip()
            live.append(pid)
            if not pid:
                break
            time.sleep(2)
        logs = run([adb, '-s', serial, 'logcat', '-d', '-v', 'threadtime'], timeout=60)
        (out / 'LOGCAT.txt').write_text(logs.stdout + logs.stderr)
        report['PID_observations'] = live
        report['native_startup_markers'] = {s: s in logs.stdout for s in (
            'Starting Kodi', 'Running on', 'CApplication::Create',
            'Fatal signal', 'dlopen failed', 'talloc', 'AT_RANDOM')}
        # Do not treat Java launch or PID presence alone as native qualification.
        if not live or not all(live) or not report['native_startup_markers']['Starting Kodi']:
            report['blocker'] = 'Original native engine did not establish a live Kodi runtime on the selected target; see source-bound LOGCAT.txt.'
            raise RuntimeError('ORIGINAL_NATIVE_RUNTIME_NOT_ESTABLISHED')
        report['status'] = 'PASS_PARENT_TARGET_STARTUP_QUALIFICATION_ONLY'
        report['remaining'] = 'Combined candidate Search/keyboard/graphics/navigation/watched/Info/white-line/install-over/recovery remain NOT_RUN'
    except Exception as error:
        report['failure'] = str(error)
        if not (out / 'LOGCAT.txt').exists():
            logs = run([adb, '-s', serial, 'logcat', '-d', '-v', 'threadtime'], timeout=60)
            (out / 'LOGCAT.txt').write_text(logs.stdout + logs.stderr)
        raise
    finally:
        save(out, 'TARGET-QUALIFICATION.json', report)
        print(json.dumps(report, sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['verify', 'android'])
    parser.add_argument('--apk', type=Path, required=True)
    parser.add_argument('--sdk', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    globals()[args.mode](args.apk, args.sdk, args.out)
