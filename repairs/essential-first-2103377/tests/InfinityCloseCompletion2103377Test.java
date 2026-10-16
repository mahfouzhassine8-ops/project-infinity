package com.projectinfinity.kodi;

import static org.junit.Assert.*;
import android.content.ComponentName;
import android.content.ServiceConnection;
import android.os.Binder;
import android.os.Looper;
import android.os.SystemClock;
import java.io.*;
import java.nio.channels.FileLock;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.*;
import org.json.JSONObject;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.Shadows;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.LooperMode;
import org.robolectric.shadows.ShadowSystemClock;
import org.robolectric.util.ReflectionHelpers;

/** Actual coordinator callbacks, real UUID file leases and durable receipt IO.
 * Scheduling is controlled to reproduce run 38852110196's post-death race.
 * This host regression does not establish Android or physical process death.
 */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35)
@LooperMode(LooperMode.Mode.PAUSED)
public class InfinityCloseCompletion2103377Test {
  private static final class WorkQueue extends AbstractExecutorService {
    final ArrayDeque<Runnable> queue=new ArrayDeque<>();boolean stopped;
    public void execute(Runnable task){if(stopped)throw new RejectedExecutionException();queue.add(task);}
    public void shutdown(){stopped=true;}
    public List<Runnable> shutdownNow(){stopped=true;List<Runnable> pending=new ArrayList<>(queue);queue.clear();return pending;}
    public boolean isShutdown(){return stopped;}
    public boolean isTerminated(){return stopped&&queue.isEmpty();}
    public boolean awaitTermination(long timeout,TimeUnit unit){return isTerminated();}
    void next(){assertFalse("Expected coordinator work",queue.isEmpty());queue.remove().run();}
  }
  private InfinityCloseGuardService guard;
  private InfinityCloseGuardService.Session session;
  private WorkQueue work;
  private ServiceConnection connection;
  private File ownerLease;
  private ComponentName endpoint;

  @Before public void setup()throws Exception{
    HostFilesystemShadow.failDirectorySync=false;
    Map<?,?> active=ReflectionHelpers.getStaticField(InfinityJavaWriteBarrier.class,"active");active.clear();
    Map<?,?> failures=ReflectionHelpers.getStaticField(InfinityJavaWriteBarrier.class,"failures");failures.clear();
    InfinityJavaWriteBarrier.userEntry();
    guard=Robolectric.buildService(InfinityCloseGuardService.class).create().get();
    ExecutorService original=ReflectionHelpers.getField(guard,"worker");original.shutdownNow();
    work=new WorkQueue();ReflectionHelpers.setField(guard,"worker",work);
    connection=ReflectionHelpers.getField(guard,"connection");endpoint=new ComponentName(guard,InfinityCloseNativeLease.class);
    String nativeJson;
    try(InputStream in=getClass().getResourceAsStream("/essential-first-native-safe-38852110196.json")){
      assertNotNull(in);nativeJson=new String(in.readAllBytes(),StandardCharsets.UTF_8);
    }
    JSONObject nativeReceipt=new JSONObject(nativeJson);assertTrue(InfinityCheckpointProtocol.safe(nativeReceipt));
    ShadowSystemClock.advanceBy(Duration.ofMillis(100));long now=SystemClock.elapsedRealtime();
    session=new InfinityCloseGuardService.Session(nativeReceipt.getString("session"),nativeReceipt.getString("owner"),nativeReceipt.getInt("pid"),now-4,-1);
    ReflectionHelpers.setField(guard,"session",session);ReflectionHelpers.setField(guard,"phase","ENGINE_TERMINATING");
    ReflectionHelpers.setField(guard,"checkpointSaved",true);ReflectionHelpers.setField(guard,"consumed",true);
    ReflectionHelpers.setField(guard,"generation",nativeReceipt.getLong("generation"));
    ReflectionHelpers.setField(guard,"safeJson",nativeJson);ReflectionHelpers.setField(guard,"safeProof",InfinityCheckpointProtocol.proof(nativeJson));
    for(String field:new String[]{"safeElapsed","terminateElapsed","consumedElapsed"})ReflectionHelpers.setField(guard,field,now-1);
    for(String field:new String[]{"safeEpoch","terminateEpoch","consumedEpoch"})ReflectionHelpers.setField(guard,field,System.currentTimeMillis());
    assertTrue(InfinityJavaWriteBarrier.begin(session.ticket));
    ReflectionHelpers.setField(guard,"javaProof",InfinityJavaWriteBarrier.sealIfReady(session.ticket));
    ReflectionHelpers.setField(guard,"engineJavaProof",UUID.randomUUID().toString());
    ownerLease=InfinityKodiShutdown.leasePath(guard.getFilesDir(),session.owner);
    try(RandomAccessFile file=new RandomAccessFile(ownerLease,"rw")){file.getFD().sync();}
  }
  @After public void cleanup(){HostFilesystemShadow.failDirectorySync=false;guard.onDestroy();work.shutdownNow();}
  private void idle(){Shadows.shadowOf(Looper.getMainLooper()).idle();}
  private void drain(){
    for(int rounds=0;rounds<20;rounds++){
      while(!work.queue.isEmpty())work.next();idle();
      if(work.queue.isEmpty())return;
    }
    fail("Coordinator failed to settle");
  }
  private String phase(){return ReflectionHelpers.getField(guard,"phase");}
  private JSONObject receipt()throws Exception{
    return new JSONObject(new String(Files.readAllBytes(new File(guard.getFilesDir(),InfinityCheckpointProtocol.RECEIPT).toPath()),StandardCharsets.UTF_8));
  }
  private String events()throws Exception{
    File file=new File(guard.getFilesDir(),InfinityCheckpointProtocol.EVIDENCE);
    return file.exists()?new String(Files.readAllBytes(file.toPath()),StandardCharsets.UTF_8):"";
  }
  private void startCompletion(){
    connection.onServiceDisconnected(endpoint);work.next();idle();
    assertEquals("ENGINE_TERMINATING",phase());assertTrue(ReflectionHelpers.<Boolean>getField(guard,"completing"));
    assertFalse("Durable COMPLETE write must still be queued",work.queue.isEmpty());
  }

