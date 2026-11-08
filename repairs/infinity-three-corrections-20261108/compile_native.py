"""Exact464 plus one reviewed native file: real ARM64 object and engine link.

Build tooling only. No APK, keys, installation, release registry or app tests.
"""
import argparse
import builtins
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / 'three-native-evidence'
BASE = '514a82e513ed2ac00ba096d87011b3d3789cfb32'
NAME = 'xbmc/interfaces/legacy/ModuleXbmc.cpp'
BEFORE = '215726b011de58f5cfb7cc1c33c42adfeb29f5f4c85a98864ab36a1819b8d888'
AFTER = 'a2e9b1ef442c46d39275b45454cbf17dad8f7c2e533e3736904462001d82442d'
BASE_ENGINE = '6fc35b8718621ef2e941540b8c858d7d7cd7f408c810ed2fd0d14f7031e8fbb7'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(name, value):
    OUT.mkdir(exist_ok=True)
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def scope():
    assert os.environ.get('GITHUB_REPOSITORY') == 'mahfouzhassine8-ops/project-infinity'
    assert os.environ.get('GITHUB_REF') == 'refs/heads/work/infinity-three-corrections-20261108'
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip() == os.environ['GITHUB_SHA']
    allowed = {'.github/workflows/infinity-combined-release.yml',
               str(HERE.relative_to(ROOT) / 'compile_native.py'),
               str(HERE.relative_to(ROOT) / 'ARM64-REQUEST.json')}
    changed = set(subprocess.check_output(['git', 'diff', '--name-only', BASE, 'HEAD'], text=True).splitlines())
    assert changed == allowed, ('UNREVIEWED_NATIVE_BUILD_SCOPE', sorted(changed ^ allowed))
    old = subprocess.check_output(['git', 'show', BASE + ':.github/workflows/infinity-combined-release.yml'], text=True)
    expected = old.replace('prepare-nine-native462-463, package-umbrella-pov-462]',
                           'prepare-nine-native462-463, package-umbrella-pov-462, verify-three-native]')
    assert (ROOT / '.github/workflows/infinity-combined-release.yml').read_text().startswith(expected.rstrip() + '\n')
    assert sha(HERE / 'native' / NAME) == AFTER
    request = json.loads((HERE / 'ARM64-REQUEST.json').read_text())
    assert request['base'] == BASE and request['operation'] == 'exact464-single-native-source-object-and-link'
    assert request['APK'] is False and request['signing'] is False and request['application_tests'] is False
    producer = '86d5b5e2b65acb878632d407c3a3a07dd1af3b6d'
    for name in ('scripts/infinity_live_app_ci_2.sh', 'repairs/android-checkpoint-shutdown/native_ci.py',
                 'repairs/android-checkpoint-shutdown/install_ndk.sh'):
        assert (ROOT / name).read_bytes() == subprocess.check_output(['git', 'show', producer + ':' + name])


