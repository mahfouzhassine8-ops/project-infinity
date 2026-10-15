package com.projectinfinity.kodi;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Matrix;
import android.os.SystemClock;
import android.view.TextureView;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.TextView;
import java.io.File;
import java.io.FileOutputStream;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import org.robolectric.annotation.LooperMode;
import static org.junit.Assert.*;
import static com.projectinfinity.kodi.CobraNavigationUiTest.*;

/** Production-view and production score-queue tests with controlled feeds and player.
 * These do not claim physical fold hardware, network/provider decoding, or delivery tests.
 * Composition deliberately avoids rerunning the inherited 2103321 @Test methods.
 */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=android.app.Application.class,manifest=Config.NONE,
    qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class CobraProRefinementTest {
  CobraProHandoffTest base;
  InfinityLiveActivity a;

  @Before public void setup() throws Exception {
    base=new CobraProHandoffTest();base.setup();a=base.a;
    base.prefs.edit().putBoolean(CobraSportsPreferences.TICKER,true).commit();
    put(get(a,"mCobraPlaybackPolicy"),"resumed",true);
  }
  @After public void cleanup() throws Exception {if(base!=null)base.cleanup();}

  @SuppressWarnings("unchecked") List<Object> games() throws Exception {
    return (List<Object>)get(a,"mCobraSportsGames");
  }
  @SuppressWarnings("unchecked") Map<String,Long> pending() throws Exception {
    return (Map<String,Long>)get(a,"mCobraScorePending");
  }
  TextView ticker() throws Exception {return (TextView)get(a,"mCobraScoreTicker");}
  String key(Object game) throws Exception {return (String)call(a,"cobraSportsKey",game);}
  void refresh() throws Exception {call(a,"cobraRefreshScoreTicker");}
  void score(Object game,String value) throws Exception {put(get(game,"away"),"score",value);}
  Object sports() throws Exception {
    base.pro();Object game=base.addLiveGameForChannel(0);
    call(a,"cobraProFilter",4);base.sportsMini(0,game);base.f.measure(a,412,915);
    return game;
  }
  void regular() throws Exception {base.pro();base.activeMini(0);base.f.measure(a,412,915);}
  Object game(String id,String tier,int score) throws Exception {
    Object game=SportsHubTest.game();put(game,"id",id);put(game,"period",1);
    put(game,"away",SportsHubTest.team(id+"-away","nfl|"+id,id+" visitors",id.toUpperCase(),Integer.toString(score)));
    put(game,"home",SportsHubTest.team(id+"-home","nfl|"+id+"-home",id+" home","HOME","3"));
    games().add(game);
    if(tier!=null)new CobraSportsPreferences(base.prefs).toggle(tier,"nfl|"+id);
    return game;
  }
  void advanceTo(long time) {int count=(int)Math.max(0,(time-SystemClock.uptimeMillis()+15)/16);base.f.frames(count);}
  void finishCurrent() throws Exception {advanceTo((Long)get(a,"mCobraScoreUntil")+400L);}
  int dp(int n) {return Math.round(n*a.getResources().getDisplayMetrics().density);}
  int[] bounds(View v) {return new int[]{v.getLeft(),v.getTop(),v.getWidth(),v.getHeight()};}
  float[] transform(TextureView v) {float[] m=new float[9];v.getTransform(new Matrix()).getValues(m);return m;}
  void assertNoPlaybackMutation(int pane) throws Exception {
    assertSame(base.player,get(a,"mCobraPreviewPlayer"));assertEquals(pane,get(a,"mCobraProHeroIndex"));
    assertEquals(0,base.state.prepares);assertEquals(0,base.state.changes);assertEquals(0,base.state.seeks);
    assertEquals(0,base.state.pauses);assertTrue(base.state.playing);assertFalse(base.state.released);
  }
  void assertBadgeGeometry(TextView alert) throws Exception {
    CobraProUi.Hero hero=base.hero();assertSame("Score alert belongs to the production Hero",hero,alert.getParent());
    assertEquals("LIVE SPORTS",hero.source.getText().toString());
    assertEquals("Same top badge row",hero.source.getTop(),alert.getTop());
    assertEquals("Same badge height",hero.source.getHeight(),alert.getHeight());
    assertEquals("Small fixed gap directly beside LIVE SPORTS",hero.source.getRight()+dp(6),alert.getLeft());
    assertTrue("LIVE and LIVE SPORTS stay in order",hero.live.getRight()<=hero.source.getLeft());
    assertTrue("Alert has usable width",alert.getWidth()>0);
    assertTrue("Protected watermark/status reservation",alert.getRight()<=hero.getWidth()-dp(68));
    assertTrue("Alert does not overlap right-side logo",alert.getRight()<=hero.logo.getLeft());
    assertEquals("A compact single line",1,alert.getMaxLines());
    assertEquals(android.text.TextUtils.TruncateAt.END,alert.getEllipsize());
    assertEquals("No vertical translation into the video",0f,alert.getTranslationY(),0f);
    assertEquals("No horizontal translation into watermark",0f,alert.getTranslationX(),0f);
  }
  void capture(String name) throws Exception {
    String evidence=System.getProperty("cobra.evidence");if(evidence==null)return;
    View view=a.getWindow().getDecorView();File dir=new File(evidence);assertTrue(dir.isDirectory()||dir.mkdirs());
    Bitmap bitmap=Bitmap.createBitmap(view.getWidth(),view.getHeight(),Bitmap.Config.ARGB_8888);
    view.draw(new Canvas(bitmap));
    try(FileOutputStream out=new FileOutputStream(new File(dir,name+".png"))){assertTrue(bitmap.compress(Bitmap.CompressFormat.PNG,100,out));}
    bitmap.recycle();
  }

  @Test public void sameLiveAlertReflowsBesideBadgesThroughCoverNarrowInnerAndLandscape() throws Exception {
    Object game=sports();put(get(game,"away"),"shortName","A very long visiting team name");
    put(get(game,"home"),"shortName","An exceptionally long home team name");refresh();
    TextView alert=ticker();assertNotNull(alert);long until=(Long)get(a,"mCobraScoreUntil");
    int pane=(Integer)get(a,"mCobraProHeroIndex");TextureView video=(TextureView)get(a,"mCobraPreviewTexture");
    for(int[] size:new int[][]{{412,915},{280,640},{673,841},{915,412},{412,915}}){
      base.f.measure(a,size[0],size[1]);refresh();base.f.measure(a,size[0],size[1]);
      assertSame("Resize retains the current alert instance",alert,ticker());assertEquals(until,get(a,"mCobraScoreUntil"));
      assertBadgeGeometry(alert);assertSame(video,get(a,"mCobraPreviewTexture"));assertNoPlaybackMutation(pane);
      if(size[0]!=412||size[1]!=915)capture("322-score-badge-"+size[0]+"x"+size[1]);
    }
    assertTrue("Long content is actually clamped",alert.getPaint().measureText(alert.getText().toString())>alert.getWidth());
  }

  @Test public void alertRevealFadeAndRemovalNeverAlterVideoBoundsCropOrControls() throws Exception {
    sports();
    // Complete the approved Sports collapse before testing alert geometry.
    base.f.frames(30);base.f.measure(a,412,915);
    assertNull("Sports collapse animation completed",get(a,"mCobraProSportsResize"));
    assertEquals(1f,(Float)get(a,"mCobraProSportsCollapse"),0f);
    CobraProUi.Hero hero=base.hero();hero.revealControls();base.f.measure(a,412,915);
    View[] stable={(View)get(a,"mCobraGuideVideo"),(View)get(a,"mCobraPreviewHost"),
      (View)get(a,"mCobraPreviewTexture"),(View)get(a,"mCobraGuideBrowser"),hero.transport,hero};
    int[][] original=new int[stable.length][];for(int i=0;i<stable.length;i++)original[i]=bounds(stable[i]);
    TextureView video=(TextureView)get(a,"mCobraPreviewTexture");float[] crop=transform(video);int pane=(Integer)get(a,"mCobraProHeroIndex");
    refresh();TextView alert=ticker();assertNotNull(alert);base.f.measure(a,412,915);assertBadgeGeometry(alert);
    for(boolean visible:new boolean[]{false,true,false,true}){
      if(visible)hero.revealControls();else{hero.clearFocus();hero.collapseControls();}
      base.f.measure(a,412,915);refresh();assertSame(alert,ticker());assertBadgeGeometry(alert);
      for(int i=0;i<stable.length;i++)assertArrayEquals("Control/alert visibility must not reflow surface "+i,original[i],bounds(stable[i]));
      assertArrayEquals(crop,transform(video),0f);assertNoPlaybackMutation(pane);
    }
    long until=(Long)get(a,"mCobraScoreUntil");advanceTo(until-32);assertSame("Six-second reading interval",alert,ticker());
    advanceTo(until+32);assertSame("Fade retains the view until it finishes",alert,ticker());
    assertEquals("Approved fade duration",380L,alert.animate().getDuration());
    advanceTo(until+416);assertNull("Alert completely removed after fade",ticker());assertNull(alert.getParent());
    base.f.measure(a,412,915);
    for(int i=0;i<stable.length;i++)assertArrayEquals("Removal must not reflow surface "+i,original[i],bounds(stable[i]));
    assertArrayEquals(crop,transform(video),0f);assertNoPlaybackMutation(pane);
  }

  @Test public void compactAlertRendersAcrossAppearanceAmbientAndCinemaWithoutChangingStoredAppearance() throws Exception {
    Object game=sports();int value=30;
    for(String appearance:new String[]{"light","dark"})for(String ambient:new String[]{"off","subtle","immersive"})for(boolean cinema:new boolean[]{false,true}){
      base.prefs.edit().putString("cobra_appearance_mode",appearance).putString(CobraPresentationEffects.AMBIENT,ambient)
        .putBoolean(CobraPresentationEffects.NIGHT,cinema).commit();
      call(a,"cobraApplyAppearanceSettings");call(a,"cobraRefreshAmbient");call(a,"cobraRemoveScoreTicker");
      score(game,Integer.toString(value++));refresh();base.f.measure(a,412,915);base.f.frames(20);
      TextView alert=ticker();assertNotNull(appearance+" "+ambient+" cinema="+cinema,alert);assertBadgeGeometry(alert);
      assertEquals(appearance,base.prefs.getString("cobra_appearance_mode",""));
      assertEquals(appearance.equals("light")?"light":"oled",call(a,"cobraEffectiveAppearanceMode"));
      assertTrue("Readable alert ink",android.graphics.Color.alpha(alert.getCurrentTextColor())>=240);
      assertNotNull("Alert retains its glass backing",alert.getBackground());
      capture("322-score-"+appearance+"-"+ambient+(cinema?"-night":""));
    }
  }

  @Test public void queuedUpdatesCoalesceAndFavoritePinFollowLeadOrdinaryAfterCurrentAlert() throws Exception {
    regular();Object current=game("current",null,7);refresh();TextView first=ticker();long until=(Long)get(a,"mCobraScoreUntil");
    Object ordinary=game("ordinary",null,10),follow=game("follow",CobraSportsPreferences.FOLLOWS,11),
      pin=game("pin",CobraSportsPreferences.PINS,12),favorite=game("favorite",CobraSportsPreferences.FAVORITES,13);
    refresh();score(favorite,"20");refresh();score(favorite,"27");refresh();
    assertSame("A favorite update waits for the current short alert",first,ticker());assertEquals(until,get(a,"mCobraScoreUntil"));
    assertEquals("One pending update per game",4,pending().size());
    for(Object expected:new Object[]{favorite,pin,follow,ordinary}){
      finishCurrent();assertNotNull(ticker());assertEquals("Priority at display time",key(expected),get(a,"mCobraScoreShownKey"));
      if(expected==favorite)assertTrue("Latest coalesced score is shown",ticker().getText().toString().contains("27"));
    }
    finishCurrent();assertNull(ticker());assertTrue(pending().isEmpty());assertNoPlaybackMutation(0);
  }

  @Test public void scorePeriodStatusAndFinalEventsDisplayButIdenticalAndClockRefreshesDoNot() throws Exception {
    regular();Object game=game("events",null,7);refresh();TextView first=ticker();long deadline=(Long)get(a,"mCobraScoreUntil");
    put(game,"detail","Q1 • 10:31");refresh();refresh();assertSame(first,ticker());assertEquals(deadline,get(a,"mCobraScoreUntil"));assertTrue(pending().isEmpty());
    finishCurrent();assertNull(ticker());put(game,"detail","Q1 • 10:30");refresh();assertNull("Clock-only refresh cannot reopen",ticker());
    score(game,"14");refresh();assertNotNull("Score change",ticker());finishCurrent();assertNull(ticker());
    put(game,"period",2);put(game,"detail","Q2 • 15:00");refresh();assertNotNull("Period change",ticker());finishCurrent();assertNull(ticker());
    put(game,"statusName","STATUS_HALFTIME");put(game,"detail","Halftime");refresh();assertNotNull("Major status change",ticker());finishCurrent();assertNull(ticker());
    put(game,"state","post");put(game,"completed",true);put(game,"statusName","STATUS_FINAL");refresh();
    assertNotNull("Final result of a previously observed live game",ticker());assertTrue(ticker().getText().toString().startsWith("FINAL"));
    finishCurrent();assertNull(ticker());refresh();assertNull("Repeated final is not reanimated",ticker());assertNoPlaybackMutation(0);
  }

  @Test public void tickerAndSpoilerPreferencesRemoveAlertsAndNeverExposeHiddenScores() throws Exception {
    regular();Object game=game("protected",null,7);refresh();assertNotNull(ticker());
    new CobraSportsPreferences(base.prefs).protection(true);score(game,"14");refresh();
    assertNull(ticker());assertTrue("Hidden updates cannot remain queued",pending().isEmpty());
    base.f.frames(450);refresh();assertNull(ticker());
    new CobraSportsPreferences(base.prefs).protection(false);refresh();assertNotNull(ticker());
    base.prefs.edit().putBoolean(CobraSportsPreferences.TICKER,false).commit();score(game,"21");refresh();
    assertNull(ticker());assertTrue(pending().isEmpty());assertTrue(((Map)get(a,"mCobraScoreSeen")).isEmpty());
    base.f.frames(450);refresh();assertNull(ticker());assertNoPlaybackMutation(0);
  }

  @Test public void cachedDisabledLeagueCannotProduceOrRetainAnAlert() throws Exception {
    regular();Object enabled=game("nfl-enabled",null,7);Object disabled=game("nba-disabled",null,14);put(disabled,"leagueKey","nba");
    base.prefs.edit().putStringSet("cobra_sports_enabled_leagues",new HashSet<>(Arrays.asList("nfl"))).commit();
    refresh();assertEquals(key(enabled),get(a,"mCobraScoreShownKey"));assertFalse(pending().containsKey(key(disabled)));
    finishCurrent();assertNull(ticker());score(disabled,"21");refresh();assertNull(ticker());
    base.prefs.edit().putStringSet("cobra_sports_enabled_leagues",new HashSet<>(Arrays.asList("nba"))).commit();refresh();
    assertEquals(key(disabled),get(a,"mCobraScoreShownKey"));games().remove(enabled);
    base.prefs.edit().putStringSet("cobra_sports_enabled_leagues",new HashSet<>(Arrays.asList("nfl"))).commit();refresh();
    assertNull("Disabling the displayed league removes the alert",ticker());assertNoPlaybackMutation(0);
  }

  @Test public void backgroundPipLockMultiAndPlayerDrawerSuppressAlertsUntilAllowed() throws Exception {
    regular();Object game=game("suppressed",null,7);int score=14;
    Object policy=get(a,"mCobraPlaybackPolicy");
    Object[][] cases={{policy,"resumed",false,true},{a,"mInPictureInPicture",true,false},
      {a,"mCobraPlayerLocked",true,false},{a,"mMultiOverlay",new FrameLayout(a),null},
      {a,"mCobraPlayerDrawer",new FrameLayout(a),null}};
    for(Object[] c:cases){
      refresh();assertNotNull("Allowed state before "+c[1],ticker());put(c[0],(String)c[1],c[2]);
      score(game,Integer.toString(score++));refresh();assertNull("Suppressed for "+c[1],ticker());
      put(c[0],(String)c[1],c[3]);refresh();assertNotNull("Pending latest update after "+c[1],ticker());
    }
    assertNoPlaybackMutation(0);
  }

  @Test public void actualMobileDrawerAndActionSheetSuppressWithoutStoppingPlayer() throws Exception {
    sports();refresh();assertNotNull(ticker());call(a,"toggleCobraDrawer");
    assertNotNull(a.getWindow().getDecorView().findViewWithTag("cobra_experience_drawer"));assertNull("Drawer suppresses immediately",ticker());
    call(a,"closeCobraExperienceDrawer");score(games().get(0),"35");refresh();assertNotNull(ticker());
    call(a,"showCobraSportsSettings");assertNotNull(get(a,"mCobraActionSheet"));assertNull("Sheet suppresses immediately",ticker());
    call(a,"closeCobraActionSheet");score(games().get(0),"42");refresh();assertNotNull(ticker());
    assertNoPlaybackMutation((Integer)call(a,"cobraProSportsSlotIndex"));
  }

  @Test public void fullscreenTransferAndReturnKeepSameAlertDeadlineAndSportsSession() throws Exception {
    sports();refresh();TextView alert=ticker();long until=(Long)get(a,"mCobraScoreUntil");
    call(a,"promoteCobraPreviewToFullscreen",base.channel(0));refresh();base.f.measure(a,412,915);
    assertSame(alert,ticker());assertSame(get(a,"mPlayerOverlay"),alert.getParent());
    assertEquals(until,get(a,"mCobraScoreUntil"));assertSame(base.player,get(a,"mPlayer"));
    call(a,"closeFullscreenToCobraView");refresh();base.f.measure(a,412,915);
    assertSame(alert,ticker());assertEquals(until,get(a,"mCobraScoreUntil"));assertBadgeGeometry(alert);
    assertNoPlaybackMutation((Integer)call(a,"cobraProSportsSlotIndex"));
  }

  @Test public void powerSheetImmediatelySuppressesScoreAlertWithoutStoppingPlayback() throws Exception {
    Object game=sports();refresh();assertNotNull(ticker());call(a,"showCobraPowerMenu");
    assertNotNull(a.getWindow().getDecorView().findViewWithTag("cobra_power_menu"));assertNull(ticker());
    score(game,"28");refresh();assertNull(ticker());call(a,"closeCobraPowerMenu");refresh();assertNotNull(ticker());
    assertNoPlaybackMutation((Integer)call(a,"cobraProSportsSlotIndex"));
  }

  @Test public void leavingSportsRemovesItsAlertAndOldDismissCannotRemoveANewSessionAlert() throws Exception {
    Object game=sports();refresh();TextView old=ticker();long firstUntil=(Long)get(a,"mCobraScoreUntil");
    // Replace during the old fade so the replacement still has reading time.
    advanceTo(firstUntil+32);assertSame(old,ticker());
    assertNotNull(get(a,"mCobraScoreFadeRemoval"));
    call(a,"cobraProStep",-1);refresh();assertNull(ticker());assertNull(old.getParent());assertTrue(base.state.released);
    assertNull(get(a,"mCobraScoreFadeRemoval"));
    call(a,"cobraProStep",1);base.freshPlayer();base.sportsMini(0,game);score(game,"35");refresh();
    TextView replacement=ticker();assertNotNull(replacement);assertNotSame(old,replacement);
    long replacementUntil=(Long)get(a,"mCobraScoreUntil");
    assertTrue(replacementUntil>firstUntil+416);
    advanceTo(firstUntil+416);assertSame("Cancelled old deadline must not dismiss a new alert",replacement,ticker());
    assertEquals(replacementUntil,get(a,"mCobraScoreUntil"));
    assertSame(base.player,get(a,"mCobraPreviewPlayer"));assertFalse(base.state.released);
    finishCurrent();assertNull(ticker());
  }
}
