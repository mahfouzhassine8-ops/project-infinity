"""Compile the five-file Kodi P0 delta with the unchanged authenticated producer.

No application execution, APK production, signing, key access or lock mutation.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import os
import subprocess
import sys
import tarfile
import artifact_preflight as inputs

ROOT = inputs.ROOT
HERE = Path(__file__).resolve().parent
SOURCE_ASSET = (13274901825, 41726452356,
                'Infinity-Kodi451-P0-Verified-Input-Evidence-41726452356', 51385496,
                '89646188945e35032c8eb5977882923b3293de4111421fbb32adfb0b77595bfc')
WORKFLOWS = {'.github/workflows/infinity-kodi451-p0-input-preflight.yml',
             '.github/workflows/infinity-kodi451-p0-native-build.yml'}
PRODUCER_FILES = ('repairs/universal-persistence-2103401/build.py',
                  'repairs/universal-persistence-2103401/patch.py',
                  'repairs/android-checkpoint-shutdown/native_ci.py',
                  'repairs/android-checkpoint-shutdown/install_ndk.sh',
                  'scripts/infinity_live_app_ci_2.sh')


def verify_maps(before, after, integration):
    inputs.require(len(before) == len(after) == 9411 and set(before) == set(after),
                   'Full native inventory changed')
    changed = {p for p in before if before[p] != after[p]}
    reviewed = json.loads((HERE / 'evidence/NATIVE-INTEGRATION-RESTORED.json').read_text())
    inputs.require(changed == set(reviewed['before']) == set(reviewed['after']),
                   'Native delta is not exactly the five reviewed files')
    inputs.require(all(before[p] == reviewed['before'][p] and after[p] == reviewed['after'][p]
                       for p in changed), 'Repair source bytes changed')
    inputs.require(integration['baseline_full_source_exact_match'] is True and
                   integration['baseline_engine_sha256'] == inputs.NATIVE_SHA,
                   'Baseline native binding lost')
    return sorted(changed)


def metadata(out):
    inputs.require(os.environ.get('GITHUB_REPOSITORY') == inputs.REPO and
                   os.environ.get('GITHUB_REF') == 'refs/heads/' + inputs.BRANCH, 'Wrong build authority')
    request = json.loads((HERE / 'NATIVE-BUILD-REQUEST.json').read_text())
    inputs.require(request['operation'] == 'compile-five-file-kodi451-p0-native' and
                   request['native_compilation_allowed'] is True and
                   request['protected_lock_commit'] == inputs.LOCK,
                   'Unselected native build')
    inputs.require(all(request[k] is False for k in ('apk_build_allowed', 'signing_allowed',
                   'android_execution_allowed', 'application_shutdown_test_allowed')), 'Unselected operation')
    changed = subprocess.check_output(['git', 'diff', '--name-only', inputs.LOCK, 'HEAD'], text=True).splitlines()
    inputs.require(changed and all(p.startswith('repairs/infinity-kodi-2103451-checkpoint-anr/') or
                   p in WORKFLOWS for p in changed), 'Protected repository source changed')
    retained = subprocess.check_output(['git', 'rev-parse',
        'refs/remotes/origin/lock/infinity-preview-2103451-user-frozen-20261103'], text=True).strip()
    inputs.require(retained == inputs.LOCK, 'Recovery lock changed')
    for name in PRODUCER_FILES:
        original = subprocess.check_output(['git', 'show', inputs.NATIVE_PRODUCER + ':' + name])
        inputs.require((ROOT / name).read_bytes() == original, 'Original native producer changed: ' + name)
    inputs.ASSETS['verified_source'] = SOURCE_ASSET
    report = {}
    for key in ('verified_source', 'dependencies'):
        result = subprocess.run(['gh', 'api', f'repos/{inputs.REPO}/actions/artifacts/{inputs.ASSETS[key][0]}'],
                                text=True, capture_output=True, check=True, timeout=30)
        report[key] = inputs.validate_metadata(key, json.loads(result.stdout))
    inputs.save(out / 'AUTHENTICATED-INPUTS.json', report)
    print('Exact source/dependency artifact identities, unchanged producer and frozen451 lock verified')


def restore(proof, out):
    before = json.loads((proof / 'BASELINE-NATIVE-SOURCE-MAP.json').read_text())
    after = json.loads((proof / 'CANDIDATE-NATIVE-SOURCE-MAP.json').read_text())
    integration = json.loads((proof / 'NATIVE-INTEGRATION.json').read_text())
    changed = verify_maps(before, after, integration)
    signed = json.loads((proof / 'SIGNED451-INPUTS-VERIFIED.json').read_text())
    inputs.require(signed['signed451_apk_sha256'] == inputs.APK_SHA and
                   signed['certificate_sha256'] == inputs.CERTIFICATE and
                   signed['native_member_sha256'] == inputs.NATIVE_SHA, 'Signed451 receipt mismatch')
    archive = proof / 'verified-p0-native-source.tar.gz'
    pin = (proof / (archive.name + '.sha256')).read_text().split()[0]
    inputs.assert_sha(archive, pin)
    native = ROOT / 'kodi'
    inputs.require(not native.exists(), 'Native output already exists')
    native.mkdir()
    with tarfile.open(archive, 'r:gz') as stream:
        stream.extractall(native, filter='data')
    actual = {p.relative_to(native).as_posix(): inputs.sha(p) for p in native.rglob('*') if p.is_file()}
    inputs.require(actual == after, 'Restored source bytes differ from complete reviewed9411 map')
    inputs.save(out / 'NATIVE-SOURCE-MAP.json', actual)
    inputs.save(out / 'SOURCE-BINDING.json', {
        'source_artifact_id': SOURCE_ASSET[0], 'source_run': SOURCE_ASSET[1],
        'source_tar_sha256': pin, 'reviewed_count': len(actual), 'changed_files': changed,
        'signed451_apk_sha256': inputs.APK_SHA, 'native451_sha256': inputs.NATIVE_SHA,
        'historical_watched_route': 'UNKNOWN', 'android_verified': False})
    print('Restored all9411 source hashes; exact five-file delta and signed451 binding verified')


def compile_native(out):
    suite = ROOT / 'repairs/universal-persistence-2103401'
    sys.path.insert(0, str(suite))
    spec = importlib.util.spec_from_file_location('unchanged_retained_native_producer', suite / 'build.py')
    producer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(producer)
    producer.OUT = out
    proof = producer.compile_engine()
    inputs.require(proof['complete_native_engine_compiled'] is True and
                   proof['reviewed_file_count'] == 9411, 'Incomplete native compilation')
    readelf = Path(os.environ['ANDROID_HOME']) / ('ndk/21.4.7075529/toolchains/llvm/prebuilt/'
                                                'linux-x86_64/bin/aarch64-linux-android-readelf')
    library = out / 'libkodi.so'
    dynamic = subprocess.check_output([str(readelf), '--dyn-syms', '--wide', str(library)], text=True)
    symbols = [s for s in dynamic.splitlines() if 'InfinityCommandCenterIdentityV1' in s]
    inputs.require(any('GLOBAL' in s and 'DEFAULT' in s for s in symbols), 'Protected native-module ABI lost')
    header = subprocess.check_output([str(readelf), '-h', str(library)], text=True)
    inputs.require('AArch64' in header and 'ELF64' in header, 'Wrong native target')
    (out / 'NATIVE-MODULE-ABI.txt').write_text('\n'.join(symbols) + '\n' + header)
    inputs.save(out / 'P0-BUILD-STATUS.json', {
        'complete_native_engine_compiled': True, 'native_sha256': inputs.sha(library),
        'source_commit': os.environ['GITHUB_SHA'], 'apk_built_or_signed': False,
        'android_executed': False, 'physical_fold_acceptance': False,
        'historical_watched_route': 'UNKNOWN', 'recovery_lock_modified': False})
    print('Complete ARM64 native build and retained ABI verified; Android/P0 acceptance NOT RUN')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['metadata', 'restore', 'compile'])
    p.add_argument('--proof', type=Path, default=ROOT / 'verified-inputs')
    p.add_argument('--out', type=Path, default=ROOT / 'p0-native-build')
    args = p.parse_args()
    args.out.mkdir(exist_ok=True)
    if args.mode == 'metadata': metadata(args.out)
    elif args.mode == 'restore': restore(args.proof, args.out)
    else: compile_native(args.out)
