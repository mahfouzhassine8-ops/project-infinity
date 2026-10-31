package com.projectinfinity.kodi;
import android.app.Application;
import android.graphics.drawable.ColorDrawable;
import android.os.Looper;
import android.view.View;
import android.widget.TextView;
import org.junit.*;
import static org.junit.Assert.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,instrumentedPackages={"com.projectinfinity.kodi"},shadows={CobraCardsLayoutTest.TerminalActions.class})
@LooperMode(LooperMode.Mode.PAUSED) @GraphicsMode(GraphicsMode.Mode.NATIVE)
public class CardsThemeTest {
 @Before public void setup(){new CobraCardsLayoutTest().frames();}
 @Test public void nativePaletteAndLiveRestyle()throws Exception{
  CobraCardsLayoutTest.Fixture f=new CobraCardsLayoutTest.Fixture("cards");
  for(String mode:new String[]{"dark","light","oled","light","dark"}){
   f.prefs.edit().putString("cobra_appearance_mode",mode).commit();
   CobraCardsLayoutTest.call(f.a,"cobraRestyleGuide");f.frames();
   assertEquals(mode.equals("light"),!((Boolean)CobraCardsLayoutTest.call(f.a,"cobraModeDark")));
   View shell=(View)CobraCardsLayoutTest.get(f.a,"mCobraGuideShell");
   int bg=((ColorDrawable)shell.getBackground()).getColor();
   int expected=mode.equals("light")?((Number)CobraCardsLayoutTest.call(f.a,"cobraModeColor","background")).intValue():0xff000000;
   assertEquals("native background "+mode,expected,bg);
   TextView label=(TextView)CobraCardsLayoutTest.get(f.a,"mCobraGuideNowLabel");
   int text=mode.equals("light")?((Number)CobraCardsLayoutTest.call(f.a,"cobraModeColor","text")).intValue():0xfff0f3f7;
   assertEquals("native text "+mode,text,label.getCurrentTextColor());
   f.image("theme-"+mode);
  }
 }
}
