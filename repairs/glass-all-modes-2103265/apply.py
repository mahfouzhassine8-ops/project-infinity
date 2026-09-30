#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,sys,tarfile
from java_members import span
A='tools/android/packaging/xbmc/'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def once(s,a,b):
    assert s.count(a)==1,(s.count(a),a[:100]);return s.replace(a,b,1)
def replace_member(s,name,new):
    a,b=span(s,name);return s[:a]+'  '+new.strip()+s[b:]
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'));p.add_argument('--evidence',type=Path,default=Path('audit265'));args=p.parse_args()
    root=args.root.resolve();ev=args.evidence.resolve();ev.mkdir(parents=True,exist_ok=True);src=root/'shell-kodi';here=Path(__file__).resolve().parent
    before={str(f.relative_to(src)):sha(f) for f in src.rglob('*') if f.is_file()}
    assert before==json.loads((root/'source264/source-hashes-after.json').read_text()),'Source must match 2103264 exactly'
    live=src/(A+'src/InfinityLiveActivity.java.in');old=live.read_text();s=old
    s=replace_member(s,'cobraModeSurface','''  private android.graphics.drawable.Drawable cobraModeSurface(int radius,boolean raised){
    return CobraVisualRenderer.phoneGlass(this,!cobraModeDark(),radius,raised);
  }''')
    a,b=span(s,'toggleCobraDrawer');part=s[a:b];part=once(part,'panel.setBackgroundColor(cobraModeColor("rail"));','panel.setBackground(CobraVisualRenderer.phoneGlass(this,!dark,22,true));');s=s[:a]+part+s[b:]
    s=once(s,'library.setBackground(surface(cobraModeColor("panel"),18,cobraModeColor("line"),1));','library.setBackground(CobraVisualRenderer.phoneGlass(this,!dark,18,true));')
    s=once(s,'power.setBackground(surface(cobraModeColor("panel"),18,cobraModeColor("line"),1));','power.setBackground(CobraVisualRenderer.phoneGlass(this,!dark,18,true));')
    a,b=span(s,'cobraPolishDrawerRow');part=s[a:b];start=part.index('    android.graphics.drawable.StateListDrawable');end=part.index('    TextView next=',start)
    part=part[:start]+'    row.setBackground(CobraVisualRenderer.phoneGlass(this,!cobraModeDark(),14,!grouped));\n'+part[end:];s=s[:a]+part+s[b:]
    s=once(s,'    cobraPolishDrawerRow(parent,row);','    row.setSelected(destination.equalsIgnoreCase(cobraDrawerOwner()));\n    cobraPolishDrawerRow(parent,row);')
    s=once(s,'close.requestFocus();vtheme().tree(panel,"sheet."+kind);return items;','if("view-mode".equals(kind))panel.setBackground(CobraVisualRenderer.phoneGlass(this,!dark,22,true));\n    close.requestFocus();vtheme().tree(panel,"sheet."+kind);return items;')
    # Guide chrome only. Do not apply glass fills over the video or Pro hero.
    s=once(s,'if("focus".equals(mCobraGuideStyle)&&mCobraProActive)cobraStyleProShell();','''if("focus".equals(mCobraGuideStyle)&&mCobraProActive)cobraStyleProShell();
    else{
      for(View panel:new View[]{mCobraModeToolbar,mCobraModeRail,mCobraModeFooter,mCobraGuideDirectory,mCobraGuideDetails})
        if(panel!=null)panel.setBackground(CobraVisualRenderer.phoneGlass(this,!cobraModeDark(),"grid".equals(mCobraGuideStyle)?6:16,true));
    }''')
    s=once(s,'tabs.setBackground(surface(cobraModeColor("panel"),16,vtheme().color("cobra.cobraModeFilters.colors.1",Color.TRANSPARENT),0));','tabs.setBackground(CobraVisualRenderer.phoneGlass(this,!cobraModeDark(),16,true));')
    a,b=span(s,'cobraRenderGuideBrowser');part=s[a:b]
    part=once(part,'mCobraGuideBrowser.setAlpha(.62f);mCobraGuideBrowser.setTranslationY(dp(7));mCobraGuideBrowser.animate().alpha(1f).translationY(0f).setDuration(vtheme().motion("cobra.cobraRenderGuideBrowser.numbers.1",190)).setInterpolator(new android.view.animation.DecelerateInterpolator()).start();mCobraRenderedMode=mCobraGuideStyle;',
      'cobraResetMotion(mCobraGuideBrowser);if(cobraMotionEnabled()){mCobraGuideBrowser.setAlpha(.65f);mCobraGuideBrowser.animate().alpha(1f).setDuration(180L).setInterpolator(new android.view.animation.PathInterpolator(.2f,0f,0f,1f)).start();}mCobraRenderedMode=mCobraGuideStyle;')
    s=s[:a]+part+s[b:]
    # Existing callbacks, clip/hit rectangles, and navigation timing stay unchanged.
    s=once(s,'panel.setTranslationX(-width);panel.setAlpha(.90f);panel.setScaleX(.99f);panel.setScaleY(.99f);panel.animate().translationX(0).alpha(1f).scaleX(1f).scaleY(1f).setDuration(vtheme().motion("cobra.toggleCobraDrawer.numbers.1",210)).setInterpolator(new android.view.animation.DecelerateInterpolator()).start();', 'panel.setTranslationX(cobraMotionEnabled()?-width:0);panel.setAlpha(cobraMotionEnabled()?.82f:1f);panel.animate().translationX(0).alpha(1f).setDuration(cobraMotionEnabled()?240L:0L).setInterpolator(new android.view.animation.PathInterpolator(.2f,0f,0f,1f)).start();')
    # Controls have glass in guide contexts; Pro keeps its current custom surfaces.
    s=once(s,'vtheme().paint(b,"widget.cobraTextButton");return b;', 'if(!"focus".equals(mCobraGuideStyle)&&mCobraGuideShell!=null)b.setBackground(CobraVisualRenderer.phoneGlass(this,!dark,12,false));vtheme().paint(b,"widget.cobraTextButton");return b;')
    s=once(s,'button.setOnClickListener(click);cobraPolishFocusable(button);return button;', 'button.setOnClickListener(click);cobraPolishFocusable(button);if(!"focus".equals(mCobraGuideStyle)&&mCobraGuideShell!=null)button.setBackground(CobraVisualRenderer.phoneGlass(this,!dark,12,false));return button;')
    live.write_text(s);(ev/'InfinityLiveActivity-before.java.in').write_text(old)
    pro=src/(A+'src/CobraProUi.java.in');s=pro.read_text()
    s=once(s,'  static int px(Context c,float dp)', '''  static boolean owns(View view){
    for(int depth=0;view!=null&&depth<24;depth++){
      if(view instanceof Ink||view instanceof Hero||view instanceof Details||view instanceof Filters||view instanceof ChannelRow||view instanceof Action)return true;
      view=view.getParent() instanceof View?(View)view.getParent():null;
    }return false;
  }
  static int px(Context c,float dp)''')
    # LIVE must have its own complete text geometry even if a parent was themed before attach.
    s=once(s,'live.setBackground(liveBg);addView(live);','live.setBackground(liveBg);live.setTag("cobra_pro_live");live.text("LIVE");addView(live);')
    pro.write_text(s)
    renderer=src/(A+'src/CobraVisualRenderer.java.in');s=renderer.read_text()
    s=once(s,'    if(view==null||(view.getTag()', '    if(view==null||CobraProUi.owns(view)||(view.getTag()')
    s=once(s,'    if(view==null||depth>24', '    if(view==null||CobraProUi.owns(view)||depth>24')
    s=once(s,'void apply(View view,Binding base){JSONObject s=stylesFor(base,view);if(s.length()==0)return;', 'void apply(View view,Binding base){JSONObject s=stylesFor(base,view);if(s.length()==0)return;')
    s=once(s,'  static int parseColor(JSONObject s', '''  static int parseColor(JSONObject s''')
    # Renderer may update text and geometry, but must retain the stateful glass finish.
    s=once(s,'    if(view instanceof TextView){TextView tv=(TextView)view;if(s.has("text"))', '    if(base.background instanceof Glass)view.setBackground(base.background);\n    if(view instanceof TextView){TextView tv=(TextView)view;if(s.has("text"))')
    s=s.rstrip()[:-1]+ '\n'+(here/'glass.java.inc').read_text()+'\n}\n';renderer.write_text(s)
    gradle=src/(A+'build.gradle.in');gradle.write_text(gradle.read_text().replace('2103264','2103265').replace('Pro-LIVE-Glass-RC1','Phone-Glass-Polish-RC1'))
    after={str(f.relative_to(src)):sha(f) for f in src.rglob('*') if f.is_file()};changed=sorted(k for k in before if before[k]!=after[k]);assert set(before)==set(after)
    allowed=[A+'src/'+f+'.java.in' for f in ['InfinityLiveActivity','CobraProUi','CobraVisualRenderer']]+[A+'build.gradle.in'];assert changed==sorted(allowed),changed
    # Preserve every Activity member except this explicit presentation allowlist.
    import re
    names=re.findall(r'(?m)^  private[^\n{;=]*?\b(\w+)\s*\(',old)
    modified=[]
    for name in set(names):
      try:
        a,b=span(old,name);c,d=span(live.read_text(),name)
        if old[a:b]!=live.read_text()[c:d]:modified.append(name)
      except AssertionError:pass
    assert set(modified)<=set(['cobraModeSurface','toggleCobraDrawer','cobraPolishDrawerRow','cobraDrawerDestination','cobraOpenSheet','cobraRestyleGuide','cobraModeFilters','cobraRenderGuideBrowser','cobraTextButton','cobraIcon']),modified
    receiptpath=root/'engine/background-resume-source.json';receipt=json.loads(receiptpath.read_text())
    for name in changed:receipt['files'][name]={'before':before[name],'after':after[name]}
    receipt.update(version_code=2103265,version_name='1.0.9-Phone-Glass-Polish-RC1',source_parent=2103264,native_engine_recompiled=False,physical_device_verified=False);receiptpath.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    archive=tarfile.open(root/'source264/reconstructed-2103264-shell.tar.gz')
    cfg=root/'scripts/infinity_background_resume.py';s=archive.extractfile('scripts/infinity_background_resume.py').read().decode().replace('VERSION_CODE = 2103264','VERSION_CODE = 2103265').replace('Pro-LIVE-Glass-RC1','Phone-Glass-Polish-RC1')
    parent=json.loads((root/'parent264/background-resume-apk-audit.json').read_text())['apk_sha256'];s=re.sub(r"BASE_APK_SHA256 = '[0-9a-f]+'", "BASE_APK_SHA256 = '"+parent+"'",s);cfg.write_text(s)
    pack=root/'scripts/package_background_resume.py';pack.write_text(archive.extractfile('scripts/package_background_resume.py').read().decode().replace('Infinity-2103264-Pro-LIVE-Glass-RC1','Infinity-2103265-Phone-Glass-Polish-RC1').replace("'base_run':36662814776","'base_run':36666385684").replace("ROOT/'repairs/pro-live-2103264/DEVICE-TEST.md'","ROOT/'repairs/glass-all-modes-2103265/DEVICE-TEST.md'"))
    result=dict(candidate_version=2103265,parent_version=2103264,changed=changed,presentation_members=sorted(modified),protected_activity_members=len(set(names))-len(modified),other_shell_files_byte_identical=len(before)-len(changed),native_engine_recompiled=False,physical_device_verified=False,stable_lock=False)
    (ev/'source-verification.json').write_text(json.dumps(result,indent=2)+'\n');(ev/'source-hashes-after.json').write_text(json.dumps(after,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
