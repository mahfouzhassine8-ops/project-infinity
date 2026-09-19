 pause=method(text,'onPause');pause=once(pause,'    mCobraPlaybackPolicy.pause();','    mCobraPlaybackPolicy.pause();\n    cobraStopFrameMeter();cobraClearRefreshRequest();','refresh pause');text=replace_method(text,'onPause',pause)
 config=method(text,'onConfigurationChanged');config=once(config,'      mMain.post(this::cobraApplySystemBarsForSurface);','      mMain.post(this::cobraApplySystemBarsForSurface);\n      mMain.post(()->cobraApplyRefreshPolicy("configuration"));','refresh config');text=replace_method(text,'onConfigurationChanged',config)
 pip=method(text,'onPictureInPictureModeChanged');pip=once(pip,'    mMain.post(()->{cobraConsumeLauncherPipReturn();cobraApplySystemBarsForSurface();});','    mMain.post(()->{cobraConsumeLauncherPipReturn();cobraApplySystemBarsForSurface();cobraApplyRefreshPolicy("pip");});','refresh pip');text=replace_method(text,'onPictureInPictureModeChanged',pip)
 multi=method(text,'onMultiWindowModeChanged');multi=once(multi,'    if (mDeviceBridge != null) mDeviceBridge.onWindowChanged("multi-window");','    if (mDeviceBridge != null) mDeviceBridge.onWindowChanged("multi-window");\n    cobraApplyRefreshPolicy("multi-window");','refresh multiwindow');text=replace_method(text,'onMultiWindowModeChanged',multi)
 focus=method(text,'onWindowFocusChanged');focus=once(focus,'      mMain.post(this::cobraApplySystemBarsForSurface);','      mMain.post(this::cobraApplySystemBarsForSurface);\n      mMain.post(()->cobraApplyRefreshPolicy("focus"));','refresh focus');text=replace_method(text,'onWindowFocusChanged',focus)

 # Smart buffering and HLS local timeshift transport.
 build=method(text,'buildPlayer')
 build=once(build,'    DefaultDataSource.Factory data=new DefaultDataSource.Factory(this,http);','''    boolean multi=mCobraCreatingMulti;
    boolean localTimeshift=!multi&&cobraLiveRewindEnabled()&&cobraLocalTimeshiftEnabled()&&cobraLiveChannel(channel)&&cobraIsHls(channel.primaryUrl);
    CobraTimeshiftStore timeshift=localTimeshift?new CobraTimeshiftStore(channel.id):null;
    androidx.media3.datasource.DataSource.Factory data=timeshift==null?new DefaultDataSource.Factory(this,http):new CobraTimeshiftDataSourceFactory(http,timeshift);''','timeshift data factory')
 build=once(build,'    boolean multi=mCobraCreatingMulti;\n    // Bound *compressed* buffering as well as time; four 180-second buffers were not a safe default.\n    DefaultLoadControl control=new DefaultLoadControl.Builder()\n        .setBufferDurationsMs(multi?6000:10000,multi?30000:60000,1500,3000)\n        .setTargetBufferBytes((multi?12:32)*1024*1024).setPrioritizeTimeOverSizeThresholds(false).build();','''    // Multi-View keeps the established bounded profile. Single-view Auto returns to Media3's default time-first policy; Resilient adds a larger refill reserve without a byte cap.
    DefaultLoadControl control;
    if(multi)control=new DefaultLoadControl.Builder().setBufferDurationsMs(6000,30000,1500,3000).setTargetBufferBytes(12*1024*1024).setPrioritizeTimeOverSizeThresholds(false).build();
    else if("resilient".equals(cobraSmartBufferMode()))control=new DefaultLoadControl.Builder().setBufferDurationsMs(20000,90000,2500,8000).setPrioritizeTimeOverSizeThresholds(true).build();
    else control=new DefaultLoadControl();''','smart buffer profile')
 build=once(build,'    CobraPlayerBinding binding=new CobraPlayerBinding(player,channel);','    CobraPlayerBinding binding=new CobraPlayerBinding(player,channel,timeshift);','binding timeshift')
 text=replace_method(text,'buildPlayer',build)

 start=method(text,'startSinglePlayer')
 start=once(start,'      mPlayer=buildPlayer(mPlayerTexture,mPlaying,true);\n      mPlayer.setMediaItem(mediaItem(url));mPlayer.prepare();startCobraPlayer(mPlayer);','''      Channel sessionChannel=cobraTimeshiftSessionChannel(mPlaying,url);String sessionUrl=sessionChannel==mPlaying?url:sessionChannel.primaryUrl;
      mPlayer=buildPlayer(mPlayerTexture,sessionChannel,true);
      mPlayer.setMediaItem(mediaItem(sessionUrl));mPlayer.prepare();startCobraPlayer(mPlayer);''','start local timeshift hls')
 text=replace_method(text,'startSinglePlayer',start)
 preview=method(text,'startCobraPreview')
 preview=once(preview,'      mGuidePreviewChannel=channel;mGuidePreviewKey=cobraChannelKey(channel);\n      mCobraPreviewPlayer=buildPlayer(mCobraPreviewTexture,channel,!mCobraPreviewMuted);\n      mCobraPreviewSessionKey=cobraChannelKey(channel);\n      mCobraPreviewPlayer.setMediaItem(mediaItem(channel.primaryUrl));mCobraPreviewPlayer.prepare();','      mGuidePreviewChannel=channel;mGuidePreviewKey=cobraChannelKey(channel);\n      Channel sessionChannel=cobraTimeshiftSessionChannel(channel,channel.primaryUrl);\n      mCobraPreviewPlayer=buildPlayer(mCobraPreviewTexture,sessionChannel,!mCobraPreviewMuted);\n      mCobraPreviewSessionKey=cobraChannelKey(channel);\n      mCobraPreviewPlayer.setMediaItem(mediaItem(sessionChannel.primaryUrl));mCobraPreviewPlayer.prepare();','preview local timeshift hls')
 text=replace_method(text,'startCobraPreview',preview)

 # Never destroy a healthy buffer by re-preparing after a long stall; observe it instead.
 old='''          if(!cobraPermitBufferRetry(mPlayer)){mBufferingSince=0L;return;}
          mPlaybackRetryCount++;
          try { mPlayer.prepare(); mPlayer.play(); } catch (Exception ignored) {}
          mBufferingSince = System.currentTimeMillis();'''
 new='''          CobraPlayerBinding binding=mCobraPlayerBindings.get(mPlayer);
          if(binding!=null&&binding.current()){binding.vitals.lastRecovery="buffering_observed_12s";binding.vitals.bufferRetries++;InfinityCobraDiagnostics.record(InfinityLiveActivity.this,"buffering","prolonged","Observed 12 s buffering; player was not re-prepared");}
          mBufferingSince = System.currentTimeMillis();'''
 text=once(text,old,new,'remove stall reprepare')

 # Binding owns optional timeshift store and rebuffer metrics.
 binding=method(text,'CobraPlayerBinding') if False else None
 # class parser is not method parser; edit exact class snippets.
 text=once(text,'    final CobraSessionVitals vitals;CobraCaptionOverlay captions;','    final CobraSessionVitals vitals;final CobraTimeshiftStore timeshift;CobraCaptionOverlay captions;','binding store field')
 text=once(text,'    CobraPlayerBinding(ExoPlayer p,Channel c){player=p;channel=c;vitals=new CobraSessionVitals(p,c);}','    CobraPlayerBinding(ExoPlayer p,Channel c,CobraTimeshiftStore store){player=p;channel=c;timeshift=store;vitals=new CobraSessionVitals(p,c);}','binding ctor')
 state=method(text,'onPlaybackStateChanged')
 # wrong: method cardinality includes Activity? multiple same name? parser will see one? It finds override inside inner class too and may cardinality 1. Use exact text global instead.
 text=once(text,'      if(state==Player.STATE_READY)error="";','      if(state==Player.STATE_READY){error="";vitals.rebuffering=false;}else if(state==Player.STATE_BUFFERING&&player.getPlayWhenReady()&&vitals.firstFrameAt>=0&&!vitals.rebuffering){vitals.rebuffering=true;vitals.rebufferCount++;}\n      if(player==mPlayer)cobraUpdatePlayerRuntimeUi();','rebuffer metrics')
 dispose=method(text,'cobraDisposePlayer');dispose=once(dispose,'    if(binding!=null){binding.closed=true;','    if(binding!=null){if(binding.timeshift!=null)binding.timeshift.destroy();binding.closed=true;','dispose timeshift cache');text=replace_method(text,'cobraDisposePlayer',dispose)

 # Vitals throughput fields and bandwidth callback.
 text=once(text,'    int loadErrors,bufferRetries;String lastError="",lastRecovery="not_requested",decoder="Not reported";','    int loadErrors,bufferRetries,rebufferCount;long bandwidthEstimate=-1;boolean rebuffering;String lastError="",lastRecovery="not_requested",decoder="Not reported";','vitals diagnostic fields')
 text=once(text,'    @Override public void onVideoDecoderInitialized(androidx.media3.exoplayer.analytics.AnalyticsListener.EventTime event,String name,long time,long duration){decoder=name==null?"Not reported":name;recovery.suspend();}','    @Override public void onBandwidthEstimate(androidx.media3.exoplayer.analytics.AnalyticsListener.EventTime event,int totalLoadTimeMs,long totalBytesLoaded,long bitrateEstimate){if(bitrateEstimate>0)this.bandwidthEstimate=bitrateEstimate;}\n    @Override public void onVideoDecoderInitialized(androidx.media3.exoplayer.analytics.AnalyticsListener.EventTime event,String name,long time,long duration){decoder=name==null?"Not reported":name;recovery.suspend();}','vitals bandwidth')

 # Health JSON + readable summary.
