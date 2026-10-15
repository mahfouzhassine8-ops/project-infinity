package com.projectinfinity.kodi;

import android.app.*;
import android.content.*;
import android.graphics.*;
import android.graphics.drawable.*;
import android.os.*;
import android.view.*;
import android.widget.*;
import java.io.*;
import java.lang.reflect.*;
import java.nio.charset.StandardCharsets;
import java.util.zip.*;
import org.json.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.shadows.ShadowAlertDialog;
import static org.junit.Assert.*;

/** Supersedes the old assumption that the painted background and safe-area root are the
 * same view. 2103175 intentionally splits them: full-window wallpaper below, inset content above. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w717dp-h917dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103175FullscreenBackgroundTest {
  CobraNavigationUiTest ui; InfinityLiveActivity a;
  ExperienceChooserUiTest chooser; CobraVisualRuntimeTest visual;
  Context context;

  static Object get(Object o,String name)throws Exception{
    for(Class<?> c=o.getClass();c!=null;c=c.getSuperclass()){
      try{Field f=c.getDeclaredField(name);f.setAccessible(true);return f.get(o);}
      catch(NoSuchFieldException ignored){}
    }
    throw new NoSuchFieldException(name);
  }
  static void set(Object o,String name,Object value)throws Exception{
    for(Class<?> c=o.getClass();c!=null;c=c.getSuperclass()){
      try{Field f=c.getDeclaredField(name);f.setAccessible(true);f.set(o,value);return;}
      catch(NoSuchFieldException ignored){}
    }
    throw new NoSuchFieldException(name);
  }
  static Object call(Object o,String name,Object...args)throws Exception{
    for(Class<?> c=o.getClass();c!=null;c=c.getSuperclass())for(Method m:c.getDeclaredMethods())
      if(m.getName().equals(name)&&m.getParameterCount()==args.length){
        m.setAccessible(true);
        try{return m.invoke(o,args);}
        catch(InvocationTargetException e){
          Throwable cause=e.getCause();
          if(cause instanceof Exception)throw (Exception)cause;
          throw new AssertionError(cause);
        }
      }
    throw new NoSuchMethodException(name);
  }
  void idle(){Shadows.shadowOf(Looper.getMainLooper()).idle();}
  void ensureBrowse()throws Exception{
    if(a!=null)return;
    ui=new CobraNavigationUiTest();ui.clock();a=ui.fixture(24);idle();
  }
  View browseRoot()throws Exception{ensureBrowse();return (View)get(a,"mRoot");}
  View browseBackground()throws Exception{ensureBrowse();return (View)get(a,"mCobraBrowseBackground");}
  int colorOf(View v){
    Drawable d=v.getBackground();assertTrue(d instanceof ColorDrawable);
    return ((ColorDrawable)d).getColor();
  }
  WindowInsets insets(int top,int bottom){
    return new WindowInsets.Builder().setInsets(WindowInsets.Type.systemBars(),Insets.of(0,top,0,bottom)).build();
  }
  View tag(Activity activity,String name){return activity.getWindow().getDecorView().findViewWithTag(name);}

  byte[] zip(JSONObject root)throws Exception{
    ByteArrayOutputStream out=new ByteArrayOutputStream();
    try(ZipOutputStream z=new ZipOutputStream(out)){
      z.putNextEntry(new ZipEntry(CobraVisualTheme.PREFIX+CobraVisualTheme.MANIFEST));
      z.write(root.toString().getBytes(StandardCharsets.UTF_8));z.closeEntry();
    }
    return out.toByteArray();
  }
  CobraVisualTheme screenTheme(String id,String fill)throws Exception{
    JSONObject root=new JSONObject()
      .put("schema",2).put("scope","cobra-presentation").put("minimum_runtime",2).put("minimum_build",2103160)
      .put("id",id).put("name","screen "+id).put("assets",new JSONObject())
      .put("base",new JSONObject()
        .put("colors",new JSONObject().put("palette.background",fill))
        .put("styles",new JSONObject().put("screen",new JSONObject().put("fill",fill))));
    return CobraVisualTheme.install(context,new ByteArrayInputStream(zip(root)));
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
  void installExperienceJson(Splash s,String background,String text)throws Exception{
    JSONObject root=new JSONObject().put("schema",1).put("scope","infinity-experience-chooser").put("minimum_bridge",1)
      .put("copy",new JSONObject().put("title","Choose Your Experience").put("initials","HM"))
      .put("palette",new JSONObject().put("background",background).put("text",text))
      .put("layout",new JSONObject());
    File file=chooser.themeFile(s);assertTrue(file.getParentFile().isDirectory()||file.getParentFile().mkdirs());
    try(FileOutputStream out=new FileOutputStream(file)){out.write(root.toString().getBytes(StandardCharsets.UTF_8));}
  }
  boolean lightStatusIcons(Activity activity){
    WindowInsetsController c=activity.getWindow().getInsetsController();assertNotNull(c);
    return (c.getSystemBarsAppearance()&WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS)!=0;
  }

  @Before public void before()throws Exception{
    context=RuntimeEnvironment.getApplication();
    CobraVisualRenderer.loading.set(true);CobraVisualTheme.deleteTree(CobraVisualTheme.store(context));
    CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer.clients.clear();
    chooser=new ExperienceChooserUiTest();ExperienceChooserUiTest.reflect();
    visual=new CobraVisualRuntimeTest();visual.context=context;
  }
  @After public void after(){
    try{if(a!=null&&ui!=null)ui.clean(a);}catch(Exception ignored){}
    try{chooser.closeWindows();}catch(Exception ignored){}
    try{visual.cleanup();}catch(Exception ignored){}
    CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer.clients.clear();
    CobraVisualTheme.deleteTree(CobraVisualTheme.store(context));
  }

  @Test public void browseBackdropAndSafeContentAreSeparateFullSizeLayers()throws Exception{
    ensureBrowse();
    ui.measure(a,717,917);View bg=browseBackground(),root=browseRoot();
    assertNotNull(bg);assertNotNull(root);assertNotSame(bg,root);
    assertEquals("cobra-browse-background",bg.getTag());assertEquals("cobra-browse-safe-content",root.getTag());
    assertEquals(root.getWidth(),bg.getWidth());assertEquals(root.getHeight(),bg.getHeight());
    assertEquals(Color.TRANSPARENT,colorOf(root));
  }

  @Test public void browseInsetsMoveOnlyForegroundNotWallpaper()throws Exception{
    ensureBrowse();
    View bg=browseBackground(),root=browseRoot();
    root.dispatchApplyWindowInsets(insets(46,24));idle();ui.measure(a,717,917);
    assertEquals(46,root.getPaddingTop());assertEquals(24,root.getPaddingBottom());
    assertEquals(0,bg.getPaddingTop());assertEquals(0,bg.getPaddingBottom());
    assertEquals(Color.TRANSPARENT,colorOf(root));
  }

  @Test public void browseThemeStillControlsStatusBarContrastWithoutPaintingRoot()throws Exception{
    ensureBrowse();
    CobraVisualTheme theme=screenTheme("light-fullscreen","#EEF3F8");CobraVisualRenderer.active=theme;
    call(a,"buildShell");idle();call(a,"cobraApplySystemBarsForSurface");idle();
    assertEquals(Color.parseColor("#EEF3F8"),(int)call(a,"cobraBrowseSystemBarSurfaceColor"));
    assertTrue(lightStatusIcons(a));
    assertEquals(Color.TRANSPARENT,a.getWindow().getStatusBarColor());
    assertEquals(Color.TRANSPARENT,colorOf(browseRoot()));
    assertNotNull(browseBackground().getBackground());
  }

  @Test public void shellRebuildPreservesBackgroundContentSplit()throws Exception{
    ensureBrowse();
    View oldBg=browseBackground(),oldRoot=browseRoot();call(a,"buildShell");idle();ui.measure(a,717,917);
    assertNotSame(oldBg,browseBackground());assertNotSame(oldRoot,browseRoot());
    browseRoot().dispatchApplyWindowInsets(insets(40,20));idle();
    assertEquals(40,browseRoot().getPaddingTop());assertEquals(0,browseBackground().getPaddingTop());
    assertEquals(Color.TRANSPARENT,colorOf(browseRoot()));
  }

  @Test public void fullscreenPlayerOwnershipIsUnchanged()throws Exception{
    ensureBrowse();
    FrameLayout overlay=new FrameLayout(a);set(a,"mPlayerOverlay",overlay);set(a,"mMultiOverlay",null);set(a,"mInPictureInPicture",false);
    call(a,"cobraApplySystemBarsForSurface");
    assertTrue((a.getWindow().getAttributes().flags&WindowManager.LayoutParams.FLAG_FULLSCREEN)!=0);
    assertEquals(Color.BLACK,a.getWindow().getStatusBarColor());
  }

  @Test public void visualChooserBackdropRemainsFullWindowWhileContentIsInset()throws Exception{
    installVisual("chooser-full","#F5F3FA","#102033");
    Splash s=chooser.activity();chooser.show(s,false,412,915);chooser.layout(s,412,915);
    View root=tag(s,"experience-themed-root"),safe=tag(s,"experience-safe-content");assertNotNull(root);assertNotNull(safe);
    safe.dispatchApplyWindowInsets(insets(44,24));idle();chooser.layout(s,412,915);
    assertEquals(0,root.getPaddingTop());assertEquals(0,root.getPaddingBottom());
    assertEquals(44,safe.getPaddingTop());assertEquals(24,safe.getPaddingBottom());
    assertTrue(root instanceof ViewGroup);View backdrop=((ViewGroup)root).getChildAt(0);
    assertEquals(root.getWidth(),backdrop.getWidth());assertEquals(root.getHeight(),backdrop.getHeight());
  }

  @Test public void chooserTransientZeroInsetCannotMoveForegroundIntoStatusIcons()throws Exception{
    installVisual("chooser-zero","#F5F3FA","#102033");
    Splash s=chooser.activity();chooser.show(s,false,412,915);View root=tag(s,"experience-themed-root"),safe=tag(s,"experience-safe-content");
    safe.dispatchApplyWindowInsets(insets(43,23));idle();
    safe.dispatchApplyWindowInsets(new WindowInsets.Builder().setInsets(WindowInsets.Type.systemBars(),Insets.NONE).build());idle();
    assertEquals(0,root.getPaddingTop());assertEquals(43,safe.getPaddingTop());assertEquals(23,safe.getPaddingBottom());
  }

  @Test public void chooserSafeContentSupersedesLegacyRootInsetContract()throws Exception{
    installVisual("chooser-supersede","#F5F3FA","#102033");
    Splash s=chooser.activity();chooser.show(s,false,412,915);
    View root=tag(s,"experience-themed-root"),safe=tag(s,"experience-safe-content");
    assertNotNull(root);assertNotNull(safe);
    safe.dispatchApplyWindowInsets(insets(32,18));idle();
    assertEquals("Wallpaper root must remain physically full-screen",0,root.getPaddingTop());
    assertEquals("Foreground chooser content must remain below status icons",32,safe.getPaddingTop());
    assertEquals(18,safe.getPaddingBottom());
  }

  @Test public void styledFallbackUsesSameFullBackgroundSafeForegroundContract()throws Exception{
    Splash s=chooser.activity();installExperienceJson(s,"#F0F2F7","#122033");
    ExperienceChooserUiTest.chooser.invoke(s);chooser.layout(s,412,915);
    View root=tag(s,"experience-themed-root"),safe=tag(s,"experience-safe-content");assertNotNull(root);assertNotNull(safe);
    safe.dispatchApplyWindowInsets(insets(42,20));idle();
    assertEquals(0,root.getPaddingTop());assertEquals(42,safe.getPaddingTop());
    assertNotNull(tag(s,"experience-title"));assertNotNull(tag(s,"experience-initials"));
  }

  @Test public void chooserLightDarkAndOledKeepCorrectStatusIconContrast()throws Exception{
    String[][] cases={{"light","#F5F3FA","#102033","true"},{"dark","#0A1020","#F5F7FF","false"},{"oled","#000000","#FFFFFF","false"}};
    for(String[] c:cases){
      chooser.closeWindows();CobraVisualTheme.deleteTree(CobraVisualTheme.store(context));CobraVisualRenderer.active=CobraVisualTheme.builtin();
      installVisual("chooser-"+c[0],c[1],c[2]);Splash s=chooser.activity();chooser.show(s,false,412,915);
      assertEquals(Boolean.parseBoolean(c[3]),lightStatusIcons(s));assertEquals(Color.TRANSPARENT,s.getWindow().getStatusBarColor());
      assertEquals(0,tag(s,"experience-themed-root").getPaddingTop());
    }
  }

  @Test public void chooserSettingsDialogCannotRestoreBlackBand()throws Exception{
    installVisual("chooser-dialog","#F5F3FA","#102033");Splash s=chooser.activity();chooser.show(s,false,412,915);
    View settings=tag(s,"experience-settings-cobra");assertNotNull(settings);assertTrue(settings.performClick());
    AlertDialog dialog=ShadowAlertDialog.getLatestAlertDialog();assertNotNull(dialog);
    assertEquals(Color.TRANSPARENT,s.getWindow().getStatusBarColor());assertEquals(0,tag(s,"experience-themed-root").getPaddingTop());
    dialog.dismiss();
  }

  @Test public void corruptThemeStillUsesUntouchedLegacyFallback()throws Exception{
    Splash s=chooser.activity();File file=chooser.themeFile(s);assertTrue(file.getParentFile().isDirectory()||file.getParentFile().mkdirs());
    try(FileOutputStream out=new FileOutputStream(file)){out.write("{broken".getBytes(StandardCharsets.UTF_8));}
    ExperienceChooserUiTest.chooser.invoke(s);chooser.layout(s,412,915);
    assertNull(tag(s,"experience-themed-root"));assertNull(tag(s,"experience-safe-content"));
    assertEquals(0,s.getWindow().getDecorView().getSystemUiVisibility()&View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN);
  }
}
