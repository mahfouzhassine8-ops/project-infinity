package com.projectinfinity.kodi;

import android.app.Application;
import android.content.Context;
import android.content.pm.ActivityInfo;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.TextView;
import androidx.media3.common.Format;
import androidx.media3.common.Player;
import androidx.media3.exoplayer.ExoPlayer;
import java.lang.reflect.*;
import java.util.concurrent.TimeUnit;
import org.json.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** 2103162: one Theme setting + reversible built-in/custom switch + Cobra player rotation. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103162ThemeRotationTest {
  CobraNavigationUiTest ui; Context app;
  @Before public void before(){
    app=RuntimeEnvironment.getApplication();
    CobraVisualRenderer.loading.set(true);CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer.clients.clear();
    CobraVisualTheme.deleteTree(CobraVisualTheme.store(app));
    ui=new CobraNavigationUiTest();ui.clock();
  }
  @After public void after(){
    CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer.clients.clear();CobraVisualTheme.deleteTree(CobraVisualTheme.store(app));
  }
  Object call(Object owner,String name,Object...args)throws Exception{
    Method found=null;
    for(Method m:owner.getClass().getDeclaredMethods())if(m.getName().equals(name)&&m.getParameterCount()==args.length){found=m;break;}
    if(found==null)throw new NoSuchMethodException(name);found.setAccessible(true);return found.invoke(owner,args);
  }
  void set(Object owner,String name,Object value)throws Exception{
    Field f=owner.getClass().getDeclaredField(name);f.setAccessible(true);f.set(owner,value);
  }
  View tag(android.app.Activity a,String value){return a.getWindow().getDecorView().findViewWithTag(value);}
  TextView findText(View v,String text){
    if(v instanceof TextView&&text.contentEquals(((TextView)v).getText()))return (TextView)v;
    if(v instanceof ViewGroup){ViewGroup g=(ViewGroup)v;for(int i=0;i<g.getChildCount();i++){TextView r=findText(g.getChildAt(i),text);if(r!=null)return r;}}
    return null;
  }
  View clickableAncestor(View v){
    View p=v;
    while(p!=null&&!p.isClickable()){android.view.ViewParent parent=p.getParent();p=parent instanceof View?(View)parent:null;}
    return p;
  }
  boolean await(java.util.concurrent.Callable<Boolean> condition)throws Exception{
    long end=System.nanoTime()+TimeUnit.SECONDS.toNanos(3);
    while(System.nanoTime()<end){Shadows.shadowOf(android.os.Looper.getMainLooper()).idle();if(condition.call())return true;Thread.sleep(10);}
    return false;
  }
  JSONObject node(String slot,int x,int y,int w,int h)throws Exception{return new JSONObject().put("id",slot).put("type","slot").put("slot",slot).put("rect",new JSONArray(java.util.Arrays.asList(x,y,w,h)));}
  JSONObject theme(String id)throws Exception{
    JSONObject scene=new JSONObject().put("width",412).put("height",915).put("nodes",new JSONArray()
      .put(node("enter.infinity",20,250,372,64)).put(node("settings.infinity",20,320,372,52))
      .put(node("enter.cobra",20,500,372,64)).put(node("settings.cobra",20,570,372,52)));
    return new JSONObject().put("schema",2).put("scope","cobra-presentation").put("minimum_runtime",2).put("minimum_build",2103162)
      .put("id",id).put("name","Theme "+id).put("assets",new JSONObject()).put("base",new JSONObject().put("scenes",new JSONObject().put("chooser",scene)));
  }
  ExoPlayer fakeVideoPlayer(int[] state,boolean[] playWhenReady){
    return (ExoPlayer)Proxy.newProxyInstance(getClass().getClassLoader(),new Class[]{ExoPlayer.class},(proxy,method,args)->{
      String n=method.getName();
      if(n.equals("getVideoFormat"))return new Format.Builder().setSampleMimeType("video/avc").build();
      if(n.equals("getPlaybackState"))return state[0];
      if(n.equals("isPlaying"))return state[0]==Player.STATE_READY&&playWhenReady[0];
      if(n.equals("getPlayWhenReady"))return playWhenReady[0];
      Class<?> t=method.getReturnType();
      if(t==boolean.class)return false;if(t==int.class)return 0;if(t==long.class)return 0L;if(t==float.class)return 0f;if(t==double.class)return 0d;
      return null;
    });
  }

  @Test public void settingsUseOneThemeEntryAndNoLegacyThemeButtonStack()throws Exception{
    InfinityLiveActivity a=ui.fixture(24);try{
      call(a,"showSettings");ui.measure(a,412,915);
      View theme=tag(a,"cobra_theme_management");assertNotNull(theme);assertTrue(theme instanceof TextView);
      assertTrue(((TextView)theme).getText().toString().contains("BUILT-IN"));
      assertNotNull(tag(a,"cobra_background_mode"));
      assertNull(tag(a,"cobra_theme_install"));assertNull(tag(a,"cobra_visual_theme_state"));
      assertNull(tag(a,"cobra-visual-theme-controls:previous"));assertNull(tag(a,"cobra-visual-theme-controls:builtin"));
    }finally{ui.clean(a);}
  }

  @Test public void oneThemeSheetSwitchesToBuiltInThenBackToSameInstalledTheme()throws Exception{
    CobraVisualRuntimeTest harness=new CobraVisualRuntimeTest();harness.context=app;
    CobraVisualTheme installed=harness.install(theme("hm-test"));harness.activate(installed);
    InfinityLiveActivity a=ui.fixture(24);try{
      call(a,"showSettings");ui.measure(a,412,915);assertTrue(((TextView)tag(a,"cobra_theme_management")).getText().toString().contains("CUSTOM"));
      assertTrue(tag(a,"cobra_theme_management").performClick());ui.measure(a,412,915);
      TextView builtin=findText(a.getWindow().getDecorView(),"Built-in appearance");assertNotNull(builtin);
      View builtRow=clickableAncestor(builtin);assertNotNull(builtRow);assertTrue(builtRow.performClick());
      assertTrue(await(()->CobraVisualRenderer.active.id.equals("builtin")));
      assertTrue(CobraVisualTheme.readPointer(a).optString("active","").isEmpty());
      assertFalse(CobraVisualTheme.readPointer(a).optString("previous","").isEmpty());

      call(a,"showSettings");ui.measure(a,412,915);assertTrue(tag(a,"cobra_theme_management").performClick());ui.measure(a,412,915);
      TextView custom=findText(a.getWindow().getDecorView(),"Installed visual theme");assertNotNull(custom);
      View customRow=clickableAncestor(custom);assertNotNull(customRow);assertTrue(customRow.performClick());
      assertTrue(await(()->CobraVisualRenderer.active.id.equals("hm-test")));
      assertFalse(CobraVisualTheme.readPointer(a).optString("active","").isEmpty());
    }finally{ui.clean(a);}
  }


  @Test public void backgroundModeStillUsesTheExistingNormalExtendedContract()throws Exception{
    InfinityLiveActivity a=ui.fixture(24);try{
      a.getSharedPreferences("infinity_runtime",Context.MODE_PRIVATE).edit().putBoolean("extended_background",true).commit();
      call(a,"showSettings");ui.measure(a,412,915);
      TextView background=(TextView)tag(a,"cobra_background_mode");assertNotNull(background);assertTrue(background.getText().toString().contains("EXTENDED"));
      assertTrue(background.performClick());ui.measure(a,412,915);
      View normal=tag(a,"cobra-background-mode:normal");View extended=tag(a,"cobra-background-mode:extended");
      assertNotNull(normal);assertNotNull(extended);assertTrue(normal.performClick());
      assertFalse(InfinityExtendedBackgroundService.isEnabled(a));
      call(a,"showSettings");ui.measure(a,412,915);
      assertTrue(((TextView)tag(a,"cobra_background_mode")).getText().toString().contains("NORMAL"));
    }finally{InfinityExtendedBackgroundService.setEnabled(a,false);ui.clean(a);}
  }

  @Test public void chooserStillConsumesSystemBarInsets()throws Exception{
    CobraVisualRuntimeTest harness=new CobraVisualRuntimeTest();harness.context=app;harness.activate(harness.install(theme("safe-area")));
    ExperienceChooserUiTest.reflect();ExperienceChooserUiTest old=new ExperienceChooserUiTest();Splash a=old.activity();try{
      ExperienceChooserUiTest.chooser.invoke(a);View root=tag(a,"experience-themed-root");assertNotNull(root);
      android.view.WindowInsets insets=new android.view.WindowInsets.Builder()
          .setSystemWindowInsets(android.graphics.Insets.of(0,32,0,20)).build();
      root.dispatchApplyWindowInsets(insets);
      assertEquals(32,root.getPaddingTop());assertEquals(20,root.getPaddingBottom());
      assertEquals(0,root.getPaddingLeft());assertEquals(0,root.getPaddingRight());
      assertNotNull(tag(a,"experience-card-infinity"));assertNotNull(tag(a,"experience-card-cobra"));
    }finally{old.closeWindows();}
  }

  @Test public void playerChromeHasRotationBesideLockAndUsesSharedInfinityPreference()throws Exception{
    InfinityLiveActivity a=ui.fixture(24);try{
      FrameLayout overlay=new FrameLayout(a);a.setContentView(overlay);set(a,"mPlayerOverlay",overlay);
      overlay.measure(View.MeasureSpec.makeMeasureSpec(412,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(915,View.MeasureSpec.EXACTLY));overlay.layout(0,0,412,915);
      call(a,"cobraBuildPlayerChrome");
      View rotate=tag(a,"cobra_player_rotation");assertNotNull(rotate);
      assertTrue(rotate.getContentDescription().toString().contains("follows device"));
      assertEquals(0,a.getSharedPreferences("infinity_player_rotation",Context.MODE_PRIVATE).getInt("mode",0));
      assertTrue(rotate.performClick());
      assertEquals(1,a.getSharedPreferences("infinity_player_rotation",Context.MODE_PRIVATE).getInt("mode",0));
      assertTrue(rotate.getContentDescription().toString().contains("unlocked"));
      assertTrue(rotate.performClick());
      assertEquals(0,a.getSharedPreferences("infinity_player_rotation",Context.MODE_PRIVATE).getInt("mode",1));
    }finally{ui.clean(a);}
  }

  @Test public void unlockedRotationRequestsFullSensorOnlyForEligibleActiveVideo()throws Exception{
    InfinityLiveActivity a=ui.fixture(24);try{
      int[] state={Player.STATE_READY};boolean[] playWhenReady={true};
      FrameLayout overlay=new FrameLayout(a);a.setContentView(overlay);set(a,"mPlayerOverlay",overlay);set(a,"mPlayer",fakeVideoPlayer(state,playWhenReady));
      a.getSharedPreferences("infinity_player_rotation",Context.MODE_PRIVATE).edit().putInt("mode",1).commit();
      call(a,"cobraApplyPlayerRotation","test-active");
      assertEquals(ActivityInfo.SCREEN_ORIENTATION_FULL_SENSOR,a.getRequestedOrientation());
      state[0]=Player.STATE_ENDED;call(a,"cobraApplyPlayerRotation","test-ended");
      assertEquals(ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,a.getRequestedOrientation());
      state[0]=Player.STATE_READY;set(a,"mBackgroundStopped",true);call(a,"cobraApplyPlayerRotation","test-background");
      assertEquals(ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,a.getRequestedOrientation());
    }finally{ui.clean(a);}
  }
}
