// COBRA-APPEND
  /** A tile is an identity, not an array index. Reflow never replaces its player or TextureView. */
  private final class CobraTile {
    final Channel channel;final FrameLayout root;final TextureView texture;final TextView notice;
    ExoPlayer player;String error="";long lastFrames=-1,lastFrameAt;
    CobraTile(Channel channel,ExoPlayer carried,TextureView carriedTexture){
      this.channel=channel;root=new FrameLayout(InfinityLiveActivity.this);root.setBackgroundColor(Color.BLACK);
      root.setFocusable(true);root.setClickable(true);root.setLongClickable(true);root.setContentDescription(channel.name);
      texture=carriedTexture==null?new TextureView(InfinityLiveActivity.this):carriedTexture;
      android.view.ViewParent parent=texture.getParent();if(parent instanceof android.view.ViewGroup)((android.view.ViewGroup)parent).removeView(texture);
      root.addView(texture,new FrameLayout.LayoutParams(-1,-1));
      notice=cobraText("",Color.WHITE,12,Gravity.CENTER);notice.setBackgroundColor(Color.argb(170,0,0,0));notice.setVisibility(View.GONE);notice.setPadding(dp(6),dp(4),dp(6),dp(4));
      root.addView(notice,new FrameLayout.LayoutParams(-1,-2,Gravity.BOTTOM));
      root.setOnClickListener(v->{int i=mCobraTiles.indexOf(this);if(i>=0)setMultiAudio(i);});
      root.setOnLongClickListener(v->{int i=mCobraTiles.indexOf(this);if(i>=0)showCobraMultiTileActions(i);return true;});
      root.setOnKeyListener((v,key,event)->{if(key==KeyEvent.KEYCODE_MENU&&event.getAction()==KeyEvent.ACTION_DOWN){int i=mCobraTiles.indexOf(this);if(i>=0)showCobraMultiTileActions(i);return true;}return false;});
      texture.addOnLayoutChangeListener((v,l,t,r,b,ol,ot,or,ob)->{if(r-l!=or-ol||b-t!=ob-ot)applyCobraVideoFit(texture,player,0);});
      if(carried!=null){player=carried;if(carriedTexture==null)player.setVideoTextureView(texture);}
      else try{mCobraCreatingMulti=true;player=buildPlayer(texture,channel,false);player.setMediaItem(mediaItem(channel.primaryUrl));player.prepare();startCobraPlayer(player);}
      catch(Exception failure){error=failure.getClass().getSimpleName();notice.setText("Unable to start this screen • hold for details");notice.setVisibility(View.VISIBLE);}
      finally{mCobraCreatingMulti=false;}
    }
  }
  private final ArrayList<CobraTile> mCobraTiles=new ArrayList<>();
  private boolean mCobraCreatingMulti;
  private CobraTile cobraTileFor(ExoPlayer player){for(CobraTile tile:mCobraTiles)if(tile.player==player)return tile;return null;}
  private void syncCobraMultiArrays(){
    int count=mCobraTiles.size();mMultiPlayers=new ExoPlayer[count];mMultiTextures=new TextureView[count];mMultiChannels=new Channel[count];
    for(int i=0;i<count;i++){CobraTile tile=mCobraTiles.get(i);mMultiPlayers[i]=tile.player;mMultiTextures[i]=tile.texture;mMultiChannels[i]=tile.channel;}
  }
  private void releaseCobraTile(CobraTile tile){
    if(tile.player!=null){mBackgroundResumePlayers.remove(tile.player);try{tile.player.release();}catch(Exception ignored){}tile.player=null;}
    android.view.ViewParent parent=tile.root.getParent();if(parent instanceof android.view.ViewGroup)((android.view.ViewGroup)parent).removeView(tile.root);
  }
  private void reconcileCobraTiles(List<Channel> channels){
    ArrayList<CobraTile> old=new ArrayList<>(mCobraTiles);ArrayList<String> oldIds=new ArrayList<>(),nextIds=new ArrayList<>();
    for(CobraTile tile:old)oldIds.add(tile.channel.id);for(Channel channel:channels)nextIds.add(channel.id);
    int[] keep=CobraCore.retained(oldIds,nextIds);
    String audio=old.isEmpty()?"":old.get(Math.max(0,Math.min(mAudioTile,old.size()-1))).channel.id;
    ArrayList<CobraTile> next=new ArrayList<>();
    for(int i=0;i<channels.size();i++){
      CobraTile tile=keep[i]>=0?old.get(keep[i]):new CobraTile(channels.get(i),null,null);
      next.add(tile);if(keep[i]<0)mMultiOverlay.addView(tile.root,new FrameLayout.LayoutParams(1,1));
    }
    for(CobraTile tile:old)if(!next.contains(tile))releaseCobraTile(tile);
    mCobraTiles.clear();mCobraTiles.addAll(next);syncCobraMultiArrays();
    int owner=nextIds.indexOf(audio);setMultiAudio(owner<0?0:owner);layoutCobraMultiTiles();
  }
  private void layoutCobraMultiTiles(){
    if(mMultiOverlay==null||mCobraTiles.isEmpty())return;
    int width=mMultiOverlay.getWidth(),height=mMultiOverlay.getHeight();if(width<=0||height<=0)return;
    if(mCobraMultiPicker!=null&&mCobraMultiPickerAdding){if(height>width)height=Math.round(height*.43f);else width=Math.round(width*.57f);}
    int count=mCobraTiles.size();boolean portrait=height>width;
    int columns=portrait&&width<dp(600)?1:2,rows=(count+columns-1)/columns;
    for(int i=0;i<count;i++){
      int row=i/columns,col=i%columns;int rowCount=Math.min(columns,count-row*columns);
      int left=width*col/rowCount,top=height*row/rows,right=width*(col+1)/rowCount,bottom=height*(row+1)/rows;
      FrameLayout.LayoutParams p=new FrameLayout.LayoutParams(Math.max(1,right-left-dp(2)),Math.max(1,bottom-top-dp(2)));p.leftMargin=left+dp(1);p.topMargin=top+dp(1);
      mCobraTiles.get(i).root.setLayoutParams(p);applyCobraVideoFit(mCobraTiles.get(i).texture,mCobraTiles.get(i).player,0);
    }
    if(mCobraMultiPicker!=null)mCobraMultiPicker.bringToFront();
  }
  private void showCobraTileDiagnostics(CobraTile tile){
    if(tile==null)return;String status=tile.error.isEmpty()?"No player error reported":tile.error;
    if(tile.player!=null){
      status+="\nState: "+tile.player.getPlaybackState()+" • playing: "+tile.player.isPlaying()+"\nBuffered: "+tile.player.getTotalBufferedDuration()+" ms";
      androidx.media3.exoplayer.DecoderCounters counters=tile.player.getVideoDecoderCounters();
      if(counters!=null)status+="\nRendered frames: "+counters.renderedOutputBufferCount+" • dropped: "+counters.droppedBufferCount;
      VideoSize size=tile.player.getVideoSize();status+="\nVideo: "+size.width+" × "+size.height;
    }
    int providerLimit=mPrefs.getInt("cobra_provider_limit:"+sourceIdForChannel(tile.channel),0);if(providerLimit>0)status+="\nProvider-reported connection limit: "+providerLimit;
    LinearLayout body=cobraOpenSheet("Screen playback",status+"\nProvider connection limits and device decoder capacity can limit simultaneous feeds.","tile-diagnostics");
    cobraSheetAction(body,"↻","Retry only this screen",false,()->{int index=mCobraTiles.indexOf(tile);if(index<0)return;releaseCobraTile(tile);CobraTile replacement=new CobraTile(tile.channel,null,null);mCobraTiles.set(index,replacement);mMultiOverlay.addView(replacement.root);syncCobraMultiArrays();setMultiAudio(mAudioTile);layoutCobraMultiTiles();});
  }

