#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,re

REL=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
BASE_BUILD=2103178
LOCKED_COMMIT='56792d4e44b381cff2c900e7b86ed99265b55d04'

def sha(v): return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()
def once(s,a,b,label='anchor'):
    c=s.count(a)
    if c!=1: raise RuntimeError(f'{label}: expected one anchor, got {c}')
    return s.replace(a,b,1)

def method_matches(text,name):
    return list(re.finditer(r'^[ \t]{2,}(?:(?:@Override(?:[ \t]*\n[ \t]+|[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',text,re.M))
def class_matches(text,name):
    return list(re.finditer(r'^[ \t]{2,}(?:(?:private|public|protected|static|final)\s+)*class\s+'+re.escape(name)+r'\b',text,re.M))
def span(text,name,kind='method'):
    ms=method_matches(text,name) if kind=='method' else class_matches(text,name)
    if len(ms)!=1: raise RuntimeError(f'{kind} cardinality {name}={len(ms)}')
    start=ms[0].start();i=text.index('{',ms[0].end());d=0;q=None;esc=line=block=False
    while i<len(text):
        c=text[i];n=text[i+1] if i+1<len(text) else ''
        if line:
            if c=='\n': line=False
        elif block:
            if c=='*' and n=='/': block=False;i+=1
        elif q:
            if esc: esc=False
            elif c=='\\': esc=True
            elif c==q: q=None
        elif c=='/' and n=='/': line=True;i+=1
        elif c=='/' and n=='*': block=True;i+=1
        elif c in ('"',"'"): q=c
        elif c=='{': d+=1
        elif c=='}':
            d-=1
            if d==0:return start,i+1
        i+=1
    raise RuntimeError('unclosed '+name)
def member(text,name,kind='method'):
    a,b=span(text,name,kind);return text[a:b]
def replace_member(text,name,new,kind='method'):
    a,b=span(text,name,kind);return text[:a]+new.rstrip()+'\n'+text[b:]

def inner_method(text,name):
    ms=list(re.finditer(r'^[ \t]{4,}(?:(?:public|private|protected|static|final|synchronized)\s+)+[^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',text,re.M))
    if len(ms)!=1: raise RuntimeError(f'inner method cardinality {name}={len(ms)}')
    start=ms[0].start();i=text.index('{',ms[0].end());d=0;q=None;esc=line=block=False
    while i<len(text):
        c=text[i];n=text[i+1] if i+1<len(text) else ''
        if line:
            if c=='\n':line=False
        elif block:
            if c=='*' and n=='/':block=False;i+=1
        elif q:
            if esc:esc=False
            elif c=='\\':esc=True
            elif c==q:q=None
        elif c=='/' and n=='/':line=True;i+=1
        elif c=='/' and n=='*':block=True;i+=1
        elif c in ('"',"'"):q=c
        elif c=='{':d+=1
        elif c=='}':
            d-=1
            if d==0:return start,i+1
        i+=1
    raise RuntimeError('unclosed inner '+name)
def replace_inner(text,name,new):
    a,b=inner_method(text,name);return text[:a]+new.rstrip()+'\n'+text[b:]

TRANSPORT_POLICY=r'''
  static final class CobraTimeshiftTransportPolicy {
    static final int CONNECT_TIMEOUT_MS=7000;
    static final int READ_TIMEOUT_MS=5000;
    static final long INITIAL_BACKOFF_MS=250L;
    static final long MAX_BACKOFF_MS=1500L;
    static long nextBackoffMs(long current){return Math.min(MAX_BACKOFF_MS,Math.max(INITIAL_BACKOFF_MS,current)*2L);}
    static String httpHeader(String status,String type,long length,boolean noStore){
      return "HTTP/1.1 "+status+"\r\n"
          +"Content-Type: "+type+"\r\n"
          +"Content-Length: "+length+"\r\n"
          +"Cache-Control: "+(noStore?"no-cache, no-store":"no-cache")+"\r\n"
          +"Connection: close\r\n\r\n";
    }
    static String playlistHeader(long mediaSequence){
      return "#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:5\n"
          +"#EXT-X-MEDIA-SEQUENCE:"+mediaSequence+"\n"
          +"#EXT-X-START:TIME-OFFSET=-9.0,PRECISE=NO\n";
    }
    static boolean hasRealHttpFraming(String value){return value!=null&&value.contains("\r\n")&&!value.contains("\\\\r\\\\n")&&value.endsWith("\r\n\r\n");}
    static boolean hasRealPlaylistLines(String value){return value!=null&&value.startsWith("#EXTM3U\n")&&!value.contains("\\\\n");}
  }
'''

