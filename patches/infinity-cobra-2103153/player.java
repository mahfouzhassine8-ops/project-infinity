// COBRA-APPEND
  private int mCobraSafeLeft,mCobraSafeTop,mCobraSafeRight,mCobraSafeBottom;
  private void applyCobraVideoFit(TextureView texture,ExoPlayer player,int mode){
    if(texture==null||player==null)return;VideoSize size=player.getVideoSize();
    if(size.width<=0||size.height<=0||texture.getWidth()<=0||texture.getHeight()<=0)return;
    float[] scales=CobraCore.scales(texture.getWidth(),texture.getHeight(),size.width,size.height,size.pixelWidthHeightRatio,0,mode,
        mPrefs.getFloat(COBRA_CUSTOM_ASPECT_X,1f),mPrefs.getFloat(COBRA_CUSTOM_ASPECT_Y,1f));
    android.graphics.Matrix matrix=new android.graphics.Matrix();matrix.setScale(scales[0],scales[1],texture.getWidth()/2f,texture.getHeight()/2f);texture.setTransform(matrix);
  }
  private void watchCobraPlayback(final ExoPlayer player,final Channel channel){
    player.addListener(new Player.Listener(){
      boolean fallback=false,reported=false;
      boolean current(){return player==mPlayer||player==mCobraPreviewPlayer||cobraTileFor(player)!=null;}
      void success(){if(reported||!current())return;reported=true;if(findChannel(channel.id)!=null)markCobraPlaybackReady(channel);}
      @Override public void onRenderedFirstFrame(){success();CobraTile tile=cobraTileFor(player);if(tile!=null){tile.error="";tile.notice.setVisibility(View.GONE);}refreshCobraGuideViews();}
      @Override public void onVideoSizeChanged(VideoSize size){
        if(player==mPlayer)applyCobraAspectTransform();if(player==mCobraPreviewPlayer)applyCobraVideoFit(mCobraPreviewTexture,player,0);
        CobraTile tile=cobraTileFor(player);if(tile!=null)applyCobraVideoFit(tile.texture,player,0);
      }
      @Override public void onIsPlayingChanged(boolean playing){if(current())refreshCobraGuideViews();}
      @Override public void onPlaybackStateChanged(int state){
        if(!isCobraAsyncAlive()||!current())return;
        if(player==mCobraPreviewPlayer){setCobraPreviewLabel(state==Player.STATE_BUFFERING?"Buffering…":state==Player.STATE_READY?channel.name:state==Player.STATE_ENDED?"Stream ended":channel.name);updateCobraPreviewPlayPause();}
        if(player==mPlayer){
          configureCobraPip(state!=Player.STATE_IDLE&&state!=Player.STATE_ENDED);
          if(state==Player.STATE_READY){
            mBufferingSince=0;mMain.removeCallbacks(mStallWatchdog);
            if(mPendingResumeMs>0){player.seekTo(mPendingResumeMs);mPendingResumeMs=0;}
            mMain.removeCallbacks(mProgressTicker);if(!mPlayingVodKey.isEmpty())mMain.postDelayed(mProgressTicker,10000);
          }else if(state==Player.STATE_BUFFERING){
            if(mBufferingSince==0)mBufferingSince=System.currentTimeMillis();mMain.removeCallbacks(mStallWatchdog);mMain.postDelayed(mStallWatchdog,4000);
          }else if(state==Player.STATE_ENDED){saveVodProgress();if(!mEpisodeQueue.isEmpty()&&mEpisodeQueueIndex+1<mEpisodeQueue.size())mMain.postDelayed(()->{if(mPlayer==player&&isCobraAsyncAlive())playNextEpisode();},650);}
          updateCobraPlayerInformation();
        }
        if(mDeviceBridge!=null)mDeviceBridge.onPlaybackChanged("cobra-state-"+state);
      }
      @Override public void onPlayerError(PlaybackException failure){
        if(!isCobraAsyncAlive()||!current())return;
        String code=failure==null?"UNKNOWN":failure.getErrorCodeName();
        // Retry only the failed feed, once. Reflow/audio selection never calls prepare().
        if(!fallback&&channel.fallbackUrl!=null&&!channel.fallbackUrl.isEmpty()&&!channel.fallbackUrl.equals(channel.primaryUrl)){
          fallback=true;if(player==mPlayer)mPlaybackRetryCount++;
          player.setMediaItem(mediaItem(channel.fallbackUrl));player.prepare();startCobraPlayer(player);return;
        }
        CobraTile tile=cobraTileFor(player);
        if(tile!=null){tile.error=code;tile.notice.setText((code.contains("DECODER")?"Decoder unavailable":"Stream unavailable")+" • hold for details");tile.notice.setVisibility(View.VISIBLE);}
        else if(player==mCobraPreviewPlayer)setCobraPreviewLabel("Stream unavailable • try another channel");
        else if(player==mPlayer){View state=mPlayerOverlay==null?null:mPlayerOverlay.findViewWithTag("player_state");if(state instanceof TextView)((TextView)state).setText("ERROR");showPlayerError(failure);}
        mFeatures.writeHealth(tile==null?"player":"multiview",sourceIdForChannel(channel),channel.id,"error",code,mPlaybackRetryCount,mCobraTiles.size(),mAudioTile,mRecordingSession.isEmpty()?"idle":"recording","unknown");
      }
    });
  }
  private void layoutCobraPlayerViewport(){
    if(mPlayerOverlay==null||mPlayerTexture==null)return;int w=mPlayerOverlay.getWidth(),h=mPlayerOverlay.getHeight();if(w<=0||h<=0)return;
    FrameLayout.LayoutParams video=new FrameLayout.LayoutParams(-1,-1);
    boolean drawer=mCobraPlayerDrawer!=null||(mCobraMultiPicker!=null&&!mCobraMultiPickerAdding);
    if(drawer){if(h>w)video.height=Math.round(h*.43f);else video.width=Math.round(w*.57f);}
    mPlayerTexture.setScaleX(1f);mPlayerTexture.setScaleY(1f);mPlayerTexture.setTranslationX(0f);mPlayerTexture.setTranslationY(0f);mPlayerTexture.setLayoutParams(video);
    if(mCobraPlayerDrawer!=null){FrameLayout.LayoutParams p=new FrameLayout.LayoutParams(h>w?-1:w-video.width,h>w?h-video.height:-1,h>w?Gravity.BOTTOM:Gravity.RIGHT);mCobraPlayerDrawer.setLayoutParams(p);mCobraPlayerDrawer.bringToFront();}
    if(mPlayerChrome!=null){mPlayerChrome.setPadding(mCobraSafeLeft,mCobraSafeTop,mCobraSafeRight,mCobraSafeBottom);if(drawer||mCobraPlayerLocked||isCobraInPictureInPicture())mPlayerChrome.setVisibility(View.GONE);}
    applyCobraAspectTransform();
  }
  private void updateCobraPlayerInformation(){
    if(mPlayerOverlay==null||mPlaying==null)return;Channel channel=mPlaying;
    ProgramPair pair=findChannel(channel.id)!=null?programFor(channel):null;
    String now=pair==null?(findChannel(channel.id)!=null?cobraGuideMessage(channel):channel.name):pair.now.isEmpty()?cobraGuideMessage(channel):pair.now;
    GuideProgram current=null;for(GuideProgram p:cobraSchedule(channel))if(CobraCore.current(p.start,p.stop,System.currentTimeMillis()))current=p;
    String time=current==null?"":cobraClock(current.start)+" – "+cobraClock(current.stop)+"  ·  "+Math.max(1,(current.stop-System.currentTimeMillis()+59999)/60000)+" min left";
    String[] tags={"cobra_player_title","cobra_player_now","cobra_player_next","cobra_player_time"};
    String[] values={channel.name,now,pair==null||pair.next.isEmpty()?"Next programme unavailable":"NEXT  "+pair.next,time};
    for(int i=0;i<tags.length;i++){View raw=mPlayerOverlay.findViewWithTag(tags[i]);if(raw instanceof TextView)((TextView)raw).setText(values[i]);}
    View state=mPlayerOverlay.findViewWithTag("player_state");
    if(state instanceof TextView&&mPlayer!=null){int s=mPlayer.getPlaybackState();((TextView)state).setText(mPlayer.getPlayerError()!=null?"ERROR":s==Player.STATE_BUFFERING?"LOADING":s==Player.STATE_ENDED?"ENDED":!mPlayer.getPlayWhenReady()?"PAUSED":mPlayingVodKey.isEmpty()?"LIVE":"PLAYING");}
    View progress=mPlayerOverlay.findViewWithTag("cobra_program_progress");if(progress!=null)progress.invalidate();
    View favorite=mPlayerOverlay.findViewWithTag("cobra_player_favorite");if(favorite instanceof Button)((Button)favorite).setText(mFavorites.contains(channel.id)?"♥":"♡");
    updateCobraPlayerPlayPause();
  }
  private void cobraPlayerFooterText(LinearLayout parent,String tag,String value,int size,int color){
    TextView label=cobraText(value,color,size,Gravity.LEFT|Gravity.CENTER_VERTICAL);label.setTag(tag);label.setSingleLine(true);label.setEllipsize(android.text.TextUtils.TruncateAt.END);
    parent.addView(label,new LinearLayout.LayoutParams(-1,dp(size+10)));
  }
  private LinearLayout cobraPlayerDrawerBody(String title,String subtitle,String mode){
    closePlayerSettingsDrawer();if(mPlayerOverlay==null)return null;
    FrameLayout panel=new FrameLayout(this);mCobraPlayerDrawer=panel;mCobraPlayerDrawerMode=mode;panel.setTag("player_settings_drawer");
    panel.setBackground(surface(cobraPanelColor(),20,cobraThemeColor("line",mTheme.line),1));panel.setClickable(true);
    LinearLayout body=new LinearLayout(this);body.setOrientation(LinearLayout.VERTICAL);body.setPadding(dp(14),dp(12),dp(14),dp(12));panel.addView(body,new FrameLayout.LayoutParams(-1,-1));
    cobraSheetHeading(body,title,subtitle,()->closePlayerSettingsDrawer());mPlayerOverlay.addView(panel,new FrameLayout.LayoutParams(1,1));
    if(mPlayerChrome!=null)mPlayerChrome.setVisibility(View.GONE);layoutCobraPlayerViewport();
    panel.setAlpha(0f);panel.animate().alpha(1f).setDuration(170).start();return body;
  }
  private void showCobraPlayerChannels(){
    if(mPlayerOverlay==null||mCobraPlayerLocked)return;
    if("channels".equals(mCobraPlayerDrawerMode)){closePlayerSettingsDrawer();return;}
    LinearLayout body=cobraPlayerDrawerBody("Channels","Choose a category, then preview a channel","channels");if(body==null)return;
    LinearLayout filters=new LinearLayout(this);String[] keys={"FAVORITES","RECENT","ALL","CATEGORIES"},labels={"Favorites","Recent","All","Categories"};
    for(int i=0;i<keys.length;i++){final String key=keys[i];Button button=cobraTextAction(labels[i],false);button.setTextSize(11);button.setOnClickListener(v->renderCobraPlayerChannels(key));filters.addView(button,new LinearLayout.LayoutParams(0,dp(48),1));}
    body.addView(filters,new LinearLayout.LayoutParams(-1,dp(48)));mCobraPlayerBrowserList=new android.widget.ListView(this);mCobraPlayerBrowserList.setDivider(null);mCobraPlayerBrowserList.setFastScrollEnabled(true);body.addView(mCobraPlayerBrowserList,new LinearLayout.LayoutParams(-1,0,1));
    renderCobraPlayerChannels("CATEGORIES");
  }
  private void renderCobraPlayerChannels(String filter){
    if(mCobraPlayerBrowserList==null)return;mCobraPlayerBrowserFilter=filter;mCobraPlayerBrowserCategories="CATEGORIES".equals(filter);
    if(mCobraPlayerBrowserCategories){ArrayList<String> groups=cobraGuideGroups();mCobraPlayerBrowserList.setAdapter(new android.widget.BaseAdapter(){
      @Override public int getCount(){return groups.size();}@Override public Object getItem(int i){return groups.get(i);}@Override public long getItemId(int i){return i;}
      @Override public View getView(int i,View old,android.view.ViewGroup parent){Button row=old instanceof Button?(Button)old:cobraTextAction("",false);String group=groups.get(i);row.setText(group+"  ›");row.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);row.setOnClickListener(v->renderCobraPlayerChannels(group));row.setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,dp(56)));return row;}
    });return;}
    String search=mSearch;mSearch="";ArrayList<Channel> channels;try{channels=cobraVisibleGuideChannels(filter,"");}finally{mSearch=search;}
    mCobraPlayerBrowserList.setAdapter(new android.widget.BaseAdapter(){
      @Override public int getCount(){return channels.size();}@Override public Object getItem(int i){return channels.get(i);}@Override public long getItemId(int i){return i;}
      @Override public View getView(int i,View old,android.view.ViewGroup parent){Button row=old instanceof Button?(Button)old:cobraTextAction("",false);Channel channel=channels.get(i);ProgramPair pair=programFor(channel);boolean active=mPlaying!=null&&mPlaying.id.equals(channel.id);
        row.setText((active?"▶  ":"")+channel.name+"\n"+(pair==null?cobraGuideMessage(channel):pair.now));row.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);row.setTextSize(12);row.setBackground(cobraTouchSurface(active,10));
        row.setOnClickListener(v->{if(mPlaying!=null&&mPlaying.id.equals(channel.id)){closePlayerSettingsDrawer();return;}
          mPlaying=channel;mPlayingIndex=mChannels.indexOf(channel);mPlayingVodKey="";mPlayingVodTitle="";mPendingResumeMs=0;startSinglePlayer(channel.primaryUrl);requestCobraGuideWindow(channel,true);notifyDataSetChanged();});
        row.setOnLongClickListener(v->{showProgramGuide(channel);return true;});row.setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,dp(72)));return row;
      }
    });
  }

