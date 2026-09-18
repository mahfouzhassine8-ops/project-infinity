#!/usr/bin/env python3
"""Cobra 2103162: consolidated visual-theme control + Cobra player rotation.

Exact delta on top of the passed/locked 2103161 source. Android presentation
runtime only: no Kodi C/C++, native renderer, provider, EPG, playback engine,
signer or resource payload changes.

Rotation deliberately reuses the established Infinity player-rotation contract:
- shared preference namespace: infinity_player_rotation / mode
- 0 = Follow Device (white)
- 1 = Unlocked while active foreground video (cyan)
- SCREEN_ORIENTATION_FULL_SENSOR only while eligible
- SCREEN_ORIENTATION_UNSPECIFIED on pause/stop/close/PiP/multi-window/TV
- never writes Android Settings.System auto-rotate state
"""
from pathlib import Path
import argparse, hashlib, json, re

LIVE=Path("tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in")
THEME=Path("tools/android/packaging/xbmc/src/CobraVisualTheme.java.in")
LIVE_PRE="3bf4c763615223bf79930e1e4064dd5a5c276c73234f0c12c7c9031c4fa7e7cc"
THEME_PRE="eeeaf101d1dc05e0510d45571397b7f312cbf2aeeb87d9250632001db9838b84"

def sha_text(s): return hashlib.sha256(s.encode()).hexdigest()

def method_end(text,start):
    brace=text.find("{",start)
    if brace<0: raise RuntimeError("method opening brace missing")
    depth=0; quote=None; esc=False; line=False; block=False; i=brace
    while i<len(text):
        c=text[i]; n=text[i+1] if i+1<len(text) else ""
        if line:
            if c=="\n": line=False
            i+=1; continue
        if block:
            if c=="*" and n=="/": block=False; i+=2; continue
            i+=1; continue
        if quote is not None:
            if esc: esc=False
            elif c=="\\": esc=True
            elif c==quote: quote=None
            i+=1; continue
        if c=="/" and n=="/": line=True; i+=2; continue
        if c=="/" and n=="*": block=True; i+=2; continue
        if c in ('"',"'"): quote=c; i+=1; continue
        if c=="{": depth+=1
        elif c=="}":
            depth-=1
            if depth==0:return i+1
        i+=1
    raise RuntimeError("method closing brace missing")

def span(text,name):
    p=re.compile(r'^  (?:@Override(?:[ \t]*\n  |[ \t]+))?(?:private|public|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',re.M)
    m=list(p.finditer(text))
    if len(m)!=1: raise RuntimeError(f"{name}: expected one method, got {len(m)}")
    return m[0].start(),method_end(text,m[0].start())

def replace_method(text,name,new):
    a,b=span(text,name); return text[:a]+new.rstrip()+"\n"+text[b:]

def edit_method(text,name,fn):
    a,b=span(text,name); block=text[a:b]; out=fn(block)
    if out==block: raise RuntimeError(name+": no change")
    return text[:a]+out+text[b:]

def once(text,old,new,label):
    if text.count(old)!=1: raise RuntimeError(f"{label}: expected one exact match, got {text.count(old)}")
    return text.replace(old,new,1)

