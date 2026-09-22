#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
VERSION=2103214
OLD_VERSION=2103213
OLD_NAME='1.0.9-Cobra-Live-Blue-Ambient-Return-RC1'
NEW_NAME='1.0.9-Cobra-Media-Details-Final-RC1'
SOURCE='tools/android/packaging/xbmc/src/'
NATIVE_SHA='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'
INCLUDE_SHA='e68bf4670b89defeb9d7df62d007abeabaef5e72e8066ba47ed8144b0fab88eb'
PARENT={
 SOURCE+'InfinityLiveActivity.java.in':'d749c82e64a787f8d20078279ee5110c90045767ea84bb7d61098cd8dbb563e1',
 SOURCE+'Splash.java.in':'7c9e8930a41da2e7c5a75fd9d18195413e1f09701d6e3dcaa196a2f848baca9c',
 SOURCE+'Main.java.in':'ddf18d30c4040369b30e861ded588a53846ff3de319a89a219344771f8db9318',
}
PROTECTED={
 'private void cobraOpenLiveTv()':'ca2104682cc43724a138310dac87361973d57a40a00a5db0e6557a3fa8f6a602',
 'private void showGuide()':'f57772610779aea49fc43c6d94db2df804e911e9c82cf224d9e5f6f96f9a93a4',
 'private void startSinglePlayer(String url)':'1c1a40c28072b5876e61ecedc5c64cfb6483b8d1c464041a16ee2b0128213708',
 'private void cobraShowQuickPeek(Channel channel,View anchor)':'bea049b1f6941709e13545eefd647915c64c2500e6b6716da2e246ab3718f869',
 'private void cobraStartLocalTimeshift':'758df5bc2d2c32df5836b13c23b33a44c35a90ef910cf3513516e4f8a3a6800a',
 'private void playChannel(Channel channel)':'48729254f6a27441b487fe8425b899ede48a804819c3d6bb466695d654087de3',
 'private void startCobraPreview(Channel channel)':'db8403d7256e8d353c9b7cef8397076ef7874646782d3972e7b3db2afa0a227c',
 'private void releaseSinglePlayer()':'1cd0ff7182a28e632f6601202c57050c87de10a923080ee64c062ced76f5b385',
 'private void releaseMulti()':'cc1a975f97fbb11dc9faa12f07e76045980e89911ed1f6cc7f0d8899886a1cad',
 'private LoadResult loadXtream(LiveSource source)':'6e9c2300e1c65095f2f8340f8764783e6852cbd8ccbc23ad238d14172e3ac2cb',
 'private LoadResult loadM3u(LiveSource source)':'ba2a26616379cd59e6b0514258e2734a19925f48627065ca33095793977d11b0',
 'private void cobraRefreshAmbient()':'5cab64cb1b99aa633b657750bbbf87194bf9991156727621a7909a884f522d09',
 'private void cobraRefreshLiveAmbientSurfaces(int mode,boolean live,int tint)':'3257363ae2ec1139403ded5861c17383f3ad12f36d87e457f8c70db64d2cee8d',
 'private void cobraApplyNightCinema(View header,View footer,View pause)':'aff0de0d495b9e18dad3ddbcc8e6dd69f55ae8f02df98c7a1084b339be657ad7',
 'private void cobraReturnFromSettings()':'c9af10a28c2c35135b04c950194f0282817ebe0cbed56b783dff7ef8566e0461',
 'private void showSettings()':'a80d4b133ba5e5ae4fd7ac00a2f67333591dd8f85900753c86be2efe01871622',
 'private void cobraDrawerDestination(LinearLayout parent,String icon,String label,String destination,Runnable action)':'e2802f9d51542e6bb40c6c4fa0c0ffd4a7e3f0f8802d258a7de93d53bf2b8197',
 'private void renderVodBrowse(ArrayList<VodItem> items, boolean series, ArrayList<String> failures)':'3a8963e3a77d43afee84df615563588b965d3b2f8f328d5b9f12bd413f1ccf0a',
 'private View cobraVodHero(VodItem item, boolean series, android.widget.ViewFlipper carousel)':'d96c2c00a16bc8f35f4eb670872fbc0d59c9cf36511560cd88c43ff9903bdc51',
 'private void cobraAddVodShelf(LinearLayout page,String title,ArrayList<VodItem> items,int limit,':'f39a00245165d9174ca7bc4d6ffe83ed992cdb4feb3f7a305c2b9cc0f3070764',
 'private void cobraAddVodGenres(LinearLayout page,ArrayList<VodItem> items,boolean series)':'a7531a9253d384fb3ee7de497cd47c914a98501f240f180bf02680f1d72e2e23',
}

