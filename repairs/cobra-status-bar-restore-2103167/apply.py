#!/usr/bin/env python3
"""2103167 micro-fix over the exact locked 2103166 baseline.

Physical Fold testing proved that the shared safe-area/layout is correct, but Samsung SystemUI can
still keep the real Android status bar hidden. This patch does not move any Cobra content. It only
hardens status-bar visibility ownership on ordinary Cobra surfaces and leaves fullscreen video /
Multi-View behavior unchanged.

The fix is deliberately redundant across the modern and legacy APIs because OEM SystemUI may carry
legacy fullscreen/immersive state across PiP/fullscreen transitions even when WindowInsetsController
is asked to show the status bar.
"""
from pathlib import Path
import argparse, hashlib, json, re

REL=Path("tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in")
BASE_LOCK="644160d0ca3baeebb6759638d3f40e2853eeed0b"

def sha_bytes(data):
    return hashlib.sha256(data if isinstance(data,bytes) else data.encode()).hexdigest()

def method_matches(text,name):
    return list(re.finditer(
        r'^  (?:(?:@Override(?:[ \t]*\n  |[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'
        +re.escape(name)+r'\s*\(',text,re.M))

def method_span(text,name):
    matches=method_matches(text,name)
    if len(matches)!=1: raise RuntimeError("Method cardinality %s = %d"%(name,len(matches)))
    start=matches[0].start();brace=text.index("{",matches[0].end())
    depth=0;quote=None;esc=False;line=False;block=False;i=brace
    while i<len(text):
        c=text[i];n=text[i+1] if i+1<len(text) else ""
        if line:
            if c=="\n":line=False
        elif block:
            if c=="*" and n=="/":block=False;i+=1
        elif quote:
            if esc:esc=False
            elif c=="\\":esc=True
            elif c==quote:quote=None
        elif c=="/" and n=="/":line=True;i+=1
        elif c=="/" and n=="*":block=True;i+=1
        elif c in ('"',"'"):quote=c
        elif c=="{":depth+=1
        elif c=="}":
            depth-=1
            if depth==0:return start,i+1
        i+=1
    raise RuntimeError("Unclosed method "+name)

def method_text(text,name):
    a,b=method_span(text,name);return text[a:b]

def replace_method(text,name,replacement):
    a,b=method_span(text,name);return text[:a]+replacement.rstrip()+text[b:]

def append_class(text,block):
    pos=text.rfind("\n}")
    if pos<0:raise RuntimeError("Class closing brace missing")
    return text[:pos]+"\n"+block.rstrip()+"\n"+text[pos:]

