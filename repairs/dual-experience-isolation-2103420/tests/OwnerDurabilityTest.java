package com.projectinfinity.kodi;

import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;

/** Focused host contract checks. No Android app, process kill or shutdown cycle. */
public final class OwnerDurabilityTest {
  static void check(boolean value,String why){if(!value)throw new AssertionError(why);}
  static String begin() {
    check(CombinedDurability.begin("ticket"),"begin");
    return CombinedDurability.sealIfReady("ticket");
  }
  public static void main(String[] args)throws Exception {
    String test=args[0];
    if(test.equals("independent_state")) {
      check(InfinityJavaWriteBarrier.ownerLock()!=CobraJavaWriteBarrier.ownerLock(),"shared lock");
      InfinityJavaWriteBarrier.begin("infinity");
      CobraJavaWriteBarrier.userEntry();
      check(InfinityJavaWriteBarrier.closing(),"Cobra entry reset Infinity");
      CobraJavaWriteBarrier.Resource saved=CobraJavaWriteBarrier.resource("Cobra setting");
      check(InfinityJavaWriteBarrier.pendingCount()==0,"Cobra write entered Infinity state");
      saved.finish(null);
    } else if(test.equals("pending_cobra_write")) {
      CobraJavaWriteBarrier.Resource saved=CobraJavaWriteBarrier.resource("accepted Cobra write");
      check(begin().isEmpty(),"unsaved Cobra write accepted");
      saved.finish(null);
      check(!CombinedDurability.sealIfReady("ticket").isEmpty(),"drained write refused");
    } else if(test.equals("pending_shell_write")) {
      ShellJavaWriteBarrier.Resource saved=ShellJavaWriteBarrier.resource("launch preference");
      check(begin().isEmpty(),"unsaved chooser preference accepted");
      saved.finish(null);check(!CombinedDurability.sealIfReady("ticket").isEmpty(),"drain");
    } else if(test.equals("failed_durability")) {
      CobraJavaWriteBarrier.Resource saved=CobraJavaWriteBarrier.resource("fsync");
      saved.finish("directory_sync_failed");check(begin().isEmpty(),"failure hidden");
      check(CombinedDurability.pending().contains("directory_sync_failed"),"failure lost");
    } else if(test.equals("accepted_continuation")) {
      CobraJavaWriteBarrier.Resource accepted=CobraJavaWriteBarrier.resource("queued");
      check(begin().isEmpty(),"queue invisible");
      try(CobraJavaWriteBarrier.Scope scope=accepted.continueOnThread()) {
        CobraJavaWriteBarrier.Resource nested=CobraJavaWriteBarrier.resource("queued output");
        nested.finish(null);check(CombinedDurability.sealIfReady("ticket").isEmpty(),"scope lost");
      }
      accepted.finish(null);check(!CombinedDurability.sealIfReady("ticket").isEmpty(),"continuation lost");
    } else if(test.equals("late_write_revokes_receipt")) {
      String proof=begin();check(!proof.isEmpty(),"seal");
      try { CobraJavaWriteBarrier.resource("late output");throw new AssertionError("late admission"); }
      catch(CobraJavaWriteBarrier.Closing expected) {}
      check(!CombinedDurability.authorized("ticket",proof),"stale receipt survived");
    } else if(test.equals("wrong_receipt")) {
      String proof=begin();check(!proof.isEmpty(),"seal");
      check(!CombinedDurability.authorized("wrong",proof),"wrong ticket");
      check(!CombinedDurability.authorized("ticket",proof+"x"),"wrong proof");
      check(!CombinedDurability.whileAuthorized("ticket","",()->{throw new AssertionError("terminated");}),"empty proof");
    } else if(test.equals("retained_cobra_keeps_writing")) {
      Object session=new Object();CobraRuntimeLease.acquire(session);
      String proof=begin();check(!proof.isEmpty(),"retained session blocks Infinity save");
      CobraJavaWriteBarrier.Resource saved=CobraJavaWriteBarrier.resource("ongoing Cobra progress");
      ShellJavaWriteBarrier.Resource launch=ShellJavaWriteBarrier.resource("Cobra chooser preference");
      launch.finish(null);
      check(CombinedDurability.authorized("ticket",proof),"retained write affects Infinity proof");
      check(!CombinedDurability.whileAuthorized("ticket",proof,()->{throw new AssertionError("killed Cobra");}),"retained process killed");
      saved.finish(null);CobraRuntimeLease.release(session);
      check(!CombinedDurability.whileAuthorized("ticket",proof,()->{throw new AssertionError("reused partial proof");}),"retained proof reinterpreted");
    } else if(test.equals("new_cobra_entry_revokes_kill")) {
      String proof=begin();Object activity=new Object();CobraRuntimeLease.acquire(activity);
      check(!CombinedDurability.whileAuthorized("ticket",proof,()->{throw new AssertionError("killed new entry");}),"entry race");
      CobraJavaWriteBarrier.userEntry();check(!CombinedDurability.authorized("ticket",proof),"owner receipt survived entry");
    } else if(test.equals("retained_coordinator_can_close_again")) {
      Object activity=new Object();CobraRuntimeLease.acquire(activity);
      String proof=begin();
      check(!CombinedDurability.finishCoordinator("ticket",proof,()->{throw new AssertionError("killed Cobra");}),"retention");
      check(!InfinityJavaWriteBarrier.closing()&&!ShellJavaWriteBarrier.closing(),"retained coordinator stuck");
      check(CombinedDurability.begin("next-ticket"),"next Infinity close rejected");
      check(!CombinedDurability.sealIfReady("next-ticket").isEmpty(),"next save proof rejected");
    } else if(test.equals("retained_failure_not_erased")) {
      Object activity=new Object();CobraRuntimeLease.acquire(activity);
      begin();InfinityJavaWriteBarrier.failure("durability","sync_failed");
      check(!CombinedDurability.finishCoordinator("ticket","",()->{throw new AssertionError("invalid kill");}),"invalid proof");
      check(InfinityJavaWriteBarrier.pending().contains("sync_failed"),"completion erased failed save");
      check(CombinedDurability.begin("next-ticket"),"next admission");
      check(CombinedDurability.sealIfReady("next-ticket").isEmpty(),"next close lost failure");
    } else if(test.equals("overlapping_cobra_leases")) {
      Object first=new Object(),second=new Object();
      CobraRuntimeLease.acquire(first);CobraRuntimeLease.acquire(second);
      CobraRuntimeLease.release(first);check(CobraRuntimeLease.active(),"old job released new job");
      CobraRuntimeLease.release(second);check(!CobraRuntimeLease.active(),"completed job retained process");
    } else if(test.equals("begin_is_atomic")) {
      CobraJavaWriteBarrier.begin("other");check(!CombinedDurability.begin("ticket"),"conflicting begin");
      check(!InfinityJavaWriteBarrier.closing()&&!ShellJavaWriteBarrier.closing(),"partial admission freeze");
    } else if(test.equals("all_locks_held_during_callback")) {
      String proof=begin();AtomicBoolean wrote=new AtomicBoolean();CountDownLatch tried=new CountDownLatch(1);
      Thread worker=new Thread(()->{
        tried.countDown();
        try { CobraJavaWriteBarrier.resource("racing write");wrote.set(true); }
        catch(CobraJavaWriteBarrier.Closing expected) {}
      });
      check(CombinedDurability.whileAuthorized("ticket",proof,()->{
        check(Thread.holdsLock(InfinityJavaWriteBarrier.ownerLock()),"Infinity lock absent");
        check(Thread.holdsLock(CobraJavaWriteBarrier.ownerLock()),"Cobra lock absent");
        check(Thread.holdsLock(ShellJavaWriteBarrier.ownerLock()),"shell lock absent");
        worker.start();
        try { check(tried.await(5,TimeUnit.SECONDS),"worker missing"); }catch(InterruptedException e){throw new AssertionError(e);}
        check(!wrote.get(),"write raced termination");
      }),"valid callback refused");
      worker.join(5000);check(!worker.isAlive()&&!wrote.get(),"late write admitted");
    } else if(test.equals("cancel_and_reentry")) {
      String proof=begin();CombinedDurability.cancel("unrelated");
      check(CombinedDurability.authorized("ticket",proof),"wrong cancel");
      CombinedDurability.cancel("ticket");check(!CombinedDurability.authorized("ticket",proof),"cancel ignored");
      check(!InfinityJavaWriteBarrier.closing()&&!CobraJavaWriteBarrier.closing()&&!ShellJavaWriteBarrier.closing(),"owner stuck");
    } else throw new AssertionError("unknown case");
    System.out.println("PASS "+test);
  }
}
