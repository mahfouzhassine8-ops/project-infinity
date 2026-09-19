package com.projectinfinity.kodi;

import android.app.Application;
import java.net.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE)
public class Cobra2103183NetworkFamilyControlTest {
  @Test public void automaticIsDefaultSafeDualStackMode(){
    assertEquals(0,InfinityLiveActivity.CobraNetworkFamilyPolicy.AUTO);
    assertEquals("Automatic (IPv4 + IPv6)",InfinityLiveActivity.CobraNetworkFamilyPolicy.label(0));
    assertEquals(0,InfinityLiveActivity.CobraNetworkFamilyPolicy.sanitize(99));
  }

  @Test public void ipv4ModeAcceptsOnlyIpv4() throws Exception {
    InetAddress v4=InetAddress.getByAddress(new byte[]{(byte)192,0,2,10});
    InetAddress v6=InetAddress.getByAddress(new byte[16]);
    assertTrue(InfinityLiveActivity.CobraNetworkFamilyPolicy.matches(v4,InfinityLiveActivity.CobraNetworkFamilyPolicy.IPV4));
    assertFalse(InfinityLiveActivity.CobraNetworkFamilyPolicy.matches(v6,InfinityLiveActivity.CobraNetworkFamilyPolicy.IPV4));
  }

  @Test public void ipv6ModeAcceptsOnlyIpv6() throws Exception {
    InetAddress v4=InetAddress.getByAddress(new byte[]{(byte)192,0,2,10});
    byte[] b=new byte[16];b[0]=0x20;b[1]=0x01;b[2]=0x0d;b[3]=(byte)0xb8;b[15]=1;
    InetAddress v6=InetAddress.getByAddress(b);
    assertTrue(InfinityLiveActivity.CobraNetworkFamilyPolicy.matches(v6,InfinityLiveActivity.CobraNetworkFamilyPolicy.IPV6));
    assertFalse(InfinityLiveActivity.CobraNetworkFamilyPolicy.matches(v4,InfinityLiveActivity.CobraNetworkFamilyPolicy.IPV6));
  }

  @Test public void routedIpv4UrlKeepsProviderPathQueryAndPort() throws Exception {
    URL original=new URL("http://provider.example:8080/live/stream.ts?token=abc");
    InetAddress v4=InetAddress.getByAddress(new byte[]{(byte)192,0,2,25});
    URL routed=InfinityLiveActivity.CobraNetworkFamilyPolicy.routedUrl(original,v4);
    assertEquals("http",routed.getProtocol());
    assertEquals(8080,routed.getPort());
    assertEquals("/live/stream.ts?token=abc",routed.getFile());
    assertEquals("192.0.2.25",routed.getHost());
  }

  @Test public void routedIpv6UrlKeepsProviderRequest() throws Exception {
    URL original=new URL("https://provider.example/live.m3u8?u=1");
    byte[] b=new byte[16];b[0]=0x20;b[1]=0x01;b[2]=0x0d;b[3]=(byte)0xb8;b[15]=2;
    InetAddress v6=InetAddress.getByAddress(b);
    URL routed=InfinityLiveActivity.CobraNetworkFamilyPolicy.routedUrl(original,v6);
    assertEquals("https",routed.getProtocol());
    assertEquals("/live.m3u8?u=1",routed.getFile());
    assertTrue(routed.toString().contains("[2001:db8:"));
  }

  @Test public void forcedRoutingPreservesOriginalHttpHost() throws Exception {
    URL standard=new URL("https://provider.example/live");
    URL custom=new URL("https://provider.example:8443/live");
    assertEquals("provider.example",InfinityLiveActivity.CobraNetworkFamilyPolicy.hostHeader(standard));
    assertEquals("provider.example:8443",InfinityLiveActivity.CobraNetworkFamilyPolicy.hostHeader(custom));
  }
}
