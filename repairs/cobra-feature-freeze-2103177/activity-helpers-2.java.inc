  private boolean cobraThermalLimited(){if(Build.VERSION.SDK_INT<29)return false;android.os.PowerManager p=(android.os.PowerManager)getSystemService(Context.POWER_SERVICE);return p!=null&&p.getCurrentThermalStatus()>=android.os.PowerManager.THERMAL_STATUS_SEVERE;}
  private float cobraDisplayMaxHz(){android.view.Display d=cobraCurrentDisplay();if(d==null)return 0f;if(Build.VERSION.SDK_INT<23)return d.getRefreshRate();android.view.Display.Mode current=d.getMode();float max=current.getRefreshRate();for(android.view.Display.Mode mode:d.getSupportedModes())if(mode.getPhysicalWidth()==current.getPhysicalWidth()&&mode.getPhysicalHeight()==current.getPhysicalHeight())max=Math.max(max,mode.getRefreshRate());return max;}
  private float cobraDisplayActiveHz(){android.view.Display d=cobraCurrentDisplay();return d==null?0f:(Build.VERSION.SDK_INT>=23?d.getMode().getRefreshRate():d.getRefreshRate());}
  private float cobraRefreshUserTarget(float max){String mode=cobraRefreshMode();if("60".equals(mode))return 60f;if("90".equals(mode))return 90f;if("120".equals(mode))return 120f;if("auto".equals(mode))return Math.min(max,120f);return max;}
  private void cobraClearRefreshRequest(){try{WindowManager.LayoutParams a=getWindow().getAttributes();if(Build.VERSION.SDK_INT>=23&&a.preferredDisplayModeId!=0){a.preferredDisplayModeId=0;getWindow().setAttributes(a);}}catch(RuntimeException ignored){}mCobraRefreshRequestedModeId=0;mCobraRefreshRequestedHz=0f;}
  private void cobraApplyRefreshPolicy(String reason){
    try{
      android.view.Display d=cobraCurrentDisplay();if(d==null){cobraClearRefreshRequest();return;}float max=cobraDisplayMaxHz();mCobraRefreshUserHz=cobraRefreshUserTarget(max);
      float target=CobraDisplayPolicy.requested(cobraRefreshMode(),max,cobraBatterySaver(),cobraThermalLimited(),cobraRefreshVideoOwns());mCobraRefreshReason=reason;
      if(target<=0f||Build.VERSION.SDK_INT<23){cobraClearRefreshRequest();cobraUpdateRefreshOverlay();return;}android.view.Display.Mode current=d.getMode();
      android.view.Display.Mode best=null;for(android.view.Display.Mode mode:d.getSupportedModes())if(mode.getPhysicalWidth()==current.getPhysicalWidth()&&mode.getPhysicalHeight()==current.getPhysicalHeight()&&mode.getRefreshRate()<=target+.5f&&(best==null||mode.getRefreshRate()>best.getRefreshRate()))best=mode;
      if(best==null){cobraClearRefreshRequest();cobraUpdateRefreshOverlay();return;}WindowManager.LayoutParams a=getWindow().getAttributes();if(a.preferredDisplayModeId!=best.getModeId()){a.preferredDisplayModeId=best.getModeId();getWindow().setAttributes(a);}mCobraRefreshRequestedModeId=best.getModeId();mCobraRefreshRequestedHz=best.getRefreshRate();cobraUpdateRefreshOverlay();
    }catch(RuntimeException failure){cobraClearRefreshRequest();}
  }
  private String cobraRefreshStatus(){float max=cobraDisplayMaxHz(),active=cobraDisplayActiveHz();float requested=mCobraRefreshUserHz>0?mCobraRefreshUserHz:cobraRefreshUserTarget(max);String status=cobraRefreshVideoOwns()?"VIDEO MATCH":CobraDisplayPolicy.status(requested,active);if(!cobraRefreshVideoOwns()&&cobraBatterySaver())status="BATTERY FALLBACK";else if(!cobraRefreshVideoOwns()&&cobraThermalLimited())status="THERMAL FALLBACK";return String.format(Locale.US,"Requested %.2f Hz • Active %.2f Hz • Max %.2f Hz • %s",requested,active,max,status);}
  private String cobraRefreshLabel(){String mode=cobraRefreshMode();return "max".equals(mode)?"MAX":"auto".equals(mode)?"AUTO":mode+" HZ";}
  private void showCobraDisplayPerformancePicker(){
    LinearLayout rows=cobraOpenSheet("Display & Performance",cobraRefreshStatus(),"display-performance");boolean dark=cobraSheetIsDark();
    String[] values={"auto","60","90","120","max"},labels={"Auto","60 Hz","90 Hz","120 Hz","Maximum supported"};for(int i=0;i<values.length;i++){final String value=values[i];rows.addView(cobraSheetRow("settings",labels[i],value.equals(cobraRefreshMode())?"Selected":null,false,dark,()->{mPrefs.edit().putString(COBRA_REFRESH_MODE,value).apply();cobraApplyRefreshPolicy("setting");showCobraDisplayPerformancePicker();}));}
    rows.addView(cobraSheetRow("health","Refresh-rate proof overlay",cobraRefreshOverlayEnabled()?"On • Android active Hz + measured UI FPS":"Off",false,dark,()->{mPrefs.edit().putBoolean(COBRA_REFRESH_OVERLAY,!cobraRefreshOverlayEnabled()).apply();cobraStartFrameMeter();cobraUpdateRefreshOverlay();showCobraDisplayPerformancePicker();}));
    cobraInfoText(rows,"Cobra requests high refresh only for its interface. Fullscreen video, Multi-View and PiP release the request so playback cadence remains owned by Android/Media3.");
  }
  private void cobraStartFrameMeter(){android.view.Choreographer.getInstance().removeFrameCallback(mCobraFrameMeter);mCobraFrameWindowStart=0;mCobraFrameCount=0;if(cobraRefreshOverlayEnabled()&&mCobraHealthForeground)android.view.Choreographer.getInstance().postFrameCallback(mCobraFrameMeter);else cobraRemoveRefreshOverlay();}
  private void cobraStopFrameMeter(){android.view.Choreographer.getInstance().removeFrameCallback(mCobraFrameMeter);mCobraFrameWindowStart=0;mCobraFrameCount=0;cobraRemoveRefreshOverlay();}
  private void cobraRemoveRefreshOverlay(){if(mCobraRefreshOverlay!=null&&mCobraRefreshOverlay.getParent() instanceof android.view.ViewGroup)((android.view.ViewGroup)mCobraRefreshOverlay.getParent()).removeView(mCobraRefreshOverlay);mCobraRefreshOverlay=null;}
  private int cobraOverlaySafeTop(){int top=dp(8);if(Build.VERSION.SDK_INT>=23&&getWindow().getDecorView().getRootWindowInsets()!=null)top+=getWindow().getDecorView().getRootWindowInsets().getSystemWindowInsetTop();return top;}
  private void cobraUpdateRefreshOverlay(){
    if(!cobraRefreshOverlayEnabled()||isFinishing()){cobraRemoveRefreshOverlay();return;}FrameLayout decor=(FrameLayout)getWindow().getDecorView();if(mCobraRefreshOverlay==null){TextView label=cobraText("",Color.WHITE,10);label.setTag("cobra_refresh_proof_overlay");label.setBackground(surface(0xc9000000,10,0x55ffffff,1));label.setPadding(dp(10),dp(5),dp(10),dp(5));label.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);mCobraRefreshOverlay=label;FrameLayout.LayoutParams p=new FrameLayout.LayoutParams(-2,dp(34),Gravity.TOP|Gravity.RIGHT);p.topMargin=cobraOverlaySafeTop();p.rightMargin=dp(10);decor.addView(label,p);}mCobraRefreshOverlay.setText(String.format(Locale.US,"DISPLAY %.2f Hz  •  UI %.0f fps",cobraDisplayActiveHz(),mCobraUiFps));mCobraRefreshOverlay.bringToFront();
  }

  static final class CobraBufferPolicy {
    static String mode(String value){return "resilient".equals(value)?"resilient":"auto";}
    static int minMs(String mode){return "resilient".equals(mode)?20000:50000;}
    static int maxMs(String mode){return "resilient".equals(mode)?90000:50000;}
    static int rebufferMs(String mode){return "resilient".equals(mode)?8000:5000;}
  }
  static final class CobraTimeshiftPolicy {
    static final long WINDOW_MS=120000L,CACHE_CAP_BYTES=160L*1024L*1024L,CACHE_TRIM_BYTES=150L*1024L*1024L;
    static boolean extendable(String text){return text!=null&&text.startsWith("#EXTM3U")&&!text.contains("#EXT-X-ENDLIST")&&!text.contains("#EXT-X-PART")&&!text.contains("#EXT-X-MAP")&&!text.contains("#EXT-X-BYTERANGE")&&!text.contains("#EXT-X-KEY")&&!text.contains("#EXT-X-DISCONTINUITY");}
