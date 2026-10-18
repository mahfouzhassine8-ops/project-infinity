#!/usr/bin/env python3
"""Record actual SDK support before running the unchanged candidate on API 37.

This only queries the runner's SDK catalog. Unavailable images are a recorded
infrastructure blocker, never a passed/skipped application qualification.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

# Observed SDK catalog in run 39124478854 publishes decimal platform IDs.
# This is the stable Android17 major release, not a fallback to another API.
IMAGE = 'system-images;android-37.0;google_apis;x86_64'


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
    args = parser.parse_args()
    print(json.dumps(check(args.sdk_root, args.out), sort_keys=True))
