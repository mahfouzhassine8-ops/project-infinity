#!/usr/bin/env python3
"""Add local Android exit evidence to the exact source-built Infinity 1.0.6 base.

Does not alter player teardown, codecs, JNI contract, UI, signing or version code.
Apply only in an isolated candidate build, after the existing 1.0.6 source steps.
No claim that diagnostic instrumentation fixes the reported post-stop crash.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    'tools/android/packaging/xbmc/src/Main.java.in':
        '4f902ac9c1dec21532c08b4041d83ca79bd898def3c350383b668fb4c18483ed',
    'cmake/scripts/android/Install.cmake':
        '0d0fdd0619ab0988c6f7ab371bb1456e83e30f26ae18517b8c60a1b04d8b26c5',
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def apply(source: Path) -> dict:
    replacements = {}
    before = {}
    for name, expected in FILES.items():
        data = (source / name).read_bytes()
        before[name] = digest(data)
        if before[name] != expected:
            raise ValueError('Not the pinned 1.0.6 source preimage: ' + name)
        text = data.decode('utf-8')
        if name.endswith('Main.java.in'):
            old = '    System.loadLibrary("@APP_NAME_LC@");'
            new = ('    // Collect previous-process evidence off the UI thread. No player access.\n'
                   '    InfinityExitDiagnostics.start(getApplicationContext());\n' + old)
        else:
            old = '                  src/InfinityCoreBridge.java\n'
            new = old + ('                  src/InfinityDiagnosticFiles.java\n'
                         '                  src/InfinityExitDiagnostics.java\n')
        if text.count(old) != 1:
            raise ValueError('Ambiguous source anchor: ' + name)
        replacements[name] = text.replace(old, new, 1).encode('utf-8')
    for name in ('InfinityDiagnosticFiles', 'InfinityExitDiagnostics'):
        destination = 'tools/android/packaging/xbmc/src/' + name + '.java.in'
        if (source / destination).exists():
            raise ValueError('Unexpected existing diagnostic source: ' + destination)
        replacements[destination] = (ROOT / 'patches/infinity-compat' / (name + '.java.in')).read_bytes()
    # Validate every precondition before modifying any input.
    for name, data in replacements.items():
        (source / name).write_bytes(data)
    return {'schema': 1, 'base': 'Infinity 1.0.6', 'diagnostics_only': True,
            'crash_fixed': False, 'android_device_tested': False,
            'changes': {n: {'before': before.get(n), 'after': digest(d)} for n, d in replacements.items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    receipt = apply(args.source)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + '\n')


if __name__ == '__main__':
    main()
