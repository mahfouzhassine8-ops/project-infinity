"""Reconstruct frozen features from exact locked source and reject repeat application."""
from pathlib import Path
import argparse
import datetime
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from apply import ROOT, checked_review, require, sha, source_inventory

GRADLE = 'tools/android/packaging/xbmc/build.gradle.in'
PARENT_ZIP_SHA256 = '87fa108ae298fc93088d8cbcfed948f7777dd1e8351abb5ef053c7c0fe4f879f'


def rehearse(parent_zip, parent_receipt, candidate, out):
    review = checked_review()
    require(sha(parent_zip) == PARENT_ZIP_SHA256, 'Wrong exact locked source archive')
    require(not out.exists(), 'Rehearsal output already exists; retain previous evidence')
    out.mkdir(parents=True)
    source = out / 'source'
    source.mkdir()
    with zipfile.ZipFile(parent_zip) as archive:
        names = archive.namelist()
        require(archive.testzip() is None and len(names) == len(set(names)) == 220,
                'Invalid locked source archive')
        for name in names:
            require(not name.startswith('/') and '..' not in Path(name).parts and not name.endswith('/'),
                    'Unsafe/non-file source archive member')
            require((archive.getinfo(name).external_attr >> 16) & 0o170000 != 0o120000,
                    'Symlinked source archive member')
        archive.extractall(source)
    receipt = out / 'parent-source-receipt.json'
    shutil.copy2(parent_receipt, receipt)
    command = ['python3', str(ROOT / 'apply.py'), '--source', str(source), '--receipt', str(receipt),
               '--out', str(out / 'patch')]
    applied = subprocess.run(command, capture_output=True, text=True, timeout=60)
    (out / 'apply.log').write_text(applied.stdout + applied.stderr)
    require(applied.returncode == 0, 'Frozen apply failed: ' + applied.stdout + applied.stderr)
    patch = json.loads((out / 'patch/patch.json').read_text())
    require(patch['files'] == review['files'] and
            patch['protected_runtime_members'] == review['protected_runtime_members'],
            'Rehearsal does not match frozen review')
    gradle = source / GRADLE
    code = gradle.read_text()
    for old, new in [('versionCode 2103204', 'versionCode 2103205'),
                     ('versionName "1.0.9-Cobra-OLED-Blue-RC1"',
                      'versionName "1.0.9-Cobra-Final-Features-RC1"')]:
        require(code.count(old) == 1, 'Release identity drift')
        code = code.replace(old, new, 1)
    gradle.write_text(code)
    final = source_inventory(source)
    require(final == source_inventory(candidate), 'Final source is not byte-identical to reviewed candidate')
    repeated = command[:-1] + [str(out / 'repeated-patch')]
    repeat = subprocess.run(repeated, capture_output=True, text=True, timeout=60)
    (out / 'repeat-rejected.log').write_text(repeat.stdout + repeat.stderr)
    require(repeat.returncode != 0 and ('Complete parent source input drift' in repeat.stderr or
                                      'Complete parent source inventory drift' in repeat.stderr),
            'Repeated patch unexpectedly accepted or rejected for wrong reason')
    require(not (out / 'repeated-patch').exists() and source_inventory(source) == final,
            'Rejected repeat mutated source or created outputs')
    guard = subprocess.run(['python3', str(ROOT / 'test_recipe_guards.py')], capture_output=True, text=True, timeout=60)
    (out / 'recipe-guards.log').write_text(guard.stdout + guard.stderr)
    require(guard.returncode == 0 and re.search(r'Ran 28 tests\b', guard.stderr) and '\nOK\n' in guard.stderr,
            'Recipe guard suite failed or incomplete')
    workflow = subprocess.run(['python3', str(ROOT / 'validate_recipe.py'), '--require-frozen'],
                              capture_output=True, text=True, timeout=60)
    (out / 'workflow-validation.log').write_text(workflow.stdout + workflow.stderr)
    require(workflow.returncode == 0, 'Frozen workflow validation failed')
    result = {
        'passed': True, 'verification_kind': 'host frozen-source reconstruction and guard tests only',
        'verified_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'parent_build': 2103204, 'parent_commit': review['parent_commit'],
        'parent_source_archive_sha256': sha(parent_zip), 'parent_source_receipt_sha256': sha(parent_receipt),
        'reviewed_sha256': sha(ROOT / 'reviewed.json'), 'features_patch_sha256': sha(ROOT / 'features.patch'),
        'runtime_files': patch['files'], 'protected_runtime_members_count': len(patch['protected_runtime_members']),
        'source_inputs_byte_identical_to_candidate': len(final), 'source_hashes': final,
        'gradle_changed_only_version_code_and_name': True, 'repeated_apply_rejected_without_mutation': True,
        'host_recipe_guard_tests': 28, 'frozen_workflow_validated': True,
        'declared_android_cases': 500 + review['new_android_cases'],
        'android_tests_executed_by_this_rehearsal': False, 'physical_device_verified': False,
        'native_engine_recompiled': False,
    }
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({name: result[name] for name in ['passed', 'source_inputs_byte_identical_to_candidate',
                                                    'protected_runtime_members_count', 'declared_android_cases',
                                                    'repeated_apply_rejected_without_mutation', 'physical_device_verified']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent-zip', type=Path, required=True)
    parser.add_argument('--parent-receipt', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    rehearse(*[p.resolve() for p in [args.parent_zip, args.parent_receipt, args.candidate, args.out]])
