#!/usr/bin/env python3
"""Package the 2103327 JobManager repair over exact passed 2103326."""
import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import xml.etree.ElementTree as ET
import zipfile

import android_identity

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = 'bcf04b0146099b05a51d00659c8b95e86809978f4cf34d9fc8db17f1beba74c8'
BASE_NATIVE = 'ca4344d110ab2f6ae12270540d2d2f0c8db73d90243627f3ae926225fc081ae0'
BASE_COMMIT = 'd3f46011ed09e386e546574a89ff2239173656a0'
BASE_RUN = 37675559057
VERSION = 2103327
RELEASE = '1.0.9-JobManager-Close-RC1'
ENGINE = 'lib/arm64-v8a/libkodi.so'

sys.path.insert(0, str(HERE.parent / 'mobile-regressions-2103304'))
sys.path.insert(0, str(HERE.parent / 'chooser-close-owner-2103324'))
from packaging_checks import (DEX, SIGNATURE, dex_contract, require, resource_ids,
                              run, sha, verify_manifest_pair)

spec = importlib.util.spec_from_file_location(
    'locked3324', HERE.parent / 'chooser-close-owner-2103324/package.py')
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)
factory = parent.parent.factory

spec = importlib.util.spec_from_file_location(
    'dex_equivalence326', HERE.parent / 'cooperative-close-2103326/dex_equivalence.py')
dex_equivalence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dex_equivalence)

spec = importlib.util.spec_from_file_location(
    'native_repair327', HERE / 'native_repair.py')
native_repair = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native_repair)

EXPECTED_SUITES = dict(parent.EXPECTED_SUITES,
                       CooperativeClose326Test=16,
                       ShutdownDiagnostics327ExportTest=9)


def bound_native(engine: Path, out: Path):
    proof = json.loads((engine / 'ENGINE-PROOF.json').read_text())
    require(proof['candidate'] == VERSION and proof['apk_parent'] == 2103326 and
            proof['locked_rollback'] == 2103324,
            'Wrong JobManager native candidate parent')
    require(proof['source_commit'] == os.environ['INFINITY_NATIVE_SOURCE_COMMIT'],
            'Wrong immutable 2103327 native source commit')
    require(proof['baseline_kodi_commit'] ==
            'a3a448d26b8d560a65655dab2cd122994dc4e146', 'Wrong Kodi baseline')
    require(proof['diagnostics_only'] is False and
            proof['shutdown_behavior_changed'] is True and
            proof['early_job_cancellation'] is True and
            proof['final_worker_join_preserved'] is True and
            proof['worker_force_stop_added'] is False,
            'Not the reviewed JobManager shutdown repair')

    source = json.loads((engine / 'source-manifest.json').read_text())
    require(sha(json.dumps(source['before'], sort_keys=True,
                           separators=(',', ':')).encode()) == native_repair.PARENT_MAP,
            'Wrong complete 2103326 native source map')
    expected = json.loads((HERE / 'native-delta.json').read_text())
    changed = {name for name in source['before'].keys() | source['after'].keys()
               if source['before'].get(name) != source['after'].get(name)}
    require(changed == set(expected['after']) and set(source['changed']) == changed,
            'Unexpected 2103327 native source delta')
    require({name: source['after'][name] for name in changed} == expected['after'],
            '2103327 native source differs from reviewed output')
    require(source['before'].keys() == source['after'].keys(),
            'Unexpected native source addition/removal')

    original = engine / 'libkodi.so'
    require(sha(original.read_bytes()) == proof['native_sha256'],
            'Raw native build does not match its proof')
    data = original.read_bytes()
    for token in (b'infinity-shutdown-2103327-v1', b'infinity-shutdown-native.jsonl',
                  b'jobs.waiting_active', b'jobs.worker_execute', b'BeginShutdown',
                  b'_infinityHeartbeat', b'/InfinityAndroidKeyboard'):
        require(token in data, 'Required native token missing: ' + repr(token))

    identity = factory.elf_identity(original, out / 'unstripped-elf-identity.txt')
    native = out / 'libkodi.so'
    shutil.copy2(original, native)
    strip = (Path(os.environ['ANDROID_HOME']) / 'ndk' /
             os.environ.get('NDK_VER', '21.4.7075529') /
             'toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip')
    run(strip, '--strip-unneeded', native)
    final_identity = factory.elf_identity(native, out / 'packaged-elf-identity.txt')
    require(final_identity[0] == identity[0], 'ELF identity kind changed')
    if identity[0] == 'build-id':
        require(final_identity == identity, 'ELF build ID changed')
    require(sha(native.read_bytes()) != BASE_NATIVE, '2103327 engine was not replaced')
    shutil.copy2(engine / 'source-manifest.json', out / 'native-source-manifest.json')
    shutil.copy2(engine / 'ENGINE-PROOF.json', out / 'ENGINE-PROOF.json')
    return native, {
        'unstripped_native_sha256': proof['native_sha256'],
        'packaged_native_sha256': sha(native.read_bytes()),
        'native_source_commit': proof['source_commit'],
        'native_build_id': identity[1] if identity[0] == 'build-id' else None,
    }


