package com.projectinfinity.kodi;

import android.app.Application;
import android.media.AudioManager;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE)
public class Cobra2103180PlaybackFinalizationTest {
  @Test public void localTimeshiftUsesFifteenSecondReserve(){
    assertEquals(15000L,InfinityLiveActivity.CobraTimeshiftTransportPolicy.LIVE_RESERVE_MS);
    String p=InfinityLiveActivity.CobraTimeshiftTransportPolicy.playlistHeader(42);
    assertTrue(p.contains("#EXT-X-START:TIME-OFFSET=-15.0,PRECISE=NO\n"));
  }

  @Test public void providerReadTimeoutNoLongerChurnsAtFiveSeconds(){
    assertEquals(15000,InfinityLiveActivity.CobraTimeshiftTransportPolicy.READ_TIMEOUT_MS);
    assertEquals(7000,InfinityLiveActivity.CobraTimeshiftTransportPolicy.CONNECT_TIMEOUT_MS);
  }

  @Test public void transientCallFocusLossPreservesVideo(){
    assertTrue(InfinityLiveActivity.CobraCallAudioPolicy.preserveVideo(AudioManager.AUDIOFOCUS_LOSS_TRANSIENT));
    assertTrue(InfinityLiveActivity.CobraCallAudioPolicy.muteForFocus(AudioManager.AUDIOFOCUS_LOSS_TRANSIENT_CAN_DUCK));
  }

  @Test public void permanentFocusLossAlsoMutesWithoutDefiningPausePolicy(){
    assertTrue(InfinityLiveActivity.CobraCallAudioPolicy.preserveVideo(AudioManager.AUDIOFOCUS_LOSS));
    assertFalse(InfinityLiveActivity.CobraCallAudioPolicy.preserveVideo(AudioManager.AUDIOFOCUS_GAIN));
  }

  @Test public void proAlignedRecoveryBudgetRemainsBounded(){
    assertEquals(2,InfinityLiveActivity.CobraTimeshiftStallPolicy.MAX_AUTO_LIVE_EDGE_ATTEMPTS);
    assertEquals(60000L,InfinityLiveActivity.CobraTimeshiftStallPolicy.RECOVERY_COOLDOWN_MS);
  }

  @Test public void rewindAnd120HzContractsRemainIntact(){
    assertEquals(120,InfinityLiveActivity.CobraFinalFeaturePolicy.timeshiftSeconds(120));
    assertEquals(120f,InfinityLiveActivity.CobraRefreshPolicy.choose("120",new float[]{60f,90f,120f},false,false),.01f);
  }
}
