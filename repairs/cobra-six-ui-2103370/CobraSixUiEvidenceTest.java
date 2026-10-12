package com.projectinfinity.kodi;
import android.content.res.Configuration;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.view.View;
import java.io.*;
import java.util.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.shadows.ShadowDisplayManager;
import org.robolectric.shadows.ShadowViewRootImpl;
import org.robolectric.shadow.api.Shadow;
import org.robolectric.util.ReflectionHelpers;
import static org.junit.Assert.*;
import static com.projectinfinity.kodi.CobraNavigationUiTest.*;
/** Actual simulated window bounds, existing configuration lifecycle, real production controls. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=android.app.Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi",shadows=CobraSixContractsTest.PipShadow.class)
@GraphicsMode(GraphicsMode.Mode.NATIVE) @LooperMode(LooperMode.Mode.PAUSED)
public class CobraSixUiEvidenceTest {
 CobraSixContractsTest c;InfinityLiveActivity a;
 @Before public void setup()throws Exception{c=new CobraSixContractsTest();c.setup();a=c.a;}
 @After public void clean()throws Exception{c.cleanup();}
 void window(int w,int h)throws Exception{
  String q="w"+w+"dp-h"+h+"dp-"+(w>h?"land":"port")+"-mdpi";
  ShadowDisplayManager.changeDisplay(0,q);RuntimeEnvironment.setQualifiers(q);
  Configuration config=new Configuration(a.getResources().getConfiguration());config.screenWidthDp=w;config.screenHeightDp=h;config.orientation=w>h?Configuration.ORIENTATION_LANDSCAPE:Configuration.ORIENTATION_PORTRAIT;
  a.getResources().updateConfiguration(config,a.getResources().getDisplayMetrics());a.onConfigurationChanged(config);Object viewRoot=ReflectionHelpers.callInstanceMethod(a.getWindow().getDecorView(),"getViewRootImpl");((ShadowViewRootImpl)Shadow.extract(viewRoot)).callDispatchResized();c.b.f.frames(1);c.b.f.measure(a,w,h);
 }
 void capture(String label,int w,int h)throws Exception{
  c.b.f.measure(a,w,h);if(get(a,"mPlayerOverlay")!=null)call(a,"showPlayerChromeTemporarily");c.b.f.frames(15);if(get(a,"mPlayerOverlay")!=null){View chrome=(View)get(a,"mPlayerChrome");assertNotNull(chrome);assertEquals("Capture the existing revealed controls, not their intentional auto-hide state",View.VISIBLE,chrome.getVisibility());assertTrue(chrome.getAlpha()>.9f);}View root=a.getWindow().getDecorView();
  assertEquals("Actual window width must match evidence label",w,root.getWidth());assertEquals("Actual window height must match evidence label",h,root.getHeight());
  File folder=new File(System.getProperty("cobra.evidence"),"window-review");folder.mkdirs();Bitmap bitmap=Bitmap.createBitmap(w,h,Bitmap.Config.ARGB_8888);root.draw(new Canvas(bitmap));try(FileOutputStream out=new FileOutputStream(new File(folder,label+".png"))){assertTrue(bitmap.compress(Bitmap.CompressFormat.PNG,100,out));}bitmap.recycle();
 }
 @Test public void allModesUseRealPortraitLandscapeAndSmallWindowBounds()throws Exception{
  for(String mode:new String[]{"mobile","grid","compact","cards","focus"}){
   c.mini(mode,false,1);window(412,915);capture(mode+"-mini-412x915",412,915);
   call(a,"promoteCobraPreviewToFullscreen",c.b.channel(0));window(915,412);capture(mode+"-fullscreen-915x412",915,412);
   if(mode.equals("focus")){window(280,280);capture("pro-small-280x280",280,280);}
   call(a,"closePlayer");call(a,"stopCobraPreviewPlayerOnly");
  }
 }
 @Test public void statusPanelMatchesReferenceAtActualFoldAndCoverBounds()throws Exception{
  c.full("focus",false,1);window(915,650);Object game=c.game();c.own(game);c.repository(c.summary(game),false);call(a,"cobraShowProGameStatus");c.drain();capture("pro-game-status-915x650",915,650);
  window(915,412);assertNull("Configuration change keeps the established sheet-dismissal lifecycle",get(a,"mCobraActionSheet"));call(a,"cobraShowProGameStatus");c.drain();capture("pro-game-status-915x412",915,412);
  call(a,"closeCobraActionSheet");call(a,"closeFullscreenToCobraView");window(412,915);call(a,"cobraShowProGameStatus");c.drain();capture("pro-mini-status-412x915",412,915);
 }
 @Test public void proHeaderUsesExistingAppearanceAndAmbientStatesAtRealBounds()throws Exception{
  c.mini("focus",false,1);window(412,915);
  for(String appearance:new String[]{"dark","light","oled","system"})for(String ambient:new String[]{"off","subtle","immersive"}){
   c.prefs.edit().putString("cobra_appearance_mode",appearance).putString(CobraPresentationEffects.AMBIENT,ambient).commit();call(a,"cobraApplyAppearanceSettings");call(a,"cobraRefreshAmbient");capture("pro-header-"+appearance+"-"+ambient,412,915);
  }
 }
}
