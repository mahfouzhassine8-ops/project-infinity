// @replace showCobraTvHub
  private void showCobraTvHub() {
    mCobraGuideRoute="categories";mCobraGuideStyle=cobraGuideViewMode();cobraShowGuideShell();
  }
// @replace showCobraMobileView
  private void showCobraMobileView() {
    mPrefs.edit().putString(COBRA_PRIMARY_VIEW,"mobile").apply();mCobraGuideStyle="mobile";cobraShowGuideShell();
  }
// @replace showGuideGrid
  private void showGuideGrid() {mCobraGuideStyle="grid";cobraShowGuideShell();}
// @replace showGuideCompact
  private void showGuideCompact() {mCobraGuideStyle="compact";cobraShowGuideShell();}
// @replace showGuideCards
  private void showGuideCards() {mCobraGuideStyle="cards";cobraShowGuideShell();}
// @replace showGuideFocus
  private void showGuideFocus() {mCobraGuideStyle="focus";cobraShowGuideShell();}
// @replace selectCobraCategory
  private void selectCobraCategory(String value) {
    mCategory=value;mSearch="";mCobraGuideRoute="channels";cobraShowGuideShell();
  }
// @replace selectGuidePreview
  private void selectGuidePreview(Channel channel) {
    if(channel==null)return;
    boolean active=mCobraPreviewPlayer!=null&&cobraChannelKey(channel).equals(mCobraPreviewSessionKey);
    if(active){promoteCobraPreviewToFullscreen(channel);return;}
    mGuidePreviewChannel=channel;mGuidePreviewKey=cobraChannelKey(channel);mGuidePreviewArmed=true;
    startCobraPreview(channel);cobraRefreshProgrammeLabels();
    if(mCobraGuideAdapter!=null)mCobraGuideAdapter.notifyDataSetChanged();
  }
// @replace cobraPreviewPanel
  private FrameLayout cobraPreviewPanel(Channel channel,boolean guide) {
    // Reuse the *view and surface*, not just the player. Navigation never calls prepare.
    if(mCobraPreviewHost!=null)return mCobraPreviewHost;
    FrameLayout host=new FrameLayout(this);mCobraPreviewHost=host;host.setTag("cobra_preview_host");
    host.setBackgroundColor(Color.BLACK);mCobraPreviewTexture=new TextureView(this);
    host.addView(mCobraPreviewTexture,new FrameLayout.LayoutParams(-1,-1));
    TextView state=cobraText("Select a channel",Color.WHITE,11);state.setTag("cobra_preview_label");
    state.setPadding(dp(10),dp(4),dp(10),dp(4));state.setBackgroundColor(0xa0000000);
    FrameLayout.LayoutParams sp=new FrameLayout.LayoutParams(-2,dp(28),Gravity.TOP|Gravity.RIGHT);sp.setMargins(dp(8),dp(8),dp(8),0);host.addView(state,sp);
    LinearLayout bar=new LinearLayout(this);bar.setGravity(Gravity.CENTER_VERTICAL);bar.setPadding(dp(6),0,dp(6),0);
    bar.setBackground(new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,new int[]{0x00000000,0xc9000000}));
    CobraIconButton pause=cobraIcon("pause","Pause preview",true,v->toggleCobraPreviewPlayPause());pause.setTag("cobra_preview_play_pause");
    CobraIconButton fav=cobraIcon("favorite","Favorite",true,v->{Channel c=mGuidePreviewChannel;if(c!=null){toggleFavorite(c);cobraRefreshProgrammeLabels();}});fav.setTag("cobra_preview_favorite");
    CobraIconButton mute=cobraIcon("audio","Mute or unmute preview",true,v->{toggleCobraPreviewMute();((CobraIconButton)v).icon(mCobraPreviewMuted?"mute":"audio");});
    CobraIconButton more=cobraIcon("more","Channel actions",true,v->{if(mGuidePreviewChannel!=null)showCobraChannelActions(mGuidePreviewChannel);});
    CobraIconButton full=cobraIcon("fullscreen","Fullscreen",true,v->{if(mGuidePreviewChannel!=null)promoteCobraPreviewToFullscreen(mGuidePreviewChannel);});
    for(Button b:new Button[]{pause,fav,mute,more,full})bar.addView(b,new LinearLayout.LayoutParams(0,dp(48),1));
    host.addView(bar,new FrameLayout.LayoutParams(-1,dp(50),Gravity.BOTTOM));
    host.setOnClickListener(v->{if(mGuidePreviewChannel!=null)promoteCobraPreviewToFullscreen(mGuidePreviewChannel);});
    host.setOnLongClickListener(v->{if(mGuidePreviewChannel!=null)showCobraChannelActions(mGuidePreviewChannel);return true;});
    return host;
  }
