package com.projectinfinity.kodi;

import android.app.*;
import android.os.*;
import android.view.*;
import android.widget.*;
import java.lang.reflect.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w717dp-h917dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103167StatusBarRestoreTest {
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
  int flags(){return a.getWindow().getDecorView().getSystemUiVisibility();}

  static final int STALE =
      View.SYSTEM_UI_FLAG_FULLSCREEN
      |View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
      |View.SYSTEM_UI_FLAG_IMMERSIVE
      |View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
      |View.SYSTEM_UI_FLAG_LOW_PROFILE
      |View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
      |View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION;

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

  @Test public void browseForcesRealStatusBarAndScrubsLegacyImmersiveState()throws Exception{
    set(a,"mPlayerOverlay",null);set(a,"mMultiOverlay",null);set(a,"mInPictureInPicture",false);
    a.getWindow().addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);
    a.getWindow().getDecorView().setSystemUiVisibility(STALE);
    call(a,"cobraApplySystemBarsForSurface");
    assertEquals(0,a.getWindow().getAttributes().flags&WindowManager.LayoutParams.FLAG_FULLSCREEN);
    assertTrue((a.getWindow().getAttributes().flags&WindowManager.LayoutParams.FLAG_FORCE_NOT_FULLSCREEN)!=0);
    assertEquals("Browse must remove every stale hide/immersive bit",0,flags()&STALE);
  }

  @Test public void fullscreenVideoHidesStatusButNeverNavigationBar()throws Exception{
    FrameLayout overlay=new FrameLayout(a);
    set(a,"mPlayerOverlay",overlay);set(a,"mMultiOverlay",null);set(a,"mInPictureInPicture",false);
    a.getWindow().getDecorView().setSystemUiVisibility(
        View.SYSTEM_UI_FLAG_HIDE_NAVIGATION|View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
    call(a,"cobraApplySystemBarsForSurface");
    assertTrue((a.getWindow().getAttributes().flags&WindowManager.LayoutParams.FLAG_FULLSCREEN)!=0);
    assertEquals(0,a.getWindow().getAttributes().flags&WindowManager.LayoutParams.FLAG_FORCE_NOT_FULLSCREEN);
    assertEquals(0,flags()&View.SYSTEM_UI_FLAG_HIDE_NAVIGATION);
    assertEquals(0,flags()&View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
    assertTrue((flags()&View.SYSTEM_UI_FLAG_FULLSCREEN)!=0);
  }

  @Test public void nextFrameConfirmationRepairsOemStyleFullscreenRelapse()throws Exception{
    set(a,"mPlayerOverlay",null);set(a,"mMultiOverlay",null);set(a,"mInPictureInPicture",false);
    a.getWindow().addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);
    a.getWindow().getDecorView().setSystemUiVisibility(STALE);
    call(a,"cobraConfirmBrowseSystemBars");
    assertEquals(0,a.getWindow().getAttributes().flags&WindowManager.LayoutParams.FLAG_FULLSCREEN);
    assertTrue((a.getWindow().getAttributes().flags&WindowManager.LayoutParams.FLAG_FORCE_NOT_FULLSCREEN)!=0);
    assertEquals(0,flags()&STALE);
  }

  @Test public void pipNeverRetainsFullscreenStatusBarOwnership()throws Exception{
    FrameLayout overlay=new FrameLayout(a);
    set(a,"mPlayerOverlay",overlay);set(a,"mMultiOverlay",null);set(a,"mInPictureInPicture",true);
    a.getWindow().addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);
    a.getWindow().getDecorView().setSystemUiVisibility(STALE);
    call(a,"cobraApplySystemBarsForSurface");
    assertEquals(0,a.getWindow().getAttributes().flags&WindowManager.LayoutParams.FLAG_FULLSCREEN);
    assertTrue((a.getWindow().getAttributes().flags&WindowManager.LayoutParams.FLAG_FORCE_NOT_FULLSCREEN)!=0);
    assertEquals(0,flags()&STALE);
  }

  @Test public void focusRecoveryReappliesBrowseStatusBarPolicy()throws Exception{
    set(a,"mPlayerOverlay",null);set(a,"mMultiOverlay",null);set(a,"mInPictureInPicture",false);
    a.getWindow().addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);
    a.getWindow().getDecorView().setSystemUiVisibility(STALE);
    a.onWindowFocusChanged(true);idle();
    assertEquals(0,a.getWindow().getAttributes().flags&WindowManager.LayoutParams.FLAG_FULLSCREEN);
    assertTrue((a.getWindow().getAttributes().flags&WindowManager.LayoutParams.FLAG_FORCE_NOT_FULLSCREEN)!=0);
    assertEquals(0,flags()&STALE);
  }
}
