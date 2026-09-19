  // 2103177 final feature-freeze: display proof, local HLS timeshift, diagnostics and last-channel.
  private static final String COBRA_REFRESH_MODE="cobra_refresh_mode";
  private static final String COBRA_REFRESH_OVERLAY="cobra_refresh_overlay";
  private static final String COBRA_LOCAL_TIMESHIFT="cobra_local_timeshift";
  private static final String COBRA_SMART_BUFFER="cobra_smart_buffer";
  private static final String COBRA_PLAYBACK_DIAGNOSTICS="cobra_playback_diagnostics";
  private TextView mCobraRefreshOverlay,mCobraPlaybackDiagnosticsOverlay,mCobraTimeshiftLabel;
  private View mCobraTimeshiftRow;
  private android.widget.SeekBar mCobraTimeshiftScrubber;
  private boolean mCobraTimeshiftDragging;
  private long mCobraFrameWindowStart,mCobraFrameCount;
  private float mCobraUiFps;
  private int mCobraRefreshRequestedModeId;
  private float mCobraRefreshRequestedHz,mCobraRefreshUserHz;
  private String mCobraRefreshReason="system";
  private final android.view.Choreographer.FrameCallback mCobraFrameMeter=new android.view.Choreographer.FrameCallback(){
    @Override public void doFrame(long frameTimeNanos){
      if(!mCobraHealthForeground||!cobraRefreshOverlayEnabled())return;
      long now=android.os.SystemClock.elapsedRealtime();if(mCobraFrameWindowStart==0)mCobraFrameWindowStart=now;mCobraFrameCount++;
      long elapsed=now-mCobraFrameWindowStart;if(elapsed>=1000L){mCobraUiFps=(float)(mCobraFrameCount*1000d/Math.max(1,elapsed));mCobraFrameCount=0;mCobraFrameWindowStart=now;cobraUpdateRefreshOverlay();}
      android.view.Choreographer.getInstance().postFrameCallback(this);
    }
  };

  static final class CobraDisplayPolicy {
    static float requested(String mode,float max,boolean saver,boolean thermal,boolean video){
      if(video)return 0f;float cap;
      if("60".equals(mode))cap=60f;else if("90".equals(mode))cap=90f;else if("120".equals(mode))cap=120f;else cap=max;
      if("auto".equals(mode))cap=Math.min(max,120f);
      if(saver||thermal)cap=Math.min(cap,60f);
      return Math.max(0f,Math.min(max,cap));
    }
    static float choose(float[] supported,float target){float best=0f;for(float hz:supported)if(hz<=target+.5f&&hz>best)best=hz;return best;}
    static String status(float requested,float active){if(requested<=0f)return "VIDEO MATCH";return Math.abs(active-requested)<=1.0f?"ACTIVE":"FALLBACK";}
  }
  private String cobraRefreshMode(){String value=mPrefs.getString(COBRA_REFRESH_MODE,"auto");return java.util.Arrays.asList("auto","60","90","120","max").contains(value)?value:"auto";}
  private boolean cobraRefreshOverlayEnabled(){return mPrefs.getBoolean(COBRA_REFRESH_OVERLAY,false);}
  private android.view.Display cobraCurrentDisplay(){return Build.VERSION.SDK_INT>=30?getDisplay():getWindowManager().getDefaultDisplay();}
  private boolean cobraRefreshVideoOwns(){return mPlayerOverlay!=null||mMultiOverlay!=null||isCobraInPictureInPicture();}
  private boolean cobraBatterySaver(){android.os.PowerManager p=(android.os.PowerManager)getSystemService(Context.POWER_SERVICE);return p!=null&&p.isPowerSaveMode();}
