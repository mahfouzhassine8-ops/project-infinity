package com.projectinfinity.kodi;

import static org.junit.Assert.*;
import android.app.Application;
import android.content.ComponentName;
import android.content.Context;
import android.content.ContextWrapper;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import java.io.File;
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
}
