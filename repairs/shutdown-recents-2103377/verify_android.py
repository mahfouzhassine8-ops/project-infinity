#!/usr/bin/env python3
"""Compile the saved Recents candidate and retain all 207 locked Android tests.

Verification only. This script cannot package, sign, promote or install an APK.
The native engine, skin, add-ons, permanent signer and user data are not changed.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUNTIME = Path('tools/android/packaging/xbmc/src')
OVERLAY = ROOT / 'repairs/android-checkpoint-shutdown/runtime/android/overlay'
PIN = '808b4acc4d1a6aa1cbc8bc4a1848de88b81103e6'
APK_SHA = '8e8e139929592daedb63e0e41040258d655f132fd025b236de7dee1e88b47649'
ARCHIVES = {
    'runtime-source.tar.gz': '639551e497b1be109b492311cc13a54921703eed5d6d8e29c25dc76a21e85997',
    'test-source.tar.gz': 'b3b96cd6affd6aae6e6a601a00279b89b1809f96f50f1970eb84429e94496f43',
}
BEFORE = {
    'InfinityCloseNativeLease.java.in': '2db2bcb9a94bb42c594e691cda7deb38b2dbf9afd4c90160a173c7c832cfeec2',
    'InfinityCloseGuardService.java.in': '4c42e3be884e6cea27ddee9c094ca379f408367e9c5d6bfb788a8ccd4fec5050',
}
EXTRA = 'InfinityCloseRecents2103377Test'


def require(value, message):
    if not value:
        raise RuntimeError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(root):
    return {p.relative_to(root).as_posix(): digest(p) for p in sorted(root.rglob('*')) if p.is_file()}


def unique(root, name):
    matches = list(root.rglob(name))
    require(len(matches) == 1, 'Missing or ambiguous ' + name)
    return matches[0]


def write(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')


def extract(archive, output):
    require(digest(archive) == ARCHIVES[archive.name], 'Unverified source archive ' + archive.name)
    with tarfile.open(archive) as stream:
        for member in stream.getmembers():
            p = Path(member.name)
            require(not p.is_absolute() and '..' not in p.parts and (member.isfile() or member.isdir()), 'Unsafe archive member')
        stream.extractall(output)


def cases(root):
    result = set()
    for p in root.rglob('TEST-*.xml'):
        for case in ET.parse(p).getroot().findall('testcase'):
            key = (case.get('classname'), case.get('name'))
            require(key not in result, 'Duplicate JUnit case ' + repr(key))
            result.add(key)
    return result


def prepare(args):
    require(digest(args.apk) == APK_SHA, 'Not the locked 2103376 APK')
    args.out.mkdir(parents=True, exist_ok=False)
    extract(unique(args.parent, 'runtime-source.tar.gz'), args.out / 'parent-source')
    before = args.out / 'parent-source/source'
    proof = json.loads(unique(args.parent, 'SOURCE-PRESERVATION.json').read_text())['after']
    original = snapshot(before)
    require(len(original) == 264 and original == proof, 'Runtime differs from compiled parent evidence')
    source = args.out / 'source'
    shutil.copytree(before, source)
    for name, expected in BEFORE.items():
        require(digest(before / RUNTIME / name) == expected, 'Parent overlay/runtime mismatch: ' + name)
        shutil.copy2(OVERLAY / RUNTIME / name, source / RUNTIME / name)
    after = snapshot(source)
    changed = sorted(k for k in original if original[k] != after[k])
    require(original.keys() == after.keys() and changed == sorted(str(RUNTIME / name) for name in BEFORE), 'Unauthorized runtime delta')
    write(args.out / 'SOURCE-PRESERVATION.json', {
        'source_commit': os.environ['GITHUB_SHA'], 'parent_commit': PIN,
        'before': original, 'after': after, 'changed': changed,
        'unchanged_runtime_files': 262, 'native_source_changed': False,
        'skin_changed': False, 'apk_packaging_authorized_by_this_job': False,
    })
    sys.path.insert(0, str(ROOT / 'repairs/mobile-regressions-2103304'))
    spec = importlib.util.spec_from_file_location('parent_android_factory', ROOT / 'repairs/mobile-regressions-2103304/package_candidate.py')
    factory = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(factory)
    factory.BASE_APK_SHA256 = APK_SHA
    factory.VERSION_CODE = 2103377
    factory.RELEASE = '1.0.9-Close-Recents-RC1'
    factory.prepare(source.resolve(), args.apk.resolve(), args.build.resolve(), args.out.resolve())
    extract(unique(args.parent, 'test-source.tar.gz'), args.build / 'xbmc/src')
    tests = args.build / 'xbmc/src/test'
    originals = snapshot(tests)
    write(args.out / 'LOCKED-TEST-SOURCES.json', originals)
    shutil.copy2(HERE / (EXTRA + '.java'), tests / 'java/com/projectinfinity/kodi' / (EXTRA + '.java'))
    parent_results = json.loads(unique(args.parent, 'RUNTIME-RESULTS.json').read_text())
    require(parent_results['totals'] == {'tests': 207, 'failures': 0, 'errors': 0, 'skipped': 0}, 'Parent test evidence changed')
    expected = {k: v['tests'] for k, v in parent_results['suites'].items()}
    require(sum(expected.values()) == 207 and len(cases(args.parent)) == 207, 'Parent test membership incomplete')
    write(args.out / 'EXPECTED-LOCKED-SUITES.json', expected)
    with (args.build / 'xbmc/build.gradle').open('a') as stream:
        stream.write('''
android { testOptions { unitTests.includeAndroidResources = true; unitTests.all {
 maxHeapSize = "3g";
 systemProperty "cobra.evidence", rootProject.file("../recents-evidence/screenshots").absolutePath;
 systemProperty "cobra.clean.evidence", rootProject.file("../recents-evidence/runtime").absolutePath;
 testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" }
} } }
dependencies { testImplementation 'junit:junit:4.13.2'; testImplementation 'org.robolectric:robolectric:4.14.1' }
tasks.withType(Test).configureEach { filter {
''')
        for name in sorted(set(expected) | {EXTRA}):
            stream.write(" includeTestsMatching 'com.projectinfinity.kodi." + name + "'\n")
        stream.write('} }\n')
    print('STAGED: 262 unchanged runtime files, two saved Recents edits, all 207 original test cases, additional targeted tests. No APK packaging.')


def review(args):
    expected = json.loads((args.out / 'EXPECTED-LOCKED-SUITES.json').read_text())
    original = json.loads((args.out / 'LOCKED-TEST-SOURCES.json').read_text())
    current = snapshot(args.build / 'xbmc/src/test')
    extra_path = 'java/com/projectinfinity/kodi/' + EXTRA + '.java'
    preserved = set(current) == set(original) | {extra_path} and all(current.get(k) == v for k, v in original.items())
    result_root = args.build / 'xbmc/build/test-results/testReleaseUnitTest'
    suites = {}
    for p in result_root.glob('TEST-*.xml'):
        xml = ET.parse(p).getroot()
        name = xml.get('name').rsplit('.', 1)[-1]
        require(name not in suites, 'Duplicate test suite')
        suites[name] = {k: int(xml.get(k, '0')) for k in ('tests', 'failures', 'errors', 'skipped')}
    locked = {k: suites[k] for k in expected if k in suites}
    total = {k: sum(v[k] for v in locked.values()) for k in ('tests', 'failures', 'errors', 'skipped')}
    named = cases(result_root)
    old_names = cases(args.parent)
    same_names = {case for case in named if case[0].rsplit('.', 1)[-1] in expected} == old_names
    targets = suites.get(EXTRA, {})
    source_proof = json.loads((args.out / 'SOURCE-PRESERVATION.json').read_text())
    runtime_preserved = snapshot(args.out / 'source') == source_proof['after']
    source = (args.build / 'xbmc/java/com/projectinfinity/kodi')
    java_matches = all((source / name.removesuffix('.in')).read_text() == (OVERLAY / RUNTIME / name).read_text().replace('@APP_PACKAGE@', 'com.projectinfinity.kodi') for name in BEFORE)
    report = {
        'source_commit': os.environ['GITHUB_SHA'], 'parent_commit': PIN,
        'locked_totals': total, 'locked_suites': locked, 'targeted_results': targets,
        'all_207_original_case_names_preserved': same_names,
        'original_test_sources_and_fixtures_unchanged': preserved,
        'runtime_source_preserved': runtime_preserved,
        'compiled_java_inputs_match_candidate': java_matches,
        'physical_device_verified': False, 'native_compilation_performed': False,
        'apk_packaged_or_signed': False, 'playlist_service_fixed': False,
    }
    write(args.out / 'ANDROID-VERIFICATION.json', report)
    require(preserved and same_names and runtime_preserved and java_matches, 'Preservation verification failed')
    require(set(suites) == set(expected) | {EXTRA}, 'Missing/unexpected test suite')
    require(all(locked[n]['tests'] == expected[n] for n in expected), 'Locked suite test count changed')
    require(total == {'tests': 207, 'failures': 0, 'errors': 0, 'skipped': 0}, 'A locked regression failed or was skipped')
    require(targets.get('tests', 0) >= 20 and all(targets.get(k) == 0 for k in ('failures', 'errors', 'skipped')), 'Targeted Recents safety tests failed or were skipped')
    print('PASS: 207 unchanged regressions and', targets['tests'], 'targeted checks. Host Android simulation only; no native/device/shutdown claim.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'review'])
    for name in ('parent', 'apk', 'build', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    globals()[args.mode](args)
