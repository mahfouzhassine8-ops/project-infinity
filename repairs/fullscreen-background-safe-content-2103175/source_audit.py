#!/usr/bin/env python3
from pathlib import Path
import argparse,json,re

ACT=Path("tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in")
SPLASH=Path("tools/android/packaging/xbmc/src/Splash.java.in")

def matches(text,name):
 return list(re.finditer(r'^[ \t]{2,}(?:(?:@Override(?:[ \t]*\n[ \t]+|[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',text,re.M))

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
 patch=json.loads(a.patch.read_text());act=(a.source/ACT).read_text();splash=(a.source/SPLASH).read_text()
 build=method(act,"buildShell");bars=method(act,"cobraApplySystemBarsForSurface");confirm=method(act,"cobraConfirmBrowseSystemBars");safe=method(act,"cobraInstallBrowseSafeArea")
 scene=method(splash,"showVisualExperienceScene");styled=method(splash,"showStyledInfinityExperienceChooser");chooserBars=method(splash,"cobraPrepareExperienceSystemBars")
 checks={
  "exact_parent":patch.get("base_build")==2103171 and patch.get("base_commit")=="59cf1958e5d911ede8df9b04c200025f4b39026e",
  "browse_backdrop_separate":'mCobraBrowseBackground.setTag("cobra-browse-background")' in build and 'mRoot.setTag("cobra-browse-safe-content")' in build,
  "browse_backdrop_full_match_parent":build.count("FrameLayout.LayoutParams.MATCH_PARENT")>=4,
  "browse_root_transparent":"mRoot.setBackgroundColor(Color.TRANSPARENT)" in build,
  "screen_role_on_backdrop":'vtheme().paint(mCobraBrowseBackground,"screen")' in build,
  "screen_role_not_on_stage":'vtheme().paint(mStage,"screen")' not in build,
  "browse_safe_area_still_on_root":"root.setOnApplyWindowInsetsListener" in safe and "stableVerticalInsets" in safe,
  "browse_edge_to_edge_preserved":"SYSTEM_UI_FLAG_LAYOUT_STABLE|View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN" in bars,
  "browse_bar_never_repaints_root":"setBackgroundColor(barColor)" not in bars and "setBackgroundColor(barColor)" not in confirm,
  "chooser_visual_background_separate":'setTag("experience-safe-content")' in scene and "root.addView(new ExperienceBackdrop(theme)" in scene,
  "chooser_styled_background_separate":'setTag("experience-safe-content")' in styled and "root.addView(new ExperienceBackdrop(theme)" in styled,
  "chooser_root_unpadded":"root.setPadding(0,0,0,0)" in chooserBars,
  "chooser_safe_content_inset":"safeContent.setOnApplyWindowInsetsListener" in chooserBars and "safeContent.requestApplyInsets()" in chooserBars,
  "chooser_root_not_inset":"root.setOnApplyWindowInsetsListener" not in chooserBars,
  "chooser_edge_to_edge_preserved":"WindowCompat.setDecorFitsSystemWindows(window,false)" in chooserBars and "setStatusBarColor(android.graphics.Color.TRANSPARENT)" in chooserBars,
  "chooser_transient_zero_guard":"stableVerticalInsets" in chooserBars,
  "approved_chooser_top_padding":'compactHeight?8:vtheme().dimension("chooser.showStyledInfinityExperienceChooser.dimensions.1",20)' in styled,
  "approved_chooser_identity_height":'compactHeight?74:vtheme().dimension("chooser.showStyledInfinityExperienceChooser.dimensions.8",98)' in styled,
  "approved_chooser_title_gap":'compactHeight?6:vtheme().dimension("chooser.showStyledInfinityExperienceChooser.dimensions.9",18)' in styled,
  "approved_chooser_card_gap":'compactHeight?10:vtheme().dimension("chooser.showStyledInfinityExperienceChooser.dimensions.10",26)' in styled,
  "player_unchanged":patch.get("player_changed") is False,
  "playback_unchanged":patch.get("playback_changed") is False,
  "native_unchanged":patch.get("native_changed") is False,
 }
 failed=[k for k,v in checks.items() if not v]
 result={"passed":not failed,"checks":checks,"failed":failed,"physical_device_verified":False}
 a.out.mkdir(parents=True,exist_ok=True);(a.out/"source-audit.json").write_text(json.dumps(result,indent=2)+"\n")
 if failed:raise RuntimeError("2103175 source audit failed: "+", ".join(failed))
 print("PASS:",len(checks),"full-window background/safe-content source checks")
if __name__=="__main__":main()
