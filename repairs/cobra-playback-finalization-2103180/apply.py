#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,re

REL=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
BASE_BUILD=2103179
BASE_COMMIT='0560b18c497e9861864126d96f9b784e488ebe32'
BASE_NAME='1.0.9-Cobra-Buffer-Resilience-RC1'

def sha(v):return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()
def once(s,a,b,label):
    c=s.count(a)
    if c!=1:raise RuntimeError(f'{label}: expected one anchor, got {c}')
    return s.replace(a,b,1)
def matches(text,name,kind='method'):
    if kind=='method':return list(re.finditer(r'^[ \t]{2,}(?:(?:@Override(?:[ \t]*\n[ \t]+|[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',text,re.M))
    return list(re.finditer(r'^[ \t]{2,}(?:(?:private|public|protected|static|final)\s+)*class\s+'+re.escape(name)+r'\b',text,re.M))
def span(text,name,kind='method'):
    ms=matches(text,name,kind)
    if len(ms)!=1:raise RuntimeError(f'{kind} cardinality {name}={len(ms)}')
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
    raise RuntimeError('unclosed '+name)
def member(text,name,kind='method'):
    a,b=span(text,name,kind);return text[a:b]
def replace_member(text,name,new,kind='method'):
    a,b=span(text,name,kind);return text[:a]+new.rstrip()+'\n'+text[b:]

AUDIO_HELPERS=r'''  static final class CobraCallAudioPolicy {
    static boolean preserveVideo(int focusChange){return focusChange==AudioManager.AUDIOFOCUS_LOSS||focusChange==AudioManager.AUDIOFOCUS_LOSS_TRANSIENT||focusChange==AudioManager.AUDIOFOCUS_LOSS_TRANSIENT_CAN_DUCK;}
    static boolean muteForFocus(int focusChange){return preserveVideo(focusChange);}
  }
  private AudioManager mCobraAudioManager;
  private ExoPlayer mCobraAudioFocusPlayer;
  private boolean mCobraAudioFocusMuted=false;
  private final AudioManager.OnAudioFocusChangeListener mCobraAudioFocusListener=this::cobraHandleAudioFocus;

  private boolean cobraPlayerAudioSelected(ExoPlayer player){
    if(player==null)return false;if(player==mPlayer)return true;if(player==mCobraPreviewPlayer)return !mCobraPreviewMuted;
    if(mMultiPlayers!=null)for(int i=0;i<mMultiPlayers.length;i++)if(mMultiPlayers[i]==player)return i==mAudioTile;
    return player==mCobraTransferPlayer||player==mCobraCarryPlayer;
  }

  private void cobraHandleAudioFocus(int change){
    ExoPlayer player=mCobraAudioFocusPlayer;if(player==null)return;
    if(change==AudioManager.AUDIOFOCUS_GAIN){mCobraAudioFocusMuted=false;if(isCurrentCobraPlayer(player)&&cobraPlayerAudioSelected(player))player.setVolume(1f);InfinityCobraDiagnostics.record(this,"audio-focus","gain","video_preserved=true");return;}
    if(CobraCallAudioPolicy.muteForFocus(change)){mCobraAudioFocusMuted=true;if(isCurrentCobraPlayer(player))player.setVolume(0f);InfinityCobraDiagnostics.record(this,"audio-focus","yield","video_preserved=true; focus="+change);}
  }

  private void cobraClaimAudioFocus(ExoPlayer player){
    if(player==null)return;
    if(mCobraAudioManager==null)mCobraAudioManager=(AudioManager)getSystemService(Context.AUDIO_SERVICE);
    if(mCobraAudioManager==null){player.setVolume(1f);return;}
    if(mCobraAudioFocusPlayer!=null&&mCobraAudioFocusPlayer!=player)cobraReleaseAudioFocus(mCobraAudioFocusPlayer);
    mCobraAudioFocusPlayer=player;
    int result=mCobraAudioManager.requestAudioFocus(mCobraAudioFocusListener,AudioManager.STREAM_MUSIC,AudioManager.AUDIOFOCUS_GAIN);
    mCobraAudioFocusMuted=result!=AudioManager.AUDIOFOCUS_REQUEST_GRANTED;
    player.setVolume(mCobraAudioFocusMuted?0f:1f);
  }

  private void cobraReleaseAudioFocus(ExoPlayer player){
    if(player==null||player!=mCobraAudioFocusPlayer)return;
    if(mCobraAudioManager!=null)try{mCobraAudioManager.abandonAudioFocus(mCobraAudioFocusListener);}catch(RuntimeException ignored){}
    mCobraAudioFocusPlayer=null;mCobraAudioFocusMuted=false;
  }
'''

