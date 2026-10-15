#!/usr/bin/env python3
"""Retain the exact protected baseline and completed integration asset gates."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
import verify_2103367 as integration
from packaging_checks import require

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('baseline', 'candidate', 'report'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    require(hashlib.sha256(args.baseline.read_bytes()).hexdigest() == integration.baseline.BASELINE_SHA,
            'Wrong protected baseline APK')
    with zipfile.ZipFile(args.baseline) as baseline, zipfile.ZipFile(args.candidate) as candidate:
        result = integration.compare(baseline, candidate)
    result['candidate_version'] = 2103368
    args.report.write_text(json.dumps(result, indent=2) + '\n')
    print('PASS 2103368 exact protected 2103365 payload and completed integration assets')
