"""Bound a graceful-exit observation; recovery remains an explicit user action."""
from native_controls import once


def apply(root):
    java=root/'tools/android/packaging/xbmc/src'
    p=java/'InfinityPowerMenuRoutes.java.in'
    p.write_text(once(p.read_text(),'static final String[] PROFILES = {"16x9"',
        'static final String[] PROFILES = {"unified","16x9"'))
    p=java/'InfinityExitCompletion.java.in';s=p.read_text()
    s=once(s,'  static final class Plan {','''  static final long STALL_BOUND_MS=15000;
  private static final java.util.concurrent.ScheduledExecutorService WATCH = Executors.newSingleThreadScheduledExecutor(r -> {
    Thread t=new Thread(r,"InfinityExitBound");t.setDaemon(true);return t;
  });
  static final class Plan {''')
    s=once(s,'    private Phase phase = Phase.RUNNING;','''    private Phase phase = Phase.RUNNING;
    private long requestedAt=-1;
    synchronized boolean stalled(long now) {
      return requestedAt>=0 && now-requestedAt>=STALL_BOUND_MS &&
          (phase==Phase.WAITING_FOR_STOP || phase==Phase.QUIT_QUEUED || phase==Phase.DESTROYING);
    }''')
    s=once(s,'      phase = Phase.WAITING_FOR_STOP; return true;',
        '      requestedAt=SystemClock.elapsedRealtime();phase = Phase.WAITING_FOR_STOP; return true;')
    s=once(s,'    record(owner, "exit.normal.requested");','''    record(owner, "exit.normal.requested");
    final WeakReference<Main> observed=new WeakReference<>(owner);
    WATCH.schedule(() -> {
      Main current=observed.get();
      if(current!=null && current.mInfinityExitPlan.stalled(SystemClock.elapsedRealtime()))
        record(current,"exit.graceful.boundExceeded.userRecoveryAvailable");
    }, STALL_BOUND_MS, java.util.concurrent.TimeUnit.MILLISECONDS);''')
    s=s.replace('// No timer, finish(), database write or kill on normal close.',
        '// The bounded observer records only. Normal close never calls finish() or kills the process.')
    s=once(s,'Normal close has NO timed force-stop fallback. Native cleanup and usable-frame timing require physical validation.',
        'Normal close is observed for 15 seconds without an automatic kill. If still closing, the chooser offers an explicit close-stalled-instance action. Native cleanup and usable-frame timing require physical validation.')
    p.write_text(s)
    p=java/'Splash.java.in';s=p.read_text()
    anchor='  private void showCobraRecovery(){'
    helper='''  private void showInfinityClosingRecovery(){
    Main owner=Main.MainActivity;
    if(owner==null || !owner.mInfinityExitPlan.stalled(android.os.SystemClock.elapsedRealtime()))return;
    cobraRecoveryDialog().setTitle("Infinity is still closing")
        .setMessage("Cleanup has not completed. You can keep waiting, or close this stalled instance and reopen Infinity. Closing it now may interrupt unfinished saves.")
        .setPositiveButton("Close stalled instance",(dialog,which)->{
          // A completion between presentation and the tap invalidates recovery.
          if(Main.MainActivity==owner && owner.mInfinityExitPlan.stalled(android.os.SystemClock.elapsedRealtime()))
            InfinityExitCompletion.requestForce(owner,this);
        }).setNegativeButton("Keep waiting",null).show();
  }

'''
    s=once(s,anchor,helper+anchor)
    # Only the three existing stale-owner gates. Never automatically restart Main.
    old='mInfinityStartupTrace.event("handoff.waitClosingOwner");'
    assert s.count(old)==3
    s=s.replace(old,old+'\n      showInfinityClosingRecovery();')
    p.write_text(s)