  @Test public void nullBindingDuringDurableCompletionCannotOverwriteAuthorizedDeath()throws Exception{
    startCompletion();connection.onNullBinding(endpoint);connection.onBindingDied(endpoint);
    assertEquals("ENGINE_TERMINATING",phase());drain();
    assertEquals("COMPLETE",phase());assertEquals("COMPLETE",receipt().getString("phase"));
    assertTrue(receipt().getBoolean("process_death_confirmed"));assertFalse(events().contains("checkpoint.failed"));
    assertEquals(1,events().split("engine.owner_lease_released",-1).length-1);
  }
  @Test public void nullBindingAloneCannotProveDeathOfALiveOwner()throws Exception{
    try(RandomAccessFile file=new RandomAccessFile(ownerLease,"rw");FileLock held=file.getChannel().lock()){
      connection.onNullBinding(endpoint);drain();assertEquals("ENGINE_TERMINATING",phase());
      assertFalse(ReflectionHelpers.<Boolean>getField(guard,"completing"));assertFalse(new File(guard.getFilesDir(),InfinityCheckpointProtocol.RECEIPT).exists());
    }
    connection.onBindingDied(endpoint);drain();assertEquals("COMPLETE",phase());
  }
  @Test public void refusalBeforeAuthorizationRemainsAFailure()throws Exception{
    ReflectionHelpers.setField(guard,"consumed",false);connection.onNullBinding(endpoint);drain();
    assertEquals("CHECKPOINT_FAILED",phase());assertEquals("engine_endpoint_refused",receipt().getString("error"));
    assertFalse(receipt().getBoolean("authorization_consumed"));assertFalse(receipt().getBoolean("process_death_confirmed"));
  }
  @Test public void missingOwnerLeaseCannotBePromotedToCompletion()throws Exception{
    assertTrue(ownerLease.delete());connection.onNullBinding(endpoint);drain();
    assertEquals("ENGINE_TERMINATING",phase());assertFalse(ReflectionHelpers.<Boolean>getField(guard,"completing"));
    assertFalse(new File(guard.getFilesDir(),InfinityCheckpointProtocol.RECEIPT).exists());
  }
  @Test public void revokedCompletionCannotOverwriteTheFailureWhileReceiptWriteIsQueued()throws Exception{
    startCompletion();ReflectionHelpers.callInstanceMethod(guard,"fail",ReflectionHelpers.ClassParameter.from(String.class,"explicit_force_close"));
    drain();assertEquals("CHECKPOINT_FAILED",phase());assertEquals("explicit_force_close",receipt().getString("error"));
    assertFalse(events().contains("engine.owner_lease_released"));
  }
  @Test public void replacementEntryDuringReceiptWritePreventsSuccessfulCompletion()throws Exception{
    startCompletion();InfinityJavaWriteBarrier.userEntry();drain();
    assertEquals("CHECKPOINT_FAILED",phase());assertEquals("coordinator_java_barrier_changed_during_completion",receipt().getString("error"));
    assertFalse(events().contains("engine.owner_lease_released"));
  }
  @Test public void actualCompletionDirectorySyncFailureRemainsAFailure()throws Exception{
    startCompletion();HostFilesystemShadow.failDirectorySync=true;work.next();HostFilesystemShadow.failDirectorySync=false;
    drain();assertEquals("CHECKPOINT_FAILED",phase());assertEquals("completion_receipt_commit_failed",receipt().getString("error"));
    assertFalse(events().contains("engine.owner_lease_released"));
  }
  @Test public void lateConnectedCallbackCannotRestartTheConsumedHandshake(){
    connection.onServiceConnected(endpoint,new Binder());assertTrue(work.queue.isEmpty());assertEquals("ENGINE_TERMINATING",phase());
  }
}
