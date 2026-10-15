// @replace showCobraTvHub
  private void showCobraTvHub(){mCobraModeGroupsExpanded=true;mCobraGuideRoute="categories";mCobraGuideStyle=cobraGuideViewMode();cobraShowGuideShell();}
// @replace showCobraMobileView
  private void showCobraMobileView(){mCobraGuideStyle="mobile";cobraShowGuideShell();}
// @replace showGuideGrid
  private void showGuideGrid(){mCobraGuideStyle="grid";cobraShowGuideShell();}
// @replace showGuideCompact
  private void showGuideCompact(){mCobraGuideStyle="compact";cobraShowGuideShell();}
// @replace showGuideCards
  private void showGuideCards(){mCobraGuideStyle="cards";cobraShowGuideShell();}
// @replace showGuideFocus
  private void showGuideFocus(){mCobraGuideStyle="focus";cobraShowGuideShell();}
// @replace selectCobraCategory
  private void selectCobraCategory(String value){cobraRememberModeScroll();mCategory=value;mSearch="";mCobraGuideRoute="channels";mCobraInspectedChannel=null;mCobraInspectedProgram=null;cobraShowGuideShell();}
// @replace cobraShowGuideShell
  private void cobraShowGuideShell(){
    if(mStage==null||!isCobraAsyncAlive())return;
    mCobraInternalScreen="root";
    if(!CobraModeLayout.valid(mCobraGuideStyle))mCobraGuideStyle="mobile";
    if("mobile".equals(mCobraGuideStyle))mPrefs.edit().putString(COBRA_PRIMARY_VIEW,"mobile").apply();
    else mPrefs.edit().putString(COBRA_PRIMARY_VIEW,"guide").putString(GUIDE_VIEW_MODE,mCobraGuideStyle).apply();
    if(mRail!=null)mRail.setVisibility(View.GONE);
    mHeader.setVisibility(View.GONE);mStatus.setVisibility(View.GONE);mStage.setPadding(dp(8),0,dp(8),0);
    if(mCobraGuideShell==null){
      mCobraGuideShell=new FrameLayout(this);mCobraGuideShell.setTag("cobra_persistent_guide_shell");
      mCobraGuideVideo=cobraPreviewPanel(mGuidePreviewChannel,true);
      mCobraGuideShell.addView(mCobraGuideVideo,new FrameLayout.LayoutParams(1,1));
      mCobraGuideDetails=new LinearLayout(this);mCobraGuideDetails.setOrientation(LinearLayout.VERTICAL);mCobraGuideDetails.setPadding(dp(12),dp(8),dp(12),dp(8));
      mCobraModeEyebrow=cobraText("",cobraModeColor("accent"),10);mCobraModeEyebrow.setLetterSpacing(.10f);mCobraModeEyebrow.setSingleLine(true);
      mCobraGuideNowLabel=cobraText("",cobraModeColor("text"),18);mCobraGuideNowLabel.setTypeface(Typeface.create("sans-serif-medium",0));mCobraGuideNowLabel.setMaxLines(2);
      mCobraGuideNextLabel=cobraText("",cobraModeColor("muted"),12);mCobraGuideNextLabel.setMaxLines(3);
      mCobraModeDescription=cobraText("",cobraModeColor("muted"),13);mCobraModeDescription.setMaxLines(5);
      mCobraGuideProgress=cobraProgress(cobraModeDark());
      mCobraGuideDetails.addView(mCobraModeEyebrow,new LinearLayout.LayoutParams(-1,-2));
      LinearLayout.LayoutParams title=new LinearLayout.LayoutParams(-1,-2);title.topMargin=dp(4);mCobraGuideDetails.addView(mCobraGuideNowLabel,title);
      LinearLayout.LayoutParams next=new LinearLayout.LayoutParams(-1,-2);next.topMargin=dp(4);mCobraGuideDetails.addView(mCobraGuideNextLabel,next);
      LinearLayout.LayoutParams progress=new LinearLayout.LayoutParams(-1,dp(3));progress.topMargin=dp(8);progress.bottomMargin=dp(8);mCobraGuideDetails.addView(mCobraGuideProgress,progress);
      mCobraGuideDetails.addView(mCobraModeDescription,new LinearLayout.LayoutParams(-1,-2));
      mCobraGuideDetails.setClickable(true);mCobraGuideDetails.setFocusable(true);mCobraGuideDetails.setOnClickListener(v->{Channel c=mCobraInspectedChannel!=null?mCobraInspectedChannel:mGuidePreviewChannel;if(c!=null){if(mCobraInspectedProgram!=null)showProgramActions(c,mCobraInspectedProgram);else showProgramGuide(c);}});
      mCobraGuideShell.addView(mCobraGuideDetails,new FrameLayout.LayoutParams(1,1));
      mCobraGuideBrowser=new LinearLayout(this);mCobraGuideBrowser.setOrientation(LinearLayout.VERTICAL);mCobraGuideShell.addView(mCobraGuideBrowser,new FrameLayout.LayoutParams(1,1));
      mCobraGuideDirectory=new LinearLayout(this);mCobraGuideDirectory.setOrientation(LinearLayout.VERTICAL);mCobraGuideShell.addView(mCobraGuideDirectory,new FrameLayout.LayoutParams(1,1));
      mCobraModeToolbar=new LinearLayout(this);mCobraModeToolbar.setGravity(Gravity.CENTER_VERTICAL);mCobraGuideShell.addView(mCobraModeToolbar,new FrameLayout.LayoutParams(1,1));
      mCobraModeRail=new LinearLayout(this);mCobraModeRail.setOrientation(LinearLayout.VERTICAL);mCobraGuideShell.addView(mCobraModeRail,new FrameLayout.LayoutParams(1,1));
      mCobraModeFooter=new LinearLayout(this);mCobraModeFooter.setTag("cobra_mode_bottom_navigation");mCobraGuideShell.addView(mCobraModeFooter,new FrameLayout.LayoutParams(1,1));
      mCobraGuideShell.addOnLayoutChangeListener((v,l,t,r,b,ol,ot,or,ob)->{if(r-l!=mCobraLastGuideWidth||b-t!=mCobraLastGuideHeight){cobraLayoutGuide();cobraRenderGuideBrowser();}});
    }
    if(mCobraGuideShell.getParent()!=mStage){
      while(mStage.getChildCount()>2)mStage.removeViewAt(2);
      if(mCobraGuideShell.getParent() instanceof android.view.ViewGroup)((android.view.ViewGroup)mCobraGuideShell.getParent()).removeView(mCobraGuideShell);
      mStage.addView(mCobraGuideShell,new LinearLayout.LayoutParams(-1,0,1));
    }
    cobraRestyleGuide();cobraLayoutGuide();cobraRenderGuideBrowser();
    if(mGuidePreviewChannel==null)ensureCobraPreviewSelection(new ArrayList<>(mChannels));
    if(mCobraPreviewAutoplayAllowed&&mCobraPreviewPlayer==null&&mPlayer==null&&mMultiOverlay==null&&mGuidePreviewChannel!=null)startCobraPreview(mGuidePreviewChannel);
    cobraRefreshProgrammeLabels();cobraStartPresentationTicker();
    for(LiveSource source:mSources)if(mFeatures.sourceEnabled(source.id))loadGuideAsync(source);
  }