def prepare():
    scope()
    recipe = load(ROOT / 'repairs/infinity-2103460-nine-corrections-20261106/downloads-native/build_native.py', 'retained_exact462_restorer')
    recipe.OUT = OUT
    recipe.restore.OUT = OUT
    recipe.restore_sources()
    map_file = ROOT / 'previous-review/NATIVE-SOURCE-MAP.json'
    assert sha(map_file) == '8a4baedfa0f978a7eedfc332b935deef3572a9deb2d78d8cd488bf02ce7e740a'
    baseline = json.loads(map_file.read_text())
    assert recipe.restore.hashes(ROOT / 'kodi') == baseline and len(baseline) == 9411
    # Restore the four already compiled/signed464 changes, with their preserved pins.
    known = json.loads((ROOT / 'repairs/infinity-final-release-462-20261107/NATIVE-ENGINE-VERIFICATION.json').read_text())
    expected = dict(baseline)
    keyboard = 'xbmc/guilib/GUIKeyboardFactory.cpp'
    assert baseline[keyboard] == known['changed_native_sources'][keyboard]['before']
    shutil.copyfile(ROOT / 'repairs/infinity-native-keyboard-scaling-462-20261107/native' / keyboard, ROOT / 'kodi' / keyboard)
    graphics = ROOT / 'repairs/infinity-native-graphics-462-20261107/GRAPHICS-GESTURE-RENDER.patch'
    subprocess.run(['git', 'apply', '--check', str(graphics)], cwd=ROOT / 'kodi', check=True)
    subprocess.run(['git', 'apply', str(graphics)], cwd=ROOT / 'kodi', check=True)
    for name, value in known['changed_native_sources'].items():
        assert expected[name] == value['before'] and sha(ROOT / 'kodi' / name) == value['after']
        expected[name] = value['after']
    assert recipe.restore.hashes(ROOT / 'kodi') == expected
    save('EXACT464-SOURCE-MAP.json', expected)
    assert expected[NAME] == BEFORE
    shutil.copyfile(HERE / 'native' / NAME, ROOT / 'kodi' / NAME)
    proposed = dict(expected)
    proposed[NAME] = AFTER
    assert recipe.restore.hashes(ROOT / 'kodi') == proposed
    save('NATIVE-SOURCE-MAP.json', proposed)
    # Baseline native bytes are authenticated by the pinned prepared artifact and source proof.
    prepared = ROOT / 'exact464'
    metadata = json.loads((prepared / 'PREPARATION.json').read_text())
    assert metadata['versionCode'] == 2103464 and metadata['CC'] == '0.3.5.62' and metadata['skin'] == '1.0.5.270'
    with ZipFile(prepared / 'components/INFINITY.zip') as z:
        with z.open('payload/lib/arm64-v8a/libkodi.so') as src, (OUT / 'baseline-libkodi.so').open('wb') as dst:
            shutil.copyfileobj(src, dst)
    assert sha(OUT / 'baseline-libkodi.so') == BASE_ENGINE
    save('SOURCE-PRESERVATION.json', dict(status='PASS_EXACT464_PLUS_ONE_SCOPED_NATIVE_SOURCE',
         baseline_engine_sha256=BASE_ENGINE, source_commit=os.environ['GITHUB_SHA'],
         changed={NAME: dict(before=BEFORE, after=AFTER)}, unchanged_native_sources=9410,
         existing_host_evidence_reused=str(HERE.relative_to(ROOT) / 'evidence/HOST-API-BOUNDARY.json'),
         APK=False, signing=False, Android='NOT_RUN', Fold='NOT_RUN'))
    print('PASS exact464 9411-file source map; only ModuleXbmc.cpp differs', flush=True)


def compile_object():
    scope()
    recipe = load(ROOT / 'repairs/infinity-native-touch-2103451-20261105/compile_only.py', 'retained_selected_compiler')
    recipe.OUT = OUT
    original = inspect.getsource(recipe.compile_objects)
    target = "wanted={'xbmc/guilib/GUIBaseContainer.cpp','xbmc/input/InputManager.cpp'}"
    assert original.count(target) == 1 and original.count('len(selected)==2') == 1
    modified = original.replace(target, 'wanted={' + repr(NAME) + '}').replace('len(selected)==2', 'len(selected)==1')
    modified = modified.replace('Two real ARM64 Android translation units compiled', 'One real ARM64 Android translation unit compiled')
    exec(builtins.compile(modified, '<retained-selected-compiler-one-translation-unit>', 'exec'), recipe.__dict__)
    recipe.compile_objects()
    rows = json.loads((OUT / 'SELECTED-COMPILE-COMMANDS.json').read_text())
    assert len(rows) == 1
    args = rows[0].get('arguments') or shlex.split(rows[0]['command'])
    obj = Path(args[args.index('-o') + 1])
    if not obj.is_absolute():
        obj = Path(rows[0]['directory']) / obj
    shutil.copyfile(obj, OUT / 'ModuleXbmc.cpp.o')
    print('PASS selected real Android ARM64 ModuleXbmc object', flush=True)


