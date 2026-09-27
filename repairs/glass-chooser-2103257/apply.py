#!/usr/bin/env python3
"""Presentation-only, exact-preimage patch over reconstructed locked phone 2103256."""
import argparse, base64, hashlib, json, re, shutil
from pathlib import Path

BASE_SHA='73e09e90680da6c8e31bff41b045cab4c6721723af1a1b31f6ff3ea1947603ca'
ENGINE_SHA='c7976ce0adb45b9264f2092a27111be4e05bde4220be2b26b1ea0e2cc74f1e2d'
BASE_COMMIT='ef0ef44a9020f6a2d1488babff87caffc0a5b686'
A='tools/android/packaging/xbmc/'
PREIMAGES={A+'src/Splash.java.in':'54e203c24ccb0fdf4eee465abbbcf77b91e6e1b88852f73ec24d40cf191ad3ad',A+'build.gradle.in':'e1489e1ea59b0ffe672d82e1f8191eb3251decfe31883cc83891a5c093dd0e54','cmake/scripts/android/Install.cmake':'ab4f8e9abe7e6acc31823bdeffd38ab956eed11944e35c05602c18f1034cc490'}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def once(s,old,new):
    assert s.count(old)==1, 'Source preimage mismatch: '+old[:100]
    return s.replace(old,new,1)

