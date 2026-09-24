#!/usr/bin/env python3
"""2103238 RC18 — TV-first Movies/Shows refinement + whole-Cobra TV polish over passed RC17.

Scope:
- Movies and TV Shows get a television-first cinematic landing layout based on the approved mockup.
- Dedicated full-screen Movies/Shows search with live narrowing, genre chips, on-screen A-Z/0-9
  keyboard, normal Android text input support, exact-title prioritization and remote focus restoration.
- Larger poster cards, clearer focus, restrained focus/section motion, cleaner spacing and hierarchy.
- Popular Now -> Recent Releases -> Genres becomes the primary TV browse order.
- Existing collections/details/seasons/episodes remain functional and section ownership stays explicit.
- Live TV keeps its approved structure/features; only a lightweight one-time section entrance polish is
  added. Drawer/Groups/Grid/Player, Left/Right contract, pulsing dot, mini-player, Multi-View,
  timeshift/rewind and native playback remain protected.
- Performance: search is debounced, results are capped on-screen, catalog reuse stays intact, no blur.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

VERSION=2103238
OLD_VERSION=2103237
OLD_NAME='1.0.9-Cobra-Onn4KPro-TV-Section-Owner-RC17'
NEW_NAME='1.0.9-Cobra-Onn4KPro-TV-Movies-Shows-Refinement-RC18'
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
        p=re.compile(r'(?m)^\s*(?:@Override\s+)?(?:(?:public|private|protected|static|final|synchronized)\s+)*[\w.<>,\[\]?]+\s+'+re.escape(name)+r'\s*\([^;{}]*\)\s*\{')
    else:
        p=re.compile(r'(?m)^\s*(?:(?:private|public|protected|static|final)\s+)*class\s+'+re.escape(name)+r'\b')
    ms=list(p.finditer(text));req(len(ms)==1,f'{kind} cardinality {name}={len(ms)}')
    st=ms[0].start();b=text.rfind('{',st,ms[0].end());req(b>=st,'opening brace missing: '+name)
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
    req('COBRA_SECTION_OWNER' in s and 'cobra_start_destination' not in s,'Expected RC17 section-owner Activity')
    req('class CobraTvPlayingDot extends View' in s,'RC16 pulsing dot missing from RC17 parent')
    req('cobra_movies_search' in s and 'cobra_shows_search' in s,'RC17 dedicated VOD search controls missing')

    # Live TV/playback ownership is protected. RC18 only edits cobraOpenLiveTv for a one-shot entrance animation.
    protected_methods=[
      'playChannel','startCobraPreview','promoteCobraPreviewToFullscreen','cobraReturnToMultiFromFullscreen',
      'setMultiAudio','cobraLayoutPlayerPanels','cobraTvChannelPlaybackState','cobraTvChannelPlaying',
      'cobraTvPlayingDotColor','cobraTvHandleDrawerKey','cobraDirectory','cobraTvHandleGuideKey',
      'cobraLayoutGuide','cobraRenderGuideBrowser','cobraBuildPlayerChrome','cobraTvHandlePlayerKey',
      'onBackPressed','showMovies','showSeries','cobraSetSectionOwner','cobraShowLoadedPrimary'
    ]
    protected={n:hb(member(s,n)) for n in protected_methods}
    dot_hash=hb(member(s,'CobraTvPlayingDot','class'))

    # Shared lightweight visual polish: one-shot section entrance, plus VOD-only focus motion.
    insert=r'''  private void cobraTvSectionEntrance(View view){
    if(view==null)return;view.animate().cancel();view.setAlpha(.94f);view.setTranslationX(dp(5));
    view.animate().alpha(1f).translationX(0f).setDuration(125L).start();
  }

  private void cobraTvVodFocusPolish(View view,float focusedScale){
    if(view==null)return;view.setFocusable(true);view.setFocusableInTouchMode(false);
    view.setOnFocusChangeListener((v,focused)->{
      v.animate().cancel();v.setTranslationZ(focused?dp(5):0f);
      v.animate().scaleX(focused?focusedScale:1f).scaleY(focused?focusedScale:1f)
          .alpha(1f).setDuration(focused?105L:85L).start();
    });
  }

  private static final class CobraTvVodSearchResult{
    final ArrayList<VodItem> items;final int total;
    CobraTvVodSearchResult(ArrayList<VodItem> values,int count){items=values;total=count;}
  }

'''
    marker='  private void cobraShowVodSectionSearch(boolean series){'
    req(s.count(marker)==1,'RC18 search helper insertion drift')
    s=s.replace(marker,insert+marker,1)

    # TV-first top bar.
    s=repl(s,'cobraVodSectionSearchMenu',r'''  private View cobraVodSectionSearchMenu(boolean series){
    LinearLayout bar=new LinearLayout(this);bar.setGravity(Gravity.CENTER_VERTICAL);bar.setPadding(dp(14),dp(6),dp(8),dp(6));
    bar.setBackground(cobraTvGlassPanelSurface(16,false));
    LinearLayout copy=new LinearLayout(this);copy.setOrientation(LinearLayout.VERTICAL);
    TextView title=text(series?"TV Shows":"Movies",cobraModeColor("text"),18,Gravity.LEFT|Gravity.CENTER_VERTICAL);
    title.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));
    TextView hint=text(series?"Find an exact show, genre, year or provider":"Find an exact movie, genre, year or provider",cobraModeColor("muted"),11,Gravity.LEFT|Gravity.CENTER_VERTICAL);
    copy.addView(title,new LinearLayout.LayoutParams(-1,dp(28)));copy.addView(hint,new LinearLayout.LayoutParams(-1,dp(22)));
    bar.addView(copy,new LinearLayout.LayoutParams(0,dp(52),1));
    Button search=action("⌕  "+(series?"Search TV Shows":"Search Movies"));search.setTag(series?"cobra_shows_search":"cobra_movies_search");
    search.setAllCaps(false);search.setTextSize(14);search.setOnClickListener(v->cobraShowVodSectionSearch(series));cobraTvVodFocusPolish(search,1.025f);
    LinearLayout.LayoutParams sp=new LinearLayout.LayoutParams(dp(isCompact()?190:236),dp(50));sp.leftMargin=dp(10);bar.addView(search,sp);return bar;
  }''')

    # Full TV search with live narrowing + on-screen keyboard + normal IME input.
    s=repl(s,'cobraShowVodSectionSearch',r'''  private void cobraShowVodSectionSearch(boolean series){
    final ArrayList<VodItem> catalog=cobraVodCatalog(series);
    if(catalog.isEmpty()){toast((series?"TV Shows":"Movies")+" are still loading");return;}
    cobraCaptureVodLandingReturn(series);mCobraInternalScreen="vod-search";
    clearStage(series?"COBRA • SEARCH TV SHOWS":"COBRA • SEARCH MOVIES");
    status("Type a title or narrow by genre");
    LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.HORIZONTAL);root.setPadding(dp(16),dp(8),dp(16),dp(14));

    LinearLayout searchPanel=new LinearLayout(this);searchPanel.setOrientation(LinearLayout.VERTICAL);searchPanel.setPadding(dp(14),dp(12),dp(14),dp(12));
    searchPanel.setBackground(cobraTvGlassPanelSurface(18,true));
    TextView eyebrow=text(series?"TV SHOW SEARCH":"MOVIE SEARCH",cobraModeColor("accent"),11,Gravity.LEFT);eyebrow.setLetterSpacing(.12f);
    searchPanel.addView(eyebrow,new LinearLayout.LayoutParams(-1,dp(28)));
    TextView heading=text("What do you want to watch?",cobraModeColor("text"),21,Gravity.LEFT);heading.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));
    searchPanel.addView(heading,new LinearLayout.LayoutParams(-1,dp(40)));

    final EditText input=field(series?"Search TV Shows":"Search Movies",InputType.TYPE_CLASS_TEXT);
    input.setSingleLine(true);input.setTextSize(18);input.setTag(series?"cobra_tv_shows_search_input":"cobra_tv_movies_search_input");
    input.setBackground(cobraTvGlassRowSurface(14));input.setPadding(dp(14),0,dp(14),0);cobraTvVodFocusPolish(input,1.015f);
    searchPanel.addView(input,new LinearLayout.LayoutParams(-1,dp(54)));

    TextView filterLabel=text("Narrow by genre",cobraModeColor("muted"),11,Gravity.LEFT|Gravity.CENTER_VERTICAL);
    searchPanel.addView(filterLabel,new LinearLayout.LayoutParams(-1,dp(34)));
    final String[] genre={""};final ArrayList<Button> genreButtons=new ArrayList<>();
    android.widget.HorizontalScrollView genreScroll=new android.widget.HorizontalScrollView(this);genreScroll.setHorizontalScrollBarEnabled(false);
    LinearLayout genreRow=new LinearLayout(this);genreRow.setOrientation(LinearLayout.HORIZONTAL);genreScroll.addView(genreRow,new android.widget.HorizontalScrollView.LayoutParams(-2,-2));
    ArrayList<String> genres=new ArrayList<>();genres.add("All");
    for(String name:cobraVodGenreBuckets(catalog).keySet()){genres.add(name);if(genres.size()>=7)break;}
    final Runnable[] refresh=new Runnable[1];final Runnable[] pending=new Runnable[1];
    for(String name:genres){
      final String value="All".equals(name)?"":name;Button chip=action(name);chip.setAllCaps(false);chip.setTextSize(11);chip.setSelected(value.isEmpty());cobraTvVodFocusPolish(chip,1.025f);
      chip.setOnClickListener(v->{genre[0]=value;for(Button b:genreButtons)b.setSelected(b==v);if(refresh[0]!=null)refresh[0].run();});
      genreButtons.add(chip);LinearLayout.LayoutParams cp=new LinearLayout.LayoutParams(dp(Math.min(178,Math.max(92,72+name.length()*5))),dp(42));cp.rightMargin=dp(7);genreRow.addView(chip,cp);
    }
    searchPanel.addView(genreScroll,new LinearLayout.LayoutParams(-1,dp(48)));

    TextView keyboardLabel=text("On-screen keyboard",cobraModeColor("muted"),11,Gravity.LEFT|Gravity.CENTER_VERTICAL);
    searchPanel.addView(keyboardLabel,new LinearLayout.LayoutParams(-1,dp(30)));
    android.widget.GridLayout keyboard=new android.widget.GridLayout(this);keyboard.setColumnCount(6);keyboard.setRowCount(6);keyboard.setUseDefaultMargins(false);
    final String keys="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";Button firstKey=null;
    for(int i=0;i<keys.length();i++){
      final String letter=String.valueOf(keys.charAt(i));final int column=i%6;
      Button key=action(letter);key.setAllCaps(false);key.setTextSize(13);key.setId(View.generateViewId());cobraTvVodFocusPolish(key,1.06f);
      key.setOnClickListener(v->{input.append(letter);});
      key.setOnKeyListener((v,k,e)->{if(e.getAction()==KeyEvent.ACTION_DOWN&&k==KeyEvent.KEYCODE_DPAD_RIGHT&&column==5){View result=mStage.findViewWithTag("cobra_vod_search_result_0");if(result!=null&&result.requestFocus())return true;}return false;});
      android.widget.GridLayout.LayoutParams kp=new android.widget.GridLayout.LayoutParams();kp.width=dp(isCompact()?42:49);kp.height=dp(42);kp.setMargins(dp(3),dp(3),dp(3),dp(3));keyboard.addView(key,kp);
      if(firstKey==null)firstKey=key;
    }
    searchPanel.addView(keyboard,new LinearLayout.LayoutParams(-1,dp(isCompact()?290:300)));
    LinearLayout keyActions=new LinearLayout(this);keyActions.setGravity(Gravity.CENTER_VERTICAL);
    Button space=action("SPACE");space.setAllCaps(false);space.setOnClickListener(v->input.append(" "));cobraTvVodFocusPolish(space,1.035f);
    Button backspace=action("⌫");backspace.setContentDescription("Backspace");backspace.setOnClickListener(v->{int n=input.length();if(n>0)input.getText().delete(n-1,n);});cobraTvVodFocusPolish(backspace,1.035f);
    Button clear=action("CLEAR");clear.setAllCaps(false);clear.setOnClickListener(v->input.setText(""));cobraTvVodFocusPolish(clear,1.035f);
    keyActions.addView(space,new LinearLayout.LayoutParams(0,dp(44),1));LinearLayout.LayoutParams bp=new LinearLayout.LayoutParams(0,dp(44),.55f);bp.leftMargin=dp(6);keyActions.addView(backspace,bp);
    LinearLayout.LayoutParams clp=new LinearLayout.LayoutParams(0,dp(44),.72f);clp.leftMargin=dp(6);keyActions.addView(clear,clp);searchPanel.addView(keyActions,new LinearLayout.LayoutParams(-1,dp(48)));

    LinearLayout resultsPanel=new LinearLayout(this);resultsPanel.setOrientation(LinearLayout.VERTICAL);resultsPanel.setPadding(dp(14),dp(10),dp(8),dp(10));
    resultsPanel.setBackground(cobraTvGlassPanelSurface(18,false));
    LinearLayout resultHeader=new LinearLayout(this);resultHeader.setGravity(Gravity.CENTER_VERTICAL);
    TextView resultTitle=text("Results",cobraModeColor("text"),19,Gravity.LEFT|Gravity.CENTER_VERTICAL);resultTitle.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));
    final TextView resultCount=text("",cobraModeColor("muted"),11,Gravity.RIGHT|Gravity.CENTER_VERTICAL);
    resultHeader.addView(resultTitle,new LinearLayout.LayoutParams(0,dp(42),1));resultHeader.addView(resultCount,new LinearLayout.LayoutParams(dp(190),dp(42)));resultsPanel.addView(resultHeader,new LinearLayout.LayoutParams(-1,dp(44)));
    android.widget.ScrollView resultScroll=new android.widget.ScrollView(this);final android.widget.GridLayout results=new android.widget.GridLayout(this);results.setColumnCount(isCompact()?2:4);results.setAlignmentMode(android.widget.GridLayout.ALIGN_BOUNDS);
    resultScroll.addView(results,new android.widget.ScrollView.LayoutParams(-1,-2));resultsPanel.addView(resultScroll,new LinearLayout.LayoutParams(-1,0,1));

    final View firstKeyboard=firstKey;
    refresh[0]=()->cobraTvRenderVodSearchResults(results,resultCount,input,genre[0],series,firstKeyboard);
    input.addTextChangedListener(new android.text.TextWatcher(){
      public void beforeTextChanged(CharSequence text,int start,int count,int after){}
      public void onTextChanged(CharSequence text,int start,int before,int count){}
      public void afterTextChanged(android.text.Editable text){
        if(pending[0]!=null)mMain.removeCallbacks(pending[0]);
        pending[0]=refresh[0];mMain.postDelayed(pending[0],110L);
      }
    });
    input.setOnClickListener(v->{input.requestFocus();android.view.inputmethod.InputMethodManager imm=(android.view.inputmethod.InputMethodManager)getSystemService(android.content.Context.INPUT_METHOD_SERVICE);if(imm!=null)imm.showSoftInput(input,android.view.inputmethod.InputMethodManager.SHOW_IMPLICIT);});
    if(firstKey!=null)input.setNextFocusDownId(firstKey.getId());

    LinearLayout.LayoutParams left=new LinearLayout.LayoutParams(0,-1,isCompact()?1.05f:.82f);left.rightMargin=dp(12);root.addView(searchPanel,left);
    root.addView(resultsPanel,new LinearLayout.LayoutParams(0,-1,1.18f));
    mStage.addView(root,new LinearLayout.LayoutParams(-1,0,1));cobraTvSectionEntrance(root);refresh[0].run();
    final Button focusKey=firstKey;if(focusKey!=null)focusKey.post(focusKey::requestFocus);
  }''')

    # Search result filtering: exact title first, then prefix, title contains, metadata.
    search_helpers=r'''  private CobraTvVodSearchResult cobraTvVodSearchMatches(boolean series,String rawQuery,String genre,int limit){
    ArrayList<VodItem> catalog=cobraVodCatalog(series),exact=new ArrayList<>(),prefix=new ArrayList<>(),titleHit=new ArrayList<>(),metaHit=new ArrayList<>();
    String q=rawQuery==null?"":rawQuery.trim().toLowerCase(Locale.US);int total=0;
    if(q.isEmpty()){
      ArrayList<VodItem> ranked=cobraVodPopularSubset(catalog);
      for(VodItem item:ranked){if(genre!=null&&!genre.isEmpty()&&!genre.equals(cobraVodGenreLabel(item.category)))continue;total++;if(exact.size()<limit)exact.add(item);}
    }else{
      for(VodItem item:catalog){
        if(genre!=null&&!genre.isEmpty()&&!genre.equals(cobraVodGenreLabel(item.category)))continue;
        String title=item.title==null?"":item.title.toLowerCase(Locale.US),category=item.category==null?"":item.category.toLowerCase(Locale.US),year=item.year==null?"":item.year.toLowerCase(Locale.US);
        int bucket=-1;if(title.equals(q))bucket=0;else if(title.startsWith(q))bucket=1;else if(title.contains(q))bucket=2;
        else if(category.contains(q)||year.contains(q))bucket=3;
        else{LiveSource source=sourceById(item.sourceId);String provider=source==null?"":source.name.toLowerCase(Locale.US);if(provider.contains(q))bucket=3;}
        if(bucket<0)continue;total++;
        ArrayList<VodItem> out=bucket==0?exact:bucket==1?prefix:bucket==2?titleHit:metaHit;if(out.size()<limit)out.add(item);
      }
    }
    ArrayList<VodItem> visible=new ArrayList<>();for(ArrayList<VodItem> bucket:new ArrayList[]{exact,prefix,titleHit,metaHit})for(VodItem item:bucket){if(visible.size()>=limit)break;visible.add(item);}return new CobraTvVodSearchResult(visible,total);
  }

  private void cobraTvRenderVodSearchResults(android.widget.GridLayout grid,TextView count,EditText input,String genre,boolean series,View keyboardFallback){
    if(grid==null||count==null)return;CobraTvVodSearchResult result=cobraTvVodSearchMatches(series,input==null?"":input.getText().toString(),genre,28);
    grid.removeAllViews();count.setText(result.total+" match"+(result.total==1?"":"es")+(result.total>result.items.size()?"  •  showing "+result.items.size():""));
    if(result.items.isEmpty()){
      TextView empty=text(input!=null&&input.length()>0?"No matching titles. Try fewer letters or another genre.":"Start typing or choose a genre.",cobraModeColor("muted"),14,Gravity.CENTER);
      android.widget.GridLayout.LayoutParams ep=new android.widget.GridLayout.LayoutParams();ep.width=dp(isCompact()?360:620);ep.height=dp(120);grid.addView(empty,ep);return;
    }
    int columns=isCompact()?2:4;
    for(int i=0;i<result.items.size();i++){
      final int position=i;View card=cobraVodCard(result.items.get(i),cobraVodContinueObject(result.items.get(i))!=null);card.setTag("cobra_vod_search_result_"+i);card.setId(View.generateViewId());
      card.setOnKeyListener((v,key,event)->{if(event.getAction()==KeyEvent.ACTION_DOWN&&key==KeyEvent.KEYCODE_DPAD_LEFT&&position%columns==0&&keyboardFallback!=null)return keyboardFallback.requestFocus();return false;});
      android.widget.GridLayout.LayoutParams lp=new android.widget.GridLayout.LayoutParams();lp.width=dp(isCompact()?142:160);lp.height=dp(isCompact()?260:292);lp.setMargins(dp(6),dp(5),dp(6),dp(7));grid.addView(card,lp);
    }
  }

'''
    marker2='  private void cobraShowVodCollection(String title,ArrayList<VodItem> items,boolean series){'
    req(s.count(marker2)==1,'search result helper insertion drift')
    s=s.replace(marker2,search_helpers+marker2,1)

    # TV landing order and spacing match the approved mockup: hero, Popular, Recent, Genres.
    s=repl(s,'renderVodBrowse',r'''  private void renderVodBrowse(ArrayList<VodItem> items, boolean series, ArrayList<String> failures) {
    cobraDiscardVodLandingReturn();clearStage(series ? "COBRA • TV SHOWS" : "COBRA • MOVIES");mCobraVodTrimRoles.clear();
    status((series?"TV Shows":"Movies")+"  •  "+items.size()+" titles across enabled providers");
    if(items.isEmpty()){renderVodItems(items,series,failures);return;}
    final ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);
    final LinearLayout page=new LinearLayout(this);page.setOrientation(LinearLayout.VERTICAL);page.setPadding(dp(isCompact()?10:18),dp(7),dp(isCompact()?10:18),dp(30));scroll.addView(page);
    page.addView(cobraVodSectionSearchMenu(series),new LinearLayout.LayoutParams(-1,dp(64)));
    ArrayList<VodItem> featured=cobraVodFeaturedSubset(items);LinearLayout.LayoutParams heroLp=new LinearLayout.LayoutParams(-1,dp(isCompact()?330:390));heroLp.topMargin=dp(8);page.addView(cobraVodHeroCarousel(featured,series),heroLp);
    ArrayList<VodItem> popular=cobraVodPopularSubset(items);cobraAddVodShelf(page,"Popular Now",popular,16,false,series);
    ArrayList<VodItem> recent=cobraVodRecentSubset(items);cobraAddVodShelf(page,"Recent Releases",recent,16,false,series);
    cobraAddVodGenres(page,items,series);
    ArrayList<VodItem> continuing=cobraVodContinueSubset(items);if(!continuing.isEmpty())cobraAddVodShelf(page,"Continue Watching",continuing,14,true,series);
    ArrayList<VodItem> because=cobraVodBecauseYouWatched(items);if(!because.isEmpty())cobraAddVodShelf(page,"Because You Watched…",because,14,false,series);
    ArrayList<VodItem> trending=cobraVodTrendingSubset(items);cobraAddVodShelf(page,series?"Trending Shows":"Trending Movies",trending,14,false,series);
    if(!failures.isEmpty()){TextView note=text("Some providers could not refresh. Existing available titles are shown.",cobraThemeColor("muted",mTheme.muted),12,Gravity.LEFT|Gravity.CENTER_VERTICAL);LinearLayout.LayoutParams np=new LinearLayout.LayoutParams(-1,dp(42));np.topMargin=dp(12);page.addView(note,np);}
    mStage.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));cobraTvSectionEntrance(scroll);
  }''')

    s=repl(s,'cobraVodHeroCarousel',r'''  private View cobraVodHeroCarousel(ArrayList<VodItem> items, boolean series) {
    android.widget.ViewFlipper carousel=new android.widget.ViewFlipper(this);carousel.setAutoStart(false);carousel.setFlipInterval(11000);
    carousel.setInAnimation(this,android.R.anim.fade_in);carousel.setOutAnimation(this,android.R.anim.fade_out);
    int count=Math.min(5,items.size());for(int i=0;i<count;i++)carousel.addView(cobraVodHero(items.get(i),series,carousel),new FrameLayout.LayoutParams(-1,-1));
    if(count>1)carousel.startFlipping();return carousel;
  }''')

    s=repl(s,'cobraVodHeroFocus',r'''  private void cobraVodHeroFocus(View view, android.widget.ViewFlipper carousel) {
    if(view==null||carousel==null)return;
    view.setOnFocusChangeListener((v,focused)->{
      if(focused)carousel.stopFlipping();else if(!carousel.hasFocus()&&carousel.getChildCount()>1)carousel.startFlipping();
      v.animate().cancel();v.setTranslationZ(focused?dp(5):0f);v.animate().scaleX(focused?1.03f:1f).scaleY(focused?1.03f:1f).setDuration(focused?105L:85L).start();
    });
  }''')

    s=repl(s,'cobraVodHero',r'''  private View cobraVodHero(VodItem item, boolean series, android.widget.ViewFlipper carousel) {
    FrameLayout hero=new FrameLayout(this);hero.setClipToOutline(true);hero.setBackground(cobraTvGlassPanelSurface(22,true));
    android.widget.ImageView art=new android.widget.ImageView(this);art.setScaleType(android.widget.ImageView.ScaleType.CENTER_CROP);art.setBackgroundColor(cobraModeColor("panel"));
    hero.addView(art,new FrameLayout.LayoutParams(-1,-1));cobraLoadVodArtwork(art,item.icon);
    View veil=new View(this);android.graphics.drawable.GradientDrawable fade=new android.graphics.drawable.GradientDrawable(
        android.graphics.drawable.GradientDrawable.Orientation.LEFT_RIGHT,new int[]{0xf70a0e15,0xe80a0e15,0xa60a0e15,0x180a0e15});
    veil.setBackground(fade);hero.addView(veil,new FrameLayout.LayoutParams(-1,-1));
    View trim=cobraTrackVodTrim(new View(this),"hero");hero.addView(trim,new FrameLayout.LayoutParams(-1,-1));
    LinearLayout overlay=new LinearLayout(this);overlay.setOrientation(LinearLayout.HORIZONTAL);
    LinearLayout copy=new LinearLayout(this);copy.setOrientation(LinearLayout.VERTICAL);copy.setGravity(Gravity.CENTER_VERTICAL);copy.setPadding(dp(isCompact()?18:28),dp(18),dp(18),dp(18));
    TextView featured=text("FEATURED",cobraModeColor("accent"),10,Gravity.LEFT|Gravity.CENTER_VERTICAL);featured.setLetterSpacing(.16f);copy.addView(featured,new LinearLayout.LayoutParams(-1,dp(24)));
    TextView eyebrow=text(series?"COBRA • TV SHOWS":"COBRA • MOVIES",0xffb9dfff,11,Gravity.LEFT);eyebrow.setLetterSpacing(.10f);copy.addView(eyebrow,new LinearLayout.LayoutParams(-1,dp(27)));
    TextView title=text(item.title,Color.WHITE,isCompact()?29:38,Gravity.LEFT|Gravity.CENTER_VERTICAL);title.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));title.setMaxLines(2);title.setEllipsize(android.text.TextUtils.TruncateAt.END);copy.addView(title,new LinearLayout.LayoutParams(-1,-2));
    LiveSource source=sourceById(item.sourceId);String provider=source==null?"Provider":source.name;String meta=item.category+"  •  "+provider;
    if(!item.year.isEmpty())meta+="  •  "+item.year;if(item.rating>0.0)meta+="  •  "+String.format(Locale.US,"%.1f ★",item.rating);
    TextView metadata=text(meta,0xffcbd7e5,12,Gravity.LEFT|Gravity.CENTER_VERTICAL);metadata.setMaxLines(1);metadata.setEllipsize(android.text.TextUtils.TruncateAt.END);copy.addView(metadata,new LinearLayout.LayoutParams(-1,dp(38)));
    TextView hint=text(series?"Browse seasons, episodes and related series from your enabled providers.":"Watch now or open details for cast, collection and related titles.",0xff9fb0c4,11,Gravity.LEFT);hint.setMaxLines(2);copy.addView(hint,new LinearLayout.LayoutParams(-1,dp(42)));
    LinearLayout actions=new LinearLayout(this);actions.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);
    Button play=action(series?"Browse Episodes":"▶  Play");play.setAllCaps(false);play.setOnClickListener(v->{carousel.stopFlipping();if(item.series)openSeries(item);else playMovie(item);});
    Button details=action("More Info");details.setAllCaps(false);details.setOnClickListener(v->{carousel.stopFlipping();cobraShowVodDetails(item);});
    Button list=action(cobraVodWatchlistContains(item)?"✓ My List":"+ My List");list.setAllCaps(false);list.setOnClickListener(v->{carousel.stopFlipping();toggleWatchlist(item);list.setText(cobraVodWatchlistContains(item)?"✓ My List":"+ My List");});
    cobraVodHeroFocus(play,carousel);cobraVodHeroFocus(details,carousel);cobraVodHeroFocus(list,carousel);
    actions.addView(play,new LinearLayout.LayoutParams(0,dp(50),1));LinearLayout.LayoutParams a2=new LinearLayout.LayoutParams(0,dp(50),1);a2.leftMargin=dp(9);actions.addView(details,a2);
    LinearLayout.LayoutParams a3=new LinearLayout.LayoutParams(0,dp(50),1);a3.leftMargin=dp(9);actions.addView(list,a3);copy.addView(actions,new LinearLayout.LayoutParams(-1,dp(54)));
    overlay.addView(copy,new LinearLayout.LayoutParams(0,-1,isCompact()?.72f:.58f));overlay.addView(new View(this),new LinearLayout.LayoutParams(0,-1,isCompact()?.28f:.42f));
    hero.addView(overlay,new FrameLayout.LayoutParams(-1,-1));return hero;
  }''')

    s=repl(s,'cobraAddVodShelf',r'''  private void cobraAddVodShelf(LinearLayout page,String title,ArrayList<VodItem> items,int limit,
      boolean progress,boolean series) {
    if(items==null||items.isEmpty())return;
    LinearLayout heading=new LinearLayout(this);heading.setGravity(Gravity.CENTER_VERTICAL);
    View edge=cobraTrackVodTrim(new View(this),"section");LinearLayout.LayoutParams edgeLp=new LinearLayout.LayoutParams(dp(4),dp(25));edgeLp.rightMargin=dp(9);heading.addView(edge,edgeLp);
    TextView label=text(title,cobraModeColor("text"),19,Gravity.LEFT|Gravity.CENTER_VERTICAL);label.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));heading.addView(label,new LinearLayout.LayoutParams(0,dp(46),1));
    TextView more=text("See all  ›",cobraModeColor("accent"),12,Gravity.RIGHT|Gravity.CENTER_VERTICAL);more.setFocusable(true);more.setClickable(true);more.setContentDescription("See all "+title);more.setOnClickListener(v->cobraShowVodCollection(title,items,series));cobraTvVodFocusPolish(more,1.03f);
    heading.addView(more,new LinearLayout.LayoutParams(dp(104),dp(46)));LinearLayout.LayoutParams headLp=new LinearLayout.LayoutParams(-1,-2);headLp.topMargin=dp(18);page.addView(heading,headLp);
    android.widget.HorizontalScrollView rail=new android.widget.HorizontalScrollView(this);rail.setHorizontalScrollBarEnabled(false);rail.setFillViewport(false);rail.setClipToPadding(false);
    LinearLayout row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);row.setPadding(dp(4),dp(2),dp(18),dp(8));rail.addView(row,new android.widget.HorizontalScrollView.LayoutParams(-2,-2));
    int count=Math.min(limit,items.size());for(int i=0;i<count;i++)row.addView(cobraVodCard(items.get(i),progress),cobraVodCardParams());
    page.addView(rail,new LinearLayout.LayoutParams(-1,dp(isCompact()?284:322)));
  }''')

    s=repl(s,'cobraVodCardParams',r'''  private LinearLayout.LayoutParams cobraVodCardParams(){
    LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(dp(isCompact()?142:164),-1);p.rightMargin=dp(12);return p;
  }''')

    s=repl(s,'cobraVodCard',r'''  private View cobraVodCard(VodItem item,boolean progress) {
    LinearLayout card=new LinearLayout(this);card.setOrientation(LinearLayout.VERTICAL);card.setFocusable(true);card.setClickable(true);card.setPadding(dp(3),dp(3),dp(3),dp(5));
    card.setBackground(cobraTvGlassRowSurface(14));card.setContentDescription(item.title+", "+item.category);cobraTvVodFocusPolish(card,1.045f);
    android.widget.ImageView poster=new android.widget.ImageView(this);poster.setScaleType(android.widget.ImageView.ScaleType.CENTER_CROP);poster.setBackground(surface(cobraModeColor("panel"),13,cobraModeColor("line"),1));
    card.addView(poster,new LinearLayout.LayoutParams(-1,dp(isCompact()?198:226)));cobraLoadVodArtwork(poster,item.icon);
    TextView name=text(item.title,cobraModeColor("text"),13,Gravity.LEFT|Gravity.CENTER_VERTICAL);name.setTypeface(Typeface.create("sans-serif-medium",Typeface.NORMAL));name.setMaxLines(2);name.setEllipsize(android.text.TextUtils.TruncateAt.END);name.setPadding(dp(5),0,dp(4),0);card.addView(name,new LinearLayout.LayoutParams(-1,dp(44)));
    String sub=progress?cobraVodContinueLabel(item):cobraVodCardMeta(item);if(!sub.isEmpty()){TextView line=text(sub,cobraModeColor("muted"),10,Gravity.LEFT|Gravity.CENTER_VERTICAL);line.setPadding(dp(5),0,dp(4),0);line.setMaxLines(1);line.setEllipsize(android.text.TextUtils.TruncateAt.END);card.addView(line,new LinearLayout.LayoutParams(-1,dp(23)));}
    if(progress){int pct=cobraVodProgressPercent(item);if(pct>0){android.widget.ProgressBar bar=new android.widget.ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);bar.setMax(100);bar.setProgress(pct);LinearLayout.LayoutParams bp=new LinearLayout.LayoutParams(-1,dp(3));bp.leftMargin=dp(5);bp.rightMargin=dp(5);card.addView(bar,bp);}}
    card.setOnClickListener(v->cobraShowVodDetails(item));card.setOnLongClickListener(v->{toggleWatchlist(item);return true;});return cobraTrackVodTrim(card,"card");
  }''')

    s=repl(s,'cobraAddVodGenres',r'''  private void cobraAddVodGenres(LinearLayout page,ArrayList<VodItem> items,boolean series) {
    LinkedHashMap<String,ArrayList<VodItem>> buckets=cobraVodGenreBuckets(items);if(buckets.isEmpty())return;
    LinearLayout heading=new LinearLayout(this);heading.setGravity(Gravity.CENTER_VERTICAL);View edge=cobraTrackVodTrim(new View(this),"section");
    LinearLayout.LayoutParams edgeLp=new LinearLayout.LayoutParams(dp(4),dp(25));edgeLp.rightMargin=dp(9);heading.addView(edge,edgeLp);
    TextView label=text("Genres",cobraModeColor("text"),19,Gravity.LEFT|Gravity.CENTER_VERTICAL);label.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));heading.addView(label,new LinearLayout.LayoutParams(0,dp(46),1));
    if(buckets.size()>12){TextView more=text("See all  ›",cobraModeColor("accent"),12,Gravity.RIGHT|Gravity.CENTER_VERTICAL);more.setFocusable(true);more.setClickable(true);more.setOnClickListener(v->cobraShowVodGenrePicker(buckets,series));cobraTvVodFocusPolish(more,1.03f);heading.addView(more,new LinearLayout.LayoutParams(dp(104),dp(46)));}
    LinearLayout.LayoutParams headLp=new LinearLayout.LayoutParams(-1,-2);headLp.topMargin=dp(18);page.addView(heading,headLp);
    LinearLayout grid=new LinearLayout(this);grid.setOrientation(LinearLayout.VERTICAL);int columns=isCompact()?2:4,index=0,shown=0;LinearLayout row=null;
    for(Map.Entry<String,ArrayList<VodItem>> entry:buckets.entrySet()){
      if(shown++>=12)break;if(index%columns==0){row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);grid.addView(row,new LinearLayout.LayoutParams(-1,dp(76)));}
      Button genre=action(entry.getKey());genre.setAllCaps(false);genre.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);genre.setTextSize(12);genre.setPadding(dp(13),0,dp(10),0);cobraTrackVodTrim(genre,"genre");cobraTvVodFocusPolish(genre,1.035f);
      final String genreName=entry.getKey();final ArrayList<VodItem> genreItems=entry.getValue();genre.setOnClickListener(v->cobraShowVodCollection(genreName,genreItems,series));
      LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(0,dp(66),1);lp.setMargins(dp(4),dp(4),dp(4),dp(4));row.addView(genre,lp);index++;
    }
    page.addView(grid,new LinearLayout.LayoutParams(-1,-2));
  }''')

    # Polish collection/series entrances without changing their behavior.
    collection=member(s,'cobraRenderVodCollection')
    collection=once(collection,
      '    mStage.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));cobraRefreshVodAmbientTrim();',
      '    mStage.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));cobraRefreshVodAmbientTrim();cobraTvSectionEntrance(scroll);',
      'collection entrance')
    s=repl(s,'cobraRenderVodCollection',collection)

    series_browser=member(s,'cobraShowSeriesBrowser')
    series_browser=once(series_browser,
      '    mStage.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));cobraRefreshVodAmbientTrim();',
      '    mStage.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));cobraRefreshVodAmbientTrim();cobraTvSectionEntrance(scroll);',
      'series entrance')
    s=repl(s,'cobraShowSeriesBrowser',series_browser)

    # Live TV: preserve all structure/behavior; add only a one-time section entrance transition.
    live=member(s,'cobraOpenLiveTv')
    live=once(live,
      '    if(mCobraGuideShell!=null)mCobraGuideShell.post(this::cobraTvAnimateGroupPanelIn);',
      '    if(mCobraGuideShell!=null)mCobraGuideShell.post(()->{cobraTvAnimateGroupPanelIn();cobraTvSectionEntrance(mCobraGuideShell);});',
      'Live TV one-shot polish')
    s=repl(s,'cobraOpenLiveTv',live)

    # Preservation gates.
    for n,h in protected.items():req(hb(member(s,n))==h,'Protected Live TV/player/section method changed: '+n)
    req(hb(member(s,'CobraTvPlayingDot','class'))==dot_hash,'RC16 pulsing dot changed')
    req('COBRA_SECTION_OWNER' in s and 'tv_section_owner' not in s,'Section owner constants drift')
    req('cobra_movies_search' in s and 'cobra_shows_search' in s,'Dedicated search tags lost')
    req('On-screen keyboard' in s and 'cobra_vod_search_result_0' in s,'TV search UI missing')
    req('NORMAL_PULSE_MS=1320L' in s and 'CINEMA_PULSE_MS=1900L' in s,'Pulsing dot cadence lost')
    req('AMBIENT MODE  •' not in s,'TV Ambient Mode returned')
    req('KEYCODE_DPAD_RIGHT' in member(s,'cobraTvHandleDrawerKey') and 'KEYCODE_DPAD_LEFT' in member(s,'cobraTvHandleDrawerKey'),'Live TV drawer key contract lost')
    req('KEYCODE_DPAD_LEFT' in member(s,'cobraDirectory') and 'KEYCODE_DPAD_RIGHT' in member(s,'cobraDirectory'),'Live TV directory key contract lost')
    req('cobraOnDemandPlayer' in s and 'Back to Movies' in s and 'Back to Shows' in s,'RC17 VOD player cleanup lost')
    path.write_text(s)
    return hb(before),sha(path)

def apply(shell:Path):
    receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text())
    req(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,'Expected exact passed RC17 parent')
    req(receipt.get('chooser_card_settings_removed') is True,'RC17 chooser cleanup missing')
    req(receipt.get('tv_section_owner_persistent') is True and receipt.get('tv_smart_return_cannot_override_vod_owner') is True,'RC17 section ownership missing')
    req(receipt.get('tv_vod_channels_control_removed') is True and receipt.get('tv_vod_multiview_control_removed') is True,'RC17 VOD player cleanup missing')
    req(receipt.get('tv_grid_pulsing_playing_dot') is True and receipt.get('tv_playing_dot_actual_session') is True,'RC16 pulsing dot missing')
    req(receipt.get('tv_ambient_mode_retired') is True and receipt.get('tv_glass_system') is True,'TV glass/Ambient contract missing')
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
      tv_movies_shows_visual_target='approved cinematic TV mockup',
      tv_movies_tv_first_refinement=True,tv_shows_tv_first_refinement=True,
      tv_vod_hero_cinematic=True,tv_vod_popular_first=True,tv_vod_recent_second=True,tv_vod_genres_third=True,
      tv_vod_larger_poster_cards=True,tv_vod_focus_animation_ms=105,tv_vod_section_transition_ms=125,
      tv_movies_full_search=True,tv_shows_full_search=True,tv_vod_search_live_narrowing=True,
      tv_vod_search_on_screen_keyboard=True,tv_vod_search_android_text_input=True,
      tv_vod_search_exact_title_priority=True,tv_vod_search_genre_filters=True,
      tv_vod_search_debounce_ms=110,tv_vod_search_visible_result_cap=28,
      tv_vod_search_focus_restore=True,tv_vod_search_section_scoped=True,
      tv_vod_collection_entrance_polish=True,tv_series_browser_entrance_polish=True,
      tv_live_end_to_end_polish=True,tv_live_structure_unchanged=True,tv_live_section_transition_ms=125,
      tv_remote_focus_audited=True,tv_motion_lightweight=True,tv_real_time_blur=False,
      tv_section_owner_persistent=True,tv_movies_persistent_until_drawer_change=True,tv_shows_persistent_until_drawer_change=True,
      tv_right_select_scope='live-tv-only',tv_left_back_scope='live-tv-drawer-directory-only',
      tv_vod_channels_control_removed=True,tv_vod_multiview_control_removed=True,tv_vod_live_timeline_removed=True,
      tv_grid_pulsing_playing_dot=True,tv_playing_dot_actual_session=True,
      tv_ambient_mode_retired=True,tv_ambient_dynamic_layering=False,tv_glass_system=True,
      tv_mini_player_preserved=True,tv_preview_engine_preserved=True,tv_multiview_row_focus_visible=True,
      multiview_two_to_one_session_preserved=True,mobile_parent_untouched=True,native_engine_rebuilt=False,
      playback_engine_unchanged=True
    )
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for name,row in receipt['files'].items():req(sha(shell/name)==row['after'],'Final receipt drift '+name)

    out=Path('audit238');out.mkdir(exist_ok=True)
    (out/'tv-movies-shows-source.json').write_text(json.dumps({
      'build':VERSION,'version_name':NEW_NAME,'parent_build':OLD_VERSION,'target_abi':'armeabi-v7a',
      'activity_before_sha256':before,'activity_after_sha256':after,
      'visual_target':'approved RC18 cinematic Movies mockup; TV Shows matching language',
      'landing_order':['Hero','Popular Now','Recent Releases','Genres','Continue Watching','Because You Watched','Trending'],
      'search':{'section_scoped':True,'live_narrowing':True,'keyboard':'A-Z + 0-9 + space/backspace/clear','android_text_input':True,'genre_filters':True,'exact_title_priority':True,'debounce_ms':110,'visible_cap':28,'focus_restore':True},
      'motion':{'vod_focus_ms':105,'section_transition_ms':125,'real_time_blur':False},
      'live_tv':{'structure_unchanged':True,'features_preserved':True,'one_shot_transition_only':True},
      'rc17_section_owner_preserved':True,'rc17_vod_player_cleanup_preserved':True,'rc16_pulsing_dot_preserved':True,
      'native_engine_rebuilt':False,'playback_engine_unchanged':True,'mobile_fold_untouched':True,'physical_device_verified':False
    },indent=2,sort_keys=True)+'\n')
    print('PASS: 2103238 RC18 Movies/Shows TV refinement + whole-Cobra polish applied over exact passed RC17')

def main():
    p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);a=p.parse_args();apply(a.shell)
if __name__=='__main__':main()
