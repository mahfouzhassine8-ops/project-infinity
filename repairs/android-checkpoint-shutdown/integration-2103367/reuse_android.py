#!/usr/bin/env python3
"""Reuse the successful immutable shell checkpoint only with identical inputs."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[1]
SOURCE = 'b00a1850233362c506f239ba0c08bd9c085b3f3d'
RUN = 38133236811
ALLOWED = {
    '.github/workflows/infinity-2103367-recovery-integration.yml',
    'repairs/android-checkpoint-shutdown/integration-2103367/reuse_android.py',
    'repairs/android-checkpoint-shutdown/integration-2103367/CHECKPOINT.json',
    'repairs/android-checkpoint-shutdown/runtime-tests/test_runtime_rpc_admission.py',
    'repairs/android-checkpoint-shutdown/runtime-tests/run_resume_preservation.py',
    'repairs/android-checkpoint-shutdown/system-stability-2103366/test_resume.py',
}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--validation', type=Path, required=True)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--donor', type=Path, required=True)
    a = p.parse_args()
    changed = set(subprocess.check_output(
        ['git', 'diff', '--name-only', SOURCE], cwd=REPO, text=True).splitlines())
    if changed - ALLOWED:
        raise ValueError('Completed Android input changed: ' + repr(sorted(changed - ALLOWED)))
    evidence = a.validation / 'checkpoint-android'
    scope = json.loads((evidence / 'COMPILATION-SCOPE.json').read_text())
    if scope['source_commit'] != SOURCE:
        raise ValueError('Wrong completed Android source checkpoint')
    sys.path.insert(0, str(HERE))
    import runtime_delta
    import participant_asset
    runtime_delta.verify(a.source, json.loads((HERE / 'runtime/android/manifest.json').read_text())['after'])
    digest = lambda data: hashlib.sha256(data).hexdigest()
    if scope['participant_asset_sha256'] != digest(participant_asset.build()):
        raise ValueError('Bundled participant changed since Android compilation')
    spec = importlib.util.spec_from_file_location('installed_build', HERE / 'installed/build.py')
    installed = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(installed)
    for addon, name in [('script.infinity.commandcenter', 'checkpoint-controller-20.zip'),
                        ('service.infinity.compat', 'checkpoint-compat-82.zip')]:
        if scope['installed_participant_assets']['assets/infinity/' + name] != digest(installed.build(addon)):
            raise ValueError('Installed participant changed since Android compilation: ' + addon)
    parent = json.loads((HERE / 'PARENT.json').read_text())
    if scope['parent_apk_sha256'] != parent['parent_apk_sha256']:
        raise ValueError('Android preservation parent changed')
    suites = {}
    for path in a.validation.glob('checkpoint-shell-build/xbmc/build/test-results/testReleaseUnitTest/TEST-*.xml'):
        suite = ET.parse(path).getroot()
        if int(suite.get('failures', '0')) or int(suite.get('errors', '0')) or int(suite.get('skipped', '0')):
            raise ValueError('Completed Android regression did not pass: ' + path.name)
        suites[suite.get('name')] = int(suite.get('tests'))
    expected = {'com.projectinfinity.kodi.CheckpointCrashExportTest': 3,
                'com.projectinfinity.kodi.CheckpointLifecycleTest': 6,
                'com.projectinfinity.kodi.InstalledCodeEvidenceTest': 3,
                'com.projectinfinity.kodi.NativeTraceBridge335Test': 2}
    if suites != expected:
        raise ValueError('Incomplete completed Android regression evidence')
    proof = {'schema': 1, 'source_commit': SOURCE, 'validation_run': RUN,
             'complete_android_inputs_identical': True, 'regression_tests_passed': sum(suites.values()),
             'donor_sha256': digest(a.donor.read_bytes()), 'recompiled': False}
    (evidence / 'REUSED-ANDROID.json').write_text(json.dumps(proof, indent=2) + '\n')
    print(json.dumps(proof))


if __name__ == '__main__':
    main()
