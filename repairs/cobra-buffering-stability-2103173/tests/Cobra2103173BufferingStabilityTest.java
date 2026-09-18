package com.projectinfinity.kodi;

import android.app.Application;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Deterministic buffer-policy gates. Session-reuse/no-reprepare behavior is also
 * source-audited because Robolectric cannot emulate a real IPTV socket stall. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE)
public class Cobra2103173BufferingStabilityTest {
  @Test public void singleViewBuildsMoreResilientHeadroom(){
    assertEquals(15000,InfinityLiveActivity.CobraBufferingPolicy.minBufferMs(false));
    assertEquals(60000,InfinityLiveActivity.CobraBufferingPolicy.maxBufferMs(false));
    assertEquals(1500,InfinityLiveActivity.CobraBufferingPolicy.playbackMs(false));
    assertEquals(5000,InfinityLiveActivity.CobraBufferingPolicy.rebufferMs(false));
  }

  @Test public void singleViewUsesLargerByteTargetAndTimePriority(){
    assertEquals(48*1024*1024,InfinityLiveActivity.CobraBufferingPolicy.targetBufferBytes(false));
    assertTrue(InfinityLiveActivity.CobraBufferingPolicy.prioritizeTime(false));
  }

  @Test public void multiViewKeepsConservativeExistingProfile(){
    assertEquals(6000,InfinityLiveActivity.CobraBufferingPolicy.minBufferMs(true));
    assertEquals(30000,InfinityLiveActivity.CobraBufferingPolicy.maxBufferMs(true));
    assertEquals(1500,InfinityLiveActivity.CobraBufferingPolicy.playbackMs(true));
    assertEquals(3000,InfinityLiveActivity.CobraBufferingPolicy.rebufferMs(true));
    assertEquals(12*1024*1024,InfinityLiveActivity.CobraBufferingPolicy.targetBufferBytes(true));
    assertFalse(InfinityLiveActivity.CobraBufferingPolicy.prioritizeTime(true));
  }

  @Test public void stallReportingDoesNotFireBeforeExistingTwelveSecondBoundary(){
    assertEquals(12000L,InfinityLiveActivity.CobraBufferingPolicy.stallReportMs());
  }
}
