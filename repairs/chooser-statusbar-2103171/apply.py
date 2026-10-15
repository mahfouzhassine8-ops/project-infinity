#!/usr/bin/env python3
"""2103171: chooser-only status-bar surface repair over exact passed 2103170.

Scope:
- Splash / Choose Your Experience only.
- Transparent edge-to-edge status bar with theme-colored underlay.
- Light/dark status-icon contrast from resolved chooser palette.
- Stable safe-area inset handling including transient-zero SystemUI handoffs.
- Legacy chooser routing, Cobra/Infinity launch behavior, Kodi/native engine untouched.
"""
from pathlib import Path
import argparse,hashlib,json,re

REL=Path("tools/android/packaging/xbmc/src/Splash.java.in")
BASE_BUILD=2103170
BASE_COMMIT="6046c0ac64c7ef83a65550d53ffd4211c6cb5bef"

def sha(v): return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()

def matches(text,name):
    return list(re.finditer(
        r'^  (?:(?:@Override(?:[ \t]*\n  |[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'
        +re.escape(name)+r'\s*\(',text,re.M))

def span(text,name):
    ms=matches(text,name)
    if len(ms)!=1: raise RuntimeError(f"Method cardinality {name}={len(ms)}")
    start=ms[0].start();i=text.index("{",ms[0].end());depth=0;quote=None;escape=line=block=False
    while i<len(text):
        c=text[i];n=text[i+1] if i+1<len(text) else ""
        if line:
            if c=="\n":line=False
        elif block:
            if c=="*" and n=="/":block=False;i+=1
        elif quote:
            if escape:escape=False
            elif c=="\\":escape=True
            elif c==quote:quote=None
        elif c=="/" and n=="/":line=True;i+=1
        elif c=="/" and n=="*":block=True;i+=1
        elif c in ('"',"'"):quote=c
        elif c=="{":depth+=1
        elif c=="}":
            depth-=1
            if depth==0:return start,i+1
        i+=1
    raise RuntimeError("Unclosed "+name)

def method(text,name):
    a,b=span(text,name);return text[a:b]

def replace_method(text,name,new):
    a,b=span(text,name);return text[:a]+new.rstrip()+"\n"+text[b:]

def once(text,old,new,label):
    if text.count(old)!=1:raise RuntimeError(f"{label}: expected one anchor, got {text.count(old)}")
    return text.replace(old,new,1)