def prepare(base: Path, build: Path, out: Path, engine: Path) -> None:
    require(sha(base.read_bytes()) == BASE, 'Not exact passed 2103326 APK')
    evidence = ROOT / 'parent3326'
    receipt = json.loads((evidence / 'APK-VERIFICATION.json').read_text())
    require(receipt['candidate'] == 2103326 and receipt['source_commit'] == BASE_COMMIT and
            receipt['validation_run'] == str(BASE_RUN) and receipt['apk_sha256'] == BASE,
            'Wrong 2103326 source/APK/run association')
    require(receipt['native_sha256'] == BASE_NATIVE and
            receipt['skin_parent'] == '1.0.5.201' and
            receipt['signer_certificate_sha256'] == parent.parent.CERT,
            'Wrong 2103326 native, skin or signer parent')

    native, native_report = bound_native(engine, out)
    with tarfile.open(evidence / 'repaired-shell-source.tar.gz') as archive:
        archive.extractall(out / 'parent-extracted', filter='data')
    dest = out / 'android-source'
    shutil.copytree(out / 'parent-extracted/shell-kodi', dest)
    metadata = json.loads((HERE.parent / 'cobra-pro-season-2103317/parent-metadata.json').read_text())
    for name, text in metadata.items():
        target = dest / name
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)

    delta = android_identity.apply(
        dest, evidence / 'SOURCE-PRESERVATION.json',
        out / 'SOURCE-PRESERVATION.json', sha(native.read_bytes()))
    (out / 'NATIVE-ASSOCIATION.json').write_text(
        json.dumps(native_report, indent=2, sort_keys=True) + '\n')

    factory.BASE_APK_SHA256 = BASE
    factory.VERSION_CODE = VERSION
    factory.RELEASE = RELEASE
    factory.prepare(dest.resolve(), base.resolve(), build.resolve(), out.resolve())

    tests = build / 'xbmc/src/test/java/com/projectinfinity/kodi'
    tests.mkdir(parents=True)
    names = [
        'repairs/cobra-navigation-2103157/tests/CobraNavigationUiTest.java',
        'repairs/sports-hub-2103270/SportsHubTest.java',
        'repairs/cobra-pro-preview-2103321/ProTeams312Test.java',
        'repairs/cobra-pro-season-2103317/CobraProSeason317Test.java',
        'repairs/cobra-pro-refinement-2103322/CobraProHandoffTest.java',
        'repairs/cobra-power-audit-2103199/tests/Cobra2103199TimeshiftRegressionTest.java',
        'repairs/whole-ui-ambient-2103276/WholeUiAmbientTest.java',
        'repairs/multiview-stability-fill-2103229/tests/Cobra2103229MultiViewStabilityFillTest.java',
        'repairs/cobra-pro-refinement-2103322/CobraProRefinementTest.java',
        'repairs/cobra-pro-refinement-2103322/CobraProControlsRefinementTest.java',
        'repairs/cobra-pro-refinement-2103322/CobraProPausedReturnTest.java',
        'repairs/cobra-sports-live-2103323/CobraSportsLiveFeedTest.java',
        'repairs/chooser-close-owner-2103324/KodiProcessStatusTest.java',
        'repairs/chooser-close-owner-2103324/CloseProgress316Test.java',
        'repairs/chooser-close-owner-2103324/CobraCloseIsolation316Test.java',
        'repairs/chooser-close-owner-2103324/AndroidTaskRemoval315Test.java',
        'repairs/chooser-close-owner-2103324/KodiOwnerLeaseTest.java',
        'repairs/cooperative-close-2103326/CooperativeClose326Test.java',
        'repairs/jobmanager-close-2103327/ShutdownDiagnostics327ExportTest.java',
    ]
    for name in names:
        shutil.copy2(ROOT / name, tests / Path(name).name)
    resources = build / 'xbmc/src/test/resources'
    resources.mkdir(parents=True)
    shutil.copy2(HERE.parent / 'cobra-pro-season-2103317/schedule-fixtures.json',
                 resources / 'schedule-fixtures.json')
    previous = tests / 'ProTeams312Test.java'
    previous.write_text(previous.read_text().replace(
        '@Test public void proDrawerSportsOpensSameHubAndSelectionSurvivesRerender()',
        '/* Sports drawer destination intentionally removed in 317; Pro tab is tested instead. */ public void proDrawerSportsOpensSameHubAndSelectionSurvivesRerender()'))
    with (build / 'xbmc/build.gradle').open('a') as gradle:
        gradle.write('''
android { testOptions { unitTests.includeAndroidResources = true; unitTests.all { maxHeapSize = "3g"; systemProperty "cobra.evidence", rootProject.file("../evidence3327/screenshots").absolutePath; testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" } } } }
configurations { preservationTools }
dependencies { testImplementation 'junit:junit:4.13.2'; testImplementation 'org.robolectric:robolectric:4.14.1'; preservationTools 'org.smali:baksmali:2.5.2' }
tasks.register('exportPreservationTools') { doLast { rootProject.file('preservation-classpath.txt').text = configurations.preservationTools.asPath } }
''')


