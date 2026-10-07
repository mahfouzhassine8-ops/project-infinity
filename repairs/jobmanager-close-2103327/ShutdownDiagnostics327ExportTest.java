package com.projectinfinity.kodi;

import static org.junit.Assert.*;
import android.app.Application;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.time.Duration;
import java.util.*;
import java.util.zip.*;
import org.json.*;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.annotation.Config;
import org.robolectric.shadows.ShadowSystemClock;

/** Production exporter and occurrence clock for the 2103327 native identity. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk = 28)
public final class ShutdownDiagnostics327ExportTest {
  private Application app() { return RuntimeEnvironment.getApplication(); }
  private void save(String name, byte[] bytes) throws Exception {
    Files.write(new File(app().getFilesDir(), name).toPath(), bytes);
  }
  private Map<String,byte[]> export() throws Exception {
    ByteArrayOutputStream output = new ByteArrayOutputStream();
    InfinityHealthExport.write(app(), output, "test diagnostic summary");
    Map<String,byte[]> files = new LinkedHashMap<>();
    try (ZipInputStream zip = new ZipInputStream(new ByteArrayInputStream(output.toByteArray()))) {
      ZipEntry entry;
      while ((entry = zip.getNextEntry()) != null) {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        byte[] buffer = new byte[8192]; int n;
        while ((n = zip.read(buffer)) != -1) bytes.write(buffer, 0, n);
        assertNull("duplicate ZIP entry", files.put(entry.getName(), bytes.toByteArray()));
      }
    }
    return files;
  }
  private JSONObject manifest(Map<String,byte[]> files) throws Exception {
    return new JSONObject(new String(files.get("exit-manifest.json"), StandardCharsets.UTF_8));
  }
  private JSONObject row(JSONObject manifest, String path) throws Exception {
    JSONArray rows = manifest.getJSONArray("diagnostic_files");
    for (int i = 0; i < rows.length(); i++) {
      JSONObject row = rows.getJSONObject(i);
      if (path.equals(row.getString("path"))) return row;
    }
    throw new AssertionError("Missing diagnostic availability row: " + path);
  }
  @Test public void exportsCurrentPreviousAndJavaWithoutEditingInputs() throws Exception {
    byte[] current = "{\"kind\":\"begin\",\"phase\":\"example\"}\n".getBytes(StandardCharsets.UTF_8);
    byte[] previous = "prior capture\n".getBytes(StandardCharsets.UTF_8);
    byte[] java = "close event\n".getBytes(StandardCharsets.UTF_8);
    save("infinity-shutdown-native.jsonl", current);
    save("infinity-shutdown-native.jsonl.previous", previous);
    save("infinity-close-history.txt", java);
    save("provider-credentials.txt", "not collected".getBytes(StandardCharsets.UTF_8));
    Map<String,byte[]> files = export();
    assertArrayEquals(current, files.get("shutdown/native.jsonl"));
    assertArrayEquals(previous, files.get("shutdown/native.previous.jsonl"));
    assertArrayEquals(java, files.get("shutdown/java-close-history.txt"));
    assertArrayEquals(current, Files.readAllBytes(new File(app().getFilesDir(), "infinity-shutdown-native.jsonl").toPath()));
    assertFalse(files.containsKey("provider-credentials.txt"));
    assertTrue(row(manifest(files), "shutdown/native.jsonl").getBoolean("snapshot_only"));
  }
  @Test public void absentNativeIsReportedUnknownNotSuccess() throws Exception {
    Files.deleteIfExists(new File(app().getFilesDir(), "infinity-shutdown-native.jsonl").toPath());
    Map<String,byte[]> files = export();
    JSONObject m = manifest(files), r = row(m, "shutdown/native.jsonl");
    assertFalse(r.getBoolean("available"));
    assertEquals("not_present", r.getString("status"));
    assertFalse(files.containsKey("shutdown/native.jsonl"));
    assertTrue(m.getString("shutdown_trace_semantics").contains("not process death"));
  }
  @Test public void exportedTraceSizeIsBoundedAndFlagged() throws Exception {
    byte[] large = new byte[InfinityHealthExport.NATIVE_TRACE_LIMIT + 7];
    Arrays.fill(large, (byte)'x'); save("infinity-shutdown-native.jsonl", large);
    Map<String,byte[]> files = export();
    assertEquals(InfinityHealthExport.NATIVE_TRACE_LIMIT, files.get("shutdown/native.jsonl").length);
    assertTrue(row(manifest(files), "shutdown/native.jsonl").getBoolean("truncated"));
    assertEquals(large.length, new File(app().getFilesDir(), "infinity-shutdown-native.jsonl").length());
  }
  @Test public void exactBoundIsNotTruncated() throws Exception {
    ByteArrayOutputStream out = new ByteArrayOutputStream();
    assertFalse(InfinityHealthExport.copyBounded(new ByteArrayInputStream(new byte[]{1,2,3}), out, 3));
    assertArrayEquals(new byte[]{1,2,3}, out.toByteArray());
  }
  @Test public void excessAndZeroLimitAreExplicit() throws Exception {
    ByteArrayOutputStream out = new ByteArrayOutputStream();
    assertTrue(InfinityHealthExport.copyBounded(new ByteArrayInputStream(new byte[]{1,2,3}), out, 2));
    assertEquals(2, out.size());
    out.reset();
    assertTrue(InfinityHealthExport.copyBounded(new ByteArrayInputStream(new byte[]{1}), out, 0));
    assertEquals(0, out.size());
  }
  @Test public void nonProgressingBulkReadMakesBoundedSingleByteProgress() throws Exception {
    InputStream input = new ByteArrayInputStream(new byte[]{1,2,3}) {
      @Override public int read(byte[] b, int off, int len) { return 0; }
    };
    ByteArrayOutputStream out = new ByteArrayOutputStream();
    assertFalse(InfinityHealthExport.copyBounded(input, out, 3));
    assertArrayEquals(new byte[]{1,2,3}, out.toByteArray());
  }
  @Test public void occurrenceTimeDoesNotChangeWhenWriterWouldRunLater() throws Exception {
    InfinityExitCompletion.Event event = InfinityExitCompletion.Event.capture("exit.test.occurrence");
    long before = event.elapsedNs;
    ShadowSystemClock.advanceBy(Duration.ofMillis(300));
    assertEquals(before, event.elapsedNs);
    assertTrue(android.os.SystemClock.elapsedRealtimeNanos() - event.elapsedNs >= 300000000L);
    assertEquals(android.os.Process.myPid(), event.pid);
  }
  @Test public void diagnosticVersionAndSemanticsAreExplicit() throws Exception {
    JSONObject m = manifest(export());
    assertEquals("infinity-shutdown-2103327-v1", m.getString("shutdown_trace_engine"));
    assertTrue(m.getString("shutdown_trace_semantics").contains("Missing or truncated data is unknown"));
  }
  @Test public void highLevelCriticalAndGuardEvidenceExportIndependently() throws Exception {
    byte[] last="{\"phase\":\"jobs.waiting_active\"}\n".getBytes(StandardCharsets.UTF_8);
    save("infinity-shutdown-native.jsonl.critical",last);
    save("infinity-shutdown-native.jsonl.critical.previous",last);
    save("infinity-close-guard.jsonl",last);
    Map<String,byte[]> files=export();
    assertArrayEquals(last,files.get("shutdown/critical.jsonl"));
    assertArrayEquals(last,files.get("shutdown/critical.previous.jsonl"));
    assertArrayEquals(last,files.get("shutdown/android-guard.jsonl"));
    assertTrue(manifest(files).getString("shutdown_critical_semantics").contains("not a clean-exit verdict"));
  }
}
