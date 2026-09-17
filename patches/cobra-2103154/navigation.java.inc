// @replace showCobraViewModeMenu
  private void showCobraViewModeMenu(){
    LinearLayout rows=cobraOpenSheet("Choose your layout","Five different ways to watch the same live library","view-mode");boolean dark=cobraSheetIsDark();
    String[] descriptions={"Touch dashboard · full preview, live feed and bottom navigation","Broadcast guide · groups, channel column and programme timeline","Channel directory · small preview, dense rows, maximum visibility","Channel wall · large identity tiles and responsive columns","Watch-first · large theatre and a channel / upcoming queue"};
    for(int i=0;i<CobraModeLayout.MODES.length;i++){
      final String mode=CobraModeLayout.MODES[i];LinearLayout row=new LinearLayout(this);row.setGravity(Gravity.CENTER_VERTICAL);row.setPadding(dp(8),dp(8),dp(10),dp(8));row.setBackground(cobraModeSurface(16,false));row.setSelected(mode.equals(mCobraGuideStyle));row.setFocusable(true);row.setFocusableInTouchMode(false);row.setClickable(true);
      CobraModeThumbnail sketch=new CobraModeThumbnail(mode,dark);row.addView(sketch,new LinearLayout.LayoutParams(dp(88),dp(62)));
      LinearLayout copy=new LinearLayout(this);copy.setOrientation(LinearLayout.VERTICAL);TextView title=cobraText(cobraModeName(mode)+(mode.equals(mCobraGuideStyle)?"  ·  Selected":""),dark?Color.WHITE:cobraModeColor("text"),15);title.setTypeface(Typeface.create("sans-serif-medium",0));title.setSingleLine(true);copy.addView(title);
      TextView description=cobraText(descriptions[i],dark?0xffa6b5c6:cobraModeColor("muted"),11);description.setMaxLines(3);copy.addView(description);LinearLayout.LayoutParams cp=new LinearLayout.LayoutParams(0,-2,1);cp.leftMargin=dp(12);row.addView(copy,cp);
      row.setMinimumHeight(dp(88));row.setContentDescription(cobraModeName(mode)+", "+descriptions[i]+(mode.equals(mCobraGuideStyle)?", selected":""));row.setOnClickListener(v->cobraSwitchMode(mode));rows.addView(row,new LinearLayout.LayoutParams(-1,-2));
    }
  }
// @replace toggleCobraDrawer
  private void toggleCobraDrawer(){
    if(closeCobraExperienceDrawer())return;
    FrameLayout decor=(FrameLayout)getWindow().getDecorView();int screen=decor.getWidth()>0?decor.getWidth():getResources().getDisplayMetrics().widthPixels;
    int width=Math.min(screen-dp(24),Math.min(dp(340),Math.max(dp(236),Math.round(screen*.80f))));boolean dark=cobraModeDark();
    FrameLayout shield=new FrameLayout(this);shield.setTag("cobra_experience_drawer");shield.setClickable(true);shield.setBackgroundColor(0x4d000000);shield.setOnClickListener(v->closeCobraExperienceDrawer());
    LinearLayout panel=new LinearLayout(this);panel.setOrientation(LinearLayout.VERTICAL);panel.setClickable(true);panel.setBackgroundColor(cobraModeColor("rail"));panel.setPadding(dp(12),dp(12),dp(12),dp(12));
    if(Build.VERSION.SDK_INT>=23&&decor.getRootWindowInsets()!=null){android.view.WindowInsets in=decor.getRootWindowInsets();panel.setPadding(dp(12)+in.getSystemWindowInsetLeft(),dp(12)+in.getSystemWindowInsetTop(),dp(12),dp(12)+in.getSystemWindowInsetBottom());}
    LinearLayout header=new LinearLayout(this);header.setGravity(Gravity.CENTER_VERTICAL);TextView brand=cobraText("COBRA",cobraModeColor("text"),20);brand.setTypeface(Typeface.create("sans-serif-medium",0));brand.setLetterSpacing(.16f);header.addView(brand,new LinearLayout.LayoutParams(0,dp(52),1));header.addView(cobraIcon("back","Collapse navigation",dark,v->closeCobraExperienceDrawer()),new LinearLayout.LayoutParams(dp(48),dp(48)));panel.addView(header);
    ScrollView scroll=new ScrollView(this);scroll.setFillViewport(false);LinearLayout items=new LinearLayout(this);items.setOrientation(LinearLayout.VERTICAL);scroll.addView(items);panel.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
    cobraDrawerDestination(items,"search","Search","SEARCH",()->{if(mChannels.isEmpty()){mCobraInternalScreen="internal";showSearch();}else{if(mCobraGuideShell==null||!mCobraGuideShell.isAttachedToWindow())cobraShowGuideShell();cobraShowChannelSearch();}});
    cobraDrawerDestination(items,"play","Live TV","TV",()->{mCobraModeGroupsExpanded=true;mCobraGuideRoute="categories";if("mobile".equals(mCobraGuideStyle))mCobraGuideStyle="grid";cobraShowGuideShell();});
    cobraDrawerDestination(items,"source","Movies","MOVIES",()->{stopCobraPreview();mCobraInternalScreen="internal";showMovies();});
    cobraDrawerDestination(items,"source","Shows","SHOWS",()->{stopCobraPreview();mCobraInternalScreen="internal";showSeries();});
    cobraDrawerDestination(items,"record","Recordings","RECORDINGS",()->{stopCobraPreview();mCobraInternalScreen="internal";showRecordings();});
    cobraDrawerDestination(items,"favorite","My List","MY LIST",()->{stopCobraPreview();mCobraInternalScreen="internal";showWatchlist();});
    TextView layout=cobraText("VIEW MODES",cobraModeColor("muted"),10);layout.setLetterSpacing(.13f);layout.setPadding(dp(12),0,0,0);items.addView(layout,new LinearLayout.LayoutParams(-1,dp(38)));
    for(String mode:CobraModeLayout.MODES){final String key=mode;Button b=cobraTextButton(cobraModeName(mode),dark,()->{closeCobraExperienceDrawer();cobraSwitchMode(key);});b.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);b.setPadding(dp(18),0,dp(12),0);b.setSelected(mode.equals(mCobraGuideStyle));items.addView(b,new LinearLayout.LayoutParams(-1,dp(48)));}
    cobraDrawerDestination(items,"more","Settings","SETTINGS",()->{stopCobraPreview();mCobraInternalScreen="internal";showSettings();});
    LinearLayout footer=new LinearLayout(this);Button infinity=cobraTextButton("∞  Infinity",dark,()->{closeCobraExperienceDrawer();returnToInfinity();});infinity.setVisibility(mUi.destinationEnabled("INFINITY")?View.VISIBLE:View.GONE);Button power=cobraTextButton("Power",dark,()->{closeCobraExperienceDrawer();showCobraPowerMenu();});footer.addView(infinity,new LinearLayout.LayoutParams(0,dp(50),1));footer.addView(power,new LinearLayout.LayoutParams(0,dp(50),1));panel.addView(footer);
    shield.addView(panel,new FrameLayout.LayoutParams(width,-1,Gravity.LEFT));decor.addView(shield,new FrameLayout.LayoutParams(-1,-1));
    panel.setTranslationX(-width);panel.animate().translationX(0).setDuration(180).start();animateCobraDrawerShift(Math.min(width,screen*.28f));
  }
