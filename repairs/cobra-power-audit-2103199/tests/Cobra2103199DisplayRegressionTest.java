package com.projectinfinity.kodi;

import android.app.Application;
import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Matrix;
import android.graphics.RectF;
import android.view.TextureView;
import android.view.View;
import android.widget.FrameLayout;
import androidx.media3.common.*;
import androidx.media3.exoplayer.ExoPlayer;
import java.lang.reflect.*;
import java.util.*;
import org.json.JSONObject;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Actual Android TextureView matrix checks, using controlled metadata, not live/GPU decoding. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w800dp-h600dp-land-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103199DisplayRegressionTest {
  CobraNavigationUiTest ui; InfinityLiveActivity a; SharedPreferences prefs;
  @Before public void before()throws Exception {
    CobraVisualRenderer.loading.set(true);CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer.clients.clear();
    ui=new CobraNavigationUiTest();ui.clock();a=ui.fixture(8);prefs=(SharedPreferences)get(a,"mPrefs");
  }
  @After public void after()throws Exception{ui.clean(a);CobraVisualRenderer.clients.clear();}
  static Object get(Object o,String n)throws Exception{return CobraNavigationUiTest.get(o,n);}
  static void put(Object o,String n,Object v)throws Exception{CobraNavigationUiTest.put(o,n,v);}
  static Object call(Object o,String n,Object...v)throws Exception{return CobraNavigationUiTest.call(o,n,v);}
  Object channel(int index)throws Exception{return ((List<?>)get(a,"mChannels")).get(index);}
  final class Controlled implements InvocationHandler {
    VideoSize size=new VideoSize(1920,1080);boolean requested=true;
    final List<String> writes=new ArrayList<>();
    TrackSelectionParameters tracks=new TrackSelectionParameters.Builder(a).build();
    final ExoPlayer player=(ExoPlayer)Proxy.newProxyInstance(ExoPlayer.class.getClassLoader(),new Class<?>[]{ExoPlayer.class},this);
    public Object invoke(Object proxy,Method m,Object[] args){String n=m.getName();
      if(n.equals("hashCode"))return System.identityHashCode(proxy);if(n.equals("equals"))return proxy==args[0];if(n.equals("toString"))return "Controlled display metadata";
      if(n.equals("getVideoSize"))return size;if(n.equals("getTrackSelectionParameters"))return tracks;
      if(n.equals("getCurrentTracks"))return Tracks.EMPTY;if(n.equals("getPlaybackState"))return Player.STATE_READY;
      if(n.equals("getPlayWhenReady")||n.equals("isPlaying"))return requested;
      if(n.equals("getAudioAttributes"))return AudioAttributes.DEFAULT;
      if(n.equals("getVideoFormat"))return new Format.Builder().setWidth(size.width).setHeight(size.height).setSampleMimeType("video/avc").build();
      if(n.startsWith("set")||n.startsWith("clear")||n.equals("release")||n.equals("prepare")||n.equals("play")||n.equals("stop")||n.startsWith("seek"))writes.add(n);
      Class<?> t=m.getReturnType();if(t==boolean.class)return false;if(t==int.class)return 0;if(t==long.class)return 0L;if(t==float.class)return 0f;if(t==double.class)return 0d;return null;
    }
  }
  @SuppressWarnings("unchecked") Object bind(Controlled c,Object channel,TextureView t,boolean fullscreen)throws Exception {
    Object b=CobraNavigationUiTest.construct("CobraPlayerBinding",a,c.player,channel);
    ((Map<ExoPlayer,Object>)get(a,"mCobraPlayerBindings")).put(c.player,b);
    if(fullscreen){put(a,"mPlaying",channel);put(a,"mPlayer",c.player);put(a,"mPlayerTexture",t);}else put(a,"mCobraPreviewPlayer",c.player);
    call(a,"cobraAttachVideo",c.player,t);return b;
  }
  TextureView texture(int w,int h)throws Exception{
    FrameLayout root=new FrameLayout(a);a.setContentView(root);TextureView t=new TextureView(a);root.addView(t,new FrameLayout.LayoutParams(-1,-1));
    put(a,"mPlayerOverlay",root);resize(root,w,h);return t;
  }
  void resize(View root,int w,int h){root.measure(View.MeasureSpec.makeMeasureSpec(w,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h,View.MeasureSpec.EXACTLY));root.layout(0,0,w,h);}
  RectF rendered(TextureView t){RectF r=new RectF(0,0,t.getWidth(),t.getHeight());t.getTransform(new Matrix()).mapRect(r);return r;}
  void checkRect(TextureView t,double expectedW,double expectedH){RectF r=rendered(t);assertEquals(expectedW,r.width(),.02);assertEquals(expectedH,r.height(),.02);assertEquals(t.getWidth()/2f,r.centerX(),.02);assertEquals(t.getHeight()/2f,r.centerY(),.02);}
  void mode(Object channel,int mode)throws Exception{String key=(String)call(a,"cobraPreferenceKey",channel);prefs.edit().putString(key,new JSONObject().put("schema",1).put("aspect",mode).put("x",1.33).put("y",.77).toString()).commit();}
  double[] expected(int mode,int sw,int sh,float par,int w,int h){
    double source=sw*(double)par/sh;if(mode==2)source=16.0/9;if(mode==3)source=4.0/3;
    double rw=w,rh=w/source;if(rh>h){rh=h;rw=h*source;}
    if(mode==1){double z=Math.max(w/rw,h/rh);rw*=z;rh*=z;}
    if(mode>=4&&mode<=6)rw*=new double[]{1.1,1.25,1.4}[mode-4];
    if(mode==7){rw*=1.24;rh*=.84;}
    if(mode>=8&&mode<=10){double z=new double[]{1.25,1.5,2}[mode-8];rw*=z;rh*=z;}
    if(mode==11){rw*=1.33;rh*=.77;}
    if(mode==12&&Math.min(w,h)>=600&&Math.max(source/(w/(double)h),(w/(double)h)/source)<=1.18){double z=Math.min(1.06,Math.max(w/rw,h/rh));rw*=z;rh*=z;}
    return new double[]{rw,rh};
  }
  @Test public void allThirteenModesProduceTheirActualCenteredTextureRectangle()throws Exception {
    Controlled c=new Controlled();TextureView t=texture(1812,2176);bind(c,channel(0),t,true);
    int[][] viewports={{1812,2176},{2176,1812},{904,2316},{2316,904},{320,240},{1920,1080}};
    int[][] sources={{1920,1080},{1440,1080},{1080,1920},{720,576}};
    for(int[] v:viewports){resize((View)t.getParent(),v[0],v[1]);for(int[] s:sources)for(float par:new float[]{1f,16f/15f}){
      c.size=new VideoSize(s[0],s[1],0,par);
      prefs.edit().putFloat("cobra_custom_aspect_x",1.33f).putFloat("cobra_custom_aspect_y",.77f).commit();
      for(int mode=0;mode<=12;mode++){call(a,"cobraFitVideo",t,c.player,mode);double[] e=expected(mode,s[0],s[1],par,v[0],v[1]);checkRect(t,e[0],e[1]);}
    }}
    assertFalse(c.writes.contains("prepare"));assertFalse(c.writes.contains("release"));assertFalse(c.writes.contains("seekTo"));
  }
  @Test public void customHundredPercentControlsReallyRenderHundredPercentWithoutSavedAxes()throws Exception{
    Controlled c=new Controlled();TextureView t=texture(1600,900);bind(c,null,t,true);
    prefs.edit().remove("cobra_custom_aspect_x").remove("cobra_custom_aspect_y").commit();
    call(a,"cobraFitVideo",t,c.player,11);checkRect(t,1600,900);
  }
  @Test public void eachChannelModeControlPersistsAndChangesActualTextureGeometry()throws Exception{
    Controlled c=new Controlled();TextureView t=texture(800,600);Object ch=channel(0);mode(ch,-1);bind(c,ch,t,true);
    for(int selected=0;selected<=12;selected++){
      call(a,"cobraShowChannelAspect",ch);ui.measure(a,800,600);
      View row=a.getWindow().getDecorView().findViewWithTag("cobra-channel-aspect:"+selected);assertNotNull("Mode control "+selected,row);assertTrue(row.performClick());
      String key=(String)call(a,"cobraPreferenceKey",ch);assertEquals(selected,new JSONObject(prefs.getString(key,"")).getInt("aspect"));
      double[] e=expected(selected,1920,1080,1f,t.getWidth(),t.getHeight());checkRect(t,e[0],e[1]);
    }
  }
  @Test public void currentChannelOverrideWinsOverStaleFullscreenAspectCache()throws Exception{
    Controlled c=new Controlled();TextureView t=texture(1600,900);Object ch=channel(1);mode(ch,3);bind(c,ch,t,true);put(a,"mAspectMode",1);
    call(a,"applyCobraAspectTransform");checkRect(t,1200,900);assertEquals(3,get(a,"mAspectMode"));
  }
  @Test public void inheritedCurrentChannelUsesGlobalDefaultInsteadOfPreviousChannelMode()throws Exception{
    Controlled c=new Controlled();TextureView t=texture(1600,900);prefs.edit().putInt("cobra_player_aspect_mode",0).commit();bind(c,channel(1),t,true);put(a,"mAspectMode",10);
    call(a,"applyCobraAspectTransform");checkRect(t,1600,900);assertEquals(0,get(a,"mAspectMode"));
  }
  @Test public void channelResetUpdatesVisibleTransformAndPreservesTransport()throws Exception{
    Controlled c=new Controlled();TextureView t=texture(1600,900);Object ch=channel(0);mode(ch,3);bind(c,ch,t,true);call(a,"applyCobraAspectTransform");checkRect(t,1200,900);c.writes.clear();
    String key=(String)call(a,"cobraPreferenceKey",ch);Object p=call(a,"cobraReadPreferences",key);assertEquals(true,call(a,"cobraSavePreferences",ch,key,p,true));checkRect(t,1600,900);
    assertFalse(prefs.contains(key));assertFalse(c.writes.contains("prepare"));assertFalse(c.writes.contains("release"));assertFalse(c.writes.contains("setTrackSelectionParameters"));
  }
  @Test public void pausedFoldReflowKeepsPlayerAndUpdatesRealTransformAcrossInnerCoverAndRotation()throws Exception{
    Controlled c=new Controlled();c.requested=false;TextureView t=texture(1812,2176);Object ch=channel(0);mode(ch,12);bind(c,ch,t,true);c.writes.clear();
    for(int[] v:new int[][]{{904,2316},{2316,904},{1812,2176},{2176,1812},{800,500},{1812,2176}}){resize((View)t.getParent(),v[0],v[1]);call(a,"applyCobraAspectTransform");double[] e=expected(12,1920,1080,1f,v[0],v[1]);checkRect(t,e[0],e[1]);assertSame(c.player,get(a,"mPlayer"));}
    assertTrue("Geometry-only changes must not mutate the decoder/transport",c.writes.isEmpty());
  }
  @Test public void reportedVideoSizeChangeRecomputesPixelAspectWithoutReattachingSurface()throws Exception{
    Controlled c=new Controlled();TextureView t=texture(1600,900);Object b=bind(c,channel(0),t,true);c.writes.clear();
    c.size=new VideoSize(720,576,0,16f/15f);call(b,"onVideoSizeChanged",c.size);checkRect(t,1200,900);
    c.size=new VideoSize(1080,1920);call(b,"onVideoSizeChanged",c.size);checkRect(t,506.25,900);
    assertTrue(c.writes.isEmpty());
  }
  @Test public void pipUsesBestFitAndExitRestoresSelectedChannelGeometry()throws Exception{
    Controlled c=new Controlled();TextureView t=texture(1600,900);Object ch=channel(0);mode(ch,3);bind(c,ch,t,true);call(a,"applyCobraAspectTransform");checkRect(t,1200,900);
    put(a,"mInPictureInPicture",true);call(a,"applyCobraAspectTransform");checkRect(t,1600,900);
    put(a,"mInPictureInPicture",false);call(a,"applyCobraAspectTransform");checkRect(t,1200,900);assertEquals(3,call(a,"cobraChannelAspect",ch));
  }
  @Test public void previewDoesNotInheritFullscreenDefaultButRespectsChannelOverride()throws Exception{
    Controlled c=new Controlled();TextureView t=texture(1600,900);prefs.edit().putInt("cobra_player_aspect_mode",10).commit();Object ch=channel(0);Object b=bind(c,ch,t,false);call(a,"cobraFitBinding",b);checkRect(t,1600,900);
    String key=(String)call(a,"cobraPreferenceKey",ch);Object p=call(a,"cobraReadPreferences",key);put(p,"aspect",3);assertEquals(true,call(a,"cobraSavePreferences",ch,key,p,false));checkRect(t,1200,900);
  }
  @Test public void geometrySnapshotReportsActualMatrixAndExplicitVerificationBoundary()throws Exception{
    Controlled c=new Controlled();TextureView t=texture(1600,900);Object ch=channel(0);mode(ch,3);Object b=bind(c,ch,t,true);call(a,"applyCobraAspectTransform");
    JSONObject d=(JSONObject)call(a,"cobraDisplayGeometry",b);assertEquals(3,d.getInt("selected_mode"));assertEquals(3,d.getInt("effective_mode"));assertEquals(1600,d.getInt("viewport_width"));assertEquals(900,d.getInt("viewport_height"));
    assertEquals(1200,d.getJSONArray("transformed_bounds").getDouble(2)-d.getJSONArray("transformed_bounds").getDouble(0),.02);
    assertEquals("texture_matrix_not_rendered_frame",d.getString("observation"));assertFalse(d.getBoolean("physical_device_verified"));assertEquals(9,d.getJSONArray("texture_matrix").length());
  }
  @Test public void captionsTrackTheVideoPaneWhenDrawerResizesFullscreen()throws Exception{
    Controlled c=new Controlled();TextureView t=texture(1600,900);Object b=bind(c,channel(0),t,true);
    View captions=(View)get(b,"captions");captions.setVisibility(View.VISIBLE);FrameLayout root=(FrameLayout)t.getParent();
    FrameLayout drawer=new FrameLayout(a);root.addView(drawer,new FrameLayout.LayoutParams(1,1));put(a,"mCobraPlayerDrawer",drawer);c.writes.clear();
    call(a,"cobraLayoutPlayerPanels");for(int i=0;i<3;i++)resize(root,1600,900);
    assertEquals(1170,t.getWidth());assertEquals(t.getLeft(),captions.getLeft());assertEquals(t.getTop(),captions.getTop());assertEquals(t.getWidth(),captions.getWidth());assertEquals(t.getHeight(),captions.getHeight());
    put(a,"mCobraPlayerDrawer",null);root.removeView(drawer);call(a,"cobraLayoutPlayerPanels");for(int i=0;i<3;i++)resize(root,1600,900);
    assertEquals(1600,t.getWidth());assertEquals(t.getWidth(),captions.getWidth());assertSame(c.player,get(a,"mPlayer"));assertTrue(c.writes.isEmpty());
  }
  @Test public void captionBoundsAccountForParentPaddingAndNeverMoveAnotherContainer()throws Exception{
    Controlled c=new Controlled();TextureView t=texture(1600,900);Object b=bind(c,channel(0),t,true);
    View captions=(View)get(b,"captions");captions.setVisibility(View.VISIBLE);FrameLayout root=(FrameLayout)t.getParent();root.setPadding(20,30,40,50);
    for(int i=0;i<3;i++)resize(root,1600,900);call(a,"cobraFitBinding",b);resize(root,1600,900);
    assertEquals(t.getLeft(),captions.getLeft());assertEquals(t.getTop(),captions.getTop());assertEquals(t.getWidth(),captions.getWidth());assertEquals(t.getHeight(),captions.getHeight());
    root.removeView(captions);FrameLayout elsewhere=new FrameLayout(a);elsewhere.addView(captions,new FrameLayout.LayoutParams(123,45));
    call(a,"cobraFitBinding",b);assertSame(elsewhere,captions.getParent());assertEquals(123,captions.getLayoutParams().width);assertEquals(45,captions.getLayoutParams().height);
  }
}
