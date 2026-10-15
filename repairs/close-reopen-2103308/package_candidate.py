#!/usr/bin/env python3
"""Native-only candidate: retain ALL 3307 DEX, Cobra, assets and other libraries."""
import argparse
import copy
import importlib.util
import json
import os
import sys
import zipfile
from pathlib import Path
import native_patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / 'mobile-regressions-2103304'))
from packaging_checks import DEX, SIGNATURE, dex_contract, require, resource_ids, run, sha, verify_manifest_pair
spec = importlib.util.spec_from_file_location('pack304', HERE.parent / 'mobile-regressions-2103304/package_candidate.py')
factory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(factory)

BASE_SHA = 'eb0636a35ef2c5b77916e0c686e48ff8f4c4f600bb53fc50110f9844e1dbdfdd'
SOURCE_MAP = '0fc7d638fa95a20dde6f331923cdf694c1774cbb748d186bc04965a4532e69f1'
BASE_NATIVE = '6ef69b123ebfd6c956280ab02463d299959671860803f937af883a7c2f86456a'
VERSION = 2103308
RELEASE = '1.0.9-Close-Reopen-RC1'
ENGINE = 'lib/arm64-v8a/libkodi.so'


def source_guard(source, proof):
    expected = json.loads(proof.read_text())['after']
    require(len(expected) == 250 and sha(json.dumps(expected, sort_keys=True, separators=(',', ':')).encode()) == SOURCE_MAP,
            'Wrong 3307 Android source map')
    actual = {p.relative_to(source).as_posix(): sha(p.read_bytes()) for p in source.rglob('*') if p.is_file()}
    require(actual == expected, 'Android/Cobra source changed; this candidate has no Java delta')


def merge(base, donor, native, output):
    with zipfile.ZipFile(base) as a, zipfile.ZipFile(donor) as b, zipfile.ZipFile(output, 'w') as z:
        require(len(a.namelist()) == len(set(a.namelist())) and len(b.namelist()) == len(set(b.namelist())), 'Duplicate entries')
        require(a.testzip() is None and b.testzip() is None, 'Bad APK CRC')
        require(sha(a.read(ENGINE)) == BASE_NATIVE, 'Wrong parent engine')
        require(dex_contract(a)[0] == dex_contract(b)[0], 'Generated manifest donor changed JNI contract')
        for info in a.infolist():
            if info.filename not in ('AndroidManifest.xml', ENGINE) and not SIGNATURE.fullmatch(info.filename):
                z.writestr(copy.copy(info), a.read(info.filename))
        info = b.getinfo('AndroidManifest.xml')
        z.writestr(copy.copy(info), b.read(info.filename))
        z.write(native, ENGINE, compress_type=zipfile.ZIP_STORED)