// COBRA-REPLACE rebuildCobraMultiPreservingSessions
  private void rebuildCobraMultiPreservingSessions(ArrayList<Channel> next,String releaseChannelId){if(mMultiOverlay!=null)reconcileCobraTiles(next);}
// COBRA-REPLACE openMultiView
  private void openMultiView(List<Channel> channels){
    if(channels==null||channels.size()<2||channels.size()>4){toast("Choose two to four channels");return;}
    if(mMultiOverlay!=null){reconcileCobraTiles(channels);return;}
    closeCobraSheet();closePlayerSettingsDrawer();closeCobraMultiPicker(true);clearCobraPlayerLockState(false);
    ExoPlayer carried=null;TextureView carriedTexture=null;Channel carriedChannel=null;
    if(mPlayer!=null&&mPlaying!=null&&channels.get(0).id.equals(mPlaying.id)){
      carried=mPlayer;carriedTexture=mPlayerTexture;carriedChannel=mPlaying;mPlayer=null;
      android.view.ViewParent parent=carriedTexture==null?null:carriedTexture.getParent();if(parent instanceof android.view.ViewGroup)((android.view.ViewGroup)parent).removeView(carriedTexture);
    }
    mReflowingMulti=true;closePlayer();mReflowingMulti=false;
    stopCobraPreview(); // Never leave a hidden third decoder behind the visible Multi-View tiles.
    mMultiOverlay=new FrameLayout(this);mMultiOverlay.setBackgroundColor(Color.BLACK);mMultiOverlay.setTag("cobra_stable_multiview");
    ((FrameLayout)getWindow().getDecorView()).addView(mMultiOverlay,new FrameLayout.LayoutParams(-1,-1));
    mMultiOverlay.addOnLayoutChangeListener((v,l,t,r,b,ol,ot,or,ob)->{if(r-l!=or-ol||b-t!=ob-ot)layoutCobraMultiTiles();});
    if(carried!=null){CobraTile first=new CobraTile(carriedChannel,carried,carriedTexture);mCobraTiles.add(first);mMultiOverlay.addView(first.root,new FrameLayout.LayoutParams(1,1));}
    reconcileCobraTiles(channels);configureCobraPip(false);
    if(mDeviceBridge!=null)mDeviceBridge.onPlaybackChanged("multiview-start");
  }
