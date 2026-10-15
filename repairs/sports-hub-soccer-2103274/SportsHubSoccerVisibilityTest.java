package com.projectinfinity.kodi;

import android.content.SharedPreferences;
import android.view.*;
import android.widget.*;
import java.util.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=android.app.Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class SportsHubSoccerVisibilityTest {
  CobraNavigationUiTest f;
  @Before public void before(){f=new CobraNavigationUiTest();f.clock();}

  static Object team(String id,String league,String name,String abbr,String score)throws Exception{
    Object t=CobraNavigationUiTest.construct("CobraSportsTeam");
    CobraNavigationUiTest.put(t,"id",id);CobraNavigationUiTest.put(t,"key",league+"|"+id);CobraNavigationUiTest.put(t,"leagueKey",league);
    CobraNavigationUiTest.put(t,"name",name);CobraNavigationUiTest.put(t,"shortName",name);CobraNavigationUiTest.put(t,"abbreviation",abbr);CobraNavigationUiTest.put(t,"score",score);
    return t;
  }
  @SuppressWarnings("unchecked") static Object game(String id,String league,String label,String sport,String state,long start,String away,String aa,String home,String ha,String as,String hs)throws Exception{
    Object g=CobraNavigationUiTest.construct("CobraSportsGame");
    CobraNavigationUiTest.put(g,"id",id);CobraNavigationUiTest.put(g,"leagueKey",league);CobraNavigationUiTest.put(g,"leagueLabel",label);
    CobraNavigationUiTest.put(g,"sport",sport);CobraNavigationUiTest.put(g,"league",league);CobraNavigationUiTest.put(g,"state",state);CobraNavigationUiTest.put(g,"detail","in".equals(state)?"2nd Half • 67'":"");CobraNavigationUiTest.put(g,"startMs",start);
    CobraNavigationUiTest.put(g,"away",team(id+"a",league,away,aa,as));CobraNavigationUiTest.put(g,"home",team(id+"h",league,home,ha,hs));
    ((List<String>)CobraNavigationUiTest.get(g,"broadcasts")).add("NBC");return g;
  }
  static ArrayList<String> texts(View v){
    ArrayList<String> out=new ArrayList<>();if(v instanceof TextView)out.add(((TextView)v).getText().toString());
    if(v instanceof ViewGroup)for(int i=0;i<((ViewGroup)v).getChildCount();i++)out.addAll(texts(((ViewGroup)v).getChildAt(i)));return out;
  }
  static int exact(List<String> values,String needle){int n=0;for(String s:values)if(needle.equals(s))n++;return n;}

  @SuppressWarnings("unchecked") @Test public void soccerSectionRemainsVisibleWhenNoSoccerMatchExists()throws Exception{
    InfinityLiveActivity a=f.fixture(4);try{
      List<Object> games=(List<Object>)CobraNavigationUiTest.get(a,"mCobraSportsGames");games.clear();
      CobraNavigationUiTest.call(a,"clearStage","COBRA • SPORTS");CobraNavigationUiTest.call(a,"cobraSportsRenderHub");f.measure(a,412,915);
      View root=a.getWindow().getDecorView();assertNotNull(root.findViewWithTag("cobra_sports_soccer_section"));assertNotNull(root.findViewWithTag("cobra_sports_soccer_heading"));assertNotNull(root.findViewWithTag("cobra_sports_soccer_empty"));assertNotNull(root.findViewWithTag("cobra_sports_soccer_leagues"));
    }finally{f.clean(a);}
  }

  @SuppressWarnings("unchecked") @Test public void soccerRailAggregatesEnabledSoccerLeaguesButNotOtherSports()throws Exception{
    InfinityLiveActivity a=f.fixture(4);try{
      List<Object> games=(List<Object>)CobraNavigationUiTest.get(a,"mCobraSportsGames");games.clear();long now=System.currentTimeMillis();
      games.add(game("epl1","epl","Premier League","soccer","in",now-1000,"Arsenal","ARS","Chelsea","CHE","2","1"));
      games.add(game("ucl1","ucl","Champions League","soccer","pre",now+86400000L,"Barcelona","BAR","Inter","INT","0","0"));
      games.add(game("mlb1","mlb","MLB","baseball","pre",now+7200000L,"White Sox","CHW","Astros","HOU","0","0"));
      CobraNavigationUiTest.call(a,"clearStage","COBRA • SPORTS");CobraNavigationUiTest.call(a,"cobraSportsRenderHub");f.measure(a,412,915);
      View rail=a.getWindow().getDecorView().findViewWithTag("cobra_sports_soccer_rail");assertNotNull(rail);assertNotNull(rail.findViewWithTag("cobra-sports-game:epl1"));assertNotNull(rail.findViewWithTag("cobra-sports-game:ucl1"));assertNull(rail.findViewWithTag("cobra-sports-game:mlb1"));
    }finally{f.clean(a);}
  }

  @SuppressWarnings("unchecked") @Test public void soccerDirectoryListsEnabledCompetitionsAndButtonOpensIt()throws Exception{
    InfinityLiveActivity a=f.fixture(4);try{
      List<Object> games=(List<Object>)CobraNavigationUiTest.get(a,"mCobraSportsGames");games.clear();games.add(game("epl1","epl","Premier League","soccer","pre",System.currentTimeMillis()+3600000L,"Arsenal","ARS","Chelsea","CHE","0","0"));
      CobraNavigationUiTest.call(a,"clearStage","COBRA • SPORTS");CobraNavigationUiTest.call(a,"cobraSportsRenderHub");f.measure(a,412,915);
      View open=a.getWindow().getDecorView().findViewWithTag("cobra_sports_soccer_leagues");assertNotNull(open);open.performClick();f.measure(a,412,915);
      assertNotNull(a.getWindow().getDecorView().findViewWithTag("cobra_sports_soccer_leagues_heading"));
      assertNotNull(a.getWindow().getDecorView().findViewWithTag("cobra-sports-soccer-league:epl"));
      assertNotNull(a.getWindow().getDecorView().findViewWithTag("cobra-sports-soccer-league:ucl"));
      assertNotNull(a.getWindow().getDecorView().findViewWithTag("cobra-sports-soccer-league:mls"));
      assertNull(a.getWindow().getDecorView().findViewWithTag("cobra-sports-soccer-league:laliga"));
    }finally{f.clean(a);}
  }

  @SuppressWarnings("unchecked") @Test public void mainHubUsesOneSoccerGroupInsteadOfDuplicatingCompetitionRails()throws Exception{
    InfinityLiveActivity a=f.fixture(4);try{
      List<Object> games=(List<Object>)CobraNavigationUiTest.get(a,"mCobraSportsGames");games.clear();long now=System.currentTimeMillis();
      games.add(game("epl1","epl","Premier League","soccer","pre",now+3600000L,"Arsenal","ARS","Chelsea","CHE","0","0"));
      games.add(game("ucl1","ucl","Champions League","soccer","pre",now+7200000L,"Barcelona","BAR","Inter","INT","0","0"));
      CobraNavigationUiTest.call(a,"clearStage","COBRA • SPORTS");CobraNavigationUiTest.call(a,"cobraSportsRenderHub");f.measure(a,412,915);
      ArrayList<String> labels=texts(a.getWindow().getDecorView());assertEquals(1,exact(labels,"SOCCER"));assertEquals(0,exact(labels,"PREMIER LEAGUE"));assertEquals(0,exact(labels,"CHAMPIONS LEAGUE"));
    }finally{f.clean(a);}
  }
}
