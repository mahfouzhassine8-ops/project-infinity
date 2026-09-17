// COBRA-REPLACE onBackPressed
  public void onBackPressed(){
    if(mCobraPlayerLocked&&mPlayerOverlay!=null){showCobraPlayerUnlockAffordance();return;}
    if(closeCobraSheet())return;
    if(mCobraMultiPicker!=null){closeCobraMultiPicker(false);return;}
    if(closeCobraPowerMenu()||closeCobraViewModeMenu()||closeCobraChannelActions()||closeCobraExperienceDrawer())return;
    if(mPlayerOverlay!=null){
      if("channels".equals(mCobraPlayerDrawerMode)&&!mCobraPlayerBrowserCategories){renderCobraPlayerChannels("CATEGORIES");return;}
      if(closePlayerSettingsDrawer())return;closeFullscreenToCobraView();return;
    }
    if(mMultiOverlay!=null){releaseMulti();showCobraPrimaryView();return;}
    if(!"root".equals(mCobraInternalScreen)){showCobraPrimaryView();return;}
    if(cobraGuideBack())return;
    moveTaskToBack(true);
  }
// COBRA-REPLACE onConfigurationChanged
  public void onConfigurationChanged(Configuration configuration){
    super.onConfigurationChanged(configuration);mTheme=Theme.load(this);mUi=UiContract.load(this);
    if(mDeviceBridge!=null)mDeviceBridge.onWindowChanged("configuration");
    closeCobraSheet();closePlayerSettingsDrawer();closeCobraMultiPicker(false);
    if(mMultiOverlay!=null){mMultiOverlay.post(()->layoutCobraMultiTiles());return;}
    if(mPlayerOverlay!=null){mPlayerOverlay.post(()->layoutCobraPlayerViewport());configureCobraPip(true);return;}
    if(mCobraBrowseRoot!=null&&mCobraBrowseRoot.getParent()==mStage){mCobraBrowseRoot.post(()->{layoutCobraGuideShell();renderCobraGuideBody();});return;}
    buildShell();if(mChannels.isEmpty()){if(mSources.isEmpty())showWelcome();else loadAllEnabledSources(false);}else showCobraPrimaryView();
  }
// COBRA-REPLACE enterCobraPictureInPicture
  private void enterCobraPictureInPicture(){
    if(!hasCobraVideo())return;if(Build.VERSION.SDK_INT<26){pauseCobraForBackground();return;}
    closeCobraSheet();closePlayerSettingsDrawer();closeCobraMultiPicker(false);
    if(mMultiOverlay!=null)multiToSingle();
    else if(mPlayer==null&&mCobraPreviewPlayer!=null&&mGuidePreviewChannel!=null)promoteCobraPreviewToFullscreen(mGuidePreviewChannel);
    try{PictureInPictureParams params=cobraPipParams(false);boolean entered=params!=null&&enterPictureInPictureMode(params);if(!entered)pauseCobraForBackground();}
    catch(IllegalStateException|IllegalArgumentException error){pauseCobraForBackground();}
  }
// COBRA-REPLACE onPictureInPictureModeChanged
  public void onPictureInPictureModeChanged(boolean inPictureInPictureMode,Configuration configuration){
    super.onPictureInPictureModeChanged(inPictureInPictureMode,configuration);mInPictureInPicture=inPictureInPictureMode;
    if(inPictureInPictureMode){closeCobraSheet();closePlayerSettingsDrawer();closeCobraMultiPicker(true);}
    if(mCobraPlayerLockOverlay!=null)mCobraPlayerLockOverlay.setVisibility(inPictureInPictureMode?View.GONE:mCobraPlayerLocked?View.VISIBLE:View.GONE);
    if(mPlayerChrome!=null)mPlayerChrome.setVisibility(inPictureInPictureMode||mCobraPlayerLocked?View.GONE:View.VISIBLE);
    if(!inPictureInPictureMode)showPlayerChromeTemporarily();
    layoutCobraPlayerViewport();if(mDeviceBridge!=null)mDeviceBridge.onWindowChanged("picture-in-picture");
  }
