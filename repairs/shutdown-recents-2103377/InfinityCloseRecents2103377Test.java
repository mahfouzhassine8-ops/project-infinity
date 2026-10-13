package com.projectinfinity.kodi;

import static org.junit.Assert.*;
import android.app.ActivityManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import java.io.File;
import java.io.RandomAccessFile;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.nio.channels.FileLock;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.Arrays;
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

/** Executes the real Session and task-retirement method, with Android task doubles.
 * Does not manufacture or certify a native save, process death or physical lifecycle.
 */
@RunWith(RobolectricTestRunner.class)
@Config(sdk = 35, shadows = InfinityCloseRecents2103377Test.OwnedTaskShadow.class)
public class InfinityCloseRecents2103377Test {
  private static final int PID = 32131, TASK = 71;
  private InfinityCloseGuardService service;
  private InfinityCloseGuardService.Session session;
  private String owner;
  private ActivityManager manager;
  private ActivityManager.AppTask task;
  private OwnedTaskShadow taskState;

  @Implements(ActivityManager.AppTask.class)
  public static class OwnedTaskShadow {
    ActivityManager.RecentTaskInfo info;
    boolean removed;
    Runnable onInfo;
    @Implementation protected ActivityManager.RecentTaskInfo getTaskInfo() {
      if (onInfo != null) { Runnable callback = onInfo; onInfo = null; callback.run(); }
      return info;
    }
    @Implementation protected void finishAndRemoveTask() { removed = true; }
  }

  @Before public void setup() throws Exception {
    service = Robolectric.buildService(InfinityCloseGuardService.class).create().get();
    owner = UUID.randomUUID().toString();
    session = new InfinityCloseGuardService.Session(UUID.randomUUID().toString(), owner, PID, 0, TASK);
    ReflectionHelpers.setField(service, "session", session);
    ReflectionHelpers.setField(service, "phase", "COMPLETE");
    ReflectionHelpers.setField(service, "checkpointSaved", true);
    ReflectionHelpers.setField(service, "consumed", true);
    manager = (ActivityManager) service.getSystemService(Context.ACTIVITY_SERVICE);
    task = makeTask(TASK, new ComponentName(service, Main.class));
    taskState = Shadow.extract(task);
    Shadow.<ShadowActivityManager>extract(manager).setAppTasks(Collections.singletonList(task));
    state(PID, owner);
  }

  @After public void releaseWorker() {
    ExecutorService worker = ReflectionHelpers.getField(service, "worker");
    worker.shutdownNow();
  }

  private ActivityManager.AppTask makeTask(int id, ComponentName root) {
    ActivityManager.AppTask result = Shadow.newInstanceOf(ActivityManager.AppTask.class);
    OwnedTaskShadow shadow = Shadow.extract(result);
    shadow.info = new ActivityManager.RecentTaskInfo();
    ReflectionHelpers.setField(shadow.info, Build.VERSION.SDK_INT >= 29 ? "taskId" : "persistentId", id);
    shadow.info.baseIntent = new Intent().setComponent(root);
    if (Build.VERSION.SDK_INT >= 23) ReflectionHelpers.setField(shadow.info, "baseActivity", root);
    return result;
  }

  private void state(int pid, String token) throws Exception {
    File lease = InfinityKodiShutdown.leasePath(service.getFilesDir(), token);
    try (RandomAccessFile file = new RandomAccessFile(lease, "rw")) { file.getFD().sync(); }
    JSONObject row = new JSONObject();
    row.put("schema", 2); row.put("pid", pid); row.put("owner", token);
    row.put("launch", ""); row.put("began", 1); row.put("close_at", 2);
    row.put("phase", "ENGINE_TERMINATING"); row.put("live", false); row.put("error", "");
    Files.write(new File(service.getFilesDir(), "kodi-process-state.json").toPath(), row.toString().getBytes(StandardCharsets.UTF_8));
  }

  private String retire(InfinityCloseGuardService.Session target) throws Exception {
    Method method = InfinityCloseGuardService.class.getDeclaredMethod("retireConfirmedClosedKodiTask", InfinityCloseGuardService.Session.class);
    method.setAccessible(true);
    try { return (String) method.invoke(service, target); }
    catch (InvocationTargetException wrapped) {
      Throwable cause = wrapped.getCause();
      if (cause instanceof Error) throw (Error) cause;
      if (cause instanceof Exception) throw (Exception) cause;
      throw new AssertionError(cause);
    }
  }
  private String retire() throws Exception { return retire(session); }
  private void untouched() throws Exception { retire(); assertFalse(taskState.removed); }

