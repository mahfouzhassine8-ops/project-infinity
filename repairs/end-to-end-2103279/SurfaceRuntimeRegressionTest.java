package com.projectinfinity.kodi;
import android.app.Application;import android.graphics.*;import android.view.*;import android.widget.*;
import androidx.media3.common.*;import androidx.media3.exoplayer.ExoPlayer;
import java.lang.reflect.*;import java.util.*;import java.util.concurrent.atomic.AtomicReference;
import org.junit.*;import org.junit.runner.RunWith;import org.robolectric.*;import org.robolectric.annotation.*;
import static org.junit.Assert.*;
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE) @LooperMode(LooperMode.Mode.PAUSED)
public class SurfaceRuntimeRegressionTest {
 CobraNavigationUiTest ui;InfinityLiveActivity a;TextureView texture;ExoPlayer player;Object binding;Player.Listener listener;
 AtomicReference<VideoSize> size=new AtomicReference<>(new VideoSize(640,480));Cobra2103201ScrubberTest.Controlled state;
 Object get(Object o,String n)throws Exception{return CobraNavigationUiTest.get(o,n);} void put(Object o,String n,Object v)throws Exception{CobraNavigationUiTest.put(o,n,v);}
 Object call(Object o,String n,Object...args)throws Exception{return CobraNavigationUiTest.call(o,n,args);}
 @Before public void before()throws Exception{
  CobraVisualRenderer.loading.set(true);CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer.clients.clear();ui=new CobraNavigationUiTest();ui.clock();a=ui.fixture(12);ui.measure(a,412,915);
  texture=(TextureView)get(a,"mCobraPreviewTexture");state=new Cobra2103201ScrubberTest.Controlled();
  player=(ExoPlayer)Proxy.newProxyInstance(ExoPlayer.class.getClassLoader(),new Class[]{ExoPlayer.class},(p,m,args)->m.getName().equals("getVideoSize")?size.get():state.invoke(p,m,args));
  Object channel=((List<?>)get(a,"mChannels")).get(0);binding=CobraNavigationUiTest.construct("CobraPlayerBinding",a,player,channel);((Map)get(a,"mCobraPlayerBindings")).put(player,binding);put(a,"mCobraPreviewPlayer",player);listener=(Player.Listener)binding;
  call(a,"cobraAttachVideo",player,texture);
 }
 @After public void after()throws Exception{ui.clean(a);CobraVisualRenderer.clients.clear();}
 void filled(){float[] v=new float[9];texture.getTransform(new Matrix()).getValues(v);assertTrue(v[0]>=.999f&&v[4]>=.999f);assertEquals(1f,Math.min(v[0],v[4]),.001f);assertEquals(640f/480,texture.getWidth()*v[0]/(texture.getHeight()*v[4]),.005f);}
 @Test public void actualBindingAppliesFillSynchronouslyOnAttachment()throws Exception{filled();assertEquals(0,state.prepares);assertEquals(0,state.mediaChanges);}
 @Test public void sameSurfaceReattachmentRepairsResetTransform()throws Exception{texture.setTransform(new Matrix());call(a,"cobraAttachVideo",player,texture);filled();assertSame(texture,get(binding,"texture"));}
 @Test public void decoderFirstFrameRestoresFillAfterTransformReset()throws Exception{texture.setTransform(new Matrix());listener.onRenderedFirstFrame();filled();assertEquals(0,state.prepares);}
 @Test public void surfaceSizeEventRestoresFillWithoutNewVideoMetadata()throws Exception{texture.setTransform(new Matrix());listener.onSurfaceSizeChanged(texture.getWidth(),texture.getHeight());filled();}
 @Test public void transientUnknownMetadataRetainsLastValidAspect()throws Exception{listener.onVideoSizeChanged(size.get());size.set(VideoSize.UNKNOWN);texture.setTransform(new Matrix());listener.onSurfaceSizeChanged(412,232);filled();}
 @Test public void fiveModesUseActualBindingLayoutCallbacks()throws Exception{for(String mode:new String[]{"mobile","grid","compact","cards","focus"}){put(a,"mCobraGuideStyle",mode);call(a,"cobraShowGuideShell");ui.measure(a,412,915);TextureView current=(TextureView)get(a,"mCobraPreviewTexture");assertSame(texture,current);listener.onRenderedFirstFrame();filled();assertSame(player,get(a,"mCobraPreviewPlayer"));}assertEquals(0,state.prepares);assertEquals(0,state.mediaChanges);}
 @Test public void repeatedLayoutCallbacksFollowNarrowWideBounds()throws Exception{for(int n=0;n<30;n++)for(int[] wh:new int[][]{{280,160},{540,300},{720,500},{320,500}}){WholeUiAmbientTest.layout(texture,wh[0],wh[1]);filled();}assertSame(player,get(a,"mCobraPreviewPlayer"));assertEquals(0,state.prepares);}
 @Test public void closedBindingRejectsDelayedDecoderEvents()throws Exception{put(binding,"closed",true);texture.setTransform(new Matrix());listener.onRenderedFirstFrame();listener.onSurfaceSizeChanged(500,300);float[] v=new float[9];texture.getTransform(new Matrix()).getValues(v);assertEquals(1f,v[0],0);assertEquals(1f,v[4],0);}
 @Test public void quickPeekActualSessionUsesMinimumCropAndFirstFrameRefits()throws Exception{
  Cobra2103207QuickPeekIntegrationTest peek=new Cobra2103207QuickPeekIntegrationTest();try{peek.before();peek.capacity(2,1);peek.open();Object session=get(peek.f.a,"mCobraQuickPeek");ExoPlayer original=(ExoPlayer)get(session,"player");TextureView view=(TextureView)get(session,"texture");put(session,"player",player);WholeUiAmbientTest.layout(view,320,104);call(session,"fit");float[] m=new float[9];view.getTransform(new Matrix()).getValues(m);assertEquals(1f,m[0],.001f);assertEquals((320f/104)/(640f/480),m[4],.001f);view.setTransform(new Matrix());((Player.Listener)get(session,"events")).onRenderedFirstFrame();view.getTransform(new Matrix()).getValues(m);assertTrue(m[4]>1f);put(session,"player",original);assertTrue(peek.main.commands.isEmpty());}finally{peek.after();}
 }
}
