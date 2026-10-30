package qa;

import android.graphics.Rect;
import android.os.SystemClock;
import com.android.uiautomator.core.Configurator;
import com.android.uiautomator.core.UiDevice;
import com.android.uiautomator.core.UiObject;
import com.android.uiautomator.core.UiObjectNotFoundException;
import com.android.uiautomator.core.UiSelector;
import com.android.uiautomator.testrunner.UiAutomatorTestCase;
import java.io.File;
import org.json.JSONArray;
import org.json.JSONObject;

/** Shell-run QA only. Queries native visible bounds and injects one real tap.
 * No application classes, callbacks, preferences, instrumentation APK or data access.
 */
public final class CobraNativeButtonProbe extends UiAutomatorTestCase {
    private static final String PACKAGE = "com.projectinfinity.kodi";
    private static final long PRESS_DEADLINE_MS = 3500;
    private static final int MIN_HIT_PX = 32;

    private static final class Hit {
        final Rect viewport, bounds;
        final String description;
        Hit(Rect viewport, Rect bounds, String description) {
            this.viewport = viewport; this.bounds = bounds; this.description = description;
        }
        boolean same(Hit other) {
            return other != null && viewport.equals(other.viewport) && bounds.equals(other.bounds)
                    && description.equals(other.description);
        }
    }

    private UiSelector action(String label) {
        return new UiSelector().packageName(PACKAGE).className("android.widget.Button")
                .description(label).enabled(true).clickable(true);
    }

    private void guardPro(UiDevice device) throws Exception {
        assertEquals("Wrong foreground package", PACKAGE, device.getCurrentPackageName());
        assertTrue("Native Pro heading missing", new UiObject(new UiSelector()
                .packageName(PACKAGE).text("Pro")).exists());
        assertTrue("Previous Pro source missing", new UiObject(new UiSelector()
                .packageName(PACKAGE).description("Previous Pro source")
                .enabled(true).clickable(true)).exists());
        assertTrue("Next Pro source missing", new UiObject(new UiSelector()
                .packageName(PACKAGE).description("Next Pro source")
                .enabled(true).clickable(true)).exists());
    }

    private UiObject inlineStrip() throws Exception {
        for (int index = 0; index < 4; index++) {
            UiObject strip = new UiObject(new UiSelector().packageName(PACKAGE)
                    .className("android.widget.HorizontalScrollView").enabled(true).instance(index));
            if (!strip.exists()) continue;
            if (strip.getChild(action("Channels")).exists()
                    || strip.getChild(action("Display")).exists()) continue;
            UiObject inlineAction = strip.getChild(new UiSelector().packageName(PACKAGE)
                    .className("android.widget.Button").enabled(true).clickable(true)
                    .descriptionMatches("^(Pause|Play|Favorite|Subtitles|Audio|Fullscreen|PiP|More)$"));
            if (inlineAction.exists()) return strip;
        }
        throw new UiObjectNotFoundException("Native Pro inline HorizontalScrollView missing");
    }

    private Hit visibleHit(UiObject strip, String label) throws Exception {
        UiObject target = strip.getChild(action(label));
        if (!target.exists()) return null;
        Rect viewport = strip.getVisibleBounds();
        Rect bounds = target.getVisibleBounds();
        String description = target.getContentDescription();
        assertEquals("Exact native target description changed", label, description);
        if (!bounds.intersect(viewport) || bounds.width() < MIN_HIT_PX
                || bounds.height() < MIN_HIT_PX) return null;
        return new Hit(viewport, bounds, description);
    }

    private JSONArray rect(Rect value) {
        return new JSONArray().put(value.left).put(value.top).put(value.right).put(value.bottom);
    }

