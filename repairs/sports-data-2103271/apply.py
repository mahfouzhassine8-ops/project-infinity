#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, json, difflib

ACTIVITY='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
GRADLE='tools/android/packaging/xbmc/build.gradle.in'
PARENT_ACTIVITY_SHA='5e7b930b410598f409446ddc26a876eb8afbb6d2ecb9accbd386bf1709f72196'
PARENT_APK='54223cd2dcc6ebbf1b0ddddc88114ca9c95541084077a7ea03dba7c6f7ac2259'
PARENT_COMMIT='fe36eda6020934e538b32f754d3175040960b2cc'
PARENT_RUN=36755538846
VERSION_CODE=2103271
RELEASE='1.0.9-Sports-Data-RC1'

def sha(data): return hashlib.sha256(data).hexdigest()
def once(s, old, new):
    count=s.count(old)
    if count!=1: raise AssertionError(f'Expected one anchor, found {count}: {old[:120]!r}')
    return s.replace(old,new,1)

OLD_SCOREBOARD='''    @Override public ArrayList<CobraSportsGame> scoreboard(CobraSportsLeagueSpec spec,long from,long to)throws Exception{
      SimpleDateFormat f=new SimpleDateFormat("yyyyMMdd",Locale.US);String dates=f.format(new Date(from))+"-"+f.format(new Date(to));
      String url=base(spec)+"/scoreboard?limit=100&dates="+dates;
      if("ncaaf".equals(spec.key))url+="&groups=80"; // FBS, not ESPN's default ranked-team subset.
      JSONObject root=cobraSportsJson(url);
      return cobraSportsParseScoreboard(spec,root);
    }'''

NEW_SCOREBOARD='''    @Override public ArrayList<CobraSportsGame> scoreboard(CobraSportsLeagueSpec spec,long from,long to)throws Exception{
      ArrayList<String> days=cobraSportsDateKeys(from,to);LinkedHashMap<String,CobraSportsGame> merged=new LinkedHashMap<>();
      ArrayList<java.util.concurrent.Callable<CobraSportsDayResult>> tasks=new ArrayList<>();
      for(String day:days)tasks.add(()->cobraSportsDay(spec,day));
      java.util.concurrent.ExecutorService pool=java.util.concurrent.Executors.newFixedThreadPool(Math.max(1,Math.min(4,tasks.size())));
      ArrayList<String> failures=new ArrayList<>();int successfulDays=0;
      try{
        for(java.util.concurrent.Future<CobraSportsDayResult> future:pool.invokeAll(tasks)){
          try{CobraSportsDayResult result=future.get();if(result.error!=null){failures.add(result.day+" "+cobraSportsErrorDetail(result.error));continue;}successfulDays++;for(CobraSportsGame game:result.games)merged.put(game.id,game);}
          catch(Exception e){failures.add(cobraSportsErrorDetail(e));}
        }
      }finally{pool.shutdownNow();}
      if(successfulDays==0)throw new java.io.IOException(failures.isEmpty()?"No sports date requests completed":android.text.TextUtils.join("; ",failures));
      return new ArrayList<>(merged.values());
    }
    private CobraSportsDayResult cobraSportsDay(CobraSportsLeagueSpec spec,String day){
      String cacheKey=spec.key+"|"+day;long now=System.currentTimeMillis();CobraSportsDayCache cached=mCobraSportsDayCache.get(cacheKey);String today=cobraSportsDateKey(now);long ttl=day.equals(today)?30000L:30L*60L*1000L;
      if(cached!=null&&now-cached.at<ttl)return new CobraSportsDayResult(day,new ArrayList<>(cached.games),null);
      String url=base(spec)+"/scoreboard?limit="+(spec.key.startsWith("ncaa")?500:200)+"&dates="+day;
      if("ncaaf".equals(spec.key))url+="&groups=80";
      if("ncaam".equals(spec.key))url+="&groups=50";
      try{ArrayList<CobraSportsGame> games=cobraSportsParseScoreboard(spec,cobraSportsJson(url));mCobraSportsDayCache.put(cacheKey,new CobraSportsDayCache(now,games));return new CobraSportsDayResult(day,games,null);}
      catch(Exception e){return new CobraSportsDayResult(day,new ArrayList<>(),e);}
    }'''

