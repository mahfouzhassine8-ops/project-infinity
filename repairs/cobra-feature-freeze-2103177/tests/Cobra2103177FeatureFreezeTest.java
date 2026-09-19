package com.projectinfinity.kodi;

import android.app.Application;
import java.util.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE)
public class Cobra2103177FeatureFreezeTest {
  @Test public void explicit120Requests120WhenSupported(){
    assertEquals(120f,InfinityLiveActivity.CobraDisplayPolicy.requested("120",120f,false,false,false),.01f);
  }
  @Test public void autoCapsInterfaceAt120(){
    assertEquals(120f,InfinityLiveActivity.CobraDisplayPolicy.requested("auto",144f,false,false,false),.01f);
    assertEquals(90f,InfinityLiveActivity.CobraDisplayPolicy.requested("auto",90f,false,false,false),.01f);
  }
  @Test public void maxCanUse144(){
    assertEquals(144f,InfinityLiveActivity.CobraDisplayPolicy.requested("max",144f,false,false,false),.01f);
  }
  @Test public void fullscreenVideoYieldsRefreshOwnership(){
    assertEquals(0f,InfinityLiveActivity.CobraDisplayPolicy.requested("120",120f,false,false,true),.01f);
  }
  @Test public void batteryAndThermalProtectionCapAt60(){
    assertEquals(60f,InfinityLiveActivity.CobraDisplayPolicy.requested("120",120f,true,false,false),.01f);
    assertEquals(60f,InfinityLiveActivity.CobraDisplayPolicy.requested("120",120f,false,true,false),.01f);
  }
  @Test public void supportedModeSelectionUsesHighestAtOrBelowTarget(){
    float[] modes={60f,90f,120f,144f};
    assertEquals(120f,InfinityLiveActivity.CobraDisplayPolicy.choose(modes,120f),.01f);
    assertEquals(90f,InfinityLiveActivity.CobraDisplayPolicy.choose(modes,100f),.01f);
  }
  @Test public void activeAndFallbackStatusAreMeasurable(){
    assertEquals("ACTIVE",InfinityLiveActivity.CobraDisplayPolicy.status(120f,120f));
    assertEquals("FALLBACK",InfinityLiveActivity.CobraDisplayPolicy.status(120f,60f));
    assertEquals("VIDEO MATCH",InfinityLiveActivity.CobraDisplayPolicy.status(0f,60f));
  }
  @Test public void smartBufferModesAreBounded(){
    assertEquals("auto",InfinityLiveActivity.CobraBufferPolicy.mode("anything"));
    assertEquals("resilient",InfinityLiveActivity.CobraBufferPolicy.mode("resilient"));
    assertEquals(50000,InfinityLiveActivity.CobraBufferPolicy.minMs("auto"));
    assertEquals(50000,InfinityLiveActivity.CobraBufferPolicy.maxMs("auto"));
    assertEquals(5000,InfinityLiveActivity.CobraBufferPolicy.rebufferMs("auto"));
    assertEquals(20000,InfinityLiveActivity.CobraBufferPolicy.minMs("resilient"));
    assertEquals(90000,InfinityLiveActivity.CobraBufferPolicy.maxMs("resilient"));
    assertEquals(8000,InfinityLiveActivity.CobraBufferPolicy.rebufferMs("resilient"));
  }
  @Test public void localTimeshiftLimitsAreExplicit(){
    assertEquals(120000L,InfinityLiveActivity.CobraTimeshiftPolicy.WINDOW_MS);
    assertEquals(160L*1024L*1024L,InfinityLiveActivity.CobraTimeshiftPolicy.CACHE_CAP_BYTES);
    assertEquals(150L*1024L*1024L,InfinityLiveActivity.CobraTimeshiftPolicy.CACHE_TRIM_BYTES);
  }
  @Test public void localTimeshiftOnlyExtendsSimpleHls(){
    String simple="#EXTM3U\n#EXT-X-TARGETDURATION:6\n#EXTINF:6.0,\na.ts\n";
    assertTrue(InfinityLiveActivity.CobraTimeshiftPolicy.extendable(simple));
    for(String forbidden:new String[]{"#EXT-X-KEY","#EXT-X-BYTERANGE","#EXT-X-PART","#EXT-X-MAP","#EXT-X-DISCONTINUITY","#EXT-X-ENDLIST"})
      assertFalse(forbidden,InfinityLiveActivity.CobraTimeshiftPolicy.extendable(simple+forbidden+"\n"));
  }
  @Test public void lastChannelSkipsCurrentAndUsesMostRecentOtherChannel(){
    assertEquals("b",InfinityLiveActivity.CobraLastChannelPolicy.choose("a",Arrays.asList("a","b","c")));
    assertEquals("a",InfinityLiveActivity.CobraLastChannelPolicy.choose("b",Arrays.asList("b","a","c")));
    assertEquals("",InfinityLiveActivity.CobraLastChannelPolicy.choose("a",Arrays.asList("a","a")));
  }
  @Test public void featureDefaultsRemainOptInAtPolicyLevel(){
    assertEquals("auto",InfinityLiveActivity.CobraBufferPolicy.mode(null));
    assertEquals(120f,InfinityLiveActivity.CobraDisplayPolicy.requested("auto",120f,false,false,false),.01f);
  }
}
