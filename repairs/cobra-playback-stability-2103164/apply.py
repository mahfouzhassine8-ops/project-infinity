#!/usr/bin/env python3
"""Exact 2103163 Android-only stability delta. Fail closed on source drift."""
from pathlib import Path
import argparse,hashlib,json,re
ROOT=Path(__file__).resolve().parent
SOURCE=Path('tools/android/packaging/xbmc/src')
PRE={'InfinityLiveActivity.java.in':'2226306907b9a702e8d3b54bdffddc2f116aa597142d64cef19228b202789feb','InfinityExtendedBackgroundService.java.in':'1a20a06c446fc4b5d2467ea44cd768fa7b3271132f6022a7ea3abd6fec71afcb'}
def digest(b):return hashlib.sha256(b if isinstance(b,bytes) else b.encode()).hexdigest()
def once(s,a,b):
 if s.count(a)!=1:raise ValueError('Expected unique anchor (%d): %s'%(s.count(a),a[:150]))
 return s.replace(a,b,1)
def end(s,start):
 i=s.index('{',start);depth=0;quote=None;escape=False;line=False;block=False
 while i<len(s):
  c=s[i];n=s[i+1:i+2]
  if line:
   if c=='\n':line=False
  elif block:
   if c=='*' and n=='/':block=False;i+=1
  elif quote:
   if escape:escape=False
   elif c=='\\':escape=True
   elif c==quote:quote=None
  elif c=='/' and n=='/':line=True;i+=1
  elif c=='/' and n=='*':block=True;i+=1
  elif c in ('"',"'"):quote=c
  elif c=='{':depth+=1
  elif c=='}':
   depth-=1
   if depth==0:return i+1
  i+=1
 raise ValueError('Unclosed Java block')
def span(s,name):
 matches=list(re.finditer(r'^  (?:(?:@Override\s*)?)(?:public|private|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',s,re.M))
 if len(matches)!=1:raise ValueError('Method cardinality: '+name+' '+str(len(matches)))
 start=matches[0].start();return start,end(s,start)
def method(s,name,new):
 a,b=span(s,name);return s[:a]+new.rstrip()+s[b:]
def edit(s,name,old,new):
 a,b=span(s,name);return s[:a]+once(s[a:b],old,new)+s[b:]
def append(s,filename):
 pos=s.rfind('\n}');assert pos>=0;return s[:pos]+'\n'+(ROOT/filename).read_text()+'\n'+s[pos:]

