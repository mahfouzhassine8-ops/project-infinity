// STATE
  private FrameLayout mRefSheet;
  private LinearLayout mRefSheetPanel;
  private boolean mRefSheetDark;

// METHODS
  private TextView cobraRefinedText(String value, int size, boolean bold) {
    TextView text = new TextView(this); text.setText(value); text.setTextSize(size);
    text.setTypeface(Typeface.SANS_SERIF, bold ? Typeface.BOLD : Typeface.NORMAL);
    text.setTextColor(cobraThemeColor("text", mTheme.text)); text.setGravity(Gravity.CENTER_VERTICAL);
    text.setPadding(dp(8), 0, dp(8), 0); return text;
  }

  private Button cobraRefinedButton(String value) {
    Button button = new Button(this); button.setText(value); button.setAllCaps(false);
    button.setTypeface(Typeface.SANS_SERIF); button.setTextSize(13);
    button.setTextColor(cobraThemeColor("text", mTheme.text));
    button.setMinWidth(0); button.setMinimumWidth(0); button.setMinHeight(dp(48)); button.setMinimumHeight(dp(48));
    button.setPadding(dp(8), dp(4), dp(8), dp(4));
    button.setBackground(new android.graphics.drawable.RippleDrawable(
        android.content.res.ColorStateList.valueOf(Color.argb(60, 120, 175, 235)),
        focusSurface(cobraThemeColor("panel", mTheme.panel), cobraThemeColor("focus", mTheme.focus), 12), null));
    return button;
  }

  private boolean closeCobraRefinedSheet() {
    if (mRefSheet == null) return false;
    android.view.ViewParent parent = mRefSheet.getParent();
    if (parent instanceof android.view.ViewGroup) ((android.view.ViewGroup) parent).removeView(mRefSheet);
    mRefSheet = null; mRefSheetPanel = null;
    return true;
  }

  private LinearLayout cobraOpenRefinedSheet(String title, boolean dark) {
    if (mCobraPlayerLocked) { showCobraPlayerUnlockAffordance(); return null; }
    closeCobraRefinedSheet(); mRefSheetDark = dark;
    FrameLayout decor = (FrameLayout) getWindow().getDecorView();
    mRefSheet = new FrameLayout(this); mRefSheet.setTag("cobra_refined_sheet");
    mRefSheet.setBackgroundColor(Color.argb(96, 0, 0, 0)); mRefSheet.setClickable(true);
    mRefSheet.setOnClickListener(v -> closeCobraRefinedSheet());
    mRefSheetPanel = new LinearLayout(this); mRefSheetPanel.setOrientation(LinearLayout.VERTICAL);
    mRefSheetPanel.setClickable(true); mRefSheetPanel.setPadding(dp(12), dp(10), dp(12), dp(20));
    int panel = dark ? Color.rgb(12, 19, 28) : cobraThemeColor("panel", mTheme.panel);
    int line = dark ? Color.rgb(40, 55, 70) : cobraThemeColor("line", mTheme.line);
    mRefSheetPanel.setBackground(surface(panel, 24, line, 1));
    LinearLayout header = new LinearLayout(this); header.setGravity(Gravity.CENTER_VERTICAL);
    TextView heading = cobraRefinedText(title, 17, true); heading.setMaxLines(2);
    if (dark) heading.setTextColor(Color.WHITE);
    Button close = cobraRefinedButton("×"); close.setContentDescription("Close panel");
    if (dark) { close.setTextColor(Color.WHITE); close.setBackgroundColor(Color.TRANSPARENT); }
    close.setOnClickListener(v -> closeCobraRefinedSheet());
    header.addView(heading, new LinearLayout.LayoutParams(0, dp(52), 1));
    header.addView(close, new LinearLayout.LayoutParams(dp(48), dp(48)));
    mRefSheetPanel.addView(header, new LinearLayout.LayoutParams(-1, dp(56)));
    LinearLayout content = new LinearLayout(this); content.setOrientation(LinearLayout.VERTICAL);
    mRefSheetPanel.addView(content, new LinearLayout.LayoutParams(-1, 0, 1));
    int sw = getResources().getDisplayMetrics().widthPixels, sh = getResources().getDisplayMetrics().heightPixels;
    FrameLayout.LayoutParams p = new FrameLayout.LayoutParams(isPortrait() ? -1 : Math.min(dp(400), sw * 46 / 100),
        isPortrait() ? Math.min(dp(520), sh * 72 / 100) : -1, isPortrait() ? Gravity.BOTTOM : Gravity.RIGHT);
    p.setMargins(dp(10), dp(10), dp(10), dp(20)); mRefSheet.addView(mRefSheetPanel, p);
    decor.addView(mRefSheet, new FrameLayout.LayoutParams(-1, -1));
    mRefSheetPanel.setAlpha(0f); mRefSheetPanel.setTranslationY(isPortrait() ? dp(12) : 0);
    mRefSheetPanel.animate().alpha(1f).translationY(0f).setDuration(170L).start();
    return content;
  }

  private void cobraFitActionSheet(int rows) {
    if (mRefSheetPanel == null || !isPortrait()) return;
    android.view.ViewGroup.LayoutParams p = mRefSheetPanel.getLayoutParams();
    p.height = Math.min(getResources().getDisplayMetrics().heightPixels * 78 / 100, dp(86 + rows * 52));
    mRefSheetPanel.setLayoutParams(p);
  }

  private void cobraSheetNote(LinearLayout sheet, String value) {
    TextView note = cobraRefinedText(value, 13, false); note.setPadding(dp(12), dp(12), dp(12), dp(12)); note.setMaxLines(6);
    if (mRefSheet != null && mRefSheetDark) note.setTextColor(Color.rgb(190, 203, 217));
    sheet.addView(note, new LinearLayout.LayoutParams(-1, -2));
  }

  private void cobraSheetAction(LinearLayout body, String label, boolean destructive, Runnable action) {
    Button row = cobraRefinedButton(label); row.setGravity(Gravity.CENTER_VERTICAL | Gravity.LEFT);
    row.setPadding(dp(16), dp(6), dp(16), dp(6));
    if (mRefSheetDark) { row.setTextColor(Color.WHITE); row.setBackground(focusSurface(Color.TRANSPARENT, Color.rgb(37, 61, 84), 10)); }
    if (destructive) row.setTextColor(mRefSheetDark || !"light".equals(cobraEffectiveAppearanceMode()) ? Color.rgb(255, 138, 149) : Color.rgb(166, 26, 47));
    row.setOnClickListener(v -> { closeCobraRefinedSheet(); action.run(); });
    body.addView(row, new LinearLayout.LayoutParams(-1, dp(52)));
  }

  private Button cobraVideoButton(String label, String description) {
    Button button = new Button(this) {
      private final android.graphics.Paint paint = new android.graphics.Paint(3);
      @Override protected void onDraw(android.graphics.Canvas canvas) {
        canvas.save(); canvas.translate(getWidth()/2f, getHeight()/2f);
        float s = dp(22)/24f; canvas.scale(s, s); canvas.translate(-12, -12);
        paint.setColor(Color.WHITE); paint.setStyle(android.graphics.Paint.Style.STROKE); paint.setStrokeWidth(1.8f);
        paint.setStrokeCap(android.graphics.Paint.Cap.ROUND); paint.setStrokeJoin(android.graphics.Paint.Join.ROUND);
        String value = getText().toString();
        if (description.contains("Play") || description.equals("Pause")) {
          paint.setStyle(android.graphics.Paint.Style.FILL);
          if (value.contains("❚")) { canvas.drawRoundRect(6,4,10,20,1,1,paint); canvas.drawRoundRect(14,4,18,20,1,1,paint); }
          else { android.graphics.Path p = new android.graphics.Path(); p.moveTo(7,3); p.lineTo(21,12); p.lineTo(7,21); p.close(); canvas.drawPath(p,paint); }
        } else if (description.contains("Previous") || description.contains("Next") || description.equals("Back")) {
          boolean next = description.contains("Next");
          canvas.drawLine(next?8:16,5,next?16:8,12,paint); canvas.drawLine(next?16:8,12,next?8:16,19,paint);
        } else if (description.contains("Favorite")) {
          android.graphics.Path p = new android.graphics.Path(); p.moveTo(12,21); p.cubicTo(-4,10,3,-2,12,6); p.cubicTo(21,-2,28,10,12,21);
          if (value.contains("♥")) paint.setStyle(android.graphics.Paint.Style.FILL); canvas.drawPath(p,paint);
        } else if (description.contains("Lock")) {
          canvas.drawRoundRect(5,10,19,22,2,2,paint); canvas.drawArc(8,1,16,15,180,180,false,paint); canvas.drawLine(12,14,12,17,paint);
        } else if (description.contains("Multi")) {
          canvas.drawRoundRect(2,3,10,10,1,1,paint); canvas.drawRoundRect(14,3,22,10,1,1,paint);
          canvas.drawRoundRect(2,14,10,21,1,1,paint); canvas.drawRoundRect(14,14,22,21,1,1,paint);
        } else if (description.contains("Aspect") || description.contains("Fullscreen")) {
          canvas.drawLine(3,9,3,3,paint); canvas.drawLine(3,3,9,3,paint); canvas.drawLine(15,3,21,3,paint); canvas.drawLine(21,3,21,9,paint);
          canvas.drawLine(3,15,3,21,paint); canvas.drawLine(3,21,9,21,paint); canvas.drawLine(15,21,21,21,paint); canvas.drawLine(21,21,21,15,paint);
        } else if (description.contains("caption") || description.contains("Audio")) {
          canvas.drawRoundRect(2,4,22,20,3,3,paint); paint.setStyle(android.graphics.Paint.Style.FILL); paint.setTextSize(10); paint.setTypeface(Typeface.DEFAULT_BOLD); canvas.drawText("CC",5,16,paint);
        } else if (description.contains("Channel") || description.contains("channel") && !description.contains("More")) {
          for (int y=5;y<=19;y+=7) { canvas.drawCircle(3,y,1,paint); canvas.drawLine(8,y,22,y,paint); }
        } else if (description.contains("Volume")) {
          android.graphics.Path p = new android.graphics.Path(); p.moveTo(3,9); p.lineTo(7,9); p.lineTo(12,4); p.lineTo(12,20); p.lineTo(7,15); p.lineTo(3,15); p.close(); canvas.drawPath(p,paint);
          if (value.contains("MUTE")) { canvas.drawLine(16,9,22,15,paint); canvas.drawLine(22,9,16,15,paint); }
          else canvas.drawArc(11,5,23,19,-65,130,false,paint);
        } else { paint.setStyle(android.graphics.Paint.Style.FILL); for(int y=4;y<=20;y+=8) canvas.drawCircle(12,y,1.7f,paint); }
        canvas.restore();
      }
    };
    button.setText(label); button.setContentDescription(description); button.setTextColor(Color.WHITE);
    button.setMinWidth(0); button.setMinimumWidth(0); button.setMinHeight(0); button.setMinimumHeight(0); button.setPadding(0,0,0,0);
    button.setBackground(new android.graphics.drawable.RippleDrawable(android.content.res.ColorStateList.valueOf(Color.argb(80,255,255,255)),
        focusSurface(Color.TRANSPARENT, Color.argb(110,60,115,165), 24), null));
    return button;
  }

  private void openPlayerOverlay(Channel channel) {
    clearCobraPlayerLockState(false);
    FrameLayout decor = (FrameLayout) getWindow().getDecorView();
    mPlayerOverlay = new FrameLayout(this); mPlayerOverlay.setBackgroundColor(Color.BLACK); mPlayerOverlay.setFocusable(true);
    mPlayerTexture = new TextureView(this); mAspectMode = mPrefs.getInt(COBRA_ASPECT_MODE,0);
    mPlayerOverlay.addView(mPlayerTexture, new FrameLayout.LayoutParams(-1,-1));
    mPlayerChrome = new LinearLayout(this); mPlayerChrome.setTag("cobra_player_reboot_chrome"); mPlayerChrome.setOrientation(LinearLayout.VERTICAL);
    mPlayerChrome.setPadding(dp(14),dp(18),dp(14),dp(24));
    mPlayerChrome.setBackground(new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,
        new int[]{Color.argb(150,0,0,0),Color.TRANSPARENT,Color.argb(220,0,0,0)}));
    LinearLayout top = new LinearLayout(this); top.setGravity(Gravity.CENTER_VERTICAL);
    Button back = cobraVideoButton("‹","Back"); back.setOnClickListener(v -> closeFullscreenToCobraView());
    TextView title = cobraRefinedText(channel.name,16,true); title.setTextColor(Color.WHITE); title.setMaxLines(1); title.setEllipsize(android.text.TextUtils.TruncateAt.END);
    TextView state = cobraRefinedText("CONNECTING",10,false); state.setTextColor(Color.WHITE); state.setTag("player_state");
    Button lock = cobraVideoButton("lock","Lock player controls"); lock.setOnClickListener(v -> lockCobraPlayer());
    top.addView(back,new LinearLayout.LayoutParams(dp(48),dp(48))); top.addView(title,new LinearLayout.LayoutParams(0,dp(48),1));
    top.addView(state,new LinearLayout.LayoutParams(dp(80),dp(48))); top.addView(lock,new LinearLayout.LayoutParams(dp(48),dp(48)));
    mPlayerChrome.addView(top,new LinearLayout.LayoutParams(-1,dp(52)));
    mPlayerChrome.addView(new View(this),new LinearLayout.LayoutParams(1,0,1));
    LinearLayout transport = new LinearLayout(this); transport.setGravity(Gravity.CENTER);
    Button prev = cobraVideoButton("‹","Previous channel"), play = cobraVideoButton("▶","Play or pause"), next = cobraVideoButton("›","Next channel");
    play.setTag("cobra_player_play_pause"); prev.setOnClickListener(v -> stepChannel(-1)); next.setOnClickListener(v -> stepChannel(1)); play.setOnClickListener(v -> toggleCobraPlayerPlayPause());
    transport.addView(prev,new LinearLayout.LayoutParams(dp(64),dp(64))); transport.addView(play,new LinearLayout.LayoutParams(dp(80),dp(72))); transport.addView(next,new LinearLayout.LayoutParams(dp(64),dp(64)));
    mPlayerChrome.addView(transport,new LinearLayout.LayoutParams(-1,dp(76)));
    mPlayerChrome.addView(new View(this),new LinearLayout.LayoutParams(1,0,1));
    TextView now = cobraRefinedText(cobraPlayerNow(channel),15,true), later = cobraRefinedText(cobraPlayerNext(channel),12,false);
    now.setTag("ref_player_now"); later.setTag("ref_player_next"); now.setTextColor(Color.WHITE); later.setTextColor(Color.rgb(201,213,228));
    now.setMaxLines(1); later.setMaxLines(1); now.setEllipsize(android.text.TextUtils.TruncateAt.END); later.setEllipsize(android.text.TextUtils.TruncateAt.END);
    now.setOnClickListener(v -> showProgramGuide(channel)); later.setOnClickListener(v -> showProgramGuide(channel));
    mPlayerChrome.addView(now,new LinearLayout.LayoutParams(-1,dp(28))); mPlayerChrome.addView(later,new LinearLayout.LayoutParams(-1,dp(26)));
    LinearLayout actions = new LinearLayout(this); actions.setGravity(Gravity.CENTER);
    Button channels = cobraVideoButton("list","Channels"), favorite = cobraVideoButton(mFavorites.contains(channel.id)?"♥":"♡","Favorite"),
        aspect = cobraVideoButton("aspect","Aspect / Display"), captions = cobraVideoButton("CC","Audio / Subtitles"),
        multi = cobraVideoButton("multi","Multi-View"), more = cobraVideoButton("more","More player controls");
    channels.setOnClickListener(v -> showCobraPlayerChannels("RECENT"));
    favorite.setOnClickListener(v -> { toggleFavorite(channel); favorite.setText(mFavorites.contains(channel.id)?"♥":"♡"); });
    aspect.setOnClickListener(v -> showCobraAspectPicker()); captions.setOnClickListener(v -> showTrackChooser());
    multi.setOnClickListener(v -> beginMultiView()); more.setOnClickListener(v -> showPlayerSettingsDrawer());
    for(Button b : new Button[]{channels,favorite,aspect,captions,multi,more}) actions.addView(b,new LinearLayout.LayoutParams(0,dp(48),1));
    mPlayerChrome.addView(actions,new LinearLayout.LayoutParams(-1,dp(52)));
    mPlayerOverlay.addView(mPlayerChrome,new FrameLayout.LayoutParams(-1,-1));
    mPlayerOverlay.setOnClickListener(v -> { if(mCobraPlayerLocked) showCobraPlayerUnlockAffordance(); else if(!closeCobraRefinedSheet()) togglePlayerChrome(); });
    mPlayerOverlay.setOnKeyListener((v,key,event) -> {
      if(event.getAction()!=KeyEvent.ACTION_DOWN) return false;
      if(mCobraPlayerLocked) { showCobraPlayerUnlockAffordance(); return true; }
      if(key==KeyEvent.KEYCODE_DPAD_UP || key==KeyEvent.KEYCODE_DPAD_DOWN || key==KeyEvent.KEYCODE_DPAD_CENTER) showPlayerChromeTemporarily();
      return false;
    });
    decor.addView(mPlayerOverlay,new FrameLayout.LayoutParams(-1,-1));
    if (!cobraTouchFirstDevice()) play.requestFocus();
    mPlayerTexture.addOnLayoutChangeListener((v,l,t,r,b,ol,ot,or,ob) -> applyCobraAspectTransform());
    updateCobraPlayerPlayPause(); scheduleChromeHide(); requestCobraShortGuide(channel);
  }

  private boolean closePlayerSettingsDrawer() { return closeCobraRefinedSheet(); }

  private void showPlayerSettingsDrawer() {
    if (mPlayerOverlay == null) return;
    LinearLayout body = cobraOpenRefinedSheet("Player settings", true); if(body==null) return;
    cobraSheetAction(body, "Record / Stop recording", false, () -> { if(mPlaying!=null) toggleRecording(mPlaying); });
    cobraSheetAction(body, "Audio & subtitles", false, () -> showTrackChooser());
    cobraSheetAction(body, "Aspect & display", false, () -> showCobraAspectPicker());
    cobraSheetAction(body, "Cast / route", false, () -> openCastSettings());
    cobraSheetAction(body, "Source", false, () -> { closePlayer(); showSources(); });
    cobraSheetAction(body, "Return to browsing", false, () -> closeFullscreenToCobraView());
    cobraFitActionSheet(6);
  }

  private void showCobraPlayerChannels(String filter) {
    if (mPlayer == null || mPlaying == null) return;
    LinearLayout body = cobraOpenRefinedSheet("Live TV · Channels", true); if(body==null) return;
    LinearLayout tabs = new LinearLayout(this);
    String[] labels = {"Favorites","Recent","All","Categories"}, keys = {"FAVORITES","RECENT","ALL","CATEGORIES"};
    for(int i=0;i<labels.length;i++) {
      String key=keys[i]; Button b=cobraRefinedButton(labels[i]); b.setTextSize(11); b.setTextColor(Color.WHITE); b.setBackgroundColor(Color.TRANSPARENT);
      b.setOnClickListener(v -> showCobraPlayerChannels(key)); tabs.addView(b,new LinearLayout.LayoutParams(0,dp(48),1));
    }
    body.addView(tabs,new LinearLayout.LayoutParams(-1,dp(48)));
    ArrayList<String> groups = new ArrayList<>(); ArrayList<Channel> channels = new ArrayList<>();
    if("CATEGORIES".equals(filter)) groups.addAll(categoriesForCurrentChannels());
    else {
      List<Channel> candidates = "RECENT".equals(filter) ? filteredChannels(false,true) : mChannels;
      for(Channel c:candidates) {
        if(isCobraHidden(c) || mFeatures.looksAdult(c.group) || mFeatures.looksAdult(c.name) || !mFeatures.sourceEnabled(sourceIdForChannel(c))) continue;
        if("FAVORITES".equals(filter) && !mFavorites.contains(c.id)) continue;
        if(filter.startsWith("GROUP:") && !filter.substring(6).equals(c.group)) continue;
        channels.add(c);
      }
    }
    android.widget.ListView list=new android.widget.ListView(this); list.setDivider(null); list.setFastScrollEnabled(channels.size()>100);
    list.setAdapter(new android.widget.BaseAdapter(){
      public int getCount(){return "CATEGORIES".equals(filter)?groups.size():channels.size();}
      public Object getItem(int i){return i;}
      public long getItemId(int i){return i;}
      public View getView(int i,View old,android.view.ViewGroup parent){
        TextView row=old instanceof TextView?(TextView)old:cobraRefinedText("",14,false);
        row.setTextColor(Color.WHITE); row.setPadding(dp(12),dp(6),dp(12),dp(6)); row.setMaxLines(3);
        row.setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,dp(76)));
        if("CATEGORIES".equals(filter)) {
          String group=groups.get(i); row.setText(group+"  ›"); row.setOnClickListener(v -> showCobraPlayerChannels("ALL".equals(group)?"ALL":"GROUP:"+group));
        } else {
          Channel c=channels.get(i); ProgramPair pair=programFor(c); boolean active=mPlaying!=null&&c.id.equals(mPlaying.id);
          row.setText((active?"▶  ":"")+c.name+"\n"+(pair==null?cobraGuideStatus(c):pair.now));
          row.setBackground(focusSurface(active?Color.rgb(30,56,80):Color.TRANSPARENT,Color.rgb(37,61,84),10));
          row.setOnClickListener(v -> { if(mPlaying!=null&&c.id.equals(mPlaying.id)) closeCobraRefinedSheet(); else { playChannel(c); if(mRefSheet!=null)mRefSheet.bringToFront(); notifyDataSetChanged(); } });
          row.setOnLongClickListener(v -> { closeCobraRefinedSheet(); showProgramGuide(c); return true; });
        } return row;
      }
    });
    body.addView(list,new LinearLayout.LayoutParams(-1,0,1));
    if(channels.isEmpty()&&groups.isEmpty()) cobraSheetNote(body,"No channels in this filter. Choose All or Categories.");
  }

  private void showProgramActions(Channel channel, GuideProgram program) {
    LinearLayout sheet=cobraOpenRefinedSheet(program.title,false); if(sheet==null)return;
    cobraSheetNote(sheet,formatTime(program.start)+"\n"+program.description);
    long now=System.currentTimeMillis(); int count=2;
    cobraSheetAction(sheet,"Play live in preview",false,() -> { if(mPlayerOverlay!=null) closeFullscreenToCobraView(); selectGuidePreview(channel); });
    if(program.start>now){
      cobraSheetAction(sheet,"Remind me",false,() -> {mFeatures.addReminder(sourceIdForChannel(channel),channel.id,program.title,Math.max(System.currentTimeMillis()+1000,program.start-60000));toast("Reminder set");});
      cobraSheetAction(sheet,"Schedule recording",false,() -> {mFeatures.scheduleRecording(channel.primaryUrl,program.title,channel.headers,Math.max(System.currentTimeMillis()+1000,program.start),program.stop,sourceIdForChannel(channel),channel.id);toast("Recording scheduled");}); count+=2;
    }
    if(program.stop<now&&mArchiveChannels.contains(channel.id)){cobraSheetAction(sheet,"Play catch-up",false,() -> playCatchup(channel,program));count++;}
    cobraFitActionSheet(count);
  }
