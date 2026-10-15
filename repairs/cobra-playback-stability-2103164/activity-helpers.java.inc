  // One decision owner for Android visibility and PiP; callbacks may arrive in either order.
  static final class CobraPlaybackPolicy {
    static final int PAUSE=0, MINI_AUDIO=1, STOP_PIP=2;
    boolean started=false,resumed=false,pipOwned=false,stopped=false,dismissed=false;
    long epoch=0;
    void start(){started=true;}
    void resume(boolean pip){started=true;resumed=true;stopped=false;pipOwned=pip;dismissed=false;}
    void pause(){resumed=false;}
    void pipChanged(boolean pip){if(pip)pipOwned=true;else if(resumed&&!stopped)pipOwned=false;}
    int stop(boolean frameworkPip,boolean miniEligible){
      started=false;resumed=false;stopped=true;
      if(pipOwned||frameworkPip){dismiss();return STOP_PIP;}
      return !dismissed&&miniEligible?MINI_AUDIO:PAUSE;
    }
    void dismiss(){if(!dismissed)epoch++;dismissed=true;stopped=true;}
    boolean acceptsRetry(long captured,boolean requested,boolean allowed){return epoch==captured&&!dismissed&&requested&&allowed;}
  }
  private final CobraPlaybackPolicy mCobraPlaybackPolicy=new CobraPlaybackPolicy();
  private ExoPlayer mCobraMiniBackgroundPlayer;
  private InfinityExtendedBackgroundService.MiniPlaybackOwner mCobraMiniOwner;

  @Override protected void onStart(){super.onStart();mCobraPlaybackPolicy.start();}

  private boolean cobraWantsFullscreenPip(){
    if(!isCobraAsyncAlive()||mBackgroundStopped)return false;
    if(mPlayerOverlay!=null&&cobraPlaybackRequested(mPlayer))return true;
    if(mMultiOverlay!=null&&mMultiPlayers!=null)for(ExoPlayer player:mMultiPlayers)if(cobraPlaybackRequested(player))return true;
    return false;
  }
  private boolean cobraPlaybackRequested(ExoPlayer player){
    if(player==null)return false;
    try{int state=player.getPlaybackState();return player.getPlayWhenReady()&&state!=Player.STATE_IDLE&&state!=Player.STATE_ENDED;}
    catch(RuntimeException ignored){return false;}
  }
  private boolean cobraOwnsMiniSession(ExoPlayer player){
    return mCobraMiniBackgroundActive&&player!=null&&player==mCobraMiniBackgroundPlayer&&player==mCobraPreviewPlayer
        &&mPlayerOverlay==null&&mMultiOverlay==null&&!mCobraPlaybackPolicy.pipOwned&&!isCobraInPictureInPicture()
        &&cobraMiniBackgroundEnabled()&&!mCobraPlaybackPolicy.dismissed;
  }
  private boolean cobraPlaybackMayRun(ExoPlayer player){
    return isCobraAsyncAlive()&&isCurrentCobraPlayer(player)&&(!mBackgroundStopped||cobraOwnsMiniSession(player));
  }
  private void cobraHaltHiddenPlayback(){
    mCobraPlaybackPolicy.dismiss();mCobraPreviewAutoplayAllowed=false;
    cobraEndMiniBackgroundPlayback();pauseCobraForBackground();
    // Include transfer/carry bindings, not just the currently visible video.
    for(ExoPlayer player:new ArrayList<>(mCobraPlayerBindings.keySet()))try{player.pause();}catch(RuntimeException ignored){}
    mBackgroundResumePlayers.clear();mMain.removeCallbacks(mProgressTicker);configureCobraPip(false);
  }
  private void cobraPublishMiniState(){
    if(mCobraMiniOwner!=null)InfinityExtendedBackgroundService.refreshMiniPlayback(mCobraMiniOwner);
  }
  private boolean cobraStartOwnedMiniPlayback(){
    if(!cobraMiniBackgroundEnabled()||!cobraMiniPreviewPlaying()||mCobraPlaybackPolicy.pipOwned
        ||mCobraPlaybackPolicy.dismissed||isCobraInPictureInPicture()||!isCobraAsyncAlive())return false;
    final ExoPlayer session=mCobraPreviewPlayer;
    if(cobraOwnsMiniSession(session)&&mCobraMiniOwner!=null)return true;
    cobraEndMiniBackgroundPlayback();mCobraMiniBackgroundPlayer=session;mCobraMiniBackgroundActive=true;
    InfinityExtendedBackgroundService.MiniPlaybackOwner owner=new InfinityExtendedBackgroundService.MiniPlaybackOwner(){
      public boolean available(){
        if(mCobraMiniOwner!=this||!cobraOwnsMiniSession(session)||!isCobraAsyncAlive())return false;
        try{int state=session.getPlaybackState();return state!=Player.STATE_IDLE&&state!=Player.STATE_ENDED;}catch(RuntimeException ignored){return false;}
      }
      public int state(){
        if(!available())return android.media.session.PlaybackState.STATE_STOPPED;
        if(session.isPlaying())return android.media.session.PlaybackState.STATE_PLAYING;
        return session.getPlayWhenReady()&&session.getPlaybackState()==Player.STATE_BUFFERING
            ?android.media.session.PlaybackState.STATE_BUFFERING:android.media.session.PlaybackState.STATE_PAUSED;
      }
      public long position(){return Math.max(0L,session.getCurrentPosition());}
      public void command(int command){
        if(!available())return;
        if(command==InfinityExtendedBackgroundService.COMMAND_PLAY)startCobraPlayer(session);
        else {
          mCobraPlaybackPolicy.epoch++;mBackgroundResumePlayers.remove(session);session.pause();
          if(command==InfinityExtendedBackgroundService.COMMAND_STOP){mCobraPreviewAutoplayAllowed=false;cobraEndMiniBackgroundPlayback();}
        }
        cobraPublishMiniState();
      }
      public void unavailable(){
        if(mCobraMiniOwner!=this||mCobraMiniBackgroundPlayer!=session)return;
        mCobraPlaybackPolicy.epoch++;mBackgroundResumePlayers.remove(session);
        try{session.pause();}catch(RuntimeException ignored){}
        cobraEndMiniBackgroundPlayback();
      }
    };
    mCobraMiniOwner=owner;
    String title=mGuidePreviewChannel==null?"Cobra Live":mGuidePreviewChannel.name;
    if(InfinityExtendedBackgroundService.startMiniPlayback(this,title,owner))return true;
    cobraEndMiniBackgroundPlayback();return false;
  }

  // Geometry is integer-only and host tested. Coordinates are scrim-local, never display metrics.
  static final class CobraSheetGeometry {
    static int clamp(int n,int low,int high){return Math.max(low,Math.min(Math.max(low,high),n));}
    static int[] place(int[] safe,int[] pane,int[] anchor,int wantedWidth,int wantedHeight,int gap){
      int sl=safe[0],st=safe[1],sr=Math.max(sl+1,safe[2]),sb=Math.max(st+1,safe[3]);
      int pl=clamp(pane[0],sl,sr-1),pr=clamp(pane[2],pl+1,sr);
      int width=Math.max(1,Math.min(Math.min(wantedWidth,sr-sl),pr-pl));
      int left=clamp(anchor[2]-width,pl,pr-width);
      int below=clamp(anchor[3]+gap,st,sb),above=clamp(anchor[1]-gap,st,sb);
      int roomBelow=sb-below,roomAbove=above-st;
      boolean down=roomBelow>=wantedHeight||(roomBelow>=roomAbove);
      int maxHeight=Math.max(1,down?roomBelow:roomAbove);
      // A tiny/zero side cannot provide accessible scrolling; use the safe window vertically.
      if(maxHeight<48){maxHeight=sb-st;below=st;down=true;}
      int height=Math.max(1,Math.min(wantedHeight,maxHeight));
      return new int[]{left,clamp(down?below:above-height,st,sb-height),width,height,maxHeight};
    }
  }
  private View mCobraNextSheetAnchor,mCobraSheetAnchor,mCobraSheetPane;
  private android.view.ViewTreeObserver.OnGlobalLayoutListener mCobraSheetLayoutListener;
  private LinearLayout mCobraSheetPanel;
  private int mCobraSheetHeightLimit=Integer.MAX_VALUE;

  private View cobraResolveSheetAnchor(String kind){
    View explicit=mCobraNextSheetAnchor;mCobraNextSheetAnchor=null;
    if(explicit!=null&&explicit.isAttachedToWindow())return explicit;
    if(mCobraActionSheet!=null&&mCobraSheetAnchor!=null&&mCobraSheetAnchor.isAttachedToWindow())return mCobraSheetAnchor;
    if(mPlayerOverlay!=null){View button=mPlayerOverlay.findViewWithTag("aspect".equals(kind)?"cobra_player_aspect_anchor":"cobra_player_options_anchor");return button!=null?button:mPlayerOverlay;}
    if("preview-actions".equals(kind)&&mCobraPreviewHost!=null)return mCobraPreviewHost;
    return null;
  }
  private View cobraResolveSheetPane(View anchor){
    if(anchor==null)return null;
    if(mPlayerOverlay!=null)return mPlayerOverlay;
    if(mMultiOverlay!=null)return mMultiOverlay;
    if(mCobraPreviewHost!=null&&mCobraPreviewHost.isAttachedToWindow())return mCobraPreviewHost;
    return anchor;
  }
  private int[] cobraLocalBounds(View view,View origin){
    int[] v=new int[2],o=new int[2];view.getLocationOnScreen(v);origin.getLocationOnScreen(o);
    return new int[]{v[0]-o[0],v[1]-o[1],v[0]-o[0]+view.getWidth(),v[1]-o[1]+view.getHeight()};
  }
  private int[] cobraSheetSafeBounds(FrameLayout scrim){
    int[] loc=new int[2];scrim.getLocationOnScreen(loc);android.graphics.Rect window=new android.graphics.Rect();scrim.getWindowVisibleDisplayFrame(window);
    int inset=dp(8),w=Math.max(1,scrim.getWidth()),h=Math.max(1,scrim.getHeight());
    int l=inset,t=inset,r=w-inset,b=h-inset;
    if(!window.isEmpty()){l=Math.max(l,window.left-loc[0]+inset);t=Math.max(t,window.top-loc[1]+inset);r=Math.min(r,window.right-loc[0]-inset);b=Math.min(b,window.bottom-loc[1]-inset);}
    l=Math.min(Math.max(0,l),w-1);t=Math.min(Math.max(0,t),h-1);
    return new int[]{l,t,Math.max(l+1,r),Math.max(t+1,b)};
  }
  private void cobraPositionAnchoredSheet(FrameLayout scrim,LinearLayout panel,View anchor,View pane){
    if(scrim!=mCobraActionSheet||scrim.getWidth()<1||scrim.getHeight()<1)return;
    if(!anchor.isAttachedToWindow()||!pane.isAttachedToWindow()){closeCobraActionSheet();return;}
    int[] safe=cobraSheetSafeBounds(scrim),p=cobraLocalBounds(pane,scrim),a=cobraLocalBounds(anchor,scrim);
    int wanted=dp(vtheme().dimension("cobra.cobraOpenSheet.dimensions.13",440));
    int measured=Math.max(dp(96),panel.getMeasuredHeight());
    int[] rect=CobraSheetGeometry.place(safe,p,a,wanted,measured,dp(6));
    int limit=Math.max(1,rect[4]-panel.getPaddingTop()-panel.getPaddingBottom());
    boolean resized=mCobraSheetHeightLimit!=limit;mCobraSheetHeightLimit=limit;
    FrameLayout.LayoutParams lp=(FrameLayout.LayoutParams)panel.getLayoutParams();
    if(lp.width!=rect[2]||lp.height!=rect[3]||lp.leftMargin!=rect[0]||lp.topMargin!=rect[1]||lp.gravity!=(Gravity.TOP|Gravity.LEFT)){
      lp.width=rect[2];lp.height=rect[3];lp.gravity=Gravity.TOP|Gravity.LEFT;
      lp.setMargins(rect[0],rect[1],0,0);panel.setLayoutParams(lp);
    }else if(resized)panel.requestLayout();
    if(panel.getLeft()==rect[0]&&panel.getTop()==rect[1]&&panel.getWidth()==rect[2]&&!panel.isLayoutRequested())panel.setAlpha(1f);
  }
