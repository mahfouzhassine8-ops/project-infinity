package com.projectinfinity.kodi;
import android.app.Application;import android.graphics.*;import android.view.TextureView;import android.view.View;
import java.util.Arrays;import org.junit.*;import org.junit.runner.RunWith;import org.robolectric.*;import org.robolectric.annotation.*;
import static org.junit.Assert.*;
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE)
@GraphicsMode(GraphicsMode.Mode.NATIVE) @LooperMode(LooperMode.Mode.PAUSED)
public class EmbeddedBorderCropTest {
 int[] image(int x,int y){int[] p=new int[96*64];Arrays.fill(p,Color.rgb(44,128,230));for(int j=0;j<64;j++)for(int i=0;i<96;i++)if(i<x||i>=96-x||j<y||j>=64-y)p[j*96+i]=Color.BLACK;return p;}
 @Test public void detectsEncodedPillars(){int[] b=new int[4];assertTrue(CobraEmbeddedCrop.detectBorders(image(12,0),96,64,b));assertArrayEquals(new int[]{12,12,0,0},b);}
 @Test public void detectsEncodedLetterbox(){int[] b=new int[4];assertTrue(CobraEmbeddedCrop.detectBorders(image(0,8),96,64,b));assertArrayEquals(new int[]{0,0,8,8},b);}
 @Test public void cleanVideoClearsPriorBorders(){int[] b={12,12,8,8};assertTrue(CobraEmbeddedCrop.detectBorders(image(0,0),96,64,b));assertArrayEquals(new int[4],b);}
 @Test public void darkSceneDoesNotChangeLastValidCrop(){int[] p=new int[96*64],b={12,12,0,0};Arrays.fill(p,Color.rgb(5,8,9));assertFalse(CobraEmbeddedCrop.detectBorders(p,96,64,b));assertArrayEquals(new int[]{12,12,0,0},b);}
 @Test public void asymmetricalDarkSceneIsNotPadding(){int[] p=image(0,0);for(int y=0;y<64;y++)for(int x=0;x<12;x++)p[y*96+x]=Color.BLACK;assertFalse(CobraEmbeddedCrop.detectBorders(p,96,64,new int[4]));}
 @Test public void almostBlackColoredEdgesArePreserved(){int[] p=image(12,0);for(int i=0;i<p.length;i++)if(p[i]==Color.BLACK)p[i]=Color.rgb(25,20,30);int[] b=new int[4];assertTrue(CobraEmbeddedCrop.detectBorders(p,96,64,b));assertArrayEquals(new int[4],b);}
 @Test public void minimumZoomAccountsForCropAlreadyAppliedByAspect(){assertEquals(1f,CobraEmbeddedCrop.requiredZoom(1.6f,1f,.75f,1f),.0001f);assertEquals(4f/3,CobraEmbeddedCrop.requiredZoom(1f,1f,.75f,1f),.0001f);assertEquals(1.25f,CobraEmbeddedCrop.requiredZoom(1f,1f,1f,.8f),.0001f);}
 @Test public void addedZoomPreservesOriginalAspect(){float sx=1f,sy=1.333333f,z=CobraEmbeddedCrop.requiredZoom(sx,sy,.75f,1f);assertEquals(sx/sy,(sx*z)/(sy*z),.0001f);}
 @Test public void disabledFullscreenUsesExactBaseTransformAndCloseIsIdempotent(){TextureView v=new TextureView(RuntimeEnvironment.getApplication());v.layout(0,0,320,180);Matrix base=new Matrix();base.setScale(.75f,1f,160,90);CobraEmbeddedCrop c=new CobraEmbeddedCrop(()->false,null);c.apply(v,null,base,false);float[] expected=new float[9],actual=new float[9];base.getValues(expected);v.getTransform(new Matrix()).getValues(actual);assertArrayEquals(expected,actual,0);c.close();c.close();c.refresh();assertEquals(1f,c.zoom(),0);}

 class Capture extends TextureView {
  int captures;boolean fail;Bitmap buffer;float[] expected;
  Capture(){super(RuntimeEnvironment.getApplication());layout(0,0,320,180);}
  @Override public boolean isAttachedToWindow(){return true;}
  @Override public boolean isShown(){return true;}
  @Override public int getWindowVisibility(){return View.VISIBLE;}
  @Override public boolean isAvailable(){return true;}
  @Override public Bitmap getBitmap(Bitmap target){captures++;float[] actual=new float[9];getTransform(new Matrix()).getValues(actual);if(expected!=null)assertArrayEquals("Sampling must never mutate the display transform",expected,actual,0);if(fail)throw new IllegalStateException("unavailable");if(buffer!=null)assertSame("Capture must reuse its bitmap",buffer,target);buffer=target;target.setPixels(image(12,0),0,96,0,0,96,64);return target;}
 }
 androidx.media3.exoplayer.ExoPlayer player(boolean[] playing){return (androidx.media3.exoplayer.ExoPlayer)java.lang.reflect.Proxy.newProxyInstance(getClass().getClassLoader(),new Class[]{androidx.media3.exoplayer.ExoPlayer.class},(p,m,args)->{if(m.getName().equals("isPlaying"))return playing[0];if(m.getName().equals("getVideoSize"))return new androidx.media3.common.VideoSize(640,360);return null;});}
 void advance(long millis){Shadows.shadowOf(android.os.Looper.getMainLooper()).idleFor(java.time.Duration.ofMillis(millis));}
 @Test public void stableEvidenceUsesOneBitmapAndStopsWhenPausedOrHidden()throws Exception{Capture v=new Capture();boolean[] live={true},playing={true};CobraEmbeddedCrop c=new CobraEmbeddedCrop(()->live[0],null);c.apply(v,player(playing),new Matrix(),true);advance(650);assertEquals(4f/3,c.zoom(),.001f);int count=v.captures;playing[0]=false;c.refresh();advance(8000);assertEquals(count,v.captures);playing[0]=true;live[0]=false;c.refresh();advance(8000);assertEquals(count,v.captures);live[0]=true;c.refresh();advance(4500);assertTrue(v.captures>count);assertTrue("Bounded cadence",v.captures<=8);Bitmap retained=v.buffer;c.close();assertTrue(retained.isRecycled());advance(5000);assertEquals(null,CobraNavigationUiTest.get(c,"player"));}
 @Test public void captureFailureRestoresTransformAndStopsFurtherWork()throws Exception{Capture v=new Capture();v.fail=true;Matrix transform=new Matrix();transform.setScale(1f,1.5f,160,90);v.expected=new float[9];transform.getValues(v.expected);CobraEmbeddedCrop c=new CobraEmbeddedCrop(()->true,null);c.apply(v,player(new boolean[]{true}),transform,true);advance(5000);assertEquals(1,v.captures);float[] before=new float[9],after=new float[9];transform.getValues(before);v.getTransform(new Matrix()).getValues(after);assertArrayEquals(before,after,0);c.refresh();advance(5000);assertEquals(1,v.captures);c.close();}
}
