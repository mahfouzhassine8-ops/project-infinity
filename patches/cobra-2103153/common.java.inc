// @append
  /** Stable identities; adding/removing/reordering never recreates retained values. */
  private static final class CobraTileStore<T> {
    interface Factory<T> { T create(String key); }
    interface Disposer<T> { void dispose(T value); }
    final LinkedHashMap<String,T> entries = new LinkedHashMap<>();
    boolean isEmpty() { return entries.isEmpty(); }
    T get(String key) { return entries.get(key); }
    ArrayList<T> values() { return new ArrayList<>(entries.values()); }
    ArrayList<String> keys() { return new ArrayList<>(entries.keySet()); }
    T take(String key) { return entries.remove(key); }
    void reconcile(List<String> requested, Factory<T> factory, Disposer<T> disposer) {
      if (new HashSet<>(requested).size()!=requested.size()) throw new IllegalArgumentException("Duplicate tile");
      if (requested.size()>4) throw new IllegalArgumentException("Too many tiles");
      LinkedHashMap<String,T> next=new LinkedHashMap<>();
      ArrayList<T> created=new ArrayList<>();
      try {
        for(String key:requested) {
          T value=entries.get(key);
          if(value==null) { value=factory.create(key); if(value==null)throw new IllegalStateException("Missing tile");created.add(value); }
          next.put(key,value);
        }
      }catch(RuntimeException error) { for(T value:created)disposer.dispose(value);throw error; }
      ArrayList<T> removed=new ArrayList<>();
      for(Map.Entry<String,T> entry:entries.entrySet())if(!next.containsKey(entry.getKey()))removed.add(entry.getValue());
      entries.clear();entries.putAll(next);
      for(T value:removed)disposer.dispose(value);
    }
    void clear(Disposer<T> disposer) {
      ArrayList<T> previous=values();entries.clear();for(T value:previous)disposer.dispose(value);
    }
  }

  private static final class CobraLayoutMath {
    static float[] fit(int vw,int vh,float pixel,int width,int height,int mode,float customX,float customY) {
      if(vw<=0||vh<=0||width<=0||height<=0)return new float[]{1f,1f};
      float aspect=vw*(pixel>0?pixel:1f)/vh;
      if(mode==2)aspect=16f/9f;else if(mode==3)aspect=4f/3f;
      float view=(float)width/height;
      float sx=aspect<view?aspect/view:1f,sy=aspect>view?view/aspect:1f;
      if(mode==1){float z=Math.max(1f/sx,1f/sy);sx*=z;sy*=z;}
      else if(mode==4)sx*=1.10f;else if(mode==5)sx*=1.25f;else if(mode==6)sx*=1.40f;
      else if(mode==7){sx*=1.24f;sy*=.84f;}
      else if(mode>=8&&mode<=10){float z=mode==8?1.25f:mode==9?1.5f:2f;sx*=z;sy*=z;}
      else if(mode==11){sx*=Math.max(.55f,Math.min(1.8f,customX));sy*=Math.max(.55f,Math.min(1.8f,customY));}
      return new float[]{sx,sy};
    }
    static int[] tile(int index,int count,int width,int height) {
      if(count<1||count>4||index<0||index>=count)return new int[]{0,0,0,0};
      if(count==1)return new int[]{0,0,width,height};
      if(height>width) { int y=height*index/count, bottom=height*(index+1)/count;return new int[]{0,y,width,bottom-y}; }
      if(count==2) { int x=width*index/2;return new int[]{x,0,width*(index+1)/2-x,height}; }
      int col=index%2,row=index/2;
      // Three feeds use the whole lower row; four use a true 2x2 grid.
      if(count==3&&index==2)return new int[]{0,height/2,width,height-height/2};
      int x=width*col/2,y=height*row/2;
      return new int[]{x,y,width*(col+1)/2-x,height*(row+1)/2-y};
    }
  }

  private TextView cobraText(String value,int color,float size) {
    TextView view=new TextView(this);view.setText(value);view.setTextColor(color);view.setTextSize(size);
    view.setTypeface(Typeface.create("sans-serif",Typeface.NORMAL));view.setIncludeFontPadding(false);
    view.setGravity(Gravity.CENTER_VERTICAL);view.setEllipsize(android.text.TextUtils.TruncateAt.END);
    return view;
  }

  private android.graphics.drawable.Drawable cobraPressSurface(boolean dark) {
    int accent=cobraThemeColor("accent",mTheme.accent);
    android.graphics.drawable.StateListDrawable states=new android.graphics.drawable.StateListDrawable();
    states.addState(new int[]{android.R.attr.state_focused},surface(Color.argb(75,40,150,220),12,accent,2));
    states.addState(new int[]{android.R.attr.state_selected},surface(Color.argb(45,40,150,220),12,Color.TRANSPARENT,0));
    states.addState(new int[]{},surface(Color.TRANSPARENT,12,Color.TRANSPARENT,0));
    return new android.graphics.drawable.RippleDrawable(
        android.content.res.ColorStateList.valueOf(dark?0x35ffffff:0x22002244),states,
        surface(Color.WHITE,12,Color.TRANSPARENT,0));
  }

  private final class CobraIconButton extends Button {
    String glyph,caption="";
    int ink=Color.WHITE;
    final android.graphics.Paint paint=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
    CobraIconButton(String icon,String description,boolean dark) {
      super(InfinityLiveActivity.this);glyph=icon;setContentDescription(description);
      setText("");setAllCaps(false);setMinWidth(0);setMinimumWidth(0);setMinHeight(0);setMinimumHeight(0);
      setPadding(0,0,0,0);setStateListAnimator(null);setBackground(cobraPressSurface(dark));
      setFocusable(true);setFocusableInTouchMode(false);
      if(!dark)ink=cobraThemeColor("text",mTheme.text);
    }
    void icon(String value){glyph=value;invalidate();}
    void caption(String value){caption=value;invalidate();}
    @Override protected void onDraw(android.graphics.Canvas canvas) {
      super.onDraw(canvas);
      float cx=getWidth()/2f,cy=caption.isEmpty()?getHeight()/2f:getHeight()/2f-dp(7);
      int save=canvas.save();canvas.translate(cx-dp(12),cy-dp(12));canvas.scale(dp(24)/24f,dp(24)/24f);
      paint.reset();paint.setAntiAlias(true);paint.setColor(ink);paint.setStrokeWidth(1.8f);
      paint.setStyle(android.graphics.Paint.Style.STROKE);paint.setStrokeCap(android.graphics.Paint.Cap.ROUND);
      android.graphics.Path p=new android.graphics.Path();
      if("play".equals(glyph)||"next".equals(glyph)||"prev".equals(glyph)) {
        if("prev".equals(glyph)){canvas.translate(24,0);canvas.scale(-1,1);}
        paint.setStyle(android.graphics.Paint.Style.FILL);p.moveTo(7,4);p.lineTo(19,12);p.lineTo(7,20);p.close();canvas.drawPath(p,paint);
        if(!"play".equals(glyph))canvas.drawRoundRect(20,4,22,20,1,1,paint);
      } else if("pause".equals(glyph)) {
        paint.setStyle(android.graphics.Paint.Style.FILL);canvas.drawRoundRect(6,4,10,20,1,1,paint);canvas.drawRoundRect(14,4,18,20,1,1,paint);
      } else if("close".equals(glyph)) {canvas.drawLine(6,6,18,18,paint);canvas.drawLine(18,6,6,18,paint);}
      else if("back".equals(glyph)){p.moveTo(15,4);p.lineTo(7,12);p.lineTo(15,20);canvas.drawPath(p,paint);}
      else if("more".equals(glyph)){paint.setStyle(android.graphics.Paint.Style.FILL);for(int y=5;y<=19;y+=7)canvas.drawCircle(12,y,1.5f,paint);}
      else if("favorite".equals(glyph)||"favorite_on".equals(glyph)) {
        if("favorite_on".equals(glyph))paint.setStyle(android.graphics.Paint.Style.FILL);
        p.moveTo(12,21);p.cubicTo(8,17,2,13,2,8);p.cubicTo(2,2,9,1,12,7);p.cubicTo(15,1,22,2,22,8);p.cubicTo(22,13,16,17,12,21);canvas.drawPath(p,paint);
      } else if("multi".equals(glyph)){for(int x=3;x<=13;x+=10)for(int y=3;y<=13;y+=10)canvas.drawRoundRect(x,y,x+8,y+8,1.5f,1.5f,paint);}
      else if("lock".equals(glyph)||"unlock".equals(glyph)) {
        canvas.drawRoundRect(5,10,19,22,2,2,paint);canvas.drawArc(8,1,16,16,"lock".equals(glyph)?180:215,"lock".equals(glyph)?180:130,false,paint);canvas.drawLine(12,14,12,18,paint);
      } else if("aspect".equals(glyph)){canvas.drawRoundRect(2,5,22,19,2,2,paint);canvas.drawLine(7,9,4,12,paint);canvas.drawLine(4,12,7,15,paint);canvas.drawLine(17,9,20,12,paint);canvas.drawLine(20,12,17,15,paint);}
      else if("fullscreen".equals(glyph)){p.moveTo(8,3);p.lineTo(3,3);p.lineTo(3,8);p.moveTo(16,3);p.lineTo(21,3);p.lineTo(21,8);p.moveTo(3,16);p.lineTo(3,21);p.lineTo(8,21);p.moveTo(21,16);p.lineTo(21,21);p.lineTo(16,21);canvas.drawPath(p,paint);}
      else if("recent".equals(glyph)){canvas.drawCircle(12,12,9,paint);canvas.drawLine(12,6,12,12,paint);canvas.drawLine(12,12,17,15,paint);}
      else if("audio".equals(glyph)||"mute".equals(glyph)) {
        p.moveTo(3,9);p.lineTo(7,9);p.lineTo(12,4);p.lineTo(12,20);p.lineTo(7,15);p.lineTo(3,15);p.close();canvas.drawPath(p,paint);
        if("mute".equals(glyph)){canvas.drawLine(16,9,22,15,paint);canvas.drawLine(22,9,16,15,paint);}
        else {canvas.drawArc(11,6,21,18,-65,130,false,paint);canvas.drawArc(10,2,26,22,-60,120,false,paint);}
      } else if("record".equals(glyph)){canvas.drawCircle(12,12,9,paint);paint.setStyle(android.graphics.Paint.Style.FILL);canvas.drawCircle(12,12,5,paint);}
      else if("add".equals(glyph)){canvas.drawLine(4,12,20,12,paint);canvas.drawLine(12,4,12,20,paint);}
      else if("remove".equals(glyph)){canvas.drawLine(4,12,20,12,paint);}
      else if("search".equals(glyph)){canvas.drawCircle(10,10,7,paint);canvas.drawLine(15,15,22,22,paint);}
      else if("cast".equals(glyph)){p.moveTo(3,8);p.lineTo(3,4);p.lineTo(22,4);p.lineTo(22,19);p.lineTo(16,19);canvas.drawPath(p,paint);for(int r=4;r<=12;r+=4)canvas.drawArc(-r,24-r,r,24+r,-90,90,false,paint);}
      else if("cc".equals(glyph)){canvas.drawRoundRect(1,4,23,20,2,2,paint);paint.setStyle(android.graphics.Paint.Style.FILL);paint.setTypeface(Typeface.create("sans-serif",Typeface.BOLD));paint.setTextSize(10);paint.setTextAlign(android.graphics.Paint.Align.CENTER);canvas.drawText("CC",12,16,paint);}
      else if("source".equals(glyph)){canvas.drawRoundRect(3,3,21,10,2,2,paint);canvas.drawRoundRect(3,14,21,21,2,2,paint);}
      else {for(int y=5;y<=19;y+=7){canvas.drawCircle(3,y,1,paint);canvas.drawLine(8,y,22,y,paint);}}
      canvas.restoreToCount(save);
      if(!caption.isEmpty()) {
        paint.setStyle(android.graphics.Paint.Style.FILL);paint.setColor(ink);paint.setTextSize(dp(10));
        paint.setTypeface(Typeface.create("sans-serif-medium",Typeface.NORMAL));paint.setTextAlign(android.graphics.Paint.Align.CENTER);
        canvas.drawText(caption,cx,getHeight()-dp(5),paint);
      }
    }
  }

  private CobraIconButton cobraIcon(String glyph,String description,boolean dark,View.OnClickListener click) {
    CobraIconButton button=new CobraIconButton(glyph,description,dark);button.setOnClickListener(click);return button;
  }

  private LinearLayout cobraSheetRow(String icon,String label,String subtitle,boolean destructive,boolean dark,Runnable action) {
    LinearLayout row=new LinearLayout(this);row.setGravity(Gravity.CENTER_VERTICAL);
    row.setPadding(dp(10),dp(3),dp(12),dp(3));row.setBackground(cobraPressSurface(dark));
    row.setFocusable(true);row.setFocusableInTouchMode(false);row.setClickable(true);
    CobraIconButton image=new CobraIconButton(icon,label,dark);image.setEnabled(false);image.setFocusable(false);
    if(destructive)image.ink=0xffff7486;
    row.addView(image,new LinearLayout.LayoutParams(dp(42),dp(42)));
    LinearLayout copy=new LinearLayout(this);copy.setOrientation(LinearLayout.VERTICAL);
    TextView title=cobraText(label,destructive?0xffff7486:dark?Color.WHITE:cobraThemeColor("text",mTheme.text),15);
    title.setMaxLines(1);copy.addView(title,new LinearLayout.LayoutParams(-1,dp(24)));
    if(subtitle!=null&&!subtitle.isEmpty()) {TextView sub=cobraText(subtitle,dark?0xffaebdcc:cobraThemeColor("muted",mTheme.muted),11);sub.setMaxLines(2);copy.addView(sub,new LinearLayout.LayoutParams(-1,-2));}
    LinearLayout.LayoutParams cp=new LinearLayout.LayoutParams(0,-2,1);cp.leftMargin=dp(10);row.addView(copy,cp);
    row.setContentDescription(label+(subtitle==null?"":", "+subtitle));
    row.setOnClickListener(v->{closeCobraActionSheet();action.run();});
    row.setMinimumHeight(dp(subtitle==null||subtitle.isEmpty()?52:64));return row;
  }

  private LinearLayout cobraOpenSheet(String title,String detail,String kind) {
    closeCobraActionSheet();
    FrameLayout parent=mMultiOverlay!=null?mMultiOverlay:mPlayerOverlay!=null?mPlayerOverlay:(FrameLayout)getWindow().getDecorView();
    boolean dark=mPlayerOverlay!=null||mMultiOverlay!=null||!"light".equals(cobraEffectiveAppearanceMode());
    mCobraSheetPreviousFocus=getCurrentFocus();mCobraSheetKind=kind;
    FrameLayout scrim=new FrameLayout(this);mCobraActionSheet=scrim;scrim.setTag("cobra_themed_sheet");
    scrim.setBackgroundColor(0x55000000);scrim.setClickable(true);scrim.setOnClickListener(v->closeCobraActionSheet());
    LinearLayout panel=new LinearLayout(this);panel.setOrientation(LinearLayout.VERTICAL);panel.setClickable(true);
    panel.setPadding(dp(12),dp(8),dp(12),dp(12));
    panel.setBackground(surface(dark?0xf5141c27:cobraThemeColor("panel",mTheme.panel),22,
        dark?0xff334457:cobraThemeColor("line",mTheme.line),1));panel.setElevation(dp(14));
    LinearLayout header=new LinearLayout(this);header.setGravity(Gravity.CENTER_VERTICAL);
    LinearLayout copy=new LinearLayout(this);copy.setOrientation(LinearLayout.VERTICAL);copy.setPadding(dp(12),dp(4),0,dp(4));
    TextView heading=cobraText(title,dark?Color.WHITE:cobraThemeColor("text",mTheme.text),18);heading.setTypeface(Typeface.create("sans-serif-medium",Typeface.NORMAL));heading.setMaxLines(2);
    copy.addView(heading,new LinearLayout.LayoutParams(-1,-2));
    if(detail!=null&&!detail.isEmpty()){TextView sub=cobraText(detail,dark?0xff9fb2c6:cobraThemeColor("muted",mTheme.muted),12);sub.setMaxLines(3);copy.addView(sub,new LinearLayout.LayoutParams(-1,-2));}
    header.addView(copy,new LinearLayout.LayoutParams(0,-2,1));
    CobraIconButton close=cobraIcon("close","Close menu",dark,v->closeCobraActionSheet());header.addView(close,new LinearLayout.LayoutParams(dp(48),dp(48)));
    panel.addView(header,new LinearLayout.LayoutParams(-1,-2));
    int available=parent.getHeight()>0?parent.getHeight():getResources().getDisplayMetrics().heightPixels;
    final int limit=Math.min(dp(480),Math.round(available*.67f));
    ScrollView scroll=new ScrollView(this) {
      @Override protected void onMeasure(int w,int h) { super.onMeasure(w,View.MeasureSpec.makeMeasureSpec(limit,View.MeasureSpec.AT_MOST)); }
    };
    scroll.setFillViewport(false);scroll.setOverScrollMode(View.OVER_SCROLL_IF_CONTENT_SCROLLS);
    LinearLayout items=new LinearLayout(this);items.setOrientation(LinearLayout.VERTICAL);scroll.addView(items,new ScrollView.LayoutParams(-1,-2));
    // Bounded scrolling, including a narrow cover display; the panel never fills the whole screen unnecessarily.
    panel.addView(scroll,new LinearLayout.LayoutParams(-1,-2));
    int width=parent.getWidth()>0?parent.getWidth():getResources().getDisplayMetrics().widthPixels;
    FrameLayout.LayoutParams pos=new FrameLayout.LayoutParams(Math.min(width-dp(24),dp(440)),-2,
        isPortrait()?Gravity.BOTTOM|Gravity.CENTER_HORIZONTAL:Gravity.RIGHT|Gravity.CENTER_VERTICAL);
    pos.setMargins(dp(12),dp(12),dp(12),dp(22));scrim.addView(panel,pos);parent.addView(scrim,new FrameLayout.LayoutParams(-1,-1));
    panel.setAlpha(0f);panel.setTranslationY(dp(10));panel.animate().alpha(1f).translationY(0f).setDuration(160).start();
    close.requestFocus();return items;
  }

  private boolean closeCobraActionSheet() {
    if(mCobraActionSheet==null)return false;
    android.view.ViewParent parent=mCobraActionSheet.getParent();
    if(parent instanceof android.view.ViewGroup)((android.view.ViewGroup)parent).removeView(mCobraActionSheet);
    mCobraActionSheet=null;mCobraSheetKind="";
    if(mCobraSheetPreviousFocus!=null&&mCobraSheetPreviousFocus.isAttachedToWindow())mCobraSheetPreviousFocus.requestFocus();
    mCobraSheetPreviousFocus=null;if(mPlayerOverlay!=null&&!mCobraPlayerLocked)scheduleChromeHide();return true;
  }

  private boolean cobraSheetIsDark() { return mPlayerOverlay!=null||mMultiOverlay!=null||!"light".equals(cobraEffectiveAppearanceMode()); }
