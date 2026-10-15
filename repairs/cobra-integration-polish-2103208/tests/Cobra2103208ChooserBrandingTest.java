package com.projectinfinity.kodi;

import android.app.AlertDialog;
import android.app.Application;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.view.View;
import java.io.ByteArrayInputStream;
import java.lang.reflect.Constructor;
import org.json.JSONObject;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.shadows.ShadowAlertDialog;
import static org.junit.Assert.*;

/** Actual Splash ExperienceMark views; no native startup or entry-flow rewrite. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103208ChooserBrandingTest {
  final CobraVisualRuntimeTest themes = new CobraVisualRuntimeTest();
  final ExperienceChooserUiTest chooser = new ExperienceChooserUiTest();
  Cobra2103208BrandingTest branding;
  Splash activity;

  @Before public void before() throws Exception {
    themes.setup();
    branding = new Cobra2103208BrandingTest(); branding.before();
    ExperienceChooserUiTest.reflect(); activity = chooser.activity();
  }
  @After public void after() throws Exception {
    chooser.closeWindows(); themes.cleanup(); if (branding != null) branding.after();
  }

  View mark(boolean cobra, int ink, int width, int height) throws Exception {
    Constructor<?> constructor = Class.forName("com.projectinfinity.kodi.Splash$ExperienceMark")
        .getDeclaredConstructor(Splash.class, boolean.class, int.class);
    constructor.setAccessible(true);
    View view = (View) constructor.newInstance(activity, cobra, ink);
    view.measure(View.MeasureSpec.makeMeasureSpec(width, View.MeasureSpec.EXACTLY),
        View.MeasureSpec.makeMeasureSpec(height, View.MeasureSpec.EXACTLY));
    view.layout(0, 0, width, height); return view;
  }
  Bitmap draw(View view) {
    Bitmap result = Bitmap.createBitmap(view.getWidth(), view.getHeight(), Bitmap.Config.ARGB_8888);
    view.draw(new Canvas(result)); return result;
  }
  Bitmap originalInfinity(int width, int height, int ink) {
    // Byte-for-byte same curve coordinates/stroke setup as the locked Infinity branch.
    Bitmap result = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888);
    Canvas canvas = new Canvas(result); Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    int w = width, h = height; float cx = w / 2f, cy = h / 2f;
    paint.setStyle(Paint.Style.STROKE); paint.setStrokeCap(Paint.Cap.ROUND);
    paint.setStrokeJoin(Paint.Join.ROUND); paint.setStrokeWidth(Math.max(2, Math.min(w, h) * .065f)); paint.setColor(ink);
    Path path = new Path(); float rx = w * .33f, ry = h * .25f;
    path.moveTo(cx, cy);
    path.cubicTo(cx - rx * .45f, cy - ry, cx - rx, cy - ry, cx - rx, cy);
    path.cubicTo(cx - rx, cy + ry, cx - rx * .45f, cy + ry, cx, cy);
    path.cubicTo(cx + rx * .45f, cy - ry, cx + rx, cy - ry, cx + rx, cy);
    path.cubicTo(cx + rx, cy + ry, cx + rx * .45f, cy + ry, cx, cy);
    canvas.drawPath(path, paint); return result;
  }

  @Test public void cobraChooserUsesExactSharedCyanRedMarkInsteadOfOldVectorOrInk() throws Exception {
    for (int ink : new int[] {Color.WHITE, Color.BLACK, Color.MAGENTA}) {
      for (int[] size : new int[][] {{112, 78}, {56, 39}}) {
        Bitmap actual = draw(mark(true, ink, size[0], size[1]));
        Bitmap expected = Bitmap.createBitmap(size[0], size[1], Bitmap.Config.ARGB_8888);
        CobraEmblem.draw(new Canvas(expected), new RectF(0, 0, size[0], size[1]), Color.WHITE, 255);
        assertTrue("Chooser draws the same approved resource as all other Cobra marks", actual.sameAs(expected));
        assertTrue(branding.count(actual, false) > 60); assertTrue(branding.count(actual, true) >= 2);
        assertEquals(0, Color.alpha(actual.getPixel(0, 0)));
      }
    }
  }

  @Test public void infinityFallbackRemainsPixelIdenticalToOriginalAtBothSizesAndPalettes() throws Exception {
    for (int ink : new int[] {Color.WHITE, Color.rgb(24, 35, 49), Color.CYAN}) {
      for (int[] size : new int[][] {{112, 78}, {56, 39}}) {
        Bitmap actual = draw(mark(false, ink, size[0], size[1]));
        assertTrue("Infinity geometry and color must remain unchanged", actual.sameAs(originalInfinity(size[0], size[1], ink)));
        assertEquals(0, branding.count(actual, true));
      }
    }
  }

  @Test public void installedThemeCannotReplaceCobraButInfinityAndOtherThemeSlotsRemainActive() throws Exception {
    JSONObject data = themes.root("chooser-brand-preservation");
    data.getJSONObject("base").put("images", new JSONObject()
        .put("chooser.mark.cobra", "badge").put("chooser.mark.infinity", "badge")
        .put("chooser.background", "badge"));
    data.getJSONObject("base").put("colors", new JSONObject().put("palette.accent", "#123456"));
    CobraVisualTheme theme = CobraVisualTheme.install(themes.context,
        new ByteArrayInputStream(themes.zip(themes.withImage(data, Color.MAGENTA))));
    themes.activate(theme);
    String pointer = CobraVisualTheme.readPointer(themes.context).toString();
    Bitmap cobra = draw(mark(true, Color.WHITE, 112, 78));
    assertTrue(branding.count(cobra, false) > 200); assertTrue(branding.count(cobra, true) > 2);
    Bitmap infinity = draw(mark(false, Color.WHITE, 112, 78));
    assertEquals(Color.MAGENTA, infinity.getPixel(56, 39));
    assertEquals(0, branding.count(infinity, true));
    CobraVisualRenderer renderer = new CobraVisualRenderer(activity);
    Bitmap backdrop = Bitmap.createBitmap(112, 78, Bitmap.Config.ARGB_8888);
    assertTrue(renderer.draw(new Canvas(backdrop), "chooser.background", 0, 0, 112, 78, "cover"));
    assertEquals(Color.MAGENTA, backdrop.getPixel(56, 39));
    assertEquals(0xff123456, renderer.color("palette.accent", 0));
    assertEquals(theme.id, CobraVisualTheme.load(themes.context).id);
    assertEquals(pointer, CobraVisualTheme.readPointer(themes.context).toString());
  }

  @Test public void actualChooserKeepsCardTagsSettingsAndCobraEntryIntent() throws Exception {
    themes.activate(themes.install(themes.root("chooser-controls-preserved")));
    chooser.show(activity, false, 412, 915);
    View cobra = chooser.tag(activity, "experience-mark-cobra");
    View infinity = chooser.tag(activity, "experience-mark-infinity");
    assertNotNull(cobra); assertNotNull(infinity);
    assertTrue(branding.count(draw(cobra), true) > 2);
    assertFalse(cobra.isClickable()); assertFalse(cobra.isFocusable());
    assertEquals(View.IMPORTANT_FOR_ACCESSIBILITY_NO, cobra.getImportantForAccessibility());
    assertNotNull(chooser.tag(activity, "experience-card-infinity"));
    assertTrue(chooser.tag(activity, "experience-settings-cobra").performClick());
    AlertDialog dialog = ShadowAlertDialog.getLatestAlertDialog(); assertNotNull(dialog);
    assertEquals("Cobra options", Shadows.shadowOf(dialog).getTitle().toString()); dialog.dismiss();
    chooser.shot(activity, "cobra208-chooser-approved-brand-412x915");
    assertTrue(chooser.tag(activity, "experience-card-cobra").performClick());
    Intent launch = Shadows.shadowOf(activity).getNextStartedActivity(); assertNotNull(launch);
    assertEquals("com.projectinfinity.kodi.InfinityLiveActivity", launch.getComponent().getClassName());
    assertEquals("cobra", launch.getStringExtra("infinity_live_profile"));
  }
}
