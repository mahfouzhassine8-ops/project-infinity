package com.projectinfinity.kodi;

import android.app.Application;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE)
public class Cobra2103181TimeshiftTransportIntegrityTest {
  @Test public void publishedDurationDoesNotCountNetworkIdle(){
    assertEquals(2900L,InfinityLiveActivity.CobraTimeshiftTransportPolicy.publishedSegmentDurationMs(1000L,3900L));
    assertEquals(4500L,InfinityLiveActivity.CobraTimeshiftTransportPolicy.publishedSegmentDurationMs(1000L,9000L));
    assertEquals(250L,InfinityLiveActivity.CobraTimeshiftTransportPolicy.publishedSegmentDurationMs(0L,9000L));
  }

  @Test public void targetDurationCannotBeExceededByPublishedDuration(){
    assertEquals(3000L,InfinityLiveActivity.CobraTimeshiftTransportPolicy.SEGMENT_TARGET_MS);
    assertTrue(InfinityLiveActivity.CobraTimeshiftTransportPolicy.MAX_PUBLISHED_SEGMENT_MS <= 5000L);
  }

  @Test public void oldPlaylistSegmentsGetLongRetentionGrace(){
    assertEquals(84,InfinityLiveActivity.CobraTimeshiftTransportPolicy.retainedSegmentCount(40));
    assertTrue(InfinityLiveActivity.CobraTimeshiftTransportPolicy.retainedSegmentCount(40) >= 80);
  }

  @Test public void livePlaylistCarriesStableDiscontinuitySequence(){
    String p=InfinityLiveActivity.CobraTimeshiftTransportPolicy.playlistHeader(42L,7L);
    assertTrue(p.contains("#EXT-X-MEDIA-SEQUENCE:42\n"));
    assertTrue(p.contains("#EXT-X-DISCONTINUITY-SEQUENCE:7\n"));
    assertTrue(p.contains("#EXT-X-START:TIME-OFFSET=-15.0,PRECISE=NO\n"));
  }

  @Test public void providerReadTimeoutAgainLeavesReserveForReconnect(){
    assertEquals(5000,InfinityLiveActivity.CobraTimeshiftTransportPolicy.READ_TIMEOUT_MS);
    assertEquals(15000L,InfinityLiveActivity.CobraTimeshiftTransportPolicy.LIVE_RESERVE_MS);
    assertTrue(InfinityLiveActivity.CobraTimeshiftTransportPolicy.READ_TIMEOUT_MS < InfinityLiveActivity.CobraTimeshiftTransportPolicy.LIVE_RESERVE_MS);
  }

  @Test public void priorPlaybackContractsRemainBounded(){
    assertEquals(2,InfinityLiveActivity.CobraTimeshiftStallPolicy.MAX_AUTO_LIVE_EDGE_ATTEMPTS);
    assertEquals(60000L,InfinityLiveActivity.CobraTimeshiftStallPolicy.RECOVERY_COOLDOWN_MS);
    assertTrue(InfinityLiveActivity.CobraCallAudioPolicy.preserveVideo(android.media.AudioManager.AUDIOFOCUS_LOSS_TRANSIENT));
  }
}
