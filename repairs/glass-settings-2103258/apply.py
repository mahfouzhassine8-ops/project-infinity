#!/usr/bin/env python3
"""Exact 2103257 -> 2103258. Options UI only; main chooser and callbacks unchanged."""
import argparse, hashlib, json, shutil, difflib
from pathlib import Path
P=Path(__file__).resolve().parent
A='tools/android/packaging/xbmc/'
BASE_APK='bc0ff18f0edf6c55eef7caa4582917738d0488c1ab58365f0669065d105867df'
PARENT_COMMIT='2711bb34bb9587f7cb3a81fd3fbf10d30743131a'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def once(s,old,new):
    assert s.count(old)==1, ('Source preimage mismatch',old[:80]);return s.replace(old,new,1)
def callback(s):
    start=s.index('.setAdapter(adapter, ')+len('.setAdapter(adapter, ')
    end=s.index('\n        .setNegativeButton',start)-1
    assert s[end]==')';return s[start:end]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path('.'));ap.add_argument('--evidence',type=Path,default=Path('audit258'));args=ap.parse_args()
    root=args.root.resolve();src=root/'shell-kodi';out=args.evidence.resolve();out.mkdir(parents=True,exist_ok=True)
    manifest=root/'source257/source-hashes-after.json'
    assert sha(manifest)=='79741833ec936f7d740692acaea0b9c37b6f4a5c1e57e4d4c6529d0921efe62d','Unexpected parent hash manifest'
    pre=json.loads(manifest.read_text());before={str(p.relative_to(src)):sha(p) for p in src.rglob('*') if p.is_file()}
    assert before==pre,'Source is not the exact 2103257 reconstructed tree'
    splash=src/(A+'src/Splash.java.in');original=splash.read_text();cb=callback(original)
    assert cb.startswith('(dialogInterface, which) -> {') and cb.endswith('}')
    s=once(original,'.setAdapter(adapter, '+cb+')','.setAdapter(adapter, existingAction)')
    marker='    // This menu is intentionally self-contained so fixing it cannot restyle any'
    injection='''    // The approved glass treatment extends to BOTH settings panels, not only colors.
    final android.content.DialogInterface.OnClickListener existingAction = '''+cb+''';
    if (!isAndroidTV() && !CobraPresentationSafety.isSafe(this)) {
      InfinityGlassOptions glass = null;
      try {
        glass = new InfinityGlassOptions(this, cobra, title, options,
            () -> "light".equals(chooserAppearanceMode()), existingAction);
        glass.show();
        return;
      } catch (RuntimeException presentationFailure) {
        if (glass != null && glass.isShowing()) glass.dismiss();
        android.util.Log.e("InfinityChooser", "Glass options unavailable; using recovery presentation", presentationFailure);
      }
    }

'''
    s=once(s,marker,injection+marker);splash.write_text(s)
    assert s.replace(injection,'',1).replace('.setAdapter(adapter, existingAction)','.setAdapter(adapter, '+cb+')',1)==original
    gradle=src/(A+'build.gradle.in');g=once(gradle.read_text(),'versionCode 2103257','versionCode 2103258');g=once(g,'1.0.9-Glass-Chooser-Light-Dark-RC1','1.0.9-Glass-Settings-Light-Dark-RC1');gradle.write_text(g)
    install=src/'cmake/scripts/android/Install.cmake';install.write_text(once(install.read_text(),'                  src/InfinityGlassChooser.java','                  src/InfinityGlassChooser.java\n                  src/InfinityGlassOptions.java'))
    shutil.copy2(P/'InfinityGlassOptions.java.in',src/(A+'src/InfinityGlassOptions.java.in'))
    after={str(p.relative_to(src)):sha(p) for p in src.rglob('*') if p.is_file()}
    changed=sorted(k for k in before if before[k]!=after.get(k));added=sorted(set(after)-set(before))
    assert changed==sorted([A+'src/Splash.java.in',A+'build.gradle.in','cmake/scripts/android/Install.cmake'])
    assert added==[A+'src/InfinityGlassOptions.java.in']
    for name in ['InfinityGlassChooser.java.in','InfinityGlassArt.java.in','InfinityLiveActivity.java.in','Main.java.in']:
        assert before[A+'src/'+name]==after[A+'src/'+name]
    rec=root/'engine/background-resume-source.json';receipt=json.loads(rec.read_text())
    for f in changed+added:receipt['files'][f]={'before':before.get(f),'after':after[f]}
    receipt.update(version_code=2103258,version_name='1.0.9-Glass-Settings-Light-Dark-RC1',source_parent=2103257,source_parent_commit=PARENT_COMMIT,settings_glass_presentation=True,chooser_sound_integrated=False,physical_device_verified=False,runtime_device_tested=False,native_engine_recompiled=False)
    rec.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    config=root/'scripts/infinity_background_resume.py';t=config.read_text();t=once(t,'VERSION_CODE = 2103257','VERSION_CODE = 2103258');t=once(t,"RELEASE = '1.0.9-Glass-Chooser-Light-Dark-RC1'","RELEASE = '1.0.9-Glass-Settings-Light-Dark-RC1'");t=once(t,"BASE_APK_SHA256 = '73e09e90680da6c8e31bff41b045cab4c6721723af1a1b31f6ff3ea1947603ca'","BASE_APK_SHA256 = '"+BASE_APK+"'");config.write_text(t)
    pack=root/'scripts/package_background_resume.py';t=pack.read_text().replace('Infinity-2103257-Glass-Chooser-Light-Dark-RC1','Infinity-2103258-Glass-Settings-Light-Dark-RC1').replace("'base_run':36235662809","'base_run':36302398518").replace("ROOT/'repairs/glass-chooser-2103257/DEVICE-TEST.md'","ROOT/'repairs/glass-settings-2103258/DEVICE-TEST.md'").replace('Glass chooser TEST CANDIDATE; exact 2103256','Glass settings TEST CANDIDATE; exact 2103257');pack.write_text(t)
    result=dict(baseline_version=2103257,candidate_version=2103258,parent_commit=PARENT_COMMIT,android_source_delta=changed,added=added,all_other_source_files_byte_identical=len(before)-len(changed),settings_callback_sha256=hashlib.sha256(cb.encode()).hexdigest(),settings_callbacks_byte_identical=True,splash_patch_reversible=True,chooser_source_and_art_byte_identical=True,native_recompiled=False,startup_sound_integrated=False,device_verified=False)
    (out/'source-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    (out/'settings-callback.java.inc').write_text(cb)
    (out/'Splash-before.java.in').write_text(original)
    (out/'Splash-settings-only.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='2103257/Splash',tofile='2103258/Splash')))
    (out/'source-hashes-before.json').write_text(json.dumps(before,indent=2)+'\n');(out/'source-hashes-after.json').write_text(json.dumps(after,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__': main()
