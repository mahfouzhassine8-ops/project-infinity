package com.projectinfinity.kodi;
import android.app.Application;import android.view.*;import android.widget.*;
import org.junit.*;import static org.junit.Assert.*;import org.junit.runner.RunWith;import org.robolectric.*;import org.robolectric.annotation.*;
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,qualifiers="w360dp-h840dp-port-480dpi",instrumentedPackages={"com.projectinfinity.kodi"},shadows={CobraActualFullscreenMoreTest.Trace.class})
@LooperMode(LooperMode.Mode.PAUSED) @GraphicsMode(GraphicsMode.Mode.NATIVE)
public class ProSportsRotationAudioTest {
 @Before public void frames(){new CobraCardsLayoutTest().frames();}
 @Test public void sportsStatsCoexistsWithRequiredPrimaryControls()throws Exception{
  for(int[] pane:new int[][]{{1080,2520,480},{1600,1800,320}}){
   CobraCardsLayoutTest.Fixture f=new CobraCardsLayoutTest.Fixture("cards",pane[0],pane[1],pane[2]);f.a.getWindow().setLayout(pane[0],pane[1]);CobraActualFullscreenMoreTest.pulses(3);CobraActualFullscreenMoreTest.actualPreviewPress(f);f.mode("focus");
   Object owner=CobraCardsLayoutTest.get(f.a,"mCobraSix");CobraCardsLayoutTest.call(owner,"recordFullContext",true);assertTrue((Boolean)CobraCardsLayoutTest.call(owner,"sports"));
   CobraCardsLayoutTest.call(f.a,"cobraBuildPlayerChrome");CobraActualFullscreenMoreTest.pulses(3);View chrome=(View)CobraCardsLayoutTest.get(f.a,"mPlayerChrome"),audio=chrome.findViewWithTag("cobra_fullscreen_audio");assertNotNull(audio);
   LinearLayout tools=(LinearLayout)audio.getParent();assertSame(audio,tools.getChildAt(1));assertEquals("Display",tools.getChildAt(2).getContentDescription());assertEquals("PiP",tools.getChildAt(4).getContentDescription());assertEquals("cobra_fullscreen_sports_stats",tools.getChildAt(5).getTag());assertNotNull(chrome.findViewWithTag("cobra_player_rotation"));
   Object player=CobraCardsLayoutTest.get(f.a,"mPlayer");f.press(audio);assertTrue((Boolean)CobraCardsLayoutTest.call(f.a,"cobraMediaMuted",player));f.press(audio);assertFalse((Boolean)CobraCardsLayoutTest.call(f.a,"cobraMediaMuted",player));assertSame(player,CobraCardsLayoutTest.get(f.a,"mPlayer"));
  }
 }
}