RESILIENCE_HELPERS=r'''
  static final class CobraWindowLifecyclePolicy {
    static boolean preservePlaybackOnStop(boolean inMultiWindow,boolean finishing){return inMultiWindow&&!finishing;}
  }
  static final class CobraTimeshiftRecoveryPolicy {
    static final long ADVANCE_WAIT_MS=12000L;
    static boolean recoverable(Throwable failure){
      Throwable t=failure;int depth=0;
      while(t!=null&&depth++<8){
        String n=t.getClass().getName();
        if(t instanceof java.io.IOException||n.contains("PlaylistStuckException")||n.contains("HttpDataSourceException"))return true;
        t=t.getCause();
      }
      return false;
    }
  }
  static final class CobraTimeshiftStallPolicy {
    static final long STALL_TRIGGER_MS=6000L;
    static final long RECOVERY_COOLDOWN_MS=60000L;
    static final int MAX_AUTO_LIVE_EDGE_ATTEMPTS=2;
    static final int BURST_COUNT=3;
    static final long BURST_WINDOW_MS=12000L;
    static boolean canAutoRecover(int attempts,long lastAttempt,long now){
      return attempts<MAX_AUTO_LIVE_EDGE_ATTEMPTS&&(lastAttempt==0L||now-lastAttempt>=RECOVERY_COOLDOWN_MS);
    }
  }

  private int mCobraTimeshiftRecoveryGeneration=0,mCobraTransientMultiWindowStops=0,mCobraTimeshiftStallGeneration=0,mCobraTimeshiftStallRecoveries=0,mCobraAutoLiveEdgeRecoveries=0,mCobraRebufferBurstObservations=0;
  private long mCobraRebufferBurstWindowStart=0L,mCobraLastAutoLiveEdgeElapsed=0L;
  private int mCobraRebufferBurstCount=0,mCobraAutoLiveEdgeAttempts=0;
  private ExoPlayer mCobraAutoLiveEdgeBudgetPlayer=null;

  private void cobraCancelTimeshiftStallCheck(){mCobraTimeshiftStallGeneration++;}

  private boolean cobraCurrentLocalTimeshiftPlayer(ExoPlayer player){
    return player!=null&&player==mCobraTimeshiftPlayer&&mCobraTimeshiftSession!=null&&(player==mPlayer||player==mCobraPreviewPlayer);
  }

  private void cobraObserveTimeshiftRebufferBurst(ExoPlayer player,Channel channel){
    if(channel==null||!cobraCurrentLocalTimeshiftPlayer(player))return;
    long now=android.os.SystemClock.elapsedRealtime();
    if(mCobraRebufferBurstWindowStart==0L||now-mCobraRebufferBurstWindowStart>CobraTimeshiftStallPolicy.BURST_WINDOW_MS){
      mCobraRebufferBurstWindowStart=now;mCobraRebufferBurstCount=1;
    }else mCobraRebufferBurstCount++;
    if(mCobraRebufferBurstCount<CobraTimeshiftStallPolicy.BURST_COUNT)return;
    mCobraRebufferBurstWindowStart=0L;mCobraRebufferBurstCount=0;mCobraRebufferBurstObservations++;
    CobraLocalTimeshiftSession session=mCobraTimeshiftSession;
    InfinityCobraDiagnostics.record(this,"timeshift","rebuffer-burst-observed",
        "count="+mCobraRebufferBurstObservations+"; no_restart=true; buffer_ms="+Math.max(0,player.getTotalBufferedDuration())+"; "+(session==null?"no-session":session.diagnostic()));
  }

  private boolean cobraPermitAutoLiveEdge(ExoPlayer player){
    long now=android.os.SystemClock.elapsedRealtime();
    if(player!=mCobraAutoLiveEdgeBudgetPlayer){
      mCobraAutoLiveEdgeBudgetPlayer=player;mCobraAutoLiveEdgeAttempts=0;mCobraLastAutoLiveEdgeElapsed=0L;
    }
    if(!CobraTimeshiftStallPolicy.canAutoRecover(mCobraAutoLiveEdgeAttempts,mCobraLastAutoLiveEdgeElapsed,now))return false;
    // Consume the attempt before the external seek, matching the earlier bounded recovery audit.
    mCobraAutoLiveEdgeAttempts++;mCobraLastAutoLiveEdgeElapsed=now;return true;
  }

  private void cobraScheduleTimeshiftStallCheck(ExoPlayer player,Channel channel){
    if(channel==null||!cobraCurrentLocalTimeshiftPlayer(player))return;
    final CobraLocalTimeshiftSession session=mCobraTimeshiftSession;final long startSeq=session.latestSequence();final int generation=++mCobraTimeshiftStallGeneration;
    mMain.postDelayed(()->{
      if(generation!=mCobraTimeshiftStallGeneration||!cobraCurrentLocalTimeshiftPlayer(player)||session!=mCobraTimeshiftSession)return;
      if(!player.getPlayWhenReady()||player.getPlaybackState()!=Player.STATE_BUFFERING)return;
      cobraRecoverTimeshiftStall(player,channel,session,startSeq,generation);
    },CobraTimeshiftStallPolicy.STALL_TRIGGER_MS);
  }

  private void cobraRecoverTimeshiftStall(ExoPlayer player,Channel channel,CobraLocalTimeshiftSession session,long startSeq,int generation){
    if(player==null||channel==null||session==null)return;
    final String surface=player==mPlayer?"fullscreen":"preview";
    InfinityCobraDiagnostics.record(this,"timeshift","stall-detected",
        surface+"; buffer_ms="+Math.max(0,player.getTotalBufferedDuration())+"; tail="+startSeq+"; "+session.diagnostic());

    // Cross-check against the passed playback audits: do not re-prepare, replace the media item,
    // or restart loading merely because Media3 reports BUFFERING. The only automatic action here
    // is the exact same-player live-edge seek that the user's manual LIVE press proved effective.
    if(!cobraPermitAutoLiveEdge(player)){
      InfinityCobraDiagnostics.record(this,"timeshift","auto-live-edge-suppressed",
          surface+"; attempts="+mCobraAutoLiveEdgeAttempts+"; cooldown_ms="+CobraTimeshiftStallPolicy.RECOVERY_COOLDOWN_MS);
      return;
    }
    try{
      if(!player.isCurrentMediaItemSeekable()){
        InfinityCobraDiagnostics.record(this,"timeshift","auto-live-edge-unavailable",surface+"; seekable=false");
        return;
      }
      mCobraAutoLiveEdgeRecoveries++;
      player.seekToDefaultPosition();
      InfinityCobraDiagnostics.record(this,"timeshift","auto-live-edge-seek",
          surface+"; same_player=true; no_restart=true; count="+mCobraAutoLiveEdgeRecoveries+"; "+session.diagnostic());
      mMain.postDelayed(()->{
        if(generation!=mCobraTimeshiftStallGeneration||!cobraCurrentLocalTimeshiftPlayer(player)||session!=mCobraTimeshiftSession)return;
        if(player.getPlayWhenReady()&&player.getPlaybackState()==Player.STATE_BUFFERING){
          InfinityCobraDiagnostics.record(this,"timeshift","stall-persists-after-live-edge",
              surface+"; error_path_owns_restart=true; "+session.diagnostic());
        }
      },2500L);
    }catch(RuntimeException liveEdgeFailure){
      InfinityCobraDiagnostics.failure(this,"timeshift-auto-live-edge",liveEdgeFailure);
    }
  }

  private void cobraFallbackFromLocalTimeshift(ExoPlayer failed,Channel failedChannel,String reason){
    if(failed==null||failedChannel==null)return;
    if(failed==mPlayer&&mPlaying!=null&&failedChannel.id.equals(mPlaying.id)){
      cobraStopLocalTimeshift(reason);releaseSinglePlayer();
      cobraStartDirectSinglePlayer(failedChannel,failedChannel.primaryUrl,"timeshift-transport-fallback");
      cobraSetTimeshiftUiState("FAILED","direct fallback active");
    }else if(failed==mCobraPreviewPlayer&&mGuidePreviewChannel!=null&&failedChannel.id.equals(mGuidePreviewChannel.id)){
      mCobraPreviewPlayer=null;mCobraPreviewSessionKey="";cobraDisposePlayer(failed);cobraStopLocalTimeshift(reason);
      cobraStartDirectPreview(failedChannel,"timeshift-transport-fallback");
      cobraSetTimeshiftUiState("FAILED","preview direct fallback");
    }
  }

  private void cobraRecoverLocalTimeshiftSource(ExoPlayer failed,Channel failedChannel,PlaybackException failure){
    final CobraLocalTimeshiftSession session=mCobraTimeshiftSession;
    if(session==null||failed==null||failedChannel==null||!CobraTimeshiftRecoveryPolicy.recoverable(failure)){
      cobraFallbackFromLocalTimeshift(failed,failedChannel,"source-error-fallback");return;
    }
    final int generation=++mCobraTimeshiftRecoveryGeneration;final long before=session.latestSequence();
    cobraSetTimeshiftUiState("RECONNECTING","waiting for provider");
    InfinityCobraDiagnostics.record(this,"timeshift","source-recovery-wait","tail="+before+"; "+session.diagnostic());
    if(!submitCobraIo(()->{
      final boolean advanced=session.awaitSequenceAfter(before,CobraTimeshiftRecoveryPolicy.ADVANCE_WAIT_MS);
      publishCobraUi(()->{
        if(generation!=mCobraTimeshiftRecoveryGeneration||session!=mCobraTimeshiftSession||failed!=mCobraTimeshiftPlayer)return;
        if(advanced){
          try{
            failed.setMediaItem(mediaItem(session.playlistUrl()+"?cobra_recovery="+generation));
            cobraPrepareObserved(failed,"timeshift-source-recovery");startCobraPlayer(failed);
            cobraSetTimeshiftUiState("READY",Math.round(session.windowDurationMs()/1000f)+"s");
            InfinityCobraDiagnostics.record(this,"timeshift","source-recovered",session.diagnostic());return;
          }catch(RuntimeException retryFailure){
            InfinityCobraDiagnostics.failure(this,"timeshift-source-recovery",retryFailure);
          }
        }
        cobraFallbackFromLocalTimeshift(failed,failedChannel,advanced?"source-recovery-prepare-failed":"source-recovery-timeout");
      });
    }))cobraFallbackFromLocalTimeshift(failed,failedChannel,"source-recovery-worker-rejected");
  }
'''

