// COBRA-APPEND
  private FrameLayout mCobraSheetOverlay;
  private LinearLayout mCobraSheetBody;
  private String mCobraSheetKind = "";
  private Channel mCobraScheduleChannel;
  private FrameLayout mCobraPlayerDrawer;
  private String mCobraPlayerDrawerMode = "", mCobraPlayerBrowserFilter = "ALL";
  private android.widget.ListView mCobraPlayerBrowserList;
  private boolean mCobraPlayerBrowserCategories;

  private TextView cobraText(String value,int color,int size,int gravity) {
    TextView view=new TextView(this);view.setText(value);view.setTextColor(color);view.setTextSize(size);view.setGravity(gravity);
    view.setPadding(0,0,0,0);view.setIncludeFontPadding(false);return view;
  }
  private String cobraClock(long time) { return android.text.format.DateFormat.getTimeFormat(this).format(new Date(time)); }
  private int cobraWindowWidth() {
    int size = getWindow().getDecorView().getWidth();
    return size > 0 ? size : getResources().getDisplayMetrics().widthPixels;
  }
  private int cobraWindowHeight() {
    int size = getWindow().getDecorView().getHeight();
    return size > 0 ? size : getResources().getDisplayMetrics().heightPixels;
  }
  private boolean cobraNarrowWindow() { return cobraWindowWidth() < dp(600) || cobraWindowHeight() > cobraWindowWidth(); }
  private int cobraInk() { return cobraThemeColor("text", mTheme.text); }
  private int cobraMutedInk() { return cobraThemeColor("muted", mTheme.muted); }
  private int cobraPanelColor() { return cobraThemeColor("panel", mTheme.panel); }
  private android.graphics.drawable.Drawable cobraTouchSurface(boolean selected, int radius) {
    int accent = cobraThemeColor("accent", mTheme.accent);
    return new android.graphics.drawable.RippleDrawable(android.content.res.ColorStateList.valueOf(cobraAlpha(accent, 45)),
        surface(selected ? cobraAlpha(accent, 28) : Color.TRANSPARENT, radius,
            selected ? cobraAlpha(accent, 140) : Color.TRANSPARENT, 1),
        surface(Color.WHITE, radius, Color.TRANSPARENT, 0));
  }
  private Button cobraTextAction(String label, boolean selected) {
    Button button = new Button(this); button.setText(label); button.setTextColor(cobraInk());
    button.setTextSize(12); button.setAllCaps(false); button.setGravity(Gravity.CENTER);
    button.setMinHeight(dp(48)); button.setMinimumHeight(dp(48)); button.setMinWidth(0); button.setMinimumWidth(0);
    button.setPadding(dp(8), 0, dp(8), 0); button.setStateListAnimator(null);
    button.setBackground(cobraTouchSurface(selected, 12)); button.setContentDescription(label);
    return button;
  }
  private final class CobraIconButton extends Button {
    final String icon;
    final android.graphics.Paint ink = new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
    CobraIconButton(String icon, String description) {
      super(InfinityLiveActivity.this); this.icon = icon; setContentDescription(description);
      setMinWidth(dp(48)); setMinHeight(dp(48)); setMinimumWidth(dp(48)); setMinimumHeight(dp(48));
      setPadding(0, 0, 0, 0); setStateListAnimator(null); setFocusable(true); setFocusableInTouchMode(false);
      setBackground(new android.graphics.drawable.RippleDrawable(
          android.content.res.ColorStateList.valueOf(Color.argb(90,255,255,255)),
          surface(Color.TRANSPARENT, 28, Color.TRANSPARENT, 0), surface(Color.WHITE, 28, Color.TRANSPARENT, 0)));
    }
    @Override protected void onDraw(android.graphics.Canvas canvas) {
      int save = canvas.save(); canvas.translate(getWidth() / 2f, getHeight() / 2f);
      float unit = dp(1); canvas.scale(unit, unit);
      ink.setColor(isEnabled() ? Color.WHITE : Color.GRAY); ink.setStyle(android.graphics.Paint.Style.STROKE);
      ink.setStrokeWidth(1.8f); ink.setStrokeCap(android.graphics.Paint.Cap.ROUND); ink.setStrokeJoin(android.graphics.Paint.Join.ROUND);
      if (isFocused()) { canvas.drawCircle(0,0,21,ink); }
      String key = icon;
      if ("play".equals(key) && getText().toString().contains("❚")) key = "pause";
      if ("play".equals(key)) {
        android.graphics.Path p = new android.graphics.Path(); p.moveTo(-5,-9); p.lineTo(9,0); p.lineTo(-5,9); p.close();
        ink.setStyle(android.graphics.Paint.Style.FILL); canvas.drawPath(p, ink);
      } else if ("pause".equals(key)) {
        ink.setStyle(android.graphics.Paint.Style.FILL); canvas.drawRoundRect(-7,-9,-3,9,1,1,ink); canvas.drawRoundRect(3,-9,7,9,1,1,ink);
      } else if ("previous".equals(key) || "next".equals(key)) {
        if ("previous".equals(key)) canvas.scale(-1,1);
        canvas.drawLine(7,-8,7,8,ink); android.graphics.Path p = new android.graphics.Path(); p.moveTo(-8,-8); p.lineTo(3,0); p.lineTo(-8,8); p.close(); canvas.drawPath(p,ink);
      } else if ("back".equals(key) || "close".equals(key)) {
        if ("back".equals(key)) { canvas.drawLine(-9,0,9,0,ink); canvas.drawLine(-9,0,-2,-7,ink); canvas.drawLine(-9,0,-2,7,ink); }
        else { canvas.drawLine(-6,-6,6,6,ink); canvas.drawLine(-6,6,6,-6,ink); }
      } else if ("lock".equals(key)) {
        canvas.drawRoundRect(-7,-1,7,10,2,2,ink); canvas.drawArc(-5,-10,5,3,180,180,false,ink); canvas.drawLine(0,3,0,6,ink);
      } else if ("aspect".equals(key) || "fullscreen".equals(key)) {
        canvas.drawLine(-10,-3,-10,-7,ink); canvas.drawLine(-10,-7,-4,-7,ink);
        canvas.drawLine(10,-3,10,-7,ink); canvas.drawLine(10,-7,4,-7,ink);
        canvas.drawLine(-10,3,-10,7,ink); canvas.drawLine(-10,7,-4,7,ink);
        canvas.drawLine(10,3,10,7,ink); canvas.drawLine(10,7,4,7,ink);
      } else if ("multi".equals(key)) {
        for (int x : new int[]{-10,2}) for (int y : new int[]{-8,2}) canvas.drawRoundRect(x,y,x+8,y+6,1,1,ink);
      } else if ("channels".equals(key)) {
        for (int y : new int[]{-7,0,7}) { canvas.drawCircle(-8,y,1,ink); canvas.drawLine(-2,y,9,y,ink); }
      } else if ("favorite".equals(key)) {
        android.graphics.Path p = new android.graphics.Path(); p.moveTo(0,9); p.cubicTo(-19,-3,-7,-15,0,-6); p.cubicTo(7,-15,19,-3,0,9);
        if (getText().toString().contains("♥")) { ink.setStyle(android.graphics.Paint.Style.FILL); ink.setColor(cobraThemeColor("accent",mTheme.accent)); }
        canvas.drawPath(p,ink);
      } else if ("audio".equals(key)) {
        canvas.drawRoundRect(-10,-7,10,7,2,2,ink); ink.setStyle(android.graphics.Paint.Style.FILL); ink.setTextSize(9); ink.setTextAlign(android.graphics.Paint.Align.CENTER); canvas.drawText("CC",0,3,ink);
      } else if ("more".equals(key)) {
        ink.setStyle(android.graphics.Paint.Style.FILL); for (int x : new int[]{-7,0,7}) canvas.drawCircle(x,0,1.8f,ink);
      } else {
        ink.setStyle(android.graphics.Paint.Style.FILL); ink.setTextSize(15); ink.setTextAlign(android.graphics.Paint.Align.CENTER); canvas.drawText("+",0,5,ink);
      }
      canvas.restoreToCount(save);
    }
  }
  private Button cobraIconButton(String key, String description) { return new CobraIconButton(key, description); }

  private LinearLayout cobraSheetHeading(LinearLayout panel, String title, String subtitle, Runnable close) {
    LinearLayout header = new LinearLayout(this); header.setGravity(Gravity.CENTER_VERTICAL);
    LinearLayout copy = new LinearLayout(this); copy.setOrientation(LinearLayout.VERTICAL);
    TextView heading = cobraText(title, cobraInk(), 18, Gravity.LEFT | Gravity.CENTER_VERTICAL);
    heading.setTypeface(null, Typeface.BOLD); copy.addView(heading, new LinearLayout.LayoutParams(-1,dp(28)));
    if (subtitle != null && !subtitle.isEmpty()) {
      TextView detail = cobraText(subtitle,cobraMutedInk(),12,Gravity.LEFT); detail.setMaxLines(2);
      copy.addView(detail,new LinearLayout.LayoutParams(-1,-2));
    }
    header.addView(copy,new LinearLayout.LayoutParams(0,-2,1));
    Button dismiss = cobraTextAction("✕",false); dismiss.setContentDescription("Close " + title);
    dismiss.setOnClickListener(v -> close.run()); header.addView(dismiss,new LinearLayout.LayoutParams(dp(48),dp(48)));
    panel.addView(header,new LinearLayout.LayoutParams(-1,-2));
    View divider = new View(this); divider.setBackgroundColor(cobraThemeColor("line",mTheme.line));
    LinearLayout.LayoutParams line = new LinearLayout.LayoutParams(-1,dp(1)); line.topMargin=dp(12);line.bottomMargin=dp(8);panel.addView(divider,line);
    return panel;
  }
  private LinearLayout cobraOpenSheet(String title, String subtitle, String kind) {
    closeCobraSheet(); mCobraSheetKind = kind;
    FrameLayout decor = (FrameLayout)getWindow().getDecorView();
    FrameLayout overlay = new FrameLayout(this); mCobraSheetOverlay=overlay;
    overlay.setTag("cobra_themed_sheet"); overlay.setBackgroundColor(Color.argb(104,0,0,0));
    overlay.setClickable(true); overlay.setOnClickListener(v -> closeCobraSheet());
    final int maxHeight=Math.max(dp(120),cobraWindowHeight()-dp(40));
    LinearLayout panel = new LinearLayout(this) {
      @Override protected void onMeasure(int w,int h) { super.onMeasure(w,View.MeasureSpec.makeMeasureSpec(maxHeight,View.MeasureSpec.AT_MOST)); }
    };
    panel.setOrientation(LinearLayout.VERTICAL);panel.setPadding(dp(18),dp(16),dp(18),dp(16));panel.setClickable(true);
    panel.setBackground(surface(cobraPanelColor(),24,cobraThemeColor("line",mTheme.line),1));
    cobraSheetHeading(panel,title,subtitle,() -> closeCobraSheet());
    ScrollView scroll=new ScrollView(this);scroll.setFillViewport(false);
    mCobraSheetBody=new LinearLayout(this);mCobraSheetBody.setOrientation(LinearLayout.VERTICAL);scroll.addView(mCobraSheetBody);
    panel.addView(scroll,new LinearLayout.LayoutParams(-1,-2));
    int width=cobraNarrowWindow()?-1:Math.min(dp(384),cobraWindowWidth()-dp(40));
    FrameLayout.LayoutParams p=new FrameLayout.LayoutParams(width,-2,cobraNarrowWindow()?Gravity.BOTTOM:Gravity.RIGHT|Gravity.CENTER_VERTICAL);
    p.setMargins(dp(12),dp(20),dp(12),dp(20));overlay.addView(panel,p);decor.addView(overlay,new FrameLayout.LayoutParams(-1,-1));
    panel.setAlpha(0f);panel.setTranslationY(dp(12));panel.animate().alpha(1f).translationY(0f).setDuration(170).start();
    return mCobraSheetBody;
  }
  private boolean closeCobraSheet() {
    if(mCobraSheetOverlay==null)return false;
    android.view.ViewParent parent=mCobraSheetOverlay.getParent();
    if(parent instanceof android.view.ViewGroup)((android.view.ViewGroup)parent).removeView(mCobraSheetOverlay);
    mCobraSheetOverlay=null;mCobraSheetBody=null;mCobraSheetKind="";mCobraScheduleChannel=null;return true;
  }
  private void cobraSheetAction(LinearLayout body,String symbol,String title,boolean destructive,Runnable command) {
    LinearLayout row=new LinearLayout(this);row.setGravity(Gravity.CENTER_VERTICAL);row.setPadding(dp(8),dp(4),dp(8),dp(4));
    row.setBackground(cobraTouchSurface(false,12));row.setFocusable(true);row.setContentDescription(title);
    TextView icon=cobraText(symbol,destructive?0xFFE45C68:cobraMutedInk(),18,Gravity.CENTER);
    TextView label=cobraText(title,destructive?0xFFE45C68:cobraInk(),14,Gravity.LEFT|Gravity.CENTER_VERTICAL);
    label.setMaxLines(2);label.setEllipsize(android.text.TextUtils.TruncateAt.END);
    row.addView(icon,new LinearLayout.LayoutParams(dp(36),dp(48)));row.addView(label,new LinearLayout.LayoutParams(0,dp(48),1));
    row.setOnClickListener(v -> {closeCobraSheet();command.run();});body.addView(row,new LinearLayout.LayoutParams(-1,dp(56)));
  }
  private void renderCobraScheduleSheet(Channel channel) {
    if(mCobraSheetBody==null||!"schedule".equals(mCobraSheetKind))return;
    mCobraSheetBody.removeAllViews();long now=System.currentTimeMillis();int count=0;
    for(GuideProgram program:cobraSchedule(channel)) {
      if(program.stop<=now||count++>=48)continue;
      cobraSheetAction(mCobraSheetBody,CobraCore.current(program.start,program.stop,now)?"▶":"◷",
          cobraClock(program.start)+" – "+cobraClock(program.stop)+"\n"+program.title,false,() -> showProgramActions(channel,program));
    }
    if(count==0){TextView note=cobraText(cobraGuideMessage(channel),cobraMutedInk(),14,Gravity.CENTER);note.setPadding(dp(8),dp(18),dp(8),dp(18));mCobraSheetBody.addView(note);}
    cobraSheetAction(mCobraSheetBody,"↻","Refresh guide",false,() -> {LiveSource source=sourceForChannel(channel);if(source!=null)loadGuideAsync(source);showProgramGuide(channel);});
  }