SETTINGS=r'''  private void showSettings() {
    mCobraInternalScreen = "internal";
    clearStage("COBRA • SETTINGS");
    status("One Infinity app • Cobra Live runtime");

    LinearLayout list = new LinearLayout(this);
    list.setOrientation(LinearLayout.VERTICAL);
    list.setPadding(0, dp(vtheme().dimension("cobra.showSettings.dimensions.1",4)), 0, dp(vtheme().dimension("cobra.showSettings.dimensions.2",12)));

    Button chooser = action(vtheme().copy("cobra.showSettings.copy.1","ASK WHICH EXPERIENCE ON NEXT LAUNCH"));
    chooser.setOnClickListener(v -> {
      getSharedPreferences(EXPERIENCE_PREFS, MODE_PRIVATE).edit().remove(EXPERIENCE_DEFAULT).apply();
      toast("Experience chooser will appear next launch");
    });

    Button theme = action("THEME  •  " + (vtheme().installed() ? "CUSTOM" : "BUILT-IN"));
    theme.setTag("cobra_theme_management");
    theme.setOnClickListener(v -> showCobraVisualThemePicker());

    Button appearance = action(vtheme().copy("cobra.showSettings.copy.4","APPEARANCE  •  ") + cobraAppearanceLabel());
    appearance.setOnClickListener(v -> showCobraAppearancePicker());

    Button backgroundMode = action("BACKGROUND MODE  •  " + cobraBackgroundModeLabel());
    backgroundMode.setTag("cobra_background_mode");
    backgroundMode.setOnClickListener(v -> showCobraBackgroundModePicker());

    TextView uiState = text(activeCobraUiLabel(), cobraThemeColor("accent_soft", mTheme.accentSoft), 13,
        Gravity.LEFT | Gravity.CENTER_VERTICAL);

    Button refresh = action(vtheme().copy("cobra.showSettings.copy.6","REFRESH CURRENT SOURCE"));
    refresh.setOnClickListener(v -> loadActiveSource(true));
    Button allSources = action(vtheme().copy("cobra.showSettings.copy.7","REFRESH ALL ENABLED SOURCES"));
    allSources.setOnClickListener(v -> loadAllEnabledSources(true));
    Button profiles = action(vtheme().copy("cobra.showSettings.copy.8","PROFILES & PARENTAL CONTROLS"));
    profiles.setOnClickListener(v -> showProfiles());
    Button health = action(vtheme().copy("cobra.showSettings.copy.9","COBRA HEALTH CENTER"));
    health.setOnClickListener(v -> showCobraHealthCenter());
    Button exportDiagnostics = action(vtheme().copy("cobra.showSettings.copy.10","EXPORT CRASH & DIAGNOSTICS ZIP"));
    exportDiagnostics.setOnClickListener(v -> showCobraDiagnosticExport());
    Button customEpg = action(vtheme().copy("cobra.showSettings.copy.11","CUSTOM EPG FOR ACTIVE SOURCE"));
    customEpg.setOnClickListener(v -> editCustomEpg());

    TextView subscriptionStatus = text(cobraSubscriptionCachedLabel(), cobraThemeColor("accent_soft", mTheme.accentSoft), 13,
        Gravity.LEFT | Gravity.CENTER_VERTICAL);
    subscriptionStatus.setTag("cobra_subscription_status");

    list.addView(chooser, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(theme, new LinearLayout.LayoutParams(-1, dp(58)));
    list.addView(appearance, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(backgroundMode, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(uiState, new LinearLayout.LayoutParams(-1, dp(44)));
    list.addView(refresh, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(allSources, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(profiles, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(health, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(exportDiagnostics, new LinearLayout.LayoutParams(-1, dp(64)));
    list.addView(customEpg, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(subscriptionStatus, new LinearLayout.LayoutParams(-1, dp(86)));

    vtheme().tree(list,"settings");
    ScrollView settingsScroll = new ScrollView(this);
    settingsScroll.setFillViewport(true);settingsScroll.addView(list);
    mStage.addView(settingsScroll, new LinearLayout.LayoutParams(-1,0,1));
    refreshCobraSubscriptionStatus();
  }'''

