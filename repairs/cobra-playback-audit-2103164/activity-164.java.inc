  // A PiP activity is paused but STARTED while its video remains visible.
  // onStop means the PiP window is no longer visible, regardless of callback order.
  private boolean mCobraActivityStarted=false;
  private boolean mCobraPipWasActive=false;
  private boolean mCobraPipDismissed=false;
  private boolean mCobraBrowseOnResume=false;
  private static final String COBRA_OPEN_BROWSE="cobra_open_browse";
  private static final String COBRA_EXPLICIT_STOP="cobra_playback_explicitly_stopped";
  private InfinityExtendedBackgroundService.MiniPlaybackOwner mCobraMiniOwner;

  @Override protected void onStart(){
    super.onStart();mCobraActivityStarted=true;
  }

  @Override protected void onNewIntent(Intent intent){
    super.onNewIntent(intent);setIntent(intent);
    if(intent!=null&&intent.getBooleanExtra(COBRA_OPEN_BROWSE,false)){
      intent.removeExtra(COBRA_OPEN_BROWSE);mCobraBrowseOnResume=true;
      if(mCobraRotationResumed)cobraConsumeBrowseRequest();
    }
  }

  private void cobraConsumeBrowseRequest(){
    Intent intent=getIntent();
    if(intent!=null&&intent.getBooleanExtra(COBRA_OPEN_BROWSE,false)){
      intent.removeExtra(COBRA_OPEN_BROWSE);mCobraBrowseOnResume=true;
    }
    if(!mCobraBrowseOnResume)return;
    mCobraBrowseOnResume=false;
    // Returning through the experience chooser is navigation, not a play command.
    // Native PiP expansion has no browse extra and retains fullscreen instead.
    if(mCobraPipDismissed){
      mCobraPreviewAutoplayAllowed=false;
      if(mRoot!=null)showCobraPrimaryView();
    }else if(mPlayerOverlay!=null){
      clearCobraPlayerLockState(false);closeFullscreenToCobraView();
    }else if(mMultiOverlay!=null){
      releaseMulti();showCobraPrimaryView();
    }else if(mRoot!=null&&mCobraGuideShell!=null){showCobraPrimaryView();}
  }

  private void cobraMarkExplicitPlayback(){
    mCobraPipDismissed=false;mCobraPreviewAutoplayAllowed=true;
    if(mPrefs!=null)mPrefs.edit().remove(COBRA_EXPLICIT_STOP).apply();
  }

  private void cobraStopDismissedPip(){
    // Set the terminal latch BEFORE pause/release callbacks can run.
    mCobraPipDismissed=true;mCobraPipWasActive=false;mInPictureInPicture=false;
    mCobraBrowseOnResume=true;mBackgroundStopped=true;mCobraPreviewAutoplayAllowed=false;
    if(mPrefs!=null)mPrefs.edit().putBoolean(COBRA_EXPLICIT_STOP,true).apply();
    cobraEndMiniBackgroundPlayback();
    // A dismissed PiP is an explicit stop, never an automatic background pause.
    mBackgroundResumePlayers.clear();mRebuildShellAfterPlayer=false;
    java.util.IdentityHashMap<ExoPlayer,Boolean> sessions=new java.util.IdentityHashMap<>();
    if(mPlayer!=null)sessions.put(mPlayer,true);
    if(mCobraPreviewPlayer!=null)sessions.put(mCobraPreviewPlayer,true);
    if(mCobraCarryPlayer!=null)sessions.put(mCobraCarryPlayer,true);
    if(mCobraTransferPlayer!=null)sessions.put(mCobraTransferPlayer,true);
    if(mMultiPlayers!=null)for(ExoPlayer player:mMultiPlayers)if(player!=null)sessions.put(player,true);
    for(ExoPlayer player:sessions.keySet())try{player.pause();}catch(RuntimeException ignored){}
    closePlayer();stopCobraPreviewPlayerOnly();releaseMulti();releaseCobraTransferPlayer();
    // Disposing existing bindings also invalidates queued retry/auto-next callbacks.
    mBackgroundResumePlayers.clear();configureCobraPip(false);
  }

  private boolean cobraMiniBackgroundStillOwned(){
    return mCobraMiniBackgroundActive&&mCobraMiniOwner!=null
        &&InfinityExtendedBackgroundService.isMiniPlaybackCurrent(mCobraMiniOwner);
  }

  private void cobraBackgroundTask(){
    mCobraMiniBackgroundActive=cobraBeginMiniBackgroundPlayback();
    moveTaskToBack(true);
  }

  // Geometry is resolved against CURRENT parent/window bounds on every measure.
  // Artwork may style a panel, but cannot move a video-settings submenu to mid-screen.
  private final class CobraVideoSettingsSheet extends FrameLayout {
    private android.view.WindowInsets currentInsets;
    CobraVideoSettingsSheet(){super(InfinityLiveActivity.this);}
    @Override public android.view.WindowInsets onApplyWindowInsets(android.view.WindowInsets insets){
      currentInsets=insets;requestLayout();return super.onApplyWindowInsets(insets);
    }
    private android.graphics.Rect safe(int width,int height){
      int left=0,top=0,right=0,bottom=0;
      if(Build.VERSION.SDK_INT>=23){
        android.view.WindowInsets insets=currentInsets!=null?currentInsets:getRootWindowInsets();
        if(insets!=null){
          left=insets.getSystemWindowInsetLeft();top=insets.getSystemWindowInsetTop();
          right=insets.getSystemWindowInsetRight();bottom=insets.getSystemWindowInsetBottom();
          if(Build.VERSION.SDK_INT>=28&&insets.getDisplayCutout()!=null){
            android.view.DisplayCutout cutout=insets.getDisplayCutout();
            left=Math.max(left,cutout.getSafeInsetLeft());top=Math.max(top,cutout.getSafeInsetTop());
            right=Math.max(right,cutout.getSafeInsetRight());bottom=Math.max(bottom,cutout.getSafeInsetBottom());
          }
          // Subtract insets already consumed by the parent (avoid double padding).
          View decor=getWindow().getDecorView();int[] origin=new int[2],local=new int[2];
          decor.getLocationInWindow(origin);getLocationInWindow(local);
          left=Math.max(0,origin[0]+left-local[0]);top=Math.max(0,origin[1]+top-local[1]);
          if(decor.getWidth()>0)right=Math.max(0,local[0]+width-(origin[0]+decor.getWidth()-right));
          if(decor.getHeight()>0)bottom=Math.max(0,local[1]+height-(origin[1]+decor.getHeight()-bottom));
        }
      }
      int gap=dp(12);
      return new android.graphics.Rect(Math.min(width/2,left+gap),Math.min(height/2,top+gap),
          Math.max(width/2,width-right-gap),Math.max(height/2,height-bottom-gap));
    }
    @Override protected void onMeasure(int widthSpec,int heightSpec){
      int width=MeasureSpec.getSize(widthSpec),height=MeasureSpec.getSize(heightSpec);
      setMeasuredDimension(width,height);
      android.graphics.Rect bounds=safe(width,height);
      if(getChildCount()>0){
        View panel=getChildAt(0);
        int panelWidth=Math.min(bounds.width(),dp(vtheme().dimension("cobra.cobraOpenSheet.dimensions.13",440)));
        panel.measure(MeasureSpec.makeMeasureSpec(Math.max(1,panelWidth),MeasureSpec.EXACTLY),
            MeasureSpec.makeMeasureSpec(Math.max(1,bounds.height()),MeasureSpec.AT_MOST));
      }
    }
    @Override protected void onLayout(boolean changed,int left,int top,int right,int bottom){
      if(getChildCount()==0)return;
      android.graphics.Rect bounds=safe(right-left,bottom-top);View panel=getChildAt(0);
      int x=bounds.left+(bounds.width()-panel.getMeasuredWidth())/2;
      int y=Math.max(bounds.top,bounds.bottom-panel.getMeasuredHeight());
      panel.layout(x,y,x+panel.getMeasuredWidth(),y+panel.getMeasuredHeight());
    }
  }