// @replace cobraLayoutGuide
  private void cobraLayoutGuide(){
    if(mCobraGuideShell==null)return;int w=mCobraGuideShell.getWidth(),h=mCobraGuideShell.getHeight();if(w<=0||h<=0)return;
    mCobraLastGuideWidth=w;mCobraLastGuideHeight=h;
    int left=0,top=0,right=0,bottom=0;
    if(Build.VERSION.SDK_INT>=23&&mCobraGuideShell.getRootWindowInsets()!=null){
      android.view.WindowInsets in=mCobraGuideShell.getRootWindowInsets();int[] loc=new int[2];mCobraGuideShell.getLocationInWindow(loc);View decor=getWindow().getDecorView();
      left=Math.max(0,in.getSystemWindowInsetLeft()-loc[0]);top=Math.max(0,in.getSystemWindowInsetTop()-loc[1]);
      right=Math.max(0,loc[0]+w-(decor.getWidth()-in.getSystemWindowInsetRight()));bottom=Math.max(0,loc[1]+h-(decor.getHeight()-in.getSystemWindowInsetBottom()));
    }
    float density=getResources().getDisplayMetrics().density;
    mCobraModeLayout=CobraModeLayout.solve(mCobraGuideStyle,Math.max(1,Math.round((w-left-right)/density)),Math.max(1,Math.round((h-top-bottom)/density)),getResources().getConfiguration().fontScale,mCobraModeGroupsExpanded);
    View[] views={mCobraModeToolbar,mCobraModeRail,mCobraGuideDirectory,mCobraGuideVideo,mCobraGuideDetails,mCobraGuideBrowser,mCobraModeFooter};
    int[][] boxes={mCobraModeLayout.toolbar,mCobraModeLayout.rail,mCobraModeLayout.directory,mCobraModeLayout.video,mCobraModeLayout.details,mCobraModeLayout.browser,mCobraModeLayout.footer};
    for(int i=0;i<views.length;i++){int[] r=boxes[i];views[i].setVisibility(r[2]>0&&r[3]>0?View.VISIBLE:View.GONE);cobraPosition(views[i],left+dp(r[0]),top+dp(r[1]),dp(r[2]),dp(r[3]));}
    View controls=mCobraGuideVideo.findViewWithTag("cobra_preview_controls");
    if(controls!=null)controls.setVisibility(mCobraModeLayout.video[2]>=300&&mCobraModeLayout.video[3]>=145?View.VISIBLE:View.GONE);
    mCobraGuideNowLabel.setTextSize("focus".equals(mCobraGuideStyle)?22:"mobile".equals(mCobraGuideStyle)?18:15);
    mCobraGuideNowLabel.setMaxLines(mCobraModeLayout.details[3]>=110?2:1);
    mCobraGuideNextLabel.setMaxLines(mCobraModeLayout.details[3]>=110?3:1);
    mCobraGuideNextLabel.setVisibility(mCobraModeLayout.details[3]>=82?View.VISIBLE:View.GONE);
    mCobraModeEyebrow.setVisibility(mCobraModeLayout.details[3]>=54?View.VISIBLE:View.GONE);
    mCobraModeDescription.setVisibility(mCobraModeLayout.details[3]>=190?View.VISIBLE:View.GONE);
    cobraRefreshModeDetails();
  }