HELPERS=r'''
  private void showCobraVisualThemePicker(){
    final boolean installed=vtheme().installed();
    final String previous=CobraVisualTheme.readPointer(this).optString("previous","");
    final boolean canRestore=!previous.isEmpty();
    LinearLayout rows=cobraOpenSheet("Theme",
        installed ? "Current • "+vtheme().displayName() : "Current • Cobra built-in appearance",
        "theme-management");
    boolean dark=cobraSheetIsDark();

    rows.addView(cobraSheetRow("source","Built-in appearance",
        installed ? "Return to Cobra's normal appearance" : "Selected",
        false,dark,()->{
          if(!vtheme().installed()){toast("Built-in appearance is already active");showSettings();return;}
          vtheme().restoreBuiltIn(this,()->{
            if(!isFinishing()&&!isDestroyed()){toast("Built-in appearance restored");showSettings();}
          });
        }));

    rows.addView(cobraSheetRow("favorite","Installed visual theme",
        installed ? "Selected • "+vtheme().displayName()
            : (canRestore ? "Return to the same visual theme you were using" : "Install a visual theme ZIP first"),
        false,dark,()->{
          if(vtheme().installed()){toast("Installed visual theme is already active");showSettings();return;}
          if(CobraVisualTheme.readPointer(this).optString("previous","").isEmpty()){
            toast("No installed visual theme is available");showCobraVisualThemePicker();return;
          }
          vtheme().restorePrevious(this,()->{
            if(!isFinishing()&&!isDestroyed()){toast("Installed visual theme restored");showSettings();}
          });
        }));

    rows.addView(cobraSheetRow("add","Install / replace theme ZIP",
        "Choose a Cobra visual-theme package",false,dark,()->openCobraUiPackagePicker()));
  }

  private static final String COBRA_ROTATION_PREFS="infinity_player_rotation";
  private static final String COBRA_ROTATION_MODE="mode";
  private static final int COBRA_ROTATION_FOLLOW_DEVICE=0;
  private static final int COBRA_ROTATION_UNLOCKED=1;
  private int mCobraLastRequestedOrientation=Integer.MIN_VALUE;
  private CobraIconButton mCobraPlayerRotationButton;

  private int cobraPlayerRotationMode(){
    int value=getSharedPreferences(COBRA_ROTATION_PREFS,MODE_PRIVATE)
        .getInt(COBRA_ROTATION_MODE,COBRA_ROTATION_FOLLOW_DEVICE);
    return value==COBRA_ROTATION_UNLOCKED?COBRA_ROTATION_UNLOCKED:COBRA_ROTATION_FOLLOW_DEVICE;
  }

  private boolean cobraRotationConstrained(){
    boolean pip=false,multiWindow=false;
    try{
      if(Build.VERSION.SDK_INT>=26)pip=isInPictureInPictureMode();
      if(Build.VERSION.SDK_INT>=24)multiWindow=isInMultiWindowMode();
    }catch(IllegalStateException ignored){return true;}
    boolean television=getPackageManager().hasSystemFeature("android.software.leanback");
    return pip||multiWindow||television||mBackgroundStopped;
  }

  private boolean cobraHasActiveVideo(){
    try{
      return mPlayer!=null&&mPlaying!=null&&mPlayer.getVideoFormat()!=null
          &&(mPlayer.isPlaying()||mPlayer.getPlayWhenReady());
    }catch(Exception ignored){return false;}
  }

  private String cobraPlayerRotationDescription(){
    return cobraPlayerRotationMode()==COBRA_ROTATION_UNLOCKED
        ?"Rotation unlocked • follows physical device"
        :"Rotation follows device setting";
  }

  private void cobraUpdatePlayerRotationButton(){
    if(mCobraPlayerRotationButton==null)return;
    boolean unlocked=cobraPlayerRotationMode()==COBRA_ROTATION_UNLOCKED;
    mCobraPlayerRotationButton.ink=unlocked?0xff55c8ff:Color.WHITE;
    mCobraPlayerRotationButton.setContentDescription(cobraPlayerRotationDescription());
    mCobraPlayerRotationButton.setSelected(unlocked);
    mCobraPlayerRotationButton.invalidate();
  }

  private void cobraTogglePlayerRotation(){
    int next=cobraPlayerRotationMode()==COBRA_ROTATION_UNLOCKED
        ?COBRA_ROTATION_FOLLOW_DEVICE:COBRA_ROTATION_UNLOCKED;
    getSharedPreferences(COBRA_ROTATION_PREFS,MODE_PRIVATE).edit().putInt(COBRA_ROTATION_MODE,next).apply();
    cobraApplyPlayerRotation("button");
    cobraUpdatePlayerRotationButton();
    toast(next==COBRA_ROTATION_UNLOCKED?"Player rotation • Unlocked":"Player rotation • Follow Device");
    showPlayerChromeTemporarily();
  }

  private void cobraApplyPlayerRotation(String reason){
    boolean unlock=cobraPlayerRotationMode()==COBRA_ROTATION_UNLOCKED
        &&mPlayerOverlay!=null&&cobraHasActiveVideo()&&!cobraRotationConstrained();
    cobraRequestPlayerOrientation(unlock
        ?android.content.pm.ActivityInfo.SCREEN_ORIENTATION_FULL_SENSOR
        :android.content.pm.ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,reason);
  }

  private void cobraRequestPlayerOrientation(int requested,String reason){
    if(mCobraLastRequestedOrientation==requested)return;
    try{
      setRequestedOrientation(requested);
      mCobraLastRequestedOrientation=requested;
      android.util.Log.i("InfinityRotation","Cobra player rotation="
          +(requested==android.content.pm.ActivityInfo.SCREEN_ORIENTATION_FULL_SENSOR?"unlocked":"follow-device")
          +" reason="+reason);
    }catch(IllegalStateException|SecurityException error){
      android.util.Log.w("InfinityRotation","Android rejected Cobra player orientation request",error);
    }
  }
'''

