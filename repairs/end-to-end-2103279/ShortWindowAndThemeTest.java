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
   shell.scrollTo(0,0);assertTrue(mode+" must expose a scroll range",shell.canScrollVertically(1));shell.scrollTo(0,10000);
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
   View backdrop=(View)f.get(f.a,"mCobraBrowseBackground");android.graphics.Bitmap image=android.graphics.Bitmap.createBitmap(8,8,android.graphics.Bitmap.Config.ARGB_8888);
   try{backdrop.getBackground().setBounds(0,0,8,8);backdrop.getBackground().draw(new android.graphics.Canvas(image));int pixel=image.getPixel(4,4);float luminance=.2126f*android.graphics.Color.red(pixel)+.7152f*android.graphics.Color.green(pixel)+.0722f*android.graphics.Color.blue(pixel);assertEquals("Backdrop contrast "+mode,"light".equals(mode),luminance>158);}finally{image.recycle();}
  }
 }
 @Test public void channelDrawerReservesTransientNavigationAndRestoresPadding()throws Exception{
  Cobra2103201ScrubberTest player=new Cobra2103201ScrubberTest();
  try{
   player.before();CobraNavigationUiTest.call(player.a,"showCobraPlayerDrawer");player.settle();
   FrameLayout panel=(FrameLayout)CobraNavigationUiTest.get(player.a,"mCobraPlayerDrawer");View content=panel.getChildAt(0);
   WindowInsets none=new WindowInsets.Builder().build();CobraNavigationUiTest.call(player.a,"cobraInsetPlayerDrawer",none);
   int base=content.getPaddingBottom();View video=(View)CobraNavigationUiTest.get(player.a,"mPlayerTexture");int width=video.getWidth(),height=video.getHeight();
   WindowInsets nav=new WindowInsets.Builder().setInsetsIgnoringVisibility(WindowInsets.Type.navigationBars(),android.graphics.Insets.of(0,0,0,48)).setVisible(WindowInsets.Type.navigationBars(),false).build();
   CobraNavigationUiTest.call(player.a,"cobraInsetPlayerDrawer",nav);assertEquals(base+48,content.getPaddingBottom());
   assertEquals(width,video.getWidth());assertEquals(height,video.getHeight());assertSame(player.player,CobraNavigationUiTest.get(player.a,"mPlayer"));
   CobraNavigationUiTest.call(player.a,"cobraInsetPlayerDrawer",none);assertEquals(base,content.getPaddingBottom());
  }finally{player.after();}
 }
}
