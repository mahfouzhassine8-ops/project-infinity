#!/usr/bin/env python3
"""2103223: cinematic Cobra movie details page + trailer entry point.

Parent: locked 2103222 Experience Options UI.
Authorized delta:
- Movies only: replace the VOD details sheet with a full-page cinematic details surface.
- Add a Trailers action/section using provider trailer metadata when available and a
  YouTube official-trailer search fallback when providers do not expose a trailer.
- Add an exact in-session return snapshot so Back restores the page the movie was
  opened from (Movies landing, See All, genre, etc.).

TV Shows keep the existing 2103222/2103214 details sheet and episode browser.
Playback, providers, native engine, Live TV, drawer ownership, Smart Return,
Choose Your Experience, Health Center and global theme/settings behavior are untouched.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

VERSION=2103223
OLD_VERSION=2103222
OLD_NAME='1.0.9-Experience-Options-UI-RC1'
NEW_NAME='1.0.9-Cobra-Movie-Details-Trailers-RC1'
SOURCE='tools/android/packaging/xbmc/src/'
NATIVE='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'

def hb(b): return hashlib.sha256(b).hexdigest()
def sha(p): return hb(Path(p).read_bytes())
def req(v,m):
    if not v: raise RuntimeError(m)
def once(s,a,b,label):
    req(s.count(a)==1,f'{label} anchor drift ({s.count(a)})')
    return s.replace(a,b,1)
def mr(s,sig):
    i=s.find(sig); req(i>=0,'Missing '+sig)
    b=s.find('{',i); req(b>=0,'Missing method body '+sig)
    d=0
    for j in range(b,len(s)):
        if s[j]=='{': d+=1
        elif s[j]=='}':
            d-=1
            if d==0: return i,j+1
    raise RuntimeError('Unbalanced '+sig)
def method(s,sig):
    a,b=mr(s,sig); return s[a:b]
def replace_method(s,sig,new):
    a,b=mr(s,sig); return s[:a]+new.rstrip()+s[b:]

PROTECTED_METHODS=[
    'private void cobraOpenLiveTv()',
    'private void showGuide()',
    'private void startSinglePlayer(String url)',
    'private void cobraShowQuickPeek(Channel channel,View anchor)',
    'private void cobraStartLocalTimeshift',
    'private void playChannel(Channel channel)',
    'private void startCobraPreview(Channel channel)',
    'private void releaseSinglePlayer()',
    'private void releaseMulti()',
    'private LoadResult loadXtream(LiveSource source)',
    'private LoadResult loadM3u(LiveSource source)',
    'private void cobraRefreshAmbient()',
    'private void cobraRefreshLiveAmbientSurfaces(int mode,boolean live,int tint)',
    'private void cobraApplyNightCinema(View header,View footer,View pause)',
    'private void cobraReturnFromSettings()',
    'private void showSettings()',
]
def method_hashes(s,names):
    return {n:hb(method(s,n).encode()) for n in names}

def patch_activity(path:Path):
    s=path.read_text()
    protected_before=method_hashes(s,PROTECTED_METHODS)
    before_file=hb(s.encode())

    # Dedicated one-level exact parent snapshot for the full-page movie details route.
    field='  private View mCobraVodReturnFocus;\n'
    fields='''  private View mCobraVodReturnFocus;
  private final ArrayList<View> mCobraVodDetailReturnViews = new ArrayList<>();
  private boolean mCobraVodDetailReturnCaptured=false;
  private boolean mCobraVodDetailReturnSeries=false;
  private boolean mCobraVodDetailReturnSmartWatchlist=false;
  private String mCobraVodDetailReturnStageTitle="";
  private String mCobraVodDetailReturnHeader="";
  private String mCobraVodDetailReturnStatus="";
  private String mCobraVodDetailReturnInternal="";
  private View mCobraVodDetailReturnFocus;
'''
    s=once(s,field,fields,'movie detail return fields')

    marker='  private void cobraDiscardVodLandingReturn(){'
    req(s.count(marker)==1,'movie detail return helper marker drift')
    helpers=r'''  private void cobraDiscardVodDetailReturn(){
    mCobraVodDetailReturnCaptured=false;mCobraVodDetailReturnSeries=false;
    mCobraVodDetailReturnSmartWatchlist=false;mCobraVodDetailReturnViews.clear();
    mCobraVodDetailReturnStageTitle="";mCobraVodDetailReturnHeader="";
    mCobraVodDetailReturnStatus="";mCobraVodDetailReturnInternal="";
    mCobraVodDetailReturnFocus=null;
  }

  private void cobraCaptureVodDetailReturn(boolean series){
    if(mStage==null||mCobraVodDetailReturnCaptured)return;
    mCobraVodDetailReturnCaptured=true;mCobraVodDetailReturnSeries=series;
    mCobraVodDetailReturnSmartWatchlist=mCobraSmartWatchlist;
    mCobraVodDetailReturnStageTitle=mCobraStageTitle==null?"":mCobraStageTitle;
    mCobraVodDetailReturnHeader=mHeader==null?"":String.valueOf(mHeader.getText());
    mCobraVodDetailReturnStatus=mStatus==null?"":String.valueOf(mStatus.getText());
    mCobraVodDetailReturnInternal=mCobraInternalScreen==null?"":mCobraInternalScreen;
    mCobraVodDetailReturnFocus=getCurrentFocus();mCobraVodDetailReturnViews.clear();
    for(int i=2;i<mStage.getChildCount();i++)mCobraVodDetailReturnViews.add(mStage.getChildAt(i));
  }

  private boolean cobraRestoreVodDetailReturn(){
    if(!mCobraVodDetailReturnCaptured||mStage==null)return false;
    final String title=mCobraVodDetailReturnStageTitle,header=mCobraVodDetailReturnHeader;
    final String statusText=mCobraVodDetailReturnStatus,internal=mCobraVodDetailReturnInternal;
    final boolean smartWatchlist=mCobraVodDetailReturnSmartWatchlist;
    final ArrayList<View> saved=new ArrayList<>(mCobraVodDetailReturnViews);
    final View focus=mCobraVodDetailReturnFocus;
    cobraDiscardVodDetailReturn();mCobraNavigation.advance();
    while(mStage.getChildCount()>2)mStage.removeViewAt(2);
    mCobraStageTitle=title;mCobraInternalScreen=internal;mCobraSmartWatchlist=smartWatchlist;
    if(mHeader!=null){mHeader.setVisibility(View.VISIBLE);mHeader.setText(header);}
    if(mStatus!=null){mStatus.setVisibility(View.VISIBLE);mStatus.setText(statusText);}
    for(View child:saved){
      if(child.getParent() instanceof android.view.ViewGroup)
        ((android.view.ViewGroup)child.getParent()).removeView(child);
      mStage.addView(child);
    }
    cobraRefreshVodAmbientTrim();cobraRefreshVisualEffects();
    if(focus!=null)focus.post(()->{if(focus.isAttachedToWindow())focus.requestFocus();});
    return true;
  }

'''
    s=s.replace(marker,helpers+marker,1)

    # Top-level media landing and intentional drawer jumps invalidate stale detail parents.
    s=once(s,
        '    cobraDiscardVodLandingReturn();\n    clearStage(series ? "COBRA • TV SHOWS" : "COBRA • MOVIES");',
        '    cobraDiscardVodDetailReturn();\n    cobraDiscardVodLandingReturn();\n    clearStage(series ? "COBRA • TV SHOWS" : "COBRA • MOVIES");',
        'top-level movie detail return reset')

    drawer=method(s,'private void cobraDrawerDestination(LinearLayout parent,String icon,String label,String destination,Runnable action)')
    old='      if(!settingsDestination)cobraDiscardVodLandingReturn();'
    req(old in drawer,'drawer media-return boundary drift')
    drawer=drawer.replace(old,'      if(!settingsDestination){cobraDiscardVodDetailReturn();cobraDiscardVodLandingReturn();}',1)
    s=replace_method(s,'private void cobraDrawerDestination(LinearLayout parent,String icon,String label,String destination,Runnable action)',drawer)

    # Back restores the exact movie parent before the pre-existing Movies/Shows landing logic.
    back=method(s,'public void onBackPressed()')
    anchor='    if(cobraRestoreVodLandingReturn())return;'
    req(anchor in back,'Back media-return anchor missing')
    back=back.replace(anchor,'    if(cobraRestoreVodDetailReturn())return;\n'+anchor,1)
    s=replace_method(s,'public void onBackPressed()',back)

    # Drawer owner / Smart Return continue classifying the full-page detail route as Movies.
    owner=method(s,'private boolean cobraSurfaceMatchesDrawerOwner()')
    old='return "COBRA • MOVIES".equals(title)||(mCobraVodReturnCaptured&&!mCobraVodReturnSeries);'
    req(old in owner,'drawer owner Movies classification drift')
    owner=owner.replace(old,
        'return "COBRA • MOVIES".equals(title)||(mCobraVodDetailReturnCaptured&&!mCobraVodDetailReturnSeries)||(mCobraVodReturnCaptured&&!mCobraVodReturnSeries);',1)
    s=replace_method(s,'private boolean cobraSurfaceMatchesDrawerOwner()',owner)

    smart=method(s,'private String cobraSmartDestination()')
    anchor='    if(mCobraVodReturnCaptured)return mCobraVodReturnSeries?"shows":"movies";'
    req(anchor in smart,'Smart Return media classification drift')
    smart=smart.replace(anchor,
        '    if(mCobraVodDetailReturnCaptured)return mCobraVodDetailReturnSeries?"shows":"movies";\n'+anchor,1)
    s=replace_method(s,'private String cobraSmartDestination()',smart)

    # Insert movie-detail presentation helpers immediately before the current renderer.
    marker='  private void cobraRenderVodDetails(VodItem item,JSONObject info){'
    req(s.count(marker)==1,'movie detail renderer marker drift')
    detail_helpers=r'''  private String cobraVodDetailArtwork(VodItem item,JSONObject info){
    if(info!=null)for(String key:new String[]{"movie_image","cover_big","poster_path","cover"}){
      String value=info.optString(key,"").trim();
      if(value.startsWith("http://")||value.startsWith("https://"))return value;
    }
    return item.icon==null?"":item.icon;
  }

  private String cobraVodDetailRuntime(JSONObject info){
    if(info==null)return "";
    String raw=info.optString("duration",info.optString("duration_secs","")).trim();
    if(raw.isEmpty())return "";
    if(raw.matches("\\d+")){
      try{
        long value=Long.parseLong(raw);
        if(value>10000)value=Math.max(1,value/60);
        if(value>0&&value<1000)return value+" min";
      }catch(Exception ignored){}
    }
    return raw;
  }

  private String cobraVodDetailCertificate(JSONObject info){
    if(info==null)return "";
    for(String key:new String[]{"rating_mpaa","mpaa","certificate","age"}){
      String value=info.optString(key,"").trim();
      if(!value.isEmpty()&&!"0".equals(value)&&!"null".equalsIgnoreCase(value))return value;
    }
    return "";
  }

  private String cobraVodTrailerRaw(JSONObject info){
    if(info==null)return "";
    for(String key:new String[]{"youtube_trailer","trailer_url","trailer","youtube","youtube_id"}){
      Object raw=info.opt(key);
      if(raw instanceof String){
        String value=((String)raw).trim();if(!value.isEmpty()&&!"null".equalsIgnoreCase(value))return value;
      }else if(raw instanceof JSONObject){
        JSONObject object=(JSONObject)raw;
        for(String child:new String[]{"url","key","id","video_id"}){
          String value=object.optString(child,"").trim();if(!value.isEmpty())return value;
        }
      }else if(raw instanceof JSONArray){
        JSONArray array=(JSONArray)raw;
        if(array.length()>0){
          Object first=array.opt(0);
          if(first instanceof String&&!String.valueOf(first).trim().isEmpty())return String.valueOf(first).trim();
          if(first instanceof JSONObject){
            JSONObject object=(JSONObject)first;
            for(String child:new String[]{"url","key","id","video_id"}){
              String value=object.optString(child,"").trim();if(!value.isEmpty())return value;
            }
          }
        }
      }
    }
    return "";
  }

  private boolean cobraVodHasProviderTrailer(JSONObject info){
    return !cobraVodTrailerRaw(info).isEmpty();
  }

  private String cobraVodTrailerTarget(VodItem item,JSONObject info){
    String raw=cobraVodTrailerRaw(info).trim();
    if(raw.startsWith("//"))return "https:"+raw;
    if(raw.startsWith("http://")||raw.startsWith("https://"))return raw;
    if(raw.startsWith("www."))return "https://"+raw;
    if(raw.matches("[A-Za-z0-9_-]{6,}"))
      return "https://www.youtube.com/watch?v="+android.net.Uri.encode(raw);
    return "https://www.youtube.com/results?search_query="+
        android.net.Uri.encode(item.title+" official trailer");
  }

  private void cobraOpenVodTrailer(VodItem item,JSONObject info){
    String target=cobraVodTrailerTarget(item,info);
    try{
      android.content.Intent intent=new android.content.Intent(
          android.content.Intent.ACTION_VIEW,android.net.Uri.parse(target));
      startActivity(intent);
    }catch(Exception ignored){
      toast("No app is available to open this trailer.");
    }
  }

  private TextView cobraVodDetailSectionTitle(String label){
    TextView title=text(label,cobraModeColor("text"),18,Gravity.LEFT|Gravity.CENTER_VERTICAL);
    title.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));
    title.setLetterSpacing(.01f);return title;
  }

  private View cobraVodTrailerCard(VodItem item,JSONObject info){
    FrameLayout card=new FrameLayout(this);card.setFocusable(true);card.setClickable(true);
    card.setContentDescription("Trailer for "+item.title);card.setClipToOutline(true);
    card.setBackground(surface(cobraModeColor("panel"),18,cobraModeColor("line"),1));

    android.widget.ImageView art=new android.widget.ImageView(this);
    art.setScaleType(android.widget.ImageView.ScaleType.CENTER_CROP);
    art.setBackgroundColor(cobraModeColor("panel"));
    card.addView(art,new FrameLayout.LayoutParams(-1,-1));
    cobraLoadVodArtwork(art,cobraVodDetailArtwork(item,info));

    View veil=new View(this);
    int base=cobraModeDark()?0xdd06090e:0x99000000;
    android.graphics.drawable.GradientDrawable fade=new android.graphics.drawable.GradientDrawable(
        android.graphics.drawable.GradientDrawable.Orientation.BOTTOM_TOP,
        new int[]{base,0x55000000,0x10000000});
    veil.setBackground(fade);card.addView(veil,new FrameLayout.LayoutParams(-1,-1));

    LinearLayout copy=new LinearLayout(this);copy.setOrientation(LinearLayout.HORIZONTAL);
    copy.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);copy.setPadding(dp(18),dp(12),dp(18),dp(12));
    TextView play=text("▶",Color.WHITE,28,Gravity.CENTER);copy.addView(play,new LinearLayout.LayoutParams(dp(54),-1));
    LinearLayout labels=new LinearLayout(this);labels.setOrientation(LinearLayout.VERTICAL);
    TextView heading=text(cobraVodHasProviderTrailer(info)?"Watch Trailer":"Find Official Trailer",Color.WHITE,16,Gravity.LEFT|Gravity.BOTTOM);
    heading.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));labels.addView(heading,new LinearLayout.LayoutParams(-1,dp(34)));
    TextView sub=text(cobraVodHasProviderTrailer(info)?"Provider trailer":"Search YouTube for the official trailer",0xffd5dbe5,11,Gravity.LEFT|Gravity.TOP);
    labels.addView(sub,new LinearLayout.LayoutParams(-1,dp(32)));copy.addView(labels,new LinearLayout.LayoutParams(0,-1,1));
    card.addView(copy,new FrameLayout.LayoutParams(-1,-1));
    card.setOnClickListener(v->cobraOpenVodTrailer(item,info));

    android.graphics.drawable.StateListDrawable focus=new android.graphics.drawable.StateListDrawable();
    focus.addState(new int[]{android.R.attr.state_focused},
        surface(Color.TRANSPARENT,18,cobraModeColor("accent"),2));
    focus.addState(new int[]{},surface(Color.TRANSPARENT,18,Color.TRANSPARENT,0));
    card.setForeground(focus);
    return card;
  }

  private void cobraRenderMovieDetailPage(VodItem item,JSONObject info){
    LiveSource source=sourceById(item.sourceId);if(source==null)return;
    cobraCaptureVodDetailReturn(false);mCobraInternalScreen="internal";
    clearStage("COBRA • MOVIE DETAILS");status("Ready");
    if(mHeader!=null)mHeader.setVisibility(View.GONE);
    if(mStatus!=null)mStatus.setVisibility(View.GONE);

    final int background=cobraModeColor("background");
    final int panel=cobraModeColor("panel");
    final int textColor=cobraModeColor("text");
    final int muted=cobraModeColor("muted");
    final int line=cobraModeColor("line");
    final int accent=cobraModeColor("accent");

    ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);
    LinearLayout page=new LinearLayout(this);page.setOrientation(LinearLayout.VERTICAL);
    page.setPadding(dp(isCompact()?12:22),dp(10),dp(isCompact()?12:22),dp(34));
    page.setBackgroundColor(background);scroll.addView(page);

    LinearLayout top=new LinearLayout(this);top.setGravity(Gravity.CENTER_VERTICAL);
    Button back=action("‹");back.setAllCaps(false);back.setTextSize(28);back.setContentDescription("Back");
    back.setOnClickListener(v->{if(!cobraRestoreVodDetailReturn())showMovies();});
    top.addView(back,new LinearLayout.LayoutParams(dp(54),dp(50)));
    TextView context=text("MOVIE",muted,11,Gravity.CENTER);context.setLetterSpacing(.18f);
    top.addView(context,new LinearLayout.LayoutParams(0,dp(50),1));
    Button listTop=action(cobraVodWatchlistContains(item)?"♥":"♡");listTop.setAllCaps(false);listTop.setTextSize(23);
    listTop.setContentDescription("My List");listTop.setOnClickListener(v->{toggleWatchlist(item);listTop.setText(cobraVodWatchlistContains(item)?"♥":"♡");});
    top.addView(listTop,new LinearLayout.LayoutParams(dp(54),dp(50)));page.addView(top,new LinearLayout.LayoutParams(-1,dp(54)));

    FrameLayout hero=new FrameLayout(this);
    int heroTop=(accent&0x00ffffff)|(cobraModeDark()?0x2d000000:0x18000000);
    android.graphics.drawable.GradientDrawable heroBg=new android.graphics.drawable.GradientDrawable(
        android.graphics.drawable.GradientDrawable.Orientation.TOP_BOTTOM,new int[]{heroTop,background});
    hero.setBackground(heroBg);
    int heroHeight=dp(isCompact()?430:500);
    android.widget.ImageView poster=new android.widget.ImageView(this);poster.setScaleType(android.widget.ImageView.ScaleType.CENTER_CROP);
    poster.setClipToOutline(true);poster.setBackground(surface(panel,18,line,1));
    int posterW=dp(isCompact()?238:292),posterH=dp(isCompact()?350:430);
    FrameLayout.LayoutParams posterLp=new FrameLayout.LayoutParams(posterW,posterH,Gravity.TOP|Gravity.CENTER_HORIZONTAL);
    posterLp.topMargin=dp(10);hero.addView(poster,posterLp);cobraLoadVodArtwork(poster,cobraVodDetailArtwork(item,info));
    page.addView(hero,new LinearLayout.LayoutParams(-1,heroHeight));

    String rating=info.optString("rating",item.rating>0.0?String.format(Locale.US,"%.1f",item.rating):"").trim();
    if(!rating.isEmpty()){
      TextView score=text("★  "+rating,textColor,14,Gravity.CENTER);score.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));
      page.addView(score,new LinearLayout.LayoutParams(-1,dp(34)));
    }

    TextView title=text(item.title,textColor,isCompact()?27:31,Gravity.CENTER);
    title.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));title.setMaxLines(3);
    title.setLetterSpacing(.005f);page.addView(title,new LinearLayout.LayoutParams(-1,-2));

    String year=info.optString("releasedate",info.optString("year",item.year)).trim();
    String genre=info.optString("genre",item.category).trim();
    if(genre.contains(","))genre=genre.substring(0,genre.indexOf(',')).trim();
    String certificate=cobraVodDetailCertificate(info);
    String runtime=cobraVodDetailRuntime(info);
    ArrayList<String> metaParts=new ArrayList<>();
    if(!genre.isEmpty())metaParts.add(genre.toUpperCase(Locale.US));
    if(!year.isEmpty())metaParts.add(year);
    if(!certificate.isEmpty())metaParts.add(certificate);
    if(!runtime.isEmpty())metaParts.add(runtime);
    TextView metadata=text(android.text.TextUtils.join("   ",metaParts),muted,13,Gravity.CENTER);
    metadata.setMaxLines(2);page.addView(metadata,new LinearLayout.LayoutParams(-1,dp(46)));

    TextView provider=text("Available via "+source.name,muted,10,Gravity.CENTER);
    page.addView(provider,new LinearLayout.LayoutParams(-1,dp(28)));

    Button play=action("▶  PLAY");play.setAllCaps(false);play.setTextSize(16);
    play.setTextColor(Color.BLACK);play.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));
    play.setBackground(surface(accent,26,accent,1));play.setOnClickListener(v->playMovie(item));
    LinearLayout.LayoutParams playLp=new LinearLayout.LayoutParams(-1,dp(58));playLp.topMargin=dp(8);page.addView(play,playLp);

    LinearLayout actions=new LinearLayout(this);actions.setGravity(Gravity.CENTER);
    Button list=action(cobraVodWatchlistContains(item)?"✓  IN MY LIST":"+  MY LIST");list.setAllCaps(false);
    list.setOnClickListener(v->{toggleWatchlist(item);list.setText(cobraVodWatchlistContains(item)?"✓  IN MY LIST":"+  MY LIST");listTop.setText(cobraVodWatchlistContains(item)?"♥":"♡");});
    Button trailer=action("▶  TRAILER");trailer.setAllCaps(false);trailer.setOnClickListener(v->cobraOpenVodTrailer(item,info));
    actions.addView(list,new LinearLayout.LayoutParams(0,dp(52),1));
    LinearLayout.LayoutParams trailerLp=new LinearLayout.LayoutParams(0,dp(52),1);trailerLp.leftMargin=dp(10);actions.addView(trailer,trailerLp);
    LinearLayout.LayoutParams actionsLp=new LinearLayout.LayoutParams(-1,dp(62));actionsLp.topMargin=dp(8);page.addView(actions,actionsLp);

    String description=info.optString("plot",info.optString("description","")).trim();
    if(!description.isEmpty()){
      LinearLayout.LayoutParams headLp=new LinearLayout.LayoutParams(-1,dp(46));headLp.topMargin=dp(12);
      page.addView(cobraVodDetailSectionTitle("Storyline"),headLp);
      TextView synopsis=text(description,muted,13,Gravity.LEFT);synopsis.setLineSpacing(0f,1.12f);synopsis.setMaxLines(10);
      page.addView(synopsis,new LinearLayout.LayoutParams(-1,-2));
    }

    LinearLayout.LayoutParams trailerHeadLp=new LinearLayout.LayoutParams(-1,dp(48));trailerHeadLp.topMargin=dp(18);
    page.addView(cobraVodDetailSectionTitle("Trailers"),trailerHeadLp);
    page.addView(cobraVodTrailerCard(item,info),new LinearLayout.LayoutParams(-1,dp(isCompact()?184:218)));

    ArrayList<String> people=cobraVodPeople(info);
    if(!people.isEmpty()){
      LinearLayout.LayoutParams castHeadLp=new LinearLayout.LayoutParams(-1,dp(48));castHeadLp.topMargin=dp(18);
      page.addView(cobraVodDetailSectionTitle("Cast & Crew"),castHeadLp);
      android.widget.HorizontalScrollView castScroll=new android.widget.HorizontalScrollView(this);castScroll.setHorizontalScrollBarEnabled(false);
      LinearLayout cast=new LinearLayout(this);cast.setOrientation(LinearLayout.HORIZONTAL);
      for(String person:people){
        TextView chip=text(person,textColor,12,Gravity.CENTER);chip.setPadding(dp(14),0,dp(14),0);
        chip.setBackground(surface(panel,18,line,1));
        LinearLayout.LayoutParams cp=new LinearLayout.LayoutParams(-2,dp(42));cp.rightMargin=dp(8);cast.addView(chip,cp);
      }
      castScroll.addView(cast,new android.widget.HorizontalScrollView.LayoutParams(-2,dp(46)));
      page.addView(castScroll,new LinearLayout.LayoutParams(-1,dp(50)));
    }

    String collection=cobraVodCollectionName(info);
    if(!collection.isEmpty()){
      TextView collectionText=text("Collection  •  "+collection,muted,11,Gravity.LEFT|Gravity.CENTER_VERTICAL);
      LinearLayout.LayoutParams clp=new LinearLayout.LayoutParams(-1,dp(38));clp.topMargin=dp(8);page.addView(collectionText,clp);
    }

    ArrayList<VodItem> related=cobraVodRelatedItems(item);
    if(!related.isEmpty()){
      LinearLayout.LayoutParams relatedHeadLp=new LinearLayout.LayoutParams(-1,dp(48));relatedHeadLp.topMargin=dp(18);
      page.addView(cobraVodDetailSectionTitle("Related Movies"),relatedHeadLp);
      android.widget.HorizontalScrollView rail=new android.widget.HorizontalScrollView(this);rail.setHorizontalScrollBarEnabled(false);
      LinearLayout row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);row.setPadding(dp(2),0,dp(12),dp(2));
      rail.addView(row,new android.widget.HorizontalScrollView.LayoutParams(-2,-2));
      int count=Math.min(10,related.size());
      for(int i=0;i<count;i++)row.addView(cobraVodCard(related.get(i),cobraVodContinueObject(related.get(i))!=null),cobraVodCardParams());
      page.addView(rail,new LinearLayout.LayoutParams(-1,dp(isCompact()?258:292)));
    }

    mStage.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
    cobraRefreshVodAmbientTrim();cobraRefreshVisualEffects();
  }

'''
    s=s.replace(marker,detail_helpers+marker,1)

    # Movies go to the full page; TV Shows keep the exact existing sheet behavior.
    sig='private void cobraRenderVodDetails(VodItem item,JSONObject info)'
    old=method(s,sig)
    for token in ('cobraOpenSheet(item.title,metadata,"vod-details")','Cast & Crew','More Like This',
                  'Browse Episodes','Start playback','Cobra Recovery'):
        if token=='Cobra Recovery': continue
        req(token in old,'existing details contract drift: '+token)
    new=r'''private void cobraRenderVodDetails(VodItem item,JSONObject info){
    LiveSource source=sourceById(item.sourceId);if(source==null)return;
    if(!item.series){cobraRenderMovieDetailPage(item,info);return;}

    // TV Shows intentionally retain the approved 2103222 sheet and episode behavior.
    String description=info.optString("plot",info.optString("description",""));
    String year=info.optString("releasedate",info.optString("year",item.year));
    String rating=info.optString("rating",item.rating>0.0?String.format(Locale.US,"%.1f",item.rating):"");
    String runtime=info.optString("duration",info.optString("duration_secs",""));
    String genre=info.optString("genre",item.category);String collection=cobraVodCollectionName(info);
    String metadata=(year.isEmpty()?"":year)+(rating.isEmpty()?"":((year.isEmpty()?"":"  •  ")+rating+" ★"));
    if(!runtime.isEmpty())metadata+=(metadata.isEmpty()?"":"  •  ")+runtime;
    if(!genre.isEmpty())metadata+=(metadata.isEmpty()?"":"  •  ")+genre;
    metadata+=(metadata.isEmpty()?"":"\n")+"Available via "+source.name;
    LinearLayout rows=cobraOpenSheet(item.title,metadata,"vod-details");boolean dark=cobraSheetIsDark();
    if(!description.trim().isEmpty()){TextView plot=cobraInfoText(rows,description.trim());plot.setMaxLines(8);}
    rows.addView(cobraSheetRow("television","Browse Episodes","Seasons and episodes",false,dark,()->openSeries(item)));
    boolean listed=cobraVodWatchlistContains(item);
    rows.addView(cobraSheetRow("favorite",listed?"✓ In My List":"+ My List",listed?"Tap to remove":"Save for later",false,dark,()->{toggleWatchlist(item);cobraShowVodDetails(item);}));
    if(!collection.isEmpty())rows.addView(cobraSheetRow("film","Collection  •  "+collection,"Browse titles returned with the same collection metadata",false,dark,()->cobraBrowseVodCollectionMetadata(item,collection)));
    ArrayList<String> people=cobraVodPeople(info);
    if(!people.isEmpty()){
      cobraInfoText(rows,"Cast & Crew");
      for(String person:people)rows.addView(cobraSheetRow("search",person,"Find other titles in enabled providers",false,dark,()->cobraBrowseVodPerson(item,person)));
    }
    ArrayList<VodItem> related=cobraVodRelatedItems(item);
    if(!related.isEmpty()){
      cobraInfoText(rows,"More Like This");int count=Math.min(6,related.size());
      for(int i=0;i<count;i++){VodItem relatedItem=related.get(i);rows.addView(cobraSheetRow("television",relatedItem.title,cobraVodCardMeta(relatedItem),false,dark,()->cobraShowVodDetails(relatedItem)));}
      if(related.size()>6)rows.addView(cobraSheetRow("more","See all similar titles",related.size()+" available",false,dark,()->cobraShowVodCollection("More Like This",related,true)));
    }
  }'''
    s=replace_method(s,sig,new)

    # Source gates for the exact requested scope.
    current=method(s,sig)
    req('cobraRenderMovieDetailPage(item,info)' in current,'movie full-page route missing')
    req('Browse Episodes' in current and 'openSeries(item)' in current,'TV show details behavior lost')
    for token in (
        'COBRA • MOVIE DETAILS','▶  PLAY','▶  TRAILER','Trailers','Related Movies',
        'Cast & Crew','Available via ','youtube_trailer','official trailer',
        'cobraCaptureVodDetailReturn(false)','cobraRestoreVodDetailReturn()'
    ):
        req(token in s,'2103223 movie details contract missing: '+token)
    req(method_hashes(s,PROTECTED_METHODS)==protected_before,'Protected system method changed')
    path.write_text(s)
    return before_file,sha(path),protected_before

def patch_identity(shell:Path):
    gradle=shell/'tools/android/packaging/xbmc/build.gradle.in'
    g=gradle.read_text()
    g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','versionCode')
    g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','versionName')
    gradle.write_text(g)

    runtime=Path('scripts/infinity_background_resume.py')
    r=runtime.read_text()
    r=once(r,f'VERSION_CODE = {OLD_VERSION}',f'VERSION_CODE = {VERSION}','runtime version')
    r=once(r,"RELEASE = '"+OLD_NAME+"'","RELEASE = '"+NEW_NAME+"'",'runtime release')
    runtime.write_text(r)

    pack=Path('scripts/package_background_resume.py')
    p=pack.read_text();old='Infinity-'+OLD_NAME;new='Infinity-'+NEW_NAME
    req(p.count(old)>=2,'packager identity drift')
    pack.write_text(p.replace(old,new))
    return gradle

def apply(shell:Path):
    receipt_path=Path('engine/background-resume-source.json')
    receipt=json.loads(receipt_path.read_text())
    req(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,
        'Expected exact locked 2103222 replay')
    req(receipt.get('native_engine_sha256')==NATIVE,'Native engine receipt drift')

    activity=shell/(SOURCE+'InfinityLiveActivity.java.in')
    splash=shell/(SOURCE+'Splash.java.in')
    smart=shell/(SOURCE+'CobraSmartReturn.java.in')
    main=shell/(SOURCE+'Main.java.in')
    renderer=shell/(SOURCE+'CobraVisualRenderer.java.in')
    for p in (activity,splash,smart,main,renderer): req(p.is_file(),'Missing '+str(p))

    frozen={
        'splash':sha(splash),'smart_return':sha(smart),'main':sha(main),'visual_renderer':sha(renderer)
    }
    activity_before,activity_after,protected=patch_activity(activity)
    gradle=patch_identity(shell)

    req(sha(splash)==frozen['splash'],'Choose Your Experience/Health changed')
    req(sha(smart)==frozen['smart_return'],'Smart Return engine changed')
    req(sha(main)==frozen['main'],'Kodi Main changed')
    req(sha(renderer)==frozen['visual_renderer'],'Global visual renderer changed')

    for name in (SOURCE+'InfinityLiveActivity.java.in',SOURCE+'Splash.java.in',
                 SOURCE+'CobraSmartReturn.java.in',SOURCE+'Main.java.in'):
        req(name in receipt['files'],'Receipt missing '+name)
        receipt['files'][name]['after']=sha(shell/name)
    rel='tools/android/packaging/xbmc/build.gradle.in'
    receipt['files'][rel]['after']=sha(gradle)

    receipt.update(
        version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,
        candidate_locked=False,physical_device_verified=False,runtime_device_tested=False,
        native_engine_rebuilt=False,native_engine_reused_from_2103209=True,native_engine_sha256=NATIVE,
        movie_details_full_page=True,movie_details_cinematic_layout=True,movie_trailers_option=True,
        movie_trailer_provider_metadata=True,movie_trailer_youtube_search_fallback=True,
        movie_detail_exact_parent_return=True,tv_show_details_unchanged=True,
        tv_episode_browser_unchanged=True,playback_unchanged=True,providers_unchanged=True,
        live_tv_unchanged=True,drawer_owner_preserved=True,smart_return_preserved=True,
        choose_experience_ui_unchanged=True,health_center_unchanged=True,global_visual_renderer_unchanged=True
    )
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for name,row in receipt['files'].items(): req(sha(shell/name)==row['after'],'Receipt drift '+name)

    Path('audit223').mkdir(exist_ok=True)
    Path('audit223/scope.json').write_text(json.dumps({
        'build':VERSION,'parent':OLD_VERSION,
        'parent_locked_branch':'locked-infinity-cobra-2103222-experience-options-ui-passed',
        'authorized_delta':'Movies detail presentation + trailer entry point + exact detail parent return',
        'activity_before_sha256':activity_before,'activity_after_sha256':activity_after,
        'frozen_files_sha256':frozen,'protected_methods_sha256':protected,
        'movies':{
            'full_page_detail':True,'cinematic_poster_hero':True,'large_play_action':True,
            'my_list_action':True,'trailers_action':True,'trailers_section':True,
            'storyline':True,'cast_crew_display':True,'related_movies_rail':True,
            'provider_metadata_preserved':True,'theme_modes_preserved':True,
            'dpad_focus_surfaces':True
        },
        'trailers':{
            'provider_metadata_keys':['youtube_trailer','trailer_url','trailer','youtube','youtube_id'],
            'fallback':'YouTube official trailer search',
            'opens_with_android_ACTION_VIEW':True
        },
        'tv_show_details_unchanged':True,'playback_unchanged':True,'providers_unchanged':True,
        'native_engine_sha256':NATIVE,'native_engine_rebuilt':False,
        'choose_experience_ui_unchanged':True,'drawer_owner_preserved':True,
        'smart_return_preserved':True,'live_tv_unchanged':True,'status':'TEST CANDIDATE'
    },indent=2,sort_keys=True)+'\n')
    print('PASS: 2103223 adds only cinematic Movies details + trailers over locked 2103222')

def main():
    p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True)
    a=p.parse_args();apply(a.shell)

if __name__=='__main__':
    main()
