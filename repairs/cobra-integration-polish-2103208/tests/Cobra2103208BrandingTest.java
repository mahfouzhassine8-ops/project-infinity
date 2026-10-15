package com.projectinfinity.kodi;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Rect;
import android.graphics.RectF;
import java.io.InputStream;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Renders the actual approved bitmap fixture, not a substitute test logo. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,manifest=Config.NONE)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
public class Cobra2103208BrandingTest {
  Bitmap mark;
  Field cache;
  Object previous;

  /** Explicit fixture seam for inherited manifest-free Robolectric render tests.
   * These contexts intentionally have no production APK resource table. */
  static void installApprovedArtwork() {
    try { new Cobra2103208BrandingTest().before(); }
    catch (Exception error) { throw new AssertionError("Cannot install approved Cobra artwork fixture", error); }
  }

  @Before public void before() throws Exception {
    try (InputStream stream = getClass().getResourceAsStream("/cobra-approved-mark.png")) {
      assertNotNull("CI must copy the successor's existing splash PNG to the fixture", stream);
      mark = BitmapFactory.decodeStream(stream);
    }
    assertNotNull(mark); assertEquals(288, mark.getWidth()); assertEquals(288, mark.getHeight());
    java.lang.reflect.Method bounds = CobraEmblem.class.getDeclaredMethod("contentBounds", Bitmap.class);
    bounds.setAccessible(true);
    Rect content = (Rect) bounds.invoke(null, mark);
    assertFalse(content.isEmpty());
    Class<?> art = Class.forName("com.projectinfinity.kodi.CobraEmblem$Artwork");
    Constructor<?> constructor = art.getDeclaredConstructor(Bitmap.class, Rect.class);
    constructor.setAccessible(true);
    cache = CobraEmblem.class.getDeclaredField("artwork"); cache.setAccessible(true);
    previous = cache.get(null); cache.set(null, constructor.newInstance(mark, content));
  }

  @After public void after() throws Exception { if (cache != null) cache.set(null, previous); }

  Bitmap render(int size, int backdrop, int tint, int alpha) {
    Bitmap output = Bitmap.createBitmap(size, size, Bitmap.Config.ARGB_8888);
    Canvas canvas = new Canvas(output); canvas.drawColor(backdrop);
    CobraEmblem.draw(canvas, new RectF(2, 2, size - 2, size - 2), tint, alpha);
    return output;
  }

  int count(Bitmap bitmap, boolean red) {
    int count = 0;
    for (int y = 0; y < bitmap.getHeight(); y++) for (int x = 0; x < bitmap.getWidth(); x++) {
      int p = bitmap.getPixel(x, y);
      if (Color.alpha(p) < 50) continue;
      if (red ? Color.red(p) > 170 && Color.red(p) > Color.green(p) * 1.4f && Color.red(p) > Color.blue(p) * 1.3f
              : Color.green(p) > 130 && Color.blue(p) > 130 && Color.red(p) < 80) count++;
    }
    return count;
  }

  @Test public void sourceContainsCyanInfinityAndDistinctRedEyes() {
    assertTrue(count(mark, false) > 1000); assertTrue(count(mark, true) > 10);
    assertEquals(0, Color.alpha(mark.getPixel(0, 0)));
    assertEquals(0, Color.alpha(mark.getPixel(144, 20)));
    assertEquals(0, Color.alpha(mark.getPixel(144, 270)));
  }

  @Test public void rendererPreservesRedEyesAndCyanRegardlessOfStatusTint() {
    Bitmap rendered = render(256, Color.TRANSPARENT, Color.GREEN, 255);
    assertTrue(count(rendered, true) > 10); assertTrue(count(rendered, false) > 1000);
    assertEquals(0, Color.alpha(rendered.getPixel(128, 20)));
    assertEquals(0, Color.alpha(rendered.getPixel(128, 235)));
  }

  @Test public void transparentMarkHasNoBlackDiscOnLightOrDarkSurfaces() {
    for (int background : new int[] { Color.rgb(244, 248, 252), Color.rgb(7, 22, 36) }) {
      Bitmap rendered = render(256, background, Color.WHITE, 255);
      assertEquals(background, rendered.getPixel(128, 20));
      assertEquals(background, rendered.getPixel(128, 235));
      assertEquals(background, rendered.getPixel(0, 128));
      assertEquals(background, rendered.getPixel(255, 128));
      assertTrue(count(rendered, true) > 10);
    }
  }

  @Test public void sourceAspectIsPreservedInsideTallViewBounds() {
    Bitmap rendered = render(100, Color.TRANSPARENT, Color.WHITE, 255);
    int top = 100, bottom = 0;
    for (int y = 0; y < 100; y++) for (int x = 0; x < 100; x++) {
      if (Color.alpha(rendered.getPixel(x, y)) < 20) continue;
      top = Math.min(top, y); bottom = Math.max(bottom, y);
    }
    assertTrue(top > 12); assertTrue(bottom < 87); assertTrue(bottom > top);
  }

  @Test public void zeroAlphaAndUnavailableArtworkAreSilentNotFallbackBranding() throws Exception {
    Bitmap hidden = render(100, Color.TRANSPARENT, Color.WHITE, 0);
    assertEquals(0, count(hidden, false)); assertEquals(0, count(hidden, true));
    cache.set(null, null);
    Bitmap missing = render(100, Color.TRANSPARENT, Color.WHITE, 255);
    for (int y = 0; y < 100; y++) for (int x = 0; x < 100; x++) assertEquals(0, Color.alpha(missing.getPixel(x, y)));
  }

  @Test public void smallLauncherSizedRenderingStillContainsBothBrandColors() {
    Bitmap rendered = render(48, Color.TRANSPARENT, Color.WHITE, 255);
    assertTrue(count(rendered, false) > 50); assertTrue(count(rendered, true) >= 2);
  }
}