OLD_JSON='''  private JSONObject cobraSportsJson(String url)throws Exception{
    HttpURLConnection connection=(HttpURLConnection)new URL(url).openConnection();connection.setConnectTimeout(6000);connection.setReadTimeout(8000);connection.setInstanceFollowRedirects(true);connection.setRequestProperty("Accept","application/json");connection.setRequestProperty("Accept-Encoding","gzip");connection.setRequestProperty("User-Agent","Cobra-Sports/2103270");
    try{int status=connection.getResponseCode();if(status<200||status>=300)throw new java.io.IOException("Sports feed HTTP "+status);InputStream raw=new BufferedInputStream(connection.getInputStream());if("gzip".equalsIgnoreCase(connection.getContentEncoding()))raw=new GZIPInputStream(raw);ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] buffer=new byte[8192];int n,total=0;while((n=raw.read(buffer))!=-1){total+=n;if(total>6*1024*1024)throw new java.io.IOException("Sports response too large");out.write(buffer,0,n);}raw.close();return new JSONObject(new String(out.toByteArray(),StandardCharsets.UTF_8));}finally{connection.disconnect();}
  }'''

NEW_JSON='''  private JSONObject cobraSportsJson(String url)throws Exception{
    ArrayList<String> candidates=new ArrayList<>();candidates.add(url);if(url.startsWith("https://site.api.espn.com/"))candidates.add(url.replace("https://site.api.espn.com/","https://site.web.api.espn.com/"));ArrayList<String> failures=new ArrayList<>();
    for(String candidate:candidates)try{return cobraSportsJsonOnce(candidate);}catch(Exception e){failures.add(new URL(candidate).getHost()+" "+cobraSportsErrorDetail(e));}
    throw new java.io.IOException(android.text.TextUtils.join("; ",failures));
  }
  private JSONObject cobraSportsJsonOnce(String url)throws Exception{
    HttpURLConnection connection=(HttpURLConnection)new URL(url).openConnection();connection.setConnectTimeout(5000);connection.setReadTimeout(7000);connection.setInstanceFollowRedirects(true);connection.setRequestProperty("Accept","application/json");connection.setRequestProperty("Accept-Encoding","identity");connection.setRequestProperty("User-Agent","Mozilla/5.0 (Linux; Android 17) Cobra-Sports/2103271");
    try{int status=connection.getResponseCode();if(status<200||status>=300)throw new java.io.IOException("HTTP "+status);InputStream raw=new BufferedInputStream(connection.getInputStream());ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] buffer=new byte[8192];int n,total=0;while((n=raw.read(buffer))!=-1){total+=n;if(total>6*1024*1024)throw new java.io.IOException("Sports response too large");out.write(buffer,0,n);}raw.close();return new JSONObject(new String(out.toByteArray(),StandardCharsets.UTF_8));}finally{connection.disconnect();}
  }
  private static String cobraSportsDateKey(long when){return new SimpleDateFormat("yyyyMMdd",Locale.US).format(new Date(when));}
  private static ArrayList<String> cobraSportsDateKeys(long from,long to){ArrayList<String> out=new ArrayList<>();Calendar day=Calendar.getInstance();day.setTimeInMillis(Math.min(from,to));day.set(Calendar.HOUR_OF_DAY,12);day.set(Calendar.MINUTE,0);day.set(Calendar.SECOND,0);day.set(Calendar.MILLISECOND,0);Calendar end=Calendar.getInstance();end.setTimeInMillis(Math.max(from,to));end.set(Calendar.HOUR_OF_DAY,12);end.set(Calendar.MINUTE,0);end.set(Calendar.SECOND,0);end.set(Calendar.MILLISECOND,0);SimpleDateFormat f=new SimpleDateFormat("yyyyMMdd",Locale.US);for(int guard=0;!day.after(end)&&guard<12;guard++){out.add(f.format(day.getTime()));day.add(Calendar.DAY_OF_MONTH,1);}return out;}
  private static String cobraSportsErrorDetail(Exception e){if(e==null)return "Unknown error";String name=e.getClass().getSimpleName(),message=e.getMessage();return message==null||message.trim().isEmpty()?name:name+": "+message.trim();}
'''

CACHE_ANCHOR='''  private static final class CobraSportsChannelInfo{
    final Channel channel;final String text;final ArrayList<GuideProgram> programs;
    CobraSportsChannelInfo(Channel channel,String text,ArrayList<GuideProgram> programs){this.channel=channel;this.text=text;this.programs=programs;}
  }
'''

