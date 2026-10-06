#!/usr/bin/env python3
"""Native shutdown candidate: retain ALL locked 3312 DEX, Cobra and assets."""
import argparse
import copy
import importlib.util
import json
import os
import sys
import zipfile
from pathlib import Path
import native_patch
import android_patch
import shutil
import re
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / 'mobile-regressions-2103304'))
from packaging_checks import DEX, SIGNATURE, dex_contract, require, resource_ids, run, sha, verify_manifest_pair
spec = importlib.util.spec_from_file_location('pack304', HERE.parent / 'mobile-regressions-2103304/package_candidate.py')
factory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(factory)

BASE_SHA = '6d6543dda3d54fd8b4ff12cdf79995c198a399839a29e71e1bf741789332deed'
SOURCE_MAP = '8c4786d60f02d67a860f923729b7556543319fe1e9311aa068571385d2b1ac42'
BASE_NATIVE = 'b4b2630e37abd56a6e522ca633649a65b255b44bd6b39bcb9f8b84866b822aa6'
VERSION = 2103314
RELEASE = '1.0.9-Shutdown-Evidence-RC1'
ENGINE = 'lib/arm64-v8a/libkodi.so'


def source_guard(source, proof):
    parent = json.loads((proof.parent / 'APK-VERIFICATION.json').read_text())
    require(parent['candidate'] == 2103312 and parent['source_commit'] == '1df07a46469040bbeee6bae34b13b4b3f8a7970d', 'Wrong locked Android build')
    require(parent['apk_sha256'] == BASE_SHA and parent['native_sha256'] == BASE_NATIVE, 'Wrong parent APK/native association')
    expected = json.loads(proof.read_text())['after']
    require(len(expected) == 254 and sha(json.dumps(expected, sort_keys=True, separators=(',', ':')).encode()) == SOURCE_MAP,
            'Wrong 3312 Android source map')
    actual = {p.relative_to(source).as_posix(): sha(p.read_bytes()) for p in source.rglob('*') if p.is_file()}
    require(actual == expected, 'Locked Android/Cobra source differs from 3312')


def merge(base, donor, native, output):
    with zipfile.ZipFile(base) as a, zipfile.ZipFile(donor) as b, zipfile.ZipFile(output, 'w') as z:
        require(len(a.namelist()) == len(set(a.namelist())) and len(b.namelist()) == len(set(b.namelist())), 'Duplicate entries')
        require(a.testzip() is None and b.testzip() is None, 'Bad APK CRC')
        require(sha(a.read(ENGINE)) == BASE_NATIVE, 'Wrong parent engine')
        require(dex_contract(a)[0] == dex_contract(b)[0], 'Generated manifest donor changed JNI contract')
        for info in a.infolist():
            if info.filename not in ('AndroidManifest.xml', ENGINE) and not DEX.fullmatch(info.filename) and not SIGNATURE.fullmatch(info.filename):
                z.writestr(copy.copy(info), a.read(info.filename))
        for info in b.infolist():
            if info.filename == 'AndroidManifest.xml' or DEX.fullmatch(info.filename):
                z.writestr(copy.copy(info), b.read(info.filename))
        z.write(native, ENGINE, compress_type=zipfile.ZIP_STORED)


def verify_bytes(base, final, native):
    with zipfile.ZipFile(base) as a, zipfile.ZipFile(final) as b:
        kept = {n for n in a.namelist() if n not in ('AndroidManifest.xml', ENGINE) and not DEX.fullmatch(n) and not SIGNATURE.fullmatch(n)}
        expected = kept | {'AndroidManifest.xml', ENGINE} | {n for n in b.namelist() if DEX.fullmatch(n) or SIGNATURE.fullmatch(n)}
        require(len(b.namelist()) == len(expected) and set(b.namelist()) == expected, 'Unexpected final APK payload')
        for name in kept:
            require(a.read(name) == b.read(name), 'Protected APK entry changed: ' + name)
        require(b.read(ENGINE) == native.read_bytes(), 'Native engine differs from verified build')
        require(dex_contract(a)[0] == dex_contract(b)[0], 'Final JNI declarations changed')
        require(b.testzip() is None, 'Final APK CRC failure')
        return {
            'jni_contract_unchanged': True,
            'other_native_libraries_byte_identical': sum(n.startswith('lib/') and not n.endswith('/') for n in kept),
            'assets_byte_identical': sum(n.startswith('assets/') and not n.endswith('/') for n in kept),
            'android_resources_byte_identical': True, 'protected_entries': len(kept),
        }


