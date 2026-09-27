#!/usr/bin/env python3
"""Exact locked 2103259 -> 2103260. Cobra Recovery and stationary chooser only."""
import argparse,difflib,hashlib,json,shutil
from pathlib import Path
A='tools/android/packaging/xbmc/'
PARENT='05dfa1ab6c06533fa02e13f5566256dde548e1ba'
APK='0e1edb8872ac4047e810fc1ee297b6edd53d86535b0f1ff722f68661bf88d969'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def once(s,a,b):
    assert s.count(a)==1,('Unexpected preimage',a[:120]);return s.replace(a,b,1)
HELPER='''  private InfinityGlassRecovery.Builder cobraRecoveryDialog(){
    return new InfinityGlassRecovery.Builder(this,()->"light".equals(chooserAppearanceMode()),
        new CobraVisualRenderer.DialogBuilder(this,vtheme(),"chooser.recovery"),
        !isAndroidTV() && !CobraPresentationSafety.isSafe(this));
  }

'''
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path('.'));ap.add_argument('--evidence',type=Path,default=Path('audit260'));args=ap.parse_args()
    root=args.root.resolve();src=root/'shell-kodi';out=args.evidence.resolve();out.mkdir(parents=True,exist_ok=True);here=Path(__file__).resolve().parent
    manifest=root/'source259/source-hashes-after.json'
    before={str(p.relative_to(src)):sha(p) for p in src.rglob('*') if p.is_file()}
    assert before==json.loads(manifest.read_text()),'Not the exact locked 2103259 reconstructed source'
    originals={n:(src/(A+'src/'+n+'.java.in')).read_text() for n in ['Splash','InfinityGlassChooser']}
    original=originals['Splash'];start=original.index('  private void showCobraRecovery(){');end=original.index('\n  // Custom chooser scenes',start)
    method=original[start:end];old='new CobraVisualRenderer.DialogBuilder(this,vtheme(),"chooser.recovery")'
    assert method.count(old)==2
    updated=method.replace(old,'cobraRecoveryDialog()')
    splash=once(original,method,HELPER+updated)
    assert splash.replace(HELPER,'',1).replace(updated,method,1)==original,'Recovery actions or another subsystem changed'
    (src/(A+'src/Splash.java.in')).write_text(splash)
    chooser=originals['InfinityGlassChooser']
    chooser=once(chooser,'import android.widget.ScrollView;\n','')
    chooser=once(chooser,'final ScrollView content;','final FrameLayout content;')
    chooser=once(chooser,'content=new ScrollView(context) {','content=new FrameLayout(context) {\n      @Override public void scrollTo(int x,int y) { super.scrollTo(0,0); }\n      @Override public boolean shouldDelayChildPressedState() { return false; }')
    chooser=once(chooser,'content.setFillViewport(true);content.setClipToPadding(true);','content.setClipToPadding(true);content.setClipChildren(true);')
    chooser=once(chooser,'content.setVerticalScrollBarEnabled(false);content.setOverScrollMode(OVER_SCROLL_IF_CONTENT_SCROLLS);','content.setOverScrollMode(OVER_SCROLL_NEVER);')
    chooser=once(chooser,'content.addView(stage,new ScrollView.LayoutParams(-1,-2));','content.addView(stage,new FrameLayout.LayoutParams(-1,-1));')
    oldmeasure='''      // ScrollView's first pass is UNSPECIFIED. Prefer its real window, not physical display.
      View parent=getParent() instanceof View?(View)getParent():null;
      int viewport=Math.max(viewportHint,parent==null?available:Math.max(available,parent.getMeasuredHeight()-parent.getPaddingTop()-parent.getPaddingBottom()));'''
    chooser=once(chooser,oldmeasure,'''      // The fixed viewport passes its current inset-adjusted height. Never use stale parent measurements.
      int viewport=MeasureSpec.getMode(hs)==MeasureSpec.UNSPECIFIED?viewportHint:available;''')
    oldheight='''      scale=Math.max(.1f,designWidth/referenceWidth);left=(w-designWidth)/2;
      int natural=(int)Math.ceil(referenceHeight*scale);
      int height=Math.max(natural,MeasureSpec.getMode(hs)==MeasureSpec.EXACTLY?available:0);'''
    chooser=once(chooser,oldheight,'''      // Fit the entire portrait composition. Short landscape windows crop only the decorative floor.
      float fittedHeight=w>viewport?(light?1340f:1205f):referenceHeight;
      if(viewport>0)designWidth=Math.min(designWidth,viewport*referenceWidth/fittedHeight);
      scale=Math.max(.01f,designWidth/referenceWidth);left=(w-designWidth)/2;
      int height=viewport>0?viewport:(int)Math.ceil(referenceHeight*scale);''')
    (src/(A+'src/InfinityGlassChooser.java.in')).write_text(chooser)
    shutil.copy2(here/'InfinityGlassRecovery.java.in',src/(A+'src/InfinityGlassRecovery.java.in'))
    gradle=src/(A+'build.gradle.in');g=once(gradle.read_text(),'versionCode 2103259','versionCode 2103260');g=once(g,'1.0.9-Options-Health-Glass-Finish-RC1','1.0.9-Recovery-Fixed-Chooser-RC1');gradle.write_text(g)
    install=src/'cmake/scripts/android/Install.cmake';install.write_text(once(install.read_text(),'                  src/InfinityGlassHealth.java','                  src/InfinityGlassHealth.java\n                  src/InfinityGlassRecovery.java'))
    after={str(p.relative_to(src)):sha(p) for p in src.rglob('*') if p.is_file()}
    changed=sorted(k for k in before if before[k]!=after.get(k));added=sorted(set(after)-set(before))
    assert changed==sorted([A+'src/Splash.java.in',A+'src/InfinityGlassChooser.java.in',A+'build.gradle.in','cmake/scripts/android/Install.cmake'])
    assert added==[A+'src/InfinityGlassRecovery.java.in']
    for name in ['InfinityGlassOptions','InfinityGlassHealth','InfinityGlassArt','Main','InfinityLiveActivity','CobraPresentationSafety']:
        assert before[A+'src/'+name+'.java.in']==after[A+'src/'+name+'.java.in']
    receiptfile=root/'engine/background-resume-source.json';receipt=json.loads(receiptfile.read_text())
    for f in changed+added:receipt['files'][f]={'before':before.get(f),'after':after[f]}
    receipt.update(version_code=2103260,version_name='1.0.9-Recovery-Fixed-Chooser-RC1',source_parent=2103259,source_parent_commit=PARENT,physical_device_verified=False,native_engine_recompiled=False,recovery_glass=True,chooser_stationary=True)
    receiptfile.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    conf=root/'scripts/infinity_background_resume.py';t=conf.read_text();t=once(t,'VERSION_CODE = 2103259','VERSION_CODE = 2103260');t=once(t,"RELEASE = '1.0.9-Options-Health-Glass-Finish-RC1'","RELEASE = '1.0.9-Recovery-Fixed-Chooser-RC1'");t=once(t,"BASE_APK_SHA256 = '3f94abba544aee75d1e12ff10d1af98e3b277685e8f39f835b67e601dfbbeded'","BASE_APK_SHA256 = '"+APK+"'");conf.write_text(t)
    pack=root/'scripts/package_background_resume.py';t=pack.read_text().replace('Infinity-2103259-Options-Health-Glass-Finish-RC1','Infinity-2103260-Recovery-Fixed-Chooser-RC1').replace("'base_run':36304211423","'base_run':36305461854").replace("ROOT/'repairs/options-health-2103259/DEVICE-TEST.md'","ROOT/'repairs/recovery-fixed-2103260/DEVICE-TEST.md'").replace('Options and Health TEST CANDIDATE; exact 2103258','Recovery and fixed chooser TEST CANDIDATE; exact 2103259');pack.write_text(t)
    report=dict(parent_commit=PARENT,baseline_version=2103259,candidate_version=2103260,android_source_delta=changed,added=added,other_source_files_byte_identical=len(before)-len(changed),splash_patch_reversible=True,recovery_labels_confirmation_and_actions_preserved=True,options_health_and_art_byte_identical=True,native_recompiled=False,startup_sound_integrated=False,device_verified=False)
    (out/'source-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'recovery-method.java.inc').write_text(updated)
    for name,new in [('Splash',splash),('InfinityGlassChooser',chooser)]:
        (out/(name+'.diff')).write_text(''.join(difflib.unified_diff(originals[name].splitlines(True),new.splitlines(True),fromfile='2103259/'+name,tofile='2103260/'+name)))
    for name,data in [('before',before),('after',after)]: (out/('source-hashes-'+name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