def verify_bytes(base, final, native):
    with zipfile.ZipFile(base) as a, zipfile.ZipFile(final) as b:
        kept = {n for n in a.namelist() if n not in ('AndroidManifest.xml', ENGINE) and not SIGNATURE.fullmatch(n)}
        expected = kept | {'AndroidManifest.xml', ENGINE} | {n for n in b.namelist() if SIGNATURE.fullmatch(n)}
        require(len(b.namelist()) == len(expected) and set(b.namelist()) == expected, 'Unexpected final APK payload')
        for name in kept:
            require(a.read(name) == b.read(name), 'Protected APK entry changed: ' + name)
        require(b.read(ENGINE) == native.read_bytes(), 'Native engine differs from verified build')
        require(dex_contract(a)[0] == dex_contract(b)[0], 'Final JNI declarations changed')
        require(b.testzip() is None, 'Final APK CRC failure')
        return {
            'dex_files_byte_identical': sum(bool(DEX.fullmatch(n)) for n in kept),
            'other_native_libraries_byte_identical': sum(n.startswith('lib/') and not n.endswith('/') for n in kept),
            'assets_byte_identical': sum(n.startswith('assets/') and not n.endswith('/') for n in kept),
            'android_resources_byte_identical': True, 'protected_entries': len(kept),
        }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['prepare', 'package'])
    for name in ('source', 'proof', 'base', 'build', 'out', 'engine'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    source_guard(a.source, a.proof)
    require(sha(a.base.read_bytes()) == BASE_SHA, 'Not exact 2103307 APK')
    a.out.mkdir(parents=True, exist_ok=True)
    bt = Path(os.environ['ANDROID_HOME']) / 'build-tools/34.0.0'
    if a.mode == 'prepare':
        factory.BASE_APK_SHA256 = BASE_SHA
        factory.VERSION_CODE = VERSION
        factory.RELEASE = RELEASE
        factory.prepare(a.source.resolve(), a.base.resolve(), a.build.resolve(), a.out.resolve())
        return
    proof = json.loads((a.engine / 'ENGINE-PROOF.json').read_text())
    require(proof['candidate'] == VERSION and proof['locked_apk_parent'] == 2103307, 'Wrong native candidate')
    native_source = json.loads((a.engine / 'source-manifest.json').read_text())
    require(set(native_source['changed']) == native_patch.ALLOWED, 'Undeclared native changes')
    require(sha(json.dumps(native_source['before'], sort_keys=True, separators=(',', ':')).encode()) == native_patch.PARENT_MAP,
            'Wrong complete native parent source map')
    changed = {n for n in native_source['before'] if native_source['before'][n] != native_source['after'].get(n)}
    require(native_source['before'].keys() == native_source['after'].keys() and changed == native_patch.ALLOWED, 'Native preservation mismatch')
    for name, expected in native_patch.PREIMAGES.items():
        require(native_source['before'][name] == expected, 'Wrong shutdown preimage')
    native, native_report = factory.prepare_native(a.engine.resolve(), a.out.resolve())
    donor = a.build / 'xbmc/build/outputs/apk/release/xbmc-release.apk'
    require(resource_ids(bt / 'aapt2', a.base, a.out / 'base-resources.txt') ==
            resource_ids(bt / 'aapt2', donor, a.out / 'donor-resources.txt'), 'Compiled manifest resource IDs changed')
    unsigned = a.out / 'Infinity-3308-unsigned.apk'
    merge(a.base, donor, native, unsigned)
    verify_manifest_pair(run(bt / 'aapt', 'dump', 'xmltree', a.base, 'AndroidManifest.xml', output=a.out / 'base-manifest.txt'),
                         run(bt / 'aapt', 'dump', 'xmltree', unsigned, 'AndroidManifest.xml', output=a.out / 'manifest.txt'))
    for name in ('INFINITY_KEYSTORE_B64', 'INFINITY_STORE_PASSWORD', 'INFINITY_KEY_PASSWORD', 'INFINITY_KEY_ALIAS'):
        require(bool(os.environ.get(name)), 'Missing permanent signing configuration: ' + name)
    final = a.out / 'Infinity-2103308-Close-Reopen-RC1.apk'
    run('bash', ROOT / 'scripts/sign-infinity71.sh', unsigned, final)
    cert = run(bt / 'apksigner', 'verify', '--verbose', '--print-certs', final, output=a.out / 'signing-verification.txt')
    require(factory.CERT in cert.lower(), 'Permanent signer changed')
    badging = run(bt / 'aapt', 'dump', 'badging', final, output=a.out / 'badging.txt')
    require(f"package: name='com.projectinfinity.kodi' versionCode='{VERSION}' versionName='{RELEASE}'" in badging, 'Wrong identity')
    kept = verify_bytes(a.base, final, native)
    report = {'candidate': VERSION, 'apk_parent': 2103307, 'base_sha256': BASE_SHA,
              'apk_sha256': sha(final.read_bytes()), 'source_commit': os.environ['GITHUB_SHA'],
              'skin_parent': '1.0.5.201', 'skin_changed': False, 'cobra_source_changed': False,
              'all_parent_dex_retained': True, 'java_source_changed': False, 'native_recompiled': True,
              'physical_device_verified': False, 'shutdown_hang_resolved': False, 'locked': False,
              **kept, **native_report}
    (a.out / 'APK-VERIFICATION.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    unsigned.unlink()
    print('PASS: permanently signed native candidate; ALL parent DEX/Cobra/assets/resources/other libs retained. NOT device accepted.')


if __name__ == '__main__':
    main()
