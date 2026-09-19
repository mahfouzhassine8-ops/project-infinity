package com.projectinfinity.kodi;

import android.app.Application;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE)
public class Cobra2103182TimeshiftStartupReserveTest {
  @Test public void startupReserveExceedsLiveTargetBySafetyMargin(){
    assertEquals(15000L,InfinityLiveActivity.CobraTimeshiftTransportPolicy.LIVE_RESERVE_MS);
    assertEquals(21000L,InfinityLiveActivity.CobraTimeshiftTransportPolicy.STARTUP_RESERVE_MS);
    assertTrue(InfinityLiveActivity.CobraTimeshiftTransportPolicy.STARTUP_RESERVE_MS >
        InfinityLiveActivity.CobraTimeshiftTransportPolicy.LIVE_RESERVE_MS);
  }

  @Test public void nineSecondWindowIsNoLongerReady(){
    assertFalse(InfinityLiveActivity.CobraTimeshiftTransportPolicy.startupReady(9000L));
    assertFalse(InfinityLiveActivity.CobraTimeshiftTransportPolicy.startupReady(15000L));
  }

  @Test public void twentyOneSecondWindowIsReady(){
    assertFalse(InfinityLiveActivity.CobraTimeshiftTransportPolicy.startupReady(20999L));
    assertTrue(InfinityLiveActivity.CobraTimeshiftTransportPolicy.startupReady(21000L));
  }

  @Test public void startupWaitAllowsReserveToActuallyBuild(){
    assertEquals(32000L,InfinityLiveActivity.CobraTimeshiftTransportPolicy.STARTUP_WAIT_MS);
    assertTrue(InfinityLiveActivity.CobraTimeshiftTransportPolicy.STARTUP_WAIT_MS >
        InfinityLiveActivity.CobraTimeshiftTransportPolicy.STARTUP_RESERVE_MS);
  }

  @Test public void providerReconnectStillUsesFiveSecondReadTimeout(){
    assertEquals(5000,InfinityLiveActivity.CobraTimeshiftTransportPolicy.READ_TIMEOUT_MS);
  }

  @Test public void priorRecoveryAndCallContractsRemain(){
    assertEquals(2,InfinityLiveActivity.CobraTimeshiftStallPolicy.MAX_AUTO_LIVE_EDGE_ATTEMPTS);
    assertEquals(60000L,InfinityLiveActivity.CobraTimeshiftStallPolicy.RECOVERY_COOLDOWN_MS);
    assertTrue(InfinityLiveActivity.CobraCallAudioPolicy.preserveVideo(android.media.AudioManager.AUDIOFOCUS_LOSS_TRANSIENT));
  }
}
