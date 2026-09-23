#!/usr/bin/env python3
"""2103226 onn. 4K Pro lightweight persistent-Live-TV pass.

Parent: exact locked 2103225 Handoff/Focus RC8 source.

TV-only goals:
- Live TV becomes one persistent player surface with lightweight overlays.
- Back from playback opens channel browsing instead of rebuilding/reattaching a guide preview surface.
- The initial TV browser does not run a second preview decoder.
- Channel Groups and player channel filters use a reusable 20K-channel index.
- Opening TV overlays never resizes the fullscreen TextureView.
- The top-level drawer remains available but no longer shifts/scales the whole TV stage.
- Fixed-TV orientation / phone-style transition work is suppressed.

No ARM64 phone/Fold changes and no native-engine rebuild.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

VERSION=2103226
OLD_VERSION=2103225
OLD_NAME='1.0.9-Cobra-Onn4KPro-TV-Handoff-Focus-RC8'
NEW_NAME='1.0.9-Cobra-Onn4KPro-TV-Lightweight-Live-RC9'
SOURCE='tools/android/packaging/xbmc/'
ACT=SOURCE+'src/InfinityLiveActivity.java.in'

def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha(path): return sha_bytes(Path(path).read_bytes())
def req(v,m):
    if not v: raise RuntimeError(m)
def once(text,old,new,label):
    req(text.count(old)==1,f'{label}: expected 1 anchor, got {text.count(old)}')
    return text.replace(old,new,1)

def span(text:str,name:str,kind='method'):
    if kind=='ctor':
        pat=re.compile(r'(?m)^\s*'+re.escape(name)+r'\s*\([^;\n]*\)\s*\{')
    else:
        pat=re.compile(r'(?m)^\s*(?:@Override\s+)?(?:(?:public|private|protected|static|final|synchronized)\s+)*[\w.<>,\[\]?]+\s+'+re.escape(name)+r'\s*\([^\n{;]*\)\s*\{')
    ms=list(pat.finditer(text)); req(len(ms)==1,f'{kind} cardinality {name}={len(ms)}')
    start=ms[0].start();brace=text.find('{',ms[0].start());depth=0;quote=None;esc=line=block=False;i=brace
    while i<len(text):
        c=text[i];n=text[i+1] if i+1<len(text) else ''
        if line:
            if c=='\n':line=False
        elif block:
            if c=='*' and n=='/':block=False;i+=1
        elif quote:
            if esc:esc=False
            elif c=='\\':esc=True
            elif c==quote:quote=None
        elif c=='/' and n=='/':line=True;i+=1
        elif c=='/' and n=='*':block=True;i+=1
        elif c in ('"',"'"):quote=c
        elif c=='{':depth+=1
        elif c=='}':
            depth-=1
            if depth==0:return start,i+1
        i+=1
    raise RuntimeError('unclosed '+name)

def member(text,name,kind='method'):
    a,b=span(text,name,kind);return text[a:b]
def replace_member(text,name,new,kind='method'):
    a,b=span(text,name,kind);return text[:a]+new.rstrip()+text[b:]

LIGHTWEIGHT_HELPERS=r'''  private static final String COBRA_TV_LIGHTWEIGHT_LIVE_BUILD="cobra_tv_lightweight_live_2103226";
  private int mCobraTvLibraryIndexSize=-1;
  private String mCobraTvLibraryIndexFirst="",mCobraTvLibraryIndexLast="";
  private boolean mCobraTvDirectRevealPending=false;
  private final java.util.HashMap<String,Channel> mCobraTvChannelById=new java.util.HashMap<>();
  private final java.util.HashMap<String,Integer> mCobraTvChannelPositionById=new java.util.HashMap<>();
  private final java.util.HashMap<String,java.util.ArrayList<Channel>> mCobraTvFilterIndex=new java.util.HashMap<>();
  private final java.util.HashMap<String,java.util.TreeMap<String,Integer>> mCobraTvGroupCountIndex=new java.util.HashMap<>();

  private String cobraTvSourceIndexKey(String source){
    return source==null||source.isEmpty()?"*":source;
  }

  private String cobraTvFilterIndexKey(String source,String filter){
    return cobraTvSourceIndexKey(source)+"\u0001"+(filter==null?"ALL":filter);
  }

  private void cobraTvInvalidateLibraryIndex(){
    mCobraTvLibraryIndexSize=-1;mCobraTvLibraryIndexFirst="";mCobraTvLibraryIndexLast="";
    mCobraTvChannelById.clear();mCobraTvChannelPositionById.clear();mCobraTvFilterIndex.clear();mCobraTvGroupCountIndex.clear();
  }

  private void cobraTvIndexChannel(String source,String filter,Channel channel){
    String key=cobraTvFilterIndexKey(source,filter);java.util.ArrayList<Channel> rows=mCobraTvFilterIndex.get(key);
    if(rows==null){rows=new java.util.ArrayList<>();mCobraTvFilterIndex.put(key,rows);}rows.add(channel);
  }

  private void cobraTvIndexGroupCount(String source,String group){
    String key=cobraTvSourceIndexKey(source);java.util.TreeMap<String,Integer> groups=mCobraTvGroupCountIndex.get(key);
    if(groups==null){groups=new java.util.TreeMap<>(String.CASE_INSENSITIVE_ORDER);mCobraTvGroupCountIndex.put(key,groups);}
    Integer count=groups.get(group);groups.put(group,count==null?1:count+1);
  }

  private void cobraTvEnsureLibraryIndex(){
    int size=mChannels==null?0:mChannels.size();
    String first=size>0&&mChannels.get(0)!=null&&mChannels.get(0).id!=null?mChannels.get(0).id:"";
    String last=size>0&&mChannels.get(size-1)!=null&&mChannels.get(size-1).id!=null?mChannels.get(size-1).id:"";
    if(size==mCobraTvLibraryIndexSize&&first.equals(mCobraTvLibraryIndexFirst)&&last.equals(mCobraTvLibraryIndexLast))return;
    cobraTvInvalidateLibraryIndex();mCobraTvLibraryIndexSize=size;mCobraTvLibraryIndexFirst=first;mCobraTvLibraryIndexLast=last;
    for(int i=0;i<size;i++){
      Channel channel=mChannels.get(i);if(channel==null||channel.id==null)continue;
      mCobraTvChannelById.put(channel.id,channel);mCobraTvChannelPositionById.put(channel.id,i);
      String source=sourceIdForChannel(channel);
      if(!mFeatures.sourceEnabled(source)||!cobraChannelAllowed(channel))continue;
      cobraTvIndexChannel("","ALL",channel);if(source!=null&&!source.isEmpty())cobraTvIndexChannel(source,"ALL",channel);
      String group=cobraNormalizeProviderGroup(channel.group);
      if(group!=null&&!group.isEmpty()&&!mFeatures.looksAdult(group)){
        cobraTvIndexChannel("",group,channel);cobraTvIndexGroupCount("",group);
        if(source!=null&&!source.isEmpty()){cobraTvIndexChannel(source,group,channel);cobraTvIndexGroupCount(source,group);}
      }
    }
  }

  private boolean cobraTvIndexedSourceMatches(Channel channel,String source){
    return channel!=null&&(source==null||source.isEmpty()||source.equals(sourceIdForChannel(channel)))&&cobraChannelAllowed(channel);
  }

  private java.util.List<Channel> cobraTvIndexedChannels(String source,String filter){
    cobraTvEnsureLibraryIndex();String resolved=filter==null?"ALL":filter;
    if(resolved.startsWith("GROUP:"))resolved=resolved.substring(6);
    if(resolved.startsWith("MY:")||!mSearch.trim().isEmpty())return null;
    if("RECENT".equals(resolved)){
      java.util.ArrayList<Channel> out=new java.util.ArrayList<>();
      for(String id:mRecents){Channel c=mCobraTvChannelById.get(id);if(cobraTvIndexedSourceMatches(c,source))out.add(c);}return out;
    }
    if("FAVORITES".equals(resolved)){
      java.util.ArrayList<Channel> out=new java.util.ArrayList<>();
      for(String id:mFavorites){Channel c=mCobraTvChannelById.get(id);if(cobraTvIndexedSourceMatches(c,source))out.add(c);}
      java.util.Collections.sort(out,(a,b)->Integer.compare(mCobraTvChannelPositionById.get(a.id),mCobraTvChannelPositionById.get(b.id)));return out;
    }
    java.util.ArrayList<Channel> rows=mCobraTvFilterIndex.get(cobraTvFilterIndexKey(source,resolved));
    return rows==null?java.util.Collections.emptyList():rows;
  }

  private java.util.TreeMap<String,Integer> cobraTvIndexedGroups(String source){
    cobraTvEnsureLibraryIndex();java.util.TreeMap<String,Integer> groups=mCobraTvGroupCountIndex.get(cobraTvSourceIndexKey(source));
    return groups==null?new java.util.TreeMap<>(String.CASE_INSENSITIVE_ORDER):groups;
  }

  private int cobraTvIndexedPosition(Channel channel){
    cobraTvEnsureLibraryIndex();if(channel==null||channel.id==null)return -1;Integer position=mCobraTvChannelPositionById.get(channel.id);return position==null?mChannels.indexOf(channel):position;
  }

'''

def patch_activity(path:Path):
    before=path.read_bytes();s=before.decode()
    marker='  private static final String COBRA_TV_HANDOFF_FOCUS_BUILD="cobra_tv_handoff_focus_2103225";'
    req(s.count(marker)==1,'2103225 handoff marker missing')
    s=s.replace(marker,LIGHTWEIGHT_HELPERS+marker,1)

    # The top-level drawer stays available, but TV no longer shifts/scales the whole stage.
    drawer=member(s,'toggleCobraDrawer')
    drawer=once(drawer,
      'panel.setTranslationX(-width);panel.setAlpha(.90f);panel.setScaleX(.99f);panel.setScaleY(.99f);panel.animate().translationX(0).alpha(1f).scaleX(1f).scaleY(1f).setDuration(vtheme().motion("cobra.toggleCobraDrawer.numbers.1",90)).setInterpolator(new android.view.animation.DecelerateInterpolator()).start();animateCobraDrawerShift(Math.min(width,screen*.28f));',
      'panel.setTranslationX(-width);panel.setAlpha(1f);panel.setScaleX(1f);panel.setScaleY(1f);panel.animate().translationX(0).setDuration(70L).setInterpolator(new android.view.animation.DecelerateInterpolator()).start();mCobraDrawerShifted=false;',
      'lightweight drawer animation')
    s=replace_member(s,'toggleCobraDrawer',drawer)

    s=replace_member(s,'closeCobraExperienceDrawer',r'''  private boolean closeCobraExperienceDrawer() {
    FrameLayout decor=(FrameLayout)getWindow().getDecorView();View old=decor.findViewWithTag("cobra_experience_drawer");
    boolean hadDrawer=old!=null||mCobraDrawerShifted;if(old!=null)decor.removeView(old);mCobraDrawerShifted=false;
    return hadDrawer;
  }''')

    destination=member(s,'cobraDrawerDestination')
    destination=once(destination,
      '      if(!settingsDestination)cobraDiscardVodLandingReturn();\n      action.run();',
      '      if(!settingsDestination)cobraDiscardVodLandingReturn();\n      if(!"TV".equalsIgnoreCase(destination)&&mPlayerOverlay!=null)closePlayer();\n      action.run();',
      'leave persistent Live TV only for TV destination')
    s=replace_member(s,'cobraDrawerDestination',destination)

    # TV entry: drawer disappears; the first screen is just the channel/guide browser.
    s=replace_member(s,'cobraOpenLiveTv',r'''  private void cobraOpenLiveTv(){
    closeCobraExperienceDrawer();
    if(mPlayerOverlay!=null&&mPlaying!=null){showCobraPlayerDrawer();return;}
    mCobraGuideRoute="channels";mCobraModeGroupsExpanded=true;mCobraGuideStyle="grid";mCobraPreviewAutoplayAllowed=false;
    stopCobraPreviewPlayerOnly();if(mCobraGuideShell!=null)mCobraGuideShell.setVisibility(View.VISIBLE);cobraShowGuideShell();
    if(mCobraGuideShell!=null)mCobraGuideShell.postDelayed(this::cobraTvEnsureLibraryIndex,80L);
  }''')

    # Keep the existing guide data/rows but remove the second preview decoder from the 32-bit TV path.
    guide=member(s,'cobraShowGuideShell')
    guide=once(guide,
      '    if(mGuidePreviewChannel==null)ensureCobraPreviewSelection(new ArrayList<>(mChannels));\n    if(mCobraPreviewAutoplayAllowed&&mCobraPreviewPlayer==null&&mPlayer==null&&mMultiOverlay==null&&mGuidePreviewChannel!=null)startCobraPreview(mGuidePreviewChannel);',
      '    stopCobraPreviewPlayerOnly();if(mGuidePreviewChannel==null&&!mChannels.isEmpty())mGuidePreviewChannel=mChannels.get(0);cobraTvEnsureLibraryIndex();',
      'disable TV guide preview decoder')
    guide=once(guide,
      '    cobraRestyleGuide();cobraLayoutGuide();cobraRenderGuideBrowser();',
      '    mCobraGuideShell.setVisibility(View.VISIBLE);cobraRestyleGuide();cobraLayoutGuide();cobraRenderGuideBrowser();',
      'show lightweight guide shell')
    s=replace_member(s,'cobraShowGuideShell',guide)

    # A TV browser is channel choices, not a phone dashboard. Keep toolbar + virtualized guide only.
    s=replace_member(s,'cobraLayoutGuide',r'''  private void cobraLayoutGuide(){
    if(mCobraGuideShell==null||mCobraTvGuideLayoutBusy)return;int w=mCobraGuideShell.getWidth(),h=mCobraGuideShell.getHeight();if(w<=0||h<=0)return;
    mCobraTvGuideLayoutBusy=true;
    try{
      mCobraLastGuideWidth=w;mCobraLastGuideHeight=h;float density=Math.max(.01f,getResources().getDisplayMetrics().density);
      mCobraModeLayout=CobraModeLayout.solve("grid",Math.max(1,Math.round(w/density)),Math.max(1,Math.round(h/density)),getResources().getConfiguration().fontScale,false);
      int toolbar=Math.min(h,dp(64));
      View[] hidden={mCobraModeRail,mCobraGuideDirectory,mCobraGuideVideo,mCobraGuideDetails,mCobraModeFooter};
      for(View view:hidden)if(view!=null&&view.getVisibility()!=View.GONE)view.setVisibility(View.GONE);
      if(mCobraModeToolbar!=null){if(mCobraModeToolbar.getVisibility()!=View.VISIBLE)mCobraModeToolbar.setVisibility(View.VISIBLE);cobraTvPositionIfChanged(mCobraModeToolbar,0,0,w,toolbar);}
      if(mCobraGuideBrowser!=null){if(mCobraGuideBrowser.getVisibility()!=View.VISIBLE)mCobraGuideBrowser.setVisibility(View.VISIBLE);cobraTvPositionIfChanged(mCobraGuideBrowser,0,toolbar,w,Math.max(1,h-toolbar));}
    }finally{mCobraTvGuideLayoutBusy=false;}
  }''')

    s=replace_member(s,'cobraRenderGuideBrowser',r'''  private void cobraRenderGuideBrowser(){
    if(mCobraGuideBrowser==null||mCobraModeLayout==null)return;
    cobraRememberModeScroll();mCobraGuideBrowser.removeAllViews();mCobraGuideAdapter=null;mCobraGuideList=null;mCobraGuideRuler=null;mCobraModeDate=null;
    mCobraListStateKey="grid|channels|"+mCobraGuideSource+"|"+mCategory+"|"+mSearch+"|"+mCobraFocusSchedule;
    if(mCobraGuideDirectory!=null)mCobraGuideDirectory.removeAllViews();
    ArrayList<Channel> channels=cobraGuideChannels();cobraRenderGridMode(mCobraGuideBrowser,channels);
    mCobraRenderedMode="grid";cobraRestoreModeScroll();cobraRefreshModeDetails();vtheme().tree(mCobraGuideBrowser,"guide.browser");
  }''')

    s=replace_member(s,'cobraGuideChannels',r'''  private ArrayList<Channel> cobraGuideChannels() {
    java.util.List<Channel> indexed=cobraTvIndexedChannels(mCobraGuideSource,mCategory);
    if(indexed!=null)return new ArrayList<>(indexed);
    ArrayList<Channel> out=new ArrayList<>();for(Channel c:cobraChannelsForCurrentView())if(mCobraGuideSource.isEmpty()||mCobraGuideSource.equals(sourceIdForChannel(c)))out.add(c);return out;
  }''')

    # Channel Groups no longer re-count the full 20K-channel library on every button press.
    s=replace_member(s,'cobraDirectory',r'''  private void cobraDirectory(LinearLayout parent,boolean sources){
    ArrayList<String> names=new ArrayList<>(),values=new ArrayList<>(),counts=new ArrayList<>();
    if(sources){
      names.add("All playlists");values.add("");counts.add("");
      for(LiveSource source:mSources)if(mFeatures.sourceEnabled(source.id)){names.add(source.name);values.add(source.id);counts.add("Playlist");}
    }else{
      cobraTvEnsureLibraryIndex();java.util.TreeMap<String,Integer> groups=cobraTvIndexedGroups(mCobraGuideSource);
      java.util.List<Channel> allRows=cobraTvIndexedChannels(mCobraGuideSource,"ALL");int all=allRows==null?0:allRows.size();
      int favorites=0;for(String id:mFavorites){Channel c=mCobraTvChannelById.get(id);if(cobraTvIndexedSourceMatches(c,mCobraGuideSource))favorites++;}
      int recent=0;for(String id:mRecents){Channel c=mCobraTvChannelById.get(id);if(cobraTvIndexedSourceMatches(c,mCobraGuideSource))recent++;}
      Collections.addAll(names,"Favorites","Recently played","All channels");Collections.addAll(values,"FAVORITES","RECENT","ALL");Collections.addAll(counts,""+favorites,""+recent,""+all);
      for(Map.Entry<String,Integer> entry:groups.entrySet()){names.add(entry.getKey());values.add(entry.getKey());counts.add(""+entry.getValue());}
      for(String group:cobraCustomGroups()){names.add(group);values.add("MY:"+group);counts.add("My group");}
    }
    if(!sources){Button playlist=cobraTextButton(cobraModeSourceName()+"  ▾",cobraModeDark(),()->cobraOpenTvDirectory(true));playlist.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);playlist.setPadding(dp(14),0,dp(10),0);playlist.setSingleLine(true);parent.addView(playlist,new LinearLayout.LayoutParams(-1,dp(58)));}
    android.widget.ListView list=new android.widget.ListView(this);list.setDividerHeight(0);list.setSelector(android.R.color.transparent);list.setFastScrollEnabled(false);list.setItemsCanFocus(true);list.setFocusable(true);list.setFocusableInTouchMode(false);
    list.setAdapter(new android.widget.BaseAdapter(){public int getCount(){return names.size();}public Object getItem(int p){return values.get(p);}public long getItemId(int p){return CobraModeLayout.stableId(values.get(p));}public boolean hasStableIds(){return true;}
      public View getView(int position,View recycled,android.view.ViewGroup host){
        CobraDirectoryRow row=recycled instanceof CobraDirectoryRow?(CobraDirectoryRow)recycled:new CobraDirectoryRow();String value=values.get(position);
        row.bind(names.get(position),counts.get(position),value.equals(sources?mCobraGuideSource:mCategory));
        row.setOnClickListener(v->{cobraRememberModeScroll();if(sources){mCobraGuideSource=value;mCategory="ALL";mSearch="";if("tv-directory".equals(mCobraSheetKind))closeCobraActionSheet();mCobraGuideRoute="channels";cobraRenderGuideBrowser();}else selectCobraCategory(value);});return row;
      }});
    parent.addView(list,new LinearLayout.LayoutParams(-1,0,1));final String current=sources?mCobraGuideSource:mCategory;final int index=Math.max(0,values.indexOf(current));list.setSelection(index);
    list.post(()->{if(list.getAdapter()==null||list.getAdapter().getCount()==0)return;list.setSelection(index);list.post(()->{int childIndex=index-list.getFirstVisiblePosition();View row=childIndex>=0&&childIndex<list.getChildCount()?list.getChildAt(childIndex):null;if(row!=null&&row.isShown())row.requestFocus();else list.requestFocus();});});
  }''')

    s=replace_member(s,'selectCobraCategory',r'''  private void selectCobraCategory(String value){
    if("tv-directory".equals(mCobraSheetKind))closeCobraActionSheet();cobraRememberModeScroll();mCategory=value;mSearch="";mCobraGuideRoute="channels";mCobraInspectedChannel=null;mCobraInspectedProgram=null;
    if(mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow()){cobraRenderGuideBrowser();if(mCobraGuideBrowser!=null)mCobraGuideBrowser.post(this::cobraTvFocusGuideBody);}
    else cobraShowGuideShell();
  }''')

    directory=member(s,'cobraOpenTvDirectory')
    directory=once(directory,'panel.setTranslationX(-position.width);panel.animate().translationX(0f).setDuration(70L).start();',
      'panel.setTranslationX(-dp(10));panel.setAlpha(.96f);panel.animate().translationX(0f).alpha(1f).setDuration(55L).start();',
      'lightweight group panel motion')
    s=replace_member(s,'cobraOpenTvDirectory',directory)

    # First tune keeps the already visible channel browser underneath until video truly renders.
    s=replace_member(s,'playChannel',r'''  private void playChannel(Channel channel) {
    if(channel==null||!isCobraAsyncAlive())return;
    stopCobraPreviewPlayerOnly();releaseMulti();
    mPlaying=channel;mPlayingIndex=cobraTvIndexedPosition(channel);mTriedFallback=false;mPlayingVodKey="";mPendingResumeMs=0L;
    if(mPlayerOverlay!=null){startSinglePlayer(channel.primaryUrl);cobraBuildPlayerChrome();showPlayerChromeTemporarily();cobraTvFocusPlayerPrimary();return;}
    mCobraTvDirectRevealPending=true;mCobraTvOpeningSurfaceHandoff=true;openPlayerOverlay(channel);startSinglePlayer(channel.primaryUrl);
  }''')

    s=replace_member(s,'cobraStartDirectSinglePlayer',r'''  private void cobraStartDirectSinglePlayer(Channel channel,String url,String reason,boolean requested){
    if(channel==null||mPlaying==null||!channel.id.equals(mPlaying.id)||mPlayerTexture==null)return;
    try{
      mPlayer=buildPlayer(mPlayerTexture,channel,true);
      if(mCobraTvDirectRevealPending){
        final ExoPlayer reveal=mPlayer;final TextureView texture=mPlayerTexture;final FrameLayout overlay=mPlayerOverlay;mCobraTvDirectRevealPending=false;
        reveal.addListener(new androidx.media3.common.Player.Listener(){
          @Override public void onRenderedFirstFrame(){
            reveal.removeListener(this);if(reveal!=mPlayer||texture!=mPlayerTexture)return;
            texture.setAlpha(1f);texture.setOpaque(true);if(overlay==mPlayerOverlay)overlay.setBackgroundColor(Color.BLACK);
            if(mCobraGuideShell!=null)mCobraGuideShell.setVisibility(View.GONE);showPlayerChromeTemporarily();cobraTvFocusPlayerPrimary();
          }
          @Override public void onPlayerError(androidx.media3.common.PlaybackException error){
            reveal.removeListener(this);if(reveal==mPlayer){mCobraTvDirectRevealPending=true;if(overlay==mPlayerOverlay)overlay.setBackgroundColor(Color.TRANSPARENT);if(texture==mPlayerTexture)texture.setAlpha(0f);}
          }
        });
      }
      mPlayer.setMediaItem(mediaItem(url));cobraPrepareObserved(mPlayer,"fullscreen-direct:"+reason);if(requested)startCobraPlayer(mPlayer);else mPlayer.pause();
      cobraStartPresentationTicker();cobraRequestShortEpg(channel);InfinityCobraDiagnostics.record(this,"playback","direct",reason);
      if(cobraChannelRewindEnabled(channel)&&cobraLiveChannel(channel)&&!cobraShouldUseLocalTimeshift(channel,url))cobraSetTimeshiftUiState("UNSUPPORTED","direct stream");
    }catch(Exception error){
      mCobraTvDirectRevealPending=false;releaseSinglePlayer();if(mPlayerOverlay!=null)mPlayerOverlay.setBackgroundColor(Color.TRANSPARENT);if(mPlayerTexture!=null)mPlayerTexture.setAlpha(0f);
      showError("Playback failed","Could not start this stream. "+error.getClass().getSimpleName());
    }
    cobraUpdatePlaybackLabels();
  }''')

    # Back/header now opens a lightweight channel overlay over the still-running player.
    s=replace_member(s,'closeFullscreenToCobraView',r'''  private void closeFullscreenToCobraView() {
    if(mCobraMultiFullscreenActive){cobraReturnToMultiFromFullscreen();return;}
    if(mCobraPlayerLocked){showCobraPlayerUnlockAffordance();return;}
    closeCobraActionSheet();closeCobraMultiPicker(true);if(mCobraPlayerDrawer==null)showCobraPlayerDrawer();else cobraTvFocusPlayerDrawerTarget();
  }''')

    chrome=member(s,'cobraBuildPlayerChrome')
    chrome=chrome.replace('cobraIcon("back",mCobraMultiFullscreenActive?"Return to Multi-View":"Return to preview",true,v->closeFullscreenToCobraView())',
                          'cobraIcon("back",mCobraMultiFullscreenActive?"Return to Multi-View":"Browse channels",true,v->closeFullscreenToCobraView())')
    req('Browse channels' in chrome,'player header browse label patch failed')
    s=replace_member(s,'cobraBuildPlayerChrome',chrome)

    # Player overlays sit on top of video. Never resize the TextureView just to show navigation.
    s=replace_member(s,'cobraLayoutPlayerPanels',r'''  private void cobraLayoutPlayerPanels() {
    FrameLayout root=mMultiOverlay!=null?mMultiOverlay:mPlayerOverlay;if(root==null)return;int w=root.getWidth(),h=root.getHeight();if(w<=0||h<=0)return;
    if(mMultiOverlay!=null){
      View panel=mCobraMultiPicker;boolean portrait=h>w;int pw=panel==null?0:portrait?w:Math.min(dp(430),(int)(w*.43f));int ph=panel==null?0:portrait?(int)(h*.56f):h;
      if(panel!=null)cobraPosition(panel,portrait?0:w-pw,portrait?h-ph:0,pw,ph);
      if(mCobraMultiCanvas!=null)cobraPosition(mCobraMultiCanvas,0,0,w,h);return;
    }
    if(mPlayerTexture!=null){cobraPosition(mPlayerTexture,0,0,w,h);mPlayerTexture.post(()->applyCobraAspectTransform());}
    if(mCobraPlayerDrawer!=null){
      int ph=Math.max(dp(240),Math.min((int)(h*.46f),dp(420)));ph=Math.min(ph,Math.max(1,h-dp(24)));cobraPosition(mCobraPlayerDrawer,0,h-ph,w,ph);
    }
    if(mCobraMultiPicker!=null){
      int pw=Math.min(dp(430),Math.max(dp(320),(int)(w*.40f)));cobraPosition(mCobraMultiPicker,w-pw,0,pw,h);
    }
  }''')

    player_drawer=member(s,'showCobraPlayerDrawer')
    player_drawer=once(player_drawer,
      'mPlayerOverlay.addView(panel,new FrameLayout.LayoutParams(1,1));mPlayerChrome.setVisibility(View.GONE);cobraRenderPlayerDrawer(mCobraDrawerFilter);cobraLayoutPlayerPanels();panel.post(()->{if(panel==mCobraPlayerDrawer&&panel.isAttachedToWindow())cobraAnimatePanelIn(panel,!isPortrait());});vtheme().tree(content,"player.channels");cobraRefreshVisualEffects();',
      'mPlayerOverlay.addView(panel,new FrameLayout.LayoutParams(1,1));mPlayerChrome.setVisibility(View.GONE);cobraRenderPlayerDrawer(mCobraDrawerFilter);cobraLayoutPlayerPanels();panel.post(()->{if(panel==mCobraPlayerDrawer&&panel.isAttachedToWindow()){panel.setAlpha(.97f);panel.setTranslationY(dp(10));panel.animate().alpha(1f).translationY(0f).setDuration(65L).start();cobraTvFocusPlayerDrawerTarget();}});vtheme().tree(content,"player.channels");',
      'lightweight player channel overlay')
    player_drawer=player_drawer.replace('vtheme().copy("cobra.showCobraPlayerDrawer.copy.1","Live TV")','vtheme().copy("cobra.showCobraPlayerDrawer.copy.1","Channels")')
    s=replace_member(s,'showCobraPlayerDrawer',player_drawer)

    # Cached list/filter ownership removes full-library scans from the player overlay.
    s=replace_member(s,'cobraRenderPlayerDrawer',r'''  private void cobraRenderPlayerDrawer(String filter) {
    if(mCobraPlayerDrawerList==null)return;mCobraDrawerFilter=filter;final boolean groups="CATEGORIES".equals(filter);cobraTvEnsureLibraryIndex();
    final ArrayList<String> names=new ArrayList<>();final java.util.List<Channel> channels;
    if(groups){names.addAll(cobraTvIndexedGroups(mCobraGuideSource).keySet());channels=java.util.Collections.emptyList();}
    else {java.util.List<Channel> indexed=cobraTvIndexedChannels(mCobraGuideSource,filter);channels=indexed==null?java.util.Collections.emptyList():indexed;}
    mCobraPlayerDrawerList.setAdapter(new android.widget.BaseAdapter(){public int getCount(){return groups?names.size():channels.size();}public Object getItem(int p){return groups?names.get(p):channels.get(p);}public long getItemId(int p){return groups?CobraModeLayout.stableId(names.get(p)):p;}
      public View getView(int p,View recycled,android.view.ViewGroup parent){Button row=recycled instanceof Button?(Button)recycled:cobraTextButton("",true,()->{});row.setTextSize(vtheme().number("cobra.cobraRenderPlayerDrawer.numbers.1",13,8f,96f));row.setPadding(dp(14),0,dp(12),0);row.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);row.setMaxLines(3);row.setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,dp(groups?52:82)));
        if(groups){String group=names.get(p);row.setText(group);row.setSelected(mPlaying!=null&&group.equals(cobraNormalizeProviderGroup(mPlaying.group)));row.setOnClickListener(v->cobraRenderPlayerDrawer("GROUP:"+group));row.setOnLongClickListener(null);}
        else {Channel c=channels.get(p);GuideProgram now=cobraCurrentProgram(c),next=cobraNextProgram(c);row.setText(c.name+"\n"+(now==null?cobraGuideStatus(c):"Now  "+now.title)+(next==null?"":"\nNext  "+next.title));row.setSelected(mPlaying!=null&&mPlaying.id.equals(c.id));row.setOnClickListener(v->{if(mPlaying!=null&&mPlaying.id.equals(c.id)){closeCobraPlayerDrawer();showPlayerChromeTemporarily();cobraTvFocusPlayerPrimary();return;}mPlaying=c;mPlayingIndex=cobraTvIndexedPosition(c);mPlayingVodKey="";mPendingResumeMs=0;startSinglePlayer(c.primaryUrl);closeCobraPlayerDrawer();cobraBuildPlayerChrome();showPlayerChromeTemporarily();cobraTvFocusPlayerPrimary();});row.setOnLongClickListener(v->{cobraShowQuickPeek(c,v);return true;});}
        return row;}});
    mCobraPlayerDrawerList.setAlpha(1f);mCobraPlayerDrawerList.setTranslationY(0f);mCobraPlayerDrawerList.post(this::cobraTvFocusPlayerDrawerTarget);
  }''')

    # MENU owns the top-level transient drawer; Back owns channel browsing.
    player_key=member(s,'cobraTvHandlePlayerKey')
    player_key=once(player_key,
      '    if(code==KeyEvent.KEYCODE_MENU){if(mCobraMultiFullscreenActive){cobraReturnToMultiFromFullscreen();return true;}showCobraPlayerDrawer();return true;}',
      '    if(code==KeyEvent.KEYCODE_MENU){if(mCobraMultiFullscreenActive){cobraReturnToMultiFromFullscreen();return true;}toggleCobraDrawer();return true;}',
      'TV player MENU top-level drawer')
    player_key=once(player_key,
      '    if(code==KeyEvent.KEYCODE_BACK){if(mPlayerChrome!=null&&mPlayerChrome.getVisibility()==View.VISIBLE){cobraTvHidePlayerChrome();return true;}return false;}',
      '    if(code==KeyEvent.KEYCODE_BACK){if(mPlayerChrome!=null&&mPlayerChrome.getVisibility()==View.VISIBLE){cobraTvHidePlayerChrome();return true;}showCobraPlayerDrawer();return true;}',
      'TV player Back channel overlay')
    s=replace_member(s,'cobraTvHandlePlayerKey',player_key)

    # Fixed TV: never hand orientation eligibility back to phone/Fold rotation policy.
    s=replace_member(s,'cobraRequestPlayerOrientation',r'''  private void cobraRequestPlayerOrientation(int requested,String reason){
    if(mDeviceBridge!=null)mDeviceBridge.setPlayerRotationEligible(false,"tv-fixed");
  }''')
    s=replace_member(s,'cobraUpdatePlayerRotationButton',r'''  private void cobraUpdatePlayerRotationButton(){
    if(mCobraPlayerRotationButton!=null)mCobraPlayerRotationButton.setVisibility(View.GONE);
  }''')

    # Invalidate the channel index exactly when library contents change.
    apply_load=member(s,'applyLoadResult')
    apply_load=once(apply_load,'    mChannels.addAll(result.channels);','    mChannels.addAll(result.channels);cobraTvInvalidateLibraryIndex();','load result index invalidation')
    s=replace_member(s,'applyLoadResult',apply_load)

    warm=member(s,'cobraTvInstallWarmLibrary')
    warm=once(warm,'    mChannels.clear();mChannels.addAll(restored);','    mChannels.clear();mChannels.addAll(restored);cobraTvInvalidateLibraryIndex();','warm library index invalidation')
    s=replace_member(s,'cobraTvInstallWarmLibrary',warm)

    all_sources=member(s,'loadAllEnabledSources')
    all_sources=once(all_sources,'        boolean hadVisible=!mChannels.isEmpty();mChannels.clear();mChannels.addAll(resolved);',
      '        boolean hadVisible=!mChannels.isEmpty();mChannels.clear();mChannels.addAll(resolved);cobraTvInvalidateLibraryIndex();',
      'source refresh index invalidation')
    s=replace_member(s,'loadAllEnabledSources',all_sources)

    # Source-level safety gates.
    req('COBRA_TV_LIGHTWEIGHT_LIVE_BUILD="cobra_tv_lightweight_live_2103226"' in s,'RC9 marker missing')
    req('startCobraPreview(mGuidePreviewChannel)' not in member(s,'cobraShowGuideShell'),'TV guide preview decoder remains')
    req('cobraDirectory(mCobraGuideDirectory' not in member(s,'cobraRenderGuideBrowser'),'Hidden directory still rebuilt')
    req('cobraTvIndexedGroups(mCobraGuideSource)' in member(s,'cobraDirectory'),'Channel Groups cache missing')
    req('showCobraPlayerDrawer();return true;' in member(s,'cobraTvHandlePlayerKey'),'Persistent player Back contract missing')
    req('toggleCobraDrawer();return true;' in member(s,'cobraTvHandlePlayerKey'),'Player MENU drawer contract missing')
    req('cobraPosition(mPlayerTexture,0,0,w,h)' in member(s,'cobraLayoutPlayerPanels'),'Player surface still resizes for overlays')
    req('onRenderedFirstFrame' in member(s,'cobraStartDirectSinglePlayer'),'Cold tune first-frame reveal missing')
    req('mCobraGuideShell.setVisibility(View.GONE)' in member(s,'cobraStartDirectSinglePlayer'),'Guide not suspended after video reveal')
    req('cobraTvInvalidateLibraryIndex()' in member(s,'loadAllEnabledSources'),'Library cache invalidation missing')
    path.write_text(s)
    return sha_bytes(before),sha(path)

def apply(shell:Path):
    receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text())
    req(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,'Expected exact locked 2103225 RC8 parent')
    req(receipt.get('tv_variant') is True and receipt.get('tv_target_abi')=='armeabi-v7a','Expected ARMv7 TV parent')
    req(receipt.get('tv_handoff_first_render') is True and receipt.get('tv_multiview_row_focus_visible') is True,'Expected RC8 handoff/focus parent')
    req(receipt.get('tv_native_remote_architecture') is True and receipt.get('tv_hardening') is True,'Expected protected TV architecture parent')

    activity=shell/ACT;gradle=shell/(SOURCE+'build.gradle.in')
    for p in (activity,gradle):req(p.is_file(),'Missing '+str(p))
    activity_before,activity_after=patch_activity(activity)
    g=gradle.read_text();g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','versionCode')
    g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','versionName');gradle.write_text(g)

    for rel in (ACT,SOURCE+'build.gradle.in'):
      req(rel in receipt['files'],'Receipt missing '+rel);receipt['files'][rel]['after']=sha(shell/rel)
    receipt.update(
      version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,candidate_locked=False,
      physical_device_verified=False,runtime_device_tested=False,tv_variant=True,tv_target_abi='armeabi-v7a',
      tv_lightweight_live_architecture=True,tv_persistent_player_surface=True,tv_player_back_opens_channels=True,
      tv_channel_drawer_bottom_overlay=True,tv_player_surface_not_resized_by_overlays=True,
      tv_guide_preview_decoder_disabled=True,tv_channel_library_index_cached=True,tv_channel_group_counts_cached=True,
      tv_drawer_stage_shift_disabled=True,tv_fixed_orientation_policy=True,
      tv_handoff_first_render=True,tv_multiview_row_focus_visible=True,tv_player_footer_unclipped=True,
      multiview_two_to_one_session_preserved=True,multiview_survivor_player_recreated=False,
      mobile_parent_untouched=True,native_engine_rebuilt=False,playback_engine_unchanged=True
    )
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for name,row in receipt['files'].items():req(sha(shell/name)==row['after'],'Final receipt drift '+name)

    Path('audit226').mkdir(exist_ok=True)
    Path('audit226/tv-lightweight-live-source.json').write_text(json.dumps({
      'build':VERSION,'version_name':NEW_NAME,'parent_build':OLD_VERSION,'target_abi':'armeabi-v7a',
      'activity_before_sha256':activity_before,'activity_after_sha256':activity_after,
      'marker':'cobra_tv_lightweight_live_2103226','mobile_fold_untouched':True,
      'persistent_live_player_surface':True,'back_opens_channel_overlay':True,
      'player_drawer_bottom_overlay':True,'player_surface_resized_for_overlays':False,
      'guide_preview_decoder_enabled':False,'channel_library_index_cached':True,'channel_group_counts_cached':True,
      'drawer_stage_shift_enabled':False,'fixed_tv_orientation':True,
      'native_engine_rebuilt':False,'playback_engine_unchanged':True,'physical_device_verified':False
    },indent=2,sort_keys=True)+'\n')
    print('PASS: 2103226 lightweight persistent Live TV applied over exact locked 2103225 RC8')

def main():
    p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);a=p.parse_args();apply(a.shell)
if __name__=='__main__':main()
