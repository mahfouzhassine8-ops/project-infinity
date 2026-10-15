// @replace onDestroy
  @Override protected void onDestroy() {
    // Terminal state must be visible before callbacks, views or decoder sessions are released.
    closeCobraAsyncWork();mBackgroundStopped=true;
    closeCobraActionSheet();closeCobraPlayerDrawer();closeCobraMultiPicker(true);clearCobraPlayerLockState(false);
    stopCobraPreview();releaseSinglePlayer();releaseMulti();releaseCobraTransferPlayer();
    for(ExoPlayer player:new ArrayList<>(mCobraPlayerBindings.keySet()))cobraDisposePlayer(player);
    mBackgroundResumePlayers.clear();mMain.removeCallbacksAndMessages(null);
    if(mDeviceBridge!=null)mDeviceBridge.close();super.onDestroy();
  }
// @replace onConfigurationChanged
  @Override public void onConfigurationChanged(Configuration configuration) {
    super.onConfigurationChanged(configuration);mTheme=Theme.load(this);mUi=UiContract.load(this);
    if(mDeviceBridge!=null)mDeviceBridge.onWindowChanged("configuration");
    // Reflow child bounds in place. No player, video texture or tile is replaced.
    closeCobraActionSheet();mRebuildShellAfterPlayer=false;
    if(mRoot!=null)mRoot.setBackgroundColor(cobraThemeColor("background",mTheme.background));
    if(mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow()){cobraLayoutGuide();cobraRenderGuideBrowser();cobraRestyleGuide();}
    if(mMultiOverlay!=null){cobraLayoutPlayerPanels();cobraLayoutMultiTiles();return;}
    if(mPlayerOverlay!=null){cobraBuildPlayerChrome();cobraLayoutPlayerPanels();configureCobraPip(true);return;}
    if(mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow())return;
    buildShell();if(mChannels.isEmpty()){if(mSources.isEmpty())showWelcome();else loadAllEnabledSources(false);}else showCobraPrimaryView();
  }
// @replace onBackPressed
  @Override public void onBackPressed() {
    if(mCobraPlayerLocked&&mPlayerOverlay!=null){showCobraPlayerUnlockAffordance();return;}
    if(closeCobraActionSheet())return;
    if(mCobraMultiPicker!=null){closeCobraMultiPicker(false);return;}
    if(mCobraPlayerDrawer!=null){if(mCobraDrawerFilter.startsWith("GROUP:")){cobraRenderPlayerDrawer("CATEGORIES");return;}closeCobraPlayerDrawer();return;}
    if(closeCobraPowerMenu()||closeCobraViewModeMenu()||closeCobraChannelActions()||closeCobraExperienceDrawer())return;
    if(mPlayerOverlay!=null){closeFullscreenToCobraView();return;}
    if(mMultiOverlay!=null){releaseMulti();return;}
    if(!"root".equals(mCobraInternalScreen)){showCobraPrimaryView();return;}
    if(mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow()&&"channels".equals(mCobraGuideRoute)){mCobraGuideRoute="categories";mSearch="";cobraRenderGuideBrowser();return;}
    if("sources".equals(mCobraGuideRoute)){mCobraGuideRoute="categories";cobraRenderGuideBrowser();return;}
    moveTaskToBack(true);
  }
// @replace onPictureInPictureModeChanged
  @Override public void onPictureInPictureModeChanged(boolean inPictureInPictureMode,Configuration configuration) {
    super.onPictureInPictureModeChanged(inPictureInPictureMode,configuration);mInPictureInPicture=inPictureInPictureMode;
    if(inPictureInPictureMode){closeCobraActionSheet();closeCobraPlayerDrawer();closeCobraMultiPicker(false);mMain.removeCallbacks(mHideCobraUnlockButton);}
    if(mCobraPlayerLockOverlay!=null)mCobraPlayerLockOverlay.setVisibility(inPictureInPictureMode?View.GONE:mCobraPlayerLocked?View.VISIBLE:View.GONE);
    if(mPlayerChrome!=null)mPlayerChrome.setVisibility(inPictureInPictureMode||mCobraPlayerLocked?View.GONE:View.VISIBLE);
    if(!inPictureInPictureMode)showPlayerChromeTemporarily();cobraLayoutPlayerPanels();
    if(mDeviceBridge!=null)mDeviceBridge.onWindowChanged("picture-in-picture");
  }
// @replace enterCobraPictureInPicture
  private void enterCobraPictureInPicture() {
    if(!hasCobraVideo())return;if(Build.VERSION.SDK_INT<26){pauseCobraForBackground();return;}
    if(mMultiOverlay!=null)multiToSingle();
    closeCobraActionSheet();closeCobraPlayerDrawer();closeCobraMultiPicker(false);
    if(mPlayerChrome!=null)mPlayerChrome.setVisibility(View.GONE);if(mCobraPlayerLockOverlay!=null)mCobraPlayerLockOverlay.setVisibility(View.GONE);
    try{PictureInPictureParams params=cobraPipParams(false);if(params==null||!enterPictureInPictureMode(params)){pauseCobraForBackground();cobraRestoreAfterPipFailure();}}
    catch(IllegalStateException|IllegalArgumentException error){pauseCobraForBackground();cobraRestoreAfterPipFailure();}
  }
