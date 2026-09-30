package com.projectinfinity.kodi;
import android.graphics.*;
import android.view.*;
import android.widget.*;
import androidx.media3.exoplayer.ExoPlayer;
import androidx.media3.common.VideoSize;
import java.lang.reflect.Proxy;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=android.app.Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class MiniPlayerFillTest {
 CobraNavigationUiTest helper;InfinityLiveActivity a;TextureView texture;AtomicReference<VideoSize> size;ExoPlayer player;
 @Before public void setup()throws Exception{
  helper=new CobraNavigationUiTest();helper.clock();a=helper.fixture(20);texture=new TextureView(a);size=new AtomicReference<>(new VideoSize(1920,1080));
  player=(ExoPlayer)Proxy.newProxyInstance(ExoPlayer.class.getClassLoader(),new Class[]{ExoPlayer.class},(p,m,args)->{
   if(m.getName().equals("getVideoSize"))return size.get();if(m.getName().equals("hashCode"))return System.identityHashCode(p);if(m.getName().equals("equals"))return p==args[0];
   Class<?> t=m.getReturnType();if(t==boolean.class)return false;if(t==int.class)return 0;if(t==long.class)return 0L;if(t==float.class)return 0f;return null;
  });
  CobraNavigationUiTest.put(a,"mCobraPreviewTexture",texture);
 }
 @After public void cleanup()throws Exception{((android.os.Handler)CobraNavigationUiTest.get(a,"mMain")).removeCallbacksAndMessages(null);a.finish();}
 float[] scale(int w,int h,int mode)throws Exception{
  WholeUiAmbientTest.layout(texture,w,h);CobraNavigationUiTest.call(a,"cobraFitVideo",texture,player,mode);
  float[] v=new float[9];texture.getTransform(new Matrix()).getValues(v);return v;
 }
 void filled(int vw,int vh,float ratio,int w,int h)throws Exception{
  size.set(new VideoSize(vw,vh,0,ratio));float[] v=scale(w,h,0);float sx=v[Matrix.MSCALE_X],sy=v[Matrix.MSCALE_Y];
  assertTrue(sx>=.99999f&&sy>=.99999f);assertEquals(1f,Math.min(sx,sy),.0001f);
  assertEquals(vw*ratio/vh,w*sx/(h*sy),.001f);
  assertEquals((1-sx)*w/2,v[Matrix.MTRANS_X],.01f);assertEquals((1-sy)*h/2,v[Matrix.MTRANS_Y],.01f);
 }
 @Test public void widescreenFillsPortraitAndLandscapeWindows()throws Exception{filled(1920,1080,1,412,232);filled(1920,1080,1,720,320);}
 @Test public void fourByThreeUsesMinimumCenterCrop()throws Exception{filled(640,480,1,412,232);}
 @Test public void portraitAndOddAspectNeverStretch()throws Exception{filled(1080,1920,1,412,232);filled(853,357,1,300,180);}
 @Test public void anamorphicPixelRatioIsPreserved()throws Exception{filled(720,576,1.42222f,412,232);}
 @Test public void savedChannelAspectCannotReintroduceMiniBars()throws Exception{size.set(new VideoSize(640,480));for(int mode=0;mode<=13;mode++){float[] v=scale(412,232,mode);assertEquals(1f,v[Matrix.MSCALE_X],.0001f);assertEquals((412f/232)/(640f/480),v[Matrix.MSCALE_Y],.0001f);}}
 @Test public void invalidDimensionsFailSafely()throws Exception{size.set(new VideoSize(0,0));float[] v=scale(412,232,0);assertEquals(1f,v[0],0);assertEquals(1f,v[4],0);}
 @Test public void repeatedFoldSplitPopupRotationResizeKeepsPlayerIdentity()throws Exception{
  for(int i=0;i<100;i++)for(int[] bounds:new int[][]{{280,160},{412,232},{720,320},{960,540},{320,500}}){filled(i%2==0?640:1080,i%2==0?480:1920,1,bounds[0],bounds[1]);assertSame(texture,CobraNavigationUiTest.get(a,"mCobraPreviewTexture"));}
 }
 @Test public void fullscreenPipAndMultiViewDoNotActivateMiniFill(){assertTrue(InfinityLiveActivity.CobraMiniFillPolicy.active(true,false,false,false));assertFalse(InfinityLiveActivity.CobraMiniFillPolicy.active(true,true,false,false));assertFalse(InfinityLiveActivity.CobraMiniFillPolicy.active(true,false,true,false));assertFalse(InfinityLiveActivity.CobraMiniFillPolicy.active(true,false,false,true));assertFalse(InfinityLiveActivity.CobraMiniFillPolicy.active(false,false,false,false));}
 @Test public void nonPreviewRetainsLockedContainPolicy()throws Exception{CobraNavigationUiTest.put(a,"mCobraPreviewTexture",null);size.set(new VideoSize(640,480));float[] v=scale(412,232,0);assertTrue(v[0]<1f);assertEquals(1f,v[4],.0001f);}
 @Test public void pipReturnRestoresFillWithoutReplacingSurface()throws Exception{size.set(new VideoSize(640,480));CobraNavigationUiTest.put(a,"mInPictureInPicture",true);assertTrue(scale(412,232,0)[0]<1f);CobraNavigationUiTest.put(a,"mInPictureInPicture",false);assertEquals(1f,scale(412,232,0)[0],.0001f);}
 @Test public void fiveModesShareFilledPreviewAndControlsInBothThemes()throws Exception{
  for(boolean dark:new boolean[]{false,true})for(String mode:new String[]{"mobile","grid","compact","cards","focus"}){
   ((android.content.SharedPreferences)CobraNavigationUiTest.get(a,"mPrefs")).edit().putString("cobra_appearance_mode",dark?"dark":"light").commit();
   CobraNavigationUiTest.put(a,"mCobraGuideStyle",mode);CobraNavigationUiTest.call(a,"cobraShowGuideShell");helper.measure(a,412,915);
   FrameLayout host=(FrameLayout)CobraNavigationUiTest.get(a,"mCobraPreviewHost");assertNotNull(host);assertTrue(host.getClipChildren());
   TextureView current=(TextureView)CobraNavigationUiTest.get(a,"mCobraPreviewTexture");assertNotNull(current);assertNull(current.getBackground());assertEquals(1f,current.getAlpha(),0);
   assertEquals(host.getWidth(),current.getWidth());assertEquals(host.getHeight(),current.getHeight());
   texture=current;size.set(new VideoSize(640,480));float[] v=scale(Math.max(2,host.getWidth()),Math.max(2,host.getHeight()),0);assertEquals(1f,Math.min(v[0],v[4]),.0001f);
   View controls=host.findViewWithTag("cobra_preview_controls");assertNotNull(controls);assertTrue(controls.getBottom()<=host.getHeight());assertTrue(controls.getTop()>=0);
  }
 }
 @Test public void pausedAmbientGeometryRefreshHasNoContinuousCadence()throws Exception{
  CobraImmersiveAmbient ambient=new CobraImmersiveAmbient(a);Bitmap b=WholeUiAmbientTest.edges();ambient.testFrame(b,new RectF(0,0,100,100),false);ambient.state(true,false);Object frame=WholeUiAmbientTest.get(ambient,"smoothed");
  for(int i=0;i<50;i++)ambient.geometryChanged();assertEquals(false,WholeUiAmbientTest.get(ambient,"scheduled"));assertSame(frame,WholeUiAmbientTest.get(ambient,"smoothed"));ambient.release();b.recycle();
 }
}
