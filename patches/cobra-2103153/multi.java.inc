// @replace openMultiView
  private void openMultiView(List<Channel> channels) {
    if(channels==null||channels.size()<2||channels.size()>4||!isCobraAsyncAlive())return;
    if(mMultiOverlay==null){
      if(mPlayer!=null&&mPlaying!=null){mCobraCarryPlayer=mPlayer;mCobraCarryChannel=mPlaying;mPlayer=null;}
      stopCobraPreviewPlayerOnly();mReflowingMulti=true;closePlayer();mReflowingMulti=false;
      mMultiOverlay=new FrameLayout(this);mMultiOverlay.setBackgroundColor(Color.BLACK);mMultiChrome=null;
      mCobraMultiCanvas=new FrameLayout(this);mMultiOverlay.addView(mCobraMultiCanvas,new FrameLayout.LayoutParams(-1,-1));
      ((FrameLayout)getWindow().getDecorView()).addView(mMultiOverlay,new FrameLayout.LayoutParams(-1,-1));
      mCobraMultiCanvas.addOnLayoutChangeListener((v,l,t,r,b,ol,ot,or,ob)->{if(r-l!=or-ol||b-t!=ob-ot)cobraLayoutMultiTiles();});
    }
    rebuildCobraMultiPreservingSessions(new ArrayList<>(channels),"");
    configureCobraPip(false);cobraStartPresentationTicker();
    if(mDeviceBridge!=null)mDeviceBridge.onPlaybackChanged("multiview-start");
  }
// @replace rebuildCobraMultiPreservingSessions
  private void rebuildCobraMultiPreservingSessions(ArrayList<Channel> channels,String releaseChannelId) {
    if(mCobraMultiCanvas==null||channels==null||channels.size()<2||channels.size()>4)return;
    String owner=mMultiChannels!=null&&mAudioTile>=0&&mAudioTile<mMultiChannels.length?mMultiChannels[mAudioTile].id:channels.get(0).id;
    final Map<String,Channel> requested=new LinkedHashMap<>();for(Channel channel:channels)if(channel!=null)requested.put(channel.id,channel);
    if(requested.size()!=channels.size()){toast("That channel is already open");return;}
    if(releaseChannelId!=null&&!releaseChannelId.isEmpty()){
      // Release only the intentionally replaced/removed tile, before allocating its replacement.
      CobraVideoTile removed=mCobraTiles.take(releaseChannelId);if(removed!=null)cobraDisposeTile(removed);
    }
    mCobraCreatingMulti=true;
    try {mCobraTiles.reconcile(new ArrayList<>(requested.keySet()),key->cobraNewMultiTile(requested.get(key)),tile->cobraDisposeTile(tile));}
    catch(RuntimeException error){toast("Unable to add this screen; other screens were kept");}
    finally {mCobraCreatingMulti=false;}
    cobraSyncMultiArrays();int audio=0;
    for(int i=0;mMultiChannels!=null&&i<mMultiChannels.length;i++)if(mMultiChannels[i].id.equals(owner))audio=i;
    setMultiAudio(audio);cobraLayoutMultiTiles();cobraStartPresentationTicker();
  }
// @replace createMultiTile
  private FrameLayout createMultiTile(int index) {
    if(mMultiChannels==null||index<0||index>=mMultiChannels.length)return new FrameLayout(this);
    CobraVideoTile tile=mCobraTiles.get(mMultiChannels[index].id);return tile==null?new FrameLayout(this):tile.view;
  }
// @replace setMultiAudio
  private void setMultiAudio(int index) {
    if(mMultiPlayers==null||index<0||index>=mMultiPlayers.length)return;mAudioTile=index;
    for(int i=0;i<mMultiPlayers.length;i++)if(mMultiPlayers[i]!=null)mMultiPlayers[i].setVolume(i==index?1f:0f);
    for(CobraVideoTile tile:mCobraTiles.values()){
      boolean owner=mMultiChannels[index].id.equals(tile.channel.id);tile.audioRing.setVisibility(owner?View.VISIBLE:View.GONE);
      tile.view.setContentDescription(tile.channel.name+(owner?", audio selected":"")+", hold for channel actions");
    }
  }