// @replace updateCobraPreviewDetails
  private void updateCobraPreviewDetails() {cobraRefreshProgrammeLabels();}
// @replace showProgramGuide
  private void showProgramGuide(Channel channel) {
    if(channel==null)return;cobraRequestShortEpg(channel);
    LinearLayout rows=cobraOpenSheet(channel.name,"Programme schedule","schedule");boolean dark=cobraSheetIsDark();
    ArrayList<GuideProgram> programs=cobraPrograms(channel);long now=System.currentTimeMillis();int shown=0;
    if(programs!=null)for(GuideProgram p:programs)if(p.stop>now-3600000L&&shown++<80){
      rows.addView(cobraSheetRow("guide",p.title,formatTime(p.start)+" – "+formatTime(p.stop),false,dark,()->showProgramActions(channel,p)));
    }
    if(shown==0){TextView empty=cobraText(cobraGuideStatus(channel),dark?0xffc5d0dd:cobraThemeColor("muted",mTheme.muted),14);empty.setPadding(dp(14),dp(18),dp(14),dp(18));rows.addView(empty);}
    rows.addView(cobraSheetRow("recent","Refresh guide","Retry this source without interrupting video",false,dark,()->cobraRefreshGuide(channel)));
  }
// @replace showProgramActions
  private void showProgramActions(Channel channel,GuideProgram program) {
    long now=System.currentTimeMillis();boolean dark=mPlayerOverlay!=null||mMultiOverlay!=null||!"light".equals(cobraEffectiveAppearanceMode());
    LinearLayout rows=cobraOpenSheet(program.title,formatTime(program.start)+" – "+formatTime(program.stop)+" • "+channel.name,"programme");
    if(!program.description.isEmpty()){TextView description=cobraText(program.description,dark?0xffc0cfdd:cobraThemeColor("text",mTheme.text),13);description.setMaxLines(7);description.setPadding(dp(14),dp(10),dp(14),dp(12));rows.addView(description);}
    rows.addView(cobraSheetRow("play","Watch channel live",null,false,dark,()->{if(mPlayerOverlay!=null)playChannel(channel);else selectGuidePreview(channel);}));
    if(program.start>now){
      rows.addView(cobraSheetRow("recent","Remind me",null,false,dark,()->{mFeatures.addReminder(sourceIdForChannel(channel),channel.id,program.title,Math.max(System.currentTimeMillis()+1000,program.start-60000));toast("Reminder set");}));
      rows.addView(cobraSheetRow("record","Schedule recording",null,false,dark,()->{mFeatures.scheduleRecording(channel.primaryUrl,program.title,channel.headers,Math.max(System.currentTimeMillis()+1000,program.start),program.stop,sourceIdForChannel(channel),channel.id);toast("Recording scheduled");}));
    }
    if(program.stop<now&&mArchiveChannels.contains(channel.id))rows.addView(cobraSheetRow("recent","Play catch-up",null,false,dark,()->playCatchup(channel,program)));
  }
