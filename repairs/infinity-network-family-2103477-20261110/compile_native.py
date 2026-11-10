"""Signed77 native foundation plus scoped networking; no key, APK or app tests."""
import argparse
import builtins
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / 'network-native-evidence'
BASE = 'daf205b5'
BRANCH = 'refs/heads/work/infinity-network-family-from-2103477-20261109'
BASE_NATIVE = 'ee3be7c7a95b86f8357539001fcd50bedbd80217b02f130d649f7f57e6075794'
BASE_APK = '93eb081cd6a86ff9cf1cb9aa75bc6d9087cd9c982fb46e0a9baa12c12aa9af22'
BASE_MAP = 'f48df24caabdf36fee25d69d47b0a2ad3c98df3936949c8dcd6d07a92e2f0412'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(name, value):
    OUT.mkdir(exist_ok=True)
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scope():
    assert os.environ['GITHUB_REPOSITORY'] == 'mahfouzhassine8-ops/project-infinity'
    assert os.environ['GITHUB_REF'] == BRANCH
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip() == os.environ['GITHUB_SHA']
    pins = json.loads((HERE / 'SOURCE-PINS.json').read_text())
    for group, values in pins.items():
        for path, digest in values.items():
            assert sha(HERE / group / path) == digest, path
    changed = subprocess.check_output(['git', 'diff', '--name-only', BASE, 'HEAD'], text=True).splitlines()
    assert all(n.startswith(HERE.relative_to(ROOT).as_posix() + '/') or
               n.startswith('handoffs/infinity-network-family-20261109/') or
               n == '.github/workflows/infinity-combined-release.yml' for n in changed), changed
    old = subprocess.check_output(['git', 'show', BASE + ':.github/workflows/infinity-combined-release.yml'], text=True)
    now = (ROOT / '.github/workflows/infinity-combined-release.yml').read_text()
    prefix = now.split('\n  verify-network-native:\n')[0].rstrip()
    assert prefix == old.rstrip().replace('sign-tracking]', 'sign-tracking, verify-network-native]')
    assert 'secrets.' not in now.split('\n  verify-network-native:\n')[1]
    return pins


def prepare():
    pins = scope()
    # Reuse the exact source restoration that produced the native engine now
    # carried unchanged in signed77. Never apply rejected468 source overlays.
    retained = load(ROOT / 'repairs/infinity-three-corrections-20261108/compile_native.py', 'native77_foundation')
    retained.OUT = OUT
    retained.scope = scope
    retained.prepare()
    map_path = ROOT / 'repairs/infinity-watchlist-playback-2103466-20261108/contract-evidence/BASE466-NATIVE-SOURCE-MAP.json'
    assert sha(map_path) == BASE_MAP
    expected = json.loads(map_path.read_text())
    assert json.loads((OUT / 'NATIVE-SOURCE-MAP.json').read_text()) == expected
    with ZipFile(ROOT / 'signed77/Infinity-2103477-Combined-Original-Signer.apk') as archive:
        assert sha(ROOT / 'signed77/Infinity-2103477-Combined-Original-Signer.apk') == BASE_APK
        (OUT / 'baseline77-libkodi.so').write_bytes(archive.read('lib/arm64-v8a/libkodi.so'))
    assert sha(OUT / 'baseline77-libkodi.so') == BASE_NATIVE
    proposed = dict(expected)
    for name, digest in pins['native'].items():
        dest = ROOT / 'kodi' / name
        if name in expected:
            assert sha(dest) == expected[name]
        else:
            assert name == 'xbmc/filesystem/InfinityNetworkFamily.h' and not dest.exists()
        shutil.copyfile(HERE / 'native' / name, dest)
        proposed[name] = digest
    hasher = load(ROOT / 'repairs/infinity-native-touch-2103451-20261105/compile_only.py', 'native77_hasher')
    assert hasher.hashes(ROOT / 'kodi') == proposed
    save('BASE77-NATIVE-SOURCE-MAP.json', expected)
    save('NATIVE-SOURCE-MAP.json', proposed)
    save('SOURCE-PRESERVATION.json', dict(baseline_versionCode=2103477,
         baseline_APK_sha256=BASE_APK, baseline_engine_sha256=BASE_NATIVE,
         native_delta={n:dict(before=expected.get(n), after=v) for n,v in pins['native'].items()},
         unchanged_native_source_count=len(expected)-len(set(expected)&set(pins['native'])),
         source_commit=os.environ['GITHUB_SHA'], APK=False, signing=False,
         application_tests=False, shutdown_tests=False))


