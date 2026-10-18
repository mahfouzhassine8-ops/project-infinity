#!/usr/bin/env python3
"""Use the unchanged approved probes with the explicitly locked 2103384 base.

The historical upgrade probe pins TEST3 (2103377). Only that input constant is
retargeted in memory; every original assertion, operation and receipt remains.
No source files are rewritten and no probe failure is caught or converted.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ORIGINAL = HERE.parent / 'android-checkpoint-shutdown/runtime-tests'
LOCKED_SHA = 'b571676731bb9bdccb25134c557be613e15cc9adaf77d6675dabc8e0586e54af'
ORIGINAL_HASHES = {
    'run_internal_observer_stage_case.py': '7385309a2348fedc221c776adc197965368adb401f34873d1bbe57fb98c7696b',
    'essential_android_probe.py': 'c8e928ad8025c920714a36e5cc3583ff8380aeb950e3a196252095bbc4998723',
    'observer_upgrade_android_probe.py': '518f5b063c284972db99d0faf52c76a2685231d1fa426900cc0a2fb6ffb7caa7',
}


def load_original(name):
    spec = importlib.util.spec_from_file_location('locked_' + name, ORIGINAL / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_inputs(args):
    for name, expected in ORIGINAL_HASHES.items():
        actual = hashlib.sha256((ORIGINAL / name).read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError('Approved probe source changed: ' + name)
    if hashlib.sha256(args.baseline_apk.read_bytes()).hexdigest() != LOCKED_SHA:
        raise RuntimeError('Baseline must be the exact protected 2103384 APK')
    if (args.expected_sha256 == LOCKED_SHA or
            hashlib.sha256(args.apk.read_bytes()).hexdigest() != args.expected_sha256):
        raise RuntimeError('Candidate identity mismatch or baseline substituted for candidate')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=('fresh', 'loaded'), required=True)
    for name in ('apk', 'baseline-apk', 'installed-addons', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--expected-sha256', required=True)
    args = parser.parse_args()
    verify_inputs(args)  # Reject all identity/source mismatches before any ADB operation.
    args.out.mkdir(parents=True, exist_ok=True)
    identity = load_original('run_internal_observer_stage_case')
    if args.case == 'fresh':
        identity.run_case(args.case, args.apk, args.baseline_apk,
                          args.installed_addons, args.out, args.expected_sha256)
        return
    upgrade = load_original('observer_upgrade_android_probe')
    if upgrade.TEST3_SHA != '4ec1e3b2cabb595d228bc07bae2c6b3073c5af12822c8e40b1ec505b00865bf8':
        raise RuntimeError('Unexpected historical probe baseline')
    (args.out / 'LOCKED-BASELINE-PARAMETER.json').write_text(json.dumps({
        'baseline_apk_sha256': LOCKED_SHA,
        'original_test3_sha256': upgrade.TEST3_SHA,
        'unchanged_probe_source_sha256': ORIGINAL_HASHES,
        'only_parameter_changed': 'TEST3_SHA',
        'shutdown_assertions_changed': False,
    }, indent=2) + '\n')
    upgrade.TEST3_SHA = LOCKED_SHA
    sys.argv = [str(ORIGINAL / 'observer_upgrade_android_probe.py'),
                '--scenario', 'loaded', '--early-boundary', 'owner',
                '--baseline-apk', str(args.baseline_apk), '--candidate-apk', str(args.apk),
                '--installed-addons', str(args.installed_addons), '--out', str(args.out)]
    upgrade.main()
    proof = identity.verify_report(args.case, args.out, args.expected_sha256)
    (args.out / 'INTERNAL-CASE-IDENTITY.json').write_text(json.dumps(proof, indent=2) + '\n')


if __name__ == '__main__':
    main()
