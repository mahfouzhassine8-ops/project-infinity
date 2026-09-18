#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,re

REL=Path("tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in")

def sha(v):return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()

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
 text=(a.source/REL).read_text();patch=json.loads(a.patch.read_text())
 watchdog=text[text.index("private long mBufferingSince"):text.index("private final Runnable mAutoRefresh")]
 build=method(text,"buildPlayer")
 promote=method(text,"promoteCobraPreviewToFullscreen")
 preview=method(text,"startCobraPreview")
 error=method(text,"onPlayerError")
 ready=method(text,"onPlaybackStateChanged")
 checks={}
 checks["exact_base"]=patch.get("base_build")==2103171 and patch.get("base_commit")=="59cf1958e5d911ede8df9b04c200025f4b39026e"
 checks["watchdog_no_prepare"]="mPlayer.prepare()" not in watchdog and "mPlayer.play()" not in watchdog
 checks["watchdog_keeps_observing"]="STATE_BUFFERING" in watchdog and "postDelayed(this,4000L)" in watchdog
 checks["watchdog_diagnostic"]="buffer_wait_network" in watchdog and "stallReportMs()" in watchdog
 checks["single_buffer_headroom"]="return multi?6000:15000" in text and "return multi?30000:60000" in text
 checks["single_rebuffer_threshold"]="return multi?3000:5000" in text
 checks["single_target_headroom"]="return (multi?12:48)*1024*1024" in text
 checks["single_prioritizes_time"]="return !multi" in text and "setPrioritizeTimeOverSizeThresholds(CobraBufferingPolicy.prioritizeTime(multi))" in build
 checks["multi_profile_preserved"]="multi?6000:15000" in text and "multi?30000:60000" in text and "multi?3000:5000" in text
 checks["http_timeouts_preserved"]=".setConnectTimeoutMs(15000)" in build and ".setReadTimeoutMs(30000)" in build
 checks["same_session_promotion"]="ExoPlayer session=" in promote and "mPlayer=session" in promote and ".prepare()" not in promote
 checks["same_channel_preview_guard"]="mCobraPreviewPlayer!=null&&cobraChannelKey(channel).equals(mCobraPreviewSessionKey)" in preview
 checks["new_preview_prepares_once"]="setMediaItem(mediaItem(channel.primaryUrl));mCobraPreviewPlayer.prepare()" in preview
 checks["fallback_only_on_error"]="onPlayerError" in error and "player.setMediaItem(mediaItem(channel.fallbackUrl));player.prepare()" in error
 checks["ready_clears_stall_state"]="mBufferStallReported=false" in ready and "mBufferingSince=0L" in ready
 checks["native_unchanged"]=patch.get("native_changed") is False
 checks["preview_contract_claim"]=patch.get("preview_fullscreen_reuses_session") is True
 failed=[k for k,v in checks.items() if not v]
 result={"passed":not failed,"checks":checks,"failed":failed,"physical_device_verified":False}
 a.out.mkdir(parents=True,exist_ok=True);(a.out/"source-audit.json").write_text(json.dumps(result,indent=2)+"\n")
 if failed:raise RuntimeError("2103173 buffering source audit failed: "+", ".join(failed))
 print("PASS:",len(checks),"buffering/session source checks")
if __name__=="__main__":main()
