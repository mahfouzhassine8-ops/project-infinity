#!/usr/bin/env python3
"""2103235 RC15 — final TV refinement over exact locked RC14.

Preservation-first scope:
- Compact/rebalance Cobra drawer branding; keep it on one line.
- Remove normal PLAYING/PAUSED state from mini-player badge; EPG row remains authoritative.
- D-pad Right = Select ONLY inside Live TV inline drawer and Live TV directory/group/playlist rows.
  Movies, TV Shows and EPG directional navigation are not remapped.
- Add dedicated Movies Search and TV Shows Search inside their own landing UIs.
- Reuse in-session VOD catalogs briefly for faster Movies/Shows re-entry.
- Remove redundant guide layout passes and tighten presentation work.
- Preserve RC14 hierarchy, glass UI, preview/fullscreen handoff, playback/timeshift,
  Multi-View, providers, ARMv7 native engine, permanent signing and mobile isolation.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

VERSION=2103235
OLD_VERSION=2103234
OLD_NAME='1.0.9-Cobra-Onn4KPro-TV-Integrated-Shell-Playing-RC14'
NEW_NAME='1.0.9-Cobra-Onn4KPro-TV-Final-Polish-RC15'
SOURCE='tools/android/packaging/xbmc/'
ACT=SOURCE+'src/InfinityLiveActivity.java.in'

def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def sha(path):return sha_bytes(Path(path).read_bytes())
def req(v,m):
    if not v:raise RuntimeError(m)
def once(text,old,new,label):
    req(text.count(old)==1,f'{label}: expected 1 anchor, got {text.count(old)}')
    return text.replace(old,new,1)
def span(text,name):
    pat=re.compile(r'(?m)^\s*(?:@Override\s+)?(?:(?:public|private|protected|static|final|synchronized)\s+)*[\w.<>,\[\]?]+\s+'+re.escape(name)+r'\s*\([^\n{;]*\)\s*\{')
    ms=list(pat.finditer(text));req(len(ms)==1,f'method cardinality {name}={len(ms)}')
    st=ms[0].start();b=text.find('{',st);d=0;q=None;esc=line=block=False
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
def member(text,name):
    a,b=span(text,name);return text[a:b]
def repl(text,name,new):
    a,b=span(text,name);return text[:a]+new.rstrip()+text[b:]

def patch_activity(path:Path):
    before=path.read_bytes();s=before.decode()
    req('COBRA_TV_INTEGRATED_SHELL_BUILD="cobra_tv_integrated_shell_playing_2103234"' in s,'Exact locked RC14 parent marker missing')

    s=once(s,
'''  private final ArrayList<VodItem> mCobraVodMoviesCatalog = new ArrayList<>();
  private final ArrayList<VodItem> mCobraVodShowsCatalog = new ArrayList<>();''',
'''  private final ArrayList<VodItem> mCobraVodMoviesCatalog = new ArrayList<>();
  private final ArrayList<VodItem> mCobraVodShowsCatalog = new ArrayList<>();
  private long mCobraVodMoviesLoadedAt=0L;
  private long mCobraVodShowsLoadedAt=0L;
  private static final long COBRA_TV_VOD_CACHE_MS=5L*60L*1000L;
  private static final String COBRA_TV_FINAL_POLISH_BUILD="cobra_tv_final_polish_2103235";''',
'RC15 VOD cache fields')

    # Compact drawer brand: one-line COBRA, smaller mark/back, tighter vertical band.
    s=repl(s,'cobraBrandHeader',r'''  private View cobraBrandHeader(){
    LinearLayout header=new LinearLayout(this);header.setGravity(Gravity.CENTER_VERTICAL);header.setPadding(0,dp(2),0,dp(6));
    LinearLayout copy=new LinearLayout(this);copy.setOrientation(LinearLayout.VERTICAL);
    TextView title=cobraText(vtheme().copy("cobra.cobraBrandHeader.copy.1","COBRA"),cobraModeColor("text"),16);
    title.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));title.setLetterSpacing(.10f);title.setSingleLine(true);title.setMaxLines(1);
    copy.addView(title,new LinearLayout.LayoutParams(-1,dp(24)));
    TextView sub=cobraText(vtheme().copy("cobra.cobraBrandHeader.copy.2","An Infinity experience"),cobraModeColor("muted"),9);
    sub.setSingleLine(true);sub.setMaxLines(1);sub.setEllipsize(android.text.TextUtils.TruncateAt.END);copy.addView(sub,new LinearLayout.LayoutParams(-1,dp(18)));
    LinearLayout.LayoutParams body=new LinearLayout.LayoutParams(0,dp(44),1);body.leftMargin=dp(8);header.addView(copy,body);
    CobraBrandMark badge=new CobraBrandMark();badge.setTag("cobra_drawer_brand");header.addView(badge,new LinearLayout.LayoutParams(dp(42),dp(32)));
    CobraIconButton back=cobraIcon("back","Collapse navigation",cobraModeDark(),v->closeCobraExperienceDrawer());
    header.addView(back,new LinearLayout.LayoutParams(dp(38),dp(38)));
    vtheme().tree(header,"drawer.header");header.setOnLongClickListener(v->{vtheme().manager(this);return true;});return header;
  }''')

    # Drawer rows: Right means Enter ONLY while the drawer is the inline Live TV column.
    s=repl(s,'cobraDrawerDestination',r'''  private void cobraDrawerDestination(LinearLayout parent,String icon,String label,String destination,Runnable action){
    if(!mUi.destinationEnabled(destination))return;
    label=vtheme().copy("drawer.label."+destination.toLowerCase(java.util.Locale.ROOT).replace(" ","_"),label);
    final boolean settingsDestination="SETTINGS".equalsIgnoreCase(destination);
    LinearLayout row=cobraDetailRow(icon,label,null,"cobra-destination:"+destination,false,()->{
      closeCobraExperienceDrawer();mCobraTvDrawerPreviousFocus=null;
      if(settingsDestination&&"COBRA • SETTINGS".equals(mCobraStageTitle)){cobraReturnFromSettings();return;}
      if("COBRA • SETTINGS".equals(mCobraStageTitle)&&!settingsDestination)cobraDiscardSettingsReturn();
      if(!settingsDestination)cobraDiscardVodLandingReturn();action.run();
    });
    row.setSelected(destination.equals(cobraTvDrawerDestination()));
    row.setOnKeyListener((v,key,event)->{
      if(event.getAction()==KeyEvent.ACTION_DOWN&&key==KeyEvent.KEYCODE_DPAD_RIGHT&&mCobraTvDrawerInline){v.performClick();return true;}
      return false;
    });
    if(row.getChildCount()>0)row.getChildAt(0).setTag("cobra-drawer-icon:"+destination);
    cobraPolishDrawerRow(parent,row);
    vtheme().tree(row,"drawer.item."+destination.toLowerCase(java.util.Locale.ROOT).replace(" ","_"));
  }''')

    # Tighten only the TV drawer structure and make Power fully readable.
    old='''    View brand=cobraBrandHeader();panel.addView(brand,new LinearLayout.LayoutParams(-1,dp(62)));'''
    new='''    View brand=cobraBrandHeader();panel.addView(brand,new LinearLayout.LayoutParams(-1,dp(52)));'''
    s=once(s,old,new,'compact drawer brand height')
    s=once(s,
'''    footer.addView(power,new LinearLayout.LayoutParams(dp(104),-2));panel.addView(footer,new LinearLayout.LayoutParams(-1,dp(50)));''',
'''    footer.addView(power,new LinearLayout.LayoutParams(dp(116),-2));panel.addView(footer,new LinearLayout.LayoutParams(-1,dp(50)));''',
'power label width')

    # Live TV directory/playlist rows only: Right is the same as Select. EPG rows are untouched.
    s=repl(s,'cobraDirectory',r'''  private void cobraDirectory(LinearLayout parent,boolean sources){
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
    if(!sources){
      Button playlist=cobraTextButton(cobraModeSourceName()+"  ▾",cobraModeDark(),()->cobraOpenTvDirectory(true));
      playlist.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);playlist.setPadding(dp(14),0,dp(10),0);playlist.setSingleLine(true);
      playlist.setOnKeyListener((v,key,event)->{if(event.getAction()==KeyEvent.ACTION_DOWN&&key==KeyEvent.KEYCODE_DPAD_RIGHT){v.performClick();return true;}return false;});
      parent.addView(playlist,new LinearLayout.LayoutParams(-1,dp(54)));
    }
    android.widget.ListView list=new android.widget.ListView(this);list.setDividerHeight(0);list.setSelector(android.R.color.transparent);list.setFastScrollEnabled(false);list.setItemsCanFocus(true);list.setFocusable(true);list.setFocusableInTouchMode(false);
    list.setAdapter(new android.widget.BaseAdapter(){public int getCount(){return names.size();}public Object getItem(int p){return values.get(p);}public long getItemId(int p){return CobraModeLayout.stableId(values.get(p));}public boolean hasStableIds(){return true;}
      public View getView(int position,View recycled,android.view.ViewGroup host){
        CobraDirectoryRow row=recycled instanceof CobraDirectoryRow?(CobraDirectoryRow)recycled:new CobraDirectoryRow();String value=values.get(position);
        row.bind(names.get(position),counts.get(position),value.equals(sources?mCobraGuideSource:mCategory));
        row.setOnClickListener(v->{cobraRememberModeScroll();if(sources){mCobraGuideSource=value;mCategory="ALL";mSearch="";if("tv-directory".equals(mCobraSheetKind))closeCobraActionSheet();mCobraGuideRoute="channels";cobraTvInvalidateGroupCache();cobraRenderGuideBrowser();}else selectCobraCategory(value);});
        row.setOnKeyListener((v,key,event)->{if(event.getAction()==KeyEvent.ACTION_DOWN&&key==KeyEvent.KEYCODE_DPAD_RIGHT){v.performClick();return true;}return false;});
        return row;
      }});
    parent.addView(list,new LinearLayout.LayoutParams(-1,0,1));
    final String current=sources?mCobraGuideSource:mCategory;final int index=Math.max(0,values.indexOf(current));
    list.setSelection(index);
    list.post(()->{if(list.getAdapter()==null||list.getAdapter().getCount()==0)return;list.setSelection(index);list.post(()->{int childIndex=index-list.getFirstVisiblePosition();View row=childIndex>=0&&childIndex<list.getChildCount()?list.getChildAt(childIndex):null;if(row!=null&&row.isShown())row.requestFocus();else list.requestFocus();});});
  }''')

    # Normal mini-player video no longer carries PLAYING/PAUSED/LIVE. Keep only exceptional states.
    s=repl(s,'cobraPreviewPanel',r'''  private FrameLayout cobraPreviewPanel(Channel channel,boolean guide){
    if(mCobraPreviewHost!=null)return mCobraPreviewHost;
    FrameLayout host=new FrameLayout(this);mCobraPreviewHost=host;host.setTag("cobra_preview_host");host.setBackground(cobraTvGlassPanelSurface(16,true));
    host.setFocusable(false);host.setFocusableInTouchMode(false);host.setClickable(false);host.setLongClickable(false);host.setDescendantFocusability(android.view.ViewGroup.FOCUS_BLOCK_DESCENDANTS);
    mCobraPreviewTexture=new TextureView(this);mCobraPreviewTexture.setFocusable(false);mCobraPreviewTexture.setClickable(false);host.addView(mCobraPreviewTexture,new FrameLayout.LayoutParams(-1,-1));
    TextView state=cobraText("",cobraThemeColor("text",mTheme.text),10);state.setTag("cobra_preview_label");state.setPadding(dp(8),dp(3),dp(8),dp(3));state.setVisibility(View.GONE);
    state.setBackground(cobraPanelSurface(cobraAlpha(cobraThemeColor("panel2",mTheme.panel2),210),10,cobraAlpha(cobraThemeColor("line",mTheme.line),78)));
    FrameLayout.LayoutParams statePos=new FrameLayout.LayoutParams(-2,dp(26),Gravity.TOP|Gravity.RIGHT);statePos.setMargins(dp(8),dp(8),dp(8),0);host.addView(state,statePos);
    cobraUpdatePreviewSubtitleState();return host;
  }''')

    s=repl(s,'cobraUpdatePlaybackLabels',r'''  private void cobraUpdatePlaybackLabels(){
    updateCobraPreviewPlayPause();updateCobraPlayerPlayPause();
    if(mCobraPreviewHost!=null){
      View badge=mCobraPreviewHost.findViewWithTag("cobra_preview_label");
      if(badge instanceof TextView){
        String raw=cobraPlayerState(mCobraPreviewPlayer),text="";
        if("Buffering…".equals(raw)||"Connecting…".equals(raw)||"Ended".equals(raw)||"Stream unavailable".equals(raw))text=raw;
        ((TextView)badge).setText(text);badge.setVisibility(text.isEmpty()?View.GONE:View.VISIBLE);
      }
    }
    if(mPlayerOverlay!=null){View badge=mPlayerOverlay.findViewWithTag("player_state");
      if(badge instanceof TextView){String text=CobraPresentationEffects.visibleStatus(mPlayingVodKey.isEmpty()?cobraPlayerState(mPlayer):mPlayer!=null&&mPlayer.getPlayWhenReady()?"PLAYING":"PAUSED");((TextView)badge).setText(text);badge.setVisibility(text.isEmpty()?View.GONE:View.VISIBLE);}}
    cobraTvRefreshPlayingIndicatorIfChanged();cobraRefreshProgrammeLabels();cobraUpdateLiveRewindControls();cobraUpdateTimeshiftSeek();cobraUpdatePerformanceOverlay();cobraRefreshVisualEffects();
  }''')

    # In-session VOD cache makes repeated Movies/TV Shows entry fast without background UI churn.
    s=repl(s,'cobraRememberVodCatalog',r'''  private void cobraRememberVodCatalog(ArrayList<VodItem> items,boolean series){
    ArrayList<VodItem> target=series?mCobraVodShowsCatalog:mCobraVodMoviesCatalog;
    target.clear();target.addAll(items);long now=System.currentTimeMillis();
    if(series)mCobraVodShowsLoadedAt=now;else mCobraVodMoviesLoadedAt=now;
  }''')

    s=repl(s,'showVodLibrary',r'''  private void showVodLibrary(boolean series){
    if(!isCobraAsyncAlive())return;
    long loadedAt=series?mCobraVodShowsLoadedAt:mCobraVodMoviesLoadedAt;
    ArrayList<VodItem> cached=cobraVodCatalog(series);
    if(!cached.isEmpty()&&loadedAt>0L&&System.currentTimeMillis()-loadedAt<COBRA_TV_VOD_CACHE_MS){
      renderVodBrowse(cached,series,new ArrayList<>());return;
    }
    clearStage(series?"COBRA • SERIES":"COBRA • MOVIES");status("Loading enabled provider libraries…");
    final long ticket=mCobraNavigation.current();
    submitCobraIo(()->{
      ArrayList<VodItem> items=new ArrayList<>();ArrayList<String> failures=new ArrayList<>();
      for(LiveSource source:mSources){
        if(!mFeatures.sourceEnabled(source.id)||!"xtream".equals(source.type))continue;
        try{
          Map<String,String> cats=new HashMap<>();JSONArray categories=new JSONArray(httpGet(xtreamUrl(source,series?"get_series_categories":"get_vod_categories")));
          for(int i=0;i<categories.length();i++){JSONObject c=categories.optJSONObject(i);if(c!=null)cats.put(c.optString("category_id"),c.optString("category_name","Other"));}
          JSONArray streams=new JSONArray(httpGet(xtreamUrl(source,series?"get_series":"get_vod_streams")));
          for(int i=0;i<streams.length()&&items.size()<10000;i++){
            JSONObject o=streams.optJSONObject(i);if(o==null)continue;String id=o.optString(series?"series_id":"stream_id","");if(id.isEmpty())continue;
            String title=o.optString("name",series?"Series":"Movie");String cat=cats.get(o.optString("category_id",""));if(cat==null)cat="Other";
            if(mFeatures.looksAdult(cat)||mFeatures.looksAdult(title))continue;
            long added=cobraVodParseEpoch(o.optString("added",o.optString("last_modified","0")));
            double rating=o.optDouble("rating",o.optDouble("rating_5based",0.0));
            String year=o.optString("year",o.optString("releaseDate",o.optString("release_date","")));
            items.add(new VodItem(source.id,id,title,cat,o.optString(series?"cover":"stream_icon",""),sanitizeExtension(o.optString("container_extension","mp4")),series,added,rating,year));
          }
        }catch(Exception e){failures.add(source.name+": "+e.getClass().getSimpleName());}
      }
      cobraPublishNavigation(ticket,()->{cobraRememberVodCatalog(items,series);renderVodBrowse(items,series,failures);});
    });
  }''')

    # Dedicated section search. It searches only the corresponding Movies or TV Shows catalog.
    search_helpers=r'''  private void cobraShowVodSectionSearch(boolean series){
    ArrayList<VodItem> catalog=cobraVodCatalog(series);
    if(catalog.isEmpty()){toast((series?"TV Shows":"Movies")+" are still loading");return;}
    EditText input=field(series?"Search TV Shows":"Search Movies",InputType.TYPE_CLASS_TEXT);
    new CobraVisualRenderer.DialogBuilder(this,vtheme(),"dialog")
      .setTitle(series?"Search TV Shows":"Search Movies").setView(input)
      .setPositiveButton("SEARCH",(d,w)->{
        String query=input.getText().toString().trim();if(query.isEmpty())return;
        String needle=query.toLowerCase(Locale.US);ArrayList<VodItem> filtered=new ArrayList<>();
        for(VodItem item:catalog){
          LiveSource source=sourceById(item.sourceId);String provider=source==null?"":source.name;
          if(item.title.toLowerCase(Locale.US).contains(needle)||item.category.toLowerCase(Locale.US).contains(needle)||
             item.year.toLowerCase(Locale.US).contains(needle)||provider.toLowerCase(Locale.US).contains(needle))filtered.add(item);
        }
        cobraShowVodCollection("Search • "+query,filtered,series);
      }).setNegativeButton("Cancel",null).show();
  }

  private View cobraVodSectionSearchMenu(boolean series){
    LinearLayout bar=new LinearLayout(this);bar.setGravity(Gravity.CENTER_VERTICAL);bar.setPadding(dp(4),dp(2),dp(4),dp(2));
    bar.setBackground(cobraTvGlassPanelSurface(14,false));TextView label=text(series?"TV Shows":"Movies",cobraModeColor("muted"),11,Gravity.LEFT|Gravity.CENTER_VERTICAL);
    label.setLetterSpacing(.08f);bar.addView(label,new LinearLayout.LayoutParams(0,dp(46),1));
    Button search=action(series?"Search TV Shows":"Search Movies");search.setTag(series?"cobra_shows_search":"cobra_movies_search");search.setAllCaps(false);
    search.setOnClickListener(v->cobraShowVodSectionSearch(series));bar.addView(search,new LinearLayout.LayoutParams(dp(190),dp(44)));return bar;
  }

'''
    marker='  private void renderVodBrowse(ArrayList<VodItem> items, boolean series, ArrayList<String> failures) {'
    req(s.count(marker)==1,'renderVodBrowse insertion marker drift')
    s=s.replace(marker,search_helpers+marker,1)

    s=once(s,
'''    scroll.addView(page);

    ArrayList<VodItem> featured = cobraVodFeaturedSubset(items);''',
'''    scroll.addView(page);
    page.addView(cobraVodSectionSearchMenu(series),new LinearLayout.LayoutParams(-1,dp(50)));

    ArrayList<VodItem> featured = cobraVodFeaturedSubset(items);''',
'dedicated Movies/Shows search menu')

    # Performance: remove redundant second layout pass around group expansion/commit.
    s=repl(s,'cobraTvShowGroupChooser',r'''  private void cobraTvShowGroupChooser(boolean animate){
    if(mCobraGuideShell==null||!mCobraGuideShell.isAttachedToWindow()){mCobraModeGroupsExpanded=true;cobraShowGuideShell();}
    else{mCobraModeGroupsExpanded=true;cobraLayoutGuide();cobraRenderGuideBrowser();}
    if(animate&&mCobraGuideDirectory!=null)mCobraGuideDirectory.post(this::cobraTvAnimateGroupPanelIn);
  }''')
    s=repl(s,'cobraTvCommitGroupSelection',r'''  private void cobraTvCommitGroupSelection(String value){
    cobraRememberModeScroll();mCategory=value;mSearch="";mCobraGuideRoute="channels";mCobraInspectedChannel=null;mCobraInspectedProgram=null;mCobraModeGroupsExpanded=false;
    cobraLayoutGuide();cobraRenderGuideBrowser();cobraTvAnimateGuideContentIn(-1);
    if(mCobraGuideBrowser!=null)mCobraGuideBrowser.postDelayed(this::cobraTvFocusGuideBody,90L);
  }''')

    # Contracts and scope guards.
    req('COBRA_TV_FINAL_POLISH_BUILD="cobra_tv_final_polish_2103235"' in s,'RC15 marker missing')
    req('title.setSingleLine(true)' in member(s,'cobraBrandHeader'),'Cobra brand can still wrap')
    req('KEYCODE_DPAD_RIGHT&&mCobraTvDrawerInline' in member(s,'cobraDrawerDestination'),'Live TV drawer Right=Select missing')
    req('KEYCODE_DPAD_RIGHT' in member(s,'cobraDirectory'),'Live TV directory Right=Select missing')
    req('KEYCODE_DPAD_RIGHT' not in member(s,'cobraVodCard'),'Movies/Shows card navigation was remapped')
    req('KEYCODE_DPAD_RIGHT' not in member(s,'renderVodBrowse'),'Movies/Shows landing navigation was remapped')
    req('cobra_movies_search' in s and 'cobra_shows_search' in s,'Dedicated VOD searches missing')
    req('Search TV Shows' in s and 'Search Movies' in s,'VOD search labels missing')
    req('▶ PLAYING' not in member(s,'cobraUpdatePlaybackLabels'),'Mini-player still renders PLAYING badge')
    req('cobraTvChannelPlaying' in s and '▶ PLAYING' in s,'Authoritative channel-row PLAYING state lost')
    req('COBRA_TV_VOD_CACHE_MS' in s,'VOD performance cache missing')
    req(member(s,'cobraTvShowGroupChooser').count('cobraLayoutGuide()')<=1,'Redundant group chooser layout pass survived')
    req(member(s,'cobraTvCommitGroupSelection').count('cobraLayoutGuide()')<=1,'Redundant group commit layout pass survived')
    req('COBRA_TV_INTEGRATED_SHELL_BUILD="cobra_tv_integrated_shell_playing_2103234"' in s,'RC14 integrated shell marker lost')
    req('mCobraGuideShell.addView(panel' in s,'RC14 inline drawer lost')
    req('Select the current channel again to watch' not in s,'Old preview instruction returned')
    req('AMBIENT MODE  •' not in s,'Ambient Mode returned')
    req('startCobraPreview(mGuidePreviewChannel)' in s and 'mCobraPreviewPlayer=session' in s,'Preview/player handoff contract lost')
    path.write_text(s)
    return sha_bytes(before),sha(path)

def apply(shell:Path):
    receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text())
    req(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,'Expected exact locked 2103234 RC14 parent')
    req(receipt.get('tv_drawer_inline_column') is True and receipt.get('tv_drawer_back_restores_underlay') is True,'Expected locked RC14 drawer')
    req(receipt.get('tv_playing_channel_indicator') is True and receipt.get('tv_playing_indicator_actual_session') is True,'Expected locked RC14 session indicator')
    req(receipt.get('tv_glass_system') is True and receipt.get('tv_ambient_mode_retired') is True,'Expected locked RC13 glass/Ambient parent')
    req(receipt.get('tv_navigation_hierarchy')=='drawer-groups-grid-player' and receipt.get('tv_back_reverses_hierarchy') is True,'Expected protected TV hierarchy')
    req(receipt.get('tv_mini_player_preserved') is True and receipt.get('tv_preview_engine_preserved') is True,'Expected protected mini-player')
    req(receipt.get('tv_target_abi')=='armeabi-v7a' and receipt.get('mobile_parent_untouched') is True,'Expected isolated ARMv7 TV parent')

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
      tv_drawer_brand_compact=True,tv_drawer_brand_single_line=True,tv_drawer_power_unclipped=True,
      tv_live_right_select_drawer=True,tv_live_right_select_directory=True,tv_right_select_scope='live-tv-only',
      tv_vod_right_navigation_untouched=True,tv_movies_dedicated_search=True,tv_shows_dedicated_search=True,
      tv_vod_search_uses_section_catalog=True,tv_vod_session_cache_ms=300000,
      tv_mini_player_playing_badge_removed=True,tv_mini_player_exception_status_only=True,
      tv_playing_channel_indicator=True,tv_playing_indicator_actual_session=True,
      tv_group_layout_pass_reduced=True,tv_performance_polish=True,tv_stability_polish=True,tv_ui_polish=True,
      tv_drawer_inline_column=True,tv_drawer_guide_overlay=False,tv_drawer_back_restores_underlay=True,
      tv_glass_system=True,tv_glass_real_time_blur=False,tv_ambient_mode_retired=True,
      tv_live_flow='drawer-live-tv-groups-grid',tv_navigation_hierarchy='drawer-groups-grid-player',tv_back_reverses_hierarchy=True,
      tv_hamburger_removed=True,tv_grid_settings_next_to_search=True,tv_mini_player_adaptive_large=True,
      tv_mini_player_preserved=True,tv_preview_engine_preserved=True,tv_group_counts_cached=True,
      tv_multiview_row_focus_visible=True,tv_player_footer_unclipped=True,multiview_two_to_one_session_preserved=True,
      mobile_parent_untouched=True,native_engine_rebuilt=False,playback_engine_unchanged=True
    )
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for name,row in receipt['files'].items():req(sha(shell/name)==row['after'],'Final receipt drift '+name)

    Path('audit235').mkdir(exist_ok=True)
    Path('audit235/tv-final-polish-source.json').write_text(json.dumps({
      'build':VERSION,'version_name':NEW_NAME,'parent_build':OLD_VERSION,'target_abi':'armeabi-v7a',
      'activity_before_sha256':before,'activity_after_sha256':after,'marker':'cobra_tv_final_polish_2103235',
      'drawer_brand':'compact-single-line','mini_player_playing_badge':False,
      'authoritative_playing_indicator':'actual Live TV channel row/session',
      'right_select':{'drawer':'live-tv-inline-only','directory':'live-tv-only','epg':False,'movies':False,'shows':False},
      'dedicated_search':['movies','tv-shows'],'vod_search_scope':'matching section catalog',
      'vod_session_cache_ms':300000,'redundant_guide_layout_passes_removed':True,
      'glass_system_preserved':True,'ambient_mode_retired':True,'navigation_preserved':'drawer-groups-grid-player',
      'mini_player_preserved':True,'multiview_preserved':True,'native_engine_rebuilt':False,
      'playback_engine_unchanged':True,'mobile_fold_untouched':True,'physical_device_verified':False
    },indent=2,sort_keys=True)+'\n')
    print('PASS: 2103235 final TV refinement applied over exact locked 2103234 RC14')

def main():
    p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);a=p.parse_args();apply(a.shell)
if __name__=='__main__':main()
