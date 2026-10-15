#!/usr/bin/env python3
"""Remove only the full-screen Cobra video's hold-to-drawer shortcut.

Input: exact reconstructed 2103255 shell, never an installed phone directory.
This patches one Java listener plus release/build metadata. Native engine,
Infinity skin, companions, provider state and every other gesture are preserved.
"""
from __future__ import annotations
import argparse
import difflib
import hashlib
import json
from pathlib import Path

VERSION = 2103256
RELEASE = '1.0.9-Cobra-No-Hold-Menu-RC1'
APK = 'Infinity-2103256-Cobra-No-Hold-Menu-RC1'
PARENT_APK = '273c7d0a88196cd9f00121b51fe5ac54a4328558c34d5c3c79a74e85a29176be'
PARENT_COMMIT = 'e650b9b0954029f4f9f168531313eabf5a7aeb68'
ENGINE = 'c7976ce0adb45b9264f2092a27111be4e05bde4220be2b26b1ea0e2cc74f1e2d'
LIVE = 'tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
GRADLE = 'tools/android/packaging/xbmc/build.gradle.in'
OLD_HOLD = '    mPlayerOverlay.setOnLongClickListener(v->{if(!mCobraPlayerLocked)showCobraPlayerDrawer();else showCobraPlayerUnlockAffordance();return true;});'
NEW_HOLD = '    // Consume a video-surface hold without opening a menu or falling through to a tap.\n    mPlayerOverlay.setOnLongClickListener(v -> true);'
EXPECTED = {
    'shell-kodi/'+LIVE: '4af3fc3775fe0711b932bb664385a705f0fc5080deba63b3b21de47986a9146e',
    'shell-kodi/'+GRADLE: 'd95c6e2fd3206438ea85e9f9f7119d671b60a928c38259d061616b38292208c3',
    'scripts/infinity_background_resume.py': '036c88a531aa1a3e750897a8a07101c9f3feb3c013e434dc041738494577ba04',
    'scripts/package_background_resume.py': 'eb0e3d555f48bb883a69be00d6d08fad559c55094965b088ba23205ed2b166f2',
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError('Unexpected source; refusing non-exact patch: '+repr(old[:100]))
    return text.replace(old, new, 1)


def inventory(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): sha(p.read_bytes()) for p in root.rglob('*') if p.is_file()}


