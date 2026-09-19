#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,re

REL=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
BASE_BUILD=2103177
BASE_SHA='7c32736583337dead1e7807111f7e779df67528121ebb8f3d9f1c6e8dd67d725'
LOCKED_COMMIT='3c51f790018eda816beeac6328d050e1fe242d6e'

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
          +"#EXT-X-START:TIME-OFFSET=-6.0,PRECISE=NO\n";
    }
    static boolean hasRealHttpFraming(String value){return value!=null&&value.contains("\r\n")&&!value.contains("\\\\r\\\\n")&&value.endsWith("\r\n\r\n");}
    static boolean hasRealPlaylistLines(String value){return value!=null&&value.startsWith("#EXTM3U\n")&&!value.contains("\\\\n");}
  }
'''

PREVIEW_HELPERS=r'''
  private String mCobraDiagnosticsCaptureContext="normal";
  private String mCobraTimeshiftUiState="OFF",mCobraTimeshiftUiDetail="";
  private int mCobraPreviewStartCount=0,mCobraPreviewDirectStarts=0,mCobraPreviewTimeshiftStarts=0,mCobraPreviewHandoffs=0,mCobraPreviewStops=0;

  private void cobraSetTimeshiftUiState(String state,String detail){
    mCobraTimeshiftUiState=state==null?"OFF":state;mCobraTimeshiftUiDetail=detail==null?"":detail;cobraUpdatePerformanceOverlay();
  }
  private String cobraTimeshiftStatusText(){
    if(!cobraLiveRewindEnabled())return "OFF";
    if(mCobraTimeshiftSession!=null)return mCobraTimeshiftSession.shortState();
    String state=mCobraTimeshiftUiState==null||mCobraTimeshiftUiState.isEmpty()?"OFF":mCobraTimeshiftUiState;
    return mCobraTimeshiftUiDetail.isEmpty()?state:state+" • "+mCobraTimeshiftUiDetail;
  }
  private void cobraPrepareObserved(ExoPlayer player,String reason){
    if(player==null)return;CobraPlayerBinding b=mCobraPlayerBindings.get(player);if(b!=null){b.vitals.prepareCalls++;b.vitals.lastPrepareReason=reason==null?"unknown":reason;}player.prepare();
  }
  private void cobraStartDirectPreview(Channel channel,String reason){
    if(channel==null||mCobraPreviewTexture==null||!isCobraAsyncAlive())return;
    try{
      mGuidePreviewChannel=channel;mGuidePreviewKey=cobraChannelKey(channel);
      mCobraPreviewPlayer=buildPlayer(mCobraPreviewTexture,channel,!mCobraPreviewMuted);mCobraPreviewSessionKey=cobraChannelKey(channel);
      mCobraPreviewPlayer.setMediaItem(mediaItem(channel.primaryUrl));cobraPrepareObserved(mCobraPreviewPlayer,"preview-direct:"+reason);mCobraPreviewDirectStarts++;
      startCobraPlayer(mCobraPreviewPlayer);cobraStartPresentationTicker();cobraRequestShortEpg(channel);cobraSetTimeshiftUiState(cobraLiveRewindEnabled()&&cobraLiveChannel(channel)?"UNSUPPORTED":"OFF",cobraLiveRewindEnabled()&&cobraLiveChannel(channel)?"direct preview":"");
    }catch(Exception failure){stopCobraPreviewPlayerOnly();setCobraPreviewLabel("Preview unavailable");}
    updateCobraPreviewPlayPause();cobraRefreshProgrammeLabels();
  }
  private void cobraStartLocalTimeshiftPreview(Channel channel,String sourceUrl){
    final int generation=++mCobraTimeshiftGeneration;final CobraLocalTimeshiftSession session=new CobraLocalTimeshiftSession(getCacheDir(),sourceUrl,channel.headers,cobraTimeshiftSeconds());mCobraTimeshiftSession=session;cobraSetTimeshiftUiState("STARTING","preview buffer");setCobraPreviewLabel("Building rewind buffer…");
    try{session.start();}catch(Exception e){mCobraTimeshiftSession=null;cobraSetTimeshiftUiState("FAILED","preview start");InfinityCobraDiagnostics.failure(this,"timeshift-preview-start",e);cobraStartDirectPreview(channel,"timeshift-start-failed");return;}
    if(!submitCobraIo(()->{boolean ready=session.awaitReady(18000L);publishCobraUi(()->{
      if(generation!=mCobraTimeshiftGeneration||session!=mCobraTimeshiftSession||mGuidePreviewChannel==null||!channel.id.equals(mGuidePreviewChannel.id)){session.stop();return;}
      if(!ready){mCobraTimeshiftSession=null;session.stop();cobraSetTimeshiftUiState("FAILED","preview timeout");InfinityCobraDiagnostics.record(this,"timeshift","preview-fallback","Local preview buffer was not ready; direct playback restored");cobraStartDirectPreview(channel,"timeshift-timeout");return;}
      try{
        mCobraPreviewPlayer=buildPlayer(mCobraPreviewTexture,channel,!mCobraPreviewMuted);mCobraPreviewSessionKey=cobraChannelKey(channel);mCobraTimeshiftPlayer=mCobraPreviewPlayer;mCobraPreviewTimeshiftStarts++;
        mCobraPreviewPlayer.setMediaItem(mediaItem(session.playlistUrl()));cobraPrepareObserved(mCobraPreviewPlayer,"preview-timeshift");startCobraPlayer(mCobraPreviewPlayer);cobraStartPresentationTicker();cobraRequestShortEpg(channel);cobraSetTimeshiftUiState("READY",Math.round(session.windowDurationMs()/1000f)+"s");InfinityCobraDiagnostics.record(this,"timeshift","preview-ready",session.diagnostic());
      }catch(Exception error){if(mCobraPreviewPlayer!=null)cobraDisposePlayer(mCobraPreviewPlayer);mCobraPreviewPlayer=null;mCobraPreviewSessionKey="";mCobraTimeshiftPlayer=null;mCobraTimeshiftSession=null;session.stop();cobraSetTimeshiftUiState("FAILED","preview player");cobraStartDirectPreview(channel,"timeshift-player-failed");}
      updateCobraPreviewPlayPause();cobraRefreshProgrammeLabels();
    });})) {mCobraTimeshiftSession=null;session.stop();cobraSetTimeshiftUiState("FAILED","preview worker");cobraStartDirectPreview(channel,"timeshift-worker-rejected");}
  }
  private void cobraCapturePreviewDiagnostics(){
    if(mCobraDiagnosticsPicker||InfinityCobraDiagnostics.exporting()){toast("A diagnostics export is already in progress");return;}
    if(mCobraPreviewPlayer==null){toast("Start the mini-player before capturing diagnostics");return;}
    mCobraDiagnosticsCaptureContext="mini_preview_direct";mCobraDiagnosticsSnapshot=cobraFreshHealthSnapshot();mCobraDiagnosticsCaptureContext="normal";mCobraDiagnosticsPicker=true;
    try{startActivityForResult(InfinityCobraDiagnostics.createDocumentIntent(),REQUEST_COBRA_DIAGNOSTICS);}
    catch(android.content.ActivityNotFoundException missing){mCobraDiagnosticsPicker=false;mCobraDiagnosticsSnapshot=null;toast("No system document picker is available on this device");}
    catch(RuntimeException failure){mCobraDiagnosticsPicker=false;mCobraDiagnosticsSnapshot=null;InfinityCobraDiagnostics.failure(this,"preview-diagnostic-picker",failure);toast("Could not open the save-location picker");}
  }