def patch_live(s):
    if sha_text(s)!=LIVE_PRE: raise RuntimeError("Not exact locked 2103161 Activity: "+sha_text(s))
    s=replace_method(s,"showSettings",SETTINGS)

    # Add a real circular-arrow glyph to the existing vector-like Cobra icon renderer.
    rotate='''else if("rotate".equals(glyph)){
        canvas.drawArc(4,4,20,20,-48,228,false,paint);
        p.moveTo(18,3);p.lineTo(22,6);p.lineTo(18,9);canvas.drawPath(p,paint);
        canvas.drawArc(4,4,20,20,132,228,false,paint);
        p.reset();p.moveTo(6,21);p.lineTo(2,18);p.lineTo(6,15);canvas.drawPath(p,paint);
      } else if("aspect".equals(glyph))'''
    s=once(s,'else if("aspect".equals(glyph))',rotate,"rotation icon hook")

    # Place Rotation beside Lock, matching the established Infinity player placement policy.
    def chrome(block):
        anchor='''    header.addView(cobraIcon("lock","Lock controls",true,v->lockCobraPlayer()),new LinearLayout.LayoutParams(dp(48),dp(48)));chrome.addView(header,new LinearLayout.LayoutParams(-1,-2));'''
        replacement='''    CobraIconButton rotation=cobraIcon("rotate",cobraPlayerRotationDescription(),true,v->cobraTogglePlayerRotation());
    rotation.setTag("cobra_player_rotation");mCobraPlayerRotationButton=rotation;cobraUpdatePlayerRotationButton();
    header.addView(rotation,new LinearLayout.LayoutParams(dp(48),dp(48)));
    header.addView(cobraIcon("lock","Lock controls",true,v->lockCobraPlayer()),new LinearLayout.LayoutParams(dp(48),dp(48)));chrome.addView(header,new LinearLayout.LayoutParams(-1,-2));'''
        block=once(block,anchor,replacement,"player rotation button")
        end='''    vtheme().tree(chrome,"player.chrome");cobraRefreshProgrammeLabels();cobraUpdatePlaybackLabels();'''
        if end in block:
            block=block.replace(end,'    vtheme().tree(chrome,"player.chrome");cobraUpdatePlayerRotationButton();cobraApplyPlayerRotation("chrome");cobraRefreshProgrammeLabels();cobraUpdatePlaybackLabels();',1)
        else:
            block=once(block,'    cobraRefreshProgrammeLabels();cobraUpdatePlaybackLabels();','    cobraUpdatePlayerRotationButton();cobraApplyPlayerRotation("chrome");cobraRefreshProgrammeLabels();cobraUpdatePlaybackLabels();',"player chrome apply")
        return block
    s=edit_method(s,"cobraBuildPlayerChrome",chrome)

    # Re-evaluate when Media3 playback state changes; no play/prepare/release ownership changes.
    def start_player(block):
        pat=re.compile(r'(@Override public void onPlaybackStateChanged\(int playbackState\) \{\s*)(if \(!isCobraAsyncAlive\(\)\) return;\s*)?')
        m=pat.search(block)
        if not m: raise RuntimeError("single-player playback callback hook missing")
        prefix=m.group(1)+(m.group(2) or "")+'          cobraApplyPlayerRotation("playback-state");\n'
        return block[:m.start()]+prefix+block[m.end():]
    s=edit_method(s,"startSinglePlayer",start_player)

    # Exact established release behavior at lifecycle and player transitions.
    def append_before_close(block,line):
        i=block.rfind("}")
        if i<0:raise RuntimeError("method close missing")
        return block[:i]+line+"\n"+block[i:]
    s=edit_method(s,"onResume",lambda b:append_before_close(b,'    cobraApplyPlayerRotation("resume");'))
    s=edit_method(s,"onPause",lambda b:once(b,"{","{\n    cobraRequestPlayerOrientation(android.content.pm.ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,\"pause\");","rotation pause release"))
    s=edit_method(s,"onStop",lambda b:once(b,"{","{\n    cobraRequestPlayerOrientation(android.content.pm.ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,\"stop\");","rotation stop release"))
    s=edit_method(s,"closePlayer",lambda b:once(b,"{","{\n    cobraRequestPlayerOrientation(android.content.pm.ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,\"close-player\");mCobraPlayerRotationButton=null;","rotation close release"))
    s=edit_method(s,"openMultiView",lambda b:once(b,"{","{\n    cobraRequestPlayerOrientation(android.content.pm.ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,\"multi-view\");mCobraPlayerRotationButton=null;","rotation multiview release"))

    def pip(block):
        anchor="    mInPictureInPicture = inPictureInPictureMode;\n"
        return once(block,anchor,anchor+'    cobraApplyPlayerRotation("pip");\n',"rotation PiP release")
    s=edit_method(s,"onPictureInPictureModeChanged",pip)

    # Append helpers without changing any playback/provider/native implementation.
    pos=s.rfind("\n}")
    if pos<0:raise RuntimeError("Activity terminator missing")
    s=s[:pos]+"\n"+HELPERS.rstrip()+"\n"+s[pos:]
    verify_live(s)
    return s

