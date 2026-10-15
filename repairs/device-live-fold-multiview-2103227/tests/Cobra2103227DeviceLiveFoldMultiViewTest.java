package com.projectinfinity.kodi;

import android.app.Application;
import androidx.media3.common.Player;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE)
public class Cobra2103227DeviceLiveFoldMultiViewTest {
  private static final float EPS=.002f;

  @Test public void unexpectedLiveEndedPolicyExcludesVodPauseAndReady(){
    assertEquals(2,InfinityLiveActivity.CobraLiveEndedPolicy.MAX_RECOVERIES);
    assertTrue(InfinityLiveActivity.CobraLiveEndedPolicy.eligible(true,false,true,Player.STATE_ENDED));
    assertFalse(InfinityLiveActivity.CobraLiveEndedPolicy.eligible(true,true,true,Player.STATE_ENDED));
    assertFalse(InfinityLiveActivity.CobraLiveEndedPolicy.eligible(true,false,false,Player.STATE_ENDED));
    assertFalse(InfinityLiveActivity.CobraLiveEndedPolicy.eligible(true,false,true,Player.STATE_READY));
    assertFalse(InfinityLiveActivity.CobraLiveEndedPolicy.eligible(false,false,true,Player.STATE_ENDED));
  }

  @Test public void foldFitUsesMoreInnerDisplayWithoutBecomingFoldFill(){
    float[] fit=InfinityLiveActivity.CobraFoldAspectPolicy.fit(1920,1080,1f,1812,2176);
    float[] fill=InfinityLiveActivity.CobraFoldAspectPolicy.fill(1920,1080,1f,1812,2176);
    float fitW=1812*fit[0],fitH=2176*fit[1],fillW=1812*fill[0],fillH=2176*fill[1];
    assertTrue("Fold Fit should materially reduce the reported black bands",fitH>=2176*.75f);
    assertTrue("Fold Fill must still be the stronger cover mode",fillW+EPS>=1812&&fillH+EPS>=2176);
    assertTrue(fit[0]<=fill[0]+EPS&&fit[1]<=fill[1]+EPS);
    assertEquals(16f/9f,fitW/fitH,.002f);
    assertEquals(16f/9f,fillW/fillH,.002f);
  }

  @Test public void foldFillStillCoversRepresentativeFoldPanes(){
    int[][] panes={{1812,2176},{2176,1812},{904,2316},{2316,904},{1088,1812},{1600,900}};
    float[][] sources={{1920,1080,1f},{1080,1920,1f},{720,576,16f/15f},{1440,1080,1f}};
    for(int[] pane:panes)for(float[] src:sources){
      float[] fill=InfinityLiveActivity.CobraFoldAspectPolicy.fill((int)src[0],(int)src[1],src[2],pane[0],pane[1]);
      float w=pane[0]*fill[0],h=pane[1]*fill[1];
      assertTrue(w+EPS>=pane[0]);assertTrue(h+EPS>=pane[1]);
      assertEquals(src[0]*src[2]/src[1],w/h,.003f);
    }
  }

  @Test public void enlargeTwoScreensKeepsSecondScreenVisible(){
    int[] large=InfinityLiveActivity.CobraMultiLayoutPolicy.rect(0,2,1600,900,0);
    int[] small=InfinityLiveActivity.CobraMultiLayoutPolicy.rect(1,2,1600,900,0);
    assertArrayEquals(new int[]{0,0,1600,630},large);
    assertEquals(630,small[1]);
    assertTrue(small[2]>0&&small[3]>0);
    assertTrue(small[2]<1600);
    assertTrue(small[0]>0);
  }

  @Test public void enlargeFourScreensLeavesThreeLiveThumbnailRegions(){
    int enlarged=2;int[][] rects=new int[4][];
    for(int i=0;i<4;i++)rects[i]=InfinityLiveActivity.CobraMultiLayoutPolicy.rect(i,4,1600,900,enlarged);
    assertArrayEquals(new int[]{0,0,1600,630},rects[enlarged]);
    for(int i=0;i<4;i++)if(i!=enlarged){
      assertEquals(630,rects[i][1]);
      assertTrue(rects[i][2]>0&&rects[i][3]>0);
      assertTrue(rects[i][0]>=0&&rects[i][0]+rects[i][2]<=1600);
    }
  }

  @Test public void invalidFoldGeometryRemainsSafe(){
    assertArrayEquals(new float[]{1f,1f},InfinityLiveActivity.CobraFoldAspectPolicy.fit(0,1080,1f,1000,1000),EPS);
    assertArrayEquals(new float[]{1f,1f},InfinityLiveActivity.CobraFoldAspectPolicy.fill(1920,0,1f,1000,1000),EPS);
  }
}
