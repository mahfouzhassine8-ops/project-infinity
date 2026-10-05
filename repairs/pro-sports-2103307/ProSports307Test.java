package com.projectinfinity.kodi;
import android.app.Activity;
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
import static com.projectinfinity.kodi.CobraNavigationUiTest.*;

/** Real production views and callbacks, controlled feed/player state, no live decoder claims. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=android.app.Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class ProSports307Test {
 CobraNavigationUiTest f;
 @Before public void before(){f=new CobraNavigationUiTest();f.clock();}
 Object game(String id,String league,String state,String as,String hs)throws Exception{
  Object g=ProSportsIntegrationTest.game(id,league,league.toUpperCase(Locale.US),"baseball",state,1791213000000L,"Phillies","PHI","Braves","ATL",as,hs);
  put(g,"detail","Top 2nd");return g;
 }
 @SuppressWarnings("unchecked") void add(InfinityLiveActivity a,Object...games)throws Exception{((List<Object>)get(a,"mCobraSportsGames")).addAll(Arrays.asList(games));put(a,"mCobraSportsLastRefresh",System.currentTimeMillis());}
 void pro(InfinityLiveActivity a)throws Exception{((SharedPreferences)get(a,"mPrefs")).edit().putString("guide_view_mode","focus").commit();put(a,"mCobraGuideStyle","focus");call(a,"cobraShowGuideShell");f.measure(a,412,915);}
 void save(View v,String name)throws Exception{File d=new File(System.getProperty("cobra.evidence"),"pro-sports");d.mkdirs();Bitmap b=Bitmap.createBitmap(v.getWidth(),v.getHeight(),Bitmap.Config.ARGB_8888);v.draw(new Canvas(b));try(FileOutputStream out=new FileOutputStream(new File(d,name+".png"))){b.compress(Bitmap.CompressFormat.PNG,100,out);}b.recycle();}
 String text(View v){String s=v instanceof TextView?((TextView)v).getText().toString():"";if(v instanceof ViewGroup)for(int i=0;i<((ViewGroup)v).getChildCount();i++)s+="\n"+text(((ViewGroup)v).getChildAt(i));return s;}
 @Test public void compactAddsListSpaceAndRestoresOriginalGeometryAcrossWindows(){
  for(int[] size:new int[][]{{320,720},{412,915},{768,1024},{960,540}})for(float font:new float[]{1,1.5f,2})for(int state=0;state<3;state++){
   int[][] normal=CobraProUi.geometry(size[0],size[1],font,state),restored=CobraProUi.sportsGeometry(size[0],size[1],font,state,0),small=CobraProUi.sportsGeometry(size[0],size[1],font,state,1);
   for(int i=0;i<4;i++)assertArrayEquals(normal[i],restored[i]);
   assertTrue(small[1][3]<=normal[1][3]);assertTrue(small[3][3]>=normal[3][3]);
   if(normal[3][1]>normal[1][1])assertEquals(normal[1][3]-small[1][3],small[3][3]-normal[3][3]);
   for(int[] b:small){assertTrue(b[0]>=0&&b[1]>=0&&b[2]>=0&&b[3]>=0);assertTrue(b[0]+b[2]<=size[0]);assertTrue(b[1]+b[3]<=size[1]);}
  }
 }
 @Test public void actualSportsTapAndHoldKeepTextureAndRestoreNormalSize()throws Exception{
  InfinityLiveActivity a=f.fixture(8);try{add(a,game("live","mlb","in","1","1"));pro(a);
   View texture=(View)get(a,"mCobraPreviewTexture");int original=((View)get(a,"mCobraGuideVideo")).getLayoutParams().height;
   call(a,"cobraProFilter",4);f.frames(28);f.measure(a,412,915);
   assertEquals(true,get(a,"mCobraProSportsCompact"));assertTrue(((View)get(a,"mCobraGuideVideo")).getLayoutParams().height<original);assertSame(texture,get(a,"mCobraPreviewTexture"));
   View sports=a.getWindow().getDecorView().findViewWithTag("pro_filter_4");assertNotNull(sports);assertTrue(sports.performLongClick());f.frames(28);f.measure(a,412,915);
   assertEquals(false,get(a,"mCobraProSportsCompact"));assertEquals(original,((View)get(a,"mCobraGuideVideo")).getLayoutParams().height);assertSame(texture,get(a,"mCobraPreviewTexture"));
  }finally{f.clean(a);}
 }
 @Test public void groupsHighlightSurvivesRerender()throws Exception{
  InfinityLiveActivity a=f.fixture(8);try{pro(a);call(a,"cobraProFilter",1);call(a,"cobraProFilter",3);f.measure(a,412,915);
   for(int i=0;i<2;i++){View groups=a.getWindow().getDecorView().findViewWithTag("pro_filter_3");assertNotNull(groups);assertTrue(groups.isSelected());assertFalse(a.getWindow().getDecorView().findViewWithTag("pro_filter_1").isSelected());call(a,"cobraRenderGuideBrowser");f.measure(a,412,915);}
  }finally{f.clean(a);}
 }
 @Test public void pollingUpdatesRowsWithoutRetuningOrRebuildingList()throws Exception{
  InfinityLiveActivity a=f.fixture(8);try{Object g=game("live","mlb","in","1","1");add(a,g);pro(a);call(a,"cobraProFilter",4);f.frames(28);f.measure(a,412,915);
   Object texture=get(a,"mCobraPreviewTexture"),adapter=get(a,"mCobraGuideAdapter"),channel=((List<?>)get(a,"mChannels")).get(0);
   put(a,"mCobraProSportsResolvedChannel",channel);put(a,"mCobraProSportsResolvingId","preserve-request");put(get(g,"home"),"score","2");call(a,"cobraProOnSportsDataChanged");f.measure(a,412,915);
   assertSame(adapter,get(a,"mCobraGuideAdapter"));assertSame(texture,get(a,"mCobraPreviewTexture"));assertSame(channel,get(a,"mCobraProSportsResolvedChannel"));assertEquals("preserve-request",get(a,"mCobraProSportsResolvingId"));
   assertTrue(text((View)get(a,"mCobraGuideBrowser")).contains("1  -  2"));save((View)get(a,"mCobraGuideShell"),"compact-live-production");
  }finally{f.clean(a);}
 }
 @Test public void upcomingHasExactDateLocalTimeZoneAndNoScore()throws Exception{
  InfinityLiveActivity a=f.fixture(4);TimeZone old=TimeZone.getDefault();Locale locale=Locale.getDefault();try{TimeZone.setDefault(TimeZone.getTimeZone("America/New_York"));Locale.setDefault(Locale.US);
   CobraProUi.SportsGame data=(CobraProUi.SportsGame)call(a,"cobraProSportsUiGame",game("next","mlb","pre","0","0"));
   assertEquals("Oct 5, 2026",data.date);assertEquals("11:10 AM EDT",data.time);assertEquals("",data.score);assertTrue(data.upcoming);
  }finally{TimeZone.setDefault(old);Locale.setDefault(locale);f.clean(a);}
 }
 @Test public void emptyHeroHidesTeamGraphicsAndKeepsControls()throws Exception{
  InfinityLiveActivity a=f.fixture(4);try{
   CobraProUi.Program data=(CobraProUi.Program)call(a,"cobraProSportsProgram",game("next","mlb","pre","0","0"));assertFalse(data.live);assertEquals("",data.sportsAwayLogo);
   CobraProUi.Hero hero=new CobraProUi.Hero(a,false,new ProSportsIntegrationTest.Calls(),null);hero.bind(data,5,6);ProSportsIntegrationTest.layout(hero,412,300);
   assertEquals(View.GONE,hero.sportsAway.getVisibility());assertEquals(View.GONE,hero.sportsHome.getVisibility());assertEquals(View.GONE,hero.sportsScore.getVisibility());assertEquals(View.VISIBLE,hero.sportsMulti.getVisibility());save(hero,"empty-hero");
  }finally{f.clean(a);}
 }
 @Test public void liveRowsHaveReadableCenteredScoreSeparateTeamsAndExactUpcoming()throws Exception{
  InfinityLiveActivity a=f.fixture(4);try{for(boolean light:new boolean[]{false,true})for(int width:new int[]{320,412,768}){
   CobraProUi.SportsGame data=(CobraProUi.SportsGame)call(a,"cobraProSportsUiGame",game("live","mlb","in","3","2"));
   CobraProUi.GameRow row=new CobraProUi.GameRow(a,light,()->{},()->{});row.bind(data,null);ProSportsIntegrationTest.layout(row,width,CobraProUi.GameRow.height(a,width));
   assertEquals("3  -  2",row.score.getText().toString());assertTrue(row.awayName.getRight()<=row.score.getLeft());assertTrue(row.score.getRight()<=row.homeName.getLeft());assertTrue(row.homeName.getRight()<=row.play.getLeft());assertTrue(row.play.getWidth()>=44&&row.more.getWidth()>=44);
   Bitmap b=Bitmap.createBitmap(width,row.getHeight(),Bitmap.Config.ARGB_8888);row.draw(new Canvas(b));int ink=0;for(int y=row.score.getTop();y<row.score.getBottom();y++)for(int x=row.score.getLeft();x<row.score.getRight();x++){int c=b.getPixel(x,y);if(light?Color.red(c)<80:Color.red(c)>210&&Color.green(c)>210)ink++;}assertTrue("Score ink must render",ink>35);b.recycle();save(row,"live-"+width+"-"+(light?"light":"dark"));
   data=(CobraProUi.SportsGame)call(a,"cobraProSportsUiGame",game("next","mlb","pre","0","0"));row.bind(data,null);ProSportsIntegrationTest.layout(row,width,CobraProUi.GameRow.height(a,width));assertEquals(data.date,row.score.getText().toString());assertEquals(data.time,row.meta.getText().toString());save(row,"upcoming-"+width+"-"+(light?"light":"dark"));
  }}finally{f.clean(a);}
 }
 @Test public void spoilerSettingAppliesWithoutMutatingFeed()throws Exception{
  InfinityLiveActivity a=f.fixture(4);try{Object g=game("live","mlb","in","3","2");((SharedPreferences)get(a,"mPrefs")).edit().putBoolean("cobra_sports_hide_scores",true).commit();CobraProUi.SportsGame d=(CobraProUi.SportsGame)call(a,"cobraProSportsUiGame",g);assertEquals("Scores hidden",d.score);assertEquals("3",get(get(g,"away"),"score"));}finally{f.clean(a);}
 }
 @Test public void channelsSportsTabIsProOnlyAndGroupsStaySelected()throws Exception{
  InfinityLiveActivity a=f.fixture(8);try{pro(a);assertEquals(true,call(a,"cobraProPlayerSportsEnabled"));call(a,"openPlayerOverlay",((List<?>)get(a,"mChannels")).get(0));call(a,"showCobraPlayerDrawer");f.measure(a,412,915);
   View drawer=(View)get(a,"mCobraPlayerDrawer");assertNotNull(drawer.findViewWithTag("cobra_player_tab_SPORTS"));call(a,"cobraRenderPlayerDrawer","CATEGORIES");assertTrue(drawer.findViewWithTag("cobra_player_tab_CATEGORIES").isSelected());call(a,"cobraRenderPlayerDrawer","SPORTS");assertTrue(drawer.findViewWithTag("cobra_player_tab_SPORTS").isSelected());assertTrue(text(drawer).contains("No games are live right now."));
   ((SharedPreferences)get(a,"mPrefs")).edit().putString("guide_view_mode","grid").commit();assertEquals(false,call(a,"cobraProPlayerSportsEnabled"));
  }finally{f.clean(a);}
 }
 @Test public void multiPickerIncludesAllLeaguesAndDoesNotSilentlyAutoLaunch()throws Exception{
  InfinityLiveActivity a=f.fixture(8);try{add(a,game("baseball","mlb","in","1","1"),game("football","nfl","in","17","14"),game("future","nhl","pre","0","0"));pro(a);call(a,"cobraProSportsMulti");
   View sheet=(View)get(a,"mCobraActionSheet");assertNotNull(sheet.findViewWithTag("pro_multi_game_baseball"));assertNotNull(sheet.findViewWithTag("pro_multi_game_football"));assertNull(sheet.findViewWithTag("pro_multi_game_future"));assertFalse(sheet.findViewWithTag("pro_multi_launch").isEnabled());assertNull(get(a,"mMultiOverlay"));
  }finally{f.clean(a);}
 }
 @Test public void multiRejectsDuplicateBroadcastAndEndedGame()throws Exception{
  InfinityLiveActivity a=f.fixture(8);try{Object g=game("one","mlb","in","1","1"),g2=game("two","nfl","in","17","14");add(a,g,g2);pro(a);LinkedHashMap<String,Object> choices=new LinkedHashMap<>();Object channel=((List<?>)get(a,"mChannels")).get(0);
   call(a,"cobraProChooseResolved",g,channel,choices);assertEquals(1,choices.size());call(a,"cobraProChooseResolved",g2,channel,choices);assertEquals(1,choices.size());assertTrue(text((View)get(a,"mCobraActionSheet")).contains("already selected"));
   put(g2,"state","post");call(a,"cobraProChooseResolved",g2,((List<?>)get(a,"mChannels")).get(1),choices);assertEquals(1,choices.size());assertTrue(text((View)get(a,"mCobraActionSheet")).contains("no longer available"));
  }finally{f.clean(a);}
 }
}
