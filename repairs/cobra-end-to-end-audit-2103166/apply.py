#!/usr/bin/env python3
"""2103166 end-to-end Cobra presentation/lifecycle audit over the locked 2103165 baseline.

The fix is intentionally structural rather than screen-by-screen: every ordinary Cobra surface
shares one browse root, so that root becomes the single owner of system-bar/cutout safe insets.
Fullscreen video and Multi-View remain decor-level surfaces and keep the locked 2103165
fullscreen/PiP behavior.

No provider, EPG, player, media-session, background-playback, theme payload, native engine,
signer, or user-data contract is redesigned here.
"""
from pathlib import Path
import argparse, hashlib, json, re

ROOT=Path(__file__).resolve().parent
REL=Path("tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in")
BASE_LOCK="6148e34be3024c5939c736a7b4316572d7bd50c0"

def sha_bytes(data):
    return hashlib.sha256(data if isinstance(data,bytes) else data.encode()).hexdigest()

def once(text,old,new):
    count=text.count(old)
    if count!=1: raise RuntimeError("Exact anchor drift (%d): %r"%(count,old[:180]))
    return text.replace(old,new,1)

def method_matches(text,name):
    return list(re.finditer(
        r'^  (?:(?:@Override(?:[ \t]*\n  |[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'
        +re.escape(name)+r'\s*\(',text,re.M))

def method_span(text,name):
    matches=method_matches(text,name)
    if len(matches)!=1: raise RuntimeError("Method cardinality %s = %d"%(name,len(matches)))
    start=matches[0].start();brace=text.index("{",matches[0].end())
    depth=0;quote=None;escape=False;line=False;block=False;i=brace
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
    raise RuntimeError("Unclosed method "+name)

def method_text(text,name):
    a,b=method_span(text,name);return text[a:b]

def replace_method(text,name,replacement):
    a,b=method_span(text,name);return text[:a]+replacement.rstrip()+text[b:]

def edit_method(text,name,old,new):
    a,b=method_span(text,name);return text[:a]+once(text[a:b],old,new)+text[b:]

def append_class(text,block):
    pos=text.rfind("\n}")
    if pos<0:raise RuntimeError("Class closing brace missing")
    return text[:pos]+"\n"+block.rstrip()+"\n"+text[pos:]

def collect_hashes(text,names):
    return {name:sha_bytes(method_text(text,name)) for name in names}

