package com.projectinfinity.kodi;

import static org.junit.Assert.*;
import android.app.Application;
import android.content.ComponentName;
import android.content.Context;
import android.content.ContextWrapper;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import java.io.File;
import java.io.ByteArrayOutputStream;
import java.lang.reflect.Modifier;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.zip.ZipFile;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.annotation.Config;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=35, application=Application.class)
public class DecoyIdentityTest {
  private Context context() { return RuntimeEnvironment.getApplication(); }

  @Test public void installIdAndRetainedNativeClassNamespaceAreDistinct() {
    assertEquals(InfinityDecoyIdentity.INSTALL_ID, context().getPackageName());
    assertEquals("com.projectinfinity.kodi.Main", Main.class.getName());
    assertNotEquals(context().getPackageName(), Main.class.getPackage().getName());
    InfinityDecoyIdentity.requireDecoy(context());
  }

  @Test public void approvedPowerCommandIsOwnedByDecoyWithoutEditingItsInput() {
    Intent original = new Intent("com.projectinfinity.kodi.action.CLOSE_KODI")
        .setComponent(new ComponentName("com.projectinfinity.kodi",
                                       "com.projectinfinity.kodi.InfinityPowerControlActivity"));
    Intent next = InfinityDecoyIdentity.ownIntent(context(), original);
    assertEquals(InfinityDecoyIdentity.INSTALL_ID, next.getComponent().getPackageName());
    assertEquals(original.getComponent().getClassName(), next.getComponent().getClassName());
    assertEquals(original.getAction(), next.getAction());
    assertEquals("com.projectinfinity.kodi", original.getComponent().getPackageName());
  }

  @Test public void implicitSelfCommandCannotResolveToDailyInfinity() {
    Intent next = InfinityDecoyIdentity.ownIntent(context(),
        new Intent("com.projectinfinity.kodi.action.PLAYER_ROTATION_UNLOCKED"));
    assertEquals(InfinityDecoyIdentity.INSTALL_ID, next.getPackage());
  }

  @Test public void unexpectedProductionComponentIsRejected() {
    Intent attempted = new Intent().setComponent(new ComponentName(
        "com.projectinfinity.kodi", "com.projectinfinity.kodi.InfinityLiveActivity"));
    try { InfinityDecoyIdentity.ownIntent(context(), attempted); fail("Production route accepted"); }
    catch (SecurityException expected) {}
  }

  @Test public void productionContextCannotInitializeDecoy() {
    Context production = new ContextWrapper(context()) {
      @Override public String getPackageName() { return "com.projectinfinity.kodi"; }
    };
    try { InfinityDecoyIdentity.requireDecoy(production); fail("Production context accepted"); }
    catch (SecurityException expected) {}
  }

  @Test public void externalApplicationIntentRemainsUserOwned() {
    Intent external = new Intent(Intent.ACTION_VIEW).setPackage("com.android.chrome");
    Intent next = InfinityDecoyIdentity.ownIntent(context(), external);
    assertEquals(external.getPackage(), next.getPackage());
    assertEquals(external.getAction(), next.getAction());
  }

  @Test public void cachedEnginePackageNameLookupConstructsRegisteredReceiverSubclass() throws Exception {
    Class<?> bridge = InfinityDecoyIdentity.nativeReceiver(context());
    Object instance = context().getClassLoader().loadClass(context().getPackageName() + ".XBMCBroadcastReceiver")
        .getConstructor().newInstance();
    assertEquals(bridge, instance.getClass());
    assertEquals(XBMCBroadcastReceiver.class, bridge.getSuperclass());
    assertEquals(XBMCBroadcastReceiver.class,
        bridge.getMethod("onReceive", Context.class, Intent.class).getDeclaringClass());
    assertTrue(Modifier.isNative(XBMCBroadcastReceiver.class.getDeclaredMethod("_onReceive", Intent.class).getModifiers()));
    assertEquals(0, bridge.getDeclaredMethods().length);
  }

  @Test public void startupExportHasExperimentalIdentityAndOnlySelectedEvidence() throws Exception {
    Files.write(new File(context().getFilesDir(), InfinityDecoyDiagnostics.JAVA_CRASH).toPath(), "java crash fixture".getBytes(StandardCharsets.UTF_8));
    Files.write(new File(context().getFilesDir(), "unselected-userdata.txt").toPath(), "must not export".getBytes(StandardCharsets.UTF_8));
    try (ZipFile zip = new ZipFile(InfinityDecoyDiagnostics.collect(context()))) {
      assertNotNull(zip.getEntry("experimental-identity.json"));
      assertNotNull(zip.getEntry(InfinityDecoyDiagnostics.JAVA_CRASH));
      assertNotNull(zip.getEntry("android-exits.json"));
      assertNull(zip.getEntry("unselected-userdata.txt"));
      assertTrue(new String(zip.getInputStream(zip.getEntry("experimental-identity.json")).readAllBytes(), StandardCharsets.UTF_8)
          .contains(InfinityDecoyIdentity.INSTALL_ID));
    }
  }

