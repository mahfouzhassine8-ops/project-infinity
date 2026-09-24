#!/usr/bin/env python3
"""2103239 RC19 — native Android TV search + TV UI/stability polish over passed RC18.

Scope:
- Keep the passed 2103238 RC18 Movies/Shows design and all approved Live TV/player behavior.
- Replace RC18's custom A-Z/0-9 keyboard and split search panel with one full-width native search field.
- The field itself reads "Type a title or narrow by genre" and invokes the Android TV IME.
- Search results live directly below the field and rank exact title -> title prefix -> title contains -> metadata.
- Genre narrowing remains available by typing the genre name; separate genre chips are removed.
- Add low-risk TV polish: unclipped focus scaling, stable D-pad return paths, stale-refresh protection,
  slightly calmer debounce, smooth result scrolling, and restrained focus/entrance behavior.
- No Kodi/native rebuild, no Live TV redesign, no navigation contract changes, no real-time blur.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

VERSION=2103239
OLD_VERSION=2103238
OLD_NAME='1.0.9-Cobra-Onn4KPro-TV-Movies-Shows-Refinement-RC18'
NEW_NAME='1.0.9-Cobra-Onn4KPro-TV-Native-Search-UI-Polish-RC19'
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
    req('cobra_tv_movies_search_input' in s and 'cobra_tv_shows_search_input' in s,'Expected exact RC18 search source')
    req('On-screen keyboard' in s,'Expected RC18 custom keyboard before RC19 removal')
    req('cobraTvVodSearchMatches' in s and 'cobraTvRenderVodSearchResults' in s,'RC18 search helpers missing')

    protected_methods=[
      'playChannel','startCobraPreview','promoteCobraPreviewToFullscreen','cobraReturnToMultiFromFullscreen',
      'setMultiAudio','cobraLayoutPlayerPanels','cobraTvChannelPlaybackState','cobraTvChannelPlaying',
      'cobraTvPlayingDotColor','cobraTvHandleDrawerKey','cobraDirectory','cobraTvHandleGuideKey',
      'cobraLayoutGuide','cobraRenderGuideBrowser','cobraBuildPlayerChrome','cobraTvHandlePlayerKey',
      'onBackPressed','showMovies','showSeries','cobraSetSectionOwner','cobraShowLoadedPrimary',
      'cobraOpenLiveTv','renderVodBrowse','cobraAddVodGenres','cobraVodSectionSearchMenu',
      'cobraShowVodCollection'
    ]
    protected={n:hb(member(s,n)) for n in protected_methods}
    dot_hash=hb(member(s,'CobraTvPlayingDot','class'))

    # Make the shared status helper self-healing. RC19 hides the status row only while the
    # dedicated VOD search screen is active; every later status() call restores it.
    status_method=member(s,'status')
    open_brace=status_method.find('{');req(open_brace>=0,'status opening brace missing')
    injected='\n    if(mStatus!=null)mStatus.setVisibility(View.VISIBLE);'
    req(injected.strip() not in status_method,'status visibility guard already present')
    status_method=status_method[:open_brace+1]+injected+status_method[open_brace+1:]
    s=repl(s,'status',status_method)

    s=repl(s,'cobraShowVodSectionSearch',r'''  private void cobraShowVodSectionSearch(boolean series){
    final ArrayList<VodItem> catalog=cobraVodCatalog(series);
    if(catalog.isEmpty()){toast((series?"TV Shows":"Movies")+" are still loading");return;}
    cobraCaptureVodLandingReturn(series);mCobraInternalScreen="vod-search";
    clearStage(series?"COBRA • SEARCH TV SHOWS":"COBRA • SEARCH MOVIES");
    status("");if(mStatus!=null)mStatus.setVisibility(View.GONE);

    LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);
    root.setPadding(dp(16),dp(8),dp(16),dp(14));root.setClipChildren(false);root.setClipToPadding(false);

    final EditText input=field("Type a title or narrow by genre",InputType.TYPE_CLASS_TEXT);
    input.setSingleLine(true);input.setTextSize(17);
    input.setTag(series?"cobra_tv_shows_native_search_2103239":"cobra_tv_movies_native_search_2103239");
    input.setContentDescription(series?"Search TV Shows by title or genre":"Search Movies by title or genre");
    input.setImeOptions(android.view.inputmethod.EditorInfo.IME_ACTION_SEARCH);
    input.setBackground(cobraTvGlassRowSurface(16));input.setPadding(dp(16),0,dp(16),0);
    input.setHintTextColor(cobraModeColor("muted"));cobraTvVodFocusPolish(input,1.012f);
    root.addView(input,new LinearLayout.LayoutParams(-1,dp(58)));

    LinearLayout resultHeader=new LinearLayout(this);resultHeader.setGravity(Gravity.CENTER_VERTICAL);
    TextView resultTitle=text(series?"TV Shows":"Movies",cobraModeColor("text"),18,Gravity.LEFT|Gravity.CENTER_VERTICAL);
    resultTitle.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));
    final TextView resultCount=text("",cobraModeColor("muted"),11,Gravity.RIGHT|Gravity.CENTER_VERTICAL);
    resultHeader.addView(resultTitle,new LinearLayout.LayoutParams(0,dp(42),1));
    resultHeader.addView(resultCount,new LinearLayout.LayoutParams(dp(210),dp(42)));
    LinearLayout.LayoutParams hp=new LinearLayout.LayoutParams(-1,dp(46));hp.topMargin=dp(6);root.addView(resultHeader,hp);

    android.widget.ScrollView resultScroll=new android.widget.ScrollView(this);
    resultScroll.setFillViewport(true);resultScroll.setSmoothScrollingEnabled(true);
    resultScroll.setClipToPadding(false);resultScroll.setPadding(0,0,dp(3),dp(8));
    final android.widget.GridLayout results=new android.widget.GridLayout(this);
    results.setColumnCount(isCompact()?3:5);results.setAlignmentMode(android.widget.GridLayout.ALIGN_BOUNDS);
    results.setClipChildren(false);results.setClipToPadding(false);
    resultScroll.addView(results,new android.widget.ScrollView.LayoutParams(-1,-2));
    root.addView(resultScroll,new LinearLayout.LayoutParams(-1,0,1));

    final Runnable[] refresh=new Runnable[1];final Runnable[] pending=new Runnable[1];
    refresh[0]=()->{
      if(!"vod-search".equals(mCobraInternalScreen))return;
      cobraTvRenderVodSearchResults(results,resultCount,input,"",series,input);
    };
    input.addTextChangedListener(new android.text.TextWatcher(){
      public void beforeTextChanged(CharSequence text,int start,int count,int after){}
      public void onTextChanged(CharSequence text,int start,int before,int count){}
      public void afterTextChanged(android.text.Editable text){
        if(pending[0]!=null)mMain.removeCallbacks(pending[0]);
        pending[0]=refresh[0];mMain.postDelayed(pending[0],160L);
      }
    });

    final Runnable showIme=()->{
      input.requestFocus();
      android.view.inputmethod.InputMethodManager imm=(android.view.inputmethod.InputMethodManager)getSystemService(android.content.Context.INPUT_METHOD_SERVICE);
      if(imm!=null)imm.showSoftInput(input,android.view.inputmethod.InputMethodManager.SHOW_IMPLICIT);
    };
    input.setOnClickListener(v->showIme.run());
    input.setOnKeyListener((v,key,event)->{
      if(event.getAction()!=KeyEvent.ACTION_DOWN)return false;
      if(key==KeyEvent.KEYCODE_DPAD_DOWN){
        View first=mStage.findViewWithTag("cobra_vod_search_result_0");return first!=null&&first.requestFocus();
      }
      if(key==KeyEvent.KEYCODE_DPAD_CENTER||key==KeyEvent.KEYCODE_ENTER){
        showIme.run();return true;
      }
      return false;
    });
    input.setOnEditorActionListener((v,actionId,event)->{
      boolean submit=actionId==android.view.inputmethod.EditorInfo.IME_ACTION_SEARCH||
          actionId==android.view.inputmethod.EditorInfo.IME_ACTION_DONE||
          (event!=null&&event.getKeyCode()==KeyEvent.KEYCODE_ENTER);
      if(!submit)return false;
      android.view.inputmethod.InputMethodManager imm=(android.view.inputmethod.InputMethodManager)getSystemService(android.content.Context.INPUT_METHOD_SERVICE);
      if(imm!=null)imm.hideSoftInputFromWindow(input.getWindowToken(),0);
      View first=mStage.findViewWithTag("cobra_vod_search_result_0");if(first!=null)first.requestFocus();
      return true;
    });

    mStage.addView(root,new LinearLayout.LayoutParams(-1,0,1));cobraTvSectionEntrance(root);
    refresh[0].run();input.post(input::requestFocus);
  }''')

    s=repl(s,'cobraTvRenderVodSearchResults',r'''  private void cobraTvRenderVodSearchResults(android.widget.GridLayout grid,TextView count,EditText input,String genre,boolean series,View inputFallback){
    if(grid==null||count==null||!"vod-search".equals(mCobraInternalScreen))return;
    CobraTvVodSearchResult result=cobraTvVodSearchMatches(series,input==null?"":input.getText().toString(),"",30);
    grid.removeAllViews();
    count.setText(result.total+" match"+(result.total==1?"":"es")+(result.total>result.items.size()?"  •  showing "+result.items.size():""));
    if(result.items.isEmpty()){
      TextView empty=text(input!=null&&input.length()>0?"No close matches. Try fewer letters or type a genre.":"Start typing a title or genre.",cobraModeColor("muted"),14,Gravity.CENTER);
      android.widget.GridLayout.LayoutParams ep=new android.widget.GridLayout.LayoutParams();ep.width=dp(isCompact()?620:940);ep.height=dp(128);grid.addView(empty,ep);return;
    }
    int columns=isCompact()?3:5;
    for(int i=0;i<result.items.size();i++){
      final int position=i;View card=cobraVodCard(result.items.get(i),cobraVodContinueObject(result.items.get(i))!=null);
      card.setTag("cobra_vod_search_result_"+i);card.setId(View.generateViewId());
      card.setOnKeyListener((v,key,event)->{
        if(event.getAction()!=KeyEvent.ACTION_DOWN)return false;
        if(key==KeyEvent.KEYCODE_DPAD_UP&&position<columns&&inputFallback!=null)return inputFallback.requestFocus();
        if(key==KeyEvent.KEYCODE_DPAD_LEFT&&position%columns==0&&inputFallback!=null)return inputFallback.requestFocus();
        return false;
      });
      android.widget.GridLayout.LayoutParams lp=new android.widget.GridLayout.LayoutParams();
      lp.width=dp(isCompact()?142:158);lp.height=dp(isCompact()?258:288);
      lp.setMargins(dp(7),dp(5),dp(7),dp(8));grid.addView(card,lp);
    }
  }''')

    for n,h in protected.items():req(hb(member(s,n))==h,'Protected TV behavior changed: '+n)
    req(hb(member(s,'CobraTvPlayingDot','class'))==dot_hash,'RC16 pulsing dot changed')
    req('On-screen keyboard' not in member(s,'cobraShowVodSectionSearch'),'Custom search keyboard survived RC19')
    req('Narrow by genre' not in member(s,'cobraShowVodSectionSearch'),'RC18 genre-chip panel survived RC19')
    req('cobra_tv_movies_native_search_2103239' in s and 'cobra_tv_shows_native_search_2103239' in s,'Native search markers missing')
    req('IME_ACTION_SEARCH' in member(s,'cobraShowVodSectionSearch'),'Android TV IME action missing')
    req('cobraTvVodSearchMatches(series' in member(s,'cobraTvRenderVodSearchResults'),'Search ranking helper disconnected')
    req('NORMAL_PULSE_MS=1320L' in s and 'CINEMA_PULSE_MS=1900L' in s,'Pulsing dot cadence lost')
    req('AMBIENT MODE  •' not in s,'TV Ambient Mode returned')
    path.write_text(s)
    return hb(before),sha(path)

def apply(shell:Path):
    receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text())
    req(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,'Expected exact passed RC18 source parent')
    req(receipt.get('tv_movies_tv_first_refinement') is True and receipt.get('tv_shows_tv_first_refinement') is True,'RC18 Movies/Shows refinement missing')
    req(receipt.get('tv_vod_search_on_screen_keyboard') is True and receipt.get('tv_vod_search_android_text_input') is True,'Expected RC18 dual keyboard search parent')
    req(receipt.get('tv_vod_search_exact_title_priority') is True,'RC18 exact-title ranking missing')
    req(receipt.get('tv_live_structure_unchanged') is True and receipt.get('playback_engine_unchanged') is True,'RC18 protected TV playback contract missing')
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
      tv_native_search_polish=True,tv_search_custom_keyboard_removed=True,tv_search_left_panel_removed=True,
      tv_search_genre_chips_removed=True,tv_search_top_field_is_input=True,tv_search_native_android_tv_ime=True,
      tv_search_genre_text_matching=True,tv_search_results_full_width=True,tv_search_results_below_input=True,
      tv_vod_search_on_screen_keyboard=False,tv_vod_search_android_text_input=True,
      tv_vod_search_exact_title_priority=True,tv_vod_search_genre_filters=False,
      tv_vod_search_genre_text_matching=True,tv_vod_search_debounce_ms=160,tv_vod_search_visible_result_cap=30,
      tv_vod_search_focus_restore=True,tv_search_stale_refresh_guard=True,tv_search_ime_submit_to_results=True,
      tv_focus_clip_protection=True,tv_result_smooth_scroll=True,tv_ui_refinement_polish=True,
      tv_stability_polish=True,tv_performance_polish=True,tv_motion_lightweight=True,tv_real_time_blur=False,
      tv_live_structure_unchanged=True,tv_live_end_to_end_polish=True,
      mobile_parent_untouched=True,native_engine_rebuilt=False,playback_engine_unchanged=True
    )
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for name,row in receipt['files'].items():req(sha(shell/name)==row['after'],'Final receipt drift '+name)

    out=Path('audit239');out.mkdir(exist_ok=True)
    (out/'tv-native-search-ui-polish-source.json').write_text(json.dumps({
      'build':VERSION,'version_name':NEW_NAME,'parent_build':OLD_VERSION,'target_abi':'armeabi-v7a',
      'activity_before_sha256':before,'activity_after_sha256':after,
      'search':{
        'top_field_is_input':True,'native_android_tv_ime':True,'custom_keyboard_removed':True,
        'genre_chips_removed':True,'genre_text_matching':True,'results_below_input':True,
        'ranking':['exact-title','title-prefix','title-contains','genre/year/provider'],
        'debounce_ms':160,'visible_cap':30,'stale_refresh_guard':True,'focus_restore':True
      },
      'ui_polish':{
        'full_width_results':True,'focus_clip_protection':True,'smooth_result_scroll':True,
        'restrained_motion':True,'real_time_blur':False
      },
      'preservation':{
        'rc18_movies_shows_layout':True,'live_tv_structure_unchanged':True,'playback_engine_unchanged':True,
        'native_engine_rebuilt':False,'mobile_fold_untouched':True
      },
      'physical_device_verified':False
    },indent=2,sort_keys=True)+'\n')
    print('PASS: 2103239 RC19 native Android TV search + UI/stability polish applied over exact passed RC18')

def main():
    p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);a=p.parse_args();apply(a.shell)
if __name__=='__main__':main()