// COBRA-REPLACE buildPlayer
  private ExoPlayer buildPlayer(TextureView texture,Channel channel,boolean audible){
    DefaultHttpDataSource.Factory http=new DefaultHttpDataSource.Factory().setAllowCrossProtocolRedirects(true).setConnectTimeoutMs(15000).setReadTimeoutMs(30000).setUserAgent("Infinity Cobra/3.0");
    if(channel.headers!=null&&!channel.headers.isEmpty())http.setDefaultRequestProperties(channel.headers);
    DefaultDataSource.Factory data=new DefaultDataSource.Factory(this,http);
    DefaultLoadControl.Builder buffers=new DefaultLoadControl.Builder();
    if(mCobraCreatingMulti)buffers.setBufferDurationsMs(5000,30000,1000,2000).setTargetBufferBytes(6*1024*1024).setPrioritizeTimeOverSizeThresholds(false);
    else buffers.setBufferDurationsMs(15000,180000,2500,5000).setPrioritizeTimeOverSizeThresholds(true);
    ExoPlayer player=new ExoPlayer.Builder(this,new DefaultRenderersFactory(this).setEnableDecoderFallback(true))
        .setMediaSourceFactory(new DefaultMediaSourceFactory(data)).setLoadControl(buffers.build()).build();
    player.setAudioAttributes(new AudioAttributes.Builder().setUsage(C.USAGE_MEDIA).setContentType(C.AUDIO_CONTENT_TYPE_MOVIE).build(),false);
    player.setHandleAudioBecomingNoisy(true);player.setVideoTextureView(texture);player.setVolume(audible?1f:0f);watchCobraPlayback(player,channel);return player;
  }
