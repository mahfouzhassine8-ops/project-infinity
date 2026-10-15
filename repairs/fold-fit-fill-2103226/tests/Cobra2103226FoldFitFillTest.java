package com.projectinfinity.kodi;

import android.app.Application;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE)
public class Cobra2103226FoldFitFillTest {
  private static final float EPS=.001f;

  @Test public void legacyMode12IsNowFoldFitWithoutChangingItsValue(){
    assertEquals(12,InfinityLiveActivity.CobraFoldAspectPolicy.MODE);
    assertEquals(12,InfinityLiveActivity.CobraFoldAspectPolicy.FIT_MODE);
    assertEquals(13,InfinityLiveActivity.CobraFoldAspectPolicy.FILL_MODE);
    assertEquals(13,InfinityLiveActivity.CobraFoldAspectPolicy.MAX_MODE);
    assertTrue(InfinityLiveActivity.CobraFoldAspectPolicy.foldMode(12));
    assertTrue(InfinityLiveActivity.CobraFoldAspectPolicy.foldMode(13));
    assertFalse(InfinityLiveActivity.CobraFoldAspectPolicy.foldMode(1));
  }

  @Test public void inheritedScaleEntryPointStillMeansWholeFrameFit(){
    float[] legacy=InfinityLiveActivity.CobraFoldAspectPolicy.scale(1920,1080,1f,1812,2176);
    float[] fit=InfinityLiveActivity.CobraFoldAspectPolicy.fit(1920,1080,1f,1812,2176);
    assertArrayEquals(fit,legacy,EPS);
    assertArrayEquals(fit,InfinityLiveActivity.CobraFoldAspectPolicy.scaleForMode(12,1920,1080,1f,1812,2176),EPS);
  }

  @Test public void foldFitContainsEntireFrameAcrossRepresentativeFoldPanes(){
    int[][] panes={{1812,2176},{2176,1812},{904,2316},{2316,904},{1088,1812},{452,2316},{900,1600},{1600,900},{601,601}};
    float[][] sources={{1920,1080,1f},{1080,1920,1f},{720,576,16f/15f},{1440,1080,1f}};
    for(int[] pane:panes)for(float[] src:sources){
      float[] scale=InfinityLiveActivity.CobraFoldAspectPolicy.fit((int)src[0],(int)src[1],src[2],pane[0],pane[1]);
      float width=pane[0]*scale[0],height=pane[1]*scale[1];
      assertTrue(width<=pane[0]+EPS);assertTrue(height<=pane[1]+EPS);
      assertTrue(Math.abs(width-pane[0])<EPS||Math.abs(height-pane[1])<EPS);
      float expected=src[0]*src[2]/src[1];
      assertEquals(expected,width/height,EPS);
    }
  }

  @Test public void foldFillCoversPaneWithOnlyMinimumProportionalCrop(){
    int[][] panes={{1812,2176},{2176,1812},{904,2316},{2316,904},{1088,1812},{452,2316},{900,1600},{1600,900},{601,601}};
    float[][] sources={{1920,1080,1f},{1080,1920,1f},{720,576,16f/15f},{1440,1080,1f}};
    for(int[] pane:panes)for(float[] src:sources){
      float[] scale=InfinityLiveActivity.CobraFoldAspectPolicy.fill((int)src[0],(int)src[1],src[2],pane[0],pane[1]);
      float width=pane[0]*scale[0],height=pane[1]*scale[1];
      assertTrue(width+EPS>=pane[0]);assertTrue(height+EPS>=pane[1]);
      assertTrue(Math.abs(width-pane[0])<EPS||Math.abs(height-pane[1])<EPS);
      assertTrue(scale[0]>=1f-EPS&&scale[1]>=1f-EPS);
      float expected=src[0]*src[2]/src[1];
      assertEquals(expected,width/height,EPS);
      assertArrayEquals(scale,InfinityLiveActivity.CobraFoldAspectPolicy.scaleForMode(13,(int)src[0],(int)src[1],src[2],pane[0],pane[1]),EPS);
    }
  }

  @Test public void invalidGeometryIsSafeForBothModes(){
    assertArrayEquals(new float[]{1f,1f},InfinityLiveActivity.CobraFoldAspectPolicy.fit(0,1080,1f,1000,1000),EPS);
    assertArrayEquals(new float[]{1f,1f},InfinityLiveActivity.CobraFoldAspectPolicy.fill(1920,0,1f,1000,1000),EPS);
  }
}
