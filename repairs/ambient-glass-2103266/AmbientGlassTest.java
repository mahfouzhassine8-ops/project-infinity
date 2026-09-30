package com.projectinfinity.kodi;
import android.content.*;import android.graphics.*;import android.graphics.drawable.*;import android.view.*;import android.widget.*;
import org.junit.*;import org.junit.runner.RunWith;import org.robolectric.*;import org.robolectric.annotation.*;
import static org.junit.Assert.*;
@RunWith(RobolectricTestRunner.class) @Config(sdk=35) @GraphicsMode(GraphicsMode.Mode.NATIVE)
public class AmbientGlassTest {
 final PhoneGlassTest helper=new PhoneGlassTest();
 @Before public void setup(){helper.stableRenderer();}
 @After public void clear(){helper.clearRenderer();}
 InfinityLiveActivity activity(boolean light)throws Exception{InfinityLiveActivity a=helper.activity(light,412,915);PhoneGlassTest.put(a,"mCobraEffects",new CobraPresentationEffects(a));return a;}
 void prefs(InfinityLiveActivity a,String mode,boolean night)throws Exception{((SharedPreferences)PhoneGlassTest.get(a,"mPrefs")).edit().putString(CobraPresentationEffects.AMBIENT,mode).putBoolean(CobraPresentationEffects.NIGHT,night).apply();}
 int pixel(Drawable d){d.setBounds(0,0,160,56);d.jumpToCurrentState();Bitmap b=Bitmap.createBitmap(160,56,Bitmap.Config.ARGB_8888);d.draw(new Canvas(b));int c=b.getPixel(80,28);b.recycle();return c;}
 void close(InfinityLiveActivity a)throws Exception{((CobraPresentationEffects)PhoneGlassTest.get(a,"mCobraEffects")).close();((android.os.Handler)PhoneGlassTest.get(a,"mMain")).removeCallbacksAndMessages(null);a.finish();}
 @Test public void bothGlassPalettesHaveDistinctStrengthsAndExactOffRestoration()throws Exception{
  for(boolean light:new boolean[]{false,true}){InfinityLiveActivity a=activity(light);CobraVisualRenderer.Glass g=(CobraVisualRenderer.Glass)CobraVisualRenderer.phoneGlass(a,light,16,true);g.setState(new int[]{android.R.attr.state_enabled});int original=pixel(g);
   g.effects(0xff49a9ff,1,false);int subtle=pixel(g);g.effects(0xff49a9ff,2,false);int immersive=pixel(g);assertNotEquals(original,subtle);assertNotEquals(subtle,immersive);assertTrue(Color.blue(immersive)-Color.red(immersive)>Color.blue(subtle)-Color.red(subtle));
   g.effects(0xff49a9ff,0,false);assertEquals(original,pixel(g));g.setState(new int[]{android.R.attr.state_enabled,android.R.attr.state_selected});assertNotEquals(original,pixel(g));assertEquals(160,g.getBounds().width());if(light)assertTrue(Color.red(immersive)>180);close(a);
  }
 }
 @Test public void actualGuideRestylingAndDrawerChooserKeepAmbientGlass()throws Exception{
  for(boolean light:new boolean[]{false,true})for(String mode:new String[]{"mobile","grid","compact","cards"}){
   InfinityLiveActivity a=activity(light);PhoneGlassTest.put(a,"mCobraGuideStyle",mode);PhoneGlassTest.put(a,"mCobraPreviewAutoplayAllowed",false);PhoneGlassTest.call(a,"cobraShowGuideShell");View root=(View)PhoneGlassTest.get(a,"mRoot");PhoneGlassTest.layout(root,412,915);
   prefs(a,"immersive",false);PhoneGlassTest.call(a,"cobraRestyleGuide");PhoneGlassTest.call(a,"cobraRenderGuideBrowser");PhoneGlassTest.layout(root,412,915);
   for(String field:new String[]{"mCobraModeToolbar","mCobraModeFooter","mCobraGuideDirectory","mCobraGuideDetails"}){View v=(View)PhoneGlassTest.get(a,field);assertTrue(field,v.getBackground() instanceof CobraVisualRenderer.Glass);assertEquals(field,2,((CobraVisualRenderer.Glass)v.getBackground()).effectMode);}
   assertTrue(((View)PhoneGlassTest.get(a,"mCobraModeToolbar")).findViewWithTag("cobra_mode_visuals").isSelected());
   View host=(View)PhoneGlassTest.get(a,"mCobraPreviewHost");assertFalse(host.getBackground() instanceof CobraVisualRenderer.Glass);ViewGroup controls=(ViewGroup)host.findViewWithTag("cobra_preview_controls");CobraVisualRenderer.Glass control=(CobraVisualRenderer.Glass)controls.getChildAt(0).getBackground();assertEquals(2,control.effectMode);assertFalse(control.light);assertTrue(Color.red(pixel(control))<100);
   View browser=(View)PhoneGlassTest.get(a,"mCobraGuideBrowser");browser.animate().cancel();browser.setAlpha(1);PhoneGlassTest.save(root,"ambient-"+mode+"-"+light);
   if(mode.equals("mobile")){PhoneGlassTest.call(a,"toggleCobraDrawer");View drawer=a.getWindow().getDecorView().findViewWithTag("cobra_experience_drawer");PhoneGlassTest.layout(drawer,412,915);View panel=((ViewGroup)drawer).getChildAt(0);panel.animate().cancel();panel.setAlpha(1);panel.setTranslationX(0);assertEquals(2,((CobraVisualRenderer.Glass)panel.getBackground()).effectMode);assertEquals(2,((CobraVisualRenderer.Glass)drawer.findViewWithTag("cobra-destination:TV").getBackground()).effectMode);PhoneGlassTest.save(drawer,"ambient-drawer-"+light);PhoneGlassTest.call(a,"closeCobraExperienceDrawer");
    PhoneGlassTest.call(a,"cobraPremiumViewMenu");View chooser=(View)PhoneGlassTest.get(a,"mCobraActionSheet");PhoneGlassTest.layout(chooser,412,915);View cp=((ViewGroup)chooser).getChildAt(0);cp.animate().cancel();cp.setAlpha(1);cp.setTranslationY(0);cp.setScaleX(1);cp.setScaleY(1);assertEquals(2,((CobraVisualRenderer.Glass)cp.getBackground()).effectMode);assertEquals(2,((CobraVisualRenderer.Glass)chooser.findViewWithTag("cobra-view-mode:cards").getBackground()).effectMode);PhoneGlassTest.save(chooser,"ambient-chooser-"+light);PhoneGlassTest.call(a,"closeCobraActionSheet");
   }
   prefs(a,"off",false);PhoneGlassTest.call(a,"cobraRefreshAmbient");assertEquals(0,((CobraVisualRenderer.Glass)((View)PhoneGlassTest.get(a,"mCobraModeToolbar")).getBackground()).effectMode);assertNull(PhoneGlassTest.get(a,"mPlayer"));assertNull(PhoneGlassTest.get(a,"mCobraPreviewPlayer"));close(a);
  }
 }
 @Test public void repeatedRefreshNeverStacksTheGuideBackdrop()throws Exception{
  InfinityLiveActivity a=activity(false);PhoneGlassTest.call(a,"cobraShowGuideShell");View shell=(View)PhoneGlassTest.get(a,"mCobraGuideShell");CobraPresentationEffects fx=(CobraPresentationEffects)PhoneGlassTest.get(a,"mCobraEffects");Drawable original=shell.getBackground();fx.backdrop(shell,Color.BLACK,0xff49a9ff,2);Drawable first=shell.getBackground();assertTrue(first instanceof LayerDrawable);
  for(int i=0;i<100;i++)PhoneGlassTest.call(a,"cobraRefreshLiveAmbientSurfaces",2,true,0xff49a9ff);assertSame(first,shell.getBackground());assertEquals(2,((LayerDrawable)first).getNumberOfLayers());fx.backdrop(shell,Color.BLACK,0xff49a9ff,0);assertSame(original,shell.getBackground());close(a);
 }
 @Test public void actualFullscreenCinemaChromeUsesQuietGlassAndRestoresAmbient()throws Exception{
  for(boolean light:new boolean[]{false,true}){InfinityLiveActivity a=activity(light);PhoneGlassTest.call(a,"cobraShowGuideShell");FrameLayout overlay=new FrameLayout(a);overlay.setBackgroundColor(Color.BLACK);a.setContentView(overlay);PhoneGlassTest.put(a,"mPlayerOverlay",overlay);PhoneGlassTest.layout(overlay,412,915);prefs(a,"immersive",true);PhoneGlassTest.call(a,"cobraBuildPlayerChrome");PhoneGlassTest.layout(overlay,412,915);
   View pause=overlay.findViewWithTag("cobra_player_play_pause");assertNotNull(pause);assertTrue(pause.getBackground() instanceof CobraVisualRenderer.Glass);CobraVisualRenderer.Glass glass=(CobraVisualRenderer.Glass)pause.getBackground();assertTrue(glass.night);assertFalse(glass.light);assertEquals(0,glass.effectMode);int quiet=pixel(glass);assertEquals(true,PhoneGlassTest.call(a,"cobraNightCinemaActive"));PhoneGlassTest.save(overlay,"night-cinema-"+light);
   prefs(a,"immersive",false);PhoneGlassTest.call(a,"cobraBuildPlayerChrome");pause=overlay.findViewWithTag("cobra_player_play_pause");glass=(CobraVisualRenderer.Glass)pause.getBackground();assertFalse(glass.night);assertEquals(2,glass.effectMode);assertNotEquals(quiet,pixel(glass));PhoneGlassTest.layout(overlay,412,915);PhoneGlassTest.save(overlay,"cinema-off-ambient-"+light);
   prefs(a,"immersive",true);PhoneGlassTest.put(a,"mInPictureInPicture",true);assertEquals(false,PhoneGlassTest.call(a,"cobraNightCinemaActive"));PhoneGlassTest.put(a,"mInPictureInPicture",false);PhoneGlassTest.put(a,"mMultiOverlay",new FrameLayout(a));assertEquals(false,PhoneGlassTest.call(a,"cobraNightCinemaActive"));assertNull(PhoneGlassTest.get(a,"mPlayer"));close(a);
  }
 }
 @Test public void safeModeReturnsUnmodifiedGlassAndDisablesCinema()throws Exception{
  InfinityLiveActivity a=activity(false);a.setIntent(new Intent().putExtra(CobraPresentationSafety.EXTRA_SAFE,true));prefs(a,"immersive",true);PhoneGlassTest.put(a,"mPlayerOverlay",new FrameLayout(a));CobraVisualRenderer.Glass g=(CobraVisualRenderer.Glass)PhoneGlassTest.call(a,"cobraPhoneGlass",false,16,true);assertEquals(0,g.effectMode);assertFalse(g.night);assertEquals(false,PhoneGlassTest.call(a,"cobraNightCinemaActive"));close(a);
 }
}