// @append
  private void cobraShowGuideShell() {
    if(mStage==null||!isCobraAsyncAlive())return;
    mCobraInternalScreen="root";
    if(!"mobile".equals(mCobraGuideStyle))mPrefs.edit().putString(COBRA_PRIMARY_VIEW,"guide").apply();
    mHeader.setTypeface(Typeface.create("sans-serif-medium",Typeface.NORMAL));mHeader.setTextSize(19);
    mHeader.setText("☰  COBRA  /  "+("mobile".equals(mCobraGuideStyle)?"LIVE":"TV GUIDE"));
    mHeader.setBackgroundColor(Color.TRANSPARENT);mHeader.setPadding(dp(8),0,dp(8),0);
    LinearLayout.LayoutParams hp=new LinearLayout.LayoutParams(-1,dp(48));mHeader.setLayoutParams(hp);
    mStatus.setTypeface(Typeface.create("sans-serif",Typeface.NORMAL));mStatus.setTextSize(11);mStatus.setBackgroundColor(Color.TRANSPARENT);
    mStatus.setPadding(dp(8),0,dp(8),0);mStatus.setLayoutParams(new LinearLayout.LayoutParams(-1,dp(24)));
    if(mCobraGuideShell==null){
      mCobraGuideShell=new FrameLayout(this);mCobraGuideShell.setTag("cobra_persistent_guide_shell");
      mCobraGuideVideo=cobraPreviewPanel(mGuidePreviewChannel,true);mCobraGuideShell.addView(mCobraGuideVideo,new FrameLayout.LayoutParams(1,1));
      mCobraGuideDetails=new LinearLayout(this);mCobraGuideDetails.setOrientation(LinearLayout.VERTICAL);mCobraGuideDetails.setPadding(dp(10),dp(5),dp(8),dp(5));
      mCobraGuideNowLabel=cobraText("",cobraThemeColor("text",mTheme.text),15);mCobraGuideNowLabel.setTypeface(Typeface.create("sans-serif-medium",Typeface.NORMAL));mCobraGuideNowLabel.setSingleLine(true);
      mCobraGuideNextLabel=cobraText("",cobraThemeColor("muted",mTheme.muted),11);mCobraGuideNextLabel.setMaxLines(2);
      mCobraGuideProgress=cobraProgress(false);mCobraGuideDetails.addView(mCobraGuideNowLabel,new LinearLayout.LayoutParams(-1,dp(25)));mCobraGuideDetails.addView(mCobraGuideNextLabel,new LinearLayout.LayoutParams(-1,dp(32)));
      mCobraGuideDetails.addView(mCobraGuideProgress,new LinearLayout.LayoutParams(-1,dp(3)));mCobraGuideDetails.setOnClickListener(v->{if(mGuidePreviewChannel!=null)showProgramGuide(mGuidePreviewChannel);});
      mCobraGuideShell.addView(mCobraGuideDetails,new FrameLayout.LayoutParams(1,1));
      mCobraGuideBrowser=new LinearLayout(this);mCobraGuideBrowser.setOrientation(LinearLayout.VERTICAL);mCobraGuideShell.addView(mCobraGuideBrowser,new FrameLayout.LayoutParams(1,1));
      mCobraGuideDirectory=new LinearLayout(this);mCobraGuideDirectory.setOrientation(LinearLayout.VERTICAL);mCobraGuideShell.addView(mCobraGuideDirectory,new FrameLayout.LayoutParams(1,1));
      mCobraGuideShell.addOnLayoutChangeListener((v,l,t,r,b,ol,ot,or,ob)->{if(r-l!=mCobraLastGuideWidth||b-t!=mCobraLastGuideHeight){cobraLayoutGuide();cobraRenderGuideBrowser();}});
    }
    if(mCobraGuideShell.getParent()!=mStage){
      while(mStage.getChildCount()>2)mStage.removeViewAt(2);
      if(mCobraGuideShell.getParent() instanceof android.view.ViewGroup)((android.view.ViewGroup)mCobraGuideShell.getParent()).removeView(mCobraGuideShell);
      mStage.addView(mCobraGuideShell,new LinearLayout.LayoutParams(-1,0,1));
    }
    cobraLayoutGuide();cobraRenderGuideBrowser();
    if(mGuidePreviewChannel==null)ensureCobraPreviewSelection(new ArrayList<>(mChannels));
    if(mCobraPreviewAutoplayAllowed&&mCobraPreviewPlayer==null&&mPlayer==null&&mMultiOverlay==null&&mGuidePreviewChannel!=null)startCobraPreview(mGuidePreviewChannel);
    cobraRefreshProgrammeLabels();cobraStartPresentationTicker();
    for(LiveSource source:mSources)if(mFeatures.sourceEnabled(source.id))loadGuideAsync(source);
  }

  private android.widget.ProgressBar cobraProgress(boolean dark) {
    android.widget.ProgressBar bar=new android.widget.ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);bar.setMax(1000);
    bar.setProgressTintList(android.content.res.ColorStateList.valueOf(0xff41c8ef));
    bar.setProgressBackgroundTintList(android.content.res.ColorStateList.valueOf(dark?0xff465565:0xffd5dfe9));return bar;
  }

  private void cobraPosition(View child,int left,int top,int width,int height) {
    if(child==null)return;FrameLayout.LayoutParams p=new FrameLayout.LayoutParams(Math.max(1,width),Math.max(1,height));p.leftMargin=Math.max(0,left);p.topMargin=Math.max(0,top);child.setLayoutParams(p);
  }

  private void cobraLayoutGuide() {
    if(mCobraGuideShell==null)return;int w=mCobraGuideShell.getWidth(),h=mCobraGuideShell.getHeight();if(w<=0||h<=0)return;
    mCobraLastGuideWidth=w;mCobraLastGuideHeight=h;boolean wide=w>h&&w>=dp(600);boolean focus="focus".equals(mCobraGuideStyle);
    if(wide&&focus){int vw=(int)(w*.61f);cobraPosition(mCobraGuideVideo,0,0,vw,Math.min(h-dp(82),vw*9/16));cobraPosition(mCobraGuideDetails,0,Math.min(h-dp(82),vw*9/16),vw,dp(78));cobraPosition(mCobraGuideBrowser,vw+dp(12),0,w-vw-dp(12),h);mCobraGuideDirectory.setVisibility(View.GONE);}
    else if(wide){int ph=Math.min((int)(h*.37f),dp(190)),vw=Math.min(w/2,ph*16/9);cobraPosition(mCobraGuideVideo,0,0,vw,ph);cobraPosition(mCobraGuideDetails,vw+dp(12),dp(8),w-vw-dp(12),ph-dp(8));int rail=Math.min(dp(210),w/5);cobraPosition(mCobraGuideDirectory,0,ph+dp(10),rail,h-ph-dp(10));cobraPosition(mCobraGuideBrowser,rail+dp(8),ph+dp(10),w-rail-dp(8),h-ph-dp(10));mCobraGuideDirectory.setVisibility(View.VISIBLE);}
    else {int max="compact".equals(mCobraGuideStyle)?dp(135):(int)(h*(focus?.39f:.32f));int vh=Math.max(dp(96),Math.min(w*9/16,max));cobraPosition(mCobraGuideVideo,0,0,w,vh);cobraPosition(mCobraGuideDetails,0,vh,w,dp(72));cobraPosition(mCobraGuideBrowser,0,vh+dp(76),w,h-vh-dp(76));mCobraGuideDirectory.setVisibility(View.GONE);}
  }

  private ArrayList<Channel> cobraGuideChannels() {
    ArrayList<Channel> out=new ArrayList<>();for(Channel c:cobraChannelsForCurrentView())if(mCobraGuideSource.isEmpty()||mCobraGuideSource.equals(sourceIdForChannel(c)))out.add(c);return out;
  }

  private void cobraRenderGuideBrowser() {
    if(mCobraGuideBrowser==null)return;mCobraGuideBrowser.removeAllViews();mCobraGuideAdapter=null;mCobraGuideList=null;
    boolean dark=!"light".equals(cobraEffectiveAppearanceMode());boolean directory=mCobraGuideDirectory.getVisibility()==View.VISIBLE;
    if(directory){mCobraGuideDirectory.removeAllViews();cobraDirectory(mCobraGuideDirectory,false);}
    LinearLayout navigation=new LinearLayout(this);navigation.setGravity(Gravity.CENTER_VERTICAL);
    CobraIconButton groups=cobraIcon("guide","Browse categories",dark,v->{mCobraGuideRoute="categories";cobraRenderGuideBrowser();});groups.caption("Groups");navigation.addView(groups,new LinearLayout.LayoutParams(dp(52),dp(52)));
    TextView crumb=cobraText("sources".equals(mCobraGuideRoute)?"Playlists":"categories".equals(mCobraGuideRoute)?"Live TV / Groups":("FAVORITES".equals(mCategory)?"Favorites":"RECENT".equals(mCategory)?"Recently played":"ALL".equals(mCategory)?"All channels":mCategory),cobraThemeColor("text",mTheme.text),14);crumb.setSingleLine(true);crumb.setEllipsize(android.text.TextUtils.TruncateAt.END);navigation.addView(crumb,new LinearLayout.LayoutParams(0,dp(48),1));
    CobraIconButton source=cobraIcon("source","Select playlist",dark,v->{mCobraGuideRoute="sources";cobraRenderGuideBrowser();});navigation.addView(source,new LinearLayout.LayoutParams(dp(48),dp(48)));
    CobraIconButton search=cobraIcon("search","Search channels",dark,v->cobraShowChannelSearch());navigation.addView(search,new LinearLayout.LayoutParams(dp(48),dp(48)));
    mCobraGuideBrowser.addView(navigation,new LinearLayout.LayoutParams(-1,dp(52)));
    if(!"channels".equals(mCobraGuideRoute)){cobraDirectory(mCobraGuideBrowser,"sources".equals(mCobraGuideRoute));return;}
    ArrayList<Channel> channels=cobraGuideChannels();
    boolean timeline="grid".equals(mCobraGuideStyle)&&mCobraLastGuideWidth>mCobraLastGuideHeight&&mCobraLastGuideWidth>=dp(600);
    if(timeline){
      if(mCobraGuideWindow==0L){long now=System.currentTimeMillis();mCobraGuideWindow=now-now%1800000L;}
      LinearLayout times=new LinearLayout(this);times.setGravity(Gravity.CENTER_VERTICAL);
      CobraIconButton prev=cobraIcon("prev","Earlier programmes",dark,v->{mCobraGuideWindow-=3600000L;cobraRenderGuideBrowser();});times.addView(prev,new LinearLayout.LayoutParams(dp(48),dp(48)));
      Button now=cobraTextButton("Now",dark,()->{long time=System.currentTimeMillis();mCobraGuideWindow=time-time%1800000L;cobraRenderGuideBrowser();});times.addView(now,new LinearLayout.LayoutParams(dp(58),dp(48)));
      TextView label=cobraText(formatTime(mCobraGuideWindow)+"  —  "+formatTime(mCobraGuideWindow+7200000L),cobraThemeColor("muted",mTheme.muted),12);label.setGravity(Gravity.CENTER);times.addView(label,new LinearLayout.LayoutParams(0,dp(48),1));
      times.addView(cobraIcon("next","Later programmes",dark,v->{mCobraGuideWindow+=3600000L;cobraRenderGuideBrowser();}),new LinearLayout.LayoutParams(dp(48),dp(48)));mCobraGuideBrowser.addView(times,new LinearLayout.LayoutParams(-1,dp(48)));
    }
    if(channels.isEmpty()){TextView none=cobraText("No channels in this selection",cobraThemeColor("muted",mTheme.muted),14);none.setGravity(Gravity.CENTER);mCobraGuideBrowser.addView(none,new LinearLayout.LayoutParams(-1,0,1));return;}
    final boolean gridCards="cards".equals(mCobraGuideStyle)||"focus".equals(mCobraGuideStyle);
    android.widget.AbsListView list;
    if(gridCards){android.widget.GridView grid=new android.widget.GridView(this);int width=mCobraGuideBrowser.getWidth();grid.setNumColumns(Math.max(1,width/dp(240)));grid.setHorizontalSpacing(dp(8));grid.setVerticalSpacing(dp(6));list=grid;}
    else {android.widget.ListView rows=new android.widget.ListView(this);rows.setDivider(new android.graphics.drawable.ColorDrawable(cobraThemeColor("line",mTheme.line)));rows.setDividerHeight(dp(1));list=rows;}
    list.setSelector(android.R.color.transparent);list.setFastScrollEnabled(channels.size()>160);list.setOverScrollMode(View.OVER_SCROLL_IF_CONTENT_SCROLLS);
    final long window=mCobraGuideWindow;final String style=mCobraGuideStyle;
    mCobraGuideAdapter=new android.widget.BaseAdapter(){
      public int getCount(){return channels.size();}public Object getItem(int p){return channels.get(p);}public long getItemId(int p){return p;}
      public View getView(int position,View recycled,android.view.ViewGroup parent){Channel c=channels.get(position);
        if(timeline){CobraTimelineRow row=recycled instanceof CobraTimelineRow?(CobraTimelineRow)recycled:new CobraTimelineRow();row.bind(c,window);return row;}
        LinearLayout row=recycled instanceof LinearLayout?(LinearLayout)recycled:new LinearLayout(InfinityLiveActivity.this);row.removeAllViews();row.setOrientation(LinearLayout.VERTICAL);row.setGravity(Gravity.CENTER_VERTICAL);row.setPadding(dp(12),dp(6),dp(12),dp(6));row.setBackground(cobraPressSurface(dark));row.setSelected(mGuidePreviewChannel!=null&&c.id.equals(mGuidePreviewChannel.id));
        TextView title=cobraText((mFavorites.contains(c.id)?"♥  ":"")+c.name,cobraThemeColor("text",mTheme.text),14);title.setTypeface(Typeface.create("sans-serif-medium",Typeface.NORMAL));title.setSingleLine(true);title.setEllipsize(android.text.TextUtils.TruncateAt.END);row.addView(title,new LinearLayout.LayoutParams(-1,dp(23)));
        GuideProgram playing=cobraCurrentProgram(c),next=cobraNextProgram(c);TextView current=cobraText(playing==null?cobraGuideStatus(c):formatTime(playing.start)+"  "+playing.title,cobraThemeColor("muted",mTheme.muted),12);current.setSingleLine(true);current.setEllipsize(android.text.TextUtils.TruncateAt.END);row.addView(current,new LinearLayout.LayoutParams(-1,dp(20)));
        if(!"compact".equals(style)){TextView upcoming=cobraText(next==null?"Upcoming schedule unavailable":"Next  "+formatTime(next.start)+"  "+next.title,cobraThemeColor("muted",mTheme.muted),11);upcoming.setSingleLine(true);upcoming.setEllipsize(android.text.TextUtils.TruncateAt.END);row.addView(upcoming,new LinearLayout.LayoutParams(-1,dp(20)));}
        row.setFocusable(true);row.setFocusableInTouchMode(false);row.setOnClickListener(v->selectGuidePreview(c));row.setOnLongClickListener(v->{showCobraChannelActions(c);return true;});
        row.setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,dp("compact".equals(style)?60:gridCards?104:84)));return row;
      }};
    if(list instanceof android.widget.GridView)((android.widget.GridView)list).setAdapter(mCobraGuideAdapter);else ((android.widget.ListView)list).setAdapter(mCobraGuideAdapter);
    mCobraGuideList=list;mCobraGuideBrowser.addView(list,new LinearLayout.LayoutParams(-1,0,1));
    list.setOnScrollListener(new android.widget.AbsListView.OnScrollListener(){public void onScrollStateChanged(android.widget.AbsListView v,int state){if(state==SCROLL_STATE_IDLE)cobraQueueVisibleGuides();else mMain.removeCallbacks(mCobraVisibleGuideFetch);}public void onScroll(android.widget.AbsListView v,int first,int visible,int total){}});cobraQueueVisibleGuides();
  }

  private void cobraDirectory(LinearLayout parent,boolean sources) {
    ArrayList<String> labels=new ArrayList<>(),values=new ArrayList<>();
    if(sources){labels.add("All playlists");values.add("");for(LiveSource s:mSources)if(mFeatures.sourceEnabled(s.id)){labels.add(s.name);values.add(s.id);}}
    else {labels.add("Favorites");values.add("FAVORITES");labels.add("Recently played");values.add("RECENT");labels.add("All channels");values.add("ALL");java.util.TreeSet<String> groups=new java.util.TreeSet<>(String.CASE_INSENSITIVE_ORDER);
      for(Channel c:mChannels)if(!isCobraHidden(c)&&!mFeatures.looksAdult(c.name)&&!mFeatures.looksAdult(c.group)&&(mCobraGuideSource.isEmpty()||mCobraGuideSource.equals(sourceIdForChannel(c))))if(c.group!=null&&!c.group.isEmpty())groups.add(c.group);
      for(String g:groups){labels.add(g);values.add(g);}for(String g:cobraCustomGroups()){labels.add(g);values.add("MY:"+g);}}
    android.widget.ListView list=new android.widget.ListView(this);list.setDividerHeight(0);list.setSelector(android.R.color.transparent);boolean dark=!"light".equals(cobraEffectiveAppearanceMode());
    list.setAdapter(new android.widget.BaseAdapter(){public int getCount(){return labels.size();}public Object getItem(int p){return labels.get(p);}public long getItemId(int p){return p;}public View getView(int p,View old,android.view.ViewGroup host){
      Button row=old instanceof Button?(Button)old:new Button(InfinityLiveActivity.this);row.setAllCaps(false);row.setText(labels.get(p));row.setSingleLine(true);row.setEllipsize(android.text.TextUtils.TruncateAt.END);row.setTypeface(Typeface.create("sans-serif-medium",Typeface.NORMAL));row.setTextSize(14);row.setTextColor(cobraThemeColor("text",mTheme.text));row.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);row.setPadding(dp(14),0,dp(12),0);row.setBackground(cobraPressSurface(dark));row.setSelected(values.get(p).equals(sources?mCobraGuideSource:mCategory));row.setFocusableInTouchMode(false);row.setOnClickListener(v->{if(sources){mCobraGuideSource=values.get(p);mCobraGuideRoute="categories";cobraRenderGuideBrowser();}else selectCobraCategory(values.get(p));});row.setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,dp(52)));return row;}});
    parent.addView(list,new LinearLayout.LayoutParams(-1,0,1));
  }

  private Button cobraTextButton(String label,boolean dark,Runnable action) {
    Button b=new Button(this);b.setAllCaps(false);b.setText(label);b.setTextSize(13);b.setTypeface(Typeface.create("sans-serif-medium",Typeface.NORMAL));b.setTextColor(dark?Color.WHITE:cobraThemeColor("text",mTheme.text));b.setMinWidth(0);b.setMinimumWidth(0);b.setPadding(dp(6),0,dp(6),0);b.setBackground(cobraPressSurface(dark));b.setOnClickListener(v->action.run());return b;
  }

  private void cobraShowChannelSearch() {
    LinearLayout sheet=cobraOpenSheet("Search Live TV","Search this playlist without stopping video","search");boolean dark=cobraSheetIsDark();
    EditText input=new EditText(this);input.setSingleLine(true);input.setTextColor(dark?Color.WHITE:cobraThemeColor("text",mTheme.text));input.setHintTextColor(dark?0xffa7b6c7:cobraThemeColor("muted",mTheme.muted));input.setHint("Channel name");input.setText(mSearch);sheet.addView(input,new LinearLayout.LayoutParams(-1,dp(52)));
    sheet.addView(cobraSheetRow("search","Search",null,false,dark,()->{mSearch=input.getText().toString().trim();mCategory="ALL";mCobraGuideRoute="channels";cobraRenderGuideBrowser();((android.view.inputmethod.InputMethodManager)getSystemService(INPUT_METHOD_SERVICE)).hideSoftInputFromWindow(input.getWindowToken(),0);}));
    sheet.addView(cobraSheetRow("close","Clear search",null,false,dark,()->{mSearch="";mCobraGuideRoute="channels";cobraRenderGuideBrowser();}));
  }

  private final class CobraTimelineRow extends FrameLayout {
    Channel channel;long window;int labelWidth;final android.graphics.Paint line=new android.graphics.Paint(3);final ArrayList<float[]> bounds=new ArrayList<>();
    CobraTimelineRow(){super(InfinityLiveActivity.this);setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,dp(74)));}
    void bind(Channel c,long time){channel=c;window=time;removeAllViews();bounds.clear();boolean dark=!"light".equals(cobraEffectiveAppearanceMode());
      Button title=cobraTextButton(c.name,dark,()->selectGuidePreview(c));title.setTextSize(12);title.setMaxLines(2);title.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);title.setSelected(mGuidePreviewChannel!=null&&c.id.equals(mGuidePreviewChannel.id));title.setOnLongClickListener(v->{showCobraChannelActions(c);return true;});addView(title);bounds.add(null);
      ArrayList<GuideProgram> programs=cobraPrograms(c);int count=0;
      if(programs!=null)for(GuideProgram p:programs){float[] interval=CobraGuideMath.interval(p.start,p.stop,time,7200000L);if(interval==null)continue;Button cell=cobraTextButton(p.title,dark,()->{long n=System.currentTimeMillis();if(p.start<=n&&p.stop>n)selectGuidePreview(c);else showProgramActions(c,p);});cell.setMaxLines(2);cell.setTextSize(11);cell.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);cell.setContentDescription(formatTime(p.start)+" to "+formatTime(p.stop)+", "+p.title);cell.setSelected(p.start<=System.currentTimeMillis()&&p.stop>System.currentTimeMillis());cell.setOnLongClickListener(v->{showProgramActions(c,p);return true;});addView(cell);bounds.add(interval);count++;}
      if(count==0){Button empty=cobraTextButton(cobraGuideStatus(c),dark,()->showProgramGuide(c));empty.setTextSize(11);addView(empty);bounds.add(new float[]{0f,1f});}
      requestLayout();invalidate();
    }
    @Override protected void onMeasure(int width,int height){int w=View.MeasureSpec.getSize(width),h=dp(74);labelWidth=Math.max(dp(110),Math.min(dp(180),w/4));setMeasuredDimension(w,h);for(int i=0;i<getChildCount();i++){float[] r=bounds.get(i);int cw=r==null?labelWidth:Math.max(1,Math.round((w-labelWidth)*(r[1]-r[0]))-dp(2));getChildAt(i).measure(View.MeasureSpec.makeMeasureSpec(cw,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h-dp(3),View.MeasureSpec.EXACTLY));}}
    @Override protected void onLayout(boolean change,int l,int t,int r,int b){int w=r-l;for(int i=0;i<getChildCount();i++){View v=getChildAt(i);float[] range=bounds.get(i);int x=range==null?0:labelWidth+Math.round((w-labelWidth)*range[0]);v.layout(x,0,x+v.getMeasuredWidth(),v.getMeasuredHeight());}}
    @Override protected void dispatchDraw(android.graphics.Canvas c){super.dispatchDraw(c);long now=System.currentTimeMillis();if(now>=window&&now<=window+7200000L){float x=labelWidth+(getWidth()-labelWidth)*(now-window)/7200000f;line.setColor(0xffff526b);line.setStrokeWidth(dp(2));c.drawLine(x,0,x,getHeight(),line);}}
  }

  private void cobraRefreshProgrammeLabels() {
    if(!isCobraAsyncAlive())return;
    Channel channel=mGuidePreviewChannel;GuideProgram now=cobraCurrentProgram(channel),next=cobraNextProgram(channel);
    if(mCobraGuideNowLabel!=null)mCobraGuideNowLabel.setText(channel==null?"Select a channel":channel.name+(now==null?"":"  ·  "+now.title));
    if(mCobraGuideNextLabel!=null)mCobraGuideNextLabel.setText(now==null?cobraGuideStatus(channel):(formatTime(now.start)+" – "+formatTime(now.stop)+"  ·  "+Math.max(0,(now.stop-System.currentTimeMillis()+59999)/60000)+" min left\n"+(next==null?"Upcoming schedule unavailable":"Next  "+next.title)));
    if(mCobraGuideProgress!=null){mCobraGuideProgress.setVisibility(now==null?View.INVISIBLE:View.VISIBLE);if(now!=null)mCobraGuideProgress.setProgress(Math.round(CobraGuideMath.progress(now.start,now.stop,System.currentTimeMillis())*1000));}
    if(mCobraPreviewHost!=null){View favorite=mCobraPreviewHost.findViewWithTag("cobra_preview_favorite");if(favorite instanceof CobraIconButton)((CobraIconButton)favorite).icon(channel!=null&&mFavorites.contains(channel.id)?"favorite_on":"favorite");}
    channel=mPlaying;now=cobraCurrentProgram(channel);next=cobraNextProgram(channel);
    if(mCobraPlayerProgram!=null)mCobraPlayerProgram.setText(now==null?channel==null?"":channel.name:now.title);
    if(mCobraPlayerSchedule!=null)mCobraPlayerSchedule.setText(now==null?cobraGuideStatus(channel):formatTime(now.start)+" – "+formatTime(now.stop)+"   ·   "+Math.max(0,(now.stop-System.currentTimeMillis()+59999)/60000)+" min left");
    if(mCobraPlayerUpcoming!=null)mCobraPlayerUpcoming.setText(next==null?"":"Next  "+next.title);
    if(mCobraPlayerProgramProgress!=null){mCobraPlayerProgramProgress.setVisibility(now==null?View.INVISIBLE:View.VISIBLE);if(now!=null)mCobraPlayerProgramProgress.setProgress(Math.round(CobraGuideMath.progress(now.start,now.stop,System.currentTimeMillis())*1000));}
    if(mPlayerOverlay!=null){View play=mPlayerOverlay.findViewWithTag("cobra_player_play_pause");if(play instanceof CobraIconButton)((CobraIconButton)play).icon(mPlayer!=null&&mPlayer.getPlayWhenReady()?"pause":"play");}
  }

  private void cobraRefreshGuide(Channel channel) {
    if(channel==null)return;String id=sourceIdForChannel(channel);mCobraEpgLastAttempt.remove(id);mCobraShortEpgAttempt.remove(channel.id);mCobraShortEpgStatus.remove(channel.id);
    if(mCobraEpgRequest.containsKey(id)){toast("Guide refresh is already running");return;}
    for(LiveSource source:mSources)if(source.id.equals(id)){
      mCobraEpgLastAttempt.remove(id+"|"+cobraEpgIdentity(source));
      CobraEpgData old=mCobraEpg.get(id);if(old!=null)old.fetched=0;final java.io.File cache=cobraEpgCacheFile(id);
      // Invalidate the private cache before dispatching the refresh, never the channel library.
      submitCobraIo(()->{new android.util.AtomicFile(cache).delete();new android.util.AtomicFile(cobraEpgCacheFile("@short:"+channel.id)).delete();publishCobraUi(()->{loadGuideAsync(source);cobraRequestShortEpg(channel);});});break;
    }
    toast("Refreshing programme guide");
  }
