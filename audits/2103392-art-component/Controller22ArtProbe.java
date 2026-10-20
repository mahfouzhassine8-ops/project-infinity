/* Test-only entrypoint for the ALREADY BUILT startup DEX. Never packaged in Infinity.
 * No Android Context, Kodi native library, installed profile or shutdown is invoked.
 */
import java.io.File;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class Controller22ArtProbe {
  private static final String CLASS = "com.projectinfinity.kodi.InfinityInstalledCheckpointInstaller";
  private static final String CANDIDATE = "2b54ba6ede1461cfcd0e1788de8c35a7cf63df582d9c8e03bb3c583890b8de54";
  private static final String BASELINE = "67e556c37a534be95789b3d88a9468219ecc5ea47d81dd5aab9b5911ba1c6573";
  private static final String SHARD2 = "d4df6604044e7cb66584229562186bf2ed8f0031d2d3efba03bba8ebe38934ca";
  private static final String CC = "script.infinity.commandcenter";
  private static final List<String> PASSED = new ArrayList<>();
  private static Method verifier;

  private Controller22ArtProbe() {}
  private static void require(boolean value, String reason) {
    if (!value) throw new AssertionError(reason);
  }
  private static void pass(String name, boolean value) {
    require(value, name); require(!PASSED.contains(name), "Duplicate case: " + name);
    PASSED.add(name); System.out.println("ART_CASE_PASS " + name);
  }
  private static String digest(byte[] data) throws Exception {
    StringBuilder text = new StringBuilder();
    for (byte b : MessageDigest.getInstance("SHA-256").digest(data)) {
      text.append(String.format(java.util.Locale.ROOT, "%02x", b & 255));
    }
    return text.toString();
  }
  private static String hash(Path path) throws Exception { return digest(Files.readAllBytes(path)); }
  private static boolean accepts(Path addons) throws Exception {
    Object result = verifier.invoke(null, addons.toFile());
    require(result instanceof Boolean, "Verifier did not return a boolean");
    return ((Boolean)result).booleanValue();
  }
  private static int androidApi() throws Exception {
    return Class.forName("android.os.Build$VERSION").getField("SDK_INT").getInt(null);
  }
  private static String androidRelease() throws Exception {
    return (String)Class.forName("android.os.Build$VERSION").getField("RELEASE").get(null);
  }
  private static void summary(String variant, int api) throws Exception {
    StringBuilder cases = new StringBuilder();
    for (String name : PASSED) {
      require(name.matches("[a-z0-9_:/.-]+"), "Unsafe case identifier");
      if (cases.length() > 0) cases.append(',');
      cases.append('"').append(name).append('"');
    }
    String release = androidRelease();
    require(release.matches("[0-9.]+"), "Unexpected platform release");
    System.out.println("ART_RESULT {\"variant\":\"" + variant + "\",\"api\":" + api +
        ",\"android_release\":\"" + release + "\",\"passed\":true,\"cases\":[" + cases +
        "],\"native_engine_loaded\":false,\"installed_app_started\":false," +
        "\"whole_process_shutdown_tested\":false,\"physical_fold_verified\":false}");
  }
  public static void main(String[] args) throws Exception {
    require(args.length == 3, "usage: probe baseline|candidate disposable_root expected_api");
    String variant = args[0];
    require(variant.equals("baseline") || variant.equals("candidate"), "Unknown variant");
    Path root = Paths.get(args[1]).toAbsolutePath();
    require(root.toString().startsWith("/data/local/tmp/infinity-cc22-art-"), "Not an isolated shell fixture");
    require(root.equals(root.toRealPath()), "Linked fixture root");
    int api = androidApi(); require(api == Integer.parseInt(args[2]), "Wrong Android API");
    Path dex = root.resolve(variant.equals("baseline") ? "baseline.dex" : "candidate.dex");
    require(hash(dex).equals(variant.equals("baseline") ? BASELINE : CANDIDATE), "Wrong tested DEX bytes");
    require(hash(root.resolve("classes2.dex")).equals(SHARD2), "Wrong unchanged second shard");
    // Classpath is provided by the host runner. Class.forName loads the original
    // package-private production class, not a test double or recompiled helper.
    Class<?> controller = Class.forName(CLASS);
    if (variant.equals("baseline")) {
      boolean absent = false;
      try { controller.getDeclaredMethod("verifyReviewedController22", File.class); }
      catch (NoSuchMethodException expected) { absent = true; }
      pass("baseline_has_no_cc22_verifier", absent);
      summary(variant, api); return;
    }
    verifier = controller.getDeclaredMethod("verifyReviewedController22", File.class);
    verifier.setAccessible(true);
    pass("component_fingerprint", hash(dex).equals(CANDIDATE));
    Path source = root.resolve("controller-input");
    Map<String,byte[]> original = new LinkedHashMap<>();
    for (String row : Files.readAllLines(root.resolve("pins.tsv"), StandardCharsets.UTF_8)) {
      String[] item = row.split("\t", -1);
      require(item.length == 2 && item[0].matches("[a-zA-Z0-9_./-]+") &&
          !item[0].startsWith("/") && !Arrays.asList(item[0].split("/")).contains("..") &&
          item[1].matches("[0-9a-f]{64}"), "Invalid pin row");
      byte[] bytes = Files.readAllBytes(source.resolve(item[0]));
      require(digest(bytes).equals(item[1]), "Fixture hash mismatch: " + item[0]);
      require(original.put(item[0], bytes) == null, "Duplicate fixture pin");
    }
    pass("fixture_fingerprints", original.size() == 13);
    Path addons = root.resolve("profile/addons");
    Path cc = addons.resolve(CC); Files.createDirectories(cc);
    for (Map.Entry<String,byte[]> row : original.entrySet()) {
      Path path = cc.resolve(row.getKey()); Files.createDirectories(path.getParent());
      require(!Files.exists(path), "Refusing fixture overwrite"); Files.write(path, row.getValue());
    }
    Path sentinel = root.resolve("profile/userdata-sentinel.bin");
    byte[] sentinelBytes = "unchanged disposable test sentinel".getBytes(StandardCharsets.UTF_8);
    require(!Files.exists(sentinel), "Sentinel already exists"); Files.write(sentinel, sentinelBytes);
    pass("reviewed_cc22_accepted", accepts(addons));
    for (Map.Entry<String,byte[]> row : original.entrySet()) {
      String name = row.getKey(); Path file = cc.resolve(name); byte[] bytes = row.getValue();
      byte[] changed = Arrays.copyOf(bytes, bytes.length + 1); changed[bytes.length] = 1;
      try { Files.write(file, changed); pass("changed:" + name, !accepts(addons)); }
      finally { Files.write(file, bytes); }
      Path moved = file.resolveSibling(file.getFileName().toString() + ".absent");
      try { Files.move(file, moved); pass("missing:" + name, !accepts(addons)); }
      finally { if (Files.exists(moved)) Files.move(moved, file); }
    }
    Path marker = cc.resolve("addon.xml"); byte[] markerBytes = original.get("addon.xml");
    try {
      Files.delete(marker); Files.createSymbolicLink(marker, source.resolve("addon.xml"));
      pass("symlinked_file_rejected", !accepts(addons));
    } finally { Files.deleteIfExists(marker); Files.write(marker, markerBytes); }
    Path linkedAddons = root.resolve("linked-addons"); Files.createDirectories(linkedAddons);
    Files.createSymbolicLink(linkedAddons.resolve(CC), cc);
    pass("symlinked_controller_root_rejected", !accepts(linkedAddons));
    try { Files.write(marker, new byte[4 * 1024 * 1024 + 1]); pass("oversized_file_rejected", !accepts(addons)); }
    finally { Files.write(marker, markerBytes); }
    pass("missing_controller_root_rejected", !accepts(root.resolve("missing-addons")));
    try {
      String legacy = new String(markerBytes, StandardCharsets.UTF_8);
      require(legacy.contains("version=\"0.3.5.22\""), "Wrong CC22 manifest fixture");
      Files.write(marker, legacy.replace("version=\"0.3.5.22\"", "version=\"0.3.5.21\"").getBytes(StandardCharsets.UTF_8));
      pass("legacy_cc21_rejected", !accepts(addons));
    } finally { Files.write(marker, markerBytes); }
    pass("restored_cc22_accepted", accepts(addons));
    boolean preserved = Arrays.equals(Files.readAllBytes(sentinel), sentinelBytes);
    for (Map.Entry<String,byte[]> row : original.entrySet()) {
      preserved &= Arrays.equals(row.getValue(), Files.readAllBytes(source.resolve(row.getKey())));
      preserved &= Arrays.equals(row.getValue(), Files.readAllBytes(cc.resolve(row.getKey())));
    }
    pass("fixture_and_sentinel_unchanged", preserved);
    pass("component_still_identical", hash(dex).equals(CANDIDATE));
    require(PASSED.size() == 37, "Incomplete candidate matrix"); summary(variant, api);
  }
}
