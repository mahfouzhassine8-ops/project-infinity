#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Compile-only selective upstream port on the exact approved 2103327 source.
No new close coordinator, saving mechanism, cancellation policy, or shortened join.
"""
from pathlib import Path
import argparse, difflib, hashlib, json, os, subprocess, tarfile

VERSION = 2103339
BASE_COMMIT = '2bb8f12f700ee69fe5d86629e6639bc0b1a0b79e'
BASE_NATIVE_COMMIT = '541fdbb25dae16d6e38d7814948a5a8ae54ad13e'
PARENT_MAP = 'cb7a8610093b5e2d3eef627e789f2ced674a77ab4e5031ca6a70adc7719a6a13'
APP = 'xbmc/application/Application.cpp'
TRACE = 'xbmc/platform/android/activity/InfinityShutdownTrace.h'
APP_HASH = 'e20467d13ceabdbf9634c9341e31e7ba96aa42172dc8941baed83111dcc080d6'
UPSTREAM = '843ed46fc638b0623fd0d25e865e16f676f61273'
OLD_TAG = 'infinity-shutdown-2103327-v1'
NEW_TAG = 'infinity-shutdown-2103339-v1'
OUT = Path('engine3339')
SOURCE = Path('kodi')

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def file_digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()

def map_digest(values):
    return digest(json.dumps(values, sort_keys=True, separators=(',', ':')).encode())

def snapshot(root):
    return {p.relative_to(root).as_posix(): file_digest(p)
            for p in root.rglob('*') if p.is_file() and '.git' not in p.relative_to(root).parts}

def save(name, value):
    OUT.mkdir(exist_ok=True)
    (OUT / name).write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')

def function(text, signature):
    start = text.index(signature)
    pos = text.index('{', start)
    level, end = 1, pos + 1
    while level:
        require(end < len(text), 'Unterminated method')
        level += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]

def transform(text):
    require(digest(text.encode()) == APP_HASH, 'Unexpected complete Application.cpp preimage')
    old = function(text, 'void CApplication::StopPlaying()')
    window = '    int iWin = gui->GetWindowManager().GetActiveWindow();\n'
    close = '      appPlayer->ClosePlayer();'
    require(old.count(window) == old.count(close) == 1, 'StopPlaying preimage mismatch')
    require('exitFrameMove' not in old and 'exitGfx' not in old, 'Port already exists')
    replacement = '''      {
        // let script threads into the GUI while we close, or they can deadlock us
        CSingleExit exitGfx(CServiceBroker::GetWinSystem()->GetGfxContext());
        CSingleExit exitFrameMove(m_frameMoveGuard);
        appPlayer->ClosePlayer();
      }

      const int iWin = gui->GetWindowManager().GetActiveWindow();'''
    new = old.replace(window, '', 1).replace(close, replacement, 1)
    require(text.count(old) == 1, 'Non-unique target')
    return text.replace(old, new, 1), old, new

def reconstruct():
    import yaml
    require(not SOURCE.exists(), 'Use a new workspace: source already exists')
    recipe = yaml.safe_load(subprocess.check_output([
        'git', 'show', BASE_NATIVE_COMMIT + ':.github/workflows/infinity-2103327-native-jobmanager.yml'], text=True))
    names = ('Reconstruct exact passed 2103326 native source',
             'Apply exact JobManager repair and exercise production methods')
    steps = recipe['jobs']['native-engine']['steps']
    OUT.mkdir(exist_ok=True)
    for i, name in enumerate(names):
        found = [s['run'] for s in steps if s.get('name') == name]
        require(len(found) == 1, 'Pinned reconstruction step missing: ' + name)
        script = OUT / ('reconstruct-' + str(i) + '.sh')
        script.write_text(found[0])
        subprocess.run(['bash', str(script)], check=True)
    expected = json.loads(Path('engine3327/source-manifest.json').read_text())['after']
    require(map_digest(expected) == PARENT_MAP, 'Wrong approved native map')
    require(snapshot(SOURCE) == expected, 'Reconstruction differs from approved native source')
    originals = {n: (SOURCE/n).read_text() for n in (APP, TRACE)}
    patched, old, new = transform(originals[APP])
    require(originals[TRACE].count(OLD_TAG) == 1, 'Unexpected diagnostic tag')
    (SOURCE/APP).write_text(patched)
    (SOURCE/TRACE).write_text(originals[TRACE].replace(OLD_TAG, NEW_TAG, 1))
    after = snapshot(SOURCE)
    changed = {n for n in expected.keys() | after.keys() if expected.get(n) != after.get(n)}
    require(changed == {APP, TRACE} and expected.keys() == after.keys(), 'Unexpected native delta')
    save('source-manifest.json', dict(candidate=VERSION, parent=2103327, before=expected,
        after=after, changed=sorted(changed), upstream_commit=UPSTREAM,
        only_behavior_delta='StopPlaying graphics/frame guard release and window read order',
        final_joins_preserved=True, python_unchanged=True, scanner_order_unchanged=True,
        no_new_persistence=True, physical_device_verified=False, locked=False))
    (OUT/'StopPlaying-parent.cpp').write_text(old + '\n')
    (OUT/'StopPlaying-patched.cpp').write_text(new + '\n')
    patch = ''.join(''.join(difflib.unified_diff(originals[n].splitlines(True),
        (SOURCE/n).read_text().splitlines(True), fromfile='a/'+n, tofile='b/'+n)) for n in sorted(changed))
    (OUT/'native-reviewed.patch').write_text(patch)
    # Source retained before compilation so a compiler failure does not erase it.
    with tarfile.open(OUT/'reviewed-native-source.tar.gz', 'w:gz') as archive:
        for name in sorted(after):
            archive.add(SOURCE/name, arcname='kodi/'+name, recursive=False)
    print('PASS: all 9373 native source inputs matched approved 3327; only player method and trace identity changed')

def verify():
    receipt = json.loads((OUT/'source-manifest.json').read_text())
    require(map_digest(receipt['before']) == PARENT_MAP, 'Wrong native parent manifest')
    require(set(receipt['changed']) == {APP, TRACE}, 'Unexpected native allowlist')
    for name, value in receipt['after'].items():
        require((SOURCE/name).is_file() and file_digest(SOURCE/name) == value,
                'Protected source mutated: ' + name)
    return receipt

def compile_engine():
    verify()
    build = Path(os.environ['BUILD_DIR'])
    require(not build.exists(), 'Native build directory must be fresh')
    stage = Path('scripts/infinity_live_app_ci_2.sh').read_text()
    old = 'python3 scripts/infinity_gui_render_hardening_v3.py apply --source kodi --receipt engine/gui-render-hardening-source.json'
    require(stage.count(old) == 1, 'Changed build recipe')
    stage = stage.replace(old, 'python3 scripts/infinity_gui_render_hardening_v3.py verify --source kodi', 1)
    marker = 'make -C "$BUILD_DIR" apk -j"$(nproc)"'
    require(stage.count(marker) == 1, 'Native build boundary missing')
    (OUT/'compile.sh').write_text(stage[:stage.index(marker)])
    subprocess.run(['bash', str(OUT/'compile.sh')], check=True)
    verify()
    libraries = list(build.rglob('libkodi.so'))
    require(len(libraries) == 1, 'Expected exactly one new engine')
    library = libraries[0]
    import shutil
    shutil.copy2(library, OUT/'libkodi.so')
    with (OUT/'elf-identity.txt').open('w') as stream:
        subprocess.run(['readelf', '-h', '-n', '-W', str(library)], check=True, stdout=stream)
    strings = subprocess.check_output(['strings', str(library)])
    for token in (NEW_TAG.encode(), b'jobs.waiting_active', b'_infinityHeartbeat'):
        require(token in strings, 'Required native identity/feature missing: ' + repr(token))
    proof = dict(candidate=VERSION, apk_parent=2103327, native_parent=2103327,
        locked_rollback=2103327, source_commit=os.environ['GITHUB_SHA'],
        build_run=os.environ['GITHUB_RUN_ID'], native_sha256=file_digest(library),
        baseline_kodi_commit='a3a448d26b8d560a65655dab2cd122994dc4e146',
        upstream_commit=UPSTREAM, player_guard_forwardport=True,
        parent_packaged_native_sha256='a3f95a64b4433a999df37c18ecc48a3a43876c0cc49ae6c5433e82c98835764c',
        trace_engine=NEW_TAG, final_joins_preserved=True, python_unchanged=True,
        scanner_order_unchanged=True, no_new_persistence=True,
        native_recompiled=True, physical_device_verified=False, locked=False)
    save('ENGINE-PROOF.json', proof)
    print('PASS: new ARM64 engine compiled and all protected source hashes retained')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('reconstruct', 'verify', 'compile'))
    mode = parser.parse_args().mode
    {'reconstruct': reconstruct, 'verify': verify, 'compile': compile_engine}[mode]()
