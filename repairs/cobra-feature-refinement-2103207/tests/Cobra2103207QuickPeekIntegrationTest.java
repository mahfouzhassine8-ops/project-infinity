package com.projectinfinity.kodi;
import android.app.Application;
import android.view.View;
import androidx.media3.common.C;
import androidx.media3.exoplayer.ExoPlayer;
import java.util.*;
import org.json.JSONObject;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Activity capacity/ownership wiring with controlled response delivery and a missing
 * local media file. No external provider traffic or simultaneous decoder claim. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103207QuickPeekIntegrationTest {
  Cobra2103205SessionUiTest f;Object source;Cobra2103205SessionUiTest.CounterPlayer main;
  @Before public void before()throws Exception{
    f=new Cobra2103205SessionUiTest();f.before();main=f.main();
    List<Object> sources=(List<Object>)f.get(f.a,"mSources");sources.clear();
    source=CobraNavigationUiTest.construct("LiveSource","fixture","xtream","Fixture","https://example.invalid","test","test","","");sources.add(source);
    f.put(f.second,"primaryUrl","file:///does-not-exist-cobra207-peek.ts");
  }
  @After public void after()throws Exception{if(f!=null)f.after();}
  void capacity(int max,int active)throws Exception{f.call("cobraRememberPeekCapacity",source,new JSONObject().put("max_connections",max).put("active_cons",active));}
  void open()throws Exception{f.call("cobraShowQuickPeek",f.second,f.get(f.a,"mPlayerTexture"));}
  @Test public void spareCapacityCreatesSilentSecondaryAndCloseNeverTouchesMain()throws Exception{
    capacity(2,1);open();Object session=f.get(f.a,"mCobraQuickPeek");assertNotNull(session);
    ExoPlayer secondary=(ExoPlayer)f.get(session,"player");assertNotNull(secondary);assertNotSame(main.player,secondary);assertEquals(0f,secondary.getVolume(),0f);assertTrue(secondary.getTrackSelectionParameters().disabledTrackTypes.contains(C.TRACK_TYPE_AUDIO));
    assertEquals(View.VISIBLE,f.tag("cobra_quick_peek_video").getVisibility());assertTrue(f.tag("cobra_quick_peek_video").isClickable());assertTrue(main.commands.isEmpty());
    f.call("closeCobraActionSheet");assertEquals(true,CobraNavigationUiTest.call(session,"closed"));assertSame(main.player,f.get(f.a,"mPlayer"));assertTrue(main.commands.isEmpty());
  }
  @Test public void expiredCapacityWaitsForRefreshInsteadOfPrematureUnavailable()throws Exception{
    ((Map<String,CobraQuickPeekSession.Capacity>)f.get(f.a,"mCobraPeekCapacity")).put("fixture",new CobraQuickPeekSession.Capacity(2,1,System.currentTimeMillis()-120001));open();assertNull(f.get(f.a,"mCobraQuickPeek"));
    assertNotNull(f.get(f.a,"mCobraQuickPeekCapacityReady"));assertTrue(((Set<?>)f.get(f.a,"mCobraPeekCapacityRequests")).contains("fixture"));assertTrue(main.commands.isEmpty());
    capacity(2,1);((Runnable)f.get(f.a,"mCobraQuickPeekCapacityReady")).run();assertNotNull(f.get(f.a,"mCobraQuickPeek"));assertTrue(main.commands.isEmpty());
  }
  @Test public void closedSheetRejectsLateCapacityDelivery()throws Exception{open();Runnable old=(Runnable)f.get(f.a,"mCobraQuickPeekCapacityReady");f.call("closeCobraActionSheet");capacity(2,1);old.run();assertNull(f.get(f.a,"mCobraQuickPeek"));assertTrue(main.commands.isEmpty());}
  @Test public void exhaustedCapacityNeverCreatesSecondStream()throws Exception{capacity(1,1);open();assertNull(f.get(f.a,"mCobraQuickPeek"));assertEquals(View.GONE,f.tag("cobra_quick_peek_video").getVisibility());assertTrue(main.commands.isEmpty());}
}
