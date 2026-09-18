#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,re

REL=Path("tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in")
PREIMAGE="8797019d960d0861937d3a93ef4e93b94c3e9034179b429b7cd55d8cfb586831"

def sha(v):return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()

def matches(text,name):
    return list(re.finditer(
        r'^  (?:(?:@Override(?:[ \t]*\n  |[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'
        +re.escape(name)+r'\s*\(',text,re.M))
def method(text,name):
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
            if d==0:return text[start:i+1]
        i+=1
    raise RuntimeError("Unclosed "+name)

def main():
    p=argparse.ArgumentParser();p.add_argument("--source",type=Path,required=True);p.add_argument("--patch",type=Path,required=True);p.add_argument("--out",type=Path,required=True);a=p.parse_args()
    text=(a.source/REL).read_text();patch=json.loads(a.patch.read_text())
    oncreate=method(text,"onCreate")
    bars=method(text,"cobraApplySystemBarsForSurface")
    confirm=method(text,"cobraConfirmBrowseSystemBars")
    safe=method(text,"cobraInstallBrowseSafeArea")
    resolver=method(text,"cobraBrowseSystemBarSurfaceColor")
    fullscreen=method(text,"openPlayerOverlay")
    pip=method(text,"onPictureInPictureModeChanged")

    checks={}
    checks["exact_patch_scope"]=patch.get("changed_methods")==["onCreate","cobraApplySystemBarsForSurface","cobraConfirmBrowseSystemBars"]
    checks["edge_to_edge_explicit"]="WindowCompat.setDecorFitsSystemWindows(getWindow(),false)" in oncreate
    checks["edge_to_edge_configured_once"]=oncreate.count("setDecorFitsSystemWindows")==1 and "setDecorFitsSystemWindows" not in bars+confirm
    checks["contrast_scrim_disabled"]="setStatusBarContrastEnforced(false)" in oncreate and "setStatusBarContrastEnforced(false)" in bars and "setStatusBarContrastEnforced(false)" in confirm
    checks["draws_system_bar_backgrounds"]="FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS" in oncreate
    checks["translucent_status_cleared"]="FLAG_TRANSLUCENT_STATUS" in oncreate
    checks["browse_does_not_force_not_fullscreen"]="addFlags(WindowManager.LayoutParams.FLAG_FORCE_NOT_FULLSCREEN)" not in bars+confirm
    checks["stale_force_not_fullscreen_cleared"]="clearFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN" in bars and "FLAG_FORCE_NOT_FULLSCREEN" in bars and "FLAG_FORCE_NOT_FULLSCREEN" in confirm
    checks["browse_draws_behind_status"]="SYSTEM_UI_FLAG_LAYOUT_STABLE|View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN" in bars and "SYSTEM_UI_FLAG_LAYOUT_STABLE|View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN" in confirm
    checks["browse_does_not_strip_status_underlay"]="flags&=~(View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN" not in bars
    checks["status_transparent"]="setStatusBarColor(fullscreen?Color.BLACK:Color.TRANSPARENT)" in bars and "setStatusBarColor(Color.TRANSPARENT)" in confirm
    checks["system_status_visible"]="controller.show(android.view.WindowInsets.Type.statusBars())" in bars and "statusBars()" in confirm
    checks["safe_area_root_owns_insets"]="WindowInsets.Type.systemBars()" in safe and "WindowInsets.Type.displayCutout()" in safe and "v.setPadding(left,top,right,bottom)" in safe
    checks["matched_underlay"]="mRoot.setBackgroundColor(barColor)" in bars and "mRoot.setBackgroundColor(barColor)" in confirm
    checks["persisted_theme_resolver"]="CobraVisualTheme.readPointer(this)" in resolver and "CobraVisualTheme.hash(raw)" in resolver
    checks["theme_screen_cascade"]='new String[]{"all.panel","screen.panel","screen"}' in resolver
    checks["fullscreen_video_contract"]="mPlayerOverlay" in fullscreen and "Color.BLACK" in bars and "controller.hide(android.view.WindowInsets.Type.statusBars())" in bars
    checks["pip_callback_untouched"]="cobraConsumeLauncherPipReturn" in pip and "cobraApplySystemBarsForSurface" in pip
    checks["no_layout_or_safe_area_rewrite"]=patch.get("safe_area_changed") is False and patch.get("player_changed") is False and patch.get("pip_changed") is False
    checks["native_unchanged"]=patch.get("native_changed") is False

    failed=[k for k,v in checks.items() if not v]
    result={"passed":not failed,"checks":checks,"failed":failed,
            "changed_methods":patch.get("changed_methods"),"protected_methods":len(patch.get("protected_methods",{})),
            "physical_device_verified":False}
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"source-audit.json").write_text(json.dumps(result,indent=2)+"\n")
    if failed:raise RuntimeError("2103170 source audit failed: "+", ".join(failed))
    print("PASS:",len(checks),"2103170 status-bar ownership checks;",result["protected_methods"],"protected methods")

if __name__=="__main__":main()