def compare_dex(base, final, build, out):
    classpath = (build / 'preservation-classpath.txt').read_text()
    for label, apk in [('base', base), ('final', final)]:
        extracted = out / ('dex-' + label); extracted.mkdir()
        target = out / ('smali-' + label)
        with zipfile.ZipFile(apk) as z:
            for name in z.namelist():
                if DEX.fullmatch(name):
                    dex = extracted / name; dex.write_bytes(z.read(name))
                    subprocess.run(['java', '-cp', classpath, 'org.jf.baksmali.Main', 'disassemble', str(dex), '-o', str(target)], check=True)
    old = {p.relative_to(out / 'smali-base').as_posix(): p.read_text() for p in (out / 'smali-base').rglob('*.smali')}
    new = {p.relative_to(out / 'smali-final').as_posix(): p.read_text() for p in (out / 'smali-final').rglob('*.smali')}
    changed = sorted(n for n in old.keys() | new.keys() if old.get(n) != new.get(n))
    allowed = re.compile(r'com/projectinfinity/kodi/(?:InfinityHealthExport|InfinityExitDiagnostics|Splash|BuildConfig)(?:\$[^/]*)?\.smali$')
    unexpected = [n for n in changed if not allowed.fullmatch(n)]
    require(not unexpected, 'Compiled behavior changed outside diagnostics owners: ' + repr(unexpected))
    report = {'changed_dex_classes': changed, 'all_other_protected_dex_classes_identical': True,
              'cobra_compiled_classes_unchanged': True, 'unchanged_classes': len(old.keys() & new.keys()) - sum(n in old and n in new for n in changed)}
    (out / 'DEX-PRESERVATION.json').write_text(json.dumps(report, indent=2) + '\n')
    for label in ['dex-base', 'dex-final', 'smali-base', 'smali-final']: shutil.rmtree(out / label)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['prepare', 'package'])
    for name in ('source', 'proof', 'base', 'build', 'out', 'engine'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    source_guard(a.source, a.proof)
    require(sha(a.base.read_bytes()) == BASE_SHA, 'Not exact 2103312 APK')
    a.out.mkdir(parents=True, exist_ok=True)
    bt = Path(os.environ['ANDROID_HOME']) / 'build-tools/34.0.0'
    if a.mode == 'prepare':
        factory.BASE_APK_SHA256 = BASE_SHA
        factory.VERSION_CODE = VERSION
        factory.RELEASE = RELEASE
        native, native_report = factory.prepare_native(a.engine.resolve(), a.out.resolve())
        diagnostic_source = a.out / 'diagnostic-source'
        shutil.copytree(a.source, diagnostic_source)
        delta = android_patch.apply(diagnostic_source, sha(native.read_bytes()))
        require(set(delta['changed']) == android_patch.ALLOWED, 'Java diagnostics delta exceeds scope')
        (a.out / 'ANDROID-SOURCE-DELTA.json').write_text(json.dumps(delta, indent=2) + '\n')
        factory.prepare(diagnostic_source.resolve(), a.base.resolve(), a.build.resolve(), a.out.resolve())
        tests = a.build / 'xbmc/src/test/java/com/projectinfinity/kodi'
        tests.mkdir(parents=True, exist_ok=True)
        shutil.copy2(HERE / 'ShutdownEvidence314Test.java', tests)
        with (a.build / 'xbmc/build.gradle').open('a') as gradle:
            gradle.write('''
android { testOptions { unitTests.includeAndroidResources = true; unitTests.all { maxHeapSize = "3g"; testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" } } } }
configurations { preservationTools }
dependencies {
  testImplementation 'junit:junit:4.13.2'
  testImplementation 'org.robolectric:robolectric:4.14.1'
  preservationTools 'org.smali:baksmali:2.5.2'
}
tasks.register('exportPreservationTools') {
  doLast { rootProject.file('preservation-classpath.txt').text = configurations.preservationTools.asPath }
}
''')
        
        return
    proof = json.loads((a.engine / 'ENGINE-PROOF.json').read_text())
    require(proof['candidate'] == VERSION and proof['locked_apk_parent'] == 2103312, 'Wrong native candidate')
    native_source = json.loads((a.engine / 'source-manifest.json').read_text())
    require(set(native_source['changed']) == native_patch.ALLOWED, 'Undeclared native changes')
    require(sha(json.dumps(native_source['before'], sort_keys=True, separators=(',', ':')).encode()) == native_patch.PARENT_MAP,
            'Wrong complete native parent source map')
    changed = {n for n in set(native_source['before']) | set(native_source['after']) if native_source['before'].get(n) != native_source['after'].get(n)}
    require(changed == native_patch.ALLOWED and set(native_source['after']) - set(native_source['before']) == {native_patch.HEADER}, 'Native preservation mismatch')
    for name, expected in json.loads((HERE / 'preimages.json').read_text()).items():
        require(native_source['before'][name] == expected, 'Wrong shutdown preimage')
    native, native_report = factory.prepare_native(a.engine.resolve(), a.out.resolve())
    delta = json.loads((a.out / 'ANDROID-SOURCE-DELTA.json').read_text())
    actual = {p.relative_to(a.out / 'diagnostic-source').as_posix(): sha(p.read_bytes()) for p in (a.out / 'diagnostic-source').rglob('*') if p.is_file()}
    require(actual == delta['after'] and set(delta['changed']) == android_patch.ALLOWED, 'Diagnostic Java source changed after validation')
    require(delta['engine_sha256'] == sha(native.read_bytes()), 'Runtime identity is not packaged engine hash')
    donor = a.build / 'xbmc/build/outputs/apk/release/xbmc-release.apk'
    require(resource_ids(bt / 'aapt2', a.base, a.out / 'base-resources.txt') ==
            resource_ids(bt / 'aapt2', donor, a.out / 'donor-resources.txt'), 'Compiled manifest resource IDs changed')
    unsigned = a.out / 'Infinity-3314-unsigned.apk'
    merge(a.base, donor, native, unsigned)
    verify_manifest_pair(run(bt / 'aapt', 'dump', 'xmltree', a.base, 'AndroidManifest.xml', output=a.out / 'base-manifest.txt'),
                         run(bt / 'aapt', 'dump', 'xmltree', unsigned, 'AndroidManifest.xml', output=a.out / 'manifest.txt'))
    for name in ('INFINITY_KEYSTORE_B64', 'INFINITY_STORE_PASSWORD', 'INFINITY_KEY_PASSWORD', 'INFINITY_KEY_ALIAS'):
        require(bool(os.environ.get(name)), 'Missing permanent signing configuration: ' + name)
    final = a.out / 'Infinity-2103314-Shutdown-Evidence-RC1.apk'
    run('bash', ROOT / 'scripts/sign-infinity71.sh', unsigned, final)
    cert = run(bt / 'apksigner', 'verify', '--verbose', '--print-certs', final, output=a.out / 'signing-verification.txt')
    require(factory.CERT in cert.lower(), 'Permanent signer changed')
    badging = run(bt / 'aapt', 'dump', 'badging', final, output=a.out / 'badging.txt')
    require(f"package: name='com.projectinfinity.kodi' versionCode='{VERSION}' versionName='{RELEASE}'" in badging, 'Wrong identity')
    kept = verify_bytes(a.base, final, native)
    dex_preservation = compare_dex(a.base, final, a.build, a.out)
    report = {'candidate': VERSION, 'apk_parent': 2103312, 'base_sha256': BASE_SHA,
              'apk_sha256': sha(final.read_bytes()), 'source_commit': os.environ['GITHUB_SHA'],
              'skin_parent': '1.0.5.201', 'skin_changed': False, 'cobra_source_changed': False,
              'all_parent_dex_retained': False, 'java_source_changed': True, 'declared_java_changes': sorted(android_patch.ALLOWED), 'native_recompiled': True,
              'physical_device_verified': False, 'shutdown_hang_resolved': False, 'locked': False,
              'repair_scope': 'native shutdown call boundaries, Health Center export, correct runtime engine identity', 'diagnostics_only': True, 'shutdown_behavior_changed': False, 'automatic_process_kill_added': False,
              **kept, **native_report, **dex_preservation}
    (a.out / 'APK-VERIFICATION.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    unsigned.unlink()
    print('PASS: signed diagnostics candidate; Cobra source/assets/resources/other libs protected. No device root-cause claim.')


if __name__ == '__main__':
    main()
