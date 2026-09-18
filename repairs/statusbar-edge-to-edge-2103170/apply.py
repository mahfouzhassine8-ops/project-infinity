#!/usr/bin/env python3
"""2103170: restore true edge-to-edge status-bar ownership over locked 2103168 native baseline.

Physical Fold testing proved 2103169 still showed a black band behind status icons.
The prior repair correctly matched the app surface but left two window-level blockers:
  * 2103167 browse code actively forced NOT_FULLSCREEN and stripped layout-fullscreen.
  * transparent status bars still allowed the framework/OEM contrast scrim.

This patch returns browse mode to transparent edge-to-edge, keeps the 2103166 safe-area padding,
and disables only the status-bar contrast scrim. Fullscreen player/multiview remains unchanged.
"""
from pathlib import Path
import argparse,hashlib,json,re

REL=Path("tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in")
PREIMAGE="8797019d960d0861937d3a93ef4e93b94c3e9034179b429b7cd55d8cfb586831"
BASE_LOCK="3c2005cb62ae2115170a0aae1a8b22813ee7eeb9"

def sha_bytes(v):return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()

def matches(text,name):
    return list(re.finditer(
        r'^  (?:(?:@Override(?:[ \t]*\n  |[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'
        +re.escape(name)+r'\s*\(',text,re.M))

def span(text,name):
    ms=matches(text,name)
    if len(ms)!=1:raise RuntimeError(f"Method cardinality {name}={len(ms)}")
    start=ms[0].start();i=text.index("{",ms[0].end());d=0;q=None;esc=line=block=False
    while i<len(text):
        c=text[i];n=text[i+1] if i+1<len(text) else ""
        if line:
            if c=="\n":line=False
        elif block:
            if c=="*" and n=="/":block=False;i+=1
        elif q:
            if esc:esc=False
            elif c=="\\":esc=True
            elif c==q:q=None
        elif c=="/" and n=="/":line=True;i+=1
        elif c=="/" and n=="*":block=True;i+=1
        elif c in ('"',"'"):q=c
        elif c=="{":d+=1
        elif c=="}":
            d-=1
            if d==0:return start,i+1
        i+=1
    raise RuntimeError("Unclosed "+name)

def method(text,name):
    a,b=span(text,name);return text[a:b]

def replace_method(text,name,new):
    a,b=span(text,name);return text[:a]+new.rstrip()+text[b:]

