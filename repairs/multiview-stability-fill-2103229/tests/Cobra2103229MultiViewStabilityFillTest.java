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
public class Cobra2103229MultiViewStabilityFillTest {
  private static long area(int[] r){return (long)r[2]*r[3];}

  @Test public void fitPathPreserves2103227Geometry(){
    for(int count=2;count<=4;count++)for(int enlarged=-1;enlarged<count;enlarged++)for(int i=0;i<count;i++)
      assertArrayEquals(InfinityLiveActivity.CobraMultiLayoutPolicy.rect(i,count,1812,2176,enlarged),
          InfinityLiveActivity.CobraMultiLayoutPolicy.rect(i,count,1812,2176,enlarged,false));
  }

  @Test public void fillTwoPortraitIsContiguousTopBottom(){
    assertArrayEquals(new int[]{0,0,1000,1000},InfinityLiveActivity.CobraMultiLayoutPolicy.rect(0,2,1000,2000,-1,true));
    assertArrayEquals(new int[]{0,1000,1000,1000},InfinityLiveActivity.CobraMultiLayoutPolicy.rect(1,2,1000,2000,-1,true));
  }

  @Test public void fillTwoLandscapeIsSideBySide(){
    assertArrayEquals(new int[]{0,0,1000,1000},InfinityLiveActivity.CobraMultiLayoutPolicy.rect(0,2,2000,1000,-1,true));
    assertArrayEquals(new int[]{1000,0,1000,1000},InfinityLiveActivity.CobraMultiLayoutPolicy.rect(1,2,2000,1000,-1,true));
  }

  @Test public void fillThreeUsesOneLargePlusTwoSmallerAndNoDeadCanvas(){
    int w=1000,h=2000;long sum=0;
    int[] a=InfinityLiveActivity.CobraMultiLayoutPolicy.rect(0,3,w,h,-1,true);
    int[] b=InfinityLiveActivity.CobraMultiLayoutPolicy.rect(1,3,w,h,-1,true);
    int[] c=InfinityLiveActivity.CobraMultiLayoutPolicy.rect(2,3,w,h,-1,true);
    assertEquals(w,a[2]);assertTrue(a[3]>b[3]);assertEquals(b[3],c[3]);
    assertEquals(0,b[0]);assertEquals(b[2],c[0]);assertEquals(w,c[0]+c[2]);
    sum=area(a)+area(b)+area(c);assertEquals((long)w*h,sum);
  }

  @Test public void fillFourIsTrueEdgeToEdgeTwoByTwo(){
    int[][] expected={{0,0,1000,500},{1000,0,1000,500},{0,500,1000,500},{1000,500,1000,500}};
    for(int i=0;i<4;i++)assertArrayEquals(expected[i],InfinityLiveActivity.CobraMultiLayoutPolicy.rect(i,4,2000,1000,-1,true));
  }

  @Test public void fillEnlargeUsesAllCanvasAndLeavesPeersVisible(){
    int w=1600,h=900,count=4,enlarged=2;long sum=0;
    for(int i=0;i<count;i++){
      int[] r=InfinityLiveActivity.CobraMultiLayoutPolicy.rect(i,count,w,h,enlarged,true);
      assertTrue(r[2]>0&&r[3]>0);sum+=area(r);
      if(i==enlarged){assertEquals(0,r[0]);assertEquals(0,r[1]);assertEquals(h,r[3]);}
    }
    assertEquals((long)w*h,sum);
  }

  @Test public void fillVideoScaleCoversWithoutDistortion(){
    float[] s=InfinityLiveActivity.CobraFoldAspectPolicy.fill(1920,1080,1f,1000,1000);
    float rw=1000*s[0],rh=1000*s[1];
    assertTrue(rw>=1000-.001f&&rh>=1000-.001f);
    assertEquals(16f/9f,rw/rh,.001f);
  }

  @Test public void multiRecoveryNeverAutoResumesUserPausedOrSuppressedTile(){
    assertEquals("",InfinityLiveActivity.CobraMultiRecoveryPolicy.reason(true,false,Player.PLAYBACK_SUPPRESSION_REASON_NONE,Player.STATE_IDLE,false,60000,0,false));
    assertEquals("",InfinityLiveActivity.CobraMultiRecoveryPolicy.reason(true,true,1,Player.STATE_BUFFERING,false,60000,0,false));
  }

  @Test public void multiRecoveryOwnsOnlyErrorIdleAndLongBuffering(){
    int none=Player.PLAYBACK_SUPPRESSION_REASON_NONE;
    assertEquals("idle",InfinityLiveActivity.CobraMultiRecoveryPolicy.reason(true,true,none,Player.STATE_IDLE,false,6000,0,false));
    assertEquals("",InfinityLiveActivity.CobraMultiRecoveryPolicy.reason(true,true,none,Player.STATE_IDLE,false,5999,0,false));
    assertEquals("buffering",InfinityLiveActivity.CobraMultiRecoveryPolicy.reason(true,true,none,Player.STATE_BUFFERING,false,18000,0,false));
    assertEquals("",InfinityLiveActivity.CobraMultiRecoveryPolicy.reason(true,true,none,Player.STATE_BUFFERING,false,17999,0,false));
    assertEquals("error",InfinityLiveActivity.CobraMultiRecoveryPolicy.reason(true,true,none,Player.STATE_READY,true,0,3000,false));
    assertEquals("",InfinityLiveActivity.CobraMultiRecoveryPolicy.reason(true,true,none,Player.STATE_READY,true,0,7999,true));
    assertEquals("error",InfinityLiveActivity.CobraMultiRecoveryPolicy.reason(true,true,none,Player.STATE_READY,true,0,8000,true));
    assertEquals("",InfinityLiveActivity.CobraMultiRecoveryPolicy.reason(true,true,none,Player.STATE_READY,false,60000,0,false));
    assertEquals("",InfinityLiveActivity.CobraMultiRecoveryPolicy.reason(true,true,none,Player.STATE_ENDED,false,60000,0,false));
  }

  @Test public void multiRecoveryIsBoundedAndCooledDown(){
    assertTrue(InfinityLiveActivity.CobraMultiRecoveryPolicy.canAttempt(0,0,1000));
    assertFalse(InfinityLiveActivity.CobraMultiRecoveryPolicy.canAttempt(2,0,100000));
    assertFalse(InfinityLiveActivity.CobraMultiRecoveryPolicy.canAttempt(1,90000,100000));
    assertTrue(InfinityLiveActivity.CobraMultiRecoveryPolicy.canAttempt(1,80000,100000));
  }
}
