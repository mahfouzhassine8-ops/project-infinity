#!/usr/bin/env python3
"""Run one unchanged disposable Android probe against the same internal APK."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
CASES = ('fresh', 'cold', 'core-initialized', 'loaded')


def command_for(case, apk, baseline, addons, out):
    if case not in CASES:
        raise ValueError('Unknown internal shutdown case: '+str(case))
    common = ['--installed-addons', str(addons), '--out', str(out)]
    if case == 'fresh':
        return [sys.executable, str(HERE/'essential_android_probe.py'), '--apk', str(apk),
                '--require-java-save-proof', *common]
    return [sys.executable, str(HERE/'observer_upgrade_android_probe.py'),
            '--scenario', 'loaded' if case == 'loaded' else 'early',
            '--early-boundary', 'core-initialized' if case == 'core-initialized' else 'owner',
            '--baseline-apk', str(baseline), '--candidate-apk', str(apk), *common]


def verify_report(case, out, expected_sha):
    if case not in CASES:
        raise ValueError('Unknown internal shutdown case: '+str(case))
    fresh = case == 'fresh'
    name = 'ANDROID-PROCESS-PROBE.json' if fresh else 'OBSERVER-UPGRADE-PROBE.json'
    report = json.loads((out/name).read_text())
    key = 'apk_sha256' if fresh else 'candidate_apk_sha256'
    if report.get(key) != expected_sha or report.get('passed') is not True:
        raise RuntimeError('Internal candidate identity or probe result failed: '+case)
    if not fresh:
        scenario = 'loaded' if case == 'loaded' else 'early'
        boundary = 'core-initialized' if case == 'core-initialized' else 'owner'
        if report.get('scenario') != scenario or report.get('early_boundary') != boundary:
            raise RuntimeError('Wrong internal shutdown phase: '+case)
    if report.get('physical_fold_accepted') is not False:
        raise RuntimeError('Disposable probe cannot establish physical Fold acceptance')
    return dict(case=case, apk_sha256=expected_sha, original_probe_report=name,
                passed=True, apk_deliverable=False, physical_fold_accepted=False,
                final_lock_authorized=False)


def run_case(case, apk, baseline, addons, out, expected_sha):
    if hashlib.sha256(apk.read_bytes()).hexdigest() != expected_sha:
        raise RuntimeError('APK changed before Android probe')
    subprocess.run(command_for(case, apk, baseline, addons, out), check=True)
    proof = verify_report(case, out, expected_sha)
    (out/'INTERNAL-CASE-IDENTITY.json').write_text(json.dumps(proof, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=CASES, required=True)
    parser.add_argument('--apk', type=Path, required=True)
    parser.add_argument('--baseline-apk', type=Path, required=True)
    parser.add_argument('--installed-addons', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--expected-sha256', required=True)
    args = parser.parse_args()
    run_case(args.case, args.apk, args.baseline_apk, args.installed_addons, args.out, args.expected_sha256)
