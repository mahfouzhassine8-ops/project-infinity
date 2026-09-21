"""Explicitly freeze reviewed source and test identities; never dispatch a build."""
from pathlib import Path
import argparse
import difflib
import hashlib
import json
import re
import sys
from apply import (ACTIVITY, INSTALL, PARENT_COMMIT, ROOT, permitted_file,
                   protected_members, require, sha, source_inventory, validate_install)

GRADLE = 'tools/android/packaging/xbmc/build.gradle.in'


def collect_tests():
    tests, hashes = {}, {}
    paths = sorted((ROOT / 'tests').glob('Cobra2103205*.java'))
    require(bool(paths), 'No new Android regressions')
    for path in paths:
        text = path.read_text()
        require('@Ignore' not in text and 'Assume.' not in text and 'Assumptions.' not in text,
                'Ignored or conditionally skipped feature test: ' + path.name)
        require('@Parameterized' not in text and 'Parameterized.class' not in text,
                'Parameterized inventories require explicit audited test identity support')
        methods = re.findall(r'@Test(?:\([^\n]*?\))?\s*'
                             r'(?:@[A-Za-z][A-Za-z0-9_.]*(?:\([^\n]*?\))?\s*)*'
                             r'public\s+void\s+(\w+)\s*\(', text)
        require(methods and len(methods) == len(set(methods)), 'Invalid test inventory: ' + path.name)
        require(len(re.findall(r'@Test\b', text)) == len(methods), 'Unparsed @Test declaration: ' + path.name)
        name = 'com.projectinfinity.kodi.' + path.stem
        require(re.search(r'package\s+com\.projectinfinity\.kodi\s*;', text), 'Wrong test package')
        tests[name] = sorted([[name, method] for method in methods])
        hashes[str(path.relative_to(ROOT))] = sha(path)
    return tests, hashes


def freeze(parent, candidate, rollback_receipt):
    rollback = json.loads(rollback_receipt.read_text())
    require(bool(rollback['results']) and all(row['status'] == 'succeeded' and row['local_metadata_applied']
                for row in rollback['results']), 'Complete parent rollback was not saved')
    complete = json.loads((ROOT / 'parent-complete-source-hashes.json').read_text())
    expected = json.loads((ROOT / 'parent-source-hashes.json').read_text())
    require(len(complete) == 220 and len(expected) == 21, 'Parent inventory drift')
    require(source_inventory(parent) == complete, 'Complete locked parent differs')
    require(all(complete[n] == s for n, s in expected.items()), 'Parent receipt inconsistency')
    new_inventory = source_inventory(candidate)
    require(set(complete) <= set(new_inventory), 'Deleting an existing source file is forbidden')
    files, patch = {}, []
    for name in sorted(new_inventory):
        before, after = complete.get(name), new_inventory[name]
        if before == after:
            continue
        if name == GRADLE:
            wanted = (parent / name).read_text().replace('versionCode 2103204', 'versionCode 2103205')
            wanted = wanted.replace('1.0.9-Cobra-OLED-Blue-RC1', '1.0.9-Cobra-Final-Features-RC1')
            require((candidate / name).read_text() == wanted, 'Gradle changed outside release identity')
            continue
        require(permitted_file(name, before), 'Unapproved source owner: ' + name)
        files[name] = {'before': before, 'after': after}
        old_text = (parent / name).read_text() if before else ''
        new_text = (candidate / name).read_text()
        require(new_text.endswith('\n') and (not old_text or old_text.endswith('\n')),
                'Patch source requires final newline: ' + name)
        patch.extend(difflib.unified_diff(old_text.splitlines(True), new_text.splitlines(True),
                                        'a/' + name if before else '/dev/null', 'b/' + name))
    require(files, 'No approved feature delta')
    additions = [n for n, r in files.items() if r['before'] is None]
    validate_install((parent / INSTALL).read_text(), (candidate / INSTALL).read_text(), additions)
    protected = protected_members((parent / ACTIVITY).read_text(), (candidate / ACTIVITY).read_text())
    previous = ROOT.parent / 'cobra-oled-blue-2103204'
    inherited = (json.loads((previous / 'inherited-android-cases.json').read_text()) |
                 json.loads((previous / 'new-android-cases.json').read_text()))
    require(len(inherited) == 53 and sum(map(len, inherited.values())) == 500, 'Parent Android inventory drift')
    require(inherited == json.loads((ROOT / 'inherited-android-cases.json').read_text()), 'Inherited cases changed')
    tests, hashes = collect_tests()
    require(not (set(inherited) & set(tests)), 'Overlapping new test suites')
    patch_text = ''.join(patch)
    reviewed = {
        'status': 'frozen', 'parent_build': 2103204, 'parent_commit': PARENT_COMMIT,
        'files': files, 'patch_sha256': hashlib.sha256(patch_text.encode()).hexdigest(),
        'parent_png_pixels_sha256': sha(ROOT / 'parent-png-pixels.json'),
        'parent_source_files': 220, 'new_source_files': len(additions),
        'protected_runtime_members': protected, 'inherited_android_cases': 500,
        'new_android_cases': sum(map(len, tests.values())), 'test_source_hashes': hashes,
        'native_engine_recompiled': False, 'physical_device_verified': False,
        'user_requested_controls': True, 'new_features': True,
        'excluded_features': ['4 Command Palette', '11 dedicated Fold Continuity'],
    }
    (ROOT / 'features.patch').write_text(patch_text)
    (ROOT / 'new-android-cases.json').write_text(json.dumps(tests, indent=2) + '\n')
    (ROOT / 'reviewed.json').write_text(json.dumps(reviewed, indent=2) + '\n')
    print(json.dumps({'status': 'frozen', 'source_files': sorted(files), 'protected_members': len(protected),
                      'inherited_cases': 500, 'new_cases': reviewed['new_android_cases'],
                      'patch_sha256': reviewed['patch_sha256'], 'physical_device_verified': False}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze', action='store_true', required=True)
    parser.add_argument('--parent', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--rollback-upload-receipt', type=Path, required=True)
    args = parser.parse_args()
    freeze(args.parent.resolve(), args.candidate.resolve(), args.rollback_upload_receipt.resolve())
