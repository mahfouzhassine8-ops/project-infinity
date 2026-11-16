package com.projectinfinity.kodi;

import android.app.Activity;
import android.app.Dialog;
import android.content.res.Configuration;
import android.graphics.Color;
import android.graphics.RectF;
import android.os.Bundle;
import android.os.Handler;
import android.os.SystemClock;
import android.view.KeyEvent;
import android.view.MotionEvent;
import android.view.View;
import android.widget.TextView;
import org.json.JSONArray;
import org.json.JSONObject;

/** Disposable component owner. No Kodi, Main replacement, native bridge or owner data. */
public final class InfinityLockProbeActivity extends Activity implements InfinityVideoLockDialog.Host {
  InfinityVideoLockDialog lock;
  View underlay;
  Dialog focusFixture;
  long session = 1000, readyEpoch, requestEpoch, request, requestAt;
  int readyCount, revokeCount, requestCount, retiredCount, unavailableCount;
  int touches, keys, configurations, heartbeat;
  int pipEnteredCallbacks, pipExitedCallbacks, pipDraws, pipDrawWidth, pipDrawHeight;
  boolean revokeConfirmRejected = true, reenterReady, alive = true;
  boolean lightPalette;
  final JSONArray events = new JSONArray();
  final Handler clock = new Handler();

  @Override public void onCreate(Bundle saved) {
    super.onCreate(saved);
    underlay = new View(this) {
      @Override public boolean onTouchEvent(MotionEvent event) { touches++; return true; }
      @Override protected void onDraw(android.graphics.Canvas canvas) {
        super.onDraw(canvas);
        if (isInPictureInPictureMode()) {
          pipDraws++; pipDrawWidth=getWidth(); pipDrawHeight=getHeight();
        }
      }
    };
    underlay.setBackgroundColor(Color.rgb(12, 28, 44));
    underlay.setFocusableInTouchMode(true);
    setContentView(underlay);
    lock = new InfinityVideoLockDialog(this, this);
    applyPaletteFixture();
    underlay.addOnLayoutChangeListener((v,l,t,r,b,ol,ot,or,ob) -> updateViewport());
    clock.post(new Runnable() {
      @Override public void run() { if (alive) { heartbeat++; clock.postDelayed(this, 16); } }
    });
  }