// COBRA-REPLACE createMultiTile
  private FrameLayout createMultiTile(int index){return mCobraTiles.get(index).root;}
// COBRA-REPLACE setMultiAudio
  private void setMultiAudio(int index){
    if(index<0||index>=mCobraTiles.size())return;mAudioTile=index;
    for(int i=0;i<mCobraTiles.size();i++){
      CobraTile tile=mCobraTiles.get(i);if(tile.player!=null)tile.player.setVolume(i==index?1f:0f);
      tile.root.setForeground(i==index?surface(Color.TRANSPARENT,0,cobraAlpha(cobraThemeColor("accent",mTheme.accent),175),1):null);
      tile.root.setContentDescription(tile.channel.name+(i==index?". Audio selected":". Muted")+". Hold for screen actions.");
    }
  }
// COBRA-REPLACE multiToSingle
  private void multiToSingle(){
    if(mCobraTiles.isEmpty())return;int index=Math.max(0,Math.min(mAudioTile,mCobraTiles.size()-1));
    CobraTile selected=mCobraTiles.remove(index);ExoPlayer session=selected.player;selected.player=null;
    mReflowingMulti=true;releaseMulti();mReflowingMulti=false;
    if(session==null){playChannel(selected.channel);return;}
    mPlaying=selected.channel;mPlayingIndex=mChannels.indexOf(mPlaying);openPlayerOverlay(mPlaying);mPlayer=session;
    session.setVideoTextureView(mPlayerTexture);session.setVolume(1f);applyCobraAspectTransform();updateCobraPlayerInformation();configureCobraPip(true);
  }
// COBRA-REPLACE removeSelectedMultiTile
  private void removeSelectedMultiTile(){removeCobraMultiTileClean(mAudioTile);}
// COBRA-REPLACE releaseMulti
  private void releaseMulti(){
    closeCobraMultiPicker(true);closeCobraSheet();
    for(CobraTile tile:new ArrayList<>(mCobraTiles))releaseCobraTile(tile);mCobraTiles.clear();
    mMultiPlayers=null;mMultiTextures=null;mMultiChannels=null;mMultiChrome=null;
    if(mMultiOverlay!=null){android.view.ViewParent parent=mMultiOverlay.getParent();if(parent instanceof android.view.ViewGroup)((android.view.ViewGroup)parent).removeView(mMultiOverlay);}
    mMultiOverlay=null;mMain.removeCallbacks(mHideMultiChrome);configureCobraPip(false);
    if(mDeviceBridge!=null)mDeviceBridge.onPlaybackChanged("multiview-stop");
    if(!mReflowingMulti)rebuildCobraShellIfNeeded();
  }
