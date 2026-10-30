package com.projectinfinity.kodi;

import android.app.Application;
import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Rect;
import android.os.Looper;
import android.os.SystemClock;
import android.view.KeyEvent;
import android.view.MotionEvent;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import java.lang.reflect.*;
import java.time.Duration;
import java.util.*;
import androidx.media3.common.*;
import androidx.media3.exoplayer.ExoPlayer;
import org.junit.*;
import static org.junit.Assert.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.shadows.ShadowActivity;
import org.robolectric.shadows.ShadowChoreographer;

/** Actual native non-Pro preview controls. No Pro entry or Pro dispatcher.
 * Only fullscreen/menu/platform-PiP terminal boundaries are host spies.
 * This does not establish physical Fold, decoder, or Android PiP acceptance. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,
  qualifiers="w480dp-h900dp-port-mdpi",instrumentedPackages={"com.projectinfinity.kodi"},
  shadows={CobraNonProButtonDispatchTest.TerminalActions.class})
@LooperMode(LooperMode.Mode.PAUSED)
public class CobraNonProButtonDispatchTest {
  static final List<String> ENDPOINTS=new ArrayList<>();
  static final String[] MODES={"mobile","compact","cards","grid"};
  static final String[] GLYPHS={"fullscreen","pip","more"};
  static Object get(Object o,String n)throws Exception{Field f=o.getClass().getDeclaredField(n);f.setAccessible(true);return f.get(o);}
  static void set(Object o,String n,Object v)throws Exception{Field f=o.getClass().getDeclaredField(n);f.setAccessible(true);f.set(o,v);}
  static Object call(Object o,String n,Object...args)throws Exception{
    for(Method m:o.getClass().getDeclaredMethods())if(m.getName().equals(n)&&m.getParameterCount()==args.length){m.setAccessible(true);return m.invoke(o,args);}
    throw new NoSuchMethodException(n);
  }
  static Object construct(String n,Object...args)throws Exception{
    Class<?> type=Class.forName("com.projectinfinity.kodi.InfinityLiveActivity$"+n);
    for(Constructor<?> c:type.getDeclaredConstructors())if(c.getParameterCount()==args.length){c.setAccessible(true);return c.newInstance(args);}
    throw new NoSuchMethodException(n);
  }
  static void measure(View v,int w,int h){v.measure(View.MeasureSpec.makeMeasureSpec(w,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h,View.MeasureSpec.EXACTLY));v.layout(0,0,w,h);}
  @Before public void controlledFrames(){ShadowChoreographer.setPaused(true);ShadowChoreographer.setFrameDelay(Duration.ofMillis(16));}

  static final class Playback implements InvocationHandler {
    public Object invoke(Object p,Method m,Object[] args){
      String n=m.getName();
      if(n.equals("equals"))return p==args[0];if(n.equals("hashCode"))return System.identityHashCode(p);
      if(n.equals("getPlayWhenReady")||n.equals("isPlaying"))return true;
      if(n.equals("getPlaybackState"))return Player.STATE_READY;
      if(n.equals("getVolume"))return 1f;
      if(n.equals("getTrackSelectionParameters"))return TrackSelectionParameters.DEFAULT_WITHOUT_CONTEXT;
      if(n.equals("getCurrentTracks"))return Tracks.EMPTY;
      if(n.equals("getVideoSize"))return VideoSize.UNKNOWN;
      if(n.equals("getAudioAttributes"))return AudioAttributes.DEFAULT;
      if(n.equals("getPlaybackParameters"))return PlaybackParameters.DEFAULT;
      if(n.equals("getAvailableCommands"))return Player.Commands.EMPTY;
      if(n.equals("getApplicationLooper"))return Looper.getMainLooper();
      Class<?> t=m.getReturnType();if(t==boolean.class)return false;if(t==int.class)return 0;if(t==long.class)return 0L;if(t==float.class)return 0f;if(t==double.class)return 0d;return null;
    }
  }
  @Implements(value=InfinityLiveActivity.class,isInAndroidSdk=false,callThroughByDefault=true,looseSignatures=true)
  public static class TerminalActions extends ShadowActivity {
    @RealObject InfinityLiveActivity owner;
    @Implementation protected void promoteCobraPreviewToFullscreen(Object channel)throws Exception{
      ENDPOINTS.add("fullscreen");set(owner,"mPlayer",get(owner,"mCobraPreviewPlayer"));set(owner,"mPlayerOverlay",new FrameLayout(owner));
    }
    @Implementation protected void showCobraChannelActions(Object channel){ENDPOINTS.add("more");}
    @Implementation protected void enterCobraPictureInPicture(){ENDPOINTS.add("pip");}
  }
  static final class Fixture {
    final InfinityLiveActivity a;final FrameLayout root,preview;final LinearLayout row;
    final SharedPreferences prefs;final Object channel,player;
    String mode;int width,height;
    Fixture(String initialMode,int w,int h)throws Exception{
      RuntimeEnvironment.setQualifiers("w"+w+"dp-h"+h+"dp-"+(w>=h?"land":"port")+"-mdpi");
      ActivityController<InfinityLiveActivity> controller=Robolectric.buildActivity(InfinityLiveActivity.class);a=controller.get();
      a.setTheme(android.R.style.Theme_Material_NoActionBar);
      prefs=a.getSharedPreferences("cobra-native-nonpro-"+UUID.randomUUID(),Context.MODE_PRIVATE);
      prefs.edit().putString("cobra_appearance_mode","dark").commit();set(a,"mPrefs",prefs);
      set(a,"mTheme",construct("Theme"));set(a,"mUi",construct("UiContract"));
      set(a,"mFeatures",new InfinityCobraFeatureRuntime(a));
      set(a,"mCobraPreviewAutoplayAllowed",false);set(a,"mCobraGuideDetails",new LinearLayout(a));
      mode(initialMode);
      channel=construct("Channel","nonpro-qa","Synthetic non-Pro QA","Group","epg","","https://example.invalid/nonpro","source",Collections.emptyMap());
      set(a,"mGuidePreviewChannel",channel);((List)get(a,"mChannels")).add(channel);
      preview=(FrameLayout)call(a,"cobraPreviewPanel",channel,false);row=preview.findViewWithTag("cobra_preview_controls");
      root=new FrameLayout(a);root.addView(preview,new FrameLayout.LayoutParams(w,240));a.setContentView(root);
      player=Proxy.newProxyInstance(ExoPlayer.class.getClassLoader(),new Class<?>[]{ExoPlayer.class},new Playback());
      ready();controller.visible();Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(400));layout(w,h);
      assertEquals("native touch preview includes separate PiP view",7,row.getChildCount());
      assertEquals("ordinary LinearLayout, not a Pro Hero",LinearLayout.class,row.getClass());
      assertNull(get(a,"mCobraProHeroUi"));assertNonPro();
    }
    void mode(String value)throws Exception{mode=value;prefs.edit().putString("guide_view_mode",value).commit();set(a,"mCobraGuideStyle",value);set(a,"mCobraProActive",false);}
    void assertNonPro()throws Exception{assertEquals(mode,get(a,"mCobraGuideStyle"));assertEquals(false,get(a,"mCobraProActive"));assertEquals(mode,prefs.getString("guide_view_mode",""));assertEquals(false,call(get(a,"mCobraSix"),"pro"));}
    void ready()throws Exception{
      set(a,"mPlayerOverlay",null);set(a,"mPlayer",null);set(a,"mMultiOverlay",null);
      set(a,"mGuidePreviewChannel",channel);set(a,"mCobraPreviewPlayer",player);
      set(a,"mCobraPreviewSessionKey",call(a,"cobraChannelKey",channel));set(a,"mCobraPlayerLocked",false);
      row.setVisibility(View.VISIBLE);ENDPOINTS.clear();assertNonPro();
    }
    void layout(int w,int h)throws Exception{
      width=w;height=h;preview.setLayoutParams(new FrameLayout.LayoutParams(w,Math.min(240,h-40)));
      measure(a.getWindow().getDecorView(),w,h);measure(root,w,h);assertNonPro();
    }
    View target(String glyph)throws Exception{
      View found=null;
      for(int i=0;i<row.getChildCount();i++){View v=row.getChildAt(i);if(glyph.equals(get(v,"glyph"))){assertNull("duplicate native glyph",found);found=v;}}
      assertNotNull(glyph,found);assertTrue(found.hasOnClickListeners());return found;
    }
    String geometry(View view){StringBuilder s=new StringBuilder();for(View v=view;v!=null;v=v.getParent() instanceof View?(View)v.getParent():null)s.append(v.getClass().getSimpleName()).append(" ").append(v.getWidth()).append("x").append(v.getHeight()).append(" measured=").append(v.getMeasuredWidth()).append("x").append(v.getMeasuredHeight()).append(" vis=").append(v.getVisibility()).append(" at=").append(v.getLeft()).append(",").append(v.getTop()).append(" attached=").append(v.isAttachedToWindow()).append(" | ");return s.toString();}
    void press(String glyph,boolean remote)throws Exception{
      ready();layout(width,height);View view=target(glyph);
      assertEquals(glyph,get(view,"glyph"));assertEquals(View.VISIBLE,view.getVisibility());assertTrue(view.isEnabled());
      Rect box=new Rect();assertTrue("actual visible target bounds: "+geometry(view),view.getGlobalVisibleRect(box));assertTrue(box.width()>8&&box.height()>8);
      if(remote){
        view.setFocusableInTouchMode(true);assertTrue(view.requestFocus());long t=SystemClock.uptimeMillis();
        assertTrue(root.dispatchKeyEvent(new KeyEvent(t,t,KeyEvent.ACTION_DOWN,KeyEvent.KEYCODE_DPAD_CENTER,0)));
        assertTrue(root.dispatchKeyEvent(new KeyEvent(t,t+16,KeyEvent.ACTION_UP,KeyEvent.KEYCODE_DPAD_CENTER,0)));
      }else{
        int[] origin=new int[2];root.getLocationOnScreen(origin);float x=box.exactCenterX()-origin[0],y=box.exactCenterY()-origin[1];long t=SystemClock.uptimeMillis();
        for(int action:new int[]{MotionEvent.ACTION_DOWN,MotionEvent.ACTION_UP}){MotionEvent e=MotionEvent.obtain(t,t+(action==MotionEvent.ACTION_UP?32:0),action,x,y,0);try{assertTrue(root.dispatchTouchEvent(e));}finally{e.recycle();}}
      }
      Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(32));assertNonPro();
      List<String> expected=glyph.equals("pip")?Arrays.asList("fullscreen","pip"):Arrays.asList(glyph);
      System.out.println("COBRA_NONPRO_NATIVE_BUTTON mode="+mode+" glyph="+glyph+" index="+row.indexOfChild(view)+" bounds="+box+" via="+(remote?"remote":"coordinate")+" endpoints="+ENDPOINTS+" Pro=false");
      assertEquals("one visible native "+mode+" "+glyph+" press",expected,new ArrayList<>(ENDPOINTS));
      if(glyph.equals("more"))assertSame(player,get(a,"mCobraPreviewPlayer"));else assertSame(player,get(a,"mPlayer"));
    }
  }
  @Test public void nativeCoordinatesInEveryNonProModeReachTheirOwnActions()throws Exception{
    for(String mode:MODES)for(String glyph:GLYPHS)new Fixture(mode,480,900).press(glyph,false);
  }
  @Test public void reusedNativePreviewAcrossNonProModesKeepsViewAndListenerIdentity()throws Exception{
    Fixture f=new Fixture("mobile",480,900);Map<String,View> original=new LinkedHashMap<>();for(String glyph:GLYPHS)original.put(glyph,f.target(glyph));
    for(String mode:new String[]{"compact","cards","grid","mobile"}){
      f.mode(mode);assertSame(f.preview,call(f.a,"cobraPreviewPanel",f.channel,false));
      for(String glyph:GLYPHS){assertSame(original.get(glyph),f.target(glyph));f.press(glyph,false);}
    }
  }
  @Test public void nativeNarrowWideAndRemoteTargetsRemainModeOwned()throws Exception{
    for(String mode:MODES)for(int[] size:new int[][]{{280,700},{720,420}}){
      // Separate attached windows match the actual display configuration. A
      // manual root.measure alone cannot resize an existing ViewRoot window.
      Fixture f=new Fixture(mode,size[0],size[1]);
      for(String glyph:GLYPHS)f.press(glyph,false);
      if(size[0]==720)for(String glyph:GLYPHS)f.press(glyph,true);
    }
  }
}
