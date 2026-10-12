package com.projectinfinity.kodi;

import java.lang.reflect.Method;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import static org.junit.Assert.*;

/** Compiled-Java removal gate; the unchanged 206 cases exercise surviving behavior. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk = 28)
public class CobraVerifiedDeadweightTest {
  @Test public void exactUnusedPrivateDefinitionsAreAbsent() {
    Set<String> removed = new HashSet<>(Arrays.asList(
      "showLiveHome", "showRecents", "cobraGuideViewLabel", "cobraPlayerNow",
      "cobraPlayerNext", "closePlayerSettingsDrawer", "cycleAspectMode", "cobraSportsScore"));
    for (Method method : InfinityLiveActivity.class.getDeclaredMethods()) {
      assertFalse("Removed helper survived: " + method.getName(), removed.contains(method.getName()));
    }
  }
}
