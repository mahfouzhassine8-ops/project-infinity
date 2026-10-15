  private static final String COBRA_AUTO_RECOVERY="cobra_auto_surface_recovery";
  private boolean mCobraHealthForeground;
  private TextView mCobraHealthSummary;
  private final Runnable mCobraHealthTick=new Runnable(){public void run(){
    if(!mCobraHealthForeground||!isCobraAsyncAlive())return;
    cobraObserveSessions();cobraRefreshHealthSummary();
    if(!mCobraPlayerBindings.isEmpty()||"health-center".equals(mCobraSheetKind))mMain.postDelayed(this,1000L);
  }};
  private void cobraStartHealthTicker(){
    mMain.removeCallbacks(mCobraHealthTick);
    if(mCobraHealthForeground&&isCobraAsyncAlive())mMain.postDelayed(mCobraHealthTick,1000L);
  }
  private void cobraSuspendHealth(){
    mCobraHealthForeground=false;mMain.removeCallbacks(mCobraHealthTick);
    for(CobraPlayerBinding binding:mCobraPlayerBindings.values())binding.vitals.recovery.suspend();
  }
  private boolean cobraLiveChannel(Channel channel){
    if(channel==null||channel.id==null||channel.id.isEmpty())return false;
    for(Channel known:mChannels)if(channel.id.equals(known.id))return true;
    return false;
  }
  private String cobraPreferenceKey(Channel channel){return CobraPreferencePolicy.key(mFeatures.activeProfileId(),sourceIdForChannel(channel),channel.id);}

  private static final class CobraChannelPreferences {
    int aspect=-1;float x=1f,y=1f;String audio="",subtitles="inherit",fallback="inherit",recovery="inherit";
    static CobraChannelPreferences parse(String json){
      CobraChannelPreferences p=new CobraChannelPreferences();
      if(json==null||json.length()>4096)return p;
      try {JSONObject o=new JSONObject(json);if(o.optInt("schema",0)!=1)return p;
        p.aspect=CobraPreferencePolicy.aspect(o.optInt("aspect",-1));p.x=CobraPreferencePolicy.scale((float)o.optDouble("x",1));p.y=CobraPreferencePolicy.scale((float)o.optDouble("y",1));
        p.audio=CobraPreferencePolicy.language(o.optString("audio",""));
        String text=o.optString("subtitles","inherit");p.subtitles="off".equals(text)||"auto".equals(text)?text:CobraPreferencePolicy.language(text);if(p.subtitles.isEmpty())p.subtitles="inherit";
        p.fallback=CobraPreferencePolicy.choice(o.optString("fallback","inherit"),"allow","primary");
        p.recovery=CobraPreferencePolicy.choice(o.optString("recovery","inherit"),"on","off");
      }catch(Exception ignored){}return p;
    }
    String json(){try{return new JSONObject().put("schema",1).put("aspect",CobraPreferencePolicy.aspect(aspect)).put("x",CobraPreferencePolicy.scale(x)).put("y",CobraPreferencePolicy.scale(y)).put("audio",CobraPreferencePolicy.language(audio)).put("subtitles",subtitles).put("fallback",fallback).put("recovery",recovery).toString();}catch(Exception e){throw new IllegalArgumentException("Invalid channel preferences",e);}}
  }
  private CobraChannelPreferences cobraReadPreferences(String key){
    try{return CobraChannelPreferences.parse(mPrefs.getString(key,""));}
    catch(ClassCastException invalid){return new CobraChannelPreferences();}
  }
  private CobraChannelPreferences cobraPreferences(Channel channel){return channel==null?new CobraChannelPreferences():cobraReadPreferences(cobraPreferenceKey(channel));}
  private boolean cobraSavePreferences(Channel channel,String expectedKey,CobraChannelPreferences prefs,boolean reset){
    if(!isCobraAsyncAlive()||!cobraLiveChannel(channel)||!expectedKey.equals(cobraPreferenceKey(channel))){toast("Channel or profile changed. Reopen its playback settings.");return false;}
    if(!reset&&!mPrefs.contains(expectedKey)){
      int count=0;for(String key:mPrefs.getAll().keySet())if(key.startsWith("cobra.channel.v1."))count++;
      if(count>=CobraPreferencePolicy.MAX_SAVED){toast("Saved channel limit reached. Reset unused channel settings first.");return false;}
    }
    SharedPreferences.Editor edit=mPrefs.edit();if(reset)edit.remove(expectedKey);else edit.putString(expectedKey,prefs.json());edit.apply();
    for(CobraPlayerBinding b:new ArrayList<>(mCobraPlayerBindings.values()))if(b.current()&&expectedKey.equals(b.vitals.preferenceKey)){
      CobraChannelPreferences old=b.vitals.preferences;
      b.vitals.preferences=reset?new CobraChannelPreferences():CobraChannelPreferences.parse(prefs.json());
      b.vitals.recovery.suspend();
      if(!old.audio.equals(b.vitals.preferences.audio)||!old.subtitles.equals(b.vitals.preferences.subtitles))cobraApplyChannelTracks(b);
      cobraFitBinding(b);
    }
    if(mPlaying!=null&&expectedKey.equals(cobraPreferenceKey(mPlaying))){mAspectMode=cobraChannelAspect(mPlaying);applyCobraAspectTransform();}
    return true;
  }
  private int cobraChannelAspect(Channel channel){
    if(cobraLiveChannel(channel)){CobraChannelPreferences p=cobraPreferences(channel);if(p.aspect>=0)return p.aspect;}
    int mode=mPrefs.getInt(COBRA_ASPECT_MODE,0);return mode>=0&&mode<=11?mode:0;
  }
  private void cobraApplyChannelTracks(CobraPlayerBinding b){
    if(!b.current()||!b.vitals.live)return;
    CobraChannelPreferences p=b.vitals.preferences;
    androidx.media3.common.TrackSelectionParameters base=b.vitals.defaultTracks;
    androidx.media3.common.TrackSelectionParameters.Builder next=b.player.getTrackSelectionParameters().buildUpon();
    next.clearOverridesOfType(C.TRACK_TYPE_AUDIO).clearOverridesOfType(C.TRACK_TYPE_TEXT);
    next.setPreferredAudioLanguages(p.audio.isEmpty()?base.preferredAudioLanguages.toArray(new String[0]):new String[]{p.audio});
    if("inherit".equals(p.subtitles))next.setPreferredTextLanguages(base.preferredTextLanguages.toArray(new String[0])).setSelectUndeterminedTextLanguage(base.selectUndeterminedTextLanguage).setTrackTypeDisabled(C.TRACK_TYPE_TEXT,base.disabledTrackTypes.contains(C.TRACK_TYPE_TEXT));
    else next.setPreferredTextLanguages("off".equals(p.subtitles)||"auto".equals(p.subtitles)?new String[0]:new String[]{p.subtitles}).setSelectUndeterminedTextLanguage("auto".equals(p.subtitles)).setTrackTypeDisabled(C.TRACK_TYPE_TEXT,"off".equals(p.subtitles));
    b.player.setTrackSelectionParameters(next.build());
    if("off".equals(p.subtitles)&&b.captions!=null)b.captions.cues(Collections.emptyList());
  }

  private final class CobraSessionVitals implements androidx.media3.exoplayer.analytics.AnalyticsListener {
    final long createdAt=android.os.SystemClock.elapsedRealtime();final boolean live;
    final String preferenceKey;final androidx.media3.common.TrackSelectionParameters defaultTracks;
    CobraChannelPreferences preferences;final CobraRecoveryPolicy recovery=new CobraRecoveryPolicy();
    androidx.media3.exoplayer.DecoderCounters videoCounters,audioCounters;
    long observedAt=-1,firstFrameAt=-1,frameCount=-1,droppedFrames=-1,audioCount=-1,bufferMs,bufferSince=-1,lastLoadMs=-1,lastLoadBytes=-1,lastErrorAt;
    int loadErrors,bufferRetries;String lastError="",lastRecovery="not_requested",decoder="Not reported";
    boolean exhaustedReported;
    CobraSessionVitals(ExoPlayer player,Channel channel){
      live=cobraLiveChannel(channel);preferenceKey=live?cobraPreferenceKey(channel):"";
      preferences=live?cobraReadPreferences(preferenceKey):new CobraChannelPreferences();defaultTracks=player.getTrackSelectionParameters();
    }
    @Override public void onLoadCompleted(androidx.media3.exoplayer.analytics.AnalyticsListener.EventTime event,androidx.media3.exoplayer.source.LoadEventInfo info,androidx.media3.exoplayer.source.MediaLoadData data){lastLoadMs=info.loadDurationMs;lastLoadBytes=info.bytesLoaded;}
    @Override public void onLoadError(androidx.media3.exoplayer.analytics.AnalyticsListener.EventTime event,androidx.media3.exoplayer.source.LoadEventInfo info,androidx.media3.exoplayer.source.MediaLoadData data,java.io.IOException error,boolean canceled){if(!canceled){loadErrors++;lastError=error.getClass().getSimpleName();lastErrorAt=System.currentTimeMillis();}}
    @Override public void onVideoDecoderInitialized(androidx.media3.exoplayer.analytics.AnalyticsListener.EventTime event,String name,long time,long duration){decoder=name==null?"Not reported":name;recovery.suspend();}
  }
  private boolean cobraRecoveryEnabled(CobraPlayerBinding b){
    if(!b.vitals.live||"off".equals(b.vitals.preferences.recovery))return false;
    return "on".equals(b.vitals.preferences.recovery)||mPrefs.getBoolean(COBRA_AUTO_RECOVERY,true);
  }
  private void cobraObserveSessions(){
    long now=android.os.SystemClock.elapsedRealtime();
    for(CobraPlayerBinding b:new ArrayList<>(mCobraPlayerBindings.values()))if(b.current()){
      try{
        CobraSessionVitals s=b.vitals;ExoPlayer p=b.player;
        androidx.media3.exoplayer.DecoderCounters v=p.getVideoDecoderCounters(),a=p.getAudioDecoderCounters();
        if(v!=s.videoCounters||a!=s.audioCounters){s.recovery.suspend();s.videoCounters=v;s.audioCounters=a;}
        if(v!=null){v.ensureUpdated();s.frameCount=v.renderedOutputBufferCount;s.droppedFrames=v.droppedBufferCount;}else{s.frameCount=-1;s.droppedFrames=-1;}
        if(a!=null){a.ensureUpdated();s.audioCount=a.renderedOutputBufferCount;}else s.audioCount=-1;
        boolean buffering=p.getPlaybackState()==Player.STATE_BUFFERING&&p.getPlayWhenReady();
        if(buffering&&s.bufferSince<0)s.bufferSince=now;
        if(!buffering&&s.bufferSince>=0){s.bufferMs+=Math.max(0,now-s.bufferSince);s.bufferSince=-1;}
        TextureView texture=b.texture;long stamp=-1;
        boolean visible=texture!=null&&texture.isAttachedToWindow()&&texture.isShown()&&texture.getAlpha()>.9f&&texture.getWidth()>32&&texture.getHeight()>24&&texture.isAvailable();
        if(visible&&texture.getSurfaceTexture()!=null){try{stamp=texture.getSurfaceTexture().getTimestamp();}catch(RuntimeException unavailable){stamp=-1;}}
        Format format=p.getVideoFormat();
        boolean eligible=cobraRecoveryEnabled(b)&&mCobraHealthForeground&&!mBackgroundStopped&&!isCobraInPictureInPicture()&&getWindow().getDecorView().hasWindowFocus()
          &&mCobraActionSheet==null&&mCobraPlayerDrawer==null&&getWindow().getDecorView().findViewWithTag("cobra_experience_drawer")==null
          &&visible&&s.live&&s.preferenceKey.equals(cobraPreferenceKey(b.channel))&&b.error.isEmpty()&&p.getPlayerError()==null&&p.getPlayWhenReady()&&p.isPlaying()&&p.getPlaybackState()==Player.STATE_READY
          &&p.getPlaybackSuppressionReason()==Player.PLAYBACK_SUPPRESSION_REASON_NONE&&format!=null&&format.width>0&&format.height>0&&(format.frameRate<=0||format.frameRate>=1f)&&p.getAudioFormat()!=null
          &&!p.getTrackSelectionParameters().disabledTrackTypes.contains(C.TRACK_TYPE_VIDEO);
        s.observedAt=now;
        if(s.recovery.observe(now,eligible,p.getCurrentPosition(),s.frameCount,s.audioCount,stamp))cobraReattachObservedSurface(b);
        if("automatic_limit_reached".equals(s.recovery.state)&&!s.exhaustedReported){s.exhaustedReported=true;InfinityCobraDiagnostics.record(this,"recovery","automatic-limit","Two attempts used; manual diagnosis required");}
      }catch(RuntimeException failure){b.vitals.recovery.suspend();b.vitals.lastRecovery="observation_unavailable";}
    }
  }
  private void cobraReattachObservedSurface(CobraPlayerBinding binding){
    // Re-check identity and lifecycle at the action boundary. Never recreate a player or change its media.
    if(!binding.current()||!cobraRecoveryEnabled(binding)||!mCobraHealthForeground||mBackgroundStopped||isCobraInPictureInPicture())return;
    TextureView texture=binding.texture;ExoPlayer player=binding.player;
    if(!binding.vitals.preferenceKey.equals(cobraPreferenceKey(binding.channel))||!binding.error.isEmpty())return;
    if(texture==null||texture.getWidth()<=32||texture.getHeight()<=24||!texture.isAttachedToWindow()||!texture.isAvailable()||!texture.isShown()||player.getPlaybackState()!=Player.STATE_READY||!player.getPlayWhenReady()||!player.isPlaying()||player.getPlayerError()!=null)return;
    binding.vitals.lastRecovery="reattach_requested";
    try{
      player.clearVideoTextureView(texture);player.setVideoTextureView(texture);cobraFitBinding(binding);
      InfinityCobraDiagnostics.record(this,"recovery","surface-reattach","channel_hash="+InfinityCobraFeatureRuntime.hashId(binding.channel.id)+"; attempt="+binding.vitals.recovery.attempts+"; reason="+binding.vitals.recovery.state);
    }catch(RuntimeException failure){binding.vitals.lastRecovery="reattach_failed";InfinityCobraDiagnostics.failure(this,"surface-reattach",failure);}
  }
  private boolean cobraPermitBufferRetry(ExoPlayer player){
    CobraPlayerBinding b=mCobraPlayerBindings.get(player);if(b==null||!b.current())return false;
    if(b.vitals.bufferRetries>=2){b.vitals.lastRecovery="buffer_retry_limit";return false;}
    b.vitals.bufferRetries++;b.vitals.recovery.suspend();
    InfinityCobraDiagnostics.record(this,"recovery","buffer-retry","Attempt "+b.vitals.bufferRetries+" of 2 for this player session");return true;
  }
  private String cobraAge(long time,long now){return time<=0?"Not observed":Math.max(0,(now-time)/1000L)+" s ago";}
  private void cobraAddSessionHealth(JSONObject root)throws Exception{
    JSONArray sessions=new JSONArray();long now=android.os.SystemClock.elapsedRealtime();
    for(CobraPlayerBinding b:mCobraPlayerBindings.values()){
      CobraSessionVitals s=b.vitals;JSONObject row=new JSONObject();row.put("channel_hash",InfinityCobraFeatureRuntime.hashId(b.channel.id));
      row.put("role",b.player==mPlayer?"fullscreen":b.player==mCobraPreviewPlayer?"preview":"multiview_or_transfer");
      row.put("observation_age_ms",s.observedAt<0?-1:Math.max(0,now-s.observedAt));row.put("observed_frames",s.frameCount);row.put("dropped_frames",s.droppedFrames);row.put("observed_audio_buffers",s.audioCount);
      row.put("first_frame_ms",s.firstFrameAt<0?-1:Math.max(0,s.firstFrameAt-s.createdAt));row.put("buffer_ms",s.bufferMs+(s.bufferSince<0?0:Math.max(0,now-s.bufferSince)));
      row.put("last_media_load_ms",s.lastLoadMs);row.put("last_media_load_bytes",s.lastLoadBytes);row.put("media_load_errors",s.loadErrors);
      row.put("last_error_code",s.lastError);row.put("last_error_at_ms",s.lastErrorAt);row.put("recovery_enabled",cobraRecoveryEnabled(b));
      row.put("recovery_state",s.recovery.state);row.put("surface_attempts",s.recovery.attempts);row.put("buffer_retries",s.bufferRetries);row.put("last_recovery_action",s.lastRecovery);
      row.put("channel_preference_scope",s.live?"profile_and_source_and_channel":"not_live_channel");sessions.put(row);
    }
    root.put("session_health",sessions);root.put("surface_recovery_limit",2);root.put("health_observation","decoder counters and surface timestamps; not proof of correct visible video");
  }