def merge(base: Path, donor: Path, native: Path, output: Path) -> None:
    with zipfile.ZipFile(base) as original, zipfile.ZipFile(donor) as compiled, \
            zipfile.ZipFile(output, 'w') as result:
        require(len(original.namelist()) == len(set(original.namelist())) and
                len(compiled.namelist()) == len(set(compiled.namelist())),
                'Duplicate APK entries')
        require(original.testzip() is None and compiled.testzip() is None, 'Bad APK CRC')
        require(sha(original.read(ENGINE)) == BASE_NATIVE, 'Wrong 2103326 native payload')
        require(dex_contract(original)[0] == dex_contract(compiled)[0],
                'JNI declarations changed')
        require(not any(name.startswith(('lib/', 'assets/')) and not name.endswith('/')
                        for name in compiled.namelist()),
                'Unexpected donor assets or native code')
        for info in original.infolist():
            if (info.filename not in ('AndroidManifest.xml', ENGINE) and
                    not DEX.fullmatch(info.filename) and
                    not SIGNATURE.fullmatch(info.filename)):
                result.writestr(copy.copy(info), original.read(info.filename))
        for info in compiled.infolist():
            if info.filename == 'AndroidManifest.xml' or DEX.fullmatch(info.filename):
                result.writestr(copy.copy(info), compiled.read(info.filename))
        result.write(native, ENGINE, compress_type=zipfile.ZIP_STORED)


def verify_payload(base: Path, final: Path, native: Path) -> dict:
    with zipfile.ZipFile(base) as original, zipfile.ZipFile(final) as candidate:
        kept = {name for name in original.namelist()
                if name not in ('AndroidManifest.xml', ENGINE) and
                not DEX.fullmatch(name) and not SIGNATURE.fullmatch(name)}
        expected = (kept | {'AndroidManifest.xml', ENGINE} |
                    {name for name in candidate.namelist()
                     if DEX.fullmatch(name) or SIGNATURE.fullmatch(name)})
        require(set(candidate.namelist()) == expected and
                len(candidate.namelist()) == len(expected), 'Unexpected final APK payload')
        for name in kept:
            require(original.read(name) == candidate.read(name),
                    'Protected entry changed: ' + name)
        require(candidate.read(ENGINE) == native.read_bytes(),
                'Native payload differs from validated engine')
        require(dex_contract(original)[0] == dex_contract(candidate)[0],
                'Final JNI contract changed')
        require(candidate.testzip() is None, 'Bad final APK CRC')
        return {
            'protected_entries': len(kept),
            'skin_and_assets_byte_identical': True,
            'android_resources_byte_identical': True,
            'other_native_libraries_byte_identical': True,
            'jni_contract_unchanged': True,
        }


