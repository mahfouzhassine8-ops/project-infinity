package com.projectinfinity.kodi;

import android.app.*;
import android.content.*;
import android.content.res.Configuration;
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
public class Cobra2103165InsetsPipPlayerTest {
  CobraNavigationUiTest ui;
  InfinityLiveActivity a;

  static Object get(Object o,String name)throws Exception{
    for(Class<?> c=o.getClass();c!=null;c=c.getSuperclass()){
      try{Field f=c.getDeclaredField(name);f.setAccessible(true);return f.get(o);}catch(NoSuchFieldException ignored){}
    }
    throw new NoSuchFieldException(name);
  }
  static void set(Object o,String name,Object value)throws Exception{
    for(Class<?> c=o.getClass();c!=null;c=c.getSuperclass()){
      try{Field f=c.getDeclaredField(name);f.setAccessible(true);f.set(o,value);return;}catch(NoSuchFieldException ignored){}
    }
    throw new NoSuchFieldException(name);
  }
  static Object call(Object o,String name,Object...args)throws Exception{
    for(Class<?> c=o.getClass();c!=null;c=c.getSuperclass())for(Method m:c.getDeclaredMethods())
      if(m.getName().equals(name)&&m.getParameterCount()==args.length){
        m.setAccessible(true);
        try{return m.invoke(o,args);}catch(InvocationTargetException e){
          Throwable cause=e.getCause();if(cause instanceof Exception)throw (Exception)cause;throw new AssertionError(cause);
        }
      }
    throw new NoSuchMethodException(name);
  }
  void idle(){Shadows.shadowOf(Looper.getMainLooper()).idle();}

  @Before public void before()throws Exception{
    CobraVisualRenderer.loading.set(true);CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer.clients.clear();
    ui=new CobraNavigationUiTest();ui.clock();a=ui.fixture(24);idle();
  }
  @After public void after()throws Exception{
    if(a!=null)ui.clean(a);CobraVisualRenderer.clients.clear();
  }

  @Test public void browseSurfaceDoesNotOwnFullscreenStatusBar()throws Exception{
    set(a,"mPlayerOverlay",null);set(a,"mMultiOverlay",null);set(a,"mInPictureInPicture",false);
    call(a,"cobraApplySystemBarsForSurface");idle();
    assertEquals(0,a.getWindow().getAttributes().flags&WindowManager.LayoutParams.FLAG_FULLSCREEN);
  }

  @Test public void fullscreenVideoAloneOwnsStatusBarHiding()throws Exception{
    FrameLayout overlay=new FrameLayout(a);set(a,"mPlayerOverlay",overlay);set(a,"mMultiOverlay",null);set(a,"mInPictureInPicture",false);
    call(a,"cobraApplySystemBarsForSurface");idle();
    assertTrue((a.getWindow().getAttributes().flags&WindowManager.LayoutParams.FLAG_FULLSCREEN)!=0);
    set(a,"mPlayerOverlay",null);call(a,"cobraApplySystemBarsForSurface");idle();
    assertEquals(0,a.getWindow().getAttributes().flags&WindowManager.LayoutParams.FLAG_FULLSCREEN);
  }

  @Test public void configurationRefreshCannotLeaveBrowseFullscreen()throws Exception{
    set(a,"mPlayerOverlay",null);set(a,"mMultiOverlay",null);set(a,"mInPictureInPicture",false);
    a.getWindow().addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);
    call(a,"onConfigurationChanged",new Configuration(a.getResources().getConfiguration()));idle();
    assertEquals(0,a.getWindow().getAttributes().flags&WindowManager.LayoutParams.FLAG_FULLSCREEN);
  }

  @Test public void launcherIntentIsARealBrowseReturnSignal()throws Exception{
    set(a,"mCobraPipReturnArmed",true);
    Intent launcher=new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER);
    a.onNewIntent(launcher);
    assertEquals(Boolean.TRUE,get(a,"mCobraLauncherPipReentry"));
    assertEquals(Boolean.TRUE,call(a,"cobraIsLauncherReturn",launcher));
  }

  @Test public void launcherReturnRemovesOrphanedFullscreenSurface()throws Exception{
    FrameLayout decor=(FrameLayout)a.getWindow().getDecorView();
    FrameLayout overlay=new FrameLayout(a);decor.addView(overlay,new FrameLayout.LayoutParams(-1,-1));
    set(a,"mPlayerOverlay",overlay);set(a,"mInPictureInPicture",false);set(a,"mCobraPipReturnArmed",true);
    Intent launcher=new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER);
    a.onNewIntent(launcher);call(a,"cobraConsumeLauncherPipReturn");idle();
    assertNull("Launcher reentry after PiP must return to Cobra browsing",get(a,"mPlayerOverlay"));
    assertEquals(0,a.getWindow().getAttributes().flags&WindowManager.LayoutParams.FLAG_FULLSCREEN);
  }

  @Test public void nativePipExpansionWithoutLauncherKeepsFullscreenSurface()throws Exception{
    FrameLayout overlay=new FrameLayout(a);set(a,"mPlayerOverlay",overlay);set(a,"mInPictureInPicture",false);set(a,"mCobraPipReturnArmed",true);
    set(a,"mCobraLauncherPipReentry",false);
    call(a,"cobraConsumeLauncherPipReturn");idle();
    assertSame("Tapping native PiP to expand must keep the approved fullscreen player",overlay,get(a,"mPlayerOverlay"));
    assertEquals(Boolean.FALSE,get(a,"mCobraPipReturnArmed"));
  }
}