// @replace releaseMulti
  private void releaseMulti() {
    closeCobraMultiPicker(true);if(mMultiOverlay!=null)closeCobraActionSheet();
    mCobraTiles.clear(tile->cobraDisposeTile(tile));mMultiPlayers=null;mMultiTextures=null;mMultiChannels=null;
    if(mMultiOverlay!=null&&mMultiOverlay.getParent() instanceof android.view.ViewGroup)((android.view.ViewGroup)mMultiOverlay.getParent()).removeView(mMultiOverlay);
    mMultiOverlay=null;mCobraMultiCanvas=null;mMultiChrome=null;mAudioTile=0;mCobraMultiReplaceIndex=-1;mMain.removeCallbacks(mHideMultiChrome);
    if(mCobraCarryPlayer!=null){cobraDisposePlayer(mCobraCarryPlayer);mCobraCarryPlayer=null;mCobraCarryChannel=null;}
    configureCobraPip(false);if(mDeviceBridge!=null&&isCobraAsyncAlive())mDeviceBridge.onPlaybackChanged("multiview-stop");
  }
// @replace multiToSingle
  private void multiToSingle() {
    if(mMultiChannels==null||mMultiChannels.length==0)return;
    int owner=Math.max(0,Math.min(mAudioTile,mMultiChannels.length-1));CobraVideoTile tile=mCobraTiles.take(mMultiChannels[owner].id);if(tile==null)return;
    ExoPlayer session=tile.player;Channel channel=tile.channel;tile.player=null;
    mReflowingMulti=true;releaseMulti();mReflowingMulti=false;
    mPlaying=channel;mPlayingIndex=mChannels.indexOf(channel);openPlayerOverlay(channel);mPlayer=session;
    if(session!=null){cobraAttachVideo(session,mPlayerTexture);session.setVolume(1f);}else startSinglePlayer(channel.primaryUrl);
    configureCobraPip(true);cobraUpdatePlaybackLabels();cobraStartPresentationTicker();
  }
// @replace showCobraMultiTileActions
  private void showCobraMultiTileActions(int index) {
    if(mMultiChannels==null||index<0||index>=mMultiChannels.length)return;
    String key=mMultiChannels[index].id;CobraVideoTile tile=mCobraTiles.get(key);if(tile==null)return;
    LinearLayout rows=cobraOpenSheet(tile.channel.name,"Multi-View • screen "+(index+1),"multi-tile");
    rows.addView(cobraSheetRow("audio","Use audio here",null,false,true,()->{int i=cobraMultiIndex(key);if(i>=0)setMultiAudio(i);}));
    rows.addView(cobraSheetRow("guide","Change channel",null,false,true,()->{mCobraMultiReplaceIndex=cobraMultiIndex(key);if(mCobraMultiReplaceIndex>=0)showCobraMultiPicker(true);}));
    if(mCobraTiles.keys().size()<4)rows.addView(cobraSheetRow("add","Add screen",null,false,true,()->{mCobraMultiReplaceIndex=-1;showCobraMultiPicker(true);}));
    rows.addView(cobraSheetRow("fullscreen","Watch fullscreen",null,false,true,()->{int i=cobraMultiIndex(key);if(i>=0){setMultiAudio(i);multiToSingle();}}));
    rows.addView(cobraSheetRow("recent","Retry this screen","Other videos will keep playing",false,true,()->cobraRetryMultiTile(key)));
    rows.addView(cobraSheetRow("source","Playback details","State, decoder and connection diagnostics",false,true,()->cobraShowMultiDiagnostics(key)));
    rows.addView(cobraSheetRow("remove","Remove screen",null,true,true,()->{int i=cobraMultiIndex(key);if(i>=0)removeCobraMultiTileClean(i);}));
    rows.addView(cobraSheetRow("close","Close Multi-View","Stops every screen",true,true,()->releaseMulti()));
  }