// COBRA-REPLACE showCobraMultiTileActions
  private void showCobraMultiTileActions(int index){
    if(index<0||index>=mCobraTiles.size())return;CobraTile tile=mCobraTiles.get(index);
    LinearLayout body=cobraOpenSheet(tile.channel.name,"Multi-View • screen "+(index+1),"multiview-actions");
    cobraSheetAction(body,"♪","Use audio here",false,()->setMultiAudio(mCobraTiles.indexOf(tile)));
    cobraSheetAction(body,"⇄","Change channel",false,()->{mCobraMultiReplaceIndex=mCobraTiles.indexOf(tile);showCobraMultiPicker(true);});
    if(mCobraTiles.size()<4)cobraSheetAction(body,"+","Add screen",false,()->{mCobraMultiReplaceIndex=-1;showCobraMultiPicker(true);});
    cobraSheetAction(body,"⛶","Fullscreen this",false,()->{setMultiAudio(mCobraTiles.indexOf(tile));multiToSingle();});
    cobraSheetAction(body,"ⓘ","Playback status / retry",false,()->showCobraTileDiagnostics(tile));
    cobraSheetAction(body,"−","Remove screen",true,()->removeCobraMultiTileClean(mCobraTiles.indexOf(tile)));
    cobraSheetAction(body,"×","Close Multi-View",true,()->{releaseMulti();showCobraPrimaryView();});
  }
// COBRA-REPLACE showCobraMultiPicker
  private void showCobraMultiPicker(boolean adding){
    if(mCobraPlayerLocked)return;
    FrameLayout parent=adding?mMultiOverlay:mPlayerOverlay;if(parent==null)return;
    int replace=mCobraMultiReplaceIndex;closeCobraMultiPicker(false);mCobraMultiReplaceIndex=replace;mCobraMultiPickerAdding=adding;
    FrameLayout panel=new FrameLayout(this);mCobraMultiPicker=panel;panel.setBackground(surface(cobraPanelColor(),20,cobraThemeColor("line",mTheme.line),1));
    LinearLayout body=new LinearLayout(this);body.setOrientation(LinearLayout.VERTICAL);body.setPadding(dp(12),dp(12),dp(12),dp(12));panel.addView(body,new FrameLayout.LayoutParams(-1,-1));
    cobraSheetHeading(body,replace>=0?"Change screen":adding?"Add screen":"Choose a second screen","Playback continues while you browse",()->closeCobraMultiPicker(false));
    LinearLayout filters=new LinearLayout(this);String[] keys={"FAVORITES","RECENT","ALL","CATEGORIES"},labels={"Favorites","Recent","All","Categories"};
    for(int i=0;i<keys.length;i++){final String filter=keys[i];Button button=cobraTextAction(labels[i],false);button.setTextSize(11);button.setOnClickListener(v->renderCobraMultiPicker(filter));filters.addView(button,new LinearLayout.LayoutParams(0,dp(48),1));}
    body.addView(filters,new LinearLayout.LayoutParams(-1,dp(48)));
    android.widget.ListView list=new android.widget.ListView(this);list.setTag("cobra_multi_picker_list");list.setDivider(null);list.setFastScrollEnabled(true);body.addView(list,new LinearLayout.LayoutParams(-1,0,1));
    boolean portrait=cobraWindowHeight()>cobraWindowWidth();FrameLayout.LayoutParams p=new FrameLayout.LayoutParams(portrait?-1:Math.round(cobraWindowWidth()*.43f),portrait?Math.round(cobraWindowHeight()*.57f):-1,portrait?Gravity.BOTTOM:Gravity.RIGHT);parent.addView(panel,p);
    if(mPlayerChrome!=null)mPlayerChrome.setVisibility(View.GONE);
    if(adding)layoutCobraMultiTiles();else layoutCobraPlayerViewport();renderCobraMultiPicker("CATEGORIES");
  }
// COBRA-REPLACE closeCobraMultiPicker
  private boolean closeCobraMultiPicker(boolean keepVideoDocked){
    if(mCobraMultiPicker==null)return false;android.view.ViewParent parent=mCobraMultiPicker.getParent();if(parent instanceof android.view.ViewGroup)((android.view.ViewGroup)parent).removeView(mCobraMultiPicker);
    mCobraMultiPicker=null;mCobraMultiPickerAdding=false;if(!keepVideoDocked)mCobraMultiReplaceIndex=-1;
    if(!keepVideoDocked){layoutCobraMultiTiles();layoutCobraPlayerViewport();showPlayerChromeTemporarily();}return true;
  }
// COBRA-REPLACE cobraMultiChannels
  private ArrayList<Channel> cobraMultiChannels(String filter){
    String category=filter!=null&&filter.startsWith("GROUP:")?filter.substring(6):filter==null?"ALL":filter;
    String search=mSearch;mSearch="";ArrayList<Channel> out;
    try{out=cobraVisibleGuideChannels(category,"");}finally{mSearch=search;}
    Set<String> open=new HashSet<>();for(CobraTile tile:mCobraTiles)open.add(tile.channel.id);if(mPlaying!=null)open.add(mPlaying.id);
    out.removeIf(channel->open.contains(channel.id));return out;
  }
