// @replace buildPlayer
  private ExoPlayer buildPlayer(TextureView texture, Channel channel, boolean audible) {
    DefaultHttpDataSource.Factory http=new DefaultHttpDataSource.Factory()
        .setAllowCrossProtocolRedirects(true).setConnectTimeoutMs(15000).setReadTimeoutMs(30000)
        .setUserAgent("Infinity Cobra/3.0");
    if(channel.headers!=null&&!channel.headers.isEmpty())http.setDefaultRequestProperties(channel.headers);
    DefaultDataSource.Factory data=new DefaultDataSource.Factory(this,http);
    DefaultRenderersFactory renderers=new DefaultRenderersFactory(this).setEnableDecoderFallback(true);
    boolean multi=mCobraCreatingMulti;
    // Bound *compressed* buffering as well as time; four 180-second buffers were not a safe default.
    DefaultLoadControl control=new DefaultLoadControl.Builder()
        .setBufferDurationsMs(multi?6000:10000,multi?30000:60000,1500,3000)
        .setTargetBufferBytes((multi?12:32)*1024*1024).setPrioritizeTimeOverSizeThresholds(false).build();
    ExoPlayer player=new ExoPlayer.Builder(this,renderers).setMediaSourceFactory(new DefaultMediaSourceFactory(data))
        .setLoadControl(control).build();
    player.setAudioAttributes(new AudioAttributes.Builder().setUsage(C.USAGE_MEDIA)
        .setContentType(C.AUDIO_CONTENT_TYPE_MOVIE).build(),false);
    player.setHandleAudioBecomingNoisy(true);player.setVolume(audible?1f:0f);
    CobraPlayerBinding binding=new CobraPlayerBinding(player,channel);
    mCobraPlayerBindings.put(player,binding);player.addListener(binding);
    cobraAttachVideo(player,texture);
    return player;
  }

// @replace startCobraPreview
  private void startCobraPreview(Channel channel) {
    if(channel==null||mCobraPreviewTexture==null||!isCobraAsyncAlive())return;
    if(mCobraPreviewPlayer!=null&&cobraChannelKey(channel).equals(mCobraPreviewSessionKey)) {
      updateCobraPreviewPlayPause();return;
    }
    stopCobraPreviewPlayerOnly();
    mCobraPreviewAutoplayAllowed=true;mCobraPreviewTexture.setVisibility(View.VISIBLE);
    try {
      mGuidePreviewChannel=channel;mGuidePreviewKey=cobraChannelKey(channel);
      mCobraPreviewPlayer=buildPlayer(mCobraPreviewTexture,channel,!mCobraPreviewMuted);
      mCobraPreviewSessionKey=cobraChannelKey(channel);
      mCobraPreviewPlayer.setMediaItem(mediaItem(channel.primaryUrl));mCobraPreviewPlayer.prepare();
      startCobraPlayer(mCobraPreviewPlayer);cobraStartPresentationTicker();cobraRequestShortEpg(channel);
    }catch(Exception failure){setCobraPreviewLabel("Preview unavailable");}
    updateCobraPreviewPlayPause();cobraRefreshProgrammeLabels();
  }

// @replace startSinglePlayer
  private void startSinglePlayer(String url) {
    if(!isCobraAsyncAlive()||mPlayerTexture==null||mPlaying==null)return;
    releaseSinglePlayer();
    try {
      mPlayer=buildPlayer(mPlayerTexture,mPlaying,true);
      mPlayer.setMediaItem(mediaItem(url));mPlayer.prepare();startCobraPlayer(mPlayer);
      cobraStartPresentationTicker();cobraRequestShortEpg(mPlaying);
    }catch(Exception error){showError("Playback failed","Could not start this stream. "+error.getClass().getSimpleName());}
    cobraUpdatePlaybackLabels();
  }

// @replace playChannel
  private void playChannel(Channel channel) {
    if(channel==null||!isCobraAsyncAlive())return;
    if(mCobraPreviewPlayer!=null&&cobraChannelKey(channel).equals(mCobraPreviewSessionKey)) {
      promoteCobraPreviewToFullscreen(channel);return;
    }
    // A direct launch may not leave an invisible preview using another decoder/provider connection.
    stopCobraPreviewPlayerOnly();releaseMulti();closePlayer();
    mPlaying=channel;mPlayingIndex=mChannels.indexOf(channel);mTriedFallback=false;
    openPlayerOverlay(channel);startSinglePlayer(channel.primaryUrl);
  }

