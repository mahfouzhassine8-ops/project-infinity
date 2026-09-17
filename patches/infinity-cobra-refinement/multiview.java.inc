// STATE
  private FrameLayout mRefMultiCanvas;
  private FrameLayout[] mRefMultiTiles;
  private boolean mRefBuildingMulti = false;
  private final java.util.IdentityHashMap<ExoPlayer, RefTileHealth> mRefTileHealth = new java.util.IdentityHashMap<>();
  private final Runnable mRefMultiWatch = new Runnable() {
    public void run() {
      if (!isCobraAsyncAlive() || mMultiPlayers == null || mMultiOverlay == null) return;
      if (!mBackgroundStopped && !isCobraInPictureInPicture()) {
        long now = android.os.SystemClock.elapsedRealtime();
        JSONArray records = new JSONArray();
        for (int i = 0; i < mMultiPlayers.length; i++) {
          ExoPlayer player = mMultiPlayers[i]; if (player == null) continue;
          RefTileHealth health = mRefTileHealth.get(player); if (health == null) continue;
          String status = health.error;
          long frame = health.lastFrame;
          if (status.isEmpty() && now - health.created > 18000L && (frame == 0 || now - frame > 15000L)) {
            status = player.getPlaybackState() == Player.STATE_BUFFERING ? "Buffering · hold for options"
                : !player.getPlayWhenReady() ? "Paused · hold to resume" : "Video stalled · hold to retry";
          }
          if (mRefMultiTiles != null && i < mRefMultiTiles.length) {
            View raw = mRefMultiTiles[i].findViewWithTag("tile_status");
            if (raw instanceof TextView) { ((TextView) raw).setText(status); raw.setVisibility(status.isEmpty() ? View.GONE : View.VISIBLE); }
          }
          try {
            JSONObject row = new JSONObject().put("tile", i+1).put("state", player.getPlaybackState())
                .put("play_when_ready", player.getPlayWhenReady()).put("is_playing", player.isPlaying())
                .put("suppression", player.getPlaybackSuppressionReason()).put("frame_age_ms", frame == 0 ? -1 : now-frame)
                .put("buffer_ms", player.getTotalBufferedDuration()).put("surface_available", mMultiTextures[i].isAvailable())
                .put("error", health.error).put("audio_owner", i==mAudioTile);
            records.put(row);
          } catch (Exception ignored) {}
        }
        String snapshot = records.toString();
        submitCobraIo(() -> {
          try (java.io.FileOutputStream out = openFileOutput("cobra-multiview-health.json", MODE_PRIVATE)) {
            out.write(snapshot.getBytes(StandardCharsets.UTF_8));
          } catch (Exception ignored) {}
        });
      }
      mMain.postDelayed(this, 5000L);
    }
  };