// COBRA-REPLACE startSinglePlayer
  private void startSinglePlayer(String url){
    if(!isCobraAsyncAlive()||mPlaying==null||mPlayerTexture==null)return;releaseSinglePlayer();
    try{mPlayer=buildPlayer(mPlayerTexture,mPlaying,true);mPlayer.setMediaItem(mediaItem(url));mPlayer.prepare();startCobraPlayer(mPlayer);updateCobraPlayerInformation();}
    catch(Exception error){showError("Playback failed","Could not start this stream. "+error.getClass().getSimpleName());}
  }
// COBRA-REPLACE startCobraPreview
  private void startCobraPreview(Channel channel){
    if(channel==null||mCobraPreviewTexture==null||!isCobraAsyncAlive()||mPlayer!=null||mMultiOverlay!=null)return;
    String key=cobraChannelKey(channel);if(mCobraPreviewPlayer!=null&&key.equals(mCobraPreviewSessionKey))return;
    stopCobraPreviewPlayerOnly();mGuidePreviewChannel=channel;mGuidePreviewKey=key;mCobraPreviewSessionKey=key;
    try{mCobraPreviewPlayer=buildPlayer(mCobraPreviewTexture,channel,true);mCobraPreviewPlayer.setVolume(mCobraPreviewMuted?0f:1f);mCobraPreviewPlayer.setMediaItem(mediaItem(channel.primaryUrl));mCobraPreviewPlayer.prepare();startCobraPlayer(mCobraPreviewPlayer);requestCobraGuideWindow(channel,true);}
    catch(Exception error){setCobraPreviewLabel("Unable to start preview");}
  }
