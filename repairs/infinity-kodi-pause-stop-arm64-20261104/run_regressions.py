"""Run the selected existing host regressions against exact integrated source inputs."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PRIOR = ROOT / 'repairs/infinity-kodi-checkpoint-pause-stop-20261104'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--map', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    expected = json.loads(args.map.read_text())
    original = json.loads((PRIOR / 'evidence/HOST-RESULTS.json').read_text())
    delta = json.loads((PRIOR / 'SOURCE-DELTA.json').read_text())
    bindings = dict(original['source_bindings'], **delta['after'])
    for name, digest in bindings.items():
        assert sha(args.native / name) == expected[name] == digest, name
    cpp = PRIOR / 'evidence/after.cpp'
    assert sha(cpp) == original['after_compile']['harness_cpp_sha256']
    executable = args.out / 'controls'
    command = ['g++', '-std=c++17', '-pthread', '-Wall', '-Wextra', '-Werror',
               '-DTARGET_ANDROID', str(cpp), '-o', str(executable)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=60)
    (args.out / 'COMPILE.txt').write_text(result.stdout + result.stderr)
    assert result.returncode == 0, result.stderr
    results = []
    selected = json.loads((PRIOR / 'SELECTED-TESTS.json').read_text())['cases_after']
    assert len(selected) == 15
    for case in selected:
        result = subprocess.run([str(executable), 'after', case], capture_output=True, text=True, timeout=15)
        row = {'case': case, 'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
        results.append(row)
        (args.out / 'CONTROL-RESULTS.json').write_text(json.dumps({
            'integrated_source_bindings': bindings, 'original_harness_sha256': sha(cpp),
            'source_map_sha256': sha(args.map), 'host_only': True,
            'android_verified': False, 'cases': results}, indent=2) + '\n')
        print(result.stdout, end='', flush=True)
        assert result.returncode == 0, row
    watched = ROOT / 'repairs/infinity-kodi-2103451-checkpoint-anr/test_watched_repair.py'
    command = ['python3', str(watched), '--source', str(args.native), '--inputs', '/tmp/kodi451-p0-inputs',
               '--out', str(args.out / 'watched'), '--database-barrier',
               str(args.native / 'xbmc/dbwrappers/InfinityDatabaseBarrier.h'),
               '--full-native-map', str(args.map), '--test-protected-resources', '--cases', 'commit-failure', 'close-failure',
               'unknown-job', 'callback-failure', 'unknown-pvr']
    result = subprocess.run(command, capture_output=True, text=True, timeout=90)
    (args.out / 'WATCHED-OUTPUT.txt').write_text(result.stdout + result.stderr)
    print(result.stdout, end='', flush=True)
    assert result.returncode == 0, result.stderr
    (args.out / 'REGRESSION-SUMMARY.json').write_text(json.dumps({
        'existing_control_cases_passed': 15, 'existing_durability_cases_passed': 5,
        'android_runtime_verified': False, 'physical_fold_verified': False,
        'real_sqlite_test_files_only': True, 'apk_created': False}, indent=2) + '\n')


if __name__ == '__main__':
    main()
