#!/usr/bin/env python3
"""Verify and unpack the reviewed audit source; run offline tests, not an APK build."""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import lzma
import re
import subprocess
import sys
from pathlib import Path

PAYLOAD_SHA = 'fedca0939214d589f7d316afa82da1de5bfd0b75184b8bf94398dcdbe0b917ef'
EXPECTED = {
    'candidate/script.kodihealthcenter/khc_native.py',
    'candidate/script.kodihealthcenter/khc_download.py',
    'candidate/script.infinity.authsurface/repair_transaction.py',
    'candidate/script.infinity.authsurface/repair_core.py',
    'tests/test_core.py', 'component-deltas.json', 'stage_identity_fix.py',
}


def unpack(payload: Path, output: Path) -> None:
    """Decode only exact reviewed paths into a NEW, non-installed output folder."""
    if output.exists() or output.is_symlink():
        raise ValueError('Review output must be new; existing files are not overwritten')
    parts = [payload / ('part%02d' % i) for i in range(3)]
    if set(payload.glob('part*')) != set(parts) or any(p.is_symlink() for p in parts):
        raise ValueError('Unexpected payload parts')
    encoded = ''.join(p.read_text(encoding='ascii') for p in parts)
    if len(encoded) > 100000:
        raise ValueError('Payload encoding exceeds limit')
    compressed = base64.b64decode(encoded, validate=True)
    if hashlib.sha256(compressed).hexdigest() != PAYLOAD_SHA:
        raise ValueError('Reviewed source payload SHA-256 mismatch')
    decoder = lzma.LZMADecompressor(memlimit=128 * 1024 * 1024)
    data = decoder.decompress(compressed, max_length=2 * 1024 * 1024)
    if not decoder.eof or decoder.unused_data:
        raise ValueError('Payload is too large or has trailing data')
    sources = json.loads(data)
    if not isinstance(sources, dict) or set(sources) != EXPECTED:
        raise ValueError('Payload source allowlist mismatch')
    if any(not isinstance(v, str) for v in sources.values()):
        raise ValueError('Payload content must be UTF-8 source text')
    for name, text in sources.items():
        if name.endswith('.py'):
            compile(text, name, 'exec')
    output.mkdir(parents=True, exist_ok=False)
    for name, text in sources.items():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--payload', type=Path, default=Path(__file__).resolve().parent/'payload')
    parser.add_argument('--source', type=Path, default=Path.cwd())
    parser.add_argument('--apk', type=Path, default=Path('audit-input/candidate/Infinity-1.0.9-Python-Runtime-Native-Repair-RC1.apk'))
    parser.add_argument('--output', type=Path, default=Path('audit-output'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    review = args.output/'review-source'
    unpack(args.payload, review)
    result = subprocess.run([sys.executable, str(review/'tests/test_core.py')],
                            capture_output=True, text=True, timeout=120, check=False)
    text = result.stdout + result.stderr
    (args.output/'core-regression-tests.txt').write_text(text, encoding='utf-8')
    print(text, end='')
    if result.returncode or not re.search(r'Ran 60 tests\b', text) or not re.search(r'^OK\s*$', text, re.M):
        raise RuntimeError('The 60-test core regression gate did not pass cleanly')
    subprocess.run([sys.executable, str(review/'stage_identity_fix.py'),
                    '--source', str(args.source), '--apk', str(args.apk),
                    '--output', str(args.output/'identity-only-stage')], check=True, timeout=120)
    receipt = {
        'schema': 1, 'source_payload_sha256': PAYLOAD_SHA, 'core_regression_tests': 60,
        'core_regression_result': 'PASS', 'test_scope': 'offline synthetic and source tests',
        'full_local_suite': '82 checks; separate local evidence, not 82 CI tests',
        'native_identity_patch': 'staged only', 'android_native_compilation': 'not run',
        'new_apk_built': False, 'cobra_changed': False, 'device_verified': False,
        'shipping_audit_complete': False, 'final_stage': 'source-preservation-audit',
        'release_blockers': ['native FD_SET cause and fix unverified',
                             'live provider Trakt refresh unverified',
                             'physical-device acceptance pending'],
    }
    (args.output/'regression-verification.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