// COBRA-REPLACE cobraPreviewPanel
  private FrameLayout cobraPreviewPanel(Channel channel,boolean guide){
    if(mCobraPreviewHost!=null)return mCobraPreviewHost;
    FrameLayout host=new FrameLayout(this);host.setBackgroundColor(Color.BLACK);host.setTag("cobra_preview_host");mCobraPreviewHost=host;
    mCobraPreviewTexture=new TextureView(this);FrameLayout.LayoutParams vp=new FrameLayout.LayoutParams(-1,-1);vp.bottomMargin=dp(48);host.addView(mCobraPreviewTexture,vp);
    mCobraPreviewTexture.addOnLayoutChangeListener((v,l,t,r,b,ol,ot,or,ob)->{if(r-l!=or-ol||b-t!=ob-ot)applyCobraVideoFit(mCobraPreviewTexture,mCobraPreviewPlayer,0);});
    mCobraPreviewTexture.setOnClickListener(v->{if(mGuidePreviewChannel!=null)promoteCobraPreviewToFullscreen(mGuidePreviewChannel);});
    LinearLayout controls=new LinearLayout(this);controls.setGravity(Gravity.CENTER_VERTICAL);controls.setBackgroundColor(0xFF0A0D13);
    Button play=cobraIconButton("play","Pause preview");play.setTag("cobra_preview_play_pause");play.setText("❚❚");play.setOnClickListener(v->toggleCobraPreviewPlayPause());
    TextView title=cobraText(channel==null?"Choose a channel":channel.name,Color.WHITE,12,Gravity.LEFT|Gravity.CENTER_VERTICAL);title.setTag("cobra_preview_label");title.setSingleLine(true);title.setEllipsize(android.text.TextUtils.TruncateAt.END);
    Button full=cobraIconButton("fullscreen","Fullscreen");full.setOnClickListener(v->{if(mGuidePreviewChannel!=null)promoteCobraPreviewToFullscreen(mGuidePreviewChannel);});
    Button more=cobraIconButton("more","Preview actions");more.setOnClickListener(v->{if(mGuidePreviewChannel!=null)showCobraChannelActions(mGuidePreviewChannel);});
    controls.addView(play,new LinearLayout.LayoutParams(dp(48),dp(48)));controls.addView(title,new LinearLayout.LayoutParams(0,dp(48),1));controls.addView(full,new LinearLayout.LayoutParams(dp(48),dp(48)));controls.addView(more,new LinearLayout.LayoutParams(dp(48),dp(48)));
    host.addView(controls,new FrameLayout.LayoutParams(-1,dp(48),Gravity.BOTTOM));return host;
  }
