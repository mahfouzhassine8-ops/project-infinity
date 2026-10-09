package com.projectinfinity.kodi;

import static org.junit.Assert.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.*;
import java.util.zip.*;
import org.json.*;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.annotation.Config;

@RunWith(RobolectricTestRunner.class)
@Config(sdk = 28)
public final class CheckpointCrashExportTest {
  private File source() throws Exception {
    File directory = new File(RuntimeEnvironment.getApplication().getFilesDir(), "infinity-native-diagnostics");
    assertTrue(directory.isDirectory() || directory.mkdirs());
    return new File(directory, "native-crash-last.txt");
  }
  private Map<String,byte[]> export() throws Exception {
    ByteArrayOutputStream output = new ByteArrayOutputStream();
    InfinityHealthExport.write(RuntimeEnvironment.getApplication(), output, "test");
    Map<String,byte[]> entries = new HashMap<>();
    try (ZipInputStream zip = new ZipInputStream(new ByteArrayInputStream(output.toByteArray()))) {
      ZipEntry entry;
      while ((entry = zip.getNextEntry()) != null) {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        byte[] buffer = new byte[8192]; int count;
        while ((count = zip.read(buffer)) != -1) bytes.write(buffer, 0, count);
        assertNull(entries.put(entry.getName(), bytes.toByteArray()));
      }
    }
    return entries;
  }
  private JSONObject availability(Map<String,byte[]> entries) throws Exception {
    JSONObject manifest = new JSONObject(new String(entries.get("exit-manifest.json"), StandardCharsets.UTF_8));
    JSONArray rows = manifest.getJSONArray("diagnostic_files");
    for (int i = 0; i < rows.length(); i++)
      if ("crash/native-crash-last.txt".equals(rows.getJSONObject(i).getString("path"))) return rows.getJSONObject(i);
    throw new AssertionError("Missing crash availability record");
  }
  @Test public void originalCrashIsExportedWithoutModification() throws Exception {
    File source = source();
    byte[] original = "pid=22881 tid=23093 pc=0x1234 signal=11\n".getBytes(StandardCharsets.UTF_8);
    Files.write(source.toPath(), original);
    Map<String,byte[]> entries = export();
    assertArrayEquals(original, entries.get("crash/native-crash-last.txt"));
    assertArrayEquals(original, Files.readAllBytes(source.toPath()));
    assertTrue(availability(entries).getBoolean("available"));
  }
  @Test public void absentCrashRemainsUnknown() throws Exception {
    Files.deleteIfExists(source().toPath());
    Map<String,byte[]> entries = export();
    assertFalse(entries.containsKey("crash/native-crash-last.txt"));
    assertFalse(availability(entries).getBoolean("available"));
    assertEquals("not_present", availability(entries).getString("status"));
  }
  @Test public void symlinkIsRejected() throws Exception {
    File source = source();
    Files.deleteIfExists(source.toPath());
    File other = new File(source.getParentFile(), "unrelated.txt");
    Files.write(other.toPath(), "private".getBytes(StandardCharsets.UTF_8));
    Files.createSymbolicLink(source.toPath(), other.toPath());
    try {
      Map<String,byte[]> entries = export();
      assertFalse(entries.containsKey("crash/native-crash-last.txt"));
      assertEquals("noncanonical_path_rejected", availability(entries).getString("status"));
    } finally { Files.deleteIfExists(source.toPath()); Files.deleteIfExists(other.toPath()); }
  }
}
