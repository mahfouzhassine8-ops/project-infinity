  private void cobraRecoverUnexpectedLiveEnded(final CobraPlayerBinding binding){
    if(!cobraAuditLiveOwner(binding)||!cobraAuditRetryAllowed(binding,binding.intentEpoch)
        ||binding.player.getPlaybackState()!=Player.STATE_ENDED||binding.liveEndedRecovering||binding.fallbackPending)return;
    if(binding.liveEndedRecoveries>=CobraLiveEndedPolicy.MAX_RECOVERIES){
      binding.error="LIVE_ENDED";cobraUpdatePlaybackLabels();return;
    }
    final ExoPlayer ended=binding.player;final Channel channel=binding.channel;
    final long epoch=binding.intentEpoch,serial=binding.stateSerial;
    binding.liveEndedRecovering=true;binding.liveEndedRecoveryAt=android.os.SystemClock.elapsedRealtime();
    mMain.postDelayed(()->{
      if(!binding.current()||binding.intentEpoch!=epoch||binding.stateSerial!=serial)return;
      // Clear before external player calls: a new ENDED without intermediate READY must
      // remain eligible for the second bounded attempt, not get stuck behind this flag.
      binding.liveEndedRecovering=false;
      if(!cobraAuditLiveOwner(binding)||!cobraAuditRetryAllowed(binding,epoch)||ended.getPlaybackState()!=Player.STATE_ENDED)return;
      if(binding.liveEndedRecoveries>=CobraLiveEndedPolicy.MAX_RECOVERIES)return;
      binding.liveEndedRecoveries++;
      binding.vitals.audit.add("live_recovery_attempt",binding.liveEndedRecoveries,serial);
      if(ended==mCobraTimeshiftPlayer||ended==mCobraTimeshiftProxyPlayer){
        cobraFallbackFromLocalTimeshift(ended,channel,"unexpected-live-ended");return;
      }
      boolean useFallback=binding.liveEndedRecoveries>1&&!binding.fallback
          &&!"primary".equals(binding.vitals.preferences.fallback)
          &&channel!=null&&!channel.fallbackUrl.isEmpty()&&!channel.fallbackUrl.equals(channel.primaryUrl);
      try{
        binding.vitals.recovery.suspend();binding.vitals.prepareCalls++;binding.vitals.lastPrepareReason="unexpected-live-ended";
        if(useFallback){binding.fallback=true;ended.setMediaItem(mediaItem(channel.fallbackUrl));}
        else ended.seekToDefaultPosition();
        ended.prepare();startCobraPlayer(ended);
        InfinityCobraDiagnostics.record(this,"playback","live-ended-recovery",
            "session_id="+binding.sessionId+"; attempt="+binding.liveEndedRecoveries+"; route="+(useFallback?"fallback":"same-player")+"; verified=false");
      }catch(RuntimeException failure){
        binding.error="LIVE_ENDED";InfinityCobraDiagnostics.failure(this,"live-ended-recovery",failure);cobraUpdatePlaybackLabels();
      }
    },420L);
  }