// @replace cobraRenderGuideBrowser
  private void cobraRenderGuideBrowser(){
    if(mCobraGuideBrowser==null||mCobraModeLayout==null)return;
    cobraRememberModeScroll();mCobraGuideBrowser.removeAllViews();mCobraGuideAdapter=null;mCobraGuideList=null;mCobraGuideRuler=null;mCobraModeDate=null;
    mCobraListStateKey=mCobraGuideStyle+"|"+mCobraGuideRoute+"|"+mCobraGuideSource+"|"+mCategory+"|"+mSearch+"|"+mCobraFocusSchedule;
    mCobraGuideDirectory.removeAllViews();
    boolean rail=mCobraModeLayout.directory[2]>0;
    if(rail){TextView label=cobraText("LIVE TV",cobraModeColor("muted"),11);label.setPadding(dp(14),0,0,0);mCobraGuideDirectory.addView(label,new LinearLayout.LayoutParams(-1,dp(32)));cobraDirectory(mCobraGuideDirectory,"sources".equals(mCobraGuideRoute));}
    if(!rail&&!"channels".equals(mCobraGuideRoute)){
      cobraModeBrowserHeader(mCobraGuideBrowser,"sources".equals(mCobraGuideRoute)?"Playlists":"Live TV / Groups");cobraDirectory(mCobraGuideBrowser,"sources".equals(mCobraGuideRoute));return;
    }
    ArrayList<Channel> channels=cobraGuideChannels();
    switch(mCobraGuideStyle){
      case "grid":cobraRenderGridMode(mCobraGuideBrowser,channels);break;
      case "compact":cobraRenderCompactMode(mCobraGuideBrowser,channels);break;
      case "cards":cobraRenderCardsMode(mCobraGuideBrowser,channels);break;
      case "focus":cobraRenderFocusMode(mCobraGuideBrowser,channels);break;
      default:cobraRenderMobileMode(mCobraGuideBrowser,channels);
    }
    if(!mCobraGuideStyle.equals(mCobraRenderedMode)){
      mCobraGuideBrowser.setAlpha(.65f);mCobraGuideBrowser.animate().alpha(1f).setDuration(160).start();mCobraRenderedMode=mCobraGuideStyle;
    }
    cobraRestoreModeScroll();cobraRefreshModeDetails();
  }
