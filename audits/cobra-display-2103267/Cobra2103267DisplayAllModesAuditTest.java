package com.projectinfinity.kodi;

import android.app.Application;
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

/** Full Cobra Display audit over the exact 2103267 Activity.
 * Uses controlled VideoSize metadata and the real TextureView matrix/UI code.
 * It does not claim physical-device decoder/GPU verification.
 */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w800dp-h600dp-land-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103267DisplayAllModesAuditTest {
  CobraNavigationUiTest ui; InfinityLiveActivity a; SharedPreferences prefs;
  static final float EPS=.03f;

  @Before public void before()throws Exception{
    CobraVisualRenderer.loading.set(true);CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer.clients.clear();
    ui=new CobraNavigationUiTest();ui.clock();a=ui.fixture(8);prefs=(SharedPreferences)get(a,"mPrefs");
  }
  @After public void after()throws Exception{ui.clean(a);CobraVisualRenderer.clients.clear();}
  static Object get(Object o,String n)throws Exception{return CobraNavigationUiTest.get(o,n);}
  static void put(Object o,String n,Object v)throws Exception{CobraNavigationUiTest.put(o,n,v);}
  static Object call(Object o,String n,Object...v)throws Exception{return CobraNavigationUiTest.call(o,n,v);}
  static Object construct(String n,Object...v)throws Exception{return CobraNavigationUiTest.construct(n,v);}

  final class Controlled implements InvocationHandler{
    VideoSize size=new VideoSize(1920,1080);boolean requested=true;
    final List<String>writes=new ArrayList<>();
    TrackSelectionParameters tracks=new TrackSelectionParameters.Builder(a).build();
    final ExoPlayer player=(ExoPlayer)Proxy.newProxyInstance(ExoPlayer.class.getClassLoader(),new Class<?>[]{ExoPlayer.class},this);
    public Object invoke(Object proxy,Method m,Object[]args){
      String n=m.getName();
      if(n.equals("hashCode"))return System.identityHashCode(proxy);
      if(n.equals("equals"))return proxy==args[0];
      if(n.equals("toString"))return "Controlled Display Audit Player";
      if(n.equals("getVideoSize"))return size;
      if(n.equals("getTrackSelectionParameters"))return tracks;
      if(n.equals("getCurrentTracks"))return Tracks.EMPTY;
      if(n.equals("getPlaybackState"))return Player.STATE_READY;
      if(n.equals("getPlaybackSuppressionReason"))return Player.PLAYBACK_SUPPRESSION_REASON_NONE;
      if(n.equals("getPlayWhenReady")||n.equals("isPlaying"))return requested;
      if(n.equals("getAudioAttributes"))return AudioAttributes.DEFAULT;
      if(n.equals("getVideoFormat"))return new Format.Builder().setWidth(size.width).setHeight(size.height).setSampleMimeType("video/avc").build();
      if(n.startsWith("set")||n.startsWith("clear")||n.equals("release")||n.equals("prepare")||n.equals("play")||n.equals("stop")||n.startsWith("seek"))writes.add(n);
      Class<?>t=m.getReturnType();if(t==boolean.class)return false;if(t==int.class)return 0;if(t==long.class)return 0L;if(t==float.class)return 0f;if(t==double.class)return 0d;return null;
    }
  }

  @SuppressWarnings("unchecked") Object channel(int index)throws Exception{return ((List<Object>)get(a,"mChannels")).get(index);}
  @SuppressWarnings("unchecked") Object bind(Controlled c,Object channel,TextureView t)throws Exception{
    Object b=construct("CobraPlayerBinding",a,c.player,channel);
    ((Map<ExoPlayer,Object>)get(a,"mCobraPlayerBindings")).put(c.player,b);
    put(a,"mPlaying",channel);put(a,"mPlayer",c.player);put(a,"mPlayerTexture",t);
    call(a,"cobraAttachVideo",c.player,t);return b;
  }
  TextureView texture(int w,int h)throws Exception{
    FrameLayout root=new FrameLayout(a);a.setContentView(root);TextureView t=new TextureView(a);root.addView(t,new FrameLayout.LayoutParams(-1,-1));put(a,"mPlayerOverlay",root);resize(root,w,h);return t;
  }
  void resize(View root,int w,int h){root.measure(View.MeasureSpec.makeMeasureSpec(w,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h,View.MeasureSpec.EXACTLY));root.layout(0,0,w,h);}
  RectF rendered(TextureView t){RectF r=new RectF(0,0,t.getWidth(),t.getHeight());t.getTransform(new Matrix()).mapRect(r);return r;}
  void rect(TextureView t,double w,double h){RectF r=rendered(t);assertEquals(w,r.width(),EPS);assertEquals(h,r.height(),EPS);assertEquals(t.getWidth()/2f,r.centerX(),EPS);assertEquals(t.getHeight()/2f,r.centerY(),EPS);}

  double[] expected(int mode,int sw,int sh,float par,int w,int h,double cx,double cy){
    double source=sw*(par>0?par:1f)/sh,view=w/(double)h;
    double sx=source<view?source/view:1.0,sy=source>view?view/source:1.0;
    if(mode==12){
      double smaller=Math.min(sx,sy);
      if(smaller<.78){
        double fillZoom=Math.max(1.0/sx,1.0/sy),cap=(view>=.65&&view<=1.35)?1.70:2.40,smart=Math.max(1.0,.78/Math.max(.0001,smaller));
        double z=Math.min(fillZoom,Math.min(cap,smart));sx*=z;sy*=z;
      }
    } else if(mode==13){
      double z=Math.max(1.0/sx,1.0/sy);sx*=z;sy*=z;
    } else {
      if(mode==2){source=16.0/9; sx=source<view?source/view:1;sy=source>view?view/source:1;}
      else if(mode==3){source=4.0/3; sx=source<view?source/view:1;sy=source>view?view/source:1;}
      if(mode==1){double z=Math.max(1.0/sx,1.0/sy);sx*=z;sy*=z;}
      else if(mode>=4&&mode<=6)sx*=new double[]{1.10,1.25,1.40}[mode-4];
      else if(mode==7){sx*=1.24;sy*=.84;}
      else if(mode>=8&&mode<=10){double z=new double[]{1.25,1.50,2.00}[mode-8];sx*=z;sy*=z;}
      else if(mode==11){sx*=Math.max(.55,Math.min(1.8,cx));sy*=Math.max(.55,Math.min(1.8,cy));}
    }
    return new double[]{w*sx,h*sy};
  }

  void saved(Object ch,int aspect,float x,float y)throws Exception{
    String key=(String)call(a,"cobraPreferenceKey",ch);
    prefs.edit().putString(key,new JSONObject().put("schema",1).put("aspect",aspect).put("x",x).put("y",y).toString()).commit();
  }

  void saveThroughOwner(Object ch,int aspect,float x,float y)throws Exception{
    String key=(String)call(a,"cobraPreferenceKey",ch);Object p=call(a,"cobraReadPreferences",key);
    put(p,"aspect",aspect);put(p,"x",x);put(p,"y",y);
    assertEquals(true,call(a,"cobraSavePreferences",ch,key,p,false));
  }

  @Test public void toolbarChannelDisplayContainsAllFifteenChoicesAndTruthfulSelection()throws Exception{
    Controlled c=new Controlled();TextureView t=texture(1600,900);Object ch=channel(0);prefs.edit().putInt("cobra_player_aspect_mode",3).commit();saved(ch,-1,1,1);bind(c,ch,t);
    int[] choices={12,13,-1,0,1,2,3,4,5,6,7,8,9,10,11};
    String[] labels={"Fold Fit","Fold Fill","Inherit default","Best Fit","Crop / Fill","16:9","4:3","Wide 1.10x","Wide 1.25x","Wide 1.40x","Short + Wide","Zoom 1.25x","Zoom 1.50x","Zoom 2.00x","Custom Width / Height"};
    for(int i=0;i<choices.length;i++){
      call(a,"cobraShowChannelAspect",ch);View decor=a.getWindow().getDecorView();
      for(int j=0;j<choices.length;j++){View row=decor.findViewWithTag("cobra-channel-aspect:"+choices[j]);assertNotNull(labels[j],row);assertEquals("selected state before click "+labels[j],choices[j]==(i==0?-1:choices[i-1]),row.isSelected());}
      View row=decor.findViewWithTag("cobra-channel-aspect:"+choices[i]);assertTrue("click "+labels[i],row.performClick());
      String key=(String)call(a,"cobraPreferenceKey",ch);JSONObject stored=new JSONObject(prefs.getString(key,""));assertEquals("persist "+labels[i],choices[i],stored.getInt("aspect"));
      int effective=(Integer)call(a,"cobraChannelAspect",ch);assertEquals("effective "+labels[i],choices[i]<0?3:choices[i],effective);
      assertEquals(effective,get(a,"mAspectMode"));
    }
    call(a,"cobraShowChannelAspect",ch);assertTrue(a.getWindow().getDecorView().findViewWithTag("cobra-channel-aspect:11").isSelected());
  }

  @Test public void everyGeometryModeMatchesItsDocumentedTransformAcrossRepresentativeScreens()throws Exception{
    Controlled c=new Controlled();TextureView t=texture(1812,2176);Object ch=channel(0);bind(c,ch,t);
    int[][] views={{1812,2176},{2176,1812},{904,2316},{2316,904},{412,915},{915,412},{1600,900},{900,1600}};
    int[][] sources={{1920,1080},{1440,1080},{720,576},{1080,1920},{3840,1600}};
    for(int[]v:views){resize((View)t.getParent(),v[0],v[1]);for(int[]s:sources)for(float par:new float[]{1f,16f/15f}){
      c.size=new VideoSize(s[0],s[1],0,par);
      prefs.edit().putFloat("cobra_custom_aspect_x",1.33f).putFloat("cobra_custom_aspect_y",.77f).commit();
      for(int mode=0;mode<=13;mode++){
        call(a,"cobraFitVideo",t,c.player,mode);double[]e=expected(mode,s[0],s[1],par,v[0],v[1],1.33,.77);rect(t,e[0],e[1]);
        RectF r=rendered(t);
        if(mode==0){assertTrue("Best Fit no crop",r.width()<=v[0]+EPS&&r.height()<=v[1]+EPS);}
        if(mode==1||mode==13){assertTrue("Fill covers viewport",r.width()+EPS>=v[0]&&r.height()+EPS>=v[1]);}
        if(mode==12){double[]fill=expected(13,s[0],s[1],par,v[0],v[1],1.33,.77);assertTrue(r.width()<=fill[0]+EPS&&r.height()<=fill[1]+EPS);}
      }
    }}
    assertFalse(c.writes.contains("prepare"));assertFalse(c.writes.contains("release"));assertFalse(c.writes.contains("seekTo"));
  }

  @Test public void switchingAnyDisplayModeClearsThePreviousTransform()throws Exception{
    Controlled c=new Controlled();TextureView t=texture(1812,2176);bind(c,channel(0),t);
    c.size=new VideoSize(1920,1080);
    int[] sequence={10,7,13,4,0,12,3,8,1,11,2,9,5,6,0};
    prefs.edit().putFloat("cobra_custom_aspect_x",1.66f).putFloat("cobra_custom_aspect_y",.61f).commit();
    for(int mode:sequence){call(a,"cobraFitVideo",t,c.player,mode);double[]e=expected(mode,1920,1080,1f,1812,2176,1.66,.61);rect(t,e[0],e[1]);}
    double[]best=expected(0,1920,1080,1f,1812,2176,1,1);RectF r=rendered(t);assertEquals(best[0],r.width(),EPS);assertEquals(best[1],r.height(),EPS);
  }

  @Test public void inheritUsesGlobalDefaultAndInvalidStateFallsBackSafely()throws Exception{
    Controlled c=new Controlled();TextureView t=texture(1600,900);Object ch=channel(0);prefs.edit().putInt("cobra_player_aspect_mode",3).commit();saved(ch,-1,1,1);bind(c,ch,t);call(a,"applyCobraAspectTransform");rect(t,1200,900);assertEquals(3,get(a,"mAspectMode"));
    prefs.edit().putInt("cobra_player_aspect_mode",99).commit();assertEquals(0,call(a,"cobraChannelAspect",ch));call(a,"applyCobraAspectTransform");rect(t,1600,900);
    String key=(String)call(a,"cobraPreferenceKey",ch);prefs.edit().putString(key,new JSONObject().put("schema",1).put("aspect",99).toString()).commit();assertEquals(0,call(a,"cobraChannelAspect",ch));
  }

  @Test public void customWidthHeightAreBoundedAndChannelScoped()throws Exception{
    Controlled c=new Controlled();TextureView t=texture(1600,900);Object ch=channel(0);saved(ch,11,1.33f,.77f);bind(c,ch,t);call(a,"applyCobraAspectTransform");rect(t,1600*1.33,900*.77);
    String key=(String)call(a,"cobraPreferenceKey",ch);
    saveThroughOwner(ch,11,99f,.01f);
    call(a,"applyCobraAspectTransform");rect(t,1600*1.8,900*.55);
  }

  @Test public void foldFitFoldFillReflowWithoutRestartAndPipReturnsToSelection()throws Exception{
    Controlled c=new Controlled();c.requested=false;TextureView t=texture(1812,2176);Object ch=channel(0);saved(ch,12,1,1);bind(c,ch,t);c.writes.clear();
    for(int mode:new int[]{12,13}){saveThroughOwner(ch,mode,1,1);for(int[]v:new int[][]{{1812,2176},{2176,1812},{904,2316},{2316,904},{900,1600},{1600,900}}){resize((View)t.getParent(),v[0],v[1]);call(a,"applyCobraAspectTransform");double[]e=expected(mode,1920,1080,1f,v[0],v[1],1,1);rect(t,e[0],e[1]);}}
    assertTrue("Display-only reflow cannot restart/prepare/seek/release",c.writes.isEmpty());
    saveThroughOwner(ch,10,1,1);resize((View)t.getParent(),1600,900);call(a,"applyCobraAspectTransform");rect(t,3200,1800);
    put(a,"mInPictureInPicture",true);call(a,"applyCobraAspectTransform");rect(t,1600,900);
    put(a,"mInPictureInPicture",false);call(a,"applyCobraAspectTransform");rect(t,3200,1800);assertEquals(10,call(a,"cobraChannelAspect",ch));
  }

  @Test public void videoSizeAndPixelAspectChangesRecomputeWithoutTransportMutation()throws Exception{
    Controlled c=new Controlled();TextureView t=texture(1600,900);Object ch=channel(0);saved(ch,0,1,1);Object b=bind(c,ch,t);c.writes.clear();
    c.size=new VideoSize(720,576,0,16f/15f);call(b,"onVideoSizeChanged",c.size);rect(t,1200,900);
    c.size=new VideoSize(1080,1920);call(b,"onVideoSizeChanged",c.size);rect(t,506.25,900);
    assertTrue(c.writes.isEmpty());
  }

  @Test public void geometryDiagnosticsReportSelectedEffectiveCropAndBars()throws Exception{
    Controlled c=new Controlled();TextureView t=texture(1600,900);Object ch=channel(0);saved(ch,3,1,1);Object b=bind(c,ch,t);call(a,"applyCobraAspectTransform");
    JSONObject g=(JSONObject)call(a,"cobraDisplayGeometry",b);assertEquals(3,g.getInt("selected_mode"));assertEquals(3,g.getInt("effective_mode"));assertEquals(1600,g.getInt("viewport_width"));assertEquals(900,g.getInt("viewport_height"));assertEquals(9,g.getJSONArray("texture_matrix").length());
    assertEquals(1200,g.getJSONArray("transformed_bounds").getDouble(2)-g.getJSONArray("transformed_bounds").getDouble(0),EPS);
    assertTrue(g.has("cropped_edges_pixels"));assertTrue(g.has("uncovered_edges_pixels"));assertEquals("texture_matrix_not_rendered_frame",g.getString("observation"));assertFalse(g.getBoolean("physical_device_verified"));
  }
}
