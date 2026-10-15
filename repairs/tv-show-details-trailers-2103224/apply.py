#!/usr/bin/env python3
"""2103224: carry the locked 2103223 cinematic details treatment to TV Shows.

Parent: locked 2103223 Movie Details + Trailers.
Authorized delta:
- TV Shows only: replace the legacy details sheet with the same full-page cinematic
  presentation language already approved for Movies.
- Add the same Trailers action/section to TV Shows.
- Preserve the existing seasons/episodes browser and all playback behavior exactly.

Movies, Choose Your Experience, Live TV, providers, Smart Return, drawer ownership,
Health Center, native engine, playback, and the locked 2103223 movie detail page are
protected and unchanged.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

VERSION=2103224
OLD_VERSION=2103223
OLD_NAME='1.0.9-Cobra-Movie-Details-Trailers-RC1'
NEW_NAME='1.0.9-Cobra-Movie-TV-Details-Trailers-RC1'
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
def mh(s,names):
    return {n:hb(method(s,n).encode()) for n in names}

PROTECTED_METHODS=[
    'private void cobraRenderMovieDetailPage(VodItem item,JSONObject info)',
    'private void cobraOpenVodTrailer(VodItem item,JSONObject info)',
    'private View cobraVodTrailerCard(VodItem item,JSONObject info)',
    'private String cobraVodTrailerTarget(VodItem item,JSONObject info)',
    'private String cobraVodTrailerRaw(JSONObject info)',
    'private void cobraShowSeriesBrowser(VodItem parent,JSONObject root,ArrayList<VodItem> episodes)',
    'private void cobraPlaySeriesEpisode(VodItem parent,VodItem episode,ArrayList<VodItem> episodes)',
    'private void cobraRenderSeasonEpisodes(LinearLayout container,VodItem parent,ArrayList<VodItem> all,int season)',
    'private void openSeries(VodItem item)',
    'private void startSinglePlayer(String url)',
    'private void playChannel(Channel channel)',
    'private void cobraStartLocalTimeshift',
    'private LoadResult loadXtream(LiveSource source)',
    'private LoadResult loadM3u(LiveSource source)',
    'private void showSettings()',
    'private void cobraRefreshAmbient()',
]

def patch_activity(path:Path):
    s=path.read_text()
    before_file=hb(s.encode())
    protected_before=mh(s,PROTECTED_METHODS)

    # 2103223 already taught Smart Return about both kinds of detail parents.
    smart=method(s,'private String cobraSmartDestination()')
    req('if(mCobraVodDetailReturnCaptured)return mCobraVodDetailReturnSeries?"shows":"movies";' in smart,
        '2103223 detail Smart Return classification missing')

    # Extend drawer-owner surface matching to TV Show details. Movies line remains byte-identical.
    sig='private boolean cobraSurfaceMatchesDrawerOwner()'
    owner=method(s,sig)
    movie_line='return "COBRA • MOVIES".equals(title)||(mCobraVodDetailReturnCaptured&&!mCobraVodDetailReturnSeries)||(mCobraVodReturnCaptured&&!mCobraVodReturnSeries);'
    req(movie_line in owner,'locked 2103223 Movies owner classification drift')
    old='''    if(COBRA_OWNER_SHOWS.equals(owner))
      return "COBRA • TV SHOWS".equals(title)||"COBRA • SERIES".equals(title)||
          (mCobraVodReturnCaptured&&mCobraVodReturnSeries);'''
    new='''    if(COBRA_OWNER_SHOWS.equals(owner))
      return "COBRA • TV SHOWS".equals(title)||"COBRA • SERIES".equals(title)||
          (mCobraVodDetailReturnCaptured&&mCobraVodDetailReturnSeries)||
          (mCobraVodReturnCaptured&&mCobraVodReturnSeries);'''
    req(old in owner,'TV Shows drawer owner classification anchor drift')
    owner=owner.replace(old,new,1)
    s=replace_method(s,sig,owner)

    # Add the TV Show detail page next to the already-approved movie detail page.
    marker='  private void cobraRenderVodDetails(VodItem item,JSONObject info){'
    req(s.count(marker)==1,'details renderer marker drift')
    page=r'''  private void cobraRenderSeriesDetailPage(VodItem item,JSONObject info){
    LiveSource source=sourceById(item.sourceId);if(source==null)return;
    cobraCaptureVodDetailReturn(true);mCobraInternalScreen="internal";
    clearStage("COBRA • TV SHOW DETAILS");status("Ready");
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
    back.setOnClickListener(v->{if(!cobraRestoreVodDetailReturn())showSeries();});
    top.addView(back,new LinearLayout.LayoutParams(dp(54),dp(50)));
    TextView context=text("TV SHOW",muted,11,Gravity.CENTER);context.setLetterSpacing(.18f);
    top.addView(context,new LinearLayout.LayoutParams(0,dp(50),1));
    Button listTop=action(cobraVodWatchlistContains(item)?"♥":"♡");listTop.setAllCaps(false);listTop.setTextSize(23);
    listTop.setContentDescription("My List");
    listTop.setOnClickListener(v->{toggleWatchlist(item);listTop.setText(cobraVodWatchlistContains(item)?"♥":"♡");});
    top.addView(listTop,new LinearLayout.LayoutParams(dp(54),dp(50)));
    page.addView(top,new LinearLayout.LayoutParams(-1,dp(54)));

    FrameLayout hero=new FrameLayout(this);
    int heroTop=(accent&0x00ffffff)|(cobraModeDark()?0x2d000000:0x18000000);
    android.graphics.drawable.GradientDrawable heroBg=new android.graphics.drawable.GradientDrawable(
        android.graphics.drawable.GradientDrawable.Orientation.TOP_BOTTOM,new int[]{heroTop,background});
    hero.setBackground(heroBg);
    int heroHeight=dp(isCompact()?430:500);
    android.widget.ImageView poster=new android.widget.ImageView(this);
    poster.setScaleType(android.widget.ImageView.ScaleType.CENTER_CROP);
    poster.setClipToOutline(true);poster.setBackground(surface(panel,18,line,1));
    int posterW=dp(isCompact()?238:292),posterH=dp(isCompact()?350:430);
    FrameLayout.LayoutParams posterLp=new FrameLayout.LayoutParams(posterW,posterH,Gravity.TOP|Gravity.CENTER_HORIZONTAL);
    posterLp.topMargin=dp(10);hero.addView(poster,posterLp);
    cobraLoadVodArtwork(poster,cobraVodDetailArtwork(item,info));
    page.addView(hero,new LinearLayout.LayoutParams(-1,heroHeight));

    String rating=info.optString("rating",item.rating>0.0?String.format(Locale.US,"%.1f",item.rating):"").trim();
    if(!rating.isEmpty()){
      TextView score=text("★  "+rating,textColor,14,Gravity.CENTER);
      score.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));
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

    Button episodes=action("▶  BROWSE EPISODES");episodes.setAllCaps(false);episodes.setTextSize(16);
    episodes.setTextColor(Color.BLACK);
    episodes.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));
    episodes.setBackground(surface(accent,26,accent,1));episodes.setOnClickListener(v->openSeries(item));
    LinearLayout.LayoutParams episodesLp=new LinearLayout.LayoutParams(-1,dp(58));
    episodesLp.topMargin=dp(8);page.addView(episodes,episodesLp);

    LinearLayout actions=new LinearLayout(this);actions.setGravity(Gravity.CENTER);
    Button list=action(cobraVodWatchlistContains(item)?"✓  IN MY LIST":"+  MY LIST");list.setAllCaps(false);
    list.setOnClickListener(v->{toggleWatchlist(item);
      list.setText(cobraVodWatchlistContains(item)?"✓  IN MY LIST":"+  MY LIST");
      listTop.setText(cobraVodWatchlistContains(item)?"♥":"♡");});
    Button trailer=action("▶  TRAILER");trailer.setAllCaps(false);
    trailer.setOnClickListener(v->cobraOpenVodTrailer(item,info));
    actions.addView(list,new LinearLayout.LayoutParams(0,dp(52),1));
    LinearLayout.LayoutParams trailerLp=new LinearLayout.LayoutParams(0,dp(52),1);
    trailerLp.leftMargin=dp(10);actions.addView(trailer,trailerLp);
    LinearLayout.LayoutParams actionsLp=new LinearLayout.LayoutParams(-1,dp(62));
    actionsLp.topMargin=dp(8);page.addView(actions,actionsLp);

    String description=info.optString("plot",info.optString("description","")).trim();
    if(!description.isEmpty()){
      LinearLayout.LayoutParams headLp=new LinearLayout.LayoutParams(-1,dp(46));headLp.topMargin=dp(12);
      page.addView(cobraVodDetailSectionTitle("Storyline"),headLp);
      TextView synopsis=text(description,muted,13,Gravity.LEFT);
      synopsis.setLineSpacing(0f,1.12f);synopsis.setMaxLines(10);
      page.addView(synopsis,new LinearLayout.LayoutParams(-1,-2));
    }

    LinearLayout.LayoutParams trailerHeadLp=new LinearLayout.LayoutParams(-1,dp(48));
    trailerHeadLp.topMargin=dp(18);
    page.addView(cobraVodDetailSectionTitle("Trailers"),trailerHeadLp);
    page.addView(cobraVodTrailerCard(item,info),new LinearLayout.LayoutParams(-1,dp(isCompact()?184:218)));

    ArrayList<String> people=cobraVodPeople(info);
    if(!people.isEmpty()){
      LinearLayout.LayoutParams castHeadLp=new LinearLayout.LayoutParams(-1,dp(48));
      castHeadLp.topMargin=dp(18);page.addView(cobraVodDetailSectionTitle("Cast & Crew"),castHeadLp);
      android.widget.HorizontalScrollView castScroll=new android.widget.HorizontalScrollView(this);
      castScroll.setHorizontalScrollBarEnabled(false);
      LinearLayout cast=new LinearLayout(this);cast.setOrientation(LinearLayout.HORIZONTAL);
      for(String person:people){
        TextView chip=text(person,textColor,12,Gravity.CENTER);chip.setPadding(dp(14),0,dp(14),0);
        chip.setBackground(surface(panel,18,line,1));
        LinearLayout.LayoutParams cp=new LinearLayout.LayoutParams(-2,dp(42));cp.rightMargin=dp(8);
        cast.addView(chip,cp);
      }
      castScroll.addView(cast,new android.widget.HorizontalScrollView.LayoutParams(-2,dp(46)));
      page.addView(castScroll,new LinearLayout.LayoutParams(-1,dp(50)));
    }

    String collection=cobraVodCollectionName(info);
    if(!collection.isEmpty()){
      TextView collectionText=text("Collection  •  "+collection,muted,11,Gravity.LEFT|Gravity.CENTER_VERTICAL);
      LinearLayout.LayoutParams clp=new LinearLayout.LayoutParams(-1,dp(38));
      clp.topMargin=dp(8);page.addView(collectionText,clp);
    }

    ArrayList<VodItem> related=cobraVodRelatedItems(item);
    if(!related.isEmpty()){
      LinearLayout.LayoutParams relatedHeadLp=new LinearLayout.LayoutParams(-1,dp(48));
      relatedHeadLp.topMargin=dp(18);page.addView(cobraVodDetailSectionTitle("Related Shows"),relatedHeadLp);
      android.widget.HorizontalScrollView rail=new android.widget.HorizontalScrollView(this);
      rail.setHorizontalScrollBarEnabled(false);
      LinearLayout row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);
      row.setPadding(dp(2),0,dp(12),dp(2));
      rail.addView(row,new android.widget.HorizontalScrollView.LayoutParams(-2,-2));
      int count=Math.min(10,related.size());
      for(int i=0;i<count;i++)
        row.addView(cobraVodCard(related.get(i),cobraVodContinueObject(related.get(i))!=null),cobraVodCardParams());
      page.addView(rail,new LinearLayout.LayoutParams(-1,dp(isCompact()?258:292)));
    }

    mStage.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
    cobraRefreshVodAmbientTrim();cobraRefreshVisualEffects();
  }

'''
    s=s.replace(marker,page+marker,1)

    # Route Movies to their exact locked page and TV Shows to the new sibling page.
    old_render=method(s,'private void cobraRenderVodDetails(VodItem item,JSONObject info)')
    req('if(!item.series){cobraRenderMovieDetailPage(item,info);return;}' in old_render,
        'locked 2103223 movie route missing')
    req('Browse Episodes' in old_render and 'cobraOpenSheet(item.title,metadata,"vod-details")' in old_render,
        'expected legacy TV Show details sheet missing')
    new_render=r'''private void cobraRenderVodDetails(VodItem item,JSONObject info){
    LiveSource source=sourceById(item.sourceId);if(source==null)return;
    if(item.series){cobraRenderSeriesDetailPage(item,info);return;}
    cobraRenderMovieDetailPage(item,info);
  }'''
    s=replace_method(s,'private void cobraRenderVodDetails(VodItem item,JSONObject info)',new_render)

    # Guard the requested result and the locked movie implementation.
    for token in (
        'COBRA • TV SHOW DETAILS','▶  BROWSE EPISODES','▶  TRAILER',
        'Trailers','Storyline','Cast & Crew','Related Shows',
        'cobraCaptureVodDetailReturn(true)','cobraRenderSeriesDetailPage(item,info)',
        'cobraRenderMovieDetailPage(item,info)'
    ):
        req(token in s,'2103224 TV Show detail contract missing: '+token)
    req(mh(s,PROTECTED_METHODS)==protected_before,'Protected 2103223 method changed')

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
        'Expected exact locked 2103223 replay')
    req(receipt.get('native_engine_sha256')==NATIVE,'Native engine receipt drift')
    req(receipt.get('movie_details_full_page') is True and receipt.get('movie_trailers_option') is True,
        'Locked 2103223 Movies detail contract missing')

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
        movie_details_full_page=True,movie_details_unchanged_from_2103223=True,movie_trailers_option=True,
        tv_show_details_full_page=True,tv_show_details_cinematic_layout=True,tv_show_trailers_option=True,
        tv_show_detail_exact_parent_return=True,tv_episode_browser_unchanged=True,
        tv_resume_episode_unchanged=True,tv_play_next_episode_unchanged=True,
        playback_unchanged=True,providers_unchanged=True,live_tv_unchanged=True,
        drawer_owner_preserved=True,smart_return_preserved=True,
        choose_experience_ui_unchanged=True,health_center_unchanged=True,
        global_visual_renderer_unchanged=True
    )
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for name,row in receipt['files'].items(): req(sha(shell/name)==row['after'],'Receipt drift '+name)

    Path('audit224').mkdir(exist_ok=True)
    Path('audit224/scope.json').write_text(json.dumps({
        'build':VERSION,'parent':OLD_VERSION,
        'parent_locked_branch':'locked-infinity-cobra-2103223-movie-details-trailers-passed',
        'authorized_delta':'TV Show detail presentation + trailer entry point + TV detail drawer-owner classification',
        'activity_before_sha256':activity_before,'activity_after_sha256':activity_after,
        'frozen_files_sha256':frozen,'protected_2103223_methods_sha256':protected,
        'movies':{'locked_2103223_detail_page_unchanged':True,'trailers_unchanged':True},
        'tv_shows':{
            'full_page_detail':True,'cinematic_poster_hero':True,'browse_episodes_primary_action':True,
            'my_list_action':True,'trailers_action':True,'trailers_section':True,
            'storyline':True,'cast_crew_display':True,'related_shows_rail':True,
            'provider_metadata_preserved':True,'theme_modes_preserved':True,
            'dpad_focus_surfaces':True,'exact_parent_return':True
        },
        'episode_browser':{
            'unchanged':True,'resume_episode_unchanged':True,'play_next_episode_unchanged':True,
            'episode_progress_unchanged':True,'playback_unchanged':True
        },
        'native_engine_sha256':NATIVE,'native_engine_rebuilt':False,
        'providers_unchanged':True,'live_tv_unchanged':True,'smart_return_preserved':True,
        'drawer_owner_preserved':True,'choose_experience_ui_unchanged':True,
        'health_center_unchanged':True,'status':'TEST CANDIDATE'
    },indent=2,sort_keys=True)+'\n')
    print('PASS: 2103224 carries locked cinematic details/trailers to TV Shows only')

def main():
    p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True)
    a=p.parse_args();apply(a.shell)

if __name__=='__main__':
    main()
