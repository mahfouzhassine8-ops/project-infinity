package com.projectinfinity.kodi;

import android.app.Application;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE)
public class Cobra2103177FinalFeatureFreezeTest {
  @Test public void autoChoosesHighestSupportedRefresh(){
    assertEquals(120f,InfinityLiveActivity.CobraRefreshPolicy.choose("auto",new float[]{60f,90f,120f},false,false),.01f);
  }

  @Test public void explicit120Chooses120WhenSupported(){
    assertEquals(120f,InfinityLiveActivity.CobraRefreshPolicy.choose("120",new float[]{60f,90f,120f},false,false),.01f);
  }

  @Test public void unsupported90FallsBackWithoutInventingMode(){
    assertEquals(60f,InfinityLiveActivity.CobraRefreshPolicy.choose("90",new float[]{60f,120f},false,false),.01f);
    assertFalse(InfinityLiveActivity.CobraRefreshPolicy.requestedExactly("90",60f));
  }

  @Test public void batterySaverCapsHighRefresh(){
    assertEquals(60f,InfinityLiveActivity.CobraRefreshPolicy.choose("120",new float[]{60f,90f,120f},true,false),.01f);
  }

  @Test public void severeThermalCapsHighRefresh(){
    assertEquals(60f,InfinityLiveActivity.CobraRefreshPolicy.choose("max",new float[]{60f,120f},false,true),.01f);
  }

  @Test public void maxUsesDisplayMaximum(){
    assertEquals(144f,InfinityLiveActivity.CobraRefreshPolicy.choose("max",new float[]{60f,120f,144f},false,false),.01f);
  }

  @Test public void timeshiftWindowsAreStrictlyBounded(){
    assertEquals(60,InfinityLiveActivity.CobraFinalFeaturePolicy.timeshiftSeconds(5));
    assertEquals(60,InfinityLiveActivity.CobraFinalFeaturePolicy.timeshiftSeconds(60));
    assertEquals(120,InfinityLiveActivity.CobraFinalFeaturePolicy.timeshiftSeconds(61));
    assertEquals(180,InfinityLiveActivity.CobraFinalFeaturePolicy.timeshiftSeconds(180));
    assertEquals(180,InfinityLiveActivity.CobraFinalFeaturePolicy.timeshiftSeconds(999));
  }

  @Test public void localTimeshiftAcceptsOnlyRawHttpTs(){
    assertTrue(InfinityLiveActivity.CobraFinalFeaturePolicy.localTsEligible("https://tv.example/live/1.ts","ts"));
    assertTrue(InfinityLiveActivity.CobraFinalFeaturePolicy.localTsEligible("http://tv.example/live/1","ts"));
    assertFalse(InfinityLiveActivity.CobraFinalFeaturePolicy.localTsEligible("https://tv.example/live/1.m3u8","m3u8"));
    assertFalse(InfinityLiveActivity.CobraFinalFeaturePolicy.localTsEligible("rtsp://tv.example/1","ts"));
  }

  @Test public void throughputEstimateIsDeterministic(){
    assertEquals(8000L,InfinityLiveActivity.CobraFinalFeaturePolicy.throughputKbps(1_000_000L,1000L));
    assertEquals(-1L,InfinityLiveActivity.CobraFinalFeaturePolicy.throughputKbps(0L,1000L));
    assertEquals(-1L,InfinityLiveActivity.CobraFinalFeaturePolicy.throughputKbps(1000L,0L));
  }

  @Test public void requestedExactlyDistinguishesFallback(){
    assertTrue(InfinityLiveActivity.CobraRefreshPolicy.requestedExactly("120",120f));
    assertFalse(InfinityLiveActivity.CobraRefreshPolicy.requestedExactly("120",60f));
    assertTrue(InfinityLiveActivity.CobraRefreshPolicy.requestedExactly("auto",90f));
    assertTrue(InfinityLiveActivity.CobraRefreshPolicy.requestedExactly("max",120f));
  }
}