TIMESHIFT_SEEK=r'''  private boolean cobraTimeshiftTimelineAvailable(){
    try{return mPlayer!=null&&cobraLiveChannel(mPlaying)&&mPlayer.isCurrentMediaItemSeekable()&&mPlayer.getDuration()>0&&mPlayer.getDuration()!=C.TIME_UNSET;}
    catch(RuntimeException unavailable){return false;}
  }

  private void cobraUpdateTimeshiftSeek(){
    if(mCobraTimeshiftSeek==null)return;
    boolean available=cobraTimeshiftTimelineAvailable();long duration=0,position=0;
    if(available)try{duration=mPlayer.getDuration();position=mPlayer.getCurrentPosition();}catch(RuntimeException unavailable){available=false;}
    if(!available){mCobraTimeshiftSeek.setVisibility(View.GONE);return;}
    int value=(int)Math.max(0,Math.min(1000,(position*1000L)/Math.max(1,duration)));
    mCobraTimeshiftSeek.setVisibility(View.VISIBLE);
    if(mCobraPlayerProgramProgress!=null){mCobraPlayerProgramProgress.setVisibility(View.VISIBLE);mCobraPlayerProgramProgress.setProgress(value);}
    if(!mCobraTimeshiftDragging)mCobraTimeshiftSeek.setProgress(value);
  }'''

