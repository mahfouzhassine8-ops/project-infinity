package com.projectinfinity.kodi;

import android.app.*;
import android.content.*;
import android.content.res.Configuration;
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

/** 2103166 end-to-end presentation audit.
 * Exercises the shared browse root across internal screens, Fold-size reflow and fullscreen handoff.
 * It does not claim physical Samsung SystemUI or hardware-decoder acceptance. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w717dp-h917dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103166EndToEndUiAuditTest {
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
  TextView header()throws Exception{return (TextView)get(a,"mHeader");}

  WindowInsets insets(int left,int top,int right,int bottom){
    return new WindowInsets.Builder()
        .setInsets(WindowInsets.Type.systemBars(),Insets.of(left,top,right,bottom))
        .build();
  }
  WindowInsets insetsWithCutout(int sysTop,int cutTop,int bottom){
    return new WindowInsets.Builder()
        .setInsets(WindowInsets.Type.systemBars(),Insets.of(0,sysTop,0,bottom))
        .setInsets(WindowInsets.Type.displayCutout(),Insets.of(0,cutTop,0,0))
        .build();
  }
  void dispatch(WindowInsets insets)throws Exception{root().dispatchApplyWindowInsets(insets);idle();}

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

  @Test public void browseRootConsumesSystemBarsWithoutAccumulating()throws Exception{
    dispatch(insets(3,36,5,24));
    assertEquals(3,root().getPaddingLeft());assertEquals(36,root().getPaddingTop());
    assertEquals(5,root().getPaddingRight());assertEquals(24,root().getPaddingBottom());
    dispatch(insets(1,42,2,18));
    assertEquals("Insets must replace, never accumulate",42,root().getPaddingTop());
    assertEquals(18,root().getPaddingBottom());
  }

  @Test public void settingsHeaderLivesInsideSharedTopSafeArea()throws Exception{
    call(a,"showSettings");dispatch(insets(0,40,0,22));ui.measure(a,717,917);
    assertEquals("COBRA • SETTINGS",header().getText().toString());
    assertEquals(40,root().getPaddingTop());
    assertEquals(View.VISIBLE,header().getVisibility());
    assertTrue("Header must retain measurable height",header().getHeight()>0);
  }

  @Test public void internalScreensKeepOneSafeRoot()throws Exception{
    View safe=root();dispatch(insets(0,34,0,20));
    String[] screens={"showSettings","showSources","showProfiles","showCobraHealthCenter"};
    for(String screen:screens){
      call(a,screen);ui.measure(a,717,917);
      assertSame("Internal screen replaced the safe browse root: "+screen,safe,root());
      assertEquals("Top inset lost on "+screen,34,root().getPaddingTop());
      assertEquals("Bottom inset lost on "+screen,20,root().getPaddingBottom());
    }
  }

  @Test public void shellRebuildReinstallsSafeAreaContract()throws Exception{
    View old=root();call(a,"buildShell");idle();View rebuilt=root();assertNotSame(old,rebuilt);
    dispatch(insets(4,38,6,26));ui.measure(a,717,917);
    assertEquals(4,rebuilt.getPaddingLeft());assertEquals(38,rebuilt.getPaddingTop());
    assertEquals(6,rebuilt.getPaddingRight());assertEquals(26,rebuilt.getPaddingBottom());
  }

  @Test public void foldLandscapeReflowRetainsSafeAreaContract()throws Exception{
    RuntimeEnvironment.setQualifiers("w915dp-h412dp-land-mdpi");
    Configuration c=new Configuration(a.getResources().getConfiguration());
    call(a,"onConfigurationChanged",c);idle();
    dispatch(insets(8,28,8,18));ui.measure(a,915,412);
    assertEquals(28,root().getPaddingTop());assertEquals(18,root().getPaddingBottom());
    assertTrue(root().getWidth()>0);assertTrue(root().getHeight()>0);
  }

  @Test public void cutoutWinsWhenItIsLargerThanStatusBar()throws Exception{
    dispatch(insetsWithCutout(24,46,16));
    assertEquals("Display cutout must be included in safe top",46,root().getPaddingTop());
    assertEquals(16,root().getPaddingBottom());
  }

  @Test public void fullscreenPlayerDoesNotStealBrowseSafeAreaOwnership()throws Exception{
    dispatch(insets(0,36,0,22));
    FrameLayout overlay=new FrameLayout(a);
    ((ViewGroup)a.getWindow().getDecorView()).addView(overlay,new ViewGroup.LayoutParams(-1,-1));
    set(a,"mPlayerOverlay",overlay);set(a,"mMultiOverlay",null);set(a,"mInPictureInPicture",false);
    call(a,"cobraApplySystemBarsForSurface");idle();
    assertTrue((a.getWindow().getAttributes().flags&WindowManager.LayoutParams.FLAG_FULLSCREEN)!=0);
    assertEquals("Player overlay must stay edge-to-edge",0,overlay.getPaddingTop());
    set(a,"mPlayerOverlay",null);((ViewGroup)overlay.getParent()).removeView(overlay);
    call(a,"cobraApplySystemBarsForSurface");dispatch(insets(0,36,0,22));
    assertEquals(0,a.getWindow().getAttributes().flags&WindowManager.LayoutParams.FLAG_FULLSCREEN);
    assertEquals(36,root().getPaddingTop());
  }

  @Test public void settingsReturnAfterFullscreenCannotClipHeader()throws Exception{
    FrameLayout overlay=new FrameLayout(a);set(a,"mPlayerOverlay",overlay);set(a,"mInPictureInPicture",false);
    call(a,"cobraApplySystemBarsForSurface");set(a,"mPlayerOverlay",null);
    call(a,"cobraApplySystemBarsForSurface");call(a,"showSettings");
    dispatch(insets(0,44,0,24));ui.measure(a,717,917);
    assertEquals("COBRA • SETTINGS",header().getText().toString());
    assertEquals(44,root().getPaddingTop());
    assertEquals(0,a.getWindow().getAttributes().flags&WindowManager.LayoutParams.FLAG_FULLSCREEN);
  }
}