  @Test public void exactClosedTaskRemovedOnly() throws Exception {
    ActivityManager.AppTask unrelated = makeTask(TASK + 1, new ComponentName(service, Splash.class));
    Shadow.<ShadowActivityManager>extract(manager).setAppTasks(Arrays.asList(unrelated, task));
    assertEquals("removed_confirmed_closed_main_task", retire());
    assertTrue(taskState.removed);
    assertFalse(Shadow.<OwnedTaskShadow>extract(unrelated).removed);
  }
  @Test public void absentTaskIsHarmless() throws Exception {
    Shadow.<ShadowActivityManager>extract(manager).setAppTasks(Collections.emptyList());
    assertEquals("closed_task_already_absent", retire());
  }
  @Test public void differentTaskUntouched() throws Exception {
    ReflectionHelpers.setField(taskState.info, "taskId", TASK + 1); untouched();
  }
  @Test public void differentRootUntouched() throws Exception {
    taskState.info.baseActivity = new ComponentName(service, Splash.class); untouched();
  }
  @Test public void otherPackageUntouched() throws Exception {
    taskState.info.baseActivity = new ComponentName("other.app", Main.class.getName()); untouched();
  }
  @Test public void baseIntentFallbackWorks() throws Exception {
    taskState.info.baseActivity = null; assertEquals("removed_confirmed_closed_main_task", retire());
  }
  @Test public void absentRootUntouched() throws Exception {
    taskState.info.baseActivity = null; taskState.info.baseIntent = null; untouched();
  }
  @Test public void nullTaskInfoUntouched() throws Exception { taskState.info = null; untouched(); }
  @Test public void normalHomeResumeUntouched() throws Exception { ReflectionHelpers.setField(service, "phase", "RUNNING"); untouched(); }
  @Test public void failedCloseUntouched() throws Exception { ReflectionHelpers.setField(service, "phase", "CHECKPOINT_FAILED"); untouched(); }
  @Test public void pendingCloseUntouched() throws Exception { ReflectionHelpers.setField(service, "phase", "PERSISTING"); untouched(); }
  @Test public void forceCloseUntouched() throws Exception { ReflectionHelpers.setField(service, "phase", "FORCED"); untouched(); }
  @Test public void unsavedUntouched() throws Exception { ReflectionHelpers.setField(service, "checkpointSaved", false); untouched(); }
  @Test public void unconsumedUntouched() throws Exception { ReflectionHelpers.setField(service, "consumed", false); untouched(); }
  @Test public void revokedUntouched() throws Exception { ReflectionHelpers.setField(service, "revoked", true); untouched(); }
  @Test public void differentSessionUntouched() throws Exception {
    retire(new InfinityCloseGuardService.Session(session.ticket, owner, PID, 0, TASK)); assertFalse(taskState.removed);
  }
  @Test public void unavailableTaskIdUntouched() throws Exception {
    session = new InfinityCloseGuardService.Session(session.ticket, owner, PID, 0, -1);
    ReflectionHelpers.setField(service, "session", session); untouched();
  }
  @Test public void replacementPidUntouched() throws Exception { state(PID + 1, UUID.randomUUID().toString()); untouched(); }
  @Test public void recycledPidNewOwnerUntouched() throws Exception { state(PID, UUID.randomUUID().toString()); untouched(); }
  @Test public void missingOwnerStateCannotAuthorizeRemoval() throws Exception {
    Files.delete(new File(service.getFilesDir(), "kodi-process-state.json").toPath()); untouched();
  }
  @Test public void unreadableOwnerStateCannotAuthorizeRemoval() throws Exception {
    Files.write(new File(service.getFilesDir(), "kodi-process-state.json").toPath(), new byte[]{'!'}); untouched();
  }
  @Test public void stillHeldOwnerCannotAuthorizeRemoval() throws Exception {
    try (RandomAccessFile file = new RandomAccessFile(InfinityKodiShutdown.leasePath(service.getFilesDir(), owner), "rw");
         FileLock held = file.getChannel().lock()) { assertTrue(held.isValid()); untouched(); }
  }
  @Test public void replacementDuringTaskLookupUntouched() throws Exception {
    taskState.onInfo = () -> { try { state(PID + 1, UUID.randomUUID().toString()); } catch (Exception error) { throw new AssertionError(error); } };
    untouched();
  }
  @Test @Config(sdk = 28) public void preAndroid10TaskIdentityCompatible() throws Exception {
    assertEquals("removed_confirmed_closed_main_task", retire()); assertTrue(taskState.removed);
  }
  @Test @Config(sdk = 21) public void minimumSdkTaskRootCompatible() throws Exception {
    assertEquals("removed_confirmed_closed_main_task", retire()); assertTrue(taskState.removed);
  }
  @Test public void sessionIdentityIncludesTask() {
    assertFalse(session.same(new InfinityCloseGuardService.Session(session.ticket, owner, PID, 0, TASK + 1)));
  }
  @Test public void homeIntentStillTargetsHome() {
    Intent home = InfinityCloseGuardService.homeIntent();
    assertEquals(Intent.ACTION_MAIN, home.getAction()); assertTrue(home.hasCategory(Intent.CATEGORY_HOME));
    assertTrue((home.getFlags() & Intent.FLAG_ACTIVITY_NEW_TASK) != 0);
  }
}