'''

NEW_START_PREVIEW=r'''  private void startCobraPreview(Channel channel) {
    if(channel==null||mCobraPreviewTexture==null||!isCobraAsyncAlive())return;
    if(mCobraPreviewPlayer!=null&&cobraChannelKey(channel).equals(mCobraPreviewSessionKey)){updateCobraPreviewPlayPause();return;}
    stopCobraPreviewPlayerOnly();cobraStopLocalTimeshift("preview-retune");mCobraPreviewAutoplayAllowed=true;mCobraPreviewTexture.setVisibility(View.VISIBLE);mCobraPreviewStartCount++;
    mGuidePreviewChannel=channel;mGuidePreviewKey=cobraChannelKey(channel);
    if(cobraShouldUseLocalTimeshift(channel,channel.primaryUrl)){cobraStartLocalTimeshiftPreview(channel,channel.primaryUrl);return;}
    cobraStartDirectPreview(channel,"normal");
  }'''

NEW_PROMOTE=r'''  private void promoteCobraPreviewToFullscreen(Channel channel) {
    if(channel==null||mCobraPlayerLocked)return;
    cobraResetLiveRewindState();
    if(mPlayer!=null&&mPlaying!=null&&channel.id.equals(mPlaying.id))return;
    cobraRememberChannelTransition(channel);
    ExoPlayer session=cobraChannelKey(channel).equals(mCobraPreviewSessionKey)?mCobraPreviewPlayer:null;
    if(session==null){playChannel(channel);return;}
    boolean local=session==mCobraTimeshiftPlayer&&mCobraTimeshiftSession!=null;
    cobraEndMiniBackgroundPlayback();mCobraPreviewPlayer=null;mCobraPreviewSessionKey="";mCobraPreviewHandoffs++;
    if(mMultiOverlay!=null)releaseMulti();if(mPlayerOverlay!=null)closePlayer();
    mPlaying=channel;mPlayingIndex=mChannels.indexOf(channel);mTriedFallback=false;openPlayerOverlay(channel);mPlayer=session;
    if(local)mCobraTimeshiftPlayer=session;
    cobraAttachVideo(session,mPlayerTexture);session.setAudioAttributes(session.getAudioAttributes(),true);session.setVolume(1f);
    cobraStartPresentationTicker();cobraUpdatePlaybackLabels();configureCobraPip(true);cobraSetTimeshiftUiState(local?"READY":cobraLiveRewindEnabled()&&cobraLiveChannel(channel)?"UNSUPPORTED":"OFF",local?Math.round(mCobraTimeshiftSession.windowDurationMs()/1000f)+"s":"");
    if(mDeviceBridge!=null)mDeviceBridge.onPlaybackChanged(local?"preview-timeshift-fullscreen":"preview-fullscreen");
  }'''

NEW_START_LOCAL_FULLSCREEN=r'''  private void cobraStartLocalTimeshift(Channel channel,String sourceUrl){
    final int generation=++mCobraTimeshiftGeneration;final CobraLocalTimeshiftSession session=new CobraLocalTimeshiftSession(getCacheDir(),sourceUrl,channel.headers,cobraTimeshiftSeconds());mCobraTimeshiftSession=session;cobraSetTimeshiftUiState("STARTING","fullscreen buffer");
    TextView state=mPlayerOverlay==null?null:(TextView)mPlayerOverlay.findViewWithTag("player_state");if(state!=null)state.setText("BUILDING BUFFER");
    try{session.start();}catch(Exception e){mCobraTimeshiftSession=null;cobraSetTimeshiftUiState("FAILED","fullscreen start");InfinityCobraDiagnostics.failure(this,"timeshift-start",e);cobraStartDirectSinglePlayer(channel,sourceUrl,"timeshift-start-failed");return;}
    if(!submitCobraIo(()->{boolean ready=session.awaitReady(18000L);publishCobraUi(()->{
      if(generation!=mCobraTimeshiftGeneration||session!=mCobraTimeshiftSession||mPlaying==null||!channel.id.equals(mPlaying.id)){session.stop();return;}
      if(!ready){InfinityCobraDiagnostics.record(this,"timeshift","fallback","Local buffer was not ready; direct playback restored");mCobraTimeshiftSession=null;session.stop();cobraSetTimeshiftUiState("FAILED","fullscreen timeout");cobraStartDirectSinglePlayer(channel,sourceUrl,"timeshift-timeout");return;}
      try{mPlayer=buildPlayer(mPlayerTexture,channel,true);mCobraTimeshiftPlayer=mPlayer;mPlayer.setMediaItem(mediaItem(session.playlistUrl()));cobraPrepareObserved(mPlayer,"fullscreen-timeshift");startCobraPlayer(mPlayer);cobraStartPresentationTicker();cobraRequestShortEpg(channel);cobraSetTimeshiftUiState("READY",Math.round(session.windowDurationMs()/1000f)+"s");cobraUpdatePlaybackLabels();InfinityCobraDiagnostics.record(this,"timeshift","ready",session.diagnostic());}
      catch(Exception error){releaseSinglePlayer();mCobraTimeshiftPlayer=null;mCobraTimeshiftSession=null;session.stop();cobraSetTimeshiftUiState("FAILED","fullscreen player");cobraStartDirectSinglePlayer(channel,sourceUrl,"timeshift-player-failed");}
    });})) {mCobraTimeshiftSession=null;session.stop();cobraSetTimeshiftUiState("FAILED","fullscreen worker");cobraStartDirectSinglePlayer(channel,sourceUrl,"timeshift-worker-rejected");}
  }'''

NEW_DIRECT_SINGLE=r'''  private void cobraStartDirectSinglePlayer(Channel channel,String url,String reason){
    if(channel==null||mPlaying==null||!channel.id.equals(mPlaying.id)||mPlayerTexture==null)return;
    try{mPlayer=buildPlayer(mPlayerTexture,channel,true);mPlayer.setMediaItem(mediaItem(url));cobraPrepareObserved(mPlayer,"fullscreen-direct:"+reason);startCobraPlayer(mPlayer);cobraStartPresentationTicker();cobraRequestShortEpg(channel);InfinityCobraDiagnostics.record(this,"playback","direct",reason);if(cobraLiveRewindEnabled()&&cobraLiveChannel(channel)&&!cobraShouldUseLocalTimeshift(channel,url))cobraSetTimeshiftUiState("UNSUPPORTED","direct stream");}
    catch(Exception error){releaseSinglePlayer();showError("Playback failed","Could not start this stream. "+error.getClass().getSimpleName());}cobraUpdatePlaybackLabels();
  }'''

NEW_STOP_TS=r'''  private void cobraStopLocalTimeshift(String reason){
    CobraLocalTimeshiftSession session=mCobraTimeshiftSession;mCobraTimeshiftSession=null;mCobraTimeshiftPlayer=null;mCobraTimeshiftGeneration++;
    if(session!=null){InfinityCobraDiagnostics.record(this,"timeshift","stop",reason+"; "+session.diagnostic());session.stop();}
    if(reason!=null&&(reason.contains("error")||reason.contains("failed")||reason.contains("timeout")))cobraSetTimeshiftUiState("FAILED",reason);
    else if("rewind-off".equals(reason))cobraSetTimeshiftUiState("OFF","");
    else if(mCobraTimeshiftUiState==null||!mCobraTimeshiftUiState.startsWith("FAILED"))cobraSetTimeshiftUiState("OFF","");
  }'''

NEW_TS_SERVE=r'''    private void serve(java.net.Socket socket){
      httpRequests++;
      try(java.net.Socket s=socket){
        s.setSoTimeout(5000);java.io.BufferedReader reader=new java.io.BufferedReader(new java.io.InputStreamReader(s.getInputStream(),StandardCharsets.US_ASCII));String first=reader.readLine();if(first==null)return;String line;while((line=reader.readLine())!=null&&!line.isEmpty()){}
        String[] parts=first.split(" ");String method=parts.length>0?parts[0]:"GET",path=parts.length>1?parts[1]:"/";boolean head="HEAD".equalsIgnoreCase(method);if(!head&&!"GET".equalsIgnoreCase(method)){reply(s,"405 Method Not Allowed","text/plain","method".getBytes(StandardCharsets.UTF_8),false);return;}
        int q=path.indexOf('?');if(q>=0)path=path.substring(0,q);
        if("/live.m3u8".equals(path)){playlistRequests++;byte[] body=playlist().getBytes(StandardCharsets.UTF_8);reply(s,"200 OK","application/vnd.apple.mpegurl",body,head);}
        else if(path.matches("/seg-[0-9]+\\.ts")){segmentRequests++;long seq=Long.parseLong(path.substring(5,path.length()-3));File file=null;long length=0;synchronized(lock){for(Segment seg:segments)if(seg.seq==seq){file=seg.file;length=seg.length;break;}}if(file==null||!file.isFile()){reply(s,"404 Not Found","text/plain","missing".getBytes(StandardCharsets.UTF_8),head);return;}java.io.OutputStream out=s.getOutputStream();String h=CobraTimeshiftTransportPolicy.httpHeader("200 OK","video/mp2t",length,false);out.write(h.getBytes(StandardCharsets.US_ASCII));if(!head)try(java.io.BufferedInputStream in=new java.io.BufferedInputStream(new java.io.FileInputStream(file))){byte[] b=new byte[32768];int n;while((n=in.read(b))>0)out.write(b,0,n);}out.flush();}
        else reply(s,"404 Not Found","text/plain","not found".getBytes(StandardCharsets.UTF_8),head);
      }catch(Exception error){httpFailures++;lastHttpError=error.getClass().getSimpleName();if(!stopped)lastError="local-http:"+lastHttpError;}
    }'''
NEW_TS_REPLY=r'''    private void reply(java.net.Socket s,String status,String type,byte[] body,boolean head)throws Exception{java.io.OutputStream out=s.getOutputStream();String h=CobraTimeshiftTransportPolicy.httpHeader(status,type,body.length,true);out.write(h.getBytes(StandardCharsets.US_ASCII));if(!head)out.write(body);out.flush();}'''
NEW_TS_PLAYLIST=r'''    private String playlist(){
      ArrayList<Segment> list=new ArrayList<>();synchronized(lock){int skip=Math.max(0,segments.size()-maxSegments),i=0;for(Segment seg:segments)if(i++>=skip)list.add(seg);}if(list.isEmpty())return CobraTimeshiftTransportPolicy.playlistHeader(0L);
      StringBuilder p=new StringBuilder(CobraTimeshiftTransportPolicy.playlistHeader(list.get(0).seq));for(Segment seg:list){if(seg.discontinuity)p.append("#EXT-X-DISCONTINUITY\n");p.append(String.format(Locale.US,"#EXTINF:%.3f,\nseg-%d.ts\n",Math.max(.25,seg.durationMs/1000d),seg.seq));}return p.toString();
    }'''

def apply(source,receipt_path,out):
    source=Path(source);receipt=json.loads(Path(receipt_path).read_text());out=Path(out)
    if receipt.get('version_code')!=BASE_BUILD:raise RuntimeError('Expected exact passed 2103177 source receipt')
    path=source/REL;before_b=path.read_bytes();before=before_b.decode();expected=receipt.get('files',{}).get(str(REL),{}).get('after')
    if sha(before_b)!=BASE_SHA or expected!=BASE_SHA:raise RuntimeError('2103177 Activity preimage mismatch')
    text=before

    protected=['cobraApplyDisplayPerformance','showCobraDisplayPerformancePicker','cobraOpenFilePicker','cobraLaunchFilePicker','loadXtream','parseM3u','cobraInstallBrowseSafeArea','cobraApplySystemBarsForSurface','cobraStartProviderCatchup','cobraGoLive','cobraTuneLastChannel']
    guards={n:sha(member(before,n)) for n in protected}

    preview_actions=member(text,'cobraShowPreviewActions')
    preview_actions=once(preview_actions,'    rows.addView(cobraSheetRow("cc","Captions",null,false,dark,()->toggleCobraPreviewCaptions()));',
'''    rows.addView(cobraSheetRow("cc","Captions",null,false,dark,()->toggleCobraPreviewCaptions()));
    rows.addView(cobraSheetRow("health","Capture diagnostics","Snapshots this mini-player before Android opens the save picker",false,dark,()->cobraCapturePreviewDiagnostics()));''','preview diagnostics action')
    text=replace_member(text,'cobraShowPreviewActions',preview_actions)

    text=replace_member(text,'startCobraPreview',NEW_START_PREVIEW)
    text=replace_member(text,'promoteCobraPreviewToFullscreen',NEW_PROMOTE)

    stop_preview=member(text,'stopCobraPreviewPlayerOnly')
    stop_preview=once(stop_preview,'    ExoPlayer previous=mCobraPreviewPlayer;mCobraPreviewPlayer=null;mCobraPreviewSessionKey="";','    ExoPlayer previous=mCobraPreviewPlayer;mCobraPreviewPlayer=null;mCobraPreviewSessionKey="";if(previous!=null)mCobraPreviewStops++;','preview stop counter')
    text=replace_member(text,'stopCobraPreviewPlayerOnly',stop_preview)

    text=replace_member(text,'cobraStartLocalTimeshift',NEW_START_LOCAL_FULLSCREEN)
    text=replace_member(text,'cobraStartDirectSinglePlayer',NEW_DIRECT_SINGLE)
    text=replace_member(text,'cobraStopLocalTimeshift',NEW_STOP_TS)

    attach=member(text,'cobraAttachVideo')
    attach=once(attach,'    binding.texture=texture;player.setVideoTextureView(texture);','    binding.texture=texture;binding.vitals.surfaceAttachCalls++;player.setVideoTextureView(texture);','surface attach metric')
    text=replace_member(text,'cobraAttachVideo',attach)

    binding=member(text,'CobraPlayerBinding',kind='class')
    old='''    @Override public void onPlayerError(PlaybackException failure) {
      if(!current())return;
      if(player==mCobraTimeshiftPlayer)cobraStopLocalTimeshift("player-error");
      if(player==mPlayer)cobraRequestPlayerOrientation(android.content.pm.ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,"player-error");'''
    new='''    @Override public void onPlayerError(PlaybackException failure) {
      if(!current())return;
      final boolean localTimeshift=player==mCobraTimeshiftPlayer;
      if(localTimeshift)cobraStopLocalTimeshift("player-error");
      if(player==mPlayer)cobraRequestPlayerOrientation(android.content.pm.ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,"player-error");'''
    binding=once(binding,old,new,'timeshift error detect')
    anchor='''      InfinityCobraDiagnostics.failure(InfinityLiveActivity.this,"player",failure);
      // Retry only this failed session and only its configured fallback. Never restart healthy peers.'''
    fallback='''      InfinityCobraDiagnostics.failure(InfinityLiveActivity.this,"player",failure);
      if(localTimeshift){
        final ExoPlayer failed=player;final Channel failedChannel=channel;
        mMain.post(()->{
          if(failed==mPlayer&&mPlaying!=null&&failedChannel.id.equals(mPlaying.id)){releaseSinglePlayer();cobraStartDirectSinglePlayer(failedChannel,failedChannel.primaryUrl,"timeshift-transport-fallback");cobraSetTimeshiftUiState("FAILED","direct fallback active");}
          else if(failed==mCobraPreviewPlayer&&mGuidePreviewChannel!=null&&failedChannel.id.equals(mGuidePreviewChannel.id)){mCobraPreviewPlayer=null;mCobraPreviewSessionKey="";cobraDisposePlayer(failed);cobraStartDirectPreview(failedChannel,"timeshift-transport-fallback");cobraSetTimeshiftUiState("FAILED","preview direct fallback");}
        });
        cobraUpdatePlaybackLabels();return;
      }
      // Retry only this failed session and only its configured fallback. Never restart healthy peers.'''
    binding=once(binding,anchor,fallback,'timeshift error direct fallback')
    text=replace_member(text,'CobraPlayerBinding',binding,kind='class')

    vitals=member(text,'CobraSessionVitals',kind='class')
    vitals=once(vitals,'    int loadErrors,bufferRetries,rebufferEvents,longStalls;boolean everReady=false;String lastError="",lastRecovery="not_requested",decoder="Not reported";','    int loadErrors,bufferRetries,rebufferEvents,longStalls,prepareCalls,surfaceAttachCalls;boolean everReady=false;String lastError="",lastRecovery="not_requested",lastPrepareReason="none",decoder="Not reported";','vitals counters')
    text=replace_member(text,'CobraSessionVitals',vitals,kind='class')

    fresh=member(text,'cobraFreshHealthSnapshot')
    fresh=once(fresh,'      root.put("captured_at_ms",System.currentTimeMillis());root.put("snapshot_kind","live_activity_observation");','      root.put("captured_at_ms",System.currentTimeMillis());root.put("snapshot_kind","live_activity_observation");root.put("capture_context",mCobraDiagnosticsCaptureContext);','capture context')
    fresh=once(fresh,'      root.put("preview_height",mCobraPreviewTexture==null?0:mCobraPreviewTexture.getHeight());','      root.put("preview_height",mCobraPreviewTexture==null?0:mCobraPreviewTexture.getHeight());root.put("preview_start_count",mCobraPreviewStartCount);root.put("preview_direct_starts",mCobraPreviewDirectStarts);root.put("preview_timeshift_starts",mCobraPreviewTimeshiftStarts);root.put("preview_handoffs",mCobraPreviewHandoffs);root.put("preview_stops",mCobraPreviewStops);root.put("timeshift_ui_state",cobraTimeshiftStatusText());','preview counters')
    text=replace_member(text,'cobraFreshHealthSnapshot',fresh)

    health=member(text,'cobraAddSessionHealth')
    health=once(health,'      row.put("recovery_state",s.recovery.state);row.put("surface_attempts",s.recovery.attempts);row.put("buffer_retries",s.bufferRetries);row.put("last_recovery_action",s.lastRecovery);','      row.put("recovery_state",s.recovery.state);row.put("surface_attempts",s.recovery.attempts);row.put("surface_attach_calls",s.surfaceAttachCalls);row.put("prepare_calls",s.prepareCalls);row.put("last_prepare_reason",s.lastPrepareReason);row.put("buffer_retries",s.bufferRetries);row.put("last_recovery_action",s.lastRecovery);row.put("buffered_ahead_ms",Math.max(0,b.player.getTotalBufferedDuration()));try{long liveOffset=b.player.getCurrentLiveOffset();row.put("live_edge_ms",liveOffset==C.TIME_UNSET?-1:liveOffset);}catch(RuntimeException ignored){row.put("live_edge_ms",-1);}','session detail metrics')
    health=once(health,'root.put("timeshift_network_stall_ms",mCobraTimeshiftSession.stallMs());','root.put("timeshift_network_stall_ms",mCobraTimeshiftSession.stallMs());root.put("timeshift_http_requests",mCobraTimeshiftSession.httpRequests());root.put("timeshift_http_failures",mCobraTimeshiftSession.httpFailures());root.put("timeshift_playlist_requests",mCobraTimeshiftSession.playlistRequests());root.put("timeshift_segment_requests",mCobraTimeshiftSession.segmentRequests());root.put("timeshift_last_http_error",mCobraTimeshiftSession.lastHttpError());','timeshift http diagnostics')
    text=replace_member(text,'cobraAddSessionHealth',health)

    overlay=member(text,'cobraUpdatePerformanceOverlay')
    overlay=once(overlay,'String shift=mCobraTimeshiftSession==null?"OFF":mCobraTimeshiftSession.shortState();','String shift=cobraTimeshiftStatusText();','timeshift overlay state')
    text=replace_member(text,'cobraUpdatePerformanceOverlay',overlay)

    ts=member(text,'CobraLocalTimeshiftSession',kind='class')
    ts=once(ts,'    private volatile boolean stopped=false,ready=false;private volatile String state="STARTING",lastError="";private volatile long bytesRead=0,reconnects=0,stallMs=0;private volatile long startedElapsed=android.os.SystemClock.elapsedRealtime();','    private volatile boolean stopped=false,ready=false;private volatile String state="STARTING",lastError="",lastHttpError="";private volatile long bytesRead=0,reconnects=0,stallMs=0,httpRequests=0,httpFailures=0,playlistRequests=0,segmentRequests=0;private volatile long startedElapsed=android.os.SystemClock.elapsedRealtime();','http counters')
    ts=once(ts,'    long diskBytes(){synchronized(lock){return totalBytes;}}long reconnects(){return reconnects;}long stallMs(){return stallMs;}long ingestKbps(){long elapsed=Math.max(1,android.os.SystemClock.elapsedRealtime()-startedElapsed);return (bytesRead*8L)/elapsed;}','    long diskBytes(){synchronized(lock){return totalBytes;}}long reconnects(){return reconnects;}long stallMs(){return stallMs;}long httpRequests(){return httpRequests;}long httpFailures(){return httpFailures;}long playlistRequests(){return playlistRequests;}long segmentRequests(){return segmentRequests;}String lastHttpError(){return lastHttpError;}long ingestKbps(){long elapsed=Math.max(1,android.os.SystemClock.elapsedRealtime()-startedElapsed);return (bytesRead*8L)/elapsed;}','http accessors')
    ts=once(ts,'    String diagnostic(){return "state="+state+"; window_s="+Math.round(windowDurationMs()/1000f)+"; bytes="+diskBytes()+"; provider_kbps="+ingestKbps()+"; reconnects="+reconnects+"; stall_ms="+stallMs+(lastError.isEmpty()?"":"; last="+lastError);}','    String diagnostic(){return "state="+state+"; window_s="+Math.round(windowDurationMs()/1000f)+"; bytes="+diskBytes()+"; provider_kbps="+ingestKbps()+"; reconnects="+reconnects+"; stall_ms="+stallMs+"; http="+httpRequests+"/"+httpFailures+"; playlists="+playlistRequests+"; segments="+segmentRequests+(lastError.isEmpty()?"":"; last="+lastError)+(lastHttpError.isEmpty()?"":"; local_http="+lastHttpError);}','diagnostic http')
    ts=replace_inner(ts,'serve',NEW_TS_SERVE)
    ts=replace_inner(ts,'reply',NEW_TS_REPLY)
    ts=replace_inner(ts,'playlist',NEW_TS_PLAYLIST)
    text=replace_member(text,'CobraLocalTimeshiftSession',ts,kind='class')

    marker='  private static final class CobraLocalTimeshiftSession {'
    if text.count(marker)!=1:raise RuntimeError('timeshift class marker drift')
    text=text.replace(marker,TRANSPORT_POLICY.rstrip()+'\n\n'+PREVIEW_HELPERS.rstrip()+'\n\n'+marker,1)

    for n,h in guards.items():
        if sha(member(text,n))!=h:raise RuntimeError('Protected contract changed: '+n)

    required=['CobraTimeshiftTransportPolicy','hasRealHttpFraming','hasRealPlaylistLines','cobraCapturePreviewDiagnostics','mini_preview_direct','preview_timeshift_starts','timeshift_http_failures','timeshift-transport-fallback','preview-timeshift-fullscreen','mCobraPreviewTimeshiftStarts++','cobraPrepareObserved','surfaceAttachCalls++']
    for token in required:
        if token not in text:raise RuntimeError('2103178 contract missing: '+token)
    ts_after=member(text,'CobraLocalTimeshiftSession',kind='class')
    if '\\\\r\\\\n' in ts_after or '"#EXTM3U\\\\n' in ts_after:raise RuntimeError('Escaped local HTTP/HLS framing survived 2103178')
    watchdog=text[text.index('private final Runnable mStallWatchdog'):text.index('private final Runnable mAutoRefresh')]
    if 'mPlayer.prepare()' in watchdog or 'mPlayer.play()' in watchdog:raise RuntimeError('watchdog regained restart behavior')

    after=text.encode();path.write_bytes(after);out.mkdir(parents=True,exist_ok=True);(out/'source-before').mkdir(exist_ok=True);(out/'source-before'/path.name).write_bytes(before_b)
    report={'base_build':BASE_BUILD,'base_commit':LOCKED_COMMIT,'files':{str(REL):{'before':sha(before_b),'after':sha(after)}},'timeshift_http_crlf_repaired':True,'timeshift_playlist_lf_repaired':True,'timeshift_direct_fallback':True,'mini_preview_local_reserve':True,'mini_preview_same_player_handoff':True,'mini_preview_diagnostic_capture':True,'timeshift_explicit_states':True,'native_changed':False,'theme_zip_changed':False,'physical_device_verified':False}
    (out/'patch.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS: 2103178 timeshift transport + mini-player audit/repair applied')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();apply(a.source,a.receipt,a.out)
