package com.projectinfinity.kodi;
import static org.junit.Assert.*;
import android.app.Service;
import android.content.*;
import android.os.*;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.annotation.Config;

/** Actual state machine and service lifecycle under Android API 35 shadows.
 * This is not a claim about real cross-process priority or Samsung freezer state. */
@RunWith(RobolectricTestRunner.class) @Config(sdk=35)
public class CooperativeClose326Test {
  static final String T="11111111-1111-1111-1111-111111111111", O="22222222-2222-2222-2222-222222222222";
  Intent intent(long start){return new Intent().putExtra(InfinityCloseNativeLease.TICKET,T).putExtra(InfinityCloseNativeLease.TOKEN,O).putExtra(InfinityCloseNativeLease.PID,1234).putExtra(InfinityCloseNativeLease.START,start);}
  @Test public void guardedCloseWaitsForProtectionNotAndroidStop(){
    InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();assertTrue(p.requestGuardedClose());assertTrue(p.guardedWaiting());
    assertFalse(p.stopped(false));assertFalse(p.stopped(true));assertEquals(InfinityExitCompletion.Plan.Phase.WAITING_FOR_STOP,p.phase());
  }
  @Test public void readyClaimsOneQuitOnly(){
    InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();p.requestGuardedClose();assertTrue(p.claimGuardedDispatch());
    assertFalse(p.claimGuardedDispatch());assertEquals(InfinityExitCompletion.Plan.Phase.QUIT_QUEUED,p.phase());
  }
  @Test public void failedProtectionLeavesRunningNoDestruction(){
    InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();p.requestGuardedClose();assertTrue(p.cancelGuardedClose());
    assertFalse(p.pending());assertEquals(InfinityExitCompletion.Plan.Phase.RUNNING,p.phase());assertFalse(p.claimGuardedDispatch());
  }
  @Test public void protectionFailureCanBeRetried(){
    InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();p.requestGuardedClose();p.cancelGuardedClose();assertTrue(p.requestGuardedClose());assertTrue(p.claimGuardedDispatch());
  }
  @Test public void quitCannotBeCancelledAsThoughItNeverStarted(){
    InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();p.requestGuardedClose();p.claimGuardedDispatch();assertFalse(p.cancelGuardedClose());assertTrue(p.pending());
  }
  @Test public void duplicateRequestCannotRestartClose(){
    InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();p.requestGuardedClose();assertFalse(p.requestGuardedClose());p.claimGuardedDispatch();assertFalse(p.requestGuardedClose());
  }
  @Test public void elapsedTimeNeverCompletesClose(){
    InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();p.requestGuardedClose();p.claimGuardedDispatch();
    assertTrue(p.stalled(SystemClock.elapsedRealtime()+900000));assertTrue(p.pending());assertEquals(InfinityExitCompletion.Plan.Phase.QUIT_QUEUED,p.phase());
  }
  @Test public void forceStillDominatesCompletion(){
    InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();p.requestGuardedClose();assertTrue(p.force());assertFalse(p.claimGuardedDispatch());p.destroying();p.completed();assertEquals(InfinityExitCompletion.Plan.Phase.FORCED,p.phase());
  }
  @Test public void legacyPlanPathRemainsIndependent(){
    InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();assertTrue(p.requestNormal());assertTrue(p.stopped(false));assertFalse(p.claimGuardedDispatch());
  }
  @Test public void sessionRequiresExactValidIdentity(){
    assertNotNull(InfinityCloseGuardService.Session.from(intent(1000),1001));
    assertNull(InfinityCloseGuardService.Session.from(intent(1000).putExtra(InfinityCloseNativeLease.TOKEN,"../invalid"),1001));
    assertNull(InfinityCloseGuardService.Session.from(intent(1000).putExtra(InfinityCloseNativeLease.PID,-1),1001));
  }
  @Test public void staleAndFutureStartAreRejected(){
    assertNull(InfinityCloseGuardService.Session.from(intent(1000),20000));assertNull(InfinityCloseGuardService.Session.from(intent(1000),999));assertNull(InfinityCloseGuardService.Session.from(null,1000));
  }
  @Test public void fixedProtectionDeadlineCannotBeExtendedByDuplicate(){
    InfinityCloseGuardService.Session s=InfinityCloseGuardService.Session.from(intent(1000),1001);
    assertFalse(s.expired(150999));assertTrue(s.expired(151000));
    assertFalse(s.same(InfinityCloseGuardService.Session.from(intent(2000),2001)));assertTrue(s.same(InfinityCloseGuardService.Session.from(intent(1000),1002)));
  }
  @Test public void bindingNeverRequestsNativeAutoCreation(){assertEquals(0,InfinityCloseGuardService.BIND_FLAGS&Context.BIND_AUTO_CREATE);assertTrue((InfinityCloseGuardService.BIND_FLAGS&Context.BIND_IMPORTANT)!=0);}
  @Test public void identityBundlePreservesBothPidAndOwner(){
    Bundle b=InfinityCloseGuardService.Session.from(intent(1000),1000).bundle();assertEquals(1234,b.getInt(InfinityCloseNativeLease.PID));assertEquals(T,b.getString(InfinityCloseNativeLease.TICKET));assertEquals(O,b.getString(InfinityCloseNativeLease.TOKEN));
  }
  @Test public void nativeLeaseNeverStartsEngineWithoutExistingOwner(){
    android.app.Activity old=Main.MainActivity;Main.MainActivity=null;
    try{
      InfinityCloseNativeLease service=Robolectric.buildService(InfinityCloseNativeLease.class).create().get();
      assertEquals(Service.START_NOT_STICKY,service.onStartCommand(null,0,1));service.onDestroy();
    }finally{Main.MainActivity=(Main)old;}
  }
  @Test public void foregroundGuardRestartIsNonstickyAndTimeoutIsHandled(){
    InfinityCloseGuardService service=Robolectric.buildService(InfinityCloseGuardService.class).create().get();
    assertEquals(Service.START_NOT_STICKY,service.onStartCommand(null,0,1));
    service.onTimeout(1);service.onTimeout(1,2048);service.onDestroy();
  }
}
