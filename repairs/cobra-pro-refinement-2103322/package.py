#!/usr/bin/env python3
"""Build a Cobra-only candidate over exact user-locked 2103321; never rebuild Kodi."""
import argparse
import difflib
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

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / 'mobile-regressions-2103304'))
from packaging_checks import DEX, require, resource_ids, run, sha, verify_manifest_pair

spec = importlib.util.spec_from_file_location(
    'parent316', HERE.parent / 'close-progress-isolation-2103316/package_candidate.py')
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)
BASE = '9c581733e803b7b41b35373ec67ab5ecae574964b642f34871062a097520422b'
BASE_COMMIT = '50ae3f9ffab6178912d730e24c614d93a676a8f7'
BASE_SOURCE_MAP = '19bcb43e514db0d1e0fd4671eebf77fa1d5a5d1c73951b0ed73c7335104db92d'
BASE_RUN = 37561829546
VERSION = 2103322
RELEASE = '1.0.9-Cobra-Pro-Refinement-RC1'
parent.BASE_SHA = BASE
ALLOWED_SOURCE = sorted('tools/android/packaging/xbmc/src/' + name + '.java.in'
                        for name in ('CobraProUi', 'InfinityLiveActivity'))
ALLOWED_DEX = re.compile(
    r'com/projectinfinity/kodi/(?:InfinityLiveActivity|CobraProUi|BuildConfig)(?:\$[^/]*)?\.smali$')
EXPECTED_SUITES = {
    'Cobra2103199TimeshiftRegressionTest': 7,
    'Cobra2103229MultiViewStabilityFillTest': 10,
    'CobraProHandoffTest': 50,
    'CobraProSeason317Test': 13,
    'ProTeams312Test': 17,
    'WholeUiAmbientTest': 23,
    'CobraProRefinementTest': 12,
    'CobraProControlsRefinementTest': 11,
    'CobraProPausedReturnTest': 8,
}


def snapshot(root):
    return {p.relative_to(root).as_posix(): sha(p.read_bytes())
            for p in root.rglob('*') if p.is_file()}


def prepare(base, build, out):
    require(sha(base.read_bytes()) == BASE, 'Wrong user-locked 2103321 APK')
    proof = ROOT / 'parent3321/evidence3321/SOURCE-PRESERVATION.json'
    require(proof.exists(), 'Missing locked 2103321 source receipt')
    expected = json.loads(proof.read_text())['after']
    require(len(expected) == 254 and sha(json.dumps(expected, sort_keys=True, separators=(',', ':')).encode()) == BASE_SOURCE_MAP,
            'Wrong locked 2103321 source map')
    receipt = json.loads((proof.parent / 'APK-VERIFICATION.json').read_text())
    require(receipt['candidate'] == 2103321 and receipt['apk_sha256'] == BASE
            and receipt['source_commit'] == BASE_COMMIT
            and receipt['signer_certificate_sha256'] == parent.CERT
            and receipt['native_sha256'] == parent.BASE_NATIVE
            and receipt['skin_parent'] == '1.0.5.201' and receipt['skin_changed'] is False,
            'Locked 2103321 source/APK/signer/native/skin association mismatch')
    # The successful run's receipt predates the user's lock decision. Its locked:false
    # means it was a candidate at build time, and does not supersede the user lock.
    dest = out / 'android-source'
    shutil.copytree(proof.parent / 'android-source', dest)
    metadata = json.loads((HERE.parent / 'cobra-pro-season-2103317/parent-metadata.json').read_text())
    for name, content in metadata.items():
        target = dest / name
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
    require(snapshot(dest) == expected, 'Exact locked 2103321 source unavailable')
    subprocess.run([sys.executable, str(HERE / 'apply.py'), str(dest)], check=True)
    actual = snapshot(dest)
    changed = sorted(n for n in expected if expected[n] != actual.get(n))
    require(changed == ALLOWED_SOURCE and actual.keys() == expected.keys(),
            'Source changes outside the two declared Cobra presentation families')
    (out / 'SOURCE-PRESERVATION.json').write_text(json.dumps({
        'before': expected, 'after': actual, 'changed': changed, 'base': 2103321,
        'base_source_commit': BASE_COMMIT, 'base_validation_run': BASE_RUN,
    }, indent=2) + '\n')
    parent.factory.BASE_APK_SHA256 = BASE
    parent.factory.VERSION_CODE = VERSION
    parent.factory.RELEASE = RELEASE
    parent.factory.prepare(dest.resolve(), base.resolve(), build.resolve(), out.resolve())
    tests = build / 'xbmc/src/test/java/com/projectinfinity/kodi'
    tests.mkdir(parents=True)
    test_files = [
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
    ]
    for name in test_files:
        shutil.copy2(ROOT / name, tests / Path(name).name)
    resources = build / 'xbmc/src/test/resources'
    resources.mkdir(parents=True)
    shutil.copy2(HERE.parent / 'cobra-pro-season-2103317/schedule-fixtures.json',
                 resources / 'schedule-fixtures.json')
    # Retain the exact established exclusion from the locked 2103321 recipe.
    previous = tests / 'ProTeams312Test.java'
    previous.write_text(previous.read_text().replace(
        '@Test public void proDrawerSportsOpensSameHubAndSelectionSurvivesRerender()',
        '/* Sports drawer destination intentionally removed in 317; Pro tab is tested instead. */ public void proDrawerSportsOpensSameHubAndSelectionSurvivesRerender()'))
    with (build / 'xbmc/build.gradle').open('a') as f:
        f.write('''
android { testOptions { unitTests.includeAndroidResources = true; unitTests.all { maxHeapSize = "3g"; systemProperty "cobra.evidence", rootProject.file("../evidence3322/screenshots").absolutePath; testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" } } } }
configurations { preservationTools }
dependencies { testImplementation 'junit:junit:4.13.2'; testImplementation 'org.robolectric:robolectric:4.14.1'; preservationTools 'org.smali:baksmali:2.5.2' }
tasks.register('exportPreservationTools') { doLast { rootProject.file('preservation-classpath.txt').text = configurations.preservationTools.asPath } }
''')


