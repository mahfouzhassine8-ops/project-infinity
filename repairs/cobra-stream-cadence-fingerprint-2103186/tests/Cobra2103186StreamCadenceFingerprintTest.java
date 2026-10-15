package com.projectinfinity.kodi;

import android.app.Application;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE)
public class Cobra2103186StreamCadenceFingerprintTest {
  @Test public void cadenceBucketIsHalfSecond(){
    assertEquals(500L,InfinityLiveActivity.CobraStreamCadencePolicy.BUCKET_MS);
    assertEquals(0L,InfinityLiveActivity.CobraStreamCadencePolicy.bucket(0L));
    assertEquals(0L,InfinityLiveActivity.CobraStreamCadencePolicy.bucket(499L));
    assertEquals(1L,InfinityLiveActivity.CobraStreamCadencePolicy.bucket(500L));
  }

  @Test public void gapTiersAreExplicit(){
    assertEquals(0,InfinityLiveActivity.CobraStreamCadencePolicy.gapTier(499L));
    assertEquals(1,InfinityLiveActivity.CobraStreamCadencePolicy.gapTier(500L));
    assertEquals(2,InfinityLiveActivity.CobraStreamCadencePolicy.gapTier(1000L));
    assertEquals(3,InfinityLiveActivity.CobraStreamCadencePolicy.gapTier(2000L));
  }

  @Test public void severeGapThresholdIsTwoSeconds(){
    assertEquals(500L,InfinityLiveActivity.CobraStreamCadencePolicy.GAP_WARN_MS);
    assertEquals(1000L,InfinityLiveActivity.CobraStreamCadencePolicy.GAP_BAD_MS);
    assertEquals(2000L,InfinityLiveActivity.CobraStreamCadencePolicy.GAP_SEVERE_MS);
  }

  @Test public void priorNetworkModesRemainStable(){
    assertEquals("Automatic (IPv4 + IPv6)",InfinityLiveActivity.CobraNetworkFamilyPolicy.label(0));
    assertEquals("IPv4 only",InfinityLiveActivity.CobraNetworkFamilyPolicy.label(4));
    assertEquals("IPv6 only",InfinityLiveActivity.CobraNetworkFamilyPolicy.label(6));
  }

  @Test public void priorTimeshiftSafetyRemains(){
    assertEquals(15000L,InfinityLiveActivity.CobraTimeshiftTransportPolicy.LIVE_RESERVE_MS);
    assertEquals(21000L,InfinityLiveActivity.CobraTimeshiftTransportPolicy.STARTUP_RESERVE_MS);
    assertEquals(5000,InfinityLiveActivity.CobraTimeshiftTransportPolicy.READ_TIMEOUT_MS);
  }
}
