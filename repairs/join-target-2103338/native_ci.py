#!/usr/bin/env python3
"""Build a diagnostic engine over the pinned 2103337 source recipe."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PARENT = ROOT / 'repairs/android-checkpoint-shutdown'
OUT = Path('join-build')
TAG = 'infinity-shutdown-2103338-diagnostic-v1'
TRACE = 'xbmc/platform/android/activity/InfinityShutdownTrace.h'
INPUT_COMMIT = '83bb461c1523f7e648ea4b32148e9e9eb7998598'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')

def verify(source, expected):
    for name, digest in expected.items():
        if Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError('Unsafe source-map entry')
        path = source / name
        if not path.is_file() or sha(path.read_bytes()) != digest:
            raise ValueError('Reviewed source changed: ' + name)

def parent_module():
    sys.path.insert(0, str(PARENT))
    spec = importlib.util.spec_from_file_location('join_diagnostic_parent_native', PARENT / 'native_ci.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def apply_diagnostic(source, before, destination):
    verify(source, before)
    delta = destination / 'diagnostic-delta'
    subprocess.run([sys.executable, str(HERE / 'diagnostic/prepare_delta.py'),
                    '--source', str(source), '--output', str(delta)], check=True)
    receipt = json.loads((delta / 'DELTA-RECEIPT.json').read_text())
    paths = ['xbmc/interfaces/generic/LanguageInvokerThread.cpp',
             'xbmc/interfaces/generic/LanguageInvokerThread.h',
             'xbmc/interfaces/generic/InfinityInvokerTarget.h']
    # Check the trace identity preimage before copying any prepared file.
    old = (source / TRACE).read_text()
    if old.count('infinity-shutdown-2103334-v1') != 1:
        raise ValueError('Unexpected inherited diagnostic identity')
    new_trace = old.replace('infinity-shutdown-2103334-v1', TAG)
    expected = dict(before)
    for name in paths:
        target = source / name
        if name.endswith('InfinityInvokerTarget.h') and target.exists():
            raise ValueError('Diagnostic helper already exists')
        expected[name] = sha((delta / name).read_bytes())
    expected[TRACE] = sha(new_trace.encode())
    changed = sorted(name for name in expected if before.get(name) != expected[name])
    if changed != sorted(paths + [TRACE]):
        raise ValueError('Unexpected diagnostic source scope')
    for name in paths:
        shutil.copyfile(delta / name, source / name)
    (source / TRACE).write_text(new_trace)
    verify(source, expected)
    result = {'schema': 1, 'input_recipe_commit': INPUT_COMMIT,
              'before': before, 'after': expected, 'changed': changed,
              'added': [paths[-1]], 'deleted': [], 'diagnostic_delta': receipt,
              'engine_tag': TAG, 'diagnostic_only': True, 'device_accepted': False,
              'locked': False}
    dump(destination / 'SOURCE-MANIFEST.json', result)
    return result

def prepare():
    parent = parent_module()
    parent.OUT.mkdir(exist_ok=True)
    parent.prepare()
    manifest = json.loads((PARENT / 'runtime/native/manifest.json').read_text())
    apply_diagnostic(Path('kodi'), manifest['after'], OUT)

def compile_engine(use_cache):
    parent = parent_module()
    manifest = json.loads((OUT / 'SOURCE-MANIFEST.json').read_text())
    verify(Path('kodi'), manifest['after'])
    stage = Path('scripts/infinity_live_app_ci_2.sh').read_text()
    inherited = 'python3 scripts/infinity_gui_render_hardening_v3.py apply --source kodi --receipt engine/gui-render-hardening-source.json'
    if stage.count(inherited) != 1:
        raise ValueError('Inherited compiler recipe changed')
    stage = stage.replace(inherited, 'python3 scripts/infinity_gui_render_hardening_v3.py verify --source kodi')
    old = '''rm -f "$TARBALLS/fontconfig-2.14.0.tar.xz" "$TARBALLS/fontconfig-2.14.0.tar.xz.sha512"
make -C target/fontconfig FULL_URL=https://gstreamer.freedesktop.org/data/src/mirror/fontconfig-2.14.0.tar.xz download
make -j"$(nproc)"
make -C target/cmakebuildsys BUILD_DIR="$BUILD_DIR"'''
    if use_cache:
        parent.verify_dependencies()
        if stage.count(old) != 1:
            raise ValueError('Dependency recipe preimage changed')
        stage = stage.replace(old, '''test -x "$DEPENDS/x86_64-linux-gnu-native/bin/cmake"
test -x "$DEPENDS/x86_64-linux-gnu-native/bin/pkg-config"
test -d "$DEPENDS/aarch64-linux-android-21-debug/include"
test -d "$DEPENDS/aarch64-linux-android-21-debug/lib"
make -C target/cmakebuildsys BUILD_DIR="$BUILD_DIR"''')
    else:
        marker = 'make -C target/cmakebuildsys BUILD_DIR="$BUILD_DIR"'
        if stage.count(marker) != 1:
            raise ValueError('Dependency completion marker changed')
        stage = stage.replace(marker, 'python3 "$GITHUB_WORKSPACE/repairs/android-checkpoint-shutdown/native_ci.py" mark-dependencies\n' + marker)
    end = 'make -C "$BUILD_DIR" apk -j"$(nproc)"'
    if stage.count(end) != 1:
        raise ValueError('Inherited native-only recipe boundary changed')
    script = OUT / 'compile-native.sh'
    script.write_text(stage[:stage.index(end)])
    subprocess.run(['bash', str(script)], check=True)
    verify(Path('kodi'), manifest['after'])
    libraries = list(Path(os.environ['BUILD_DIR']).rglob('libkodi.so'))
    if len(libraries) != 1:
        raise ValueError('Native output is ambiguous')
    data = libraries[0].read_bytes()
    for token in (TAG.encode(), b'scripts.target_before_stop', b'scripts.target_before_join',
                  b'os_tid.%u.stage.%s', b'scripts.target_before_nonblocking_stop',
                  b'thread.std_join_fallback', b'infinityRequestPersistenceCheckpoint'):
        if token not in data:
            raise ValueError('Missing native diagnostic or inherited entry: ' + repr(token))
    shutil.copyfile(libraries[0], OUT / 'libkodi.so')
    proof = {'schema': 1, 'candidate': 2103338, 'purpose': 'join-target diagnostic Fold candidate',
             'source_commit': os.environ['GITHUB_SHA'], 'input_recipe_commit': INPUT_COMMIT,
             'parent_apk_candidate': 2103337, 'engine_tag': TAG,
             'native_sha256': sha(data),
             'source_manifest_sha256': sha((PARENT / 'runtime/native/manifest.json').read_bytes()),
             'diagnostic_source_manifest_sha256': sha((OUT / 'SOURCE-MANIFEST.json').read_bytes()),
             'diagnostic_changes': manifest['changed'],
             'protected_parent_inputs_preserved': True,
             'shutdown_behavior_changed': False, 'diagnostic_only': True,
             'legacy_shutdown_implementations_retained': True,
             'device_accepted': False, 'locked': False}
    dump(OUT / 'ENGINE-PROOF.json', proof)
    with (OUT / 'elf-identity.txt').open('w') as output:
        subprocess.run(['readelf', '-h', '-n', '-W', str(OUT / 'libkodi.so')], stdout=output, check=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('prepare', 'compile', 'verify-dependencies'))
    parser.add_argument('--completed-cache', action='store_true')
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)
    if args.mode == 'prepare':
        prepare()
    elif args.mode == 'verify-dependencies':
        parent_module().verify_dependencies()
    else:
        compile_engine(args.completed_cache)

if __name__ == '__main__':
    main()
