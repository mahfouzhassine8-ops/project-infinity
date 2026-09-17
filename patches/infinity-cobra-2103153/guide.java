// COBRA-APPEND
  private FrameLayout mCobraBrowseRoot;
  private LinearLayout mCobraBrowseContent;
  private TextView mCobraBrowseSummary;
  private android.widget.AbsListView mCobraGuideList;
  private android.widget.BaseAdapter mCobraGuideAdapter;
  private String mCobraBrowseMode="mobile",mCobraGuideSource="";
  private boolean mCobraBrowseGroups=false,mCobraRefreshQueued=false,mCobraLastWide=false;
  private long mCobraGuideAnchor;
  private View mCobraTimelineHeader;
  private final Runnable mCobraUiTick=new Runnable(){@Override public void run(){
    if(!isCobraAsyncAlive())return;
    refreshCobraGuideViews();mMain.postDelayed(this,10000L);
  }};
  private long cobraGuideWindowStart(){long now=System.currentTimeMillis();return mCobraGuideAnchor==0?now-now%1800000L:mCobraGuideAnchor;}
  private void moveCobraGuideTime(int hours){
    long now=System.currentTimeMillis();
    mCobraGuideAnchor=hours==0?0:Math.max(now-86400000L,Math.min(now+7L*86400000L,cobraGuideWindowStart()+hours*3600000L));
    refreshCobraGuideViews();
  }
  private ArrayList<Channel> cobraVisibleGuideChannels(String filter,String source){
    ArrayList<Channel> out=new ArrayList<>();String search=CobraCore.alias(mSearch);
    for(Channel channel:mChannels){
      if(channel==null||isCobraHidden(channel))continue;
      if(mFeatures.looksAdult(channel.group)||mFeatures.looksAdult(channel.name))continue;
      String owner=sourceIdForChannel(channel);
      if(!mFeatures.sourceEnabled(owner)||(!source.isEmpty()&&!source.equals(owner)))continue;
      if(!search.isEmpty()&&!CobraCore.alias(channel.name+" "+channel.group).contains(search))continue;
      if("FAVORITES".equals(filter)&&!mFavorites.contains(channel.id))continue;
      if("RECENT".equals(filter)&&!mRecents.contains(channel.id))continue;
      if(filter.startsWith("MY:")&&!filter.substring(3).equals(cobraCustomGroup(channel)))continue;
      if(!filter.startsWith("MY:")&&!"ALL".equals(filter)&&!"FAVORITES".equals(filter)&&!"RECENT".equals(filter)&&!filter.equals(channel.group))continue;
      out.add(channel);
    }
    if("RECENT".equals(filter))Collections.sort(out,Comparator.comparingInt(c -> mRecents.indexOf(c.id)));
    return out;
  }
  private ArrayList<String> cobraGuideGroups(){
    Set<String> seen=new java.util.TreeSet<>(String.CASE_INSENSITIVE_ORDER);
    for(Channel c:cobraVisibleGuideChannels("ALL",mCobraGuideSource))if(c.group!=null&&!c.group.isEmpty())seen.add(c.group);
    ArrayList<String> result=new ArrayList<>(seen);
    for(String group:cobraCustomGroups())result.add("MY:"+group);
    return result;
  }
  private void chooseCobraGuideSource(){
    LinearLayout body=cobraOpenSheet("Live TV sources","Choose a provider, then a category","guide-source");
    cobraSheetAction(body,"◈","All sources",false,() -> {mCobraGuideSource="";mCategory="ALL";mCobraBrowseGroups=true;renderCobraGuideBody();});
    for(LiveSource source:mSources)if(mFeatures.sourceEnabled(source.id))
      cobraSheetAction(body,"◈",source.name,false,() -> {mCobraGuideSource=source.id;mCategory="ALL";mCobraBrowseGroups=true;renderCobraGuideBody();});
  }
  private void showCobraGuideExperience(String mode,boolean groups){
    mCobraBrowseMode=mode;mCobraBrowseGroups=groups;mCobraInternalScreen="root";
    mPrefs.edit().putString(COBRA_PRIMARY_VIEW,"mobile".equals(mode)?"mobile":"guide").apply();
    if(mCobraBrowseRoot==null||mCobraBrowseRoot.getParent()!=mStage){
      clearStage("COBRA • LIVE TV");
      mCobraBrowseRoot=new FrameLayout(this);mCobraBrowseRoot.setTag("cobra_persistent_live_shell");
      mCobraBrowseContent=new LinearLayout(this);mCobraBrowseContent.setOrientation(LinearLayout.VERTICAL);
      mCobraBrowseSummary=cobraText("",cobraInk(),14,Gravity.LEFT|Gravity.CENTER_VERTICAL);
      mCobraBrowseSummary.setPadding(dp(16),dp(8),dp(12),dp(8));
      if(mCobraPreviewHost==null)cobraPreviewPanel(mGuidePreviewChannel,true);
      android.view.ViewParent parent=mCobraPreviewHost.getParent();
      if(parent instanceof android.view.ViewGroup)((android.view.ViewGroup)parent).removeView(mCobraPreviewHost);
      mCobraBrowseRoot.addView(mCobraPreviewHost,new FrameLayout.LayoutParams(-1,dp(180)));
      mCobraBrowseRoot.addView(mCobraBrowseSummary,new FrameLayout.LayoutParams(1,1));
      mCobraBrowseRoot.addView(mCobraBrowseContent,new FrameLayout.LayoutParams(-1,-1));
      mCobraBrowseRoot.addOnLayoutChangeListener((v,l,t,r,b,ol,ot,or,ob)->{
        if(r-l==or-ol&&b-t==ob-ot)return;
        boolean wide=r-l>=dp(600)&&r-l>b-t;
        layoutCobraGuideShell();if(wide!=mCobraLastWide){mCobraLastWide=wide;renderCobraGuideBody();}
      });
      mStage.addView(mCobraBrowseRoot,new LinearLayout.LayoutParams(-1,0,1));
    }
    ArrayList<Channel> all=cobraVisibleGuideChannels("ALL","");
    ensureCobraPreviewSelection(all);
    if(mCobraPreviewPlayer==null&&mPlayer==null&&mMultiOverlay==null&&mGuidePreviewChannel!=null)startCobraPreview(mGuidePreviewChannel);
    if(mGuidePreviewChannel!=null)requestCobraGuideWindow(mGuidePreviewChannel,true);
    renderCobraGuideBody();layoutCobraGuideShell();refreshCobraGuideViews();
    mMain.removeCallbacks(mCobraUiTick);mMain.postDelayed(mCobraUiTick,10000L);
  }
  private void layoutCobraGuideShell(){
    if(mCobraBrowseRoot==null||mCobraPreviewHost==null||mCobraPreviewHost.getParent()!=mCobraBrowseRoot)return;
    int width=mCobraBrowseRoot.getWidth(),height=mCobraBrowseRoot.getHeight();if(width<=0||height<=0)return;
    boolean wide=width>=dp(600)&&width>height;
    FrameLayout.LayoutParams video,content,summary;
    if(wide&&!"grid".equals(mCobraBrowseMode)){
      int vw=Math.round(width*("focus".equals(mCobraBrowseMode)?.58f:"compact".equals(mCobraBrowseMode)?.30f:.40f));
      video=new FrameLayout.LayoutParams(vw,height);content=new FrameLayout.LayoutParams(width-vw-dp(12),height);content.leftMargin=vw+dp(12);
      summary=new FrameLayout.LayoutParams(0,0);
    }else{
      int vh=Math.min(Math.round(height*("compact".equals(mCobraBrowseMode)?.23f:"focus".equals(mCobraBrowseMode)?.40f:.33f)),Math.round(width*9f/16)+dp(48));
      vh=Math.max(Math.min(dp(126),height/3),vh);
      if(wide)vh=Math.min(vh,dp(174));
      int vw=wide?Math.min(dp(310),Math.round(width*.37f)):width;
      video=new FrameLayout.LayoutParams(vw,vh);
      summary=new FrameLayout.LayoutParams(wide?width-vw:0,wide?vh:0);summary.leftMargin=vw;
      content=new FrameLayout.LayoutParams(width,Math.max(1,height-vh-dp(8)));content.topMargin=vh+dp(8);
    }
    mCobraPreviewHost.setLayoutParams(video);mCobraBrowseContent.setLayoutParams(content);mCobraBrowseSummary.setLayoutParams(summary);
    applyCobraVideoFit(mCobraPreviewTexture,mCobraPreviewPlayer,0);
  }
  private void renderCobraGuideBody(){
    if(mCobraBrowseContent==null)return;
    mCobraBrowseContent.removeAllViews();mCobraGuideAdapter=null;mCobraGuideList=null;
    LinearLayout crumb=new LinearLayout(this);crumb.setGravity(Gravity.CENTER_VERTICAL);
    LiveSource source=sourceById(mCobraGuideSource);
    Button location=cobraTextAction(mCobraBrowseGroups?"Live TV  ›  "+(source==null?"All sources":source.name)+"  ▾":"‹  "+("ALL".equals(mCategory)?"All channels":mCategory.replace("MY:","")),false);
    location.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);
    location.setOnClickListener(v->{if(mCobraBrowseGroups)chooseCobraGuideSource();else{mCobraBrowseGroups=true;renderCobraGuideBody();}});
    crumb.addView(location,new LinearLayout.LayoutParams(0,dp(48),1));
    Button search=cobraTextAction("⌕",false);search.setContentDescription("Search channels");search.setOnClickListener(v->showSearch());crumb.addView(search,new LinearLayout.LayoutParams(dp(48),dp(48)));
    mCobraBrowseContent.addView(crumb,new LinearLayout.LayoutParams(-1,dp(48)));
    LinearLayout filters=new LinearLayout(this);
    String[] labels={"Favorites","Recently played","All","Categories"},keys={"FAVORITES","RECENT","ALL","CATEGORIES"};
    for(int i=0;i<keys.length;i++){final String key=keys[i];Button filter=cobraTextAction(labels[i],mCobraBrowseGroups?i==3:key.equals(mCategory));
      filter.setTextSize(11);filter.setOnClickListener(v->{if("CATEGORIES".equals(key)){mCobraBrowseGroups=true;renderCobraGuideBody();}else selectCobraCategory(key);});filters.addView(filter,new LinearLayout.LayoutParams(0,dp(48),1));}
    mCobraBrowseContent.addView(filters,new LinearLayout.LayoutParams(-1,dp(48)));
    if(mCobraBrowseGroups){
      ArrayList<String> groups=cobraGuideGroups();android.widget.ListView list=new android.widget.ListView(this);list.setDivider(null);list.setFastScrollEnabled(true);
      list.setAdapter(new android.widget.BaseAdapter(){
        @Override public int getCount(){return groups.size();}@Override public Object getItem(int i){return groups.get(i);}@Override public long getItemId(int i){return i;}
        @Override public View getView(int i,View recycled,android.view.ViewGroup parent){Button row=recycled instanceof Button?(Button)recycled:cobraTextAction("",false);
          String group=groups.get(i);row.setText(group.replace("MY:","My group · ")+"  ›");row.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);row.setTextSize(14);
          row.setOnClickListener(v->selectCobraCategory(group));row.setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,dp(56)));return row;}
      });mCobraBrowseContent.addView(list,new LinearLayout.LayoutParams(-1,0,1));return;
    }
    boolean timeline="grid".equals(mCobraBrowseMode)&&mCobraBrowseRoot.getWidth()>=dp(600)&&mCobraBrowseRoot.getWidth()>mCobraBrowseRoot.getHeight();
    if(timeline){
      LinearLayout times=new LinearLayout(this);Button earlier=cobraTextAction("‹",false),now=cobraTextAction("Now",false),later=cobraTextAction("›",false);
      earlier.setContentDescription("Previous guide hour");later.setContentDescription("Next guide hour");earlier.setOnClickListener(v->moveCobraGuideTime(-1));later.setOnClickListener(v->moveCobraGuideTime(1));now.setOnClickListener(v->moveCobraGuideTime(0));
      times.addView(earlier,new LinearLayout.LayoutParams(dp(48),dp(48)));times.addView(now,new LinearLayout.LayoutParams(dp(60),dp(48)));times.addView(later,new LinearLayout.LayoutParams(dp(48),dp(48)));
      View header=new View(this){final android.graphics.Paint paint=new android.graphics.Paint(3);@Override protected void onDraw(android.graphics.Canvas c){paint.setColor(cobraMutedInk());paint.setTextSize(dp(11));for(int i=0;i<4;i++)c.drawText(cobraClock(cobraGuideWindowStart()+i*1800000L),i*getWidth()/4f+dp(4),getHeight()/2f+dp(4),paint);}};
      mCobraTimelineHeader=header;times.addView(header,new LinearLayout.LayoutParams(0,dp(48),1));mCobraBrowseContent.addView(times,new LinearLayout.LayoutParams(-1,dp(48)));
    }
    ArrayList<Channel> channels=cobraVisibleGuideChannels(mCategory,mCobraGuideSource);
    if(channels.isEmpty()){
      TextView empty=cobraText("No channels here. Choose another category or clear search.",cobraMutedInk(),14,Gravity.CENTER);mCobraBrowseContent.addView(empty,new LinearLayout.LayoutParams(-1,0,1));return;
    }
    boolean cards="cards".equals(mCobraBrowseMode);boolean compact="compact".equals(mCobraBrowseMode);
    mCobraGuideAdapter=new android.widget.BaseAdapter(){
      @Override public int getCount(){return channels.size();}@Override public Channel getItem(int i){return channels.get(i);}@Override public long getItemId(int i){return channels.get(i).id.hashCode();}
      @Override public View getView(int i,View recycled,android.view.ViewGroup parent){
        CobraGuideRow row=recycled instanceof CobraGuideRow?(CobraGuideRow)recycled:new CobraGuideRow();
        row.bind(channels.get(i),timeline,compact,cards);
        row.setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,dp(cards?112:compact?56:timeline?66:86)));return row;
      }
    };
    if(cards){android.widget.GridView grid=new android.widget.GridView(this);int usable=mCobraBrowseContent.getWidth();if(usable<=0)usable=cobraWindowWidth();grid.setNumColumns(Math.max(1,usable/dp(250)));grid.setHorizontalSpacing(dp(8));grid.setVerticalSpacing(dp(8));grid.setAdapter(mCobraGuideAdapter);mCobraGuideList=grid;}
    else{android.widget.ListView list=new android.widget.ListView(this);list.setDivider(null);list.setAdapter(mCobraGuideAdapter);list.setFastScrollEnabled(true);mCobraGuideList=list;}
    mCobraGuideList.setSelector(android.R.color.transparent);mCobraBrowseContent.addView(mCobraGuideList,new LinearLayout.LayoutParams(-1,0,1));
  }
  private final class CobraGuideRow extends View{
    Channel channel;ArrayList<GuideProgram> programmes=new ArrayList<>();boolean timeline,compact,cards;
    final android.graphics.Paint paint=new android.graphics.Paint(3);float downX,downY;boolean horizontal,longPressed;
    final Runnable hold=()->{longPressed=true;performLongClick();};
    CobraGuideRow(){super(InfinityLiveActivity.this);setFocusable(true);setClickable(true);setLongClickable(true);setBackground(cobraTouchSurface(false,10));}
    void bind(Channel channel,boolean timeline,boolean compact,boolean cards){this.channel=channel;this.timeline=timeline;this.compact=compact;this.cards=cards;programmes=new ArrayList<>(cobraSchedule(channel));
      ProgramPair pair=programFor(channel);setContentDescription(channel.name+". "+(pair==null?cobraGuideMessage(channel):"Now "+pair.now+". Next "+pair.next)+". Activate to preview. Hold for channel actions.");invalidate();}
    void label(android.graphics.Canvas canvas,String value,float x,float y,float max,int color,int size,boolean bold){
      paint.setColor(color);paint.setTextSize(dp(size)*getResources().getConfiguration().fontScale);paint.setTypeface(bold?Typeface.DEFAULT_BOLD:Typeface.DEFAULT);
      String safe=value==null?"":value;int length=paint.breakText(safe,true,Math.max(0,max),null);if(length<safe.length()&&length>1)safe=safe.substring(0,length-1)+"…";else safe=safe.substring(0,length);canvas.drawText(safe,x,y,paint);
    }
    @Override protected void onDraw(android.graphics.Canvas canvas){
      if(channel==null)return;long now=System.currentTimeMillis();boolean active=mGuidePreviewChannel!=null&&channel.id.equals(mGuidePreviewChannel.id);
      float w=getWidth(),h=getHeight();paint.setColor(active?cobraAlpha(cobraThemeColor("accent",mTheme.accent),25):cards?cobraPanelColor():Color.TRANSPARENT);canvas.drawRoundRect(0,1,w,h-1,dp(10),dp(10),paint);
      if(active){paint.setColor(cobraThemeColor("accent",mTheme.accent));canvas.drawRoundRect(0,dp(10),dp(3),h-dp(10),dp(2),dp(2),paint);}
      if(timeline){
        float channelWidth=dp(156);label(canvas,channel.name,dp(12),h/2+dp(4),channelWidth-dp(20),cobraInk(),13,true);
        long start=cobraGuideWindowStart(),end=start+7200000L;float unit=(w-channelWidth)/7200000f;boolean any=false;
        int save=canvas.save();canvas.clipRect(channelWidth,0,w,h);
        for(GuideProgram p:programmes){if(p.stop<=start||p.start>=end)continue;any=true;float left=channelWidth+Math.max(0,p.start-start)*unit,right=channelWidth+Math.min(7200000L,p.stop-start)*unit;
          boolean on=CobraCore.current(p.start,p.stop,now);paint.setColor(on?cobraAlpha(cobraThemeColor("accent",mTheme.accent),38):cobraThemeColor("panel2",mTheme.panel2));canvas.drawRoundRect(left+dp(2),dp(3),right-dp(2),h-dp(3),dp(6),dp(6),paint);
          label(canvas,p.title,left+dp(8),dp(27),right-left-dp(16),cobraInk(),12,on);label(canvas,cobraClock(p.start)+" – "+cobraClock(p.stop),left+dp(8),dp(47),right-left-dp(16),cobraMutedInk(),10,false);
        }
        if(!any)label(canvas,cobraGuideMessage(channel),channelWidth+dp(10),h/2+dp(4),w-channelWidth-dp(20),cobraMutedInk(),12,false);
        if(now>=start&&now<end){paint.setColor(cobraThemeColor("accent",mTheme.accent));float x=channelWidth+(now-start)*unit;canvas.drawRect(x,0,x+dp(1),h,paint);}canvas.restoreToCount(save);
      }else{
        label(canvas,channel.name,dp(12),dp(23),w-dp(24),cobraInk(),compact?13:15,true);
        GuideProgram present=null,next=null;for(GuideProgram p:programmes){if(CobraCore.current(p.start,p.stop,now))present=p;else if(p.start>now&&next==null)next=p;}
        label(canvas,present==null?cobraGuideMessage(channel):"NOW  "+present.title,dp(12),dp(compact?43:46),w-dp(24),cobraMutedInk(),compact?11:12,false);
        if(!compact)label(canvas,next==null?"NEXT  Schedule unavailable":"NEXT  "+cobraClock(next.start)+"  "+next.title,dp(12),dp(67),w-dp(24),cobraMutedInk(),11,false);
        if(present!=null&&!compact){paint.setColor(cobraThemeColor("line",mTheme.line));canvas.drawRect(dp(12),h-dp(7),w-dp(12),h-dp(5),paint);paint.setColor(cobraThemeColor("accent",mTheme.accent));canvas.drawRect(dp(12),h-dp(7),dp(12)+(w-dp(24))*(now-present.start)/(float)(present.stop-present.start),h-dp(5),paint);}
      }
      if(isFocused()){paint.setStyle(android.graphics.Paint.Style.STROKE);paint.setStrokeWidth(dp(2));paint.setColor(cobraThemeColor("accent",mTheme.accent));canvas.drawRoundRect(dp(1),dp(1),w-dp(1),h-dp(1),dp(9),dp(9),paint);paint.setStyle(android.graphics.Paint.Style.FILL);}
    }
    @Override public boolean performClick(){super.performClick();if(channel!=null)selectGuidePreview(channel);return true;}
    @Override public boolean performLongClick(){super.performLongClick();if(channel!=null)showCobraChannelActions(channel);return true;}
    @Override public boolean onTouchEvent(android.view.MotionEvent e){
      if(e.getActionMasked()==android.view.MotionEvent.ACTION_DOWN){downX=e.getX();downY=e.getY();horizontal=false;longPressed=false;setPressed(true);postDelayed(hold,android.view.ViewConfiguration.getLongPressTimeout());return true;}
      if(e.getActionMasked()==android.view.MotionEvent.ACTION_MOVE){float dx=e.getX()-downX,dy=e.getY()-downY;if(Math.abs(dx)>dp(12)||Math.abs(dy)>dp(12)){removeCallbacks(hold);setPressed(false);}if(timeline&&Math.abs(dx)>dp(20)&&Math.abs(dx)>Math.abs(dy)*1.5){horizontal=true;getParent().requestDisallowInterceptTouchEvent(true);}return true;}
      if(e.getActionMasked()==android.view.MotionEvent.ACTION_UP){removeCallbacks(hold);setPressed(false);if(longPressed)return true;if(horizontal){moveCobraGuideTime(e.getX()<downX?1:-1);return true;}
        if(Math.abs(e.getX()-downX)>dp(16)||Math.abs(e.getY()-downY)>dp(16))return true;
        if(timeline&&e.getX()>dp(156)){long time=cobraGuideWindowStart()+(long)((e.getX()-dp(156))/Math.max(1,getWidth()-dp(156))*7200000L);for(GuideProgram p:programmes)if(time>=p.start&&time<p.stop&&!CobraCore.current(p.start,p.stop,System.currentTimeMillis())){showProgramActions(channel,p);return true;}}
        return performClick();}
      if(e.getActionMasked()==android.view.MotionEvent.ACTION_CANCEL){removeCallbacks(hold);setPressed(false);}return true;
    }
    @Override public boolean onKeyDown(int key,KeyEvent event){if(timeline&&(key==KeyEvent.KEYCODE_DPAD_LEFT||key==KeyEvent.KEYCODE_DPAD_RIGHT)){moveCobraGuideTime(key==KeyEvent.KEYCODE_DPAD_LEFT?-1:1);return true;}if(key==KeyEvent.KEYCODE_MENU){performLongClick();return true;}return super.onKeyDown(key,event);}
    @Override public void onInitializeAccessibilityNodeInfo(android.view.accessibility.AccessibilityNodeInfo info){super.onInitializeAccessibilityNodeInfo(info);info.setClassName(Button.class.getName());info.setContentDescription(getContentDescription());}
  }
  private void refreshCobraGuideViews(){
    if(mCobraRefreshQueued||!isCobraAsyncAlive())return;mCobraRefreshQueued=true;
    mMain.postDelayed(()->{mCobraRefreshQueued=false;if(!isCobraAsyncAlive())return;
      if(mCobraGuideAdapter!=null&&mCobraBrowseRoot!=null&&mCobraBrowseRoot.getParent()==mStage)mCobraGuideAdapter.notifyDataSetChanged();
      if(mCobraBrowseSummary!=null&&mGuidePreviewChannel!=null){ProgramPair pair=programFor(mGuidePreviewChannel);mCobraBrowseSummary.setText(mGuidePreviewChannel.name+"\n\n"+(pair==null?cobraGuideMessage(mGuidePreviewChannel):"NOW  "+pair.now+"\nNEXT  "+pair.next));}
      updateCobraPreviewPlayPause();updateCobraPlayerInformation();
      if(mCobraPlayerBrowserList!=null&&mCobraPlayerBrowserList.getAdapter() instanceof android.widget.BaseAdapter)((android.widget.BaseAdapter)mCobraPlayerBrowserList.getAdapter()).notifyDataSetChanged();
      if("schedule".equals(mCobraSheetKind)&&mCobraScheduleChannel!=null)renderCobraScheduleSheet(mCobraScheduleChannel);
      if(mCobraTimelineHeader!=null)mCobraTimelineHeader.invalidate();
    },48L);
  }
  private boolean cobraGuideBack(){if(mCobraBrowseRoot==null||mCobraBrowseRoot.getParent()!=mStage)return false;
    if(!mCobraBrowseGroups){mCobraBrowseGroups=true;renderCobraGuideBody();return true;}
    if(!mCobraGuideSource.isEmpty()){mCobraGuideSource="";renderCobraGuideBody();return true;}return false;
  }

// COBRA-REPLACE showCobraMobileView
  private void showCobraMobileView(){showCobraGuideExperience("mobile",false);}
// COBRA-REPLACE showGuideGrid
  private void showGuideGrid(){showCobraGuideExperience("grid",false);}
// COBRA-REPLACE showGuideCompact
  private void showGuideCompact(){showCobraGuideExperience("compact",false);}
// COBRA-REPLACE showGuideCards
  private void showGuideCards(){showCobraGuideExperience("cards",false);}
// COBRA-REPLACE showGuideFocus
  private void showGuideFocus(){showCobraGuideExperience("focus",false);}
// COBRA-REPLACE showCobraTvHub
  private void showCobraTvHub(){showCobraGuideExperience(cobraGuideViewMode(),true);}
// COBRA-REPLACE selectCobraCategory
  private void selectCobraCategory(String value){mCategory=value==null?"ALL":value;mSearch="";mCobraBrowseGroups=false;if(mCobraBrowseRoot!=null&&mCobraBrowseRoot.getParent()==mStage)renderCobraGuideBody();else showCobraPrimaryView();}
