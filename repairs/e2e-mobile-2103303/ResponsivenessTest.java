package com.projectinfinity.kodi;
import org.junit.Test;
import static org.junit.Assert.*;

public class ResponsivenessTest {
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