  @Test public void crashRecorderOutputIsBounded() throws Exception {
    ByteArrayOutputStream output = new ByteArrayOutputStream();
    InfinityDecoyDiagnostics.BoundedOutput bounded = new InfinityDecoyDiagnostics.BoundedOutput(output, 8);
    bounded.write("abcdefghijklmnop".getBytes(StandardCharsets.UTF_8)); bounded.write(1);
    assertEquals("abcdefgh", output.toString("UTF-8"));
  }

  @Test public void diagnosticProviderRejectsOtherPathsAndProductionAuthorities() {
    assertTrue(InfinityDecoyDiagnosticsProvider.allowed(android.net.Uri.parse("content://" + InfinityDecoyDiagnostics.AUTHORITY + "/startup.zip")));
    for (String attempted : new String[]{
        "content://com.projectinfinity.kodi.startup-diagnostics/startup.zip",
        "content://" + InfinityDecoyDiagnostics.AUTHORITY + "/../files/settings.xml",
        "content://" + InfinityDecoyDiagnostics.AUTHORITY + "/startup.zip?path=other",
        "content://" + InfinityDecoyDiagnostics.AUTHORITY + "/startup.zip#other"})
      assertFalse(InfinityDecoyDiagnosticsProvider.allowed(android.net.Uri.parse(attempted)));
  }

  @Test public void diagnosticProviderRefusesWriteMode() {
    InfinityDecoyDiagnosticsProvider provider = new InfinityDecoyDiagnosticsProvider();
    try {
      provider.openFile(android.net.Uri.parse("content://" + InfinityDecoyDiagnostics.AUTHORITY + "/startup.zip"), "rw");
      fail("Writable diagnostics URI accepted");
    } catch (java.io.FileNotFoundException expected) { }
  }

  @Test public void startupExporterRejectsLinkedOutputDirectory() throws Exception {
    File folder = new File(context().getCacheDir().getCanonicalFile(), "experimental-startup-export");
    if (folder.isDirectory()) for (File child : folder.listFiles()) child.delete();
    folder.delete();
    File outside = Files.createTempDirectory("unowned-startup-export").toFile();
    Files.createSymbolicLink(folder.toPath(), outside.toPath());
    try { InfinityDecoyDiagnostics.archive(context()); fail("Linked export path accepted"); }
    catch (java.io.IOException expected) { }
    finally { Files.delete(folder.toPath()); outside.delete(); }
  }

  @Test public void ownedPathsArePreparedBeforeNativeWithoutSharedEnvironment() throws Exception {
    File root = Files.createTempDirectory("decoy-owned-paths").toFile().getCanonicalFile();
    File files = new File(root, "private/files"), cache = new File(root, "private/cache");
    File external = new File(root, "Android/data/" + InfinityDecoyIdentity.INSTALL_ID + "/files");
    files.mkdirs(); cache.mkdirs(); external.mkdirs();
    Context owned = new ContextWrapper(context()) {
      @Override public File getFilesDir() { return files; }
      @Override public File getCacheDir() { return cache; }
      @Override public File getExternalFilesDir(String type) { return external; }
      @Override public ApplicationInfo getApplicationInfo() {
        ApplicationInfo info = new ApplicationInfo(context().getApplicationInfo());
        info.dataDir = new File(root, "private").getAbsolutePath(); return info;
      }
    };
    String[] keys = {"xbmc.proploaded", "xbmc.data", "xbmc.home", "xbmc.temp", "xbmc.jsonPort"};
    String[] previous = new String[keys.length];
    for (int i=0;i<keys.length;i++) previous[i] = System.getProperty(keys[i]);
    try {
      System.setProperty("xbmc.data", "/unapproved/shared/profile");
      InfinityDecoyIdentity.configure(owned);
      assertEquals(external.getAbsolutePath(), System.getProperty("xbmc.data"));
      assertEquals(new File(cache, "apk").getAbsolutePath(), System.getProperty("xbmc.home"));
      assertEquals(new File(cache, "temp").getAbsolutePath(), System.getProperty("xbmc.temp"));
    } finally {
      for (int i=0;i<keys.length;i++) {
        if (previous[i] == null) System.clearProperty(keys[i]); else System.setProperty(keys[i], previous[i]);
      }
    }
  }

  @Test public void javaCrashRecorderPreservesTheAndroidFatalHandler() throws Exception {
    Thread.UncaughtExceptionHandler original = Thread.getDefaultUncaughtExceptionHandler();
    java.util.concurrent.atomic.AtomicBoolean delegated = new java.util.concurrent.atomic.AtomicBoolean();
    RuntimeException failure = new RuntimeException("startup fixture failure");
    Thread.setDefaultUncaughtExceptionHandler((thread, caught) -> {
      assertSame(failure, caught); delegated.set(true);
    });
    try {
      InfinityDecoyDiagnostics.installJavaCrashRecorder(context());
      Thread.getDefaultUncaughtExceptionHandler().uncaughtException(Thread.currentThread(), failure);
      assertTrue(delegated.get());
      String record = new String(Files.readAllBytes(new File(context().getFilesDir(), InfinityDecoyDiagnostics.JAVA_CRASH).toPath()), StandardCharsets.UTF_8);
      assertTrue(record.contains("startup fixture failure"));
      assertTrue(record.contains(InfinityDecoyIdentity.INSTALL_ID));
    } finally { Thread.setDefaultUncaughtExceptionHandler(original); }
  }
}
