package com.projectinfinity.kodi;

import android.app.Application;
import android.content.SharedPreferences;
import android.os.Looper;
import android.os.SystemClock;
import android.view.KeyEvent;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.ListView;
import android.widget.TextView;
import java.lang.reflect.Method;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import org.json.JSONObject;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;
import static com.projectinfinity.kodi.CobraNavigationUiTest.*;

/** Deliberately conflicting saved/active experiences, actual Back handlers and production renderers. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi",
 instrumentedPackages={"com.projectinfinity.kodi"},
 shadows={CobraCleanRuntimeTest.PlayerFactory.class,CobraCleanRuntimeTest.PipPlatform.class,CobraCleanRuntimeTest.TsIo.class})
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class CobraTargetedIsolationTest {
 static final String[] NON_PRO={"mobile","compact","cards","grid"};
 CobraCleanRuntimeTest r;
 @Before public void setup(){SystemClock.setCurrentTimeMillis(1800000L);r=new CobraCleanRuntimeTest();r.before();}
 @After public void cleanup()throws Exception{r.after();}
 void savedPro(){r.prefs.edit().putString("guide_view_mode","focus").commit();}
 void openChannels()throws Exception{r.click(r.description((View)get(r.a,"mPlayerChrome"),"Channels"));}
 void assertNoRetiredScreen()throws Exception{
  assertFalse(String.valueOf(get(r.a,"mCobraStageTitle")).startsWith("COBRA • SPORTS"));
  assertNull(r.tag("cobra_sports_drawer_header"));assertNull(r.tag("cobra_sports_soccer_section"));
 }
 void androidBack()throws Exception{
  // KEYCODE_BACK reaches Android's Activity dispatcher, then the production onBackPressed handler.
  r.a.dispatchKeyEvent(new KeyEvent(KeyEvent.ACTION_DOWN,KeyEvent.KEYCODE_BACK));
  r.a.dispatchKeyEvent(new KeyEvent(KeyEvent.ACTION_UP,KeyEvent.KEYCODE_BACK));r.measure();
 }
 void game()throws Exception{
  put(r.game,"feedUpdatedAtMs",org.robolectric.shadows.ShadowSystem.currentTimeMillis());
  ((List)get(r.a,"mCobraSportsGames")).clear();((List)get(r.a,"mCobraSportsGames")).add(r.game);
  r.prefs.edit().putBoolean(CobraSportsPreferences.TICKER,true).commit();
  put(get(r.a,"mCobraPlaybackPolicy"),"resumed",true);
 }
 void multi()throws Exception{
  ((Map)get(r.a,"mCobraSportsMultiAssignments")).put(get(r.channel(0),"id"),r.game);
  call(r.a,"openMultiView",new ArrayList<>(Arrays.asList(r.channel(0),r.channel(1))));r.measure();
  call(r.a,"cobraSportsRefreshMultiOverlays");
 }
 @Test(timeout=90000) public void savedProCannotExposeFullscreenSportsTabInAnyOtherExperience()throws Exception{
  for(String mode:NON_PRO){r.open(mode,false);savedPro();r.full();openChannels();
   assertFalse(mode,(Boolean)call(r.a,"cobraProPlayerSportsEnabled"));assertNull(mode,r.tag("cobra_player_tab_SPORTS"));
   assertNotNull(r.tag("cobra_player_tab_ALL"));assertNotNull(r.tag("cobra_player_tab_CATEGORIES"));
   assertSame(r.state.proxy,get(r.a,"mPlayer"));assertEquals(1f,r.state.volume,0f);assertNoRetiredScreen();
  }
 }
 @Test(timeout=90000) public void activeProKeepsSportsChannelsOnRegularLiveTvDespiteSavedNonPro()throws Exception{
  for(String mode:new String[]{"focus","sports"}){r.open(mode,false);game();r.prefs.edit().putString("guide_view_mode","compact").commit();r.full();openChannels();
   assertTrue((Boolean)call(r.a,"cobraProPlayerSportsEnabled"));r.click(r.tag("cobra_player_tab_SPORTS"));
   ListView list=(ListView)get(r.a,"mCobraPlayerDrawerList");assertTrue(list.getCount()>0);
   assertTrue(list.getAdapter().getView(0,null,list) instanceof CobraProUi.GameRow);assertSame(r.state.proxy,get(r.a,"mPlayer"));
  }
 }
 @Test(timeout=90000) public void sequentialTransitionsClearSportsDrawerAndAndroidBackRetainsActiveMode()throws Exception{
  r.open("sports",false);r.full();openChannels();r.click(r.tag("cobra_player_tab_SPORTS"));
  for(String mode:NON_PRO){call(r.a,"cobraSwitchMode",mode);savedPro();r.measure();
   assertNull(r.tag("cobra_player_tab_SPORTS"));assertNull(r.tag("cobra_fullscreen_sports_stats"));
   androidBack();assertEquals(mode,get(r.a,"mCobraGuideStyle"));assertNoRetiredScreen();
   r.evidence("TARGETED-BACK-"+mode,new JSONObject().put("active",mode).put("saved","focus").put("retiredScreen",false));
  }
 }
 @Test(timeout=90000) public void staleSportsOwnerCannotReopenDashboardWithBackOrPrimaryReturn()throws Exception{
  for(String mode:NON_PRO){r.open(mode,false);savedPro();
   put(r.a,"mCobraDrawerOwner","sports");r.prefs.edit().putString("cobra_drawer_active_section","sports").commit();
   androidBack();assertEquals("live",call(r.a,"cobraDrawerOwner"));assertEquals(mode,get(r.a,"mCobraGuideStyle"));assertNoRetiredScreen();
   put(r.a,"mCobraDrawerOwner","");assertEquals("live",call(r.a,"cobraDrawerOwner"));call(r.a,"showCobraPrimaryView");r.measure();assertNoRetiredScreen();
  }
 }
 @Test public void retiredDashboardMethodsAndCallbacksAreAbsentFromCompiledActivity()throws Exception{
  List<String> retired=Arrays.asList("showCobraSportsHub","cobraSportsPrepareHeader","cobraSportsRenderCurrent","cobraSportsRenderHub",
   "cobraSportsAddSection","cobraSportsAddSoccerSection","showCobraSportsSoccer","cobraSportsAddLeagueSection","cobraSportsGameCard",
   "cobraSportsTeamMark","showCobraSportsGame","cobraSportsAddTeamRow","showCobraSportsLeague");
  for(Method method:InfinityLiveActivity.class.getDeclaredMethods())assertFalse(method.getName(),retired.contains(method.getName()));
 }
 @Test(timeout=90000) public void approvedProSportsSectionAndBackStayAvailableWithoutStandaloneHub()throws Exception{
  r.open("focus",false);game();call(r.a,"cobraOpenProSportsSection");r.measure();assertTrue((Boolean)get(r.a,"mCobraProSportsActive"));
  assertNotNull(get(r.a,"mCobraGuideList"));assertNoRetiredScreen();androidBack();assertNoRetiredScreen();assertEquals("focus",get(r.a,"mCobraGuideStyle"));
 }
 @Test(timeout=90000) public void savedProCannotCreatePlayerTickerOrClockInOtherExperiences()throws Exception{
  for(String mode:NON_PRO){r.open(mode,false);savedPro();game();r.full();call(r.a,"cobraRefreshScoreTicker");
   assertNull(r.tag("cobra_sports_score_ticker"));assertTrue(((Map)get(r.a,"mCobraScorePending")).isEmpty());
   assertSame(r.state.proxy,get(r.a,"mPlayer"));assertEquals(1f,r.state.volume,0f);
  }
 }
 @Test(timeout=90000) public void leavingProClearsVisibleTickerQueueAndDelayedFadeWithoutMutatingPlayer()throws Exception{
  r.open("focus",false);game();r.full();call(r.a,"cobraRefreshScoreTicker");assertNotNull(get(r.a,"mCobraScoreTicker"));
  Object player=get(r.a,"mPlayer");call(r.a,"cobraSwitchMode","mobile");savedPro();
  assertNull(get(r.a,"mCobraScoreTicker"));assertTrue(((Map)get(r.a,"mCobraScorePending")).isEmpty());assertEquals("",get(r.a,"mCobraScoreWatchedGame"));
  Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofSeconds(8));assertNull(r.tag("cobra_sports_score_ticker"));
  assertSame(player,get(r.a,"mPlayer"));assertFalse(r.state.released);
 }
 @Test(timeout=90000) public void activeProKeepsFreshScoreGameTimingAndScoreAlerts()throws Exception{
  r.open("focus",false);game();put(r.game,"detail","Q3 6:42");r.prefs.edit().putString("guide_view_mode","grid").commit();r.full();
  call(r.a,"cobraRefreshScoreTicker");TextView ticker=(TextView)get(r.a,"mCobraScoreTicker");assertNotNull(ticker);
  assertTrue(ticker.getText().toString().contains("Q3 6:42"));assertTrue(ticker.getText().toString().contains("Lions"));
 }
 @Test(timeout=90000) public void leavingProViaNavigationDisposalImmediatelyClearsPlayerScorePresentation()throws Exception{
  r.open("focus",false);game();r.full();call(r.a,"cobraRefreshScoreTicker");assertNotNull(get(r.a,"mCobraScoreTicker"));
  Object player=get(r.a,"mPlayer");call(r.a,"stopCobraPreview");
  assertFalse((Boolean)get(r.a,"mCobraProActive"));assertNull(get(r.a,"mCobraScoreTicker"));assertTrue(((Map)get(r.a,"mCobraScorePending")).isEmpty());
  assertSame(player,get(r.a,"mPlayer"));assertFalse(r.state.released);
 }
 @Test(timeout=90000) public void sportsMultiScoresCannotRenderOutsideProAndOrdinaryTilesStayAlive()throws Exception{
  for(String mode:NON_PRO){r.open(mode,false);savedPro();game();multi();
   assertNotNull(get(r.a,"mMultiOverlay"));List tiles=(List)call(get(r.a,"mCobraTiles"),"values");assertEquals(2,tiles.size());
   for(Object tile:tiles){assertNull("Sports Multi-View label must be absent",((FrameLayout)get(tile,"view")).findViewWithTag("cobra_sports_multi_overlay"));assertNotNull(get(tile,"player"));}
  }
 }
 @Test(timeout=90000) public void activeProMultiScoresDisappearOnExitAndReturnWithoutReplacingTiles()throws Exception{
  r.open("focus",false);game();multi();Object tile=call(get(r.a,"mCobraTiles"),"get",get(r.channel(0),"id"));
  FrameLayout view=(FrameLayout)get(tile,"view");Object player=get(tile,"player");assertNotNull(view.findViewWithTag("cobra_sports_multi_overlay"));
  put(r.a,"mCobraGuideStyle","mobile");call(r.a,"cobraClearProSportsPresentation");assertNull(view.findViewWithTag("cobra_sports_multi_overlay"));assertSame(player,get(tile,"player"));
  put(r.a,"mCobraGuideStyle","focus");call(r.a,"cobraSportsRefreshMultiOverlays");assertNotNull(view.findViewWithTag("cobra_sports_multi_overlay"));assertSame(player,get(tile,"player"));
 }
 @Test(timeout=90000) public void queuedSportsActionCannotPublishAfterLeavingPro()throws Exception{
  r.open("sports",false);game();r.broadcasts(5);call(r.a,"cobraSportsWatch",r.game);
  call(r.a,"cobraSwitchMode","compact");savedPro();((CobraNavigationUiTest.PendingIo)get(r.a,"mIo")).drain();r.f.frames(3);r.measure();
  assertNull(r.tag("cobra_pro_broadcast_choices"));assertNull(r.tag("cobra_pro_stats_panel"));assertNoRetiredScreen();assertEquals("compact",get(r.a,"mCobraGuideStyle"));
 }
}