// METHODS
  private static final class RefTileHealth {
    volatile long lastFrame;
    long created = android.os.SystemClock.elapsedRealtime();
    String error = "";
    androidx.media3.exoplayer.video.VideoFrameMetadataListener frames;
    Player.Listener events;
  }

  private int cobraMultiIndex(String id) {
    if (mMultiChannels != null) for (int i=0;i<mMultiChannels.length;i++) if (mMultiChannels[i]!=null&&mMultiChannels[i].id.equals(id)) return i;
    return -1;
  }

  private void cobraWatchTile(ExoPlayer player, Channel channel, TextureView texture) {
    if (mRefTileHealth.containsKey(player)) return;
    RefTileHealth health = new RefTileHealth(); mRefTileHealth.put(player,health);
    health.frames = (presentationTimeUs, releaseTimeNs, format, mediaFormat) -> health.lastFrame = android.os.SystemClock.elapsedRealtime();
    player.setVideoFrameMetadataListener(health.frames);
    health.events = new Player.Listener() {
      @Override public void onVideoSizeChanged(VideoSize size) { texture.post(() -> cobraFitTexture(texture,size,0)); }
      @Override public void onPlaybackStateChanged(int state) {
        if (!isCobraAsyncAlive()) return;
        int index = cobraMultiIndex(channel.id);
        if (index<0 || mMultiPlayers[index]!=player) return;
        if (state==Player.STATE_READY) { health.error=""; if(index==mAudioTile)markCobraPlaybackReady(channel); }
      }
      @Override public void onPlayerError(PlaybackException error) {
        if (!isCobraAsyncAlive()) return;
        int index = cobraMultiIndex(channel.id); if(index<0 || mMultiPlayers[index]!=player)return;
        health.error=error==null?"Stream error":error.getErrorCodeName();
        mFeatures.writeHealth("multiview",sourceIdForChannel(channel),channel.id,"error",health.error,0,mMultiPlayers.length,mAudioTile,
            mRecordingSession.isEmpty()?"idle":"recording","ready");
      }
    };
    player.addListener(health.events);
    texture.addOnLayoutChangeListener((v,l,t,r,b,ol,ot,or,ob) -> {
      int index=cobraMultiIndex(channel.id);
      if(index>=0&&mMultiPlayers[index]==player)cobraFitTexture(texture,player.getVideoSize(),0);
    });
  }

  private void cobraUnwatchTile(ExoPlayer player) {
    RefTileHealth health = mRefTileHealth.remove(player); if(health==null)return;
    try { player.removeListener(health.events); player.clearVideoFrameMetadataListener(health.frames); } catch(Exception ignored){}
  }

  private void cobraFitTexture(TextureView texture, VideoSize size, int mode) {
    if(texture==null||size==null||size.width<=0||size.height<=0||texture.getWidth()<=0||texture.getHeight()<=0)return;
    float ar=size.width*(size.pixelWidthHeightRatio>0?size.pixelWidthHeightRatio:1f)/size.height;
    float vr=texture.getWidth()/(float)texture.getHeight();
    if(mode==2)ar=16f/9f; else if(mode==3)ar=4f/3f;
    float sx=Math.min(1f,ar/vr),sy=Math.min(1f,vr/ar);
    if(mode==1){float zoom=1f/Math.min(sx,sy);sx*=zoom;sy*=zoom;}
    else if(mode==4)sx*=1.10f; else if(mode==5)sx*=1.25f; else if(mode==6)sx*=1.40f;
    else if(mode==7){sx*=1.24f;sy*=.84f;}
    else if(mode==8){sx*=1.25f;sy*=1.25f;} else if(mode==9){sx*=1.5f;sy*=1.5f;} else if(mode==10){sx*=2f;sy*=2f;}
    else if(mode==11){sx*=Math.max(.55f,Math.min(1.80f,mPrefs.getFloat(COBRA_CUSTOM_ASPECT_X,1.15f)));sy*=Math.max(.55f,Math.min(1.80f,mPrefs.getFloat(COBRA_CUSTOM_ASPECT_Y,.92f)));}
    texture.setPivotX(texture.getWidth()/2f);texture.setPivotY(texture.getHeight()/2f);texture.setScaleX(sx);texture.setScaleY(sy);
  }

  private void applyCobraAspectTransform() {
    if(mPlayerTexture==null||mPlayer==null)return;
    mPlayerTexture.setTranslationX(0f);mPlayerTexture.setTranslationY(0f);
    cobraFitTexture(mPlayerTexture,mPlayer.getVideoSize(),mAspectMode);
  }

  private FrameLayout createMultiTile(int index) {
    final Channel channel=mMultiChannels[index];
    FrameLayout tile=new FrameLayout(this);tile.setBackgroundColor(Color.BLACK);tile.setFocusable(true);tile.setContentDescription(channel.name);
    TextureView texture=new TextureView(this);mMultiTextures[index]=texture;
    tile.addView(texture,new FrameLayout.LayoutParams(-1,-1));
    TextView status=cobraRefinedText("",11,false);status.setTag("tile_status");status.setTextColor(Color.WHITE);
    status.setBackgroundColor(Color.argb(185,0,0,0));status.setVisibility(View.GONE);
    tile.addView(status,new FrameLayout.LayoutParams(-1,dp(32),Gravity.BOTTOM));
    tile.setOnClickListener(v -> {int i=cobraMultiIndex(channel.id);if(i>=0)setMultiAudio(i);});
    tile.setOnLongClickListener(v -> {int i=cobraMultiIndex(channel.id);if(i>=0)showCobraMultiTileActions(i);return true;});
    tile.setOnFocusChangeListener((v,focused)->{if(focused&&!cobraTouchFirstDevice()){int i=cobraMultiIndex(channel.id);if(i>=0)setMultiAudio(i);}});
    ExoPlayer player=null;
    try {
      boolean carried=index==0&&mCobraCarryPlayer!=null&&mCobraCarryChannel!=null&&mCobraCarryChannel.id.equals(channel.id);
      if(carried){player=mCobraCarryPlayer;mCobraCarryPlayer=null;mCobraCarryChannel=null;player.setVideoTextureView(texture);}
      else {mRefBuildingMulti=true;try{player=buildPlayer(texture,channel,false);}finally{mRefBuildingMulti=false;}}
      mMultiPlayers[index]=player;cobraWatchTile(player,channel,texture);
      if(!carried){player.setMediaItem(mediaItem(channel.primaryUrl));player.prepare();startCobraPlayer(player);}
    } catch(Exception error){status.setText("Unable to open · hold to retry");status.setVisibility(View.VISIBLE);}
    return tile;
  }

  private void layoutCobraMultiTiles() {
    if(mRefMultiCanvas==null||mRefMultiTiles==null||mRefMultiCanvas.getWidth()<=0||mRefMultiCanvas.getHeight()<=0)return;
    int w=mRefMultiCanvas.getWidth(),h=mRefMultiCanvas.getHeight(),count=mRefMultiTiles.length,gap=dp(2);
    boolean portrait=h>w;
    for(int i=0;i<count;i++) {
      int left=0,top=0,right=w,bottom=h;
      if(portrait&&count<4){top=h*i/count;bottom=h*(i+1)/count;}
      else if(count==2){left=w*i/2;right=w*(i+1)/2;}
      else {left=w*(i%2)/2;right=w*((i%2)+1)/2;top=h*(i/2)/2;bottom=h*((i/2)+1)/2;if(count==3&&i==2){left=0;right=w;}}
      FrameLayout.LayoutParams p=new FrameLayout.LayoutParams(Math.max(1,right-left-gap),Math.max(1,bottom-top-gap));
      p.leftMargin=left;p.topMargin=top;mRefMultiTiles[i].setLayoutParams(p);
    }
  }

  private void openMultiView(List<Channel> channels) {
    if(channels==null||channels.size()<2){toast("Choose at least two channels");return;}
    ExoPlayer carry=null;Channel playing=mPlaying;TextureView oldTexture=mPlayerTexture;
    if(mPlayer!=null&&playing!=null&&channels.get(0).id.equals(playing.id)){carry=mPlayer;mPlayer=null;if(oldTexture!=null)carry.clearVideoTextureView(oldTexture);}
    mReflowingMulti=true;try{closePlayer();releaseMulti();}finally{mReflowingMulti=false;}
    stopCobraPreview();mCobraCarryPlayer=carry;mCobraCarryChannel=playing;
    int count=Math.min(4,channels.size());mMultiChannels=channels.subList(0,count).toArray(new Channel[0]);
    mMultiPlayers=new ExoPlayer[count];mMultiTextures=new TextureView[count];mRefMultiTiles=new FrameLayout[count];mAudioTile=0;
    mMultiOverlay=new FrameLayout(this);mMultiOverlay.setBackgroundColor(Color.BLACK);
    mRefMultiCanvas=new FrameLayout(this);mMultiOverlay.addView(mRefMultiCanvas,new FrameLayout.LayoutParams(-1,-1));
    for(int i=0;i<count;i++){mRefMultiTiles[i]=createMultiTile(i);mRefMultiCanvas.addView(mRefMultiTiles[i]);}
    mRefMultiCanvas.addOnLayoutChangeListener((v,l,t,r,b,ol,ot,or,ob)->{if(r-l!=or-ol||b-t!=ob-ot)layoutCobraMultiTiles();});
    ((FrameLayout)getWindow().getDecorView()).addView(mMultiOverlay,new FrameLayout.LayoutParams(-1,-1));
    setMultiAudio(0);configureCobraPip(false);
    mMain.removeCallbacks(mRefMultiWatch);mMain.postDelayed(mRefMultiWatch,5000L);
    if(mDeviceBridge!=null)mDeviceBridge.onPlaybackChanged("multiview-start");
  }

  private void rebuildCobraMultiPreservingSessions(ArrayList<Channel> next, String releaseChannelId) {
    if(mMultiPlayers==null||mRefMultiCanvas==null||next==null||next.size()<2||next.size()>4)return;
    ExoPlayer[] oldPlayers=mMultiPlayers;TextureView[] oldTextures=mMultiTextures;Channel[] oldChannels=mMultiChannels;
    FrameLayout[] oldTiles=mRefMultiTiles;
    String owner=oldChannels[Math.max(0,Math.min(mAudioTile,oldChannels.length-1))].id;
    mMultiChannels=next.toArray(new Channel[0]);mMultiPlayers=new ExoPlayer[next.size()];mMultiTextures=new TextureView[next.size()];mRefMultiTiles=new FrameLayout[next.size()];
    boolean[] reused=new boolean[oldPlayers.length];
    for(int i=0;i<next.size();i++) {
      for(int j=0;j<oldChannels.length;j++)if(!reused[j]&&oldChannels[j].id.equals(next.get(i).id)&&!oldChannels[j].id.equals(releaseChannelId)) {
        mMultiPlayers[i]=oldPlayers[j];mMultiTextures[i]=oldTextures[j];mRefMultiTiles[i]=oldTiles[j];reused[j]=true;break;
      }
    }
    for(int j=0;j<oldPlayers.length;j++)if(!reused[j]) {
      ExoPlayer p=oldPlayers[j];if(p!=null){cobraUnwatchTile(p);mBackgroundResumePlayers.remove(p);p.release();}
      if(oldTiles[j]!=null)mRefMultiCanvas.removeView(oldTiles[j]);
    }
    for(int i=0;i<next.size();i++)if(mRefMultiTiles[i]==null){mRefMultiTiles[i]=createMultiTile(i);mRefMultiCanvas.addView(mRefMultiTiles[i]);}
    // Existing tiles stay in the same attached parent. No clearVideoTextureView,
    // setMediaItem, prepare, stop or release is called on any retained player.
    int audio=cobraMultiIndex(owner);setMultiAudio(audio<0?0:audio);layoutCobraMultiTiles();
  }

  private void setMultiAudio(int index) {
    if(mMultiPlayers==null||index<0||index>=mMultiPlayers.length)return;
    mAudioTile=index;
    for(int i=0;i<mMultiPlayers.length;i++)if(mMultiPlayers[i]!=null) {
      ExoPlayer player=mMultiPlayers[i];player.setVolume(i==index?1f:0f);
      player.setTrackSelectionParameters(player.getTrackSelectionParameters().buildUpon().setTrackTypeDisabled(C.TRACK_TYPE_AUDIO,i!=index).build());
      if(mRefMultiTiles!=null&&i<mRefMultiTiles.length)
        mRefMultiTiles[i].setForeground(surface(Color.TRANSPARENT,0,i==index?Color.argb(145,82,181,236):Color.TRANSPARENT,1));
    }
  }

  private void multiToSingle() {
    if(mMultiPlayers==null||mMultiChannels==null||mMultiChannels.length==0)return;
    int index=Math.max(0,Math.min(mAudioTile,mMultiChannels.length-1));
    ExoPlayer session=mMultiPlayers[index];Channel channel=mMultiChannels[index];TextureView texture=mMultiTextures[index];
    if(session==null){toast("This screen has no active player");return;}
    cobraUnwatchTile(session);session.clearVideoTextureView(texture);mMultiPlayers[index]=null;
    mReflowingMulti=true;try{releaseMulti();}finally{mReflowingMulti=false;}
    mPlaying=channel;mPlayingIndex=mChannels.indexOf(channel);openPlayerOverlay(channel);mPlayer=session;
    session.setTrackSelectionParameters(session.getTrackSelectionParameters().buildUpon().setTrackTypeDisabled(C.TRACK_TYPE_AUDIO,false).build());
    session.setVideoTextureView(mPlayerTexture);session.setVolume(1f);applyCobraAspectTransform();updateCobraPlayerPlayPause();
  }

  private void showCobraMultiTileActions(int index) {
    if(mMultiChannels==null||index<0||index>=mMultiChannels.length)return;
    final String id=mMultiChannels[index].id;
    LinearLayout body=cobraOpenRefinedSheet(mMultiChannels[index].name,false);if(body==null)return;
    cobraSheetAction(body,"Use audio here",false,()->{int i=cobraMultiIndex(id);if(i>=0)setMultiAudio(i);});
    cobraSheetAction(body,"Change channel",false,()->{int i=cobraMultiIndex(id);if(i>=0){mCobraMultiReplaceIndex=i;showCobraMultiPicker(true);}});
    if(mMultiChannels.length<4)cobraSheetAction(body,"Add screen",false,()->{mCobraMultiReplaceIndex=-1;showCobraMultiPicker(true);});
    cobraSheetAction(body,"Fullscreen this",false,()->{int i=cobraMultiIndex(id);if(i>=0){setMultiAudio(i);multiToSingle();}});
    cobraSheetAction(body,"Retry this screen",false,()->{int i=cobraMultiIndex(id);if(i<0)return;ExoPlayer p=mMultiPlayers[i];if(p!=null){RefTileHealth h=mRefTileHealth.get(p);if(h!=null){h.error="";h.created=android.os.SystemClock.elapsedRealtime();}if(p.getPlayerError()!=null||p.getPlaybackState()==Player.STATE_IDLE)p.prepare();startCobraPlayer(p);}});
    cobraSheetAction(body,"Remove screen",true,()->{int i=cobraMultiIndex(id);if(i>=0)removeCobraMultiTileClean(i);});
    cobraSheetAction(body,"Close Multi-View",true,()->{multiToSingle();closeFullscreenToCobraView();});
    cobraFitActionSheet(mMultiChannels.length<4?7:6);
  }