def verify_live(s):
    required=[
      'THEME  •  ','cobra_theme_management','showCobraVisualThemePicker()',
      'Built-in appearance','Installed visual theme','Install / replace theme ZIP',
      'COBRA_ROTATION_PREFS="infinity_player_rotation"','COBRA_ROTATION_MODE="mode"',
      'SCREEN_ORIENTATION_FULL_SENSOR','SCREEN_ORIENTATION_UNSPECIFIED',
      'cobra_player_rotation','cobraTogglePlayerRotation()','"rotate".equals(glyph)',
      'cobraApplyPlayerRotation("playback-state")','cobraApplyPlayerRotation("pip")',
      'cobraRequestPlayerOrientation(android.content.pm.ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,"pause")'
    ]
    for token in required:
        if token not in s: raise RuntimeError("missing 2103162 contract: "+token)
    settings=s[s.index("  private void showSettings()"):span(s,"showSettings")[1]]
    for forbidden in ["PREVIOUS VISUAL THEME","REMOVE VISUAL THEME","RELOAD COBRA UI THEME","INSTALL COBRA UI / VISUAL THEME ZIP","cobra_visual_theme_state"]:
        if forbidden in settings: raise RuntimeError("old theme clutter remains: "+forbidden)
    if "Settings.System" in s or "ACCELEROMETER_ROTATION" in s:
        raise RuntimeError("rotation must not mutate Android global auto-rotate")
    if s.count('private void showCobraVisualThemePicker()')!=1: raise RuntimeError("theme picker duplicate")
    if s.count('private void cobraTogglePlayerRotation()')!=1: raise RuntimeError("rotation controller duplicate")

def patch_theme(s):
    if sha_text(s)!=THEME_PRE: raise RuntimeError("Not exact locked 2103161 visual runtime: "+sha_text(s))
    s=once(s,"public static final int RUNTIME=2, BUILD=2103161;","public static final int RUNTIME=2, BUILD=2103162;","visual runtime build")
    return s

def main():
    p=argparse.ArgumentParser();p.add_argument("--source",type=Path,required=True);p.add_argument("--receipt",type=Path,required=True);a=p.parse_args()
    live=a.source/LIVE;theme=a.source/THEME
    before_live=live.read_text();before_theme=theme.read_text()
    after_live=patch_live(before_live);after_theme=patch_theme(before_theme)
    live.write_text(after_live);theme.write_text(after_theme)
    row={"base_build":2103161,"target_build":2103162,"files":{
      str(LIVE):{"before":sha_text(before_live),"after":sha_text(after_live)},
      str(THEME):{"before":sha_text(before_theme),"after":sha_text(after_theme)}
    },"rotation_contract":{"shared_with_infinity":True,"follow_device":0,"unlocked":1,"global_setting_mutated":False},
       "theme_settings":"single settings row -> built-in / installed theme / install ZIP"}
    a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(row,indent=2)+"\n")
    print("PASS: exact 2103161 -> 2103162 theme switch + Cobra player rotation delta applied")
if __name__=="__main__":main()
