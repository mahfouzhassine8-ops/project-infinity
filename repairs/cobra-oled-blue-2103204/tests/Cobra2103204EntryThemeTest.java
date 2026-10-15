package com.projectinfinity.kodi;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.drawable.ColorDrawable;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import java.io.File;
import java.io.FileOutputStream;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.List;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.android.controller.ActivityController;
import static org.junit.Assert.*;

/** Real fallback chooser factory, drawn by Android; no Kodi startup or device claim. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34, application=android.app.Application.class, manifest=Config.NONE,
    qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103204EntryThemeTest {
  ActivityController<Splash> controller;
  Splash a;
  View root;
  List<TextView> texts = new ArrayList<>();
  @Before public void before() {
    CobraVisualRenderer.active = CobraVisualTheme.builtin();
    CobraVisualRenderer.loading.set(true);
    synchronized(CobraVisualRenderer.clients){CobraVisualRenderer.clients.clear();}
    controller = Robolectric.buildActivity(Splash.class);
    a = controller.get();
    a.setTheme(android.R.style.Theme_NoTitleBar);
    a.getSharedPreferences("infinity_cobra_live",0).edit().clear().commit();
  }
  @After public void after() { if (controller != null) controller.destroy(); }
  void show(String mode,int width,int height,String name)throws Exception {
    a.getSharedPreferences("infinity_cobra_live",0).edit().putString("cobra_appearance_mode",mode).commit();
    Method method=Splash.class.getDeclaredMethod("showLegacyInfinityExperienceChooser");
    method.setAccessible(true);method.invoke(a);
    View decor=a.getWindow().getDecorView();controller.visible();
    decor.measure(View.MeasureSpec.makeMeasureSpec(width,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(height,View.MeasureSpec.EXACTLY));
    decor.layout(0,0,width,height);
    root=((ViewGroup)a.findViewById(android.R.id.content)).getChildAt(0);texts.clear();collect(root);
    assertTrue(a.getWindow().hasFeature(android.view.Window.FEATURE_NO_TITLE));
    for(TextView text:texts){
      assertNotNull(text.getText().toString(),text.getLayout());
      assertTrue("No vertical text clipping: "+text.getText(),text.getLayout().getHeight()<=text.getHeight()-text.getCompoundPaddingTop()-text.getCompoundPaddingBottom());
    }
    File dir=new File(System.getProperty("cobra.evidence","."));assertTrue(dir.isDirectory()||dir.mkdirs());
    Bitmap b=Bitmap.createBitmap(width,height,Bitmap.Config.ARGB_8888);decor.draw(new Canvas(b));
    try(FileOutputStream out=new FileOutputStream(new File(dir,"entry-204-"+name+".png"))){assertTrue(b.compress(Bitmap.CompressFormat.PNG,100,out));}b.recycle();
  }
  void collect(View v){if(v instanceof TextView)texts.add((TextView)v);if(v instanceof ViewGroup)for(int i=0;i<((ViewGroup)v).getChildCount();i++)collect(((ViewGroup)v).getChildAt(i));}
  TextView text(String prefix){for(TextView t:texts)if(t.getText().toString().startsWith(prefix))return t;throw new AssertionError(prefix);}
  void canvas(int color){assertEquals(color,((ColorDrawable)root.getBackground()).getColor());}
  void controls(){assertTrue(text("∞").isClickable());assertTrue(text("◈").isClickable());int count=0;for(TextView t:texts)if("⚙".contentEquals(t.getText())){assertTrue(t.isClickable());assertTrue(t.isFocusable());assertTrue(t.getWidth()>=44&&t.getHeight()>=44);count++;}assertEquals(2,count);}
  void bars(int color,boolean darkIcons){
    android.view.Window window=a.getWindow();View decor=window.getDecorView();
    assertEquals(color,window.getStatusBarColor());assertEquals(color,window.getNavigationBarColor());
    assertFalse(window.isStatusBarContrastEnforced());assertFalse(window.isNavigationBarContrastEnforced());
    assertEquals(color,((ColorDrawable)decor.getBackground()).getColor());
    int mask=android.view.WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS|android.view.WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS;
    assertEquals(darkIcons?mask:0,window.getInsetsController().getSystemBarsAppearance()&mask);
    assertEquals("Retain the fallback's fitted layout",0,decor.getSystemUiVisibility()&(View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN|View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION));
  }
  @Test public void lightWindowUsesMatchingBarPaintAndDarkIconsWithoutChangingFittedLayout()throws Exception{
    show("light",412,915,"light-bars");bars(Color.WHITE,true);
  }
  @Test public void darkWindowClearsStaleDarkIconsAndUsesBlackBarPaint()throws Exception{
    int mask=android.view.WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS|android.view.WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS;
    a.getWindow().getDecorView();a.getWindow().getInsetsController().setSystemBarsAppearance(mask,mask);
    show("dark",412,915,"dark-bars");bars(Color.BLACK,false);
  }
  @Test public void oledWindowKeepsBothBarsAndUnderlayTrulyBlack()throws Exception{
    show("oled",412,915,"oled-bars");bars(Color.BLACK,false);
  }
  @Test public void lightUsesWhiteCanvasBlueInkAndExistingControls()throws Exception{
    show("light",412,915,"light-cover");canvas(Color.WHITE);assertEquals(0xff101b2c,text("Choose Your").getCurrentTextColor());controls();
  }
  @Test public void darkUsesTrueBlackCanvasAndLegibleText()throws Exception{
    show("dark",412,915,"dark-cover");canvas(Color.BLACK);assertEquals(0xfff7faff,text("Choose Your").getCurrentTextColor());controls();
  }
  @Test public void oledKeepsTrueBlackCanvas()throws Exception{
    show("oled",412,915,"oled-cover");canvas(Color.BLACK);controls();
  }
  @Test @Config(qualifiers="w412dp-h915dp-port-notnight-mdpi")
  public void followSystemDayResolvesSameLightCanvas()throws Exception{
    show("system",412,915,"system-day");canvas(Color.WHITE);assertEquals("system",a.getSharedPreferences("infinity_cobra_live",0).getString("cobra_appearance_mode",""));
  }
  @Test @Config(qualifiers="w412dp-h915dp-port-night-mdpi")
  public void followSystemNightHonorsExistingOledPreference()throws Exception{
    a.getSharedPreferences("infinity_cobra_live",0).edit().putString("cobra_system_dark_variant","oled").commit();
    show("system",412,915,"system-night");canvas(Color.BLACK);Method m=Splash.class.getDeclaredMethod("chooserAppearanceMode");m.setAccessible(true);assertEquals("oled",m.invoke(a));
  }
  @Test public void unknownAppearanceFallsBackWithoutRewritingPreference()throws Exception{
    show("broken",412,915,"unknown-dark");canvas(Color.BLACK);assertEquals("broken",a.getSharedPreferences("infinity_cobra_live",0).getString("cobra_appearance_mode",""));
  }
  @Test @Config(qualifiers="w960dp-h540dp-land-mdpi")
  public void innerLandscapePreservesTwoSideBySideExperiences()throws Exception{
    show("light",960,540,"light-inner-landscape");controls();assertEquals(text("∞").getWidth(),text("◈").getWidth());
  }
  @Test @Config(qualifiers="w320dp-h720dp-port-mdpi")
  public void narrowCoverKeepsAllExistingControlsReachable()throws Exception{
    show("dark",320,720,"dark-narrow");controls();assertTrue(text("∞").getWidth()>0);assertTrue(text("◈").getWidth()>0);
  }
  @Test @Config(qualifiers="w320dp-h720dp-port-mdpi")
  public void largeFontGrowsAndScrollsRatherThanClippingOrShrinkingText()throws Exception{
    RuntimeEnvironment.setFontScale(1.5f);
    show("light",320,720,"light-narrow-font150");controls();
    assertTrue(root instanceof android.widget.ScrollView);
    android.widget.ScrollView scroll=(android.widget.ScrollView)root;
    assertTrue("Content fills the viewport and may grow when needed",scroll.getChildAt(0).getHeight()>=scroll.getHeight());
    assertEquals("Accessibility size is not reduced to fit",android.util.TypedValue.applyDimension(android.util.TypedValue.COMPLEX_UNIT_SP,32,a.getResources().getDisplayMetrics()),text("Choose Your").getTextSize(),.1f);
    TextView infinity=text("∞");assertTrue("INFINITY remains an unbroken word",infinity.getPaint().measureText("INFINITY")<=infinity.getWidth()-infinity.getCompoundPaddingLeft()-infinity.getCompoundPaddingRight());
    TextView cobra=text("◈");assertTrue("Powerful. remains an unbroken word",cobra.getPaint().measureText("Powerful.")<=cobra.getWidth()-cobra.getCompoundPaddingLeft()-cobra.getCompoundPaddingRight());
    scroll.fullScroll(View.FOCUS_DOWN);
  }
  @Test @Config(qualifiers="w320dp-h480dp-port-mdpi")
  public void largeFontShortWindowCanScrollToBothCardBottoms()throws Exception{
    RuntimeEnvironment.setFontScale(1.5f);show("dark",320,480,"dark-short-font150");controls();
    android.widget.ScrollView scroll=(android.widget.ScrollView)root;
    assertTrue(scroll.getChildAt(0).getHeight()>scroll.getHeight());
    scroll.setSmoothScrollingEnabled(false);assertTrue(scroll.fullScroll(View.FOCUS_DOWN));assertTrue(scroll.getScrollY()>0);
    android.graphics.Rect bounds=new android.graphics.Rect();assertTrue(text("∞").getGlobalVisibleRect(bounds));assertTrue(text("◈").getGlobalVisibleRect(bounds));
  }
  @Test public void cardPressAndReleaseRetainBoundsAndClickOwner()throws Exception{
    show("light",412,915,"light-before-press");TextView card=text("◈");int w=card.getWidth(),h=card.getHeight();card.setPressed(true);card.setPressed(false);assertEquals(w,card.getWidth());assertEquals(h,card.getHeight());assertTrue(card.performClick());assertEquals("com.projectinfinity.kodi.InfinityLiveActivity",Shadows.shadowOf(a).getNextStartedActivity().getComponent().getClassName());
  }
}
