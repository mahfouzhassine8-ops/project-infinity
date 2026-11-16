package com.projectinfinity.kodi;

import android.app.Activity;
import android.app.Dialog;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Rect;
import android.graphics.RectF;
import android.graphics.drawable.ColorDrawable;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.MotionEvent;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;

/**
 * A separate, focused input window above the native player. No engine or persistence calls.
 * Every entry point and Host callback runs on the main Looper. The native host owns session IDs.
 */
final class InfinityVideoLockDialog {
  interface Host {
    /** The focused lock window has a valid affordance; native 1199 may now be hidden safely. */
    void onReady(long session, long windowEpoch);
    /** Revoke this readiness lease before hiding/reflow or clearing its pending request. */
    void onNotReady(long session, long windowEpoch, long cancelledRequest);
    /** Showing this exact session's input window failed; candidate cleanup has completed. */
    void onWindowUnavailable(long session);
    /** A genuine hold completed. Keep native lock enforcement until restoration is acknowledged. */
    void onUnlockRequested(long session, long windowEpoch, long request);
    /** This exact session retired after positively identified playback stop or owner destruction. */
    void onRetired(long session);
  }

  private final Activity owner;
  private final Host host;
  private final Handler handler = new Handler(Looper.getMainLooper());
  private final InfinityVideoLockState state = new InfinityVideoLockState();
  private final Rect playerOnScreen = new Rect();
  private boolean haveViewport;
  private long announcedSession;
  private long announcedEpoch;
  private boolean announcing;
  private boolean revoking;
  private boolean destroyed;
  private LockWindow window;
  private Runnable tick;
  private int surfaceColor = 0xe60a1720;
  private int foregroundColor = Color.WHITE;
  private int accentColor = 0xff00d9ff;

  InfinityVideoLockDialog(Activity owner, Host host) {
    requireMain();
    if (owner == null || host == null) throw new IllegalArgumentException("owner and host required");
    this.owner = owner;
    this.host = host;
  }

  /** The caller passes the native player's actual screen bounds, not physical display metrics. */
  void setPlayerViewport(int screenLeft, int screenTop, int width, int height) {
    requireMain();
    Rect next = new Rect(screenLeft, screenTop, screenLeft + width, screenTop + height);
    boolean valid = width > 0 && height > 0 && next.right > next.left && next.bottom > next.top;
    if (!valid || !haveViewport || !playerOnScreen.equals(next)) {
      revokeReady();
      state.setViewportReady(false);
      stopTick();
    }
    haveViewport = valid;
    playerOnScreen.set(next);
    if (window != null) window.content.updateAffordance();
  }

  /** Theme values are supplied by the host; this class never reads or writes a theme preference. */
  void setColors(int surface, int foreground, int accent) {
    requireMain();
    surfaceColor = surface;
    foregroundColor = foreground;
    accentColor = accent;
    redraw();
  }

  boolean lock(long nativeSession) {
    requireMain();
    if (destroyed || !state.lock(nativeSession)) return false;
    showIfNeeded();
    return true;
  }

  boolean isLocked(long nativeSession) {
    requireMain();
    return state.owns(nativeSession);
  }

  void setForeground(boolean foreground) {
    requireMain();
    if (!foreground) revokeReady();
    state.setForeground(foreground);
    updateVisibility();
  }

  void setPictureInPicture(boolean active) {
    requireMain();
    if (active) revokeReady();
    state.setPictureInPicture(active);
    updateVisibility();
  }

  /** Rotation/fold cancels a gesture, and requires a new actual player viewport before holding. */
  void configurationChanged() {
    requireMain();
    revokeReady();
    state.configurationChanged();
    haveViewport = false;
    stopTick();
    if (window != null) {
      window.fit();
      window.content.requestLayout();
      window.content.invalidate();
    }
  }

  /** Only the matching native restoration acknowledgement can release the input window. */
  boolean canConfirmUnlocked(long nativeSession, long windowEpoch, long request) {
    requireMain();
    return !revoking && announcedSession == nativeSession && announcedEpoch == windowEpoch &&
        state.canConfirmUnlocked(nativeSession, windowEpoch, request);
  }

