// @replace openPlayerOverlay
  private void openPlayerOverlay(Channel channel) {
    clearCobraPlayerLockState(false);mCobraPlayerUiWidth=-1;mCobraPlayerUiHeight=-1;
    mPlayerOverlay=new FrameLayout(this);mPlayerOverlay.setBackgroundColor(Color.BLACK);mPlayerOverlay.setFocusable(true);mPlayerOverlay.setFocusableInTouchMode(false);
    mPlayerTexture=new TextureView(this);mAspectMode=mPrefs.getInt(COBRA_ASPECT_MODE,0);mPlayerOverlay.addView(mPlayerTexture,new FrameLayout.LayoutParams(-1,-1));
    mPlayerOverlay.setOnClickListener(v->{if(mCobraPlayerLocked)showCobraPlayerUnlockAffordance();else if(!closeCobraActionSheet()&&!closeCobraPlayerDrawer()&&!closeCobraMultiPicker(false))togglePlayerChrome();});
    mPlayerOverlay.setOnLongClickListener(v->{if(!mCobraPlayerLocked)showCobraPlayerDrawer();else showCobraPlayerUnlockAffordance();return true;});
    mPlayerOverlay.setOnKeyListener((v,code,event)->{if(event.getAction()!=KeyEvent.ACTION_DOWN)return false;if(mCobraPlayerLocked){showCobraPlayerUnlockAffordance();return true;}if(code==KeyEvent.KEYCODE_DPAD_CENTER||code==KeyEvent.KEYCODE_ENTER){showPlayerChromeTemporarily();return true;}if(code==KeyEvent.KEYCODE_MENU){showCobraPlayerDrawer();return true;}return false;});
    mPlayerOverlay.addOnLayoutChangeListener((v,l,t,r,b,ol,ot,or,ob)->{if(r-l!=mCobraPlayerUiWidth||b-t!=mCobraPlayerUiHeight){cobraBuildPlayerChrome();cobraLayoutPlayerPanels();}});
    ((FrameLayout)getWindow().getDecorView()).addView(mPlayerOverlay,new FrameLayout.LayoutParams(-1,-1));
    cobraBuildPlayerChrome();mPlayerOverlay.post(()->{cobraBuildPlayerChrome();cobraLayoutPlayerPanels();});scheduleChromeHide();
  }
// @replace showPlayerSettingsDrawer
  private void showPlayerSettingsDrawer() {
    if(mPlayerOverlay==null||mCobraPlayerLocked)return;
    closeCobraPlayerDrawer();if("player-settings".equals(mCobraSheetKind)){closeCobraActionSheet();return;}
    LinearLayout rows=cobraOpenSheet("Player settings","Viewing preferences and recording","player-settings");
    rows.addView(cobraSheetRow("record",mRecordingSession.isEmpty()?"Record now":"Stop recording",null,false,true,()->{if(mPlaying!=null)toggleRecording(mPlaying);}));
    rows.addView(cobraSheetRow("cc","Audio & subtitles",null,false,true,()->showTrackChooser()));
    rows.addView(cobraSheetRow("aspect","Aspect / Display",cobraAspectLabel(mAspectMode),false,true,()->showCobraAspectPicker()));
    rows.addView(cobraSheetRow("cast","Cast / Route",null,false,true,()->openCastSettings()));
    rows.addView(cobraSheetRow("source","Manage sources","Leaves this player",false,true,()->{closePlayer();stopCobraPreview();mCobraInternalScreen="internal";showSources();}));
    rows.addView(cobraSheetRow("close","Close player","Stop playback and return to browsing",true,true,()->{mCobraPreviewAutoplayAllowed=false;closePlayer();showCobraPrimaryView();cobraUpdatePlaybackLabels();}));
  }
// @replace closePlayerSettingsDrawer
  private boolean closePlayerSettingsDrawer() {return "player-settings".equals(mCobraSheetKind)&&closeCobraActionSheet();}