def apply(source,receipt_path,out):
    receipt=json.loads(Path(receipt_path).read_text())
    if receipt.get("version_code")!=2103165:
        raise RuntimeError("Expected exact locked 2103165 source receipt")
    src=Path(source)/REL
    before_bytes=src.read_bytes()
    expected=receipt.get("files",{}).get(str(REL),{}).get("after")
    if not expected or sha_bytes(before_bytes)!=expected:
        raise RuntimeError("Locked 2103165 Activity identity mismatch")
    before=before_bytes.decode()

    # End-to-end protection: these are the working contracts this audit is forbidden to rewrite.
    protected=[
        # Approved player / preview presentation.
        "cobraBuildPlayerChrome","showCobraPlayerDrawer","showPlayerSettingsDrawer",
        "showTrackChooser","lockCobraPlayer","toggleCobraPlayerPlayPause","cobraPreviewPanel",
        # 2103165 PiP / lifecycle ownership.
        "onStart","onResume","onPause","onStop","onUserLeaveHint",
        "onPictureInPictureModeChanged","onNewIntent","onConfigurationChanged",
        "cobraConsumeLauncherPipReturn",
        # Playback/background ownership.
        "cobraStartOwnedMiniPlayback","cobraEndMiniBackgroundPlayback","startCobraPlayer",
        "pauseCobraForBackground",
        # Primary navigation and internal screens.
        "clearStage","showSettings","showSources","showProfiles","showCobraHealthCenter",
        "showCobraPrimaryView","cobraShowGuideShell","showVodLibrary",
        # Provider/catalogue/EPG filtering.
        "loadXtream","parseM3u","loadAllEnabledSources","filteredChannels","cobraDirectory",
    ]
    protected_before=collect_hashes(before,protected)

    # Source-level topology audit before editing.
    if before.count("setContentView(")!=1 or "setContentView(frame);" not in method_text(before,"buildShell"):
        raise RuntimeError("Browse content topology drift: expected one Activity content root")
    on_create=method_text(before,"onCreate")
    if re.search(r'\\b(?:setFlags|addFlags)\\s*\\([^;]*FLAG_FULLSCREEN',on_create,re.S):
        raise RuntimeError("Locked 2103165 unexpectedly regained global fullscreen ownership")
    if "clearFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN)" not in on_create:
        raise RuntimeError("Locked 2103165 browse-mode fullscreen clear is missing")

    text=before

    # Every ordinary screen is a descendant of mRoot. Install one idempotent safe-area listener
    # there instead of accumulating per-screen margins/padding.
    text=edit_method(
        text,"buildShell","    setContentView(frame);",
        "    cobraInstallBrowseSafeArea(mRoot);\n"
        "    setContentView(frame);\n"
        "    mRoot.requestApplyInsets();"
    )

    # Keep the locked surface ownership, but make bar appearance deterministic after Android
    # edge-to-edge enforcement: browse = theme bar + correct icon contrast; player = black bar.
    bars='''  private void cobraApplySystemBarsForSurface(){
    boolean fullscreen=!isCobraInPictureInPicture()&&(mPlayerOverlay!=null||mMultiOverlay!=null);
    android.view.Window window=getWindow();
    int barColor=fullscreen?Color.BLACK:cobraThemeColor("background",mTheme.background);
    boolean darkIcons=!fullscreen&&cobraDarkIconsFor(barColor);
    if(fullscreen)window.addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);
    else window.clearFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);
    window.setStatusBarColor(barColor);window.setNavigationBarColor(barColor);
    if(Build.VERSION.SDK_INT>=30){
      android.view.WindowInsetsController controller=window.getInsetsController();
      if(controller!=null){
        if(fullscreen)controller.hide(android.view.WindowInsets.Type.statusBars());
        else controller.show(android.view.WindowInsets.Type.statusBars());
        int mask=android.view.WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS
            |android.view.WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS;
        controller.setSystemBarsAppearance(darkIcons?mask:0,mask);
      }
    }else{
      View decor=window.getDecorView();int flags=decor.getSystemUiVisibility();
      if(fullscreen)flags|=View.SYSTEM_UI_FLAG_FULLSCREEN;else flags&=~View.SYSTEM_UI_FLAG_FULLSCREEN;
      if(Build.VERSION.SDK_INT>=23){
        if(darkIcons)flags|=View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;else flags&=~View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
      }
      if(Build.VERSION.SDK_INT>=26){
        if(darkIcons)flags|=View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;else flags&=~View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
      }
      decor.setSystemUiVisibility(flags);
    }
    View decor=window.getDecorView();decor.requestApplyInsets();decor.requestLayout();
    if(mRoot!=null){mRoot.requestApplyInsets();mRoot.requestLayout();}
  }'''
    text=replace_method(text,"cobraApplySystemBarsForSurface",bars)

    helpers=r'''
  private boolean cobraDarkIconsFor(int color){
    double luma=(0.299*Color.red(color)+0.587*Color.green(color)+0.114*Color.blue(color))/255.0;
    return luma>=0.62;
  }

  private void cobraInstallBrowseSafeArea(View root){
    if(root==null)return;
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
      if(v.getPaddingLeft()!=left||v.getPaddingTop()!=top||v.getPaddingRight()!=right||v.getPaddingBottom()!=bottom)
        v.setPadding(left,top,right,bottom);
      return insets;
    });
  }
'''
    if len(method_matches(text,"cobraInstallBrowseSafeArea")) or len(method_matches(text,"cobraDarkIconsFor")):
        raise RuntimeError("2103166 helper name collision")
    text=append_class(text,helpers)

    # Nothing except buildShell and the bar helper may have moved.
    for name,expected_hash in protected_before.items():
        actual=sha_bytes(method_text(text,name))
        if actual!=expected_hash:raise RuntimeError("Protected method changed: "+name)

    build=method_text(text,"buildShell")
    if "cobraInstallBrowseSafeArea(mRoot);" not in build or "mRoot.requestApplyInsets();" not in build:
        raise RuntimeError("Browse safe-area hook missing after patch")
    bars_after=method_text(text,"cobraApplySystemBarsForSurface")
    for token in ("statusBars()","APPEARANCE_LIGHT_STATUS_BARS","mRoot.requestApplyInsets()"):
        if token not in bars_after:raise RuntimeError("System-bar contract missing "+token)

    after_bytes=text.encode()
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    (out/"source-before").mkdir(exist_ok=True)
    (out/"source-before"/src.name).write_bytes(before_bytes)
    src.write_bytes(after_bytes)
    proof={
        "base_locked_commit":BASE_LOCK,
        "base_version_code":2103165,
        "files":{str(REL):{"before":sha_bytes(before_bytes),"after":sha_bytes(after_bytes)}},
        "protected_methods":protected_before,
        "changed_methods":["buildShell","cobraApplySystemBarsForSurface"],
        "new_helpers":["cobraInstallBrowseSafeArea","cobraDarkIconsFor"],
        "browse_insets":"systemBars + displayCutout, idempotent root padding",
        "fullscreen_owner":"player/multiview only",
        "navigation_bar_hidden":False,
        "native_changed":False,
        "physical_device_verified":False,
    }
    (out/"patch.json").write_text(json.dumps(proof,indent=2)+"\n")
    print("PASS: locked 2103165 -> 2103166 end-to-end safe-area repair; protected contracts unchanged")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();apply(a.source,a.receipt,a.out)