CACHE_ADD='''  private static final class CobraSportsChannelInfo{
    final Channel channel;final String text;final ArrayList<GuideProgram> programs;
    CobraSportsChannelInfo(Channel channel,String text,ArrayList<GuideProgram> programs){this.channel=channel;this.text=text;this.programs=programs;}
  }
  private static final class CobraSportsDayCache{
    final long at;final ArrayList<CobraSportsGame> games;
    CobraSportsDayCache(long at,ArrayList<CobraSportsGame> games){this.at=at;this.games=new ArrayList<>(games);}
  }
  private static final class CobraSportsDayResult{
    final String day;final ArrayList<CobraSportsGame> games;final Exception error;
    CobraSportsDayResult(String day,ArrayList<CobraSportsGame> games,Exception error){this.day=day;this.games=games;this.error=error;}
  }
  private final java.util.concurrent.ConcurrentHashMap<String,CobraSportsDayCache> mCobraSportsDayCache=new java.util.concurrent.ConcurrentHashMap<>();
'''

OLD_EMPTY='''    if(mCobraSportsGames.isEmpty()){LinearLayout empty=new LinearLayout(this);empty.setOrientation(LinearLayout.VERTICAL);empty.setGravity(Gravity.CENTER);empty.setPadding(dp(16),dp(48),dp(16),dp(48));TextView title=cobraText(mCobraSportsLoading?"LOADING SPORTS…":"SPORTS DATA UNAVAILABLE",cobraModeColor("text"),22);title.setGravity(Gravity.CENTER);TextView detail=cobraText(mCobraSportsLoading?"Building your live scoreboard and matching layer.":(mCobraSportsLastError.isEmpty()?"Refresh to try again.":mCobraSportsLastError),cobraModeColor("muted"),14);detail.setGravity(Gravity.CENTER);empty.addView(title,new LinearLayout.LayoutParams(-1,-2));empty.addView(detail,new LinearLayout.LayoutParams(-1,-2));body.addView(empty,new LinearLayout.LayoutParams(-1,-2));}'''

NEW_EMPTY='''    if(mCobraSportsGames.isEmpty()){LinearLayout empty=new LinearLayout(this);empty.setOrientation(LinearLayout.VERTICAL);empty.setGravity(Gravity.CENTER);empty.setPadding(dp(16),dp(24),dp(16),dp(30));boolean failed=!mCobraSportsLastError.isEmpty(),never=mCobraSportsLastRefresh==0L;TextView title=cobraText(mCobraSportsLoading||never?"LOADING SPORTS…":failed?"SPORTS DATA UNAVAILABLE":"NO GAMES SCHEDULED",cobraModeColor("text"),22);title.setGravity(Gravity.CENTER);TextView detail=cobraText(mCobraSportsLoading||never?"Connecting to the live sports feed…":failed?mCobraSportsLastError:"No games were returned for the current sports window.",cobraModeColor("muted"),14);detail.setGravity(Gravity.CENTER);empty.addView(title,new LinearLayout.LayoutParams(-1,-2));empty.addView(detail,new LinearLayout.LayoutParams(-1,-2));body.addView(empty,new LinearLayout.LayoutParams(-1,-2));}'''

OLD_REFRESH='''private void cobraSportsRefresh(boolean force){if(mCobraSportsLoading)return;long now=System.currentTimeMillis();if(!force&&!mCobraSportsGames.isEmpty()&&now-mCobraSportsLastRefresh<COBRA_SPORTS_STALE_MS){cobraSportsScheduleNext();return;}mCobraSportsLoading=true;cobraSportsRenderCurrent();Set<String> enabled=cobraSportsEnabledLeagues();Set<String> liveLeagues=new HashSet<>();for(CobraSportsGame g:mCobraSportsGames)if(g.live())liveLeagues.add(g.leagueKey);boolean liveTick=!force&&!liveLeagues.isEmpty()&&now-mCobraSportsLastRefresh<COBRA_SPORTS_IDLE_REFRESH_MS;final Set<String> fetch=liveTick?liveLeagues:enabled;final long from=now-86400000L,to=now+8L*86400000L;
    if(!submitCobraIo(()->{ArrayList<CobraSportsGame> fresh=new ArrayList<>();ArrayList<String> failures=new ArrayList<>(),failedKeys=new ArrayList<>();for(CobraSportsLeagueSpec spec:COBRA_SPORTS_SPECS)if(fetch.contains(spec.key)){try{fresh.addAll(mCobraSportsRepository.scoreboard(spec,from,to));}catch(Exception e){failures.add(spec.label);failedKeys.add(spec.key);}}publishCobraUi(()->{'''

