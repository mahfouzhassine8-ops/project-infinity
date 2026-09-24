#!/usr/bin/env python3
"""2103237 RC17 — TV startup/section ownership/on-demand player cleanup over locked RC16.

Authorized behavior:
- Remove upper-right Choose Experience Settings controls from Infinity and Cobra cards/scenes.
- Choosing Cobra explicitly starts the integrated Live TV shell with Drawer + Groups + Grid.
- Live TV Drawer: Right=Select, Left=Back. Live TV Groups/playlist directory: Right=Select, Left=Back.
- Persist explicit section owner for Live TV / Movies / Shows. No automatic Movies/Shows -> Live TV fallback.
- VOD player removes Live-TV-only controls and key actions (Channels, Multi-View, channel stepping,
  last channel, channel favorite, live rewind/go-live, live recording, live EPG/timeshift chrome).
- Preserve locked RC16 pulsing dot, glass shell, native engine, playback/timeshift engine, Multi-View Live TV,
  providers, permanent signer and ARMv7 target.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

VERSION=2103237
OLD_VERSION=2103236
OLD_NAME='1.0.9-Cobra-Onn4KPro-TV-Pulsing-Dot-RC16'
NEW_NAME='1.0.9-Cobra-Onn4KPro-TV-Section-Owner-RC17'
SOURCE='tools/android/packaging/xbmc/'
ACT=SOURCE+'src/InfinityLiveActivity.java.in'
SPLASH=SOURCE+'src/Splash.java.in'

def hb(v): return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()
def sha(p): return hb(Path(p).read_bytes())
def req(v,m):
    if not v: raise RuntimeError(m)
def once(s,a,b,label):
    req(s.count(a)==1,f'{label}: expected 1 anchor, got {s.count(a)}')
    return s.replace(a,b,1)
def span(text,name,kind='method'):
    if kind=='method':
        p=re.compile(r'(?m)^\s*(?:@Override\s+)?(?:(?:public|private|protected|static|final|synchronized)\s+)*[\w.<>,\[\]?]+\s+'+re.escape(name)+r'\s*\([^\n{;]*\)\s*\{')
    else:
        p=re.compile(r'(?m)^\s*(?:(?:private|public|protected|static|final)\s+)*class\s+'+re.escape(name)+r'\b')
    ms=list(p.finditer(text));req(len(ms)==1,f'{kind} cardinality {name}={len(ms)}')
    st=ms[0].start();b=text.rfind('{',st,ms[0].end());req(b>=st,'opening brace missing: '+name);d=0;q=None;esc=line=block=False
    for i in range(b,len(text)):
        c=text[i];n=text[i+1] if i+1<len(text) else ''
        if line:
            if c=='\n':line=False
        elif block:
            if c=='*' and n=='/':block=False
        elif q:
            if esc:esc=False
            elif c=='\\':esc=True
            elif c==q:q=None
        elif c=='/' and n=='/':line=True
        elif c=='/' and n=='*':block=True
        elif c in ('"',"'"):q=c
        elif c=='{':d+=1
        elif c=='}':
            d-=1
            if d==0:return st,i+1
    raise RuntimeError('unclosed '+name)
def member(text,name,kind='method'):
    a,b=span(text,name,kind);return text[a:b]
def repl(text,name,new,kind='method'):
    a,b=span(text,name,kind);return text[:a]+new.rstrip()+"\n"+text[b:]

def patch_splash(path:Path):
    before=path.read_bytes();s=before.decode()
    protected=['onCreate','startXBMC','showInfinityHealthCenter','showCobraRecovery']
    hashes={n:hb(member(s,n)) for n in protected}

    legacy=member(s,'showLegacyInfinityExperienceChooser')
    legacy=once(legacy,
'''    android.widget.Button infinitySettings = new android.widget.Button(this);
    infinitySettings.setText("⚙");
    infinitySettings.setTextColor(white);
    infinitySettings.setTextSize(18);
    infinitySettings.setAllCaps(false);
    infinitySettings.setPadding(0, 0, 0, 0);
    infinitySettings.setMinHeight(0);
    infinitySettings.setMinWidth(0);
    infinitySettings.setContentDescription("Infinity settings");
    infinitySettings.setBackground(chooserControlSurface(panel, rim, 18));
    android.widget.FrameLayout.LayoutParams infinityGearParams =
        new android.widget.FrameLayout.LayoutParams(
            chooserDp(48), chooserDp(48), android.view.Gravity.TOP | android.view.Gravity.END);
    infinityGearParams.setMargins(0, chooserDp(10), chooserDp(10), 0);
    infinityCard.addView(infinitySettings, infinityGearParams);

''','',
'legacy Infinity chooser settings removal')
    legacy=once(legacy,
'''    android.widget.Button cobraSettings = new android.widget.Button(this);
    cobraSettings.setText("⚙");
    cobraSettings.setTextColor(white);
    cobraSettings.setTextSize(18);
    cobraSettings.setAllCaps(false);
    cobraSettings.setPadding(0, 0, 0, 0);
    cobraSettings.setMinHeight(0);
    cobraSettings.setMinWidth(0);
    cobraSettings.setContentDescription("Cobra settings");
    cobraSettings.setBackground(chooserControlSurface(panel, rim, 18));
    android.widget.FrameLayout.LayoutParams cobraGearParams =
        new android.widget.FrameLayout.LayoutParams(
            chooserDp(48), chooserDp(48), android.view.Gravity.TOP | android.view.Gravity.END);
    cobraGearParams.setMargins(0, chooserDp(10), chooserDp(10), 0);
    cobraCard.addView(cobraSettings, cobraGearParams);

''','',
'legacy Cobra chooser settings removal')
    legacy=once(legacy,
'''    infinitySettings.setOnClickListener(v -> showExperienceCardSettings("infinity"));
    cobraSettings.setOnClickListener(v -> showExperienceCardSettings("live"));
''','',
'legacy chooser settings click removal')
    s=repl(s,'showLegacyInfinityExperienceChooser',legacy)

    card=member(s,'chooserExperienceCard')
    start=card.index('    android.widget.TextView gear = chooserStyledText(')
    end=card.index('    card.setOnClickListener',start)
    card=card[:start]+card[end:]
    req('experience-settings-' not in card and 'settings.run()' not in card,'Styled chooser card settings survived')
    s=repl(s,'chooserExperienceCard',card)

    visual=member(s,'showVisualExperienceScene')
    old='''        android.widget.TextView settings=chooserStyledText(vtheme().copy("chooser.showVisualExperienceScene.copy.2","Settings"),theme.text,14,false,android.view.Gravity.CENTER);settings.setFocusable(true);settings.setClickable(true);settings.setTag("experience-settings-"+experience);settings.setContentDescription(experience+" settings");settings.setOnClickListener(v->showExperienceCardSettings(destination));
        settings.setBackground(chooserSurface(theme.background,experience.equals("infinity")?theme.infinityBorder:theme.cobraBorder,16));slots.put("settings."+experience,settings);'''
    new='''        View removedSettings=new View(this);removedSettings.setVisibility(View.GONE);removedSettings.setFocusable(false);removedSettings.setClickable(false);removedSettings.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);slots.put("settings."+experience,removedSettings);'''
    visual=once(visual,old,new,'custom chooser settings slots')
    s=repl(s,'showVisualExperienceScene',visual)

    s=repl(s,'cobraAttachRecoveryGear',r'''  private void cobraAttachRecoveryGear(android.widget.FrameLayout root){
    // RC17: chooser card Settings/recovery gear is intentionally not exposed.
    // Recovery remains available through normal Cobra Settings / recovery flows.
    mCobraRecoveryGear=null;
  }''')

    launch=member(s,'launchInfinityExperience')
    # The first overload found by method parser is the one-argument wrapper. Patch the 3-arg body directly by anchor.
    s=once(s,
'''    if ("live".equals(experience))
      intent.putExtra("infinity_live_profile", "cobra");''',
'''    if ("live".equals(experience)){
      intent.putExtra("infinity_live_profile", "cobra");
      intent.putExtra("cobra_start_destination", "live_tv");
    }''','Cobra chooser startup destination')

    for n,h in hashes.items():req(hb(member(s,n))==h,'Protected Splash method changed: '+n)
    req('experience-settings-infinity' not in s,'Infinity chooser settings tag still exposed')
    req('experience-settings-cobra' not in s,'Cobra chooser settings tag still exposed')
    req('cobra_start_destination' in s,'Cobra explicit startup marker missing')
    path.write_text(s)
    return hb(before),sha(path)

def patch_activity(path:Path):
    before=path.read_bytes();s=before.decode()
    req('class CobraTvPlayingDot extends View' in s,'Locked RC16 pulsing-dot parent missing')
    req('COBRA_TV_FINAL_POLISH_BUILD="cobra_tv_final_polish_2103235"' in s,'RC15 parent marker missing')

    protected_methods=[
      'playChannel','startCobraPreview','promoteCobraPreviewToFullscreen',
      'cobraReturnToMultiFromFullscreen','setMultiAudio','cobraLayoutPlayerPanels',
      'cobraTvChannelPlaybackState','cobraTvChannelPlaying','cobraTvPlayingDotColor'
    ]
    protected={n:hb(member(s,n)) for n in protected_methods}

    s=once(s,
'''  private static final String COBRA_PRIMARY_VIEW = "cobra_primary_view";''',
'''  private static final String COBRA_PRIMARY_VIEW = "cobra_primary_view";
  private static final String COBRA_SECTION_OWNER = "cobra_section_owner";
  private static final String COBRA_SECTION_LIVE_TV = "LIVE_TV";
  private static final String COBRA_SECTION_MOVIES = "MOVIES";
  private static final String COBRA_SECTION_SHOWS = "SHOWS";
  private String mCobraSectionOwner=COBRA_SECTION_LIVE_TV;
  private boolean mCobraChooserLiveStart=false;''','section ownership fields')

    s=once(s,
'''    mPrefs = getSharedPreferences(PREFS, MODE_PRIVATE);
    mFeatures = new InfinityCobraFeatureRuntime(this);''',
'''    mPrefs = getSharedPreferences(PREFS, MODE_PRIVATE);
    mCobraSectionOwner=cobraNormalizeSectionOwner(mPrefs.getString(COBRA_SECTION_OWNER,COBRA_SECTION_LIVE_TV));
    mCobraChooserLiveStart=getIntent()!=null&&"live_tv".equals(getIntent().getStringExtra("cobra_start_destination"));
    if(mCobraChooserLiveStart)cobraSetSectionOwner(COBRA_SECTION_LIVE_TV);
    mFeatures = new InfinityCobraFeatureRuntime(this);''','onCreate section owner initialization')

    owner_helpers=r'''  private String cobraNormalizeSectionOwner(String value){
    if(COBRA_SECTION_MOVIES.equals(value))return COBRA_SECTION_MOVIES;
    if(COBRA_SECTION_SHOWS.equals(value))return COBRA_SECTION_SHOWS;
    return COBRA_SECTION_LIVE_TV;
  }
  private void cobraSetSectionOwner(String owner){
    String normalized=cobraNormalizeSectionOwner(owner);mCobraSectionOwner=normalized;
    if(mPrefs!=null)mPrefs.edit().putString(COBRA_SECTION_OWNER,normalized).apply();
  }
  private boolean cobraVodSectionOwner(){
    return COBRA_SECTION_MOVIES.equals(mCobraSectionOwner)||COBRA_SECTION_SHOWS.equals(mCobraSectionOwner);
  }
  private boolean cobraOnDemandPlayer(){return mPlayingVodKey!=null&&!mPlayingVodKey.isEmpty();}
  private String cobraOnDemandSectionLabel(){return COBRA_SECTION_SHOWS.equals(mCobraSectionOwner)?"TV SHOW":"MOVIE";}
  private boolean cobraAtOwnedVodLanding(){
    if(COBRA_SECTION_MOVIES.equals(mCobraSectionOwner))return "COBRA • MOVIES".equals(mCobraStageTitle);
    if(COBRA_SECTION_SHOWS.equals(mCobraSectionOwner))return "COBRA • TV SHOWS".equals(mCobraStageTitle);
    return false;
  }
  private void cobraOpenLiveTvStartup(){
    cobraSetSectionOwner(COBRA_SECTION_LIVE_TV);mCobraGuideRoute="channels";mCobraModeGroupsExpanded=true;mCobraGuideStyle="grid";
    cobraShowGuideShell();
    if(mCobraGuideShell!=null)mCobraGuideShell.post(()->{
      if(mCobraTvDrawerPanel==null||!mCobraTvDrawerPanel.isAttachedToWindow())toggleCobraDrawer();
      else cobraTvFocusDrawer(mCobraTvDrawerPanel);
    });
  }
  private void cobraShowLoadedPrimary(){
    if(mCobraChooserLiveStart){mCobraChooserLiveStart=false;cobraOpenLiveTvStartup();return;}
    if(cobraVodSectionOwner()){showCobraPrimaryView();return;}
    if(!cobraTrySmartReturn())showCobraPrimaryView();
  }

'''
    marker='  private String cobraPrimaryView() {'
    req(s.count(marker)==1,'primary-view helper insertion drift')
    s=s.replace(marker,owner_helpers+marker,1)

    s=repl(s,'showCobraPrimaryView',r'''  private void showCobraPrimaryView() {
    if(COBRA_SECTION_MOVIES.equals(mCobraSectionOwner)){showMovies();return;}
    if(COBRA_SECTION_SHOWS.equals(mCobraSectionOwner)){showSeries();return;}
    cobraOpenLiveTv();
    mMain.post(this::cobraApplySystemBarsForSurface);
  }''')

    s=repl(s,'cobraOpenLiveTv',r'''  private void cobraOpenLiveTv(){
    cobraSetSectionOwner(COBRA_SECTION_LIVE_TV);
    mCobraGuideRoute="channels";mCobraModeGroupsExpanded=true;
    if("mobile".equals(mCobraGuideStyle))mCobraGuideStyle="grid";
    cobraShowGuideShell();
    if(mCobraGuideShell!=null)mCobraGuideShell.post(this::cobraTvAnimateGroupPanelIn);
  }''')

    s=repl(s,'showMovies',r'''  private void showMovies() {
    cobraSetSectionOwner(COBRA_SECTION_MOVIES);
    mCobraInternalScreen = "internal";
    showVodLibrary(false);
  }''')
    s=repl(s,'showSeries',r'''  private void showSeries() {
    cobraSetSectionOwner(COBRA_SECTION_SHOWS);
    mCobraInternalScreen = "internal";
    showVodLibrary(true);
  }''')

    s=once(s,
'''        if(!hadVisible){if(!cobraTrySmartReturn())showCobraPrimaryView();}
        else if(changed)cobraTvScheduleGuideRebuild(220L);''',
'''        if(!hadVisible)cobraShowLoadedPrimary();
        else if(changed)cobraTvScheduleGuideRebuild(220L);''','cold source load section restore')
    s=once(s,
'''    if(!cobraTrySmartReturn())showCobraPrimaryView();
  }

  private static final String COBRA_TV_PLAYER_MULTIVIEW_BUILD''',
'''    cobraShowLoadedPrimary();
  }

  private static final String COBRA_TV_PLAYER_MULTIVIEW_BUILD''','warm source load section restore')

    s=repl(s,'onBackPressed',r'''  @Override public void onBackPressed(){
    if(mCobraPlayerLocked&&mPlayerOverlay!=null){showCobraPlayerUnlockAffordance();return;}
    if(closeCobraActionSheet())return;
    if(mCobraMultiPicker!=null){closeCobraMultiPicker(false);return;}
    if(mCobraPlayerDrawer!=null){if(mCobraDrawerFilter.startsWith("GROUP:")){cobraRenderPlayerDrawer("CATEGORIES");return;}closeCobraPlayerDrawer();return;}
    if(mCobraTvDrawerPanel!=null&&mCobraTvDrawerPanel.isAttachedToWindow()){cobraTvCloseDrawerRestoreFocus();return;}
    if(closeCobraPowerMenu()||closeCobraViewModeMenu()||closeCobraChannelActions())return;
    if(mCobraMultiFullscreenActive&&mPlayerOverlay!=null){cobraReturnToMultiFromFullscreen();return;}
    if(mPlayerOverlay!=null){closeFullscreenToCobraView();return;}
    if(mMultiOverlay!=null){releaseMulti();return;}
    if(cobraRestoreVodLandingReturn())return;
    if(!"root".equals(mCobraInternalScreen)){
      if(cobraAtOwnedVodLanding()){toggleCobraDrawer();return;}
      showCobraPrimaryView();return;
    }
    if("grid".equals(mCobraGuideStyle)&&mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow()){
      if(!mSearch.isEmpty()){mSearch="";cobraRenderGuideBrowser();return;}
      if("sources".equals(mCobraGuideRoute)){mCobraGuideRoute="channels";cobraRenderGuideBrowser();return;}
      if(!mCobraModeGroupsExpanded){cobraTvShowGroupChooser(true);return;}
      toggleCobraDrawer();return;
    }
    if(mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow()&&"channels".equals(mCobraGuideRoute)){cobraTvShowGroupChooser(true);return;}
    if("sources".equals(mCobraGuideRoute)){mCobraGuideRoute="channels";cobraRenderGuideBrowser();return;}
    toggleCobraDrawer();
  }''')

    s=repl(s,'cobraTvHandleDrawerKey',r'''  private boolean cobraTvHandleDrawerKey(KeyEvent event){
    if(mCobraTvDrawerPanel==null||!mCobraTvDrawerPanel.isAttachedToWindow()||event.getAction()!=KeyEvent.ACTION_DOWN)return false;
    int code=event.getKeyCode();
    if(code==KeyEvent.KEYCODE_BACK||code==KeyEvent.KEYCODE_DPAD_LEFT){cobraTvCloseDrawerRestoreFocus();return true;}
    if(code==KeyEvent.KEYCODE_DPAD_UP)return cobraTvMoveDrawerFocus(-1);
    if(code==KeyEvent.KEYCODE_DPAD_DOWN)return cobraTvMoveDrawerFocus(1);
    if(code==KeyEvent.KEYCODE_DPAD_RIGHT){
      View focus=getCurrentFocus();if(focus!=null&&focus.isShown()&&focus.isEnabled()&&focus.isClickable())focus.performClick();
      return true;
    }
    return false;
  }''')

    directory=member(s,'cobraDirectory')
    directory=directory.replace(
'''      playlist.setOnKeyListener((v,key,event)->{if(event.getAction()==KeyEvent.ACTION_DOWN&&key==KeyEvent.KEYCODE_DPAD_RIGHT){v.performClick();return true;}return false;});''',
'''      playlist.setOnKeyListener((v,key,event)->{if(event.getAction()!=KeyEvent.ACTION_DOWN)return false;if(key==KeyEvent.KEYCODE_DPAD_RIGHT){v.performClick();return true;}if(key==KeyEvent.KEYCODE_DPAD_LEFT){toggleCobraDrawer();return true;}return false;});''')
    directory=directory.replace(
'''        row.setOnKeyListener((v,key,event)->{if(event.getAction()==KeyEvent.ACTION_DOWN&&key==KeyEvent.KEYCODE_DPAD_RIGHT){v.performClick();return true;}return false;});''',
'''        row.setOnKeyListener((v,key,event)->{if(event.getAction()!=KeyEvent.ACTION_DOWN)return false;if(key==KeyEvent.KEYCODE_DPAD_RIGHT){v.performClick();return true;}if(key==KeyEvent.KEYCODE_DPAD_LEFT){if(sources)closeCobraActionSheet();else toggleCobraDrawer();return true;}return false;});''')
    req('KEYCODE_DPAD_LEFT' in directory and 'performClick()' in directory,'Directory Left/Right mapping missing')
    s=repl(s,'cobraDirectory',directory)

    drawer_dest=member(s,'cobraTvDrawerDestination')
    drawer_dest=drawer_dest.replace(
'''    if(title.contains("MY LIST")||title.contains("WATCHLIST"))return "MY LIST";
    if(mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow())return "TV";
    return "TV";''',
'''    if(title.contains("MY LIST")||title.contains("WATCHLIST"))return "MY LIST";
    if(COBRA_SECTION_MOVIES.equals(mCobraSectionOwner))return "MOVIES";
    if(COBRA_SECTION_SHOWS.equals(mCobraSectionOwner))return "SHOWS";
    return "TV";''')
    s=repl(s,'cobraTvDrawerDestination',drawer_dest)

    # VOD player chrome: remove Live-TV-only controls at construction time.
    chrome=member(s,'cobraBuildPlayerChrome')
    chrome=once(chrome,
'''    boolean visible=mPlayerChrome==null||mPlayerChrome.getVisibility()==View.VISIBLE;boolean shortScreen=height<dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.1",340));''',
'''    boolean visible=mPlayerChrome==null||mPlayerChrome.getVisibility()==View.VISIBLE;boolean shortScreen=height<dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.1",340));boolean onDemand=cobraOnDemandPlayer();''',
'player VOD context')
    chrome=once(chrome,
'''    CobraIconButton headerBack=cobraIcon("back",mCobraMultiFullscreenActive?"Return to Multi-View":"Back to guide",true,v->closeFullscreenToCobraView());headerBack.setTag("cobra_tv_player_header_back");header.addView(headerBack,new LinearLayout.LayoutParams(dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.5",48)),dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.6",48))));''',
'''    String backLabel=mCobraMultiFullscreenActive?"Return to Multi-View":onDemand?(COBRA_SECTION_SHOWS.equals(mCobraSectionOwner)?"Back to Shows":"Back to Movies"):"Back to guide";
    CobraIconButton headerBack=cobraIcon("back",backLabel,true,v->closeFullscreenToCobraView());headerBack.setTag("cobra_tv_player_header_back");header.addView(headerBack,new LinearLayout.LayoutParams(dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.5",48)),dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.6",48))));''',
'player back context')
    old_header='''    mCobraLastChannelButton=cobraIcon("recent","Last channel",true,v->cobraTuneLastChannel());mCobraLastChannelButton.setTag("cobra_last_channel");mCobraLastChannelButton.setOnLongClickListener(v->{mCobraNextSheetAnchor=v;try{cobraShowPlaybackRecents();}finally{mCobraNextSheetAnchor=null;}return true;});cobraUpdateLastChannelButton();header.addView(mCobraLastChannelButton,new LinearLayout.LayoutParams(dp(46),dp(46)));
    CobraIconButton headerFavorite=cobraIcon(mPlaying!=null&&mFavorites.contains(mPlaying.id)?"favorite_on":"favorite","Favorite",true,v->{if(mPlaying!=null){toggleFavorite(mPlaying);((CobraIconButton)v).icon(mFavorites.contains(mPlaying.id)?"favorite_on":"favorite");}});headerFavorite.setTag("cobra_tv_player_header_favorite");header.addView(headerFavorite,new LinearLayout.LayoutParams(dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.10",48)),dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.11",48))));'''
    new_header='''    mCobraLastChannelButton=null;
    if(!onDemand){
      mCobraLastChannelButton=cobraIcon("recent","Last channel",true,v->cobraTuneLastChannel());mCobraLastChannelButton.setTag("cobra_last_channel");mCobraLastChannelButton.setOnLongClickListener(v->{mCobraNextSheetAnchor=v;try{cobraShowPlaybackRecents();}finally{mCobraNextSheetAnchor=null;}return true;});cobraUpdateLastChannelButton();header.addView(mCobraLastChannelButton,new LinearLayout.LayoutParams(dp(46),dp(46)));
      CobraIconButton headerFavorite=cobraIcon(mPlaying!=null&&mFavorites.contains(mPlaying.id)?"favorite_on":"favorite","Favorite",true,v->{if(mPlaying!=null){toggleFavorite(mPlaying);((CobraIconButton)v).icon(mFavorites.contains(mPlaying.id)?"favorite_on":"favorite");}});headerFavorite.setTag("cobra_tv_player_header_favorite");header.addView(headerFavorite,new LinearLayout.LayoutParams(dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.10",48)),dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.11",48))));
    }'''
    chrome=once(chrome,old_header,new_header,'VOD last/favorite removal')

    t0=chrome.index('    LinearLayout transport=new LinearLayout(this);')
    t1=chrome.index('    chrome.addView(new View(this),new LinearLayout.LayoutParams(1,0,1));',t0)
    transport=r'''    LinearLayout transport=new LinearLayout(this);mCobraTvPlayerTransport=transport;transport.setGravity(Gravity.CENTER);transport.setPadding(dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.14",16)),0,dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.15",16)),0);
    mCobraLiveRewindButton=null;mCobraGoLiveButton=null;
    CobraIconButton pause=cobraIcon("pause","Pause",true,v->toggleCobraPlayerPlayPause());pause.setTag("cobra_player_play_pause");pause.setBackground(new android.graphics.drawable.RippleDrawable(android.content.res.ColorStateList.valueOf(0x4062aaff),cobraPanelSurface(vtheme().color("cobra.cobraBuildPlayerChrome.colors.5",0xc909101c),40,vtheme().color("cobra.cobraBuildPlayerChrome.colors.6",0x906b9ccc)),surface(Color.WHITE,40,Color.TRANSPARENT,0)));
    if(!onDemand){
      CobraIconButton prev=cobraIcon("prev","Previous channel",true,v->stepChannel(-1));prev.setTag("cobra_tv_player_transport_prev");
      CobraIconButton rewind=cobraIcon("prev","Rewind Live TV 30 seconds",true,v->cobraRewindLive(30000L));rewind.caption("-30s");rewind.setTag("cobra_live_rewind_30");mCobraLiveRewindButton=rewind;
      CobraIconButton live=cobraIcon("play","Go Live",true,v->cobraGoLive());live.caption("LIVE");live.setTag("cobra_live_edge");mCobraGoLiveButton=live;
      CobraIconButton next=cobraIcon("next","Next channel",true,v->stepChannel(1));next.setTag("cobra_tv_player_transport_next");
      if(mCobraMultiFullscreenActive){prev.setEnabled(false);next.setEnabled(false);}
      transport.addView(prev,new LinearLayout.LayoutParams(dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.16",56)),dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.17",56))));
      transport.addView(rewind,new LinearLayout.LayoutParams(dp(52),dp(52)));
      LinearLayout.LayoutParams pp=new LinearLayout.LayoutParams(dp(shortScreen?56:68),dp(shortScreen?56:68));pp.leftMargin=dp(14);pp.rightMargin=dp(14);transport.addView(pause,pp);
      transport.addView(live,new LinearLayout.LayoutParams(dp(52),dp(52)));
      transport.addView(next,new LinearLayout.LayoutParams(dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.20",56)),dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.21",56))));
    }else{
      transport.addView(pause,new LinearLayout.LayoutParams(dp(shortScreen?56:68),dp(shortScreen?56:68)));
    }
    chrome.addView(transport,new LinearLayout.LayoutParams(-1,dp(shortScreen?60:76)));
'''
    chrome=chrome[:t0]+transport+chrome[t1:]

    timeline_start=chrome.index('    FrameLayout timeline=new FrameLayout(this);')
    timeline_end=chrome.index('    LinearLayout tools=new LinearLayout(this);',timeline_start)
    timeline=r'''    mCobraPlayerProgramProgress=null;mCobraTimeshiftSeek=null;
    if(!onDemand){
      FrameLayout timeline=new FrameLayout(this);timeline.setTag("cobra_unified_live_timeline");
      mCobraPlayerProgramProgress=new CobraLiveTimelineProgress();FrameLayout.LayoutParams lineProgress=new FrameLayout.LayoutParams(-1,dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.31",3)),Gravity.CENTER_VERTICAL);timeline.addView(mCobraPlayerProgramProgress,lineProgress);
      cobraResetTimelineGesture();mCobraTimeshiftSeek=new android.widget.SeekBar(this);mCobraTimeshiftSeek.setTag("cobra_live_timeshift_seek");mCobraTimeshiftSeek.setMax(1000);mCobraTimeshiftSeek.setVisibility(View.GONE);mCobraTimeshiftSeek.setContentDescription("Live TV timeline");mCobraTimeshiftSeek.setSplitTrack(false);mCobraTimeshiftSeek.setPadding(0,0,0,0);mCobraTimeshiftSeek.setProgressTintList(android.content.res.ColorStateList.valueOf(Color.TRANSPARENT));mCobraTimeshiftSeek.setProgressBackgroundTintList(android.content.res.ColorStateList.valueOf(Color.TRANSPARENT));mCobraTimeshiftSeek.setFocusable(true);mCobraTimeshiftSeek.setFocusableInTouchMode(false);mCobraTimeshiftSeek.setOnKeyListener((v,key,event)->{if(event.getAction()!=KeyEvent.ACTION_DOWN)return false;if(key==KeyEvent.KEYCODE_DPAD_LEFT)return cobraTvNudgeTimeline(-1);if(key==KeyEvent.KEYCODE_DPAD_RIGHT)return cobraTvNudgeTimeline(1);if(key==KeyEvent.KEYCODE_DPAD_UP){cobraTvFocusPlayerPrimary();return true;}return false;});cobraPolishFocusable(mCobraTimeshiftSeek);
      GradientDrawable timelineThumb=new GradientDrawable();timelineThumb.setShape(GradientDrawable.OVAL);timelineThumb.setColor(vtheme().color("cobra.cobraProgress.colors.1",0xff41c8ef));timelineThumb.setSize(dp(12),dp(12));mCobraTimeshiftSeek.setThumb(timelineThumb);
      cobraBindTimelineTouch(timeline,mCobraTimeshiftSeek);timeline.addView(mCobraTimeshiftSeek,new FrameLayout.LayoutParams(-1,dp(28),Gravity.CENTER_VERTICAL));
      LinearLayout.LayoutParams timelineLp=new LinearLayout.LayoutParams(-1,dp(28));timelineLp.topMargin=dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.32",8));timelineLp.bottomMargin=dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.33",8));footer.addView(timeline,timelineLp);
    }
'''
    chrome=chrome[:timeline_start]+timeline+chrome[timeline_end:]

    tools_start=chrome.index('    LinearLayout tools=new LinearLayout(this);')
    tools_end=chrome.index('    footer.addView(tools',tools_start)
    tools=r'''    LinearLayout tools=new LinearLayout(this);mCobraTvPlayerTools=tools;
    if(onDemand){
      CobraIconButton display=cobraIcon("aspect","Display",true,v->showCobraAspectPicker());display.caption("Display");display.setTag("cobra_player_aspect_anchor");tools.addView(display,new LinearLayout.LayoutParams(0,dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.34",58)),1));
      CobraIconButton more=cobraIcon("more","More",true,v->showPlayerSettingsDrawer());more.caption("More");more.setTag("cobra_player_options_anchor");tools.addView(more,new LinearLayout.LayoutParams(0,dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.34",58)),1));
    }else{
      String[] glyphs={"guide","aspect","multi","more"},labels={"Channels","Display",mCobraMultiFullscreenActive?"Return Multi":"Multi-View","More"};
      for(int i=0;i<4;i++){final int action=i;CobraIconButton b=cobraIcon(glyphs[i],labels[i],true,v->{if(action==0){if(mCobraMultiFullscreenActive)toast("Return to Multi-View to change screens");else showCobraPlayerDrawer();}else if(action==1)showCobraAspectPicker();else if(action==2){if(mCobraMultiFullscreenActive)cobraReturnToMultiFromFullscreen();else beginMultiView();}else showPlayerSettingsDrawer();});b.caption(labels[i]);b.setTag(action==0?"cobra_tv_player_tool_channels":action==1?"cobra_player_aspect_anchor":action==2?"cobra_tv_player_tool_multi":"cobra_player_options_anchor");tools.addView(b,new LinearLayout.LayoutParams(0,dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.34",58)),1));}
    }
'''
    chrome=chrome[:tools_start]+tools+chrome[tools_end:]
    s=repl(s,'cobraBuildPlayerChrome',chrome)

    drawer=member(s,'showCobraPlayerDrawer')
    drawer=once(drawer,
'''    if(mPlayerOverlay==null||mCobraPlayerLocked||mInPictureInPicture)return;''',
'''    if(mPlayerOverlay==null||mCobraPlayerLocked||mInPictureInPicture||cobraOnDemandPlayer())return;''','block VOD channel drawer')
    s=repl(s,'showCobraPlayerDrawer',drawer)

    settings=member(s,'showPlayerSettingsDrawer')
    settings=once(settings,
'''    rows.addView(cobraSheetRow("record",mRecordingSession.isEmpty()?"Record now":"Stop recording",null,false,true,()->{if(mPlaying!=null)toggleRecording(mPlaying);}));''',
'''    if(!cobraOnDemandPlayer())rows.addView(cobraSheetRow("record",mRecordingSession.isEmpty()?"Record now":"Stop recording",null,false,true,()->{if(mPlaying!=null)toggleRecording(mPlaying);}));''','remove VOD live recording')
    s=repl(s,'showPlayerSettingsDrawer',settings)

    labels=member(s,'cobraRefreshProgrammeLabels')
    old_labels='''    channel=mPlaying;now=cobraCurrentProgram(channel);next=cobraNextProgram(channel);
    cobraTvSetText(mCobraPlayerProgram,now==null?channel==null?"":channel.name:now.title);
    cobraTvSetText(mCobraPlayerSchedule,now==null?cobraGuideStatus(channel):formatTime(now.start)+" – "+formatTime(now.stop)+"   ·   "+Math.max(0,(now.stop-nowMs+59999)/60000)+" min left");
    cobraTvSetText(mCobraPlayerUpcoming,next==null?"":"Next  "+next.title);
    if(mCobraPlayerProgramProgress!=null&&!cobraTimeshiftTimelineAvailable()){int visibility=now==null?View.INVISIBLE:View.VISIBLE;if(mCobraPlayerProgramProgress.getVisibility()!=visibility)mCobraPlayerProgramProgress.setVisibility(visibility);if(now!=null){int p=Math.round(CobraGuideMath.progress(now.start,now.stop,nowMs)*1000);if(mCobraPlayerProgramProgress.getProgress()!=p)mCobraPlayerProgramProgress.setProgress(p);}}'''
    new_labels='''    channel=mPlaying;
    if(cobraOnDemandPlayer()){
      cobraTvSetText(mCobraPlayerProgram,mPlayingVodTitle==null||mPlayingVodTitle.isEmpty()?(channel==null?"":channel.name):mPlayingVodTitle);
      cobraTvSetText(mCobraPlayerSchedule,cobraOnDemandSectionLabel());
      cobraTvSetText(mCobraPlayerUpcoming,"");
      if(mCobraPlayerProgramProgress!=null)mCobraPlayerProgramProgress.setVisibility(View.GONE);
    }else{
      now=cobraCurrentProgram(channel);next=cobraNextProgram(channel);
      cobraTvSetText(mCobraPlayerProgram,now==null?channel==null?"":channel.name:now.title);
      cobraTvSetText(mCobraPlayerSchedule,now==null?cobraGuideStatus(channel):formatTime(now.start)+" – "+formatTime(now.stop)+"   ·   "+Math.max(0,(now.stop-nowMs+59999)/60000)+" min left");
      cobraTvSetText(mCobraPlayerUpcoming,next==null?"":"Next  "+next.title);
      if(mCobraPlayerProgramProgress!=null&&!cobraTimeshiftTimelineAvailable()){int visibility=now==null?View.INVISIBLE:View.VISIBLE;if(mCobraPlayerProgramProgress.getVisibility()!=visibility)mCobraPlayerProgramProgress.setVisibility(visibility);if(now!=null){int p=Math.round(CobraGuideMath.progress(now.start,now.stop,nowMs)*1000);if(mCobraPlayerProgramProgress.getProgress()!=p)mCobraPlayerProgramProgress.setProgress(p);}}
    }'''
    labels=once(labels,old_labels,new_labels,'VOD programme label cleanup')
    s=repl(s,'cobraRefreshProgrammeLabels',labels)

    focus=member(s,'cobraTvPlayerFocusGraph')
    focus=once(focus,
'''    if(code==KeyEvent.KEYCODE_DPAD_DOWN){
      if(header)return cobraTvFocusPlayerTag("cobra_player_play_pause");
      if(transport){if(mCobraTimeshiftSeek!=null&&mCobraTimeshiftSeek.getVisibility()==View.VISIBLE)return mCobraTimeshiftSeek.requestFocus();return cobraTvFocusPlayerTag("cobra_tv_player_tool_channels");}
      if(timeline)return cobraTvFocusPlayerTag("cobra_tv_player_tool_channels");
      if(tools)return true;
    }''',
'''    if(code==KeyEvent.KEYCODE_DPAD_DOWN){
      String lower=cobraOnDemandPlayer()?"cobra_player_aspect_anchor":"cobra_tv_player_tool_channels";
      if(header)return cobraTvFocusPlayerTag("cobra_player_play_pause");
      if(transport){if(mCobraTimeshiftSeek!=null&&mCobraTimeshiftSeek.getVisibility()==View.VISIBLE)return mCobraTimeshiftSeek.requestFocus();return cobraTvFocusPlayerTag(lower);}
      if(timeline)return cobraTvFocusPlayerTag(lower);
      if(tools)return true;
    }''','VOD focus graph')
    s=repl(s,'cobraTvPlayerFocusGraph',focus)

    seek_helper=r'''  private boolean cobraSeekOnDemandBy(long deltaMs){
    if(!cobraOnDemandPlayer()||mPlayer==null)return false;
    try{
      long duration=mPlayer.getDuration(),position=mPlayer.getCurrentPosition();
      if(duration<=0||duration==C.TIME_UNSET||!mPlayer.isCurrentMediaItemSeekable())return true;
      mPlayer.seekTo(Math.max(0L,Math.min(duration,position+deltaMs)));showPlayerChromeTemporarily();return true;
    }catch(RuntimeException ignored){return true;}
  }

'''
    marker='  private boolean cobraTvHandlePlayerKey(KeyEvent event){'
    req(s.count(marker)==1,'player key helper insertion drift')
    s=s.replace(marker,seek_helper+marker,1)

    playerkey=member(s,'cobraTvHandlePlayerKey')
    playerkey=once(playerkey,
'''    if(code==KeyEvent.KEYCODE_MENU){if(mCobraMultiFullscreenActive){cobraReturnToMultiFromFullscreen();return true;}showCobraPlayerDrawer();return true;}
    if(code==KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE){toggleCobraPlayerPlayPause();return true;}
    if(code==KeyEvent.KEYCODE_MEDIA_REWIND){cobraRewindLive(30000L);return true;}
    if(code==KeyEvent.KEYCODE_MEDIA_FAST_FORWARD){if(!cobraTvNudgeTimeline(1))cobraGoLive();return true;}
    if(code==KeyEvent.KEYCODE_CHANNEL_UP&&!mCobraMultiFullscreenActive){stepChannel(1);return true;}
    if(code==KeyEvent.KEYCODE_CHANNEL_DOWN&&!mCobraMultiFullscreenActive){stepChannel(-1);return true;}''',
'''    if(code==KeyEvent.KEYCODE_MENU){if(mCobraMultiFullscreenActive){cobraReturnToMultiFromFullscreen();return true;}if(cobraOnDemandPlayer())showPlayerSettingsDrawer();else showCobraPlayerDrawer();return true;}
    if(code==KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE){toggleCobraPlayerPlayPause();return true;}
    if(code==KeyEvent.KEYCODE_MEDIA_REWIND){if(cobraOnDemandPlayer())return cobraSeekOnDemandBy(-30000L);cobraRewindLive(30000L);return true;}
    if(code==KeyEvent.KEYCODE_MEDIA_FAST_FORWARD){if(cobraOnDemandPlayer())return cobraSeekOnDemandBy(30000L);if(!cobraTvNudgeTimeline(1))cobraGoLive();return true;}
    if(code==KeyEvent.KEYCODE_CHANNEL_UP&&!mCobraMultiFullscreenActive){if(cobraOnDemandPlayer())return true;stepChannel(1);return true;}
    if(code==KeyEvent.KEYCODE_CHANNEL_DOWN&&!mCobraMultiFullscreenActive){if(cobraOnDemandPlayer())return true;stepChannel(-1);return true;}''','VOD remote key cleanup')
    s=repl(s,'cobraTvHandlePlayerKey',playerkey)

    dispatch=member(s,'dispatchKeyEvent')
    dispatch=once(dispatch,
'''    if(event.getAction()==KeyEvent.ACTION_DOWN&&event.getKeyCode()==KeyEvent.KEYCODE_LAST_CHANNEL&&mPlayerOverlay!=null&&!mCobraPlayerLocked){cobraTuneLastChannel();return true;}''',
'''    if(event.getAction()==KeyEvent.ACTION_DOWN&&event.getKeyCode()==KeyEvent.KEYCODE_LAST_CHANNEL&&mPlayerOverlay!=null&&!mCobraPlayerLocked){if(cobraOnDemandPlayer())return true;cobraTuneLastChannel();return true;}''','VOD last-channel key guard')
    s=repl(s,'dispatchKeyEvent',dispatch)

    # Preservation and scope gates.
    for n,h in protected.items():req(hb(member(s,n))==h,'Protected playback/session method changed: '+n)
    req('class CobraTvPlayingDot extends View' in s and 'NORMAL_PULSE_MS=1320L' in s and 'CINEMA_PULSE_MS=1900L' in s,'RC16 dot regressed')
    req('getStringExtra("cobra_start_destination")' in s,'Cobra startup destination receiver missing from Activity')
    req('COBRA_SECTION_OWNER' in s and 'cobraShowLoadedPrimary' in s,'Section owner missing')
    req('cobraOpenLiveTvStartup' in s and 'toggleCobraDrawer()' in member(s,'cobraOpenLiveTvStartup'),'Startup integrated drawer missing')
    req('KEYCODE_DPAD_RIGHT' in member(s,'cobraTvHandleDrawerKey') and 'performClick()' in member(s,'cobraTvHandleDrawerKey'),'Drawer Right=Select missing')
    req('KEYCODE_DPAD_LEFT' in member(s,'cobraDirectory') and 'KEYCODE_DPAD_RIGHT' in member(s,'cobraDirectory'),'Directory Left/Right missing')
    req('cobraRestoreVodLandingReturn()' in member(s,'onBackPressed'),'VOD landing return missing')
    req('cobraAtOwnedVodLanding()' in member(s,'onBackPressed'),'VOD landing lock missing')
    chrome=member(s,'cobraBuildPlayerChrome')
    req('if(onDemand)' in chrome and 'String[] glyphs={"guide","aspect","multi","more"}' in chrome,'Conditional VOD player tools missing')
    req('cobra_tv_player_tool_channels' in chrome and 'cobra_tv_player_tool_multi' in chrome,'Live TV controls accidentally removed globally')
    req('CobraIconButton display=' in chrome and 'CobraIconButton more=' in chrome,'VOD Display/More controls missing')
    req('if(!cobraOnDemandPlayer())rows.addView(cobraSheetRow("record"' in member(s,'showPlayerSettingsDrawer'),'VOD record guard missing')
    req('cobraOnDemandPlayer())return;' in member(s,'showCobraPlayerDrawer'),'VOD Channels drawer guard missing')
    req('mPlayingVodKey' in member(s,'cobraOnDemandPlayer'),'VOD player origin is not explicit')
    req('AMBIENT MODE  •' not in s,'TV Ambient Mode returned')
    req('cobra_movies_search' in s and 'cobra_shows_search' in s,'RC15 dedicated searches lost')
    req('KEYCODE_DPAD_RIGHT&&mCobraTvDrawerInline' in s,'RC15 per-row drawer Right mapping lost')
    path.write_text(s)
    return hb(before),sha(path)

def apply(shell:Path):
    receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text())
    req(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,'Expected exact locked RC16 parent')
    req(receipt.get('tv_grid_pulsing_playing_dot') is True,'RC16 pulsing-dot receipt missing')
    req(receipt.get('tv_right_select_scope')=='live-tv-only','RC16 input scope missing')
    req(receipt.get('tv_movies_dedicated_search') is True and receipt.get('tv_shows_dedicated_search') is True,'RC16 VOD searches missing')
    req(receipt.get('tv_ambient_mode_retired') is True,'TV Ambient retirement missing')
    req(receipt.get('tv_target_abi')=='armeabi-v7a' and receipt.get('mobile_parent_untouched') is True,'Expected isolated ARMv7 TV parent')

    activity=shell/ACT;splash=shell/SPLASH;gradle=shell/(SOURCE+'build.gradle.in')
    for p in (activity,splash,gradle):req(p.is_file(),'Missing '+str(p))
    a0,a1=patch_activity(activity);s0,s1=patch_splash(splash)
    g=gradle.read_text();g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','versionCode')
    g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','versionName');gradle.write_text(g)

    for rel in (ACT,SPLASH,SOURCE+'build.gradle.in'):
        req(rel in receipt['files'],'Receipt missing '+rel);receipt['files'][rel]['after']=sha(shell/rel)
    receipt.update(
      version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,candidate_locked=False,
      physical_device_verified=False,runtime_device_tested=False,tv_variant=True,tv_target_abi='armeabi-v7a',
      chooser_card_settings_removed=True,chooser_infinity_settings_removed=True,chooser_cobra_settings_removed=True,
      chooser_visual_scene_settings_removed=True,chooser_cobra_recovery_gear_removed=True,
      cobra_explicit_start_destination='live_tv',tv_cobra_startup_integrated_shell=True,
      tv_cobra_startup_drawer_open=True,tv_cobra_startup_groups_visible=True,tv_cobra_startup_grid=True,
      tv_drawer_right_select=True,tv_drawer_left_back=True,tv_directory_right_select=True,tv_directory_left_back=True,
      tv_right_select_scope='live-tv-only',tv_left_back_scope='live-tv-drawer-directory-only',
      tv_section_owner_persistent=True,tv_section_owner_values=['LIVE_TV','MOVIES','SHOWS'],
      tv_movies_persistent_until_drawer_change=True,tv_shows_persistent_until_drawer_change=True,
      tv_live_persistent_until_drawer_change=True,tv_smart_return_cannot_override_vod_owner=True,
      tv_vod_player_origin_explicit=True,tv_vod_channels_control_removed=True,tv_vod_multiview_control_removed=True,
      tv_vod_channel_stepping_removed=True,tv_vod_last_channel_removed=True,tv_vod_channel_favorite_removed=True,
      tv_vod_live_rewind_removed=True,tv_vod_go_live_removed=True,tv_vod_live_timeline_removed=True,
      tv_vod_live_record_removed=True,tv_vod_epg_labels_removed=True,tv_vod_display_preserved=True,
      tv_vod_more_preserved=True,tv_vod_audio_subtitles_preserved=True,tv_vod_remote_seek_ms=30000,
      tv_grid_pulsing_playing_dot=True,tv_playing_dot_actual_session=True,tv_playing_dot_frame_ms=33,
      tv_ambient_mode_retired=True,tv_ambient_dynamic_layering=False,tv_glass_system=True,
      tv_movies_dedicated_search=True,tv_shows_dedicated_search=True,
      tv_mini_player_playing_badge_removed=True,tv_navigation_hierarchy='drawer-groups-grid-player',
      tv_back_reverses_hierarchy=True,tv_mini_player_preserved=True,tv_preview_engine_preserved=True,
      tv_multiview_row_focus_visible=True,multiview_two_to_one_session_preserved=True,
      mobile_parent_untouched=True,native_engine_rebuilt=False,playback_engine_unchanged=True
    )
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for name,row in receipt['files'].items():req(sha(shell/name)==row['after'],'Final receipt drift '+name)

    out=Path('audit237');out.mkdir(exist_ok=True)
    (out/'tv-section-owner-source.json').write_text(json.dumps({
      'build':VERSION,'version_name':NEW_NAME,'parent_build':OLD_VERSION,'target_abi':'armeabi-v7a',
      'activity_before_sha256':a0,'activity_after_sha256':a1,'splash_before_sha256':s0,'splash_after_sha256':s1,
      'chooser_settings_removed':['Infinity','Cobra','visual-scene recovery gear'],
      'cobra_startup':'Drawer | Groups | Preview/Details + TV Grid',
      'remote_scope':{'drawer':{'right':'select','left':'back'},'groups':{'right':'select','left':'back'},'epg':'unchanged','movies':'unchanged','shows':'unchanged'},
      'section_owner':['LIVE_TV','MOVIES','SHOWS'],'section_change_owner':'explicit drawer selection only',
      'vod_removed':['Channels','Multi-View','channel stepping','last channel','channel favorite','live rewind','Go Live','live timeline','live recording','EPG programme chrome'],
      'vod_preserved':['play/pause','Display','More','Audio & subtitles','Night Cinema','remote +/-30s media seek'],
      'rc16_pulsing_dot_preserved':True,'ambient_mode_retired':True,'playback_engine_unchanged':True,
      'native_engine_rebuilt':False,'mobile_fold_untouched':True,'physical_device_verified':False
    },indent=2,sort_keys=True)+'\n')
    print('PASS: 2103237 RC17 section ownership/startup/VOD player cleanup applied over exact locked RC16')

def main():
    p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);a=p.parse_args();apply(a.shell)
if __name__=='__main__':main()