  /** Call in the same UI turn after canConfirmUnlocked and successful native COMMIT enqueue. */
  boolean confirmUnlocked(long nativeSession, long windowEpoch, long request) {
    requireMain();
    if (!canConfirmUnlocked(nativeSession, windowEpoch, request) ||
        !state.confirmUnlocked(nativeSession, windowEpoch, request)) return false;
    hideWindow();
    return true;
  }

  void rejectUnlock(long nativeSession, long windowEpoch, long request) {
    requireMain();
    if (state.canConfirmUnlocked(nativeSession, windowEpoch, request)) interrupt();
  }

  /** Unknown/unavailable player state must not call this method. */
  void playbackStopped(long nativeSession) {
    requireMain();
    if (!state.playbackStopped(nativeSession)) return;
    hideWindow();
    host.onRetired(nativeSession);
  }

  void ownerDestroyed() {
    requireMain();
    if (destroyed) return;
    destroyed = true;
    long session = state.session();
    boolean retired = state.ownerDestroyed();
    hideWindow();
    handler.removeCallbacksAndMessages(null);
    if (retired) host.onRetired(session);
  }

  private static void requireMain() {
    if (Looper.myLooper() != Looper.getMainLooper())
      throw new IllegalStateException("Video lock must be called on the main Looper");
  }

  private void updateVisibility() {
    if (state.wantsWindow()) showIfNeeded();
    else hideWindow();
  }

  private void showIfNeeded() {
    if (destroyed || !state.wantsWindow() || owner.isFinishing() || owner.isDestroyed()) return;
    if (window != null && window.isShowing()) return;
    revokeReady();
    if (destroyed || !state.wantsWindow() || owner.isFinishing() || owner.isDestroyed()) return;
    state.setDialogFocused(false);
    state.setViewportReady(false);
    final long showingSession = state.session();
    LockWindow candidate = new LockWindow();
    window = candidate;
    candidate.setOnDismissListener(ignored -> {
      if (window != candidate) return;
      revokeReady();
      if (window != candidate) return;
      window = null;
      state.setDialogFocused(false);
      state.setViewportReady(false);
      stopTick();
      // An unexpected platform dismissal does not retire the session or authorize native unlock.
      if (state.wantsWindow() && !destroyed) handler.post(this::showIfNeeded);
    });
    try {
      candidate.show();
      candidate.fit();
    } catch (WindowManager.BadTokenException | IllegalStateException unavailable) {
      // Keep native enforcement until Host distinguishes initial-entry failure from a lost window.
      if (window == candidate) {
        revokeReady();
        if (window == candidate) {
          window = null;
          state.setDialogFocused(false);
          state.setViewportReady(false);
          stopTick();
        }
      }
      candidate.detachBackCallback();
      candidate.setOnDismissListener(null);
      candidate.dismiss();
      if (!destroyed && state.owns(showingSession)) host.onWindowUnavailable(showingSession);
    }
  }

  private void hideWindow() {
    if (state.isLocked()) revokeReady();
    else {
      announcedSession = 0;
      announcedEpoch = 0;
    }
    stopTick();
    state.setDialogFocused(false);
    state.setViewportReady(false);
    LockWindow previous = window;
    window = null;
    if (previous != null) {
      previous.detachBackCallback();
      previous.dismiss();
    }
  }

  private void readyIfPossible() {
    if (announcing || revoking || window == null || !window.isShowing() || !state.canHold()) return;
    long session = state.session();
    long epoch = state.windowEpoch();
    if (announcedSession == session && announcedEpoch == epoch) return;
    announcedSession = session;
    announcedEpoch = epoch;
    announcing = true;
    try {
      host.onReady(session, epoch);
    } finally {
      announcing = false;
    }
    // Host callbacks may synchronously revoke/reflow/retire; never reuse their old readiness.
    if (!destroyed && window != null && window.isShowing() && state.canHold() &&
        (announcedSession != state.session() || announcedEpoch != state.windowEpoch()))
      handler.post(this::readyIfPossible);
  }