def apply(root: Path, evidence: Path) -> dict:
    if evidence.exists():
        raise ValueError('Evidence output already exists; preserve it')
    old = {}
    for name, expected in EXPECTED.items():
        data = (root/name).read_bytes()
        if sha(data) != expected:
            raise ValueError('Wrong 2103255 source: '+name)
        old[name] = data.decode('utf-8')
    receipt_path = root/'engine/background-resume-source.json'
    receipt = json.loads(receipt_path.read_text())
    if receipt.get('version_code') != 2103255:
        raise ValueError('Wrong parent source receipt')
    for name, row in receipt['files'].items():
        if sha((root/'shell-kodi'/name).read_bytes()) != row['after']:
            raise ValueError('Parent audited source drift: '+name)
    before = inventory(root/'shell-kodi')
    changes = dict(old)
    changes['shell-kodi/'+LIVE] = once(old['shell-kodi/'+LIVE], OLD_HOLD, NEW_HOLD)
    changes['shell-kodi/'+GRADLE] = once(once(old['shell-kodi/'+GRADLE],
        'versionCode 2103255', 'versionCode 2103256'),
        '1.0.9-Infinity-Shipping-Audit-Lifecycle-RC2', RELEASE)
    config = changes['scripts/infinity_background_resume.py']
    for a, b in (
        ('VERSION_CODE = 2103255', 'VERSION_CODE = 2103256'),
        ("RELEASE = '1.0.9-Infinity-Shipping-Audit-Lifecycle-RC2'", 'RELEASE = '+repr(RELEASE)),
        ("BASE_COMMIT = '2674c05e605afbf19a2fe54bdab1a552e76ec394'", 'BASE_COMMIT = '+repr(PARENT_COMMIT)),
        ("BASE_APK_SHA256 = '7f0d5f4c3946d5a4d557ee862f6c59847098d29ac7d4c6e853bb5ddd11197206'", 'BASE_APK_SHA256 = '+repr(PARENT_APK)),
    ):
        config = once(config, a, b)
    changes['scripts/infinity_background_resume.py'] = config
    pack = changes['scripts/package_background_resume.py']
    # writestr mutates ZipInfo.header_offset. Do not corrupt the input archive's
    # cached offsets: it is reread below to validate the retained recorder.
    pack = once(pack, 'import argparse\n', 'import argparse\nimport copy\n')
    pack = once(pack, 'z.writestr(info,a.read(n))', 'z.writestr(copy.copy(info),a.read(n))')
    pack = once(pack, 'z.writestr(info,b.read(n))', 'z.writestr(copy.copy(info),b.read(n))')
    # The parent already contains the recorder. Verify/reuse it rather than append a duplicate ZIP entry.
    pack = once(pack,
        '        z.write(recorder, CRASH_RECORDER_APK_PATH, compress_type=zipfile.ZIP_STORED)',
        "        if CRASH_RECORDER_APK_PATH in an:\n            require(a.read(CRASH_RECORDER_APK_PATH) == recorder.read_bytes(), 'Recorder differs from exact parent')\n        else:\n            z.write(recorder, CRASH_RECORDER_APK_PATH, compress_type=zipfile.ZIP_STORED)")
    if pack.count('Infinity-1.0.9-Infinity-Shipping-Audit-Lifecycle-RC2') != 2:
        raise ValueError('Unexpected packaging filenames')
    pack = pack.replace('Infinity-1.0.9-Infinity-Shipping-Audit-Lifecycle-RC2', APK)
    pack = once(pack, "'base_run':35676573761", "'base_run':36230424118")
    pack = once(pack, "'diagnostic_native_library_added':CRASH_RECORDER_APK_PATH", "'diagnostic_native_library_preserved':CRASH_RECORDER_APK_PATH")
    pack = once(pack, "ROOT/'docs/background-resume-rc1.md'", "ROOT/'repairs/cobra-no-hold-2103256/DEVICE-TEST.md'")
    pack = once(pack,
        'PASS: source-built Android background/resume APK; exact run-40 native engine/assets/resources; permanent signer verified',
        'PASS: Cobra no-video-hold menu APK; exact 2103255 native/assets/resources; permanent signer verified')
    changes['scripts/package_background_resume.py'] = pack
    for name, source in changes.items():
        if name.endswith('.py'):
            compile(source, name, 'exec')
    evidence.mkdir(parents=True)
    (evidence/'InfinityLiveActivity-before.java.in').write_text(old['shell-kodi/'+LIVE])
    for name, source in changes.items():
        (root/name).write_text(source, encoding='utf-8')
    after = inventory(root/'shell-kodi')
    changed = sorted(n for n in set(before)|set(after) if before.get(n)!=after.get(n))
    if changed != sorted([LIVE, GRADLE]):
        raise ValueError('Unexpected Android source delta: '+repr(changed))
    diff = ''.join(difflib.unified_diff(old['shell-kodi/'+LIVE].splitlines(True),
        changes['shell-kodi/'+LIVE].splitlines(True), fromfile='2103255/'+LIVE, tofile='2103256/'+LIVE))
    (evidence/'video-hold-only.patch').write_text(diff)
    for name in changed:
        receipt['files'][name] = {'before': before[name], 'after': after[name]}
    receipt.update(version_code=VERSION, version_name=RELEASE, base_source_commit=PARENT_COMMIT,
        source_parent=2103255, source_parent_commit=PARENT_COMMIT, source_parent_locked=True,
        native_engine_sha256=ENGINE, native_engine_recompiled=False, native_engine_unchanged=True,
        cobra_video_hold_opens_menu=False, cobra_channel_button_preserved=True,
        cobra_channel_quickpeek_preserved=True, runtime_device_tested=False,
        physical_device_verified=False)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
    result = {'version_code': VERSION, 'version_name': RELEASE, 'parent_commit': PARENT_COMMIT,
        'parent_apk_sha256': PARENT_APK, 'engine_sha256': ENGINE,
        'android_source_delta': changed, 'unchanged_shell_files': len(before)-len(changed),
        'shell_inventory_before': before, 'shell_inventory_after': after,
        'one_listener_change_only': True, 'native_recompiled': False, 'device_verified': False}
    (evidence/'source-verification.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print('PASS: exactly one Cobra listener plus release/build metadata changed; all other shell source preserved')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    apply(args.root.resolve(), args.evidence.resolve())
