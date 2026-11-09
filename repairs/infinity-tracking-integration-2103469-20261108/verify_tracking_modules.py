"""Selected signed69-to-tracking module installer host checks.

Requires the complete originally signed module pair before javac or any fixture
execution. Uses the unchanged original Java installer and host API adapters;
never builds/signs an APK or accesses a device, owner profile, or private key.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIRST = ROOT / 'repairs/infinity-final-closure-2103407'
SOURCE = 'a76e29b84996304241e6b309d56a31e6659ad190'
CC = 'script.infinity.commandcenter'
MANIFEST = 'INFINITY-MODULES.v1'
HELPER = CC + '/saved_playback.py'
PYTHON = {CC + '/' + name for name in ('plugin.py', 'resume_hub.py', 'service.py')}
BASE_MANIFEST_SHA = '6fb82d58f2488a2eac23d2f0aa0e8a4eaa600f5fcf35901a24445b32beb852d2'
BASE_APK_SHA = '804eebc57af2e4ef4e5418b56994bda64eb7fd7e7f2c0653b5c6e2a9f7833058'
PRIOR = ROOT / 'repairs/infinity-watchlist-playback-2103466-20261108'
PRIOR_VERIFIER_SHA = 'dfc1f71802b0d0b18cf49a559ed4fe8965e8cbf7bed49ebfa1bd6ee860cd9b43'
PRODUCTION_SOURCE = 'e410f30ba9e38182e4e77810e5237e5442cbd31a'
SELECTION = ('signed69_to_tracking_complete80_and_data', 'same_candidate_idempotent_noop',
             'forward_recovery_restores_exact69_functional80_and_data',
             'older_candidate_retains_authenticated_recovery')


def check(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def hashes(root):
    return {path.relative_to(root).as_posix(): sha(path)
            for path in sorted(root.rglob('*')) if path.is_file()}


def original_tools():
    """Establish immutable source ownership BEFORE importing any producer."""
    reference = ROOT / 'repairs/infinity-2103460-nine-corrections-20261106/fold-regressions/CC-AUDIT-REFERENCE.json'
    paths = [FIRST / name for name in ('module_dex.py', 'module_bundle.py',
             'InfinityInstalledModules.java.in', 'ORIGINAL-INFINITY-PUBLIC-KEY.pem',
             'FIRSTPARTY-COMPOSITION-PLAN.json')]
    paths += [reference, PRIOR / 'verify_modules.py', PRIOR / 'evidence/MODULE-UPGRADE-RECOVERY.json']
    paths += sorted((FIRST / 'host-java').rglob('*.java'))
    for path in paths:
        relative = path.relative_to(ROOT).as_posix()
        check(path.is_file() and not path.is_symlink(), 'Regular original tool required: ' + relative)
        original = subprocess.run(['git', '-C', str(ROOT), 'show', SOURCE + ':' + relative],
                                  check=True, capture_output=True, timeout=15).stdout
        check(path.read_bytes() == original, 'Original tool differs before import: ' + relative)
    check(sha(PRIOR / 'verify_modules.py') == PRIOR_VERIFIER_SHA, 'Retained verifier preimage differs')
    reviewed = load(reference)
    host = {path.relative_to(FIRST).as_posix(): sha(path)
            for path in (FIRST / 'host-java').rglob('*.java')}
    check(host == reviewed['host_java_sha256'], 'Original host Java inventory differs before import')
    modules = {}
    for name in ('module_bundle', 'module_dex'):
        spec = importlib.util.spec_from_file_location('tracking_original_' + name, FIRST / (name + '.py'))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        modules[name] = module
    source = modules['module_dex'].source()
    check(hashlib.sha256(source.encode()).hexdigest() == reviewed['java_source_sha256'],
          'Original generated Java installer differs')
    return modules['module_bundle'], source, reviewed, host, {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}


def verify_signature(modules):
    subprocess.run(['openssl', 'dgst', '-sha256', '-verify', str(FIRST / 'ORIGINAL-INFINITY-PUBLIC-KEY.pem'),
                    '-signature', str(modules / CC / (MANIFEST + '.sig')),
                    str(modules / CC / MANIFEST)], check=True, capture_output=True, timeout=15)


def admitted_versions(path):
    admission = load(path)
    check(admission['status'] == 'CONFIRMED_UNUSED_FORWARD_PAIR' and
          admission['authority_source'] == SOURCE and admission['generation'] == 56 and
          admission['latest_signed_versionCode'] == 2103469 and admission['reserved'] is False,
          'Root-confirmed unchanged69 forward-pair admission required')
    candidate, recovery = admission['candidate_versionCode'], admission['recovery_versionCode']
    check(type(candidate) is int and type(recovery) is int and
          (candidate, recovery) == (2103472, 2103473), 'Fresh internal labels required; no APK issuance')
    versions = [admission['candidate_CC'], admission['recovery_CC']]
    check(all(isinstance(v, str) and re.fullmatch(r'0\.3\.5\.[0-9]+', v) for v in versions) and
          versions == ['0.3.5.70', '0.3.5.71'] and admission['APK_build'] is False and
          admission['version_issued'] is False and admission['publication'] is False,
          'Admitted increasing CC pair required')
    return [(candidate, versions[0]), (recovery, versions[1])]


def audit(prepared, out):
    prepared, out = prepared.resolve(), out.absolute()
    check(not out.exists(), 'Fresh selected host output required')
    bundle, source, reference, host, tools = original_tools()
    pins = load(prepared / 'SOURCE-PINS.json')
    versions = admitted_versions(prepared / 'VERSION-ADMISSION.json')
    check(sha(prepared / 'VERSION-ADMISSION.json') == pins['version_admission_sha256'] and
          pins['baseline_APK_sha256'] == BASE_APK_SHA, 'Frozen exact69 input admission differs')
    selection = load(HERE / 'CURRENT-INPUT-FIXTURE.json')
    check(tuple(selection['selected_installer_cases']) == SELECTION and selection['production_source'] == PRODUCTION_SOURCE and
          pins['production_source'] == PRODUCTION_SOURCE and
          pins['installer_selection_sha256'] == sha(HERE / 'CURRENT-INPUT-FIXTURE.json'), 'Frozen four-case selection differs')
    baseline = prepared / 'baseline-modules'
    payload, base_files = bundle.build(baseline)
    check(len(base_files) == 80 and hashlib.sha256(payload).hexdigest() == BASE_MANIFEST_SHA and
          payload == (baseline / CC / MANIFEST).read_bytes(), 'Exact signed69 complete80 baseline required')
    verify_signature(baseline)
    signed_inputs = {}
    for index, (version, cc_version) in enumerate(versions):
        work = prepared / str(version)
        check(sha(work / 'INPUTS.json') == pins['input_metadata_sha256'][str(version)], 'Frozen pair metadata differs')
        pin = load(work / 'INPUTS.json')
        modules = work / 'modules'
        payload, files = bundle.build(modules)
        check(len(files) == pin['authenticated_source_count'] == 80 and HELPER in files and
              pin['versionCode'] == version and pin['CC'] == cc_version and
              pin['recovery'] is (index == 1), 'Exact admitted complete80 input required')
        check(hashlib.sha256(payload).hexdigest() == pin['module_manifest_sha256'] and
              payload == (modules / CC / MANIFEST).read_bytes(), 'Frozen full signed manifest differs')
        current = hashes(modules)
        check({name: digest for name, digest in current.items() if name != CC + '/' + MANIFEST + '.sig'} == pin['modules'],
              'Frozen authenticated sources differ')
        verify_signature(modules)
        expected = dict(base_files)
        if index == 0:
            for name in PYTHON:
                expected[name] = (HERE / 'overlay' / name).read_bytes()
            check({name for name in base_files if files[name] != base_files[name]} == PYTHON | {CC + '/addon.xml'},
                  'Only the three selected Python files and CC version may change')
        addon = base_files[CC + '/addon.xml']
        check(addon.count(b'version="0.3.5.67"') == 1, 'Exact69 CC metadata preimage required')
        expected[CC + '/addon.xml'] = addon.replace(b'version="0.3.5.67"', ('version="' + cc_version + '"').encode(), 1)
        check(files == expected, 'Candidate/recovery source preservation differs')
        check(files[HELPER] == base_files[HELPER], 'Inactive authenticated helper must remain unchanged')
        check(ET.fromstring(files[CC + '/addon.xml']).get('version') == cc_version, 'Full manifest CC version differs')
        signed_inputs[str(version)] = dict(CC=cc_version, module_manifest_sha256=sha(modules / CC / MANIFEST),
            signature_sha256=sha(modules / CC / (MANIFEST + '.sig')), source_sha256=current)
    # No javac, Java fixture, or output mutation occurs before all three full
    # manifests and original-key signatures above have been checked.
    out.mkdir(parents=True)
    rows = []
    with tempfile.TemporaryDirectory(dir=out) as temporary:
        temp = Path(temporary)
        assets = {}
        for version, cc_version in versions:
            target = temp / str(version) / 'assets/addons'
            shutil.copytree(prepared / str(version) / 'modules', target)
            assets[cc_version] = target.parent
        candidate_version, recovery_version = [version for _, version in versions]
        java = temp / 'InfinityInstalledCheckpointInstaller.java'
        java.write_text(source)
        classes = temp / 'classes'
        classes.mkdir()
        subprocess.run(['javac', '--release', '8', '-g:none', '-d', str(classes), str(java),
                        *map(str, sorted((FIRST / 'host-java').rglob('*.java')))], check=True, timeout=90)
        retained_data = {
            '.kodi/userdata/addon_data/plugin.video.sentinel/settings.xml': b'<settings>retain provider settings</settings>',
            '.kodi/userdata/addon_data/' + CC + '/continue-watching.json': b'{"schema":2,"revision":17,"retain":{"progress":1,"custom_list":2}}',
            '.kodi/userdata/guisettings.xml': b'<settings>retain experience settings</settings>',
            '.kodi/userdata/Database/retained-fixture.db': b'disposable database byte sentinel',
            '.kodi/addons/plugin.video.sentinel/source.py': b'# unrelated provider source\n',
            '.kodi/addons/' + CC + '/user-retained-file.txt': b'unknown unlisted retained file'}

        def fixture(name):
            storage = temp / name
            shutil.copytree(baseline, storage / '.kodi/addons')
            for relative, raw in retained_data.items():
                path = storage / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
            return storage

        def call(storage, version, other_assets=None):
            return subprocess.run(['java', '-cp', str(classes), 'com.projectinfinity.kodi.Main',
                str(storage), str(other_assets or assets[version])], capture_output=True, text=True, timeout=30)

        def passed(name, storage, version):
            result = call(storage, version)
            check(result.returncode == 0 and 'VERIFIED_VERSION=' + version in result.stdout, name + ': ' + result.stderr)
            for relative in hashes(assets[version] / 'addons'):
                check((storage / '.kodi/addons' / relative).read_bytes() == (assets[version] / 'addons' / relative).read_bytes(),
                      name + ': incomplete authenticated source installation')
            for relative, raw in retained_data.items():
                check((storage / relative).read_bytes() == raw, name + ': retained data changed')
            rows.append(dict(case=name, status='PASS_REAL_UNCHANGED_JAVA', CC=version))

        storage = fixture('signed69_upgrade')
        passed('signed69_to_tracking_complete80_and_data', storage, candidate_version)
        before = hashes(storage)
        passed('same_candidate_idempotent_noop', storage, candidate_version)
        check(hashes(storage) == before, 'Same-version install wrote bytes')
        passed('forward_recovery_restores_exact69_functional80_and_data', storage, recovery_version)
        before = hashes(storage)
        result = call(storage, candidate_version)
        check(result.returncode == 0 and 'VERIFIED_VERSION=' + recovery_version in result.stdout and hashes(storage) == before,
              'Older candidate overwrote authenticated forward recovery')
        rows.append(dict(case='older_candidate_retains_authenticated_recovery', status='PASS_NO_WRITE'))
    check(tuple(row['case'] for row in rows) == SELECTION, 'Exactly four selected generation cases required')
    report = dict(status='PASS_FOUR_REAL_JAVA_CURRENT80_GENERATION_CASES', cases=rows,
        source_pins_sha256=sha(prepared / 'SOURCE-PINS.json'), signed_inputs=signed_inputs,
        original_java_source_sha256=reference['java_source_sha256'], original_host_transport_sha256=host,
        original_tools_sha256=tools, selected_tests_sha256=sha(HERE / 'CURRENT-INPUT-FIXTURE.json'),
        verifier_sha256=sha(Path(__file__)), original_installer_changed=False,
        retained_thirteen_case_evidence_sha256=sha(PRIOR / 'evidence/MODULE-UPGRADE-RECOVERY.json'),
        retained_tracking13_evidence_sha256=sha(HERE / 'evidence/signed-tracking80-42555855742/MODULE-UPGRADE-RECOVERY.json'),
        prior_thirteen_cases_rerun=False, complete80_signatures_verified=True,
        inactive_helper_unchanged=True, recovery_exact69_functional_bytes=True,
        user_data_and_unknown_files_preserved=True, native_or_APK_build=False,
        signing=False, Android='NOT_RUN_BY_HOST_TEST', Fold='NOT_RUN', shutdown='NOT_SELECTED')
    (out / 'MODULE-UPGRADE-RECOVERY.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(report['status'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    audit(args.prepared, args.out)
