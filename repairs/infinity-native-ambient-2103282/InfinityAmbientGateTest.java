package com.projectinfinity.kodi;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import static org.junit.Assert.*;
@RunWith(RobolectricTestRunner.class) @Config(sdk=28)
public class InfinityAmbientGateTest {
  @Test public void missingPresentationLibraryFailsClosedWithoutAffectingActivity() throws Exception {
    InfinityKodiAmbientGate.update(true,false);
    java.lang.reflect.Field f=InfinityKodiAmbientGate.class.getDeclaredField("loaded");f.setAccessible(true);
    assertFalse(f.getBoolean(null));
    InfinityKodiAmbientGate.update(false,false);InfinityKodiAmbientGate.update(true,true);
    assertFalse(f.getBoolean(null));
  }
  @Test public void unexpectedNativeLinkFailureDisablesOnlyObserver() throws Exception {
    java.lang.reflect.Field f=InfinityKodiAmbientGate.class.getDeclaredField("loaded");f.setAccessible(true);f.setBoolean(null,true);
    InfinityKodiAmbientGate.update(true,false);assertFalse(f.getBoolean(null));
  }
}