def activity(s):
 s=edit(s,'onPause','    super.onPause();','    mCobraPlaybackPolicy.pause();\n    super.onPause();')
 s=edit(s,'onResume','    super.onResume();','    super.onResume();\n    mCobraPlaybackPolicy.resume(isCobraInPictureInPicture());')
 s=edit(s,'onStop','    if (!isCobraInPictureInPicture()) {if(!mCobraMiniBackgroundActive)mCobraMiniBackgroundActive=cobraBeginMiniBackgroundPlayback();pauseCobraForBackground();}',
'''    int decision=mCobraPlaybackPolicy.stop(isCobraInPictureInPicture(),cobraMiniBackgroundEnabled()&&cobraMiniPreviewPlaying());
    if(decision==CobraPlaybackPolicy.STOP_PIP)cobraHaltHiddenPlayback();
    else {
      if(decision==CobraPlaybackPolicy.MINI_AUDIO&&!mCobraMiniBackgroundActive)mCobraMiniBackgroundActive=cobraBeginMiniBackgroundPlayback();
      if(decision!=CobraPlaybackPolicy.MINI_AUDIO)cobraEndMiniBackgroundPlayback();
      pauseCobraForBackground();
    }''')
 s=method(s,'onUserLeaveHint','''  @Override protected void onUserLeaveHint(){
    super.onUserLeaveHint();
    if(cobraWantsFullscreenPip()){
      cobraEndMiniBackgroundPlayback();
      // Android 12+ owns auto-entry; do not also call the manual entry API.
      if(Build.VERSION.SDK_INT>=31&&mMultiOverlay==null)configureCobraPip(true);
      else enterCobraPictureInPicture();
    }else mCobraMiniBackgroundActive=cobraBeginMiniBackgroundPlayback();
  }''')
 s=edit(s,'onPictureInPictureModeChanged',
'''    if(inPictureInPictureMode)cobraRequestPlayerOrientation(android.content.pm.ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,"pip-enter");else cobraApplyPlayerRotation("pip-exit");
    super.onPictureInPictureModeChanged(inPictureInPictureMode,configuration);mInPictureInPicture=inPictureInPictureMode;''',
'''    super.onPictureInPictureModeChanged(inPictureInPictureMode,configuration);mInPictureInPicture=inPictureInPictureMode;
    mCobraPlaybackPolicy.pipChanged(inPictureInPictureMode);
    if(inPictureInPictureMode){cobraEndMiniBackgroundPlayback();cobraRequestPlayerOrientation(android.content.pm.ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,"pip-enter");}
    else {if(!mCobraPlaybackPolicy.started&&mCobraPlaybackPolicy.pipOwned)cobraHaltHiddenPlayback();cobraApplyPlayerRotation("pip-exit");}''')
 s=edit(s,'configureCobraPip','cobraPipParams(autoEnter && mMultiOverlay == null)','cobraPipParams(autoEnter && mMultiOverlay == null && cobraWantsFullscreenPip())')
 s=edit(s,'cobraPipParams','    if(Build.VERSION.SDK_INT>=31){builder.setAutoEnterEnabled(autoEnter);',
'''    if(mPlayerTexture!=null){android.graphics.Rect source=new android.graphics.Rect();if(mPlayerTexture.getGlobalVisibleRect(source)&&!source.isEmpty())builder.setSourceRectHint(source);}
    if(Build.VERSION.SDK_INT>=31){builder.setAutoEnterEnabled(autoEnter);''')
 s=edit(s,'enterCobraPictureInPicture','    if(!hasCobraVideo())return;','    if(!cobraWantsFullscreenPip())return;')
 s=edit(s,'enterCobraPictureInPicture','{pauseCobraForBackground();cobraRestoreAfterPipFailure();}}','{pauseCobraForBackground();cobraRestoreAfterPipFailure();}else mCobraPlaybackPolicy.pipChanged(true);}')
 s=edit(s,'enterCobraPictureInPicture','catch(IllegalStateException|IllegalArgumentException error)','catch(IllegalStateException|IllegalArgumentException|SecurityException error)')
 s=method(s,'startCobraPlayer','''  private void startCobraPlayer(ExoPlayer player){
    if(player==null||!isCobraAsyncAlive())return;
    if(mBackgroundStopped&&!cobraOwnsMiniSession(player)){
      if(!mCobraPlaybackPolicy.dismissed)mBackgroundResumePlayers.put(player,Boolean.TRUE);
      player.pause();
    }else player.play();
  }''')
 s=method(s,'cobraBeginMiniBackgroundPlayback','''  private boolean cobraBeginMiniBackgroundPlayback(){return cobraStartOwnedMiniPlayback();}''')
 s=method(s,'cobraEndMiniBackgroundPlayback','''  private void cobraEndMiniBackgroundPlayback(){
    InfinityExtendedBackgroundService.MiniPlaybackOwner owner=mCobraMiniOwner;
    mCobraMiniOwner=null;mCobraMiniBackgroundPlayer=null;mCobraMiniBackgroundActive=false;
    if(owner!=null)InfinityExtendedBackgroundService.stopMiniPlayback(this,owner);
  }''')
 s=edit(s,'pauseCobraForBackground','if(!mCobraMiniBackgroundActive)rememberAndPauseCobraPlayer(mCobraPreviewPlayer);','if(!cobraOwnsMiniSession(mCobraPreviewPlayer))rememberAndPauseCobraPlayer(mCobraPreviewPlayer);')
 s=edit(s,'promoteCobraPreviewToFullscreen','    mCobraPreviewPlayer=null;mCobraPreviewSessionKey="";','    cobraEndMiniBackgroundPlayback();\n    mCobraPreviewPlayer=null;mCobraPreviewSessionKey="";')
 s=once(s,'    @Override public void onIsPlayingChanged(boolean playing){if(current()){if(player==mPlayer)cobraApplyPlayerRotation("is-playing");cobraUpdatePlaybackLabels();}}',
'''    @Override public void onIsPlayingChanged(boolean playing){if(current()){if(player==mPlayer){cobraApplyPlayerRotation("is-playing");configureCobraPip(cobraPlaybackRequested(player));}cobraUpdatePlaybackLabels();cobraPublishMiniState();}}
    @Override public void onPlayWhenReadyChanged(boolean requested,int reason){if(current()){
      if(!requested&&(!mBackgroundStopped||reason!=Player.PLAY_WHEN_READY_CHANGE_REASON_USER_REQUEST)){mCobraPlaybackPolicy.epoch++;mBackgroundResumePlayers.remove(player);}
      if(player==mPlayer)configureCobraPip(requested);cobraPublishMiniState();
    }}
    @Override public void onPlaybackSuppressionReasonChanged(int reason){if(current())cobraPublishMiniState();}''')
 s=once(s,'      if(player==mPlayer)cobraApplyPlayerRotation("playback-state");','      cobraPublishMiniState();\n      if(player==mPlayer)cobraApplyPlayerRotation("playback-state");')
 s=once(s,'        fallback=true;boolean requested=player.getPlayWhenReady();','        fallback=true;boolean requested=player.getPlayWhenReady();final long retryEpoch=mCobraPlaybackPolicy.epoch;')
 s=once(s,'          if(!current()||"primary".equals(vitals.preferences.fallback))return;',
'          if(!current()||"primary".equals(vitals.preferences.fallback)||!mCobraPlaybackPolicy.acceptsRetry(retryEpoch,requested&&player.getPlayWhenReady(),cobraPlaybackMayRun(player)))return;')
 s=once(s,'          if(!mEpisodeQueue.isEmpty()&&mEpisodeQueueIndex+1<mEpisodeQueue.size())mMain.postDelayed(()->{',
'          final long episodeEpoch=mCobraPlaybackPolicy.epoch;\n          if(!mEpisodeQueue.isEmpty()&&mEpisodeQueueIndex+1<mEpisodeQueue.size())mMain.postDelayed(()->{')
 s=once(s,'            if(current()&&player==mPlayer&&player.getPlaybackState()==Player.STATE_ENDED)playNextEpisode();',
'            if(current()&&player==mPlayer&&player.getPlaybackState()==Player.STATE_ENDED&&mCobraPlaybackPolicy.acceptsRetry(episodeEpoch,player.getPlayWhenReady(),cobraPlaybackMayRun(player)))playNextEpisode();')
 # The existing Media3 player owns focus; no second AudioManager competes with it.
 s=edit(s,'buildPlayer','.setContentType(C.AUDIO_CONTENT_TYPE_MOVIE).build(),false);','.setContentType(C.AUDIO_CONTENT_TYPE_MOVIE).build(),audible);')
 s=once(s,'    for(int i=0;i<mMultiPlayers.length;i++)if(mMultiPlayers[i]!=null)mMultiPlayers[i].setVolume(i==index?1f:0f);',
'''    // Relinquish old tile focus before the selected tile claims it.
    for(int i=0;i<mMultiPlayers.length;i++)if(mMultiPlayers[i]!=null&&i!=index){mMultiPlayers[i].setAudioAttributes(mMultiPlayers[i].getAudioAttributes(),false);mMultiPlayers[i].setVolume(0f);}
    if(mMultiPlayers[index]!=null){mMultiPlayers[index].setAudioAttributes(mMultiPlayers[index].getAudioAttributes(),true);mMultiPlayers[index].setVolume(1f);}''')
 s=once(s,'    if(session!=null){cobraAttachVideo(session,mPlayerTexture);session.setVolume(1f);}else startSinglePlayer(channel.primaryUrl);',
'    if(session!=null){cobraAttachVideo(session,mPlayerTexture);session.setAudioAttributes(session.getAudioAttributes(),true);session.setVolume(1f);}else startSinglePlayer(channel.primaryUrl);')
 # Bind the actual preview button, and preserve that anchor through nested sheets.
 s=once(s,'CobraIconButton more=cobraIcon("more","Channel actions",true,v->{if(mGuidePreviewChannel!=null)showCobraChannelActions(mGuidePreviewChannel);});',
'CobraIconButton more=cobraIcon("more","Channel actions",true,v->{if(mGuidePreviewChannel!=null){mCobraNextSheetAnchor=v;showCobraChannelActions(mGuidePreviewChannel);}});more.setTag("cobra_preview_options_anchor");')
 s=once(s,'host.setOnLongClickListener(v->{cobraShowPreviewActions();return true;});','host.setOnLongClickListener(v->{mCobraNextSheetAnchor=v;cobraShowPreviewActions();return true;});')
 s=once(s,'b.caption(labels[i]);tools.addView(b,new LinearLayout.LayoutParams(0,dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.34",52)),1));',
'b.caption(labels[i]);if(action==1)b.setTag("cobra_player_aspect_anchor");if(action==3)b.setTag("cobra_player_options_anchor");tools.addView(b,new LinearLayout.LayoutParams(0,dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.34",52)),1));')
 s=edit(s,'cobraSheetRow','    row.setOnClickListener(v->{closeCobraActionSheet();action.run();});',
'''    row.setOnClickListener(v->{View source=mCobraSheetAnchor;closeCobraActionSheet();mCobraNextSheetAnchor=source;try{action.run();}finally{mCobraNextSheetAnchor=null;}});''')
 s=edit(s,'cobraOpenSheet','    closeCobraActionSheet();',
'''    View sheetAnchor=cobraResolveSheetAnchor(kind),sheetPane=cobraResolveSheetPane(sheetAnchor);
    closeCobraActionSheet();mCobraSheetAnchor=sheetAnchor;mCobraSheetPane=sheetPane;mCobraSheetHeightLimit=Integer.MAX_VALUE;''')
 s=edit(s,'cobraOpenSheet','    panel.addView(header,new LinearLayout.LayoutParams(-1,-2));','    LinearLayout body=new LinearLayout(this);body.setOrientation(LinearLayout.VERTICAL);body.addView(header,new LinearLayout.LayoutParams(-1,-2));')
 s=edit(s,'cobraOpenSheet','super.onMeasure(w,View.MeasureSpec.makeMeasureSpec(limit,View.MeasureSpec.AT_MOST));','super.onMeasure(w,View.MeasureSpec.makeMeasureSpec(Math.min(limit,mCobraSheetHeightLimit),View.MeasureSpec.AT_MOST));')
 s=edit(s,'cobraOpenSheet','scroll.addView(items,new ScrollView.LayoutParams(-1,-2));','body.addView(items,new LinearLayout.LayoutParams(-1,-2));scroll.addView(body,new ScrollView.LayoutParams(-1,-2));')
 s=edit(s,'cobraOpenSheet','    close.requestFocus();vtheme().tree(panel,"sheet."+kind);return items;',
'''    panel.setTag("cobra_sheet_panel");mCobraSheetPanel=panel;
    if(sheetAnchor!=null&&sheetPane!=null){
      // Keep invisible until measured, so the old screen-centered location never flashes.
      panel.animate().cancel();panel.setAlpha(0f);panel.setTranslationY(0f);
      mCobraSheetLayoutListener=()->cobraPositionAnchoredSheet(scrim,panel,sheetAnchor,sheetPane);
      scrim.getViewTreeObserver().addOnGlobalLayoutListener(mCobraSheetLayoutListener);
    }
    close.requestFocus();vtheme().tree(panel,"sheet."+kind);return items;''')
 s=edit(s,'closeCobraActionSheet','    android.view.ViewParent parent=mCobraActionSheet.getParent();',
'''    if(mCobraSheetLayoutListener!=null&&mCobraActionSheet.getViewTreeObserver().isAlive())mCobraActionSheet.getViewTreeObserver().removeOnGlobalLayoutListener(mCobraSheetLayoutListener);
    mCobraSheetLayoutListener=null;mCobraSheetAnchor=null;mCobraSheetPane=null;mCobraSheetPanel=null;mCobraSheetHeightLimit=Integer.MAX_VALUE;
    android.view.ViewParent parent=mCobraActionSheet.getParent();''')
 s=once(s,'root.put("background_stopped",mBackgroundStopped);root.put("picture_in_picture",mInPictureInPicture);',
'root.put("background_stopped",mBackgroundStopped);root.put("picture_in_picture",mInPictureInPicture);root.put("pip_session_owned",mCobraPlaybackPolicy.pipOwned);root.put("activity_started",mCobraPlaybackPolicy.started);root.put("mini_audio_owned",cobraOwnsMiniSession(mCobraPreviewPlayer));root.put("mini_media_service",InfinityExtendedBackgroundService.isMiniPlaybackRunning());root.put("playback_epoch",mCobraPlaybackPolicy.epoch);')
 return append(s,'activity-helpers.java.inc')