// COBRA-REPLACE selectGuidePreview
  private void selectGuidePreview(Channel channel){
    if(channel==null)return;
    if(mPlayer!=null&&mPlayerOverlay!=null){if(mPlaying!=null&&mPlaying.id.equals(channel.id)){closeCobraSheet();closePlayerSettingsDrawer();return;}mPlaying=channel;mPlayingIndex=mChannels.indexOf(channel);startSinglePlayer(channel.primaryUrl);return;}
    String key=cobraChannelKey(channel);
    if(mCobraPreviewPlayer!=null&&key.equals(mCobraPreviewSessionKey)){
      if(mGuidePreviewArmed){promoteCobraPreviewToFullscreen(channel);return;}mGuidePreviewArmed=true;return;
    }
    mGuidePreviewChannel=channel;mGuidePreviewKey=key;mGuidePreviewArmed=true;
    if(mCobraPreviewHost==null||mCobraBrowseRoot==null||mCobraBrowseRoot.getParent()!=mStage)showCobraPrimaryView();
    startCobraPreview(channel);refreshCobraGuideViews();
  }
// COBRA-REPLACE promoteCobraPreviewToFullscreen
  private void promoteCobraPreviewToFullscreen(Channel channel){
    if(channel==null)return;ExoPlayer session=cobraChannelKey(channel).equals(mCobraPreviewSessionKey)?mCobraPreviewPlayer:null;
    if(session==null){playChannel(channel);return;}mCobraPreviewPlayer=null;mCobraPreviewSessionKey="";
    mReflowingMulti=true;releaseMulti();closePlayer();mReflowingMulti=false;
    mPlaying=channel;mPlayingIndex=mChannels.indexOf(channel);openPlayerOverlay(channel);mPlayer=session;
    session.setVideoTextureView(mPlayerTexture);session.setVolume(1f);applyCobraAspectTransform();configureCobraPip(true);updateCobraPlayerInformation();
  }
// COBRA-REPLACE closeFullscreenToCobraView
  private void closeFullscreenToCobraView(){
    closeCobraSheet();closePlayerSettingsDrawer();clearCobraPlayerLockState(false);
    Channel channel=mPlaying;ExoPlayer session=mPlayer;
    if(channel!=null&&session!=null&&findChannel(channel.id)!=null&&mPlayingVodKey.isEmpty()){
      mPlayer=null;mReflowingMulti=true;closePlayer();mReflowingMulti=false;
      mGuidePreviewChannel=channel;mGuidePreviewKey=cobraChannelKey(channel);mGuidePreviewArmed=true;
      if(mCobraPreviewHost==null)cobraPreviewPanel(channel,true);
      stopCobraPreviewPlayerOnly();mCobraPreviewPlayer=session;mCobraPreviewSessionKey=cobraChannelKey(channel);
      session.setVideoTextureView(mCobraPreviewTexture);session.setVolume(mCobraPreviewMuted?0f:1f);
      showCobraPrimaryView();applyCobraVideoFit(mCobraPreviewTexture,session,0);updateCobraPreviewPlayPause();return;
    }
    closePlayer();showCobraPrimaryView();
  }
// COBRA-REPLACE playChannel
  private void playChannel(Channel channel){
    if(channel==null)return;
    if(mCobraPreviewPlayer!=null&&cobraChannelKey(channel).equals(mCobraPreviewSessionKey)){promoteCobraPreviewToFullscreen(channel);return;}
    stopCobraPreviewPlayerOnly();mReflowingMulti=true;releaseMulti();closePlayer();mReflowingMulti=false;
    mPlaying=channel;mPlayingIndex=mChannels.indexOf(channel);mTriedFallback=false;openPlayerOverlay(channel);startSinglePlayer(channel.primaryUrl);
  }
// COBRA-REPLACE stopCobraPreview
  private void stopCobraPreview(){stopCobraPreviewPlayerOnly();}
// COBRA-REPLACE stopCobraPreviewPlayerOnly
  private void stopCobraPreviewPlayerOnly(){
    ExoPlayer player=mCobraPreviewPlayer;mCobraPreviewPlayer=null;mCobraPreviewSessionKey="";
    if(player!=null){mBackgroundResumePlayers.remove(player);try{player.release();}catch(Exception ignored){}}
  }
// COBRA-REPLACE applyCobraAspectTransform
  private void applyCobraAspectTransform(){applyCobraVideoFit(mPlayerTexture,mPlayer,mAspectMode);}
