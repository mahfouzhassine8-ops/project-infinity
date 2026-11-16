package com.projectinfinity.kodi;

/** Selected host checks for the Repair 5 state machine; no Android/app execution. */
public final class InfinityVideoLockStateTest {
  private static int checks;

  private static void check(boolean value, String message) {
    checks++;
    if (!value) throw new AssertionError(message);
  }

  private static InfinityVideoLockState ready(long session) {
    InfinityVideoLockState s = new InfinityVideoLockState();
    check(s.lock(session), "new native session admitted");
    s.setForeground(true);
    s.setPictureInPicture(false);
    s.setViewportReady(true);
    s.setDialogFocused(true);
    return s;
  }

  private static long down(InfinityVideoLockState s, long now) {
    long token = s.beginHold(s.session(), 7, 1, true, now);
    check(token != 0, "one pointer inside focused affordance starts hold");
    return token;
  }

  public static void main(String[] args) {
    InfinityVideoLockState s = ready(10);
    long hold = down(s, 100);
    check(s.requestUnlock(10, hold, 2099) == 0, "1999ms cannot request unlock");
    long request = s.requestUnlock(10, hold, 2100);
    check(request != 0 && s.isLocked() && s.isUnlockPending(), "2000ms only requests; overlay stays locked");
    check(s.requestUnlock(10, hold, 2200) == 0, "completion callback is emitted once");
    s.release(10);
    check(s.isUnlockPending(), "release after genuine completion keeps restoration request");
    check(!s.confirmUnlocked(11, s.windowEpoch(), request), "wrong session cannot confirm");
    check(!s.confirmUnlocked(10, s.windowEpoch(), request + 1), "wrong request cannot confirm");
    check(s.confirmUnlocked(10, s.windowEpoch(), request) && !s.isLocked(), "matching native restoration confirms unlock");
    check(!s.confirmUnlocked(10, s.windowEpoch(), request), "duplicate native confirmation ignored");
    check(!s.lock(10), "retired session cannot reenter from stale callback");
    check(s.lock(11), "new native session can lock");
    check(s.lock(11), "duplicate session entry is idempotent");
    check(!s.lock(12) && s.owns(11), "different session cannot steal active lock");

    s = ready(20);
    hold = down(s, 100);
    s.release(20);
    check(s.requestUnlock(20, hold, 5000) == 0 && s.isLocked(), "early release defeats delayed completion");
    hold = down(s, 6000);
    check(!s.move(20, 7, 1, false, 7000), "moving outside cancels");
    check(s.requestUnlock(20, hold, 9000) == 0 && s.isLocked(), "outside gesture stays locked");
    check(s.beginHold(20, 7, 1, false, 10000) == 0, "outside DOWN cannot start hold");
    hold = down(s, 11000);
    check(s.beginHold(20, 7, 1, true, 11500) == 0, "duplicate DOWN cancels instead of extending hold");
    check(s.requestUnlock(20, hold, 14000) == 0, "duplicate DOWN invalidates queued completion");
    hold = down(s, 15000);
    check(!s.move(20, 8, 1, true, 15500), "replaced pointer cancels");
    check(s.requestUnlock(20, hold, 18000) == 0, "replaced pointer cannot inherit elapsed time");
    hold = down(s, 19000);
    check(!s.move(20, 7, 2, true, 19500), "second pointer cancels");
    check(s.requestUnlock(20, hold, 22000) == 0, "multiple pointers cannot complete");
    check(s.beginHold(20, 7, 2, true, 23000) == 0, "multi-pointer DOWN rejected");
    hold = down(s, 24000);
    check(!s.move(20, 7, 1, true, 23999), "regressing clock cancels");
    check(s.requestUnlock(20, hold, 27000) == 0, "clock regression cannot mature old token");

    for (int interruption = 0; interruption < 6; interruption++) {
      s = ready(30 + interruption);
      hold = down(s, 1000);
      interrupt(s, interruption);
      check(s.isLocked(), "lifecycle interruption retains session lock " + interruption);
      check(s.requestUnlock(s.session(), hold, 9000) == 0, "lifecycle invalidates hold " + interruption);
      restore(s);
      long fresh = down(s, 10000);
      check(s.requestUnlock(s.session(), hold, 13000) == 0, "old token cannot affect fresh gesture " + interruption);
      request = s.requestUnlock(s.session(), fresh, 12000);
      check(request != 0 && s.isLocked(), "fresh continuous hold can request after return " + interruption);
      interrupt(s, interruption);
      restore(s);
      check(!s.confirmUnlocked(s.session(), s.windowEpoch(), request) && s.isLocked(), "interruption cancels pending native confirmation " + interruption);
    }

    s = ready(50);
    hold = down(s, 100);
    check(s.move(50, 7, 1, true, 1100), "ordinary movement within original hit region remains valid");
    check(s.progress(50, hold, 1100) == .5f, "progress tracks elapsed monotonic hold time");
    request = s.requestUnlock(50, hold, 2100);
    check(s.rejectUnlock(50, request) && s.isLocked(), "failed native restoration stays locked");
    check(!s.confirmUnlocked(50, s.windowEpoch(), request), "late success from rejected request ignored");
    hold = down(s, 3000);
    check(!s.playbackStopped(49) && s.isHolding(), "stale stop cannot retire current session or hold");
    check(s.playbackStopped(50) && !s.isLocked(), "proven current stop retires");
    check(s.requestUnlock(50, hold, 6000) == 0, "stop invalidates hold callback");
    check(!s.playbackStopped(50), "duplicate stop ignored");

    s = ready(60);
    hold = down(s, 100);
    check(s.ownerDestroyed() && !s.isLocked(), "owner destruction retires current lock");
    check(s.requestUnlock(60, hold, 3000) == 0, "destroy invalidates completion");
    check(!s.lock(61), "destroyed owner cannot admit any later session");
    check(!s.ownerDestroyed(), "duplicate destruction does not retire twice");

    s = new InfinityVideoLockState();
    check(!s.lock(0) && !s.lock(-1), "invalid native generations rejected");
    check(s.lock(70), "lock can be retained before foreground readiness");
    check(s.beginHold(70, 7, 1, true, 0) == 0, "background/unfocused session cannot hold");
    check(s.isLocked(), "missing readiness is not inferred playback stop");
    restore(s);
    check(s.beginHold(69, 7, 1, true, 0) == 0 && s.owns(70), "stale event cannot alter session");
    hold = down(s, 0);
    check(s.requestUnlock(70, hold, -1) == 0 && s.isLocked(), "invalid completion clock stays locked");
    if (checks != 106) throw new AssertionError("Original 106 assertions must remain selected");
    readinessEpochContracts();
    System.out.println("PASS InfinityVideoLockStateTest " + checks + " assertions");
  }

