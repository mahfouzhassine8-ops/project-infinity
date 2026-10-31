package com.projectinfinity.kodi;
import android.app.Application;import android.widget.TextView;
import org.junit.*;import static org.junit.Assert.*;import org.junit.runner.RunWith;
import org.robolectric.*;import org.robolectric.annotation.*;
/** Selected Cards Light -> native mode -> Cards restoration; no shutdown. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,instrumentedPackages={"com.projectinfinity.kodi"},shadows={CobraCardsLayoutTest.TerminalActions.class})
@LooperMode(LooperMode.Mode.PAUSED) @GraphicsMode(GraphicsMode.Mode.NATIVE)
public class CardsThemeReturnTest {
 @Before public void setup(){new CobraCardsLayoutTest().frames();}
 @Test public void lightSurvivesMobileAndProReturn()throws Exception{
  for(String other:new String[]{"mobile","focus"}){
   CobraCardsLayoutTest.Fixture f=new CobraCardsLayoutTest.Fixture("cards");
   f.prefs.edit().putString("cobra_appearance_mode","light").commit();CobraCardsLayoutTest.call(f.a,"cobraRestyleGuide");f.frames();
   Object selected=CobraCardsLayoutTest.get(f.a,"mGuidePreviewChannel");f.mode(other);f.mode("cards");
   assertEquals("light",f.prefs.getString("cobra_appearance_mode",""));assertSame(selected,CobraCardsLayoutTest.get(f.a,"mGuidePreviewChannel"));
   int expected=((Number)CobraCardsLayoutTest.call(f.a,"cobraModeColor","text")).intValue();
   assertEquals(expected,((TextView)CobraCardsLayoutTest.get(f.a,"mCobraGuideNowLabel")).getCurrentTextColor());
  }
 }
}