def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha(path): return sha_bytes(Path(path).read_bytes())
def require(v,m):
 if not v: raise RuntimeError(m)
def once(text,old,new,label):
 require(text.count(old)==1,f'{label} anchor drift ({text.count(old)})');return text.replace(old,new,1)
def method_range(text,sig):
 i=text.find(sig);require(i>=0,'Missing method: '+sig);b=text.find('{',i);d=0
 for j in range(b,len(text)):
  if text[j]=='{':d+=1
  elif text[j]=='}':
   d-=1
   if d==0:return i,j+1
 raise RuntimeError('Unbalanced method: '+sig)
def method(text,sig):
 a,b=method_range(text,sig);return text[a:b]
def contract(text):
 out={}
 for sig,expected in PROTECTED.items():
  digest=sha_bytes(method(text,sig).encode());require(digest==expected,'Protected 2103213 drift: '+sig);out[sig]=digest
 return out

def remove_method_after(text,sig,start):
 pos=text.find(sig,start);require(pos>=0,'Missing old method after include: '+sig)
 sub=text[pos:];a,b=method_range(sub,sig);return text[:pos+a]+text[pos+b:]

def patch_activity(path:Path):
 s=path.read_text();before=contract(s)
 include=ROOT/'media-final.java.inc';require(sha(include)==INCLUDE_SHA,'Reviewed media include drift')

 fields='''  private final ArrayList<VodItem> mEpisodeQueue = new ArrayList<>();\n  private int mEpisodeQueueIndex = -1;\n'''
 fields2='''  private final ArrayList<VodItem> mEpisodeQueue = new ArrayList<>();
  private int mEpisodeQueueIndex = -1;
  private final ArrayList<VodItem> mCobraVodMoviesCatalog = new ArrayList<>();
  private final ArrayList<VodItem> mCobraVodShowsCatalog = new ArrayList<>();
  private VodItem mCobraCurrentVodItem;
  private VodItem mCobraActiveSeriesItem;
'''
 s=once(s,fields,fields2,'Media final fields')
 s=once(s,'cobraPublishNavigation(ticket,() -> renderVodBrowse(items, series, failures));',
        'cobraPublishNavigation(ticket,() -> { cobraRememberVodCatalog(items, series); renderVodBrowse(items, series, failures); });','Catalog handoff')

 recent_old='''  private ArrayList<VodItem> cobraVodRecentSubset(ArrayList<VodItem> items) {
    ArrayList<VodItem> out=new ArrayList<>(items);
    Collections.sort(out,(a,b)->Long.compare(b.addedEpoch,a.addedEpoch));
    return out;
  }'''
 recent_new='''  private ArrayList<VodItem> cobraVodRecentSubset(ArrayList<VodItem> items) {
    ArrayList<VodItem> out=new ArrayList<>(items);final int currentYear=java.util.Calendar.getInstance().get(java.util.Calendar.YEAR);
    Collections.sort(out,(a,b)->{
      int ay=cobraVodYearNumber(a),by=cobraVodYearNumber(b);
      int ab=ay>=currentYear-1?0:ay==0?1:2,bb=by>=currentYear-1?0:by==0?1:2;
      if(ab!=bb)return Integer.compare(ab,bb);
      if(ay!=by)return Integer.compare(by,ay);
      int added=Long.compare(b.addedEpoch,a.addedEpoch);return added!=0?added:a.title.compareToIgnoreCase(b.title);
    });
    return out;
  }'''
 s=once(s,recent_old,recent_new,'Recent Releases current-year priority')

 cont_old='''        if(exact.equals(o.optString("key")))return o;
        if(item.series && item.title.equalsIgnoreCase(o.optString("group","")) &&
            o.optString("key","").startsWith(item.sourceId+":"))return o;
'''
 cont_new='''        if(exact.equals(o.optString("key")))return o;
        if(item.series){
          String parent=o.optString("parent","");String group=o.optString("group","");
          if((item.title.equalsIgnoreCase(parent)||group.toLowerCase(Locale.US).startsWith(item.title.toLowerCase(Locale.US)+" •"))
              &&o.optString("key","").startsWith(item.sourceId+":"))return o;
        }
'''
 s=once(s,cont_old,cont_new,'Series continue parent')

 insert=s.find('  private void cobraShowVodCollection(String title,ArrayList<VodItem> items,boolean series) {')
 require(insert>=0,'Collection method insertion marker missing')
 helpers=include.read_text();s=s[:insert]+helpers+'\n'+s[insert:];old_start=insert+len(helpers)
 for sig in [
   '  private void cobraShowVodCollection(String title,ArrayList<VodItem> items,boolean series)',
   '  private void cobraShowVodDetails(VodItem item)',
   '  private void openSeries(VodItem item)']:
  s=remove_method_after(s,sig,old_start)

 play_old='''  private void playVodUrl(VodItem item, String url, String group) {
    releaseMulti();
    closePlayer();
    mPlayingVodKey = item.sourceId + ":" + item.id;
'''
 play_new='''  private void playVodUrl(VodItem item, String url, String group) {
    releaseMulti();
    closePlayer();
    mCobraCurrentVodItem = item;
    if(item.parentTitle.isEmpty() && !item.series) mCobraActiveSeriesItem = null;
    mPlayingVodKey = item.sourceId + ":" + item.id;
'''
 s=once(s,play_old,play_new,'Current VOD bookkeeping')

 save_old='''        current.put("duration", dur);
        current.put("updated", System.currentTimeMillis());
        next.put(current);
'''
 save_new='''        current.put("duration", dur);
        current.put("updated", System.currentTimeMillis());
        if(mCobraCurrentVodItem!=null){
          current.put("source",mCobraCurrentVodItem.sourceId);current.put("id",mCobraCurrentVodItem.id);current.put("extension",mCobraCurrentVodItem.extension);
          current.put("parent",mCobraCurrentVodItem.parentTitle);current.put("season",mCobraCurrentVodItem.seasonNumber);current.put("episode",mCobraCurrentVodItem.episodeNumber);
          if(mCobraActiveSeriesItem!=null){current.put("parent_source",mCobraActiveSeriesItem.sourceId);current.put("parent_id",mCobraActiveSeriesItem.id);current.put("parent_title",mCobraActiveSeriesItem.title);}
        }
        next.put(current);
'''
 s=once(s,save_old,save_new,'Structured continue metadata')

 resume_old='''  private void playSavedVod(String key, String title, String url, String group, long position) {
    if (url == null || url.isEmpty()) return;
    releaseMulti(); closePlayer();
    mPlayingVodKey = key; mPlayingVodTitle = title; mPendingResumeMs = position;
'''
 resume_new='''  private void playSavedVod(String key, String title, String url, String group, long position) {
    if (url == null || url.isEmpty()) return;
    releaseMulti(); closePlayer();
    mCobraCurrentVodItem=null;mCobraActiveSeriesItem=null;
    try{
      JSONArray list=new JSONArray(mPrefs.getString(mFeatures.profileKey("continue_items"),"[]"));
      for(int i=0;i<list.length();i++){JSONObject o=list.optJSONObject(i);if(o==null||!key.equals(o.optString("key")))continue;
        String source=o.optString("source",key.contains(":")?key.substring(0,key.indexOf(':')):"");String id=o.optString("id",key.contains(":")?key.substring(key.indexOf(':')+1):key);
        String parent=o.optString("parent","");int season=o.optInt("season",0),episode=o.optInt("episode",0);String extension=o.optString("extension","mp4");
        mCobraCurrentVodItem=new VodItem(source,id,title,parent.isEmpty()?group:parent,"",extension,false,0L,0.0,"",season,episode,"","",parent);
        String parentId=o.optString("parent_id",""),parentSource=o.optString("parent_source",source),parentTitle=o.optString("parent_title",parent);
        if(!parentId.isEmpty()&&!parentTitle.isEmpty())mCobraActiveSeriesItem=new VodItem(parentSource,parentId,parentTitle,"Other","","mp4",true);break;
      }
    }catch(Exception ignored){}
    mPlayingVodKey = key; mPlayingVodTitle = title; mPendingResumeMs = position;
'''
 s=once(s,resume_old,resume_new,'Continue Watching context restore')

 ended_old='''        }else if(state==Player.STATE_ENDED&&!mPlayingVodKey.isEmpty()) {
          saveVodProgress();
          final long episodeEpoch=mCobraPlaybackPolicy.epoch;
          if(!mEpisodeQueue.isEmpty()&&mEpisodeQueueIndex+1<mEpisodeQueue.size())mMain.postDelayed(()->{
            if(current()&&player==mPlayer&&player.getPlaybackState()==Player.STATE_ENDED&&mCobraPlaybackPolicy.acceptsRetry(episodeEpoch,player.getPlayWhenReady(),cobraPlaybackMayRun(player)))playNextEpisode();
          },650L);
        }
'''
 ended_new='''        }else if(state==Player.STATE_ENDED&&!mPlayingVodKey.isEmpty()) {
          saveVodProgress();
          String watchedGroup=mCobraCurrentVodItem==null?"":mCobraCurrentVodItem.parentTitle;
          cobraMarkVodWatched(mPlayingVodKey,watchedGroup);
          final long episodeEpoch=mCobraPlaybackPolicy.epoch;
          if(!mEpisodeQueue.isEmpty()&&mEpisodeQueueIndex+1<mEpisodeQueue.size())mMain.postDelayed(()->{
            if(current()&&player==mPlayer&&player.getPlaybackState()==Player.STATE_ENDED&&mCobraPlaybackPolicy.acceptsRetry(episodeEpoch,player.getPlayWhenReady(),cobraPlaybackMayRun(player)))playNextEpisode();
          },650L);
          else mMain.postDelayed(()->{if(current()&&player==mPlayer&&player.getPlaybackState()==Player.STATE_ENDED)cobraShowVodCompletion();},420L);
        }
'''
 s=once(s,ended_old,ended_new,'Completion actions preserving autoplay')

 sig='  private static final class VodItem {';a,b=method_range(s,sig)
 vod='''  private static final class VodItem {
    final String sourceId;
    final String id;
    final String title;
    final String category;
    final String icon;
    final String extension;
    final boolean series;
    final long addedEpoch;
    final double rating;
    final String year;
    final int seasonNumber;
    final int episodeNumber;
    final String airDate;
    final String description;
    final String parentTitle;
    VodItem(String sourceId, String id, String title, String category, String icon,
            String extension, boolean series) {
      this(sourceId,id,title,category,icon,extension,series,0L,0.0,"",0,0,"","","");
    }
    VodItem(String sourceId, String id, String title, String category, String icon,
            String extension, boolean series, long addedEpoch, double rating, String year) {
      this(sourceId,id,title,category,icon,extension,series,addedEpoch,rating,year,0,0,"","","");
    }
    VodItem(String sourceId, String id, String title, String category, String icon,
            String extension, boolean series, long addedEpoch, double rating, String year,
            int seasonNumber, int episodeNumber, String airDate, String description, String parentTitle) {
      this.sourceId=sourceId;this.id=id;this.title=title;this.category=category;this.icon=icon;
      this.extension=extension;this.series=series;this.addedEpoch=addedEpoch;this.rating=rating;
      this.year=year==null?"":year.trim();this.seasonNumber=seasonNumber;this.episodeNumber=episodeNumber;
      this.airDate=airDate==null?"":airDate.trim();this.description=description==null?"":description.trim();
      this.parentTitle=parentTitle==null?"":parentTitle.trim();
    }
  }'''
 s=s[:a]+vod+s[b:]

 for token in ['Play Next Episode','Season "+season','Recently Added','Watch state','Cast & Crew','More Like This','Collection  •  ','cobraMarkVodWatched','cobraShowVodCompletion','No titles match these filters.','✓ In My List']:
  require(token in s,'Missing 2103214 final media contract: '+token)
 path.write_text(s)
 require(contract(s)==before,'Protected 2103213 behavior changed')