// @replace promoteCobraPreviewToFullscreen
  private void promoteCobraPreviewToFullscreen(Channel channel) {
    if(channel==null||mCobraPlayerLocked)return;
    if(mPlayer!=null&&mPlaying!=null&&channel.id.equals(mPlaying.id))return;
    ExoPlayer session=cobraChannelKey(channel).equals(mCobraPreviewSessionKey)?mCobraPreviewPlayer:null;
    if(session==null){playChannel(channel);return;}
    mCobraPreviewPlayer=null;mCobraPreviewSessionKey="";
    if(mMultiOverlay!=null)releaseMulti();if(mPlayerOverlay!=null)closePlayer();
    mPlaying=channel;mPlayingIndex=mChannels.indexOf(channel);mTriedFallback=false;
    openPlayerOverlay(channel);mPlayer=session;cobraAttachVideo(session,mPlayerTexture);session.setVolume(1f);
    cobraStartPresentationTicker();cobraUpdatePlaybackLabels();configureCobraPip(true);
    if(mDeviceBridge!=null)mDeviceBridge.onPlaybackChanged("preview-fullscreen");
  }

// @replace closeFullscreenToCobraView
  private void closeFullscreenToCobraView() {
    if(mCobraPlayerLocked){showCobraPlayerUnlockAffordance();return;}
    if(mPlayer==null||mPlaying==null||!mPlayingVodKey.isEmpty()) { closePlayer();showCobraPrimaryView();return; }
    Channel channel=mPlaying;ExoPlayer session=mPlayer;
    closeCobraActionSheet();closeCobraPlayerDrawer();closeCobraMultiPicker(true);clearCobraPlayerLockState(false);
    mPlayer=null;mPlaying=null;mPlayingIndex=-1;
    mMain.removeCallbacks(mHideChrome);mMain.removeCallbacks(mStallWatchdog);
    FrameLayout overlay=mPlayerOverlay;mPlayerOverlay=null;mPlayerTexture=null;mPlayerChrome=null;
    mCobraPlayerProgram=null;mCobraPlayerSchedule=null;mCobraPlayerUpcoming=null;mCobraPlayerProgramProgress=null;
    mGuidePreviewChannel=channel;mGuidePreviewKey=cobraChannelKey(channel);mGuidePreviewArmed=true;
    mCobraPreviewPlayer=session;mCobraPreviewSessionKey=cobraChannelKey(channel);
    // The guide shell and its original TextureView remain mounted behind fullscreen.
    showCobraPrimaryView();
    if(mCobraPreviewTexture!=null)mCobraPreviewTexture.setVisibility(View.VISIBLE);
    cobraAttachVideo(session,mCobraPreviewTexture);session.setVolume(mCobraPreviewMuted?0f:1f);
    if(overlay!=null&&overlay.getParent() instanceof android.view.ViewGroup)
      ((android.view.ViewGroup)overlay.getParent()).removeView(overlay);
    configureCobraPip(false);cobraUpdatePlaybackLabels();cobraStartPresentationTicker();
    if(mDeviceBridge!=null)mDeviceBridge.onPlaybackChanged("fullscreen-preview");
  }

// @replace stopCobraPreviewPlayerOnly
  private void stopCobraPreviewPlayerOnly() {
    ExoPlayer previous=mCobraPreviewPlayer;mCobraPreviewPlayer=null;mCobraPreviewSessionKey="";
    mCobraPreviewGeneration++;cobraDisposePlayer(previous);
    if(mCobraPreviewTexture!=null)mCobraPreviewTexture.setVisibility(View.INVISIBLE);
  }

// @replace stopCobraPreview
  private void stopCobraPreview() {
    stopCobraPreviewPlayerOnly();mCobraPreviewTexture=null;mCobraPreviewHost=null;
    mCobraGuideShell=null;mCobraGuideVideo=null;mCobraGuideAdapter=null;mCobraGuideList=null;
  }

// @replace releaseSinglePlayer
  private void releaseSinglePlayer() {
    ExoPlayer previous=mPlayer;mPlayer=null;cobraDisposePlayer(previous);
  }

// @replace releaseCobraTransferPlayer
  private void releaseCobraTransferPlayer() {
    ExoPlayer previous=mCobraTransferPlayer;mCobraTransferPlayer=null;mCobraTransferKey="";cobraDisposePlayer(previous);
  }

