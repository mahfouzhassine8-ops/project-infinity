package com.projectinfinity.kodi;

import android.content.res.Configuration;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.view.ViewTreeObserver;
import android.widget.Toast;
import java.lang.ref.WeakReference;

/** Private bridge for Repair5. It owns no player, profile, preferences or network state. */
public final class InfinityVideoLockBridge implements InfinityVideoLockDialog.Host {
  private static final int READY = 1, REVOKE = 2, UNLOCK = 3, VALIDATE = 4,
      ENTRY_FAILED = 6;
  private static final Handler UI = new Handler(Looper.getMainLooper());
  private static WeakReference<Main> resumed = new WeakReference<>(null);
  private static InfinityVideoLockBridge current;
  private final Main owner;
  private final long session;
  private final InfinityVideoLockDialog dialog;
  private View viewport;
  private ViewTreeObserver pendingObserver;
  private ViewTreeObserver.OnPreDrawListener pendingDraw;
  private Runnable timeout;
  private boolean disposed;
  private boolean everReady;
  private int theme;
  private final View.OnLayoutChangeListener layout = (view, l, t, r, b, ol, ot, or, ob) -> refreshViewport();

  // Registered only by the active native InfinityVideoLock entry point.
  private static native boolean nativeTransition(long session, int operation, long epoch, long request);
  private static native boolean nativeCommit(long session, long grant);
  private static native boolean nativeOwnerGone(long session);

  private InfinityVideoLockBridge(Main owner, long session, int theme) {
    this.owner = owner;
    this.session = session;
    this.theme = theme;
    dialog = new InfinityVideoLockDialog(owner, this);
  }

  private static boolean eligible(Main owner) {
    return owner != null && resumed.get() == owner && !owner.isFinishing() &&
        !owner.isDestroyed() && owner.mInfinityExitPlan != null && !owner.mInfinityExitPlan.pending();
  }

  private static void main(Runnable action) {
    if (Looper.myLooper() == Looper.getMainLooper()) action.run();
    else UI.post(action);
  }

  /** Called asynchronously from Kodi's process thread; never starts another Activity. */
  public static void open(long token, int theme) {
    UI.post(() -> {
      Main owner = Main.MainActivity;
      if (current != null && current.owner == owner && current.session == token) {
        current.theme = theme;
        current.refreshViewport();
        current.dialog.setForeground(eligible(owner));
        return;
      }
      if (token <= 0 || !eligible(owner) || owner.mMainView == null ||
          !owner.mMainView.isAttachedToWindow() || owner.mMainView.getWidth() <= 0 ||
          owner.mMainView.getHeight() <= 0) {
        transition(token, ENTRY_FAILED, 0, 0);
        return;
      }
      if (current != null) current.dispose(true);
      InfinityVideoLockBridge next = new InfinityVideoLockBridge(owner, token, theme);
      current = next;
      next.attachViewport();
      next.refreshViewport();
      next.dialog.setForeground(true);
      next.dialog.setPictureInPicture(inPip(owner));
      if (!next.dialog.lock(token)) {
        transition(token, ENTRY_FAILED, 0, 0);
        next.dispose(false);
      }
    });
  }

  /** Native's positive or negative OSD restoration outcome, never a playback-state guess. */
  public static void restored(long token, long epoch, long request, long grant) {
    UI.post(() -> {
      InfinityVideoLockBridge bridge = current;
      if (bridge == null || bridge.session != token || bridge.disposed) return;
      if (!bridge.dialog.canConfirmUnlocked(token, epoch, request)) return;
      bridge.cancelTimeout();
      // No UI event can interleave this check, atomic native CAS and Java confirmation.
      // The JNI commit does no GUI work, callbacks, allocation, or cross-thread wait.
      if (grant != 0 && nativeCommit(token, grant)) {
        if (!bridge.dialog.confirmUnlocked(token, epoch, request))
          throw new IllegalStateException("Video lock commit violated same-UI-turn ownership");
        bridge.dispose(false);
      } else {
        bridge.dialog.rejectUnlock(token, epoch, request);
        bridge.unavailable();
      }
    });
  }

  public static void retired(long token) {
    UI.post(() -> {
      InfinityVideoLockBridge bridge = current;
      if (bridge == null || bridge.session != token) return;
      bridge.dialog.playbackStopped(token);
      bridge.dispose(false);
    });
  }

  public static void validated(long token, int theme) {
    UI.post(() -> {
      InfinityVideoLockBridge bridge = current;
      if (bridge == null || bridge.session != token || bridge.disposed) return;
      bridge.theme = theme;
      bridge.applyTheme();
    });
  }

  /** Hooked only into Main's already-admitted normal resume path. */
  public static void onResume(Main owner) {
    main(() -> {
      if (owner.mInfinityExitPlan == null || owner.mInfinityExitPlan.pending()) return;
      resumed = new WeakReference<>(owner);
      InfinityVideoLockBridge bridge = current;
      if (bridge == null || bridge.owner != owner) return;
      bridge.attachViewport();
      bridge.dialog.setPictureInPicture(inPip(owner));
      bridge.dialog.setForeground(true);
      bridge.afterLayout();
      transition(bridge.session, VALIDATE, 0, 0);
    });
  }

  public static void onPause(Main owner) {
    main(() -> {
      if (resumed.get() == owner) resumed.clear();
      InfinityVideoLockBridge bridge = current;
      if (bridge != null && bridge.owner == owner) bridge.dialog.setForeground(false);
    });
  }

  public static void onConfigurationChanged(Main owner) {
    main(() -> {
      InfinityVideoLockBridge bridge = current;
      if (bridge == null || bridge.owner != owner) return;
      bridge.dialog.configurationChanged();
      bridge.attachViewport();
      bridge.afterLayout();
      transition(bridge.session, VALIDATE, 0, 0);
    });
  }