NEW_INGEST_LOOP=r'''    private void ingestLoop(){
      long backoff=CobraTimeshiftTransportPolicy.INITIAL_BACKOFF_MS,outageStart=0L;
      while(!stopped){
        HttpURLConnection c=null;
        try{
          c=(HttpURLConnection)new URL(source).openConnection();
          c.setConnectTimeout(CobraTimeshiftTransportPolicy.CONNECT_TIMEOUT_MS);
          c.setReadTimeout(CobraTimeshiftTransportPolicy.READ_TIMEOUT_MS);
          c.setInstanceFollowRedirects(true);
          c.setRequestProperty("User-Agent","Infinity Cobra Timeshift/1.0");
          for(Map.Entry<String,String> h:headers.entrySet())if(h.getKey()!=null&&h.getValue()!=null&&!h.getKey().isEmpty())c.setRequestProperty(h.getKey(),h.getValue());
          int code=c.getResponseCode();if(code<200||code>=300)throw new java.io.IOException("HTTP "+code);
          long connected=android.os.SystemClock.elapsedRealtime();
          if(outageStart>0L){stallMs+=Math.max(0L,connected-outageStart);outageStart=0L;}
          if(everConnected)pendingDiscontinuity=true;everConnected=true;state="RECORDING";backoff=CobraTimeshiftTransportPolicy.INITIAL_BACKOFF_MS;
          try(java.io.BufferedInputStream in=new java.io.BufferedInputStream(c.getInputStream(),65536)){
            byte[] b=new byte[65536];int n;
            while(!stopped&&(n=in.read(b))>=0){if(n==0)continue;bytesRead+=n;consume(b,n);}
          }
          if(!stopped)throw new java.io.EOFException("live stream ended");
        }catch(Exception e){
          if(stopped)break;
          // Keep every complete TS packet already captured before a provider drop.
          // The next connection begins with a discontinuity marker, so a short provider
          // hiccup no longer throws away nearly a full segment and then waits another
          // segment interval before Media3 can move forward.
          finishSegment(true);carryLen=0;synced=false;lastError=e.getClass().getSimpleName();reconnects++;state="RECONNECTING";
          if(outageStart==0L)outageStart=android.os.SystemClock.elapsedRealtime();
          try{Thread.sleep(backoff);}catch(InterruptedException stop){Thread.currentThread().interrupt();}
          backoff=CobraTimeshiftTransportPolicy.nextBackoffMs(backoff);
        }finally{if(c!=null)c.disconnect();}
      }
      if(outageStart>0L)stallMs+=Math.max(0L,android.os.SystemClock.elapsedRealtime()-outageStart);
      finishSegment(false);
    }'''

