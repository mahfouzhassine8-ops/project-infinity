package com.projectinfinity.kodi;

import android.content.SharedPreferences;
import android.os.Handler;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ScrollView;
import java.lang.reflect.Array;
import java.util.*;
import org.json.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.shadows.ShadowToast;
import static org.junit.Assert.*;

/** Acceptance tests for 2103270 Sports Hub. They use the production Activity/UI,
 * controlled score/EPG fixtures, and never call a live provider or video decoder. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=android.app.Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class SportsHubTest {
  CobraNavigationUiTest f;
  @Before public void before(){f=new CobraNavigationUiTest();f.clock();}

  static Object team(String id,String key,String shortName,String abbr,String score)throws Exception{
    Object t=CobraNavigationUiTest.construct("CobraSportsTeam");
    CobraNavigationUiTest.put(t,"id",id);CobraNavigationUiTest.put(t,"key",key);CobraNavigationUiTest.put(t,"leagueKey","nfl");
    CobraNavigationUiTest.put(t,"name",shortName);CobraNavigationUiTest.put(t,"shortName",shortName);CobraNavigationUiTest.put(t,"abbreviation",abbr);CobraNavigationUiTest.put(t,"score",score);return t;
  }
  @SuppressWarnings("unchecked") static Object game()throws Exception{
    Object g=CobraNavigationUiTest.construct("CobraSportsGame");long now=System.currentTimeMillis();
    CobraNavigationUiTest.put(g,"id","401999999");CobraNavigationUiTest.put(g,"leagueKey","nfl");CobraNavigationUiTest.put(g,"leagueLabel","NFL");
    CobraNavigationUiTest.put(g,"sport","football");CobraNavigationUiTest.put(g,"league","nfl");CobraNavigationUiTest.put(g,"state","in");
    CobraNavigationUiTest.put(g,"detail","Q3 • 6:42");CobraNavigationUiTest.put(g,"startMs",now-3600000L);
    CobraNavigationUiTest.put(g,"away",team("9","nfl|9","Packers","GB","17"));CobraNavigationUiTest.put(g,"home",team("8","nfl|8","Lions","DET","24"));
    ((List<String>)CobraNavigationUiTest.get(g,"broadcasts")).add("ESPN2");return g;
  }
  static Object channel(String id,String name,String epg)throws Exception{
    return CobraNavigationUiTest.construct("Channel",id,name,"Sports",epg,"","","",Collections.emptyMap());
  }
  static Object program(String epg,String title,long start,long stop)throws Exception{
    Object p=CobraNavigationUiTest.construct("GuideProgram");CobraNavigationUiTest.put(p,"channel",epg);CobraNavigationUiTest.put(p,"start",start);CobraNavigationUiTest.put(p,"stop",stop);CobraNavigationUiTest.put(p,"title",title);CobraNavigationUiTest.put(p,"description","NFL live game broadcast");return p;
  }

  @Test public void sportsIsAFirstClassDrawerOwnerAndUsesActualResponsiveWindow()throws Exception{
    InfinityLiveActivity a=f.fixture(24);try{
      f.drawer(a,"Sports");f.measure(a,412,915);
      assertEquals("sports",CobraNavigationUiTest.get(a,"mCobraDrawerOwner"));
      assertEquals("COBRA • SPORTS",CobraNavigationUiTest.get(a,"mCobraStageTitle"));
      View header=a.getWindow().getDecorView().findViewWithTag("cobra_sports_drawer_header");assertNotNull(header);assertTrue(header.isShown());
      View stage=(View)CobraNavigationUiTest.get(a,"mStage");assertTrue(stage.getWidth()>300&&stage.getHeight()>300);
      f.measure(a,320,720);assertEquals(320,a.getWindow().getDecorView().getWidth());assertEquals("COBRA • SPORTS",CobraNavigationUiTest.get(a,"mCobraStageTitle"));
      f.measure(a,720,320);assertEquals(720,a.getWindow().getDecorView().getWidth());assertEquals("COBRA • SPORTS",CobraNavigationUiTest.get(a,"mCobraStageTitle"));
    }finally{f.clean(a);}
  }

  @SuppressWarnings("unchecked") @Test public void controlledScoreboardParsesLiveTeamsScoresAndBroadcasts()throws Exception{
    InfinityLiveActivity a=f.fixture(4);try{
      Object spec=CobraNavigationUiTest.construct("CobraSportsLeagueSpec","nfl","football","nfl","NFL");
      JSONObject root=new JSONObject("{\"events\":[{\"id\":\"401999999\",\"name\":\"Green Bay Packers at Detroit Lions\",\"shortName\":\"GB @ DET\",\"date\":\"2026-09-30T16:00Z\",\"status\":{\"type\":{\"state\":\"in\",\"shortDetail\":\"Q3 6:42\",\"completed\":false}},\"competitions\":[{\"venue\":{\"fullName\":\"Ford Field\"},\"competitors\":[{\"homeAway\":\"away\",\"score\":\"17\",\"team\":{\"id\":\"9\",\"displayName\":\"Green Bay Packers\",\"shortDisplayName\":\"Packers\",\"abbreviation\":\"GB\"}},{\"homeAway\":\"home\",\"score\":\"24\",\"team\":{\"id\":\"8\",\"displayName\":\"Detroit Lions\",\"shortDisplayName\":\"Lions\",\"abbreviation\":\"DET\"}}],\"broadcasts\":[{\"names\":[\"ESPN2\"]}]}]}]}");
      List<Object> games=(List<Object>)CobraNavigationUiTest.call(a,"cobraSportsParseScoreboard",spec,root);assertEquals(1,games.size());Object g=games.get(0);
      assertEquals("in",CobraNavigationUiTest.get(g,"state"));assertEquals("Q3 6:42",CobraNavigationUiTest.get(g,"detail"));
      Object home=CobraNavigationUiTest.get(g,"home"),away=CobraNavigationUiTest.get(g,"away");assertEquals("Lions",CobraNavigationUiTest.get(home,"shortName"));assertEquals("24",CobraNavigationUiTest.get(home,"score"));assertEquals("Packers",CobraNavigationUiTest.get(away,"shortName"));
      assertEquals(Arrays.asList("ESPN2"),CobraNavigationUiTest.get(g,"broadcasts"));
    }finally{f.clean(a);}
  }

  @SuppressWarnings("unchecked") @Test public void resolverUsesAliasAndEpgEvidenceButNeverSilentlyChoosesAnAmbiguousNetwork()throws Exception{
    InfinityLiveActivity a=f.fixture(2);try{
      Object g=game();long now=System.currentTimeMillis();Object c1=channel("sports:espn2a","ESPN 2 HD","espn2a");
      ArrayList<Object> p1=new ArrayList<>();p1.add(program("espn2a","Green Bay Packers vs Detroit Lions",now-1800000L,now+7200000L));
      String n1=(String)CobraNavigationUiTest.call(a,"cobraSportsNorm","ESPN 2 HD Sports espn2a");Object i1=CobraNavigationUiTest.construct("CobraSportsChannelInfo",c1,n1,p1);
      ArrayList<Object> one=new ArrayList<>();one.add(i1);List<Object> resolved=(List<Object>)CobraNavigationUiTest.call(a,"cobraSportsResolve",g,one);assertEquals(1,resolved.size());assertEquals(100,CobraNavigationUiTest.get(resolved.get(0),"score"));assertEquals(true,CobraNavigationUiTest.call(a,"cobraSportsUniqueStrong",resolved));

      Object c2=channel("sports:espn2b","ESPN2 FHD","espn2b");Object c3=channel("sports:espn2c","ESPN 2 4K","espn2c");
      ArrayList<Object> empty=new ArrayList<>();String n2=(String)CobraNavigationUiTest.call(a,"cobraSportsNorm","ESPN2 FHD Sports espn2b"),n3=(String)CobraNavigationUiTest.call(a,"cobraSportsNorm","ESPN 2 4K Sports espn2c");
      ArrayList<Object> ambiguous=new ArrayList<>();ambiguous.add(CobraNavigationUiTest.construct("CobraSportsChannelInfo",c2,n2,empty));ambiguous.add(CobraNavigationUiTest.construct("CobraSportsChannelInfo",c3,n3,new ArrayList<>()));
      List<Object> matches=(List<Object>)CobraNavigationUiTest.call(a,"cobraSportsResolve",g,ambiguous);assertEquals(2,matches.size());assertEquals(70,CobraNavigationUiTest.get(matches.get(0),"score"));assertEquals(70,CobraNavigationUiTest.get(matches.get(1),"score"));assertEquals(false,CobraNavigationUiTest.call(a,"cobraSportsUniqueStrong",matches));
    }finally{f.clean(a);}
  }

  @SuppressWarnings("unchecked") @Test public void spoilerModeAndFavoriteTeamsPersistWithoutMutatingGameData()throws Exception{
    InfinityLiveActivity a=f.fixture(2);try{
      Object g=game(),home=CobraNavigationUiTest.get(g,"home");SharedPreferences prefs=(SharedPreferences)CobraNavigationUiTest.get(a,"mPrefs");
      String visible=(String)CobraNavigationUiTest.call(a,"cobraSportsScoreLine",g);assertTrue(visible.contains("24"));assertTrue(visible.contains("17"));
      prefs.edit().putBoolean("cobra_sports_hide_scores",true).commit();String hidden=(String)CobraNavigationUiTest.call(a,"cobraSportsScoreLine",g);assertFalse(hidden.contains("24"));assertFalse(hidden.contains("17"));assertTrue(hidden.contains("Lions"));assertTrue(hidden.contains("Packers"));
      CobraNavigationUiTest.call(a,"cobraSportsToggleFavorite",home);Set<String> stored=prefs.getStringSet("cobra_sports_favorite_teams",Collections.emptySet());assertTrue(stored.contains("nfl|8"));assertEquals("24",CobraNavigationUiTest.get(home,"score"));
    }finally{f.clean(a);}
  }

  @Test public void smartMultiViewProtectsAFullManualFourPaneLayout()throws Exception{
    InfinityLiveActivity a=f.fixture(6);try{
      @SuppressWarnings("unchecked") List<Object> channels=(List<Object>)CobraNavigationUiTest.get(a,"mChannels");Class<?> cc=channels.get(0).getClass();Object array=Array.newInstance(cc,4);for(int i=0;i<4;i++)Array.set(array,i,channels.get(i));CobraNavigationUiTest.put(a,"mMultiChannels",array);
      CobraNavigationUiTest.call(a,"cobraSportsOpenSmartMultiView","live",null);assertEquals("All four Multi-View slots are already pinned",ShadowToast.getTextOfLatestToast());
      Object after=CobraNavigationUiTest.get(a,"mMultiChannels");assertSame(array,after);assertEquals(4,Array.getLength(after));
    }finally{f.clean(a);}
  }

  @Test public void settingsExposeSportsConfigurationWithoutReplacingSettingsPage()throws Exception{
    InfinityLiveActivity a=f.fixture(8);try{
      CobraNavigationUiTest.call(a,"showSettings");f.measure(a,412,915);assertEquals("COBRA • SETTINGS",CobraNavigationUiTest.get(a,"mCobraStageTitle"));View row=a.getWindow().getDecorView().findViewWithTag("cobra_sports_settings");assertNotNull(row);assertTrue(row.isShown());assertTrue(row.performClick());assertNotNull(CobraNavigationUiTest.get(a,"mCobraActionSheet"));assertEquals("sports-settings",CobraNavigationUiTest.get(a,"mCobraSheetKind"));assertEquals("COBRA • SETTINGS",CobraNavigationUiTest.get(a,"mCobraStageTitle"));
    }finally{f.clean(a);}
  }
}
