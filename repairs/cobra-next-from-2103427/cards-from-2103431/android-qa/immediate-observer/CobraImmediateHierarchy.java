package qa;

import android.app.UiAutomation;
import android.graphics.Point;
import android.graphics.Rect;
import android.os.Build;
import android.os.SystemClock;
import android.view.Display;
import android.view.accessibility.AccessibilityNodeInfo;
import android.view.accessibility.AccessibilityEvent;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;
import org.json.JSONArray;
import org.json.JSONObject;

/** QA process only: current platform hierarchy, no idle prerequisite or input. */
public final class CobraImmediateHierarchy {
  private static final String PACKAGE = "com.projectinfinity.kodi";
  private static final String JAR = "/data/local/tmp/CobraImmediateHierarchy.jar";
  private static final String PREFIX = "/system/framework/android.test.runner.jar:/system/framework/uiautomator.jar:";
  private static final String WRAPPER = "com.android.uiautomator.core.UiAutomationShellWrapper";
  private static final String DUMPER = "com.android.uiautomator.core.AccessibilityNodeInfoDumper";
  private static final long ROOT_READINESS_BUDGET_MS = 2000;
  private static final int MAX_ROOT_QUERIES = 16;
  private CobraImmediateHierarchy() {}

  /** Pure Java signal: no framework node/event is retained between queries. */
  static class ReadinessSignal {
    private long sequence;
    private int dropped;
    private final ArrayDeque<Object[]> pulses = new ArrayDeque<>();
    synchronized long generation() { return sequence; }
    synchronized void pulse(int type, int window, String name, long arrival, long eventTime) {
      sequence++;
      if (pulses.size() < 16) pulses.add(new Object[]{sequence, type, window, name, arrival, eventTime});
      else dropped++;
      notifyAll();
    }
    synchronized List<Object[]> drain() {
      List<Object[]> result = new ArrayList<>(pulses); pulses.clear(); return result;
    }
    synchronized int dropped() { return dropped; }
    synchronized boolean awaitAfter(long observed, long maxWaitMillis) throws InterruptedException {
      long deadline = System.nanoTime() + maxWaitMillis * 1000000L;
      while (sequence == observed) {
        long remaining = deadline - System.nanoTime();
        if (remaining <= 0) return false;
        wait(remaining / 1000000L, (int) (remaining % 1000000L));
      }
      return true;
    }
  }

  private static final class RootReadiness extends ReadinessSignal implements UiAutomation.OnAccessibilityEventListener {
    private final boolean knownNotice;
    RootReadiness(boolean knownNotice) { this.knownNotice = knownNotice; }
    @Override public void onAccessibilityEvent(AccessibilityEvent event) {
      try {
        int type = event.getEventType();
        String name = event.getPackageName() == null ? "" : event.getPackageName().toString();
        boolean owned = PACKAGE.equals(name) || knownNotice && "android".equals(name);
        boolean content = type == AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED
            || type == AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED || type == AccessibilityEvent.TYPE_VIEW_FOCUSED;
        if (type == AccessibilityEvent.TYPE_WINDOWS_CHANGED || owned && content)
          pulse(type, event.getWindowId(), name, SystemClock.uptimeMillis(), event.getEventTime());
      } finally {
        // UiAutomation delivers an obtained copy; its documented owner is this listener.
        event.recycle();
      }
    }
  }