// @replace showTrackChooser
  private void showTrackChooser() {
    final ExoPlayer player=mPlayer;if(player==null||mCobraPlayerLocked)return;
    LinearLayout rows=cobraOpenSheet("Audio & subtitles","Available tracks in this stream","tracks");
    rows.addView(cobraSheetRow("cc","Subtitles off",null,false,true,()->{if(mPlayer==player)player.setTrackSelectionParameters(player.getTrackSelectionParameters().buildUpon().setTrackTypeDisabled(C.TRACK_TYPE_TEXT,true).build());}));
    int count=0;for(Tracks.Group group:player.getCurrentTracks().getGroups()) {
      if(group.getType()!=C.TRACK_TYPE_AUDIO&&group.getType()!=C.TRACK_TYPE_TEXT)continue;
      for(int i=0;i<group.length;i++)if(group.isTrackSupported(i)){
        final int index=i;Format f=group.getTrackFormat(i);boolean audio=group.getType()==C.TRACK_TYPE_AUDIO;
        String label=f.label!=null?f.label:f.language!=null?f.language:"Track "+(i+1);
        rows.addView(cobraSheetRow(audio?"audio":"cc",label,(audio?"Audio":"Subtitles")+(group.isTrackSelected(i)?" • selected":""),false,true,()->{
          if(mPlayer!=player)return;player.setTrackSelectionParameters(player.getTrackSelectionParameters().buildUpon().setTrackTypeDisabled(group.getType(),false).setOverrideForType(new TrackSelectionOverride(group.getMediaTrackGroup(),index)).build());}));count++;
      }
    }
    if(count==0){TextView label=cobraText("No additional audio or subtitle tracks supplied",0xffb7c6d8,13);label.setPadding(dp(14),dp(12),dp(14),dp(12));rows.addView(label);}
  }
// @replace showCobraAspectPicker
  private void showCobraAspectPicker() {
    if(mPlayer==null||mCobraPlayerLocked)return;
    LinearLayout rows=cobraOpenSheet("Aspect / Display","Best Fit preserves the source proportions","aspect");
    for(int i=0;i<12;i++){final int mode=i;rows.addView(cobraSheetRow("aspect",cobraAspectLabel(i),mAspectMode==i?"Selected":null,false,true,()->{
      mAspectMode=mode;mPrefs.edit().putInt(COBRA_ASPECT_MODE,mode).apply();applyCobraAspectTransform();if(mode==11)showCobraCustomAspectEditor();}));}
  }
// @replace showCobraCustomAspectEditor
  private void showCobraCustomAspectEditor() {
    if(mPlayerTexture==null||mCobraPlayerLocked)return;
    LinearLayout rows=cobraOpenSheet("Custom display","Adjust width and height independently","custom-aspect");
    String[] labels={"Width","Height"},keys={COBRA_CUSTOM_ASPECT_X,COBRA_CUSTOM_ASPECT_Y};
    for(int i=0;i<2;i++){
      final String key=keys[i],label=labels[i];TextView title=cobraText(label,Color.WHITE,14);title.setPadding(dp(12),dp(12),dp(12),dp(4));rows.addView(title);
      android.widget.SeekBar slider=new android.widget.SeekBar(this);slider.setMax(125);slider.setProgress(Math.round((mPrefs.getFloat(key,1f)-.55f)*100));slider.setPadding(dp(16),0,dp(16),0);slider.setContentDescription(label+" percent");
      slider.setOnSeekBarChangeListener(new android.widget.SeekBar.OnSeekBarChangeListener(){
        public void onProgressChanged(android.widget.SeekBar bar,int value,boolean user){float factor=(55+value)/100f;title.setText(label+"  "+(55+value)+"%");if(user){mAspectMode=11;mPrefs.edit().putInt(COBRA_ASPECT_MODE,11).putFloat(key,factor).apply();applyCobraAspectTransform();}}
        public void onStartTrackingTouch(android.widget.SeekBar bar){}public void onStopTrackingTouch(android.widget.SeekBar bar){}
      });title.setText(label+"  "+(55+slider.getProgress())+"%");rows.addView(slider,new LinearLayout.LayoutParams(-1,dp(52)));
    }
    rows.addView(cobraSheetRow("recent","Reset width & height","Return both to 100%",false,true,()->{mPrefs.edit().putFloat(COBRA_CUSTOM_ASPECT_X,1f).putFloat(COBRA_CUSTOM_ASPECT_Y,1f).apply();applyCobraAspectTransform();showCobraCustomAspectEditor();}));
  }
