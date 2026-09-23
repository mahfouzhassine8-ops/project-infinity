package com.projectinfinity.kodi;
import android.app.Application;
import org.junit.*;import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;import org.robolectric.annotation.Config;
import static org.junit.Assert.*;
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE)
public class Cobra2103230PolicyTest {
  @Test public void perPlayerIntentAndDismissalGate(){
    assertTrue(InfinityLiveActivity.CobraAuditPolicy.retryCurrent(7,7,true,true,false));
    assertFalse(InfinityLiveActivity.CobraAuditPolicy.retryCurrent(7,8,true,true,false));
    assertFalse(InfinityLiveActivity.CobraAuditPolicy.retryCurrent(7,7,false,true,false));
    assertFalse(InfinityLiveActivity.CobraAuditPolicy.retryCurrent(7,7,true,false,false));
    assertFalse(InfinityLiveActivity.CobraAuditPolicy.retryCurrent(7,7,true,true,true));
  }
  @Test public void fillBelongsOnlyToActualGridSurface(){
    assertTrue(InfinityLiveActivity.CobraAuditPolicy.fillApplies(true,false,false,true));
    assertFalse(InfinityLiveActivity.CobraAuditPolicy.fillApplies(true,false,true,true));
    assertFalse(InfinityLiveActivity.CobraAuditPolicy.fillApplies(true,true,false,true));
    assertFalse(InfinityLiveActivity.CobraAuditPolicy.fillApplies(true,false,false,false));
    assertFalse(InfinityLiveActivity.CobraAuditPolicy.fillApplies(false,false,false,true));
  }
  @Test public void insetAlreadyConsumedByParentIsNotSubtractedTwice(){
    assertArrayEquals(new int[]{0,0,0,0},InfinityLiveActivity.CobraAuditPolicy.localInsets(0,40,1000,1860,1000,2000,0,40,0,100));
  }
  @Test public void edgeToEdgeCanvasRetainsRealSafetyInsets(){
    assertArrayEquals(new int[]{10,40,20,100},InfinityLiveActivity.CobraAuditPolicy.localInsets(0,0,1000,2000,1000,2000,10,40,20,100));
  }
  @Test public void resizedCanvasKeepsOnlyIntersectingInsets(){
    assertArrayEquals(new int[]{0,0,0,0},InfinityLiveActivity.CobraAuditPolicy.localInsets(20,100,600,800,1000,2000,10,40,20,100));
    assertArrayEquals(new int[]{0,0,0,50},InfinityLiveActivity.CobraAuditPolicy.localInsets(0,40,1000,1910,1000,2000,0,40,0,100));
  }
  @Test public void bufferingNeedsNoLoaderAndNoProgress(){
    assertFalse(InfinityLiveActivity.CobraAuditPolicy.stalledBuffer(true,90000,1000));
    assertFalse(InfinityLiveActivity.CobraAuditPolicy.stalledBuffer(false,90000,89999));
    assertTrue(InfinityLiveActivity.CobraAuditPolicy.stalledBuffer(false,90000,72000));
  }
  @Test public void traceMemoryBoundedAndChronological()throws Exception{
    InfinityLiveActivity.CobraAuditTrail trail=new InfinityLiveActivity.CobraAuditTrail();
    for(int i=0;i<500;i++)trail.add("state",i,0);org.json.JSONArray rows=trail.snapshot();
    assertEquals(48,rows.length());assertEquals(452,rows.getJSONObject(0).getInt("value"));assertEquals(499,rows.getJSONObject(47).getInt("value"));
  }
  @Test public void realFillRectanglesHaveNoOverlapsAndExactUnion(){
    for(int[] viewport:new int[][]{{904,2316},{1812,2176},{2176,1812},{1600,900},{601,601},{321,721}})
    for(int count=2;count<=4;count++)for(int enlarged=-1;enlarged<count;enlarged++){
      int[][] rects=new int[count][];long area=0;
      for(int i=0;i<count;i++){
        int[] r=InfinityLiveActivity.CobraMultiLayoutPolicy.rect(i,count,viewport[0],viewport[1],enlarged,true);rects[i]=r;
        assertTrue(r[0]>=0&&r[1]>=0&&r[2]>0&&r[3]>0&&r[0]+r[2]<=viewport[0]&&r[1]+r[3]<=viewport[1]);area+=(long)r[2]*r[3];
      }
      for(int i=0;i<count;i++)for(int j=i+1;j<count;j++){
        int[] a=rects[i],b=rects[j];int w=Math.min(a[0]+a[2],b[0]+b[2])-Math.max(a[0],b[0]);int h=Math.min(a[1]+a[3],b[1]+b[3])-Math.max(a[1],b[1]);assertTrue("No overlap",w<=0||h<=0);
      }
      assertEquals((long)viewport[0]*viewport[1],area);
    }
  }
}
