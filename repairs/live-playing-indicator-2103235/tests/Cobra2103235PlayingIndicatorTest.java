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
public class Cobra2103235PlayingIndicatorTest {
  @Test public void realLiveReadyAndBufferingSessionsOwnTheDot(){
    int none=Player.PLAYBACK_SUPPRESSION_REASON_NONE;
    assertTrue(InfinityLiveActivity.CobraPlayingIndicatorPolicy.active(true,true,none,Player.STATE_READY,false));
    assertTrue(InfinityLiveActivity.CobraPlayingIndicatorPolicy.active(true,true,none,Player.STATE_BUFFERING,false));
  }

  @Test public void focusCannotFakeAPlayingStateBecausePlaybackTruthIsRequired(){
    int none=Player.PLAYBACK_SUPPRESSION_REASON_NONE;
    assertFalse(InfinityLiveActivity.CobraPlayingIndicatorPolicy.active(false,true,none,Player.STATE_READY,false));
    assertFalse(InfinityLiveActivity.CobraPlayingIndicatorPolicy.active(true,false,none,Player.STATE_READY,false));
    assertFalse(InfinityLiveActivity.CobraPlayingIndicatorPolicy.active(true,true,1,Player.STATE_READY,false));
    assertFalse(InfinityLiveActivity.CobraPlayingIndicatorPolicy.active(true,true,none,Player.STATE_IDLE,false));
    assertFalse(InfinityLiveActivity.CobraPlayingIndicatorPolicy.active(true,true,none,Player.STATE_ENDED,false));
    assertFalse(InfinityLiveActivity.CobraPlayingIndicatorPolicy.active(true,true,none,Player.STATE_READY,true));
  }

  @Test public void ambientStrengthChangesGlowWithoutChangingPlaybackTruth(){
    int off=InfinityLiveActivity.CobraPlayingIndicatorPolicy.glowAlpha(CobraPresentationEffects.OFF,false);
    int subtle=InfinityLiveActivity.CobraPlayingIndicatorPolicy.glowAlpha(CobraPresentationEffects.SUBTLE,false);
    int immersive=InfinityLiveActivity.CobraPlayingIndicatorPolicy.glowAlpha(CobraPresentationEffects.IMMERSIVE,false);
    assertTrue(off<subtle);assertTrue(subtle<immersive);
  }

  @Test public void nightCinemaUsesQuieterSlowerPulse(){
    assertTrue(InfinityLiveActivity.CobraPlayingIndicatorPolicy.glowAlpha(CobraPresentationEffects.IMMERSIVE,true)
        < InfinityLiveActivity.CobraPlayingIndicatorPolicy.glowAlpha(CobraPresentationEffects.IMMERSIVE,false));
    assertTrue(InfinityLiveActivity.CobraPlayingIndicatorPolicy.pulsePeriodMs(true)
        > InfinityLiveActivity.CobraPlayingIndicatorPolicy.pulsePeriodMs(false));
  }
}