// @replace scheduleChromeHide
  private void scheduleChromeHide() {
    mMain.removeCallbacks(mHideChrome);
    if(mPlayerChrome!=null&&!mCobraPlayerLocked&&!mInPictureInPicture&&mCobraActionSheet==null&&mCobraPlayerDrawer==null&&mCobraMultiPicker==null)mMain.postDelayed(mHideChrome,3500L);
  }
// @replace showPlayerChromeTemporarily
  private void showPlayerChromeTemporarily() {
    if(mPlayerChrome==null||mCobraPlayerLocked||mInPictureInPicture||mCobraPlayerDrawer!=null||mCobraMultiPicker!=null)return;
    mPlayerChrome.setVisibility(View.VISIBLE);mPlayerChrome.setAlpha(1f);scheduleChromeHide();
  }
// @replace togglePlayerChrome
  private void togglePlayerChrome() {
    if(mPlayerChrome==null||mCobraPlayerLocked||mInPictureInPicture)return;
    if(mPlayerChrome.getVisibility()==View.VISIBLE){mMain.removeCallbacks(mHideChrome);mPlayerChrome.setVisibility(View.GONE);}
    else showPlayerChromeTemporarily();
  }
// @replace ensureCobraPlayerLockOverlay
  private void ensureCobraPlayerLockOverlay() {
    if(mPlayerOverlay==null)return;if(mCobraPlayerLockOverlay!=null){mCobraPlayerLockOverlay.bringToFront();return;}
    FrameLayout guard=new FrameLayout(this);guard.setClickable(true);guard.setFocusable(true);guard.setFocusableInTouchMode(true);guard.setBackgroundColor(Color.TRANSPARENT);guard.setContentDescription("Player controls locked");mCobraPlayerLockOverlay=guard;
    Button unlock=cobraTextButton("Unlock controls",true,()->unlockCobraPlayer());unlock.setTag("cobra_player_unlock");unlock.setBackground(surface(0xe5202e40,24,0xff57738d,1));mCobraPlayerUnlockButton=unlock;
    FrameLayout.LayoutParams p=new FrameLayout.LayoutParams(dp(190),dp(52),Gravity.BOTTOM|Gravity.CENTER_HORIZONTAL);p.bottomMargin=dp(38);guard.addView(unlock,p);
    guard.setOnClickListener(v->showCobraPlayerUnlockAffordance());guard.setOnKeyListener((v,key,event)->{if(event.getAction()==KeyEvent.ACTION_DOWN){showCobraPlayerUnlockAffordance();return true;}return false;});
    mPlayerOverlay.addView(guard,new FrameLayout.LayoutParams(-1,-1));guard.bringToFront();guard.requestFocus();
  }
// @replace showCobraPlayerUnlockAffordance
  private void showCobraPlayerUnlockAffordance() {
    if(!mCobraPlayerLocked||mCobraPlayerUnlockButton==null||mInPictureInPicture)return;
    mCobraPlayerUnlockButton.animate().cancel();mCobraPlayerUnlockButton.setVisibility(View.VISIBLE);mCobraPlayerUnlockButton.setAlpha(0f);mCobraPlayerUnlockButton.setScaleX(.96f);mCobraPlayerUnlockButton.setScaleY(.96f);
    mCobraPlayerUnlockButton.animate().alpha(1f).scaleX(1f).scaleY(1f).setDuration(140).start();mCobraPlayerUnlockButton.requestFocus();mMain.removeCallbacks(mHideCobraUnlockButton);mMain.postDelayed(mHideCobraUnlockButton,3000L);
  }
// @replace lockCobraPlayer
  private void lockCobraPlayer() {
    if(mPlayerOverlay==null)return;closeCobraActionSheet();closeCobraPlayerDrawer();closeCobraMultiPicker(false);
    mCobraPlayerLocked=true;mMain.removeCallbacks(mHideChrome);if(mPlayerChrome!=null)mPlayerChrome.setVisibility(View.GONE);ensureCobraPlayerLockOverlay();showCobraPlayerUnlockAffordance();
  }
