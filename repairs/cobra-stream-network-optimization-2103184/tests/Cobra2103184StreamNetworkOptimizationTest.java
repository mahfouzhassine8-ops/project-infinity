package com.projectinfinity.kodi;

import android.app.Application;
import java.net.*;
import java.util.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE)
public class Cobra2103184StreamNetworkOptimizationTest {
  @Test public void manualIpv4AndIpv6FilteringRemainStrict() throws Exception {
    InetAddress v4=InetAddress.getByAddress(new byte[]{(byte)192,0,2,10});
    byte[] b=new byte[16];b[0]=0x20;b[1]=0x01;b[2]=0x0d;b[3]=(byte)0xb8;b[15]=1;
    InetAddress v6=InetAddress.getByAddress(b);
    InetAddress[] all={v6,v4};
    assertEquals(1,InfinityLiveActivity.CobraNetworkFamilyPolicy.filter(all,InfinityLiveActivity.CobraNetworkFamilyPolicy.IPV4).size());
    assertTrue(InfinityLiveActivity.CobraNetworkFamilyPolicy.filter(all,InfinityLiveActivity.CobraNetworkFamilyPolicy.IPV4).get(0) instanceof Inet4Address);
    assertTrue(InfinityLiveActivity.CobraNetworkFamilyPolicy.filter(all,InfinityLiveActivity.CobraNetworkFamilyPolicy.IPV6).get(0) instanceof Inet6Address);
    assertEquals(InfinityLiveActivity.CobraNetworkFamilyPolicy.IPV4,InfinityLiveActivity.CobraNetworkFamilyPolicy.literalFamily("192.0.2.44"));
    assertEquals(InfinityLiveActivity.CobraNetworkFamilyPolicy.IPV6,InfinityLiveActivity.CobraNetworkFamilyPolicy.literalFamily("2001:db8::44"));
    assertEquals(InfinityLiveActivity.CobraNetworkFamilyPolicy.AUTO,InfinityLiveActivity.CobraNetworkFamilyPolicy.literalFamily("provider.example"));
  }

  @Test public void happyEyeballsUsesStandardSmallStaggerAndMemory(){
    assertEquals(250L,InfinityLiveActivity.CobraNetworkFamilyPolicy.HAPPY_DELAY_MS);
    assertEquals(300000L,InfinityLiveActivity.CobraNetworkFamilyPolicy.HAPPY_MEMORY_MS);
    assertEquals(1800,InfinityLiveActivity.CobraNetworkFamilyPolicy.HAPPY_PROBE_TIMEOUT_MS);
  }

  @Test public void successfulFamilyIsRememberedAndFailureExpiresPreference(){
    String key="unit.example:443";
    InfinityLiveActivity.CobraNetworkFamilyPolicy.recordSuccess(key,InfinityLiveActivity.CobraNetworkFamilyPolicy.IPV4);
    assertEquals(InfinityLiveActivity.CobraNetworkFamilyPolicy.IPV4,InfinityLiveActivity.CobraNetworkFamilyPolicy.rememberedFamily(key));
    InfinityLiveActivity.CobraNetworkFamilyPolicy.recordFailure(key,InfinityLiveActivity.CobraNetworkFamilyPolicy.IPV4);
    assertEquals(InfinityLiveActivity.CobraNetworkFamilyPolicy.AUTO,InfinityLiveActivity.CobraNetworkFamilyPolicy.rememberedFamily(key));
  }

  @Test public void localTimeshiftLoopbackIsNeverBlockedByForcedFamily(){
    assertTrue(InfinityLiveActivity.CobraNetworkFamilyPolicy.loopbackHost("127.0.0.1"));
    assertTrue(InfinityLiveActivity.CobraNetworkFamilyPolicy.loopbackHost("::1"));
    assertFalse(InfinityLiveActivity.CobraNetworkFamilyPolicy.loopbackHost("provider.example"));
  }

  @Test public void automaticAndManualLabelsRemainStable(){
    assertEquals("Automatic (IPv4 + IPv6)",InfinityLiveActivity.CobraNetworkFamilyPolicy.label(0));
    assertEquals("IPv4 only",InfinityLiveActivity.CobraNetworkFamilyPolicy.label(4));
    assertEquals("IPv6 only",InfinityLiveActivity.CobraNetworkFamilyPolicy.label(6));
  }

  @Test public void existingTimeshiftSafetyWindowIsPreserved(){
    assertEquals(15000L,InfinityLiveActivity.CobraTimeshiftTransportPolicy.LIVE_RESERVE_MS);
    assertEquals(21000L,InfinityLiveActivity.CobraTimeshiftTransportPolicy.STARTUP_RESERVE_MS);
    assertEquals(5000,InfinityLiveActivity.CobraTimeshiftTransportPolicy.READ_TIMEOUT_MS);
  }

  @Test public void proRecoveryBudgetAndCallContinuityRemain(){
    assertEquals(2,InfinityLiveActivity.CobraTimeshiftStallPolicy.MAX_AUTO_LIVE_EDGE_ATTEMPTS);
    assertEquals(60000L,InfinityLiveActivity.CobraTimeshiftStallPolicy.RECOVERY_COOLDOWN_MS);
    assertTrue(InfinityLiveActivity.CobraCallAudioPolicy.preserveVideo(android.media.AudioManager.AUDIOFOCUS_LOSS_TRANSIENT));
  }
}
