package com.projectinfinity.kodi;

import android.app.*;
import android.content.*;
import android.graphics.*;
import android.graphics.drawable.ColorDrawable;
import android.os.*;
import android.view.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import org.json.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.shadows.ShadowAlertDialog;
import static org.junit.Assert.*;

/** Chooser-window status-bar acceptance over the real production Splash.
 * No physical OEM SystemUI/Fold-panel claim is made by these tests. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103171ChooserStatusBarTest {
  ExperienceChooserUiTest chooser;
  CobraVisualRuntimeTest visual;

  @Before public void before()throws Exception{
    chooser=new ExperienceChooserUiTest();ExperienceChooserUiTest.reflect();
    visual=new CobraVisualRuntimeTest();visual.context=RuntimeEnvironment.getApplication();
    CobraVisualRenderer.loading.set(true);CobraVisualTheme.deleteTree(CobraVisualTheme.store(visual.context));
    CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer.clients.clear();
  }
  @After public void after(){
    try{chooser.closeWindows();}catch(Exception ignored){}
    try{visual.cleanup();}catch(Exception ignored){}
  }

  JSONObject node(String slot,int x,int y,int w,int h)throws Exception{
    return new JSONObject().put("id",slot.replace('.','-')).put("type","slot").put("slot",slot)
        .put("rect",new JSONArray(java.util.Arrays.asList(x,y,w,h)));
  }
  JSONObject scene()throws Exception{
    return new JSONObject().put("width",412).put("height",915).put("nodes",new JSONArray()
      .put(node("enter.infinity",28,300,168,90)).put(node("settings.infinity",28,402,168,54))
      .put(node("enter.cobra",216,300,168,90)).put(node("settings.cobra",216,402,168,54)));
  }
  void installVisual(String id,String background,String text)throws Exception{
    JSONObject data=visual.root(id);
    data.getJSONObject("base")
      .put("colors",new JSONObject().put("chooser.palette.background",background).put("chooser.palette.text",text))
      .put("scenes",new JSONObject().put("chooser",scene()));
    visual.activate(visual.install(data));
  }
  void installExperienceJson(Splash a,String background,String text)throws Exception{
    JSONObject root=new JSONObject().put("schema",1).put("scope","infinity-experience-chooser").put("minimum_bridge",1)
      .put("copy",new JSONObject().put("title","Choose Your Experience").put("initials","HM"))
      .put("palette",new JSONObject().put("background",background).put("text",text))
      .put("layout",new JSONObject());
    File file=chooser.themeFile(a);assertTrue(file.getParentFile().isDirectory()||file.getParentFile().mkdirs());
    try(FileOutputStream out=new FileOutputStream(file)){out.write(root.toString().getBytes(StandardCharsets.UTF_8));}
  }
  View root(Splash a){View v=chooser.tag(a,"experience-themed-root");assertNotNull(v);return v;}
  boolean lightStatusIcons(Splash a){
    WindowInsetsController c=a.getWindow().getInsetsController();assertNotNull(c);
    return (c.getSystemBarsAppearance()&WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS)!=0;
  }
  int decorColor(Splash a){
    assertTrue(a.getWindow().getDecorView().getBackground() instanceof ColorDrawable);
    return ((ColorDrawable)a.getWindow().getDecorView().getBackground()).getColor();
  }
  void assertWindow(Splash a,int background,boolean darkIcons)throws Exception{
    assertEquals(Color.TRANSPARENT,a.getWindow().getStatusBarColor());
    assertFalse(a.getWindow().isStatusBarContrastEnforced());
    assertEquals(0,a.getWindow().getAttributes().flags&WindowManager.LayoutParams.FLAG_FULLSCREEN);
    assertEquals(0,a.getWindow().getAttributes().flags&WindowManager.LayoutParams.FLAG_FORCE_NOT_FULLSCREEN);
    int flags=a.getWindow().getDecorView().getSystemUiVisibility();
    assertTrue((flags&View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN)!=0);
    assertTrue((flags&View.SYSTEM_UI_FLAG_LAYOUT_STABLE)!=0);
    assertEquals(darkIcons,lightStatusIcons(a));
    assertEquals(background,decorColor(a));
  }

  @Test public void lightVisualSceneUsesLightUnderlayAndDarkStatusIcons()throws Exception{
    int background=Color.parseColor("#F5F3FA");installVisual("chooser-light","#F5F3FA","#102033");
    Splash a=chooser.activity();chooser.show(a,false,412,915);
    assertWindow(a,background,true);
    assertNotNull(chooser.tag(a,"experience-card-infinity"));assertNotNull(chooser.tag(a,"experience-card-cobra"));
  }

  @Test public void darkVisualSceneUsesDarkUnderlayAndLightStatusIcons()throws Exception{
    int background=Color.parseColor("#0A1020");installVisual("chooser-dark","#0A1020","#F5F7FF");
    Splash a=chooser.activity();chooser.show(a,false,412,915);
    assertWindow(a,background,false);
  }

  @Test public void oledVisualSceneUsesTrueBlackUnderlayAndLightStatusIcons()throws Exception{
    installVisual("chooser-oled","#000000","#FFFFFF");
    Splash a=chooser.activity();chooser.show(a,false,412,915);
    assertWindow(a,Color.BLACK,false);
  }

  @Test public void styledFallbackAlsoReceivesChooserStatusPolicy()throws Exception{
    Splash a=chooser.activity();installExperienceJson(a,"#F0F2F7","#122033");
    ExperienceChooserUiTest.chooser.invoke(a);chooser.layout(a,412,915);
    assertWindow(a,Color.parseColor("#F0F2F7"),true);
    assertNotNull(root(a));
  }

  @Test public void transientZeroInsetsCannotPullBrandingUnderStatusIcons()throws Exception{
    installVisual("chooser-insets","#F5F3FA","#102033");
    Splash a=chooser.activity();chooser.show(a,false,412,915);View r=root(a);
    WindowInsets stable=new WindowInsets.Builder()
      .setInsets(WindowInsets.Type.systemBars(),Insets.of(0,44,0,24)).build();
    r.dispatchApplyWindowInsets(stable);Shadows.shadowOf(Looper.getMainLooper()).idle();
    assertEquals(44,r.getPaddingTop());assertEquals(24,r.getPaddingBottom());
    WindowInsets zero=new WindowInsets.Builder().setInsets(WindowInsets.Type.systemBars(),Insets.NONE).build();
    r.dispatchApplyWindowInsets(zero);Shadows.shadowOf(Looper.getMainLooper()).idle();
    assertEquals("Transient zero inset must not move Infinity/HM branding into the status area",44,r.getPaddingTop());
    assertEquals(24,r.getPaddingBottom());
  }

  @Test public void cardSettingsDialogCannotRestoreBlackStatusBand()throws Exception{
    installVisual("chooser-dialog","#F5F3FA","#102033");
    Splash a=chooser.activity();chooser.show(a,false,412,915);
    View settings=chooser.tag(a,"experience-settings-cobra");assertNotNull(settings);assertTrue(settings.performClick());
    AlertDialog dialog=ShadowAlertDialog.getLatestAlertDialog();assertNotNull(dialog);
    assertWindow(a,Color.parseColor("#F5F3FA"),true);
    dialog.dismiss();
  }

  @Test public void corruptThemeStillUsesUntouchedLegacyFallback()throws Exception{
    Splash a=chooser.activity();File file=chooser.themeFile(a);assertTrue(file.getParentFile().isDirectory()||file.getParentFile().mkdirs());
    try(FileOutputStream out=new FileOutputStream(file)){out.write("{broken".getBytes(StandardCharsets.UTF_8));}
    ExperienceChooserUiTest.chooser.invoke(a);chooser.layout(a,412,915);
    assertNull("Chooser repair must not replace the locked legacy fallback",chooser.tag(a,"experience-themed-root"));
    assertEquals("Legacy fallback remains outside the themed edge-to-edge policy",0,
        a.getWindow().getDecorView().getSystemUiVisibility()&View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN);
  }
}