HELPER=r'''  private void cobraPrepareExperienceSystemBars(ExperienceTheme theme, android.widget.FrameLayout root){
    if(theme==null||root==null)return;
    android.view.Window window=getWindow();View decor=window.getDecorView();

    // Scope edge-to-edge to the chooser Activity only. The launched Infinity/Cobra Activity
    // owns its own status-bar policy after this Activity leaves the foreground.
    androidx.core.view.WindowCompat.setDecorFitsSystemWindows(window,false);
    window.addFlags(android.view.WindowManager.LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS);
    window.clearFlags(android.view.WindowManager.LayoutParams.FLAG_TRANSLUCENT_STATUS
        |android.view.WindowManager.LayoutParams.FLAG_FULLSCREEN
        |android.view.WindowManager.LayoutParams.FLAG_FORCE_NOT_FULLSCREEN);
    window.setStatusBarColor(android.graphics.Color.TRANSPARENT);
    if(Build.VERSION.SDK_INT>=29)window.setStatusBarContrastEnforced(false);

    // If root padding exposes any band while the scene/background child is inset,
    // the decor underlay is the exact resolved chooser background instead of black.
    decor.setBackgroundColor(theme.background);

    int flags=decor.getSystemUiVisibility();
    flags&=~View.SYSTEM_UI_FLAG_FULLSCREEN;
    flags|=View.SYSTEM_UI_FLAG_LAYOUT_STABLE|View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN;
    boolean darkIcons=cobraChooserDarkStatusIcons(theme.background);
    if(Build.VERSION.SDK_INT>=23&&Build.VERSION.SDK_INT<30){
      if(darkIcons)flags|=View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
      else flags&=~View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
    }
    decor.setSystemUiVisibility(flags);

    if(Build.VERSION.SDK_INT>=30){
      android.view.WindowInsetsController controller=window.getInsetsController();
      if(controller!=null){
        controller.show(android.view.WindowInsets.Type.statusBars());
        controller.setSystemBarsAppearance(
            darkIcons?android.view.WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS:0,
            android.view.WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS);
      }
    }

    final int[] stableVerticalInsets=new int[]{0,0};
    root.setOnApplyWindowInsetsListener((v,insets)->{
      int left=0,top=0,right=0,bottom=0;
      if(Build.VERSION.SDK_INT>=30){
        android.graphics.Insets bars=insets.getInsets(android.view.WindowInsets.Type.systemBars());
        android.graphics.Insets cut=insets.getInsets(android.view.WindowInsets.Type.displayCutout());
        left=Math.max(bars.left,cut.left);top=Math.max(bars.top,cut.top);
        right=Math.max(bars.right,cut.right);bottom=Math.max(bars.bottom,cut.bottom);
      }else{
        left=insets.getSystemWindowInsetLeft();top=insets.getSystemWindowInsetTop();
        right=insets.getSystemWindowInsetRight();bottom=insets.getSystemWindowInsetBottom();
        if(Build.VERSION.SDK_INT>=28&&insets.getDisplayCutout()!=null){
          android.view.DisplayCutout cut=insets.getDisplayCutout();
          left=Math.max(left,cut.getSafeInsetLeft());top=Math.max(top,cut.getSafeInsetTop());
          right=Math.max(right,cut.getSafeInsetRight());bottom=Math.max(bottom,cut.getSafeInsetBottom());
        }
      }
      // Samsung/SystemUI may briefly report zero while handing off fullscreen/PiP/Fold state.
      // Keep the last non-zero vertical chooser safe area until a real replacement arrives.
      if(top>0)stableVerticalInsets[0]=top;else if(stableVerticalInsets[0]>0)top=stableVerticalInsets[0];
      if(bottom>0)stableVerticalInsets[1]=bottom;else if(stableVerticalInsets[1]>0)bottom=stableVerticalInsets[1];
      if(v.getPaddingLeft()!=left||v.getPaddingTop()!=top||v.getPaddingRight()!=right||v.getPaddingBottom()!=bottom)
        v.setPadding(left,top,right,bottom);
      return insets;
    });
    root.requestApplyInsets();
  }

  private boolean cobraChooserDarkStatusIcons(int background){
    int r=android.graphics.Color.red(background),g=android.graphics.Color.green(background),b=android.graphics.Color.blue(background);
    return r*299+g*587+b*114>=186000;
  }'''

