package com.projectinfinity.kodi;

/** Serial, UI-thread-owned state. Time arguments must use Android uptime, never wall time. */
final class InfinityVideoLockState {
  static final long HOLD_MILLIS = 2000L;
  static final long NONE = 0L;

  private long session;
  private long lastSession;
  private long interaction;
  private long windowEpoch;
  private long request;
  private long startedAt;
  private long lastTime;
  private int pointer = -1;
  private boolean locked;
  private boolean destroyed;
  private boolean foreground;
  private boolean pictureInPicture;
  private boolean focused;
  private boolean viewportReady;
  private boolean holding;
  private boolean ready;

  boolean lock(long nativeSession) {
    if (destroyed || nativeSession <= NONE) return false;
    if (locked) return nativeSession == session;
    if (nativeSession <= lastSession) return false;
    lastSession = session = nativeSession;
    locked = true;
    interrupt();
    updateReadiness();
    return true;
  }

  long session() { return session; }
  boolean isLocked() { return locked; }
  boolean owns(long nativeSession) { return locked && session == nativeSession; }
  boolean isHolding() { return holding; }
  boolean isUnlockPending() { return request != NONE; }
  int pointer() { return pointer; }
  long interaction() { return interaction; }
  long windowEpoch() { return windowEpoch; }
  long pendingRequest() { return request; }

  boolean wantsWindow() {
    return locked && !destroyed && foreground && !pictureInPicture;
  }

  boolean canHold() {
    return ready && wantsWindow() && focused && viewportReady;
  }

  private void updateReadiness() {
    boolean next = wantsWindow() && focused && viewportReady;
    if (next && !ready) windowEpoch++;
    ready = next;
  }

  void setForeground(boolean value) {
    foreground = value;
    if (!value) interrupt();
    updateReadiness();
  }

  void setPictureInPicture(boolean value) {
    pictureInPicture = value;
    if (value) interrupt();
    updateReadiness();
  }

  void setDialogFocused(boolean value) {
    focused = value;
    if (!value) interrupt();
    updateReadiness();
  }

  void setViewportReady(boolean value) {
    viewportReady = value;
    if (!value) interrupt();
    updateReadiness();
  }

  void configurationChanged() {
    viewportReady = false;
    interrupt();
    updateReadiness();
  }

  /** A duplicate DOWN invalidates the old gesture; it cannot restart it. */
  long beginHold(long nativeSession, int pointerId, int count, boolean inside, long now) {
    if (!owns(nativeSession)) return NONE;
    if (holding || request != NONE || count != 1 || pointerId < 0 || !inside ||
        !canHold() || now < 0) {
      interrupt();
      return NONE;
    }
    interaction++;
    pointer = pointerId;
    startedAt = lastTime = now;
    holding = true;
    return interaction;
  }

  boolean move(long nativeSession, int pointerId, int count, boolean inside, long now) {
    if (!owns(nativeSession) || !holding) return false;
    if (!canHold() || count != 1 || pointerId != pointer || !inside || now < lastTime) {
      interrupt();
      return false;
    }
    lastTime = now;
    return true;
  }

  /** Release before completion cancels. Release after a completed hold keeps its pending request. */
  void release(long nativeSession) {
    if (owns(nativeSession) && holding) interrupt();
  }

  /** Return a request token once; the session stays locked until native restoration is confirmed. */
  long requestUnlock(long nativeSession, long expectedInteraction, long now) {
    if (!owns(nativeSession) || !holding || interaction != expectedInteraction) return NONE;
    if (!canHold() || now < lastTime) {
      interrupt();
      return NONE;
    }
    lastTime = now;
    if (now - startedAt < HOLD_MILLIS) return NONE;
    holding = false;
    request = interaction;
    return request;
  }

  float progress(long nativeSession, long expectedInteraction, long now) {
    if (!owns(nativeSession) || !holding || interaction != expectedInteraction ||
        !canHold() || now < lastTime) return 0f;
    return Math.min(1f, (float) (now - startedAt) / HOLD_MILLIS);
  }

  boolean canConfirmUnlocked(long nativeSession, long expectedEpoch, long expectedRequest) {
    return owns(nativeSession) && request != NONE && request == expectedRequest && canHold() &&
        expectedEpoch == windowEpoch;
  }

  boolean confirmUnlocked(long nativeSession, long expectedEpoch, long expectedRequest) {
    if (!canConfirmUnlocked(nativeSession, expectedEpoch, expectedRequest)) return false;
    locked = false;
    interrupt();
    updateReadiness();
    return true;
  }

  boolean rejectUnlock(long nativeSession, long expectedRequest) {
    if (!owns(nativeSession) || request == NONE || request != expectedRequest) return false;
    interrupt();
    return true;
  }

  /** Cancellation never changes locked/session ownership. */
  void interrupt() {
    interaction++;
    holding = false;
    pointer = -1;
    request = NONE;
    startedAt = lastTime = 0;
  }

  /** Call only for a positively identified stopped/ended playback session. */
  boolean playbackStopped(long nativeSession) {
    if (!owns(nativeSession)) return false;
    locked = false;
    interrupt();
    updateReadiness();
    return true;
  }

  boolean ownerDestroyed() {
    boolean retired = locked;
    destroyed = true;
    locked = false;
    interrupt();
    updateReadiness();
    return retired;
  }
}
