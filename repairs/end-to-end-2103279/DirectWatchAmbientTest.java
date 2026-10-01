package com.projectinfinity.kodi;
import android.app.Application;import android.view.*;
import org.junit.*;import org.junit.runner.RunWith;import org.robolectric.*;import org.robolectric.annotation.*;
import static org.junit.Assert.*;
@RunWith(RobolectricTestRunner.class) @Config(sdk=35,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE) @LooperMode(LooperMode.Mode.PAUSED)
public class DirectWatchAmbientTest {
 Cobra2103201ScrubberTest f;CobraImmersiveAmbient old;
 @Before public void setup()throws Exception{f=new Cobra2103201ScrubberTest();old=new WatchAmbientTest().activate(f);old.release();if(old.getParent() instanceof ViewGroup)((ViewGroup)old.getParent()).removeView(old);CobraNavigationUiTest.put(f.a,"mCobraImmersiveAmbient",null);CobraNavigationUiTest.put(f.a,"mPlayingVodKey","fixture:movie");}
 @After public void close()throws Exception{f.after();}
 Object refresh()throws Exception{CobraNavigationUiTest.call(f.a,"cobraRefreshImmersiveAmbient");return CobraNavigationUiTest.get(f.a,"mCobraImmersiveAmbient");}
 @Test public void directWatchRestoresOneSharedEngineAfterGuideRelease()throws Exception{CobraImmersiveAmbient engine=(CobraImmersiveAmbient)refresh();assertNotNull(engine);assertNotSame(old,engine);assertTrue(engine.isAttachedToWindow());assertTrue(engine.isAmbientActive());assertEquals(true,CobraNavigationUiTest.get(engine,"controlsOnly"));assertSame(CobraNavigationUiTest.get(f.a,"mPlayerTexture"),CobraNavigationUiTest.get(engine,"source"));for(int i=0;i<10;i++)assertSame(engine,refresh());assertEquals(0,f.state.prepares);assertEquals(0,f.state.mediaChanges);}
 @Test public void offAndSubtleDoNotCreateWatchRenderer()throws Exception{for(String mode:new String[]{"off","subtle"}){f.prefs.edit().putString(CobraPresentationEffects.AMBIENT,mode).commit();assertNull(refresh());}}
 @Test public void backgroundedWatchDoesNotCreateOrSampleRenderer()throws Exception{CobraNavigationUiTest.put(f.a,"mBackgroundStopped",true);assertNull(refresh());}
 @Test public void showingAndHidingChromeRefreshesIlluminationWithoutWaitingForTicker()throws Exception{
  CobraImmersiveAmbient engine=(CobraImmersiveAmbient)refresh();assertTrue(engine.isAmbientActive());
  CobraNavigationUiTest.call(f.a,"togglePlayerChrome");assertFalse(engine.isAmbientActive());
  CobraNavigationUiTest.call(f.a,"showPlayerChromeTemporarily");assertTrue(engine.isAmbientActive());assertSame(engine,refresh());
 }
}