def patch_identity(shell):
 gradle=shell/'tools/android/packaging/xbmc/build.gradle.in';g=gradle.read_text();g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','Gradle version');g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','Gradle name');gradle.write_text(g)
 runtime=Path('scripts/infinity_background_resume.py');r=runtime.read_text();r=once(r,f'VERSION_CODE = {OLD_VERSION}',f'VERSION_CODE = {VERSION}','Runtime version');r=once(r,"RELEASE = '"+OLD_NAME+"'","RELEASE = '"+NEW_NAME+"'",'Runtime name');runtime.write_text(r)
 pack=Path('scripts/package_background_resume.py');p=pack.read_text();old='Infinity-'+OLD_NAME;new='Infinity-'+NEW_NAME;require(p.count(old)>=2,'Packager identity drift');pack.write_text(p.replace(old,new));return gradle

def apply(shell):
 for name,digest in PARENT.items():require(sha(shell/name)==digest,'Not exact locked 2103213 parent: '+name)
 activity=shell/(SOURCE+'InfinityLiveActivity.java.in');patch_activity(activity)
 require(sha(shell/(SOURCE+'Splash.java.in'))==PARENT[SOURCE+'Splash.java.in'],'Infinity Health/chooser changed')
 require(sha(shell/(SOURCE+'Main.java.in'))==PARENT[SOURCE+'Main.java.in'],'Kodi Main changed')
 gradle=patch_identity(shell)

 receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text());require(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,'Wrong 2103213 receipt')
 for name in PARENT:require(name in receipt['files'],'Receipt missing '+name);receipt['files'][name]['after']=sha(shell/name)
 rel='tools/android/packaging/xbmc/build.gradle.in';receipt['files'][rel]['after']=sha(gradle)
 receipt.update(version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,candidate_locked=False,physical_device_verified=False,runtime_device_tested=False,
   native_engine_rebuilt=False,native_engine_reused_from_2103209=True,native_engine_sha256=NATIVE_SHA,
   final_media_refinement=True,main_media_landing_structure_unchanged=True,recent_releases_current_year_priority=True,
   tv_season_episode_browser=True,tv_resume_episode=True,tv_play_next_episode=True,tv_episode_progress=True,tv_episode_thumbnails=True,tv_episode_air_dates=True,
   collection_metadata_browse=True,collection_sort_filter=True,details_more_like_this=True,details_cast_crew=True,details_my_list_state=True,
   completion_actions=True,autoplay_behavior_preserved=True,genre_empty_clear_filters=True,
   live_tv_blue_ambient_unchanged=True,settings_return_unchanged=True,health_center_unchanged=True,video_recolored=False)
 receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
 for name,row in receipt['files'].items():require(sha(shell/name)==row['after'],'Final receipt drift: '+name)
 Path('audit214').mkdir(exist_ok=True)
 Path('audit214/scope.json').write_text(json.dumps({
   'build':VERSION,'parent_build':OLD_VERSION,'native_engine_sha256':NATIVE_SHA,'changed_java_files':[SOURCE+'InfinityLiveActivity.java.in'],
   'native_engine_rebuilt':False,'health_center_unchanged':True,'main_unchanged':True,
   'live_tv_blue_ambient_unchanged':True,'settings_return_unchanged':True,'main_media_landing_structure_unchanged':True,
   'recent_releases':'current/recent release year prioritized without displaying a year in the row name',
   'tv_show_browser':['season chips','episode thumbnails','episode number/title','air date','watched/unwatched/progress','Resume Episode','Play Next Episode'],
   'deep_browse':['Sort: Newest/A-Z/Rating/Recently Added','Provider filter','Watched/Unwatched filter','My List filter','Genre refinement','Clear filters empty state'],
   'details':['metadata','collection/franchise when supplied','Cast & Crew when supplied','More Like This','dynamic My List state'],
   'completion':['Movies: Back to Movies/More Like This','TV final episode: Back to Show/Back to Shows','existing automatic next episode preserved'],
   'video_recolored':False,'status':'TEST CANDIDATE'
 },indent=2)+'\n')
 print('PASS: 2103214 final Movies/TV Shows refinement applied over locked 2103213; protected systems unchanged')

def main():
 p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);args=p.parse_args();apply(args.shell)
if __name__=='__main__':main()
