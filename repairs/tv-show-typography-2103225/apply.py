#!/usr/bin/env python3
"""2103225: TV Shows landing typography-only correction.

Parent: locked 2103224 Movie + TV Details + Trailers.
Authorized delta: TV Shows landing/collection text metrics only.

Fixes:
- give two-line TV-show poster titles enough vertical room without changing the approved font;
- give TV-show date/rating metadata enough line height so it cannot be clipped;
- slightly reduce TV-show card-title size while preserving the exact font/design language;
- improve Light-mode TV-show metadata contrast;
- normalize a provider label of "tv" to "TV" in the TV Shows hero;
- enlarge only TV-show shelf/grid row heights to contain the corrected text metrics.

Movies retain their existing card metrics. Hero/shelf order, data, details pages, trailers,
playback, providers, episode browser, Smart Return, drawer ownership, Live TV, Health Center,
Choose Your Experience, native engine and global theme behavior are untouched.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

VERSION=2103225
OLD_VERSION=2103224
OLD_NAME='1.0.9-Cobra-Movie-TV-Details-Trailers-RC1'
NEW_NAME='1.0.9-Cobra-TV-Show-Typography-RC1'
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

PROTECTED=[
    'private void cobraRenderMovieDetailPage(VodItem item,JSONObject info)',
    'private void cobraRenderSeriesDetailPage(VodItem item,JSONObject info)',
    'private void cobraRenderVodDetails(VodItem item,JSONObject info)',
    'private void cobraOpenVodTrailer(VodItem item,JSONObject info)',
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
    protected_before=mh(s,PROTECTED)

    # Hero: text-only polish for TV Shows. Movies preserve their existing label path.
    sig='private View cobraVodHero(VodItem item, boolean series, android.widget.ViewFlipper carousel)'
    hero=method(s,sig)
    old='''    LiveSource source=sourceById(item.sourceId);String provider=source==null?"Provider":source.name;
    String meta=item.category+"  •  "+provider;'''
    new='''    LiveSource source=sourceById(item.sourceId);String provider=source==null?"Provider":source.name;
    String providerLabel=series&&"tv".equalsIgnoreCase(provider.trim())?"TV":provider;
    String meta=item.category+"  •  "+providerLabel;'''
    req(old in hero,'hero provider metadata anchor drift')
    hero=hero.replace(old,new,1)
    old='''    TextView metadata=text(meta,0xffc5d0df,12,Gravity.LEFT);metadata.setMaxLines(1);
    copy.addView(metadata,new LinearLayout.LayoutParams(-1,dp(34)));'''
    new='''    TextView metadata=text(meta,0xffc5d0df,12,Gravity.LEFT);metadata.setMaxLines(1);
    metadata.setEllipsize(android.text.TextUtils.TruncateAt.END);
    if(series)metadata.setTag("tv_show_hero_metadata_typography");
    copy.addView(metadata,new LinearLayout.LayoutParams(-1,dp(series?38:34)));'''
    req(old in hero,'hero metadata metrics anchor drift')
    hero=hero.replace(old,new,1)
    s=replace_method(s,sig,hero)

    # Shelf viewport: increase only TV Shows rows to fit the taller title/metadata metrics.
    sig='private void cobraAddVodShelf(LinearLayout page,String title,ArrayList<VodItem> items,int limit,'
    shelf=method(s,sig)
    old='    page.addView(rail,new LinearLayout.LayoutParams(-1,dp(isCompact()?258:292)));'
    new='    page.addView(rail,new LinearLayout.LayoutParams(-1,dp(series?(isCompact()?278:312):(isCompact()?258:292))));'
    req(old in shelf,'TV shelf height anchor drift')
    shelf=shelf.replace(old,new,1)
    s=replace_method(s,sig,shelf)

    # Card typography: preserve exact movie values; adjust only item.series.
    sig='private View cobraVodCard(VodItem item,boolean progress)'
    card=method(s,sig)
    old='''    TextView name=text(item.title,cobraModeColor("text"),12,Gravity.LEFT|Gravity.CENTER_VERTICAL);
    name.setMaxLines(2);name.setEllipsize(android.text.TextUtils.TruncateAt.END);
    card.addView(name,new LinearLayout.LayoutParams(-1,dp(42)));'''
    new='''    int cardTitleSize=item.series?11:12;
    int cardTitleGravity=item.series?(Gravity.LEFT|Gravity.TOP):(Gravity.LEFT|Gravity.CENTER_VERTICAL);
    TextView name=text(item.title,cobraModeColor("text"),cardTitleSize,cardTitleGravity);
    name.setMaxLines(2);name.setEllipsize(android.text.TextUtils.TruncateAt.END);
    if(item.series){
      name.setTag("tv_show_title_typography");
      name.setLineSpacing(0f,1.06f);
      name.setPadding(0,dp(5),0,dp(3));
    }
    card.addView(name,new LinearLayout.LayoutParams(-1,dp(item.series?54:42)));'''
    req(old in card,'TV card title anchor drift')
    card=card.replace(old,new,1)

    old='''    if(!sub.isEmpty()){
      TextView line=text(sub,cobraModeColor("muted"),10,Gravity.LEFT|Gravity.CENTER_VERTICAL);
      line.setMaxLines(1);line.setEllipsize(android.text.TextUtils.TruncateAt.END);
      card.addView(line,new LinearLayout.LayoutParams(-1,dp(22)));
    }'''
    new='''    if(!sub.isEmpty()){
      int metaColor=item.series&&!cobraModeDark()
          ?vtheme().color("cobra.tvShowCard.metadata.light",0xff566170)
          :cobraModeColor("muted");
      int metaGravity=item.series?(Gravity.LEFT|Gravity.TOP):(Gravity.LEFT|Gravity.CENTER_VERTICAL);
      TextView line=text(sub,metaColor,10,metaGravity);
      line.setMaxLines(1);line.setEllipsize(android.text.TextUtils.TruncateAt.END);
      if(item.series){
        line.setTag("tv_show_metadata_typography");
        line.setPadding(0,dp(3),0,dp(2));
      }
      card.addView(line,new LinearLayout.LayoutParams(-1,dp(item.series?30:22)));
    }'''
    req(old in card,'TV card metadata anchor drift')
    card=card.replace(old,new,1)
    s=replace_method(s,sig,card)

    # See All / filtered collections use the same cards; enlarge only TV Show grid rows.
    sig='private void cobraRenderVodCollection(CobraVodCollectionState state)'
    collection=method(s,sig)
    old='page.addView(row,new LinearLayout.LayoutParams(-1,dp(isCompact()?258:292)))'
    new='page.addView(row,new LinearLayout.LayoutParams(-1,dp(state.series?(isCompact()?278:312):(isCompact()?258:292))))'
    req(old in collection,'TV collection row height anchor drift')
    collection=collection.replace(old,new,1)
    s=replace_method(s,sig,collection)

    # Scope gates: movie values must remain explicitly encoded on the false branches.
    card=method(s,'private View cobraVodCard(VodItem item,boolean progress)')
    shelf=method(s,'private void cobraAddVodShelf(LinearLayout page,String title,ArrayList<VodItem> items,int limit,')
    collection=method(s,'private void cobraRenderVodCollection(CobraVodCollectionState state)')
    hero=method(s,'private View cobraVodHero(VodItem item, boolean series, android.widget.ViewFlipper carousel)')
    for token in (
        'item.series?11:12','item.series?54:42','item.series?30:22',
        'series?(isCompact()?278:312):(isCompact()?258:292)',
        'state.series?(isCompact()?278:312):(isCompact()?258:292)',
        '"tv".equalsIgnoreCase(provider.trim())?"TV":provider',
        'tv_show_title_typography','tv_show_metadata_typography',
        'tv_show_hero_metadata_typography'
    ):
        req(token in s,'2103225 typography contract missing: '+token)
    req('item.series?54:42' in card and 'item.series?30:22' in card,
        'movie card metrics are not explicitly preserved')
    req('(isCompact()?258:292)' in shelf and '(isCompact()?258:292)' in collection,
        'movie row heights not preserved')
    req(mh(s,PROTECTED)==protected_before,'Protected 2103224 behavior changed')

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
        'Expected exact locked 2103224 replay')
    req(receipt.get('native_engine_sha256')==NATIVE,'Native engine receipt drift')
    req(receipt.get('movie_details_unchanged_from_2103223') is True,
        'Locked movie details contract missing')
    req(receipt.get('tv_show_details_full_page') is True and receipt.get('tv_show_trailers_option') is True,
        'Locked TV Show details contract missing')

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
        tv_show_typography_only=True,tv_show_card_title_metrics_fixed=True,
        tv_show_metadata_clipping_fixed=True,tv_show_light_metadata_contrast_fixed=True,
        tv_show_hero_tv_capitalization_fixed=True,tv_show_font_family_unchanged=True,
        tv_show_shelf_order_unchanged=True,tv_show_data_unchanged=True,
        movie_card_metrics_unchanged=True,movie_details_unchanged=True,
        tv_show_details_unchanged=True,tv_show_trailers_unchanged=True,
        episode_browser_unchanged=True,playback_unchanged=True,providers_unchanged=True,
        live_tv_unchanged=True,drawer_owner_preserved=True,smart_return_preserved=True,
        choose_experience_ui_unchanged=True,health_center_unchanged=True,
        global_visual_renderer_unchanged=True
    )
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for name,row in receipt['files'].items(): req(sha(shell/name)==row['after'],'Receipt drift '+name)

    Path('audit225').mkdir(exist_ok=True)
    Path('audit225/scope.json').write_text(json.dumps({
        'build':VERSION,'parent':OLD_VERSION,
        'parent_locked_branch':'locked-infinity-cobra-2103224-movie-tv-details-trailers-passed',
        'authorized_delta':'TV Shows landing/collection typography metrics only',
        'activity_before_sha256':activity_before,'activity_after_sha256':activity_after,
        'frozen_files_sha256':frozen,'protected_2103224_methods_sha256':protected,
        'tv_show_typography':{
            'font_family_unchanged':True,
            'title_size_sp':11,'title_box_dp':54,'metadata_size_sp':10,'metadata_box_dp':30,
            'compact_shelf_height_dp':278,'regular_shelf_height_dp':312,
            'light_metadata_fallback':'#566170','hero_provider_tv_normalized_to_TV':True,
            'wrapping':'2 lines with END ellipsis','shelf_order_unchanged':True
        },
        'movies':{'card_metrics_unchanged':True,'details_unchanged':True,'trailers_unchanged':True},
        'tv_show_details_unchanged':True,'tv_show_trailers_unchanged':True,
        'episode_browser_unchanged':True,'playback_unchanged':True,'providers_unchanged':True,
        'native_engine_sha256':NATIVE,'native_engine_rebuilt':False,
        'live_tv_unchanged':True,'smart_return_preserved':True,'drawer_owner_preserved':True,
        'choose_experience_ui_unchanged':True,'health_center_unchanged':True,
        'status':'TEST CANDIDATE'
    },indent=2,sort_keys=True)+'\n')
    print('PASS: 2103225 fixes only TV Shows text metrics/contrast over locked 2103224')

def main():
    p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True)
    a=p.parse_args();apply(a.shell)

if __name__=='__main__':
    main()