// @replace showCobraMultiPicker
  private void showCobraMultiPicker(boolean adding) {
    if(mCobraPlayerLocked)return;closeCobraPlayerDrawer();closeCobraActionSheet();closeCobraMultiPicker(false);
    FrameLayout parent=adding?mMultiOverlay:mPlayerOverlay;if(parent==null)return;mCobraMultiPickerAdding=adding;
    FrameLayout panel=new FrameLayout(this);mCobraMultiPicker=panel;panel.setBackgroundColor(0xff101924);panel.setElevation(dp(12));
    LinearLayout content=new LinearLayout(this);content.setOrientation(LinearLayout.VERTICAL);content.setPadding(dp(10),dp(8),dp(10),dp(14));panel.addView(content,new FrameLayout.LayoutParams(-1,-1));
    LinearLayout header=new LinearLayout(this);header.setGravity(Gravity.CENTER_VERTICAL);TextView title=cobraText(mCobraMultiReplaceIndex>=0?"Change channel":adding?"Add screen":"Pick a second screen",Color.WHITE,17);title.setTypeface(Typeface.create("sans-serif-medium",Typeface.NORMAL));header.addView(title,new LinearLayout.LayoutParams(0,dp(48),1));header.addView(cobraIcon("close","Close channel picker",true,v->closeCobraMultiPicker(false)),new LinearLayout.LayoutParams(dp(48),dp(48)));content.addView(header,new LinearLayout.LayoutParams(-1,dp(50)));
    LinearLayout filters=new LinearLayout(this);String[] labels={"Favorites","Recent","All","Groups"},keys={"FAVORITES","RECENT","ALL","CATEGORIES"};
    for(int i=0;i<labels.length;i++){final String filter=keys[i];filters.addView(cobraTextButton(labels[i],true,()->renderCobraMultiPicker(filter)),new LinearLayout.LayoutParams(0,dp(48),1));}content.addView(filters,new LinearLayout.LayoutParams(-1,dp(48)));
    android.widget.ListView list=new android.widget.ListView(this);list.setTag("cobra_multi_picker_list");list.setDividerHeight(0);list.setSelector(android.R.color.transparent);list.setFastScrollEnabled(true);content.addView(list,new LinearLayout.LayoutParams(-1,0,1));
    parent.addView(panel,new FrameLayout.LayoutParams(1,1));if(mPlayerChrome!=null)mPlayerChrome.setVisibility(View.GONE);cobraLayoutPlayerPanels();renderCobraMultiPicker("RECENT");
  }
// @replace closeCobraMultiPicker
  private boolean closeCobraMultiPicker(boolean keepVideoDocked) {
    if(mCobraMultiPicker==null)return false;
    if(mCobraMultiPicker.getParent() instanceof android.view.ViewGroup)((android.view.ViewGroup)mCobraMultiPicker.getParent()).removeView(mCobraMultiPicker);
    mCobraMultiPicker=null;mCobraMultiPickerAdding=false;
    if(!keepVideoDocked){mCobraMultiReplaceIndex=-1;cobraLayoutPlayerPanels();if(mPlayerOverlay!=null)showPlayerChromeTemporarily();}return true;
  }
// @replace renderCobraMultiPicker
  private void renderCobraMultiPicker(String filter) {
    if(mCobraMultiPicker==null)return;View view=mCobraMultiPicker.findViewWithTag("cobra_multi_picker_list");if(!(view instanceof android.widget.ListView))return;
    android.widget.ListView list=(android.widget.ListView)view;boolean groups="CATEGORIES".equals(filter);
    final ArrayList<String> names=new ArrayList<>();final ArrayList<Channel> channels=new ArrayList<>();
    if(groups){java.util.TreeSet<String> all=new java.util.TreeSet<>(String.CASE_INSENSITIVE_ORDER);for(Channel c:mChannels)if(cobraChannelAllowed(c)&&c.group!=null&&!c.group.isEmpty())all.add(c.group);names.addAll(all);}
    else {for(Channel c:cobraMultiChannels(filter))if(cobraChannelAllowed(c)&&(mCobraTiles.get(c.id)==null))channels.add(c);}
    if(!groups&&channels.isEmpty()&&"RECENT".equals(filter)){renderCobraMultiPicker("ALL");return;}
    list.setAdapter(new android.widget.BaseAdapter(){public int getCount(){return groups?names.size():channels.size();}public Object getItem(int p){return groups?names.get(p):channels.get(p);}public long getItemId(int p){return p;}public View getView(int p,View old,android.view.ViewGroup host){
      Button row=old instanceof Button?(Button)old:cobraTextButton("",true,()->{});row.setTextColor(Color.WHITE);row.setTextSize(13);row.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);row.setPadding(dp(12),0,dp(12),0);row.setMaxLines(2);row.setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,dp(64)));
      if(groups){String g=names.get(p);row.setText(g);row.setOnClickListener(v->renderCobraMultiPicker("GROUP:"+g));}else{Channel c=channels.get(p);GuideProgram current=cobraCurrentProgram(c);row.setText(c.name+"\n"+(current==null?cobraGuideStatus(c):current.title));row.setOnClickListener(v->selectCobraMultiChannel(c));}return row;}});
  }
