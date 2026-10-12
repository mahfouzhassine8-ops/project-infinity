package com.projectinfinity.kodi;

import android.app.Application;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Insets;
import android.graphics.Paint;
import android.graphics.Rect;
import android.os.Looper;
import android.os.SystemClock;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowInsets;
import android.widget.HorizontalScrollView;
import android.widget.ListView;
import org.json.JSONObject;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.Shadows;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import org.robolectric.annotation.LooperMode;
import java.time.Duration;
import java.util.Arrays;
import java.util.ArrayList;
import java.util.List;
import java.lang.reflect.Proxy;
import static org.junit.Assert.*;
import static com.projectinfinity.kodi.CobraNavigationUiTest.*;

/** Supplemental delivery tests; the original 185 cases remain mandatory and unchanged. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi",
  instrumentedPackages={"com.projectinfinity.kodi"},
  shadows={CobraCleanRuntimeTest.PlayerFactory.class,CobraCleanRuntimeTest.PipPlatform.class,CobraCleanRuntimeTest.TsIo.class})
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class CobraDeliveryVerificationTest {
  CobraCleanRuntimeTest r;
  @Before public void setup(){r=new CobraCleanRuntimeTest();r.before();}
  @After public void cleanup()throws Exception{r.after();}
  void drain()throws Exception{((CobraNavigationUiTest.PendingIo)get(r.a,"mIo")).drain();r.f.frames(3);r.measure();}
  void motion(View target,long down,int action,float x,float y){MotionEvent e=MotionEvent.obtain(down,SystemClock.uptimeMillis(),action,x,y,0);try{target.dispatchTouchEvent(e);}finally{e.recycle();}}
  void openStats()throws Exception{r.full();r.click(r.tag("cobra_fullscreen_sports_stats"));}
  String sheet()throws Exception{return r.text((View)get(r.a,"mCobraActionSheet"));}

  @Test(timeout=90000) public void horizontalGestureKeepsChromeUntilReleaseAndScrollsUsingRealTouch()throws Exception{
    r.window(280,280);r.open("sports",false);r.full();HorizontalScrollView scroll=(HorizontalScrollView)r.tag("cobra_pro_fullscreen_scroll");
    View chrome=(View)get(r.a,"mPlayerChrome");call(r.a,"showPlayerChromeTemporarily");long start=SystemClock.uptimeMillis();float y=scroll.getHeight()/2f;
    motion(scroll,start,MotionEvent.ACTION_DOWN,scroll.getWidth()-12,y);motion(scroll,start,MotionEvent.ACTION_MOVE,scroll.getWidth()/2f,y);
    Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofSeconds(8));assertTrue("New horizontal control gesture must not disappear under the finger",chrome.isShown());
    motion(scroll,start,MotionEvent.ACTION_MOVE,10,y);motion(scroll,start,MotionEvent.ACTION_UP,10,y);r.f.frames(8);
    assertTrue("Gesture, not scrollTo(), must move the rail",scroll.getScrollX()>0);assertEquals(Arrays.asList("Channels","Display","Multi-View","PiP","Stats","More"),r.controls());
  }
  @Test(timeout=90000) public void delayedSportsFeedDoesNotPresentDetailedNumbersAsCurrent()throws Exception{
    r.open("sports",false);r.repository();put(r.game,"feedUpdatedAtMs",System.currentTimeMillis()-600000L);openStats();drain();String text=sheet();
    assertTrue(text.contains("delayed")||text.contains("Delayed"));assertFalse("Delayed feed must not expose unqualified current yardage",text.contains("Total yards 320"));assertFalse("Delayed feed must not expose unqualified current player leaders",text.contains("Passing 240"));assertTrue(text.contains("Ford Field"));
  }
  @Test(timeout=90000) public void openStatsDropsScoresWhenTheSameGameBecomesStale()throws Exception{
    r.open("sports",false);r.repository();openStats();drain();assertTrue(sheet().contains("Total yards 320"));put(r.game,"feedAvailable",false);
    Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofSeconds(3));r.measure();assertFalse("Already-open new Stats panel must honor freshness changes",sheet().contains("Total yards 320"));
    put(r.game,"feedAvailable",true);put(r.game,"feedUpdatedAtMs",System.currentTimeMillis());Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofSeconds(2));r.measure();
    String trace=" delayed="+call(r.a,"cobraSportsDelayed",r.game)+" sameGame="+(r.game==call(r.a,"cobraSportsGame",get(r.game,"id")))+" sports="+call(get(r.a,"mCobraSix"),"sports")+" sheet="+sheet();
    View owner=(View)get(r.a,"mCobraActionSheet");Object info=org.robolectric.util.ReflectionHelpers.getField(owner,"mListenerInfo");
    List listeners=org.robolectric.util.ReflectionHelpers.getField(info,"mOnAttachStateChangeListeners");
    if(listeners!=null)for(Object listener:listeners)if(listener.getClass().getSimpleName().equals("StatsSession"))trace+=" current="+call(listener,"current")+" closed="+get(listener,"closed")+" summary="+get(listener,"summary")+" age="+(System.currentTimeMillis()-(Long)get(listener,"receivedAt"))+" rendered="+get(listener,"rendered");
    assertTrue("Fresh data can recover without losing the sheet"+trace,sheet().contains("Total yards 320"));
  }
  @Test(timeout=90000) public void statsFeedMetadataSuppliesVenueLocationSituationAndTeamValuesWithoutInventingMissingData()throws Exception{
    r.window(840,720);r.open("sports",false);
    JSONObject payload=new JSONObject("{\"header\":{\"id\":\"401999999\",\"competitions\":[{\"id\":\"401999999\",\"status\":{\"period\":3,\"displayClock\":\"6:42\",\"type\":{\"state\":\"in\",\"shortDetail\":\"Q3 6:42\"}},\"situation\":{\"downDistanceText\":\"2nd & 9 at DET 30\",\"possession\":\"8\"}}]},\"gameInfo\":{\"venue\":{\"fullName\":\"Ford Field\",\"address\":{\"city\":\"Detroit\",\"state\":\"MI\"}}},\"boxscore\":{\"teams\":[{\"team\":{\"id\":\"9\"},\"statistics\":[{\"name\":\"totalYards\",\"label\":\"Total Yards\",\"displayValue\":\"280\"}]},{\"team\":{\"id\":\"8\"},\"statistics\":[{\"name\":\"totalYards\",\"label\":\"Total Yards\",\"displayValue\":\"320\"}]}]}}");
    Object six=get(r.a,"mCobraSix"),parsed=call(six,"readSummaryMetadata",r.game,payload);
    assertEquals("Detroit, MI",get(parsed,"location"));assertEquals("Ford Field",get(parsed,"venue"));assertTrue(((String)get(parsed,"situation")).contains("Lions"));assertTrue(((String)get(parsed,"situation")).contains("2nd & 9"));assertEquals(1,((List)get(parsed,"teamStats")).size());
    Object summary=construct("CobraSportsSummary");put(summary,"proData",parsed);((List)get(summary,"lines")).addAll(Arrays.asList("LEADERS","Player detailed fixture"));
    Class<?> type=Class.forName(InfinityLiveActivity.class.getName()+"$CobraSportsRepository");
    Object repo=Proxy.newProxyInstance(type.getClassLoader(),new Class[]{type},(p,m,args)->{if(m.getName().equals("summary"))return summary;if(m.getName().equals("label"))return "Controlled metadata";if(m.getName().equals("scoreboard"))return construct("CobraSportsBoardResult");return new ArrayList<>();});put(r.a,"mCobraSportsRepository",repo);
    openStats();drain();for(String expected:new String[]{"Detroit, MI","Lions possession","Team Stats","Total Yards","LEADERS","Player detailed fixture"})assertTrue(expected,sheet().contains(expected));r.screenshot("delivery-stats-metadata-wide");
    r.window(280,280);r.screenshot("delivery-stats-metadata-small");
    Object absent=call(six,"readSummaryMetadata",r.game,new JSONObject());assertEquals("",get(absent,"location"));assertEquals("",get(absent,"situation"));assertTrue(((List)get(absent,"teamStats")).isEmpty());
    JSONObject competition=payload.getJSONObject("header").getJSONArray("competitions").getJSONObject(0);competition.getJSONObject("status").getJSONObject("type").put("state","pre");competition.put("boxscoreAvailable",false);
    Object pre=call(six,"readSummaryMetadata",r.game,payload);assertTrue("Pre-game averages cannot masquerade as a live boxscore",((List)get(pre,"teamStats")).isEmpty());
    payload.getJSONObject("header").put("id","wrong-game");Object wrong=call(six,"readSummaryMetadata",r.game,payload);assertEquals("",get(wrong,"location"));assertTrue(((List)get(wrong,"teamStats")).isEmpty());assertFalse((Boolean)get(wrong,"valid"));
  }
  @Test(timeout=90000) public void broadcastPanelKeepsFourWholeTouchRowsInsideSystemInsetsAndScrollsBeyondEight()throws Exception{
    r.window(280,280);r.open("sports",false);r.broadcasts(12);r.full();r.watchGame();View panel=(View)get(r.a,"mCobraActionSheet");
    WindowInsets insets=new WindowInsets.Builder().setInsets(WindowInsets.Type.systemBars(),Insets.of(8,24,8,16)).build();r.decor().dispatchApplyWindowInsets(insets);panel.dispatchApplyWindowInsets(insets);r.measure();
    ListView list=(ListView)r.tag("cobra_pro_broadcast_choices");assertEquals(12,list.getCount());assertTrue(list.getHeight()>=192);Rect visible=r.rect(list);
    for(int i=0;i<4;i++){Rect row=r.rect(list.getChildAt(i));assertTrue(visible.contains(row));assertTrue(row.height()>=48);}
    r.listIndex(list,11);r.click(list.getChildAt(11-list.getFirstVisiblePosition()));assertEquals("broadcast:11",get(get(r.a,"mPlaying"),"id"));
  }
  @Test(timeout=90000) public void fullscreenStatsGlyphIsPixelIdenticalToApprovedMiniRenderer()throws Exception{
    r.open("sports",false);r.full();View stats=r.tag("cobra_fullscreen_sports_stats");int side=24;Bitmap expected=Bitmap.createBitmap(side,side,Bitmap.Config.ARGB_8888),actual=Bitmap.createBitmap(side,side,Bitmap.Config.ARGB_8888);
    try{int ink=(Integer)get(stats,"ink");CobraProUi.icon(new Canvas(expected),new Paint(3),"stats",0,0,side,ink);assertTrue((Boolean)call(get(r.a,"mCobraSix"),"drawStats",stats,new Canvas(actual),12f,12f));for(int y=0;y<side;y++)for(int x=0;x<side;x++)assertEquals("Stats glyph pixel "+x+","+y,expected.getPixel(x,y),actual.getPixel(x,y));}finally{expected.recycle();actual.recycle();}
  }
  @Test(timeout=90000) public void allModeThemeAmbientTransitionsKeepVideoAndProIsolation()throws Exception{
    for(String mode:CobraCleanRuntimeTest.MODES){r.open(mode,false);put(r.a,"mCobraEffects",new CobraPresentationEffects(r.a));Object session=get(r.a,"mCobraPreviewPlayer");
      for(String appearance:new String[]{"light","dark","oled","system"})for(String ambient:new String[]{"off","subtle","immersive"}){
        r.prefs.edit().putString("cobra_appearance_mode",appearance).putString(CobraPresentationEffects.AMBIENT,ambient).commit();call(r.a,"cobraRefreshVisualEffects");r.measure();assertSame(session,get(r.a,"mCobraPreviewPlayer"));assertEquals(appearance,r.prefs.getString("cobra_appearance_mode",""));
        if(ambient.equals("off"))r.screenshot("delivery-theme-"+mode+"-"+appearance);
      }
      r.full();r.checkControls(mode);r.screenshot("delivery-fullscreen-"+mode);assertFalse(r.state.released);
    }
  }
  @Test(timeout=90000) public void noDataAndSpoilerTransitionsRetainCloseAndNeverManufactureMetadata()throws Exception{
    r.open("sports",false);r.repository();put(r.game,"venue","");put(r.game,"timeConfirmed",false);openStats();drain();assertTrue(sheet().contains("Time TBA"));assertTrue(sheet().contains("Unavailable"));
    r.prefs.edit().putBoolean("cobra_sports_hide_scores",true).commit();Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofSeconds(3));r.measure();assertFalse("Open new Stats cannot retain protected statistics",sheet().contains("Total yards 320"));
    View close=r.description((View)get(r.a,"mCobraActionSheet"),"Close menu");r.click(close);assertNull(get(r.a,"mCobraActionSheet"));assertSame(r.state.proxy,get(r.a,"mPlayer"));
    Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofSeconds(3));assertNull("Detached observer cannot reopen its Stats panel",get(r.a,"mCobraActionSheet"));
  }
}