// COBRA-REPLACE stepChannel
  private void stepChannel(int delta){
    if(mCobraPlayerLocked)return;ArrayList<Channel> channels=cobraVisibleGuideChannels(mCategory,mCobraGuideSource);if(channels.isEmpty())channels=cobraVisibleGuideChannels("ALL","");if(channels.isEmpty())return;
    int current=-1;for(int i=0;i<channels.size();i++)if(mPlaying!=null&&channels.get(i).id.equals(mPlaying.id))current=i;
    Channel next=channels.get((Math.max(0,current)+delta+channels.size())%channels.size());playChannel(next);
  }
// COBRA-REPLACE openPlayerOverlay
  private void openPlayerOverlay(Channel channel){
    clearCobraPlayerLockState(false);mCobraSafeLeft=mCobraSafeTop=mCobraSafeRight=mCobraSafeBottom=0;
    FrameLayout overlay=new FrameLayout(this);mPlayerOverlay=overlay;overlay.setBackgroundColor(Color.BLACK);overlay.setTag("cobra_video_first_player");overlay.setFocusable(true);
    mPlayerTexture=new TextureView(this);mAspectMode=mPrefs.getInt(COBRA_ASPECT_MODE,0);overlay.addView(mPlayerTexture,new FrameLayout.LayoutParams(-1,-1));
    mPlayerTexture.addOnLayoutChangeListener((v,l,t,r,b,ol,ot,or,ob)->{if(r-l!=or-ol||b-t!=ob-ot)applyCobraAspectTransform();});
    mPlayerTexture.setOnClickListener(v->{if(mCobraPlayerLocked){showCobraPlayerUnlockAffordance();return;}if(!closePlayerSettingsDrawer())togglePlayerChrome();});
    mPlayerChrome=new LinearLayout(this);mPlayerChrome.setOrientation(LinearLayout.VERTICAL);mPlayerChrome.setTag("cobra_player_reboot_chrome");
    FrameLayout chrome=new FrameLayout(this);mPlayerChrome.addView(chrome,new LinearLayout.LayoutParams(-1,-1));
    LinearLayout header=new LinearLayout(this);header.setGravity(Gravity.CENTER_VERTICAL);header.setPadding(dp(10),0,dp(10),0);
    header.setBackground(new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,new int[]{0xB3000000,Color.TRANSPARENT}));
    Button back=cobraIconButton("back","Return to mini-player");back.setOnClickListener(v->closeFullscreenToCobraView());header.addView(back,new LinearLayout.LayoutParams(dp(48),dp(56)));
    TextView name=cobraText(channel.name,Color.WHITE,15,Gravity.LEFT|Gravity.CENTER_VERTICAL);name.setTag("cobra_player_title");name.setSingleLine(true);name.setEllipsize(android.text.TextUtils.TruncateAt.END);header.addView(name,new LinearLayout.LayoutParams(0,dp(56),1));
    Button lock=cobraIconButton("lock","Lock player controls");lock.setOnClickListener(v->lockCobraPlayer());header.addView(lock,new LinearLayout.LayoutParams(dp(48),dp(56)));chrome.addView(header,new FrameLayout.LayoutParams(-1,dp(64),Gravity.TOP));
    LinearLayout transport=new LinearLayout(this);transport.setGravity(Gravity.CENTER);
    Button previous=cobraIconButton("previous","Previous channel"),play=cobraIconButton("play","Play or pause"),next=cobraIconButton("next","Next channel");play.setTag("cobra_player_play_pause");
    previous.setOnClickListener(v->stepChannel(-1));next.setOnClickListener(v->stepChannel(1));play.setOnClickListener(v->toggleCobraPlayerPlayPause());
    transport.addView(previous,new LinearLayout.LayoutParams(dp(64),dp(64)));
    play.setBackground(new android.graphics.drawable.RippleDrawable(android.content.res.ColorStateList.valueOf(0x70FFFFFF),surface(0x48000000,40,0x70FFFFFF,1),surface(Color.WHITE,40,0,0)));
    LinearLayout.LayoutParams hero=new LinearLayout.LayoutParams(dp(76),dp(76));hero.leftMargin=dp(24);hero.rightMargin=dp(24);transport.addView(play,hero);transport.addView(next,new LinearLayout.LayoutParams(dp(64),dp(64)));
    chrome.addView(transport,new FrameLayout.LayoutParams(-1,dp(92),Gravity.CENTER));
    LinearLayout footer=new LinearLayout(this);footer.setOrientation(LinearLayout.VERTICAL);footer.setPadding(dp(16),dp(18),dp(16),dp(8));footer.setBackground(new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,new int[]{Color.TRANSPARENT,0xB0000000,0xEE000000}));
    LinearLayout info=new LinearLayout(this);info.setGravity(Gravity.CENTER_VERTICAL);LinearLayout copy=new LinearLayout(this);copy.setOrientation(LinearLayout.VERTICAL);
    cobraPlayerFooterText(copy,"cobra_player_now","",15,Color.WHITE);cobraPlayerFooterText(copy,"cobra_player_next","",11,0xFFC5CEDA);cobraPlayerFooterText(copy,"cobra_player_time","",10,0xFFA6B3C5);
    info.addView(copy,new LinearLayout.LayoutParams(0,-2,1));TextView state=cobraText("CONNECTING",Color.WHITE,9,Gravity.CENTER);state.setTag("player_state");state.setBackground(surface(0x55000000,9,0x55FFFFFF,1));info.addView(state,new LinearLayout.LayoutParams(dp(64),dp(26)));footer.addView(info);
    View progress=new View(this){final android.graphics.Paint p=new android.graphics.Paint(3);@Override protected void onDraw(android.graphics.Canvas c){long now=System.currentTimeMillis();float amount=0;boolean available=false;for(GuideProgram item:cobraSchedule(mPlaying))if(CobraCore.current(item.start,item.stop,now)){amount=(now-item.start)/(float)(item.stop-item.start);available=true;break;}if(!available)return;p.setColor(0x55FFFFFF);c.drawRect(0,dp(5),getWidth(),dp(7),p);p.setColor(cobraThemeColor("accent",mTheme.accent));c.drawRect(0,dp(5),getWidth()*amount,dp(7),p);}};
    progress.setTag("cobra_program_progress");footer.addView(progress,new LinearLayout.LayoutParams(-1,dp(12)));
    LinearLayout tools=new LinearLayout(this);String[] keys={"favorite","aspect","audio","multi","channels","more"},labels={"Favorite","Display","Audio","Multi-View","Channels","More"};
    for(int i=0;i<keys.length;i++){final String key=keys[i];Button button=cobraIconButton(key,labels[i]);if(i==0)button.setTag("cobra_player_favorite");
      button.setOnClickListener(v->{if(mCobraPlayerLocked)return;if("favorite".equals(key)){if(mPlaying!=null)toggleFavorite(mPlaying);updateCobraPlayerInformation();}else if("aspect".equals(key))showCobraAspectPicker();else if("audio".equals(key))showTrackChooser();else if("multi".equals(key))beginMultiView();else if("channels".equals(key))showCobraPlayerChannels();else showPlayerSettingsDrawer();});tools.addView(button,new LinearLayout.LayoutParams(0,dp(48),1));}
    footer.addView(tools,new LinearLayout.LayoutParams(-1,dp(48)));chrome.addView(footer,new FrameLayout.LayoutParams(-1,-2,Gravity.BOTTOM));
    overlay.addView(mPlayerChrome,new FrameLayout.LayoutParams(-1,-1));chrome.setOnClickListener(v->togglePlayerChrome());
    overlay.addOnLayoutChangeListener((v,l,t,r,b,ol,ot,or,ob)->{if(r-l!=or-ol||b-t!=ob-ot)layoutCobraPlayerViewport();});
    overlay.setOnApplyWindowInsetsListener((v,insets)->{mCobraSafeLeft=insets.getSystemWindowInsetLeft();mCobraSafeTop=insets.getSystemWindowInsetTop();mCobraSafeRight=insets.getSystemWindowInsetRight();mCobraSafeBottom=insets.getSystemWindowInsetBottom();if(Build.VERSION.SDK_INT>=28&&insets.getDisplayCutout()!=null){mCobraSafeTop=Math.max(mCobraSafeTop,insets.getDisplayCutout().getSafeInsetTop());mCobraSafeLeft=Math.max(mCobraSafeLeft,insets.getDisplayCutout().getSafeInsetLeft());mCobraSafeRight=Math.max(mCobraSafeRight,insets.getDisplayCutout().getSafeInsetRight());}layoutCobraPlayerViewport();return insets;});
    ((FrameLayout)getWindow().getDecorView()).addView(overlay,new FrameLayout.LayoutParams(-1,-1));overlay.requestApplyInsets();updateCobraPlayerInformation();scheduleChromeHide();
    if(findChannel(channel.id)!=null)requestCobraGuideWindow(channel,true);mMain.removeCallbacks(mCobraUiTick);mMain.postDelayed(mCobraUiTick,10000L);
  }
