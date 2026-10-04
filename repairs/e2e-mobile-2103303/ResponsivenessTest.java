package com.projectinfinity.kodi;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=35)
public class ResponsivenessTest {
  @Test public void completedOrCancelledExitNeverOffersStallRecovery() {
    InfinityExitCompletion.Plan plan=new InfinityExitCompletion.Plan();
    assertFalse(plan.stalled(Long.MAX_VALUE));plan.requestNormal();
    assertTrue(plan.stalled(Long.MAX_VALUE));plan.cancelBeforeQuit();
    assertFalse(plan.stalled(Long.MAX_VALUE));plan.requestNormal();plan.stopped(false);plan.destroying();
    assertTrue(plan.stalled(Long.MAX_VALUE));plan.completed();assertFalse(plan.stalled(Long.MAX_VALUE));
  }
  @Test public void stallStartsOnceAndRecoversOnlyOnANewHeartbeat() {
    InfinityResponsiveness.Stall state=new InfinityResponsiveness.Stall();
    assertFalse(state.observe(5999,1000));assertTrue(state.observe(6000,1000));
    assertFalse(state.observe(7000,1000));assertEquals(-1,state.recover(1000));
    assertEquals(1000,state.recover(7100));assertEquals(-1,state.recover(7200));
    assertTrue(state.observe(12100,7100));
  }
  @Test public void anUnavailableNativeHeartbeatIsNotAFabricatedFreeze() {
    InfinityResponsiveness.Stall state=new InfinityResponsiveness.Stall();
    assertFalse(state.observe(900000,0));assertEquals(-1,state.started);
  }
}