def compile_objects():
    pins = scope()
    recipe = load(ROOT / 'repairs/infinity-native-touch-2103451-20261105/compile_only.py', 'selected77_network_compiler')
    recipe.OUT = OUT
    code = inspect.getsource(recipe.compile_objects)
    original = "wanted={'xbmc/guilib/GUIBaseContainer.cpp','xbmc/input/InputManager.cpp'}"
    wanted = sorted(n for n in pins['native'] if n.endswith('.cpp'))
    assert len(wanted) == 4 and code.count(original) == 1 and code.count('len(selected)==2') == 1
    code = code.replace(original, 'wanted=' + repr(set(wanted))).replace('len(selected)==2', 'len(selected)==4')
    code = code.replace('Two real ARM64 Android translation units compiled', 'Four real ARM64 Android network translation units compiled')
    exec(builtins.compile(code, '<retained-selected-network-objects>', 'exec'), recipe.__dict__)
    recipe.compile_objects()


def link():
    scope()
    sys.path.insert(0, str(ROOT / 'repairs/universal-persistence-2103401'))
    recipe = load(ROOT / 'repairs/universal-persistence-2103401/build.py', 'native77_full_link')
    expected = json.loads((OUT / 'NATIVE-SOURCE-MAP.json').read_text())
    recipe.checked_sources(ROOT / 'kodi', expected, allow_generated=True)
    build = Path(os.environ['BUILD_DIR'])
    cache = dict(line.split('=', 1) for line in (build / 'CMakeCache.txt').read_text().splitlines() if '=' in line)
    subprocess.run([cache['CMAKE_COMMAND:INTERNAL'], '--build', str(build), '--target', 'kodi',
                    '--parallel', str(os.cpu_count() or 1)], check=True)
    generated = recipe.checked_sources(ROOT / 'kodi', expected, allow_generated=True)
    libs = list(build.rglob('libkodi.so'))
    assert len(libs) == 1 and not list(ROOT.glob('*.apk'))
    shutil.copyfile(libs[0], OUT / 'libkodi.so')
    tool = Path(os.environ['ANDROID_HOME']) / 'ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readelf'
    rows = {}
    for label, path in [('baseline', OUT / 'baseline77-libkodi.so'), ('candidate', OUT / 'libkodi.so')]:
        header = subprocess.check_output([str(tool), '-h', str(path)], text=True)
        assert all(x in header for x in ('ELF64', 'AArch64', 'DYN'))
        symbols = subprocess.check_output([str(tool), '--dyn-syms', '--wide', str(path)], text=True)
        dynamic = subprocess.check_output([str(tool), '-d', str(path)], text=True)
        exports = set()
        for line in symbols.splitlines():
            f = line.split()
            if len(f) >= 8 and f[4] == 'GLOBAL' and f[5] in ('DEFAULT', 'PROTECTED') and f[6] != 'UND':
                exports.add(f[7])
        rows[label] = dict(exports=exports, needed=sorted(re.findall(r'Shared library: \[([^\]]+)\]', dynamic)))
    assert rows['baseline']['exports'] <= rows['candidate']['exports'], 'ORIGINAL_STRONG_ABI_REMOVED'
    added = rows['candidate']['exports'] - rows['baseline']['exports']
    assert all('CDNSNameCache' in n or 'easy_network_family' in n for n in added), added
    assert rows['baseline']['needed'] == rows['candidate']['needed'], 'NATIVE_DEPENDENCIES_CHANGED'
    save('ARM64-LINK-VERIFIED.json', dict(status='PASS_REAL_ARM64_FULL_NATIVE_LINK',
         native_sha256=sha(OUT/'libkodi.so'), source_commit=os.environ['GITHUB_SHA'],
         preserved_strong_exports=len(rows['baseline']['exports']), added_strong_exports=sorted(added),
         unchanged_dynamic_dependencies=rows['candidate']['needed'], generated_native_paths=generated,
         APK=False, signing=False, Android_networking='NOT_RUN', physical_Fold='NOT_RUN'))
    (OUT / 'baseline77-libkodi.so').unlink()
    if (OUT / 'baseline-libkodi.so').exists():
        (OUT / 'baseline-libkodi.so').unlink()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['prepare', 'compile', 'link'])
    {'prepare': prepare, 'compile': compile_objects, 'link': link}[parser.parse_args().operation]()