// COBRA-REPLACE showPlayerSettingsDrawer
  private void showPlayerSettingsDrawer(){
    if(mPlayerOverlay==null||mCobraPlayerLocked)return;if("settings".equals(mCobraPlayerDrawerMode)){closePlayerSettingsDrawer();return;}
    LinearLayout panel=cobraPlayerDrawerBody("Player settings","Playback and output","settings");if(panel==null)return;
    ScrollView scroll=new ScrollView(this);LinearLayout body=new LinearLayout(this);body.setOrientation(LinearLayout.VERTICAL);scroll.addView(body);panel.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
    cobraSheetAction(body,"●",mRecordingSession.isEmpty()?"Record now":"Stop recording",false,()->{if(mPlaying!=null)toggleRecording(mPlaying);});
    cobraSheetAction(body,"♪","Audio / subtitles",false,()->showTrackChooser());
    cobraSheetAction(body,"▣","Aspect / display",false,()->showCobraAspectPicker());
    cobraSheetAction(body,"↗","Cast / route",false,()->openCastSettings());
    cobraSheetAction(body,"◈","Source",false,()->{closePlayer();showSources();});
    cobraSheetAction(body,"×","Close player",false,()->closeFullscreenToCobraView());
  }
// COBRA-REPLACE closePlayerSettingsDrawer
  private boolean closePlayerSettingsDrawer(){
    if(mCobraPlayerDrawer==null)return false;android.view.ViewParent parent=mCobraPlayerDrawer.getParent();if(parent instanceof android.view.ViewGroup)((android.view.ViewGroup)parent).removeView(mCobraPlayerDrawer);
    mCobraPlayerDrawer=null;mCobraPlayerDrawerMode="";mCobraPlayerBrowserList=null;layoutCobraPlayerViewport();showPlayerChromeTemporarily();return true;
  }
