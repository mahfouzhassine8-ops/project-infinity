package com.projectinfinity.kodi;

import android.os.Handler;
import android.os.Looper;
import java.io.IOException;
import java.lang.reflect.Proxy;
import java.text.SimpleDateFormat;
import java.time.Duration;
import java.util.*;
import org.json.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;
import static com.projectinfinity.kodi.CobraNavigationUiTest.*;

/** All league variants exercise the production repository result merger, refresh callback,
 * card presentation and ticker with controlled data. No device/network timing claims. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=android.app.Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE) @LooperMode(LooperMode.Mode.PAUSED)
public class CobraSportsLiveFeedTest {
  CobraProRefinementTest ui;InfinityLiveActivity a;Object realRepository;
  final Map<String,Object> replies=new LinkedHashMap<>();final List<String> requests=new ArrayList<>();
  final Map<String,List<String>> requestedDays=new LinkedHashMap<>();
  String[] leagues={"nfl","nba","mlb","nhl","ncaaf","ncaam","wnba","epl","ucl","mls","laliga","bundesliga","seriea","ligue1","uel"};

  @Before public void setup()throws Exception{
    ui=new CobraProRefinementTest();ui.setup();a=ui.a;ui.regular();
    ui.base.prefs.edit().putStringSet("cobra_sports_enabled_leagues",new HashSet<>(Arrays.asList(leagues))).commit();
    ((PendingIo)get(a,"mIo")).tasks.clear();realRepository=get(a,"mCobraSportsRepository");
    Class<?> type=Class.forName(InfinityLiveActivity.class.getName()+"$CobraSportsRepository");
    put(a,"mCobraSportsRepository",Proxy.newProxyInstance(type.getClassLoader(),new Class[]{type},(proxy,method,args)->{
      if(method.getName().equals("scoreboard")){
        String league=(String)get(args[0],"key");requests.add(league);
        requestedDays.put(league,(List<String>)call(a,"cobraSportsFetchDays",args[1],args[2]));
        Object reply=replies.get(league);if(reply instanceof Exception)throw (Exception)reply;
        return reply==null?board(Collections.emptyList(),Collections.emptyList()):reply;
      }
      if(method.getName().equals("label"))return "Controlled ESPN feed boundary";
      return new ArrayList<>();
    }));
  }
  @After public void cleanup()throws Exception{if(ui!=null)ui.cleanup();}
  Object spec(String league)throws Exception{return call(a,"cobraSportsSpec",league);}
  Object board(List<Object> games,List<String> failures)throws Exception{
    Object result=construct("CobraSportsBoardResult");((List)get(result,"games")).addAll(games);
    ((List)get(result,"failures")).addAll(failures);put(result,"successfulDays",1);return result;
  }
  JSONObject payload(String id,String away,String home,String state,int period)throws Exception{
    JSONObject type=new JSONObject().put("state",state).put("completed","post".equals(state))
      .put("name","post".equals(state)?"STATUS_FINAL":"STATUS_IN_PROGRESS").put("shortDetail","Period "+period+" • 2:33");
    JSONArray teams=new JSONArray();for(String side:new String[]{"away","home"})teams.put(new JSONObject().put("homeAway",side)
      .put("score",side.equals("away")?away:home).put("team",new JSONObject().put("id",side).put("displayName",side+" team")
      .put("shortDisplayName",side).put("abbreviation",side.equals("away")?"AWY":"HME")));
    JSONObject event=new JSONObject().put("id",id).put("date","2026-10-07T02:00Z")
      .put("status",new JSONObject().put("period",period).put("type",type))
      .put("competitions",new JSONArray().put(new JSONObject().put("competitors",teams)));
    return new JSONObject().put("events",new JSONArray().put(event));
  }
  Object game(String league,String id,String away,String home,String state,int period)throws Exception{
    return ((List)call(a,"cobraSportsParseFeed",spec(league),payload(id,away,home,state,period))).get(0);
  }
  void clearGames()throws Exception{
    call(a,"cobraRemoveScoreTicker");ui.games().clear();((Map)get(a,"mCobraScoreSeen")).clear();ui.pending().clear();replies.clear();requests.clear();requestedDays.clear();
    ((PendingIo)get(a,"mIo")).tasks.clear();((Handler)get(a,"mMain")).removeCallbacks((Runnable)get(a,"mCobraSportsTick"));
  }
  void fetch(boolean force)throws Exception{
    call(a,"cobraSportsRefresh",force);((PendingIo)get(a,"mIo")).drain();ui.base.f.frames(4);
    assertFalse((Boolean)get(a,"mCobraSportsLoading"));
  }
  void due()throws Exception{put(a,"mCobraSportsLastRefresh",System.currentTimeMillis()-45001L);}
  void delayed(Object game)throws Exception{
    assertTrue((Boolean)call(a,"cobraSportsDelayed",game));
    CobraProUi.SportsGame card=(CobraProUi.SportsGame)call(a,"cobraProSportsUiGame",game);
    assertEquals("Score delayed",card.score);assertEquals("Waiting for live feed",card.status);
    assertTrue(card.meta.contains("SCORE DELAYED"));assertFalse(card.meta.contains("2:33"));
    assertTrue(((String)call(a,"cobraSportsScoreLine",game)).contains("Score delayed"));
    CobraProUi.Program program=(CobraProUi.Program)call(a,"cobraProSportsProgram",game);assertEquals("Score delayed",program.sportsScore);
  }

  @Test public void allFifteenLeaguesRetainCurrentDateFailureBesideCachedSchedules()throws Exception{
    assertEquals(15,((Object[])get(a,"COBRA_SPORTS_SPECS")).length);
    for(String league:leagues){
      Object future=game(league,"future","0","0","pre",0);long receipt=(Long)get(future,"feedUpdatedAtMs");
      Object failed=construct("CobraSportsDayResult","20261007",new ArrayList<>(),new IOException("fixture current-day timeout"));
      Object cached=construct("CobraSportsDayResult","20261008",new ArrayList<>(Arrays.asList(future)),null);
      Object result=call(a,"cobraSportsCollectDays",Arrays.asList(failed,cached));
      assertEquals(league,1,get(result,"successfulDays"));assertEquals(1,((List)get(result,"games")).size());
      assertTrue(((List)get(result,"failures")).get(0).toString().contains("20261007"));
      assertEquals("Cached schedules retain their original receipt",receipt,get(future,"feedUpdatedAtMs"));
    }
  }

  @Test public void midnightAndDstWindowsKeepPreviousEveningAcrossDeviceZones()throws Exception{
    TimeZone original=TimeZone.getDefault();try{
      for(String zone:new String[]{"America/Detroit","America/Los_Angeles","UTC","Asia/Tokyo"}){
        TimeZone.setDefault(TimeZone.getTimeZone(zone));SimpleDateFormat format=new SimpleDateFormat("yyyy-MM-dd HH:mm",Locale.US);
        for(String date:new String[]{"2026-10-07 00:24","2026-11-01 23:30","2026-03-08 23:30"}){
          long now=format.parse(date).getTime();long tomorrow=(Long)call(a,"cobraSportsShiftDay",now,1);
          List<String> days=(List<String>)call(a,"cobraSportsFetchDays",now,tomorrow);
          assertEquals(zone+" "+date,3,days.size());
          assertEquals(call(a,"cobraSportsDateKey",call(a,"cobraSportsShiftDay",now,-1)),days.get(0));
          assertEquals(call(a,"cobraSportsDateKey",now),days.get(1));assertEquals(call(a,"cobraSportsDateKey",tomorrow),days.get(2));
        }
      }
    }finally{TimeZone.setDefault(original);}
  }

  @Test public void liveAndPreviousDateCachesNeverUseLongScheduleTtl()throws Exception{
    long now=System.currentTimeMillis();String yesterday=(String)call(a,"cobraSportsDateKey",call(a,"cobraSportsShiftDay",now,-1));
    String later=(String)call(a,"cobraSportsDateKey",call(a,"cobraSportsShiftDay",now,3));
    for(String league:leagues){
      Object live=game(league,"live","3","4","in",2);Object cache=construct("CobraSportsDayCache",now-31000L,new ArrayList<>(Arrays.asList(live)));
      assertEquals(30000L,call(a,"cobraSportsDayTtl",yesterday,cache,now));assertEquals(30000L,call(a,"cobraSportsDayTtl",later,cache,now));
      put(live,"state","pre");put(live,"startMs",now+3L*86400000L);
      assertEquals(1800000L,call(a,"cobraSportsDayTtl",later,cache,now));
      put(live,"startMs",now+20000L);assertEquals(30000L,call(a,"cobraSportsDayTtl",later,cache,now));
    }
  }

  @Test public void repositoryCacheHitDoesNotRestampEventFreshness()throws Exception{
    long now=System.currentTimeMillis();String today=(String)call(a,"cobraSportsDateKey",now);
    for(String league:leagues){
      Object live=game(league,"live","3","4","in",2);put(live,"feedUpdatedAtMs",now-20000L);
      Object cache=construct("CobraSportsDayCache",now-20000L,new ArrayList<>(Arrays.asList(live)));
      ((Map)get(a,"mCobraSportsDayCache")).put(league+"|"+today,cache);
      Object day=call(realRepository,"cobraSportsDay",spec(league),today);assertNull(get(day,"error"));
      Object found=((List)get(day,"games")).get(0);assertSame(live,found);assertEquals(now-20000L,get(found,"feedUpdatedAtMs"));
    }
  }

  @Test public void partialFailureInEveryLeagueLeavesHealthyScoresAndTickerWorking()throws Exception{
    for(int i=0;i<leagues.length;i++){
      clearGames();String league=leagues[i],other=leagues[(i+1)%leagues.length];
      Object old=game(league,"old","67","93","in",3);long receipt=System.currentTimeMillis()-180000L;put(old,"feedUpdatedAtMs",receipt);ui.games().add(old);
      Object fresh=game(other,"healthy","82","109","in",4);
      replies.put(league,board(Collections.emptyList(),Arrays.asList("today (fixture timeout)")));replies.put(other,board(Arrays.asList(fresh),Collections.emptyList()));
      fetch(true);assertSame(old,call(a,"cobraSportsGame","old"));assertEquals(receipt,get(old,"feedUpdatedAtMs"));delayed(old);
      assertTrue(((String)get(a,"mCobraSportsLastError")).contains("fixture timeout"));
      assertNotNull(league,ui.ticker());assertEquals(ui.key(fresh),get(a,"mCobraScoreShownKey"));assertTrue(ui.ticker().getText().toString().contains("82"));
      ui.assertNoPlaybackMutation(0);
    }
  }

  @Test public void confirmedScorePeriodAndFinalChangesReachCardAndTickerForEveryLeague()throws Exception{
    for(String league:leagues){
      clearGames();Object old=game(league,"live","67","93","in",3);replies.put(league,board(Arrays.asList(old),Collections.emptyList()));fetch(true);
      assertNotNull(league+" initial feed",ui.ticker());ui.finishCurrent();assertNull(ui.ticker());
      Object updated=game(league,"live","82","109","in",4);replies.put(league,board(Arrays.asList(updated),Collections.emptyList()));fetch(true);
      CobraProUi.SportsGame card=(CobraProUi.SportsGame)call(a,"cobraProSportsUiGame",updated);assertEquals("82  -  109",card.score);
      assertNotNull(league+" score change",ui.ticker());assertTrue(ui.ticker().getText().toString().contains("82"));ui.finishCurrent();
      put(updated,"detail","Period 4 • 2:32");fetch(true);assertNull(league+" clock only",ui.ticker());
      put(updated,"period",5);fetch(true);assertNotNull(league+" period change",ui.ticker());ui.finishCurrent();
      Object finalGame=game(league,"live","82","109","post",5);replies.put(league,board(Arrays.asList(finalGame),Collections.emptyList()));fetch(true);
      assertNotNull(league+" final",ui.ticker());assertTrue(ui.ticker().getText().toString().startsWith("FINAL"));ui.finishCurrent();fetch(true);assertNull(ui.ticker());ui.assertNoPlaybackMutation(0);
    }
  }

  @Test public void recoveryWithIdenticalScoreDoesNotInventAnAlert()throws Exception{
    Object old=game("nba","live","67","93","in",3);replies.put("nba",board(Arrays.asList(old),Collections.emptyList()));fetch(true);ui.finishCurrent();
    replies.put("nba",new IOException("NBA offline"));fetch(true);delayed(old);assertNull(ui.ticker());
    Object same=game("nba","live","67","93","in",3);replies.put("nba",board(Arrays.asList(same),Collections.emptyList()));fetch(true);assertNull("Recovered same score is not a new scoring event",ui.ticker());
    Object changed=game("nba","live","69","93","in",3);replies.put("nba",board(Arrays.asList(changed),Collections.emptyList()));fetch(true);assertNotNull(ui.ticker());assertTrue(ui.ticker().getText().toString().contains("69"));
  }

  @Test public void validEmptyFeedCreatesNoGamesAndDelaysAnOmittedLiveEvent()throws Exception{
    clearGames();fetch(true);assertTrue(ui.games().isEmpty());assertNull(ui.ticker());assertEquals("",get(a,"mCobraSportsLastError"));
    Object old=game("mlb","live","5","1","in",6);ui.games().add(old);ui.refresh();ui.finishCurrent();
    fetch(true);delayed(old);assertNull(ui.ticker());assertSame("Missing data must not tear down existing playback",ui.base.player,get(a,"mCobraPreviewPlayer"));ui.assertNoPlaybackMutation(0);
  }

  @Test public void fullLeagueSweepIsIndependentOfContinuousLiveChecks()throws Exception{
    ui.base.prefs.edit().putStringSet("cobra_sports_enabled_leagues",new HashSet<>(Arrays.asList("nfl","nba"))).commit();
    Object nfl=game("nfl","live","7","3","in",1);ui.games().add(nfl);replies.put("nfl",board(Arrays.asList(nfl),Collections.emptyList()));
    put(a,"mCobraSportsLastFullRefresh",System.currentTimeMillis());due();fetch(false);assertEquals(Arrays.asList("nfl"),requests);
    assertEquals("Fast polling covers the previous, current and next dates",3,requestedDays.get("nfl").size());
    requests.clear();put(a,"mCobraSportsLastFullRefresh",System.currentTimeMillis()-300001L);due();fetch(false);
    assertEquals(new HashSet<>(Arrays.asList("nfl","nba")),new HashSet<>(requests));assertFalse(requests.contains("nhl"));
    assertTrue(requestedDays.get("nba").size()>=8);
  }

  @Test public void soonStartingGameInAnotherLeagueJoinsFastPolling()throws Exception{
    ui.base.prefs.edit().putStringSet("cobra_sports_enabled_leagues",new HashSet<>(Arrays.asList("nfl","nba"))).commit();
    Object nfl=game("nfl","live","7","3","in",1),nba=game("nba","soon","0","0","pre",0),disabled=game("nhl","disabled","1","0","in",1);
    put(nba,"startMs",System.currentTimeMillis()+20000L);ui.games().addAll(Arrays.asList(nfl,nba,disabled));
    assertEquals(45000L,call(a,"cobraSportsRefreshInterval",System.currentTimeMillis()));put(a,"mCobraSportsLastFullRefresh",System.currentTimeMillis());due();fetch(false);
    assertEquals(new HashSet<>(Arrays.asList("nfl","nba")),new HashSet<>(requests));
  }

  @Test public void frequentUiSchedulingCannotPostponeAnAlreadyDueFeedCheck()throws Exception{
    ui.games().add(game("nba","live","67","93","in",3));put(a,"mCobraSportsLastRefresh",System.currentTimeMillis()-44000L);
    for(int i=0;i<3;i++){call(a,"cobraSportsScheduleNext");Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(250));}
    Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(300));
    assertTrue("Refresh must already be queued near its original 45-second deadline",(Boolean)get(a,"mCobraSportsLoading"));
    assertFalse(((PendingIo)get(a,"mIo")).tasks.isEmpty());
  }

  @Test public void staleVisibleAndQueuedScoresAreSuppressedWithoutLosingSeenSignature()throws Exception{
    Object first=game("nba","a","67","93","in",3),second=game("nhl","b","5","1","in",3);ui.games().add(first);ui.refresh();ui.games().add(second);ui.refresh();
    assertNotNull(ui.ticker());assertFalse(ui.pending().isEmpty());
    put(first,"feedUpdatedAtMs",System.currentTimeMillis()-120001L);put(second,"feedAvailable",false);ui.refresh();
    assertNull(ui.ticker());assertTrue(ui.pending().isEmpty());assertEquals(2,((Map)get(a,"mCobraScoreSeen")).size());delayed(first);delayed(second);
    put(first,"feedUpdatedAtMs",System.currentTimeMillis());put(second,"feedAvailable",true);ui.refresh();assertNull("Same recovered scores are not new alerts",ui.ticker());
    ui.score(first,"69");ui.refresh();assertNotNull(ui.ticker());
  }

  @Test public void allLeagueFeedsDistinguishValidEmptyScoreboardsFromMalformedResponses()throws Exception{
    for(String league:leagues){
      assertTrue(((List)call(a,"cobraSportsParseFeed",spec(league),new JSONObject().put("events",new JSONArray()))).isEmpty());
      try{call(a,"cobraSportsParseFeed",spec(league),new JSONObject().put("message","upstream unavailable"));fail(league+" missing events accepted");}
      catch(AssertionError expected){assertTrue(expected.getCause() instanceof IOException);}
    }
  }

  @Test public void scoreboardHttpBypassesCachesAndRejectsExpiredCachedResponses()throws Exception{
    java.net.ServerSocket server=new java.net.ServerSocket(0,2,java.net.InetAddress.getByName("127.0.0.1"));
    Map<String,String> headers=new java.util.concurrent.ConcurrentHashMap<>();
    java.util.concurrent.atomic.AtomicReference<Throwable> failure=new java.util.concurrent.atomic.AtomicReference<>();
    Thread responder=new Thread(()->{
      try{for(int i=0;i<2;i++)try(java.net.Socket client=server.accept()){
        client.setSoTimeout(3000);java.io.BufferedReader reader=new java.io.BufferedReader(new java.io.InputStreamReader(client.getInputStream(),java.nio.charset.StandardCharsets.US_ASCII));
        String line;while((line=reader.readLine())!=null&&!line.isEmpty()){int colon=line.indexOf(':');if(colon>0)headers.put(line.substring(0,colon).toLowerCase(Locale.US),line.substring(colon+1).trim());}
        byte[] body="{\"events\":[]}".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        String response="HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAge: "+(i==0?0:121)+"\r\nContent-Length: "+body.length+"\r\nConnection: close\r\n\r\n";
        java.io.OutputStream out=client.getOutputStream();out.write(response.getBytes(java.nio.charset.StandardCharsets.US_ASCII));out.write(body);out.flush();
      }}catch(Throwable error){failure.set(error);}
    },"scoreboard-fixture-http");responder.setDaemon(true);responder.start();
    try{
      String url="http://127.0.0.1:"+server.getLocalPort()+"/scoreboard";
      JSONObject fresh=(JSONObject)call(a,"cobraSportsJsonOnce",url);assertEquals(0,fresh.getJSONArray("events").length());
      assertEquals("no-cache",headers.get("cache-control"));assertEquals("no-cache",headers.get("pragma"));
      try{call(a,"cobraSportsJsonOnce",url);fail("Expired HTTP cache accepted as fresh scoreboard");}
      catch(AssertionError expected){assertTrue(expected.getCause() instanceof IOException);assertTrue(expected.getCause().getMessage().contains("stale"));}
      responder.join(1000L);assertNull(failure.get());
    }finally{server.close();}
  }
}
