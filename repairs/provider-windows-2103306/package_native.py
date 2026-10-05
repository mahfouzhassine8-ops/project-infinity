#!/usr/bin/env python3
"""Package the validated 3306 engine over exact locked APK 3305.

No Java rebuild, asset replacement, skin installer change or provider rewrite.
The manifest's integer versionCode alone changes; versionName remains inherited.
The permanent signer is mandatory. A produced APK is not device acceptance.
"""
import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile

from native_patch import (FILES, PARENT_SOURCE_MAP_SHA256, digest, transform)
from restore_assets import HERE, locked_map

ROOT = HERE.parents[1]
BASE_SHA = 'e82ce26b666bc5df089f8b4b3d493a44daf0634690854eb4b6fbbc2c007471ab'
BASE_NATIVE_SHA = 'b6724bc5cff3f3e79c5035f82e77be331535a9e3a7bf33e7650b7ab1e95c0626'
CERT = 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
MANIFEST_SHA = '6cff3e95b573bd866510a50237199c913596c0a162f0836a989bb542c45a64fa'
VERSION = 2103306
VERSION_NAME = '1.0.9-Power-Route-RC1'
ENGINE = 'lib/arm64-v8a/libkodi.so'
SIGNATURE = re.compile(r'META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))$', re.I)
APK_NAME = 'Infinity-2103306-Provider-Coordinates-RC1.apk'

spec = importlib.util.spec_from_file_location(
    'retained_manifest_patch', ROOT / 'repairs/fold-unification-2103293/package_apk.py')
manifest_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manifest_module)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def run(*args, output=None):
    result = subprocess.run([str(a) for a in args], check=True,
                            stdout=subprocess.PIPE if output else None, text=True)
    if output:
        Path(output).write_text(result.stdout)
        return result.stdout


def expected_source_changes():
    # Reconstruct the exact three native preimages, independently of the CI
    # receipt being authenticated. This never substitutes a complete engine.
    with tempfile.TemporaryDirectory(prefix='infinity3306-host-preimage-') as temp:
        subprocess.run([sys.executable, str(HERE / 'prepare_host.py'), '--output', temp],
                       check=True, stdout=subprocess.PIPE, text=True)
        root = Path(temp)
        return {n: digest(transform(n, (root / n).read_text()).encode()) for n in FILES}


def check_source_receipt(receipt):
    parent = locked_map(HERE / 'fixtures/locked-3305-source-manifest.json.gz')
    require(receipt['candidate'] == VERSION, 'Wrong native source candidate')
    require(receipt['locked_apk_parent'] == 2103305 and
            receipt['locked_skin_parent'] == '1.0.5.196', 'Wrong native parent pair')
    require(receipt['parent_source_map_sha256'] == PARENT_SOURCE_MAP_SHA256,
            'Wrong pinned source map')
    require(receipt['before'] == parent, 'Complete native preimage differs from locked 3305')
    expected = dict(parent)
    expected.update(expected_source_changes())
    require(receipt['after'] == expected and set(receipt['changed']) == set(FILES),
            'Native source delta differs from exact three-file transform')
    for name in ('provider_python_changed', 'back_dispatch_policy_changed',
                 'back_freeze_resolved', 'shutdown_changed', 'weather_changed',
                 'video_framing_changed', 'physical_device_verified', 'crash_owner_proven'):
        require(receipt.get(name) is False, 'Unapproved or unsupported claim: ' + name)
    require(receipt.get('active_skin_adaptation_preserved') is True,
            'Active-skin adaptation preservation missing')


def manifest_delta(data):
    require(digest(data) == MANIFEST_SHA, 'Wrong locked compiled manifest')
    require(data[:4] == b'\x03\x00\x08\x00' and
            struct.unpack_from('<I', data, 4)[0] == len(data), 'Invalid binary manifest root')
    candidate, previous = manifest_module.version_code(data, VERSION)
    require(previous == 2103305, 'Wrong manifest version preimage')
    require(manifest_module.version_code(candidate)[1] == VERSION,
            'Candidate version code not committed')
    require(manifest_module.version_code(candidate, 2103305)[0] == data,
            'Manifest changed outside integer versionCode')
    require(0 < sum(a != b for a, b in zip(data, candidate)) <= 4,
            'Unexpected manifest byte delta')
    return candidate


