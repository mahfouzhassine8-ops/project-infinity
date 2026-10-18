#!/usr/bin/env python3
"""Record actual SDK support before running the unchanged candidate on API 37.

This only queries the runner's SDK catalog. Unavailable images are a recorded
infrastructure blocker, never a passed/skipped application qualification.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

# Observed SDK catalog in run 39124478854 publishes decimal platform IDs.
# This is the stable Android17 major release, not a fallback to another API.
IMAGE = 'system-images;android-37.0;google_apis;x86_64'


def pin_tools(sdk_root, out):
    """Keep the emulator action from shadowing setup-android's current tools.

    Its pinned sdk-installer.ts prepends cmdline-tools/latest/bin, which is
    9.0 on ubuntu-22.04, even after setup-android installs 22.0 separately.
    Old avdmanager misparses decimal platform IDs as android-0. Only change
    the disposable CI runner SDK; retain the old directory for inspection.
    """
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise RuntimeError('SDK path preparation is restricted to the CI runner')
    root = Path(sdk_root) / 'cmdline-tools'
    current, latest = root / '22.0', root / 'latest'
    props = (current / 'source.properties').read_text()
    if 'Pkg.Revision=22.0' not in props.replace(' ', ''):
        raise RuntimeError('setup-android did not provide the pinned 22.0 tools')
    before = (latest / 'source.properties').read_text()
    if latest.resolve() != current.resolve():
        latest.rename(root / 'infinity-original-latest')
        latest.symlink_to(current, target_is_directory=True)
    report = dict(before=before, after=props, resolved_latest=str(latest.resolve()),
                  scope='disposable CI SDK only', application_changed=False)
    Path(out).mkdir(parents=True, exist_ok=True)
    (Path(out) / 'SDK-TOOLS.json').write_text(json.dumps(report, indent=2) + '\n')


def check_avd(avd_home, out):
    """Require real platform metadata before launching the API37 emulator."""
    ini = Path(avd_home) / 'infinity-four-repair-api37.ini'
    config = ini.read_text()
    Path(out).mkdir(parents=True, exist_ok=True)
    (Path(out) / 'api37-avd.ini.txt').write_text(config)
    values = dict(line.split('=', 1) for line in config.splitlines() if '=' in line)
    if values.get('target') != 'android-37.0':
        raise RuntimeError('API37 AVD target is not android-37.0; refusing a misidentified image')
    avd_config = Path(values['path']) / 'config.ini'
    (Path(out) / 'api37-avd-config.ini.txt').write_text(avd_config.read_text())


def check(sdk_root, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    report = dict(requested_image=IMAGE, requested_api=37, android_release='17',
                  samsung_one_ui_emulated=False, application_test_passed=False,
                  observed_utc=datetime.now(timezone.utc).isoformat())
    command = [str(Path(sdk_root) / 'cmdline-tools/latest/bin/sdkmanager'),
               '--sdk_root=' + str(sdk_root), '--list', '--channel=0']
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        (out / 'sdkmanager-list.stdout.txt').write_text(result.stdout)
        (out / 'sdkmanager-list.stderr.txt').write_text(result.stderr)
        paths = {line.split('|')[0].strip() for line in result.stdout.splitlines()
                 if '|' in line}
        report.update(returncode=result.returncode,
                      api37_packages=sorted(p for p in paths if 'android-37' in p),
                      requested_image_available=IMAGE in paths)
        if result.returncode != 0:
            raise RuntimeError('SDK catalog query failed; inspect recorded stdout/stderr')
        if IMAGE not in paths:
            raise RuntimeError('Required API37 x86_64 Google APIs image is unavailable in this runner catalog; no lower API substituted')
        report['status'] = 'image_available_runtime_test_required'
    except Exception as error:
        report.update(status='blocked', failure=str(error))
        raise
    finally:
        (out / 'API37-SUPPORT.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk-root', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--pin-tools', action='store_true')
    parser.add_argument('--check-avd', action='store_true')
    args = parser.parse_args()
    if args.check_avd:
        check_avd(os.environ['ANDROID_AVD_HOME'], args.out)
    else:
        if args.pin_tools:
            pin_tools(args.sdk_root, args.out)
        print(json.dumps(check(args.sdk_root, args.out), sort_keys=True))