def apply(source,receipt_path,out):
    receipt=json.loads(Path(receipt_path).read_text())
    if receipt.get("version_code")!=2103166:
        raise RuntimeError("Expected exact locked 2103166 source receipt")
    src=Path(source)/REL
    before_bytes=src.read_bytes();before=before_bytes.decode()
    expected=receipt.get("files",{}).get(str(REL),{}).get("after")
    if not expected or sha_bytes(before_bytes)!=expected:
        raise RuntimeError("Locked 2103166 Activity identity mismatch")

    # 2103166 layout/safe-area, player, PiP, provider and background behavior are immutable here.
    protected=[
        "onCreate","buildShell","cobraInstallBrowseSafeArea","cobraDarkIconsFor",
        "onStart","onResume","onPause","onStop","onUserLeaveHint",
        "onPictureInPictureModeChanged","onNewIntent","onConfigurationChanged",
        "cobraConsumeLauncherPipReturn",
        "cobraBuildPlayerChrome","openPlayerOverlay","showCobraPlayerDrawer",
        "showPlayerSettingsDrawer","showTrackChooser","lockCobraPlayer",
        "toggleCobraPlayerPlayPause","cobraPreviewPanel",
        "cobraStartOwnedMiniPlayback","cobraEndMiniBackgroundPlayback",
        "startCobraPlayer","pauseCobraForBackground",
        "clearStage","showSettings","showSources","showProfiles","showCobraHealthCenter",
        "showCobraPrimaryView","cobraShowGuideShell","showVodLibrary",
        "loadXtream","parseM3u","loadAllEnabledSources","filteredChannels","cobraDirectory",
    ]
    protected_before={name:sha_bytes(method_text(before,name)) for name in protected}

    old=method_text(before,"cobraApplySystemBarsForSurface")
    focus_before=method_text(before,"onWindowFocusChanged")
    if "if(hasFocus)mMain.post(this::cobraApplySystemBarsForSurface);" not in focus_before:
        raise RuntimeError("Locked 2103166 focus-recovery preimage drift")
    for token in (
        "controller.show(android.view.WindowInsets.Type.statusBars())",
        "window.clearFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN)",
        "mRoot.requestApplyInsets()",
    ):
        if token not in old: raise RuntimeError("Locked 2103166 status-bar preimage drift: "+token)

    bars='''  private void cobraApplySystemBarsForSurface(){
    boolean fullscreen=!isCobraInPictureInPicture()&&(mPlayerOverlay!=null||mMultiOverlay!=null);
    android.view.Window window=getWindow();View decor=window.getDecorView();
    int barColor=fullscreen?Color.BLACK:cobraThemeColor("background",mTheme.background);
    boolean darkIcons=!fullscreen&&cobraDarkIconsFor(barColor);

    // Keep the navigation/gesture bar visible in all Cobra surfaces. Scrub any legacy immersive
    // state before the modern controller runs because Samsung SystemUI can otherwise carry that
    // state across PiP/fullscreen transitions.
    int flags=decor.getSystemUiVisibility();
    flags&=~(View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
        |View.SYSTEM_UI_FLAG_IMMERSIVE
        |View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
        |View.SYSTEM_UI_FLAG_LOW_PROFILE);
    if(fullscreen){
      window.clearFlags(WindowManager.LayoutParams.FLAG_FORCE_NOT_FULLSCREEN);
      window.addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);
      flags|=View.SYSTEM_UI_FLAG_FULLSCREEN;
    }else{
      window.clearFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);
      window.addFlags(WindowManager.LayoutParams.FLAG_FORCE_NOT_FULLSCREEN);
      flags&=~View.SYSTEM_UI_FLAG_FULLSCREEN;
      // Browse surfaces should never retain a legacy layout-fullscreen request. The shared
      // 2103166 root-insets listener owns the actual status/cutout safe area.
      flags&=~(View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN|View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION);
    }
    if(Build.VERSION.SDK_INT>=23){
      if(darkIcons)flags|=View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
      else flags&=~View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
    }
    if(Build.VERSION.SDK_INT>=26){
      if(darkIcons)flags|=View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
      else flags&=~View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
    }
    decor.setSystemUiVisibility(flags);

    window.setStatusBarColor(barColor);window.setNavigationBarColor(barColor);
    if(Build.VERSION.SDK_INT>=30){
      android.view.WindowInsetsController controller=window.getInsetsController();
      if(controller!=null){
        controller.setSystemBarsBehavior(android.view.WindowInsetsController.BEHAVIOR_DEFAULT);
        if(fullscreen)controller.hide(android.view.WindowInsets.Type.statusBars());
        else controller.show(android.view.WindowInsets.Type.statusBars());
        // Navigation bars remain visible by contract.
        controller.show(android.view.WindowInsets.Type.navigationBars());
        int mask=android.view.WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS
            |android.view.WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS;
        controller.setSystemBarsAppearance(darkIcons?mask:0,mask);
      }
    }

    decor.requestApplyInsets();decor.requestLayout();
    if(mRoot!=null){mRoot.requestApplyInsets();mRoot.requestLayout();}
    if(!fullscreen)decor.postOnAnimation(this::cobraConfirmBrowseSystemBars);
  }'''

    text=replace_method(before,"cobraApplySystemBarsForSurface",bars)

    focus='''  @Override public void onWindowFocusChanged(boolean hasFocus){
    super.onWindowFocusChanged(hasFocus);
    if(hasFocus){
      // Apply synchronously so an OEM focus handoff cannot leave one frame in stale fullscreen,
      // then apply once more after queued window work settles.
      cobraApplySystemBarsForSurface();
      mMain.post(this::cobraApplySystemBarsForSurface);
    }
  }'''
    text=replace_method(text,"onWindowFocusChanged",focus)

    confirm=r'''
  private void cobraConfirmBrowseSystemBars(){
    if(isFinishing()||isDestroyed()||isCobraInPictureInPicture()
        ||mPlayerOverlay!=null||mMultiOverlay!=null)return;
    android.view.Window window=getWindow();View decor=window.getDecorView();
    window.clearFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);
    window.addFlags(WindowManager.LayoutParams.FLAG_FORCE_NOT_FULLSCREEN);
    int flags=decor.getSystemUiVisibility();
    flags&=~(View.SYSTEM_UI_FLAG_FULLSCREEN
        |View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
        |View.SYSTEM_UI_FLAG_IMMERSIVE
        |View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
        |View.SYSTEM_UI_FLAG_LOW_PROFILE
        |View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
        |View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION);
    int barColor=cobraThemeColor("background",mTheme.background);
    boolean darkIcons=cobraDarkIconsFor(barColor);
    if(Build.VERSION.SDK_INT>=23){
      if(darkIcons)flags|=View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
      else flags&=~View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
    }
    if(Build.VERSION.SDK_INT>=26){
      if(darkIcons)flags|=View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
      else flags&=~View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
    }
    decor.setSystemUiVisibility(flags);
    window.setStatusBarColor(barColor);window.setNavigationBarColor(barColor);
    if(Build.VERSION.SDK_INT>=30){
      android.view.WindowInsetsController controller=window.getInsetsController();
      if(controller!=null){
        controller.setSystemBarsBehavior(android.view.WindowInsetsController.BEHAVIOR_DEFAULT);
        controller.show(android.view.WindowInsets.Type.statusBars()
            |android.view.WindowInsets.Type.navigationBars());
        int mask=android.view.WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS
            |android.view.WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS;
        controller.setSystemBarsAppearance(darkIcons?mask:0,mask);
      }
    }
    decor.requestApplyInsets();decor.requestLayout();
    if(mRoot!=null){mRoot.requestApplyInsets();mRoot.requestLayout();}
  }
'''
    if method_matches(text,"cobraConfirmBrowseSystemBars"):
        raise RuntimeError("2103167 helper name collision")
    text=append_class(text,confirm)

    # Nothing except status-bar ownership may move.
    for name,expected_hash in protected_before.items():
        actual=sha_bytes(method_text(text,name))
        if actual!=expected_hash:raise RuntimeError("Protected 2103166 method changed: "+name)

    after=method_text(text,"cobraApplySystemBarsForSurface")
    helper=method_text(text,"cobraConfirmBrowseSystemBars")
    required=[
        "FLAG_FORCE_NOT_FULLSCREEN",
        "SYSTEM_UI_FLAG_IMMERSIVE_STICKY",
        "SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN",
        "BEHAVIOR_DEFAULT",
        "controller.show(android.view.WindowInsets.Type.statusBars())",
        "controller.show(android.view.WindowInsets.Type.navigationBars())",
        "postOnAnimation(this::cobraConfirmBrowseSystemBars)",
    ]
    for token in required:
        if token not in after:raise RuntimeError("2103167 compiled contract missing: "+token)
    for token in ("FLAG_FORCE_NOT_FULLSCREEN","statusBars()","navigationBars()","SYSTEM_UI_FLAG_IMMERSIVE_STICKY"):
        if token not in helper:raise RuntimeError("2103167 confirmation helper missing: "+token)

    after_bytes=text.encode()
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    (out/"source-before").mkdir(exist_ok=True)
    (out/"source-before"/src.name).write_bytes(before_bytes)
    src.write_bytes(after_bytes)
    proof={
        "base_locked_commit":BASE_LOCK,
        "base_version_code":2103166,
        "files":{str(REL):{"before":sha_bytes(before_bytes),"after":sha_bytes(after_bytes)}},
        "changed_methods":["cobraApplySystemBarsForSurface","onWindowFocusChanged"],
        "new_helpers":["cobraConfirmBrowseSystemBars"],
        "protected_methods":protected_before,
        "browse_status_bar":"forced visible + legacy immersive scrub + next-frame confirmation",
        "fullscreen_status_bar":"hidden only for player/multiview",
        "navigation_bar":"always visible",
        "layout_changed":False,
        "native_changed":False,
        "physical_device_verified":False,
    }
    (out/"patch.json").write_text(json.dumps(proof,indent=2)+"\n")
    print("PASS: locked 2103166 -> 2103167 status-bar micro-fix; layout/player/PiP contracts unchanged")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();apply(a.source,a.receipt,a.out)
