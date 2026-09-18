#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,re

REL=Path("tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in")
def sha(v):return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()
def matches(text,name):return list(re.finditer(r'^[ \t]{2,}(?:(?:@Override(?:[ \t]*\n[ \t]+|[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',text,re.M))
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
 build=method(text,"buildPlayer");observe=method(text,"cobraObserveSessions");reattach=method(text,"cobraReattachObservedSurface")
 error=method(text,"onPlayerError");promote=method(text,"promoteCobraPreviewToFullscreen")
 watchdog=text[text.index("private long mBufferingSince"):text.index("private final Runnable mAutoRefresh")]
 checks={
  "exact_parent":patch.get("base_commit")=="59cf1958e5d911ede8df9b04c200025f4b39026e",
  "single_default_load_control":"control=new DefaultLoadControl();" in build,
  "single_old_override_removed":"multi?6000:10000" not in build and "multi?12:32" not in build,
  "multi_bounded":"multiMinMs()" in build and "multiTargetBytes()" in build,
  "http_timeouts_unchanged":".setConnectTimeoutMs(15000)" in build and ".setReadTimeoutMs(30000)" in build,
  "watchdog_observational":"mPlayer.prepare()" not in watchdog and "mPlayer.play()" not in watchdog and "buffer_wait_network" in watchdog,
  "surface_only_ready":"p.getPlaybackState()==Player.STATE_READY" in observe and "p.isPlaying()" in observe,
  "surface_no_media_restart":all(x not in reattach for x in (".prepare(",".setMediaItem(",".seekTo(",".play(")),
  "fallback_error_only":"channel.fallbackUrl" in error and "player.prepare()" in error and "STATE_BUFFERING" not in error,
  "preview_fullscreen_same_session":"ExoPlayer session=" in promote and "mPlayer=session" in promote and ".prepare()" not in promote,
  "native_unchanged":patch.get("native_changed") is False
 }
 failed=[k for k,v in checks.items() if not v]
 result={"passed":not failed,"checks":checks,"failed":failed,"physical_device_verified":False}
 a.out.mkdir(parents=True,exist_ok=True);(a.out/"source-audit.json").write_text(json.dumps(result,indent=2)+"\n")
 if failed:raise RuntimeError("2103174 source audit failed: "+", ".join(failed))
 print("PASS:",len(checks),"end-to-end buffering source checks")
if __name__=="__main__":main()
