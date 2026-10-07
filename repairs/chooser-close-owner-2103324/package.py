#!/usr/bin/env python3
"""Build only the shutdown monitor and chooser correction over exact user-locked 2103323."""
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
BASE = '1ab9354722f5f36c0441f0a604ff38ee8ee5beec11eceaeb415aeef247ae8055'
BASE_COMMIT = '5de1ce637d136ab6ae737303e758ad96b092cc57'
BASE_SOURCE_MAP = '1d5e56fd0cb8af866cec522d093c41017161e1557555ee77104b41c733e6906d'
BASE_RUN = 37574574345
VERSION = 2103324
RELEASE = '1.0.9-Chooser-Close-Owner-RC1'
parent.BASE_SHA = BASE
ALLOWED_SOURCE = sorted('tools/android/packaging/xbmc/src/' + name + '.java.in'
                        for name in ('InfinityKodiShutdown', 'Splash'))
ALLOWED_DEX = re.compile(
    r'com/projectinfinity/kodi/(?:InfinityKodiShutdown|Splash|BuildConfig)(?:\$[^/]*)?\.smali$')
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
    'CobraSportsLiveFeedTest': 16,
    'KodiProcessStatusTest': 8,
    'CloseProgress316Test': 10,
    'CobraCloseIsolation316Test': 13,
    'AndroidTaskRemoval315Test': 2,
    'KodiOwnerLeaseTest': 14,
}


def snapshot(root):
    return {p.relative_to(root).as_posix(): sha(p.read_bytes())
            for p in root.rglob('*') if p.is_file()}


