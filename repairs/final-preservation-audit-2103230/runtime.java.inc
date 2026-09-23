  // 2103230: bounded observations and geometry/ownership corrections only.
  static final class CobraAuditPolicy {
    static boolean retryCurrent(long captured,long current,boolean requested,boolean allowed,boolean dismissed){
      return captured==current&&requested&&allowed&&!dismissed;
    }
    static boolean fillApplies(boolean enabled,boolean pip,boolean promoted,boolean tileSurface){
      return enabled&&!pip&&!promoted&&tileSurface;
    }
    static boolean stalledBuffer(boolean loading,long now,long progressAt){
      return !loading&&now>=progressAt&&now-progressAt>=18000L;
    }
    static int[] localInsets(int x,int y,int w,int h,int rootW,int rootH,int l,int t,int r,int b){
      if(w<=0||h<=0||rootW<=0||rootH<=0)return new int[]{0,0,0,0};
      int left=Math.min(w,Math.max(0,l-x)),top=Math.min(h,Math.max(0,t-y));
      int right=Math.min(w-left,Math.max(0,x+w-(rootW-r)));
      int bottom=Math.min(h-top,Math.max(0,y+h-(rootH-b)));
      return new int[]{left,top,right,bottom};
    }
  }

  static final class CobraAuditTrail {
    static final int LIMIT=48;
    private final java.util.ArrayDeque<JSONObject> events=new java.util.ArrayDeque<>();
    void add(String kind,long value,long extra){
      try{
        JSONObject row=new JSONObject();row.put("elapsed_ms",android.os.SystemClock.elapsedRealtime());
        row.put("kind",kind);row.put("value",value);row.put("extra",extra);
        while(events.size()>=LIMIT)events.removeFirst();events.addLast(row);
      }catch(org.json.JSONException ignored){}
    }
    JSONArray snapshot(){return new JSONArray(new ArrayList<>(events));}
  }

  private boolean cobraAuditLiveOwner(CobraPlayerBinding b){
    if(b==null||!b.current()||!b.vitals.live)return false;
    if(b.player==mPlayer)return mPlayingVodKey.isEmpty()&&!mCobraProviderCatchupActive;
    if(b.player==mCobraPreviewPlayer)return true;
    CobraVideoTile tile=mCobraTiles.get(b.channel.id);
    return tile!=null&&tile.player==b.player;
  }

  private boolean cobraAuditRetryAllowed(CobraPlayerBinding b,long epoch){
    return b!=null&&b.current()&&CobraAuditPolicy.retryCurrent(epoch,b.intentEpoch,
        b.player.getPlayWhenReady(),cobraPlaybackMayRun(b.player),mCobraPlaybackPolicy.dismissed);
  }

  private boolean cobraAuditFillApplies(CobraPlayerBinding b){
    CobraVideoTile tile=b==null||b.channel==null?null:mCobraTiles.get(b.channel.id);
    return CobraAuditPolicy.fillApplies(cobraMultiFillScreen(),mInPictureInPicture,
        mCobraMultiFullscreenActive,tile!=null&&tile.player==b.player&&tile.texture==b.texture);
  }

  private JSONObject cobraAuditSnapshot(CobraPlayerBinding b){
    JSONObject row=new JSONObject();
    try{
      ExoPlayer p=b.player;
      row.put("session_id",b.sessionId);row.put("channel_hash",InfinityCobraFeatureRuntime.hashId(b.channel.id));
      row.put("source_role",b.fallback?"fallback":"primary");row.put("fallback_pending",b.fallbackPending);
      row.put("live_channel",b.vitals.live);row.put("state",p.getPlaybackState());
      row.put("requested",p.getPlayWhenReady());row.put("playing",p.isPlaying());row.put("suppression",p.getPlaybackSuppressionReason());
      row.put("position_ms",p.getCurrentPosition());row.put("buffered_ms",p.getTotalBufferedDuration());row.put("loading",p.isLoading());
      row.put("media_count",p.getMediaItemCount());row.put("intent_epoch",b.intentEpoch);row.put("state_serial",b.stateSerial);
      row.put("background_stopped",mBackgroundStopped);row.put("pip",mInPictureInPicture);
      row.put("timeshift_owner",p==mCobraTimeshiftPlayer);row.put("proxy_owner",p==mCobraTimeshiftProxyPlayer);
      row.put("role",p==mPlayer?"fullscreen":p==mCobraPreviewPlayer?"preview":"multiview_or_transfer");
      row.put("surface_available",b.texture!=null&&b.texture.isAvailable());row.put("surface_shown",b.texture!=null&&b.texture.isShown());
      row.put("error_code",b.error);row.put("decoder",b.vitals.decoder);row.put("recent_events",b.vitals.audit.snapshot());
      androidx.media3.common.Timeline timeline=p.getCurrentTimeline();
      if(timeline!=null&&!timeline.isEmpty()){
        int index=p.getCurrentMediaItemIndex();
        if(index>=0&&index<timeline.getWindowCount()){
          androidx.media3.common.Timeline.Window window=timeline.getWindow(index,new androidx.media3.common.Timeline.Window());
          row.put("window_live",window.isLive());row.put("window_dynamic",window.isDynamic);row.put("window_seekable",window.isSeekable);
          row.put("window_duration_ms",window.getDurationMs());row.put("window_default_ms",window.getDefaultPositionMs());
        }
      }
      Object manifest=p.getCurrentManifest();
      if(manifest instanceof androidx.media3.exoplayer.hls.HlsManifest){
        androidx.media3.exoplayer.hls.playlist.HlsMediaPlaylist playlist=((androidx.media3.exoplayer.hls.HlsManifest)manifest).mediaPlaylist;
        row.put("hls_end_tag",playlist.hasEndTag);row.put("hls_type",playlist.playlistType);
        row.put("hls_media_sequence",playlist.mediaSequence);row.put("hls_segments",playlist.segments.size());
        row.put("hls_duration_us",playlist.durationUs);row.put("hls_target_duration_us",playlist.targetDurationUs);
      }
    }catch(Exception unavailable){try{row.put("snapshot_incomplete",unavailable.getClass().getSimpleName());}catch(org.json.JSONException ignored){}}
    return row;
  }

  private void cobraAuditUnexpectedEnd(CobraPlayerBinding b){
    b.lastEndSnapshot=cobraAuditSnapshot(b);
    InfinityCobraDiagnostics.record(this,"playback","unexpected-live-ended",b.lastEndSnapshot.toString());
  }

  private void cobraAuditVerifyLiveRecovery(CobraPlayerBinding b){
    if(b.liveEndedRecoveries==0)return;
    final long serial=b.stateSerial,epoch=b.intentEpoch,position=b.player.getCurrentPosition();
    final androidx.media3.exoplayer.DecoderCounters counters=b.player.getVideoDecoderCounters();
    if(counters!=null)counters.ensureUpdated();final int frames=counters==null?-1:counters.renderedOutputBufferCount;
    mMain.postDelayed(()->{
      if(!cobraAuditRetryAllowed(b,epoch)||b.stateSerial!=serial||b.player.getPlaybackState()!=Player.STATE_READY||!b.player.isPlaying())return;
      androidx.media3.exoplayer.DecoderCounters current=b.player.getVideoDecoderCounters();
      if(current==null||current!=counters)return;current.ensureUpdated();
      if(b.player.getCurrentPosition()>position&&current.renderedOutputBufferCount>frames){
        b.liveEndedRecoveries=0;b.vitals.audit.add("live_recovery_verified",serial,0L);
        InfinityCobraDiagnostics.record(this,"playback","live-recovery-verified","session_id="+b.sessionId+"; position_and_frames_advanced=true");
      }
    },30000L);
  }
