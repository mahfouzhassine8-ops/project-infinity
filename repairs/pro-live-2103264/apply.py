#!/usr/bin/env python3
"""Badge-only delta on the exact locked 2103263 shell."""
from pathlib import Path
import argparse, hashlib, json

A = 'tools/android/packaging/xbmc/'
PARENT = 'dbe1925cbafc7edf423cd45ded7295ee73f12cd1'
APK = '00c3f00eaf336ef2102e9f2226e8cb02e8d95767c043431690024018772153e4'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def once(s, old, new):
    assert s.count(old) == 1, (s.count(old), old)
    return s.replace(old, new, 1)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, default=Path('.'))
    p.add_argument('--evidence', type=Path, default=Path('audit264'))
    a = p.parse_args()
    root, ev = a.root.resolve(), a.evidence.resolve()
    ev.mkdir(parents=True, exist_ok=True)
    source = root / 'shell-kodi'
    before = {str(f.relative_to(source)): sha(f) for f in source.rglob('*') if f.is_file()}
    manifest = root / 'source263/source-hashes-after.json'
    assert sha(manifest) == 'bb2ab4a2c66358b5c4f8027d807393c0a306c0909ebc4664decfc84e2a2b32f8'
    assert before == json.loads(manifest.read_text()), 'Not exact locked 2103263 source'
    pro = source / (A + 'src/CobraProUi.java.in')
    old = pro.read_text()
    new = once(old, 'live=new Ink(c,Color.WHITE,10,false);live.setGravity(Gravity.CENTER);GradientDrawable liveBg=new GradientDrawable();liveBg.setColor(0xffdf2337);liveBg.setCornerRadius(px(c,7));live.setBackground(liveBg);addView(live);',
        'live=new Ink(c,0xffff6b75,10,true);live.setGravity(Gravity.CENTER);GradientDrawable liveBg=new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,new int[]{0xff133540,0xff0b2430,0xff06151c});liveBg.setCornerRadius(px(c,16));liveBg.setStroke(Math.max(1,px(c,1)),CYAN);live.setBackground(liveBg);addView(live);')
    new = once(new, 'int liveW=live.getVisibility()==VISIBLE?px(getContext(),43):0;',
        'int liveW=live.getVisibility()==VISIBLE?Math.max(px(getContext(),43),(int)Math.ceil(live.getPaint().measureText("LIVE"))+px(getContext(),16)):0;')
    pro.write_text(new)
    (ev / 'CobraProUi-before.java.in').write_text(old)
    gradle = source / (A + 'build.gradle.in')
    g = once(gradle.read_text(), 'versionCode 2103263', 'versionCode 2103264')
    gradle.write_text(once(g, '1.0.9-Pro-OLED-Light-Polish-RC1', '1.0.9-Pro-LIVE-Glass-RC1'))
    after = {str(f.relative_to(source)): sha(f) for f in source.rglob('*') if f.is_file()}
    changed = sorted(f for f in before if before[f] != after.get(f))
    assert set(before) == set(after)
    assert changed == sorted([A+'src/CobraProUi.java.in', A+'build.gradle.in'])
    receiptpath = root / 'engine/background-resume-source.json'
    receipt = json.loads(receiptpath.read_text())
    for name in changed:
        receipt['files'][name] = {'before': before[name], 'after': after[name]}
    receipt.update(version_code=2103264, version_name='1.0.9-Pro-LIVE-Glass-RC1', source_parent=2103263,
                   source_parent_commit=PARENT, native_engine_recompiled=False, physical_device_verified=False)
    receiptpath.write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
    cfg = root / 'scripts/infinity_background_resume.py'
    c = once(cfg.read_text(), 'VERSION_CODE = 2103263', 'VERSION_CODE = 2103264')
    c = once(c, "RELEASE = '1.0.9-Pro-OLED-Light-Polish-RC1'", "RELEASE = '1.0.9-Pro-LIVE-Glass-RC1'")
    c = once(c, "BASE_APK_SHA256 = 'be06ce257594f4ba82f0c8bafe7a3b180bf44331cbe9605e47b0f41d1cd3865f'", "BASE_APK_SHA256 = '"+APK+"'")
    cfg.write_text(c)
    pack = root / 'scripts/package_background_resume.py'
    t = pack.read_text().replace('Infinity-2103263-Pro-OLED-Light-Polish-RC1', 'Infinity-2103264-Pro-LIVE-Glass-RC1')
    t = once(t, "'base_run':36342321400", "'base_run':36662814776")
    t = once(t, "ROOT/'repairs/pro-polish-2103263/DEVICE-TEST.md'", "ROOT/'repairs/pro-live-2103264/DEVICE-TEST.md'")
    pack.write_text(t)
    result = dict(candidate_version=2103264, parent_version=2103263, parent_commit=PARENT, changed=changed,
                  other_shell_files_byte_identical=len(before)-2, all_activity_code_byte_identical=True,
                  playback_and_other_modes_byte_identical=True, new_player_owner=False, native_engine_recompiled=False,
                  physical_device_verified=False, stable_lock=False, glass='static layered cyan shading and rim, no live backdrop blur')
    (ev / 'source-verification.json').write_text(json.dumps(result, indent=2)+'\n')
    (ev / 'source-hashes-after.json').write_text(json.dumps(after, indent=2)+'\n')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