def prepare(base, build, out):
    require(sha(base.read_bytes()) == BASE, 'Wrong user-locked 2103323 APK')
    proof = ROOT / 'parent3323/SOURCE-PRESERVATION.json'
    require(proof.exists(), 'Missing locked 2103323 source receipt')
    expected = json.loads(proof.read_text())['after']
    require(len(expected) == 254 and sha(json.dumps(expected, sort_keys=True, separators=(',', ':')).encode()) == BASE_SOURCE_MAP,
            'Wrong locked 2103323 source map')
    receipt = json.loads((proof.parent / 'APK-VERIFICATION.json').read_text())
    require(receipt['candidate'] == 2103323 and receipt['apk_sha256'] == BASE
            and receipt['source_commit'] == BASE_COMMIT
            and receipt['signer_certificate_sha256'] == parent.CERT
            and receipt['native_sha256'] == parent.BASE_NATIVE
            and receipt['skin_parent'] == '1.0.5.201' and receipt['skin_changed'] is False,
            'Locked 2103323 source/APK/signer/native/skin association mismatch')
    # The successful 3323 receipt predates the user lock and is associated with
    # docs/cobra-2103323-LOCK.md in this branch's exact parent commit.
    dest = out / 'android-source'
    with tarfile.open(proof.parent / 'repaired-shell-source.tar.gz') as archive:
        archive.extractall(out / 'parent-extracted', filter='data')
    shutil.copytree(out / 'parent-extracted/shell-kodi', dest)
    metadata = json.loads((HERE.parent / 'cobra-pro-season-2103317/parent-metadata.json').read_text())
    for name, content in metadata.items():
        target = dest / name
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
    require(snapshot(dest) == expected, 'Exact locked 2103323 source unavailable')
    subprocess.run([sys.executable, str(HERE / 'apply.py'), str(dest)], check=True)
    from source_preservation import verify as verify_sports_scope
    rel = 'tools/android/packaging/xbmc/src/Splash.java.in'
    verify_sports_scope((out / 'parent-extracted/shell-kodi' / rel).read_text(),
                        (dest / rel).read_text(), out / 'SHUTDOWN-SOURCE-SCOPE.json')
    actual = snapshot(dest)
    changed = sorted(n for n in expected if expected[n] != actual.get(n))
    require(changed == ALLOWED_SOURCE and actual.keys() == expected.keys(),
            'Source changes outside the declared shutdown monitor/dispatch source')
    (out / 'SOURCE-PRESERVATION.json').write_text(json.dumps({
        'before': expected, 'after': actual, 'changed': changed, 'base': 2103323,
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
        'repairs/cobra-sports-live-2103323/CobraSportsLiveFeedTest.java',
        'repairs/chooser-close-owner-2103324/KodiProcessStatusTest.java',
        'repairs/chooser-close-owner-2103324/CloseProgress316Test.java',
        'repairs/chooser-close-owner-2103324/CobraCloseIsolation316Test.java',
        'repairs/chooser-close-owner-2103324/AndroidTaskRemoval315Test.java',
        'repairs/chooser-close-owner-2103324/KodiOwnerLeaseTest.java',

    ]
    for name in test_files:
        shutil.copy2(ROOT / name, tests / Path(name).name)
    resources = build / 'xbmc/src/test/resources'
    resources.mkdir(parents=True)
    shutil.copy2(HERE.parent / 'cobra-pro-season-2103317/schedule-fixtures.json',
                 resources / 'schedule-fixtures.json')
    # Retain the exact established exclusion from the locked 2103323 recipe.
    previous = tests / 'ProTeams312Test.java'
    previous.write_text(previous.read_text().replace(
        '@Test public void proDrawerSportsOpensSameHubAndSelectionSurvivesRerender()',
        '/* Sports drawer destination intentionally removed in 317; Pro tab is tested instead. */ public void proDrawerSportsOpensSameHubAndSelectionSurvivesRerender()'))
    with (build / 'xbmc/build.gradle').open('a') as f:
        f.write('''
android { testOptions { unitTests.includeAndroidResources = true; unitTests.all { maxHeapSize = "3g"; systemProperty "cobra.evidence", rootProject.file("../evidence3324/screenshots").absolutePath; testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" } } } }
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
    # Same exact-body, protected-call-site bridge guard as the locked 2103323 build.
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
            'Compiled behavior changed outside the declared shutdown monitor/dispatch/version families: ' + repr(unexpected))
    report = {
        'changed_dex_classes': changed, 'all_other_classes_behavior_identical': True,
        'api_bridge_renumbering_verified': True, 'Cobra_source_and_behavior_preserved': True, 'normal_close_and_native_cleanup_behavior_preserved': True,
        'unchanged_classes': len(old.keys() & new.keys()) - sum(n in old and n in new for n in changed),
    }
    (out / 'DEX-PRESERVATION.json').write_text(json.dumps(report, indent=2) + '\n')
    for label in ['dex-base', 'dex-final', 'smali-base', 'smali-final']:
        shutil.rmtree(out / label)
    return report


def package(base, build, out):
    require(sha(base.read_bytes()) == BASE, 'Wrong user-locked 2103323 APK at packaging')
    receipt = json.loads((out / 'SOURCE-PRESERVATION.json').read_text())
    require(receipt['base'] == 2103323 and receipt['changed'] == ALLOWED_SOURCE,
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
    final = out / f'Infinity-{VERSION}-Chooser-Close-Owner-RC1.apk'
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
        'candidate': VERSION, 'version_name': RELEASE, 'apk_parent': 2103323,
        'locked_base': 2103323, 'base_apk_sha256': BASE,
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
        'runtime_environment': 'GitHub Actions ubuntu-22.04, Java 17, Android API 35 Robolectric and actual cross-process OS file locks',
        'locked_base_commit': '65e58a8fc21c3c62c7fc9db2014585e71e0b6a2b',
    }
    (out / 'APK-VERIFICATION.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    with tarfile.open(out / 'repaired-shell-source.tar.gz', 'w:gz') as tar:
        tar.add(out / 'android-source', arcname='shell-kodi')
    unsigned.unlink()
    print('PASS: signed 2103324 shutdown owner candidate over locked 2103323; protected payload preserved. Candidate is not locked.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'package'])
    for name in ('base', 'build', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    (prepare if args.mode == 'prepare' else package)(args.base, args.build, args.out)

