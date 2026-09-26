#!/usr/bin/env python3
"""Run the current 113 offline regressions against hash-verified audit sources."""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import lzma
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

PAYLOAD_SHA = '2c00aeef3586666c1f4f497cff11d9b5feda7a92f4a538721771f430354a861d'
EXPECTED = {
    'candidate/script.kodihealthcenter/khc_dependency.py',
    'candidate/script.kodihealthcenter/khc_download.py',
    'candidate/script.kodihealthcenter/khc_safety.py',
    'candidate/script.infinity.authsurface/repair_core.py',
    'candidate/script.infinity.authsurface/default.py',
    'candidate/script.infinity.authsurface/addon.xml',
    'tests/test_followup.py', 'tests/test_core_retained.py',
    'health-functions.json', 'component-deltas.json', 'source-preservation-summary.json',
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--payload', type=Path, default=Path(__file__).resolve().parent/'payload')
    p.add_argument('--previous', type=Path, default=Path('audit-output/review-source'))
    p.add_argument('--upstream', type=Path, default=Path('audit-output/upstream-review'))
    p.add_argument('--output', type=Path, default=Path('audit-output/followup-review'))
    args = p.parse_args()
    if args.output.exists() or args.output.is_symlink():
        raise ValueError('Review destination must be new; no existing files are overwritten')
    parts = [args.payload/('part%02d' % i) for i in range(4)]
    if set(args.payload.glob('part*')) != set(parts) or any(x.is_symlink() for x in parts):
        raise ValueError('Unexpected source payload parts')
    encoded = ''.join(x.read_text(encoding='ascii') for x in parts)
    if len(encoded) > 100000:
        raise ValueError('Encoded source limit exceeded')
    compressed = base64.b64decode(encoded, validate=True)
    if digest(compressed) != PAYLOAD_SHA:
        raise ValueError('Reviewed source payload hash mismatch')
    decoder = lzma.LZMADecompressor(memlimit=128*1024*1024)
    raw = decoder.decompress(compressed, max_length=2*1024*1024)
    if not decoder.eof or decoder.unused_data:
        raise ValueError('Source exceeds limit or contains trailing bytes')
    sources = json.loads(raw)
    if not isinstance(sources, dict) or set(sources) != EXPECTED:
        raise ValueError('Source allowlist mismatch')
    for name, text in sources.items():
        if not isinstance(text, str):
            raise ValueError('Source must be UTF-8 text')
        if name.endswith('.py'):
            compile(text, name, 'exec')
    deltas = json.loads(sources['component-deltas.json'])['components']
    for name, item in json.loads(sources['health-functions.json']).items():
        if digest(item['source'].encode()) != item['function_sha256']:
            raise ValueError('Exact tested function changed: '+name)
        expected = deltas['script.kodihealthcenter']['files'][item['source_file']]['after_sha256']
        if expected != item['source_file_sha256']:
            raise ValueError('Function provenance does not match distribution delta')
    for name, text in sources.items():
        if name.startswith('candidate/'):
            _, component, relative = name.split('/', 2)
            change = deltas[component]['files'].get(relative)
            if change is not None and digest(text.encode()) != change['after_sha256']:
                raise ValueError('Candidate source does not match distribution delta: '+name)
    args.output.mkdir(parents=True, exist_ok=False)
    for name, text in sources.items():
        target = args.output/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')
    # These modules are unchanged from the independently verified first batch.
    for name in ('candidate/script.kodihealthcenter/khc_native.py',
                 'candidate/script.infinity.authsurface/repair_transaction.py'):
        data = (args.previous/name).read_bytes()
        _, component, relative = name.split('/', 2)
        if digest(data) != deltas[component]['files'][relative]['after_sha256']:
            raise ValueError('Retained module identity differs: '+name)
        (args.output/name).write_bytes(data)
    receipt = json.loads((args.upstream/'SOURCE-RECEIPT.json').read_text())
    if receipt['git_blob_sha1'] != 'b9de2983bd5785c14c9bdf9aabbe12fe9783cbda':
        raise ValueError('AM Lite source archive identity differs')
    for name, expected in receipt['files'].items():
        if digest((args.upstream/name).read_bytes()) != expected:
            raise ValueError('AM Lite source changed after acquisition: '+name)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1',
               INFINITY_FOLLOWUP_ROOT=str(args.output.resolve()),
               INFINITY_UPSTREAM_ROOT=str(args.upstream.resolve()),
               INFINITY_PREVIOUS_CORE=str((args.previous/'candidate/script.infinity.authsurface/repair_core.py').resolve()))
    for name, count in (('test_core_retained.py', 55), ('test_followup.py', 58)):
        result = subprocess.run([sys.executable, str(args.output/'tests'/name)],
                                env=env, capture_output=True, text=True, timeout=120, check=False)
        log = result.stdout + result.stderr
        (args.output/(name+'.log')).write_text(log, encoding='utf-8')
        print(log, end='')
        if result.returncode or not re.search(r'Ran '+str(count)+r' tests\b', log) or not re.search(r'^OK\s*$', log, re.M):
            raise RuntimeError('Regression gate failed: '+name)
    result = {
        'schema': 1, 'current_tests_passed': 113, 'retained_tests': 55, 'followup_tests': 58,
        'source_payload_sha256': PAYLOAD_SHA, 'scope': 'offline source and mocked integration',
        'previous_60_tests_overlap_not_additive': True, 'device_verified': False,
        'live_trakt_verified': False, 'native_fd_crash_fixed': False,
        'new_apk_built': False, 'cobra_changed': False, 'shipping_audit_complete': False,
        'health_center_version': '2.5.17', 'accounts_version': '0.5.2',
        'health_center_zip_sha256': 'f659173c224bae64534cd27cd904416d45fdbd7bb5bc9861f2cc98113b647640',
        'accounts_zip_sha256': '2efbdfd842738b720220009db2e08a9644dd479113480f9987934937c48ab894',
        'zip_checks_scope': 'local delivery archives; full component sources reconstruct from exact baseline plus delta',
        'final_stage': 'source-preservation-audit', 'release_approved': False,
    }
    (args.output/'followup-verification.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