def elf_identity(path, output):
    data = path.read_bytes()
    require(data[:6] == b'\x7fELF\x02\x01', 'Expected ELF64 little-endian engine')
    require(struct.unpack_from('<HH', data, 16) == (3, 183), 'Expected ARM64 shared library')
    text = run('readelf', '-h', '-n', '-W', path, output=output)
    ids = re.findall(r'Build ID: ([0-9a-f]+)', text)
    require(len(ids) <= 1, 'Ambiguous native build ID')
    return ids[0] if ids else None


def prepare_native(engine, out, expected_commit):
    proof = json.loads((engine / 'ENGINE-PROOF.json').read_text())
    require(proof['source_commit'] == expected_commit, 'Native build source commit mismatch')
    require(proof['baseline_kodi_commit'] == 'a3a448d26b8d560a65655dab2cd122994dc4e146',
            'Wrong native Kodi lineage')
    require(proof['candidate'] == VERSION and proof['locked_apk_parent'] == 2103305 and
            proof['locked_skin_parent'] == '1.0.5.196' and
            proof['skin_id'] == 'skin.infinity.diggz', 'Wrong compiled candidate identity')
    for key in ('provider_python_changed', 'back_freeze_resolved', 'shutdown_changed',
                'deferred_movie_video_framing_changed', 'physical_device_verified',
                'historical_crash_owner_proven', 'installable_apk'):
        require(proof.get(key) is False, 'Unsupported engine proof claim: ' + key)
    receipt = json.loads((engine / 'source-manifest.json').read_text())
    check_source_receipt(receipt)
    original = engine / 'libkodi.so'
    require(digest(original.read_bytes()) == proof['native_sha256'],
            'Engine bytes differ from full-build proof')
    build_id = elf_identity(original, out / 'unstripped-elf.txt')
    packaged = out / 'staged-libkodi.so'
    shutil.copy2(original, packaged)
    strip = Path(os.environ['ANDROID_HOME']) / 'ndk' / '21.4.7075529' / \
        'toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip'
    run(strip, '--strip-unneeded', packaged)
    require(elf_identity(packaged, out / 'packaged-elf.txt') == build_id,
            'Native build-ID state changed during strip')
    native = packaged.read_bytes()
    for token in (b'Infinity provider window:', b'Infinity provider Back queued:',
                  b'/InfinityAndroidKeyboard', b'_infinityHeartbeat'):
        require(token in native, 'Compiled native diagnostic/JNI contract missing: ' + repr(token))
    require(digest(native) != BASE_NATIVE_SHA, 'Old engine reused instead of candidate')
    shutil.copy2(engine / 'ENGINE-PROOF.json', out / 'ENGINE-PROOF.json')
    shutil.copy2(engine / 'source-manifest.json', out / 'native-source-manifest.json')
    return packaged, proof['native_sha256'], build_id


def payloads(archive):
    names = archive.namelist()
    require(len(names) == len(set(names)), 'Duplicate APK members')
    require(archive.testzip() is None, 'APK CRC failure')
    return {n for n in names if not n.endswith('/') and not SIGNATURE.fullmatch(n)}


def merge(base, native, output):
    require(not output.exists(), 'Refusing to overwrite an APK')
    require(base.resolve() != output.resolve(), 'Input and output must differ')
    with zipfile.ZipFile(base) as old, zipfile.ZipFile(output, 'w') as new:
        payloads(old)
        require(digest(old.read(ENGINE)) == BASE_NATIVE_SHA, 'Wrong locked native engine')
        for info in old.infolist():
            if SIGNATURE.fullmatch(info.filename):
                continue
            data = old.read(info.filename)
            if info.filename == ENGINE:
                data = native.read_bytes()
            elif info.filename == 'AndroidManifest.xml':
                data = manifest_delta(data)
            new.writestr(copy.copy(info), data)


