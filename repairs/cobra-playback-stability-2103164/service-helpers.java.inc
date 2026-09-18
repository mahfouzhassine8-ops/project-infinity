  public static final int COMMAND_PLAY=1,COMMAND_PAUSE=2,COMMAND_STOP=3;
  private static final String ACTION_MINI_COMMAND="com.projectinfinity.kodi.action.MINI_MEDIA_COMMAND";
  private static final String EXTRA_GENERATION="mini_generation",EXTRA_COMMAND="mini_command";
  public interface MiniPlaybackOwner {
    boolean available();int state();long position();void command(int command);void unavailable();
  }
  static final class MiniGrant {
    volatile boolean requested=false;volatile long generation=0;
    synchronized long grant(){requested=true;return ++generation;}
    synchronized void revoke(){requested=false;generation++;}
    synchronized boolean accepts(long value){return requested&&generation==value;}
  }
  private static final MiniGrant sMiniGrant=new MiniGrant();
  private static java.lang.ref.WeakReference<MiniPlaybackOwner> sMiniOwner=new java.lang.ref.WeakReference<>(null);
  private static java.lang.ref.WeakReference<InfinityExtendedBackgroundService> sInstance=new java.lang.ref.WeakReference<>(null);
  private static String sMiniTitle="Cobra Live";
  private long mMediaGeneration=-1;
  private boolean mReconciling=false,mTerminating=false;

  @Override public void onCreate(){super.onCreate();sInstance=new java.lang.ref.WeakReference<>(this);}

  private static void revokeMini(boolean pauseOwner){
    MiniPlaybackOwner owner=sMiniOwner.get();sMiniGrant.revoke();sMiniOwner=new java.lang.ref.WeakReference<>(null);sMiniPlayback=false;
    if(pauseOwner&&owner!=null)try{owner.unavailable();}catch(RuntimeException error){Log.w(TAG,"Mini owner cleanup failed",error);}
  }
  public static void refreshMiniPlayback(MiniPlaybackOwner owner){
    if(owner==null||sMiniOwner.get()!=owner||!sMiniGrant.requested)return;
    InfinityExtendedBackgroundService service=sInstance.get();
    if(service!=null)service.reconcileMiniAndContinuity();
  }
  public static void stopMiniPlayback(Context context,MiniPlaybackOwner owner){
    if(owner!=null&&sMiniOwner.get()==owner)stopMiniPlayback(context);
  }
  private static void dispatchMiniCommand(long generation,int command){
    if(command<COMMAND_PLAY||command>COMMAND_STOP||!sMiniGrant.accepts(generation))return;
    MiniPlaybackOwner owner=sMiniOwner.get();
    if(owner==null||!owner.available()){revokeMini(true);InfinityExtendedBackgroundService stale=sInstance.get();if(stale!=null)stale.reconcileMiniAndContinuity();return;}
    try{owner.command(command);}catch(RuntimeException error){Log.w(TAG,"Mini media command failed",error);revokeMini(true);}
    InfinityExtendedBackgroundService service=sInstance.get();if(service!=null)service.reconcileMiniAndContinuity();
  }
  private int reconcileMiniAndContinuity(){
    if(mReconciling||mTerminating)return START_NOT_STICKY;
    mReconciling=true;
    try{
      MiniPlaybackOwner owner=sMiniOwner.get();
      boolean mini=sMiniGrant.requested&&owner!=null&&owner.available();
      if(sMiniGrant.requested&&!mini)revokeMini(true);
      if(!notificationsAllowed(this)||(!mini&&!isEnabled(this))){endSession();return START_NOT_STICKY;}
      sMiniPlayback=mini;mMiniTitle=sMiniTitle;
      if(!mini)releaseMediaSession();
      ensureChannel();Notification notification=mini?buildMiniPlaybackNotification():buildNotification();
      if(Build.VERSION.SDK_INT>=34){
        int type=mini?ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PLAYBACK:ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE;
        if(mini&&isEnabled(this))type|=ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE;
        startForeground(NOTIFICATION_ID,notification,type);
      }else startForeground(NOTIFICATION_ID,notification);
      sRunning=true;return mini?START_NOT_STICKY:START_STICKY;
    }catch(RuntimeException error){Log.w(TAG,"Foreground promotion refused",error);endSession();return START_NOT_STICKY;}
    finally{mReconciling=false;}
  }
  private PendingIntent miniOpenPendingIntent(){
    Intent intent=new Intent(this,InfinityLiveActivity.class)
        .addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_SINGLE_TOP);
    int flags=PendingIntent.FLAG_UPDATE_CURRENT;if(Build.VERSION.SDK_INT>=23)flags|=PendingIntent.FLAG_IMMUTABLE;
    return PendingIntent.getActivity(this,10935,intent,flags);
  }
  private PendingIntent miniCommandPendingIntent(int command){
    Intent intent=new Intent(this,InfinityExtendedBackgroundService.class).setAction(ACTION_MINI_COMMAND)
        .setData(android.net.Uri.parse("infinity-cobra://mini/"+sMiniGrant.generation+"/"+command))
        .putExtra(EXTRA_GENERATION,sMiniGrant.generation).putExtra(EXTRA_COMMAND,command);
    int flags=PendingIntent.FLAG_UPDATE_CURRENT;if(Build.VERSION.SDK_INT>=23)flags|=PendingIntent.FLAG_IMMUTABLE;
    return PendingIntent.getService(this,10936+command,intent,flags);
  }

  private android.media.session.MediaSession.Callback cobraMiniMediaCallback(final long generation){
    return new android.media.session.MediaSession.Callback(){
      @Override public void onPlay(){dispatchMiniCommand(generation,COMMAND_PLAY);}
      @Override public void onPause(){dispatchMiniCommand(generation,COMMAND_PAUSE);}
      @Override public void onStop(){dispatchMiniCommand(generation,COMMAND_STOP);}
    };
  }
  private android.media.session.PlaybackState cobraMiniPlaybackState(MiniPlaybackOwner owner){
    int state=owner.state();
    return new android.media.session.PlaybackState.Builder()
        .setActions(android.media.session.PlaybackState.ACTION_PLAY|android.media.session.PlaybackState.ACTION_PAUSE|android.media.session.PlaybackState.ACTION_PLAY_PAUSE|android.media.session.PlaybackState.ACTION_STOP)
        .setState(state,owner.position(),state==android.media.session.PlaybackState.STATE_PLAYING?1f:0f,android.os.SystemClock.elapsedRealtime()).build();
  }
