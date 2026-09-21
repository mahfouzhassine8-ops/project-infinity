"""208 is a reviewed successor to the exact passed 207, never a native rebuild."""
from pathlib import Path
import argparse
import base64
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from contract import *

ROOT = Path(__file__).resolve().parent

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

def replace(path, old, new):
    path = Path(path)
    text = path.read_text()
    require(text.count(old) == 1, 'Identity anchor drift: ' + old)
    path.write_text(text.replace(old, new, 1))

def review():
    reviewed = json.loads((ROOT / 'reviewed.json').read_text())
    require(reviewed['parent_commit'] == PARENT_COMMIT, 'Wrong immutable 207 parent')
    require(reviewed['parent_apk_sha256'] == PARENT_APK, 'Wrong rollback identity')
    require(set(reviewed['files']) <= ALLOWED_JAVA | set(ICON_SLOTS) | {GRADLE}, 'Unreviewed source scope')
    require(set(reviewed['files']) & ALLOWED_JAVA, 'No reviewed Java delta')
    for name, digest in reviewed['recipe_hashes'].items():
        require(sha(ROOT / name) == digest, 'Recipe drift: ' + name)
    require(len(reviewed['parent_inventory']) == 226, 'Parent source inventory drift')
    return reviewed

def protect(source, parser_path):
    parser = module('protected208_parser', parser_path)
    text = (Path(source) / ACTIVITY).read_text()
    contract = json.loads((ROOT / 'protected-members.json').read_text())
    require(len(contract) == 49, 'Protected member inventory reduced')
    for name, row in contract.items():
        member = parser.member(text, name, row['kind']) if row['kind'] == 'class' else parser.member(text, name)
        require(hashlib.sha256(member.encode()).hexdigest() == row['sha256'], 'Protected member changed: ' + name)

def upgrade():
    reviewed = review()
    source = Path('kodi')
    rollback = Path('baseline207') / ('Infinity-' + OLD + '.apk')
    export = Path('baseline207/Cobra-2103207-Generated-Android-Source.zip')
    require(sha(rollback) == PARENT_APK, 'Wrong locked 207 rollback APK')
    require(sha(export) == PARENT_SOURCE, 'Wrong locked 207 source export')
    baseline = json.loads(Path('signed207/ACCEPTANCE.json').read_text())
    require(baseline['build'] == 2103207 and baseline['candidate_tests'] == 691 and baseline['candidate_suites'] == 69, 'Original 207 tests did not pass')
    require(sha(Path('signed207') / ('Infinity-' + OLD + '.apk')) == PARENT_APK, 'Reconstructed 207 APK differs from exact lock')
    receipt = Path('engine/background-resume-source.json')
    data = json.loads(receipt.read_text())
    require(data['version_code'] == 2103207, 'Not a built 207 source')
    for name, digest in reviewed['parent_inventory'].items():
        require(sha(source / name) == digest, 'Locked 207 source drift: ' + name)
    parser_path = Path('audit206/repairs/cobra-original-player-menu-2103197/apply.py')
    protect(source, parser_path)
    subprocess.run(['git', 'apply', '--check', str(ROOT / 'features.patch')], cwd=source, check=True)
    subprocess.run(['git', 'apply', str(ROOT / 'features.patch')], cwd=source, check=True)
    assets = json.loads((ROOT / 'asset-payloads.json').read_text())
    require(set(assets) == set(reviewed['files']) & set(ICON_SLOTS), 'Binary source scope mismatch')
    for name, encoded in assets.items():
        target = source / name
        require(sha(target) == reviewed['files'][name]['before'], 'Parent icon source drift: ' + name)
        content = base64.b64decode(encoded, validate=True)
        require(hashlib.sha256(content).hexdigest() == reviewed['files'][name]['after'], 'Unreviewed binary source')
        target.write_bytes(content)
    for name, row in reviewed['files'].items():
        require(sha(source / name) == row['after'], 'Unexpected patch result: ' + name)
        if name in data['files']:
            data['files'][name]['after'] = row['after']
        else:
            data['files'][name] = dict(before=row['before'], after=row['after'])
    protect(source, parser_path)
    replace('scripts/infinity_background_resume.py', 'VERSION_CODE = 2103207', 'VERSION_CODE = 2103208')
    replace('scripts/infinity_background_resume.py', "RELEASE = '" + OLD + "'", "RELEASE = '" + NEW + "'")
    packager = Path('scripts/package_background_resume.py')
    text = packager.read_text()
    require(text.count('Infinity-' + OLD) >= 2, 'Packager output identity drift')
    text = text.replace('Infinity-' + OLD, 'Infinity-' + NEW)
    text = text.replace('exact run-40 native engine/assets/resources; permanent signer verified',
                        'exact native engine/assets/resource table; approved icon-only payload delta; permanent signer verified')
    packager.write_text(text)
    data.update(version_code=VERSION, version_name=NEW, source_parent=2103207,
                source_parent_commit=PARENT_COMMIT, candidate_locked=False,
                physical_device_verified=False, runtime_device_tested=False,
                native_engine_recompiled=False, complete_product_acceptance=False,
                new_features=False, user_requested_controls=True,
                reviewed_branding_delta='approved-resources.json')
    receipt.write_text(json.dumps(data, indent=2) + '\n')
    for name, row in data['files'].items():
        require(sha(source / name) == row['after'], 'Final source receipt drift: ' + name)
    with Path('audit208/native-after.patch').open('wb') as output:
        subprocess.run(['git', '-C', 'kodi', 'diff', '--binary', '--', 'xbmc'], stdout=output, check=True)
    require(Path('audit208/native-after.patch').read_bytes() == Path('engine/native-before.patch').read_bytes(), 'Native source diff changed')
    Path('audit208/source-preservation.json').write_text(json.dumps(dict(
        parent_commit=PARENT_COMMIT, changed_source_files=sorted(reviewed['files']),
        protected_members=49, native_source_unchanged=True,
        no_new_permissions=True, physical_device_verified=False), indent=2) + '\n')

