package com.projectinfinity.kodi;

import android.app.Application;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE)
public class Cobra2103179BufferResilienceTest {
  @Test public void localPlaylistStartsWithNineSecondReserve(){
    String p=InfinityLiveActivity.CobraTimeshiftTransportPolicy.playlistHeader(42);
    assertTrue(p.contains("#EXT-X-START:TIME-OFFSET=-9.0,PRECISE=NO\n"));
    assertFalse(p.contains("TIME-OFFSET=-6.0"));
  }

  @Test public void providerTimeoutsAreBoundedForLiveRecovery(){
    assertEquals(7000,InfinityLiveActivity.CobraTimeshiftTransportPolicy.CONNECT_TIMEOUT_MS);
    assertEquals(5000,InfinityLiveActivity.CobraTimeshiftTransportPolicy.READ_TIMEOUT_MS);
  }

  @Test public void reconnectBackoffRecoversQuicklyWithoutBusyLoop(){
    assertEquals(250L,InfinityLiveActivity.CobraTimeshiftTransportPolicy.INITIAL_BACKOFF_MS);
    assertEquals(500L,InfinityLiveActivity.CobraTimeshiftTransportPolicy.nextBackoffMs(250L));
    assertEquals(1000L,InfinityLiveActivity.CobraTimeshiftTransportPolicy.nextBackoffMs(500L));
    assertEquals(1500L,InfinityLiveActivity.CobraTimeshiftTransportPolicy.nextBackoffMs(1000L));
    assertEquals(1500L,InfinityLiveActivity.CobraTimeshiftTransportPolicy.nextBackoffMs(1500L));
  }

  @Test public void fixedLocalHttpFramingRemainsIntact(){
    String h=InfinityLiveActivity.CobraTimeshiftTransportPolicy.httpHeader("200 OK","video/mp2t",1880,false);
    assertTrue(InfinityLiveActivity.CobraTimeshiftTransportPolicy.hasRealHttpFraming(h));
    assertTrue(h.endsWith("\r\n\r\n"));
  }

  @Test public void rawTransportEligibilityForRewindIsUnchanged(){
    assertTrue(InfinityLiveActivity.CobraFinalFeaturePolicy.localTsEligible("https://tv.example/live/7.ts","ts"));
    assertTrue(InfinityLiveActivity.CobraFinalFeaturePolicy.localTsEligible("http://tv.example/live/7","ts"));
    assertFalse(InfinityLiveActivity.CobraFinalFeaturePolicy.localTsEligible("https://tv.example/live/7.m3u8","m3u8"));
  }

  @Test public void rewindWindowPolicyIsUnchanged(){
    assertEquals(60,InfinityLiveActivity.CobraFinalFeaturePolicy.timeshiftSeconds(60));
    assertEquals(120,InfinityLiveActivity.CobraFinalFeaturePolicy.timeshiftSeconds(120));
    assertEquals(180,InfinityLiveActivity.CobraFinalFeaturePolicy.timeshiftSeconds(180));
  }

  @Test public void approved120HzPolicyStillWorks(){
    assertEquals(120f,InfinityLiveActivity.CobraRefreshPolicy.choose("120",new float[]{60f,90f,120f},false,false),.01f);
    assertTrue(InfinityLiveActivity.CobraRefreshPolicy.requestedExactly("120",120f));
  }

  @Test public void multitaskResizeStopPreservesPlayback(){
    assertTrue(InfinityLiveActivity.CobraWindowLifecyclePolicy.preservePlaybackOnStop(true,false));
    assertFalse(InfinityLiveActivity.CobraWindowLifecyclePolicy.preservePlaybackOnStop(true,true));
    assertFalse(InfinityLiveActivity.CobraWindowLifecyclePolicy.preservePlaybackOnStop(false,false));
  }

  @Test public void localTimeshiftSourceIoErrorsAreRecoverable(){
    assertTrue(InfinityLiveActivity.CobraTimeshiftRecoveryPolicy.recoverable(new java.io.IOException("provider hiccup")));
    assertFalse(InfinityLiveActivity.CobraTimeshiftRecoveryPolicy.recoverable(new IllegalArgumentException("not source io")));
  }

  @Test public void localTimeshiftRecoveryWaitIsBounded(){
    assertEquals(12000L,InfinityLiveActivity.CobraTimeshiftRecoveryPolicy.ADVANCE_WAIT_MS);
  }

  @Test public void automaticLiveEdgeRecoveryIsBudgetedLikePassedPlaybackAudit(){
    assertEquals(6000L,InfinityLiveActivity.CobraTimeshiftStallPolicy.STALL_TRIGGER_MS);
    assertEquals(60000L,InfinityLiveActivity.CobraTimeshiftStallPolicy.RECOVERY_COOLDOWN_MS);
    assertEquals(2,InfinityLiveActivity.CobraTimeshiftStallPolicy.MAX_AUTO_LIVE_EDGE_ATTEMPTS);
    assertEquals(3,InfinityLiveActivity.CobraTimeshiftStallPolicy.BURST_COUNT);
    assertEquals(12000L,InfinityLiveActivity.CobraTimeshiftStallPolicy.BURST_WINDOW_MS);
    assertTrue(InfinityLiveActivity.CobraTimeshiftStallPolicy.canAutoRecover(0,0L,1000L));
    assertFalse(InfinityLiveActivity.CobraTimeshiftStallPolicy.canAutoRecover(2,0L,100000L));
    assertFalse(InfinityLiveActivity.CobraTimeshiftStallPolicy.canAutoRecover(1,1000L,60999L));
    assertTrue(InfinityLiveActivity.CobraTimeshiftStallPolicy.canAutoRecover(1,1000L,61000L));
  }
}