    public void testPress() throws Exception {
        final String label = getParams().getString("label", "");
        final String direction = getParams().getString("direction", "left");
        final String forceText = getParams().getString("force", "false");
        final String capturePrefix = getParams().getString("capturePrefix", "");
        assertTrue("Unsupported target", label.equals("Fullscreen") || label.equals("More")
                || label.equals("PiP"));
        assertTrue("Unsupported scroll direction", direction.equals("left") || direction.equals("right"));
        assertTrue("Invalid force parameter", forceText.equals("true") || forceText.equals("false"));
        assertTrue("Unsafe or missing public QA capture basename",
                capturePrefix.matches("[A-Za-z0-9][A-Za-z0-9_-]{0,63}"));
        final File postXml = new File("/data/local/tmp", capturePrefix + ".xml");
        final File postPng = new File("/data/local/tmp", capturePrefix + ".png");
        assertFalse("Refuse stale public QA XML", postXml.exists());
        assertFalse("Refuse stale public QA PNG", postPng.exists());
        final int heroX = Integer.parseInt(getParams().getString("heroX", "-1"));
        final int heroY = Integer.parseInt(getParams().getString("heroY", "-1"));
        UiDevice device = getUiDevice();
        assertTrue("Hero coordinate outside current native display", heroX > 0 && heroY > 0
                && heroX < device.getDisplayWidth() && heroY < device.getDisplayHeight());
        Configurator config = Configurator.getInstance();
        long oldIdle = config.getWaitForIdleTimeout(), oldSelector = config.getWaitForSelectorTimeout();
        JSONObject report = new JSONObject().put("scope", "ON_DEVICE_PUBLIC_UIAUTOMATOR_COORDINATE_TAP")
                .put("package", PACKAGE).put("requested_label", label)
                .put("press_deadline_ms", PRESS_DEADLINE_MS).put("attempts", new JSONArray())
                .put("injection_attempted", false).put("shutdown", "NOT_RUN");
        JSONArray attempts = report.getJSONArray("attempts");
        try {
            // These change this short-lived QA bridge only. Application timers stay unchanged.
            config.setWaitForIdleTimeout(0).setWaitForSelectorTimeout(0);
            guardPro(device);
            long changedAt = SystemClock.uptimeMillis();
            assertTrue("Hero reveal coordinate injection failed", device.click(heroX, heroY));
            device.waitForIdle(80);
            boolean forcePending = forceText.equals("true");
            for (int attempt = 0; attempt < 7; attempt++) {
                guardPro(device);
                assertTrue("Native strip observation exceeded unchanged deadline",
                        SystemClock.uptimeMillis() - changedAt < PRESS_DEADLINE_MS);
                JSONObject step = new JSONObject().put("attempt", attempt)
                        .put("hero_coordinate", new JSONArray().put(heroX).put(heroY));
                attempts.put(step);
                UiObject strip;
                try {
                    strip = inlineStrip();
                } catch (UiObjectNotFoundException notVisibleYet) {
                    step.put("native_strip_not_observed", true);
                    SystemClock.sleep(50);
                    continue;
                }
                Rect viewport = strip.getVisibleBounds();
                assertTrue("Inline viewport too small", viewport.width() > 64 && viewport.height() > 32);
                step.put("viewport", rect(viewport));
                Hit first = visibleHit(strip, label);
                if (first == null || forcePending) {
                    int inset = Math.max(12, viewport.width() / 8);
                    int left = viewport.left + inset, right = viewport.right - inset;
                    int from = direction.equals("left") ? right : left;
                    int to = direction.equals("left") ? left : right;
                    assertTrue("Expired before native strip swipe",
                            SystemClock.uptimeMillis() - changedAt < PRESS_DEADLINE_MS);
                    assertTrue("Native strip swipe failed", device.swipe(from, viewport.centerY(),
                            to, viewport.centerY(), 30));
                    step.put("native_strip_swipe", direction);
                    // The native strip's ACTION_UP renews its original four-second timer.
                    // Observe again directly; revealing Hero here would move the viewport.
                    changedAt = SystemClock.uptimeMillis();
                    forcePending = false;
                    continue;
                }
                // Two fresh native observations, separated by one short frame opportunity.
                // Neither a host dump nor a reveal/layout mutation occurs after this measurement.
                SystemClock.sleep(32);
                guardPro(device);
                Hit second = visibleHit(inlineStrip(), label);
                step.put("first_bounds", rect(first.bounds));
                if (!first.same(second)) {
                    step.put("stale_bounds_rejected", true);
                    continue;
                }
                long before = SystemClock.uptimeMillis();
                step.put("native_elapsed_before_injection_ms", before - changedAt);
                assertTrue("Native visible target exceeded unchanged 3.5-second press deadline",
                        before - changedAt < PRESS_DEADLINE_MS);
                report.put("injection_attempted", true);
                boolean injected = device.click(second.bounds.centerX(), second.bounds.centerY());
                long elapsed = SystemClock.uptimeMillis() - changedAt;
                report.put("observed_native_label", second.description)
                        .put("visible_hit_bounds", rect(second.bounds)).put("viewport", rect(second.viewport))
                        .put("coordinate", new JSONArray().put(second.bounds.centerX()).put(second.bounds.centerY()))
                        .put("native_elapsed_ms", elapsed).put("injection_result", injected);
                assertTrue("Coordinate injection failed; do not retry uncertain press", injected);
                assertTrue("Press completed after unchanged deadline; do not retry uncertain press",
                        elapsed < PRESS_DEADLINE_MS);
                // Capture while this same bridge is connected, before runner teardown and
                // another host-launched hierarchy process can miss transient controls.
                // AOSP UiDevice.dumpWindowHierarchy(String) places this basename under
                // Environment.getDataDirectory()/local/tmp; no application data is accessed.
                report.put("post_ui_xml", postXml.getAbsolutePath())
                        .put("post_ui_png", postPng.getAbsolutePath());
                long captureStarted = SystemClock.uptimeMillis();
                SystemClock.sleep(80);
                device.dumpWindowHierarchy(capturePrefix + ".xml");
                report.put("post_xml_elapsed_after_injection_ms",
                        SystemClock.uptimeMillis() - changedAt - elapsed);
                assertTrue("Native post-press XML capture missing; do not retry press",
                        postXml.isFile() && postXml.length() > 0);
                assertTrue("Native post-press PNG capture failed; do not retry press",
                        device.takeScreenshot(postPng) && postPng.isFile() && postPng.length() > 0);
                report.put("post_capture_duration_ms", SystemClock.uptimeMillis() - captureStarted)
                        .put("post_xml_bytes", postXml.length()).put("post_png_bytes", postPng.length());
                report.put("status", "INJECTED_ONE_FRESH_NATIVE_VISIBLE_TARGET");
                return;
            }
            fail("No stable current native target after seven bounded attempts");
        } catch (Throwable failure) {
            report.put("status", "FAILED_CLOSED").put("error", failure.toString());
            if (failure instanceof Exception) throw (Exception) failure;
            if (failure instanceof Error) throw (Error) failure;
            throw new RuntimeException(failure);
        } finally {
            config.setWaitForIdleTimeout(oldIdle).setWaitForSelectorTimeout(oldSelector);
            System.out.println("COBRA_NATIVE_BUTTON_PROBE=" + report.toString());
        }
    }
}
