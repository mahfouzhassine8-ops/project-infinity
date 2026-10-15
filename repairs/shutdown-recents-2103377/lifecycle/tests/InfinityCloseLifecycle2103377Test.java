package com.projectinfinity.kodi;

import static org.junit.Assert.*;
import android.app.Activity;
import android.app.ActivityManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import java.io.File;
import java.io.RandomAccessFile;
import java.lang.reflect.Method;
import java.nio.channels.FileLock;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.Collections;
import java.util.UUID;
import java.util.concurrent.ExecutorService;
import org.json.JSONObject;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.Implementation;
import org.robolectric.annotation.Implements;
import org.robolectric.shadow.api.Shadow;
import org.robolectric.shadows.ShadowActivityManager;
import org.robolectric.util.ReflectionHelpers;

/** Real admission/gate/retirement code with Android task peers, not a Fold test. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk = 35, shadows = InfinityCloseLifecycle2103377Test.TaskShadow.class)
public class InfinityCloseLifecycle2103377Test {
  static final int TASK = 71;
  public static class OwnerActivity extends Activity {
    int taskId = TASK;
    boolean managerMissing;
    @Override public int getTaskId() { return taskId; }
    @Override public Object getSystemService(String name) {
      return managerMissing && Context.ACTIVITY_SERVICE.equals(name) ? null : super.getSystemService(name);
    }
  }
  @Implements(ActivityManager.AppTask.class)
  public static class TaskShadow {
    ActivityManager.RecentTaskInfo info;
    boolean removed;
    Runnable onInfo, onRemove;
    @Implementation protected ActivityManager.RecentTaskInfo getTaskInfo() {
      if (onInfo != null) { Runnable callback = onInfo; onInfo = null; callback.run(); }
      return info;
    }
    @Implementation protected void finishAndRemoveTask() {
      if (onRemove != null) onRemove.run();
      removed = true;
    }
  }

  private OwnerActivity owner;
  private TaskShadow task;
  private InfinityCloseGuardService guard;
  private InfinityCloseGuardService.Session session;

  @Before public void setup() throws Exception {
    resetProcessForTest();
    owner = Robolectric.buildActivity(OwnerActivity.class).create().get();
    owner.setIntent(new Intent(Intent.ACTION_MAIN));
    ActivityManager.AppTask appTask = Shadow.newInstanceOf(ActivityManager.AppTask.class);
    task = Shadow.extract(appTask);
    task.info = new ActivityManager.RecentTaskInfo();
    ReflectionHelpers.setField(task.info, Build.VERSION.SDK_INT >= 29 ? "taskId" : "persistentId", TASK);
    task.info.baseIntent = new Intent().setComponent(new ComponentName(owner, Main.class));
    if (Build.VERSION.SDK_INT >= 23) task.info.baseActivity = new ComponentName(owner, Main.class);
    ActivityManager manager = (ActivityManager) owner.getSystemService(Context.ACTIVITY_SERVICE);
    Shadow.<ShadowActivityManager>extract(manager).setAppTasks(Collections.singletonList(appTask));
  }

  @After public void cleanup() throws Exception {
    if (guard != null) {
      ExecutorService worker = ReflectionHelpers.getField(guard, "worker");
      worker.shutdownNow();
    }
    resetProcessForTest();
  }

  // Test teardown only. Production intentionally exposes NO Activity-lifetime
  // release/reset and cannot clear nativeAdmissionUsed until the process exits.
  private static void resetProcessForTest() throws Exception {
    InfinityTaskLifecycleGate.Removal removal = ReflectionHelpers.getStaticField(InfinityTaskLifecycleGate.class, "removal");
    if (removal != null) removal.close();
    FileLock lock = ReflectionHelpers.getStaticField(InfinityTaskLifecycleGate.class, "entryLock");
    RandomAccessFile file = ReflectionHelpers.getStaticField(InfinityTaskLifecycleGate.class, "entryFile");
    if (lock != null && lock.isValid()) lock.release();
    if (file != null) file.close();
    for (String name : new String[]{"entryLock", "entryFile", "entryDirectory", "removal"})
      ReflectionHelpers.setStaticField(InfinityTaskLifecycleGate.class, name, null);
    ReflectionHelpers.setStaticField(InfinityNativeTaskEntry.class, "pendingTicket", null);
    ReflectionHelpers.setStaticField(InfinityNativeTaskEntry.class, "nativeAdmissionUsed", false);
  }
  private void ticket() { InfinityNativeTaskEntry.prepareFreshIntent(owner.getIntent()); }
  private File gateFile() { return new File(owner.getFilesDir(), InfinityTaskLifecycleGate.FILE_NAME); }
  private void closedGuard() throws Exception {
    guard = Robolectric.buildService(InfinityCloseGuardService.class).create().get();
    String token = UUID.randomUUID().toString();
    session = new InfinityCloseGuardService.Session(UUID.randomUUID().toString(), token, 43210, 0, TASK);
    ReflectionHelpers.setField(guard, "session", session);
    ReflectionHelpers.setField(guard, "phase", "COMPLETE");
    ReflectionHelpers.setField(guard, "checkpointSaved", true);
    ReflectionHelpers.setField(guard, "consumed", true);
    try (RandomAccessFile lease = new RandomAccessFile(InfinityKodiShutdown.leasePath(guard.getFilesDir(), token), "rw")) {
      lease.getFD().sync();
    }
    JSONObject row = new JSONObject();
    row.put("schema", 2); row.put("pid", 43210); row.put("owner", token);
    row.put("launch", ""); row.put("began", 1); row.put("close_at", 2);
    row.put("phase", "ENGINE_TERMINATING"); row.put("live", false); row.put("error", "");
    Files.write(new File(guard.getFilesDir(), InfinityKodiShutdown.STATE).toPath(), row.toString().getBytes(StandardCharsets.UTF_8));
  }
  private String retire() throws Exception {
    Method method = InfinityCloseGuardService.class.getDeclaredMethod("retireConfirmedClosedKodiTask", InfinityCloseGuardService.Session.class);
    method.setAccessible(true);
    return (String) method.invoke(guard, session);
  }

  @Test public void noTicketCannotStartEngine() { assertFalse(InfinityNativeTaskEntry.admit(owner)); }
  @Test public void nullIntentCannotStartEngine() { owner.setIntent(null); assertFalse(InfinityNativeTaskEntry.admit(owner)); }
  @Test public void forgedTicketCannotStartEngine() {
    owner.getIntent().putExtra(InfinityNativeTaskEntry.TICKET, UUID.randomUUID().toString());
    assertFalse(InfinityNativeTaskEntry.admit(owner));
  }
  @Test public void freshTicketCanAdmitCurrentMainTask() { ticket(); assertTrue(InfinityNativeTaskEntry.admit(owner)); }
  @Test public void ticketIsRemovedAfterAdmission() { ticket(); assertTrue(InfinityNativeTaskEntry.admit(owner)); assertFalse(owner.getIntent().hasExtra(InfinityNativeTaskEntry.TICKET)); }
  @Test public void consumedTicketCannotBeReplayed() {
    ticket(); Intent copy = new Intent(owner.getIntent()); assertTrue(InfinityNativeTaskEntry.admit(owner));
    owner.setIntent(copy); assertFalse(InfinityNativeTaskEntry.admit(owner));
  }
  @Test public void secondFreshTicketCannotStartSecondProcessEngine() {
    ticket(); assertTrue(InfinityNativeTaskEntry.admit(owner)); ticket(); assertFalse(InfinityNativeTaskEntry.admit(owner));
  }
  @Test public void supersededTicketRejected() {
    ticket(); Intent old = new Intent(owner.getIntent()); ticket(); owner.setIntent(old);
    assertFalse(InfinityNativeTaskEntry.admit(owner));
  }
  @Test public void nullFreshIntentIsFalse() { assertFalse(InfinityNativeTaskEntry.hasFreshIntent(null)); }
  @Test public void freshIntentMatchesOnlyPendingTicket() { ticket(); assertTrue(InfinityNativeTaskEntry.hasFreshIntent(owner.getIntent())); }
  @Test public void finishingTaskDenied() { owner.finish(); ticket(); assertFalse(InfinityNativeTaskEntry.admit(owner)); }
  @Test public void missingTaskIdDenied() { owner.taskId = -1; ticket(); assertFalse(InfinityNativeTaskEntry.admit(owner)); }
  @Test public void differentTaskIdDenied() { owner.taskId = TASK + 1; ticket(); assertFalse(InfinityNativeTaskEntry.admit(owner)); }
  @Test public void missingManagerDenied() { owner.managerMissing = true; ticket(); assertFalse(InfinityNativeTaskEntry.admit(owner)); }
  @Test public void missingTaskInfoDenied() { task.info = null; ticket(); assertFalse(InfinityNativeTaskEntry.admit(owner)); }
  @Test public void otherRootDenied() { task.info.baseActivity = new ComponentName(owner, Splash.class); ticket(); assertFalse(InfinityNativeTaskEntry.admit(owner)); }
  @Test public void otherPackageDenied() { task.info.baseActivity = new ComponentName("other.app", Main.class.getName()); ticket(); assertFalse(InfinityNativeTaskEntry.admit(owner)); }
  @Test public void missingRootDenied() { task.info.baseActivity = null; task.info.baseIntent = null; ticket(); assertFalse(InfinityNativeTaskEntry.admit(owner)); }
  @Test public void taskIntentRootFallbackAccepted() { task.info.baseActivity = null; ticket(); assertTrue(InfinityNativeTaskEntry.admit(owner)); }
  @Test @Config(sdk = 21) public void minimumApiAdmissionWorks() { ticket(); assertTrue(InfinityNativeTaskEntry.admit(owner)); }
  @Test @Config(sdk = 28) public void persistentIdAdmissionWorks() { ticket(); assertTrue(InfinityNativeTaskEntry.admit(owner)); }
  @Test public void removedDuringTaskLookupDenied() { task.onInfo = () -> owner.finish(); ticket(); assertFalse(InfinityNativeTaskEntry.admit(owner)); }
  @Test public void taskLookupExceptionDenied() { task.onInfo = () -> { throw new IllegalArgumentException("removed task"); }; ticket(); assertFalse(InfinityNativeTaskEntry.admit(owner)); }
  @Test public void entryRetainedAcrossRepeatedAdmissionPreparation() throws Exception {
    assertTrue(InfinityTaskLifecycleGate.retainEntry(owner.getFilesDir()));
    assertTrue(InfinityTaskLifecycleGate.retainEntry(owner.getFilesDir()));
    assertNull(InfinityTaskLifecycleGate.beginRemoval(owner.getFilesDir()));
  }
  @Test public void differentDirectoryCannotReuseEntryLease() throws Exception {
    assertTrue(InfinityTaskLifecycleGate.retainEntry(owner.getFilesDir()));
    assertFalse(InfinityTaskLifecycleGate.retainEntry(Files.createTempDirectory("other-gate").toFile()));
  }
  @Test public void removalExcludesAdmission() throws Exception {
    try (InfinityTaskLifecycleGate.Removal removal = InfinityTaskLifecycleGate.beginRemoval(owner.getFilesDir())) {
      assertNotNull(removal); ticket(); assertFalse(InfinityNativeTaskEntry.admit(owner));
    }
  }
  @Test public void duplicateRemovalRejectedBeforeOpeningDescriptor() throws Exception {
    try (InfinityTaskLifecycleGate.Removal removal = InfinityTaskLifecycleGate.beginRemoval(owner.getFilesDir())) {
      assertNotNull(removal); assertNull(InfinityTaskLifecycleGate.beginRemoval(owner.getFilesDir()));
      assertFalse(InfinityTaskLifecycleGate.retainEntry(owner.getFilesDir()));
    }
  }
  @Test public void removalReleaseAllowsNewEntry() throws Exception {
    InfinityTaskLifecycleGate.Removal removal = InfinityTaskLifecycleGate.beginRemoval(owner.getFilesDir());
    assertNotNull(removal); removal.close(); removal.close();
    assertTrue(InfinityTaskLifecycleGate.retainEntry(owner.getFilesDir()));
  }
  @Test public void missingDirectoryAdmissionFailsClosed() { assertFalse(InfinityTaskLifecycleGate.retainEntry(new File(owner.getFilesDir(), "not-created/subdir"))); }
  @Test public void gateIsNotUnlinkedAtRemovalEnd() throws Exception {
    try (InfinityTaskLifecycleGate.Removal removal = InfinityTaskLifecycleGate.beginRemoval(owner.getFilesDir())) { assertNotNull(removal); }
    assertTrue(gateFile().isFile());
  }
  @Test public void pendingEntryProtectsTaskBeforeOwnerJsonPublication() throws Exception {
    closedGuard(); assertTrue(InfinityTaskLifecycleGate.retainEntry(owner.getFilesDir()));
    assertEquals("replacement_engine_entry_or_removal_in_progress", retire()); assertFalse(task.removed);
  }
  @Test public void entryAtLastMomentCannotPublishOrStart() throws Exception {
    closedGuard(); final boolean[] blocked = {false};
    task.onRemove = () -> { blocked[0] = !InfinityTaskLifecycleGate.retainEntry(owner.getFilesDir()); };
    assertEquals("removed_confirmed_closed_main_task", retire()); assertTrue(task.removed); assertTrue(blocked[0]);
    assertTrue(InfinityTaskLifecycleGate.retainEntry(owner.getFilesDir()));
  }
  @Test public void revokedDuringLookupNeverRemovesTask() throws Exception {
    closedGuard(); task.onInfo = () -> ReflectionHelpers.setField(guard, "revoked", true);
    assertEquals("completion_authority_changed", retire()); assertFalse(task.removed);
    assertTrue(InfinityTaskLifecycleGate.retainEntry(owner.getFilesDir()));
  }
  @Test public void taskFailureReleasesRemovalGate() throws Exception {
    closedGuard(); task.onRemove = () -> { throw new IllegalStateException("task manager unavailable"); };
    assertTrue(retire().startsWith("closed_task_retirement_unavailable_")); assertFalse(task.removed);
    assertTrue(InfinityTaskLifecycleGate.retainEntry(owner.getFilesDir()));
  }
  @Test public void failedCheckpointStillCannotRemove() throws Exception {
    closedGuard(); ReflectionHelpers.setField(guard, "phase", "CHECKPOINT_FAILED"); retire(); assertFalse(task.removed);
  }
  @Test public void ordinaryBackgroundStillCannotRemove() throws Exception {
    closedGuard(); ReflectionHelpers.setField(guard, "phase", "RUNNING"); retire(); assertFalse(task.removed);
  }
  @Test public void coldRecentsRoutesWithoutForcingRecoveryMode() {
    Intent next = InfinityNativeTaskEntry.chooserIntent(owner, false);
    assertEquals(Splash.class.getName(), next.getComponent().getClassName());
    assertFalse(next.getBooleanExtra("infinity_checkpoint_chooser", false));
  }
  @Test public void contendedEntryRoutesExistingRecoveryChooser() {
    assertTrue(InfinityNativeTaskEntry.chooserIntent(owner, true).getBooleanExtra("infinity_checkpoint_chooser", false));
  }
  @Test public void reroutePreservesContentAndPermissionGrants() {
    Uri uri = Uri.parse("content://example.test/video/7");
    owner.setIntent(new Intent(Intent.ACTION_VIEW).setDataAndType(uri, "video/mp4")
        .putExtra("approved-extra", "keep").addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION));
    Intent next = InfinityNativeTaskEntry.chooserIntent(owner, false);
    assertEquals(Intent.ACTION_VIEW, next.getAction()); assertEquals(uri, next.getData());
    assertEquals("video/mp4", next.getType()); assertEquals("keep", next.getStringExtra("approved-extra"));
    assertTrue((next.getFlags() & Intent.FLAG_GRANT_READ_URI_PERMISSION) != 0);
    assertTrue((next.getFlags() & Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION) != 0);
  }
  @Test public void rerouteStripsEntryTicketsAndStaleLaunchFlags() {
    ticket(); owner.getIntent().putExtra(InfinityKodiShutdown.TOKEN, "stale");
    owner.getIntent().addFlags(Intent.FLAG_ACTIVITY_CLEAR_TASK | Intent.FLAG_ACTIVITY_MULTIPLE_TASK);
    Intent next = InfinityNativeTaskEntry.chooserIntent(owner, false);
    assertFalse(next.hasExtra(InfinityNativeTaskEntry.TICKET)); assertFalse(next.hasExtra(InfinityKodiShutdown.TOKEN));
    assertEquals(0, next.getFlags() & (Intent.FLAG_ACTIVITY_CLEAR_TASK | Intent.FLAG_ACTIVITY_MULTIPLE_TASK));
  }
}
