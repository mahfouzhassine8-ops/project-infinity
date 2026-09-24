package com.projectinfinity.kodi;

import android.app.Application;
import androidx.media3.common.Player;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE)
public class Cobra2103236AllViewsPlayingIndicatorTest {
  @Test public void cinemaUsesApprovedWarmAmber(){
    assertEquals(0xffffc247,InfinityLiveActivity.CobraPlayingIndicatorPolicy.CINEMA_AMBER);
    int color=InfinityLiveActivity.CobraPlayingIndicatorPolicy.CINEMA_AMBER;
    assertTrue(android.graphics.Color.red(color)>240);
    assertTrue(android.graphics.Color.green(color)>170);
    assertTrue(android.graphics.Color.blue(color)<100);
  }

  @Test public void cinemaKeepsQuieterSlowerPulse(){
    assertTrue(InfinityLiveActivity.CobraPlayingIndicatorPolicy.pulsePeriodMs(true)
        > InfinityLiveActivity.CobraPlayingIndicatorPolicy.pulsePeriodMs(false));
    assertTrue(InfinityLiveActivity.CobraPlayingIndicatorPolicy.glowAlpha(CobraPresentationEffects.IMMERSIVE,true)
        < InfinityLiveActivity.CobraPlayingIndicatorPolicy.glowAlpha(CobraPresentationEffects.IMMERSIVE,false));
  }

  @Test public void ambientStrengthContractFrom2103235IsPreserved(){
    int off=InfinityLiveActivity.CobraPlayingIndicatorPolicy.glowAlpha(CobraPresentationEffects.OFF,false);
    int subtle=InfinityLiveActivity.CobraPlayingIndicatorPolicy.glowAlpha(CobraPresentationEffects.SUBTLE,false);
    int immersive=InfinityLiveActivity.CobraPlayingIndicatorPolicy.glowAlpha(CobraPresentationEffects.IMMERSIVE,false);
    assertTrue(off<subtle);
    assertTrue(subtle<immersive);
  }

  @Test public void playbackTruthContractFrom2103235IsPreserved(){
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
