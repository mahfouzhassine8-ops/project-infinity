#!/usr/bin/env python3
"""2103173: reduce self-inflicted rebuffer loops on exact locked 2103171.

The current live-player stall watchdog calls prepare() again while ExoPlayer is already
BUFFERING. That can restart loading before the HTTP read-timeout/fallback path is allowed
to finish. This delta removes that restart, keeps the same player/session alive, and gives
single-view playback modest additional time/byte headroom. Multi-View remains bounded.
"""
from pathlib import Path
import argparse,hashlib,json,re

REL=Path("tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in")
BASE_BUILD=2103171
BASE_COMMIT="59cf1958e5d911ede8df9b04c200025f4b39026e"

def sha(v):return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()

def matches(text,name):
    return list(re.finditer(
        r'^  (?:(?:@Override(?:[ \t]*\n  |[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'
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
    count=text.count(old)
    if count!=1:raise RuntimeError(f"{label}: expected one anchor, got {count}")
    return text.replace(old,new,1)

POLICY=r'''  static final class CobraBufferingPolicy {
    static int minBufferMs(boolean multi){return multi?6000:15000;}
    static int maxBufferMs(boolean multi){return multi?30000:60000;}
    static int playbackMs(boolean multi){return 1500;}
    static int rebufferMs(boolean multi){return multi?3000:5000;}
    static int targetBufferBytes(boolean multi){return (multi?12:48)*1024*1024;}
    static boolean prioritizeTime(boolean multi){return !multi;}
    static long stallReportMs(){return 12000L;}
  }'''

OLD_STALL=r'''  private long mBufferingSince = 0L;
  private final Runnable mStallWatchdog = new Runnable() {
    @Override public void run() {
      if ((mBackgroundStopped && !isCobraInPictureInPicture())
          || mPlayer == null || !mPlayer.getPlayWhenReady()) {
        mBufferingSince = 0L; return;
      }
      if (mPlayer.getPlaybackState() == Player.STATE_BUFFERING) {
        if (mBufferingSince == 0L) mBufferingSince = System.currentTimeMillis();
        if (System.currentTimeMillis() - mBufferingSince >= 12000L) {
          if(!cobraPermitBufferRetry(mPlayer)){mBufferingSince=0L;return;}
          mPlaybackRetryCount++;
          try { mPlayer.prepare(); mPlayer.play(); } catch (Exception ignored) {}
          mBufferingSince = System.currentTimeMillis();
        }
        mMain.postDelayed(this, 4000L);
      } else { mBufferingSince = 0L; }
    }
  };'''

NEW_STALL=r'''  private long mBufferingSince = 0L;
  private boolean mBufferStallReported = false;
  private final Runnable mStallWatchdog = new Runnable() {
    @Override public void run() {
      if ((mBackgroundStopped && !isCobraInPictureInPicture())
          || mPlayer == null || !mPlayer.getPlayWhenReady()) {
        mBufferingSince = 0L;mBufferStallReported=false;return;
      }
      if (mPlayer.getPlaybackState() == Player.STATE_BUFFERING) {
        long now=System.currentTimeMillis();
        if (mBufferingSince == 0L) {mBufferingSince=now;mBufferStallReported=false;}
        // Do not call prepare()/play() while Media3 is already loading. The old 12-second
        // watchdog could reset the same live request before the 30-second HTTP timeout and
        // fallback/error path had a chance to complete, producing repeated buffer loops.
        if(!mBufferStallReported&&now-mBufferingSince>=CobraBufferingPolicy.stallReportMs()){
          CobraPlayerBinding binding=mCobraPlayerBindings.get(mPlayer);
          if(binding!=null&&binding.current()){
            binding.vitals.lastRecovery="buffer_wait_network";
            InfinityCobraDiagnostics.record(InfinityLiveActivity.this,"buffering","waiting",
                "same_session=true; elapsed_ms="+(now-mBufferingSince));
          }
          mBufferStallReported=true;
        }
        mMain.postDelayed(this,4000L);
      } else {mBufferingSince=0L;mBufferStallReported=false;}
    }
  };'''

def apply(source,receipt_path,out):
    source=Path(source);receipt_path=Path(receipt_path);out=Path(out)
    receipt=json.loads(receipt_path.read_text())
    if receipt.get("version_code")!=BASE_BUILD:
        raise RuntimeError("Expected exact locked 2103171 source receipt")
    expected=receipt.get("files",{}).get(str(REL),{}).get("after")
    if not expected:raise RuntimeError("2103171 Activity identity missing from source receipt")

    path=source/REL;before_bytes=path.read_bytes();before=before_bytes.decode()
    if sha(before_bytes)!=expected:raise RuntimeError("2103171 Activity preimage mismatch")

    protected=[
      "promoteCobraPreviewToFullscreen","startCobraPreview","startSinglePlayer",
      "cobraStartOwnedMiniPlayback","cobraEndMiniBackgroundPlayback",
      "onUserLeaveHint","onStop","onPictureInPictureModeChanged",
      "cobraApplySystemBarsForSurface","cobraInstallBrowseSafeArea",
      "cobraAttachVideo","cobraDisposePlayer"
    ]
    protected_before={n:sha(method(before,n)) for n in protected}

    if OLD_STALL not in before:raise RuntimeError("Stall-watchdog preimage drift")
    text=once(before,OLD_STALL,NEW_STALL,"stall watchdog")

    build=method(text,"buildPlayer")
    old_buffer='''.setBufferDurationsMs(multi?6000:10000,multi?30000:60000,1500,3000)
        .setTargetBufferBytes((multi?12:32)*1024*1024).setPrioritizeTimeOverSizeThresholds(false).build();'''
    new_buffer='''.setBufferDurationsMs(CobraBufferingPolicy.minBufferMs(multi),CobraBufferingPolicy.maxBufferMs(multi),
            CobraBufferingPolicy.playbackMs(multi),CobraBufferingPolicy.rebufferMs(multi))
        .setTargetBufferBytes(CobraBufferingPolicy.targetBufferBytes(multi))
        .setPrioritizeTimeOverSizeThresholds(CobraBufferingPolicy.prioritizeTime(multi)).build();'''
    if build.count(old_buffer)!=1:raise RuntimeError("LoadControl preimage drift")
    build=build.replace(old_buffer,new_buffer,1)
    build=build.replace(
      "// Bound *compressed* buffering as well as time; four 180-second buffers were not a safe default.",
      "// Single-view gets more resilient time/byte headroom; Multi-View stays conservatively bounded.",1)
    text=replace_method(text,"buildPlayer",build)

    state=method(text,"onPlaybackStateChanged")
    old_ready="mBufferingSince=0L;mMain.removeCallbacks(mStallWatchdog);"
    new_ready="mBufferingSince=0L;mBufferStallReported=false;mMain.removeCallbacks(mStallWatchdog);"
    if state.count(old_ready)!=1:raise RuntimeError("Playback READY reset anchor drift")
    state=state.replace(old_ready,new_ready,1)
    text=replace_method(text,"onPlaybackStateChanged",state)

    if "static final class CobraBufferingPolicy" in text:raise RuntimeError("Buffering policy already exists")
    pos=text.rfind("\n}")
    if pos<0:raise RuntimeError("Activity class terminator missing")
    text=text[:pos]+"\n"+POLICY+"\n"+text[pos:]

    for n,h in protected_before.items():
        if sha(method(text,n))!=h:raise RuntimeError("Protected playback/lifecycle method changed: "+n)

    watchdog=text[text.index("private long mBufferingSince"):text.index("private final Runnable mAutoRefresh")]
    if "mPlayer.prepare()" in watchdog or "mPlayer.play()" in watchdog:
        raise RuntimeError("Buffering watchdog still restarts the player")
    if "buffer_wait_network" not in watchdog or "stallReportMs()" not in watchdog:
        raise RuntimeError("Buffering diagnostics contract missing")

    build_after=method(text,"buildPlayer")
    for token in (
      "CobraBufferingPolicy.minBufferMs(multi)",
      "CobraBufferingPolicy.targetBufferBytes(multi)",
      "CobraBufferingPolicy.prioritizeTime(multi)",
      ".setConnectTimeoutMs(15000)",
      ".setReadTimeoutMs(30000)",
    ):
        if token not in build_after:raise RuntimeError("Buffering policy contract missing: "+token)

    promote=method(text,"promoteCobraPreviewToFullscreen")
    if "ExoPlayer session=" not in promote or "mPlayer=session" not in promote or ".prepare()" in promote:
        raise RuntimeError("Preview->fullscreen no-reconnect contract drift")

    out.mkdir(parents=True,exist_ok=True);(out/"source-before").mkdir(exist_ok=True)
    (out/"source-before"/path.name).write_bytes(before_bytes)
    after=text.encode();path.write_bytes(after)
    report={
      "base_build":BASE_BUILD,"base_commit":BASE_COMMIT,
      "files":{str(REL):{"before":sha(before_bytes),"after":sha(after)}},
      "changed":["stall-watchdog","buildPlayer","onPlaybackStateChanged"],
      "new_helpers":["CobraBufferingPolicy"],
      "protected_methods":protected_before,
      "single_buffer_ms":{"min":15000,"max":60000,"playback":1500,"rebuffer":5000},
      "single_target_bytes":48*1024*1024,
      "multi_buffer_ms":{"min":6000,"max":30000,"playback":1500,"rebuffer":3000},
      "multi_target_bytes":12*1024*1024,
      "watchdog_reprepare_removed":True,
      "http_timeouts_unchanged":True,
      "preview_fullscreen_reuses_session":True,
      "native_changed":False,"physical_device_verified":False
    }
    (out/"patch.json").write_text(json.dumps(report,indent=2)+"\n")
    print("PASS: 2103173 buffering stability delta; no watchdog re-prepare, same session preserved")

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--source",type=Path,required=True);p.add_argument("--receipt",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();apply(a.source,a.receipt,a.out)
