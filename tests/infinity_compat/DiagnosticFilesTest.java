package com.projectinfinity.kodi;

import java.io.*;
import java.nio.file.*;
import java.util.Arrays;

/** Real JVM file-I/O fixture; does not emulate Android's exit-history service. */
public final class DiagnosticFilesTest {
  private static void require(boolean condition, String message) {
    if (!condition) throw new AssertionError(message);
  }
  public static void main(String[] args) throws Exception {
    Path root = Files.createTempDirectory("infinity-diagnostic-test-");
    File dest = root.resolve("report.trace").toFile();
    try {
      InfinityDiagnosticFiles.Result result = InfinityDiagnosticFiles.copyBounded(
          new ByteArrayInputStream(new byte[]{1,2,3}), dest, 5);
      require(result.bytes == 3 && !result.truncated, "short stream");
      result = InfinityDiagnosticFiles.copyBounded(new ByteArrayInputStream(new byte[]{4,5,6}), dest, 3);
      require(result.bytes == 3 && !result.truncated, "exact limit");
      result = InfinityDiagnosticFiles.copyBounded(new ByteArrayInputStream(new byte[]{7,8,9,10}), dest, 3);
      require(result.bytes == 3 && result.truncated, "truncated stream");
      require(Arrays.equals(Files.readAllBytes(dest.toPath()), new byte[]{7,8,9}), "bounded bytes");
      try {
        InfinityDiagnosticFiles.copyBounded(new ByteArrayInputStream(new byte[]{1}), dest, 0);
        throw new AssertionError("invalid limit accepted");
      } catch (IllegalArgumentException expected) { }
      InputStream broken = new InputStream() {
        public int read() throws IOException { throw new IOException("deliberate fixture failure"); }
      };
      try {
        InfinityDiagnosticFiles.copyBounded(broken, dest, 5);
        throw new AssertionError("read error suppressed");
      } catch (IOException expected) { }
      require(Arrays.equals(Files.readAllBytes(dest.toPath()), new byte[]{7,8,9}), "previous trace lost");
      require(root.toFile().list().length == 1, "temporary write leaked");
      result = InfinityDiagnosticFiles.copyBounded(new ByteArrayInputStream(new byte[0]), dest, 5);
      require(result.bytes == 0 && !result.truncated, "empty stream incorrectly described");
      System.out.println("PASS: seven file-I/O regression scenarios; Android service untested.");
    } finally {
      for (File file : root.toFile().listFiles()) file.delete();
      Files.delete(root);
    }
  }
}