def link():
    scope()
    sys.path.insert(0, str(ROOT / 'repairs/universal-persistence-2103401'))
    recipe = load(ROOT / 'repairs/universal-persistence-2103401/build.py', 'retained_full_native_link')
    recipe.OUT = OUT
    expected = json.loads((OUT / 'NATIVE-SOURCE-MAP.json').read_text())
    objects = json.loads((OUT / 'COMPILE-RESULT.json').read_text())
    generated = recipe.checked_sources(ROOT / 'kodi', expected, allow_generated=True)
    assert set(generated) == set(objects['generated_native_paths'])
    # The selected compile already configured the original CMake graph. Build
    # its native owning target once; do not reconfigure or invoke APK targets.
    build_dir = Path(os.environ['BUILD_DIR'])
    cache = {}
    for line in (build_dir / 'CMakeCache.txt').read_text().splitlines():
        if '=' in line:
            key, value = line.split('=', 1)
            cache[key] = value
    cmake = cache['CMAKE_COMMAND:INTERNAL']
    subprocess.run([cmake, '--build', str(build_dir), '--target', 'kodi', '--parallel', str(os.cpu_count() or 1)], check=True)
    additions = recipe.checked_sources(ROOT / 'kodi', expected, allow_generated=True)
    libraries = list(build_dir.rglob('libkodi.so'))
    assert len(libraries) == 1 and not list(ROOT.glob('*.apk'))
    shutil.copyfile(libraries[0], OUT / 'libkodi.so')
    binary = (OUT / 'libkodi.so').read_bytes()
    for marker in (b'argument_rejected_before_native_write', b'removed_namespace_inventory_exhausted',
                   b'native_clean_io_inventory_exhausted', b'unverified_dirty_buffer_namespace',
                   b'pending_protected_', b'sqlite_write_transaction', b'SAFE_TO_TERMINATE', b'CHECKPOINT_FAILED'):
        assert marker in binary, marker
    save('ENGINE-PROOF.json', dict(source_commit=os.environ['GITHUB_SHA'], complete_native_engine_compiled=True,
         reviewed_file_count=len(expected), changed_or_missing_reviewed=[], build_generated_additions=additions,
         native_sha256=sha(OUT / 'libkodi.so'), native_CMake_target='kodi', APK=False, signing=False))
    # Retain the final linked generation of the selected object, even if normal
    # CMake header generation legitimately refreshed it after the fail-fast compile.
    row = json.loads((OUT / 'SELECTED-COMPILE-COMMANDS.json').read_text())[0]
    args = row.get('arguments') or shlex.split(row['command'])
    obj = Path(args[args.index('-o') + 1])
    if not obj.is_absolute():
        obj = Path(row['directory']) / obj
    shutil.copyfile(obj, OUT / 'ModuleXbmc.cpp.o')
    tool = Path(os.environ['ANDROID_HOME']) / 'ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readelf'
    rows = {}
    for label, path in [('baseline', OUT / 'baseline-libkodi.so'), ('candidate', OUT / 'libkodi.so')]:
        header = subprocess.check_output([str(tool), '-h', str(path)], text=True)
        assert 'ELF64' in header and 'AArch64' in header and 'DYN' in header
        symbols = subprocess.check_output([str(tool), '--dyn-syms', '--wide', str(path)], text=True)
        dynamic = subprocess.check_output([str(tool), '-d', str(path)], text=True)
        exports = set()
        label_symbol = None
        for line in symbols.splitlines():
            fields = line.split()
            if len(fields) < 8 or fields[4] != 'GLOBAL' or fields[5] not in ('DEFAULT', 'PROTECTED') or fields[6] == 'UND':
                continue
            exports.add((fields[7], fields[3], fields[4], fields[5]))
            if fields[7] == '_ZN9XBMCAddon4xbmc12getInfoLabelEPKc':
                label_symbol = dict(name=fields[7], size=int(fields[2]), address=fields[1])
        assert label_symbol and any(x[0] == 'InfinityCommandCenterIdentityV1' for x in exports)
        rows[label] = dict(exports=sorted(exports), needed=sorted(re.findall(r'Shared library: \[([^\]]+)\]', dynamic)), getInfoLabel=label_symbol)
        (OUT / (label + '-ELF-HEADER.txt')).write_text(header)
    assert rows['baseline']['exports'] == rows['candidate']['exports'], 'ORIGINAL_STRONG_ABI_CHANGED'
    assert rows['baseline']['needed'] == rows['candidate']['needed'], 'NATIVE_DEPENDENCIES_CHANGED'
    assert rows['candidate']['getInfoLabel']['size'] > rows['baseline']['getInfoLabel']['size']
    expected = json.loads((OUT / 'EXACT464-SOURCE-MAP.json').read_text())
    actual = json.loads((OUT / 'NATIVE-SOURCE-MAP.json').read_text())
    assert {n for n in expected if expected[n] != actual[n]} == {NAME}
    save('ARM64-LINK-VERIFIED.json', dict(status='PASS_REAL_ARM64_OBJECT_AND_FULL_NATIVE_LINK',
         source_commit=os.environ['GITHUB_SHA'], source_sha256=AFTER,
         native_sha256=sha(OUT / 'libkodi.so'), native_bytes=(OUT / 'libkodi.so').stat().st_size,
         object_sha256=sha(OUT / 'ModuleXbmc.cpp.o'), preserved_strong_exports=len(rows['candidate']['exports']),
         unchanged_dynamic_dependencies=rows['candidate']['needed'], label_function={k:v['getInfoLabel'] for k,v in rows.items()},
         unchanged_native_source_count=9410, APK=False, signing=False, Android_Search='NOT_RUN',
         deadlock_safety='NOT_PROVEN_BY_COMPILE_OR_LINK', physical_Fold='NOT_RUN', production_repair=False))
    # The retained baseline is only a comparison input; avoid duplicating it in CI output.
    (OUT / 'baseline-libkodi.so').unlink()
    print('PASS real ARM64 object/full link and exact strong native ABI; device stability NOT_RUN', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['prepare', 'compile', 'link'])
    args = parser.parse_args()
    {'prepare': prepare, 'compile': compile_object, 'link': link}[args.operation]()
