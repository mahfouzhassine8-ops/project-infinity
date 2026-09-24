#!/usr/bin/env python3
"""2103240 RC20 — inline VOD landing search + TV remote/focus crash hardening over passed RC19.

Scope:
- Keep exact passed RC19 as rollback/base.
- Replace the Movies/Shows landing-page search strip + separate Search button with one full-width
  "Type a title or narrow by genre" EditText directly under the provider/status row.
- Use the native Android TV IME only. Search stays on the landing page; typing replaces the content
  beneath the field with closest results (exact title -> prefix -> contains -> genre/year/provider).
- Empty query restores the approved RC18/RC19 cinematic hero/shelves/genres landing UI.
- Harden the Live-TV drawer + directory/channel-selection remote path:
  suppress repeated Left/Right edge actions, guard stale/detached clicks, cancel stale delayed focus,
  and restore focus only to attached/visible/focusable targets.
- Preserve EPG directional navigation, Live TV structure, playback, timeshift/rewind, Multi-View,
  mini-player, pulsing PLAYING dot, providers, ARMv7 native engine/resources and phone/Fold scope.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

VERSION=2103240
OLD_VERSION=2103239
OLD_NAME='1.0.9-Cobra-Onn4KPro-TV-Native-Search-UI-Polish-RC19'
NEW_NAME='1.0.9-Cobra-Onn4KPro-TV-Search-Remote-Hardening-RC20'
SOURCE='tools/android/packaging/xbmc/'
ACT=SOURCE+'src/InfinityLiveActivity.java.in'

def hb(v): return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()
def sha(p): return hb(Path(p).read_bytes())
def req(v,m):
    if not v: raise RuntimeError(m)
def once(s,a,b,label):
    req(s.count(a)==1,f'{label}: expected 1 anchor, got {s.count(a)}')
    return s.replace(a,b,1)
def span(text,name,kind='method'):
    if kind=='method':
        p=re.compile(r'(?m)^\s*(?:@Override\s+)?(?:(?:public|private|protected|static|final|synchronized)\s+)*[\w.<>,\[\]?]+\s+'+re.escape(name)+r'\s*\([^;{}]*\)\s*\{')
    else:
        p=re.compile(r'(?m)^\s*(?:(?:private|public|protected|static|final)\s+)*class\s+'+re.escape(name)+r'\b')
    ms=list(p.finditer(text));req(len(ms)==1,f'{kind} cardinality {name}={len(ms)}')
    st=ms[0].start();b=(text.rfind('{',st,ms[0].end()) if kind=='method' else text.find('{',ms[0].end()));req(b>=st,'opening brace missing: '+name)
    d=0;q=None;esc=line=block=False
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

def patch_activity(path:Path):
    before=path.read_bytes();s=before.decode()
    req('cobra_tv_movies_native_search_2103239' in s and 'cobra_tv_shows_native_search_2103239' in s,'Expected exact RC19 native-search source')
    req('Type a title or narrow by genre' in s and 'On-screen keyboard' not in s,'RC19 search contract missing')
    req('page.addView(cobraVodSectionSearchMenu(series)' in member(s,'renderVodBrowse'),'Expected RC19 landing Search button strip')
    req('KEYCODE_DPAD_RIGHT' in member(s,'cobraTvHandleDrawerKey'),'Expected RC19 drawer Right=Select contract')
    req('KEYCODE_DPAD_LEFT' in member(s,'cobraDirectory') and 'KEYCODE_DPAD_RIGHT' in member(s,'cobraDirectory'),'Expected RC19 directory Left/Right contract')

    protected_methods=[
      'playChannel','startCobraPreview','promoteCobraPreviewToFullscreen','cobraReturnToMultiFromFullscreen',
      'setMultiAudio','cobraLayoutPlayerPanels','cobraTvChannelPlaybackState','cobraTvChannelPlaying',
      'cobraTvPlayingDotColor','cobraTvHandleGuideKey','cobraLayoutGuide','cobraRenderGuideBrowser',
      'cobraBuildPlayerChrome','cobraTvHandlePlayerKey','showMovies','showSeries','cobraSetSectionOwner',
      'cobraShowLoadedPrimary','cobraOpenLiveTv'
    ]
    protected={n:hb(member(s,n)) for n in protected_methods}
    dot_hash=hb(member(s,'CobraTvPlayingDot','class'))

    remote_helpers=r'''  private static final long COBRA_TV_REMOTE_EDGE_GUARD_MS=120L;
  private long mCobraTvRemoteEdgeAt=0L;
  private int mCobraTvRemoteEdgeKey=KeyEvent.KEYCODE_UNKNOWN;
  private int mCobraTvDirectoryFocusEpoch=0;

  private boolean cobraTvBeginRemoteEdgeAction(KeyEvent event){
    if(event==null||event.getAction()!=KeyEvent.ACTION_DOWN)return false;
    int key=event.getKeyCode();
    if(event.getRepeatCount()>0)return false;
    long now=android.os.SystemClock.uptimeMillis();
    if(now-mCobraTvRemoteEdgeAt<COBRA_TV_REMOTE_EDGE_GUARD_MS)return false;
    mCobraTvRemoteEdgeAt=now;mCobraTvRemoteEdgeKey=key;mCobraTvDirectoryFocusEpoch++;
    return true;
  }

  private boolean cobraTvSafeRemoteClick(View scope,View target){
    if(target==null||!target.isAttachedToWindow()||target.getWindowToken()==null||!target.isShown()||
        !target.isEnabled()||!target.isClickable())return false;
    if(scope!=null&&target!=scope&&!cobraTvViewInside(scope,target))return false;
    target.performClick();return true;
  }

  private void cobraTvPostDirectoryFocus(android.widget.ListView list,int requested){
    final int epoch=++mCobraTvDirectoryFocusEpoch;
    mMain.postDelayed(()->{
      if(epoch!=mCobraTvDirectoryFocusEpoch||list==null||!list.isAttachedToWindow()||!list.isShown())return;
      android.widget.ListAdapter adapter=list.getAdapter();if(adapter==null||adapter.getCount()==0)return;
      int index=Math.max(0,Math.min(requested,adapter.getCount()-1));list.setSelection(index);
      list.postOnAnimation(()->{
        if(epoch!=mCobraTvDirectoryFocusEpoch||!list.isAttachedToWindow()||!list.isShown())return;
        int childIndex=index-list.getFirstVisiblePosition();
        View row=childIndex>=0&&childIndex<list.getChildCount()?list.getChildAt(childIndex):null;
        if(row!=null&&row.isAttachedToWindow()&&row.isShown()&&row.isEnabled()&&row.isFocusable())row.requestFocus();
        else if(list.isEnabled()&&list.isFocusable())list.requestFocus();
      });
    },24L);
  }

'''
    marker='  private boolean cobraTvHandleDrawerKey(KeyEvent event){'
    req(s.count(marker)==1,'RC20 drawer helper insertion drift')
    s=s.replace(marker,remote_helpers+marker,1)

    s=repl(s,'cobraTvFocusTagged',r'''  private boolean cobraTvFocusTagged(View root,String tag){
    View target=cobraTvTagged(root,tag);
    if(target!=null&&target.isAttachedToWindow()&&target.getWindowToken()!=null&&target.isShown()&&
        target.isEnabled()&&target.isFocusable()&&target.requestFocus()){cobraTvReveal(target);return true;}
    return false;
  }''')

    s=repl(s,'cobraTvHandleDrawerKey',r'''  private boolean cobraTvHandleDrawerKey(KeyEvent event){
    if(mCobraTvDrawerPanel==null||!mCobraTvDrawerPanel.isAttachedToWindow()||event.getAction()!=KeyEvent.ACTION_DOWN)return false;
    int code=event.getKeyCode();
    if(code==KeyEvent.KEYCODE_BACK||code==KeyEvent.KEYCODE_DPAD_LEFT){
      if(!cobraTvBeginRemoteEdgeAction(event))return true;
      cobraTvCloseDrawerRestoreFocus();return true;
    }
    if(code==KeyEvent.KEYCODE_DPAD_UP)return cobraTvMoveDrawerFocus(-1);
    if(code==KeyEvent.KEYCODE_DPAD_DOWN)return cobraTvMoveDrawerFocus(1);
    if(code==KeyEvent.KEYCODE_DPAD_RIGHT){
      if(!cobraTvBeginRemoteEdgeAction(event))return true;
      View focus=getCurrentFocus();
      if(!cobraTvSafeRemoteClick(mCobraTvDrawerPanel,focus))cobraTvFocusDrawer(mCobraTvDrawerPanel);
      return true;
    }
    return false;
  }''')

    s=repl(s,'cobraTvCloseDrawerRestoreFocus',r'''  private boolean cobraTvCloseDrawerRestoreFocus(){
    View restore=mCobraTvDrawerPreviousFocus;boolean closed=closeCobraExperienceDrawer();mCobraTvDrawerPreviousFocus=null;
    final int epoch=++mCobraTvDirectoryFocusEpoch;
    if(closed)mMain.postDelayed(()->{
      if(epoch!=mCobraTvDirectoryFocusEpoch)return;
      if(restore!=null&&restore.isAttachedToWindow()&&restore.getWindowToken()!=null&&restore.isShown()&&
          restore.isEnabled()&&restore.isFocusable()&&restore.requestFocus())return;
      if(mCobraGuideShell==null||!mCobraGuideShell.isAttachedToWindow())return;
      if(mCobraModeGroupsExpanded)cobraTvFocusFirst(mCobraGuideDirectory);else cobraTvFocusGuideBody();
    },24L);
    return closed;
  }''')

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
      if(event.getAction()!=KeyEvent.ACTION_DOWN)return false;
      if(key==KeyEvent.KEYCODE_DPAD_RIGHT&&mCobraTvDrawerInline){
        if(!cobraTvBeginRemoteEdgeAction(event))return true;
        cobraTvSafeRemoteClick(mCobraTvDrawerPanel,v);return true;
      }
      return false;
    });
    if(row.getChildCount()>0)row.getChildAt(0).setTag("cobra-drawer-icon:"+destination);
    cobraPolishDrawerRow(parent,row);
    vtheme().tree(row,"drawer.item."+destination.toLowerCase(java.util.Locale.ROOT).replace(" ","_"));
  }''')

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
      playlist.setOnKeyListener((v,key,event)->{
        if(event.getAction()!=KeyEvent.ACTION_DOWN)return false;
        if(key==KeyEvent.KEYCODE_DPAD_RIGHT){if(!cobraTvBeginRemoteEdgeAction(event))return true;cobraTvSafeRemoteClick(parent,v);return true;}
        if(key==KeyEvent.KEYCODE_DPAD_LEFT){if(!cobraTvBeginRemoteEdgeAction(event))return true;toggleCobraDrawer();return true;}
        return false;
      });
      parent.addView(playlist,new LinearLayout.LayoutParams(-1,dp(54)));
    }
    android.widget.ListView list=new android.widget.ListView(this);list.setDividerHeight(0);list.setSelector(android.R.color.transparent);
    list.setFastScrollEnabled(false);list.setItemsCanFocus(true);list.setFocusable(true);list.setFocusableInTouchMode(false);
    list.setOverScrollMode(View.OVER_SCROLL_IF_CONTENT_SCROLLS);list.setSmoothScrollbarEnabled(true);
    list.setAdapter(new android.widget.BaseAdapter(){public int getCount(){return names.size();}public Object getItem(int p){return values.get(p);}public long getItemId(int p){return CobraModeLayout.stableId(values.get(p));}public boolean hasStableIds(){return true;}
      public View getView(int position,View recycled,android.view.ViewGroup host){
        CobraDirectoryRow row=recycled instanceof CobraDirectoryRow?(CobraDirectoryRow)recycled:new CobraDirectoryRow();String value=values.get(position);
        row.bind(names.get(position),counts.get(position),value.equals(sources?mCobraGuideSource:mCategory));
        row.setOnClickListener(v->{cobraRememberModeScroll();if(sources){mCobraGuideSource=value;mCategory="ALL";mSearch="";if("tv-directory".equals(mCobraSheetKind))closeCobraActionSheet();mCobraGuideRoute="channels";cobraTvInvalidateGroupCache();cobraRenderGuideBrowser();}else selectCobraCategory(value);});
        row.setOnKeyListener((v,key,event)->{
          if(event.getAction()!=KeyEvent.ACTION_DOWN)return false;
          if(key==KeyEvent.KEYCODE_DPAD_RIGHT){if(!cobraTvBeginRemoteEdgeAction(event))return true;cobraTvSafeRemoteClick(list,v);return true;}
          if(key==KeyEvent.KEYCODE_DPAD_LEFT){
            if(!cobraTvBeginRemoteEdgeAction(event))return true;
            if(sources)closeCobraActionSheet();else toggleCobraDrawer();return true;
          }
          return false;
        });
        return row;
      }});
    parent.addView(list,new LinearLayout.LayoutParams(-1,0,1));
    final String current=sources?mCobraGuideSource:mCategory;final int index=Math.max(0,values.indexOf(current));
    list.setSelection(index);cobraTvPostDirectoryFocus(list,index);
  }''')

    landing_helpers=r'''  private void cobraPopulateVodLandingDefault(LinearLayout content,ArrayList<VodItem> items,boolean series,ArrayList<String> failures){
    content.removeAllViews();
    ArrayList<VodItem> featured=cobraVodFeaturedSubset(items);LinearLayout.LayoutParams heroLp=new LinearLayout.LayoutParams(-1,dp(isCompact()?330:390));heroLp.topMargin=dp(8);content.addView(cobraVodHeroCarousel(featured,series),heroLp);
    ArrayList<VodItem> popular=cobraVodPopularSubset(items);cobraAddVodShelf(content,"Popular Now",popular,16,false,series);
    ArrayList<VodItem> recent=cobraVodRecentSubset(items);cobraAddVodShelf(content,"Recent Releases",recent,16,false,series);
    cobraAddVodGenres(content,items,series);
    ArrayList<VodItem> continuing=cobraVodContinueSubset(items);if(!continuing.isEmpty())cobraAddVodShelf(content,"Continue Watching",continuing,14,true,series);
    ArrayList<VodItem> because=cobraVodBecauseYouWatched(items);if(!because.isEmpty())cobraAddVodShelf(content,"Because You Watched…",because,14,false,series);
    ArrayList<VodItem> trending=cobraVodTrendingSubset(items);cobraAddVodShelf(content,series?"Trending Shows":"Trending Movies",trending,14,false,series);
    if(!failures.isEmpty()){TextView note=text("Some providers could not refresh. Existing available titles are shown.",cobraThemeColor("muted",mTheme.muted),12,Gravity.LEFT|Gravity.CENTER_VERTICAL);LinearLayout.LayoutParams np=new LinearLayout.LayoutParams(-1,dp(42));np.topMargin=dp(12);content.addView(note,np);}
  }

  private void cobraPopulateVodLandingSearchResults(LinearLayout content,EditText input,boolean series){
    if(content==null||input==null||!input.isAttachedToWindow())return;
    String query=input.getText()==null?"":input.getText().toString().trim();
    if(query.isEmpty())return;
    CobraTvVodSearchResult result=cobraTvVodSearchMatches(series,query,"",35);content.removeAllViews();
    LinearLayout header=new LinearLayout(this);header.setGravity(Gravity.CENTER_VERTICAL);
    TextView title=text(series?"Matching TV Shows":"Matching Movies",cobraModeColor("text"),18,Gravity.LEFT|Gravity.CENTER_VERTICAL);
    title.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));
    TextView count=text(result.total+" match"+(result.total==1?"":"es")+(result.total>result.items.size()?"  •  showing "+result.items.size():""),cobraModeColor("muted"),11,Gravity.RIGHT|Gravity.CENTER_VERTICAL);
    header.addView(title,new LinearLayout.LayoutParams(0,dp(44),1));header.addView(count,new LinearLayout.LayoutParams(dp(210),dp(44)));
    LinearLayout.LayoutParams hp=new LinearLayout.LayoutParams(-1,dp(48));hp.topMargin=dp(5);content.addView(header,hp);
    if(result.items.isEmpty()){
      TextView empty=text("No close matches. Try fewer letters or type a genre.",cobraModeColor("muted"),14,Gravity.CENTER);
      content.addView(empty,new LinearLayout.LayoutParams(-1,dp(130)));return;
    }
    final android.widget.GridLayout grid=new android.widget.GridLayout(this);int columns=isCompact()?3:5;
    grid.setColumnCount(columns);grid.setAlignmentMode(android.widget.GridLayout.ALIGN_BOUNDS);grid.setClipChildren(false);grid.setClipToPadding(false);
    for(int i=0;i<result.items.size();i++){
      final int position=i;View card=cobraVodCard(result.items.get(i),cobraVodContinueObject(result.items.get(i))!=null);
      card.setTag("cobra_vod_landing_search_result_"+i);card.setId(View.generateViewId());
      card.setOnKeyListener((v,key,event)->{
        if(event.getAction()==KeyEvent.ACTION_DOWN&&key==KeyEvent.KEYCODE_DPAD_UP&&position<columns)return input.requestFocus();
        return false;
      });
      android.widget.GridLayout.LayoutParams lp=new android.widget.GridLayout.LayoutParams();
      lp.width=dp(isCompact()?142:158);lp.height=dp(isCompact()?258:288);lp.setMargins(dp(7),dp(5),dp(7),dp(8));grid.addView(card,lp);
    }
    content.addView(grid,new LinearLayout.LayoutParams(-1,-2));
  }

'''
    landing_marker='  private void renderVodBrowse(ArrayList<VodItem> items, boolean series, ArrayList<String> failures) {'
    req(s.count(landing_marker)==1,'RC20 landing helper insertion drift')
    s=s.replace(landing_marker,landing_helpers+landing_marker,1)

    s=repl(s,'renderVodBrowse',r'''  private void renderVodBrowse(ArrayList<VodItem> items, boolean series, ArrayList<String> failures) {
    cobraDiscardVodLandingReturn();clearStage(series ? "COBRA • TV SHOWS" : "COBRA • MOVIES");mCobraVodTrimRoles.clear();
    status((series?"TV Shows":"Movies")+"  •  "+items.size()+" titles across enabled providers");
    if(items.isEmpty()){renderVodItems(items,series,failures);return;}
    final ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);scroll.setClipToPadding(false);
    final LinearLayout page=new LinearLayout(this);page.setOrientation(LinearLayout.VERTICAL);page.setPadding(dp(isCompact()?10:18),dp(7),dp(isCompact()?10:18),dp(30));page.setClipChildren(false);page.setClipToPadding(false);scroll.addView(page);

    final EditText input=field("Type a title or narrow by genre",InputType.TYPE_CLASS_TEXT);
    input.setSingleLine(true);input.setTextSize(17);input.setTag(series?"cobra_tv_shows_landing_search_2103240":"cobra_tv_movies_landing_search_2103240");
    input.setContentDescription(series?"Search TV Shows by title or genre":"Search Movies by title or genre");
    input.setImeOptions(android.view.inputmethod.EditorInfo.IME_ACTION_SEARCH);input.setBackground(cobraTvGlassRowSurface(16));input.setPadding(dp(16),0,dp(16),0);
    input.setHintTextColor(cobraModeColor("muted"));cobraTvVodFocusPolish(input,1.012f);
    LinearLayout.LayoutParams searchLp=new LinearLayout.LayoutParams(-1,dp(58));searchLp.topMargin=dp(4);searchLp.bottomMargin=dp(5);page.addView(input,searchLp);

    final LinearLayout content=new LinearLayout(this);content.setOrientation(LinearLayout.VERTICAL);content.setClipChildren(false);content.setClipToPadding(false);
    page.addView(content,new LinearLayout.LayoutParams(-1,-2));cobraPopulateVodLandingDefault(content,items,series,failures);

    final Runnable[] pending=new Runnable[1];final int[] generation={0};
    input.addTextChangedListener(new android.text.TextWatcher(){
      public void beforeTextChanged(CharSequence text,int start,int count,int after){}
      public void onTextChanged(CharSequence text,int start,int before,int count){}
      public void afterTextChanged(android.text.Editable text){
        if(pending[0]!=null)mMain.removeCallbacks(pending[0]);final int token=++generation[0];
        pending[0]=()->{
          if(token!=generation[0]||!input.isAttachedToWindow()||!content.isAttachedToWindow())return;
          String q=input.getText()==null?"":input.getText().toString().trim();
          if(q.isEmpty())cobraPopulateVodLandingDefault(content,items,series,failures);
          else cobraPopulateVodLandingSearchResults(content,input,series);
        };
        mMain.postDelayed(pending[0],150L);
      }
    });
    final Runnable showIme=()->{
      if(!input.isAttachedToWindow())return;input.requestFocus();
      android.view.inputmethod.InputMethodManager imm=(android.view.inputmethod.InputMethodManager)getSystemService(android.content.Context.INPUT_METHOD_SERVICE);
      if(imm!=null)imm.showSoftInput(input,android.view.inputmethod.InputMethodManager.SHOW_IMPLICIT);
    };
    input.setOnClickListener(v->showIme.run());
    input.setOnKeyListener((v,key,event)->{
      if(event.getAction()!=KeyEvent.ACTION_DOWN)return false;
      if(key==KeyEvent.KEYCODE_DPAD_CENTER||key==KeyEvent.KEYCODE_ENTER){showIme.run();return true;}
      if(key==KeyEvent.KEYCODE_DPAD_DOWN){View next=input.focusSearch(View.FOCUS_DOWN);return next!=null&&next!=input&&next.requestFocus();}
      return false;
    });
    input.setOnEditorActionListener((v,actionId,event)->{
      boolean submit=actionId==android.view.inputmethod.EditorInfo.IME_ACTION_SEARCH||
          actionId==android.view.inputmethod.EditorInfo.IME_ACTION_DONE||
          (event!=null&&event.getKeyCode()==KeyEvent.KEYCODE_ENTER);
      if(!submit)return false;
      android.view.inputmethod.InputMethodManager imm=(android.view.inputmethod.InputMethodManager)getSystemService(android.content.Context.INPUT_METHOD_SERVICE);
      if(imm!=null)imm.hideSoftInputFromWindow(input.getWindowToken(),0);
      View first=content.findViewWithTag("cobra_vod_landing_search_result_0");
      if(first!=null&&first.isAttachedToWindow()&&first.isShown()&&first.isFocusable())first.requestFocus();
      return true;
    });
    mStage.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));cobraTvSectionEntrance(scroll);
  }''')

    for n,h in protected.items():req(hb(member(s,n))==h,'Protected TV/player behavior changed: '+n)
    req(hb(member(s,'CobraTvPlayingDot','class'))==dot_hash,'RC16 pulsing dot changed')
    req('cobraVodSectionSearchMenu(series)' not in member(s,'renderVodBrowse'),'Separate landing Search button strip survived RC20')
    req('cobra_tv_movies_landing_search_2103240' in s and 'cobra_tv_shows_landing_search_2103240' in s,'Inline landing search markers missing')
    req('cobraPopulateVodLandingSearchResults' in member(s,'renderVodBrowse'),'Inline landing result renderer disconnected')
    req('COBRA_TV_REMOTE_EDGE_GUARD_MS=120L' in s,'Remote edge guard missing')
    req('event.getRepeatCount()>0' in s and 'cobraTvSafeRemoteClick' in s,'Remote repeat/safe-click hardening missing')
    req('cobraTvPostDirectoryFocus(list,index)' in member(s,'cobraDirectory'),'Directory stale-focus guard missing')
    req('KEYCODE_DPAD_LEFT' in member(s,'cobraDirectory') and 'KEYCODE_DPAD_RIGHT' in member(s,'cobraDirectory'),'Directory Left/Right contract lost')
    req('KEYCODE_DPAD_RIGHT' in member(s,'cobraTvHandleDrawerKey'),'Drawer Right=Select lost')
    req('NORMAL_PULSE_MS=1320L' in s and 'CINEMA_PULSE_MS=1900L' in s,'Pulsing dot cadence lost')
    req('AMBIENT MODE  •' not in s,'TV Ambient Mode returned')
    path.write_text(s)
    return hb(before),sha(path)

def apply(shell:Path):
    receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text())
    req(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,'Expected exact passed RC19 source parent')
    req(receipt.get('tv_native_search_polish') is True and receipt.get('tv_search_native_android_tv_ime') is True,'RC19 native-search contract missing')
    req(receipt.get('tv_search_custom_keyboard_removed') is True and receipt.get('tv_search_left_panel_removed') is True,'RC19 search cleanup missing')
    req(receipt.get('tv_live_structure_unchanged') is True and receipt.get('playback_engine_unchanged') is True,'RC19 playback preservation missing')
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
      physical_device_verified=False,runtime_device_tested=False,
      tv_vod_landing_search_inline=True,tv_vod_search_separate_landing_button_removed=True,
      tv_vod_search_top_field_inline=True,tv_vod_search_native_android_tv_ime=True,
      tv_vod_search_inline_live_narrowing=True,tv_vod_search_empty_restores_cinematic_landing=True,
      tv_vod_search_exact_title_priority=True,tv_vod_search_genre_text_matching=True,
      tv_vod_search_debounce_ms=150,tv_vod_search_visible_result_cap=35,
      tv_remote_edge_guard_ms=120,tv_remote_repeat_suppressed=True,tv_remote_safe_click=True,
      tv_directory_focus_epoch_guard=True,tv_drawer_focus_epoch_guard=True,tv_remote_crash_hardening=True,
      tv_remote_left_back_preserved=True,tv_remote_right_select_preserved=True,
      tv_focus_target_attachment_guard=True,tv_ui_refinement_polish=True,tv_stability_polish=True,
      tv_motion_lightweight=True,tv_real_time_blur=False,tv_live_structure_unchanged=True,
      mobile_parent_untouched=True,native_engine_rebuilt=False,playback_engine_unchanged=True
    )
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for name,row in receipt['files'].items():req(sha(shell/name)==row['after'],'Final receipt drift '+name)

    out=Path('audit240');out.mkdir(exist_ok=True)
    (out/'tv-search-remote-hardening-source.json').write_text(json.dumps({
      'build':VERSION,'version_name':NEW_NAME,'parent_build':OLD_VERSION,'target_abi':'armeabi-v7a',
      'activity_before_sha256':before,'activity_after_sha256':after,
      'search':{
        'landing_inline':True,'separate_search_button_removed':True,'native_android_tv_ime':True,
        'empty_query_restores_cinematic_landing':True,'live_narrowing':True,
        'ranking':['exact-title','title-prefix','title-contains','genre/year/provider'],
        'debounce_ms':150,'visible_cap':35
      },
      'remote_hardening':{
        'edge_guard_ms':120,'repeat_suppression':True,'safe_attached_click':True,
        'directory_focus_epoch':True,'drawer_focus_epoch':True,'left_back_preserved':True,'right_select_preserved':True
      },
      'preservation':{
        'live_tv_structure_unchanged':True,'guide_directional_navigation_unchanged':True,
        'playback_engine_unchanged':True,'native_engine_rebuilt':False,'mobile_fold_untouched':True
      },
      'physical_device_verified':False
    },indent=2,sort_keys=True)+'\n')
    print('PASS: 2103240 RC20 inline VOD search + TV remote/focus crash hardening applied over exact passed RC19')

def main():
    p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);a=p.parse_args();apply(a.shell)
if __name__=='__main__':main()
