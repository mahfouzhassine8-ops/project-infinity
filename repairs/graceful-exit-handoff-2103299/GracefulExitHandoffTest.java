package com.projectinfinity.kodi;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.util.ReflectionHelpers;
import static org.junit.Assert.*;

/** Policy/lifecycle tests, not proof of real native shutdown or displayed frames. */
@RunWith(RobolectricTestRunner.class) @Config(sdk=35) @LooperMode(LooperMode.Mode.PAUSED)
public class GracefulExitHandoffTest {
  @After public void reset(){Main.MainActivity=null;}
  @Test public void ordinaryHomeDoesNotRequestQuit(){
    InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();
    assertFalse(p.stopped(false));assertFalse(p.pending());
    assertEquals(InfinityExitCompletion.Plan.Phase.RUNNING,p.phase());
  }
  @Test public void normalQuitIsQueuedOnlyAfterAndroidStopped(){
    InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();assertTrue(p.requestNormal());
    assertEquals(InfinityExitCompletion.Plan.Phase.WAITING_FOR_STOP,p.phase());
    assertTrue(p.pending());assertTrue(p.stopped(false));assertFalse(p.stopped(false));
    assertEquals(InfinityExitCompletion.Plan.Phase.QUIT_QUEUED,p.phase());
    p.destroying();p.completed();assertEquals(InfinityExitCompletion.Plan.Phase.COMPLETE,p.phase());
  }
  @Test public void configurationChangeCannotDispatchQuit(){
    InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();p.requestNormal();
    assertFalse(p.stopped(true));assertEquals(InfinityExitCompletion.Plan.Phase.WAITING_FOR_STOP,p.phase());
  }
  @Test public void repeatedClicksCannotQueueDuplicateQuit(){
    InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();assertTrue(p.requestNormal());
    for(int i=0;i<20;i++)assertFalse(p.requestNormal());
    assertTrue(p.stopped(false));for(int i=0;i<20;i++)assertFalse(p.stopped(false));
  }
  @Test public void rejectedTaskBackgroundDoesNotForceOrQuit(){
    InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();p.requestNormal();
    assertTrue(p.cancelBeforeQuit());assertFalse(p.stopped(false));assertFalse(p.pending());
    assertEquals(InfinityExitCompletion.Plan.Phase.RUNNING,p.phase());
  }
  @Test public void longGracefulCleanupNeverBecomesForced(){
    InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();p.requestNormal();p.stopped(false);p.destroying();
    org.robolectric.shadows.ShadowSystemClock.advanceBy(java.time.Duration.ofMinutes(5));
    assertEquals(InfinityExitCompletion.Plan.Phase.DESTROYING,p.phase());
  }
  @Test public void forceIsAnIndependentExplicitCommandAndIdempotent(){
    InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();p.requestNormal();
    assertTrue(p.force());assertFalse(p.force());assertFalse(p.stopped(false));
    p.destroying();p.completed();assertEquals(InfinityExitCompletion.Plan.Phase.FORCED,p.phase());
  }
  @Test public void closeRelaunchCycleResetsOnlyWithNewOwner(){
    for(int i=0;i<20;i++){
      InfinityExitCompletion.Plan old=new InfinityExitCompletion.Plan();old.requestNormal();old.stopped(false);old.destroying();old.completed();
      assertFalse(old.requestNormal());InfinityExitCompletion.Plan fresh=new InfinityExitCompletion.Plan();assertFalse(fresh.pending());assertTrue(fresh.requestNormal());
    }
  }
  @Test public void closingMainIsNotAnEligibleLiveOwner(){
    Main main=Robolectric.buildActivity(Main.class).get();ReflectionHelpers.setField(main,"mInfinityLaunchReady",true);
    assertSame(main,Main.infinityLiveActivity());main.mInfinityExitPlan.requestNormal();
    assertNull(Main.infinityLiveActivity());assertTrue(Main.infinityClosePending());
  }
  @Test public void destroyedOldOwnerDoesNotBlockFreshOwner(){
    Main old=Robolectric.buildActivity(Main.class).get();old.mInfinityExitPlan.requestNormal();
    Main fresh=Robolectric.buildActivity(Main.class).get();ReflectionHelpers.setField(fresh,"mInfinityLaunchReady",true);
    assertSame(fresh,Main.infinityLiveActivity());assertFalse(Main.infinityClosePending());
  }
  @Test public void unknownPowerActionNeverCreatesOrKillsMain(){
    android.content.Intent i=new android.content.Intent("unknown");
    org.robolectric.android.controller.ActivityController<InfinityPowerControlActivity> c=Robolectric.buildActivity(InfinityPowerControlActivity.class,i).create();
    assertTrue(c.get().isFinishing());assertNull(Main.MainActivity);
  }
  @Test public void diagnosticsDoNotClaimNativeOrPhysicalPass(){
    android.app.Activity a=Robolectric.buildActivity(android.app.Activity.class).setup().get();
    String report=InfinityExitCompletion.report(a);assertTrue(report.contains("NO timed force-stop"));assertTrue(report.contains("require physical validation"));
  }
}