// @append
  private final class CobraVideoTile {
    final Channel channel;final FrameLayout view;final TextureView texture;final View audioRing;final TextView warning;
    ExoPlayer player;int frames=-1;long changed=android.os.SystemClock.elapsedRealtime(),lastReport=0;String lastState="";
    CobraVideoTile(Channel c){channel=c;view=new FrameLayout(InfinityLiveActivity.this);view.setBackgroundColor(Color.BLACK);texture=new TextureView(InfinityLiveActivity.this);view.addView(texture,new FrameLayout.LayoutParams(-1,-1));
      warning=cobraText("",Color.WHITE,11);warning.setGravity(Gravity.CENTER);warning.setBackgroundColor(0xbb07111c);warning.setPadding(dp(8),dp(4),dp(8),dp(4));warning.setVisibility(View.GONE);view.addView(warning,new FrameLayout.LayoutParams(-1,dp(32),Gravity.BOTTOM));
      audioRing=new View(InfinityLiveActivity.this);audioRing.setBackgroundColor(0xff41c8ef);audioRing.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);view.addView(audioRing,new FrameLayout.LayoutParams(dp(2),-1,Gravity.LEFT));
      view.setFocusable(true);view.setFocusableInTouchMode(false);view.setOnClickListener(v->{int i=cobraMultiIndex(c.id);if(i>=0)setMultiAudio(i);});view.setOnLongClickListener(v->{int i=cobraMultiIndex(c.id);if(i>=0)showCobraMultiTileActions(i);return true;});
      view.setOnKeyListener((v,code,event)->{if(event.getAction()==KeyEvent.ACTION_DOWN&&(code==KeyEvent.KEYCODE_MENU||code==KeyEvent.KEYCODE_INFO)){int i=cobraMultiIndex(c.id);if(i>=0)showCobraMultiTileActions(i);return true;}return false;});
    }
  }

  private CobraVideoTile cobraNewMultiTile(Channel channel) {
    CobraVideoTile tile=new CobraVideoTile(channel);
    try {
      if(mCobraCarryPlayer!=null&&mCobraCarryChannel!=null&&channel.id.equals(mCobraCarryChannel.id)){
        tile.player=mCobraCarryPlayer;mCobraCarryPlayer=null;mCobraCarryChannel=null;cobraAttachVideo(tile.player,tile.texture);
      }else {tile.player=buildPlayer(tile.texture,channel,false);tile.player.setMediaItem(mediaItem(channel.primaryUrl));tile.player.prepare();startCobraPlayer(tile.player);}
      mCobraMultiCanvas.addView(tile.view,new FrameLayout.LayoutParams(1,1));return tile;
    }catch(RuntimeException error){cobraDisposePlayer(tile.player);tile.player=null;tile.warning.setText("Screen unavailable • hold for options");tile.warning.setVisibility(View.VISIBLE);if(tile.view.getParent()==null)mCobraMultiCanvas.addView(tile.view,new FrameLayout.LayoutParams(1,1));return tile;}
  }

  private void cobraDisposeTile(CobraVideoTile tile) {
    if(tile==null)return;cobraDisposePlayer(tile.player);tile.player=null;
    if(tile.view.getParent() instanceof android.view.ViewGroup)((android.view.ViewGroup)tile.view.getParent()).removeView(tile.view);
  }

  private void cobraSyncMultiArrays() {
    ArrayList<CobraVideoTile> tiles=mCobraTiles.values();mMultiPlayers=new ExoPlayer[tiles.size()];mMultiTextures=new TextureView[tiles.size()];mMultiChannels=new Channel[tiles.size()];
    for(int i=0;i<tiles.size();i++){CobraVideoTile t=tiles.get(i);mMultiPlayers[i]=t.player;mMultiTextures[i]=t.texture;mMultiChannels[i]=t.channel;}
  }

  private void cobraLayoutMultiTiles() {
    if(mCobraMultiCanvas==null)return;int w=mCobraMultiCanvas.getWidth(),h=mCobraMultiCanvas.getHeight();if(w<=0||h<=0)return;ArrayList<CobraVideoTile> tiles=mCobraTiles.values();
    for(int i=0;i<tiles.size();i++){int[] rect=CobraLayoutMath.tile(i,tiles.size(),w,h);cobraPosition(tiles.get(i).view,rect[0],rect[1],rect[2],rect[3]);}
  }

  private int cobraMultiIndex(String key) {if(mMultiChannels!=null)for(int i=0;i<mMultiChannels.length;i++)if(mMultiChannels[i].id.equals(key))return i;return -1;}

  private boolean cobraChannelAllowed(Channel c) {return c!=null&&!isCobraHidden(c)&&!mFeatures.looksAdult(c.group)&&!mFeatures.looksAdult(c.name)&&mFeatures.sourceEnabled(sourceIdForChannel(c));}

  private void cobraRetryMultiTile(String key) {
    CobraVideoTile tile=mCobraTiles.get(key);if(tile==null||!isCobraAsyncAlive())return;
    int owner=mAudioTile;cobraDisposePlayer(tile.player);tile.player=null;tile.frames=-1;tile.changed=android.os.SystemClock.elapsedRealtime();
    mCobraCreatingMulti=true;
    try{tile.player=buildPlayer(tile.texture,tile.channel,false);tile.player.setMediaItem(mediaItem(tile.channel.primaryUrl));tile.player.prepare();startCobraPlayer(tile.player);}
    catch(Exception error){tile.warning.setText("Cannot restart this screen");tile.warning.setVisibility(View.VISIBLE);}
    finally{mCobraCreatingMulti=false;}
    cobraSyncMultiArrays();setMultiAudio(owner);
  }

  private void cobraInspectMultiHealth() {
    if(mBackgroundStopped||mInPictureInPicture||mCobraTiles.isEmpty())return;
    long now=android.os.SystemClock.elapsedRealtime();
    for(CobraVideoTile tile:mCobraTiles.values()) {
      ExoPlayer player=tile.player;String state="";CobraPlayerBinding binding=mCobraPlayerBindings.get(player);
      if(player==null)state="Stream unavailable";
      else {
        androidx.media3.exoplayer.DecoderCounters counters=player.getVideoDecoderCounters();
        if(counters!=null){counters.ensureUpdated();int frames=counters.renderedOutputBufferCount;if(frames!=tile.frames){tile.frames=frames;tile.changed=now;}}
        if(binding!=null&&!binding.error.isEmpty())state=binding.error.contains("DECOD")?"Decoder unavailable • hold for details":"Stream error • hold for details";
        else if(!player.getPlayWhenReady()){state="Paused • hold to retry";tile.changed=now;}
        else if(player.getPlaybackSuppressionReason()!=Player.PLAYBACK_SUPPRESSION_REASON_NONE)state="Playback suppressed • hold for details";
        else if(player.getPlaybackState()==Player.STATE_BUFFERING&&now-tile.changed>12000)state="Buffering • hold for details";
        else if(player.getPlaybackState()==Player.STATE_READY&&player.getVideoSize().width>0&&now-tile.changed>15000)state="Video stalled • hold to retry";
        else if(player.getPlaybackState()==Player.STATE_ENDED)state="Stream ended • hold to retry";
      }
      tile.warning.setText(state);tile.warning.setVisibility(state.isEmpty()?View.GONE:View.VISIBLE);
      if(!state.equals(tile.lastState)||(!state.isEmpty()&&now-tile.lastReport>30000)){
        tile.lastState=state;tile.lastReport=now;
        mFeatures.writeHealth("multiview",sourceIdForChannel(tile.channel),tile.channel.id,state.isEmpty()?"playing":"attention",binding==null?state:binding.error,0,mCobraTiles.keys().size(),mAudioTile,mRecordingSession.isEmpty()?"idle":"recording","ready");
      }
    }
  }

  private void cobraShowMultiDiagnostics(String key) {
    CobraVideoTile tile=mCobraTiles.get(key);if(tile==null)return;ExoPlayer p=tile.player;CobraPlayerBinding binding=mCobraPlayerBindings.get(p);
    String detail=p==null?"No active player":"State "+p.getPlaybackState()+"  ·  play requested "+p.getPlayWhenReady()+"\nSuppression "+p.getPlaybackSuppressionReason()+"  ·  video frames "+tile.frames+"\nSurface attached "+tile.texture.isAttachedToWindow()+" / ready "+tile.texture.isAvailable();
    if(p!=null&&p.getVideoFormat()!=null){Format f=p.getVideoFormat();detail+="\n"+f.width+"×"+f.height+"  "+f.sampleMimeType;}
    if(binding!=null&&!binding.error.isEmpty())detail+="\n"+binding.error;
    detail+="\nA third stream may also depend on the provider's connection allowance and the device's decoder capacity. This panel does not guess which limit applies.";
    LinearLayout rows=cobraOpenSheet(tile.channel.name,"Playback diagnostics","multi-diagnostics");TextView text=cobraText(detail,0xffc8d7e7,13);text.setPadding(dp(14),dp(12),dp(14),dp(12));rows.addView(text);
    rows.addView(cobraSheetRow("recent","Retry this screen",null,false,true,()->cobraRetryMultiTile(key)));
  }
