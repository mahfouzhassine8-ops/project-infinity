package com.projectinfinity.kodi;
import android.app.Application;import android.graphics.Rect;import android.view.*;import android.widget.*;
import org.junit.*;import org.junit.runner.RunWith;import org.robolectric.annotation.*;
import static org.junit.Assert.*;
@RunWith(org.robolectric.RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE) @LooperMode(LooperMode.Mode.PAUSED)
public class ShortWindowAndThemeTest {
 SurfaceRuntimeRegressionTest f;
 @Before public void before()throws Exception{f=new SurfaceRuntimeRegressionTest();f.before();}
 @After public void after()throws Exception{f.after();}
 @Test public void shortWindowsReachTheExistingChannelBrowserAcrossFiveModes()throws Exception{
  Object player=f.player,texture=f.texture;
  for(String mode:new String[]{"mobile","grid","compact","cards","focus"}){
   f.put(f.a,"mCobraGuideStyle",mode);f.call(f.a,"cobraShowGuideShell");ResponsiveWindowTest.window(f.ui,f.a,380,190);
   View shell=(View)f.get(f.a,"mCobraGuideShell"),browser=(View)f.get(f.a,"mCobraGuideBrowser");
   assertTrue(shell.canScrollVertically(1));shell.scrollTo(0,10000);
   Rect shown=new Rect();assertTrue(mode,browser.getGlobalVisibleRect(shown));assertTrue(mode,shown.height()>=100);
   assertNotNull(f.get(f.a,"mCobraGuideList"));assertSame(player,f.get(f.a,"mCobraPreviewPlayer"));assertSame(texture,f.get(f.a,"mCobraPreviewTexture"));
  }assertEquals(0,f.state.prepares);assertEquals(0,f.state.mediaChanges);
 }
 @Test public void expandingAWindowResetsOverflowWithoutReplacingTheSurface()throws Exception{
  ResponsiveWindowTest.window(f.ui,f.a,380,190);View shell=(View)f.get(f.a,"mCobraGuideShell");shell.scrollTo(0,10000);assertTrue(shell.getScrollY()>0);
  ResponsiveWindowTest.window(f.ui,f.a,412,915);assertEquals(0,shell.getScrollY());assertFalse(shell.canScrollVertically(1));assertSame(f.texture,f.get(f.a,"mCobraPreviewTexture"));
 }
 @Test public void normalWindowsDoNotAddScrollingOrChangeLockedGeometry()throws Exception{
  View shell=(View)f.get(f.a,"mCobraGuideShell");assertFalse(shell.canScrollVertically(1));shell.scrollTo(0,1000);assertEquals(0,shell.getScrollY());
  assertEquals(600,f.call(f.a,"cobraGuideWorkingHeight",600));assertEquals(240,f.call(f.a,"cobraGuideWorkingHeight",240));
 }
 @Test public void changingAppearanceRefreshesActualSystemBarContrast()throws Exception{
  android.content.SharedPreferences prefs=(android.content.SharedPreferences)f.get(f.a,"mPrefs");
  for(String mode:new String[]{"light","dark","oled"}){
   prefs.edit().putString("cobra_appearance_mode",mode).commit();f.call(f.a,"cobraApplyAppearanceSettings");
   boolean darkIcons=(f.a.getWindow().getDecorView().getSystemUiVisibility()&View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR)!=0;
   assertEquals(mode,"light".equals(mode),darkIcons);
  }
 }
}
