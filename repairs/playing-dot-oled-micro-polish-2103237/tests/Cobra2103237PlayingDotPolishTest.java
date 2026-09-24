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
public class Cobra2103237PlayingDotPolishTest {
  @Test public void handoffIsImmediateTruthWithShortVisualBlend(){
    assertEquals(180L,InfinityLiveActivity.CobraPlayingIndicatorPolicy.HANDOFF_MS);
    assertEquals(.42f,InfinityLiveActivity.CobraPlayingIndicatorPolicy.handoffAlpha(true,0L),.001f);
    assertEquals(1f,InfinityLiveActivity.CobraPlayingIndicatorPolicy.handoffAlpha(true,180L),.001f);
    assertEquals(1f,InfinityLiveActivity.CobraPlayingIndicatorPolicy.handoffAlpha(false,0L),.001f);
    assertEquals(0f,InfinityLiveActivity.CobraPlayingIndicatorPolicy.handoffAlpha(false,180L),.001f);
  }

  @Test public void ambientAndCinemaColorMorphUsesBoundedSmoothInterpolation(){
    assertEquals(240L,InfinityLiveActivity.CobraPlayingIndicatorPolicy.COLOR_MORPH_MS);
    int from=Color.rgb(0,200,255),to=InfinityLiveActivity.CobraPlayingIndicatorPolicy.CINEMA_AMBER;
    assertEquals(from,InfinityLiveActivity.CobraPlayingIndicatorPolicy.blendColor(from,to,0f));
    assertEquals(to,InfinityLiveActivity.CobraPlayingIndicatorPolicy.blendColor(from,to,1f));
    int mid=InfinityLiveActivity.CobraPlayingIndicatorPolicy.blendColor(from,to,.5f);
    assertNotEquals(from,mid);assertNotEquals(to,mid);
    assertEquals(128,Color.red(mid),1);
  }

  @Test public void oledCoreNeverDisappearsAtPulseFloor(){
    assertEquals(218,InfinityLiveActivity.CobraPlayingIndicatorPolicy.OLED_CORE_FLOOR_ALPHA);
    assertEquals(218,InfinityLiveActivity.CobraPlayingIndicatorPolicy.oledCoreAlpha(0f));
    assertEquals(255,InfinityLiveActivity.CobraPlayingIndicatorPolicy.oledCoreAlpha(1f));
    assertTrue(InfinityLiveActivity.CobraPlayingIndicatorPolicy.oledCoreAlpha(.5f)>=218);
  }

  @Test public void oledGlowKeepsTransparentNonzeroFloor(){
    assertEquals(.58f,InfinityLiveActivity.CobraPlayingIndicatorPolicy.OLED_GLOW_FLOOR,.001f);
    assertEquals(.58f,InfinityLiveActivity.CobraPlayingIndicatorPolicy.oledGlowFactor(0f),.001f);
    assertEquals(1f,InfinityLiveActivity.CobraPlayingIndicatorPolicy.oledGlowFactor(1f),.001f);
  }

  @Test public void nightCinemaKeepsApprovedAmberAndSlowerQuieterPulse(){
    assertEquals(0xffffc247,InfinityLiveActivity.CobraPlayingIndicatorPolicy.CINEMA_AMBER);
    assertTrue(InfinityLiveActivity.CobraPlayingIndicatorPolicy.pulsePeriodMs(true)
        > InfinityLiveActivity.CobraPlayingIndicatorPolicy.pulsePeriodMs(false));
    assertTrue(InfinityLiveActivity.CobraPlayingIndicatorPolicy.glowAlpha(CobraPresentationEffects.IMMERSIVE,true)
        < InfinityLiveActivity.CobraPlayingIndicatorPolicy.glowAlpha(CobraPresentationEffects.IMMERSIVE,false));
  }

  @Test public void playbackTruthContractRemains2103236(){
    int none=Player.PLAYBACK_SUPPRESSION_REASON_NONE;
    assertTrue(InfinityLiveActivity.CobraPlayingIndicatorPolicy.active(true,true,none,Player.STATE_READY,false));
    assertTrue(InfinityLiveActivity.CobraPlayingIndicatorPolicy.active(true,true,none,Player.STATE_BUFFERING,false));
    assertFalse(InfinityLiveActivity.CobraPlayingIndicatorPolicy.active(false,true,none,Player.STATE_READY,false));
    assertFalse(InfinityLiveActivity.CobraPlayingIndicatorPolicy.active(true,false,none,Player.STATE_READY,false));
    assertFalse(InfinityLiveActivity.CobraPlayingIndicatorPolicy.active(true,true,1,Player.STATE_READY,false));
    assertFalse(InfinityLiveActivity.CobraPlayingIndicatorPolicy.active(true,true,none,Player.STATE_IDLE,false));
    assertFalse(InfinityLiveActivity.CobraPlayingIndicatorPolicy.active(true,true,none,Player.STATE_ENDED,false));
    assertFalse(InfinityLiveActivity.CobraPlayingIndicatorPolicy.active(true,true,none,Player.STATE_READY,true));
  }
}
