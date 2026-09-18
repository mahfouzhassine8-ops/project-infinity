#!/usr/bin/env python3
"""2103175: full-screen wallpaper + safe foreground content over locked 2103171.

Goal:
- Choose Your Experience wallpaper/background fills the physical window behind the status bar.
- Cobra browse/main-menu wallpaper/background fills the physical window behind the status bar.
- Foreground content alone receives system-bar/display-cutout safe insets.
- Approved chooser/menu component sizing and internal spacing remain unchanged.
- Player, PiP, playback, native engine and theme ZIP payloads are untouched.
"""
from pathlib import Path
import argparse,hashlib,json,re

ACT=Path("tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in")
SPLASH=Path("tools/android/packaging/xbmc/src/Splash.java.in")
BASE_BUILD=2103171
BASE_COMMIT="59cf1958e5d911ede8df9b04c200025f4b39026e"

def sha(v):return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()

def matches(text,name):
    return list(re.finditer(
        r'^[ \t]{2,}(?:(?:@Override(?:[ \t]*\n[ \t]+|[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'
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
    a,b=span(text,name);return text[:a]+new.rstrip()+"\n"+text[b:]

def once(text,old,new,label):
    c=text.count(old)
    if c!=1:raise RuntimeError(f"{label}: expected one anchor, got {c}")
    return text.replace(old,new,1)

def patch_activity(before):
    protected=[
      "onCreate","onResume","onPause","onStop","onUserLeaveHint","onPictureInPictureModeChanged",
      "startSinglePlayer","buildPlayer","promoteCobraPreviewToFullscreen","cobraStartOwnedMiniPlayback",
      "cobraEndMiniBackgroundPlayback","cobraBuildPlayerChrome","showPlayerSettingsDrawer",
      "cobraInstallBrowseSafeArea","cobraBrowseSystemBarSurfaceColor","clearStage","showCobraPrimaryView"
    ]
    protected_before={n:sha(method(before,n)) for n in protected}
    text=before

    text=once(text,
      "  private LinearLayout mRoot;\n",
      "  private View mCobraBrowseBackground;\n  private LinearLayout mRoot;\n",
      "browse background field")

    build=method(text,"buildShell")
    old_top='''    FrameLayout frame = new FrameLayout(this);
    frame.setBackgroundColor(cobraThemeColor("background", mTheme.background));

    mRoot = new LinearLayout(this);
    mRoot.setOrientation(LinearLayout.HORIZONTAL);
    mRoot.setBackgroundColor(cobraThemeColor("background", mTheme.background));
    frame.addView(mRoot, new FrameLayout.LayoutParams(
        FrameLayout.LayoutParams.MATCH_PARENT,
        FrameLayout.LayoutParams.MATCH_PARENT));'''
    new_top='''    FrameLayout frame = new FrameLayout(this);
    frame.setBackgroundColor(cobraThemeColor("background", mTheme.background));

    // Full-window backdrop owns presentation behind the transparent status bar.
    // Foreground controls remain in mRoot and alone receive safe-area insets.
    mCobraBrowseBackground = new View(this);
    mCobraBrowseBackground.setTag("cobra-browse-background");
    mCobraBrowseBackground.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
    mCobraBrowseBackground.setFocusable(false);
    mCobraBrowseBackground.setClickable(false);
    mCobraBrowseBackground.setBackgroundColor(cobraThemeColor("background", mTheme.background));
    frame.addView(mCobraBrowseBackground, new FrameLayout.LayoutParams(
        FrameLayout.LayoutParams.MATCH_PARENT,
        FrameLayout.LayoutParams.MATCH_PARENT));

    mRoot = new LinearLayout(this);
    mRoot.setTag("cobra-browse-safe-content");
    mRoot.setOrientation(LinearLayout.HORIZONTAL);
    mRoot.setBackgroundColor(Color.TRANSPARENT);
    frame.addView(mRoot, new FrameLayout.LayoutParams(
        FrameLayout.LayoutParams.MATCH_PARENT,
        FrameLayout.LayoutParams.MATCH_PARENT));'''
    build=once(build,old_top,new_top,"buildShell backdrop split")

    old_end='''    cobraInstallBrowseSafeArea(mRoot);
    setContentView(frame);
    mRoot.requestApplyInsets();vtheme().tree(mRail,"rail");vtheme().paint(mStage,"screen");vtheme().paint(mHeader,"screen.header");vtheme().paint(mStatus,"screen.status");'''
    new_end='''    cobraInstallBrowseSafeArea(mRoot);
    setContentView(frame);
    // Move the exact approved "screen" visual role to the full-window backdrop.
    // Do not restyle/rescale mStage; its previously approved internal geometry stays intact.
    vtheme().paint(mCobraBrowseBackground,"screen");
    mRoot.requestApplyInsets();vtheme().tree(mRail,"rail");vtheme().paint(mHeader,"screen.header");vtheme().paint(mStatus,"screen.status");'''
    build=once(build,old_end,new_end,"buildShell screen role")
    text=replace_method(text,"buildShell",build)

    config=method(text,"onConfigurationChanged")
    config=once(config,
      '    if(mRoot!=null)mRoot.setBackgroundColor(cobraThemeColor("background",mTheme.background));',
      '''    if(mRoot!=null)mRoot.setBackgroundColor(Color.TRANSPARENT);
    if(mCobraBrowseBackground!=null){
      mCobraBrowseBackground.setBackgroundColor(cobraThemeColor("background",mTheme.background));
      vtheme().paint(mCobraBrowseBackground,"screen");
      mCobraBrowseBackground.invalidate();
    }''',
      "configuration background ownership")
    text=replace_method(text,"onConfigurationChanged",config)

    bars=method(text,"cobraApplySystemBarsForSurface")
    bars=once(bars,
      '''    if(mRoot!=null){if(!fullscreen)mRoot.setBackgroundColor(barColor);mRoot.requestApplyInsets();mRoot.requestLayout();}
    if(!fullscreen)decor.postOnAnimation(this::cobraConfirmBrowseSystemBars);''',
      '''    if(mRoot!=null){
      if(!fullscreen)mRoot.setBackgroundColor(Color.TRANSPARENT);
      mRoot.requestApplyInsets();mRoot.requestLayout();
    }
    if(!fullscreen&&mCobraBrowseBackground!=null)mCobraBrowseBackground.invalidate();
    if(!fullscreen)decor.postOnAnimation(this::cobraConfirmBrowseSystemBars);''',
      "browse bar background ownership")
    text=replace_method(text,"cobraApplySystemBarsForSurface",bars)

    confirm=method(text,"cobraConfirmBrowseSystemBars")
    confirm=once(confirm,
      '    if(mRoot!=null){mRoot.setBackgroundColor(barColor);mRoot.requestApplyInsets();mRoot.requestLayout();}',
      '''    if(mRoot!=null){
      mRoot.setBackgroundColor(Color.TRANSPARENT);
      mRoot.requestApplyInsets();mRoot.requestLayout();
    }
    if(mCobraBrowseBackground!=null)mCobraBrowseBackground.invalidate();''',
      "confirmed browse background ownership")
    text=replace_method(text,"cobraConfirmBrowseSystemBars",confirm)

    for n,h in protected_before.items():
        if sha(method(text,n))!=h:raise RuntimeError("Protected Activity contract changed: "+n)

    build_after=method(text,"buildShell")
    bars_after=method(text,"cobraApplySystemBarsForSurface")
    confirm_after=method(text,"cobraConfirmBrowseSystemBars")
    for token in (
      'mCobraBrowseBackground.setTag("cobra-browse-background")',
      'mRoot.setTag("cobra-browse-safe-content")',
      'mRoot.setBackgroundColor(Color.TRANSPARENT)',
      'vtheme().paint(mCobraBrowseBackground,"screen")',
      'cobraInstallBrowseSafeArea(mRoot)',
    ):
        if token not in build_after:raise RuntimeError("Browse layer contract missing: "+token)
    if 'vtheme().paint(mStage,"screen")' in build_after:
        raise RuntimeError("Inset mStage still owns full-screen wallpaper")
    if "setBackgroundColor(barColor)" in bars_after or "setBackgroundColor(barColor)" in confirm_after:
        raise RuntimeError("Foreground safe-content root still paints status-bar underlay")
    if "SYSTEM_UI_FLAG_LAYOUT_STABLE|View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN" not in bars_after:
        raise RuntimeError("2103170 edge-to-edge window contract lost")

    return text,protected_before

NEW_CHOOSER_BARS=r'''  private void cobraPrepareExperienceSystemBars(ExperienceTheme theme, android.widget.FrameLayout root, View safeContent){
    if(theme==null||root==null||safeContent==null)return;
    android.view.Window window=getWindow();View decor=window.getDecorView();

    androidx.core.view.WindowCompat.setDecorFitsSystemWindows(window,false);
    window.addFlags(android.view.WindowManager.LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS);
    window.clearFlags(android.view.WindowManager.LayoutParams.FLAG_TRANSLUCENT_STATUS
        |android.view.WindowManager.LayoutParams.FLAG_FULLSCREEN
        |android.view.WindowManager.LayoutParams.FLAG_FORCE_NOT_FULLSCREEN);
    window.setStatusBarColor(android.graphics.Color.TRANSPARENT);
    if(Build.VERSION.SDK_INT>=29)window.setStatusBarContrastEnforced(false);

    // Root/backdrop remains physically full-screen. Insets belong to foreground content only.
    root.setPadding(0,0,0,0);
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
    safeContent.setOnApplyWindowInsetsListener((v,insets)->{
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
      if(top>0)stableVerticalInsets[0]=top;else if(stableVerticalInsets[0]>0)top=stableVerticalInsets[0];
      if(bottom>0)stableVerticalInsets[1]=bottom;else if(stableVerticalInsets[1]>0)bottom=stableVerticalInsets[1];
      if(v.getPaddingLeft()!=left||v.getPaddingTop()!=top||v.getPaddingRight()!=right||v.getPaddingBottom()!=bottom)
        v.setPadding(left,top,right,bottom);
      return insets;
    });
    safeContent.requestApplyInsets();
  }'''

def patch_splash(before):
    protected=[
      "onCreate","startXBMC","showExperienceCardSettings","launchInfinityExperience",
      "showInfinityExperienceChooser","showLegacyInfinityExperienceChooser",
      "loadExperienceTheme","chooserExperienceCard","resolveVisualExperienceTheme",
      "cobraChooserDarkStatusIcons"
    ]
    protected_before={n:sha(method(before,n)) for n in protected}
    text=before

    scene=method(text,"showVisualExperienceScene")
    old_layers='''      android.widget.FrameLayout root=new android.widget.FrameLayout(this);root.setTag("experience-themed-root");root.addView(new ExperienceBackdrop(theme),new android.widget.FrameLayout.LayoutParams(-1,-1));root.addView(view,new android.widget.FrameLayout.LayoutParams(-1,-1));'''
    new_layers='''      android.widget.FrameLayout root=new android.widget.FrameLayout(this);root.setTag("experience-themed-root");
      root.addView(new ExperienceBackdrop(theme),new android.widget.FrameLayout.LayoutParams(-1,-1));
      android.widget.FrameLayout safeContent=new android.widget.FrameLayout(this);safeContent.setTag("experience-safe-content");
      safeContent.addView(view,new android.widget.FrameLayout.LayoutParams(-1,-1));
      root.addView(safeContent,new android.widget.FrameLayout.LayoutParams(-1,-1));'''
    scene=once(scene,old_layers,new_layers,"visual chooser layer split")
    scene=once(scene,
      "      setContentView(root);cobraPrepareExperienceSystemBars(theme,root);slots.get(\"enter.infinity\").requestFocus();",
      "      setContentView(root);cobraPrepareExperienceSystemBars(theme,root,safeContent);slots.get(\"enter.infinity\").requestFocus();",
      "visual chooser safe-content owner")
    text=replace_method(text,"showVisualExperienceScene",scene)

    styled=method(text,"showStyledInfinityExperienceChooser")
    old_add='''    scroll.addView(content, new android.widget.ScrollView.LayoutParams(-1, -2));
    root.addView(scroll, new android.widget.FrameLayout.LayoutParams(-1, -1));'''
    new_add='''    scroll.addView(content, new android.widget.ScrollView.LayoutParams(-1, -2));
    android.widget.FrameLayout safeContent=new android.widget.FrameLayout(this);safeContent.setTag("experience-safe-content");
    safeContent.addView(scroll,new android.widget.FrameLayout.LayoutParams(-1,-1));
    root.addView(safeContent, new android.widget.FrameLayout.LayoutParams(-1, -1));'''
    styled=once(styled,old_add,new_add,"styled chooser layer split")
    styled=once(styled,
      "    setContentView(root);cobraPrepareExperienceSystemBars(theme,root);\n",
      "    setContentView(root);cobraPrepareExperienceSystemBars(theme,root,safeContent);\n",
      "styled chooser safe-content owner")
    text=replace_method(text,"showStyledInfinityExperienceChooser",styled)

    text=replace_method(text,"cobraPrepareExperienceSystemBars",NEW_CHOOSER_BARS)

    for n,h in protected_before.items():
        if sha(method(text,n))!=h:raise RuntimeError("Protected chooser contract changed: "+n)

    scene_after=method(text,"showVisualExperienceScene")
    styled_after=method(text,"showStyledInfinityExperienceChooser")
    helper=method(text,"cobraPrepareExperienceSystemBars")
    for block in (scene_after,styled_after):
        if 'setTag("experience-safe-content")' not in block:
            raise RuntimeError("Chooser safe foreground layer missing")
        if "cobraPrepareExperienceSystemBars(theme,root,safeContent)" not in block:
            raise RuntimeError("Chooser system-bar owner not safe foreground")
    for token in (
      "root.setPadding(0,0,0,0)",
      "safeContent.setOnApplyWindowInsetsListener",
      "safeContent.requestApplyInsets()",
      "WindowCompat.setDecorFitsSystemWindows(window,false)",
      "setStatusBarColor(android.graphics.Color.TRANSPARENT)",
      "SYSTEM_UI_FLAG_LAYOUT_STABLE|View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN",
      "stableVerticalInsets",
    ):
        if token not in helper:raise RuntimeError("Chooser full-screen/safe-content contract missing: "+token)
    if "root.setOnApplyWindowInsetsListener" in helper:
        raise RuntimeError("Chooser background root still receives insets")

    # Approved internal chooser sizing from the older accepted layout must stay literal/unchanged.
    for token in (
      "compactHeight?8:vtheme().dimension(\"chooser.showStyledInfinityExperienceChooser.dimensions.1\",20)",
      "compactHeight?74:vtheme().dimension(\"chooser.showStyledInfinityExperienceChooser.dimensions.8\",98)",
      "compactHeight?6:vtheme().dimension(\"chooser.showStyledInfinityExperienceChooser.dimensions.9\",18)",
      "compactHeight?10:vtheme().dimension(\"chooser.showStyledInfinityExperienceChooser.dimensions.10\",26)",
      "int adaptiveCardHeight=compactHeight?Math.min(theme.cardHeight,Math.max(200,heightDp-285)):theme.cardHeight",
    ):
        if token not in styled_after:raise RuntimeError("Approved chooser sizing changed: "+token)

    return text,protected_before

def apply(source,receipt_path,out):
    source=Path(source);receipt_path=Path(receipt_path);out=Path(out)
    receipt=json.loads(receipt_path.read_text())
    if receipt.get("version_code")!=BASE_BUILD:
        raise RuntimeError("Expected exact locked 2103171 source receipt")

    pending={};proof={};protected={}
    for rel,patcher in ((ACT,patch_activity),(SPLASH,patch_splash)):
        path=source/rel
        expected=receipt.get("files",{}).get(str(rel),{}).get("after")
        if not expected:raise RuntimeError("2103171 receipt missing "+str(rel))
        before=path.read_bytes()
        if sha(before)!=expected:raise RuntimeError("2103171 preimage mismatch "+str(rel))
        after_text,guards=patcher(before.decode())
        after=after_text.encode()
        pending[path]=after
        proof[str(rel)]={"before":sha(before),"after":sha(after)}
        protected[str(rel)]=guards

    out.mkdir(parents=True,exist_ok=True);(out/"source-before").mkdir(exist_ok=True)
    for path,after in pending.items():
        (out/"source-before"/path.name).write_bytes(path.read_bytes())
    for path,after in pending.items():path.write_bytes(after)

    report={
      "base_build":BASE_BUILD,"base_commit":BASE_COMMIT,
      "files":proof,"protected_methods":protected,
      "changed_activity":["buildShell","onConfigurationChanged","cobraApplySystemBarsForSurface","cobraConfirmBrowseSystemBars","field:mCobraBrowseBackground"],
      "changed_chooser":["showVisualExperienceScene","showStyledInfinityExperienceChooser","cobraPrepareExperienceSystemBars"],
      "wallpaper_full_physical_window":True,
      "safe_insets_foreground_only":True,
      "approved_component_sizing_changed":False,
      "chooser_background_inset":False,
      "cobra_background_inset":False,
      "status_bar_visible":True,
      "status_bar_transparent":True,
      "player_changed":False,"pip_changed":False,"playback_changed":False,
      "theme_zip_changed":False,"native_changed":False,"physical_device_verified":False
    }
    (out/"patch.json").write_text(json.dumps(report,indent=2)+"\n")
    print("PASS: 2103175 full-window wallpaper + safe foreground content; approved sizing preserved")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();apply(a.source,a.receipt,a.out)