// COBRA-REPLACE showProgramGuide
  private void showProgramGuide(Channel channel) {
    if(channel==null)return;
    cobraOpenSheet(channel.name,"Programme schedule","schedule");mCobraScheduleChannel=channel;
    requestCobraGuideWindow(channel,true);renderCobraScheduleSheet(channel);
  }

// COBRA-REPLACE showProgramActions
  private void showProgramActions(Channel channel, GuideProgram program) {
    if(channel==null||program==null)return;long now=System.currentTimeMillis();
    LinearLayout body=cobraOpenSheet(program.title,cobraClock(program.start)+" – "+cobraClock(program.stop),"programme");
    if(!program.description.isEmpty()){TextView desc=cobraText(program.description,cobraMutedInk(),13,Gravity.LEFT);desc.setPadding(dp(8),dp(8),dp(8),dp(14));body.addView(desc);}
    cobraSheetAction(body,"▶","Watch live",false,() -> selectGuidePreview(channel));
    if(program.start>now) cobraSheetAction(body,"◷","Remind me",false,() -> {mFeatures.addReminder(sourceIdForChannel(channel),channel.id,program.title,Math.max(System.currentTimeMillis()+1000,program.start-60000));toast("Reminder set");});
    if(program.stop>now) cobraSheetAction(body,"●","Schedule recording",false,() -> {mFeatures.scheduleRecording(channel.primaryUrl,program.title,channel.headers,Math.max(System.currentTimeMillis()+1000,program.start),program.stop,sourceIdForChannel(channel),channel.id);toast("Recording scheduled");});
    if(program.stop<=now&&mArchiveChannels.contains(channel.id))cobraSheetAction(body,"↶","Play catch-up",false,() -> playCatchup(channel,program));
  }