def apply(source,receipt_path,out):
    source=Path(source);receipt_path=Path(receipt_path);out=Path(out)
    receipt=json.loads(receipt_path.read_text())
    if receipt.get("version_code")!=BASE_BUILD:
        raise RuntimeError("Expected exact passed 2103170 source receipt")
    expected=receipt.get("files",{}).get(str(REL),{}).get("after")
    if not expected:raise RuntimeError("Splash identity missing from 2103170 source receipt")

    path=source/REL;before_bytes=path.read_bytes();before=before_bytes.decode()
    if sha(before_bytes)!=expected:raise RuntimeError("2103170 Splash preimage mismatch")

    protected=[
      "onCreate","startXBMC","showExperienceCardSettings","launchInfinityExperience",
      "showInfinityExperienceChooser","showLegacyInfinityExperienceChooser",
      "loadExperienceTheme","chooserExperienceCard","resolveVisualExperienceTheme"
    ]
    protected_before={n:sha(method(before,n)) for n in protected}

    scene=method(before,"showVisualExperienceScene")
    styled=method(before,"showStyledInfinityExperienceChooser")
    old_listener='''      root.setOnApplyWindowInsetsListener((v,insets)->{int left=insets.getSystemWindowInsetLeft(),top=insets.getSystemWindowInsetTop(),right=insets.getSystemWindowInsetRight(),bottom=insets.getSystemWindowInsetBottom();if(v.getPaddingLeft()!=left||v.getPaddingTop()!=top||v.getPaddingRight()!=right||v.getPaddingBottom()!=bottom)v.setPadding(left,top,right,bottom);return insets;});
      setContentView(root);root.requestApplyInsets();slots.get("enter.infinity").requestFocus();'''
    new_scene='''      setContentView(root);cobraPrepareExperienceSystemBars(theme,root);slots.get("enter.infinity").requestFocus();'''
    if scene.count(old_listener)!=1:raise RuntimeError("2103161 chooser safe-area preimage drift")
    scene=scene.replace(old_listener,new_scene,1)
    text=replace_method(before,"showVisualExperienceScene",scene)

    styled=method(text,"showStyledInfinityExperienceChooser")
    styled=once(styled,
        "    setContentView(root);\n    infinity.requestFocus();",
        "    setContentView(root);cobraPrepareExperienceSystemBars(theme,root);\n    infinity.requestFocus();",
        "styled chooser status-bar hook")
    text=replace_method(text,"showStyledInfinityExperienceChooser",styled)

    if "private void cobraPrepareExperienceSystemBars" in text:raise RuntimeError("Chooser status helper already exists")
    pos=text.rfind("\n}")
    if pos<0:raise RuntimeError("Splash class terminator missing")
    text=text[:pos]+"\n"+HELPER+"\n"+text[pos:]

    for n,h in protected_before.items():
        if sha(method(text,n))!=h:raise RuntimeError("Protected chooser behavior changed: "+n)

    scene_after=method(text,"showVisualExperienceScene")
    styled_after=method(text,"showStyledInfinityExperienceChooser")
    helper=method(text,"cobraPrepareExperienceSystemBars")
    icon=method(text,"cobraChooserDarkStatusIcons")
    for block in (scene_after,styled_after):
        if "cobraPrepareExperienceSystemBars(theme,root)" not in block:
            raise RuntimeError("Chooser path missing system-bar preparation")
    for token in (
      "WindowCompat.setDecorFitsSystemWindows(window,false)",
      "setStatusBarColor(android.graphics.Color.TRANSPARENT)",
      "setStatusBarContrastEnforced(false)",
      "decor.setBackgroundColor(theme.background)",
      "SYSTEM_UI_FLAG_LAYOUT_STABLE|View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN",
      "controller.show(android.view.WindowInsets.Type.statusBars())",
      "APPEARANCE_LIGHT_STATUS_BARS",
      "stableVerticalInsets",
      "WindowInsets.Type.displayCutout()",
    ):
        if token not in helper:raise RuntimeError("Chooser system-bar contract missing: "+token)
    if "setNavigationBarColor" in helper or "navigationBars()" in helper:
        raise RuntimeError("Chooser repair must not take navigation-bar ownership")
    if "setContentView(" in helper or "startActivity(" in helper:
        raise RuntimeError("Chooser system-bar helper must not own routing/content")
    if "186000" not in icon:raise RuntimeError("Chooser icon contrast threshold missing")

    out.mkdir(parents=True,exist_ok=True);(out/"source-before").mkdir(exist_ok=True)
    (out/"source-before"/path.name).write_bytes(before_bytes)
    after=text.encode();path.write_bytes(after)
    report={
      "base_build":BASE_BUILD,"base_commit":BASE_COMMIT,
      "files":{str(REL):{"before":sha(before_bytes),"after":sha(after)}},
      "changed_methods":["showVisualExperienceScene","showStyledInfinityExperienceChooser"],
      "new_helpers":["cobraPrepareExperienceSystemBars","cobraChooserDarkStatusIcons"],
      "protected_methods":protected_before,
      "status_bar_transparent":True,"status_bar_underlay":"resolved chooser background",
      "status_icon_contrast":"resolved chooser background luminance",
      "safe_area_transient_zero_stabilized":True,
      "navigation_bar_changed":False,"chooser_routing_changed":False,
      "activity_changed":False,"native_changed":False,"physical_device_verified":False
    }
    (out/"patch.json").write_text(json.dumps(report,indent=2)+"\n")
    print("PASS: exact 2103170 -> chooser-only 2103171 system-bar surface delta")

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--source",type=Path,required=True);p.add_argument("--receipt",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();apply(a.source,a.receipt,a.out)