// @replace updateCobraPreviewPlayPause
  private void updateCobraPreviewPlayPause() {
    if(mCobraPreviewHost==null)return;
    View view=mCobraPreviewHost.findViewWithTag("cobra_preview_play_pause");
    boolean wants=mCobraPreviewPlayer!=null&&mCobraPreviewPlayer.getPlayWhenReady();
    if(view instanceof CobraIconButton)((CobraIconButton)view).icon(wants?"pause":"play");
    if(view!=null)view.setContentDescription(wants?"Pause preview":"Play preview");
  }

// @replace updateCobraPlayerPlayPause
  private void updateCobraPlayerPlayPause() {
    if(mPlayerOverlay==null)return;
    View view=mPlayerOverlay.findViewWithTag("cobra_player_play_pause");
    boolean wants=mPlayer!=null&&mPlayer.getPlayWhenReady();
    if(view instanceof CobraIconButton)((CobraIconButton)view).icon(wants?"pause":"play");
    if(view!=null)view.setContentDescription(wants?"Pause":"Play");
  }

// @replace applyCobraAspectTransform
  private void applyCobraAspectTransform() {
    cobraFitVideo(mPlayerTexture,mPlayer,mInPictureInPicture?0:mAspectMode);
  }

// @append
  private final class CobraPlayerBinding implements Player.Listener {
    final ExoPlayer player;final Channel channel;
    TextureView texture;View.OnLayoutChangeListener layoutListener;
    boolean fallback=false,recentMarked=false,closed=false;
    String error="";
    long lastFrameMs=android.os.SystemClock.elapsedRealtime();
    long lastPosition=-1;long positionAt=android.os.SystemClock.elapsedRealtime();
    CobraPlayerBinding(ExoPlayer p,Channel c){player=p;channel=c;}
    boolean current(){return !closed&&isCobraAsyncAlive()&&mCobraPlayerBindings.get(player)==this;}
    @Override public void onVideoSizeChanged(VideoSize size){if(current())cobraFitBinding(this);}
    @Override public void onRenderedFirstFrame(){if(current()){lastFrameMs=android.os.SystemClock.elapsedRealtime();if(!recentMarked){recentMarked=true;markCobraPlaybackReady(channel);}}}
    @Override public void onIsPlayingChanged(boolean playing){if(current())cobraUpdatePlaybackLabels();}
    @Override public void onPlaybackStateChanged(int state) {
      if(!current())return;
      if(state==Player.STATE_READY)error="";
      if(player==mPlayer) {
        configureCobraPip(state!=Player.STATE_IDLE&&state!=Player.STATE_ENDED);
        if(state==Player.STATE_READY) {
          mBufferingSince=0L;mMain.removeCallbacks(mStallWatchdog);
          if(mPendingResumeMs>0){player.seekTo(mPendingResumeMs);mPendingResumeMs=0;}
          mMain.removeCallbacks(mProgressTicker);
          if(!mPlayingVodKey.isEmpty())mMain.postDelayed(mProgressTicker,10000L);
        }else if(state==Player.STATE_BUFFERING&&player.getPlayWhenReady()) {
          if(mBufferingSince==0L)mBufferingSince=System.currentTimeMillis();
          mMain.removeCallbacks(mStallWatchdog);mMain.postDelayed(mStallWatchdog,4000L);
        }else if(state==Player.STATE_ENDED&&!mPlayingVodKey.isEmpty()) {
          saveVodProgress();
          if(!mEpisodeQueue.isEmpty()&&mEpisodeQueueIndex+1<mEpisodeQueue.size())mMain.postDelayed(()->{
            if(current()&&player==mPlayer&&player.getPlaybackState()==Player.STATE_ENDED)playNextEpisode();
          },650L);
        }
        if(mDeviceBridge!=null)mDeviceBridge.onPlaybackChanged("player-state-"+state);
      }
      cobraUpdatePlaybackLabels();cobraStartPresentationTicker();
    }
    @Override public void onPlayerError(PlaybackException failure) {
      if(!current())return;
      error=failure==null?"UNKNOWN":failure.getErrorCodeName();
      // Retry only this failed session and only its configured fallback. Never restart healthy peers.
      if(!fallback&&!channel.fallbackUrl.isEmpty()&&!channel.fallbackUrl.equals(channel.primaryUrl)) {
        fallback=true;boolean requested=player.getPlayWhenReady();
        mMain.postDelayed(()->{
          if(!current())return;
          player.setMediaItem(mediaItem(channel.fallbackUrl));player.prepare();
          if(requested)startCobraPlayer(player);
        },250L);
      }
      cobraUpdatePlaybackLabels();
    }
  }

  private void cobraAttachVideo(ExoPlayer player,TextureView texture) {
    if(player==null||texture==null)return;
    CobraPlayerBinding binding=mCobraPlayerBindings.get(player);if(binding==null)return;
    if(binding.texture==texture)return;
    if(binding.texture!=null){if(binding.layoutListener!=null)binding.texture.removeOnLayoutChangeListener(binding.layoutListener);player.clearVideoTextureView(binding.texture);}
    binding.texture=texture;player.setVideoTextureView(texture);
    binding.layoutListener=(v,l,t,r,b,ol,ot,or,ob)->{if(binding.current()&&binding.texture==texture)cobraFitBinding(binding);};
    texture.addOnLayoutChangeListener(binding.layoutListener);
    texture.post(()->{if(binding.current()&&binding.texture==texture)cobraFitBinding(binding);});
  }

  private void cobraFitBinding(CobraPlayerBinding binding) {
    cobraFitVideo(binding.texture,binding.player,binding.player==mPlayer&&!mInPictureInPicture?mAspectMode:0);
  }

  private void cobraFitVideo(TextureView texture,ExoPlayer player,int mode) {
    if(texture==null||player==null)return;
    VideoSize size=player.getVideoSize();
    float[] scale=CobraLayoutMath.fit(size.width,size.height,size.pixelWidthHeightRatio,
        texture.getWidth(),texture.getHeight(),mode,mPrefs.getFloat(COBRA_CUSTOM_ASPECT_X,1.15f),mPrefs.getFloat(COBRA_CUSTOM_ASPECT_Y,.92f));
    android.graphics.Matrix matrix=new android.graphics.Matrix();
    matrix.setScale(scale[0],scale[1],texture.getWidth()/2f,texture.getHeight()/2f);texture.setTransform(matrix);
  }

  private void cobraDisposePlayer(ExoPlayer player) {
    if(player==null)return;
    CobraPlayerBinding binding=mCobraPlayerBindings.remove(player);
    if(binding!=null){binding.closed=true;player.removeListener(binding);if(binding.texture!=null&&binding.layoutListener!=null)binding.texture.removeOnLayoutChangeListener(binding.layoutListener);}
    mBackgroundResumePlayers.remove(player);
    try{player.clearVideoSurface();}catch(RuntimeException ignored){}
    try{player.release();}catch(RuntimeException ignored){}
  }

  private void cobraStartPresentationTicker() {
    mMain.removeCallbacks(mCobraPresentationTick);
    if(isCobraAsyncAlive())mMain.postDelayed(mCobraPresentationTick,200L);
  }

  private String cobraPlayerState(ExoPlayer player) {
    if(player==null)return "Select a channel";
    CobraPlayerBinding binding=mCobraPlayerBindings.get(player);
    if(binding!=null&&!binding.error.isEmpty())return "Stream unavailable";
    if(player.getPlaybackState()==Player.STATE_BUFFERING)return "Buffering…";
    if(player.getPlaybackState()==Player.STATE_ENDED)return "Ended";
    if(!player.getPlayWhenReady())return "Paused";
    return player.getPlaybackState()==Player.STATE_READY?"LIVE":"Connecting…";
  }

  private void cobraUpdatePlaybackLabels() {
    updateCobraPreviewPlayPause();updateCobraPlayerPlayPause();
    if(mCobraPreviewHost!=null){View badge=mCobraPreviewHost.findViewWithTag("cobra_preview_label");
      if(badge instanceof TextView){((TextView)badge).setText(cobraPlayerState(mCobraPreviewPlayer));badge.setVisibility(mCobraPreviewPlayer!=null&&mCobraPreviewPlayer.isPlaying()?View.GONE:View.VISIBLE);}}
    if(mPlayerOverlay!=null){View badge=mPlayerOverlay.findViewWithTag("player_state");
      if(badge instanceof TextView)((TextView)badge).setText(mPlayingVodKey.isEmpty()?cobraPlayerState(mPlayer):
          mPlayer!=null&&mPlayer.getPlayWhenReady()?"PLAYING":"PAUSED");}
    cobraRefreshProgrammeLabels();
  }
