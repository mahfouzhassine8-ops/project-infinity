package com.projectinfinity.kodi;

import android.app.Application;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE)
public class Cobra2103190TsClockNormalizationTest {
  @Test public void problemNicktoonsClockRateQualifies(){
    assertTrue(InfinityLiveActivity.CobraTimelineNormalizerPolicy.eligible(
      228824L,7681L,1197L,559L,559L,559L));
  }

  @Test public void normalClockDoesNotQualify(){
    assertFalse(InfinityLiveActivity.CobraTimelineNormalizerPolicy.eligible(
      120000L,4000L,1000L,1000L,1000L,1000L));
  }

  @Test public void mismatchedTracksDoNotQualify(){
    assertFalse(InfinityLiveActivity.CobraTimelineNormalizerPolicy.eligible(
      120000L,4000L,1000L,559L,700L,559L));
  }

  @Test public void scaleCorrectsFiveFiftyNinePermille(){
    long ppm=InfinityLiveActivity.CobraTimelineNormalizerPolicy.scalePpm(559L);
    assertTrue(ppm>=1788000L&&ppm<=1790000L);
    long normalized=InfinityLiveActivity.CobraTimelineNormalizerPolicy.scaleDelta90k(55900L,ppm);
    assertTrue(normalized>=99900L&&normalized<=100100L);
  }

  @Test public void priorPlaybackSafetyRemains(){
    assertTrue(InfinityLiveActivity.CobraTsParserPolicy.detectsAccessUnits());
    assertTrue(InfinityLiveActivity.CobraTsParserPolicy.allowsNonIdrKeyframes());
    assertEquals(15000L,InfinityLiveActivity.CobraTimeshiftTransportPolicy.LIVE_RESERVE_MS);
    assertEquals(5000,InfinityLiveActivity.CobraTimeshiftTransportPolicy.READ_TIMEOUT_MS);
  }
}
