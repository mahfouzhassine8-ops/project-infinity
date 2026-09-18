#!/usr/bin/env python3
"""2103174: restore pre-2103153 single-view buffering behavior over locked 2103171.

Audit finding:
- Pre-2103153 single-view players used Media3's normal DefaultLoadControl.
- 2103153 introduced a much shallower custom single-view profile:
  min=10s, max=60s, startup=1.5s, rebuffer=3s, explicit 32 MiB target.
- The inherited 12s stall watchdog could also call prepare() on an already-buffering
  player, restarting the same load.

This delta restores normal Media3 LoadControl for single-view playback, preserves the
memory-bounded Multi-View profile, and makes the watchdog observational only.
"""
from pathlib import Path
import argparse,hashlib,json,re

REL=Path("tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in")
BASE_BUILD=2103171
BASE_COMMIT="59cf1958e5d911ede8df9b04c200025f4b39026e"

def sha(v):return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()

def matches(text,name):
    return list(re.finditer(
        r'^[ \t]{2,}(?:(?:@Override(?:[ \t]*\n[ \t]+|[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'
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
    c=text.count(old)
    if c!=1:raise RuntimeError(f"{label}: expected one anchor, got {c}")
    return text.replace(old,new,1)

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
        mBufferingSince=0L;mBufferStallReported=false;return;
      }
      if (mPlayer.getPlaybackState() == Player.STATE_BUFFERING) {
        long now=System.currentTimeMillis();
        if(mBufferingSince==0L){mBufferingSince=now;mBufferStallReported=false;}
        // Observe a long buffer; never restart a request that Media3 is already loading.
        if(!mBufferStallReported&&now-mBufferingSince>=12000L){
          CobraPlayerBinding binding=mCobraPlayerBindings.get(mPlayer);
          if(binding!=null&&binding.current()){
            binding.vitals.lastRecovery="buffer_wait_network";
            InfinityCobraDiagnostics.record(InfinityLiveActivity.this,"buffering","waiting",
                "same_session=true; elapsed_ms="+(now-mBufferingSince));
          }
          mBufferStallReported=true;
        }
        mMain.postDelayed(this,4000L);
      }else{mBufferingSince=0L;mBufferStallReported=false;}
    }
  };'''

PROFILE=r'''  static final class CobraBufferRegressionProfile {
    static boolean singleUsesMedia3Defaults(){return true;}
    static int multiMinMs(){return 6000;}
    static int multiMaxMs(){return 30000;}
    static int multiStartMs(){return 1500;}
    static int multiRebufferMs(){return 3000;}
    static int multiTargetBytes(){return 12*1024*1024;}
    static long stallObservationMs(){return 12000L;}
  }'''

def apply(source,receipt_path,out):
    source=Path(source);receipt_path=Path(receipt_path);out=Path(out)
    receipt=json.loads(receipt_path.read_text())
    if receipt.get("version_code")!=BASE_BUILD:
        raise RuntimeError("Expected exact locked 2103171 source receipt")
    expected=receipt.get("files",{}).get(str(REL),{}).get("after")
    if not expected:raise RuntimeError("2103171 Activity identity missing")
    path=source/REL;before_bytes=path.read_bytes();before=before_bytes.decode()
    if sha(before_bytes)!=expected:raise RuntimeError("2103171 Activity preimage mismatch")

    protected=[
      "promoteCobraPreviewToFullscreen","startCobraPreview","startSinglePlayer",
      "cobraStartOwnedMiniPlayback","cobraEndMiniBackgroundPlayback",
      "onUserLeaveHint","onStop","onPictureInPictureModeChanged",
      "cobraApplySystemBarsForSurface","cobraInstallBrowseSafeArea",
      "cobraAttachVideo","cobraDisposePlayer","cobraReattachObservedSurface"
    ]
    protected_before={n:sha(method(before,n)) for n in protected}

    text=once(before,OLD_STALL,NEW_STALL,"stall watchdog")

    build=method(text,"buildPlayer")
    old='''    boolean multi=mCobraCreatingMulti;
    // Bound *compressed* buffering as well as time; four 180-second buffers were not a safe default.
    DefaultLoadControl control=new DefaultLoadControl.Builder()
        .setBufferDurationsMs(multi?6000:10000,multi?30000:60000,1500,3000)
        .setTargetBufferBytes((multi?12:32)*1024*1024).setPrioritizeTimeOverSizeThresholds(false).build();'''
    new='''    boolean multi=mCobraCreatingMulti;
    // Single-view returns to the pre-2103153 Media3 default LoadControl. Multi-View keeps
    // its explicit memory-bounded profile so concurrent tiles cannot each consume a full buffer.
    DefaultLoadControl control;
    if(multi){
      control=new DefaultLoadControl.Builder()
          .setBufferDurationsMs(CobraBufferRegressionProfile.multiMinMs(),
              CobraBufferRegressionProfile.multiMaxMs(),
              CobraBufferRegressionProfile.multiStartMs(),
              CobraBufferRegressionProfile.multiRebufferMs())
          .setTargetBufferBytes(CobraBufferRegressionProfile.multiTargetBytes())
          .setPrioritizeTimeOverSizeThresholds(false).build();
    }else{
      control=new DefaultLoadControl();
    }'''
    if build.count(old)!=1:raise RuntimeError("2103153 custom LoadControl preimage drift")
    build=build.replace(old,new,1)
    text=replace_method(text,"buildPlayer",build)

    state=method(text,"onPlaybackStateChanged")
    old_ready="mBufferingSince=0L;mMain.removeCallbacks(mStallWatchdog);"
    if state.count(old_ready)!=1:raise RuntimeError("READY buffering reset anchor drift")
    state=state.replace(old_ready,"mBufferingSince=0L;mBufferStallReported=false;mMain.removeCallbacks(mStallWatchdog);",1)
    text=replace_method(text,"onPlaybackStateChanged",state)

    if "static final class CobraBufferRegressionProfile" in text:raise RuntimeError("Profile helper exists")
    pos=text.rfind("\n}")
    if pos<0:raise RuntimeError("Activity class terminator missing")
    text=text[:pos]+"\n"+PROFILE+"\n"+text[pos:]

    for n,h in protected_before.items():
        if sha(method(text,n))!=h:raise RuntimeError("Protected contract changed: "+n)

    watchdog=text[text.index("private long mBufferingSince"):text.index("private final Runnable mAutoRefresh")]
    if "mPlayer.prepare()" in watchdog or "mPlayer.play()" in watchdog or "cobraPermitBufferRetry" in watchdog:
        raise RuntimeError("Watchdog can still restart buffering playback")

    build_after=method(text,"buildPlayer")
    for token in ("if(multi)","control=new DefaultLoadControl();","CobraBufferRegressionProfile.multiTargetBytes()",
                  ".setConnectTimeoutMs(15000)",".setReadTimeoutMs(30000)"):
        if token not in build_after:raise RuntimeError("LoadControl contract missing: "+token)

    # Recovery is not allowed to act while Media3 reports actual BUFFERING.
    observe=method(text,"cobraObserveSessions")
    if "p.getPlaybackState()==Player.STATE_READY" not in observe or "p.isPlaying()" not in observe:
        raise RuntimeError("Surface recovery eligibility no longer requires READY/playing")
    reattach=method(text,"cobraReattachObservedSurface")
    for forbidden in (".prepare(", ".setMediaItem(", ".seekTo(", ".play("):
        if forbidden in reattach:raise RuntimeError("Surface recovery became a media restart path: "+forbidden)

    # Configured fallback remains single-use and error-only, never a STATE_BUFFERING action.
    err=method(text,"onPlayerError")
    if "fallback=true" not in err or "channel.fallbackUrl" not in err or "player.prepare()" not in err:
        raise RuntimeError("Existing error fallback contract missing")
    if "STATE_BUFFERING" in err:raise RuntimeError("Fallback incorrectly tied to buffering state")

    promote=method(text,"promoteCobraPreviewToFullscreen")
    if "ExoPlayer session=" not in promote or "mPlayer=session" not in promote or ".prepare()" in promote:
        raise RuntimeError("Preview-to-fullscreen session reuse drift")

    out.mkdir(parents=True,exist_ok=True);(out/"source-before").mkdir(exist_ok=True)
    (out/"source-before"/path.name).write_bytes(before_bytes)
    after=text.encode();path.write_bytes(after)
    report={
      "base_build":BASE_BUILD,"base_commit":BASE_COMMIT,
      "files":{str(REL):{"before":sha(before_bytes),"after":sha(after)}},
      "changed":["single-view-load-control","stall-watchdog","ready-stall-reset"],
      "new_helpers":["CobraBufferRegressionProfile"],
      "protected_methods":protected_before,
      "pre_2103153_single_view_behavior_restored":True,
      "single_view_load_control":"Media3 DefaultLoadControl",
      "multi_view":{"min_ms":6000,"max_ms":30000,"start_ms":1500,"rebuffer_ms":3000,"target_bytes":12582912},
      "watchdog_reprepare_removed":True,
      "surface_recovery_buffering_ineligible":True,
      "surface_recovery_reconnects_media":False,
      "fallback_error_only":True,
      "preview_fullscreen_reuses_session":True,
      "http_timeouts_unchanged":True,
      "native_changed":False,"physical_device_verified":False
    }
    (out/"patch.json").write_text(json.dumps(report,indent=2)+"\n")
    print("PASS: 2103174 restored pre-2103153 single-view buffering and removed self-reprepare")

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--source",type=Path,required=True);p.add_argument("--receipt",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();apply(a.source,a.receipt,a.out)
