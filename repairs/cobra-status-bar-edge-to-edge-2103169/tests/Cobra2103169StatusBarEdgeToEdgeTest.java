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
import java.util.*;
import java.util.zip.*;
import org.json.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w717dp-h917dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103169StatusBarEdgeToEdgeTest {
  CobraNavigationUiTest ui;
  InfinityLiveActivity a;
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

  byte[] zip(JSONObject root)throws Exception{
    ByteArrayOutputStream out=new ByteArrayOutputStream();
    try(ZipOutputStream z=new ZipOutputStream(out)){
      z.putNextEntry(new ZipEntry(CobraVisualTheme.PREFIX+CobraVisualTheme.MANIFEST));
      z.write(root.toString().getBytes(StandardCharsets.UTF_8));
      z.closeEntry();
    }
    return out.toByteArray();
  }
  CobraVisualTheme screenTheme(String id,String fill)throws Exception{
    JSONObject root=new JSONObject()
        .put("schema",2).put("scope","cobra-presentation")
        .put("minimum_runtime",2).put("minimum_build",2103160)
        .put("id",id).put("name","Status bar "+id)
        .put("assets",new JSONObject())
        .put("base",new JSONObject().put("styles",
            new JSONObject().put("screen",new JSONObject().put("fill",fill))));
    return CobraVisualTheme.install(context,new ByteArrayInputStream(zip(root)));
  }
  void persistBeforeRendererPublication(CobraVisualTheme theme){
    assertNotNull(theme);
    CobraVisualRenderer.active=CobraVisualTheme.builtin();
    Shadows.shadowOf(Looper.getMainLooper()).idle();
    assertEquals("Test must exercise persistent-manifest fallback before renderer publication",
        "builtin",CobraVisualRenderer.active.id);
  }
  int rootColor()throws Exception{
    Drawable d=((View)get(a,"mRoot")).getBackground();
    assertTrue("Root band must be a concrete color after system-bar reconciliation",d instanceof ColorDrawable);
    return ((ColorDrawable)d).getColor();
  }

  @Before public void before()throws Exception{
    context=RuntimeEnvironment.getApplication();
    CobraVisualRenderer.loading.set(true);
    CobraVisualTheme.deleteTree(CobraVisualTheme.store(context));
    CobraVisualRenderer.active=CobraVisualTheme.builtin();
    CobraVisualRenderer.clients.clear();
    ui=new CobraNavigationUiTest();ui.clock();a=ui.fixture(24);
    Shadows.shadowOf(Looper.getMainLooper()).idle();
  }
  @After public void after()throws Exception{
    if(a!=null)ui.clean(a);
    CobraVisualRenderer.active=CobraVisualTheme.builtin();
    CobraVisualRenderer.clients.clear();
    CobraVisualTheme.deleteTree(CobraVisualTheme.store(context));
  }

  @Test public void customScreenFillOwnsTransparentBrowseStatusBarBand()throws Exception{
    int expected=Color.parseColor("#DCE5EF");
    persistBeforeRendererPublication(screenTheme("bar-light","#DCE5EF"));
    set(a,"mPlayerOverlay",null);set(a,"mMultiOverlay",null);set(a,"mInPictureInPicture",false);
    call(a,"cobraApplySystemBarsForSurface");
    assertEquals(expected,(int)call(a,"cobraBrowseSystemBarSurfaceColor"));
    assertEquals(Color.TRANSPARENT,a.getWindow().getStatusBarColor());
    assertEquals(expected,rootColor());
    assertTrue((((View)get(a,"mRoot")).getSystemUiVisibility()&View.SYSTEM_UI_FLAG_FULLSCREEN)==0);
  }

  @Test public void customLightScreenFillRequestsDarkStatusIcons()throws Exception{
    persistBeforeRendererPublication(screenTheme("bar-icons-light","#F1F4F8"));
    set(a,"mPlayerOverlay",null);set(a,"mMultiOverlay",null);set(a,"mInPictureInPicture",false);
    call(a,"cobraApplySystemBarsForSurface");
    int flags=a.getWindow().getDecorView().getSystemUiVisibility();
    assertTrue((flags&View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR)!=0);
  }

  @Test public void customDarkScreenFillKeepsLightStatusIcons()throws Exception{
    persistBeforeRendererPublication(screenTheme("bar-icons-dark","#101720"));
    set(a,"mPlayerOverlay",null);set(a,"mMultiOverlay",null);set(a,"mInPictureInPicture",false);
    call(a,"cobraApplySystemBarsForSurface");
    int flags=a.getWindow().getDecorView().getSystemUiVisibility();
    assertEquals(0,flags&View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR);
    assertEquals(Color.parseColor("#101720"),rootColor());
  }

  @Test public void confirmationCannotEraseAlreadyDeliveredSafeInset()throws Exception{
    set(a,"mPlayerOverlay",null);set(a,"mMultiOverlay",null);set(a,"mInPictureInPicture",false);
    View root=(View)get(a,"mRoot");
    WindowInsets delivered=new WindowInsets.Builder()
        .setInsets(WindowInsets.Type.systemBars(),android.graphics.Insets.of(0,44,0,24))
        .build();
    root.dispatchApplyWindowInsets(delivered);
    assertEquals(44,root.getPaddingTop());
    call(a,"cobraConfirmBrowseSystemBars");
    ui.frames(2);
    assertEquals("Posted status-bar confirmation must preserve the last delivered top inset",44,root.getPaddingTop());
    assertEquals(24,root.getPaddingBottom());
  }

  @Test public void browseUsesDrawableTransparentSystemBarWindow()throws Exception{
    persistBeforeRendererPublication(screenTheme("bar-window","#DCE5EF"));
    set(a,"mPlayerOverlay",null);set(a,"mMultiOverlay",null);set(a,"mInPictureInPicture",false);
    a.getWindow().addFlags(WindowManager.LayoutParams.FLAG_TRANSLUCENT_STATUS);
    call(a,"cobraApplySystemBarsForSurface");
    assertTrue((a.getWindow().getAttributes().flags&WindowManager.LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS)!=0);
    assertEquals(0,a.getWindow().getAttributes().flags&WindowManager.LayoutParams.FLAG_TRANSLUCENT_STATUS);
    assertEquals(Color.TRANSPARENT,a.getWindow().getStatusBarColor());
  }

  @Test @Config(sdk=29,application=Application.class,manifest=Config.NONE,qualifiers="w717dp-h917dp-port-mdpi")
  public void legacyBrowseLaysOutBehindVisibleStatusBar()throws Exception{
    set(a,"mPlayerOverlay",null);set(a,"mMultiOverlay",null);set(a,"mInPictureInPicture",false);
    call(a,"cobraApplySystemBarsForSurface");
    int flags=a.getWindow().getDecorView().getSystemUiVisibility();
    assertTrue((flags&View.SYSTEM_UI_FLAG_LAYOUT_STABLE)!=0);
    assertTrue((flags&View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN)!=0);
    assertEquals(0,flags&View.SYSTEM_UI_FLAG_FULLSCREEN);
    assertEquals(0,flags&View.SYSTEM_UI_FLAG_HIDE_NAVIGATION);
  }

  @Test public void fullscreenVideoStillOwnsBlackHiddenStatusBar()throws Exception{
    persistBeforeRendererPublication(screenTheme("bar-player","#DCE5EF"));
    FrameLayout overlay=new FrameLayout(a);
    set(a,"mPlayerOverlay",overlay);set(a,"mMultiOverlay",null);set(a,"mInPictureInPicture",false);
    call(a,"cobraApplySystemBarsForSurface");
    assertEquals(Color.BLACK,a.getWindow().getStatusBarColor());
    assertTrue((a.getWindow().getAttributes().flags&WindowManager.LayoutParams.FLAG_FULLSCREEN)!=0);
    assertTrue((a.getWindow().getDecorView().getSystemUiVisibility()&View.SYSTEM_UI_FLAG_FULLSCREEN)!=0);
  }
}
