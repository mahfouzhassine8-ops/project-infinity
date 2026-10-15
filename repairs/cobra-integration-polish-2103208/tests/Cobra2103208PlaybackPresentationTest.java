package com.projectinfinity.kodi;

import android.app.Application;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.TextView;
import androidx.media3.common.Player;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Controlled Android presentation/state wiring; no hardware decoding claim. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w960dp-h540dp-land-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103208PlaybackPresentationTest {
  Cobra2103205PresentationUiTest f;
  @Before public void before()throws Exception{f=new Cobra2103205PresentationUiTest();f.before();}
  @After public void after()throws Exception{if(f!=null)f.after();}

  @Test public void healthyLiveAndOrdinaryPlaybackHaveNoPersistentMark(){
    for(boolean live:new boolean[]{false,true})assertEquals(CobraPresentationEffects.PulseState.NONE,
        CobraPresentationEffects.pulseState(true,false,false,false,false,false,false,live));
  }
  @Test public void actualTasksStillUseObservedStatusPriority(){
    assertEquals(CobraPresentationEffects.PulseState.NETWORK,CobraPresentationEffects.pulseState(true,true,true,true,true,true,true,true));
    assertEquals(CobraPresentationEffects.PulseState.RECOVERING,CobraPresentationEffects.pulseState(true,false,true,true,false,false,false,true));
    assertEquals(CobraPresentationEffects.PulseState.BUFFERING,CobraPresentationEffects.pulseState(true,false,false,true,false,false,false,true));
    assertEquals(CobraPresentationEffects.PulseState.TIMESHIFT,CobraPresentationEffects.pulseState(true,false,false,false,false,false,true,false));
  }
  @Test public void presentationSuppressesGenericNoiseWithoutHidingFailures(){
    for(String s:new String[]{"LIVE","PLAYING","Buffering","Buffering…","Buffering...","LIVE • rewind warming","rewind warming"})
      assertEquals(s,"",CobraPresentationEffects.visibleStatus(s));
    for(String s:new String[]{"Stream unavailable","Paused","Select a channel","Ended"})
      assertEquals(s,s,CobraPresentationEffects.visibleStatus(s));
  }
  @Test public void noneCannotResurrectLegacyLiveAndErrorStillAppears(){
    CobraPresentationEffects effects=new CobraPresentationEffects(f.a);FrameLayout root=new FrameLayout(f.a);
    TextView legacy=new TextView(f.a);legacy.setText("LIVE");View slot=effects.status(legacy);root.addView(slot);
    effects.updateStatus(root,CobraPresentationEffects.PulseState.BUFFERING,true);assertEquals(View.INVISIBLE,legacy.getVisibility());
    effects.updateStatus(root,CobraPresentationEffects.PulseState.NONE,true);assertEquals(View.GONE,legacy.getVisibility());
    assertEquals(View.GONE,slot.findViewWithTag("cobra_pulse_emblem").getVisibility());assertEquals("",slot.getContentDescription());
    legacy.setText("Stream unavailable");effects.updateStatus(root,CobraPresentationEffects.PulseState.NONE,true);
    assertEquals(View.VISIBLE,legacy.getVisibility());assertEquals("Stream unavailable",slot.getContentDescription());effects.close();
  }
  @Test public void healthyLocalProxyHidesMarkWithoutChangingItsPlayer(){
    try{
      f.single();CobraNavigationUiTest.put(f.a,"mCobraTimeshiftProxyPlayer",f.player.instance);
      f.call("cobraUpdatePlaybackLabels");assertEquals(CobraPresentationEffects.PulseState.NONE,f.call("cobraVisualPulseState",f.player.instance));
      assertEquals(View.GONE,f.tag("player_state").getVisibility());assertEquals(View.GONE,f.tag("cobra_pulse_emblem").getVisibility());
      assertTrue(f.player.writes.isEmpty());assertSame(f.player.instance,CobraNavigationUiTest.get(f.a,"mCobraTimeshiftProxyPlayer"));
    }catch(Exception e){throw new AssertionError(e);}
  }
  @Test public void realBufferingUsesOneIndicatorThenDisappearsOnRecovery()throws Exception{
    f.single();f.player.state=Player.STATE_BUFFERING;f.call("cobraUpdatePlaybackLabels");
    assertEquals("Buffering…",f.call("cobraPlayerState",f.player.instance));
    assertEquals("",((TextView)f.tag("player_state")).getText().toString());
    assertEquals(View.VISIBLE,f.tag("cobra_pulse_emblem").getVisibility());
    f.player.state=Player.STATE_READY;f.call("cobraUpdatePlaybackLabels");
    assertEquals(View.GONE,f.tag("cobra_pulse_emblem").getVisibility());assertEquals(View.GONE,f.tag("player_state").getVisibility());
    assertTrue(f.player.writes.isEmpty());
  }
  @Test public void rewindWarmupIsHiddenAtPresentationBoundaryOnly()throws Exception{
    f.single();
    f.prefs.edit().putBoolean("cobra_live_rewind_enabled",true).commit();
    TextView proof=new TextView(f.a);CobraNavigationUiTest.put(f.a,"mCobraPerformanceOverlayView",proof);
    f.call("cobraSetTimeshiftUiState","STARTING","rewind warming");
    assertEquals("rewind warming",CobraNavigationUiTest.get(f.a,"mCobraTimeshiftUiDetail"));
    assertTrue(((String)f.call("cobraTimeshiftStatusText")).contains("rewind warming"));
    assertEquals("STARTING",CobraPresentationEffects.visibleTimeshiftStatus("STARTING • rewind warming"));
    assertFalse(proof.getText().toString().contains("rewind warming"));
  }
}