def service(s):
 s=method(s,'isMiniPlaybackRunning','  public static boolean isMiniPlaybackRunning(){return sMiniPlayback||sMiniGrant.requested;}')
 s=method(s,'startMiniPlayback','''  public static boolean startMiniPlayback(Context context,String title,MiniPlaybackOwner owner){
    if(owner==null||!owner.available()||!notificationsAllowed(context))return false;
    MiniPlaybackOwner previous=sMiniOwner.get();if(previous!=null&&previous!=owner)revokeMini(true);
    sMiniOwner=new java.lang.ref.WeakReference<>(owner);sMiniTitle=title==null||title.trim().isEmpty()?"Cobra Live":title.trim();
    long generation=sMiniGrant.grant();
    if(request(context,new Intent(context,InfinityExtendedBackgroundService.class).setAction(ACTION_MINI_START).putExtra(EXTRA_GENERATION,generation)))return true;
    revokeMini(false);return false;
  }''')
 s=method(s,'stopMiniPlayback','''  public static void stopMiniPlayback(Context context){
    // Invalidate pending starts synchronously, even before onStartCommand runs.
    revokeMini(false);InfinityExtendedBackgroundService service=sInstance.get();
    if(service!=null)service.reconcileMiniAndContinuity();
  }''')
 s=edit(s,'setEnabled','if (!sMiniPlayback) stopForExit(activity);','if (!sMiniGrant.requested) stopForExit(activity);')
 s=edit(s,'sync','    if (sMiniPlayback) return;','    if (sMiniGrant.requested) return;')
 s=edit(s,'stopForExit','    sMiniPlayback = false;','    revokeMini(true);')
 s=method(s,'onStartCommand','''  @Override public int onStartCommand(Intent intent,int flags,int startId){
    mTerminating=false;String action=intent==null?"":intent.getAction();
    if(ACTION_DISABLE.equals(action))preferences(this).edit().putBoolean(KEY_ENABLED,false).apply();
    if(ACTION_MINI_COMMAND.equals(action))dispatchMiniCommand(intent.getLongExtra(EXTRA_GENERATION,-1L),intent.getIntExtra(EXTRA_COMMAND,0));
    // START/SYNC never grants playback. Only the live Activity can grant the existing session.
    // Reconcile current ownership, not a possibly stale start/stop intent payload.
    return reconcileMiniAndContinuity();
  }''')
 s=method(s,'ensureMediaSession','''  private void ensureMediaSession(){
    MiniPlaybackOwner owner=sMiniOwner.get();if(owner==null||!owner.available())throw new IllegalStateException("No live mini-player owner");
    final long generation=sMiniGrant.generation;
    if(mMediaSession==null||mMediaGeneration!=generation){
      releaseMediaSession();mMediaGeneration=generation;
      mMediaSession=new android.media.session.MediaSession(this,"InfinityCobraMini");
      mMediaSession.setFlags(android.media.session.MediaSession.FLAG_HANDLES_MEDIA_BUTTONS|android.media.session.MediaSession.FLAG_HANDLES_TRANSPORT_CONTROLS);
      mMediaSession.setCallback(cobraMiniMediaCallback(generation),new android.os.Handler(android.os.Looper.getMainLooper()));
      mMediaSession.setSessionActivity(miniOpenPendingIntent());
    }
    mMediaSession.setMetadata(new android.media.MediaMetadata.Builder().putString(android.media.MediaMetadata.METADATA_KEY_TITLE,mMiniTitle).putString(android.media.MediaMetadata.METADATA_KEY_ARTIST,"Infinity • Cobra").build());
    mMediaSession.setPlaybackState(cobraMiniPlaybackState(owner));
    mMediaSession.setActive(true);
  }''')
 s=method(s,'buildMiniPlaybackNotification','''  private Notification buildMiniPlaybackNotification(){
    ensureMediaSession();int state=sMiniOwner.get().state();
    boolean playing=state==android.media.session.PlaybackState.STATE_PLAYING||state==android.media.session.PlaybackState.STATE_BUFFERING;
    Notification.Builder builder=builder().setSmallIcon(android.R.drawable.ic_media_play)
        .setContentTitle(mMiniTitle).setContentText("Infinity • Cobra mini-player • "+(state==android.media.session.PlaybackState.STATE_BUFFERING?"Buffering":playing?"Playing":"Paused"))
        .setContentIntent(miniOpenPendingIntent()).setDeleteIntent(miniCommandPendingIntent(COMMAND_STOP))
        .setCategory(Notification.CATEGORY_TRANSPORT).setOngoing(playing).setOnlyAlertOnce(true).setShowWhen(false)
        .addAction(new Notification.Action.Builder(playing?android.R.drawable.ic_media_pause:android.R.drawable.ic_media_play,playing?"Pause":"Play",miniCommandPendingIntent(playing?COMMAND_PAUSE:COMMAND_PLAY)).build())
        .addAction(new Notification.Action.Builder(android.R.drawable.ic_menu_close_clear_cancel,"Stop",miniCommandPendingIntent(COMMAND_STOP)).build())
        .setStyle(new Notification.MediaStyle().setMediaSession(mMediaSession.getSessionToken()).setShowActionsInCompactView(0,1));
    if(Build.VERSION.SDK_INT>=31)builder.setForegroundServiceBehavior(Notification.FOREGROUND_SERVICE_IMMEDIATE);
    return builder.build();
  }''')
 s=edit(s,'endSession','    sRunning = false;sMiniPlayback = false;releaseMediaSession();','    mTerminating=true;sRunning=false;revokeMini(true);releaseMediaSession();')
 s=method(s,'onDestroy','''  @Override public void onDestroy(){
    mTerminating=true;if(sInstance.get()==this){sInstance=new java.lang.ref.WeakReference<>(null);sRunning=false;revokeMini(true);}
    releaseMediaSession();
    super.onDestroy();
  }''')
 return append(s,'service-helpers.java.inc')

def apply(source,out):
 pending={};proof={}
 for name,expected in PRE.items():
  p=source/SOURCE/name;before=p.read_bytes()
  if digest(before)!=expected:raise ValueError('Not exact 2103163: '+name+' '+digest(before))
  after=(activity if name.startswith('InfinityLive') else service)(before.decode()).encode()
  pending[p]=(before,after);proof[str(SOURCE/name)]={'before':digest(before),'after':digest(after)}
 out.mkdir(parents=True,exist_ok=True)
 for p,(before,after) in pending.items():(out/'source-before').mkdir(exist_ok=True);(out/'source-before'/p.name).write_bytes(before)
 try:
  for p,(before,after) in pending.items():p.write_bytes(after)
 except Exception:
  for p,(before,after) in pending.items():p.write_bytes(before)
  raise
 (out/'patch.json').write_text(json.dumps({'base_commit':'8f2c9c7b0fdd7bfcaa0d903f8df997a139c23261','files':proof,'native_changed':False,'physical_device_verified':False},indent=2)+'\n')
 return proof
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();apply(a.source,a.out)