// @replace animateCobraDrawerShift
  private void animateCobraDrawerShift(float translation){
    // Header is a child of Stage: never translate both (the old drawer moved it twice).
    if(mStage!=null)mStage.animate().translationX(translation).setDuration(180).start();
    if(mHeader!=null)mHeader.setTranslationX(0f);mCobraDrawerShifted=translation!=0f;
  }
// @append
  private void cobraDrawerDestination(LinearLayout parent,String icon,String label,String destination,Runnable action){
    if(!mUi.destinationEnabled(destination))return;
    LinearLayout row=cobraSheetRow(icon,label,null,false,cobraModeDark(),()->{closeCobraExperienceDrawer();action.run();});parent.addView(row,new LinearLayout.LayoutParams(-1,dp(50)));
  }
  private final class CobraModeThumbnail extends View{
    final String mode;final boolean dark;final android.graphics.Paint paint=new android.graphics.Paint(3);
    CobraModeThumbnail(String key,boolean night){super(InfinityLiveActivity.this);mode=key;dark=night;setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);}
    void rect(android.graphics.Canvas c,float l,float t,float r,float b,int color){paint.setColor(color);c.drawRoundRect(l,t,r,b,2,2,paint);}
    @Override protected void onDraw(android.graphics.Canvas canvas){int save=canvas.save();canvas.scale(getWidth()/100f,getHeight()/70f);int line=dark?0xff637a90:0xff9db2c7,base=dark?0xff0b131d:0xffe4edf5,video=0xff3496bb;rect(canvas,0,0,100,70,base);
      if("grid".equals(mode)){rect(canvas,3,4,9,66,line);rect(canvas,12,4,30,66,line);rect(canvas,33,4,62,24,video);rect(canvas,66,5,96,10,line);rect(canvas,66,14,89,18,line);for(int y=30;y<66;y+=11){rect(canvas,33,y,51,y+8,line);rect(canvas,54,y,74,y+8,line);rect(canvas,77,y,97,y+8,line);}}
      else if("compact".equals(mode)){rect(canvas,70,4,96,18,video);rect(canvas,4,5,56,9,line);for(int y=24;y<66;y+=7){rect(canvas,4,y,40,y+3,line);rect(canvas,46,y,96,y+3,line);}}
      else if("cards".equals(mode)){rect(canvas,4,4,44,22,video);rect(canvas,50,7,94,12,line);for(int y=28;y<65;y+=20)for(int x=4;x<98;x+=32)rect(canvas,x,y,x+27,y+16,line);}
      else if("focus".equals(mode)){rect(canvas,4,4,64,49,video);rect(canvas,4,54,64,59,line);for(int y=4;y<65;y+=15)rect(canvas,71,y,96,y+10,line);}
      else{rect(canvas,4,4,96,28,video);rect(canvas,4,32,76,36,line);for(int y=42;y<60;y+=7){rect(canvas,4,y,13,y+5,line);rect(canvas,18,y,96,y+5,line);}rect(canvas,4,63,96,67,line);}canvas.restoreToCount(save);
    }
  }