// COBRA-REPLACE showCobraAspectPicker
  private void showCobraAspectPicker() {
    if(mPlayer==null||mCobraPlayerLocked)return;
    LinearLayout body=cobraOpenSheet("Aspect / Display","Change picture shape without restarting playback","aspect");
    for(int i=0;i<12;i++){final int mode=i;cobraSheetAction(body,mAspectMode==i?"✓":"",cobraAspectLabel(i),false,() -> {
      mAspectMode=mode;mPrefs.edit().putInt(COBRA_ASPECT_MODE,mode).apply();applyCobraAspectTransform();if(mode==11)showCobraCustomAspectEditor();});}
  }

// COBRA-REPLACE showCobraCustomAspectEditor
  private void showCobraCustomAspectEditor() {
    if(mPlayerTexture==null||mCobraPlayerLocked)return;
    LinearLayout body=cobraOpenSheet("Custom picture","Independent width and height • 100% is Best Fit","custom-aspect");
    for(String axis:new String[]{"Width","Height"}){
      String key="Width".equals(axis)?COBRA_CUSTOM_ASPECT_X:COBRA_CUSTOM_ASPECT_Y;
      TextView label=cobraText("",cobraInk(),14,Gravity.LEFT);body.addView(label);
      android.widget.SeekBar slider=new android.widget.SeekBar(this);slider.setMax(125);
      slider.setProgress(Math.round(mPrefs.getFloat(key,1f)*100)-55);
      label.setText(axis+"  "+(slider.getProgress()+55)+"%");body.addView(slider,new LinearLayout.LayoutParams(-1,dp(56)));
      slider.setOnSeekBarChangeListener(new android.widget.SeekBar.OnSeekBarChangeListener(){
        @Override public void onProgressChanged(android.widget.SeekBar bar,int progress,boolean user){if(!user)return;mAspectMode=11;mPrefs.edit().putInt(COBRA_ASPECT_MODE,11).putFloat(key,(progress+55)/100f).apply();label.setText(axis+"  "+(progress+55)+"%");applyCobraAspectTransform();}
        @Override public void onStartTrackingTouch(android.widget.SeekBar bar){}
        @Override public void onStopTrackingTouch(android.widget.SeekBar bar){}
      });
    }
    cobraSheetAction(body,"↺","Reset to Best Fit",false,() -> {mAspectMode=0;mPrefs.edit().putInt(COBRA_ASPECT_MODE,0).putFloat(COBRA_CUSTOM_ASPECT_X,1f).putFloat(COBRA_CUSTOM_ASPECT_Y,1f).apply();applyCobraAspectTransform();});
  }