// @replace cobraDirectory
  private void cobraDirectory(LinearLayout parent,boolean sources){
    ArrayList<String> names=new ArrayList<>(),values=new ArrayList<>(),counts=new ArrayList<>();
    if(sources){names.add("All playlists");values.add("");counts.add("");for(LiveSource s:mSources)if(mFeatures.sourceEnabled(s.id)){names.add(s.name);values.add(s.id);counts.add("Playlist");}}
    else{
      java.util.TreeMap<String,Integer> groups=new java.util.TreeMap<>(String.CASE_INSENSITIVE_ORDER);int all=0,favorites=0,recent=0;
      for(Channel c:mChannels)if(cobraChannelAllowed(c)&&(mCobraGuideSource.isEmpty()||mCobraGuideSource.equals(sourceIdForChannel(c)))){all++;if(mFavorites.contains(c.id))favorites++;if(mRecents.contains(c.id))recent++;if(c.group!=null&&!c.group.isEmpty())groups.put(c.group,groups.containsKey(c.group)?groups.get(c.group)+1:1);}
      Collections.addAll(names,"Favorites","Recently played","All channels");Collections.addAll(values,"FAVORITES","RECENT","ALL");Collections.addAll(counts,""+favorites,""+recent,""+all);
      for(Map.Entry<String,Integer> e:groups.entrySet()){names.add(e.getKey());values.add(e.getKey());counts.add(""+e.getValue());}
      for(String group:cobraCustomGroups()){names.add(group);values.add("MY:"+group);counts.add("My group");}
    }
    if(!sources){Button playlist=cobraTextButton(cobraModeSourceName()+"  ▾",cobraModeDark(),()->{mCobraGuideRoute="sources";cobraRenderGuideBrowser();});playlist.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);playlist.setPadding(dp(12),0,dp(8),0);playlist.setSingleLine(true);parent.addView(playlist,new LinearLayout.LayoutParams(-1,dp(48)));}
    android.widget.ListView list=new android.widget.ListView(this);list.setDividerHeight(0);list.setSelector(android.R.color.transparent);
    list.setAdapter(new android.widget.BaseAdapter(){public int getCount(){return names.size();}public Object getItem(int p){return values.get(p);}public long getItemId(int p){return CobraModeLayout.stableId(values.get(p));}public boolean hasStableIds(){return true;}
      public View getView(int position,View recycled,android.view.ViewGroup host){
        CobraDirectoryRow row=recycled instanceof CobraDirectoryRow?(CobraDirectoryRow)recycled:new CobraDirectoryRow();String value=values.get(position);
        row.bind(names.get(position),counts.get(position),value.equals(sources?mCobraGuideSource:mCategory));
        row.setOnClickListener(v->{cobraRememberModeScroll();if(sources){mCobraGuideSource=value;mCobraGuideRoute="categories";cobraRenderGuideBrowser();}else selectCobraCategory(value);});return row;
      }});
    parent.addView(list,new LinearLayout.LayoutParams(-1,0,1));
  }
// @replace cobraRestyleGuide
  private void cobraRestyleGuide(){
    int bg=cobraModeColor("background");if(mRoot!=null)mRoot.setBackgroundColor(bg);if(mStage!=null)mStage.setBackgroundColor(bg);
    if(mHeader!=null)mHeader.setTextColor(cobraModeColor("text"));if(mStatus!=null)mStatus.setTextColor(cobraModeColor("muted"));
    if(mCobraGuideShell==null)return;mCobraGuideShell.setBackgroundColor(bg);mCobraGuideBrowser.setBackgroundColor(bg);
    mCobraGuideDirectory.setBackground(surface(cobraModeColor("rail"),"grid".equals(mCobraGuideStyle)?3:16,Color.TRANSPARENT,0));
    mCobraGuideDetails.setBackground(surface("mobile".equals(mCobraGuideStyle)?cobraModeColor("panel"):Color.TRANSPARENT,"mobile".equals(mCobraGuideStyle)?16:0,Color.TRANSPARENT,0));
    mCobraGuideNowLabel.setTextColor(cobraModeColor("text"));mCobraGuideNextLabel.setTextColor(cobraModeColor("muted"));mCobraModeDescription.setTextColor(cobraModeColor("muted"));mCobraModeEyebrow.setTextColor(cobraModeColor("accent"));
    cobraBuildModeChrome();
  }
