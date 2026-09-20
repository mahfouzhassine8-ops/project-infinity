package com.projectinfinity.kodi;

import android.app.Application;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE)
public class Cobra2103187TsAccessUnitCompatibilityTest {
  @Test public void detectsAccessUnitsForTs(){
    assertTrue(InfinityLiveActivity.CobraTsParserPolicy.detectsAccessUnits());
  }

  @Test public void keepsNonIdrKeyframesDisabled(){
    assertFalse(InfinityLiveActivity.CobraTsParserPolicy.allowsNonIdrKeyframes());
  }

  @Test public void exactFlagIsNarrow(){
    assertEquals(androidx.media3.extractor.ts.DefaultTsPayloadReaderFactory.FLAG_DETECT_ACCESS_UNITS,
        InfinityLiveActivity.CobraTsParserPolicy.TS_FLAGS);
  }

  @Test public void networkModesRemainStable(){
    assertEquals("Automatic (IPv4 + IPv6)",InfinityLiveActivity.CobraNetworkFamilyPolicy.label(0));
    assertEquals("IPv4 only",InfinityLiveActivity.CobraNetworkFamilyPolicy.label(4));
    assertEquals("IPv6 only",InfinityLiveActivity.CobraNetworkFamilyPolicy.label(6));
  }

  @Test public void timeshiftSafetyRemainsStable(){
    assertEquals(15000L,InfinityLiveActivity.CobraTimeshiftTransportPolicy.LIVE_RESERVE_MS);
    assertEquals(21000L,InfinityLiveActivity.CobraTimeshiftTransportPolicy.STARTUP_RESERVE_MS);
    assertEquals(5000,InfinityLiveActivity.CobraTimeshiftTransportPolicy.READ_TIMEOUT_MS);
  }
}
