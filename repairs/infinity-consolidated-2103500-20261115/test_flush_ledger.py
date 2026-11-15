#!/usr/bin/env python3
"""Compile exact signed500 native guard headers; run only flush-related cases."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
# The signed500 producer retained these exact unmodified headers from its
# explicitly recorded frozen build-tool source. Authenticate against its map.
PRODUCER = '9ce852ebb044a82853ef93af24e34a07ed96daff'
PREFIX = 'repairs/infinity-essential-only-shutdown-2103483-20261112/native/overlay/'
NATIVE = 'xbmc/platform/android/activity/'
CASES = ('baseline_closed', 'candidate_closed', 'optional_failure', 'real_failure',
         'prior_failure', 'dirty', 'transaction', 'unobserved', 'fsync_failure')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source_map', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    source_map = json.loads(args.source_map.read_bytes())
    host = json.loads((HERE / 'CLOSED-FLUSH-HOST.json').read_bytes())
    assert host['results']['baseline'][0]['new_failures'] == ['buffer_flush_failed']
    assert host['results']['candidate'][0]['new_failures'] == []
    with tempfile.TemporaryDirectory(prefix='infinity500-ledger-', dir='/dev/shm') as temp:
        temp = Path(temp)
        headers = {}
        for name in ('InfinityScriptPersistence.h', 'InfinityProtectedWrites.h'):
            path = NATIVE + name
            raw = subprocess.check_output(['git', 'show', PRODUCER + ':' + PREFIX + path], cwd=ROOT)
            digest = hashlib.sha256(raw).hexdigest()
            assert digest == source_map[path], path
            (temp / name).write_bytes(raw)
            headers[path] = digest
        binary = temp / 'ledger'
        subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', '-pthread',
                        '-I' + str(temp), str(HERE / 'test_flush_ledger.cpp'), '-o', str(binary)], check=True)
        results = []
        for scenario in CASES:
            output = subprocess.check_output([str(binary), scenario, str(temp / scenario)], text=True, timeout=10)
            results.append({'case': scenario, 'result': output.strip()})
        receipt = dict(status='PASS_HOST_NATIVE_LEDGER_CALLBACK_REPLAY', source_headers=headers,
                       cases=results, actual_embedded_CPython_native_bridge='NOT_EXECUTED',
                       ARM64='NOT_EXECUTED', Android_process_termination='NOT_EXECUTED',
                       physical_incident_root_cause='NOT_ESTABLISHED')
        args.out.write_text(json.dumps(receipt, indent=2) + '\n')
        print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
