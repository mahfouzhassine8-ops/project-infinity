#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import hashlib, json

ROOT=Path(__file__).resolve().parents[2]
THEME=ROOT/"themes/cobra-liquid-glass-v1/visual-theme.json"
DIST=ROOT/"dist"
SAFE_KEYS={
  "screen","screen.header","screen.status","rail",
  "drawer.panel","drawer.header","drawer.items","drawer.power",
  "drawer.item.search","drawer.item.tv","drawer.item.movies","drawer.item.shows",
  "drawer.item.recordings","drawer.item.my_list","drawer.item.settings","drawer.item.view",
  "settings","sheet.row","sheet.detail","dialog.panel","dialog.button",
  "guide.shell","guide.directory","guide.details","guide.browser",
  "player.chrome","player.channels","chooser","chooser.card.infinity","chooser.card.cobra"
}
FORBIDDEN_PREFIXES=("all.","widget.","font.","tag.","art.")
GEOMETRY={"width_dp","height_dp","min_height_dp","margin_dp","margin_left_dp","margin_top_dp","margin_right_dp","margin_bottom_dp",
          "padding_dp","padding_left_dp","padding_top_dp","padding_right_dp","padding_bottom_dp","weight","orientation","gravity","max_lines"}

def require(v,msg):
    if not v:
        raise SystemExit("FAIL: "+msg)

def blob_sha(path:Path)->str:
    raw=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def parse(c):
    h=c[1:]
    if len(h)==6: return 255,int(h[:2],16),int(h[2:4],16),int(h[4:6],16)
    return int(h[:2],16),int(h[2:4],16),int(h[4:6],16),int(h[6:8],16)

def comp(fg,bg):
    a,r,g,b=parse(fg); _,rb,gb,bb=parse(bg); q=a/255
    return (r*q+rb*(1-q),g*q+gb*(1-q),b*q+bb*(1-q))

def lum(rgb):
    def f(x):
        x=x/255
        return x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4
    r,g,b=map(f,rgb)
    return .2126*r+.7152*g+.0722*b

def ratio(fg,bg):
    a=lum(comp(fg,bg)); b=lum(comp(bg,"#FF000000"))
    hi,lo=max(a,b),min(a,b)
    return (hi+.05)/(lo+.05)

d=json.loads(THEME.read_text())
require(d["id"]=="cobra.liquid-glass.hm.safe.v1","unsafe/old Liquid Glass manifest still active")
require(d["assets"]=={},"binary assets forbidden")
require(set(d["variants"])=={"light","dark","oled"},"unexpected layout or appearance variant")

for name,layer in [("base",d["base"])]+list(d["variants"].items()):
    styles=layer.get("styles",{})
    for key,style in styles.items():
        require(key in SAFE_KEYS,f"{name}: unsafe style scope {key}")
        require(not key.startswith(FORBIDDEN_PREFIXES),f"{name}: global style cascade {key}")
        require(not (set(style)&GEOMETRY),f"{name}: geometry mutation in {key}")
        require("image" not in style and "font_asset" not in style,f"{name}: binary-backed style {key}")
        if "fill" in style:
            alpha=parse(style["fill"])[0]
            require(alpha>=204,f"{name}: surface too transparent for safe readability: {key}")
    for group in ("dimensions","images","scenes","guide_layouts"):
        require(not layer.get(group),f"{name}: forbidden ownership of {group}")

base_keys=set(d["base"].get("styles",{}))
require(base_keys==SAFE_KEYS,"base scoped surface coverage is incomplete")
require(set(d["variants"]["light"].get("styles",{}))==SAFE_KEYS,"Light must explicitly cover every scoped surface")
require(set(d["variants"]["oled"].get("styles",{}))==SAFE_KEYS,"OLED must explicitly cover every scoped surface")
require(d["variants"]["dark"].get("styles",{})=={},"Dark variant must inherit the safe dark base without duplicate/global rules")

for mode,layer in (("dark",d["base"]),("light",d["variants"]["light"]),("oled",d["variants"]["oled"])):
    colors={**d["base"].get("colors",{}),**layer.get("colors",{})}
    styles=d["base"]["styles"] if mode=="dark" else layer["styles"]
    text=colors["palette.text"]
    screen=styles["screen"]["fill"]
    require(ratio(text,screen)>=7.0,f"{mode}: root text contrast below safe threshold")
    for key in ("drawer.panel","settings","dialog.panel","guide.shell","player.chrome","player.channels","chooser.card.infinity","chooser.card.cobra"):
        require(ratio(text,styles[key]["fill"])>=4.5,f"{mode}: low contrast on {key}")

oled=d["variants"]["oled"]
require(oled["styles"]["screen"]["fill"]=="#FF000000","OLED root must be true black")
require(oled["colors"]["palette.background"]=="#FF000000","OLED palette root must be true black")

motion=d["base"].get("numbers",{}).get("chooser.layout.motion_ms")
require(isinstance(motion,(int,float)) and 0<=motion<=250,"motion budget exceeded")

