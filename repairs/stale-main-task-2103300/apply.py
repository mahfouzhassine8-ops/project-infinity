#!/usr/bin/env python3
"""Apply the 2103300 stale single-instance task repair over exact 2103299."""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
from pathlib import Path

PARENT_SHA = 'e46f1745668d6cd6b3df05ae12785e8a3a952e94c9e14cec70a2901ed0bd9dc5'
PARENT_COMMIT = '56a9ec9ed5fc6a2cd02a4d64975d7fb6b77f93aa'
LOCKED_2103297 = 'e0e70f6a0fc8ff9fbd8836f5979f90c64de4678fe0d468336fc59ce7cf4e9f0c'
LOCKED_2103295 = 'dba26141addbacd64f334bcc32633669ffcc3c4677961e7ce3e23f01684416a0'
RELEASE = '1.0.9-Clean-Task-Relaunch-RC1'
VERSION = 2103300

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f'Unexpected source preimage ({text.count(old)} matches): {old[:100]!r}')
    return text.replace(old, new, 1)

def apply_source(root: Path, out: Path) -> None:
    shell = root / 'shell-kodi'
    handoff = shell / 'tools/android/packaging/xbmc/src/InfinityStartupHandoff.java.in'
    gradle = shell / 'tools/android/packaging/xbmc/build.gradle.in'
    before = {str(p.relative_to(shell)): sha(p.read_bytes()) for p in (handoff, gradle)}

    text = handoff.read_text()
    old = '''    int unsafe = Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED | Intent.FLAG_ACTIVITY_CLEAR_TASK |
        Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_MULTIPLE_TASK |
        Intent.FLAG_ACTIVITY_NEW_DOCUMENT | Intent.FLAG_ACTIVITY_PREVIOUS_IS_TOP |
        Intent.FLAG_ACTIVITY_REORDER_TO_FRONT;
    intent.setFlags((intent.getFlags() & ~unsafe) | Intent.FLAG_ACTIVITY_NEW_TASK |
        Intent.FLAG_ACTIVITY_SINGLE_TOP | (live ? Intent.FLAG_ACTIVITY_REORDER_TO_FRONT : 0));'''
    new = '''    int unsafe = Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED | Intent.FLAG_ACTIVITY_CLEAR_TASK |
        Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_MULTIPLE_TASK |
        Intent.FLAG_ACTIVITY_NEW_DOCUMENT | Intent.FLAG_ACTIVITY_PREVIOUS_IS_TOP |
        Intent.FLAG_ACTIVITY_REORDER_TO_FRONT | Intent.FLAG_ACTIVITY_SINGLE_TOP;
    int launchFlags = (intent.getFlags() & ~unsafe) | Intent.FLAG_ACTIVITY_NEW_TASK;
    if (live) {
      // Reuse only the already-validated live single-instance Kodi task.
      launchFlags |= Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_REORDER_TO_FRONT;
    } else {
      // Main is android:launchMode="singleInstance". Clear its stale task record
      // so Android cannot restore a dead NativeActivity/saved native state.
      launchFlags |= Intent.FLAG_ACTIVITY_CLEAR_TASK;
    }
    intent.setFlags(launchFlags);'''
    text = once(text, old, new)
    handoff.write_text(text)

    gradle_text = gradle.read_text()
    gradle_text = once(gradle_text, 'versionCode 2103299', f'versionCode {VERSION}')
    gradle_text = once(gradle_text, '1.0.9-Graceful-Exit-Handoff-RC1', RELEASE)
    gradle.write_text(gradle_text)

    receipt_path = root / 'engine/background-resume-source.json'
    receipt = json.loads(receipt_path.read_text())
    if receipt.get('version_code') != 2103299 or receipt.get('release') != '1.0.9-Graceful-Exit-Handoff-RC1':
        raise RuntimeError('Source receipt is not the 2103299 parent')
    if receipt.get('base_apk_sha256') != 'c816160d25648741882e4a13f47af1ef20f08bda057a777e205a8fe13be2a237':
        raise RuntimeError('Inherited 2103299 source lineage differs from the audited parent')
    after = {str(p.relative_to(shell)): sha(p.read_bytes()) for p in (handoff, gradle)}
    for path, digest in after.items():
        receipt.setdefault('files', {})[path] = {'before': before[path], 'after': digest}
    receipt.update(version_code=VERSION, release=RELEASE,
                   base_apk_sha256=PARENT_SHA, base_source_commit=PARENT_COMMIT)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')

    producer = root / 'scripts/infinity_background_resume.py'
    source = producer.read_text()
    source = once(source, 'VERSION_CODE = 2103299', f'VERSION_CODE = {VERSION}')
    source = once(source, "RELEASE = '1.0.9-Graceful-Exit-Handoff-RC1'", f"RELEASE = '{RELEASE}'")
    source = once(source, "BASE_COMMIT = 'e5f91a7e632ff581158131cba1a1cc8a33b54331'", f"BASE_COMMIT = '{PARENT_COMMIT}'")
    source = once(source, "BASE_APK_SHA256 = 'c816160d25648741882e4a13f47af1ef20f08bda057a777e205a8fe13be2a237'", f"BASE_APK_SHA256 = '{PARENT_SHA}'")
    producer.write_text(source)

    packager = root / 'scripts/package_background_resume.py'
    source = packager.read_text()
    source = source.replace('2103299', str(VERSION)).replace('Graceful-Exit-Handoff-RC1', RELEASE)
    source = source.replace('37105329683', '37117015142')
    source = source.replace('repairs/graceful-exit-handoff-2103300/DEVICE-TEST.txt',
                            'repairs/stale-main-task-2103300/DEVICE-TEST.txt')
    old_bridge_audit = '''    app=next(n for n in new['children'] if n['tag']=='application')
    bridge=[n for n in app['children'] if n['tag']=='activity' and 'InfinityPowerControlActivity' in n['attrs'].get('android:name','')]
    require(len(bridge)==1,'Exactly one private power bridge required')
    node=bridge[0]
    require(set(node['attrs'])=={'android:name','android:exported','android:excludeFromRecents','android:noHistory','android:theme'} and not node['children'],'Power bridge manifest expanded unexpectedly')
    require(node['attrs']['android:exported']=='(type 0x12)0x0','Power bridge must be private')
    require(node['attrs']['android:excludeFromRecents']=='(type 0x12)0xffffffff' and node['attrs']['android:noHistory']=='(type 0x12)0xffffffff','Power bridge must be transient')
    require(node['attrs']['android:theme']=='@0x01030055','Power bridge must use framework Theme.NoDisplay')
    app['children'].remove(node)
    require(old==new,'Compiled manifest drift beyond versions and exact private power bridge')'''
    source = once(source, old_bridge_audit,
                  "    require(old==new,'Compiled manifest drift from exact 2103299 base outside version identity')")
    packager.write_text(source)

    checklist_dir = root / 'repairs/stale-main-task-2103300'
    checklist_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(__file__).parent / 'DEVICE-TEST.txt', checklist_dir / 'DEVICE-TEST.txt')

    out.mkdir(parents=True, exist_ok=True)
    changes = []
    for path in sorted(after):
        changes.append({'path': path, 'before_2103299': before[path],
                        'after_2103300': after[path], 'status': 'unchanged' if before[path] == after[path] else 'changed'})
    (out / 'SOURCE-CHANGES-2103300.json').write_text(json.dumps([r for r in changes if r['status'] == 'changed'], indent=2) + '\n')
    (out / 'SOURCE-BYTE-MANIFEST-2103300.json').write_text(json.dumps(changes, indent=2) + '\n')
    (out / 'REPAIR-SCOPE-2103300.json').write_text(json.dumps({
        'parent_2103299_apk_sha256': PARENT_SHA,
        'parent_2103299_source_commit': PARENT_COMMIT,
        'locked_2103297_apk_sha256': LOCKED_2103297,
        'locked_2103295_apk_sha256': LOCKED_2103295,
        'version_code': VERSION,
        'version_name': RELEASE,
        'native_recompiled': False,
        'skin_assets_or_xml_modified': False,
        'change': 'Only stale Main launches clear the old single-instance Android task. A validated live Main keeps its task and is reordered forward.',
        'diagnostic_correlation': 'Three fresh Main handoffs were each followed within 102–128ms by an Android native SIGSEGV exit while Kodi was initializing.',
        'root_cause': 'The prior fresh-launch intent stripped CLEAR_TASK for stale Main. Because Main is singleInstance, Android could restore its stale task/native state instead of making a clean Main task.',
        'physical_device_verified': False,
        'locked': False
    }, indent=2) + '\n')
    print('PASS: exact 2103299 parent checked; stale single-instance task cleared only on fresh Main handoff')

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--parent', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    if sha(args.parent.read_bytes()) != PARENT_SHA:
        raise RuntimeError('Not the exact 2103299 parent APK')
    apply_source(args.root.resolve(), args.out.resolve())

if __name__ == '__main__':
    main()