def package(base: Path, build: Path, out: Path, engine: Path) -> None:
    require(sha(base.read_bytes()) == BASE, 'Wrong 2103326 APK at packaging')
    delta = json.loads((out / 'SOURCE-PRESERVATION.json').read_text())
    android_identity.verify(out / 'android-source', out / 'SOURCE-PRESERVATION.json')
    native, native_report = bound_native(engine, out)
    require(delta['native_sha256'] == sha(native.read_bytes()),
            'Android diagnostics native identity mismatch')

    bt = Path(os.environ['ANDROID_HOME']) / 'build-tools/34.0.0'
    donor = build / 'xbmc/build/outputs/apk/release/xbmc-release.apk'
    require(resource_ids(bt / 'aapt2', base, out / 'base-resources.txt') ==
            resource_ids(bt / 'aapt2', donor, out / 'donor-resources.txt'),
            'Resource IDs changed')
    unsigned = out / 'candidate-unsigned.apk'
    merge(base, donor, native, unsigned)
    verify_manifest_pair(
        run(bt / 'aapt', 'dump', 'xmltree', base, 'AndroidManifest.xml',
            output=out / 'base-manifest.txt'),
        run(bt / 'aapt', 'dump', 'xmltree', unsigned, 'AndroidManifest.xml',
            output=out / 'candidate-manifest.txt'))

    final = out / 'Infinity-2103327-JobManager-Close-RC1.apk'
    run('bash', ROOT / 'scripts/sign-infinity71.sh', unsigned, final)
    cert = run(bt / 'apksigner', 'verify', '--verbose', '--print-certs', final,
               output=out / 'signing-verification.txt')
    require(parent.parent.CERT in cert.lower(), 'Permanent signer changed')
    badging = run(bt / 'aapt', 'dump', 'badging', final, output=out / 'badging.txt')
    require(f"package: name='com.projectinfinity.kodi' versionCode='{VERSION}' versionName='{RELEASE}'" in badging,
            'Wrong APK identity')
    require('application-debuggable' not in badging, 'Release is debuggable')

    recording = dex_equivalence.verify(base, final, build, out, DEX, require)
    allowed_dex = re.compile(
        r'com/projectinfinity/kodi/(?:InfinityHealthExport|InfinityExitDiagnostics|BuildConfig)'
        r'(?:\$[^/]*)?\.smali$|'
        r'com/projectinfinity/kodi/InfinityCobraRecordingService'
        r'(?:\$\$ExternalSyntheticLambda\d+)?\.smali$')
    import bridge_preservation as bridge_guard
    parent.ALLOWED_DEX = allowed_dex
    bridge_guard.ALLOWED = allowed_dex
    dex = parent.compare_dex(base, final, build, out)
    dex['cobra_recording_compiler_equivalence'] = recording
    require(dex['all_other_classes_behavior_identical'] is True and
            dex['api_bridge_renumbering_verified'] is True,
            'DEX preservation did not prove unrelated behavior unchanged')
    (out / 'DEX-PRESERVATION.json').write_text(json.dumps(dex, indent=2) + '\n')

    suites = []
    for result_path in sorted((build / 'xbmc/build/test-results/testReleaseUnitTest').glob('TEST-*.xml')):
        attrs = ET.parse(result_path).getroot().attrib
        suites.append({'suite': attrs['name'], **{
            key: int(attrs.get(key, 0)) for key in ('tests', 'failures', 'errors', 'skipped')}})
    expected_names = {'com.projectinfinity.kodi.' + name for name in EXPECTED_SUITES}
    require({suite['suite'] for suite in suites} == expected_names,
            'An inherited or 2103327 exporter suite is missing')
    require(all(suite['tests'] >= EXPECTED_SUITES[suite['suite'].rsplit('.', 1)[-1]] and
                suite['failures'] == suite['errors'] == suite['skipped'] == 0
                for suite in suites),
            'Tests missing, reduced, failed or skipped')

    report = {
        'candidate': VERSION,
        'version_name': RELEASE,
        'apk_parent': 2103326,
        'locked_rollback': 2103324,
        'base_apk_sha256': BASE,
        'base_source_commit': BASE_COMMIT,
        'base_validation_run': BASE_RUN,
        'apk_sha256': sha(final.read_bytes()),
        'native_sha256': sha(native.read_bytes()),
        'source_commit': os.environ['GITHUB_SHA'],
        'validation_run': os.environ.get('GITHUB_RUN_ID'),
        'signer_certificate_sha256': parent.parent.CERT,
        'skin_parent': '1.0.5.201',
        'skin_changed': False,
        'data_reset': False,
        'native_recompiled': True,
        'diagnostics_only': False,
        'shutdown_hang_resolved': False,
        'early_job_cancellation': True,
        'final_worker_join_preserved': True,
        'worker_force_stop_added': False,
        'physical_device_verified': False,
        'locked': False,
        'android_source_delta': delta['changed'],
        'test_suites': suites,
        'test_total': sum(suite['tests'] for suite in suites),
        **native_report,
        **verify_payload(base, final, native),
        **dex,
    }
    (out / 'APK-VERIFICATION.json').write_text(
        json.dumps(report, indent=2, sort_keys=True) + '\n')
    with tarfile.open(out / 'repaired-shell-source.tar.gz', 'w:gz') as archive:
        archive.add(out / 'android-source', arcname='shell-kodi')
    unsigned.unlink()
    print('PASS: permanently signed 2103327 JobManager close candidate; protected payload verified. Not device accepted or locked.')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'package'])
    for name in ('base', 'build', 'out', 'engine'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    (prepare if args.mode == 'prepare' else package)(
        args.base, args.build, args.out, args.engine)


if __name__ == '__main__':
    main()
