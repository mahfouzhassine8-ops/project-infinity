package com.projectinfinity.kodi;

import android.app.Application;
import android.content.SharedPreferences;
import android.content.res.Configuration;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.drawable.Drawable;
import android.widget.FrameLayout;
import java.io.File;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import org.json.JSONObject;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Actual native Android drawable pixels, not preference-only palette assertions.
 * Controlled Activity fixtures do not establish physical display/GPU behaviour.
 */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103204PaletteTest {
  Cobra2103199DisplayRegressionTest f;
  InfinityLiveActivity a;
  SharedPreferences prefs;

  @Before public void before()throws Exception {
    f=new Cobra2103199DisplayRegressionTest();f.before();a=f.a;prefs=f.prefs;
  }
  @After public void after()throws Exception {
    CobraVisualRenderer.active=CobraVisualTheme.builtin();
    if(f!=null)f.after();
  }
  Object call(String name,Object...args)throws Exception{return CobraNavigationUiTest.call(a,name,args);}
  void mode(String value){prefs.edit().putString("cobra_appearance_mode",value).commit();}
  int color(String name)throws Exception{return (Integer)call("cobraModeColor",name);}
  int sample(Drawable drawable,int[] state,int x,int y){
    drawable.setBounds(0,0,128,64);drawable.setState(state);drawable.jumpToCurrentState();
    Bitmap bitmap=Bitmap.createBitmap(128,64,Bitmap.Config.ARGB_8888);
    drawable.draw(new Canvas(bitmap));int pixel=bitmap.getPixel(x,y);bitmap.recycle();return pixel;
  }
  int fill(Drawable drawable,int...state){return sample(drawable,state,64,32);}
  Drawable surface()throws Exception{return (Drawable)call("cobraModeSurface",14,true);}
  static double luminance(int color){
    double[] values={Color.red(color)/255d,Color.green(color)/255d,Color.blue(color)/255d};
    for(int i=0;i<values.length;i++)values[i]=values[i]<=.04045?values[i]/12.92:Math.pow((values[i]+.055)/1.055,2.4);
    return values[0]*.2126+values[1]*.7152+values[2]*.0722;
  }
  static double contrast(int a,int b){double x=luminance(a),y=luminance(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);}

  @Test public void lightCanvasIsWhiteAndAllFiveGuideModesUseTheShellPalette()throws Exception {
    mode("light");assertEquals(Color.WHITE,color("background"));
    Object theme=CobraNavigationUiTest.get(a,"mTheme");
    for(String view:new String[]{"mobile","compact","cards","focus","grid"}){
      CobraNavigationUiTest.put(a,"mCobraGuideStyle",view);
      for(String key:new String[]{"background","rail","panel","text","muted","line","accent"}){
        int expected=(Integer)call("cobraThemeColor",key,(Integer)CobraNavigationUiTest.get(theme,key));
        assertEquals(view+" / "+key,expected,color(key));
      }
    }
  }
  @Test public void darkAndOledCanvasesAreActuallyBlackWithDistinctInsetSurfaces()throws Exception {
    for(String palette:new String[]{"dark","oled"}){
      mode(palette);assertEquals(Color.BLACK,color("background"));assertEquals(Color.BLACK,color("rail"));
      int actual=fill(surface());assertEquals(color("panel"),actual);assertNotEquals(Color.BLACK,actual);
      assertEquals("Inset must be opaque and cannot accidentally reveal video",255,Color.alpha(actual));
    }
    mode("dark");int dark=fill(surface());mode("oled");assertNotEquals(dark,fill(surface()));
  }
  @Test public void lightNormalSelectedAndFocusedTextRemainReadableOnRenderedSurfaces()throws Exception {
    mode("light");Drawable background=surface();
    for(int[] state:new int[][]{new int[0],{android.R.attr.state_selected},{android.R.attr.state_focused}}){
      int actual=fill(background,state);assertEquals(255,Color.alpha(actual));
      assertTrue("Main text contrast",contrast(color("text"),actual)>=4.5);
      assertTrue("Secondary text contrast",contrast(color("muted"),actual)>=4.5);
    }
  }
  @Test public void darkAndOledNormalSelectedAndFocusedTextRemainReadableOnRenderedSurfaces()throws Exception {
    for(String palette:new String[]{"dark","oled"}){
      mode(palette);Drawable background=surface();
      for(int[] state:new int[][]{new int[0],{android.R.attr.state_selected},{android.R.attr.state_focused}}){
        int actual=fill(background,state);
        assertTrue(palette+" main text",contrast(color("text"),actual)>=4.5);
        assertTrue(palette+" secondary text",contrast(color("muted"),actual)>=4.5);
      }
    }
  }
  @Test public void selectionFocusAndNormalAreVisiblyDifferentWithoutChangingBounds()throws Exception {
    for(String palette:new String[]{"light","dark","oled"}){
      mode(palette);Drawable background=surface();int normal=fill(background),selected=fill(background,android.R.attr.state_selected),focused=fill(background,android.R.attr.state_focused);
      assertNotEquals(palette,normal,selected);assertNotEquals(palette,normal,focused);assertNotEquals(palette,selected,focused);
      assertEquals(128,background.getBounds().width());assertEquals(64,background.getBounds().height());
    }
  }
  @Test public void raisedSurfaceHasFineRimButTransparentControlSurfaceStaysTransparent()throws Exception {
    mode("light");Drawable raised=surface();assertNotEquals(fill(raised),sample(raised,new int[0],0,32));
    Drawable plain=(Drawable)call("cobraModeSurface",14,false);assertEquals(Color.TRANSPARENT,fill(plain));
    assertEquals("Rounded outside corner stays transparent",Color.TRANSPARENT,sample(raised,new int[0],0,0));
  }
  @Test public void lightBrowsingStillRendersDarkVideoSheetSurfaces()throws Exception {
    mode("light");CobraNavigationUiTest.put(a,"mPlayerOverlay",new FrameLayout(a));
    assertEquals(true,call("cobraSheetIsDark"));Drawable background=(Drawable)call("cobraSheetDetailSurface",14);
    assertEquals(0xff0b0f16,fill(background));assertEquals(0xff162d49,fill(background,android.R.attr.state_focused));
    assertTrue(contrast(0xfff7faff,fill(background,android.R.attr.state_selected))>=4.5);
  }
  @Test public void loadedLegacyDarkPaletteStillOwnsGuideAndShellFallbacks()throws Exception {
    mode("dark");Object theme=CobraNavigationUiTest.get(a,"mTheme");
    CobraNavigationUiTest.put(theme,"background",0xff140919);CobraNavigationUiTest.put(theme,"panel",0xff2a1734);
    CobraNavigationUiTest.put(theme,"accent",0xffe3a8ff);
    assertEquals(0xff140919,color("background"));assertEquals(0xff2a1734,fill(surface()));assertEquals(0xffe3a8ff,color("accent"));
    assertEquals(0xff140919,call("cobraBuiltInAppearanceColor","dark","background",0xff140919));
  }
  @Test public void publishedPerComponentAndGlobalThemeSlotsKeepTheirPrecedence()throws Exception {
    mode("light");CobraVisualTheme theme=CobraVisualTheme.builtin();
    JSONObject colors=new JSONObject().put("cobra.cobraModeColorBuiltin.colors.12","#EDF0E0").put("palette.panel","#E2E8D5");
    theme.data.put("base",new JSONObject().put("colors",colors));CobraVisualRenderer.active=theme;
    assertEquals(0xffedf0e0,call("cobraModeColorBuiltin","panel"));assertEquals(0xffe2e8d5,color("panel"));assertEquals(0xffe2e8d5,fill(surface()));
    CobraVisualRenderer.active=CobraVisualTheme.builtin();assertEquals(0xfff5f8fd,fill(surface()));
    assertFalse(((CobraVisualRenderer)call("vtheme")).installed());
  }
  @Test public void followSystemKeepsDarkVariantPreferenceWhileRenderingCorrectFoundation()throws Exception {
    mode("system");prefs.edit().putString("cobra_system_dark_variant","oled").commit();
    for(boolean night:new boolean[]{false,true,false,true}){
      Configuration c=new Configuration(a.getResources().getConfiguration());
      c.uiMode=(c.uiMode&~Configuration.UI_MODE_NIGHT_MASK)|(night?Configuration.UI_MODE_NIGHT_YES:Configuration.UI_MODE_NIGHT_NO);
      a.getResources().updateConfiguration(c,a.getResources().getDisplayMetrics());
      assertEquals(night?Color.BLACK:Color.WHITE,color("background"));
      assertEquals(night?0xff070a10:0xfff5f8fd,fill(surface()));assertEquals("oled",prefs.getString("cobra_system_dark_variant",""));
    }
  }

  static final String FACTORY = "{\n"
      +"  \"schema\": 2,\n"
      +"  \"background\": \"#01050B\",\n"
      +"  \"rail\": \"#06111E\",\n"
      +"  \"panel\": \"#091726\",\n"
      +"  \"panel2\": \"#0C2034\",\n"
      +"  \"focus\": \"#095FD8\",\n"
      +"  \"accent\": \"#24B7FF\",\n"
      +"  \"accent_soft\": \"#7BD6FF\",\n"
      +"  \"text\": \"#F5FAFF\",\n"
      +"  \"muted\": \"#8FA7BD\",\n"
      +"  \"line\": \"#1B3852\",\n"
      +"  \"row_height\": 72,\n"
      +"  \"guide_row_height\": 98,\n"
      +"  \"touch_target\": 60,\n"
      +"  \"rail_item_height\": 54,\n"
      +"  \"motion_ms\": 190\n"
      +"}\n";
  Object loadFile(String contents)throws Exception {
    File file=new File(a.getExternalFilesDir(null),".kodi/addons/script.infinity.cobra.theme/resources/cobra-theme.json");
    byte[] previous=file.isFile()?CobraVisualTheme.readFile(file,65536):null;
    assertTrue(file.getParentFile().isDirectory()||file.getParentFile().mkdirs());
    byte[] payload=contents.getBytes(StandardCharsets.UTF_8);
    try{
      try(FileOutputStream out=new FileOutputStream(file)){out.write(payload);}
      Object theme=CobraNavigationUiTest.construct("Theme");Object loaded=CobraNavigationUiTest.call(theme,"load",a);
      assertArrayEquals("Loading must not rewrite the installed palette",payload,CobraVisualTheme.readFile(file,65536));return loaded;
    }finally{
      if(previous==null)assertTrue(file.delete());
      else try(FileOutputStream out=new FileOutputStream(file)){out.write(previous);}
    }
  }
  @Test public void exactPackagedFactoryPaletteMigratesOnlyColorsAndPreservesItsGeometry()throws Exception {
    byte[] payload=FACTORY.getBytes(StandardCharsets.UTF_8);assertEquals(362,payload.length);
    assertEquals("3afe4362451ad394f4a0f95bc790955b10de27ffdbf4d36247ebe85d60adbb3b",CobraVisualTheme.hash(payload));
    Object theme=loadFile(FACTORY);assertEquals(Color.BLACK,CobraNavigationUiTest.get(theme,"background"));
    assertEquals(0xff62aaff,CobraNavigationUiTest.get(theme,"accent"));assertEquals(0xff0b0f16,CobraNavigationUiTest.get(theme,"panel"));
    assertEquals(72,CobraNavigationUiTest.get(theme,"rowHeight"));assertEquals(98,CobraNavigationUiTest.get(theme,"guideRowHeight"));
    assertEquals(60,CobraNavigationUiTest.get(theme,"touchTarget"));assertEquals(54,CobraNavigationUiTest.get(theme,"railItemHeight"));assertEquals(190,CobraNavigationUiTest.get(theme,"motionMs"));
    CobraNavigationUiTest.put(a,"mTheme",theme);mode("dark");assertEquals(Color.BLACK,color("background"));assertEquals(0xff0b0f16,fill(surface()));
  }
  @Test public void editedFactoryPaletteRetainsEveryOriginalAndCustomColor()throws Exception {
    Object theme=loadFile(FACTORY.replace("#24B7FF","#DB8DFF"));
    assertEquals(0xff01050b,CobraNavigationUiTest.get(theme,"background"));assertEquals(0xffdb8dff,CobraNavigationUiTest.get(theme,"accent"));
    assertEquals(0xff091726,CobraNavigationUiTest.get(theme,"panel"));assertEquals(60,CobraNavigationUiTest.get(theme,"touchTarget"));
  }
  @Test public void reformattedFactoryManifestIsTreatedAsCustomRatherThanGuessedFactory()throws Exception {
    Object theme=loadFile(new JSONObject(FACTORY).toString());
    assertEquals(0xff01050b,CobraNavigationUiTest.get(theme,"background"));assertEquals(0xff24b7ff,CobraNavigationUiTest.get(theme,"accent"));
    assertEquals(0xff091726,CobraNavigationUiTest.get(theme,"panel"));
  }
}