def compare_dex(base, final, build, out):
    classpath = (build / 'preservation-classpath.txt').read_text()
    for label, apk in [('base', base), ('final', final)]:
        extracted = out / ('dex-' + label)
        extracted.mkdir()
        target = out / ('smali-' + label)
        with zipfile.ZipFile(apk) as z:
            for name in z.namelist():
                if DEX.fullmatch(name):
                    dex = extracted / name
                    dex.write_bytes(z.read(name))
                    subprocess.run(['java', '-cp', classpath, 'org.jf.baksmali.Main',
                                    'disassemble', str(dex), '-o', str(target)], check=True)
    old = {p.relative_to(out / 'smali-base').as_posix(): p.read_text()
           for p in (out / 'smali-base').rglob('*.smali')}
    new = {p.relative_to(out / 'smali-final').as_posix(): p.read_text()
           for p in (out / 'smali-final').rglob('*.smali')}
    # Same exact-body, protected-call-site bridge guard as the locked 2103321 build.
    from bridge_preservation import verify
    old, new, bridge_report = verify(old, new, out)
    changed = sorted(n for n in old.keys() | new.keys() if old.get(n) != new.get(n))
    unexpected = [n for n in changed if not ALLOWED_DEX.fullmatch(n)]
    diagnostic = out / 'compiler-diffs'
    diagnostic.mkdir(exist_ok=True)
    for name in unexpected:
        (diagnostic / (Path(name).name + '.diff')).write_text(''.join(difflib.unified_diff(
            old.get(name, '').splitlines(True), new.get(name, '').splitlines(True),
            fromfile='base/' + name, tofile='candidate/' + name)))
    require(not unexpected,
            'Compiled behavior changed outside the two declared Cobra/version families: ' + repr(unexpected))
    report = {
        'changed_dex_classes': changed, 'all_other_classes_behavior_identical': True,
        'api_bridge_renumbering_verified': True, 'infinity_kodi_source_and_behavior_preserved': True,
        'unchanged_classes': len(old.keys() & new.keys()) - sum(n in old and n in new for n in changed),
    }
    (out / 'DEX-PRESERVATION.json').write_text(json.dumps(report, indent=2) + '\n')
    for label in ['dex-base', 'dex-final', 'smali-base', 'smali-final']:
        shutil.rmtree(out / label)
    return report