def verify():
    reviewed = review()
    from branding_package import verify_exact_payload_delta
    base = Path('baseline207') / ('Infinity-' + OLD + '.apk')
    apk = Path('signed208') / ('Infinity-' + NEW + '.apk')
    require(sha(base) == PARENT_APK, 'Locked rollback drift')
    audit = json.loads(Path('signed208/background-resume-apk-audit.json').read_text())
    require(audit['version_code'] == VERSION and audit['version_name'] == NEW, 'Wrong successor identity')
    require(audit['apk_sha256'] == sha(apk) and audit['signer_certificate_sha256'] == CERT, 'Signer/hash mismatch')
    require(audit['native_recompiled'] is False and audit['smali_used'] is False, 'Forbidden native/SMALI work')
    rows = json.loads((ROOT / 'approved-resources.json').read_text())
    preserved = verify_exact_payload_delta(base, apk, rows)
    with zipfile.ZipFile(apk) as archive:
        joined = b''.join(archive.read(name) for name in archive.namelist() if re.fullmatch(r'classes\d*\.dex', name))
        require(all(('Cobra' + str(number)).encode() not in joined for number in range(2103201, 2103209)), 'Test classes packaged')
    badging = Path('signed208/badging.txt').read_text()
    require("package: name='com.projectinfinity.kodi' versionCode='2103208'" in badging, 'Wrong package/version')
    require("application-label:'Infinity'" in badging and 'application-debuggable' not in badging, 'Launcher identity/debuggable drift')
    require(len(re.findall(r'^launchable-activity:', badging, re.M)) == 1, 'Launcher count drift')
    Path('audit208/final-verification.json').write_text(json.dumps(dict(
        apk_sha256=sha(apk), parent_apk_sha256=PARENT_APK, signer=CERT,
        parent_commit=PARENT_COMMIT, physical_device_verified=False,
        resource_id_map_verified=audit['resource_id_map_verified'], **preserved), indent=2) + '\n')