// @replace showCobraChannelActions
  private void showCobraChannelActions(Channel channel) {
    if(channel==null)return;LinearLayout rows=cobraOpenSheet(channel.name,"Channel actions","channel");boolean dark=cobraSheetIsDark();
    rows.addView(cobraSheetRow("favorite",mFavorites.contains(channel.id)?"Remove from favorites":"Add to favorites",null,false,dark,()->{toggleFavorite(channel);cobraRefreshProgrammeLabels();if(mCobraGuideAdapter!=null)mCobraGuideAdapter.notifyDataSetChanged();}));
    rows.addView(cobraSheetRow("record","Schedule recording",null,false,dark,()->showCobraScheduleRecording(channel)));
    rows.addView(cobraSheetRow("add","Add to group",null,false,dark,()->showCobraAddToGroup(channel)));
    rows.addView(cobraSheetRow("source","Share to a friend",null,false,dark,()->shareCobraChannel(channel)));
    rows.addView(cobraSheetRow("guide","View channel schedule",null,false,dark,()->showProgramGuide(channel)));
    rows.addView(cobraSheetRow("remove","Hide channel","Restore from Live TV settings",true,dark,()->hideCobraChannel(channel)));
  }
// @append
  @Override public boolean dispatchKeyEvent(KeyEvent event) {
    if(mCobraPlayerLocked&&mPlayerOverlay!=null&&!mInPictureInPicture){
      int code=event.getKeyCode();boolean system=code==KeyEvent.KEYCODE_VOLUME_UP||code==KeyEvent.KEYCODE_VOLUME_DOWN||code==KeyEvent.KEYCODE_VOLUME_MUTE||code==KeyEvent.KEYCODE_POWER;
      boolean unlock=getCurrentFocus()==mCobraPlayerUnlockButton&&mCobraPlayerUnlockButton!=null&&mCobraPlayerUnlockButton.getVisibility()==View.VISIBLE&&(code==KeyEvent.KEYCODE_DPAD_CENTER||code==KeyEvent.KEYCODE_ENTER);
      if(!system&&!unlock){if(event.getAction()==KeyEvent.ACTION_DOWN)showCobraPlayerUnlockAffordance();return true;}
    }
    return super.dispatchKeyEvent(event);
  }

  private void cobraBuildPlayerChrome() {
    if(mPlayerOverlay==null)return;
    int width=mPlayerOverlay.getWidth(),height=mPlayerOverlay.getHeight();if(width<=0||height<=0)return;
    boolean visible=mPlayerChrome==null||mPlayerChrome.getVisibility()==View.VISIBLE;boolean shortScreen=height<dp(340);
    mCobraPlayerUiWidth=width;mCobraPlayerUiHeight=height;
    if(mPlayerChrome!=null)mPlayerOverlay.removeView(mPlayerChrome);
    LinearLayout chrome=new LinearLayout(this);mPlayerChrome=chrome;chrome.setTag("cobra_player_refined_chrome");chrome.setOrientation(LinearLayout.VERTICAL);
    int left=dp(12),right=dp(12),top=dp(shortScreen?4:12),bottom=dp(shortScreen?8:16);
    if(Build.VERSION.SDK_INT>=23&&mPlayerOverlay.getRootWindowInsets()!=null){android.view.WindowInsets insets=mPlayerOverlay.getRootWindowInsets();left+=insets.getSystemWindowInsetLeft();right+=insets.getSystemWindowInsetRight();top+=insets.getSystemWindowInsetTop();bottom+=insets.getSystemWindowInsetBottom();}
    LinearLayout header=new LinearLayout(this);header.setGravity(Gravity.CENTER_VERTICAL);header.setPadding(left,top,right,dp(6));header.setBackground(new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,new int[]{0xcf000000,0x65000000,Color.TRANSPARENT}));
    header.addView(cobraIcon("back","Return to preview",true,v->closeFullscreenToCobraView()),new LinearLayout.LayoutParams(dp(48),dp(48)));
    TextView title=cobraText(mPlaying==null?"Cobra Live":mPlaying.name,Color.WHITE,15);title.setTag("cobra_player_channel_title");title.setTypeface(Typeface.create("sans-serif-medium",Typeface.NORMAL));title.setSingleLine(true);title.setPadding(dp(8),0,dp(8),0);header.addView(title,new LinearLayout.LayoutParams(0,dp(48),1));
    header.addView(cobraIcon(mPlaying!=null&&mFavorites.contains(mPlaying.id)?"favorite_on":"favorite","Favorite",true,v->{if(mPlaying!=null){toggleFavorite(mPlaying);((CobraIconButton)v).icon(mFavorites.contains(mPlaying.id)?"favorite_on":"favorite");}}),new LinearLayout.LayoutParams(dp(48),dp(48)));
    header.addView(cobraIcon("lock","Lock controls",true,v->lockCobraPlayer()),new LinearLayout.LayoutParams(dp(48),dp(48)));chrome.addView(header,new LinearLayout.LayoutParams(-1,-2));
    chrome.addView(new View(this),new LinearLayout.LayoutParams(1,0,1));
    LinearLayout transport=new LinearLayout(this);transport.setGravity(Gravity.CENTER);transport.setPadding(dp(16),0,dp(16),0);
    CobraIconButton prev=cobraIcon("prev","Previous channel",true,v->stepChannel(-1)),pause=cobraIcon("pause","Pause",true,v->toggleCobraPlayerPlayPause()),next=cobraIcon("next","Next channel",true,v->stepChannel(1));pause.setTag("cobra_player_play_pause");pause.setBackground(surface(0x87000000,40,0x55ffffff,1));
    transport.addView(prev,new LinearLayout.LayoutParams(dp(56),dp(56)));LinearLayout.LayoutParams pp=new LinearLayout.LayoutParams(dp(shortScreen?56:72),dp(shortScreen?56:72));pp.leftMargin=dp(24);pp.rightMargin=dp(24);transport.addView(pause,pp);transport.addView(next,new LinearLayout.LayoutParams(dp(56),dp(56)));chrome.addView(transport,new LinearLayout.LayoutParams(-1,dp(shortScreen?60:76)));
    chrome.addView(new View(this),new LinearLayout.LayoutParams(1,0,1));
    LinearLayout footer=new LinearLayout(this);footer.setOrientation(LinearLayout.VERTICAL);footer.setPadding(left+dp(4),dp(shortScreen?8:24),right+dp(4),bottom);footer.setBackground(new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,new int[]{Color.TRANSPARENT,0xba000000,0xe6000000}));
    LinearLayout programLine=new LinearLayout(this);programLine.setGravity(Gravity.CENTER_VERTICAL);mCobraPlayerProgram=cobraText("",Color.WHITE,height>width?19:21);mCobraPlayerProgram.setTypeface(Typeface.create("sans-serif-medium",Typeface.NORMAL));mCobraPlayerProgram.setSingleLine(true);programLine.addView(mCobraPlayerProgram,new LinearLayout.LayoutParams(0,dp(30),1));
    TextView state=cobraText("CONNECTING",0xff7ce2ff,10);state.setTag("player_state");state.setGravity(Gravity.RIGHT|Gravity.CENTER_VERTICAL);programLine.addView(state,new LinearLayout.LayoutParams(dp(82),dp(30)));footer.addView(programLine,new LinearLayout.LayoutParams(-1,dp(30)));
    mCobraPlayerSchedule=cobraText("",0xffd6e0e9,12);mCobraPlayerSchedule.setSingleLine(true);footer.addView(mCobraPlayerSchedule,new LinearLayout.LayoutParams(-1,dp(22)));
    mCobraPlayerUpcoming=cobraText("",0xffaabccc,11);mCobraPlayerUpcoming.setSingleLine(true);if(shortScreen)mCobraPlayerUpcoming.setVisibility(View.GONE);if(height<dp(280))mCobraPlayerSchedule.setVisibility(View.GONE);footer.addView(mCobraPlayerUpcoming,new LinearLayout.LayoutParams(-1,dp(20)));
    mCobraPlayerProgramProgress=cobraProgress(true);LinearLayout.LayoutParams progress=new LinearLayout.LayoutParams(-1,dp(3));progress.topMargin=dp(8);progress.bottomMargin=dp(8);footer.addView(mCobraPlayerProgramProgress,progress);
    LinearLayout tools=new LinearLayout(this);String[] glyphs={"guide","aspect","multi","more"},labels={"Channels","Display","Multi-View","More"};
    for(int i=0;i<4;i++){final int action=i;CobraIconButton b=cobraIcon(glyphs[i],labels[i],true,v->{if(action==0)showCobraPlayerDrawer();else if(action==1)showCobraAspectPicker();else if(action==2)beginMultiView();else showPlayerSettingsDrawer();});b.caption(labels[i]);tools.addView(b,new LinearLayout.LayoutParams(0,dp(52),1));}
    footer.addView(tools,new LinearLayout.LayoutParams(-1,dp(52)));chrome.addView(footer,new LinearLayout.LayoutParams(-1,-2));mPlayerOverlay.addView(chrome,new FrameLayout.LayoutParams(-1,-1));
    chrome.setVisibility(visible&&!mCobraPlayerLocked&&!mInPictureInPicture&&mCobraPlayerDrawer==null&&mCobraMultiPicker==null?View.VISIBLE:View.GONE);
    if(mCobraPlayerDrawer!=null)mCobraPlayerDrawer.bringToFront();if(mCobraMultiPicker!=null)mCobraMultiPicker.bringToFront();if(mCobraActionSheet!=null)mCobraActionSheet.bringToFront();if(mCobraPlayerLockOverlay!=null)mCobraPlayerLockOverlay.bringToFront();
    cobraRefreshProgrammeLabels();cobraUpdatePlaybackLabels();
  }

  private void showCobraPlayerDrawer() {
    if(mPlayerOverlay==null||mCobraPlayerLocked||mInPictureInPicture)return;
    if(closeCobraPlayerDrawer())return;closeCobraActionSheet();closeCobraMultiPicker(false);
    FrameLayout panel=new FrameLayout(this);mCobraPlayerDrawer=panel;panel.setTag("cobra_player_channel_drawer");panel.setBackgroundColor(0xff101924);panel.setElevation(dp(12));
    LinearLayout content=new LinearLayout(this);content.setOrientation(LinearLayout.VERTICAL);content.setPadding(dp(10),dp(8),dp(10),dp(14));panel.addView(content,new FrameLayout.LayoutParams(-1,-1));
    LinearLayout head=new LinearLayout(this);head.setGravity(Gravity.CENTER_VERTICAL);TextView title=cobraText("Live TV",Color.WHITE,18);title.setTypeface(Typeface.create("sans-serif-medium",Typeface.NORMAL));head.addView(title,new LinearLayout.LayoutParams(0,dp(48),1));head.addView(cobraIcon("close","Close channel drawer",true,v->closeCobraPlayerDrawer()),new LinearLayout.LayoutParams(dp(48),dp(48)));content.addView(head,new LinearLayout.LayoutParams(-1,dp(50)));
    LinearLayout tabs=new LinearLayout(this);String[] labels={"Favorites","Recent","All","Groups"},filters={"FAVORITES","RECENT","ALL","CATEGORIES"};for(int i=0;i<labels.length;i++){final String filter=filters[i];tabs.addView(cobraTextButton(labels[i],true,()->cobraRenderPlayerDrawer(filter)),new LinearLayout.LayoutParams(0,dp(48),1));}content.addView(tabs,new LinearLayout.LayoutParams(-1,dp(48)));
    mCobraPlayerDrawerList=new android.widget.ListView(this);mCobraPlayerDrawerList.setDividerHeight(0);mCobraPlayerDrawerList.setSelector(android.R.color.transparent);mCobraPlayerDrawerList.setFastScrollEnabled(true);content.addView(mCobraPlayerDrawerList,new LinearLayout.LayoutParams(-1,0,1));
    TextView hint=cobraText("Tap to tune • tap playing channel to expand • hold for schedule",0xff91a8be,11);hint.setGravity(Gravity.CENTER);hint.setMaxLines(2);content.addView(hint,new LinearLayout.LayoutParams(-1,dp(34)));
    mPlayerOverlay.addView(panel,new FrameLayout.LayoutParams(1,1));mPlayerChrome.setVisibility(View.GONE);cobraRenderPlayerDrawer(mCobraDrawerFilter);cobraLayoutPlayerPanels();
  }

  private boolean closeCobraPlayerDrawer() {
    if(mCobraPlayerDrawer==null)return false;if(mCobraPlayerDrawer.getParent() instanceof android.view.ViewGroup)((android.view.ViewGroup)mCobraPlayerDrawer.getParent()).removeView(mCobraPlayerDrawer);
    mCobraPlayerDrawer=null;mCobraPlayerDrawerList=null;cobraLayoutPlayerPanels();showPlayerChromeTemporarily();return true;
  }

  private void cobraRenderPlayerDrawer(String filter) {
    if(mCobraPlayerDrawerList==null)return;mCobraDrawerFilter=filter;final boolean groups="CATEGORIES".equals(filter);
    final ArrayList<String> names=new ArrayList<>();final ArrayList<Channel> channels=new ArrayList<>();
    if(groups){java.util.TreeSet<String> g=new java.util.TreeSet<>(String.CASE_INSENSITIVE_ORDER);for(Channel c:mChannels)if(cobraChannelAllowed(c)&&c.group!=null&&!c.group.isEmpty())g.add(c.group);names.addAll(g);}
    else if("RECENT".equals(filter)){for(String id:mRecents){Channel c=findChannel(id);if(cobraChannelAllowed(c))channels.add(c);}}
    else for(Channel c:mChannels)if(cobraChannelAllowed(c)&&(!"FAVORITES".equals(filter)||mFavorites.contains(c.id))&&(!filter.startsWith("GROUP:")||filter.substring(6).equals(c.group)))channels.add(c);
    cobraQueueVisibleGuides();
    mCobraPlayerDrawerList.setAdapter(new android.widget.BaseAdapter(){public int getCount(){return groups?names.size():channels.size();}public Object getItem(int p){return groups?names.get(p):channels.get(p);}public long getItemId(int p){return p;}
      public View getView(int p,View recycled,android.view.ViewGroup parent){Button row=recycled instanceof Button?(Button)recycled:cobraTextButton("",true,()->{});row.setTextSize(13);row.setPadding(dp(14),0,dp(12),0);row.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);row.setMaxLines(3);row.setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,dp(groups?52:82)));
        if(groups){String group=names.get(p);row.setText(group);row.setSelected(false);row.setOnClickListener(v->cobraRenderPlayerDrawer("GROUP:"+group));row.setOnLongClickListener(null);}
        else {Channel c=channels.get(p);GuideProgram now=cobraCurrentProgram(c),next=cobraNextProgram(c);row.setText(c.name+"\n"+(now==null?cobraGuideStatus(c):"Now  "+now.title)+(next==null?"":"\nNext  "+next.title));row.setSelected(mPlaying!=null&&mPlaying.id.equals(c.id));row.setOnClickListener(v->{if(mPlaying!=null&&mPlaying.id.equals(c.id)){closeCobraPlayerDrawer();return;}mPlaying=c;mPlayingIndex=mChannels.indexOf(c);mPlayingVodKey="";mPendingResumeMs=0;startSinglePlayer(c.primaryUrl);cobraBuildPlayerChrome();if(mCobraPlayerDrawerList!=null&&mCobraPlayerDrawerList.getAdapter() instanceof android.widget.BaseAdapter)((android.widget.BaseAdapter)mCobraPlayerDrawerList.getAdapter()).notifyDataSetChanged();});row.setOnLongClickListener(v->{showProgramGuide(c);return true;});}
        return row;}});
  }

  private void cobraLayoutPlayerPanels() {
    FrameLayout root=mMultiOverlay!=null?mMultiOverlay:mPlayerOverlay;if(root==null)return;int w=root.getWidth(),h=root.getHeight();if(w<=0||h<=0)return;
    View panel=mCobraMultiPicker!=null?mCobraMultiPicker:mCobraPlayerDrawer;boolean portrait=h>w;
    int pw=panel==null?0:portrait?w:Math.min(dp(430),(int)(w*.43f));int ph=panel==null?0:portrait?(int)(h*.56f):h;
    if(panel!=null)cobraPosition(panel,portrait?0:w-pw,portrait?h-ph:0,pw,ph);
    View video=mMultiOverlay!=null?mCobraMultiCanvas:mPlayerTexture;
    if(video!=null)cobraPosition(video,0,0,portrait?w:w-pw,portrait?h-ph:h);
    if(mPlayerTexture!=null&&mMultiOverlay==null)mPlayerTexture.post(()->applyCobraAspectTransform());
  }