def package(base, build, out):
    require(sha(base.read_bytes()) == BASE, 'Wrong user-locked 2103321 APK at packaging')
    receipt = json.loads((out / 'SOURCE-PRESERVATION.json').read_text())
    require(receipt['base'] == 2103321 and receipt['changed'] == ALLOWED_SOURCE,
            'Unexpected source delta receipt')
    require(snapshot(out / 'android-source') == receipt['after'], 'Source changed after testing')
    bt = Path(os.environ['ANDROID_HOME']) / 'build-tools/34.0.0'
    donor = build / 'xbmc/build/outputs/apk/release/xbmc-release.apk'
    require(resource_ids(bt / 'aapt2', base, out / 'base-resources.txt')
            == resource_ids(bt / 'aapt2', donor, out / 'donor-resources.txt'), 'Resource IDs changed')
    unsigned = out / 'candidate-unsigned.apk'
    parent.merge(base, donor, unsigned)
    verify_manifest_pair(
        run(bt / 'aapt', 'dump', 'xmltree', base, 'AndroidManifest.xml', output=out / 'base-manifest.txt'),
        run(bt / 'aapt', 'dump', 'xmltree', unsigned, 'AndroidManifest.xml', output=out / 'candidate-manifest.txt'))
    final = out / f'Infinity-{VERSION}-Cobra-Pro-Refinement-RC1.apk'
    run('bash', ROOT / 'scripts/sign-infinity71.sh', unsigned, final)
    cert = run(bt / 'apksigner', 'verify', '--verbose', '--print-certs', final,
               output=out / 'signing-verification.txt')
    require(parent.CERT in cert.lower(), 'Permanent signer changed')
    badging = run(bt / 'aapt', 'dump', 'badging', final, output=out / 'badging.txt')
    require(f"package: name='{parent.PACKAGE}' versionCode='{VERSION}' versionName='{RELEASE}'" in badging,
            'Wrong APK identity')
    dex = compare_dex(base, final, build, out)
    suites = []
    for result in sorted((build / 'xbmc/build/test-results/testReleaseUnitTest').glob('TEST-*.xml')):
        suite = ET.parse(result).getroot()
        suites.append({'suite': suite.attrib['name'], **{
            key: int(suite.attrib.get(key, 0)) for key in ['tests', 'failures', 'errors', 'skipped']}})
    expected_names = {'com.projectinfinity.kodi.' + name for name in EXPECTED_SUITES}
    require({suite['suite'] for suite in suites} == expected_names,
            'Focused refinement or one of the six locked regression suites is missing')
    require(all(s['failures'] == s['errors'] == s['skipped'] == 0
                and s['tests'] >= EXPECTED_SUITES[s['suite'].rsplit('.', 1)[-1]] for s in suites),
            'Tests missing, reduced, failed, or skipped')
    report = {
        'candidate': VERSION, 'version_name': RELEASE, 'apk_parent': 2103321,
        'locked_base': 2103321, 'base_apk_sha256': BASE,
        'base_source_commit': BASE_COMMIT, 'base_validation_run': BASE_RUN,
        'apk_sha256': sha(final.read_bytes()), 'native_sha256': parent.BASE_NATIVE,
        'source_commit': os.environ['GITHUB_SHA'],
        'validation_run': os.environ.get('GITHUB_RUN_ID'),
        'signer_certificate_sha256': parent.CERT, 'skin_parent': '1.0.5.201',
        'skin_changed': False, 'native_recompiled': False, 'data_reset': False,
        'physical_device_verified': False, 'real_provider_playback_verified': False,
        'locked': False, 'android_source_delta': receipt['changed'],
        **parent.verify_payload(base, final), **dex,
        'test_suites': suites, 'test_total': sum(s['tests'] for s in suites),
        'runtime_environment': 'GitHub Actions ubuntu-22.04, Java 17, Android API 35 Robolectric controlled fixtures',
    }
    (out / 'APK-VERIFICATION.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    with tarfile.open(out / 'repaired-shell-source.tar.gz', 'w:gz') as tar:
        tar.add(out / 'android-source', arcname='shell-kodi')
    unsigned.unlink()
    print('PASS: signed Cobra 2103322 device-test candidate; locked 2103321 payload preserved. Candidate is not locked.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'package'])
    for name in ('base', 'build', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    (prepare if args.mode == 'prepare' else package)(args.base, args.build, args.out)
