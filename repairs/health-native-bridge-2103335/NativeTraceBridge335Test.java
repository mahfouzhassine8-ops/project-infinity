package com.projectinfinity.kodi;

import static org.junit.Assert.*;
import android.app.Application;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.*;
import java.util.zip.*;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.annotation.Config;

@RunWith(RobolectricTestRunner.class)
@Config(sdk = 28)
public final class NativeTraceBridge335Test {
  private Application app() { return RuntimeEnvironment.getApplication(); }

  private void save(String name, String text) throws Exception {
    Files.write(new File(app().getFilesDir(), name).toPath(), text.getBytes(StandardCharsets.UTF_8));
  }

  private Map<String,byte[]> export(String report) throws Exception {
    ByteArrayOutputStream output = new ByteArrayOutputStream();
    InfinityHealthExport.write(app(), output, report);
    Map<String,byte[]> files = new LinkedHashMap<>();
    try (ZipInputStream zip = new ZipInputStream(new ByteArrayInputStream(output.toByteArray()))) {
      ZipEntry entry;
      while ((entry = zip.getNextEntry()) != null) {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        byte[] buffer = new byte[8192];
        int n;
        while ((n = zip.read(buffer)) != -1) bytes.write(buffer, 0, n);
        files.put(entry.getName(), bytes.toByteArray());
      }
    }
    return files;
  }

  @Test public void reportContainsCurrentAndPreviousCriticalTimeline() throws Exception {
    save("infinity-shutdown-native.jsonl.critical.previous",
        "{\"phase\":\"android.kodi_thread_join\",\"pid\":7645}\n");
    save("infinity-shutdown-native.jsonl.critical",
        "{\"phase\":\"jobs.waiting_active\",\"pid\":9605}\n");
    Map<String,byte[]> files = export("BASE REPORT");
    String report = new String(files.get("report.txt"), StandardCharsets.UTF_8);
    assertTrue(report.contains("BASE REPORT"));
    assertTrue(report.contains("Previous / failed native shutdown critical timeline"));
    assertTrue(report.contains("android.kodi_thread_join"));
    assertTrue(report.contains("Current native shutdown critical timeline"));
    assertTrue(report.contains("jobs.waiting_active"));
    assertArrayEquals(
        "{\"phase\":\"jobs.waiting_active\",\"pid\":9605}\n".getBytes(StandardCharsets.UTF_8),
        files.get("shutdown/critical.jsonl"));
    assertArrayEquals(
        "{\"phase\":\"android.kodi_thread_join\",\"pid\":7645}\n".getBytes(StandardCharsets.UTF_8),
        files.get("shutdown/critical.previous.jsonl"));
  }

  @Test public void missingCriticalFilesAreExplicitNotSuccess() throws Exception {
    Files.deleteIfExists(new File(app().getFilesDir(), "infinity-shutdown-native.jsonl.critical").toPath());
    Files.deleteIfExists(new File(app().getFilesDir(), "infinity-shutdown-native.jsonl.critical.previous").toPath());
    String report = new String(export("BASE").get("report.txt"), StandardCharsets.UTF_8);
    assertTrue(report.contains("[not present — absence is not a clean-exit verdict]"));
    assertFalse(report.contains("shutdown completed successfully"));
  }
}
