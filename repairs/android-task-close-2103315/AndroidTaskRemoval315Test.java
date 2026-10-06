package com.projectinfinity.kodi;

import static org.junit.Assert.*;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=28)
public final class AndroidTaskRemoval315Test {
  @Test public void closeRequestStaysPendingUntilAndroidDestroysTheOwner() {
    InfinityExitCompletion.Plan plan=new InfinityExitCompletion.Plan();
    assertTrue(plan.requestAndroidTaskRemoval());
    assertEquals(InfinityExitCompletion.Plan.Phase.ANDROID_TASK_REMOVAL,plan.phase());
    assertTrue(plan.pending());
    assertTrue(plan.stalled(android.os.SystemClock.elapsedRealtime()+InfinityExitCompletion.STALL_BOUND_MS));
    assertFalse(plan.stopped(false));
    plan.destroying();
    assertEquals(InfinityExitCompletion.Plan.Phase.DESTROYING,plan.phase());
    assertTrue(plan.pending());
    plan.completed();
    assertEquals(InfinityExitCompletion.Plan.Phase.COMPLETE,plan.phase());
    assertFalse(plan.pending());
  }

  @Test public void rejectedTaskRemovalCanReleaseTheGate() {
    InfinityExitCompletion.Plan plan=new InfinityExitCompletion.Plan();
    assertTrue(plan.requestAndroidTaskRemoval());
    assertTrue(plan.cancelAndroidTaskRemoval());
    assertEquals(InfinityExitCompletion.Plan.Phase.RUNNING,plan.phase());
    assertFalse(plan.pending());
  }
}