// COBRA-REPLACE hasCobraVideo
  private boolean hasCobraVideo(){
    ArrayList<ExoPlayer> players=new ArrayList<>();if(mPlayer!=null)players.add(mPlayer);if(mCobraPreviewPlayer!=null)players.add(mCobraPreviewPlayer);for(CobraTile tile:mCobraTiles)if(tile.player!=null)players.add(tile.player);
    for(ExoPlayer player:players){int state=player.getPlaybackState();if(state!=Player.STATE_IDLE&&state!=Player.STATE_ENDED)return true;}return false;
  }
// COBRA-REPLACE isCurrentCobraPlayer
  private boolean isCurrentCobraPlayer(ExoPlayer player){return player!=null&&(player==mPlayer||player==mCobraPreviewPlayer||player==mCobraTransferPlayer||cobraTileFor(player)!=null);}
// COBRA-REPLACE showCobraChannelActions
  private void showCobraChannelActions(Channel channel){
    if(channel==null)return;LinearLayout body=cobraOpenSheet(channel.name,channel.group,"channel-actions");
    cobraSheetAction(body,"♥",mFavorites.contains(channel.id)?"Remove from Favorites":"Add to Favorites",false,()->{toggleFavorite(channel);refreshCobraGuideViews();});
    cobraSheetAction(body,"◷","Schedule recording",false,()->showCobraScheduleRecording(channel));
    cobraSheetAction(body,"+","Add to group",false,()->showCobraAddToGroup(channel));
    cobraSheetAction(body,"↗","Share channel",false,()->shareCobraChannel(channel));
    cobraSheetAction(body,"▤","Programme schedule",false,()->showProgramGuide(channel));
    if(mCobraPreviewPlayer!=null&&mGuidePreviewChannel!=null&&channel.id.equals(mGuidePreviewChannel.id)){
      cobraSheetAction(body,"♪",mCobraPreviewMuted?"Unmute preview":"Mute preview",false,()->toggleCobraPreviewMute());
      cobraSheetAction(body,"CC","Preview captions",false,()->toggleCobraPreviewCaptions());
    }
    cobraSheetAction(body,"−","Hide channel",true,()->hideCobraChannel(channel));
  }
// COBRA-REPLACE showCobraScheduleRecording
  private void showCobraScheduleRecording(Channel channel){showProgramGuide(channel);}
// COBRA-REPLACE guideTitleAt
  private String guideTitleAt(Channel channel,long instant){for(GuideProgram p:cobraSchedule(channel))if(CobraCore.current(p.start,p.stop,instant))return p.title;return cobraGuideMessage(channel);}
// COBRA-REPLACE ensureCobraPreviewSelection
  private void ensureCobraPreviewSelection(ArrayList<Channel> channels){
    if(channels==null||channels.isEmpty())return;
    if(mGuidePreviewChannel!=null){Channel updated=findChannel(mGuidePreviewChannel.id);if(updated!=null&&updated.primaryUrl.equals(mGuidePreviewChannel.primaryUrl))return;stopCobraPreviewPlayerOnly();mGuidePreviewChannel=null;}
    Channel recent=cobraLastGoodChannel(channels);mGuidePreviewChannel=recent==null?channels.get(0):recent;mGuidePreviewKey=cobraChannelKey(mGuidePreviewChannel);mGuidePreviewArmed=false;
  }

// COBRA-REPLACE showCobraViewModeMenu
  private void showCobraViewModeMenu(){
    LinearLayout body=cobraOpenSheet("View mode","One live session • layouts adapt to your window","view-mode");
    String[] modes={"mobile","grid","compact","cards","focus"},labels={"Mobile · touch-first browsing","TV Guide · channel timeline","Compact · dense channel list","Cards · programme cards","Focus · larger video with channel browser"};
    for(int i=0;i<modes.length;i++){final String mode=modes[i];cobraSheetAction(body,"▤",labels[i],false,()->{if(!"mobile".equals(mode))mPrefs.edit().putString(GUIDE_VIEW_MODE,mode).apply();showCobraGuideExperience(mode,false);});}
  }

// COBRA-REPLACE showGuideOverlay
  private void showGuideOverlay(){if(mPlayerOverlay!=null)showCobraPlayerChannels();else showGuide();}