  private void revokeReady() {
    long session = announcedSession;
    long epoch = announcedEpoch;
    long cancelledRequest = state.pendingRequest();
    announcedSession = 0;
    announcedEpoch = 0;
    if (epoch == 0 || revoking) return;
    revoking = true;
    try {
      // Confirm is blocked by revoking before the Host can reenter, while the old token is intact.
      host.onNotReady(session, epoch, cancelledRequest);
    } finally {
      revoking = false;
    }
  }

  private void interrupt() {
    boolean pending = state.isUnlockPending();
    if (pending) {
      revokeReady();
      state.setViewportReady(false);
    }
    state.interrupt();
    stopTick();
    redraw();
    if (pending && window != null) window.content.updateAffordance();
  }

  private void redraw() {
    if (window != null) window.content.invalidate();
  }

  private void stopTick() {
    if (tick != null) handler.removeCallbacks(tick);
    tick = null;
  }

  private void startTick(long nativeSession, long interaction) {
    stopTick();
    final long epoch = state.windowEpoch();
    tick = new Runnable() {
      @Override public void run() {
        if (tick != this || window == null || !window.isShowing() ||
            !state.owns(nativeSession) || state.interaction() != interaction ||
            state.windowEpoch() != epoch) return;
        long request = state.requestUnlock(nativeSession, interaction, SystemClock.uptimeMillis());
        redraw();
        if (request != InfinityVideoLockState.NONE) {
          tick = null;
          window.content.announceForAccessibility("Unlock requested");
          host.onUnlockRequested(nativeSession, epoch, request);
        } else if (state.isHolding()) {
          handler.postDelayed(this, 16);
        } else {
          tick = null;
        }
      }
    };
    handler.post(tick);
  }

  private final class LockWindow extends Dialog {
    final LockContent content;
    private Object backCallback;

