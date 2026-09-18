#!/usr/bin/env python3
"""2103168 status-bar surface-match repair over exact locked 2103167.

2103167 successfully restored Android's real status bar. Physical Fold testing then proved the
remaining black strip was not a visibility failure: the system bar was transparent/edge-to-edge,
while the safe-area band beneath it still used Cobra's old base background instead of the active
Visual Theme "screen" surface.

This repair does not change insets, layout, player, PiP, navigation, providers, or playback. It
makes the safe-area/status-bar band use the same resolved top surface color as the active screen.
"""
from pathlib import Path
import argparse,hashlib,json,re

REL=Path("tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in")
BASE_LOCK="2d72c733998d3c535a16d354058344007c5f7921"

def sha_bytes(data):
    return hashlib.sha256(data if isinstance(data,bytes) else data.encode()).hexdigest()

def method_matches(text,name):
    return list(re.finditer(
        r'^  (?:(?:@Override(?:[ \t]*\n  |[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'
        +re.escape(name)+r'\s*\(',text,re.M))

def method_span(text,name):
    ms=method_matches(text,name)
    if len(ms)!=1: raise RuntimeError("Method cardinality %s = %d"%(name,len(ms)))
    start=ms[0].start();i=text.index("{",ms[0].end());depth=0;quote=None;esc=False;line=False;block=False
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
    if receipt.get("version_code")!=2103167:
        raise RuntimeError("Expected exact locked 2103167 source receipt")
    src=Path(source)/REL
    before_bytes=src.read_bytes();before=before_bytes.decode()
    expected=receipt.get("files",{}).get(str(REL),{}).get("after")
    if not expected or sha_bytes(before_bytes)!=expected:
        raise RuntimeError("Locked 2103167 Activity identity mismatch")

    protected=[
        "onCreate","buildShell","cobraInstallBrowseSafeArea","cobraDarkIconsFor",
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
    protected_before={name:sha_bytes(method_text(before,name)) for name in protected}

    old_bars=method_text(before,"cobraApplySystemBarsForSurface")
    old_confirm=method_text(before,"cobraConfirmBrowseSystemBars")
    for token in (
        'int barColor=fullscreen?Color.BLACK:cobraThemeColor("background",mTheme.background);',
        'window.setStatusBarColor(barColor);window.setNavigationBarColor(barColor);',
        'postOnAnimation(this::cobraConfirmBrowseSystemBars)',
    ):
        if token not in old_bars:raise RuntimeError("Locked 2103167 bar preimage drift: "+token)
    if 'int barColor=cobraThemeColor("background",mTheme.background);' not in old_confirm:
        raise RuntimeError("Locked 2103167 confirmation preimage drift")

    bars=old_bars.replace(
        'int barColor=fullscreen?Color.BLACK:cobraThemeColor("background",mTheme.background);',
        'int barColor=fullscreen?Color.BLACK:cobraBrowseSystemBarSurfaceColor();'
    ).replace(
        'window.setStatusBarColor(barColor);window.setNavigationBarColor(barColor);',
        'window.setStatusBarColor(fullscreen?Color.BLACK:Color.TRANSPARENT);window.setNavigationBarColor(barColor);'
    ).replace(
        'if(mRoot!=null){mRoot.requestApplyInsets();mRoot.requestLayout();}',
        'if(mRoot!=null){if(!fullscreen)mRoot.setBackgroundColor(barColor);mRoot.requestApplyInsets();mRoot.requestLayout();}'
    )
    text=replace_method(before,"cobraApplySystemBarsForSurface",bars)

    confirm=old_confirm.replace(
        'int barColor=cobraThemeColor("background",mTheme.background);',
        'int barColor=cobraBrowseSystemBarSurfaceColor();'
    ).replace(
        'window.setStatusBarColor(barColor);window.setNavigationBarColor(barColor);',
        'window.setStatusBarColor(Color.TRANSPARENT);window.setNavigationBarColor(barColor);'
    ).replace(
        'if(mRoot!=null){mRoot.requestApplyInsets();mRoot.requestLayout();}',
        'if(mRoot!=null){mRoot.setBackgroundColor(barColor);mRoot.requestApplyInsets();mRoot.requestLayout();}'
    )
    text=replace_method(text,"cobraConfirmBrowseSystemBars",confirm)

    helper=r'''
  private int cobraBrowseSystemBarSurfaceColor(){
    int fallback=cobraThemeColor("background",mTheme.background);
    try{
      CobraVisualRenderer renderer=vtheme();
      String palette=cobraEffectiveAppearanceMode();
      String layout=renderer.layout();
      JSONObject manifest=null;

      // The installed Visual Theme pointer is the persistent source of truth. Read only its
      // small JSON manifest here; never decode images/fonts on the UI thread. This also avoids
      // an async renderer-publication race during Activity/window restoration.
      JSONObject pointer=CobraVisualTheme.readPointer(this);
      String generation=pointer.optString("active","");
      if(generation!=null&&!generation.isEmpty()){
        File directory=CobraVisualTheme.inside(CobraVisualTheme.store(this),generation);
        File manifestFile=CobraVisualTheme.inside(directory,CobraVisualTheme.MANIFEST);
        byte[] raw=CobraVisualTheme.readFile(manifestFile,CobraVisualTheme.MAX_JSON);
        if(generation.equals(CobraVisualTheme.hash(raw)))
          manifest=new JSONObject(new String(raw,StandardCharsets.UTF_8));
      }

      // If no installed pointer exists, a currently published runtime theme may still be active.
      if(manifest==null&&CobraVisualRenderer.active!=null
          &&CobraVisualRenderer.active.data!=null
          &&CobraVisualRenderer.active.data.length()>0)
        manifest=CobraVisualRenderer.active.data;

      if(manifest!=null){
        int resolved=fallback;boolean found=false;
        JSONObject variants=manifest.optJSONObject("variants");
        JSONObject[] layers=new JSONObject[]{
            manifest.optJSONObject("base"),
            variants==null?null:variants.optJSONObject(layout),
            variants==null?null:variants.optJSONObject(palette)};
        for(JSONObject layer:layers){
          if(layer==null)continue;

          // Palette token first; the actual screen panel styles override it in the same order
          // CobraVisualRenderer.stylesFor() uses for mStage: all.panel -> screen.panel -> screen.
          JSONObject colors=layer.optJSONObject("colors");
          if(colors!=null){
            String encoded=colors.optString("palette.background","");
            if(encoded!=null&&!encoded.isEmpty()){
              int color=android.graphics.Color.parseColor(encoded);
              if(android.graphics.Color.alpha(color)>0){resolved=color;found=true;}
            }
          }
          JSONObject styles=layer.optJSONObject("styles");
          if(styles!=null){
            for(String key:new String[]{"all.panel","screen.panel","screen"}){
              JSONObject style=styles.optJSONObject(key);
              if(style==null)continue;
              String encoded=style.optString("fill","");
              if(encoded!=null&&!encoded.isEmpty()){
                int color=android.graphics.Color.parseColor(encoded);
                if(android.graphics.Color.alpha(color)>0){resolved=color;found=true;}
              }
            }
          }
        }
        if(found)return resolved;
      }

      // Runtime-only fallback for a theme that has been published but is not persisted.
      int resolved=fallback;boolean found=false;
      for(String key:new String[]{"all.panel","screen.panel","screen"}){
        Object raw=renderer.get("styles",key);
        if(raw instanceof JSONObject){
          String encoded=((JSONObject)raw).optString("fill","");
          if(encoded!=null&&!encoded.isEmpty()){
            int color=android.graphics.Color.parseColor(encoded);
            if(android.graphics.Color.alpha(color)>0){resolved=color;found=true;}
          }
        }
      }
      if(found)return resolved;
      int paletteColor=renderer.color("palette.background",fallback);
      if(android.graphics.Color.alpha(paletteColor)>0)return paletteColor;
    }catch(Exception ignored){}
    return fallback;
  }
'''
    if method_matches(text,"cobraBrowseSystemBarSurfaceColor"):
        raise RuntimeError("2103168 helper collision")
    text=append_class(text,helper)

    for name,h in protected_before.items():
        if sha_bytes(method_text(text,name))!=h:
            raise RuntimeError("Protected 2103167 method changed: "+name)

    after_bars=method_text(text,"cobraApplySystemBarsForSurface")
    after_confirm=method_text(text,"cobraConfirmBrowseSystemBars")
    surface=method_text(text,"cobraBrowseSystemBarSurfaceColor")
    for token in (
        "cobraBrowseSystemBarSurfaceColor()",
        "setStatusBarColor(fullscreen?Color.BLACK:Color.TRANSPARENT)",
        "mRoot.setBackgroundColor(barColor)",
    ):
        if token not in after_bars:raise RuntimeError("2103168 bar contract missing "+token)
    for token in (
        "setStatusBarColor(Color.TRANSPARENT)",
        "mRoot.setBackgroundColor(barColor)",
    ):
        if token not in after_confirm:raise RuntimeError("2103168 confirmation contract missing "+token)
    for token in (
        'CobraVisualTheme.readPointer(this)',
        'CobraVisualTheme.readFile(manifestFile,CobraVisualTheme.MAX_JSON)',
        'new String[]{"all.panel","screen.panel","screen"}',
        'manifest.optJSONObject("base")',
        'renderer.get("styles",key)',
    ):
        if token not in surface:raise RuntimeError("2103168 surface resolver missing "+token)

    after_bytes=text.encode()
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    (out/"source-before").mkdir(exist_ok=True)
    (out/"source-before"/src.name).write_bytes(before_bytes)
    src.write_bytes(after_bytes)
    proof={
        "base_locked_commit":BASE_LOCK,
        "base_version_code":2103167,
        "files":{str(REL):{"before":sha_bytes(before_bytes),"after":sha_bytes(after_bytes)}},
        "changed_methods":["cobraApplySystemBarsForSurface","cobraConfirmBrowseSystemBars"],
        "new_helpers":["cobraBrowseSystemBarSurfaceColor"],
        "protected_methods":protected_before,
        "root_cause":"edge-to-edge status bar exposed mRoot safe-area band using base Cobra background instead of active Visual Theme screen fill",
        "browse_status_bar":"transparent over theme-matched safe-area band",
        "fullscreen_status_bar":"black/hidden only for player and multiview",
        "layout_changed":False,
        "safe_area_changed":False,
        "player_changed":False,
        "native_changed":False,
        "physical_device_verified":False,
    }
    (out/"patch.json").write_text(json.dumps(proof,indent=2)+"\n")
    print("PASS: locked 2103167 -> 2103168 theme-matched status-bar surface; layout/player/PiP untouched")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();apply(a.source,a.receipt,a.out)
