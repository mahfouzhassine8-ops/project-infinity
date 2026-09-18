package com.projectinfinity.kodi;

import android.app.*;
import android.graphics.Insets;
import android.os.*;
import android.view.*;
import android.widget.*;
import java.lang.reflect.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Window-level regression tests for the physical black status-bar band.
 * The inherited 2103168 surface tests verify the actual underlay color.
 * These tests verify the window does not block or scrim that underlay. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w717dp-h917dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103170StatusBarEdgeTest {
  CobraNavigationUiTest ui;
  InfinityLiveActivity a;

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
  View root()throws Exception{return (View)get(a,"mRoot");}
  int flags(){return a.getWindow().getDecorView().getSystemUiVisibility();}

  @Before public void before()throws Exception{
    CobraVisualRenderer.loading.set(true);
    CobraVisualRenderer.active=CobraVisualTheme.builtin();
    CobraVisualRenderer.clients.clear();
    ui=new CobraNavigationUiTest();ui.clock();a=ui.fixture(24);idle();
  }
  @After public void after()throws Exception{
    if(a!=null)ui.clean(a);
    CobraVisualRenderer.clients.clear();
  }

  @Test public void browseIsTransparentEdgeToEdgeNotForcedBelowStatusBar()throws Exception{
    set(a,"mPlayerOverlay",null);set(a,"mMultiOverlay",null);set(a,"mInPictureInPicture",false);
    a.getWindow().addFlags(WindowManager.LayoutParams.FLAG_FORCE_NOT_FULLSCREEN|WindowManager.LayoutParams.FLAG_FULLSCREEN);
    a.getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_HIDE_NAVIGATION|View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
    call(a,"cobraApplySystemBarsForSurface");
    int wf=a.getWindow().getAttributes().flags;
    assertEquals(0,wf&WindowManager.LayoutParams.FLAG_FULLSCREEN);
    assertEquals("Browse must not force a separate system-owned top band",0,wf&WindowManager.LayoutParams.FLAG_FORCE_NOT_FULLSCREEN);
    assertEquals(0,flags()&View.SYSTEM_UI_FLAG_FULLSCREEN);
    assertTrue("Browse decor must extend behind status bar",(flags()&View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN)!=0);
    assertTrue((flags()&View.SYSTEM_UI_FLAG_LAYOUT_STABLE)!=0);
  }

  @Test public void browseDisablesOemStatusContrastScrim()throws Exception{
    set(a,"mPlayerOverlay",null);set(a,"mMultiOverlay",null);set(a,"mInPictureInPicture",false);
    a.getWindow().setStatusBarContrastEnforced(true);
    call(a,"cobraApplySystemBarsForSurface");
    assertFalse("Transparent status bar must not receive an OEM/framework dark contrast scrim",
        a.getWindow().isStatusBarContrastEnforced());
    assertEquals(android.graphics.Color.TRANSPARENT,a.getWindow().getStatusBarColor());
  }

  @Test public void confirmationRepairsStaleFullscreenWithoutDestroyingEdgeToEdge()throws Exception{
    set(a,"mPlayerOverlay",null);set(a,"mMultiOverlay",null);set(a,"mInPictureInPicture",false);
    a.getWindow().addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN|WindowManager.LayoutParams.FLAG_FORCE_NOT_FULLSCREEN);
    a.getWindow().setStatusBarContrastEnforced(true);
    a.getWindow().getDecorView().setSystemUiVisibility(
        View.SYSTEM_UI_FLAG_FULLSCREEN|View.SYSTEM_UI_FLAG_HIDE_NAVIGATION|View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
    call(a,"cobraConfirmBrowseSystemBars");
    int wf=a.getWindow().getAttributes().flags;
    assertEquals(0,wf&WindowManager.LayoutParams.FLAG_FULLSCREEN);
    assertEquals(0,wf&WindowManager.LayoutParams.FLAG_FORCE_NOT_FULLSCREEN);
    assertTrue((flags()&View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN)!=0);
    assertFalse(a.getWindow().isStatusBarContrastEnforced());
  }

  @Test public void safeAreaStillMovesContentBelowVisibleStatusIcons()throws Exception{
    set(a,"mPlayerOverlay",null);set(a,"mMultiOverlay",null);set(a,"mInPictureInPicture",false);
    call(a,"cobraApplySystemBarsForSurface");
    WindowInsets insets=new WindowInsets.Builder()
        .setInsets(WindowInsets.Type.systemBars(),Insets.of(0,48,0,24))
        .build();
    root().dispatchApplyWindowInsets(insets);idle();
    assertEquals("Root padding protects controls while root background continues behind status bar",48,root().getPaddingTop());
    assertEquals(24,root().getPaddingBottom());
    assertTrue((flags()&View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN)!=0);
  }

  @Test public void pipNeverCreatesOpaqueBrowseBand()throws Exception{
    FrameLayout overlay=new FrameLayout(a);
    set(a,"mPlayerOverlay",overlay);set(a,"mMultiOverlay",null);set(a,"mInPictureInPicture",true);
    a.getWindow().addFlags(WindowManager.LayoutParams.FLAG_FORCE_NOT_FULLSCREEN);
    a.getWindow().setStatusBarContrastEnforced(true);
    call(a,"cobraApplySystemBarsForSurface");
    int wf=a.getWindow().getAttributes().flags;
    assertEquals(0,wf&WindowManager.LayoutParams.FLAG_FULLSCREEN);
    assertEquals(0,wf&WindowManager.LayoutParams.FLAG_FORCE_NOT_FULLSCREEN);
    assertTrue((flags()&View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN)!=0);
    assertFalse(a.getWindow().isStatusBarContrastEnforced());
  }

  @Test public void fullscreenPlayerStillOwnsHiddenStatusBar()throws Exception{
    FrameLayout overlay=new FrameLayout(a);
    set(a,"mPlayerOverlay",overlay);set(a,"mMultiOverlay",null);set(a,"mInPictureInPicture",false);
    call(a,"cobraApplySystemBarsForSurface");
    assertTrue((a.getWindow().getAttributes().flags&WindowManager.LayoutParams.FLAG_FULLSCREEN)!=0);
    assertEquals(0,a.getWindow().getAttributes().flags&WindowManager.LayoutParams.FLAG_FORCE_NOT_FULLSCREEN);
    assertTrue((flags()&View.SYSTEM_UI_FLAG_FULLSCREEN)!=0);
    assertEquals(android.graphics.Color.BLACK,a.getWindow().getStatusBarColor());
  }
}
