"""Focused new80-input cases against the unchanged original Java installer.

Adapts the retained verify_module_pair.py fixture pattern, source generator,
hash helper and Android API transports. Never signs or builds an APK. Requires
both full manifests to have existing original-key signatures before javac runs.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIRST = ROOT / 'repairs/infinity-final-closure-2103407'
OLD = ROOT / 'repairs/infinity-three-corrections-20261108'
sys.path[:0] = [str(HERE), str(FIRST), str(OLD)]
import prepare_release as prep

OLD_HELPER_SHA = '0b06aa0001b7c96679e6548c4f005559e9152a0c58734820d0385282159912f5'
BASE_MANIFEST_SHA = '91a4154b44d537afd840cd7a8f4c6703e1f8f894aa61d5373daf652e8db60db0'
CC = prep.CC
MANIFEST = prep.module_bundle.MANIFEST
HELPER = CC + '/' + prep.HELPER


def check(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return prep.file_sha(path)


def retained():
    path = OLD / 'verify_module_pair.py'
    check(sha(path) == OLD_HELPER_SHA, 'Retained original verifier helper changed')
    spec = importlib.util.spec_from_file_location('retained_original_module_pair', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit(prepared, out):
    check(not out.exists(), 'Fresh module audit output required')
    original = retained()
    hashes = original.hashes
    prep.tool_pins()
    reference_path = ROOT / 'repairs/infinity-2103460-nine-corrections-20261106/fold-regressions/CC-AUDIT-REFERENCE.json'
    reference = prep.load(reference_path)
    check(reference_path.read_bytes() == prep.git('show', prep.BASE + ':' + reference_path.relative_to(ROOT).as_posix()), 'Original Java reference changed')
    prior_evidence = OLD / 'evidence/MODULE-UPGRADE-RECOVERY.json'
    check(prior_evidence.read_bytes() == prep.git('show', prep.BASE + ':' + prior_evidence.relative_to(ROOT).as_posix()), 'Retained installer evidence changed')
    source = original.module_dex.source()
    check(hashlib.sha256(source.encode()).hexdigest() == reference['java_source_sha256'], 'Original generated installer changed')
    host = {p.relative_to(FIRST).as_posix(): sha(p) for p in (FIRST / 'host-java').rglob('*.java')}
    check(host == reference['host_java_sha256'], 'Original host transport changed')
    pins = prep.load(prepared / 'SOURCE-PINS.json')
    versions = prep.admission(prepared / 'VERSION-ADMISSION.json')
    check(sha(prepared / 'VERSION-ADMISSION.json') == pins['version_admission_sha256'], 'Version admission changed')
    baseline = prepared / 'baseline-modules'
    base_payload, base_files = original.module_bundle.build(baseline)
    check(len(base_files) == 79 and hashlib.sha256(base_payload).hexdigest() == BASE_MANIFEST_SHA and
          base_payload == (baseline / CC / MANIFEST).read_bytes(), 'Exact complete79 signed466 baseline required')
    prep.verify_signature(baseline)
    signed_inputs = {}
    for version, cc_version in versions:
        work = prepared / str(version)
        check(sha(work / 'INPUTS.json') == pins['input_metadata_sha256'][str(version)], 'Frozen input metadata changed')
        pin = prep.load(work / 'INPUTS.json')
        modules = work / 'modules'
        payload, files = original.module_bundle.build(modules)
        check(len(files) == 80 and pin['authenticated_source_count'] == 80 and HELPER in files,
              'Exactly complete80 authenticated sources including the helper required')
        check(hashlib.sha256(payload).hexdigest() == pin['module_manifest_sha256'] and
              payload == (modules / CC / MANIFEST).read_bytes(), 'Frozen full manifest changed')
        now = hashes(modules)
        check({n: h for n, h in now.items() if n != CC + '/' + MANIFEST + '.sig'} == pin['modules'], 'Frozen signed sources changed')
        prep.verify_signature(modules)
        signed_inputs[str(version)] = dict(CC=cc_version, module_manifest_sha256=sha(modules / CC / MANIFEST),
                                           signature_sha256=sha(modules / CC / (MANIFEST + '.sig')), source_sha256=hashes(modules))
    candidate, recovery = [prepared / str(v) / 'modules' for v, _ in versions]
    check((candidate / HELPER).read_bytes() == (recovery / HELPER).read_bytes(), 'Recovery must authenticate the same inactive helper')
    recovery_files = original.module_bundle.source_files(recovery)
    expected = dict(base_files)
    expected[HELPER] = (candidate / HELPER).read_bytes()
    expected[CC + '/addon.xml'] = base_files[CC + '/addon.xml'].replace(b'version="0.3.5.64"', b'version="0.3.5.67"', 1)
    check(recovery_files == expected, 'Recovery must restore every baseline66 functional module byte plus inactive helper and forward CC metadata')
    out.mkdir(parents=True)
    rows = []
    with tempfile.TemporaryDirectory(dir=out) as temporary:
        temp = Path(temporary)
        assets = {}
        for apk_version, cc_version in versions:
            path = temp / str(apk_version) / 'assets/addons'
            shutil.copytree(prepared / str(apk_version) / 'modules', path)
            assets[cc_version] = path.parent
        candidate_version, recovery_version = [v for _, v in versions]
        java = temp / 'InfinityInstalledCheckpointInstaller.java'
        java.write_text(source)
        classes = temp / 'classes'
        classes.mkdir()
        subprocess.run(['javac', '--release', '8', '-g:none', '-d', str(classes), str(java),
                        *map(str, sorted((FIRST / 'host-java').rglob('*.java')))], check=True)
        retained_data = {'.kodi/userdata/addon_data/plugin.video.sentinel/settings.xml': b'<settings>retain user data</settings>',
                         '.kodi/userdata/addon_data/' + CC + '/continue-watching.json': b'{"schema":2,"retain":"progress"}',
                         '.kodi/addons/plugin.video.sentinel/source.py': b'# unrelated provider\n',
                         '.kodi/addons/' + CC + '/user-retained-file.txt': b'unknown unlisted retained file'}

        def fixture(name):
            storage = temp / name
            shutil.copytree(baseline, storage / '.kodi/addons')
            for name, raw in retained_data.items():
                target = storage / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
            return storage

        def call(storage, version, other_assets=None):
            return subprocess.run(['java', '-cp', str(classes), 'com.projectinfinity.kodi.Main', str(storage),
                                   str(other_assets or assets[version])], capture_output=True, text=True)

        def passed(name, storage, version):
            result = call(storage, version)
            check(result.returncode == 0 and 'VERIFIED_VERSION=' + version in result.stdout, name + ': ' + result.stderr)
            for relative in hashes(assets[version] / 'addons'):
                check((storage / '.kodi/addons' / relative).read_bytes() == (assets[version] / 'addons' / relative).read_bytes(), name + ': incomplete installed source')
            for relative, raw in retained_data.items():
                check((storage / relative).read_bytes() == raw, name + ': retained data changed')
            rows.append(dict(case=name, status='PASS_REAL_UNCHANGED_JAVA', CC=version))

        def refused(name, storage, version, other_assets=None):
            before = hashes(storage)
            result = call(storage, version, other_assets)
            check(result.returncode != 0 and hashes(storage) == before, name + ': refusal must preserve every byte')
            rows.append(dict(case=name, status='REFUSED_AS_REQUIRED_ALL_BYTES_RETAINED'))

        storage = fixture('signed64_to80source66')
        passed('signed64_to_complete80source66_exact_bytes_and_data', storage, candidate_version)
        before = hashes(storage)
        passed('same66_idempotent_noop', storage, candidate_version)
        check(hashes(storage) == before, 'Same66 invocation wrote files')
        passed('forward67_restores_full466_functional_code_inactive_helper_and_data', storage, recovery_version)
        before = hashes(storage)
        result = call(storage, candidate_version)
        check(result.returncode == 0 and 'VERIFIED_VERSION=' + recovery_version in result.stdout and hashes(storage) == before, 'Older66 overwrote authenticated67')
        rows.append(dict(case='older66_retains_authenticated67', status='PASS_NO_WRITE'))
        # The caller is older than an incomplete authenticated newer generation.
        (storage / '.kodi/addons' / HELPER).unlink()
        refused('older66_refuses_newer67_missing_authenticated_helper', storage, candidate_version)

        for name, change in (
                ('unknown_loose_helper', lambda root: (root / HELPER).write_bytes(b'unknown helper')),
                ('missing_installed_signature', lambda root: (root / CC / (MANIFEST + '.sig')).unlink()),
                ('unmatched_partial_signature', lambda root: shutil.copyfile(candidate / CC / (MANIFEST + '.sig'), root / CC / (MANIFEST + '.sig')))):
            storage = fixture(name)
            change(storage / '.kodi/addons')
            refused(name, storage, candidate_version)
        storage = fixture('known_partial66')
        for name in (CC + '/resume_hub.py', HELPER):
            shutil.copyfile(candidate / name, storage / '.kodi/addons' / name)
        passed('known_signed66_partial_sources_resume_from64', storage, candidate_version)
        (storage / '.kodi/addons' / HELPER).write_bytes(b'tampered authenticated helper')
        refused('tampered_installed66_helper_refuses_recovery67', storage, recovery_version)
        for name, change in (
                ('tampered_APK_helper', lambda root: (root / HELPER).write_bytes(b'tampered APK helper')),
                ('missing_APK_helper', lambda root: (root / HELPER).unlink()),
                ('tampered_APK_signature', lambda root: (root / CC / (MANIFEST + '.sig')).write_bytes(b'\0' * 256))):
            damaged = temp / name / 'assets'
            shutil.copytree(assets[candidate_version], damaged)
            change(damaged / 'addons')
            storage = fixture(name + '_storage')
            refused(name, storage, candidate_version, damaged)
    check(len(rows) == 13, 'Exactly thirteen selected new80-input cases required')
    report = dict(status='PASS_THIRTEEN_REAL_JAVA80_FILE_UPGRADE_AND_FORWARD_RECOVERY_CASES', cases=rows,
        original_pair_helper_sha256=OLD_HELPER_SHA, java_source_sha256=reference['java_source_sha256'], host_transport_sha256=host,
        source_pins_sha256=sha(prepared / 'SOURCE-PINS.json'), signed_inputs=signed_inputs,
        selected_tests_sha256=sha(HERE / 'MODULE-TEST-SELECTION.md'), original_installer_changed=False,
        user_data_and_unknown_files_preserved=True, recovery_full466_functional_module_bytes=True,
        recovery_helper_authenticated_inactive=True, original_signatures_verified=True,
        reused_prior_installer_evidence_sha256=sha(prior_evidence),
        native_or_APK_build=False, signing=False, Android='NOT_RUN_BY_HOST_TEST', Fold='NOT_RUN', shutdown='NOT_SELECTED')
    prep.save(out / 'MODULE-UPGRADE-RECOVERY.json', report)
    print(report['status'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    audit(args.prepared, args.out)