  public static void onPictureInPictureChanged(Main owner, boolean active) {
    main(() -> {
      InfinityVideoLockBridge bridge = current;
      if (bridge == null || bridge.owner != owner) return;
      bridge.dialog.setPictureInPicture(active);
      if (!active) bridge.afterLayout();
      transition(bridge.session, VALIDATE, 0, 0);
    });
  }

  public static void onPlaybackChanged(Main owner) {
    main(() -> {
      InfinityVideoLockBridge bridge = current;
      if (bridge == null || bridge.owner != owner) return;
      // An old OnStop notification must never retire a newly locked/replayed item.
      // Kodi validates the CURRENT shared-item lifetime on its process thread.
      transition(bridge.session, VALIDATE, 0, 0);
    });
  }

  public static void onDestroy(Main owner) {
    main(() -> {
      if (resumed.get() == owner) resumed.clear();
      InfinityVideoLockBridge bridge = current;
      if (bridge != null && bridge.owner == owner) bridge.dispose(true);
    });
  }

  private static boolean inPip(Main owner) {
    return Build.VERSION.SDK_INT >= 26 && owner.isInPictureInPictureMode();
  }

  private static boolean transition(long token, int operation, long epoch, long request) {
    if (token <= 0) return false;
    try { return nativeTransition(token, operation, epoch, request); }
    catch (LinkageError unavailable) { return false; } // Never treat missing native as unlock.
  }

  @Override public void onReady(long token, long epoch) {
    if (!disposed && token == session) {
      everReady = true;
      transition(token, READY, epoch, 0);
    }
  }

  @Override public void onWindowUnavailable(long token) {
    if (disposed || token != session) return;
    if (!everReady) {
      transition(token, ENTRY_FAILED, 0, 0);
      if (eligible(owner))
        Toast.makeText(owner, "Video lock window could not open.", Toast.LENGTH_SHORT).show();
    } else {
      // A previously established lock is never retired for focus/window loss.
      // The normal resumed/configuration path retries its input window.
      unavailable();
    }
  }

  @Override public void onNotReady(long token, long epoch, long cancelledRequest) {
    if (disposed || token != session) return;
    cancelTimeout();
    transition(token, REVOKE, epoch, cancelledRequest);
  }

  @Override public void onUnlockRequested(long token, long epoch, long request) {
    if (disposed || token != session) return;
    cancelTimeout();
    // Resend the actual current readiness before a new request. This also permits
    // a safe retry if an earlier bounded queue refusal prevented its first READY.
    if (!transition(token, READY, epoch, 0) || !transition(token, UNLOCK, epoch, request)) {
      dialog.rejectUnlock(token, epoch, request);
      unavailable();
      return;
    }
    timeout = () -> {
      timeout = null;
      if (disposed || current != this || !dialog.canConfirmUnlocked(token, epoch, request)) return;
      dialog.rejectUnlock(token, epoch, request);
      unavailable();
    };
    UI.postDelayed(timeout, 5000);
  }

  @Override public void onRetired(long token) {
    if (!disposed && token == session) retireNativeOwner(token);
  }

  private static void retireNativeOwner(long token) {
    try { nativeOwnerGone(token); }
    catch (LinkageError unavailable) { /* Engine teardown cannot manufacture an unlock ACK. */ }
  }

  private void applyTheme() {
    boolean light = theme == 1 || (theme != 0 &&
        (owner.getResources().getConfiguration().uiMode & Configuration.UI_MODE_NIGHT_MASK) == Configuration.UI_MODE_NIGHT_NO);
    dialog.setColors(light ? 0xeef5f9fc : 0xee0a1117,
        light ? 0xff0f191f : 0xffebf3f8, 0xff00c1e0);
  }

  private void attachViewport() {
    View next = owner.mMainView;
    if (viewport == next) return;
    cancelDraw();
    if (viewport != null) viewport.removeOnLayoutChangeListener(layout);
    viewport = next;
    if (viewport != null) viewport.addOnLayoutChangeListener(layout);
  }

  private void refreshViewport() {
    if (disposed) return;
    applyTheme();
    if (viewport == null || !viewport.isAttachedToWindow()) {
      dialog.setPlayerViewport(0, 0, 0, 0);
      return;
    }
    int[] location = new int[2];
    viewport.getLocationOnScreen(location);
    dialog.setPlayerViewport(location[0], location[1], viewport.getWidth(), viewport.getHeight());
  }

  private void afterLayout() {
    cancelDraw();
    if (viewport == null) return;
    pendingObserver = viewport.getViewTreeObserver();
    pendingDraw = () -> { cancelDraw(); refreshViewport(); return true; };
    pendingObserver.addOnPreDrawListener(pendingDraw);
    viewport.invalidate();
  }

  private void cancelDraw() {
    if (pendingObserver != null && pendingObserver.isAlive() && pendingDraw != null)
      pendingObserver.removeOnPreDrawListener(pendingDraw);
    pendingObserver = null;
    pendingDraw = null;
  }

  private void cancelTimeout() {
    if (timeout != null) UI.removeCallbacks(timeout);
    timeout = null;
  }

  private void unavailable() {
    if (!disposed && eligible(owner))
      Toast.makeText(owner, "Player controls did not respond. Video stays locked; hold again to retry.", Toast.LENGTH_SHORT).show();
  }

  private void dispose(boolean notifyNative) {
    if (disposed) return;
    disposed = true;
    if (notifyNative) retireNativeOwner(session);
    cancelTimeout();
    cancelDraw();
    if (viewport != null) viewport.removeOnLayoutChangeListener(layout);
    viewport = null;
    dialog.ownerDestroyed();
    if (current == this) current = null;
  }
}
