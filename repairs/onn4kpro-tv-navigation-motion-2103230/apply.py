#!/usr/bin/env python3
"""2103230: preservation-first onn. TV navigation hierarchy + lightweight motion.

Parent: exact locked 2103225 RC8.

Contract:
- Preserve RC8 mini player / preview player, EPG, fullscreen player, Multi-View and playback engine.
- Drawer -> Groups -> Full Grid -> Player.
- Back reverses exactly one level: Player -> Grid -> Groups -> Drawer.
- Group chooser is a real left-side guide state, not a modal player channel drawer.
- Selecting a group collapses the group chooser and expands the existing RC8 guide.
- Use short translation/alpha motion only; no per-frame layout animator.
- Cache expensive 20K-channel group counts between library/source/profile changes.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

VERSION=2103230
OLD_VERSION=2103225
OLD_NAME='1.0.9-Cobra-Onn4KPro-TV-Handoff-Focus-RC8'
NEW_NAME='1.0.9-Cobra-Onn4KPro-TV-Navigation-Motion-RC10'
SOURCE='tools/android/packaging/xbmc/'
ACT=SOURCE+'src/InfinityLiveActivity.java.in'

def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha(path): return sha_bytes(Path(path).read_bytes())
def req(v,m):
    if not v: raise RuntimeError(m)
def once(text,old,new,label):
    req(text.count(old)==1,f'{label}: expected 1 anchor, got {text.count(old)}')
    return text.replace(old,new,1)

def span(text:str,name:str):
    pat=re.compile(r'(?m)^\s*(?:@Override\s+)?(?:(?:public|private|protected|static|final|synchronized)\s+)*[\w.<>,\[\]?]+\s+'+re.escape(name)+r'\s*\([^\n{;]*\)\s*\{')
    ms=list(pat.finditer(text)); req(len(ms)==1,f'method cardinality {name}={len(ms)}')
    start=ms[0].start(); brace=text.find('{',start); depth=0; quote=None; esc=line=block=False; i=brace
    while i<len(text):
        c=text[i]; n=text[i+1] if i+1<len(text) else ''
        if line:
            if c=='\n': line=False
        elif block:
            if c=='*' and n=='/': block=False; i+=1
        elif quote:
            if esc: esc=False
            elif c=='\\': esc=True
            elif c==quote: quote=None
        elif c=='/' and n=='/': line=True; i+=1
        elif c=='/' and n=='*': block=True; i+=1
        elif c in ('"',"'"): quote=c
        elif c=='{': depth+=1
        elif c=='}':
            depth-=1
            if depth==0:return start,i+1
        i+=1
    raise RuntimeError('unclosed '+name)

def member(text,name):
    a,b=span(text,name); return text[a:b]
def replace_member(text,name,new):
    a,b=span(text,name); return text[:a]+new.rstrip()+text[b:]

HELPERS=r'''  private static final String COBRA_TV_NAVIGATION_MOTION_BUILD="cobra_tv_navigation_motion_2103230";
  private int mCobraTvChannelRevision=0;
  private int mCobraTvGroupCacheRevision=-1;
  private String mCobraTvGroupCacheSource="",mCobraTvGroupCacheProfile="";
  private int mCobraTvGroupCacheAll=0;
  private final java.util.TreeMap<String,Integer> mCobraTvGroupCacheGroups=new java.util.TreeMap<>(String.CASE_INSENSITIVE_ORDER);
  private final java.util.HashSet<String> mCobraTvGroupCacheAllowedIds=new java.util.HashSet<>();

  private void cobraTvInvalidateGroupCache(){
    mCobraTvChannelRevision++;mCobraTvGroupCacheRevision=-1;mCobraTvGroupCacheSource="";mCobraTvGroupCacheProfile="";
    mCobraTvGroupCacheAll=0;mCobraTvGroupCacheGroups.clear();mCobraTvGroupCacheAllowedIds.clear();
  }

  private void cobraTvEnsureGroupCache(){
    if(!isCobraAsyncAlive())return;
    String source=mCobraGuideSource==null?"":mCobraGuideSource;
    String profile=mFeatures.activeProfileId()==null?"":mFeatures.activeProfileId();
    if(mCobraTvGroupCacheRevision==mCobraTvChannelRevision&&source.equals(mCobraTvGroupCacheSource)&&profile.equals(mCobraTvGroupCacheProfile))return;
    mCobraTvGroupCacheGroups.clear();mCobraTvGroupCacheAllowedIds.clear();mCobraTvGroupCacheAll=0;
    for(Channel channel:mChannels){
      if(channel==null||(!source.isEmpty()&&!source.equals(sourceIdForChannel(channel)))||!mFeatures.sourceEnabled(sourceIdForChannel(channel)))continue;
      String providerGroup=cobraNormalizeProviderGroup(channel.group);
      if(!cobraChannelAllowed(channel))continue;
      mCobraTvGroupCacheAllowedIds.add(channel.id);mCobraTvGroupCacheAll++;
      if(!providerGroup.isEmpty()&&!mFeatures.looksAdult(providerGroup)){
        Integer count=mCobraTvGroupCacheGroups.get(providerGroup);mCobraTvGroupCacheGroups.put(providerGroup,count==null?1:count+1);
      }
    }
    mCobraTvGroupCacheSource=source;mCobraTvGroupCacheProfile=profile;mCobraTvGroupCacheRevision=mCobraTvChannelRevision;
  }

  private int cobraTvGroupPanelWidth(int width){
    return Math.max(dp(260),Math.min(dp(360),Math.round(width*.29f)));
  }

  private void cobraTvAnimateGuideContentIn(int direction){
    int delta=dp(direction>=0?14:-14);
    View[] views={mCobraGuideVideo,mCobraGuideDetails,mCobraGuideBrowser};
    for(View view:views){
      if(view==null||!view.isShown())continue;
      view.animate().cancel();view.setTranslationX(delta);view.setAlpha(.96f);
      view.animate().translationX(0f).alpha(1f).setDuration(120L).setInterpolator(new android.view.animation.DecelerateInterpolator()).start();
    }
  }

  private void cobraTvAnimateGroupPanelIn(){
    if(mCobraGuideDirectory==null||!mCobraGuideDirectory.isShown())return;
    mCobraGuideDirectory.animate().cancel();mCobraGuideDirectory.setTranslationX(-Math.max(dp(80),mCobraGuideDirectory.getWidth()));mCobraGuideDirectory.setAlpha(.94f);
    mCobraGuideDirectory.animate().translationX(0f).alpha(1f).setDuration(130L).setInterpolator(new android.view.animation.DecelerateInterpolator()).start();
    cobraTvAnimateGuideContentIn(1);
  }

  private void cobraTvShowGroupChooser(boolean animate){
    if(mCobraGuideShell==null||!mCobraGuideShell.isAttachedToWindow()){mCobraModeGroupsExpanded=true;cobraShowGuideShell();}
    else {mCobraModeGroupsExpanded=true;cobraLayoutGuide();cobraRenderGuideBrowser();cobraLayoutGuide();}
    if(animate&&mCobraGuideDirectory!=null)mCobraGuideDirectory.post(this::cobraTvAnimateGroupPanelIn);
  }

  private void cobraTvCommitGroupSelection(String value){
    cobraRememberModeScroll();mCategory=value;mSearch="";mCobraGuideRoute="channels";mCobraInspectedChannel=null;mCobraInspectedProgram=null;mCobraModeGroupsExpanded=false;
    cobraLayoutGuide();cobraRenderGuideBrowser();cobraLayoutGuide();cobraTvAnimateGuideContentIn(-1);
    if(mCobraGuideBrowser!=null)mCobraGuideBrowser.postDelayed(this::cobraTvFocusGuideBody,90L);
  }

  private void cobraTvSelectGroup(String value){
    if(mCobraGuideDirectory!=null&&mCobraModeGroupsExpanded&&mCobraGuideDirectory.isShown()){
      mCobraGuideDirectory.animate().cancel();
      mCobraGuideDirectory.animate().translationX(-Math.max(dp(80),mCobraGuideDirectory.getWidth())).alpha(.90f).setDuration(100L)
        .setInterpolator(new android.view.animation.AccelerateInterpolator()).withEndAction(()->{
          if(mCobraGuideDirectory!=null){mCobraGuideDirectory.setTranslationX(0f);mCobraGuideDirectory.setAlpha(1f);}
          cobraTvCommitGroupSelection(value);
        }).start();
      return;
    }
    cobraTvCommitGroupSelection(value);
  }

'''

def patch_activity(path:Path):
    before=path.read_bytes();s=before.decode()
    marker='  private static final String COBRA_TV_HANDOFF_FOCUS_BUILD="cobra_tv_handoff_focus_2103225";'
    req(s.count(marker)==1,'Exact RC8 handoff marker missing')
    s=s.replace(marker,HELPERS+marker,1)

    # TV entry: drawer selection reveals group choices first, while preserving RC8 guide/mini-player.
    s=replace_member(s,'cobraOpenLiveTv',r'''  private void cobraOpenLiveTv(){
    mCobraGuideRoute="channels";mCobraModeGroupsExpanded=true;
    if("mobile".equals(mCobraGuideStyle))mCobraGuideStyle="grid";
    cobraShowGuideShell();
    if(mCobraGuideShell!=null)mCobraGuideShell.post(this::cobraTvAnimateGroupPanelIn);
  }''')

    # The group chooser becomes a real left-side guide state. The RC8 mini-player/details/grid
    # are only translated/resized once at state boundaries; no ValueAnimator/layout loop.
    s=replace_member(s,'cobraLayoutGuide',r'''  private void cobraLayoutGuide(){
    if(mCobraGuideShell==null||mCobraTvGuideLayoutBusy)return;int w=mCobraGuideShell.getWidth(),h=mCobraGuideShell.getHeight();if(w<=0||h<=0)return;
    mCobraTvGuideLayoutBusy=true;
    try{
      mCobraLastGuideWidth=w;mCobraLastGuideHeight=h;float density=Math.max(.01f,getResources().getDisplayMetrics().density);
      mCobraModeLayout=CobraModeLayout.solve("grid",Math.max(1,Math.round(w/density)),Math.max(1,Math.round(h/density)),getResources().getConfiguration().fontScale,false);
      int[][] boxes={mCobraModeLayout.toolbar,mCobraModeLayout.rail,mCobraModeLayout.directory,mCobraModeLayout.video,mCobraModeLayout.details,mCobraModeLayout.browser,mCobraModeLayout.footer};
      View[] views={mCobraModeToolbar,mCobraModeRail,mCobraGuideDirectory,mCobraGuideVideo,mCobraGuideDetails,mCobraGuideBrowser,mCobraModeFooter};
      int groupW=mCobraModeGroupsExpanded?Math.min(w-dp(220),cobraTvGroupPanelWidth(w)):0;
      int toolbarBottom=Math.max(0,Math.min(h,Math.round((mCobraModeLayout.toolbar[1]+mCobraModeLayout.toolbar[3])*density)));
      float contentScale=groupW>0?Math.max(.10f,(w-groupW)/(float)Math.max(1,w)):1f;
      for(int i=0;i<boxes.length;i++){
        View view=views[i];if(view==null)continue;
        if(i==2){
          if(groupW<=0){if(view.getVisibility()!=View.GONE)view.setVisibility(View.GONE);continue;}
          if(view.getVisibility()!=View.VISIBLE)view.setVisibility(View.VISIBLE);
          cobraTvPositionIfChanged(view,0,toolbarBottom,groupW,Math.max(1,h-toolbarBottom));continue;
        }
        int[] r=boxes[i];int x=Math.max(0,Math.min(w,Math.round(r[0]*density))),y=Math.max(0,Math.min(h,Math.round(r[1]*density)));
        int rw=Math.max(0,Math.min(w-x,Math.round(r[2]*density))),rh=Math.max(0,Math.min(h-y,Math.round(r[3]*density)));
        if(groupW>0&&(i==3||i==4||i==5||i==6)){x=groupW+Math.round(x*contentScale);rw=Math.max(0,Math.min(w-x,Math.round(rw*contentScale)));}
        if(rw<=0||rh<=0){if(view.getVisibility()!=View.GONE)view.setVisibility(View.GONE);continue;}
        if(view.getVisibility()!=View.VISIBLE)view.setVisibility(View.VISIBLE);cobraTvPositionIfChanged(view,x,y,rw,rh);
      }
    }finally{mCobraTvGuideLayoutBusy=false;}
  }''')

    s=replace_member(s,'cobraRenderGuideBrowser',r'''  private void cobraRenderGuideBrowser(){
    if(mCobraGuideBrowser==null||mCobraModeLayout==null)return;
    cobraRememberModeScroll();mCobraGuideBrowser.removeAllViews();mCobraGuideAdapter=null;mCobraGuideList=null;mCobraGuideRuler=null;mCobraModeDate=null;
    mCobraListStateKey=mCobraGuideStyle+"|"+mCobraGuideRoute+"|"+mCobraGuideSource+"|"+mCategory+"|"+mSearch+"|"+mCobraFocusSchedule;
    mCobraGuideDirectory.removeAllViews();
    boolean rail="grid".equals(mCobraGuideStyle)&&mCobraModeGroupsExpanded;
    if(rail){
      TextView label=cobraText("CHANNELS",cobraModeColor("muted"),11);label.setPadding(dp(14),0,0,0);mCobraGuideDirectory.addView(label,new LinearLayout.LayoutParams(-1,dp(32)));
      cobraDirectory(mCobraGuideDirectory,false);
    }
    if(!"grid".equals(mCobraGuideStyle)&&!rail&&!"channels".equals(mCobraGuideRoute)){
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
    mCobraRenderedMode="grid";
    cobraRestoreModeScroll();cobraRefreshModeDetails();vtheme().tree(mCobraGuideBrowser,"guide.browser");
  }''')

    s=replace_member(s,'cobraToggleModeGroups',r'''  private void cobraToggleModeGroups(){
    cobraRememberModeScroll();cobraTvShowGroupChooser(true);
  }''')

    # Group-count cache: build once per library/source/profile revision instead of rescanning
    # ~20K channels whenever the user opens the group level.
    s=replace_member(s,'cobraDirectory',r'''  private void cobraDirectory(LinearLayout parent,boolean sources){
    ArrayList<String> names=new ArrayList<>(),values=new ArrayList<>(),counts=new ArrayList<>();
    if(sources){names.add("All playlists");values.add("");counts.add("");for(LiveSource source:mSources)if(mFeatures.sourceEnabled(source.id)){names.add(source.name);values.add(source.id);counts.add("Playlist");}}
    else{
      cobraTvEnsureGroupCache();int favorites=0,recent=0;
      for(String id:mFavorites)if(mCobraTvGroupCacheAllowedIds.contains(id))favorites++;
      for(String id:mRecents)if(mCobraTvGroupCacheAllowedIds.contains(id))recent++;
      Collections.addAll(names,"Favorites","Recently played","All channels");Collections.addAll(values,"FAVORITES","RECENT","ALL");Collections.addAll(counts,""+favorites,""+recent,""+mCobraTvGroupCacheAll);
      for(Map.Entry<String,Integer> entry:mCobraTvGroupCacheGroups.entrySet()){names.add(entry.getKey());values.add(entry.getKey());counts.add(""+entry.getValue());}
      for(String group:cobraCustomGroups()){names.add(group);values.add("MY:"+group);counts.add("My group");}
    }
    if(!sources){Button playlist=cobraTextButton(cobraModeSourceName()+"  ▾",cobraModeDark(),()->cobraOpenTvDirectory(true));playlist.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);playlist.setPadding(dp(14),0,dp(10),0);playlist.setSingleLine(true);parent.addView(playlist,new LinearLayout.LayoutParams(-1,dp(58)));}
    android.widget.ListView list=new android.widget.ListView(this);list.setDividerHeight(0);list.setSelector(android.R.color.transparent);list.setFastScrollEnabled(false);list.setItemsCanFocus(true);list.setFocusable(true);list.setFocusableInTouchMode(false);
    list.setAdapter(new android.widget.BaseAdapter(){public int getCount(){return names.size();}public Object getItem(int p){return values.get(p);}public long getItemId(int p){return CobraModeLayout.stableId(values.get(p));}public boolean hasStableIds(){return true;}
      public View getView(int position,View recycled,android.view.ViewGroup host){
        CobraDirectoryRow row=recycled instanceof CobraDirectoryRow?(CobraDirectoryRow)recycled:new CobraDirectoryRow();String value=values.get(position);
        row.bind(names.get(position),counts.get(position),value.equals(sources?mCobraGuideSource:mCategory));
        row.setOnClickListener(v->{cobraRememberModeScroll();if(sources){mCobraGuideSource=value;mCategory="ALL";mSearch="";if("tv-directory".equals(mCobraSheetKind))closeCobraActionSheet();mCobraGuideRoute="channels";cobraTvInvalidateGroupCache();cobraRenderGuideBrowser();}else selectCobraCategory(value);});return row;
      }});
    parent.addView(list,new LinearLayout.LayoutParams(-1,0,1));
    final String current=sources?mCobraGuideSource:mCategory;final int index=Math.max(0,values.indexOf(current));
    list.setSelection(index);
    list.post(()->{if(list.getAdapter()==null||list.getAdapter().getCount()==0)return;list.setSelection(index);list.post(()->{int childIndex=index-list.getFirstVisiblePosition();View row=childIndex>=0&&childIndex<list.getChildCount()?list.getChildAt(childIndex):null;if(row!=null&&row.isShown())row.requestFocus();else list.requestFocus();});});
  }''')

    # "Groups" is no longer a modal on TV. Playlist/source selection remains a modal.
    old_open=member(s,'cobraOpenTvDirectory')
    req('private void cobraOpenTvDirectory(boolean sources)' in old_open,'TV directory method missing')
    body=old_open.replace('  private void cobraOpenTvDirectory(boolean sources){',
      '  private void cobraOpenTvDirectory(boolean sources){\n    if(!sources){cobraTvShowGroupChooser(true);return;}',
      1)
    s=replace_member(s,'cobraOpenTvDirectory',body)

    s=replace_member(s,'selectCobraCategory',r'''  private void selectCobraCategory(String value){
    if("tv-directory".equals(mCobraSheetKind))closeCobraActionSheet();
    cobraTvSelectGroup(value);
  }''')

    # Keep RC8 mini-player creation exactly; just warm the group cache after the guide becomes idle.
    show=member(s,'cobraShowGuideShell')
    anchor='    for(LiveSource source:mSources)if(mFeatures.sourceEnabled(source.id))loadGuideAsync(source);'
    req(show.count(anchor)==1,'Guide-shell load anchor missing')
    show=show.replace(anchor,anchor+'\n    if(mCobraGuideShell!=null)mCobraGuideShell.postDelayed(this::cobraTvEnsureGroupCache,120L);',1)
    s=replace_member(s,'cobraShowGuideShell',show)

    # Library changes invalidate/prewarm the group index. No change to load/provider behavior.
    apply_load=member(s,'applyLoadResult')
    apply_load=once(apply_load,'    mChannels.addAll(result.channels);','    mChannels.addAll(result.channels);cobraTvInvalidateGroupCache();mMain.postDelayed(this::cobraTvEnsureGroupCache,120L);','applyLoadResult cache invalidation')
    s=replace_member(s,'applyLoadResult',apply_load)

    warm=member(s,'cobraTvInstallWarmLibrary')
    warm=once(warm,'    mChannels.clear();mChannels.addAll(restored);String active=',
      '    mChannels.clear();mChannels.addAll(restored);cobraTvInvalidateGroupCache();mMain.postDelayed(this::cobraTvEnsureGroupCache,120L);String active=',
      'warm cache invalidation')
    s=replace_member(s,'cobraTvInstallWarmLibrary',warm)

    load=member(s,'loadAllEnabledSources')
    load=once(load,'        boolean hadVisible=!mChannels.isEmpty();mChannels.clear();mChannels.addAll(resolved);',
      '        boolean hadVisible=!mChannels.isEmpty();mChannels.clear();mChannels.addAll(resolved);cobraTvInvalidateGroupCache();mMain.postDelayed(this::cobraTvEnsureGroupCache,120L);',
      'source refresh cache invalidation')
    s=replace_member(s,'loadAllEnabledSources',load)

    # Physical Back in fullscreen is navigation, not "hide chrome". It returns to the full guide.
    player_key=member(s,'cobraTvHandlePlayerKey')
    player_key=once(player_key,
      '    if(code==KeyEvent.KEYCODE_BACK){if(mPlayerChrome!=null&&mPlayerChrome.getVisibility()==View.VISIBLE){cobraTvHidePlayerChrome();return true;}return false;}',
      '    if(code==KeyEvent.KEYCODE_BACK){closeFullscreenToCobraView();return true;}',
      'player Back hierarchy')
    s=replace_member(s,'cobraTvHandlePlayerKey',player_key)

    # Player header arrow follows the same hierarchy; Channels remains an independent control.
    chrome=member(s,'cobraBuildPlayerChrome')
    chrome=chrome.replace('mCobraMultiFullscreenActive?"Return to Multi-View":"Return to preview"',
                          'mCobraMultiFullscreenActive?"Return to Multi-View":"Back to guide"',1)
    req('"Back to guide"' in chrome,'Header Back label patch failed')
    s=replace_member(s,'cobraBuildPlayerChrome',chrome)

    # Fullscreen always returns to the full-grid level. Preserve RC8 session/mini-player handoff.
    close_full=member(s,'closeFullscreenToCobraView')
    anchor='  private void closeFullscreenToCobraView() {\n    if(mCobraMultiFullscreenActive)'
    req(close_full.startswith(anchor),'Fullscreen return anchor drift')
    close_full=close_full.replace(anchor,
      '  private void closeFullscreenToCobraView() {\n    if(mCobraMultiFullscreenActive)',1)
    close_full=once(close_full,
      '    Channel channel=mPlaying;ExoPlayer session=mPlayer;closeCobraActionSheet();closeCobraPlayerDrawer();closeCobraMultiPicker(true);clearCobraPlayerLockState(false);',
      '    mCobraModeGroupsExpanded=false;Channel channel=mPlaying;ExoPlayer session=mPlayer;closeCobraActionSheet();closeCobraPlayerDrawer();closeCobraMultiPicker(true);clearCobraPlayerLockState(false);',
      'fullscreen return to grid level')
    s=replace_member(s,'closeFullscreenToCobraView',close_full)

    # Reverse hierarchy:
    # full grid -> groups, groups -> drawer. Search/source transient states unwind first.
    s=replace_member(s,'onBackPressed',r'''  @Override public void onBackPressed() {
    if(mCobraPlayerLocked&&mPlayerOverlay!=null){showCobraPlayerUnlockAffordance();return;}
    if(closeCobraActionSheet())return;
    if(mCobraMultiPicker!=null){closeCobraMultiPicker(false);return;}
    if(mCobraPlayerDrawer!=null){if(mCobraDrawerFilter.startsWith("GROUP:")){cobraRenderPlayerDrawer("CATEGORIES");return;}closeCobraPlayerDrawer();return;}
    if(closeCobraPowerMenu()||closeCobraViewModeMenu()||closeCobraChannelActions()||closeCobraExperienceDrawer())return;
    if(mCobraMultiFullscreenActive&&mPlayerOverlay!=null){cobraReturnToMultiFromFullscreen();return;}
    if(mPlayerOverlay!=null){closeFullscreenToCobraView();return;}
    if(mMultiOverlay!=null){releaseMulti();return;}
    if(!"root".equals(mCobraInternalScreen)){showCobraPrimaryView();return;}
    if(cobraRestoreVodLandingReturn())return;
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

    # Small fade on the already-safe RC8 surface swap: new preview has rendered before old
    # fullscreen frame fades. This is purely presentation; session ownership is unchanged.
    s=replace_member(s,'cobraTvRemoveOverlayAfterSurface',r'''  private void cobraTvRemoveOverlayAfterSurface(FrameLayout overlay,Runnable after){
    if(overlay==null){if(after!=null)after.run();return;}
    overlay.animate().cancel();
    overlay.animate().alpha(0f).setDuration(90L).setInterpolator(new android.view.animation.DecelerateInterpolator()).withEndAction(()->{
      if(overlay.getParent() instanceof android.view.ViewGroup)((android.view.ViewGroup)overlay.getParent()).removeView(overlay);
      overlay.setAlpha(1f);if(after!=null)after.run();
    }).start();
  }''')

    # Source-level gates: mini player and preview engine must remain, while new hierarchy is explicit.
    req('startCobraPreview(mGuidePreviewChannel)' in member(s,'cobraShowGuideShell'),'RC8 mini-player autoplay path was removed')
    req('mCobraPreviewPlayer=session' in member(s,'closeFullscreenToCobraView'),'RC8 fullscreen->mini session handoff was removed')
    req('showCobraPlayerDrawer()' in member(s,'cobraBuildPlayerChrome'),'Player Channels control was removed')
    req('cobraTvShowGroupChooser(true)' in member(s,'onBackPressed'),'Grid -> Groups Back hierarchy missing')
    req('toggleCobraDrawer();return;' in member(s,'onBackPressed'),'Groups -> Drawer Back hierarchy missing')
    req('closeFullscreenToCobraView();return true;' in member(s,'cobraTvHandlePlayerKey'),'Player -> Grid Back hierarchy missing')
    req('cobraTvEnsureGroupCache()' in member(s,'cobraDirectory'),'Group count cache missing')
    req('mCobraModeGroupsExpanded=false;Channel channel=mPlaying' in member(s,'closeFullscreenToCobraView'),'Fullscreen must return to full grid')
    req('COBRA_TV_NAVIGATION_MOTION_BUILD="cobra_tv_navigation_motion_2103230"' in s,'RC10 marker missing')
    path.write_text(s)
    return sha_bytes(before),sha(path)

def apply(shell:Path):
    receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text())
    req(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,'Expected exact locked 2103225 RC8 parent')
    req(receipt.get('tv_variant') is True and receipt.get('tv_target_abi')=='armeabi-v7a','Expected ARMv7 TV parent')
    req(receipt.get('tv_handoff_first_render') is True and receipt.get('tv_multiview_row_focus_visible') is True,'Expected RC8 handoff/focus parent')
    req(receipt.get('tv_player_footer_unclipped') is True and receipt.get('multiview_two_to_one_session_preserved') is True,'Expected RC8 player/Multi-View parent')

    activity=shell/ACT;gradle=shell/(SOURCE+'build.gradle.in')
    for p in (activity,gradle):req(p.is_file(),'Missing '+str(p))
    before,after=patch_activity(activity)
    g=gradle.read_text();g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','versionCode')
    g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','versionName');gradle.write_text(g)

    for rel in (ACT,SOURCE+'build.gradle.in'):
      req(rel in receipt['files'],'Receipt missing '+rel);receipt['files'][rel]['after']=sha(shell/rel)
    receipt.update(
      version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,candidate_locked=False,
      physical_device_verified=False,runtime_device_tested=False,tv_variant=True,tv_target_abi='armeabi-v7a',
      tv_navigation_hierarchy='drawer-groups-grid-player',tv_back_reverses_hierarchy=True,
      tv_group_chooser_persistent=True,tv_group_selection_expands_grid=True,
      tv_mini_player_preserved=True,tv_preview_engine_preserved=True,tv_player_channels_control_preserved=True,
      tv_group_counts_cached=True,tv_motion_translation_alpha_only=True,tv_motion_layout_animator=False,
      tv_surface_exit_fade_ms=90,tv_handoff_first_render=True,tv_multiview_row_focus_visible=True,
      tv_player_footer_unclipped=True,multiview_two_to_one_session_preserved=True,
      multiview_survivor_player_recreated=False,mobile_parent_untouched=True,
      native_engine_rebuilt=False,playback_engine_unchanged=True
    )
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for name,row in receipt['files'].items():req(sha(shell/name)==row['after'],'Final receipt drift '+name)

    Path('audit230').mkdir(exist_ok=True)
    Path('audit230/tv-navigation-motion-source.json').write_text(json.dumps({
      'build':VERSION,'version_name':NEW_NAME,'parent_build':OLD_VERSION,'target_abi':'armeabi-v7a',
      'activity_before_sha256':before,'activity_after_sha256':after,
      'marker':'cobra_tv_navigation_motion_2103230','navigation':['drawer','groups','grid','player'],
      'back_reverses_one_level':True,'mini_player_preserved':True,'preview_engine_preserved':True,
      'player_channels_control_preserved':True,'group_counts_cached':True,
      'motion':['translation','alpha'],'per_frame_layout_animation':False,'surface_exit_fade_ms':90,
      'native_engine_rebuilt':False,'playback_engine_unchanged':True,'mobile_fold_untouched':True,
      'physical_device_verified':False
    },indent=2,sort_keys=True)+'\n')
    print('PASS: 2103230 TV navigation/motion applied over exact locked 2103225 RC8')

def main():
    p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);a=p.parse_args();apply(a.shell)
if __name__=='__main__':main()
