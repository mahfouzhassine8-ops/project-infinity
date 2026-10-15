// @append
  private boolean cobraModeDark(){return !"light".equals(cobraEffectiveAppearanceMode());}
  private int cobraModeColor(String name){
    boolean dark=cobraModeDark(),oled="oled".equals(cobraEffectiveAppearanceMode()),tv="grid".equals(mCobraGuideStyle);
    if("accent".equals(name))return cobraThemeColor("accent",mTheme.accent);
    if("text".equals(name))return dark?0xffeef3f8:0xff152536;
    if("muted".equals(name))return dark?0xffa6b5c6:0xff526476;
    if("line".equals(name))return dark?0xff2a3542:0xffd4dde7;
    if("rail".equals(name))return oled?0xff080b10:dark?0xff151c25:0xffe4eaf1;
    if("panel".equals(name))return oled?0xff0c1118:dark?0xff1a2430:Color.WHITE;
    return oled?Color.BLACK:dark?(tv?0xff0e141d:0xff0a121c):(tv?0xffedf1f6:0xfff4f7fb);
  }
  private String cobraModeName(String key){return "grid".equals(key)?"TV Grid":"compact".equals(key)?"Compact":"cards".equals(key)?"Cards":"focus".equals(key)?"Focus":"Mobile";}
  private String cobraModeSourceName(){for(LiveSource s:mSources)if(s.id.equals(mCobraGuideSource))return s.name;return "All playlists";}
  private String cobraModeGroupName(){return "ALL".equals(mCategory)?"All channels":"FAVORITES".equals(mCategory)?"Favorites":"RECENT".equals(mCategory)?"Recently played":mCategory==null?"All channels":mCategory.startsWith("MY:")?mCategory.substring(3):mCategory;}
  private int cobraModeRowHeight(String mode){return dp(CobraModeLayout.cellHeight(mode,getResources().getConfiguration().fontScale));}
  private void cobraRememberModeScroll(){
    if(mCobraGuideList==null||mCobraListStateKey.isEmpty())return;
    View first=mCobraGuideList.getChildCount()>0?mCobraGuideList.getChildAt(0):null;
    mCobraModeScroll.put(mCobraListStateKey,new int[]{mCobraGuideList.getFirstVisiblePosition(),first==null?0:first.getTop()});
    View focus=mCobraGuideList.findFocus();if(focus!=null&&focus.getTag() instanceof String)mCobraModeFocused.put(mCobraListStateKey,(String)focus.getTag());
    while(mCobraModeScroll.size()>32){String key=mCobraModeScroll.keySet().iterator().next();mCobraModeScroll.remove(key);mCobraModeFocused.remove(key);}
  }
  private void cobraRestoreModeScroll(){
    if(mCobraGuideList==null)return;int[] saved=mCobraModeScroll.get(mCobraListStateKey);
    if(saved!=null&&mCobraGuideList.getCount()>0){int p=Math.min(saved[0],mCobraGuideList.getCount()-1);if(mCobraGuideList instanceof android.widget.ListView)((android.widget.ListView)mCobraGuideList).setSelectionFromTop(p,saved[1]);else mCobraGuideList.setSelection(p);}
    final android.widget.AbsListView list=mCobraGuideList;String tag=mCobraModePendingFocus.isEmpty()?mCobraModeFocused.get(mCobraListStateKey):mCobraModePendingFocus;mCobraModePendingFocus="";
    if(tag!=null&&!tag.isEmpty()&&!list.isInTouchMode())list.post(()->{if(list!=mCobraGuideList)return;View view=list.findViewWithTag(tag);if(view!=null)view.requestFocus();});
  }
  private void cobraSwitchMode(String mode){
    if(!CobraModeLayout.valid(mode))return;cobraRememberModeScroll();closeCobraActionSheet();closeCobraExperienceDrawer();
    mCobraGuideStyle=mode;mCobraGuideRoute="channels";mCobraInspectedChannel=null;mCobraInspectedProgram=null;cobraShowGuideShell();
  }
  private void cobraBuildModeChrome(){
    if(mCobraModeToolbar==null)return;boolean dark=cobraModeDark();mCobraModeToolbar.removeAllViews();
    mCobraModeToolbar.addView(cobraIcon("guide","Open Cobra navigation",dark,v->toggleCobraDrawer()),new LinearLayout.LayoutParams(dp(48),-1));
    LinearLayout title=new LinearLayout(this);title.setOrientation(LinearLayout.VERTICAL);title.setGravity(Gravity.CENTER_VERTICAL);title.setPadding(dp(8),0,0,0);
    mCobraModeTitle=cobraText(cobraModeName(mCobraGuideStyle),cobraModeColor("text"),19);mCobraModeTitle.setTypeface(Typeface.create("sans-serif-medium",0));mCobraModeTitle.setSingleLine(true);
    mCobraModeSub=cobraText("COBRA LIVE",cobraModeColor("muted"),10);mCobraModeSub.setSingleLine(true);mCobraModeSub.setLetterSpacing(.10f);title.addView(mCobraModeTitle);title.addView(mCobraModeSub);title.setOnClickListener(v->showCobraViewModeMenu());
    mCobraModeToolbar.addView(title,new LinearLayout.LayoutParams(0,-1,1));
    CobraIconButton play=cobraIcon("pause","Play or pause live preview",dark,v->{toggleCobraPreviewPlayPause();cobraRefreshModeDetails();});play.setTag("cobra_mode_play_pause");mCobraModeToolbar.addView(play,new LinearLayout.LayoutParams(dp(48),-1));
    mCobraModeToolbar.addView(cobraIcon("multi","Choose one of five view modes",dark,v->showCobraViewModeMenu()),new LinearLayout.LayoutParams(dp(48),-1));
    mCobraModeRail.removeAllViews();mCobraModeRail.setBackgroundColor(cobraModeColor("rail"));
    String[] icons={"search","guide","favorite","recent","multi","more"},labels={"Search","Groups","Favorites","Recent","Views","Menu"};
    for(int i=0;i<icons.length;i++){final int action=i;CobraIconButton b=cobraIcon(icons[i],labels[i],dark,v->{if(action==0)cobraShowChannelSearch();else if(action==1)cobraToggleModeGroups();else if(action==2)selectCobraCategory("FAVORITES");else if(action==3)selectCobraCategory("RECENT");else if(action==4)showCobraViewModeMenu();else toggleCobraDrawer();});mCobraModeRail.addView(b,new LinearLayout.LayoutParams(-1,dp(48)));}
    mCobraModeFooter.removeAllViews();mCobraModeFooter.setBackground(surface(cobraModeColor("panel"),18,Color.TRANSPARENT,0));
    String[] fi={"play","guide","search","multi"},fl={"Live","Groups","Search","Views"};
    for(int i=0;i<fi.length;i++){final int a=i;CobraIconButton b=cobraIcon(fi[i],fl[i],dark,v->{if(a==0){mCobraGuideRoute="channels";cobraRenderGuideBrowser();}else if(a==1)cobraToggleModeGroups();else if(a==2)cobraShowChannelSearch();else showCobraViewModeMenu();});b.caption(fl[i]);mCobraModeFooter.addView(b,new LinearLayout.LayoutParams(0,-1,1));}
  }
  private void cobraToggleModeGroups(){
    cobraRememberModeScroll();if(mCobraModeLayout!=null&&mCobraModeLayout.wide&&"grid".equals(mCobraGuideStyle))mCobraModeGroupsExpanded=!mCobraModeGroupsExpanded;
    mCobraGuideRoute="channels".equals(mCobraGuideRoute)?"categories":"channels";cobraLayoutGuide();cobraRenderGuideBrowser();
  }
  private void cobraModeBrowserHeader(LinearLayout parent,String name){
    LinearLayout row=new LinearLayout(this);row.setGravity(Gravity.CENTER_VERTICAL);
    Button group=cobraTextButton(name+"  ▾",cobraModeDark(),()->cobraToggleModeGroups());group.setSingleLine(true);group.setEllipsize(android.text.TextUtils.TruncateAt.END);group.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);group.setPadding(dp(10),0,dp(4),0);
    row.addView(group,new LinearLayout.LayoutParams(0,dp(48),1));row.addView(cobraIcon("source","Choose playlist",cobraModeDark(),v->{mCobraGuideRoute="sources";cobraRenderGuideBrowser();}),new LinearLayout.LayoutParams(dp(48),dp(48)));
    row.addView(cobraIcon("search","Search channels",cobraModeDark(),v->cobraShowChannelSearch()),new LinearLayout.LayoutParams(dp(48),dp(48)));parent.addView(row,new LinearLayout.LayoutParams(-1,dp(48)));
  }
  private void cobraModeFilters(LinearLayout parent){
    LinearLayout tabs=new LinearLayout(this);tabs.setPadding(dp(2),dp(2),dp(2),dp(2));tabs.setBackground(surface(cobraModeColor("panel"),16,Color.TRANSPARENT,0));
    String[] keys={"ALL","FAVORITES","RECENT"},names={"All","Favorites","Recent"};
    for(int i=0;i<3;i++){final String key=keys[i];Button b=cobraTextButton(names[i],cobraModeDark(),()->selectCobraCategory(key));b.setSelected(key.equals(mCategory));tabs.addView(b,new LinearLayout.LayoutParams(0,dp(48),1));}
    LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,dp(52));p.bottomMargin=dp(8);parent.addView(tabs,p);
  }
  private void cobraModeEmpty(LinearLayout parent,String text){TextView empty=cobraText(text,cobraModeColor("muted"),14);empty.setGravity(Gravity.CENTER);empty.setPadding(dp(20),dp(12),dp(20),dp(12));parent.addView(empty,new LinearLayout.LayoutParams(-1,0,1));}
  private void cobraInstallModeList(LinearLayout parent,android.widget.AbsListView list,android.widget.BaseAdapter adapter){
    mCobraGuideList=list;mCobraGuideAdapter=adapter;list.setSelector(android.R.color.transparent);list.setOverScrollMode(View.OVER_SCROLL_IF_CONTENT_SCROLLS);list.setFastScrollEnabled(adapter.getCount()>160);list.setClipToPadding(false);
    if(list instanceof android.widget.GridView)((android.widget.GridView)list).setAdapter(adapter);else{((android.widget.ListView)list).setItemsCanFocus("grid".equals(mCobraGuideStyle));((android.widget.ListView)list).setDividerHeight(0);((android.widget.ListView)list).setAdapter(adapter);}
    parent.addView(list,new LinearLayout.LayoutParams(-1,0,1));
    list.setOnScrollListener(new android.widget.AbsListView.OnScrollListener(){public void onScrollStateChanged(android.widget.AbsListView v,int state){if(state==SCROLL_STATE_IDLE)cobraQueueVisibleGuides();else mMain.removeCallbacks(mCobraVisibleGuideFetch);}public void onScroll(android.widget.AbsListView v,int a,int b,int c){}});cobraQueueVisibleGuides();
  }
  private abstract class CobraModeAdapter extends android.widget.BaseAdapter{
    final ArrayList<Channel> channels;CobraModeAdapter(ArrayList<Channel> values){channels=values;}
    public int getCount(){return channels.size();}public Channel getItem(int p){return channels.get(p);}public long getItemId(int p){return CobraModeLayout.stableId(channels.get(p).id);}public boolean hasStableIds(){return true;}
  }