def apply(source,receipt_path,out):
    receipt=json.loads(Path(receipt_path).read_text())
    if receipt.get("version_code")!=2103168:
        raise RuntimeError("Expected exact successful 2103168 status-surface source receipt")
    src=Path(source)/REL
    before_bytes=src.read_bytes();before=before_bytes.decode()
    if sha_bytes(before_bytes)!=PREIMAGE:
        raise RuntimeError("2103168 status-surface Activity preimage mismatch")

    protected=[
        "buildShell","cobraInstallBrowseSafeArea","cobraDarkIconsFor",
        "cobraBrowseSystemBarSurfaceColor",
        "onStart","onResume","onPause","onStop","onUserLeaveHint",
        "onPictureInPictureModeChanged","onNewIntent","onConfigurationChanged",
        "cobraConsumeLauncherPipReturn","onWindowFocusChanged",
        "cobraBuildPlayerChrome","openPlayerOverlay","showCobraPlayerDrawer",
        "showPlayerSettingsDrawer","showTrackChooser","lockCobraPlayer",
        "toggleCobraPlayerPlayPause","cobraPreviewPanel",
        "cobraStartOwnedMiniPlayback","cobraEndMiniBackgroundPlayback",
        "startCobraPlayer","pauseCobraForBackground",
        "clearStage","showSettings","showSources","showProfiles","showCobraHealthCenter",
        "showCobraPrimaryView","cobraShowGuideShell","showVodLibrary",
        "loadXtream","parseM3u","loadAllEnabledSources","filteredChannels","cobraDirectory",
    ]
    protected_before={n:sha_bytes(method(before,n)) for n in protected}

    oncreate=method(before,"onCreate")
    bars=method(before,"cobraApplySystemBarsForSurface")
    confirm=method(before,"cobraConfirmBrowseSystemBars")

    for token in (
        "window.addFlags(WindowManager.LayoutParams.FLAG_FORCE_NOT_FULLSCREEN)",
        "flags&=~(View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN|View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION)",
        "setStatusBarColor(fullscreen?Color.BLACK:Color.TRANSPARENT)",
        "mRoot.setBackgroundColor(barColor)",
    ):
        if token not in bars:raise RuntimeError("Expected 2103169 preimage token missing: "+token)
    for token in (
        "window.addFlags(WindowManager.LayoutParams.FLAG_FORCE_NOT_FULLSCREEN)",
        "|View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN",
        "setStatusBarColor(Color.TRANSPARENT)",
    ):
        if token not in confirm:raise RuntimeError("Expected confirmation preimage token missing: "+token)

    new_oncreate=oncreate.replace(
        "    requestWindowFeature(Window.FEATURE_NO_TITLE);",
        """    requestWindowFeature(Window.FEATURE_NO_TITLE);
    androidx.core.view.WindowCompat.setDecorFitsSystemWindows(getWindow(),false);
    getWindow().addFlags(WindowManager.LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS);
    getWindow().clearFlags(WindowManager.LayoutParams.FLAG_TRANSLUCENT_STATUS);
    if(Build.VERSION.SDK_INT>=29)getWindow().setStatusBarContrastEnforced(false);""",1)
    text=replace_method(before,"onCreate",new_oncreate)

    new_bars=bars
    new_bars=new_bars.replace(
        "android.view.Window window=getWindow();View decor=window.getDecorView();",
        """android.view.Window window=getWindow();View decor=window.getDecorView();
    if(Build.VERSION.SDK_INT>=29)window.setStatusBarContrastEnforced(false);""",
        1)
    new_bars=new_bars.replace(
        """    }else{
      window.clearFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);
      window.addFlags(WindowManager.LayoutParams.FLAG_FORCE_NOT_FULLSCREEN);
      flags&=~View.SYSTEM_UI_FLAG_FULLSCREEN;
      // Browse surfaces should never retain a legacy layout-fullscreen request. The shared
      // 2103166 root-insets listener owns the actual status/cutout safe area.
      flags&=~(View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN|View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION);
    }""",
        """    }else{
      // Browse must stay edge-to-edge. The root owns the status/cutout padding, while its
      // background continues behind the transparent system status bar.
      window.clearFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN
          |WindowManager.LayoutParams.FLAG_FORCE_NOT_FULLSCREEN);
      flags&=~View.SYSTEM_UI_FLAG_FULLSCREEN;
      flags|=View.SYSTEM_UI_FLAG_LAYOUT_STABLE|View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN;
      flags&=~View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION;
    }""",1)
    text=replace_method(text,"cobraApplySystemBarsForSurface",new_bars)

    new_confirm=confirm
    new_confirm=new_confirm.replace(
        "android.view.Window window=getWindow();View decor=window.getDecorView();",
        """android.view.Window window=getWindow();View decor=window.getDecorView();
    if(Build.VERSION.SDK_INT>=29)window.setStatusBarContrastEnforced(false);""",
        1)
    new_confirm=new_confirm.replace(
        """    window.clearFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);
    window.addFlags(WindowManager.LayoutParams.FLAG_FORCE_NOT_FULLSCREEN);""",
        """    window.clearFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN
        |WindowManager.LayoutParams.FLAG_FORCE_NOT_FULLSCREEN);""",1)
    new_confirm=new_confirm.replace(
        """    flags&=~(View.SYSTEM_UI_FLAG_FULLSCREEN
        |View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
        |View.SYSTEM_UI_FLAG_IMMERSIVE
        |View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
        |View.SYSTEM_UI_FLAG_LOW_PROFILE
        |View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
        |View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION);""",
        """    flags&=~(View.SYSTEM_UI_FLAG_FULLSCREEN
        |View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
        |View.SYSTEM_UI_FLAG_IMMERSIVE
        |View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
        |View.SYSTEM_UI_FLAG_LOW_PROFILE
        |View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION);
    flags|=View.SYSTEM_UI_FLAG_LAYOUT_STABLE|View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN;""",1)
    text=replace_method(text,"cobraConfirmBrowseSystemBars",new_confirm)

    for n,h in protected_before.items():
        if sha_bytes(method(text,n))!=h:raise RuntimeError("Protected method changed: "+n)

    after_oncreate=method(text,"onCreate")
    after_bars=method(text,"cobraApplySystemBarsForSurface")
    after_confirm=method(text,"cobraConfirmBrowseSystemBars")
    for token in (
        "WindowCompat.setDecorFitsSystemWindows(getWindow(),false)",
        "FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS",
        "FLAG_TRANSLUCENT_STATUS",
        "setStatusBarContrastEnforced(false)",
    ):
        if token not in after_oncreate:raise RuntimeError("2103170 one-time window setup missing: "+token)
    required=[
        "setStatusBarContrastEnforced(false)",
        "FLAG_FORCE_NOT_FULLSCREEN",
        "SYSTEM_UI_FLAG_LAYOUT_STABLE|View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN",
        "setStatusBarColor(fullscreen?Color.BLACK:Color.TRANSPARENT)",
        "mRoot.setBackgroundColor(barColor)",
    ]
    for token in required:
        if token not in after_bars:raise RuntimeError("2103170 browse edge-to-edge contract missing: "+token)
    for token in (
        "setStatusBarContrastEnforced(false)",
        "SYSTEM_UI_FLAG_LAYOUT_STABLE|View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN",
        "setStatusBarColor(Color.TRANSPARENT)",
    ):
        if token not in after_confirm:raise RuntimeError("2103170 confirmation contract missing: "+token)

    # FORCE_NOT_FULLSCREEN may only appear in clearFlags after this repair, never addFlags.
    if "addFlags(WindowManager.LayoutParams.FLAG_FORCE_NOT_FULLSCREEN)" in after_bars+after_confirm:
        raise RuntimeError("Browse still forces non-edge-to-edge status bar ownership")
    if "flags&=~(View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN" in after_bars:
        raise RuntimeError("Browse still strips layout-fullscreen underlay")

    after_bytes=text.encode();out=Path(out);out.mkdir(parents=True,exist_ok=True)
    (out/"source-before").mkdir(exist_ok=True)
    (out/"source-before"/src.name).write_bytes(before_bytes)
    src.write_bytes(after_bytes)
    proof={
        "base_locked_commit":BASE_LOCK,
        "base_version_code":2103168,
        "files":{str(REL):{"before":sha_bytes(before_bytes),"after":sha_bytes(after_bytes)}},
        "changed_methods":["onCreate","cobraApplySystemBarsForSurface","cobraConfirmBrowseSystemBars"],
        "new_helpers":[],
        "protected_methods":protected_before,
        "root_cause":[
          "2103167 forced FLAG_FORCE_NOT_FULLSCREEN and stripped LAYOUT_FULLSCREEN on browse",
          "transparent status bar left framework/OEM contrast protection enabled",
          "2103169 painted the correct root surface but did not remove those window-level blockers"
        ],
        "browse_window":"edge-to-edge transparent status bar; root paints underlay and owns insets",
        "status_bar_contrast_enforced":False,
        "safe_area_changed":False,
        "player_changed":False,
        "pip_changed":False,
        "native_changed":False,
        "physical_device_verified":False,
    }
    (out/"patch.json").write_text(json.dumps(proof,indent=2)+"\n")
    print("PASS: 2103170 restored browse edge-to-edge status-bar ownership; protected contracts untouched")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();apply(a.source,a.receipt,a.out)
