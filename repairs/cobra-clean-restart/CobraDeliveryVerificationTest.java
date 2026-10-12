package com.projectinfinity.kodi;

import android.app.Application;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Insets;
import android.graphics.Paint;
import android.graphics.Rect;
import android.os.Looper;
import android.os.SystemClock;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
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
import java.util.List;
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

  @Test public void horizontalGestureKeepsChromeUntilReleaseAndScrollsUsingRealTouch()throws Exception{
    r.window(280,280);r.open("sports",false);r.full();
    HorizontalScrollView scroll=(HorizontalScrollView)r.tag("cobra_pro_fullscreen_scroll");
    View chrome=(View)get(r.a,"mPlayerChrome");call(r.a,"showPlayerChromeTemporarily");
    long start=SystemClock.uptimeMillis();float y=scroll.getHeight()/2f;
    motion(scroll,start,MotionEvent.ACTION_DOWN,scroll.getWidth()-12,y);
    motion(scroll,start,MotionEvent.ACTION_MOVE,scroll.getWidth()/2f,y);
    Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofSeconds(8));
    assertTrue("New horizontal control gesture must not disappear under the finger",chrome.isShown());
    motion(scroll,start,MotionEvent.ACTION_MOVE,10,y);motion(scroll,start,MotionEvent.ACTION_UP,10,y);r.f.frames(8);
    assertTrue("Gesture, not scrollTo(), must move the rail",scroll.getScrollX()>0);
    assertEquals(Arrays.asList("Channels","Display","Multi-View","PiP","Stats","More"),r.controls());
  }
  @Test public void delayedSportsFeedDoesNotPresentDetailedNumbersAsCurrent()throws Exception{
    r.open("sports",false);r.repository();put(r.game,"feedUpdatedAtMs",System.currentTimeMillis()-600000L);
    openStats();drain();String text=sheet();
    assertTrue(text.contains("delayed")||text.contains("Delayed"));
    assertFalse("Delayed feed must not expose unqualified current yardage",text.contains("Total yards 320"));
    assertFalse("Delayed feed must not expose unqualified current player leaders",text.contains("Passing 240"));
    assertTrue(text.contains("Ford Field"));
  }
  @Test public void openStatsDropsScoresWhenTheSameGameBecomesStale()throws Exception{
    r.open("sports",false);r.repository();openStats();drain();assertTrue(sheet().contains("Total yards 320"));
    put(r.game,"feedAvailable",false);
    Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofSeconds(3));r.measure();
    assertFalse("Already-open new Stats panel must honor freshness changes",sheet().contains("Total yards 320"));
  }
  @Test public void statsFeedMetadataSuppliesVenueLocationSituationAndTeamValuesWithoutInventingMissingData()throws Exception{
    r.open("sports",false);
    JSONObject payload=new JSONObject("{\"header\":{\"id\":\"401999999\",\"competitions\":[{\"id\":\"401999999\",\"status\":{\"period\":3,\"displayClock\":\"6:42\",\"type\":{\"state\":\"in\",\"shortDetail\":\"Q3 6:42\"}},\"situation\":{\"downDistanceText\":\"2nd & 9 at DET 30\",\"possession\":\"8\"}}]},\"gameInfo\":{\"venue\":{\"fullName\":\"Ford Field\",\"address\":{\"city\":\"Detroit\",\"state\":\"MI\"}}},\"boxscore\":{\"teams\":[{\"team\":{\"id\":\"9\"},\"statistics\":[{\"name\":\"totalYards\",\"label\":\"Total Yards\",\"displayValue\":\"280\"}]},{\"team\":{\"id\":\"8\"},\"statistics\":[{\"name\":\"totalYards\",\"label\":\"Total Yards\",\"displayValue\":\"320\"}]}]}}");
    Object six=get(r.a,"mCobraSix");Object parsed=call(six,"readSummaryMetadata",r.game,payload);
    assertEquals("Detroit, MI",get(parsed,"location"));assertEquals("Ford Field",get(parsed,"venue"));
    assertTrue(((String)get(parsed,"situation")).contains("Lions"));assertTrue(((String)get(parsed,"situation")).contains("2nd & 9"));
    assertEquals(1,((List)get(parsed,"teamStats")).size());
    Object absent=call(six,"readSummaryMetadata",r.game,new JSONObject());assertEquals("",get(absent,"location"));assertEquals("",get(absent,"situation"));assertTrue(((List)get(absent,"teamStats")).isEmpty());
    payload.getJSONObject("header").put("id","wrong-game");Object wrong=call(six,"readSummaryMetadata",r.game,payload);assertEquals("",get(wrong,"location"));assertTrue(((List)get(wrong,"teamStats")).isEmpty());
  }
  @Test public void broadcastPanelKeepsFourWholeTouchRowsInsideSystemInsetsAndScrollsBeyondEight()throws Exception{
    r.window(280,280);r.open("sports",false);r.broadcasts(12);r.full();r.watchGame();
    View panel=(View)get(r.a,"mCobraActionSheet");
    WindowInsets insets=new WindowInsets.Builder().setInsets(WindowInsets.Type.systemBars(),Insets.of(8,24,8,16)).build();
    r.decor().dispatchApplyWindowInsets(insets);panel.dispatchApplyWindowInsets(insets);r.measure();
    ListView list=(ListView)r.tag("cobra_pro_broadcast_choices");assertEquals(12,list.getCount());
    assertTrue(list.getHeight()>=192);Rect visible=r.rect(list);
    for(int i=0;i<4;i++){Rect row=r.rect(list.getChildAt(i));assertTrue(visible.contains(row));assertTrue(row.height()>=48);}
    r.listIndex(list,11);r.click(list.getChildAt(11-list.getFirstVisiblePosition()));assertEquals("broadcast:11",get(get(r.a,"mPlaying"),"id"));
  }
  @Test public void fullscreenStatsGlyphIsPixelIdenticalToApprovedMiniRenderer()throws Exception{
    r.open("sports",false);r.full();View stats=r.tag("cobra_fullscreen_sports_stats");int side=24;
    Bitmap expected=Bitmap.createBitmap(side,side,Bitmap.Config.ARGB_8888),actual=Bitmap.createBitmap(side,side,Bitmap.Config.ARGB_8888);
    try{
      int ink=(Integer)get(stats,"ink");CobraProUi.icon(new Canvas(expected),new Paint(3),"stats",0,0,side,ink);
      assertTrue((Boolean)call(get(r.a,"mCobraSix"),"drawStats",stats,new Canvas(actual),12f,12f));
      for(int y=0;y<side;y++)for(int x=0;x<side;x++)assertEquals("Stats glyph pixel "+x+","+y,expected.getPixel(x,y),actual.getPixel(x,y));
    }finally{expected.recycle();actual.recycle();}
  }
  @Test public void allModeThemeAmbientTransitionsKeepVideoAndProIsolation()throws Exception{
    for(String mode:CobraCleanRuntimeTest.MODES){r.open(mode,false);put(r.a,"mCobraEffects",new CobraPresentationEffects(r.a));Object session=get(r.a,"mCobraPreviewPlayer");
      for(String appearance:new String[]{"light","dark","oled","system"})for(int ambient:new int[]{0,1,2}){
        r.prefs.edit().putString("cobra_appearance_mode",appearance).putInt(CobraPresentationEffects.AMBIENT,ambient).commit();
        call(r.a,"cobraRefreshVisualEffects");r.measure();assertSame(session,get(r.a,"mCobraPreviewPlayer"));
        assertEquals(appearance,r.prefs.getString("cobra_appearance_mode",""));
      }
      r.screenshot("delivery-theme-"+mode);r.full();r.checkControls(mode);r.screenshot("delivery-fullscreen-"+mode);
      assertFalse(r.state.released);
    }
  }
  @Test public void noDataAndSpoilerTransitionsRetainCloseAndNeverManufactureMetadata()throws Exception{
    r.open("sports",false);r.repository();put(r.game,"venue","");put(r.game,"timeConfirmed",false);openStats();drain();
    assertTrue(sheet().contains("Time TBA"));assertTrue(sheet().contains("Unavailable"));
    r.prefs.edit().putBoolean("cobra_sports_hide_scores",true).commit();
    Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofSeconds(3));r.measure();
    assertFalse("Open new Stats cannot retain protected statistics",sheet().contains("Total yards 320"));
    View close=r.description((View)get(r.a,"mCobraActionSheet"),"Close menu");r.click(close);assertNull(get(r.a,"mCobraActionSheet"));assertSame(r.state.proxy,get(r.a,"mPlayer"));
  }
}
