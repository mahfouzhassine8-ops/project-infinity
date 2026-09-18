#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,re

REL=Path("tools/android/packaging/xbmc/src/Splash.java.in")
ACT=Path("tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in")

def sha(v):return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()
def matches(text,name):
 return list(re.finditer(r'^  (?:(?:@Override(?:[ \t]*\n  |[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',text,re.M))
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
 p=argparse.ArgumentParser();p.add_argument("--source",type=Path,required=True);p.add_argument("--patch",type=Path,required=True);p.add_argument("--receipt",type=Path,required=True);p.add_argument("--out",type=Path,required=True);a=p.parse_args()
 patch=json.loads(a.patch.read_text());receipt=json.loads(a.receipt.read_text())
 splash=(a.source/REL).read_text();activity=(a.source/ACT).read_bytes()
 expected=patch["files"][str(REL)]["after"]
 if sha(splash)!=expected:raise RuntimeError("Chooser source/postimage mismatch")
 # Activity is outside this repair and must remain exactly at the current reconstructed receipt.
 act_expected=receipt.get("files",{}).get(str(ACT),{}).get("after")
 if not act_expected or sha(activity)!=act_expected:raise RuntimeError("Cobra Activity changed outside chooser repair")

 helper=method(splash,"cobraPrepareExperienceSystemBars")
 icon=method(splash,"cobraChooserDarkStatusIcons")
 scene=method(splash,"showVisualExperienceScene")
 styled=method(splash,"showStyledInfinityExperienceChooser")
 checks={
  "exact_scope":patch.get("changed_methods")==["showVisualExperienceScene","showStyledInfinityExperienceChooser"],
  "activity_untouched":True,
  "both_themed_paths_hooked":all("cobraPrepareExperienceSystemBars(theme,root)" in block for block in (scene,styled)),
  "edge_to_edge":"WindowCompat.setDecorFitsSystemWindows(window,false)" in helper,
  "transparent_status":"setStatusBarColor(android.graphics.Color.TRANSPARENT)" in helper,
  "contrast_scrim_disabled":"setStatusBarContrastEnforced(false)" in helper,
  "resolved_underlay":"decor.setBackgroundColor(theme.background)" in helper,
  "status_visible":"controller.show(android.view.WindowInsets.Type.statusBars())" in helper,
  "icon_contrast":"APPEARANCE_LIGHT_STATUS_BARS" in helper and "186000" in icon,
  "safe_area":"WindowInsets.Type.systemBars()" in helper and "WindowInsets.Type.displayCutout()" in helper and "v.setPadding(left,top,right,bottom)" in helper,
  "transient_zero_stabilized":"stableVerticalInsets" in helper and "if(top>0)stableVerticalInsets[0]=top" in helper and "if(bottom>0)stableVerticalInsets[1]=bottom" in helper,
  "navigation_bar_not_owned":"setNavigationBarColor" not in helper and "navigationBars()" not in helper,
  "routing_not_owned":"setContentView(" not in helper and "startActivity(" not in helper,
  "legacy_fallback_preserved":"cobraPrepareExperienceSystemBars" not in method(splash,"showLegacyInfinityExperienceChooser"),
  "launch_ownership_preserved":"cobraPrepareExperienceSystemBars" not in method(splash,"launchInfinityExperience"),
  "native_unchanged":patch.get("native_changed") is False,
 }
 failed=[k for k,v in checks.items() if not v]
 result={"passed":not failed,"checks":checks,"failed":failed,"physical_device_verified":False}
 a.out.mkdir(parents=True,exist_ok=True);(a.out/"source-audit.json").write_text(json.dumps(result,indent=2)+"\n")
 if failed:raise RuntimeError("2103171 chooser source audit failed: "+", ".join(failed))
 print("PASS:",len(checks),"chooser system-bar source checks; Activity/native contracts untouched")
if __name__=="__main__":main()
