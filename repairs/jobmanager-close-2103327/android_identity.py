#!/usr/bin/env python3
"""Bind Android shutdown diagnostics to the exact 2103327 native engine."""
import argparse
import hashlib
import json
import re
from pathlib import Path

CANDIDATE = 2103327
PARENT = 2103326
LOCKED_ROLLBACK = 2103324
PARENT_MAP = '615b6445d67e4785f70ae1c4170e40d01cc0d9c6b61dc89cc8c9cde32e81432c'
OLD_NATIVE = 'ca4344d110ab2f6ae12270540d2d2f0c8db73d90243627f3ae926225fc081ae0'
OLD_ENGINE = 'infinity-shutdown-2103326-v1'
NEW_ENGINE = 'infinity-shutdown-2103327-v1'
HEALTH = 'tools/android/packaging/xbmc/src/InfinityHealthExport.java.in'
EXIT = 'tools/android/packaging/xbmc/src/InfinityExitDiagnostics.java.in'
ALLOWED = {HEALTH, EXIT}
PREIMAGES = {
    HEALTH: 'e2018ab82ab566d8744d66218cfd8e51a5b8453f7e258fa10dc3927218eabb81',
    EXIT: '8ba6f0ffd16b0aba42b3dacf143a235eeaab5c262014e097bf29b3d41aa35b74',
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def map_digest(value: dict[str, str]) -> str:
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())


def snapshot(source: Path) -> dict[str, str]:
    return {
        p.relative_to(source).as_posix(): sha(p.read_bytes())
        for p in source.rglob('*')
        if p.is_file() and '.git' not in p.relative_to(source).parts
    }


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def apply(source: Path, proof: Path, receipt: Path, native_sha: str) -> dict:
    require(re.fullmatch(r'[0-9a-f]{64}', native_sha) is not None,
            'Actual packaged native SHA-256 is required')
    expected = json.loads(proof.read_text())['after']
    require(map_digest(expected) == PARENT_MAP, 'Wrong complete 2103326 Android source map')
    before = snapshot(source)
    require(before == expected, 'Android source is not the exact passed 2103326 parent')
    for name, digest in PREIMAGES.items():
        require(before.get(name) == digest, 'Unexpected 2103326 Android preimage: ' + name)

    health = source / HEALTH
    text = health.read_text()
    require(text.count(OLD_NATIVE) == 1, 'Health exporter native identity preimage missing')
    require(text.count(OLD_ENGINE) == 1, 'Health exporter engine tag preimage missing')
    health.write_text(text.replace(OLD_NATIVE, native_sha, 1).replace(OLD_ENGINE, NEW_ENGINE, 1))

    exit_diagnostics = source / EXIT
    text = exit_diagnostics.read_text()
    require(text.count(OLD_NATIVE) == 1, 'Exit diagnostics native identity preimage missing')
    require(OLD_ENGINE not in text, 'Unexpected engine tag in exit diagnostics')
    exit_diagnostics.write_text(text.replace(OLD_NATIVE, native_sha, 1))

    after = snapshot(source)
    changed = {name for name in before.keys() | after.keys() if before.get(name) != after.get(name)}
    require(changed == ALLOWED, 'Undeclared Android identity delta: ' + repr(sorted(changed)))
    require(before.keys() == after.keys(), 'Unexpected Android source addition/removal')

    result = {
        'candidate': CANDIDATE,
        'parent': PARENT,
        'locked_rollback': LOCKED_ROLLBACK,
        'kind': 'android-identity',
        'before': before,
        'after': after,
        'changed': sorted(changed),
        'native_sha256': native_sha,
        'shutdown_trace_engine': NEW_ENGINE,
        'physical_device_verified': False,
        'locked': False,
    }
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    return result


def verify(source: Path, receipt: Path) -> None:
    result = json.loads(receipt.read_text())
    require(result['candidate'] == CANDIDATE and result['changed'] == sorted(ALLOWED),
            'Wrong Android identity receipt')
    require(snapshot(source) == result['after'], 'Android source changed after tests')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['apply', 'verify'])
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--proof', type=Path)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--native-sha')
    args = parser.parse_args()
    if args.mode == 'apply':
        require(args.proof is not None, 'apply requires --proof')
        require(args.native_sha is not None, 'apply requires --native-sha')
        apply(args.source, args.proof, args.receipt, args.native_sha)
    else:
        verify(args.source, args.receipt)
    print('PASS: exact 2103326 Android parent; 2103327 native identity and engine tag only')


if __name__ == '__main__':
    main()
