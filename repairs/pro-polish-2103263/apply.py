#!/usr/bin/env python3
"""Pro-only presentation delta on the exact locked 2103262 shell."""
from pathlib import Path
import argparse, hashlib, json, shutil
from java_members import member, span

A = 'tools/android/packaging/xbmc/'
APK = 'be06ce257594f4ba82f0c8bafe7a3b180bf44331cbe9605e47b0f41d1cd3865f'
PARENT = '00b4f8778fba72389884a5859828c107c0d1800a'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def once(s, old, new):
    assert s.count(old) == 1, (s.count(old), old)
    return s.replace(old, new, 1)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, default=Path('.'))
    p.add_argument('--evidence', type=Path, default=Path('audit263'))
    a = p.parse_args()
    root, ev, here = a.root.resolve(), a.evidence.resolve(), Path(__file__).resolve().parent
    ev.mkdir(parents=True, exist_ok=True)
    source = root / 'shell-kodi'
    before = {str(f.relative_to(source)): sha(f) for f in source.rglob('*') if f.is_file()}
    manifest = root / 'source262/source-hashes-after.json'
    assert sha(manifest) == '2c4730c22925ba42181905fef20f76851d1c5b66a165c2ae6b7614e301433e91'
    assert before == json.loads(manifest.read_text()), 'Not exact locked 2103262 source'
    live = source / (A + 'src/InfinityLiveActivity.java.in')
    old = live.read_text()
    start, end = span(old, 'cobraStyleProShell')
    style = member(old, 'cobraStyleProShell')
    assert 'if (!mCobraProActive' in style or 'if(!mCobraProActive' in style
    style = style[:-1] + '''  // Focus-only page finish; shared restyling restores other modes on exit.
    int page = cobraModeDark() ? Color.BLACK : CobraProUi.PALE;
    if (mRoot != null) mRoot.setBackgroundColor(page);
    if (mStage != null) mStage.setBackgroundColor(page);
    if (mCobraGuideShell != null) mCobraGuideShell.setBackgroundColor(page);
    if (mCobraBrowserHost != null) mCobraBrowserHost.setBackgroundColor(page);
  }'''
    new = old[:start] + style + old[end:]
    assert old[:start] == new[:start] and old[end:] == new[start+len(style):]
    live.write_text(new)
    (ev / 'InfinityLiveActivity-before.java.in').write_text(old)
    shutil.copy2(here / 'CobraProUi.java.in', source / (A + 'src/CobraProUi.java.in'))
    gradle = source / (A + 'build.gradle.in')
    g = once(gradle.read_text(), 'versionCode 2103262', 'versionCode 2103263')
    gradle.write_text(once(g, '1.0.9-Pro-Visual-Correction-RC1', '1.0.9-Pro-OLED-Light-Polish-RC1'))
    after = {str(f.relative_to(source)): sha(f) for f in source.rglob('*') if f.is_file()}
    changed = sorted(f for f in before if before[f] != after.get(f))
    assert set(before) == set(after)
    assert changed == sorted([A+'src/InfinityLiveActivity.java.in', A+'src/CobraProUi.java.in', A+'build.gradle.in'])
    receiptpath = root / 'engine/background-resume-source.json'
    receipt = json.loads(receiptpath.read_text())
    for name in changed:
        receipt['files'][name] = {'before': before[name], 'after': after[name]}
    receipt.update(version_code=2103263, version_name='1.0.9-Pro-OLED-Light-Polish-RC1', source_parent=2103262,
                   source_parent_commit=PARENT, native_engine_recompiled=False, physical_device_verified=False)
    receiptpath.write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
    cfg = root / 'scripts/infinity_background_resume.py'
    c = once(cfg.read_text(), 'VERSION_CODE = 2103262', 'VERSION_CODE = 2103263')
    c = once(c, "RELEASE = '1.0.9-Pro-Visual-Correction-RC1'", "RELEASE = '1.0.9-Pro-OLED-Light-Polish-RC1'")
    c = once(c, "BASE_APK_SHA256 = 'be8d14a7df80759eb41a6f3f4adfee63f5c1e6e27b70aa5c4afaf66b0fb5c393'", "BASE_APK_SHA256 = '"+APK+"'")
    cfg.write_text(c)
    pack = root / 'scripts/package_background_resume.py'
    t = pack.read_text().replace('Infinity-2103262-Pro-Visual-Correction-RC1', 'Infinity-2103263-Pro-OLED-Light-Polish-RC1')
    t = once(t, "'base_run':36335696395", "'base_run':36342321400")
    t = once(t, "ROOT/'repairs/pro-visual-2103262/DEVICE-TEST.md'", "ROOT/'repairs/pro-polish-2103263/DEVICE-TEST.md'")
    pack.write_text(t)
    result = dict(candidate_version=2103263, parent_version=2103262, parent_commit=PARENT, changed=changed,
                  other_shell_files_byte_identical=len(before)-3, all_activity_code_except_pro_style_byte_identical=True,
                  playback_and_other_modes_byte_identical=True, new_player_owner=False, native_engine_recompiled=False,
                  physical_device_verified=False, stable_lock=False, glass='static layered surfaces, no live backdrop blur')
    (ev / 'source-verification.json').write_text(json.dumps(result, indent=2)+'\n')
    (ev / 'source-hashes-after.json').write_text(json.dumps(after, indent=2)+'\n')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
