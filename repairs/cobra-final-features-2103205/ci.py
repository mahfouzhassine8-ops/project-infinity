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
OLD = '1.0.9-Cobra-OLED-Blue-RC1'
NEW = '1.0.9-Cobra-Final-Features-RC1'
VERSION = 2103205
PARENT = '166cf9dad40a8a0333563830a3c0965ce4e81da6'
PARENT_APK = 'fd6f02c3d1e5bac5ea1814f76b6dba29939d48c1debafd06c4fd16e9123d62a9'
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
    require(sha('baseline204/Infinity-' + OLD + '.apk') == PARENT_APK, 'Wrong locked rollback APK')
    subprocess.run(['python3', str(ROOT / 'apply.py'), '--source', 'kodi', '--receipt', str(receipt),
                    '--out', 'audit205/patch'], check=True)
    patch = json.loads(Path('audit205/patch/patch.json').read_text())
    for name, row in patch['files'].items():
        data['files'].setdefault(name, {'before': row['before']})['after'] = row['after']
    replace(Path('kodi') / GRADLE, 'versionCode 2103204', 'versionCode 2103205')
    replace(Path('kodi') / GRADLE, 'versionName "' + OLD + '"', 'versionName "' + NEW + '"')
    replace('scripts/infinity_background_resume.py', 'VERSION_CODE = 2103204', 'VERSION_CODE = 2103205')
    replace('scripts/infinity_background_resume.py', "RELEASE = '" + OLD + "'", "RELEASE = '" + NEW + "'")
    packager = Path('scripts/package_background_resume.py')
    text = packager.read_text()
    require(text.count('Infinity-' + OLD) >= 2, 'Packager drift')
    packager.write_text(text.replace('Infinity-' + OLD, 'Infinity-' + NEW))
    data['files'][GRADLE]['after'] = sha(Path('kodi') / GRADLE)
    data.update(version_code=VERSION, version_name=NEW, source_parent=2103204,
                source_parent_commit=PARENT, source_parent_locked=True, candidate_locked=False,
                physical_device_verified=False, runtime_device_tested=False,
                native_engine_recompiled=False, new_controls=True, user_requested_controls=True, new_features=True,
                complete_product_acceptance=False)
    receipt.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
    for name, row in data['files'].items():
        require(sha(Path('kodi') / name) == row['after'], 'Final input drift: ' + name)
    with Path('audit205/native-after.patch').open('wb') as output:
        subprocess.run(['git', '-C', 'kodi', 'diff', '--binary', '--', 'xbmc'], stdout=output, check=True)
    require(Path('audit205/native-after.patch').read_bytes() == Path('engine/native-before.patch').read_bytes(),
            'Native source changed')
    Path('audit205/source-preservation.json').write_text(json.dumps({
        'passed': True, 'parent_commit': PARENT, 'changed_runtime_files': sorted(patch['files']),
        'protected_runtime_members': patch['protected_runtime_members'],
        'native_source_unchanged': True, 'physical_device_verified': False,
    }, indent=2) + '\n')


def verify():
    checked_review()
    baseline = Path('baseline204/Infinity-' + OLD + '.apk')
    final = Path('signed205/Infinity-' + NEW + '.apk')
    require(sha(baseline) == PARENT_APK, 'Wrong baseline')
    audit = json.loads(Path('signed205/background-resume-apk-audit.json').read_text())
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
        require(all(('Cobra' + str(version)).encode() not in dex for version in [2103201, 2103202, 2103203, 2103204, 2103205]),
                'Test code packaged')
    badging = Path('signed205/badging.txt').read_text()
    require("package: name='com.projectinfinity.kodi' versionCode='2103205'" in badging,
            'Package identity changed')
    require('application-debuggable' not in badging, 'Debuggable release')
    Path('audit205/final-verification.json').write_text(json.dumps({
        'build': VERSION, 'parent_commit': PARENT, 'parent_apk_sha256': PARENT_APK,
        'apk_sha256': sha(final), 'signer': CERT, 'protected_payload_entries': len(keep),
        'native_engine_recompiled': False, 'native_assets_resources_byte_identical': True,
        'physical_device_verified': False, 'installed_update_tested': False,
    }, indent=2) + '\n')


def deliver():
    inherited = json.loads((ROOT / 'inherited-android-cases.json').read_text())
    new = json.loads((ROOT / 'new-android-cases.json').read_text())
    parent = ROOT.parent / 'cobra-oled-blue-2103204'
    parent_cases = (json.loads((parent / 'inherited-android-cases.json').read_text()) |
                    json.loads((parent / 'new-android-cases.json').read_text()))
    require(inherited == parent_cases and sum(map(len, inherited.values())) == 500,
            'Inherited 500-test identity inventory drift')
    require(not (set(inherited) & set(new)) and bool(new), 'Missing/overlapping new suites')
    reviewed = checked_review()
    require(reviewed['inherited_android_cases'] == 500 and
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
    final = json.loads(Path('audit205/final-verification.json').read_text())
    require(final['apk_sha256'] == sha('signed205/Infinity-' + NEW + '.apk'), 'APK drift')
    result = {
        'build': VERSION, 'immediate_parent': 2103204, 'parent_commit': PARENT,
        'inherited_android_tests': 500, 'new_android_tests': sum(map(len, new.values())),
        'android_test_suites': list(suites.values()), 'apk_sha256': final['apk_sha256'],
        'native_engine_recompiled': False, 'user_requested_controls': True, 'new_features': True,
        'physical_device_verified': False, 'installed_update_tested': False,
        'audible_phone_call_playback_verified': False, 'systemui_pip_controls_verified': False,
        'physical_theme_rendering_verified': False,
        'candidate_locked': False, 'complete_product_acceptance': False,
        'status': 'TEST CANDIDATE: physical Android/Samsung acceptance required',
    }
    Path('signed205/ACCEPTANCE.json').write_text(json.dumps(result, indent=2) + '\n')
    for name in ['final-verification.json', 'source-preservation.json']:
        shutil.copy2(Path('audit205') / name, Path('signed205') / ('2103205-' + name))
    shutil.copy2(ROOT / 'AUDIT.md', 'signed205/AUDIT-2103205.md')
    shutil.copy2(ROOT / 'DEVICE-TEST.md', 'signed205/DEVICE-TEST.md')
    print('PASS: all 500 inherited identities and exact new cases; physical acceptance not claimed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['upgrade', 'verify', 'deliver'])
    globals()[parser.parse_args().phase]()
