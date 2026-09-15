#!/usr/bin/env python3
"""Whole-release Infinity certification gate.

Static CI is necessary but not sufficient. This gate stays red until release packaging,
exact-artifact assembly, first-party device acceptance, and provider playback coverage
are all explicitly observed and recorded.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / 'stability' / 'runtime-acceptance.json'

PASS = 'pass'


def walk_checks(prefix, value, blockers):
    if isinstance(value, dict):
        for key, item in value.items():
            walk_checks(f'{prefix}.{key}' if prefix else key, item, blockers)
    elif value in {'pending', 'fail'}:
        blockers.append({'gate': prefix, 'status': value})


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--state', type=Path, default=STATE)
    p.add_argument('--report', type=Path, default=ROOT / 'release-certification-report.json')
    p.add_argument('--strict', action='store_true')
    args = p.parse_args()
    state = json.loads(args.state.read_text())
    blockers = []

    pipeline = state['release_pipeline']
    required_pipeline = {
        'candidate2_preflight': 'pass',
        'candidate2_native_build': 'pass',
        'candidate2_packaging': 'pass',
        'candidate2_signing': 'pass',
        'exact_signing_failure_reconciled': True,
        'final_apk_signature_verified': True,
        'final_apk_update_identity_verified': True,
    }
    for key, expected in required_pipeline.items():
        if pipeline.get(key) != expected:
            blockers.append({'gate': 'release_pipeline.' + key, 'status': pipeline.get(key), 'required': expected})

    for addon in state.get('first_party', []):
        addon_id = addon.get('addon_id', 'unknown')
        for key, value in addon.items():
            if key in {'addon_id', 'version', 'artifact_status'}:
                continue
            if value != PASS:
                blockers.append({'gate': f'first_party.{addon_id}.{key}', 'status': value, 'required': PASS})

    declared = set(state.get('providers', []))
    checks = state.get('provider_checks', {})
    if declared != set(checks):
        blockers.append({'gate': 'providers.inventory', 'status': 'mismatch', 'missing_checks': sorted(declared - set(checks)), 'undeclared_checks': sorted(set(checks) - declared)})
    for provider in sorted(declared):
        for key, value in checks.get(provider, {}).items():
            if value != PASS:
                blockers.append({'gate': f'providers.{provider}.{key}', 'status': value, 'required': PASS})

    for fault, value in state.get('separate_fault_classes', {}).items():
        if fault == 'rule':
            continue
        if value != PASS:
            blockers.append({'gate': 'fault_classes.' + fault, 'status': value, 'required': PASS})

    report = {
        'schema': 1,
        'release_certified': not blockers,
        'blocker_count': len(blockers),
        'blockers': blockers,
        'note': 'A green static audit does not override this runtime/release gate.'
    }
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'release_certified': report['release_certified'], 'blocker_count': len(blockers)}))
    for item in blockers:
        print('[BLOCK] ' + item['gate'] + ' = ' + repr(item.get('status')))
    if args.strict and blockers:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