def verify_bytes(base, final, native):
    with zipfile.ZipFile(base) as old, zipfile.ZipFile(final) as new:
        before, after = payloads(old), payloads(new)
        require(before == after, 'APK payload member set drift')
        changed = [n for n in sorted(before) if old.read(n) != new.read(n)]
        require(changed == ['AndroidManifest.xml', ENGINE], 'Unexpected payload delta: ' + repr(changed))
        require(new.read('AndroidManifest.xml') == manifest_delta(old.read('AndroidManifest.xml')),
                'Final manifest version-only check failed')
        require(new.read(ENGINE) == native.read_bytes(), 'Final engine differs from staged candidate')
        return {'changed_payloads': changed, 'unchanged_payload_count': len(before) - 2,
                'dex_resources_assets_native_companions_byte_preserved': True,
                'manifest_change_only_integer_version_code': True}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base-apk', type=Path, required=True)
    p.add_argument('--engine', type=Path, required=True)
    p.add_argument('--native-source-commit', required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    require(digest(args.base_apk.read_bytes()) == BASE_SHA, 'Not exact locked APK 2103305')
    for name in ('INFINITY_KEYSTORE_B64', 'INFINITY_STORE_PASSWORD',
                 'INFINITY_KEY_PASSWORD', 'INFINITY_KEY_ALIAS'):
        require(bool(os.environ.get(name)), 'Missing permanent signing configuration: ' + name)
    args.out.mkdir(parents=True, exist_ok=False)
    native, unstripped_sha, build_id = prepare_native(args.engine, args.out, args.native_source_commit)
    unsigned = args.out / 'unsigned3306.apk'
    final = args.out / APK_NAME
    merge(args.base_apk, native, unsigned)
    bt = Path(os.environ['ANDROID_HOME']) / 'build-tools/34.0.0'
    # Authenticate the input signature too, not just its known full-file hash.
    cert = run(bt / 'apksigner', 'verify', '--verbose', '--print-certs', args.base_apk,
               output=args.out / 'baseline-signing.txt')
    require(CERT in cert.lower(), 'Input permanent signer mismatch')
    run('bash', ROOT / 'scripts/sign-infinity71.sh', unsigned, final)
    cert = run(bt / 'apksigner', 'verify', '--verbose', '--print-certs', final,
               output=args.out / 'signing-verification.txt')
    require(CERT in cert.lower(), 'Candidate permanent signer mismatch')
    badging = run(bt / 'aapt', 'dump', 'badging', final, output=args.out / 'badging.txt')
    require(f"package: name='com.projectinfinity.kodi' versionCode='{VERSION}' versionName='{VERSION_NAME}'"
            in badging, 'Wrong final APK identity')
    require("application-label:'Infinity'" in badging and 'application-debuggable' not in badging,
            'Branding/debuggable contract drift')
    preserved = verify_bytes(args.base_apk, final, native)
    report = {'schema': 1, 'candidate': VERSION, 'apk': final.name,
              'apk_sha256': digest(final.read_bytes()), 'size_bytes': final.stat().st_size,
              'baseline_apk_sha256': BASE_SHA, 'baseline_native_sha256': BASE_NATIVE_SHA,
              'native_source_commit': args.native_source_commit,
              'packaging_source_commit': os.environ.get('GITHUB_SHA'),
              'unstripped_native_sha256': unstripped_sha,
              'packaged_native_sha256': digest(native.read_bytes()), 'native_build_id': build_id,
              'signer_certificate_sha256': CERT, 'skin_id': 'skin.infinity.diggz',
              'compatible_skin': '1.0.5.196; separate 1.0.5.197 browser-focus candidate',
              'version_code': VERSION, 'version_name': VERSION_NAME,
              'version_name_inherited_from_exact_3305': True,
              'native_recompiled': True, 'provider_python_changed': False,
              'weather_changed': False, 'home_player_drawer_changed': False,
              'provider_responsive_layouts_complete': False, 'back_freeze_resolved': False,
              'shutdown_changed': False, 'deferred_movie_video_framing_changed': False,
              'physical_device_verified': False, 'accepted': False, **preserved}
    (args.out / 'APK-AUDIT.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    # These are task-created staging files only; never remove source inputs.
    unsigned.unlink()
    native.unlink()
    print('PASS separately versioned, permanently signed native-coordinate candidate; not device accepted')


if __name__ == '__main__':
    main()