renderer=ROOT/"repairs/cobra-theme-runtime-2103160/CobraVisualRenderer.java.in"
runtime=ROOT/"repairs/cobra-theme-runtime-2103160/CobraVisualTheme.java.in"
runtime_test=ROOT/"repairs/cobra-theme-runtime-2103160/tests/CobraVisualRuntimeTest.java"
layout_test=ROOT/"repairs/cobra-theme-runtime-2103160/tests/CobraVisualLayoutTest.java"
theme_rotation=ROOT/"repairs/cobra-theme-rotation-2103162/tests/Cobra2103162ThemeRotationTest.java"
pip_test=ROOT/"repairs/cobra-inner-insets-pip-return-2103165/tests/Cobra2103165InsetsPipPlayerTest.java"
freeze=ROOT/"repairs/cobra-final-feature-freeze-2103177/tests/Cobra2103177FinalFeatureFreezeTest.java"
mini=ROOT/"repairs/cobra-timeshift-miniplayer-2103178/tests/Cobra2103178TimeshiftMiniPlayerTest.java"
buffer=ROOT/"repairs/cobra-buffer-resilience-2103179/tests/Cobra2103179BufferResilienceTest.java"
ci179=ROOT/"repairs/cobra-buffer-resilience-2103179/ci.py"

pins={
 renderer:"70260208842b1c1059f2938688e5e84ffb28836e",
 runtime:"3ff720be9fde73bdcd78089a99cc25f637132acf",
 runtime_test:"013645540b4061e8e27e96d5eda6575259ad1c95",
 layout_test:"e7bc4ccde2be13fadc04f7bdfa6808879b283130",
 theme_rotation:"73065e7df48cb3eff243e2fd9711dc1088f924b7",
 pip_test:"d9b81e1ee8610c4885c537b19772071303bf3c22",
 freeze:"565d84774949986219073234db06a362c80eef03",
 mini:"b7d59b04f2add307df6deadbfc36a50d31e9f4a8",
 buffer:"a7f970ce4a8323d8f3cb3b4e1e91e9f2e1676422",
 ci179:"4c116ab0ef4e2bdba25188cee94f3982f6b83cef"
}
for path,sha in pins.items():
    require(path.is_file() and blob_sha(path)==sha,"protected runtime/test drift: "+str(path.relative_to(ROOT)))

r=renderer.read_text()
require(r.count("view instanceof TextureView||view instanceof SurfaceView||view instanceof android.webkit.WebView")>=2,"video-surface protection missing")
require('if(width>0&&width<360)return "cover"' in r,"cover classifier missing")
require('if(q.smallestScreenWidthDp>=600)return "tablet"' in r,"Fold/tablet classifier missing")
require("ValueAnimator.areAnimatorsEnabled()" in r,"system animation-disable policy missing")
require("depth>24||++count[0]>512" in r,"theme traversal bound missing")

require("textureViewsAreNeverStyledRecreatedOrReparented" in runtime_test.read_text(),"TextureView regression test missing")
require("themeInstallDoesNotReplaceGuideOrItsVideoTexture" in runtime_test.read_text(),"guide/video identity test missing")
require("fullscreenToPreviewReleasesRotationWithoutReplacingThePlayer" in theme_rotation.read_text(),"player handoff identity test missing")
p=pip_test.read_text()
for token in ("nativePipExpansionWithoutLauncherKeepsFullscreenSurface","launcherReturnRemovesOrphanedFullscreenSurface","configurationRefreshCannotLeaveBrowseFullscreen"):
    require(token in p,"PiP regression gate missing: "+token)
require("autoChoosesHighestSupportedRefresh" in freeze.read_text(),"120Hz policy gate missing")
require("refreshPolicyStillRequests120WhenSupported" in mini.read_text(),"mini-player refresh gate missing")
b=buffer.read_text()
for token in ("multitaskResizeStopPreservesPlayback","automaticLiveEdgeRecoveryIsBudgetedLikePassedPlaybackAudit","approved120HzPolicyStillWorks"):
    require(token in b,"buffer/timeshift gate missing: "+token)
c=ci179.read_text()
require("total==161" in c,"inherited Android acceptance count changed")

DIST.mkdir(exist_ok=True)
report={
  "status":"PASS",
  "scope":"Cobra Liquid Glass HM SAFE v1.1 automated safety audit",
  "base_commit":"0560b18c497e9861864126d96f9b784e488ebe32",
  "user_reported_v1_regression_acknowledged":True,
  "global_style_cascades":False,
  "scoped_surface_styles":len(SAFE_KEYS),
  "ordinary_buttons_text_panels_use_builtin_rendering":True,
  "layout_geometry_overrides":False,
  "binary_assets":0,
  "fold_cover":"PASS - no layout variants/geometry ownership",
  "oled":"PASS - true black root, scoped surfaces only",
  "pip":"PASS - runtime and inherited PiP gates pinned",
  "mini_player_timeshift":"PASS - protected 2103178/2103179 gates pinned",
  "animations":"PASS - bounded motion and system disable policy retained",
  "performance":"PASS - no images/fonts, no geometry overrides, bounded tree traversal",
  "physical_device_verified":False,
  "visual_device_acceptance_required":True,
  "warning":"Do not call SAFE v1.1 physically certified until it is visibly navigable on the user's device."
}
(DIST/"safe-audit.json").write_text(json.dumps(report,indent=2)+"\n")
print("PASS: Liquid Glass SAFE v1.1 automated safety audit")
print(json.dumps(report,indent=2))