def apply(source,receipt_path,out):
    source=Path(source);receipt=json.loads(Path(receipt_path).read_text());out=Path(out)
    if receipt.get('version_code')!=BASE_BUILD:raise RuntimeError('Expected exact passed 2103178 source receipt')
    if receipt.get('version_name')!='1.0.9-Cobra-Timeshift-Mini-Player-Repair-RC1':raise RuntimeError('Unexpected 2103178 source identity')
    path=source/REL;before_b=path.read_bytes();before=before_b.decode();expected=receipt.get('files',{}).get(str(REL),{}).get('after')
    if not expected or sha(before_b)!=expected:raise RuntimeError('2103178 Activity preimage mismatch')
    text=before

    protected=[
      'cobraStartLocalTimeshift','cobraStartLocalTimeshiftPreview','promoteCobraPreviewToFullscreen',
      'cobraStartProviderCatchup','cobraGoLive','cobraTimeshiftSeconds','cobraUpdateTimeshiftSeek',
      'cobraBuildPlayerChrome','cobraAttachVideo','cobraStartDirectSinglePlayer','cobraStartDirectPreview',
      'cobraApplyDisplayPerformance','cobraOpenFilePicker','cobraLaunchFilePicker','cobraTuneLastChannel'
    ]
    guards={n:sha(member(before,n)) for n in protected}

    text=replace_member(text,'CobraTimeshiftTransportPolicy',TRANSPORT_POLICY,kind='class')

    marker='  private static final class CobraLocalTimeshiftSession {'
    if text.count(marker)!=1:raise RuntimeError('timeshift class marker drift')
    text=text.replace(marker,RESILIENCE_HELPERS.rstrip()+'\n\n'+marker,1)

    ts=member(text,'CobraLocalTimeshiftSession',kind='class')
    ts=once(ts,
'    long diskBytes(){synchronized(lock){return totalBytes;}}long reconnects(){return reconnects;}long stallMs(){return stallMs;}long httpRequests(){return httpRequests;}long httpFailures(){return httpFailures;}long playlistRequests(){return playlistRequests;}long segmentRequests(){return segmentRequests;}String lastHttpError(){return lastHttpError;}long ingestKbps(){long elapsed=Math.max(1,android.os.SystemClock.elapsedRealtime()-startedElapsed);return (bytesRead*8L)/elapsed;}',
'''    long diskBytes(){synchronized(lock){return totalBytes;}}long reconnects(){return reconnects;}long stallMs(){return stallMs;}long httpRequests(){return httpRequests;}long httpFailures(){return httpFailures;}long playlistRequests(){return playlistRequests;}long segmentRequests(){return segmentRequests;}String lastHttpError(){return lastHttpError;}long ingestKbps(){long elapsed=Math.max(1,android.os.SystemClock.elapsedRealtime()-startedElapsed);return (bytesRead*8L)/elapsed;}
    long latestSequence(){synchronized(lock){Segment last=segments.peekLast();return last==null?0L:last.seq;}}
    boolean awaitSequenceAfter(long prior,long ms){long end=android.os.SystemClock.elapsedRealtime()+Math.max(0L,ms);while(!stopped&&android.os.SystemClock.elapsedRealtime()<end){if(latestSequence()>prior)return true;try{Thread.sleep(120L);}catch(InterruptedException e){Thread.currentThread().interrupt();return false;}}return !stopped&&latestSequence()>prior;}''',
'timeshift advance observation')
    ts=replace_inner(ts,'ingestLoop',NEW_INGEST_LOOP)
    text=replace_member(text,'CobraLocalTimeshiftSession',ts,kind='class')

    binding=member(text,'CobraPlayerBinding',kind='class')
    binding=once(binding,
'''      if(state==Player.STATE_BUFFERING&&vitals.everReady)vitals.rebufferEvents++;
      if(state==Player.STATE_READY)vitals.everReady=true;''',
'''      if(state==Player.STATE_BUFFERING&&vitals.everReady){
        vitals.bufferingTransitions++;
        if(vitals.bufferingStartedElapsed==0L)vitals.bufferingStartedElapsed=android.os.SystemClock.elapsedRealtime();
        if(player==mCobraTimeshiftPlayer){cobraObserveTimeshiftRebufferBurst(player,channel);cobraScheduleTimeshiftStallCheck(player,channel);}
      }
      if(state==Player.STATE_READY){
        if(player==mCobraTimeshiftPlayer)cobraCancelTimeshiftStallCheck();
        if(vitals.everReady&&vitals.bufferingStartedElapsed>0L){
          long bufferedFor=Math.max(0L,android.os.SystemClock.elapsedRealtime()-vitals.bufferingStartedElapsed);
          if(bufferedFor>=750L){vitals.rebufferEvents++;vitals.rebufferDurationMs+=bufferedFor;}
        }
        vitals.bufferingStartedElapsed=0L;vitals.everReady=true;
      }else if(state==Player.STATE_IDLE||state==Player.STATE_ENDED){vitals.bufferingStartedElapsed=0L;if(player==mCobraTimeshiftPlayer)cobraCancelTimeshiftStallCheck();}''','visible rebuffer accounting')
    binding=once(binding,
'''      final boolean localTimeshift=player==mCobraTimeshiftPlayer;
      if(localTimeshift)cobraStopLocalTimeshift("player-error");''',
'''      final boolean localTimeshift=player==mCobraTimeshiftPlayer;''',
'do not kill local session before source recovery')
    binding=once(binding,
'''      if(localTimeshift){
        final ExoPlayer failed=player;final Channel failedChannel=channel;
        mMain.post(()->{
          if(failed==mPlayer&&mPlaying!=null&&failedChannel.id.equals(mPlaying.id)){releaseSinglePlayer();cobraStartDirectSinglePlayer(failedChannel,failedChannel.primaryUrl,"timeshift-transport-fallback");cobraSetTimeshiftUiState("FAILED","direct fallback active");}
          else if(failed==mCobraPreviewPlayer&&mGuidePreviewChannel!=null&&failedChannel.id.equals(mGuidePreviewChannel.id)){mCobraPreviewPlayer=null;mCobraPreviewSessionKey="";cobraDisposePlayer(failed);cobraStartDirectPreview(failedChannel,"timeshift-transport-fallback");cobraSetTimeshiftUiState("FAILED","preview direct fallback");}
        });
        cobraUpdatePlaybackLabels();return;
      }''',
'''      if(localTimeshift){
        final ExoPlayer failed=player;final Channel failedChannel=channel;
        mMain.post(()->cobraRecoverLocalTimeshiftSource(failed,failedChannel,failure));
        cobraUpdatePlaybackLabels();return;
      }''',
'targeted timeshift source recovery')
    text=replace_member(text,'CobraPlayerBinding',binding,kind='class')

    stop=member(text,'onStop')
    stop=once(stop,
'''    int decision=mCobraPlaybackPolicy.stop(isCobraInPictureInPicture(),cobraMiniBackgroundEnabled()&&cobraMiniPreviewPlaying());
    if(decision==CobraPlaybackPolicy.STOP_PIP)cobraHaltHiddenPlayback();
    else {
      if(decision==CobraPlaybackPolicy.MINI_AUDIO&&!mCobraMiniBackgroundActive)mCobraMiniBackgroundActive=cobraBeginMiniBackgroundPlayback();
      if(decision!=CobraPlaybackPolicy.MINI_AUDIO)cobraEndMiniBackgroundPlayback();
      pauseCobraForBackground();
    }''',
'''    boolean preserveMultiWindow=Build.VERSION.SDK_INT>=24&&CobraWindowLifecyclePolicy.preservePlaybackOnStop(isInMultiWindowMode(),isFinishing());
    if(preserveMultiWindow){
      mCobraTransientMultiWindowStops++;
      InfinityCobraDiagnostics.record(this,"lifecycle","multitask-window-stop","Playback preserved during multi-window resize");
    }else{
      int decision=mCobraPlaybackPolicy.stop(isCobraInPictureInPicture(),cobraMiniBackgroundEnabled()&&cobraMiniPreviewPlaying());
      if(decision==CobraPlaybackPolicy.STOP_PIP)cobraHaltHiddenPlayback();
      else {
        if(decision==CobraPlaybackPolicy.MINI_AUDIO&&!mCobraMiniBackgroundActive)mCobraMiniBackgroundActive=cobraBeginMiniBackgroundPlayback();
        if(decision!=CobraPlaybackPolicy.MINI_AUDIO)cobraEndMiniBackgroundPlayback();
        pauseCobraForBackground();
      }
    }''',
'multi-window stop preservation')
    text=replace_member(text,'onStop',stop)

    vitals=member(text,'CobraSessionVitals',kind='class')
    vitals=once(vitals,
'    int loadErrors,bufferRetries,rebufferEvents,longStalls,prepareCalls,surfaceAttachCalls;boolean everReady=false;String lastError="",lastRecovery="not_requested",lastPrepareReason="none",decoder="Not reported";',
'    int loadErrors,bufferRetries,rebufferEvents,longStalls,prepareCalls,surfaceAttachCalls,bufferingTransitions;long bufferingStartedElapsed=0L,rebufferDurationMs=0L;boolean everReady=false;String lastError="",lastRecovery="not_requested",lastPrepareReason="none",decoder="Not reported";',
'buffer metrics')
    text=replace_member(text,'CobraSessionVitals',vitals,kind='class')

    overlay=member(text,'cobraUpdatePerformanceOverlay')
    overlay=once(overlay,
'    if(mCobraPerformanceOverlayView==null)return;android.view.Display proofDisplay=cobraCurrentDisplay();if(proofDisplay!=null&&Build.VERSION.SDK_INT>=23){mCobraActiveHz=proofDisplay.getMode().getRefreshRate();if(!cobraVideoOwnsRefresh()&&mCobraRequestedHz>0&&Math.abs(mCobraActiveHz-mCobraRequestedHz)<.75f)mCobraRefreshStatus="ACTIVE";}long buffered=mPlayer==null?0:Math.max(0,mPlayer.getTotalBufferedDuration());long live=-1;try{if(mPlayer!=null)live=mPlayer.getCurrentLiveOffset();}catch(RuntimeException ignored){}',
'    if(mCobraPerformanceOverlayView==null)return;android.view.Display proofDisplay=cobraCurrentDisplay();if(proofDisplay!=null&&Build.VERSION.SDK_INT>=23){mCobraActiveHz=proofDisplay.getMode().getRefreshRate();if(!cobraVideoOwnsRefresh()&&mCobraRequestedHz>0&&Math.abs(mCobraActiveHz-mCobraRequestedHz)<.75f)mCobraRefreshStatus="ACTIVE";}ExoPlayer proofPlayer=mPlayer!=null?mPlayer:mCobraPreviewPlayer;long buffered=proofPlayer==null?0:Math.max(0,proofPlayer.getTotalBufferedDuration());long live=-1;try{if(proofPlayer!=null)live=proofPlayer.getCurrentLiveOffset();}catch(RuntimeException ignored){}',
'source-aware performance overlay')
    text=replace_member(text,'cobraUpdatePerformanceOverlay',overlay)

    health=member(text,'cobraRefreshHealthSummary')
    health=once(health,
'      text.append("\\nBuffered ahead: ").append(Math.max(0,p.getTotalBufferedDuration())).append(" ms • rebuffers: ").append(s.rebufferEvents).append(" • long stalls: ").append(s.longStalls);',
'      text.append("\\nBuffered ahead: ").append(Math.max(0,p.getTotalBufferedDuration())).append(" ms • visible rebuffers: ").append(s.rebufferEvents).append(" / ").append(s.rebufferDurationMs).append(" ms • buffer transitions: ").append(s.bufferingTransitions).append(" • long stalls: ").append(s.longStalls);',
'health visible rebuffer summary')
    text=replace_member(text,'cobraRefreshHealthSummary',health)

    fresh=member(text,'cobraFreshHealthSnapshot')
    fresh=once(fresh,
'      root.put("preview_height",mCobraPreviewTexture==null?0:mCobraPreviewTexture.getHeight());root.put("preview_start_count",mCobraPreviewStartCount);',
'      root.put("preview_height",mCobraPreviewTexture==null?0:mCobraPreviewTexture.getHeight());root.put("multi_window",Build.VERSION.SDK_INT>=24&&isInMultiWindowMode());root.put("transient_multiwindow_stops",mCobraTransientMultiWindowStops);root.put("timeshift_stall_recoveries",mCobraTimeshiftStallRecoveries);root.put("auto_live_edge_recoveries",mCobraAutoLiveEdgeRecoveries);root.put("auto_live_edge_attempts",mCobraAutoLiveEdgeAttempts);root.put("rebuffer_burst_observations",mCobraRebufferBurstObservations);root.put("preview_start_count",mCobraPreviewStartCount);',
'multi-window diagnostic evidence')
    text=replace_member(text,'cobraFreshHealthSnapshot',fresh)

    session_health=member(text,'cobraAddSessionHealth')
    session_health=once(session_health,
'row.put("rebuffer_events",s.rebufferEvents);row.put("long_stalls",s.longStalls);',
'row.put("rebuffer_events",s.rebufferEvents);row.put("rebuffer_duration_ms",s.rebufferDurationMs);row.put("buffering_transitions",s.bufferingTransitions);row.put("long_stalls",s.longStalls);',
'diagnostic rebuffer metrics')
    text=replace_member(text,'cobraAddSessionHealth',session_health)

    for n,h in guards.items():
        if sha(member(text,n))!=h:raise RuntimeError('Protected rewind/playback contract changed: '+n)

    required=[
      '#EXT-X-START:TIME-OFFSET=-9.0,PRECISE=NO',
      'CONNECT_TIMEOUT_MS=7000','READ_TIMEOUT_MS=5000','INITIAL_BACKOFF_MS=250L','MAX_BACKOFF_MS=1500L',
      'finishSegment(true)','bufferingTransitions','rebufferDurationMs','bufferedFor>=750L',
      'CobraWindowLifecyclePolicy','preservePlaybackOnStop','multitask-window-stop',
      'CobraTimeshiftRecoveryPolicy','awaitSequenceAfter','timeshift-source-recovery','source-recovered',
      'CobraTimeshiftStallPolicy','STALL_TRIGGER_MS=6000L','RECOVERY_COOLDOWN_MS=60000L','MAX_AUTO_LIVE_EDGE_ATTEMPTS=2',
      'rebuffer-burst-observed','no_restart=true','auto-live-edge-seek','same_player=true',
      'stall-persists-after-live-edge','error_path_owns_restart=true','mCobraAutoLiveEdgeRecoveries',
      'ExoPlayer proofPlayer=mPlayer!=null?mPlayer:mCobraPreviewPlayer',
      'timeshift-transport-fallback','preview-timeshift-fullscreen','cobra_live_timeshift_seek',
      'preferredDisplayModeId','cobra_last_channel','buffer_observed_no_restart'
    ]
    for token in required:
        if token not in text:raise RuntimeError('2103179 contract missing: '+token)
    if '#EXT-X-START:TIME-OFFSET=-6.0,PRECISE=NO' in member(text,'CobraTimeshiftTransportPolicy',kind='class'):
        raise RuntimeError('Old six-second live reserve survived 2103179')
    watchdog=text[text.index('private final Runnable mStallWatchdog'):text.index('private final Runnable mAutoRefresh')]
    if 'mPlayer.prepare()' in watchdog or 'mPlayer.play()' in watchdog:raise RuntimeError('watchdog regained restart behavior')

    after=text.encode();path.write_bytes(after);out.mkdir(parents=True,exist_ok=True);(out/'source-before').mkdir(exist_ok=True);(out/'source-before'/path.name).write_bytes(before_b)
    report={
      'base_build':BASE_BUILD,'base_commit':LOCKED_COMMIT,
      'files':{str(REL):{'before':sha(before_b),'after':sha(after)}},
      'live_reserve_seconds':9,'connect_timeout_ms':7000,'read_timeout_ms':5000,
      'reconnect_backoff_initial_ms':250,'reconnect_backoff_max_ms':1500,
      'partial_segment_preservation':True,'visible_rebuffer_threshold_ms':750,
      'multitask_resize_playback_preserved':True,'timeshift_source_recovery':True,
      'timeshift_recovery_wait_ms':12000,'timeshift_stall_recovery':True,'timeshift_stall_detect_ms':6000,
      'rebuffer_burst_observation_only':True,'rebuffer_burst_count':3,'rebuffer_burst_window_ms':12000,
      'auto_live_edge_first':True,'auto_live_edge_verify_ms':2500,'auto_live_edge_max_attempts':2,
      'auto_live_edge_cooldown_ms':60000,'buffering_media_restart_forbidden':True,
      'manual_live_seek_equivalent':True,'performance_overlay_source_aware':True,'rewind_contract_preserved':True,'native_changed':False,'theme_zip_changed':False,
      'physical_device_verified':False
    }
    (out/'patch.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: 2103179 evidence-driven buffer + multitask + timeshift recovery patch applied without changing rewind ownership')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();apply(a.source,a.receipt,a.out)
