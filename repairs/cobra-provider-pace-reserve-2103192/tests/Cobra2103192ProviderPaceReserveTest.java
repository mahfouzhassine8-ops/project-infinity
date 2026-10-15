package com.projectinfinity.kodi;

import android.app.Application;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE)
public class Cobra2103192ProviderPaceReserveTest {
  @Test public void steadyCleanUnderrateIsClassifiedAsPaceLimit(){
    assertTrue(InfinityLiveActivity.CobraProviderPacePolicy.limited(
      30000L,900L,180L,560L,560L,560L,10L,500L,0L,0L,0L));
  }

  @Test public void normalRateIsNotClassifiedAsPaceLimit(){
    assertFalse(InfinityLiveActivity.CobraProviderPacePolicy.limited(
      30000L,900L,180L,1000L,1000L,1000L,10L,500L,0L,0L,0L));
  }

  @Test public void trueNetworkGapsAreNotMisclassified(){
    assertFalse(InfinityLiveActivity.CobraProviderPacePolicy.limited(
      30000L,900L,180L,560L,560L,560L,20L,17000L,40L,0L,0L));
  }

  @Test public void disprovenTimelineRewriteIsDisabled(){
    assertFalse(InfinityLiveActivity.CobraTimelineNormalizerPolicy.REWRITE_ENABLED);
    assertTrue(InfinityLiveActivity.CobraTimelineNormalizerPolicy.eligible(
      228824L,7681L,1197L,559L,559L,559L));
  }

  @Test public void inheritedPlaybackSafetyRemains(){
    assertTrue(InfinityLiveActivity.CobraTsParserPolicy.detectsAccessUnits());
    assertTrue(InfinityLiveActivity.CobraTsParserPolicy.allowsNonIdrKeyframes());
    assertEquals(15000L,InfinityLiveActivity.CobraTimeshiftTransportPolicy.LIVE_RESERVE_MS);
    assertEquals(5000,InfinityLiveActivity.CobraTimeshiftTransportPolicy.READ_TIMEOUT_MS);
  }
}
