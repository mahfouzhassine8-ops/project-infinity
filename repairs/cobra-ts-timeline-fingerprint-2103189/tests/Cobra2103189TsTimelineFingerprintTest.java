package com.projectinfinity.kodi;

import android.app.Application;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE)
public class Cobra2103189TsTimelineFingerprintTest {
  @Test public void ptsWrapMathIsStable(){
    long mod=InfinityLiveActivity.CobraTsTimelinePolicy.PTS_MOD;
    assertEquals(15L,InfinityLiveActivity.CobraTsTimelinePolicy.forwardDiff90k(10L,mod-5L));
  }

  @Test public void signedDiffSeesSmallBackwardMove(){
    assertEquals(-90L,InfinityLiveActivity.CobraTsTimelinePolicy.signedDiff90k(910L,1000L));
    assertEquals(90L,InfinityLiveActivity.CobraTsTimelinePolicy.signedDiff90k(1090L,1000L));
  }

  @Test public void intraSliceTypesAreRecognized(){
    assertTrue(InfinityLiveActivity.CobraTsTimelinePolicy.intraSliceType(2));
    assertTrue(InfinityLiveActivity.CobraTsTimelinePolicy.intraSliceType(7));
    assertFalse(InfinityLiveActivity.CobraTsTimelinePolicy.intraSliceType(0));
    assertFalse(InfinityLiveActivity.CobraTsTimelinePolicy.intraSliceType(1));
  }

  @Test public void oneToOneClockRateIsOneThousandPermille(){
    assertEquals(1000L,InfinityLiveActivity.CobraTsTimelinePolicy.ratePermille(0L,900000L,1000L,11000L));
  }

  @Test public void priorPlaybackSafetyRemains(){
    assertTrue(InfinityLiveActivity.CobraTsParserPolicy.detectsAccessUnits());
    assertTrue(InfinityLiveActivity.CobraTsParserPolicy.allowsNonIdrKeyframes());
    assertEquals(15000L,InfinityLiveActivity.CobraTimeshiftTransportPolicy.LIVE_RESERVE_MS);
    assertEquals(5000,InfinityLiveActivity.CobraTimeshiftTransportPolicy.READ_TIMEOUT_MS);
  }
}