NEW_REFRESH='''private void cobraSportsRefresh(boolean force){if(mCobraSportsLoading)return;long now=System.currentTimeMillis();if(!force&&!mCobraSportsGames.isEmpty()&&now-mCobraSportsLastRefresh<COBRA_SPORTS_STALE_MS){cobraSportsScheduleNext();return;}mCobraSportsLoading=true;cobraSportsRenderCurrent();Set<String> enabled=cobraSportsEnabledLeagues();Set<String> liveLeagues=new HashSet<>();for(CobraSportsGame g:mCobraSportsGames)if(g.live())liveLeagues.add(g.leagueKey);boolean liveTick=!force&&!liveLeagues.isEmpty()&&now-mCobraSportsLastRefresh<COBRA_SPORTS_IDLE_REFRESH_MS;final Set<String> fetch=liveTick?liveLeagues:enabled;final long from=now,to=now+7L*86400000L;
    if(!submitCobraIo(()->{ArrayList<CobraSportsGame> fresh=new ArrayList<>();ArrayList<String> failures=new ArrayList<>(),failedKeys=new ArrayList<>();for(CobraSportsLeagueSpec spec:COBRA_SPORTS_SPECS)if(fetch.contains(spec.key)){try{fresh.addAll(mCobraSportsRepository.scoreboard(spec,from,to));}catch(Exception e){failures.add(spec.label+" ("+cobraSportsErrorDetail(e)+")");failedKeys.add(spec.key);}}publishCobraUi(()->{'''

def patch_activity(s):
    s=once(s,CACHE_ANCHOR,CACHE_ADD)
    s=once(s,OLD_SCOREBOARD,NEW_SCOREBOARD)
    s=once(s,OLD_JSON,NEW_JSON)
    s=once(s,OLD_EMPTY,NEW_EMPTY)
    s=once(s,OLD_REFRESH,NEW_REFRESH)
    return s

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    shell=a.root/'shell-kodi';a.out.mkdir(parents=True,exist_ok=True)
    activity=shell/ACTIVITY;before=activity.read_text();assert sha(activity.read_bytes())==PARENT_ACTIVITY_SHA,'Not exact 2103270 Sports Hub source'
    after=patch_activity(before);activity.write_text(after)
    gradle=shell/GRADLE;g=gradle.read_text();g=once(g,'versionCode 2103270','versionCode 2103271');g=once(g,'versionName "1.0.9-Sports-Hub-RC1"','versionName "1.0.9-Sports-Data-RC1"');gradle.write_text(g)
    script=a.root/'scripts/infinity_background_resume.py';v=script.read_text();v=once(v,'VERSION_CODE = 2103270','VERSION_CODE = 2103271');v=once(v,"RELEASE = '1.0.9-Sports-Hub-RC1'",f"RELEASE = '{RELEASE}'");v=once(v,"BASE_COMMIT = '3804ae1a680606e15b931fa33537644b0dc21e20'",f"BASE_COMMIT = '{PARENT_COMMIT}'");v=once(v,"BASE_APK_SHA256 = 'f71fdfad769ae30e57c2c96ab4dbaf51062fc483e54f1702114517fcf47befce'",f"BASE_APK_SHA256 = '{PARENT_APK}'");script.write_text(v)
    package=a.root/'scripts/package_background_resume.py';v=package.read_text();v=v.replace('Infinity-2103270-Sports-Hub-RC1','Infinity-2103271-Sports-Data-RC1');v=once(v,"'base_run':36741769377",f"'base_run':{PARENT_RUN}");v=once(v,"ROOT/'repairs/sports-hub-2103270/DEVICE-TEST.md'","ROOT/'repairs/sports-data-2103271/DEVICE-TEST.md'");package.write_text(v)
    receipt=a.root/'engine/background-resume-source.json';r=json.loads(receipt.read_text());r.update(base_source_commit=PARENT_COMMIT,base_apk_sha256=PARENT_APK,version_code=VERSION_CODE,release=RELEASE,candidate_locked=False,physical_device_verified=False,complete_product_audit=False,sports_data_single_day_queries=True,sports_data_parallel_day_fetch=True,sports_data_day_cache=True,sports_data_host_fallback=True,sports_data_error_diagnostics=True,sports_empty_state_truthful=True)
    for n in [ACTIVITY,GRADLE]:r['files'].setdefault(n,{})['after']=sha((shell/n).read_bytes())
    receipt.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
    (a.out/'sports-data.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='candidate2103270/'+ACTIVITY,tofile='candidate2103271/'+ACTIVITY)))
    print('Applied 2103271 Sports data repair over exact 2103270 source; player/provider/Multi-View ownership unchanged.')

if __name__=='__main__':main()
