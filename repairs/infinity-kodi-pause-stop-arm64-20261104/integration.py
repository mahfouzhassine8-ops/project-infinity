"""One-file ARM64 integration; no APK, installation, signing or data operations."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OLD = ROOT / 'repairs/infinity-kodi-2103451-checkpoint-anr'
CANDIDATE = ROOT / 'repairs/infinity-kodi-checkpoint-pause-stop-20261104'
BRANCH = 'work/infinity-kodi-452-pause-stop-arm64-20261104'
START = '7f2c93f94c7372679b756091d5b2666a7d909fd0'
PATH = 'xbmc/messaging/ApplicationMessenger.cpp'
NATIVE452 = 'f89a40b5653c0091a06edd44f6ac5cdf056a649301b6751ee638c8ba88db9674'
sys.path.insert(0, str(OLD))
import artifact_preflight as inputs
import native_build as retained


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def save(path, value):
    inputs.save(path, value)


def metadata(out):
    inputs.require(os.environ.get('GITHUB_REPOSITORY') == inputs.REPO and
                   os.environ.get('GITHUB_REF') == 'refs/heads/' + BRANCH, 'Wrong integration authority')
    request = json.loads((HERE / 'BUILD-REQUEST.json').read_text())
    inputs.require(request['candidate_commit'] == START and request['branch'] == BRANCH and
                   request['native_compilation_allowed'] is True, 'Unselected integration')
    for flag in ('apk_build_allowed', 'signing_allowed', 'installation_allowed', 'automatic_lock_allowed'):
        inputs.require(request[flag] is False, 'Unauthorized operation: ' + flag)
    changed = subprocess.check_output(['git', 'diff', '--name-only', START, 'HEAD'], text=True).splitlines()
    inputs.require(changed and all(p.startswith('repairs/infinity-kodi-pause-stop-arm64-20261104/') or
                   p == '.github/workflows/infinity-kodi452-pause-stop-arm64.yml' for p in changed),
                   'Unexpected source/workflow change')
    for name in retained.PRODUCER_FILES:
        inputs.require((ROOT / name).read_bytes() == subprocess.check_output(['git', 'show', inputs.NATIVE_PRODUCER + ':' + name]),
                       'Native build recipe changed: ' + name)
    for name in ('candidate/' + PATH, 'SOURCE-DELTA.json', 'evidence/after.cpp'):
        relative = str((CANDIDATE / name).relative_to(ROOT))
        inputs.require((CANDIDATE / name).read_bytes() == subprocess.check_output(['git', 'show', START + ':' + relative]),
                       'Approved candidate/test changed: ' + name)
    lock = subprocess.check_output(['git', 'rev-parse', 'refs/remotes/origin/lock/infinity-preview-2103451-user-frozen-20261103'], text=True).strip()
    inputs.require(lock == inputs.LOCK, 'Protected recovery lock changed')
    inputs.ASSETS['verified_source'] = retained.SOURCE_ASSET
    inputs.ASSETS['native452'] = (13276398254, 41729462691,
        'Infinity-Kodi451-P0-ARM64-Native-41729462691-INTERNAL-NOT-APK', 184610295,
        'cac2281741679eaebbdf167969afdbeccdd0a8e1a1f4e2e5fd7eb529807571e0')
    receipts = {}
    for key in ('verified_source', 'dependencies', 'native452'):
        value = subprocess.check_output(['gh', 'api', f'repos/{inputs.REPO}/actions/artifacts/{inputs.ASSETS[key][0]}'], text=True, timeout=30)
        receipts[key] = inputs.validate_metadata(key, json.loads(value))
    save(out / 'AUTHENTICATED-INPUTS.json', receipts)


def restore(proof, native, out):
    before = json.loads((proof / 'CANDIDATE-NATIVE-SOURCE-MAP.json').read_text())
    baseline = json.loads((proof / 'BASELINE-NATIVE-SOURCE-MAP.json').read_text())
    retained.verify_maps(baseline, before, json.loads((proof / 'NATIVE-INTEGRATION.json').read_text()))
    expected = json.loads((CANDIDATE / 'SOURCE-DELTA.json').read_text())
    inputs.require(expected['changed_paths'] == [PATH] and before[PATH] == expected['before'][PATH], 'Wrong native preimage')
    candidate = CANDIDATE / 'candidate' / PATH
    inputs.assert_sha(candidate, expected['after'][PATH])
    archive = proof / 'verified-p0-native-source.tar.gz'
    pin = (proof / (archive.name + '.sha256')).read_text().split()[0]
    inputs.assert_sha(archive, pin)
    inputs.require(not native.exists(), 'Do not overwrite existing native source')
    native.mkdir()
    with tarfile.open(archive, 'r:gz') as stream:
        stream.extractall(native, filter='data')
    actual = {p.relative_to(native).as_posix(): inputs.sha(p) for p in native.rglob('*') if p.is_file()}
    inputs.require(actual == before and len(actual) == 9411, 'Original452 full source mismatch')
    (native / PATH).write_bytes(candidate.read_bytes())
    after = {p.relative_to(native).as_posix(): inputs.sha(p) for p in native.rglob('*') if p.is_file()}
    inputs.require(after == dict(before, **expected['after']), 'Unexpected integration delta')
    save(out / 'NATIVE-SOURCE-MAP.json', after)
    save(out / 'SOURCE-COMPARISON.json', {'parent_native_sha256': NATIVE452, 'candidate_commit': START,
        'source_count': len(after), 'changed': {PATH: {'before': before[PATH], 'after': after[PATH]}},
        'all_other_mapped_sources_identical': True, 'restored_archive_sha256': pin,
        'retirement_changed': False, 'preview_or_cobra_changed': False})
    print('Integrated exact one-file candidate into9411 preserved452 source inputs; no other native source change')


def compile_native(out):
    suite = ROOT / 'repairs/universal-persistence-2103401'
    sys.path.insert(0, str(suite))
    producer = load(suite / 'build.py', 'unchanged_452_native_producer')
    producer.OUT = out
    proof = producer.compile_engine()
    previous = json.loads((OLD / 'evidence/COMPILED-ENGINE-PROOF.json').read_text())
    inputs.require(proof['complete_native_engine_compiled'] and proof['reviewed_file_count'] == 9411 and
                   not proof['changed_or_missing_reviewed'], 'Incomplete native integration')
    inputs.require(proof['compile_recipe_sha256'] == previous['compile_recipe_sha256'], 'Compile recipe drift')
    tools = Path(os.environ['ANDROID_HOME']) / 'ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin'
    readelf = tools / 'aarch64-linux-android-readelf'
    library = out / 'libkodi.so'
    header = subprocess.check_output([str(readelf), '-h', str(library)], text=True)
    inputs.require('AArch64' in header and 'ELF64' in header, 'Wrong architecture')
    dynamic = subprocess.check_output([str(readelf), '--dyn-syms', '--wide', str(library)], text=True)
    protected = [line for line in dynamic.splitlines() if 'InfinityCommandCenterIdentityV1' in line]
    inputs.require(any('GLOBAL' in line and 'DEFAULT' in line for line in protected), 'Native module ABI lost')
    (out / 'ELF-IDENTITY.txt').write_text(header + '\n' + '\n'.join(protected) + '\n')
    objdump = tools / 'llvm-objdump'
    symbols = subprocess.check_output([str(readelf), '--syms', '--wide', str(library)], text=True)
    wanted = ['ProcessCheckpointDisplayMessages', 'IsCheckpointPlaybackControl', 'CApplication8OnAction',
              'CGUIWindowManager20OnApplicationMessage', 'CApplicationMessenger7SendMsg',
              'CApplicationMessenger14ProcessMessage']
    found = []
    for line in symbols.splitlines():
        parts = line.split()
        if len(parts) < 8 or parts[3] != 'FUNC' or parts[6] == 'UND':
            continue
        if any(key in parts[7] for key in wanted):
            name, start, size = parts[7], int(parts[1], 16), int(parts[2])
            if not size:
                continue
            found.append({'name': name, 'address': start, 'size': size})
            output = subprocess.check_output([str(objdump), '-d', '--demangle',
                     '--start-address=' + str(start), '--stop-address=' + str(start + size), str(library)], text=True)
            (out / (name + '.disassembly.txt')).write_text(output)
    inputs.require(any('ProcessCheckpointDisplayMessages' in item['name'] for item in found), 'Compiled selective pump absent')
    save(out / 'SELECTED-NATIVE-SYMBOLS.json', found)
    save(out / 'INTEGRATION-STATUS.json', {'native_compiled': True, 'native_sha256': inputs.sha(library),
         'source_commit': os.environ['GITHUB_SHA'], 'parent_native_sha256': NATIVE452,
         'recipe_unchanged': True, 'source_delta': [PATH], 'android_runtime_verified': False,
         'apk_built': False, 'signed': False, 'installed': False, 'locked': False})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['metadata', 'restore', 'compile'])
    parser.add_argument('--proof', type=Path, default=ROOT / 'verified-inputs')
    parser.add_argument('--native', type=Path, default=ROOT / 'kodi')
    parser.add_argument('--out', type=Path, default=ROOT / 'pause-stop-native')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if args.mode == 'metadata': metadata(args.out)
    elif args.mode == 'restore': restore(args.proof, args.native, args.out)
    else: compile_native(args.out)
