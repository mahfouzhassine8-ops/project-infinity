package com.projectinfinity.kodi;

import android.app.Application;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE)
public class Cobra2103191ProviderRouteFingerprintTest {
  @Test public void routeFingerprintIsStableAndCompact(){
    String a=InfinityLiveActivity.CobraNetworkFamilyPolicy.routeFingerprint("203.0.113.10");
    String b=InfinityLiveActivity.CobraNetworkFamilyPolicy.routeFingerprint("203.0.113.10");
    assertEquals(a,b);
    assertEquals(16,a.length());
  }

  @Test public void differentEndpointsProduceDifferentFingerprints(){
    assertNotEquals(
      InfinityLiveActivity.CobraNetworkFamilyPolicy.routeFingerprint("203.0.113.10"),
      InfinityLiveActivity.CobraNetworkFamilyPolicy.routeFingerprint("198.51.100.20"));
  }

  @Test public void emptyInputsStayEmpty(){
    assertEquals("",InfinityLiveActivity.CobraNetworkFamilyPolicy.routeFingerprint(""));
    assertEquals("",InfinityLiveActivity.CobraNetworkFamilyPolicy.routeFingerprint(null));
  }

  @Test public void clockNormalizerContractIsPreserved(){
    assertTrue(InfinityLiveActivity.CobraTimelineNormalizerPolicy.eligible(
      228824L,7681L,1197L,559L,559L,559L));
    assertFalse(InfinityLiveActivity.CobraTimelineNormalizerPolicy.eligible(
      120000L,4000L,1000L,1000L,1000L,1000L));
  }

  @Test public void inheritedPlaybackSafetyRemains(){
    assertTrue(InfinityLiveActivity.CobraTsParserPolicy.detectsAccessUnits());
    assertTrue(InfinityLiveActivity.CobraTsParserPolicy.allowsNonIdrKeyframes());
    assertEquals(15000L,InfinityLiveActivity.CobraTimeshiftTransportPolicy.LIVE_RESERVE_MS);
    assertEquals(5000,InfinityLiveActivity.CobraTimeshiftTransportPolicy.READ_TIMEOUT_MS);
  }
}