def apply(source,receipt_path,out):
    source=Path(source);out=Path(out);receipt=json.loads(Path(receipt_path).read_text())
    if receipt.get('version_code')!=BASE_BUILD or receipt.get('version_name')!=BASE_NAME:raise RuntimeError('Expected exact passed 2103179 source receipt')
    path=source/REL;before_b=path.read_bytes();before=before_b.decode();expected=receipt.get('files',{}).get(str(REL),{}).get('after')
    if not expected or sha(before_b)!=expected:raise RuntimeError('2103179 Activity preimage mismatch')
    text=before

    protected=['cobraStartLocalTimeshift','cobraStartLocalTimeshiftPreview','cobraStartProviderCatchup','cobraGoLive','cobraRewindLive','onStop','onPictureInPictureModeChanged','cobraAttachVideo','cobraApplyDisplayPerformance','cobraTuneLastChannel']
    guards={n:sha(member(before,n)) for n in protected}

    transport=member(text,'CobraTimeshiftTransportPolicy',kind='class')
    transport=once(transport,'    static final int READ_TIMEOUT_MS=5000;','    static final int READ_TIMEOUT_MS=15000;\n    static final long LIVE_RESERVE_MS=15000L;','timeshift read timeout/reserve')
    transport=once(transport,'          +"#EXT-X-START:TIME-OFFSET=-9.0,PRECISE=NO\\n";','          +"#EXT-X-START:TIME-OFFSET=-15.0,PRECISE=NO\\n";','timeshift playlist reserve')
    text=replace_member(text,'CobraTimeshiftTransportPolicy',transport,kind='class')

    media=member(text,'mediaItem')
    media=once(media,'    if (lower.contains(".m3u8")) item.setMimeType("application/x-mpegURL");',
'''    if (lower.contains(".m3u8")) {
      item.setMimeType("application/x-mpegURL");
      if(lower.contains("127.0.0.1")&&lower.contains("/live.m3u8")){
        item.setLiveConfiguration(new MediaItem.LiveConfiguration.Builder()
            .setTargetOffsetMs(CobraTimeshiftTransportPolicy.LIVE_RESERVE_MS)
            .setMinOffsetMs(12000L).setMaxOffsetMs(24000L)
            .setMinPlaybackSpeed(.98f).setMaxPlaybackSpeed(1.02f).build());
      }
    }''','local timeshift live target')
    text=replace_member(text,'mediaItem',media)

    chrome=member(text,'cobraBuildPlayerChrome')
    old='''    mCobraPlayerProgramProgress=cobraProgress(true);LinearLayout.LayoutParams progress=new LinearLayout.LayoutParams(-1,dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.31",3)));progress.topMargin=dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.32",8));progress.bottomMargin=dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.33",8));footer.addView(mCobraPlayerProgramProgress,progress);
    mCobraTimeshiftSeek=new android.widget.SeekBar(this);mCobraTimeshiftSeek.setTag("cobra_live_timeshift_seek");mCobraTimeshiftSeek.setMax(1000);mCobraTimeshiftSeek.setVisibility(View.GONE);mCobraTimeshiftSeek.setContentDescription("Live TV timeshift position");mCobraTimeshiftSeek.setOnSeekBarChangeListener(new android.widget.SeekBar.OnSeekBarChangeListener(){public void onStartTrackingTouch(android.widget.SeekBar b){mCobraTimeshiftDragging=true;mMain.removeCallbacks(mHideChrome);}public void onProgressChanged(android.widget.SeekBar b,int value,boolean user){if(!user||mPlayer==null)return;long duration=mPlayer.getDuration();if(duration>0&&duration!=C.TIME_UNSET&&mPlayer.isCurrentMediaItemSeekable())mPlayer.seekTo((duration*value)/1000L);}public void onStopTrackingTouch(android.widget.SeekBar b){mCobraTimeshiftDragging=false;showPlayerChromeTemporarily();}});footer.addView(mCobraTimeshiftSeek,new LinearLayout.LayoutParams(-1,dp(28)));'''
    new='''    FrameLayout timeline=new FrameLayout(this);timeline.setTag("cobra_unified_live_timeline");
    mCobraPlayerProgramProgress=cobraProgress(true);FrameLayout.LayoutParams lineProgress=new FrameLayout.LayoutParams(-1,dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.31",3)),Gravity.CENTER_VERTICAL);timeline.addView(mCobraPlayerProgramProgress,lineProgress);
    mCobraTimeshiftSeek=new android.widget.SeekBar(this);mCobraTimeshiftSeek.setTag("cobra_live_timeshift_seek");mCobraTimeshiftSeek.setMax(1000);mCobraTimeshiftSeek.setVisibility(View.GONE);mCobraTimeshiftSeek.setContentDescription("Live TV timeline");mCobraTimeshiftSeek.setSplitTrack(false);mCobraTimeshiftSeek.setPadding(0,0,0,0);mCobraTimeshiftSeek.setProgressTintList(android.content.res.ColorStateList.valueOf(Color.TRANSPARENT));mCobraTimeshiftSeek.setProgressBackgroundTintList(android.content.res.ColorStateList.valueOf(Color.TRANSPARENT));
    GradientDrawable timelineThumb=new GradientDrawable();timelineThumb.setShape(GradientDrawable.OVAL);timelineThumb.setColor(vtheme().color("cobra.cobraProgress.colors.1",0xff41c8ef));timelineThumb.setSize(dp(12),dp(12));mCobraTimeshiftSeek.setThumb(timelineThumb);
    mCobraTimeshiftSeek.setOnSeekBarChangeListener(new android.widget.SeekBar.OnSeekBarChangeListener(){public void onStartTrackingTouch(android.widget.SeekBar b){mCobraTimeshiftDragging=true;mMain.removeCallbacks(mHideChrome);}public void onProgressChanged(android.widget.SeekBar b,int value,boolean user){if(!user||mPlayer==null)return;long duration=mPlayer.getDuration();if(duration>0&&duration!=C.TIME_UNSET&&mPlayer.isCurrentMediaItemSeekable()){if(mCobraPlayerProgramProgress!=null)mCobraPlayerProgramProgress.setProgress(value);mPlayer.seekTo((duration*value)/1000L);}}public void onStopTrackingTouch(android.widget.SeekBar b){mCobraTimeshiftDragging=false;showPlayerChromeTemporarily();}});timeline.addView(mCobraTimeshiftSeek,new FrameLayout.LayoutParams(-1,dp(28),Gravity.CENTER_VERTICAL));
    LinearLayout.LayoutParams timelineLp=new LinearLayout.LayoutParams(-1,dp(28));timelineLp.topMargin=dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.32",8));timelineLp.bottomMargin=dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.33",8));footer.addView(timeline,timelineLp);'''
    chrome=once(chrome,old,new,'unified blue timeline')
    text=replace_member(text,'cobraBuildPlayerChrome',chrome)

    text=replace_member(text,'cobraUpdateTimeshiftSeek',TIMESHIFT_SEEK)
    labels=member(text,'cobraRefreshProgrammeLabels')
    labels=once(labels,
'    if(mCobraPlayerProgramProgress!=null){mCobraPlayerProgramProgress.setVisibility(now==null?View.INVISIBLE:View.VISIBLE);if(now!=null)mCobraPlayerProgramProgress.setProgress(Math.round(CobraGuideMath.progress(now.start,now.stop,System.currentTimeMillis())*1000));}',
'    if(mCobraPlayerProgramProgress!=null&&!cobraTimeshiftTimelineAvailable()){mCobraPlayerProgramProgress.setVisibility(now==null?View.INVISIBLE:View.VISIBLE);if(now!=null)mCobraPlayerProgramProgress.setProgress(Math.round(CobraGuideMath.progress(now.start,now.stop,System.currentTimeMillis())*1000));}',
'unified timeline program mode')
    text=replace_member(text,'cobraRefreshProgrammeLabels',labels)

    marker='  static final class CobraWindowLifecyclePolicy {'
    if text.count(marker)!=1:raise RuntimeError('audio helper marker drift')
    text=text.replace(marker,AUDIO_HELPERS+'\n'+marker,1)

    build=member(text,'buildPlayer')
    build=once(build,'.setContentType(C.AUDIO_CONTENT_TYPE_MOVIE).build(),audible);','.setContentType(C.AUDIO_CONTENT_TYPE_MOVIE).build(),false);','disable Media3 auto-pause focus')
    build=once(build,'    cobraAttachVideo(player,texture);cobraStartHealthTicker();','    cobraAttachVideo(player,texture);if(audible)cobraClaimAudioFocus(player);cobraStartHealthTicker();','claim app audio focus')
    text=replace_member(text,'buildPlayer',build)

    previewmute=member(text,'toggleCobraPreviewMute')
    previewmute=once(previewmute,'    if (mCobraPreviewPlayer != null) mCobraPreviewPlayer.setVolume(mCobraPreviewMuted ? 0f : 1f);','    if (mCobraPreviewPlayer != null) {if(mCobraPreviewMuted){cobraReleaseAudioFocus(mCobraPreviewPlayer);mCobraPreviewPlayer.setVolume(0f);}else cobraClaimAudioFocus(mCobraPreviewPlayer);}','preview mute focus ownership')
    text=replace_member(text,'toggleCobraPreviewMute',previewmute)

    closepreview=member(text,'closeFullscreenToCobraView')
    closepreview=once(closepreview,'    cobraAttachVideo(session,mCobraPreviewTexture);session.setVolume(mCobraPreviewMuted?0f:1f);','    cobraAttachVideo(session,mCobraPreviewTexture);if(mCobraPreviewMuted){cobraReleaseAudioFocus(session);session.setVolume(0f);}else cobraClaimAudioFocus(session);','fullscreen preview audio focus')
    text=replace_member(text,'closeFullscreenToCobraView',closepreview)

    text=text.replace('session.setAudioAttributes(session.getAudioAttributes(),true);session.setVolume(1f);','session.setAudioAttributes(session.getAudioAttributes(),false);session.setVolume(1f);cobraClaimAudioFocus(session);')
    multi=member(text,'setMultiAudio')
    multi=once(multi,'for(int i=0;i<mMultiPlayers.length;i++)if(mMultiPlayers[i]!=null&&i!=index){mMultiPlayers[i].setAudioAttributes(mMultiPlayers[i].getAudioAttributes(),false);mMultiPlayers[i].setVolume(0f);}',
'for(int i=0;i<mMultiPlayers.length;i++)if(mMultiPlayers[i]!=null&&i!=index){cobraReleaseAudioFocus(mMultiPlayers[i]);mMultiPlayers[i].setAudioAttributes(mMultiPlayers[i].getAudioAttributes(),false);mMultiPlayers[i].setVolume(0f);}',
'multiview release focus')
    multi=once(multi,'if(mMultiPlayers[index]!=null){mMultiPlayers[index].setAudioAttributes(mMultiPlayers[index].getAudioAttributes(),true);mMultiPlayers[index].setVolume(1f);}',
'if(mMultiPlayers[index]!=null){mMultiPlayers[index].setAudioAttributes(mMultiPlayers[index].getAudioAttributes(),false);mMultiPlayers[index].setVolume(1f);cobraClaimAudioFocus(mMultiPlayers[index]);}',
'multiview claim focus')
    text=replace_member(text,'setMultiAudio',multi)

    start=member(text,'startCobraPlayer')
    start=once(start,'    }else player.play();','    }else {if(player.getVolume()>0f)cobraClaimAudioFocus(player);player.play();}','player start focus')
    text=replace_member(text,'startCobraPlayer',start)

    dispose=member(text,'cobraDisposePlayer')
    dispose=once(dispose,'    mBackgroundResumePlayers.remove(player);','    mBackgroundResumePlayers.remove(player);cobraReleaseAudioFocus(player);','dispose focus')
    text=replace_member(text,'cobraDisposePlayer',dispose)

    if re.search(r'setAudioAttributes\([^\n;]*,true\)',text):raise RuntimeError('Media3 managed audio focus survived call-continuity repair')

    for n,h in guards.items():
        if sha(member(text,n))!=h:raise RuntimeError('Protected contract changed: '+n)

    required=['READ_TIMEOUT_MS=15000','LIVE_RESERVE_MS=15000L','TIME-OFFSET=-15.0','setTargetOffsetMs(CobraTimeshiftTransportPolicy.LIVE_RESERVE_MS)',
      'cobra_unified_live_timeline','Color.TRANSPARENT','timelineThumb','cobraTimeshiftTimelineAvailable','CobraCallAudioPolicy','video_preserved=true','cobraClaimAudioFocus','cobraReleaseAudioFocus',
      'buffer_observed_no_restart','MAX_AUTO_LIVE_EDGE_ATTEMPTS=2','RECOVERY_COOLDOWN_MS=60000L']
    for token in required:
        if token not in text:raise RuntimeError('2103180 contract missing: '+token)
    if 'footer.addView(mCobraTimeshiftSeek' in member(text,'cobraBuildPlayerChrome'):raise RuntimeError('yellow second scrubber still separately rendered')
    watchdog=text[text.index('private final Runnable mStallWatchdog'):text.index('private final Runnable mAutoRefresh')]
    if 'mPlayer.prepare()' in watchdog or 'mPlayer.play()' in watchdog:raise RuntimeError('watchdog regained restart behavior')

    after=text.encode();path.write_bytes(after);out.mkdir(parents=True,exist_ok=True);(out/'source-before').mkdir(exist_ok=True);(out/'source-before'/path.name).write_bytes(before_b)
    report={'base_build':BASE_BUILD,'base_commit':BASE_COMMIT,'files':{str(REL):{'before':sha(before_b),'after':sha(after)}},
      'provider_read_timeout_ms':15000,'live_reserve_ms':15000,'live_target_min_ms':12000,'live_target_max_ms':24000,
      'single_unified_blue_timeline':True,'yellow_scrubber_removed':True,'phone_call_video_continuity':True,'transient_focus_mutes_without_pause':True,
      'media3_managed_focus_disabled':True,'pro_buffer_safeguards_preserved':True,'native_changed':False,'theme_zip_changed':False,'physical_device_verified':False}
    (out/'patch.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: 2103180 playback finalization patch applied')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();apply(a.source,a.receipt,a.out)
