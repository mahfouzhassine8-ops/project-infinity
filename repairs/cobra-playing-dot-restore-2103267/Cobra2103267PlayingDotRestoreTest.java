package com.projectinfinity.kodi;

import android.app.Application;
import android.graphics.Color;
import androidx.media3.common.Player;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE)
public class Cobra2103267PlayingDotRestoreTest {
  @Test public void actualPlaybackTruthOwnsTheIndicator(){
    int none=Player.PLAYBACK_SUPPRESSION_REASON_NONE;
    assertTrue(InfinityLiveActivity.CobraPlayingIndicatorPolicy.active(true,true,none,Player.STATE_READY,false));
    assertTrue(InfinityLiveActivity.CobraPlayingIndicatorPolicy.active(true,true,none,Player.STATE_BUFFERING,false));
    assertFalse(InfinityLiveActivity.CobraPlayingIndicatorPolicy.active(false,true,none,Player.STATE_READY,false));
    assertFalse(InfinityLiveActivity.CobraPlayingIndicatorPolicy.active(true,false,none,Player.STATE_READY,false));
    assertFalse(InfinityLiveActivity.CobraPlayingIndicatorPolicy.active(true,true,1,Player.STATE_READY,false));
    assertFalse(InfinityLiveActivity.CobraPlayingIndicatorPolicy.active(true,true,none,Player.STATE_ENDED,false));
    assertFalse(InfinityLiveActivity.CobraPlayingIndicatorPolicy.active(true,true,none,Player.STATE_READY,true));
  }
  @Test public void lockedHandoffAndColorMorphAreRestored(){
    assertEquals(180L,InfinityLiveActivity.CobraPlayingIndicatorPolicy.HANDOFF_MS);
    assertEquals(240L,InfinityLiveActivity.CobraPlayingIndicatorPolicy.COLOR_MORPH_MS);
    assertEquals(.42f,InfinityLiveActivity.CobraPlayingIndicatorPolicy.handoffAlpha(true,0),.001f);
    assertEquals(1f,InfinityLiveActivity.CobraPlayingIndicatorPolicy.handoffAlpha(true,180),.001f);
    assertEquals(0f,InfinityLiveActivity.CobraPlayingIndicatorPolicy.handoffAlpha(false,180),.001f);
  }
  @Test public void oledFloorCannotDisappear(){
    assertEquals(218,InfinityLiveActivity.CobraPlayingIndicatorPolicy.OLED_CORE_FLOOR_ALPHA);
    assertEquals(.58f,InfinityLiveActivity.CobraPlayingIndicatorPolicy.OLED_GLOW_FLOOR,.001f);
    assertEquals(218,InfinityLiveActivity.CobraPlayingIndicatorPolicy.oledCoreAlpha(0f));
    assertEquals(255,InfinityLiveActivity.CobraPlayingIndicatorPolicy.oledCoreAlpha(1f));
  }
  @Test public void nightCinemaKeepsLockedAmber(){
    assertEquals(0xffffc247,InfinityLiveActivity.CobraPlayingIndicatorPolicy.CINEMA_AMBER);
    assertTrue(InfinityLiveActivity.CobraPlayingIndicatorPolicy.pulsePeriodMs(true)>InfinityLiveActivity.CobraPlayingIndicatorPolicy.pulsePeriodMs(false));
    int cyan=Color.rgb(0,200,255), amber=InfinityLiveActivity.CobraPlayingIndicatorPolicy.CINEMA_AMBER;
    assertEquals(cyan,InfinityLiveActivity.CobraPlayingIndicatorPolicy.blendColor(cyan,amber,0f));
    assertEquals(amber,InfinityLiveActivity.CobraPlayingIndicatorPolicy.blendColor(cyan,amber,1f));
  }
}
