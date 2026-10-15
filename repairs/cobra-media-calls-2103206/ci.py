"""Gate the frozen final requested features; no native engine rebuild."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from apply import checked_review

ROOT = Path(__file__).resolve().parent
OLD = '1.0.9-Cobra-Final-Features-RC1'
NEW = '1.0.9-Cobra-Media-Calls-RC1'
VERSION = 2103206
PARENT = 'd4abe960873929ebee3f13af6a976c19011d0cdc'
PARENT_APK = 'd91fc127fda0c9f37c7f8d44e17eabb067a3fc7137e15c115837e4b69feec89d'
CERT = 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
GRADLE = 'tools/android/packaging/xbmc/build.gradle.in'
ACTIVITY = 'tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def replace(path, old, new):
    path = Path(path)
    text = path.read_text()
    require(text.count(old) == 1, 'Identity drift: ' + old)
    path.write_text(text.replace(old, new, 1))


def upgrade():
    receipt = Path('engine/background-resume-source.json')
    data = json.loads(receipt.read_text())
    require(sha('baseline205/Infinity-' + OLD + '.apk') == PARENT_APK, 'Wrong locked rollback APK')
    subprocess.run(['python3', str(ROOT / 'apply.py'), '--source', 'kodi', '--receipt', str(receipt),
                    '--out', 'audit206/patch'], check=True)
    patch = json.loads(Path('audit206/patch/patch.json').read_text())
    for name, row in patch['files'].items():
        data['files'].setdefault(name, {'before': row['before']})['after'] = row['after']
    replace(Path('kodi') / GRADLE, 'versionCode 2103205', 'versionCode 2103206')
    replace(Path('kodi') / GRADLE, 'versionName "' + OLD + '"', 'versionName "' + NEW + '"')
    replace('scripts/infinity_background_resume.py', 'VERSION_CODE = 2103205', 'VERSION_CODE = 2103206')
    replace('scripts/infinity_background_resume.py', "RELEASE = '" + OLD + "'", "RELEASE = '" + NEW + "'")
    packager = Path('scripts/package_background_resume.py')
    text = packager.read_text()
    require(text.count('Infinity-' + OLD) >= 2, 'Packager drift')
    packager.write_text(text.replace('Infinity-' + OLD, 'Infinity-' + NEW))
    data['files'][GRADLE]['after'] = sha(Path('kodi') / GRADLE)
    data.update(version_code=VERSION, version_name=NEW, source_parent=2103205,
                source_parent_commit=PARENT, source_parent_locked=True, candidate_locked=False,
                physical_device_verified=False, runtime_device_tested=False,
                native_engine_recompiled=False, new_controls=True, user_requested_controls=True, new_features=True,
                complete_product_acceptance=False)
    receipt.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
    for name, row in data['files'].items():
        require(sha(Path('kodi') / name) == row['after'], 'Final input drift: ' + name)
    with Path('audit206/native-after.patch').open('wb') as output:
        subprocess.run(['git', '-C', 'kodi', 'diff', '--binary', '--', 'xbmc'], stdout=output, check=True)
    require(Path('audit206/native-after.patch').read_bytes() == Path('engine/native-before.patch').read_bytes(),
            'Native source changed')
    Path('audit206/source-preservation.json').write_text(json.dumps({
        'passed': True, 'parent_commit': PARENT, 'changed_runtime_files': sorted(patch['files']),
        'protected_runtime_members': patch['protected_runtime_members'],
        'native_source_unchanged': True, 'physical_device_verified': False,
    }, indent=2) + '\n')


def verify():
    checked_review()
    baseline = Path('baseline205/Infinity-' + OLD + '.apk')
    final = Path('signed206/Infinity-' + NEW + '.apk')
    require(sha(baseline) == PARENT_APK, 'Wrong baseline')
    audit = json.loads(Path('signed206/background-resume-apk-audit.json').read_text())
    require(audit['version_code'] == VERSION and audit['version_name'] == NEW, 'Wrong release identity')
    require(audit['apk_sha256'] == sha(final) and audit['signer_certificate_sha256'] == CERT,
            'Signer/hash mismatch')
    require(audit['native_recompiled'] is False, 'Native rebuilt')
    with zipfile.ZipFile(baseline) as old, zipfile.ZipFile(final) as new:
        require(new.testzip() is None and len(new.namelist()) == len(set(new.namelist())),
                'APK corrupt/duplicate members')
        require(set(old.namelist()) == set(new.namelist()), 'APK member inventory changed')
        keep = {name for name in old.namelist()
                if name.startswith(('lib/', 'assets/', 'res/')) or name == 'resources.arsc'}
        for name in keep:
            require(old.read(name) == new.read(name), 'Protected payload changed: ' + name)
        dex = b''.join(new.read(name) for name in new.namelist() if re.fullmatch(r'classes\d*\.dex', name))
        require(all(('Cobra' + str(version)).encode() not in dex for version in [2103201, 2103202, 2103203, 2103204, 2103205, 2103206]),
                'Test code packaged')
    badging = Path('signed206/badging.txt').read_text()
    require("package: name='com.projectinfinity.kodi' versionCode='2103206'" in badging,
            'Package identity changed')
    require('application-debuggable' not in badging, 'Debuggable release')
    Path('audit206/final-verification.json').write_text(json.dumps({
        'build': VERSION, 'parent_commit': PARENT, 'parent_apk_sha256': PARENT_APK,
        'apk_sha256': sha(final), 'signer': CERT, 'protected_payload_entries': len(keep),
        'native_engine_recompiled': False, 'native_assets_resources_byte_identical': True,
        'physical_device_verified': False, 'installed_update_tested': False,
    }, indent=2) + '\n')


def deliver():
    theme_guards = json.loads(Path('audit205/theme-fixture-adapter-guards.json').read_text())
    theme_fixture = json.loads(Path('audit205/theme-fixture-adaptation.json').read_text())
    require(theme_guards.get('suite') == '205 explicit theme-preview fixture adapter guards' and
            theme_guards.get('tests') == 7 and theme_guards.get('failures') == 0 and
            theme_guards.get('errors') == 0 and theme_guards.get('passed') is True and
            theme_guards.get('physical_device_verified') is False, 'Theme fixture adapter guards missing/nonpassing')
    require(theme_fixture.get('status') == 'adapted' and
            theme_fixture.get('frozen_source_sha256') == theme_fixture.get('input_sha256') ==
            '0a17437b2064e81df1e721ab0ef439a2d2a0aa76c26ae01dfbd4e9b708651ddb' and
            theme_fixture.get('output_sha256') ==
            sha('audit205/theme-fixture/Cobra2103162ThemeRotationTest.java') ==
            'ebf89cdcda0c0ec2d96d53493e0f141a9b842d36cce41e0246636f9abf738962',
            'Unreviewed generated theme fixture adaptation')
    require(theme_fixture.get('historical_repository_tests_modified') is False and
            theme_fixture.get('case_names_unchanged') is True and
            theme_fixture.get('original_assertions_byte_identical') is True and
            theme_fixture.get('changes_outside_reviewed_insertion') is False and
            theme_fixture.get('physical_device_verified') is False,
            'Inherited theme assertion preservation contract missing')
    inherited = json.loads((ROOT / 'inherited-android-cases.json').read_text())
    new = json.loads((ROOT / 'new-android-cases.json').read_text())
    parent = ROOT.parent / 'cobra-final-features-2103205'
    parent_cases = (json.loads((parent / 'inherited-android-cases.json').read_text()) |
                    json.loads((parent / 'new-android-cases.json').read_text()))
    require(inherited == parent_cases and sum(map(len, inherited.values())) == 637,
            'Inherited 637-test identity inventory drift')
    require(not (set(inherited) & set(new)) and bool(new), 'Missing/overlapping new suites')
    reviewed = checked_review()
    require(reviewed['inherited_android_cases'] == 637 and
            reviewed['new_android_cases'] == sum(map(len, new.values())), 'Reviewed test count drift')
    expected = inherited | new
    suites = {}
    for folder in ['audit159/android/cobra-regression/test-results',
                   'audit159/android/experience/test-results',
                   'audit198/android/runtime/test-results', 'audit198/targeted/test-results']:
        require(Path(folder).is_dir(), 'Missing evidence: ' + folder)
        for path in Path(folder).glob('TEST-*.xml'):
            root = ET.parse(path).getroot()
            name, cases = root.get('name'), root.findall('testcase')
            require(len(cases) == int(root.get('tests', '-1')), 'Invalid testcase count')
            require(all(int(root.get(key, '0')) == 0 for key in ['failures', 'errors', 'skipped']),
                    'Nonpassing suite: ' + str(name))
            require(all(all(case.find(key) is None for key in ['failure', 'error', 'skipped'])
                        for case in cases), 'Nonpassing case')
            require(all(case.get('classname') and case.get('name') for case in cases),
                    'Missing testcase identity')
            identities = sorted((case.get('classname'), case.get('name')) for case in cases)
            require(len(identities) == len(set(identities)), 'Duplicate test identity: ' + str(name))
            row = {'suite': name, 'tests': len(cases), 'evidence': str(path),
                   'cases': [list(case) for case in identities]}
            if name in suites:
                require(suites[name]['cases'] == row['cases'], 'Conflicting suite')
            suites[name] = row
    require(set(suites) == set(expected), 'Suite inventory mismatch: ' + str(set(suites) ^ set(expected)))
    for name, cases in expected.items():
        require(suites[name]['cases'] == cases, 'Test identity mismatch: ' + name)
    final = json.loads(Path('audit206/final-verification.json').read_text())
    require(final['apk_sha256'] == sha('signed206/Infinity-' + NEW + '.apk'), 'APK drift')
    result = {
        'build': VERSION, 'immediate_parent': 2103205, 'parent_commit': PARENT,
        'inherited_android_tests': 637, 'new_android_tests': sum(map(len, new.values())),
        'android_test_suites': list(suites.values()), 'apk_sha256': final['apk_sha256'],
        'native_engine_recompiled': False, 'user_requested_controls': True, 'new_features': True,
        'physical_device_verified': False, 'installed_update_tested': False,
        'audible_phone_call_playback_verified': False, 'systemui_pip_controls_verified': False,
        'physical_theme_rendering_verified': False,
        'candidate_locked': False, 'complete_product_acceptance': False,
        'status': 'TEST CANDIDATE: physical Android/Samsung acceptance required',
    }
    Path('signed206/ACCEPTANCE.json').write_text(json.dumps(result, indent=2) + '\n')
    for name in ['final-verification.json', 'source-preservation.json']:
        shutil.copy2(Path('audit206') / name, Path('signed206') / ('2103206-' + name))
    shutil.copy2(ROOT / 'AUDIT.md', 'signed206/AUDIT-2103206.md')
    shutil.copy2(ROOT / 'DEVICE-TEST.md', 'signed206/DEVICE-TEST.md')
    print('PASS: all 637 inherited identities and exact new cases; physical acceptance not claimed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['upgrade', 'verify', 'deliver'])
    globals()[parser.parse_args().phase]()
