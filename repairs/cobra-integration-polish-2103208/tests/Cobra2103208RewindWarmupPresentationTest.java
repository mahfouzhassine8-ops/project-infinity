package com.projectinfinity.kodi;

import android.app.Application;
import android.view.View;
import android.widget.TextView;
import androidx.media3.common.Player;
import java.util.Collections;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Owned rewind warmup is observed, never driven, by the presentation bridge.
 * Sessions below are constructed only: no proxy, provider request or ingest starts. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w960dp-h540dp-land-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103208RewindWarmupPresentationTest {
  Cobra2103205PresentationUiTest f;Object session;
  @Before public void before()throws Exception {
    f=new Cobra2103205PresentationUiTest();f.before();f.single();
    session=newSession();put("mCobraTimeshiftSession",session);put("mCobraTimeshiftProxyPlayer",f.player.instance);
    put("mCobraTimeshiftGeneration",17);put("mCobraTimeshiftUiState","STARTING");
    f.player.writes.clear();
  }
  Object newSession()throws Exception {
    return CobraNavigationUiTest.construct("CobraLocalTimeshiftSession",f.a.getCacheDir(),
        "https://example.invalid/controlled-warmup.ts",Collections.emptyMap(),120,0);
  }
  void put(String field,Object value)throws Exception {CobraNavigationUiTest.put(f.a,field,value);}
  void sessionField(String field,Object value)throws Exception {CobraNavigationUiTest.put(session,field,value);}
  Object pulse()throws Exception {return f.call("cobraVisualPulseState",f.player.instance);}
  @After public void after()throws Exception {
    if(f!=null){put("mCobraTimeshiftSession",null);put("mCobraTimeshiftProxyPlayer",null);put("mCobraTimeshiftPlayer",null);f.after();}
  }
  @Test public void realOwnedWarmupShowsMarkAndReadyHidesItWithoutTransportWrites()throws Exception {
    for(String state:new String[]{"STARTING","RECORDING"}) {
      put("mCobraTimeshiftUiState",state);f.call("cobraUpdatePlaybackLabels");
      assertEquals(CobraPresentationEffects.PulseState.TIMESHIFT,pulse());
      assertEquals(View.VISIBLE,f.tag("cobra_pulse_emblem").getVisibility());
      assertEquals("",((TextView)f.tag("player_state")).getText().toString());
    }
    // Real readiness wins immediately, even before the UI watcher updates its copy.
    sessionField("ready",true);f.call("cobraUpdatePlaybackLabels");
    assertEquals(CobraPresentationEffects.PulseState.NONE,pulse());
    assertEquals(View.GONE,f.tag("cobra_pulse_emblem").getVisibility());
    assertSame(session,CobraNavigationUiTest.get(f.a,"mCobraTimeshiftSession"));
    assertEquals(17,CobraNavigationUiTest.get(f.a,"mCobraTimeshiftGeneration"));
    assertTrue(f.player.writes.isEmpty());
  }
  @Test public void noWarmupForStoppedClearedOtherOwnerOrNonWarmupStates()throws Exception {
    for(String state:new String[]{"READY","OFF","FAILED","UNSUPPORTED","RECONNECTING"}) {
      put("mCobraTimeshiftUiState",state);assertEquals(state,CobraPresentationEffects.PulseState.NONE,pulse());
    }
    put("mCobraTimeshiftUiState","RECORDING");sessionField("stopped",true);
    assertEquals(CobraPresentationEffects.PulseState.NONE,pulse());sessionField("stopped",false);
    put("mPlayer",null);put("mCobraPreviewPlayer",null);
    assertEquals(CobraPresentationEffects.PulseState.NONE,pulse());
    put("mCobraPreviewPlayer",f.player.instance);assertEquals(CobraPresentationEffects.PulseState.TIMESHIFT,pulse());
    put("mCobraTimeshiftProxyPlayer",null);assertEquals(CobraPresentationEffects.PulseState.NONE,pulse());
    put("mCobraTimeshiftProxyPlayer",f.player.instance);put("mCobraTimeshiftSession",null);
    assertEquals(CobraPresentationEffects.PulseState.NONE,pulse());assertTrue(f.player.writes.isEmpty());
  }
  @Test public void troubleAndSuppressionPriorityRemainAboveWarmup()throws Exception {
    f.player.state=Player.STATE_BUFFERING;assertEquals(CobraPresentationEffects.PulseState.BUFFERING,pulse());
    Object vitals=CobraNavigationUiTest.get(f.binding,"vitals");CobraNavigationUiTest.put(vitals,"lastRecovery","reattach_requested");
    assertEquals(CobraPresentationEffects.PulseState.RECOVERING,pulse());
    CobraNavigationUiTest.put(f.binding,"error","NETWORK_CONNECTION_TIMEOUT");
    assertEquals(CobraPresentationEffects.PulseState.NETWORK,pulse());
    CobraNavigationUiTest.put(f.binding,"error","DECODER_FAILURE");assertEquals(CobraPresentationEffects.PulseState.NONE,pulse());
    CobraNavigationUiTest.put(f.binding,"error","");f.player.state=Player.STATE_READY;f.player.requested=false;
    assertEquals(CobraPresentationEffects.PulseState.NONE,pulse());f.player.requested=true;
    f.player.suppression=Player.PLAYBACK_SUPPRESSION_REASON_TRANSIENT_AUDIO_FOCUS_LOSS;
    assertEquals(CobraPresentationEffects.PulseState.NONE,pulse());f.player.suppression=Player.PLAYBACK_SUPPRESSION_REASON_NONE;
    f.player.state=Player.STATE_IDLE;assertEquals(CobraPresentationEffects.PulseState.NONE,pulse());
    f.player.state=Player.STATE_ENDED;assertEquals(CobraPresentationEffects.PulseState.NONE,pulse());
    assertTrue(f.player.writes.isEmpty());
  }
  @Test public void staleReadinessCallbacksCannotPublishStateForAnotherGenerationOrSession()throws Exception {
    Object stale=newSession();CobraNavigationUiTest.put(stale,"ready",true);
    f.call("cobraWatchTimeshiftReady",stale,16,f.channel,false);
    f.call("cobraWatchTimeshiftReady",stale,17,f.channel,false);
    f.call("cobraWatchTimeshiftReady",session,16,f.channel,false);
    assertEquals("STARTING",CobraNavigationUiTest.get(f.a,"mCobraTimeshiftUiState"));
    assertEquals(CobraPresentationEffects.PulseState.TIMESHIFT,pulse());
    assertSame(session,CobraNavigationUiTest.get(f.a,"mCobraTimeshiftSession"));
    assertEquals(17,CobraNavigationUiTest.get(f.a,"mCobraTimeshiftGeneration"));
    assertTrue(f.player.writes.isEmpty());
  }
}
