package com.projectinfinity.kodi;

import android.app.Activity;
import android.view.*;
import android.widget.*;
import java.lang.reflect.Array;
import java.util.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.android.controller.ActivityController;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=android.app.Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class ProSportsIntegrationTest {
  CobraNavigationUiTest f;
  @Before public void before(){f=new CobraNavigationUiTest();f.clock();}

  static void layout(View v,int w,int h){
    v.measure(View.MeasureSpec.makeMeasureSpec(w,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h,View.MeasureSpec.EXACTLY));
    v.layout(0,0,w,h);
  }
  static class Calls implements CobraProUi.Actions {
    int preview,unmute,watch,stats,multi;final ArrayList<Integer> steps=new ArrayList<>(),controls=new ArrayList<>();
    public void preview(){preview++;}public void unmute(){unmute++;}public void step(int d){steps.add(d);}public void control(int i){controls.add(i);}
    public void sportsWatch(){watch++;}public void sportsStats(){stats++;}public void sportsMulti(){multi++;}
  }
  static Object team(String id,String league,String name,String abbr,String score)throws Exception{
    Object t=CobraNavigationUiTest.construct("CobraSportsTeam");
    CobraNavigationUiTest.put(t,"id",id);CobraNavigationUiTest.put(t,"key",league+"|"+id);CobraNavigationUiTest.put(t,"leagueKey",league);
    CobraNavigationUiTest.put(t,"name",name);CobraNavigationUiTest.put(t,"shortName",name);CobraNavigationUiTest.put(t,"abbreviation",abbr);CobraNavigationUiTest.put(t,"score",score);
    return t;
  }
  @SuppressWarnings("unchecked") static Object game(String id,String league,String label,String sport,String state,long start,String away,String aa,String home,String ha,String as,String hs)throws Exception{
    Object g=CobraNavigationUiTest.construct("CobraSportsGame");
    CobraNavigationUiTest.put(g,"id",id);CobraNavigationUiTest.put(g,"leagueKey",league);CobraNavigationUiTest.put(g,"leagueLabel",label);
    CobraNavigationUiTest.put(g,"sport",sport);CobraNavigationUiTest.put(g,"league",league);CobraNavigationUiTest.put(g,"state",state);
    CobraNavigationUiTest.put(g,"detail","in".equals(state)?"2nd Half • 67'":"");CobraNavigationUiTest.put(g,"startMs",start);
    CobraNavigationUiTest.put(g,"away",team(id+"a",league,away,aa,as));CobraNavigationUiTest.put(g,"home",team(id+"h",league,home,ha,hs));
    ((List<String>)CobraNavigationUiTest.get(g,"broadcasts")).add("NBC");return g;
  }

  @Test public void proMainNavigationHasSixImmediateTabsIncludingSports()throws Exception{
    ActivityController<Activity> ctl=Robolectric.buildActivity(Activity.class).setup();Activity a=ctl.get();try{
      ArrayList<Integer> calls=new ArrayList<>();CobraProUi.Filters ui=new CobraProUi.Filters(a,true,calls::add);a.setContentView(ui);layout(ui,412,CobraProUi.Filters.height(a,412));
      assertArrayEquals(new String[]{"All Channels","Favorites","Recents","Groups","Sports","Search"},CobraProUi.Filters.LABELS);
      assertEquals(6,ui.buttons.length);assertEquals("pro_six_action_row",ui.getTag());
      for(int i=0;i<6;i++){assertEquals("pro_filter_"+i,ui.buttons[i].getTag());assertTrue(ui.buttons[i].getWidth()>=48);assertTrue(ui.buttons[i].getHeight()>=48);ui.buttons[i].performClick();}
      assertEquals(Arrays.asList(0,1,2,3,4,5),calls);
    }finally{ctl.pause().stop().destroy();}
  }

  @Test public void sportsBrowserHasLiveTeamsUpcomingAndLeaguesTabs()throws Exception{
    ActivityController<Activity> ctl=Robolectric.buildActivity(Activity.class).setup();Activity a=ctl.get();try{
      ArrayList<Integer> calls=new ArrayList<>();CobraProUi.SportsTabs tabs=new CobraProUi.SportsTabs(a,true,calls::add);a.setContentView(tabs);layout(tabs,412,CobraProUi.SportsTabs.height(a));
      assertArrayEquals(new String[]{"Live Now","My Teams","Upcoming","Leagues"},CobraProUi.SportsTabs.LABELS);
      assertEquals("pro_sports_tabs",tabs.getTag());for(int i=0;i<4;i++){assertTrue(tabs.buttons[i].getWidth()>=48);assertTrue(tabs.buttons[i].getHeight()>=48);tabs.buttons[i].performClick();}
      assertEquals(Arrays.asList(0,1,2,3),calls);
    }finally{ctl.pause().stop().destroy();}
  }

  @Test public void sportsHeroUsesWatchStatsAndMultiViewThenRestoresNormalProHero()throws Exception{
    ActivityController<Activity> ctl=Robolectric.buildActivity(Activity.class).setup();Activity a=ctl.get();try{
      FrameLayout root=new FrameLayout(a);a.setContentView(root);Calls calls=new Calls();CobraProUi.Hero hero=new CobraProUi.Hero(a,true,calls,null);root.addView(hero,new FrameLayout.LayoutParams(-1,-1));
      CobraProUi.Program sport=new CobraProUi.Program();sport.sports=true;sport.source="LIVE SPORTS";sport.channel="Premier League";sport.live=true;sport.sportsAvailable=true;sport.sportsMultiAvailable=true;sport.sportsAway="Arsenal";sport.sportsAwayAbbr="ARS";sport.sportsHome="Chelsea";sport.sportsHomeAbbr="CHE";sport.sportsScore="Arsenal  2   •   Chelsea  1";sport.sportsMeta="LIVE • 2nd Half • 67' • NBC";
      hero.bind(sport,5,6);hero.setState(CobraProUi.RESTING,null,false);layout(root,412,330);
      assertEquals(View.GONE,hero.preview.getVisibility());assertEquals(View.VISIBLE,hero.sportsWatch.getVisibility());assertEquals(View.VISIBLE,hero.sportsStats.getVisibility());assertEquals(View.VISIBLE,hero.sportsMulti.getVisibility());assertEquals("LIVE SPORTS",hero.source.getText().toString());assertTrue(hero.sportsMatchup.getText().toString().contains("ARS"));assertTrue(hero.sportsScore.getText().toString().contains("2"));
      hero.sportsWatch.performClick();hero.sportsStats.performClick();hero.sportsMulti.performClick();assertEquals(1,calls.watch);assertEquals(1,calls.stats);assertEquals(1,calls.multi);
      CobraProUi.Program normal=new CobraProUi.Program();normal.channel="Nicktoons";normal.title="SpongeBob SquarePants";normal.source="FROM FAVORITES";normal.live=true;hero.bind(normal,0,6);layout(root,412,330);
      assertEquals(View.VISIBLE,hero.preview.getVisibility());assertEquals(View.GONE,hero.sportsWatch.getVisibility());assertEquals(View.GONE,hero.sportsStats.getVisibility());assertEquals(View.GONE,hero.sportsMulti.getVisibility());
    }finally{ctl.pause().stop().destroy();}
  }

  @Test public void soccerRowsUseTheSameNativeSportsBrowserAndIdentifySoccer()throws Exception{
    ActivityController<Activity> ctl=Robolectric.buildActivity(Activity.class).setup();Activity a=ctl.get();try{
      CobraProUi.SportsGame game=new CobraProUi.SportsGame();game.id="soc1";game.league="Premier League";game.away="Arsenal";game.awayAbbr="ARS";game.home="Chelsea";game.homeAbbr="CHE";game.score="Arsenal 2 • Chelsea 1";game.meta="LIVE • 2nd Half • 67' • NBC";game.live=true;game.soccer=true;
      CobraProUi.GameRow row=new CobraProUi.GameRow(a,true,()->{},()->{});row.bind(game,null);a.setContentView(row);layout(row,412,CobraProUi.GameRow.height(a,412));
      assertTrue(row.league.getText().toString().contains("SOCCER"));assertTrue(row.matchup.getText().toString().contains("ARS"));assertTrue(row.matchup.getText().toString().contains("CHE"));assertTrue(row.meta.getText().toString().contains("67"));
    }finally{ctl.pause().stop().destroy();}
  }

  @SuppressWarnings("unchecked") @Test public void proHeroSlotsReserveExactlyOnePermanentLiveSportsSource()throws Exception{
    InfinityLiveActivity a=f.fixture(20);try{
      List<Object> channels=(List<Object>)CobraNavigationUiTest.get(a,"mChannels");CobraNavigationUiTest.call(a,"cobraBuildProSlots",new ArrayList<>(channels));
      List<Object> slots=(List<Object>)CobraNavigationUiTest.get(a,"mCobraProSlots");int sports=0,regular=0;String source="";
      for(Object slot:slots){boolean isSports=(Boolean)CobraNavigationUiTest.get(slot,"sports");if(isSports){sports++;source=(String)CobraNavigationUiTest.get(slot,"source");assertNull(CobraNavigationUiTest.get(slot,"channel"));}else regular++;}
      assertEquals(1,sports);assertEquals("LIVE SPORTS",source);assertTrue(regular<=5);assertTrue(slots.size()<=6);
    }finally{f.clean(a);}
  }

  @SuppressWarnings("unchecked") @Test public void soccerCoreLeaguesAreEnabledByDefaultAndExtendedLeaguesExist()throws Exception{
    InfinityLiveActivity a=f.fixture(4);try{
      Set<String> enabled=(Set<String>)CobraNavigationUiTest.call(a,"cobraSportsEnabledLeagues");
      for(String key:new String[]{"epl","ucl","mls"})assertTrue("Default soccer league "+key,enabled.contains(key));
      for(String key:new String[]{"epl","ucl","mls","laliga","bundesliga","seriea","ligue1","uel"})assertNotNull("Missing soccer league "+key,CobraNavigationUiTest.call(a,"cobraSportsSpec",key));
      Object liga=CobraNavigationUiTest.call(a,"cobraSportsSpec","laliga");assertEquals("soccer",CobraNavigationUiTest.get(liga,"sport"));assertEquals("La Liga",CobraNavigationUiTest.get(liga,"label"));assertEquals("SOCCER",CobraNavigationUiTest.call(a,"cobraProSportGroup",liga));
    }finally{f.clean(a);}
  }

  @Test public void soccerGameMapsIntoTheSameLiveSportsHeroDataShape()throws Exception{
    InfinityLiveActivity a=f.fixture(4);try{
      Object soccer=game("soc1","epl","Premier League","soccer","in",System.currentTimeMillis()-3600000L,"Arsenal","ARS","Chelsea","CHE","2","1");
      CobraProUi.SportsGame row=(CobraProUi.SportsGame)CobraNavigationUiTest.call(a,"cobraProSportsUiGame",soccer);assertTrue(row.soccer);assertTrue(row.live);assertEquals("Premier League",row.league);assertEquals("ARS",row.awayAbbr);assertEquals("CHE",row.homeAbbr);assertTrue(row.score.contains("2"));
      CobraProUi.Program hero=(CobraProUi.Program)CobraNavigationUiTest.call(a,"cobraProSportsProgram",soccer);assertTrue(hero.sports);assertEquals("LIVE SPORTS",hero.source);assertTrue(hero.live);assertEquals("ARS",hero.sportsAwayAbbr);assertEquals("CHE",hero.sportsHomeAbbr);assertTrue(hero.sportsMeta.contains("67"));
    }finally{f.clean(a);}
  }

  @SuppressWarnings("unchecked") @Test public void favoriteLiveGameWinsSportsHeroPreferenceWithoutChangingStoredGameData()throws Exception{
    InfinityLiveActivity a=f.fixture(4);try{
      long now=System.currentTimeMillis();Object normal=game("g1","mlb","MLB","baseball","in",now-300000L,"Phillies","PHI","Braves","ATL","1","1");Object favorite=game("g2","epl","Premier League","soccer","in",now-600000L,"Arsenal","ARS","Chelsea","CHE","2","1");
      List<Object> games=(List<Object>)CobraNavigationUiTest.get(a,"mCobraSportsGames");games.add(normal);games.add(favorite);Object home=CobraNavigationUiTest.get(favorite,"home");String key=(String)CobraNavigationUiTest.get(home,"key");
      ((android.content.SharedPreferences)CobraNavigationUiTest.get(a,"mPrefs")).edit().putStringSet("cobra_sports_favorite_teams",new HashSet<>(Arrays.asList(key))).commit();
      Object selected=CobraNavigationUiTest.call(a,"cobraProPreferredSportsGame");assertSame(favorite,selected);assertEquals("2",CobraNavigationUiTest.get(CobraNavigationUiTest.get(favorite,"away"),"score"));assertEquals("1",CobraNavigationUiTest.get(home,"score"));
    }finally{f.clean(a);}
  }
}
