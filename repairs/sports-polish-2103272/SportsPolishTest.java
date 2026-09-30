package com.projectinfinity.kodi;

import android.content.SharedPreferences;
import android.graphics.*;
import android.view.*;
import android.widget.*;
import java.io.*;
import java.util.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=android.app.Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class SportsPolishTest {
  CobraNavigationUiTest f;
  @Before public void before(){f=new CobraNavigationUiTest();f.clock();}

  static Object team(String id,String league,String name,String abbr,String score)throws Exception{
    Object t=CobraNavigationUiTest.construct("CobraSportsTeam");
    CobraNavigationUiTest.put(t,"id",id);CobraNavigationUiTest.put(t,"key",league+"|"+id);CobraNavigationUiTest.put(t,"leagueKey",league);
    CobraNavigationUiTest.put(t,"name",name);CobraNavigationUiTest.put(t,"shortName",name);CobraNavigationUiTest.put(t,"abbreviation",abbr);CobraNavigationUiTest.put(t,"score",score);
    return t;
  }
  @SuppressWarnings("unchecked") static Object game(String id,String league,String label,boolean live,long start,String away,String aa,String home,String ha,String as,String hs)throws Exception{
    Object g=CobraNavigationUiTest.construct("CobraSportsGame");
    CobraNavigationUiTest.put(g,"id",id);CobraNavigationUiTest.put(g,"leagueKey",league);CobraNavigationUiTest.put(g,"leagueLabel",label);
    CobraNavigationUiTest.put(g,"sport","sport");CobraNavigationUiTest.put(g,"league",league);CobraNavigationUiTest.put(g,"state",live?"in":"pre");
    CobraNavigationUiTest.put(g,"detail",live?"Top 2nd":"");CobraNavigationUiTest.put(g,"startMs",start);
    CobraNavigationUiTest.put(g,"away",team(id+"a",league,away,aa,as));CobraNavigationUiTest.put(g,"home",team(id+"h",league,home,ha,hs));
    ((List<String>)CobraNavigationUiTest.get(g,"broadcasts")).add(live?"NBC":"Prime Video");return g;
  }
  static ArrayList<String> texts(View v){
    ArrayList<String> out=new ArrayList<>();if(v instanceof TextView)out.add(((TextView)v).getText().toString());
    if(v instanceof ViewGroup)for(int i=0;i<((ViewGroup)v).getChildCount();i++)out.addAll(texts(((ViewGroup)v).getChildAt(i)));return out;
  }
  static boolean has(ArrayList<String> all,String needle){for(String s:all)if(s.contains(needle))return true;return false;}
  static void save(View v,String name)throws Exception{
    File dir=new File(System.getProperty("sports.polish.evidence"));dir.mkdirs();Bitmap b=Bitmap.createBitmap(v.getWidth(),v.getHeight(),Bitmap.Config.ARGB_8888);v.draw(new Canvas(b));
    try(FileOutputStream o=new FileOutputStream(new File(dir,name+".png"))){b.compress(Bitmap.CompressFormat.PNG,100,o);}b.recycle();
  }

  @Test public void upcomingCardsNeverPresentPregameZeroZeroAsAScore()throws Exception{
    InfinityLiveActivity a=f.fixture(4);try{
      Object upcoming=game("u1","nfl","NFL",false,System.currentTimeMillis()+86400000L,"Steelers","PIT","Browns","CLE","0","0");
      View card=(View)CobraNavigationUiTest.call(a,"cobraSportsGameCard",upcoming);
      card.measure(View.MeasureSpec.makeMeasureSpec(270,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(150,View.MeasureSpec.EXACTLY));card.layout(0,0,270,150);
      ArrayList<String> labels=texts(card);assertTrue(has(labels,"Steelers  @  Browns"));assertFalse(has(labels,"Steelers  0"));assertFalse(has(labels,"Browns  0"));
      assertNotNull(card.findViewWithTag("cobra_sports_upcoming_matchup"));
    }finally{f.clean(a);}
  }

  @SuppressWarnings("unchecked") @Test public void hubUsesSportsSummaryAndCompactGlassActionsInsteadOfGenericStatus()throws Exception{
    InfinityLiveActivity a=f.fixture(6);try{
      List<Object> games=(List<Object>)CobraNavigationUiTest.get(a,"mCobraSportsGames");long now=System.currentTimeMillis();
      games.add(game("l1","mlb","MLB",true,now-900000L,"Phillies","PHI","Braves","ATL","1","1"));
      games.add(game("u1","nfl","NFL",false,now+86400000L,"Steelers","PIT","Browns","CLE","0","0"));
      games.add(game("u2","nhl","NHL",false,now+172800000L,"Penguins","PIT","Bruins","BOS","0","0"));
      CobraNavigationUiTest.put(a,"mCobraSportsLastRefresh",now);CobraNavigationUiTest.call(a,"clearStage","COBRA • SPORTS");CobraNavigationUiTest.call(a,"cobraSportsRenderHub");f.measure(a,412,915);
      TextView summary=a.getWindow().getDecorView().findViewWithTag("cobra_sports_summary");assertNotNull(summary);assertTrue(summary.getText().toString().contains("1 LIVE"));assertTrue(summary.getText().toString().contains("2 UPCOMING"));
      View status=(View)CobraNavigationUiTest.get(a,"mStatus");assertEquals(View.GONE,status.getVisibility());
      View bar=a.getWindow().getDecorView().findViewWithTag("cobra_sports_action_bar");assertNotNull(bar);assertTrue(bar.getHeight()<=60);
      View smart=a.getWindow().getDecorView().findViewWithTag("cobra_sports_smart_multiview");assertNotNull(smart);assertTrue(smart.isShown());
    }finally{f.clean(a);}
  }

  @SuppressWarnings("unchecked") @Test public void liveCardGetsHeroTreatmentAndLivePill()throws Exception{
    InfinityLiveActivity a=f.fixture(4);try{
      Object live=game("l1","mlb","MLB",true,System.currentTimeMillis()-900000L,"Phillies","PHI","Braves","ATL","1","1");
      View card=(View)CobraNavigationUiTest.call(a,"cobraSportsGameCard",live);card.measure(View.MeasureSpec.makeMeasureSpec(360,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(202,View.MeasureSpec.EXACTLY));card.layout(0,0,360,202);
      View pill=card.findViewWithTag("cobra_sports_live_pill");assertNotNull(pill);assertEquals(View.VISIBLE,pill.getVisibility());assertTrue(has(texts(card),"Phillies  1"));assertTrue(has(texts(card),"Braves  1"));assertTrue(card.getElevation()>0);
    }finally{f.clean(a);}
  }

  @SuppressWarnings("unchecked") @Test public void leagueNavigationUsesSeeAllAndRetainsWorkingGameCards()throws Exception{
    InfinityLiveActivity a=f.fixture(4);try{
      List<Object> games=(List<Object>)CobraNavigationUiTest.get(a,"mCobraSportsGames");games.add(game("u1","nfl","NFL",false,System.currentTimeMillis()+86400000L,"Steelers","PIT","Browns","CLE","0","0"));
      CobraNavigationUiTest.put(a,"mCobraSportsLastRefresh",System.currentTimeMillis());CobraNavigationUiTest.call(a,"clearStage","COBRA • SPORTS");CobraNavigationUiTest.call(a,"cobraSportsRenderHub");f.measure(a,412,915);
      View all=a.getWindow().getDecorView().findViewWithTag("cobra_sports_league_all:nfl");assertNotNull(all);assertTrue(((TextView)all).getText().toString().contains("See All"));
      assertNotNull(a.getWindow().getDecorView().findViewWithTag("cobra-sports-game:u1"));
    }finally{f.clean(a);}
  }

  @SuppressWarnings("unchecked") @Test public void polishedHubRendersInLightAndOledAtPhoneAndWideBounds()throws Exception{
    for(String appearance:new String[]{"light","oled"}){InfinityLiveActivity a=f.fixture(8);try{
      SharedPreferences prefs=(SharedPreferences)CobraNavigationUiTest.get(a,"mPrefs");prefs.edit().putString("cobra_appearance_mode",appearance).commit();CobraNavigationUiTest.call(a,"buildShell");
      List<Object> games=(List<Object>)CobraNavigationUiTest.get(a,"mCobraSportsGames");long now=System.currentTimeMillis();games.add(game("l1","mlb","MLB",true,now-600000L,"Phillies","PHI","Braves","ATL","1","1"));games.add(game("u1","nfl","NFL",false,now+86400000L,"Steelers","PIT","Browns","CLE","0","0"));
      CobraNavigationUiTest.put(a,"mCobraSportsLastRefresh",now);CobraNavigationUiTest.call(a,"clearStage","COBRA • SPORTS");CobraNavigationUiTest.call(a,"cobraSportsRenderHub");
      for(int[] pane:new int[][]{{412,915},{720,320}}){f.measure(a,pane[0],pane[1]);View root=a.getWindow().getDecorView();assertEquals(pane[0],root.getWidth());assertEquals(pane[1],root.getHeight());assertNotNull(root.findViewWithTag("cobra_sports_action_bar"));save(root,"sports-polish-"+appearance+"-"+pane[0]+"x"+pane[1]);}
    }finally{f.clean(a);}}
  }
}
