#!/usr/bin/env python3
from pathlib import Path
import argparse, importlib.util, json, re, hashlib

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("p162",ROOT/"apply.py")
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

def method(text,name):
 a,b=p.span(text,name);return text[a:b]

def strip_lines(text,needles):
 out=[]
 for line in text.splitlines():
  if any(n in line for n in needles):continue
  out.append(line)
 return "\n".join(out)

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--source",type=Path,required=True);ap.add_argument("--out",type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 live=(a.source/p.LIVE).read_text();theme=(a.source/p.THEME).read_text()
 assert p.sha_text(live)==p.LIVE_PRE,(p.sha_text(live),p.LIVE_PRE)
 assert p.sha_text(theme)==p.THEME_PRE,(p.sha_text(theme),p.THEME_PRE)
 after=p.patch_live(live);after_theme=p.patch_theme(theme)
 checks=0

 # Untouched functional owners must remain byte-identical.
 protected=["buildPlayer","startCobraPlayer","cobraLayoutGuide","cobraRenderGuideBrowser",
            "cobraSavePreferences","cobraPreferenceKey","loadGuideAsync","mediaItem",
            "cobraFreshHealthSnapshot","showCobraHealthCenter","configureCobraPip"]
 unchanged=[]
 for name in protected:
  try:b=method(live,name);c=method(after,name)
  except RuntimeError:continue
  assert b==c,name;unchanged.append(name);checks+=1

 # Lifecycle changes are orientation-only.
 for name,needle in [
   ("onPause",'cobraRequestPlayerOrientation(android.content.pm.ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,"pause")'),
   ("onStop",'cobraRequestPlayerOrientation(android.content.pm.ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,"stop")'),
   ("onResume",'cobraApplyPlayerRotation("resume")'),
   ("onPictureInPictureModeChanged",'cobraApplyPlayerRotation("pip")'),
   ("onMultiWindowModeChanged",'cobraApplyPlayerRotation("multi-window")')]:
  b=method(live,name);c=method(after,name);assert needle in c
  assert strip_lines(c,[needle])==strip_lines(b,[]),name;checks+=2

 # closePlayer/openMultiView only add orientation release/reference clearing.
 for name,needles in [
   ("closePlayer",["cobraRequestPlayerOrientation(android.content.pm.ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED","mCobraPlayerRotationButton=null"]),
   ("openMultiView",["cobraRequestPlayerOrientation(android.content.pm.ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED","mCobraPlayerRotationButton=null"])]:
  b=method(live,name);c=method(after,name)
  for n in needles:assert n in c;checks+=1
  assert strip_lines(c,needles)==strip_lines(b,[]),name;checks+=1

 # Single-player start/ownership remains byte-identical. Rotation observes the existing
 # CobraPlayerBinding callbacks instead of adding another listener.
 b=method(live,"startSinglePlayer");c=method(after,"startSinglePlayer")
 assert b==c;checks+=1
 for before_token,after_token in [
   ('@Override public void onVideoSizeChanged(VideoSize size){if(current())cobraFitBinding(this);}',
    '@Override public void onVideoSizeChanged(VideoSize size){if(current()){cobraFitBinding(this);if(player==mPlayer)cobraApplyPlayerRotation("video-size");}}'),
   ('@Override public void onIsPlayingChanged(boolean playing){if(current())cobraUpdatePlaybackLabels();}',
    '@Override public void onIsPlayingChanged(boolean playing){if(current()){if(player==mPlayer)cobraApplyPlayerRotation("is-playing");cobraUpdatePlaybackLabels();}}'),
   ('@Override public void onPlaybackStateChanged(int state) {\n      if(!current())return;',
    '@Override public void onPlaybackStateChanged(int state) {\n      if(!current())return;\n      if(player==mPlayer)cobraApplyPlayerRotation("playback-state");')]:
  assert before_token in live and after_token in after,(before_token,after_token);checks+=1

 # Theme setting is one row in Settings, not three recovery rows + reload.
 settings=method(after,"showSettings")
 for token in ["cobra_theme_management","showCobraVisualThemePicker()","THEME  •  ","BACKGROUND MODE"]:
  assert token in settings,token;checks+=1
 for old in ["PREVIOUS VISUAL THEME","REMOVE VISUAL THEME","RELOAD COBRA UI THEME",
             "INSTALL COBRA UI / VISUAL THEME ZIP","cobra_visual_theme_state"]:
  assert old not in settings,old;checks+=1
 picker=method(after,"showCobraVisualThemePicker")
 for token in ["Built-in appearance","Installed visual theme","Install / replace theme ZIP",
               "restoreBuiltIn","restorePrevious","openCobraUiPackagePicker"]:
  assert token in picker,token;checks+=1

 # Exact Infinity rotation semantics are reused; no system-setting or playback ownership.
 for token in ['"infinity_player_rotation"','"mode"',"COBRA_ROTATION_FOLLOW_DEVICE=0",
               "COBRA_ROTATION_UNLOCKED=1","SCREEN_ORIENTATION_FULL_SENSOR",
               "SCREEN_ORIENTATION_UNSPECIFIED",'mPlayer!=null&&mPlayer.getVideoFormat()!=null',
               '"android.software.leanback"']:
  assert token in after,token;checks+=1
 for forbidden in ["ACCELEROMETER_ROTATION","Settings.System","setMediaItem(","prepare()","release()","stop()"]:
  for name in ["cobraTogglePlayerRotation","cobraApplyPlayerRotation","cobraRequestPlayerOrientation",
               "cobraPlayerRotationMode","cobraRotationConstrained","cobraHasActiveVideo"]:
   try:body=method(after,name)
   except RuntimeError:continue
   assert forbidden not in body,(name,forbidden)
  checks+=1

 chrome=method(after,"cobraBuildPlayerChrome")
 assert chrome.index('setTag("cobra_player_rotation")')<chrome.index('cobraIcon("lock","Lock controls"');checks+=1
 assert '"rotate".equals(glyph)' in after;checks+=1
 assert "BUILD=2103162" in after_theme;checks+=1

 result={"checks":checks,"unchanged_methods":unchanged,
         "rotation":"Infinity Follow Device / Unlocked semantics shared via infinity_player_rotation",
         "theme_ui":"single Theme row with built-in, installed-theme restore, install/replace",
         "native_engine_changed":False,"physical_device_verified":False}
 (a.out/"source-tests.json").write_text(json.dumps(result,indent=2)+"\n")
 print("PASS:",checks,"source assertions;",len(unchanged),"functional owners byte-identical")
if __name__=="__main__":main()
