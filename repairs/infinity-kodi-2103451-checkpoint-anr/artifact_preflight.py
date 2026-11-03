"""Read-only recovery of authenticated 451 assets and its exact native source."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
REPO = 'mahfouzhassine8-ops/project-infinity'
BRANCH = 'work/infinity-kodi-2103451-checkpoint-anr-20261103'
LOCK = '0b3450433adc3349056167a6697dae92dad63d86'
NATIVE_PRODUCER = '89300fa6690015f17378657f96230040bb4766ea'
CERTIFICATE = 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
APK_SHA = 'd77c31c458c4571212022bea7cea1e76c1d415cd5792b780b3c655fba97c6399'
NATIVE_SHA = '151128c176b6094f28bb3fc716cc07c3985a9aa38f1fe41e1bb1424f0285a47e'
COMPONENTS = {
    'INFINITY.zip': '7aea7edf649f5718bf858d97c61ec87e976ddd84cee320bed28b78721f449130',
    'COBRA.zip': 'f63d4c1e491dc94591c5623bf02be90d4f9c187b91a0511b36398ee96745f8a8',
    'CHOOSER_SHELL.zip': '70da3f8ff060c4709ef8c0a61821f001a24355d6f3c086ecaf9c6fc707d42360',
    'MINIMAL_ANDROID_CONTRACT.zip': '1c4a2890ef5ca8665b86b148dd293c06a56d76ec846de1e0c9c037a3b0151a25',
}
# IDs, names, run, size and archive digest are pinned before download. Actions'
# official downloader also checks the service's archive digest during transfer.
ASSETS = {
 'signed451': (13200361701, 41568721264, 'Infinity-Combined-Original-Signer-41568721264', 328005311, '7e2eb67204ecc24e1a9d27007e90050b40683f0442bd8c32aec9b3bac32a9c41'),
 'components451': (13200925524, 41568721264, 'Infinity-Combined-Owner-Components-41568721264', 319074381, 'e5f3017e5154625561103580c86020eab0176cc4d1f6ca033f0c1bb8726baedd'),
 'native451': (12636606216, 40287479124, 'Infinity-Final-Native-Modules-40287479124-INTERNAL-NOT-APK', 184980906, '98fd817ea50e3a4246903067d6518b43a53aadf9305330737a5ba194265c9b0f'),
 'foundation': (12558054743, 40089463702, 'Infinity-Saved-Navigation-MultiImage-INTERNAL-QA-NOT-ACCEPTED', 443320169, 'f64393d7c73a28243df8be0b94e1284053ed5f61ec0f08d05693e6addec88b54'),
 'owner': (12583100246, 40149635167, 'Infinity-2103402-MATCHING-NATIVE-OWNER-SIGNED-QA-NOT-FOLD-VERIFIED', 379239569, '47fd2810c08f39e5ee900ba82e6da61c9defda98603768a459ad3e57cc79c27f'),
 'compiled': (12586095094, 40158384817, 'Infinity-2103402-REUSABLE-ARM64-Context-Favourites-Engine', 184390374, '954c9e541d9360e4ba1e395482fe8f51a7574e39d42ed8e4b0f021e59036c4c1'),
 'signed407': (12613590219, 40230842944, 'Infinity-2103407-SEARCH-SINGLE-FLIGHT-ORIGINAL-SIGNER-QA', 379244757, 'bfc2a55e799f767bd01d535a3bdb77b65b91c9336755627f9b2297bfa3766baa'),
 'dependencies': (11698374892, 38132105717, 'Infinity-2103367-Verified-Compiler-Dependencies', 1199235695, 'c26ea3ea6f21fe42e5ff9ff1d3f0adc5bf7adaa775348d812c14a0a377227b69'),
}


def require(ok, detail):
    if not ok:
        raise ValueError(detail)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def validate_metadata(key, metadata):
    identity, run, name, size, digest = ASSETS[key]
    require(metadata.get('id') == identity and metadata.get('name') == name,
            'Artifact identity mismatch: ' + key)
    require(metadata.get('workflow_run', {}).get('id') == run, 'Artifact run mismatch: ' + key)
    require(metadata.get('size_in_bytes') == size and metadata.get('digest') == 'sha256:' + digest,
            'Artifact byte/digest metadata mismatch: ' + key)
    require(metadata.get('expired') is False, 'Artifact expired or unknown expiry: ' + key)
    return {'id': identity, 'run': run, 'name': name, 'bytes': size, 'archive_sha256': digest}


def assert_sha(path, expected):
    actual = sha(path)
    require(actual == expected, 'Unexpected bytes: ' + str(path))
    return actual


def verify_certificate(output):
    values = re.findall(r'Signer #\d+ certificate SHA-256 digest:\s*([a-fA-F0-9]{64})', output)
    require(values == [CERTIFICATE], 'Original signing certificate mismatch/ambiguity')
    return CERTIFICATE


def one(root, filename):
    paths = [p for p in Path(root).rglob(filename) if p.is_file()]
    require(len(paths) == 1, 'Missing/ambiguous verified input ' + filename)
    return paths[0]


def metadata(out):
    require(os.environ.get('GITHUB_REPOSITORY') == REPO, 'Wrong repository authority')
    require(os.environ.get('GITHUB_REF') == 'refs/heads/' + BRANCH, 'Wrong P0 branch')
    request = json.loads((HERE / 'ARTIFACT-PREFLIGHT-REQUEST.json').read_text())
    require(request['operation'] == 'restore-verified-kodi451-inputs' and request['branch'] == BRANCH,
            'Wrong input-recovery request')
    require(all(request[key] is False for key in ('apk_build_allowed', 'signing_allowed',
            'android_execution_allowed', 'application_shutdown_test_allowed')), 'Unselected operation')
    changed = subprocess.check_output(['git', 'diff', '--name-only', LOCK, 'HEAD'], text=True).splitlines()
    workflow = '.github/workflows/infinity-kodi451-p0-input-preflight.yml'
    require(changed and all(p.startswith('repairs/infinity-kodi-2103451-checkpoint-anr/') or p == workflow
                           for p in changed), 'Protected source or workflow changed')
    receipts = {}
    for key, (identity, *_rest) in ASSETS.items():
        run = subprocess.run(['gh', 'api', f'repos/{REPO}/actions/artifacts/{identity}'],
                             capture_output=True, text=True, timeout=30)
        require(run.returncode == 0, 'GitHub artifact metadata access denied: ' + key)
        receipts[key] = validate_metadata(key, json.loads(run.stdout))
    save(out / 'ARTIFACT-METADATA.json', receipts)
    print('Exact repository/branch/source scope and eight immutable artifact identities verified; no key access')


def verify(inputs, sdk, out):
    out.mkdir(parents=True, exist_ok=True)
    apk = one(inputs / 'signed451', 'Infinity-2103451-Combined-Original-Signer.apk')
    assert_sha(apk, APK_SHA)
    require(apk.stat().st_size == 778596097, 'Signed451 APK size mismatch')
    signer = sdk / 'apksigner'
    require(signer.is_file(), 'Existing approved Android build-tools apksigner unavailable')
    result = subprocess.run([str(signer), 'verify', '--verbose', '--print-certs', str(apk)],
                            capture_output=True, text=True, timeout=120)
    require(result.returncode == 0, 'Original APK cryptographic verification failed')
    verify_certificate(result.stdout)
    (out / 'SIGNED451-SIGNATURE.txt').write_text(result.stdout + result.stderr)
    component_receipts = {}
    for name, digest in COMPONENTS.items():
        path = one(inputs / 'components451', name)
        assert_sha(path, digest)
        with ZipFile(path) as z:
            require(len(z.namelist()) == len(set(z.namelist())) and z.testzip() is None,
                    'Component duplicate/CRC failure: ' + name)
        component_receipts[name] = {'sha256': digest, 'bytes': path.stat().st_size}
    with ZipFile(apk) as z:
        require(len(z.namelist()) == len(set(z.namelist())) and z.testzip() is None,
                'Original APK duplicate/CRC failure')
        with z.open('lib/arm64-v8a/libkodi.so') as stream:
            native = hashlib.file_digest(stream, 'sha256').hexdigest()
        require(native == NATIVE_SHA, 'Native451 member does not match retained compiled engine')
        native_members = sum(n.startswith('lib/') and n.endswith('.so') for n in z.namelist())
        require(native_members == 47, 'Unexpected baseline native inventory')
    native_root = inputs / 'native451/final-native'
    assert_sha(native_root / 'libkodi.so', NATIVE_SHA)
    proof = json.loads((native_root / 'ENGINE-PROOF.json').read_text())
    source_map = json.loads((native_root / 'NATIVE-SOURCE-MAP.json').read_text())
    require(proof['source_commit'] == NATIVE_PRODUCER and proof['native_sha256'] == NATIVE_SHA and
            proof['complete_native_engine_compiled'] is True and proof['reviewed_file_count'] == 9411,
            'Native producer/output binding mismatch')
    require(len(source_map) == 9411 and all(isinstance(v, str) and re.fullmatch('[a-f0-9]{64}', v)
                                         for v in source_map.values()), 'Invalid complete native source map')
    report = {'signed451_apk_sha256': APK_SHA, 'certificate_sha256': CERTIFICATE,
              'components': component_receipts, 'native_member_sha256': native,
              'native_member_count': native_members, 'native_source_count': len(source_map),
              'native_producer_commit': NATIVE_PRODUCER, 'retrieval_context': 'authorized repository Actions runner',
              'local_client_forbidden_resolved': False, 'signing_key_accessed': False,
              'apk_created': False, 'android_executed': False, 'historical_watched_route': 'UNKNOWN'}
    save(out / 'SIGNED451-INPUTS-VERIFIED.json', report)
    print('Actual signed451 hash/certificate, exact components and native source/output identity verified')


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def source_restore(inputs, producer, native, out):
    require(subprocess.check_output(['git', '-C', str(producer), 'rev-parse', 'HEAD'], text=True).strip()
            == NATIVE_PRODUCER, 'Not the exact successful native producer commit')
    require((out / 'SIGNED451-INPUTS-VERIFIED.json').is_file(), 'Signed451 verification required first')
    evidence = out / 'reconstruction'
    command = [sys.executable, str(producer / 'repairs/infinity-final-closure-2103407/reconstruct_signed407_native.py'),
               '--foundation', str(inputs / 'foundation'), '--owner', str(inputs / 'owner/native-owner-package'),
               '--compiled', str(inputs / 'compiled/native-owner-build'),
               '--signed407', str(one(inputs / 'signed407', 'Infinity-2103407-Search-Single-Flight-SIGNED-QA.apk')),
               '--target', str(native), '--evidence', str(evidence)]
    subprocess.run(command, check=True)
    module_out = out / 'retained-module-source'
    subprocess.run([sys.executable, str(producer / 'repairs/infinity-final-closure-2103407/stage_native_modules.py'),
                    '--native', str(native), '--map', str(evidence / 'SIGNED407-NATIVE-SOURCE-MAP.json'),
                    '--out', str(module_out)], check=True)
    expected = json.loads((inputs / 'native451/final-native/NATIVE-SOURCE-MAP.json').read_text())
    reconstructed = json.loads((module_out / 'NATIVE-SOURCE-MAP.json').read_text())
    require(reconstructed == expected, 'Reconstructed full source differs from actual signed451 native source map')
    actual = {p.relative_to(native).as_posix(): sha(p) for p in native.rglob('*') if p.is_file()}
    require(actual == expected and len(actual) == 9411, 'Full restored native file inventory mismatch')
    save(out / 'BASELINE-NATIVE-SOURCE-MAP.json', expected)
    lifecycle = load(HERE / 'stage_lifecycle_repair.py', 'verified_p0_lifecycle')
    watched = load(HERE / 'stage_watched_repair.py', 'verified_p0_watched')
    plans = (lifecycle, watched)
    before = {}
    replacements = {}
    for plan in plans:
        for name in plan.PINS:
            raw = (native / name).read_bytes()
            require(expected[name] == plan.PINS[name], 'Staged repair preimage differs from actual451 source: ' + name)
            before[name] = expected[name]
            replacements[name] = plan.transform(name, raw)
    require(len(replacements) == 5, 'Unexpected native repair file scope')
    for name, raw in replacements.items():
        (native / name).write_bytes(raw)
    after = {p.relative_to(native).as_posix(): sha(p) for p in native.rglob('*') if p.is_file()}
    changed = sorted(name for name in expected.keys() | after.keys() if expected.get(name) != after.get(name))
    require(changed == sorted(replacements) and expected.keys() == after.keys(), 'Unowned native source changed')
    host = json.loads((HERE / 'evidence/WATCHED-HOST-VERIFICATION.json').read_text())['source_sha256']
    supporting = {name.removeprefix('retained/'): digest for name, digest in host.items()
                  if name.startswith('retained/') and not name.startswith('retained/threads/')}
    supporting['dbwrappers/InfinityDatabaseBarrier.h'] = host['repairs/android-checkpoint-shutdown/runtime/native/overlay/xbmc/dbwrappers/InfinityDatabaseBarrier.h']
    mismatch = {name: {'host': digest, 'native': expected.get('xbmc/' + name)} for name, digest in supporting.items()
                if expected.get('xbmc/' + name) != digest}
    save(out / 'CANDIDATE-NATIVE-SOURCE-MAP.json', after)
    save(out / 'NATIVE-INTEGRATION.json', {
        'baseline_engine_sha256': NATIVE_SHA, 'baseline_source_count': 9411,
        'baseline_full_source_exact_match': True, 'candidate_source_count': len(after),
        'changed_files': changed, 'before': before, 'after': {name: after[name] for name in changed},
        'supporting_host_source_mismatches': mismatch,
        'native_engine_compiled': False, 'android_verified': False, 'apk_built_or_signed': False,
        'historical_watched_route': 'UNKNOWN', 'unknown_remote_and_recursive_work_remains_blocking': True})
    print('Full signed451 native source recovered and exactly five P0 source edits integrated; no engine/APK compiled')
    print('Supporting host/native source mismatches:', json.dumps(mismatch, sort_keys=True))


def dependencies(inputs, out):
    base = inputs / 'dependencies'
    sums = one(base, 'SHA256SUMS')
    verified = []
    for line in sums.read_text().splitlines():
        if not line.strip():
            continue
        digest, relative = line.split(maxsplit=1)
        relative = relative.lstrip('*')
        path = sums.parent / relative
        require(not Path(relative).is_absolute() and path.resolve().is_relative_to(base.resolve()),
                'Dependency checksum path escapes authorized artifact')
        assert_sha(path, digest)
        verified.append({'file': relative, 'sha256': digest, 'bytes': path.stat().st_size})
    require(verified and any('verified-android-dependencies.tar' in row['file'] for row in verified) and
            any('verified-compiler-cache.tar' in row['file'] for row in verified), 'Incomplete existing dependency transfer')
    save(out / 'DEPENDENCY-TRANSFER-VERIFIED.json', {'files': verified, 'extracted': False,
                                                  'ndk_verified': False, 'engine_compiled': False})
    print('Existing compiler/dependency transfer checksums verified; extraction/toolchain verification not run')


def capabilities(out):
    sdk = Path(os.environ.get('ANDROID_HOME', '/nonexistent'))
    images = sorted(str(p.relative_to(sdk)) for p in (sdk / 'system-images').glob('*/*/*') if p.is_dir())
    save(out / 'RUNNER-CAPABILITIES.json', {
        'host_arch': platform.machine(), 'kvm_exposed': Path('/dev/kvm').exists(),
        'adb_available': shutil.which('adb') is not None or (sdk / 'platform-tools/adb').exists(),
        'emulator_available': (sdk / 'emulator/emulator').exists(), 'installed_system_images': images,
        'emulator_launched': False, 'application_run': False,
        'native_arm_android_target_proven': False, 'physical_fold_acceptance': False})


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['metadata', 'verify', 'source', 'dependencies', 'capabilities'])
    p.add_argument('--inputs', type=Path, default=Path('p0-inputs'))
    p.add_argument('--out', type=Path, default=Path('p0-proof'))
    p.add_argument('--sdk', type=Path)
    p.add_argument('--producer', type=Path)
    p.add_argument('--native', type=Path, default=Path('kodi'))
    a = p.parse_args()
    if a.mode == 'metadata':
        metadata(a.out)
    elif a.mode == 'verify':
        require(a.sdk is not None, 'Approved SDK path required')
        verify(a.inputs, a.sdk, a.out)
    elif a.mode == 'source':
        require(a.producer is not None, 'Exact retained native producer required')
        source_restore(a.inputs.resolve(), a.producer.resolve(), a.native.resolve(), a.out.resolve())
    elif a.mode == 'dependencies':
        dependencies(a.inputs, a.out)
    else:
        capabilities(a.out)
