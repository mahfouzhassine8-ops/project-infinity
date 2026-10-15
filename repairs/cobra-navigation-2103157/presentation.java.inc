  // Independent preference: system decides WHEN; this decides WHICH dark palette.
  private static final String COBRA_SYSTEM_DARK = "cobra_system_dark_variant";
  private final CobraNavigationEpoch mCobraNavigation = new CobraNavigationEpoch();
  private String mCobraStageTitle = "";

  private static final class CobraNavigationEpoch {
    private long generation;
    long advance(){return ++generation;}
    long current(){return generation;}
    boolean accepts(long request){return request==generation;}
  }
  private static final class CobraAppearancePolicy {
    static String dark(String value){return "oled".equals(value)?"oled":"dark";}
    static String effective(String mode,String variant,boolean night){
      if("system".equals(mode))return night?dark(variant):"light";
      return "light".equals(mode)?"light":"oled".equals(mode)?"oled":"dark";
    }
  }
  private String cobraSystemDarkVariant(){return CobraAppearancePolicy.dark(mPrefs==null?"dark":mPrefs.getString(COBRA_SYSTEM_DARK,"dark"));}
  private String cobraDarkVariantName(){return "oled".equals(cobraSystemDarkVariant())?"True OLED Black":"Dark";}
  private void cobraApplyAppearanceSettings(){
    mCobraPaletteSourceStamp=Long.MIN_VALUE;mCobraPaletteCache=null;mTheme=Theme.load(this);
    if(mRoot!=null)mRoot.setBackgroundColor(cobraThemeColor("background",mTheme.background));
    if(mPlayerOverlay!=null||mMultiOverlay!=null){toast("Appearance saved; browsing will use your selection");return;}
    if(mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow()){
      cobraRestyleGuide();cobraLayoutGuide();cobraRenderGuideBrowser();
    }else{buildShell();showSettings();}
  }
  private void showCobraSystemDarkPicker(){
    LinearLayout rows=cobraOpenSheet("System dark appearance","Used whenever Follow System switches Cobra to dark mode.","system-dark-palette");boolean dark=cobraSheetIsDark();
    for(String value:new String[]{"dark","oled"}){
      final String chosen=value;String label="oled".equals(value)?"True OLED Black":"Dark";
      LinearLayout row=cobraSheetRow("oled".equals(value)?"focus":"more",label+(value.equals(cobraSystemDarkVariant())?" • Selected":""),"oled".equals(value)?"Black surfaces for OLED displays":"Soft charcoal surfaces",false,dark,()->{
        mPrefs.edit().putString(COBRA_SYSTEM_DARK,chosen).apply();cobraApplyAppearanceSettings();
      });row.setTag("cobra-system-dark:"+value);rows.addView(row);
    }
  }
  private void cobraPublishNavigation(long ticket,Runnable action){
    publishCobraUi(()->{if(mCobraNavigation.accepts(ticket))action.run();});
  }
  private void cobraOpenLiveTv(){
    // A TV entry point opens a GUIDE, not a page filled only with category names.
    mCobraGuideRoute="channels";mCobraModeGroupsExpanded=true;
    if("mobile".equals(mCobraGuideStyle))mCobraGuideStyle="grid";
    cobraShowGuideShell();
  }
  private void cobraOpenTvDirectory(boolean sources){
    if(!"grid".equals(mCobraGuideStyle)){mCobraGuideRoute=sources?"sources":"categories";cobraRenderGuideBrowser();return;}
    if(mCobraModeLayout!=null&&mCobraModeLayout.width>=760){
      mCobraModeGroupsExpanded=true;mCobraGuideRoute=sources?"sources":"channels";
      cobraLayoutGuide();cobraRenderGuideBrowser();mCobraGuideDirectory.requestFocus();return;
    }
    // Narrow screens get a contextual side drawer over the guide, NEVER a replacement list page.
    closeCobraActionSheet();FrameLayout decor=(FrameLayout)getWindow().getDecorView();
    mCobraSheetPreviousFocus=getCurrentFocus();mCobraSheetKind="tv-directory";
    FrameLayout scrim=new FrameLayout(this);mCobraActionSheet=scrim;scrim.setTag("cobra_tv_directory_overlay");scrim.setBackgroundColor(0x66000000);scrim.setClickable(true);scrim.setOnClickListener(v->closeCobraActionSheet());
    LinearLayout panel=new LinearLayout(this);panel.setOrientation(LinearLayout.VERTICAL);panel.setClickable(true);panel.setBackgroundColor(cobraModeColor("rail"));panel.setPadding(dp(6),dp(8),dp(6),dp(8));
    LinearLayout heading=new LinearLayout(this);heading.setGravity(Gravity.CENTER_VERTICAL);
    TextView label=cobraText(sources?"Playlists":"Channel groups",cobraModeColor("text"),16);label.setTypeface(Typeface.create("sans-serif-medium",0));label.setPadding(dp(8),0,0,0);
    heading.addView(label,new LinearLayout.LayoutParams(0,dp(48),1));heading.addView(cobraIcon("close","Close channel groups",cobraModeDark(),v->closeCobraActionSheet()),new LinearLayout.LayoutParams(dp(48),dp(48)));panel.addView(heading);
    cobraDirectory(panel,sources);
    int w=decor.getWidth()>0?decor.getWidth():getResources().getDisplayMetrics().widthPixels,h=decor.getHeight()>0?decor.getHeight():getResources().getDisplayMetrics().heightPixels;
    int top=dp(64),bottom=dp(20);if(Build.VERSION.SDK_INT>=23&&decor.getRootWindowInsets()!=null){top+=decor.getRootWindowInsets().getSystemWindowInsetTop();bottom+=decor.getRootWindowInsets().getSystemWindowInsetBottom();}
    FrameLayout.LayoutParams position=new FrameLayout.LayoutParams(Math.max(1,Math.min(dp(312),Math.round(w*.82f))),Math.max(1,h-top-bottom),Gravity.TOP|Gravity.LEFT);position.topMargin=top;position.bottomMargin=bottom;
    scrim.addView(panel,position);decor.addView(scrim,new FrameLayout.LayoutParams(-1,-1));
    panel.setTranslationX(-position.width);panel.animate().translationX(0f).setDuration(160).start();heading.requestFocus();
  }
