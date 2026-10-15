#!/usr/bin/env python3
"""Exact passed 2103258 -> 2103259; options and Health presentation only."""
import argparse, hashlib, json, shutil, difflib
from pathlib import Path
P=Path(__file__).resolve().parent
A='tools/android/packaging/xbmc/'
PARENT='f84a49191b2d47c7b84d280e100eeda62cfe6df7'
BASE_APK='3f94abba544aee75d1e12ff10d1af98e3b277685e8f39f835b67e601dfbbeded'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def once(s,old,new):
    assert s.count(old)==1,('Unexpected preimage',old[:100]);return s.replace(old,new,1)

SURFACE=r'''  /** One continuous opaque-backed optical surface: no frame-slice seams or text bleed.
   * Glass depth comes from low-contrast highlights above the backing, not transparency
   * onto the chooser's lettering. All gradients are prepared only when bounds change.
   */
  static final class GlassSurface extends Drawable {
    final Palette palette;final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
    final RectF box=new RectF(),rim=new RectF();final Path clip=new Path();
    final float density,radius;Shader base,glow,sheen,bevel;int opacity=255;ColorFilter filter;
    GlassSurface(Context c,Palette p){palette=p;density=c.getResources().getDisplayMetrics().density;radius=28*density;}
    @Override protected void onBoundsChange(Rect bounds){
      box.set(bounds);clip.reset();clip.addRoundRect(box,radius,radius,Path.Direction.CW);
      int middle=palette.light?(palette.cobra?0xffe5f0f5:0xfff2ede3):
          (palette.cobra?0xff102839:0xff29271f);
      base=new LinearGradient(box.left,box.top,box.right,box.bottom,
          new int[]{palette.top,middle,palette.bottom},new float[]{0,.56f,1},Shader.TileMode.CLAMP);
      glow=new RadialGradient(box.right,box.top,Math.max(1,box.width()*.9f),
          new int[]{alpha(palette.accent,palette.light?22:28),alpha(palette.accent,0)},null,Shader.TileMode.CLAMP);
      sheen=new LinearGradient(box.left,box.top,box.right,box.top+Math.max(1,box.height()*.28f),
          new int[]{alpha(Color.WHITE,palette.light?105:24),alpha(Color.WHITE,0)},null,Shader.TileMode.CLAMP);
      bevel=new LinearGradient(box.left,box.top,box.right,box.bottom,
          new int[]{alpha(Color.WHITE,245),alpha(palette.accent,150),alpha(Color.WHITE,palette.light?225:135),alpha(palette.accent,235)},
          new float[]{0,.34f,.64f,1},Shader.TileMode.CLAMP);
    }
    @Override public void draw(Canvas canvas){
      int save=canvas.save();canvas.clipPath(clip);
      paint.setStyle(Paint.Style.FILL);paint.setColorFilter(filter);paint.setAlpha(opacity);
      paint.setShader(base);canvas.drawRect(box,paint);
      paint.setShader(glow);canvas.drawRect(box,paint);
      paint.setShader(sheen);canvas.drawRect(box,paint);
      paint.setStyle(Paint.Style.STROKE);paint.setShader(bevel);
      rim.set(box);rim.inset(2.5f*density,2.5f*density);paint.setStrokeWidth(4*density);
      canvas.drawRoundRect(rim,radius-2.5f*density,radius-2.5f*density,paint);
      paint.setShader(null);paint.setColor(alpha(palette.accent,palette.light?150:185));
      paint.setAlpha(Math.round(Color.alpha(paint.getColor())*(opacity/255f)));paint.setStrokeWidth(.75f*density);
      rim.set(box);rim.inset(.6f*density,.6f*density);canvas.drawRoundRect(rim,radius-.6f*density,radius-.6f*density,paint);
      paint.setColor(alpha(Color.WHITE,palette.light?220:64));paint.setAlpha(Math.round(Color.alpha(paint.getColor())*(opacity/255f)));
      rim.set(box);rim.inset(5*density,5*density);canvas.drawRoundRect(rim,radius-5*density,radius-5*density,paint);
      paint.setColorFilter(null);paint.setShader(null);canvas.restoreToCount(save);
    }
    @Override public void getOutline(Outline out){out.setRoundRect(getBounds(),radius);}
    @Override public void setAlpha(int a){opacity=a;invalidateSelf();}
    @Override public void setColorFilter(ColorFilter f){filter=f;invalidateSelf();}
    @Override public int getOpacity(){return PixelFormat.TRANSLUCENT;}
  }
'''

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'));p.add_argument('--evidence',type=Path,default=Path('audit259'));a=p.parse_args()
    root=a.root.resolve();src=root/'shell-kodi';out=a.evidence.resolve();out.mkdir(parents=True,exist_ok=True)
    manifest=root/'source258/source-hashes-after.json'
    assert sha(manifest)=='55ea652e217186341286c7a572983591b0d0147f99a1b44f536294ce3e4fa8ba'
    before={str(f.relative_to(src)):sha(f) for f in src.rglob('*') if f.is_file()}
    assert before==json.loads(manifest.read_text()),'Not the exact passed 2103258 source'
    options=src/(A+'src/InfinityGlassOptions.java.in');old_options=options.read_text();s=old_options
    start=s.index('  /** Brand-matched shell with an independently rendered inset edge')
    end=s.index('  /** No rectangular matte:',start)
    s=s[:start]+SURFACE+s[end:]
    s=once(s,'top=light?0xf5f4f7fc:0xf20c1b2b;bottom=light?0xf3e1e9f3:0xf305101e;',
        'top=light?0xfff8fbff:0xff142637;bottom=light?0xffe8edf3:0xff081624;')
    s=once(s,'setClipChildren(false);setClipToPadding(false);','setClipChildren(true);setClipToPadding(true);setClipToOutline(true);')
    s=once(s,'new LinearLayout.LayoutParams(dp(64),dp(54));logo.rightMargin=dp(14);',
        'new LinearLayout.LayoutParams(dp(48),dp(48));logo.rightMargin=dp(12);')
    s=once(s,'title=text(c,heading,24,palette.ink,true);','title=text(c,heading,22,palette.ink,true);')
    s=once(s,'int pad=dp(20),gap=dp(12),inner=','int pad=dp(24),gap=dp(12),inner=')
    s=once(s,'int p=dp(20),g=dp(12),right=','int p=dp(24),g=dp(12),right=')
    s=once(s,'private static Drawable rowSurface','static Drawable rowSurface')
    s=once(s,'private static TextView text','static TextView text')
    options.write_text(s)
    # All options handling, window lifecycle and preference handling remain byte-for-byte.
    assert old_options[:old_options.index('  /** Header and Cancel')]==s[:s.index('  /** Header and Cancel')]
    splash=src/(A+'src/Splash.java.in');original=splash.read_text();s=original
    hstart=original.index('  private void showInfinityHealthCenter()')
    arrays=original[original.index('    String[][] rows={',hstart):original.index('    for(int i=0;i<rows.length;i++){',hstart)]
    assert arrays.count('()->')==4 and 'infinityCopyHealthReport();' in arrays
    helper='''  /** Same Health labels/actions; presentation shared with the two gear panels. */
  private boolean showGlassHealthCenter() {
    if(isAndroidTV() || CobraPresentationSafety.isSafe(this)) return false;
    InfinityGlassHealth created=null;
    try {
      final InfinityGlassHealth dialog=new InfinityGlassHealth(this,"Infinity Health Center",
          "DIAGNOSTICS  •  RECOVERY",()->"light".equals(chooserAppearanceMode()));
      created=dialog;
'''+arrays+'''      dialog.menu(rows,actions);dialog.show();return true;
    } catch(RuntimeException failure) {
      if(created!=null && created.isShowing())created.dismiss();
      android.util.Log.e("InfinityChooser","Health presentation unavailable; using original",failure);
      return false;
    }
  }
  private boolean showGlassHealthText(String title,String body) {
    if(isAndroidTV() || CobraPresentationSafety.isSafe(this)) return false;
    InfinityGlassHealth dialog=null;
    try {
      dialog=new InfinityGlassHealth(this,title,"INFINITY DIAGNOSTICS",()->"light".equals(chooserAppearanceMode()));
      dialog.report(body==null||body.trim().isEmpty()?"No diagnostic information available.":body);
      dialog.show();return true;
    } catch(RuntimeException failure) {
      if(dialog!=null && dialog.isShowing())dialog.dismiss();
      android.util.Log.e("InfinityChooser","Health text presentation unavailable; using original",failure);
      return false;
    }
  }

'''
    s=once(s,'  private void showInfinityHealthCenter()\n  {','  private void showInfinityHealthCenter()\n  {\n    if(showGlassHealthCenter()) return;')
    s=once(s,'  private void infinityShowHealthText(String title,String body)\n  {','  private void infinityShowHealthText(String title,String body)\n  {\n    if(showGlassHealthText(title,body)) return;')
    s=once(s,'  private void showInfinityHealthCenter()',helper+'  private void showInfinityHealthCenter()')
    assert s.replace(helper,'',1).replace('    if(showGlassHealthCenter()) return;\n','',1).replace('    if(showGlassHealthText(title,body)) return;\n','',1)==original
    splash.write_text(s)
    shutil.copy2(P/'InfinityGlassHealth.java.in',src/(A+'src/InfinityGlassHealth.java.in'))
    gradle=src/(A+'build.gradle.in');g=once(gradle.read_text(),'versionCode 2103258','versionCode 2103259');g=once(g,'1.0.9-Glass-Settings-Light-Dark-RC1','1.0.9-Options-Health-Glass-Finish-RC1');gradle.write_text(g)
    cmake=src/'cmake/scripts/android/Install.cmake';cmake.write_text(once(cmake.read_text(),'                  src/InfinityGlassOptions.java','                  src/InfinityGlassOptions.java\n                  src/InfinityGlassHealth.java'))
    after={str(f.relative_to(src)):sha(f) for f in src.rglob('*') if f.is_file()}
    changed=sorted(k for k in before if before[k]!=after.get(k));added=sorted(set(after)-set(before))
    assert changed==sorted([A+'src/Splash.java.in',A+'src/InfinityGlassOptions.java.in',A+'build.gradle.in','cmake/scripts/android/Install.cmake'])
    assert added==[A+'src/InfinityGlassHealth.java.in']
    for name in ['InfinityGlassChooser.java.in','InfinityGlassArt.java.in','Main.java.in','InfinityLiveActivity.java.in']:
        assert before[A+'src/'+name]==after[A+'src/'+name]
    rec=root/'engine/background-resume-source.json';receipt=json.loads(rec.read_text())
    for f in changed+added:receipt['files'][f]={'before':before.get(f),'after':after[f]}
    receipt.update(version_code=2103259,version_name='1.0.9-Options-Health-Glass-Finish-RC1',source_parent=2103258,source_parent_commit=PARENT,options_health_finish=True,physical_device_verified=False,native_engine_recompiled=False)
    rec.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    conf=root/'scripts/infinity_background_resume.py';t=conf.read_text();t=once(t,'VERSION_CODE = 2103258','VERSION_CODE = 2103259');t=once(t,"RELEASE = '1.0.9-Glass-Settings-Light-Dark-RC1'","RELEASE = '1.0.9-Options-Health-Glass-Finish-RC1'");t=once(t,"BASE_APK_SHA256 = 'bc0ff18f0edf6c55eef7caa4582917738d0488c1ab58365f0669065d105867df'","BASE_APK_SHA256 = '"+BASE_APK+"'");conf.write_text(t)
    pack=root/'scripts/package_background_resume.py';t=pack.read_text().replace('Infinity-2103258-Glass-Settings-Light-Dark-RC1','Infinity-2103259-Options-Health-Glass-Finish-RC1').replace("'base_run':36302398518","'base_run':36304211423").replace("ROOT/'repairs/glass-settings-2103258/DEVICE-TEST.md'","ROOT/'repairs/options-health-2103259/DEVICE-TEST.md'").replace('Glass settings TEST CANDIDATE; exact 2103257','Options and Health TEST CANDIDATE; exact 2103258');pack.write_text(t)
    report=dict(parent_commit=PARENT,baseline_version=2103258,candidate_version=2103259,android_source_delta=changed,added=added,
        all_other_source_files_byte_identical=len(before)-len(changed),chooser_source_and_art_byte_identical=True,
        splash_patch_reversible=True,health_labels_and_callbacks_byte_identical=True,options_callback_and_lifecycle_byte_identical=True,
        diagnostic_collection_export_copy_unchanged=True,native_recompiled=False,startup_sound_integrated=False,device_verified=False)
    (out/'source-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'Splash-before.java.in').write_text(original);(out/'health-rows-and-actions.java.inc').write_text(arrays)
    for name,old,new in [('Splash',original,s),('InfinityGlassOptions',old_options,options.read_text())]:
        (out/(name+'.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='2103258/'+name,tofile='2103259/'+name)))
    for name,data in [('before',before),('after',after)]: (out/('source-hashes-'+name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