  private static void readinessEpochContracts() {
    InfinityVideoLockState s = ready(80);
    long epoch = s.windowEpoch();
    check(epoch > 0, "genuine focused readiness has a nonzero epoch");
    restore(s);
    check(s.windowEpoch() == epoch, "duplicate ready facts do not mint a new epoch");
    long hold = down(s, 1000);
    long request = s.requestUnlock(80, hold, 3000);
    check(s.pendingRequest() == request && request != 0, "revocation can capture exact pending request before clear");
    check(s.canConfirmUnlocked(80, epoch, request), "matching ready tuple can be validated before COMMIT enqueue");
    check(s.canConfirmUnlocked(80, epoch, request) && s.isLocked() && s.pendingRequest() == request,
        "validation is read-only, so failed COMMIT enqueue leaves the input barrier locked");
    s.move(80, 7, 1, true, 3010);
    s.release(80);
    check(s.canConfirmUnlocked(80, epoch, request), "ordinary MOVE and UP after genuine completion preserve pending acknowledgement");
    s.setDialogFocused(false);
    check(s.pendingRequest() == 0 && !s.canConfirmUnlocked(80, epoch, request) && s.isLocked(),
        "focus revocation cancels pending acknowledgement and retains lock");
    s.setDialogFocused(true);
    long newEpoch = s.windowEpoch();
    check(newEpoch > epoch, "regained Dialog focus mints a new readiness epoch");
    hold = down(s, 4000);
    long freshRequest = s.requestUnlock(80, hold, 6000);
    check(!s.canConfirmUnlocked(80, epoch, freshRequest), "old window epoch cannot confirm even a fresh request token");
    check(!s.confirmUnlocked(80, newEpoch, request), "new window epoch cannot revive old request token");
    check(s.canConfirmUnlocked(80, newEpoch, freshRequest), "retry uses current epoch and fresh request");
    check(s.confirmUnlocked(80, newEpoch, freshRequest), "matching COMMIT candidate confirms after retry");

    s = ready(81);
    epoch = s.windowEpoch();
    hold = down(s, 1000);
    request = s.requestUnlock(81, hold, 3000);
    long capturedCancellation = s.pendingRequest();
    s.setViewportReady(false);
    check(capturedCancellation == request && s.pendingRequest() == 0,
        "viewport revocation preserves old token for Host notification before state clear");
    s.setViewportReady(true);
    check(s.windowEpoch() > epoch && !s.canConfirmUnlocked(81, epoch, request),
        "viewport restoration cannot accept old window acknowledgement");
    epoch = s.windowEpoch();
    s.setForeground(false);
    s.setPictureInPicture(true);
    s.setForeground(true);
    check(s.windowEpoch() == epoch && !s.canHold() && s.isLocked(),
        "foreground return while PiP is active does not falsely announce readiness");
    s.setPictureInPicture(false);
    check(s.windowEpoch() > epoch && s.canHold(), "leaving PiP creates one fresh readiness epoch");
    epoch = s.windowEpoch();
    s.setPictureInPicture(false);
    check(s.windowEpoch() == epoch, "duplicate PiP overload callbacks are idempotent");
  }

  private static void interrupt(InfinityVideoLockState s, int kind) {
    switch (kind) {
      case 0: s.setDialogFocused(false); break;
      case 1: s.configurationChanged(); break;
      case 2: s.setForeground(false); break;
      case 3: s.setPictureInPicture(true); break;
      case 4: s.setViewportReady(false); break;
      default: s.interrupt(); break; // ACTION_CANCEL / Back / interrupted gesture
    }
  }

  private static void restore(InfinityVideoLockState s) {
    s.setForeground(true);
    s.setPictureInPicture(false);
    s.setViewportReady(true);
    s.setDialogFocused(true);
  }
}