    LockWindow() {
      super(owner);
      setOwnerActivity(owner);
      requestWindowFeature(Window.FEATURE_NO_TITLE);
      setCancelable(false);
      setCanceledOnTouchOutside(false);
      content = new LockContent();
      setContentView(content);
      Window w = getWindow();
      if (w != null) {
        w.setBackgroundDrawable(new ColorDrawable(Color.TRANSPARENT));
        w.clearFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND |
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE |
            WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE |
            WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL);
        w.setGravity(Gravity.FILL);
        w.setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_HIDDEN);
        w.getDecorView().setSystemUiVisibility(owner.getWindow().getDecorView().getSystemUiVisibility());
        if (Build.VERSION.SDK_INT >= 30) w.setDecorFitsSystemWindows(false);
        if (Build.VERSION.SDK_INT >= 33) backCallback = BackApi33.attach(w, InfinityVideoLockDialog.this::interrupt);
      }
    }

    void fit() {
      Window w = getWindow();
      if (w != null) {
        w.setLayout(WindowManager.LayoutParams.MATCH_PARENT, WindowManager.LayoutParams.MATCH_PARENT);
        // This focused window must retain Main's existing modern fullscreen
        // policy; legacy flags alone leave the approved unlock target inset.
        if (Build.VERSION.SDK_INT >= 30) {
          w.setDecorFitsSystemWindows(false);
          android.view.WindowInsetsController controller = w.getInsetsController();
          if (controller != null) {
            controller.hide(android.view.WindowInsets.Type.statusBars() |
                android.view.WindowInsets.Type.navigationBars());
            controller.setSystemBarsBehavior(
                android.view.WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
          }
        }
      }
      content.requestLayout();
    }

    void detachBackCallback() {
      if (backCallback != null && Build.VERSION.SDK_INT >= 33 && getWindow() != null)
        BackApi33.detach(getWindow(), backCallback);
      backCallback = null;
    }

    @Override public void onWindowFocusChanged(boolean focused) {
      super.onWindowFocusChanged(focused);
      if (window != this) return;
      if (!focused) {
        revokeReady();
        if (window != this) return;
      }
      state.setDialogFocused(focused);
      if (!focused) {
        stopTick();
      }
      content.updateAffordance();
      readyIfPossible();
    }

    @Override public void onBackPressed() {
      if (window == this) interrupt();
    }

    @Override public boolean dispatchKeyEvent(KeyEvent event) {
      switch (event.getKeyCode()) {
        // These remain Android/system functions. They never go to the native player window.
        case KeyEvent.KEYCODE_HOME:
        case KeyEvent.KEYCODE_APP_SWITCH:
        case KeyEvent.KEYCODE_POWER:
        case KeyEvent.KEYCODE_SLEEP:
        case KeyEvent.KEYCODE_WAKEUP:
        case KeyEvent.KEYCODE_CALL:
        case KeyEvent.KEYCODE_ENDCALL:
        case KeyEvent.KEYCODE_VOLUME_UP:
        case KeyEvent.KEYCODE_VOLUME_DOWN:
        case KeyEvent.KEYCODE_VOLUME_MUTE:
          return super.dispatchKeyEvent(event);
        default:
          if (window == this) interrupt();
          return true; // Back, keyboard, controller and player media keys cannot bypass the lock.
      }
    }

    @Override public boolean dispatchTouchEvent(MotionEvent event) {
      if (window == this) content.consume(event);
      return true;
    }

    @Override public boolean dispatchGenericMotionEvent(MotionEvent event) {
      if (window == this) interrupt();
      return true;
    }
  }

  private final class LockContent extends View {
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final RectF target = new RectF();
    private final RectF ring = new RectF();
    private final int[] location = new int[2];

    LockContent() {
      super(owner);
      setFocusable(true);
      setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_YES);
      setContentDescription("Video locked. Hold the top-left lock continuously for two seconds to unlock.");
    }

    @Override protected void onLayout(boolean changed, int left, int top, int right, int bottom) {
      super.onLayout(changed, left, top, right, bottom);
      updateAffordance();
    }

    void updateAffordance() {
      boolean ready = false;
      if (haveViewport && getWidth() > 0 && getHeight() > 0 && isAttachedToWindow()) {
        getLocationOnScreen(location);
        float x = playerOnScreen.left - location[0] + playerOnScreen.width() * .037037f;
        float y = playerOnScreen.top - location[1] + playerOnScreen.height() * .0225f;
        float width = playerOnScreen.width() * .0851851f;
        float height = playerOnScreen.height() * (92f / 2400f);
        RectF next = new RectF(x, y, x + width, y + height);
        if (!target.equals(next)) {
          revokeReady();
          if (window == null || window.content != this) return;
          state.setViewportReady(false);
          stopTick();
          target.set(next);
        }
        ready = width > 0 && height > 0 && target.left >= 0 && target.top >= 0 &&
            target.right <= getWidth() && target.bottom <= getHeight();
      }
      if (!ready) {
        revokeReady();
        if (window == null || window.content != this) return;
      }
      state.setViewportReady(ready);
      if (!ready) {
        stopTick();
      }
      invalidate();
      readyIfPossible();
    }

    void consume(MotionEvent event) {
      long session = state.session();
      int action = event.getActionMasked();
      if (action == MotionEvent.ACTION_CANCEL || action == MotionEvent.ACTION_OUTSIDE ||
          action == MotionEvent.ACTION_POINTER_DOWN || action == MotionEvent.ACTION_POINTER_UP) {
        interrupt();
        return;
      }
      if (action == MotionEvent.ACTION_UP) {
        state.release(session);
        stopTick();
        invalidate();
        return;
      }
      if (action != MotionEvent.ACTION_DOWN && action != MotionEvent.ACTION_MOVE) return;
      if (action == MotionEvent.ACTION_DOWN && state.isUnlockPending()) {
        interrupt(); // New contact cancels the old request through the native revocation callback.
        return;
      }
      getLocationOnScreen(location);
      int index = action == MotionEvent.ACTION_DOWN ? event.getActionIndex() :
          event.findPointerIndex(state.pointer());
      if (index < 0 || event.getPointerCount() != 1) {
        interrupt();
        return;
      }
      // Dialog events use window coordinates; locate the actual content view without assuming insets.
      float x = event.getX(index) + event.getRawX() - event.getX(0) - location[0];
      float y = event.getY(index) + event.getRawY() - event.getY(0) - location[1];
      boolean inside = target.contains(x, y);
      long now = SystemClock.uptimeMillis();
      if (action == MotionEvent.ACTION_DOWN) {
        long interaction = state.beginHold(session, event.getPointerId(index), 1, inside, now);
        if (interaction != InfinityVideoLockState.NONE) startTick(session, interaction);
        else stopTick();
      } else {
        // Batched Android motion can leave and reenter between delivered samples.
        for (int history = 0; history < event.getHistorySize(); history++) {
          float hx = event.getHistoricalX(index, history) + event.getRawX() - event.getX(0) - location[0];
          float hy = event.getHistoricalY(index, history) + event.getRawY() - event.getY(0) - location[1];
          if (!state.move(session, event.getPointerId(index), 1, target.contains(hx, hy), now)) break;
        }
        if (!state.move(session, event.getPointerId(index), 1, inside, now)) stopTick();
      }
      invalidate();
    }

    @Override protected void onDraw(Canvas canvas) {
      super.onDraw(canvas);
      if (!haveViewport || target.isEmpty()) return;
      int save = canvas.save();
      canvas.clipRect(target);
      float unit = Math.min(target.width(), target.height());
      float stroke = Math.max(1f, unit * .035f);
      paint.setStyle(Paint.Style.FILL);
      paint.setColor(surfaceColor);
      canvas.drawRoundRect(target, unit * .18f, unit * .18f, paint);
      float cx = target.centerX();
      float cy = target.top + target.height() * .38f;
      float radius = unit * .27f;
      ring.set(cx - radius, cy - radius, cx + radius, cy + radius);
      paint.setStyle(Paint.Style.STROKE);
      paint.setStrokeWidth(stroke);
      paint.setColor(0x5586e5f5);
      canvas.drawOval(ring, paint);
      float progress = state.isUnlockPending() ? 1f :
          state.progress(state.session(), state.interaction(), SystemClock.uptimeMillis());
      paint.setColor(accentColor);
      canvas.drawArc(ring, -90f, 360f * progress, false, paint);
      RectF shackle = new RectF(cx - unit * .085f, cy - unit * .13f, cx + unit * .085f, cy + unit * .04f);
      canvas.drawArc(shackle, 180f, 180f, false, paint);
      paint.setStyle(Paint.Style.FILL);
      canvas.drawRoundRect(new RectF(cx - unit * .125f, cy - unit * .02f,
          cx + unit * .125f, cy + unit * .14f), stroke, stroke, paint);
      paint.setColor(foregroundColor);
      paint.setTextAlign(Paint.Align.CENTER);
      paint.setTextSize(Math.min(target.width() * .16f, target.height() * .17f));
      String text = state.isUnlockPending() ? "Unlocking" : "Hold 2s";
      canvas.drawText(text, cx, target.top + target.height() * .88f, paint);
      canvas.restoreToCount(save);
    }
  }

  /** Keep API 33 types out of the older-platform class verification path. */
  private static final class BackApi33 {
    static Object attach(Window window, Runnable consumedBack) {
      android.window.OnBackInvokedCallback callback = consumedBack::run;
      window.getOnBackInvokedDispatcher().registerOnBackInvokedCallback(
          android.window.OnBackInvokedDispatcher.PRIORITY_DEFAULT, callback);
      return callback;
    }

    static void detach(Window window, Object callback) {
      window.getOnBackInvokedDispatcher().unregisterOnBackInvokedCallback(
          (android.window.OnBackInvokedCallback) callback);
    }
  }
}