// COBRA-REPLACE togglePlayerChrome
  private void togglePlayerChrome(){if(mCobraPlayerLocked){showCobraPlayerUnlockAffordance();return;}if(mPlayerChrome==null||mCobraPlayerDrawer!=null||mCobraMultiPicker!=null||isCobraInPictureInPicture())return;mPlayerChrome.setVisibility(mPlayerChrome.getVisibility()==View.VISIBLE?View.GONE:View.VISIBLE);if(mPlayerChrome.getVisibility()==View.VISIBLE){updateCobraPlayerInformation();scheduleChromeHide();}}
// COBRA-REPLACE showPlayerChromeTemporarily
  private void showPlayerChromeTemporarily(){if(mCobraPlayerLocked){showCobraPlayerUnlockAffordance();return;}if(mPlayerChrome==null||mCobraPlayerDrawer!=null||mCobraMultiPicker!=null||isCobraInPictureInPicture())return;mPlayerChrome.setVisibility(View.VISIBLE);updateCobraPlayerInformation();scheduleChromeHide();}
// COBRA-REPLACE scheduleChromeHide
  private void scheduleChromeHide(){mMain.removeCallbacks(mHideChrome);mMain.postDelayed(mHideChrome,3500L);}
// COBRA-REPLACE lockCobraPlayer
  private void lockCobraPlayer(){if(mPlayerOverlay==null)return;closeCobraSheet();closePlayerSettingsDrawer();closeCobraMultiPicker(false);mCobraPlayerLocked=true;mMain.removeCallbacks(mHideChrome);if(mPlayerChrome!=null)mPlayerChrome.setVisibility(View.GONE);ensureCobraPlayerLockOverlay();showCobraPlayerUnlockAffordance();}

// COBRA-APPEND
  @Override public boolean dispatchKeyEvent(KeyEvent event) {
    int key=event.getKeyCode();
    boolean volume=key==KeyEvent.KEYCODE_VOLUME_UP||key==KeyEvent.KEYCODE_VOLUME_DOWN||key==KeyEvent.KEYCODE_VOLUME_MUTE;
    if(mCobraPlayerLocked&&mPlayerOverlay!=null&&!volume){
      if(event.getAction()==KeyEvent.ACTION_DOWN){
        boolean visible=mCobraPlayerUnlockButton!=null&&mCobraPlayerUnlockButton.getVisibility()==View.VISIBLE;
        if(visible&&(key==KeyEvent.KEYCODE_DPAD_CENTER||key==KeyEvent.KEYCODE_ENTER))unlockCobraPlayer();else showCobraPlayerUnlockAffordance();
      }
      return true;
    }
    if(mPlayerOverlay!=null&&mPlayer!=null&&event.getAction()==KeyEvent.ACTION_DOWN){
      if(key==KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE){toggleCobraPlayerPlayPause();return true;}
      if(key==KeyEvent.KEYCODE_MEDIA_PLAY){mPlayer.play();return true;}
      if(key==KeyEvent.KEYCODE_MEDIA_PAUSE){mPlayer.pause();return true;}
      if(key==KeyEvent.KEYCODE_MENU){showCobraPlayerChannels();return true;}
      if(mPlayerChrome!=null&&mPlayerChrome.getVisibility()!=View.VISIBLE&&mCobraPlayerDrawer==null&&mCobraMultiPicker==null
          &&(key==KeyEvent.KEYCODE_DPAD_CENTER||key==KeyEvent.KEYCODE_DPAD_UP||key==KeyEvent.KEYCODE_DPAD_DOWN)){
        showPlayerChromeTemporarily();View play=mPlayerOverlay.findViewWithTag("cobra_player_play_pause");if(play!=null)play.requestFocus();return true;
      }
    }
    return super.dispatchKeyEvent(event);
  }
