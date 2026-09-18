package com.projectinfinity.kodi;

import android.app.Application;
import android.content.Context;
import android.os.Looper;
import android.view.View;
import android.view.WindowInsets;
import android.widget.TextView;
import java.util.concurrent.TimeUnit;
import org.json.JSONArray;
import org.json.JSONObject;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** 2103161 acceptance: visible theme recovery, restored Background Mode, and chooser safe area. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103161SettingsTest {
  CobraNavigationUiTest ui;
  Context app;
  @Before public void before(){
    app=RuntimeEnvironment.getApplication();
    CobraVisualRenderer.loading.set(true);CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer.clients.clear();
    CobraVisualTheme.deleteTree(CobraVisualTheme.store(app));
    ui=new CobraNavigationUiTest();ui.clock();
  }
  @After public void after(){
    CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer.clients.clear();CobraVisualTheme.deleteTree(CobraVisualTheme.store(app));
  }
  View tag(android.app.Activity a,String value){return a.getWindow().getDecorView().findViewWithTag(value);}
  TextView textTag(android.app.Activity a,String value){View v=tag(a,value);assertTrue(v instanceof TextView);return (TextView)v;}
  boolean await(java.util.concurrent.Callable<Boolean> condition)throws Exception{
    long end=System.nanoTime()+TimeUnit.SECONDS.toNanos(3);while(System.nanoTime()<end){Shadows.shadowOf(Looper.getMainLooper()).idle();if(condition.call())return true;Thread.sleep(10);}return false;
  }
  JSONObject node(String slot,int x,int y,int w,int h)throws Exception{return new JSONObject().put("id",slot.replace('.','-')).put("type","slot").put("slot",slot).put("rect",new JSONArray(java.util.Arrays.asList(x,y,w,h)));}
  JSONObject sceneTheme(String id)throws Exception{
    JSONObject scene=new JSONObject().put("width",412).put("height",915).put("nodes",new JSONArray()
      .put(node("enter.infinity",20,250,372,64)).put(node("settings.infinity",20,320,372,52))
      .put(node("enter.cobra",20,500,372,64)).put(node("settings.cobra",20,570,372,52)));
    return new JSONObject().put("schema",2).put("scope","cobra-presentation").put("minimum_runtime",2).put("minimum_build",2103161)
      .put("id",id).put("name","Theme "+id).put("assets",new JSONObject()).put("base",new JSONObject().put("scenes",new JSONObject().put("chooser",scene)));
  }
  @Test public void settingsExposeBackgroundAndThemeManagementNearTop()throws Exception{
    InfinityLiveActivity a=ui.fixture(24);try{
      CobraNavigationUiTest.call(a,"showSettings");ui.measure(a,412,915);
      assertNotNull(tag(a,"cobra_theme_install"));assertNotNull(tag(a,"cobra_background_mode"));assertNotNull(tag(a,"cobra_visual_theme_state"));
      assertNotNull(tag(a,"cobra-visual-theme-controls:previous"));assertNotNull(tag(a,"cobra-visual-theme-controls:builtin"));
      assertTrue(textTag(a,"cobra_background_mode").getText().toString().contains("NORMAL"));
      assertTrue(textTag(a,"cobra_visual_theme_state").getText().toString().toLowerCase(java.util.Locale.ROOT).contains("builtin"));
    }finally{InfinityExtendedBackgroundService.setEnabled(a,false);ui.clean(a);}
  }
  @Test public void backgroundModeUsesExistingExtendedBackgroundPreferenceAndNormalDisablesIt()throws Exception{
    InfinityLiveActivity a=ui.fixture(24);try{
      a.getSharedPreferences("infinity_runtime",Context.MODE_PRIVATE).edit().putBoolean("extended_background",true).commit();
      CobraNavigationUiTest.call(a,"showSettings");ui.measure(a,412,915);assertTrue(textTag(a,"cobra_background_mode").getText().toString().contains("EXTENDED"));
      assertTrue(tag(a,"cobra_background_mode").performClick());ui.measure(a,412,915);View normal=tag(a,"cobra-background-mode:normal");View extended=tag(a,"cobra-background-mode:extended");assertNotNull(normal);assertNotNull(extended);
      assertTrue(normal.performClick());assertFalse(InfinityExtendedBackgroundService.isEnabled(a));
      CobraNavigationUiTest.call(a,"showSettings");ui.measure(a,412,915);assertTrue(textTag(a,"cobra_background_mode").getText().toString().contains("NORMAL"));
    }finally{InfinityExtendedBackgroundService.setEnabled(a,false);ui.clean(a);}
  }
  @Test @Config(sdk=28,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi") public void extendedBackgroundRowRequestsTheExistingServicePreference()throws Exception{
    InfinityLiveActivity a=ui.fixture(24);try{
      InfinityExtendedBackgroundService.setEnabled(a,false);CobraNavigationUiTest.call(a,"showCobraBackgroundModePicker");ui.measure(a,412,915);View extended=tag(a,"cobra-background-mode:extended");assertNotNull(extended);assertTrue(extended.performClick());
      assertTrue("Extended row must use the existing Infinity runtime preference",InfinityExtendedBackgroundService.isEnabled(a));
    }finally{InfinityExtendedBackgroundService.setEnabled(a,false);ui.clean(a);}
  }
  @Test public void visibleBuiltInRecoveryActuallyClearsAnInstalledVisualTheme()throws Exception{
    CobraVisualRuntimeTest theme=new CobraVisualRuntimeTest();theme.context=app;CobraVisualTheme installed=theme.install(sceneTheme("recovery-test"));theme.activate(installed);
    InfinityLiveActivity a=ui.fixture(24);try{
      CobraNavigationUiTest.call(a,"showSettings");ui.measure(a,412,915);assertTrue(textTag(a,"cobra_visual_theme_state").getText().toString().contains("recovery-test"));
      View reset=tag(a,"cobra-visual-theme-controls:builtin");assertNotNull(reset);assertTrue(reset.performClick());
      assertTrue("Built-in reset must complete",await(()->CobraVisualRenderer.active.id.equals("builtin")));
      assertTrue(CobraVisualTheme.readPointer(a).optString("active","").isEmpty());
    }finally{ui.clean(a);}
  }
  @Test public void chooserConsumesSystemBarInsetsBeforeLayingOutThemeScene()throws Exception{
    CobraVisualRuntimeTest theme=new CobraVisualRuntimeTest();theme.context=app;theme.activate(theme.install(sceneTheme("safe-area")));
    ExperienceChooserUiTest.reflect();ExperienceChooserUiTest old=new ExperienceChooserUiTest();Splash a=old.activity();try{
      old.show(a,false,412,915);View root=tag(a,"experience-themed-root");assertNotNull(root);
      WindowInsets insets=new WindowInsets.Builder().setSystemWindowInsets(android.graphics.Insets.of(0,32,0,20)).build();root.dispatchApplyWindowInsets(insets);
      assertEquals(32,root.getPaddingTop());assertEquals(20,root.getPaddingBottom());assertEquals(0,root.getPaddingLeft());assertEquals(0,root.getPaddingRight());
      assertNotNull(tag(a,"experience-card-infinity"));assertNotNull(tag(a,"experience-card-cobra"));
    }finally{old.closeWindows();}
  }
}
