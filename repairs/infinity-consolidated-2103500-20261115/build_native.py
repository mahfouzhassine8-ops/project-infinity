#!/usr/bin/env python3
"""Reproduce signed500's native source, then apply only the reviewed flush fix.

Historical tools reconstruct provenance, not an older application payload.
The entire reconstructed map must equal the authenticated signed500 map before
the sole candidate header is applied. No APK, profile or signing key is used.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / 'native500-output'
TOOLS = ROOT / 'native500-frozen-tools'
FROZEN = '9ce852ebb044a82853ef93af24e34a07ed96daff'
PRODUCER = '16df356f0acffbf9ca28ab7095f3a21233998d6d'
BRANCH = 'work/infinity-2103500-consolidated-repair-20261115'
OLD = 'repairs/infinity-essential-only-shutdown-2103483-20261112'
CAST = 'repairs/infinity-movies-continue-cast-2103486-20261112/native/overlay/'
OBSERVER = 'xbmc/interfaces/python/InfinityPythonPersistenceSource.h'
ENGINE = '3caccc96c23336e220b791118989f3a850b73fa8804267fb7beb2aad3b3afc75'
MAP = '26525c76540cd62fbc483b4d4ec2eb2579ef595a64f2fe564859131139498f1c'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(name, value):
    OUT.mkdir(exist_ok=True)
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def blob(ref, path):
    return subprocess.check_output(['git', 'show', ref + ':' + path], cwd=ROOT)


def gate():
    assert os.environ.get('GITHUB_ACTIONS') == 'true'
    assert os.environ['GITHUB_REPOSITORY'] == 'mahfouzhassine8-ops/project-infinity'
    assert os.environ['GITHUB_REF'] == 'refs/heads/' + BRANCH
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == os.environ['GITHUB_SHA']
    load(HERE / 'verify_scope.py', 'native500_source_gate').main()
    base = json.loads((HERE / 'BASELINE.json').read_text())
    assert base['versionCode'] == 2103500 and base['native_engine_sha256'] == ENGINE
    assert base['source_maps']['native_map_sha256'] == MAP
    assert sha(ROOT / 'baseline500-native/libkodi.so') == ENGINE
    assert sha(ROOT / 'baseline500-native/NATIVE-SOURCE-MAP.json') == MAP
    receipt = json.loads((ROOT / 'baseline500-native/CAST-ARM64.json').read_text())
    assert receipt['native_sha256'] == ENGINE and receipt['source'] == PRODUCER


def retained():
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=TOOLS, text=True).strip() == FROZEN
    path = TOOLS / OLD / 'build_native.py'
    assert path.read_bytes() == blob(FROZEN, OLD + '/build_native.py')
    module = load(path, 'frozen500_source_provenance')
    module.scope = gate
    module.OUT = OUT
    return module


def hasher():
    return load(TOOLS / 'repairs/infinity-native-touch-2103451-20261105/compile_only.py', 'native500_hasher')


def prepare():
    gate()
    assert not TOOLS.exists()
    subprocess.run(['git', 'worktree', 'add', '--detach', '--no-checkout', str(TOOLS), FROZEN], cwd=ROOT, check=True)
    subprocess.run(['git', 'sparse-checkout', 'init', '--no-cone'], cwd=TOOLS, check=True)
    names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', FROZEN], cwd=ROOT, text=True).splitlines()
    suffixes = {'.py', '.sh', '.json', '.java', '.in', '.h', '.hpp', '.cpp', '.c', '.txt', '.patch', '.xml', '.pem', '.sig', '.v1', '.cmake', '.yml', '.md'}
    selected = [n for n in names if Path(n).suffix in suffixes or Path(n).name == 'CMakeLists.txt']
    subprocess.run(['git', 'sparse-checkout', 'set', '--no-cone', '--stdin'], input=''.join('/' + n + '\n' for n in selected), cwd=TOOLS, text=True, check=True)
    subprocess.run(['git', 'checkout'], cwd=TOOLS, check=True)
    for name in ('verified-inputs', 'previous-review', 'exact464', 'signed80'):
        (TOOLS / name).symlink_to(ROOT / name, target_is_directory=True)
    retained().prepare()
    native = TOOLS / 'kodi'
    # These are the exact three Cast integration inputs used by the signed500
    # native producer. They are not taken from a current or historical APK.
    for name in ('xbmc/platform/android/activity/InfinityCastNative.cpp',
                 'xbmc/platform/android/activity/CMakeLists.txt',
                 'xbmc/interfaces/builtins/AndroidBuiltins.cpp'):
        (native / name).write_bytes(blob(PRODUCER, CAST + name))
    expected = json.loads((ROOT / 'baseline500-native/NATIVE-SOURCE-MAP.json').read_text())
    assert len(expected) == 9413 and hasher().hashes(native) == expected, 'Exact500 source preimage mismatch'
    save('BASE500-NATIVE-SOURCE-MAP.json', expected)
    row = next(r for r in json.loads((HERE / 'SCOPE.json').read_text())['production_allowlist'] if r.get('native_path') == OBSERVER)
    assert sha(native / OBSERVER) == expected[OBSERVER] == row['baseline_sha256']
    candidate = HERE / 'native/overlay' / OBSERVER
    (native / OBSERVER).write_bytes(candidate.read_bytes())
    after = dict(expected)
    after[OBSERVER] = sha(candidate)
    assert after[OBSERVER] != expected[OBSERVER]
    assert hasher().hashes(native) == after
    save('NATIVE-SOURCE-MAP.json', after)
    save('SOURCE-PRESERVATION.json', dict(
        status='PASS_EXACT_SIGNED500_SOURCE_PLUS_ONE_REVIEWED_OBSERVER_HEADER',
        source=os.environ['GITHUB_SHA'], baseline_native_sha256=ENGINE,
        baseline_source_map_sha256=MAP, unchanged_native_files=9412,
        changed={OBSERVER: dict(before=expected[OBSERVER], after=after[OBSERVER])},
        Cast_native='UNCHANGED', Cobra='UNCHANGED', Python_startup='UNCHANGED',
        admission_SQLite_durability_guards='UNCHANGED', Android_execution='NOT_RUN', signed=False))


def with_tools(action):
    previous = os.environ.get('GITHUB_WORKSPACE')
    os.environ['GITHUB_WORKSPACE'] = str(TOOLS)
    try:
        return action()
    finally:
        if previous is None:
            os.environ.pop('GITHUB_WORKSPACE', None)
        else:
            os.environ['GITHUB_WORKSPACE'] = previous


def dependencies():
    gate()
    with_tools(retained().dependencies)


def compile_native():
    gate()
    expected = json.loads((OUT / 'NATIVE-SOURCE-MAP.json').read_text())
    assert len(expected) == 9413
    compiler = load(TOOLS / 'repairs/universal-persistence-2103401/build.py', 'frozen500_arm64_compiler')
    compiler.OUT = OUT
    original = compiler.checked_sources

    def checked(root, pins, allow_generated=False):
        extra = original(root, pins, allow_generated=True)
        if not allow_generated:
            assert Path(root) == TOOLS / 'kodi' and pins == expected
            assert all(n.startswith('tools/depends/') for n in extra), extra
        return extra

    compiler.checked_sources = checked
    proof = with_tools(compiler.compile_engine)
    assert proof['complete_native_engine_compiled'] and proof['reviewed_file_count'] == 9413
    library = OUT / 'libkodi.so'
    assert sha(library) == proof['native_sha256']
    readelf = Path(os.environ['ANDROID_HOME']) / 'ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readelf'

    def abi(path):
        header = subprocess.check_output([readelf, '-h', path], text=True)
        assert all(s in header for s in ('ELF64', 'AArch64', 'DYN'))
        dynamic = subprocess.check_output([readelf, '-d', path], text=True)
        rows = subprocess.check_output([readelf, '--dyn-syms', '--wide', path], text=True).splitlines()
        symbols = set()
        for line in rows:
            fields = line.split()
            if len(fields) >= 8 and fields[4] in ('GLOBAL', 'WEAK') and fields[5] in ('DEFAULT', 'PROTECTED') and fields[6] != 'UND':
                symbols.add((fields[7], fields[3], fields[4], fields[5]))
        return symbols, set(re.findall(r'Shared library: \[([^\]]+)\]', dynamic))

    before, after = abi(ROOT / 'baseline500-native/libkodi.so'), abi(library)
    removed, added = before[0] - after[0], after[0] - before[0]
    save('ABI-COMPARISON.json', dict(removed=sorted(removed), added=sorted(added),
                                   dependencies_before=sorted(before[1]), dependencies_after=sorted(after[1])))
    assert before == after, 'Native exports/dependencies changed; review required'
    save('ARM64.json', dict(status='PASS_FULL_ARM64_LINK_AND_EXACT500_ABI',
        source=os.environ['GITHUB_SHA'], baseline_native_sha256=ENGINE,
        native_sha256=sha(library), exported_interfaces_preserved=len(after[0]),
        dependencies=sorted(after[1]), Android_execution='NOT_RUN', signed=False,
        application_acceptance=False, physical_Fold_acceptance=False))


if __name__ == '__main__':
    assert len(sys.argv) == 2
    {'prepare': prepare, 'dependencies': dependencies, 'compile': compile_native}[sys.argv[1]]()