GLASS_METHOD='''  /** Built-in locked phone visual; original native routing/recovery own all actions. */
  private boolean showLockedGlassChooser() {
    if (isAndroidTV() || CobraPresentationSafety.isSafe(this)) return false;
    try {
      InfinityGlassChooser glass = new InfinityGlassChooser(this, new InfinityGlassChooser.Actions() {
        public void enter(String experience) { launchInfinityExperience(experience); }
        public void settings(String experience) { showExperienceCardSettings(experience); }
        public void themes() { vtheme().manager(Splash.this); }
        public String appearance() { return chooserAppearanceMode(); }
        public void appearanceChanged() { cobraRefreshSafetyChooser(); }
      });
      org.json.JSONObject spec = new org.json.JSONObject();
      spec.put("schema",1);spec.put("scope","infinity-experience-chooser");spec.put("minimum_bridge",1);
      spec.put("copy",new org.json.JSONObject());
      org.json.JSONObject palette = new org.json.JSONObject();
      palette.put("background",glass.light?"#EEF1F5":"#041326");spec.put("palette",palette);
      ExperienceTheme bars = new ExperienceTheme(spec);
      setContentView(glass);
      cobraPrepareExperienceSystemBars(bars,glass,glass.content);
      glass.focusEntry();
      return true;
    } catch (RuntimeException | org.json.JSONException failed) {
      // Presentation failure returns to the existing native chooser; never reset user data.
      android.util.Log.e("InfinityChooser","Glass presentation unavailable; using existing chooser",failed);
      return false;
    }
  }

'''

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path('.'));ap.add_argument('--evidence',type=Path,default=Path('audit257'));args=ap.parse_args()
    root=args.root.resolve();source=root/'shell-kodi';here=Path(__file__).resolve().parent;evidence=args.evidence.resolve();evidence.mkdir(parents=True,exist_ok=True)
    before={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()}
    for name,digest in PREIMAGES.items():assert before[name]==digest,(name,'not locked 2103256')
    splash=source/(A+'src/Splash.java.in');old=splash.read_text()
    s=once(old,'  private void showInfinityExperienceChooser()\n  {','  private void showInfinityExperienceChooser()\n  {\n    if (showLockedGlassChooser()) return;')
    s=once(s,'  void cobraRefreshSafetyChooser()',GLASS_METHOD+'  void cobraRefreshSafetyChooser()')
    # Settings: palette only. Preserve every action, option and callback byte-for-byte.
    s=once(s,'    final int accent = cobra ? 0xff35c7d9 : 0xffb59a5a;\n    final int text = 0xfff5f7fb;\n    final int panelTop = cobra ? 0xff0d1720 : 0xff15130f;\n    final int panelBottom = 0xff080d14;',
      '    final boolean glassLight = "light".equals(chooserAppearanceMode());\n    final int accent = glassLight ? (cobra ? 0xff087797 : 0xff896018) : (cobra ? 0xff35c7d9 : 0xffb59a5a);\n    final int text = glassLight ? 0xff081c34 : 0xfff5f7fb;\n    final int panelTop = glassLight ? 0xfff8fbff : (cobra ? 0xff0d1720 : 0xff15130f);\n    final int panelBottom = glassLight ? 0xffe8edf3 : 0xff080d14;')
    splash.write_text(s)
    gradle=source/(A+'build.gradle.in');g=gradle.read_text();g=once(g,'versionCode 2103256','versionCode 2103257');g=once(g,'1.0.9-Cobra-No-Hold-Menu-RC1','1.0.9-Glass-Chooser-Light-Dark-RC1');gradle.write_text(g)
    shutil.copy2(here/'InfinityGlassChooser.java.in',source/(A+'src/InfinityGlassChooser.java.in'))
    art=json.loads((here/'assets/art.json').read_text());assert set(art)=={m+'_'+p for m in ['light','dark'] for p in ['gold','cyan','orb','background']}
    artcode='package @APP_PACKAGE@;\n\n/** Small immutable golden-master material plates; no stored Context. */\nfinal class InfinityGlassArt {\n  private InfinityGlassArt() {}\n  static android.graphics.Bitmap decode(String key) {\n    String data;\n    switch(key) {\n'
    sizes={}
    for key,value in sorted(art.items()):
        raw=base64.b64decode(value,validate=True);assert raw[:4]==b'RIFF';sizes[key]=len(raw)
        artcode+='      case '+json.dumps(key)+': data='+json.dumps(value)+'; break;\n'
    artcode+='      default: throw new IllegalArgumentException("Unknown chooser material");\n    }\n    byte[] bytes=android.util.Base64.decode(data,android.util.Base64.DEFAULT);\n    android.graphics.Bitmap bitmap=android.graphics.BitmapFactory.decodeByteArray(bytes,0,bytes.length);\n    if(bitmap!=null)bitmap.setDensity(android.graphics.Bitmap.DENSITY_NONE);\n    return bitmap;\n  }\n}\n'
    (source/(A+'src/InfinityGlassArt.java.in')).write_text(artcode)
    cmake=source/'cmake/scripts/android/Install.cmake';cmake.write_text(once(cmake.read_text(),'                  src/Splash.java','                  src/Splash.java\n                  src/InfinityGlassChooser.java\n                  src/InfinityGlassArt.java'))
    after={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()}
    changed=sorted(k for k in before if before[k]!=after.get(k));added=sorted(set(after)-set(before))
    assert changed==sorted(PREIMAGES);assert added==sorted([A+'src/InfinityGlassChooser.java.in',A+'src/InfinityGlassArt.java.in'])
    # Surgically reverse the presentation patch and prove the baseline bytes are restored.
    undo=s.replace(GLASS_METHOD,'').replace('    if (showLockedGlassChooser()) return;\n','',1)
    new_palette=s[s.index('    final boolean glassLight'):s.index('\n\n    android.widget.ArrayAdapter',s.index('    final boolean glassLight'))]
    original_palette=old[old.index('    final int accent = cobra ? 0xff35c7d9'):old.index('\n\n    android.widget.ArrayAdapter',old.index('    final int accent = cobra ? 0xff35c7d9'))]
    undo=undo.replace(new_palette,original_palette,1);assert undo==old,'Unexpected changes outside chooser presentation'
    receipt_file=root/'engine/background-resume-source.json';receipt=json.loads(receipt_file.read_text())
    for name in changed+added:receipt['files'][name]={'before':before.get(name),'after':after[name]}
    receipt.update(version_code=2103257,version_name='1.0.9-Glass-Chooser-Light-Dark-RC1',source_parent=2103256,source_parent_commit=BASE_COMMIT,chooser_glass_presentation=True,chooser_sound_integrated=False,physical_device_verified=False,runtime_device_tested=False,native_engine_recompiled=False)
    receipt_file.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    config=root/'scripts/infinity_background_resume.py';text=config.read_text();text=once(text,'VERSION_CODE = 2103256','VERSION_CODE = 2103257');text=once(text,"RELEASE = '1.0.9-Cobra-No-Hold-Menu-RC1'","RELEASE = '1.0.9-Glass-Chooser-Light-Dark-RC1'")
    text=once(text,"BASE_APK_SHA256 = '273c7d0a88196cd9f00121b51fe5ac54a4328558c34d5c3c79a74e85a29176be'","BASE_APK_SHA256 = '"+BASE_SHA+"'");config.write_text(text)
    package=root/'scripts/package_background_resume.py';text=package.read_text().replace('Infinity-2103256-Cobra-No-Hold-Menu-RC1','Infinity-2103257-Glass-Chooser-Light-Dark-RC1').replace("'base_run':36230424118","'base_run':36235662809").replace("ROOT/'repairs/cobra-no-hold-2103256/DEVICE-TEST.md'","ROOT/'repairs/glass-chooser-2103257/DEVICE-TEST.md'").replace('PASS: Cobra no-video-hold menu APK; exact 2103255 native/assets/resources; permanent signer verified','PASS: Glass chooser TEST CANDIDATE; exact 2103256 native/assets/resources; permanent signer verified');package.write_text(text)
    report={'baseline_commit':BASE_COMMIT,'baseline_version':2103256,'candidate_version':2103257,'android_source_delta':changed,'added':added,'all_other_source_files_byte_identical':len(before)-len(changed),'splash_changes_fully_reversible':True,'startup_lifecycle_unchanged':True,'settings_callbacks_unchanged':True,'native_recompiled':False,'startup_sound_integrated':False,'tv_source_changed':False,'art_compressed_bytes':sum(sizes.values()),'art_sizes':sizes,'reference_png_sha256':{'dark':'407fbb2a5c558ccc8b37d67c121a7ed56a195435591f406a9c16043b680f4067','light':'672b2cbe362881bd268b6f8fdcdc542439bae175ffb8476d264a4a4663a6e6ce'},'device_verified':False,'pixel_perfect_verified':False}
    (evidence/'source-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    import difflib
    (evidence/'Splash-presentation-only.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='locked-2103256/Splash',tofile='candidate-2103257/Splash')))
    (evidence/'source-hashes-before.json').write_text(json.dumps(before,indent=2)+'\n');(evidence/'source-hashes-after.json').write_text(json.dumps(after,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
