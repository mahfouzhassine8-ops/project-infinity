package com.projectinfinity.kodi;

import android.app.Application;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE)
public class Cobra2103178TimeshiftMiniPlayerTest {
  @Test public void httpHeaderUsesRealCrLf(){
    String h=InfinityLiveActivity.CobraTimeshiftTransportPolicy.httpHeader("200 OK","video/mp2t",1880,false);
    assertTrue(InfinityLiveActivity.CobraTimeshiftTransportPolicy.hasRealHttpFraming(h));
    assertTrue(h.startsWith("HTTP/1.1 200 OK\r\n"));
    assertTrue(h.endsWith("\r\n\r\n"));
  }

  @Test public void httpHeaderDoesNotEmitEscapedCrLfText(){
    String h=InfinityLiveActivity.CobraTimeshiftTransportPolicy.httpHeader("200 OK","video/mp2t",1880,false);
    assertFalse(h.contains("\\r\\n"));
  }

  @Test public void httpHeaderCarriesExactContentLength(){
    String h=InfinityLiveActivity.CobraTimeshiftTransportPolicy.httpHeader("200 OK","application/vnd.apple.mpegurl",321,true);
    assertTrue(h.contains("Content-Length: 321\r\n"));
    assertTrue(h.contains("Cache-Control: no-cache, no-store\r\n"));
  }

  @Test public void playlistHeaderUsesRealLineFeeds(){
    String p=InfinityLiveActivity.CobraTimeshiftTransportPolicy.playlistHeader(42);
    assertTrue(InfinityLiveActivity.CobraTimeshiftTransportPolicy.hasRealPlaylistLines(p));
    assertFalse(p.contains("\\n"));
  }

  @Test public void playlistHeaderCarriesSequenceAndLiveReserve(){
    String p=InfinityLiveActivity.CobraTimeshiftTransportPolicy.playlistHeader(42);
    assertTrue(p.contains("#EXT-X-MEDIA-SEQUENCE:42\n"));
    assertTrue(p.contains("#EXT-X-START:TIME-OFFSET=-6.0,PRECISE=NO\n"));
  }

  @Test public void rawHttpTsRemainsEligibleForLocalReserve(){
    assertTrue(InfinityLiveActivity.CobraFinalFeaturePolicy.localTsEligible("https://tv.example/live/7.ts","ts"));
    assertTrue(InfinityLiveActivity.CobraFinalFeaturePolicy.localTsEligible("http://tv.example/live/7","ts"));
  }

  @Test public void hlsAndRtspRemainOutsideRawTsBridge(){
    assertFalse(InfinityLiveActivity.CobraFinalFeaturePolicy.localTsEligible("https://tv.example/live/7.m3u8","m3u8"));
    assertFalse(InfinityLiveActivity.CobraFinalFeaturePolicy.localTsEligible("rtsp://tv.example/live/7","ts"));
  }

  @Test public void localReserveWindowRemainsBounded(){
    assertEquals(60,InfinityLiveActivity.CobraFinalFeaturePolicy.timeshiftSeconds(60));
    assertEquals(120,InfinityLiveActivity.CobraFinalFeaturePolicy.timeshiftSeconds(120));
    assertEquals(180,InfinityLiveActivity.CobraFinalFeaturePolicy.timeshiftSeconds(180));
    assertEquals(180,InfinityLiveActivity.CobraFinalFeaturePolicy.timeshiftSeconds(999));
  }

  @Test public void throughputEvidenceRemainsDeterministic(){
    assertEquals(8000L,InfinityLiveActivity.CobraFinalFeaturePolicy.throughputKbps(1_000_000L,1000L));
    assertEquals(-1L,InfinityLiveActivity.CobraFinalFeaturePolicy.throughputKbps(0L,1000L));
  }

  @Test public void refreshPolicyStillRequests120WhenSupported(){
    assertEquals(120f,InfinityLiveActivity.CobraRefreshPolicy.choose("120",new float[]{60f,90f,120f},false,false),.01f);
    assertTrue(InfinityLiveActivity.CobraRefreshPolicy.requestedExactly("120",120f));
  }
}