def tests():
    reviewed = review()
    build = Path('refinement208-build')
    app = build / 'xbmc'
    prior = Path('refinement207-build/xbmc')
    output = Path('audit208/android')
    shutil.copytree(prior / 'src/test', app / 'src/test', dirs_exist_ok=True)
    gradle = (prior / 'build.gradle').read_text()
    require('versionCode 2103207' in gradle, 'Wrong baseline test project')
    (app / 'build.gradle').write_text(gradle.replace('versionCode 2103207', 'versionCode 2103208').replace(OLD, NEW))
    folder = app / 'src/test/java/com/projectinfinity/kodi'
    module('adapt208', ROOT / 'adapt_tests.py').adapt(folder, Path('audit208/test-expectation-supersessions.json'))
    for test in (ROOT / 'tests').glob('*.java'):
        shutil.copy2(test, folder / test.name)
    resources = app / 'src/test/resources'
    resources.mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path('kodi/tools/android/packaging/xbmc/res/drawable-nodpi/infinity_splash_icon.png'), resources / 'cobra-approved-mark.png')
    expected = json.loads(Path('audit207/expected-cases.json').read_text())
    require(sum(map(len, expected.values())) == 691 and len(expected) == 69, 'Inherited test inventory drift')
    additions = json.loads((ROOT / 'new-cases.json').read_text())
    require(not set(expected) & set(additions), 'New test suite shadows existing suite')
    expected.update(additions)
    Path('audit208/expected-cases.json').write_text(json.dumps(expected, indent=2) + '\n')
    runner = module('runner208', Path('experience-delta/repairs/infinity-experience-2103159/tests/android.py'))
    environment = runner.test_environment(output, Path('experience-delta/repairs/infinity-experience-2103159/experience-theme.json'))
    command = ['./gradlew', '--no-daemon', '--console=plain', ':xbmc:testReleaseUnitTest', '--rerun-tasks']
    for cases in expected.values():
        for owner, name in cases:
            command += ['--tests', owner + '.' + name]
    command += ['--stacktrace']
    try:
        runner.run_process(command, build, environment, output, timeout=900)
    finally:
        runner.copy_results(app, output)
    actual = {}
    for path in (output / 'test-results').glob('TEST-*.xml'):
        result = ET.parse(path).getroot()
        cases = result.findall('testcase')
        require(all(int(result.get(key, '0')) == 0 for key in ('failures', 'errors', 'skipped')), 'Nonpassing suite: ' + str(path))
        require(all(case.find(key) is None for case in cases for key in ('failure', 'error', 'skipped')), 'Nonpassing case')
        actual[result.get('name')] = sorted([[case.get('classname'), case.get('name')] for case in cases])
    require(actual == expected, 'Exact inherited/new test inventory mismatch')
    verify()
    acceptance = dict(build=VERSION, parent_commit=PARENT_COMMIT, parent_tests_passed=691,
        parent_suites_passed=69, candidate_tests=sum(map(len, actual.values())), candidate_suites=len(actual),
        android_test_suites=[dict(suite=name, cases=cases) for name, cases in sorted(actual.items())],
        test_expectations_superseded='See explicit 208 generated-fixture supersessions; originals ran first on exact 207',
        physical_device_verified=False, installed_update_tested=False, live_dual_decoder_verified=False,
        audible_phone_call_playback_verified=False, complete_product_acceptance=False,
        candidate_locked=False, status='TEST CANDIDATE: physical phone/provider acceptance required')
    Path('signed208/ACCEPTANCE.json').write_text(json.dumps(acceptance, indent=2) + '\n')
    for name in ('AUDIT.md', 'DEVICE-TEST.md', 'approved-resources.json'):
        shutil.copy2(ROOT / name, Path('signed208') / name)
    for name in ('source-preservation.json', 'final-verification.json', 'test-expectation-supersessions.json', 'expected-cases.json'):
        shutil.copy2(Path('audit208') / name, Path('signed208') / name)
    with zipfile.ZipFile('signed208/Cobra-2103208-Generated-Android-Source.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in reviewed['parent_inventory']:
            archive.write(Path('kodi') / name, name)
    print('PASS: all inherited/new cases; reviewed branding delta; device acceptance NOT claimed')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('upgrade', 'verify', 'tests'))
    globals()[parser.parse_args().phase]()
