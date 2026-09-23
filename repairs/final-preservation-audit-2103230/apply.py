#!/usr/bin/env python3
"""Exact 2103229 successor. No native, provider, timeshift, navigation or theme redesign."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,re
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('parent229',ROOT.parent/'multiview-stability-fill-2103229/apply.py');parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)
ACT=parent.ACT
BEFORE='4af3fc3775fe0711b932bb664385a705f0fc5080deba63b3b21de47986a9146e'
OLD='1.0.9-Cobra-MultiView-Stability-Fill-RC1';NEW='1.0.9-Cobra-Final-Preservation-Audit-RC1'
CHANGED=['cobraRecoverUnexpectedLiveEnded','CobraPlayerBinding','CobraSessionVitals','cobraAddSessionHealth','cobraMultiSafeInsets','cobraFitBinding','openMultiView','onConfigurationChanged','cobraLayoutPlayerPanels','CobraVideoTile','cobraInspectMultiHealth','cobraRecoverMultiTileSession','cobraRetryMultiTile','CobraMultiRecoveryPolicy']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hb(s):return hashlib.sha256(s.encode()).hexdigest()
def once(s,a,b):
 if s.count(a)!=1:raise RuntimeError('Anchor drift: '+a[:140]+': '+str(s.count(a)))
 return s.replace(a,b,1)
def patch(before):
 s=before
 def change(name,fn,kind='method'):
  nonlocal s
  a,b=parent.span(s,name,kind);s=s[:a]+fn(s[a:b])+s[b:]
 s=once(s,'  private boolean mCobraCreatingMulti = false;','  private boolean mCobraCreatingMulti = false;\n  private long mCobraAuditSessionSequence=0L;\n  private int[] mCobraAuditInsets;')
 marker='  private void cobraRecoverUnexpectedLiveEnded(final CobraPlayerBinding binding){'
 s=once(s,marker,(ROOT/'runtime.java.inc').read_text()+'\n'+marker)
 change('cobraRecoverUnexpectedLiveEnded',lambda _: (ROOT/'live-ended.java.inc').read_text().rstrip())
 def binding(x):
  x=once(x,'    final ExoPlayer player;final Channel channel;','    final ExoPlayer player;final Channel channel;\n    final long sessionId=++mCobraAuditSessionSequence;long intentEpoch=0L,stateSerial=0L,playerErrorElapsed=0L;\n    int auditState=-1;boolean fallbackPending=false;JSONObject lastEndSnapshot;')
  x=once(x,'    @Override public void onVideoSizeChanged', '''    @Override public void onTimelineChanged(androidx.media3.common.Timeline timeline,int reason){if(current())vitals.audit.add("timeline",reason,timeline.getWindowCount());}
    @Override public void onMediaItemTransition(MediaItem item,int reason){if(current()){intentEpoch++;fallbackPending=false;liveEndedRecovering=false;vitals.audit.add("media_transition",reason,intentEpoch);}}
    @Override public void onEvents(Player source,Player.Events events){if(current()&&events.contains(Player.EVENT_PLAYBACK_STATE_CHANGED)&&source.getPlaybackState()==Player.STATE_ENDED&&cobraAuditLiveOwner(this))cobraAuditUnexpectedEnd(this);}
    @Override public void onVideoSizeChanged''')
  x=once(x,'    @Override public void onPlayWhenReadyChanged(boolean requested,int reason){if(current()){','    @Override public void onPlayWhenReadyChanged(boolean requested,int reason){if(current()){\n      intentEpoch++;liveEndedRecovering=false;if(!requested)fallbackPending=false;vitals.audit.add("requested",requested?1:0,reason);')
  x=once(x,'    @Override public void onPlaybackStateChanged(int state) {\n      if(!current())return;','    @Override public void onPlaybackStateChanged(int state) {\n      if(!current())return;\n      if(auditState!=state){auditState=state;stateSerial++;liveEndedRecovering=false;}vitals.audit.add("state",state,stateSerial);')
  x=once(x,'        liveEndedRecovering=false;','        liveEndedRecovering=false;cobraAuditVerifyLiveRecovery(this);')
  x=once(x,'      if(CobraLiveEndedPolicy.eligible(vitals.live,!mPlayingVodKey.isEmpty(),player.getPlayWhenReady(),state))','      if(state==Player.STATE_ENDED&&cobraAuditLiveOwner(this))')
  x=once(x,'      error=failure==null?"UNKNOWN":failure.getErrorCodeName();','      error=failure==null?"UNKNOWN":failure.getErrorCodeName();\n      playerErrorElapsed=android.os.SystemClock.elapsedRealtime();vitals.audit.add("player_error",failure==null?-1:failure.errorCode,0L);')
  old='''        fallback=true;boolean requested=player.getPlayWhenReady();final long retryEpoch=mCobraPlaybackPolicy.epoch;
        mMain.postDelayed(()->{
          if(!current()||"primary".equals(vitals.preferences.fallback)||!mCobraPlaybackPolicy.acceptsRetry(retryEpoch,requested&&player.getPlayWhenReady(),cobraPlaybackMayRun(player)))return;
          player.setMediaItem(mediaItem(channel.fallbackUrl));player.prepare();
          if(requested)startCobraPlayer(player);
        },250L);'''
  new='''        if(fallbackPending)return;
        fallbackPending=true;final long retryEpoch=intentEpoch;
        mMain.postDelayed(()->{
          if(!current()||intentEpoch!=retryEpoch)return;
          fallbackPending=false;
          if("primary".equals(vitals.preferences.fallback)||!cobraAuditRetryAllowed(this,retryEpoch))return;
          try{
            fallback=true;vitals.audit.add("fallback_prepare",retryEpoch,0L);vitals.prepareCalls++;vitals.lastPrepareReason="error-fallback";
            player.setMediaItem(mediaItem(channel.fallbackUrl));player.prepare();startCobraPlayer(player);
          }catch(RuntimeException retryFailure){InfinityCobraDiagnostics.failure(InfinityLiveActivity.this,"fallback-prepare",retryFailure);}
        },250L);'''
  return once(x,old,new)
 change('CobraPlayerBinding',binding,'class')
 def vitals(x):
  x=once(x,'    final long createdAt=', '    final CobraAuditTrail audit=new CobraAuditTrail();\n    final long createdAt=')
  x=once(x,'{lastLoadMs=info.loadDurationMs;','{audit.add("load_complete",info.bytesLoaded,data.dataType);lastLoadMs=info.loadDurationMs;')
  x=once(x,'{if(!canceled){loadErrors++;','{audit.add(canceled?"load_error_canceled":"load_error",info.bytesLoaded,data.dataType);if(!canceled){loadErrors++;')
  x=once(x,'{decoder=name==null?', '{audit.add("decoder_init",time,duration);decoder=name==null?')
  pos=x.rfind('  }')
  return x[:pos]+'''    @Override public void onLoadStarted(androidx.media3.exoplayer.analytics.AnalyticsListener.EventTime event,androidx.media3.exoplayer.source.LoadEventInfo info,androidx.media3.exoplayer.source.MediaLoadData data){audit.add("load_start",info.loadTaskId,data.dataType);}
    @Override public void onLoadCanceled(androidx.media3.exoplayer.analytics.AnalyticsListener.EventTime event,androidx.media3.exoplayer.source.LoadEventInfo info,androidx.media3.exoplayer.source.MediaLoadData data){audit.add("load_cancel",info.bytesLoaded,data.dataType);}
    @Override public void onVideoDecoderReleased(androidx.media3.exoplayer.analytics.AnalyticsListener.EventTime event,String name){audit.add("decoder_release",0L,0L);}
'''+x[pos:]
 change('CobraSessionVitals',vitals,'class')
 change('cobraAddSessionHealth',lambda x:once(x,'      row.put("role",','      row.put("audit_session",b.sessionId);row.put("recent_playback_events",s.audit.snapshot());if(b.lastEndSnapshot!=null)row.put("last_unexpected_live_end",b.lastEndSnapshot);\n      row.put("role",'))
 change('cobraFitBinding',lambda x:once(x,'!mInPictureInPicture&&cobraMultiViewPlayer(binding.player)&&cobraMultiFillScreen()','cobraAuditFillApplies(binding)'))
 change('cobraMultiSafeInsets',lambda x:once(x,'    return new int[]{Math.max(0,left),Math.max(0,top),Math.max(0,right),Math.max(0,bottom)};', '''    View root=getWindow().getDecorView();int[] canvasPosition=new int[2],rootPosition=new int[2];
    mCobraMultiCanvas.getLocationInWindow(canvasPosition);root.getLocationInWindow(rootPosition);
    return CobraAuditPolicy.localInsets(canvasPosition[0]-rootPosition[0],canvasPosition[1]-rootPosition[1],
        mCobraMultiCanvas.getWidth(),mCobraMultiCanvas.getHeight(),root.getWidth(),root.getHeight(),left,top,right,bottom);'''))
 change('openMultiView',lambda x:once(x,'      mCobraMultiCanvas.addOnLayoutChangeListener', '''      mCobraMultiCanvas.setOnApplyWindowInsetsListener((v,insets)->{v.post(()->{
        if(v!=mCobraMultiCanvas)return;int[] next=cobraMultiSafeInsets();
        if(!java.util.Arrays.equals(next,mCobraAuditInsets)){mCobraAuditInsets=next;cobraLayoutMultiTiles();}
      });return insets;});
      mCobraMultiCanvas.addOnLayoutChangeListener'''))
 change('onConfigurationChanged',lambda x:once(x,'    if(mMultiOverlay!=null){cobraLayoutPlayerPanels();cobraLayoutMultiTiles();return;}','    if(mMultiOverlay!=null&&!mCobraMultiFullscreenActive){cobraLayoutPlayerPanels();cobraLayoutMultiTiles();return;}'))
 def panels(x):
  x=once(x,'    FrameLayout root=mMultiOverlay!=null?mMultiOverlay:mPlayerOverlay;', '    boolean multi=mMultiOverlay!=null&&!mCobraMultiFullscreenActive;FrameLayout root=multi?mMultiOverlay:mPlayerOverlay;')
  x=once(x,'    View video=mMultiOverlay!=null?mCobraMultiCanvas:mPlayerTexture;','    View video=multi?mCobraMultiCanvas:mPlayerTexture;')
  return once(x,'if(mPlayerTexture!=null&&mMultiOverlay==null)','if(mPlayerTexture!=null&&!multi)')
 change('cobraLayoutPlayerPanels',panels)
 change('CobraMultiRecoveryPolicy',lambda x:once(x,'      if(!live||!requested||suppression!=Player.PLAYBACK_SUPPRESSION_REASON_NONE)return "";','      if(!live||!requested||suppression!=Player.PLAYBACK_SUPPRESSION_REASON_NONE||state==Player.STATE_ENDED)return "";'),'class')
 change('CobraVideoTile',lambda x:once(x,'    ExoPlayer player;','    long mediaProgressAt=android.os.SystemClock.elapsedRealtime(),observedPosition=-1L,observedBufferedPosition=-1L,observedLoad=-1L;\n    ExoPlayer player;'),'class')
 change('cobraRetryMultiTile',lambda x:once(x,'    mCobraCreatingMulti=true;','    tile.mediaProgressAt=tile.changed;tile.observedPosition=tile.observedBufferedPosition=tile.observedLoad=-1L;\n    mCobraCreatingMulti=true;'))
 change('cobraRecoverMultiTileSession',lambda x:once(x,'    ExoPlayer player=tile.player;','    ExoPlayer player=tile.player;\n    if(!binding.vitals.live||binding.fallbackPending||mCobraTiles.get(tile.channel.id)!=tile\n        ||player.getPlaybackState()==Player.STATE_ENDED||!cobraAuditRetryAllowed(binding,binding.intentEpoch))return false;'))
 def inspect(x):
  x=once(x,'    long now=android.os.SystemClock.elapsedRealtime(),wall=System.currentTimeMillis();','    long now=android.os.SystemClock.elapsedRealtime();')
  x=once(x,'        androidx.media3.exoplayer.DecoderCounters counters=', '''        if(playbackState!=Player.STATE_READY||!player.getPlayWhenReady()||player.getPlaybackSuppressionReason()!=Player.PLAYBACK_SUPPRESSION_REASON_NONE||now-tile.changed>5000L)tile.stableSince=0L;
        long position=player.getCurrentPosition(),bufferedPosition=player.getBufferedPosition(),load=binding==null?-1L:binding.vitals.lastLoadCompletedElapsed;
        if(position!=tile.observedPosition||bufferedPosition!=tile.observedBufferedPosition||load!=tile.observedLoad){
          tile.mediaProgressAt=now;tile.observedPosition=position;tile.observedBufferedPosition=bufferedPosition;tile.observedLoad=load;
        }
        androidx.media3.exoplayer.DecoderCounters counters=''' )
  x=once(x,'          if(frames!=tile.frames){\n            tile.frames=frames;tile.changed=now;tile.recovering=false;', '          if(frames<tile.frames)tile.stableSince=0L;\n          boolean progressed=frames>Math.max(0,tile.frames);tile.frames=frames;\n          if(progressed){\n            tile.changed=now;tile.mediaProgressAt=now;if(playbackState==Player.STATE_READY)tile.recovering=false;')
  x=once(x,'long errorAge=binding==null||binding.vitals.lastErrorAt<=0L?0L:Math.max(0L,wall-binding.vitals.lastErrorAt);','long errorAge=binding==null||binding.playerErrorElapsed<=0L?0L:Math.max(0L,now-binding.playerErrorElapsed);')
  x=once(x,'boolean fallbackInFlight=hasError&&binding.fallback&&!tile.recovering;', 'boolean fallbackInFlight=binding!=null&&binding.fallbackPending;')
  return once(x,'        if(!reason.isEmpty()&&!tile.recovering&&cobraRecoverMultiTileSession', '''        if(fallbackInFlight||("buffering".equals(reason)&&!CobraAuditPolicy.stalledBuffer(player.isLoading(),now,tile.mediaProgressAt)))reason="";
        if(!reason.isEmpty()&&!tile.recovering&&cobraRecoverMultiTileSession''')
 change('cobraInspectMultiHealth',inspect)
 return s

def main():
 p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);a=p.parse_args();shell=a.shell
 activity=shell/ACT;assert sha(activity)==BEFORE,'Not exact locked 2103229 activity'
 receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text());assert receipt['version_code']==2103229
 inventory={str(p.relative_to(shell)):sha(p) for p in sorted(shell.rglob('*')) if p.is_file()}
 before=activity.read_text();after=patch(before)
 # Every top-level member outside the explicitly reviewed substitutions must remain identical.
 def strip(s):
  for n in CHANGED:
   kind='class' if n in ['CobraPlayerBinding','CobraSessionVitals','CobraVideoTile','CobraMultiRecoveryPolicy'] else 'method'
   a,b=parent.span(s,n,kind);s=s[:a]+'/* reviewed:'+n+' */'+s[b:]
  return s
 normalized=strip(after).replace((ROOT/'runtime.java.inc').read_text()+'\n','').replace('  private long mCobraAuditSessionSequence=0L;\n  private int[] mCobraAuditInsets;\n','')
 assert normalized==strip(before),'Unreviewed Activity bytes changed'
 activity.write_text(after)
 gradle=shell/'tools/android/packaging/xbmc/build.gradle.in';g=gradle.read_text();g=once(g,'versionCode 2103229','versionCode 2103230');g=once(g,'versionName "'+OLD+'"','versionName "'+NEW+'"');gradle.write_text(g)
 for path in ['scripts/infinity_background_resume.py','scripts/package_background_resume.py']:
  fp=Path(path);s=fp.read_text();assert OLD in s;s=s.replace(OLD,NEW)
  if path.endswith('infinity_background_resume.py'):s=once(s,'VERSION_CODE = 2103229','VERSION_CODE = 2103230')
  fp.write_text(s)
 changed=[n for n,d in inventory.items() if sha(shell/n)!=d]
 assert set(changed)=={ACT,'tools/android/packaging/xbmc/build.gradle.in'},changed
 for n in changed:receipt['files'][n]['after']=sha(shell/n)
 receipt.update(version_code=2103230,version_name=NEW,source_parent=2103229,candidate_locked=False,physical_device_verified=False,runtime_device_tested=False,native_engine_rebuilt=False,final_preservation_audit=True,live_ended_root_cause_confirmed=False)
 receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
 for n,row in receipt['files'].items():assert sha(shell/n)==row['after'],n
 out=Path('audit230');out.mkdir(exist_ok=True)
 (out/'source-preservation.json').write_text(json.dumps(dict(parent=2103229,build=2103230,parent_commit='7fbfc5ade1e96b272b8e7ba584332cb6c81d01bc',before=BEFORE,after=sha(activity),changed_files=changed,changed_members=CHANGED,files_before=inventory,unreviewed_activity_bytes_identical=True,physical_device_verified=False),indent=2)+'\n')
 print('PASS: exact 2103229 source; 2 generated files changed; all unreviewed Activity bytes and other files preserved')
if __name__=='__main__':main()
