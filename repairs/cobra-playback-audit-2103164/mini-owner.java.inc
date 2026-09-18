  private boolean cobraBeginMiniBackgroundPlayback(){
    if(cobraMiniBackgroundStillOwned())return true;
    // Foreground-only handoff: do not launch a new foreground service from onStop.
    if(!mCobraRotationResumed||mBackgroundStopped||mCobraPipWasActive||mCobraPipDismissed
        ||!isCobraAsyncAlive()||!cobraMiniBackgroundEnabled()||!cobraMiniPreviewPlaying())return false;
    cobraEndMiniBackgroundPlayback();
    final ExoPlayer session=mCobraPreviewPlayer;
    mCobraMiniBackgroundActive=true;
    mCobraMiniOwner=new InfinityExtendedBackgroundService.MiniPlaybackOwner(){
      @Override public boolean valid(){
        if(!isCobraAsyncAlive()||!mCobraMiniBackgroundActive||mCobraMiniOwner!=this
            ||mCobraPreviewPlayer!=session||mPlayerOverlay!=null||mMultiOverlay!=null
            ||mCobraPipWasActive||mCobraPipDismissed||!cobraMiniBackgroundEnabled())return false;
        try{int state=session.getPlaybackState();return state!=Player.STATE_IDLE&&state!=Player.STATE_ENDED;}
        catch(RuntimeException error){return false;}
      }
      @Override public int state(){
        if(!valid())return android.media.session.PlaybackState.STATE_STOPPED;
        if(!session.getPlayWhenReady())return android.media.session.PlaybackState.STATE_PAUSED;
        return session.getPlaybackState()==Player.STATE_BUFFERING
            ?android.media.session.PlaybackState.STATE_BUFFERING:android.media.session.PlaybackState.STATE_PLAYING;
      }
      @Override public long position(){try{return Math.max(0,session.getCurrentPosition());}catch(RuntimeException e){return 0;}}
      @Override public void play(){if(valid()){mBackgroundResumePlayers.remove(session);session.play();}}
      @Override public void pause(){if(valid()){mBackgroundResumePlayers.remove(session);session.pause();}}
      @Override public void stop(){
        // An OS/media stop cannot queue this session to restart on resume.
        if(mCobraMiniOwner!=this)return;
        mCobraMiniBackgroundActive=false;mCobraMiniOwner=null;mBackgroundResumePlayers.remove(session);
        mCobraPreviewAutoplayAllowed=false;
        if(mPrefs!=null)mPrefs.edit().putBoolean(COBRA_EXPLICIT_STOP,true).apply();
        try{session.pause();}catch(RuntimeException ignored){}
        if(mCobraPreviewPlayer==session){mCobraPreviewPlayer=null;mCobraPreviewSessionKey="";cobraDisposePlayer(session);}
      }
    };
    String title=mGuidePreviewChannel==null?"Cobra Live":mGuidePreviewChannel.name;
    if(InfinityExtendedBackgroundService.startMiniPlayback(this,title,mCobraMiniOwner))return true;
    // The service also fails closed, but a refused request must never grant keepalive.
    cobraEndMiniBackgroundPlayback();return false;
  }

  private void cobraEndMiniBackgroundPlayback(){
    InfinityExtendedBackgroundService.MiniPlaybackOwner owner=mCobraMiniOwner;
    mCobraMiniOwner=null;mCobraMiniBackgroundActive=false;
    if(owner!=null)InfinityExtendedBackgroundService.detachMiniPlayback(this,owner);
  }
