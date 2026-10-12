#!/usr/bin/env python3
"""Gated Android-only Cobra corrective candidate over preserved 2103369 transport."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONFIG = json.loads((HERE / 'candidate.json').read_text())
BASELINE = json.loads((HERE / 'BASELINE-GATE-A.json').read_text())
sys.path.insert(0, str(HERE.parent / 'mobile-regressions-2103304'))
from packaging_checks import require, resource_ids, run, sha, verify_manifest_pair

spec = importlib.util.spec_from_file_location('approved_android_packaging', HERE.parent / 'close-progress-isolation-2103316/package_candidate.py')
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)
parent.BASE_SHA = CONFIG['transport_apk_sha256']
parent.BASE_NATIVE = CONFIG['native_sha256']
ALLOWED = sorted('tools/android/packaging/xbmc/src/' + name + '.java.in' for name in ('InfinityLiveActivity', 'CobraProUi'))
INHERITED = {
    'Cobra2103199TimeshiftRegressionTest': ('cobra-power-audit-2103199/tests', 7),
    'Cobra2103229MultiViewStabilityFillTest': ('multiview-stability-fill-2103229/tests', 10),
    'CobraProHandoffTest': ('cobra-pro-refinement-2103322', 50),
    'CobraProSeason317Test': ('cobra-pro-season-2103317', 13),
    'ProTeams312Test': ('cobra-pro-preview-2103321', 17),
    'WholeUiAmbientTest': ('whole-ui-ambient-2103276', 23),
    'CobraProRefinementTest': ('cobra-pro-refinement-2103322', 12),
    'CobraProControlsRefinementTest': ('cobra-pro-refinement-2103322', 11),
    'CobraProPausedReturnTest': ('cobra-pro-refinement-2103322', 8),
    'CobraSportsLiveFeedTest': ('cobra-sports-live-2103323', 16),
}


def snapshot(root):
    return {p.relative_to(root).as_posix(): sha(p.read_bytes()) for p in root.rglob('*') if p.is_file()}


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def test_spec():
    extra = json.loads((HERE / 'test-spec.json').read_text())
    require(extra and all(v >= 1 for v in extra.values()), 'Corrective runtime test plan missing')
    require(not (extra.keys() & INHERITED.keys()), 'Corrective tests must not replace inherited suites')
    return {**{k: v[1] for k, v in INHERITED.items()}, **extra}


def verify_source(out):
    proof = json.loads((out / 'SOURCE-PRESERVATION.json').read_text())
    require(proof['before'] == BASELINE['transport_runtime_hashes'], 'Wrong source baseline')
    require(proof['changed'] == ALLOWED, 'Unauthorized changed source files')
    require(snapshot(out / 'android-source') == proof['after'], 'Source changed after preparation')
    return proof


def prepare(args):
    require(CONFIG.get('implementation_state') == 'READY_FOR_PRE_DEVICE_GATES', 'Stopped at preservation review; implementation has not been cleared to build')
    require(sha(args.base.read_bytes()) == CONFIG['transport_apk_sha256'], 'Wrong retained signed APK')
    require(BASELINE['gate'] == 'A' and BASELINE['result'] == 'PASS', 'Baseline gate not passed')
    archive = args.parent / 'checkpoint-android/runtime-shell-source.tar.gz'
    require(sha(archive.read_bytes()) == BASELINE['transport_archive_sha256'], 'Wrong compiled transport archive')
    with tarfile.open(archive) as source:
        source.extractall(args.out / 'baseline-extracted', filter='data')
    baseline = args.out / 'baseline-extracted/shell-kodi'
    before = snapshot(baseline)
    require(before == BASELINE['transport_runtime_hashes'], 'Transport source identity mismatch')
    for name, value in BASELINE['identity']['cobra_source_hashes'].items():
        require(before[name] == BASELINE['approved_runtime_hashes'][name] == value, 'Cobra baseline differs: ' + name)
    dest = args.out / 'android-source'
    shutil.copytree(baseline, dest)
    subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-i', str(HERE / 'changes.patch')], cwd=dest, check=True)
    from source_scope import verify
    scope = verify(baseline, dest, args.out / 'CHANGED-METHODS.json')
    after = snapshot(dest)
    changed = sorted(n for n in before.keys() | after.keys() if before.get(n) != after.get(n))
    require(changed == ALLOWED and before.keys() == after.keys(), 'Source edits exceed declared Cobra files')
    write(args.out / 'SOURCE-PRESERVATION.json', {'before': before, 'after': after, 'changed': changed, 'cobra_baseline': 2103324, 'transport': 2103369, 'source_scope': scope})
    shutil.copy2(HERE / 'BASELINE-GATE-A.json', args.out)
    parent.factory.BASE_APK_SHA256 = CONFIG['transport_apk_sha256']
    parent.factory.VERSION_CODE = CONFIG['version_code']
    parent.factory.RELEASE = CONFIG['version_name']
    parent.factory.prepare(dest.resolve(), args.base.resolve(), args.build.resolve(), args.out.resolve())
    tests = args.build / 'xbmc/src/test/java/com/projectinfinity/kodi'
    tests.mkdir(parents=True, exist_ok=True)
    for name in ('cobra-navigation-2103157/tests/CobraNavigationUiTest.java', 'sports-hub-2103270/SportsHubTest.java'):
        shutil.copy2(HERE.parent / name, tests / Path(name).name)
    test_changes = []
    for name, (folder, _) in INHERITED.items():
        original = HERE.parent / folder / (name + '.java')
        override = HERE / 'inherited' / (name + '.java')
        source = override if override.exists() else original
        shutil.copy2(source, tests / source.name)
        test_changes.append({'suite': name, 'original_sha256': sha(original.read_bytes()), 'tested_sha256': sha(source.read_bytes()), 'expectations_updated': override.exists()})
    # Exact established 2103324 exclusion: the old drawer Sports destination was
    # replaced before that lock. This is unchanged, not a corrective-test skip.
    previous = tests / 'ProTeams312Test.java'
    old = '@Test public void proDrawerSportsOpensSameHubAndSelectionSurvivesRerender()'
    require(previous.read_text().count(old) == 1, 'Inherited exclusion preimage changed')
    previous.write_text(previous.read_text().replace(old, '/* Original locked 2103324 exclusion: Sports uses Pro tab. */ public void proDrawerSportsOpensSameHubAndSelectionSurvivesRerender()'))
    for name in test_spec().keys() - INHERITED.keys():
        shutil.copy2(HERE / (name + '.java'), tests / (name + '.java'))
    resources = args.build / 'xbmc/src/test/resources'
    resources.mkdir(parents=True, exist_ok=True)
    shutil.copy2(HERE.parent / 'cobra-pro-season-2103317/schedule-fixtures.json', resources)
    if (HERE / 'fixtures').exists():
        shutil.copytree(HERE / 'fixtures', resources, dirs_exist_ok=True)
    write(args.out / 'TEST-SCOPE.json', {'expected_suites': test_spec(), 'inherited_suites': test_changes, 'inherited_test_count': 167, 'new_tests_are_not_physical_acceptance': True})
    gradle = '''
android { testOptions { unitTests.includeAndroidResources = true; unitTests.all { maxHeapSize = "3g"; systemProperty "cobra.evidence", rootProject.file("../corrective-evidence/screenshots").absolutePath; systemProperty "cobra.corrective.evidence", rootProject.file("../corrective-evidence/runtime").absolutePath; systemProperty "cobra.corrective.routingBaseline", rootProject.file("../corrective-evidence/routing-baseline/ROUTING-REFERENCE.json").absolutePath; testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" } } } }
configurations { preservationTools }
dependencies { testImplementation 'junit:junit:4.13.2'; testImplementation 'org.robolectric:robolectric:4.14.1'; preservationTools 'org.smali:baksmali:2.5.2' }
tasks.register('exportPreservationTools') { doLast { rootProject.file('preservation-classpath.txt').text = configurations.preservationTools.asPath } }
'''
    with (args.build / 'xbmc/build.gradle').open('a') as output:
        output.write(gradle)


def baseline_reference(args):
    """Execute only disputed return paths on untouched source; never assemble an APK."""
    baseline = args.out / 'baseline-extracted/shell-kodi'
    require(snapshot(baseline) == BASELINE['transport_runtime_hashes'], 'Routing reference source is not the untouched approved transport')
    require(sha(args.base.read_bytes()) == CONFIG['transport_apk_sha256'], 'Routing reference APK identity changed')
    output = args.out / 'routing-baseline'
    output.mkdir(parents=True, exist_ok=False)
    build = args.build.with_name(args.build.name + '-routing-baseline')
    parent.factory.BASE_APK_SHA256 = CONFIG['transport_apk_sha256']
    parent.factory.VERSION_CODE = 2103369
    parent.factory.RELEASE = '1.0.9-Cancelled-Script-Receipt-RC1'
    parent.factory.prepare(baseline.resolve(), args.base.resolve(), build.resolve(), output.resolve())
    testdir = build / 'xbmc/src/test/java/com/projectinfinity/kodi'
    testdir.mkdir(parents=True, exist_ok=True)
    fixtures = ('cobra-navigation-2103157/tests/CobraNavigationUiTest.java',
                'sports-hub-2103270/SportsHubTest.java',
                'cobra-pro-refinement-2103322/CobraProHandoffTest.java',
                'cobra-pro-season-2103317/CobraProSeason317Test.java')
    for relative in fixtures:
        shutil.copy2(HERE.parent / relative, testdir / Path(relative).name)
    test = HERE / 'CobraCorrectiveRoutingReferenceTest.java'
    shutil.copy2(test, testdir / test.name)
    gradle = '''
android { testOptions { unitTests.includeAndroidResources = true; unitTests.all { maxHeapSize = "3g"; systemProperty "cobra.evidence", rootProject.file("../corrective-evidence/routing-baseline/screenshots").absolutePath; systemProperty "cobra.corrective.evidence", rootProject.file("../corrective-evidence/routing-baseline").absolutePath; testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" } } } }
dependencies { testImplementation 'junit:junit:4.13.2'; testImplementation 'org.robolectric:robolectric:4.14.1' }
'''
    with (build / 'xbmc/build.gradle').open('a') as handle:
        handle.write(gradle)
    name = 'com.projectinfinity.kodi.CobraCorrectiveRoutingReferenceTest'
    subprocess.run([str(build.resolve() / 'gradlew'), '--no-daemon', '--console=plain', '-p', str(build), ':xbmc:testReleaseUnitTest', '--tests', name], check=True)
    xml = build / ('xbmc/build/test-results/testReleaseUnitTest/TEST-' + name + '.xml')
    suite = ET.parse(xml).getroot()
    require(int(suite.attrib['tests']) == 1 and all(int(suite.attrib.get(k, 0)) == 0 for k in ('failures', 'errors', 'skipped')), 'Approved routing reference test failed')
    reference = output / 'ROUTING-REFERENCE.json'
    data = json.loads(reference.read_text())
    require(data.get('schema') == 1 and set(data.get('contexts', {})) == {'stopped_pro_sports', 'return_mobile', 'return_compact', 'return_cards', 'return_grid'}, 'Approved routing reference incomplete')
    require(snapshot(baseline) == BASELINE['transport_runtime_hashes'], 'Routing reference changed approved source')
    shutil.copy2(xml, output / xml.name)
    write(args.out / 'ROUTING-BASELINE-GATE.json', {'result': 'PASS', 'test_count': 1, 'reference_sha256': sha(reference.read_bytes()), 'test_source_sha256': sha(test.read_bytes()), 'source': BASELINE['transport_runtime_hashes'], 'native_recompiled': False, 'apk_assembled': False})


def tests(args):
    verify_source(args.out)
    command = [str(args.build.resolve() / 'gradlew'), '--no-daemon', '--console=plain', '-p', str(args.build), ':xbmc:testReleaseUnitTest']
    for name in test_spec():
        command.extend(['--tests', 'com.projectinfinity.kodi.' + name])
    subprocess.run(command, check=True)


def gates(args):
    proof = verify_source(args.out)
    routing_receipt = json.loads((args.out / 'ROUTING-BASELINE-GATE.json').read_text())
    reference = args.out / 'routing-baseline/ROUTING-REFERENCE.json'
    require(routing_receipt['result'] == 'PASS' and routing_receipt['source'] == BASELINE['transport_runtime_hashes'], 'Approved route reference gate absent')
    require(sha(reference.read_bytes()) == routing_receipt['reference_sha256'], 'Approved route reference changed')
    require(sha((HERE / 'CobraCorrectiveRoutingReferenceTest.java').read_bytes()) == routing_receipt['test_source_sha256'], 'Candidate and baseline routing tests differ')
    require(json.loads(reference.read_text()) == json.loads((args.out / 'runtime/ROUTING-REFERENCE.json').read_text()), 'Protected runtime routing differs from untouched approved source')
    expected = test_spec()
    suites = []
    for path in sorted((args.build / 'xbmc/build/test-results/testReleaseUnitTest').glob('TEST-*.xml')):
        suite = ET.parse(path).getroot()
        suites.append({'suite': suite.attrib['name'], **{k: int(suite.attrib.get(k, 0)) for k in ('tests', 'failures', 'errors', 'skipped')}})
    require({s['suite'] for s in suites} == {'com.projectinfinity.kodi.' + n for n in expected}, 'Required test suite missing or unexpected')
    require(all(s['failures'] == s['errors'] == s['skipped'] == 0 and s['tests'] >= expected[s['suite'].rsplit('.', 1)[-1]] for s in suites), 'Functional/UI gate failed or tests reduced/skipped')
    inventory = args.out / 'runtime/RUNTIME-CONTROL-INVENTORY.json'
    require(inventory.exists(), 'Actual runtime control inventories missing')
    data = json.loads(inventory.read_text())
    # Runtime tests own detailed assertions; this prevents missing evidence being
    # treated as passing solely because a GitHub job completed.
    require(data.get('result') == 'PASS', 'Runtime scope-isolation gate not passed')
    require(set(data.get('contexts', {})) == {'mobile', 'compact', 'cards', 'grid', 'pro_non_sports', 'pro_sports'}, 'Six-context runtime evidence incomplete')
    receipt = {'gates': {'A': 'PASS', 'B': 'PASS', 'C': 'PASS', 'D': 'PASS'}, 'source_after': proof['after'], 'test_suites': suites, 'test_total': sum(s['tests'] for s in suites), 'approved_routing_reference_test_count': routing_receipt['test_count'], 'approved_routing_reference_sha256': routing_receipt['reference_sha256'], 'runtime_inventory_sha256': sha(inventory.read_bytes()), 'physical_fold_verified': False}
    write(args.out / 'PRE-DEVICE-GATES.json', receipt)
    return receipt


def package(args):
    require((args.out / 'PRE-DEVICE-GATES.json').exists(), 'Packaging blocked: pre-device gates absent')
    receipt = gates(args)
    require(sha(args.base.read_bytes()) == CONFIG['transport_apk_sha256'], 'Retained APK changed')
    bt = Path(os.environ['ANDROID_HOME']) / 'build-tools/34.0.0'
    donor = args.build / 'xbmc/build/outputs/apk/release/xbmc-release.apk'
    require(resource_ids(bt / 'aapt2', args.base, args.out / 'base-resources.txt') == resource_ids(bt / 'aapt2', donor, args.out / 'donor-resources.txt'), 'Protected resource IDs changed')
    unsigned = args.out / 'candidate-unsigned.apk'
    parent.merge(args.base, donor, unsigned)
    verify_manifest_pair(run(bt / 'aapt', 'dump', 'xmltree', args.base, 'AndroidManifest.xml', output=args.out / 'base-manifest.txt'), run(bt / 'aapt', 'dump', 'xmltree', unsigned, 'AndroidManifest.xml', output=args.out / 'candidate-manifest.txt'))
    from bytecode_guard import compare
    dex = compare(args.base, unsigned, (args.build / 'preservation-classpath.txt').read_text().strip(), args.out)
    preserved = parent.verify_payload(args.base, unsigned)
    for name in ('INFINITY_KEYSTORE_B64', 'INFINITY_STORE_PASSWORD', 'INFINITY_KEY_PASSWORD', 'INFINITY_KEY_ALIAS'):
        require(bool(os.environ.get(name)), 'Permanent signing identity unavailable: ' + name)
    final = args.out / CONFIG['apk_name']
    run('bash', ROOT / 'scripts/sign-infinity71.sh', unsigned, final)
    cert = run(bt / 'apksigner', 'verify', '--verbose', '--print-certs', final, output=args.out / 'signing-verification.txt')
    require(CONFIG['signer_sha256'] in cert.lower(), 'Permanent signing certificate changed')
    badging = run(bt / 'aapt', 'dump', 'badging', final, output=args.out / 'badging.txt')
    require(f"package: name='{parent.PACKAGE}' versionCode='{CONFIG['version_code']}' versionName='{CONFIG['version_name']}'" in badging, 'Wrong package/version identity')
    parent.verify_payload(args.base, final)
    report = {**CONFIG, 'implementation_state': 'SIGNED_TEST_CANDIDATE', 'android_runtime_tests': 'PASS', 'apk_created': True, 'source_commit': os.environ['GITHUB_SHA'], 'validation_run': os.environ['GITHUB_RUN_ID'], 'apk_sha256': sha(final.read_bytes()), 'apk_bytes': final.stat().st_size, 'test_total': receipt['test_total'], 'test_suites': receipt['test_suites'], 'gates': {**receipt['gates'], 'E': 'PASS', 'F': 'PENDING_USER_FOLD_TEST'}, 'native_recompiled': False, 'data_reset': False, 'physical_device_verified': False, 'locked': False, 'android_source_changes': ALLOWED, **preserved, 'bytecode_preservation': dex}
    write(args.out / 'APK-VERIFICATION.json', report)
    with tarfile.open(args.out / 'compiled-runtime-source.tar.gz', 'w:gz') as archive:
        archive.add(args.out / 'android-source', arcname='shell-kodi')
    (args.out / 'SHA256.txt').write_text(sha(final.read_bytes()) + '  ' + final.name + '\n')
    unsigned.unlink()
    print('Signed corrective test candidate packaged only after gates A–E; physical Fold acceptance pending.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('prepare', 'baseline_reference', 'tests', 'gates', 'package'))
    parser.add_argument('--base', type=Path, default=Path('transport-apk/Infinity-2103369-Cancelled-Script-Receipt-RC1.apk'))
    parser.add_argument('--parent', type=Path, default=Path('transport-evidence/evidence'))
    parser.add_argument('--build', type=Path, default=Path('corrective-build'))
    parser.add_argument('--out', type=Path, default=Path('corrective-evidence'))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    globals()[args.mode](args)