// @replace isCurrentCobraPlayer
  private boolean isCurrentCobraPlayer(ExoPlayer player) {
    if(player==null)return false;if(player==mPlayer||player==mCobraPreviewPlayer||player==mCobraTransferPlayer||player==mCobraCarryPlayer)return true;
    if(mMultiPlayers!=null)for(ExoPlayer current:mMultiPlayers)if(current==player)return true;return false;
  }
// @replace pauseCobraForBackground
  private void pauseCobraForBackground() {
    mBackgroundStopped=true;mMain.removeCallbacks(mStallWatchdog);mMain.removeCallbacks(mCobraPresentationTick);mBufferingSince=0L;
    rememberAndPauseCobraPlayer(mPlayer);rememberAndPauseCobraPlayer(mCobraPreviewPlayer);
    rememberAndPauseCobraPlayer(mCobraCarryPlayer);rememberAndPauseCobraPlayer(mCobraTransferPlayer);
    if(mMultiPlayers!=null)for(ExoPlayer player:mMultiPlayers)rememberAndPauseCobraPlayer(player);
  }
// @replace returnToInfinity
  private void returnToInfinity() {
    closeCobraAsyncWork();stopCobraPreview();releaseSinglePlayer();releaseMulti();releaseCobraTransferPlayer();
    Intent intent=new Intent(this,@APP_PACKAGE@.Main.class);intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_SINGLE_TOP);startActivity(intent);finish();
  }
// @replace reloadCobraUiIfChanged
  private void reloadCobraUiIfChanged() {
    long stamp=UiContract.sourceStamp(this);if(mUi!=null&&stamp==mUi.sourceStamp)return;mUi=UiContract.load(this);mTheme=Theme.load(this);
    if(mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow()){cobraRestyleGuide();cobraLayoutGuide();cobraRenderGuideBrowser();}
    if(mPlayerOverlay!=null){cobraBuildPlayerChrome();return;}if(mMultiOverlay!=null)return;
    if(mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow())return;
    buildShell();if(mChannels.isEmpty()){if(mSources.isEmpty())showWelcome();else loadAllEnabledSources(false);}else showCobraPrimaryView();
  }
// @replace toggleCobraPreviewPlayPause
  private void toggleCobraPreviewPlayPause() {
    if(mCobraPreviewPlayer==null){mCobraPreviewAutoplayAllowed=true;if(mGuidePreviewChannel!=null)startCobraPreview(mGuidePreviewChannel);return;}
    if(mCobraPreviewPlayer.getPlayWhenReady())mCobraPreviewPlayer.pause();else startCobraPlayer(mCobraPreviewPlayer);updateCobraPreviewPlayPause();
  }
// @replace showCobraViewModeMenu
  private void showCobraViewModeMenu() {
    LinearLayout rows=cobraOpenSheet("View mode","One live session, layouts for your screen","view-mode");boolean dark=cobraSheetIsDark();
    String[] keys={"mobile","grid","compact","cards","focus"},names={"Mobile","TV Grid","Compact","Cards","Focus"},details={"Touch-first channel list with live preview","Time-aligned programme guide; Now / Next in portrait","Dense rows for large channel lineups","Responsive programme cards","Large preview and a vertical channel browser"};
    for(int i=0;i<keys.length;i++){final String key=keys[i];rows.addView(cobraSheetRow("guide",names[i],details[i],false,dark,()->{
      if("mobile".equals(key))mPrefs.edit().putString(COBRA_PRIMARY_VIEW,"mobile").apply();else mPrefs.edit().putString(COBRA_PRIMARY_VIEW,"guide").putString(GUIDE_VIEW_MODE,key).apply();
      mCobraGuideStyle=key;mCobraGuideRoute="channels";cobraShowGuideShell();}));}
  }
// @replace cobraPipParams
  private PictureInPictureParams cobraPipParams(boolean autoEnter) {
    if(Build.VERSION.SDK_INT<26)return null;
    float ratio=16f/9f;if(mPlayer!=null){VideoSize size=mPlayer.getVideoSize();if(size.width>0&&size.height>0)ratio=size.width*(size.pixelWidthHeightRatio>0?size.pixelWidthHeightRatio:1f)/size.height;}
    ratio=Math.max(1f/2.39f,Math.min(2.39f,ratio));
    PictureInPictureParams.Builder builder=new PictureInPictureParams.Builder().setAspectRatio(new Rational(Math.round(ratio*10000),10000));
    if(Build.VERSION.SDK_INT>=31){builder.setAutoEnterEnabled(autoEnter);builder.setSeamlessResizeEnabled(true);}return builder.build();
  }
// @append
  private void cobraRestyleGuide() {
    int background=cobraThemeColor("background",mTheme.background),text=cobraThemeColor("text",mTheme.text),muted=cobraThemeColor("muted",mTheme.muted);
    if(mRoot!=null)mRoot.setBackgroundColor(background);if(mStage!=null)mStage.setBackgroundColor(background);
    if(mHeader!=null)mHeader.setTextColor(text);if(mStatus!=null)mStatus.setTextColor(muted);
    if(mCobraGuideNowLabel!=null)mCobraGuideNowLabel.setTextColor(text);if(mCobraGuideNextLabel!=null)mCobraGuideNextLabel.setTextColor(muted);
  }

  private void cobraRestoreAfterPipFailure() {
    if(mCobraPlayerLockOverlay!=null)mCobraPlayerLockOverlay.setVisibility(mCobraPlayerLocked?View.VISIBLE:View.GONE);
    showPlayerChromeTemporarily();
  }