  private static void require(boolean condition, String reason) {
    if (!condition) throw new IllegalStateException(reason);
  }
  private static byte[] read(File file) throws Exception {
    require(file.isFile() && file.length() <= 64 * 1024 * 1024, "Unexpected platform/QA file: " + file);
    ByteArrayOutputStream bytes = new ByteArrayOutputStream();
    try (FileInputStream stream = new FileInputStream(file)) {
      byte[] block = new byte[16384]; int count;
      while ((count = stream.read(block)) != -1) bytes.write(block, 0, count);
    }
    return bytes.toByteArray();
  }
  private static String hash(byte[] bytes) throws Exception {
    byte[] digest = MessageDigest.getInstance("SHA-256").digest(bytes);
    StringBuilder out = new StringBuilder();
    for (byte value : digest) out.append(String.format(java.util.Locale.ROOT, "%02x", value & 255));
    return out.toString();
  }
  private static JSONArray rect(Rect rect) {
    return new JSONArray().put(rect.left).put(rect.top).put(rect.right).put(rect.bottom);
  }
  private static Method method(Class<?> type, String name, Class<?>... parameters) throws Exception {
    Method method = type.getMethod(name, parameters);
    require(Modifier.isPublic(method.getModifiers()), "Nonpublic platform method: " + method);
    return method;
  }
  private static void surface(JSONObject report, String expectedJar) throws Exception {
    require(Build.VERSION.SDK_INT == 37, "Only the selected API37 emulator is admitted");
    String classpath = System.getProperty("java.class.path", "");
    report.put("application_classpath", classpath);
    report.put("bootclasspath", System.getenv("BOOTCLASSPATH"));
    report.put("bootclasspath_policy", "INHERITED_UNCHANGED; observer never sets it");
    require(classpath.equals(PREFIX + JAR), "Unexpected application classpath");
    require(expectedJar.matches("[0-9a-f]{64}"), "Expected QA JAR SHA256 is required");
    String actualJar = hash(read(new File(JAR)));
    report.put("QA_JAR_sha256", actualJar);
    require(actualJar.equals(expectedJar), "Actual QA JAR differs from compiled artifact");
    byte[] shell = read(new File("/system/bin/uiautomator"));
    String script = new String(shell, StandardCharsets.UTF_8);
    report.put("OS_uiautomator_script_sha256", hash(shell));
    String expectedLine = "CLASSPATH=/system/framework/android.test.runner.jar:${base}/framework/uiautomator.jar";
    require(script.contains(expectedLine), "OS UIAutomator script classpath differs from reviewed Android17 source");
    report.put("OS_script_classpath_line", expectedLine);
    JSONObject archives = new JSONObject();
    for (String path : new String[]{"/system/framework/android.test.runner.jar", "/system/framework/uiautomator.jar"})
      archives.put(path, hash(read(new File(path))));
    report.put("OS_JAR_sha256", archives);
    Class<?> wrapper = Class.forName(WRAPPER);
    Class<?> dumper = Class.forName(DUMPER);
    require(Modifier.isPublic(wrapper.getModifiers()) && Modifier.isPublic(dumper.getModifiers()), "Nonpublic platform class");
    require(Modifier.isPublic(wrapper.getConstructor().getModifiers()), "Nonpublic wrapper constructor");
    JSONArray methods = new JSONArray();
    methods.put(method(wrapper, "connect").toString());
    methods.put(method(wrapper, "getUiAutomation").toString());
    methods.put(method(wrapper, "setCompressedLayoutHierarchy", boolean.class).toString());
    methods.put(method(wrapper, "disconnect").toString());
    Method dump = method(dumper, "dumpWindowToFile", AccessibilityNodeInfo.class, File.class, int.class, int.class, int.class);
    require(Modifier.isStatic(dump.getModifiers()), "Nonstatic platform dumper");
    methods.put(dump.toString());
    Class<?> manager = Class.forName("android.hardware.display.DisplayManagerGlobal");
    methods.put(method(manager, "getInstance").toString());
    methods.put(method(manager, "getRealDisplay", int.class).toString());
    report.put("actual_public_methods", methods);
    report.put("platform_surface", "VERIFIED_PUBLIC_REFLECTION_SURFACE_NO_ACCESS_EXEMPTIONS");
  }
  private static boolean valid(AccessibilityNodeInfo root, Rect bounds, Point display, boolean knownNotice) {
    if (root == null || !root.refresh()) return false;
    root.getBoundsInScreen(bounds);
    String name = root.getPackageName() == null ? "" : root.getPackageName().toString();
    return (PACKAGE.equals(name) || knownNotice && "android".equals(name))
        && root.isVisibleToUser() && root.getWindowId() >= 0
        && Rect.intersects(bounds, new Rect(0, 0, display.x, display.y)) && bounds.width() > 0 && bounds.height() > 0;
  }
  private static AccessibilityNodeInfo acquire(UiAutomation automation, RootReadiness readiness,
      Point display, boolean knownNotice, JSONObject report) throws Exception {
    long started = SystemClock.uptimeMillis();
    JSONArray queries = new JSONArray(), events = new JSONArray();
    String outcome = "BUDGET_EXHAUSTED";
    try {
      for (int attempt = 1; attempt <= MAX_ROOT_QUERIES; attempt++) {
        if (SystemClock.uptimeMillis() - started >= ROOT_READINESS_BUDGET_MS) break;
        // Read before querying. awaitAfter compares under the same signal lock,
        // so a callback between null-return and waiting cannot be lost.
        long generation = readiness.generation();
        long before = SystemClock.uptimeMillis();
        AccessibilityNodeInfo root = automation.getRootInActiveWindow();
        long after = SystemClock.uptimeMillis();
        JSONObject query = new JSONObject().put("attempt", attempt).put("event_generation_before", generation)
            .put("query_started_uptime_ms", before).put("query_finished_uptime_ms", after)
            .put("available", root != null);
        queries.put(query);
        if (root != null) {
          Rect bounds = new Rect(); root.getBoundsInScreen(bounds);
          String name = root.getPackageName() == null ? "" : root.getPackageName().toString();
          query.put("root_package", name).put("window_id", root.getWindowId()).put("root_bounds", rect(bounds));
          boolean owned = PACKAGE.equals(name) || knownNotice && "android".equals(name);
          if (!owned || !root.isVisibleToUser() || root.getWindowId() < 0 || bounds.width() <= 0
              || bounds.height() <= 0 || !Rect.intersects(bounds, new Rect(0, 0, display.x, display.y))) {
            root.recycle(); throw new IllegalStateException("Current root package/visibility/window/bounds invalid");
          }
          if (after - started >= ROOT_READINESS_BUDGET_MS) {
            root.recycle(); outcome = "LATE_ROOT_DISCARDED";
            throw new IllegalStateException("Current-root query exceeded bounded readiness budget; late result discarded");
          }
          outcome = "CURRENT_ROOT_AVAILABLE";
          return root;
        }
        long remaining = ROOT_READINESS_BUDGET_MS - (SystemClock.uptimeMillis() - started);
        if (remaining <= 0) break;
        if (attempt == MAX_ROOT_QUERIES) { outcome = "QUERY_CEILING"; break; }
        if (!readiness.awaitAfter(generation, remaining)) break;
      }
      return null;
    } finally {
      for (Object[] pulse : readiness.drain()) events.put(new JSONObject()
          .put("arrival_sequence", pulse[0]).put("event_type", pulse[1]).put("window_id", pulse[2])
          .put("package", pulse[3]).put("callback_uptime_ms", pulse[4]).put("source_event_time_ms", pulse[5]));
      report.put("root_readiness_budget_ms", ROOT_READINESS_BUDGET_MS).put("root_query_ceiling", MAX_ROOT_QUERIES)
          .put("root_readiness_elapsed_ms", SystemClock.uptimeMillis() - started)
          .put("root_readiness_outcome", outcome).put("root_queries", queries).put("readiness_events", events)
          .put("readiness_events_dropped", readiness.dropped());
    }
  }
  private static int capture(File xml, JSONObject report, boolean knownNotice) throws Exception {
    require(xml.getAbsolutePath().matches("/sdcard/cobra-cards-baseline-[0-9]+-[0-9]+\\.xml"), "Unexpected unique XML path");
    require(!xml.exists(), "Existing XML refused");
    Class<?> wrapperClass = Class.forName(WRAPPER);
    Object wrapper = wrapperClass.getConstructor().newInstance();
    boolean connected = false;
    UiAutomation automation = null;
    AccessibilityNodeInfo root = null, current = null;
    try {
      method(wrapperClass, "connect").invoke(wrapper); connected = true;
      method(wrapperClass, "setCompressedLayoutHierarchy", boolean.class).invoke(wrapper, true);
      automation = (UiAutomation) method(wrapperClass, "getUiAutomation").invoke(wrapper);
      RootReadiness readiness = new RootReadiness(knownNotice);
      automation.setOnAccessibilityEventListener(readiness);
      Class<?> manager = Class.forName("android.hardware.display.DisplayManagerGlobal");
      Object displays = method(manager, "getInstance").invoke(null);
      Display display = (Display) method(manager, "getRealDisplay", int.class).invoke(displays, Display.DEFAULT_DISPLAY);
      require(display != null, "No current default display");
      Point size = new Point(); display.getRealSize(size); int rotation = display.getRotation();
      report.put("root_acquire_started_uptime_ms", SystemClock.uptimeMillis());
      root = acquire(automation, readiness, size, knownNotice, report);
      report.put("root_acquired_uptime_ms", SystemClock.uptimeMillis());
      if (root == null) {
        report.put("status", "ROOT_MISSING"); report.put("reason", "NULL_CURRENT_ACTIVE_ROOT");
        System.err.println("ERROR: null current active root after bounded event readiness; no XML produced"); return 3;
      }
      Rect bounds = new Rect(); root.getBoundsInScreen(bounds);
      require(valid(root, bounds, size, knownNotice), "Current root package/visibility/window/bounds invalid");
      int window = root.getWindowId();
      String initialPackage = root.getPackageName().toString();
      report.put("known_notice_root_allowed", knownNotice);
      report.put("root_package", String.valueOf(root.getPackageName())); report.put("window_id", window);
      report.put("root_bounds", rect(bounds)); report.put("display_size", new JSONArray().put(size.x).put(size.y));
      report.put("rotation", rotation);
      method(Class.forName(DUMPER), "dumpWindowToFile", AccessibilityNodeInfo.class, File.class, int.class, int.class, int.class)
          .invoke(null, root, xml, rotation, size.x, size.y);
      require(xml.isFile() && xml.length() > 0, "Platform dumper produced no nonempty XML");
      current = automation.getRootInActiveWindow();
      Rect after = new Rect(); if (current != null) current.getBoundsInScreen(after);
      Point afterSize = new Point(); display.getRealSize(afterSize);
      if (!valid(current, after, afterSize, knownNotice) || current.getWindowId() != window || !after.equals(bounds)
          || !initialPackage.contentEquals(current.getPackageName())
          || rotation != display.getRotation() || !size.equals(afterSize)) {
        require(xml.delete(), "Changed-window XML could not be removed");
        report.put("status", "ROOT_MISSING"); report.put("reason", "CURRENT_ACTIVE_WINDOW_CHANGED_DURING_DUMP");
        System.err.println("ERROR: current active window changed; XML discarded"); return 3;
      }
      report.put("dump_completed_uptime_ms", SystemClock.uptimeMillis());
      report.put("XML_sha256", hash(read(xml))); report.put("XML_bytes", xml.length());
      report.put("active_window_revalidated", true); report.put("status", "ROOT_CAPTURED");
      return 0;
    } finally {
      if (automation != null) automation.setOnAccessibilityEventListener(null);
      if (root != null) root.recycle(); if (current != null) current.recycle();
      if (connected) method(wrapperClass, "disconnect").invoke(wrapper);
    }
  }
  public static void main(String[] args) throws Exception {
    JSONObject report = new JSONObject(); report.put("observer", "IMMEDIATE_CURRENT_PLATFORM_ROOT_QA_ONLY");
    report.put("started_uptime_ms", SystemClock.uptimeMillis()); report.put("status", "ERROR");
    File metadata = null; boolean metadataAllowed = false; int code = 2;
    try {
      boolean preflight = args.length == 3 && args[0].equals("--preflight");
      boolean knownNotice = args.length == 5 && args[4].equals("--known-notice-root");
      require(preflight || (args.length == 4 || knownNotice) && args[0].equals("--dump"), "Expected --preflight metadata sha or --dump xml metadata sha [--known-notice-root]");
      metadata = new File(args[preflight ? 1 : 2]);
      require(metadata.getAbsolutePath().matches("/(?:sdcard/cobra-cards-baseline-[0-9]+-[0-9]+|data/local/tmp/CobraImmediateHierarchy-preflight)\\.json"), "Unexpected unique metadata path");
      require(!metadata.exists(), "Existing metadata refused");
      metadataAllowed = true;
      surface(report, args[preflight ? 2 : 3]);
      if (preflight) { report.put("status", "PREFLIGHT_PASS"); code = 0; }
      else code = capture(new File(args[1]), report, knownNotice);
    } catch (Throwable error) {
      report.put("status", "ERROR"); report.put("error", error.toString()); error.printStackTrace(System.err); code = 2;
    } finally {
      report.put("finished_uptime_ms", SystemClock.uptimeMillis()); report.put("exit_code", code);
      if (metadataAllowed && !metadata.exists()) {
        try (FileOutputStream output = new FileOutputStream(metadata)) {
          output.write((report.toString(2) + "\n").getBytes(StandardCharsets.UTF_8));
        }
      }
    }
    System.out.println(report.toString());
    System.exit(code);
  }
}