  @Override protected void onResume() {
    super.onResume();
    // Match exact502 Main's existing owner-window policy; no new production policy.
    if (android.os.Build.VERSION.SDK_INT >= 30) {
      getWindow().setDecorFitsSystemWindows(false);
      android.view.WindowInsetsController controller = getWindow().getInsetsController();
      if (controller != null) {
        controller.hide(android.view.WindowInsets.Type.statusBars() |
            android.view.WindowInsets.Type.navigationBars());
        controller.setSystemBarsBehavior(
            android.view.WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
      }
    } else getWindow().getDecorView().setSystemUiVisibility(0x1706);
    if (lock != null) {
      lock.setPictureInPicture(isInPictureInPictureMode());
      lock.setForeground(true);
      underlay.post(this::updateViewport);
    }
  }
  @Override protected void onPause() {
    if (lock != null) lock.setForeground(false);
    super.onPause();
  }
  @Override public void onConfigurationChanged(Configuration configuration) {
    super.onConfigurationChanged(configuration);
    configurations++;
    lock.configurationChanged();
    underlay.post(this::updateViewport);
  }
  @Override public void onPictureInPictureModeChanged(boolean active, Configuration configuration) {
    super.onPictureInPictureModeChanged(active, configuration);
    if (active) pipEnteredCallbacks++; else pipExitedCallbacks++;
    record(active ? "PIP_ENTER_CALLBACK" : "PIP_EXIT_CALLBACK",session,readyEpoch,0);
    lock.setPictureInPicture(active);
    if (!active) underlay.post(this::updateViewport);
  }
  @Override protected void onDestroy() {
    alive = false;
    clock.removeCallbacksAndMessages(null);
    if (focusFixture != null) focusFixture.dismiss();
    if (lock != null) lock.ownerDestroyed();
    super.onDestroy();
  }
  @Override public boolean onKeyDown(int code, KeyEvent event) { keys++; return true; }

  void updateViewport() {
    if (lock == null || underlay.getWidth() <= 0 || underlay.getHeight() <= 0) return;
    applyPaletteFixture();
    int[] p = new int[2]; underlay.getLocationOnScreen(p);
    lock.setPlayerViewport(p[0], p[1], underlay.getWidth(), underlay.getHeight());
  }
  /** Explicit Host palette fixture; native skin-theme resolution is not included. */
  void applyPaletteFixture() {
    lightPalette = (getResources().getConfiguration().uiMode & Configuration.UI_MODE_NIGHT_MASK)
        == Configuration.UI_MODE_NIGHT_NO;
    lock.setColors(lightPalette ? 0xeef5f9fc : 0xee0a1117,
        lightPalette ? 0xff0f191f : 0xffebf3f8, 0xff00c1e0);
  }
  boolean paletteMatches(boolean expectedLight) {
    if (lightPalette != expectedLight) return false;
    try {
      String[] names = {"surfaceColor", "foregroundColor", "accentColor"};
      int[] expected = {expectedLight ? 0xeef5f9fc : 0xee0a1117,
          expectedLight ? 0xff0f191f : 0xffebf3f8, 0xff00c1e0};
      for (int i = 0; i < names.length; ++i) {
        java.lang.reflect.Field field = InfinityVideoLockDialog.class.getDeclaredField(names[i]);
        field.setAccessible(true);
        if (field.getInt(lock) != expected[i]) return false;
      }
      return true;
    } catch (ReflectiveOperationException error) { throw new AssertionError(error); }
  }
  void begin() {
    if (lock.isLocked(session)) lock.playbackStopped(session);
    session++;
    request = 0;
    lock.setPictureInPicture(false);
    lock.setForeground(true);
    updateViewport();
    if (!lock.lock(session)) throw new AssertionError("Component lock entry refused");
  }
  boolean locked() { return lock.isLocked(session); }
  boolean holding() {
    try {
      java.lang.reflect.Field field = InfinityVideoLockDialog.class.getDeclaredField("state");
      field.setAccessible(true);
      return ((InfinityVideoLockState)field.get(lock)).isHolding();
    } catch (ReflectiveOperationException error) { throw new AssertionError(error); }
  }
  JSONObject geometryEvidence() {
    JSONObject report = new JSONObject();
    try {
      int[] p = new int[2]; underlay.getLocationOnScreen(p);
      report.put("player_bounds", new JSONArray(new int[]{p[0], p[1], underlay.getWidth(), underlay.getHeight()}));
      report.put("display_id", underlay.getDisplay() == null ? -1 : underlay.getDisplay().getDisplayId());
      report.put("rotation", underlay.getDisplay() == null ? -1 : underlay.getDisplay().getRotation());
      report.put("dialog_focused", dialogFocused()).put("ready_epoch", readyEpoch).put("locked", locked());
      report.put("task_id",getTaskId()).put("in_pip",isInPictureInPictureMode())
          .put("pip_enter_callbacks",pipEnteredCallbacks).put("pip_exit_callbacks",pipExitedCallbacks)
          .put("pip_draws",pipDraws).put("pip_draw_width",pipDrawWidth).put("pip_draw_height",pipDrawHeight);
      report.put("target", new JSONArray(target()));
    } catch (Throwable unavailable) {
      try { report.put("unavailable", unavailable.getClass().getSimpleName()); }
      catch (org.json.JSONException ignored) { }
    }
    return report;
  }
  void showFocusFixture() {
    focusFixture = new Dialog(this);
    TextView text = new TextView(this); text.setText("Disposable focus fixture");
    focusFixture.setContentView(text);
    focusFixture.show();
  }
  void closeFocusFixture() { if (focusFixture != null) { focusFixture.dismiss(); focusFixture = null; } }

  float[] target() {
    try {
      java.lang.reflect.Field wf = InfinityVideoLockDialog.class.getDeclaredField("window"); wf.setAccessible(true);
      Object window = wf.get(lock);
      java.lang.reflect.Field cf = window.getClass().getDeclaredField("content"); cf.setAccessible(true);
      View content = (View) cf.get(window);
      java.lang.reflect.Field tf = content.getClass().getDeclaredField("target"); tf.setAccessible(true);
      RectF r = (RectF) tf.get(content); int[] p = new int[2]; content.getLocationOnScreen(p);
      return new float[]{r.left+p[0], r.top+p[1], r.right+p[0], r.bottom+p[1]};
    } catch (ReflectiveOperationException error) { throw new AssertionError(error); }
  }
  boolean geometryMatches() {
    float[] r = target(); int[] p = new int[2]; underlay.getLocationOnScreen(p);
    float x = p[0]+underlay.getWidth()*.037037f, y=p[1]+underlay.getHeight()*.0225f;
    return Math.abs(r[0]-x)<.01f && Math.abs(r[1]-y)<.01f &&
        Math.abs((r[2]-r[0])-underlay.getWidth()*.0851851f)<.02f &&
        Math.abs((r[3]-r[1])-underlay.getHeight()*(92f/2400f))<.02f;
  }
  boolean dialogFocused() {
    try {
      java.lang.reflect.Field f=InfinityVideoLockDialog.class.getDeclaredField("window");f.setAccessible(true);
      Dialog d=(Dialog)f.get(lock);
      return d!=null && d.isShowing() && d.getWindow().getDecorView().hasWindowFocus();
    } catch(ReflectiveOperationException e) { throw new AssertionError(e); }
  }

  private void record(String kind,long token,long epoch,long heldRequest) {
    try { events.put(new JSONObject().put("event",kind).put("session",token).put("epoch",epoch)
        .put("request",heldRequest).put("uptime",SystemClock.uptimeMillis())); }
    catch(org.json.JSONException error) { throw new AssertionError(error); }
  }
  @Override public void onReady(long token,long epoch) {
    readyCount++; readyEpoch=epoch; record("READY",token,epoch,0);
    if(!dialogFocused())throw new AssertionError("READY without Dialog focus");
    if(reenterReady){reenterReady=false;lock.setForeground(false);}
  }
  @Override public void onNotReady(long token,long epoch,long cancelledRequest) {
    revokeCount++; record("NOT_READY",token,epoch,cancelledRequest);
    if(cancelledRequest!=0) revokeConfirmRejected &= !lock.canConfirmUnlocked(token,epoch,cancelledRequest);
  }
  @Override public void onUnlockRequested(long token,long epoch,long heldRequest) {
    requestCount++; requestEpoch=epoch; request=heldRequest;requestAt=SystemClock.uptimeMillis();
    record("UNLOCK_REQUEST",token,epoch,heldRequest);
  }
  @Override public void onWindowUnavailable(long token) { unavailableCount++;record("WINDOW_UNAVAILABLE",token,0,0); }
  @Override public void onRetired(long token) { retiredCount++;record("RETIRED",token,0,0); }
}
