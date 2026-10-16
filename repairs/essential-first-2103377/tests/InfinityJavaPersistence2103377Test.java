package com.projectinfinity.kodi;

import static org.junit.Assert.*;
import android.content.Context;
import android.content.SharedPreferences;
import java.io.*;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.annotation.Config;
import org.robolectric.util.ReflectionHelpers;

/** Actual producer adapters and held resources. Separate from physical Fold acceptance. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35)
public class InfinityJavaPersistence2103377Test {
  private Context app;
  private String ticket;
  private CountDownLatch release;
  private static ExecutorService preferences(){return ReflectionHelpers.getStaticField(InfinityJavaPersistence.class,"preferences");}
  @Before public void setup()throws Exception{
    preferences().submit(()->{}).get(10,TimeUnit.SECONDS);
    Map<?,?> active=ReflectionHelpers.getStaticField(InfinityJavaWriteBarrier.class,"active");active.clear();
    Map<?,?> failures=ReflectionHelpers.getStaticField(InfinityJavaWriteBarrier.class,"failures");failures.clear();
    InfinityJavaWriteBarrier.userEntry();
    app=RuntimeEnvironment.getApplication();ticket=UUID.randomUUID().toString();InfinityJavaPersistence.initialize(app);
  }
  @After public void cleanup()throws Exception{if(release!=null)release.countDown();preferences().submit(()->{}).get(10,TimeUnit.SECONDS);}
  private File file(String name){return new File(app.getFilesDir(),name);}
  private void begin(){assertTrue(InfinityJavaWriteBarrier.begin(ticket));}
  private String seal(){return InfinityJavaWriteBarrier.sealIfReady(ticket);}
  private static String text(File file)throws Exception{return new String(Files.readAllBytes(file.toPath()),StandardCharsets.UTF_8);}
  private static void old(File file,String data)throws Exception{Files.write(file.toPath(),data.getBytes(StandardCharsets.UTF_8));}
  private void pausePreferenceDrain()throws Exception{
    CountDownLatch entered=new CountDownLatch(1);release=new CountDownLatch(1);
    preferences().execute(()->{entered.countDown();try{release.await();}catch(InterruptedException e){Thread.currentThread().interrupt();}});
    assertTrue(entered.await(5,TimeUnit.SECONDS));
  }

  @Test public void bufferedPayloadCannotBeDeclaredSavedBeforeFlushAndSync()throws Exception{
    File target=file("buffered.txt");BufferedOutputStream stream=new BufferedOutputStream(new InfinityJavaPersistence.Output(target));
    stream.write("accepted user data".getBytes(StandardCharsets.UTF_8));assertEquals(0,target.length());
    begin();assertEquals("",seal());assertTrue(InfinityJavaWriteBarrier.pending().contains("buffered.txt"));
    stream.close();assertFalse(InfinityJavaWriteBarrier.pending(),seal().isEmpty());assertEquals("accepted user data",text(target));
  }
  @Test public void acceptedQueueReservesSaveBeforeFirstFileOpen()throws Exception{
    List<Runnable> queue=new ArrayList<>();File target=file("queued.txt");
    InfinityJavaPersistence.execute(queue::add,()->{try(OutputStream output=new InfinityJavaPersistence.Output(target)){output.write(79);}catch(IOException e){throw new IllegalStateException(e);}},"queued-setting");
    assertFalse(target.exists());begin();assertEquals("",seal());queue.remove(0).run();
    assertFalse(InfinityJavaWriteBarrier.pending(),seal().isEmpty());assertEquals("O",text(target));
  }
  @Test public void wholeNamespaceTransactionStaysPendingBetweenCloseAndRename()throws Exception{
    File stage=file("stage.txt"),saved=file("saved.txt");
    try(InfinityJavaWriteBarrier.Scope scope=InfinityJavaWriteBarrier.enter("settings-replacement")){
      try(OutputStream output=new InfinityJavaPersistence.Output(stage)){output.write(65);}
      begin();assertEquals("",seal());assertTrue(InfinityJavaPersistence.rename(stage,saved));assertEquals("",seal());
    }
    assertFalse(InfinityJavaWriteBarrier.pending(),seal().isEmpty());assertEquals("A",text(saved));
  }
  @Test public void rejectedOpenCannotTruncateExistingSavedFile()throws Exception{
    File target=file("protected.txt");old(target,"keep");begin();String proof=seal();assertFalse(proof.isEmpty());
    try{new InfinityJavaPersistence.Output(target);fail("New essential writer passed closed admission");}
    catch(InfinityJavaWriteBarrier.Closing expected){}
    assertEquals("keep",text(target));assertFalse(InfinityJavaWriteBarrier.authorized(ticket,proof));assertEquals("",seal());
  }
  @Test public void failedFileOpenIsNotReportedAsSaved()throws Exception{
    File parent=file("not-a-directory");old(parent,"original");
    try{new InfinityJavaPersistence.Output(new File(parent,"child"));fail("Open unexpectedly succeeded");}catch(FileNotFoundException expected){}
    begin();assertEquals("",seal());assertTrue(InfinityJavaWriteBarrier.pending().startsWith("java_save_failed:"));assertEquals("original",text(parent));
  }
  @Test public void fileChannelStillOwnsTheOutstandingFileResource()throws Exception{
    File target=file("channel.txt");InfinityJavaPersistence.Output output=new InfinityJavaPersistence.Output(target);
    output.getChannel().write(ByteBuffer.wrap(new byte[]{66}));begin();assertEquals("",seal());output.getChannel().close();
    assertFalse(InfinityJavaWriteBarrier.pending(),seal().isEmpty());assertEquals("B",text(target));
  }
  @Test public void twoOpenBuffersRequireBothOwners()throws Exception{
    OutputStream first=new InfinityJavaPersistence.Output(file("first")),second=new InfinityJavaPersistence.Output(file("second"));
    first.write(49);second.write(50);begin();first.close();assertEquals("",seal());second.close();assertFalse(seal().isEmpty());
  }
  @Test public void alreadyClosedHandleCannotReviveAValidSaveProof()throws Exception{
    InfinityJavaPersistence.Output output=new InfinityJavaPersistence.Output(file("closed"));output.write(67);output.close();begin();String proof=seal();
    try{output.write(68);fail("Closed file write succeeded");}catch(IOException expected){}
    assertFalse(InfinityJavaWriteBarrier.authorized(ticket,proof));
  }
  @Test public void preferenceApplyKeepsImmediateMemoryAndWaitsForDurableReadback()throws Exception{
    pausePreferenceDrain();SharedPreferences prefs=InfinityJavaPersistence.preferences(app,"essential_async",0);
    prefs.edit().putString("profile","saved-user").putInt("quality",7).apply();
    assertEquals("saved-user",prefs.getString("profile",""));begin();assertEquals("",seal());
    release.countDown();preferences().submit(()->{}).get(10,TimeUnit.SECONDS);
    assertFalse(InfinityJavaWriteBarrier.pending(),seal().isEmpty());
    File xml=new File(app.getApplicationInfo().dataDir,"shared_prefs/essential_async.xml");assertTrue(text(xml).contains("saved-user"));
  }
  @Test public void synchronousPreferencesCoverEveryAndroidValueType()throws Exception{
    SharedPreferences prefs=InfinityJavaPersistence.preferences(app,"essential_values",0);
    assertTrue(InfinityJavaWriteBarrier.pending(),prefs.edit().putString("s","<&> \uD83C\uDF0D").putBoolean("b",true).putInt("i",42)
      .putLong("l",Long.MAX_VALUE).putFloat("f",1.25f).putStringSet("set",new HashSet<>(Arrays.asList("alpha","beta"))).commit());
    begin();assertFalse(InfinityJavaWriteBarrier.pending(),seal().isEmpty());
  }
  @Test public void preferenceListenerReceivesProtectedObject()throws Exception{
    SharedPreferences prefs=InfinityJavaPersistence.preferences(app,"essential_listener",0);AtomicBoolean wrapped=new AtomicBoolean();
    SharedPreferences.OnSharedPreferenceChangeListener callback=(value,key)->wrapped.set(value==prefs);
    prefs.registerOnSharedPreferenceChangeListener(callback);assertTrue(prefs.edit().putString("key","value").commit());
    org.robolectric.Shadows.shadowOf(android.os.Looper.getMainLooper()).idle();assertTrue(wrapped.get());prefs.unregisterOnSharedPreferenceChangeListener(callback);
  }
  @Test public void atomicReplacementRequiresActualReadback()throws Exception{
    File target=file("atomic.txt");old(target,"previous");InfinityJavaPersistence.Atomic atomic=new InfinityJavaPersistence.Atomic(target);
    FileOutputStream stream=atomic.startWrite();stream.write("replacement".getBytes(StandardCharsets.UTF_8));begin();assertEquals("",seal());atomic.finishWrite(stream);
    assertEquals("replacement",text(target));assertFalse(InfinityJavaWriteBarrier.pending(),seal().isEmpty());
  }
  @Test public void atomicRollbackPreservesPreviousDataAndRefusesSuccessfulSave()throws Exception{
    File target=file("rollback.txt");old(target,"previous");InfinityJavaPersistence.Atomic atomic=new InfinityJavaPersistence.Atomic(target);
    FileOutputStream stream=atomic.startWrite();stream.write(88);atomic.failWrite(stream);begin();assertEquals("",seal());assertEquals("previous",text(target));
  }
  @Test public void wrongSessionOrSealCannotAuthorizeTermination(){
    begin();String proof=seal();assertFalse(proof.isEmpty());assertFalse(InfinityJavaWriteBarrier.authorized("other",proof));
    assertFalse(InfinityJavaWriteBarrier.authorized(ticket,"other"));AtomicBoolean killed=new AtomicBoolean();
    assertFalse(InfinityJavaWriteBarrier.whileAuthorized(ticket,"",()->killed.set(true)));assertFalse(killed.get());
  }
  @Test public void explicitUserEntryRevokesTheClosingSession(){
    begin();String proof=seal();InfinityJavaWriteBarrier.userEntry();assertFalse(InfinityJavaWriteBarrier.authorized(ticket,proof));
  }
  @Test public void optionalWeatherCacheDoesNotBecomeAnEssentialOwner()throws Exception{
    begin();String proof=seal();InfinityJavaPersistence.preferences(app,"infinity_chooser_weather",0).edit().putString("condition","rain").apply();
    assertTrue(InfinityJavaWriteBarrier.authorized(ticket,proof));
  }
  @Test public void appCacheBufferDoesNotBlockEssentialClosure()throws Exception{
    File target=new File(app.getCacheDir(),"reproducible-cache");OutputStream output=new InfinityJavaPersistence.Output(target);
    try{output.write(65);begin();assertFalse(InfinityJavaWriteBarrier.pending(),seal().isEmpty());}finally{output.close();}
  }
  @Test public void cancellationDuringCloseCannotInventCompletion()throws Exception{
    ExecutorService pool=Executors.newSingleThreadExecutor();CountDownLatch occupied=new CountDownLatch(1),free=new CountDownLatch(1);
    pool.execute(()->{occupied.countDown();try{free.await();}catch(InterruptedException e){Thread.currentThread().interrupt();}});assertTrue(occupied.await(5,TimeUnit.SECONDS));
    try{
      Future<?> pending=InfinityJavaPersistence.submit(pool,()->{throw new AssertionError("Canceled task ran");},"accepted-save");
      begin();assertEquals("",seal());assertTrue(pending.cancel(false));assertEquals("",seal());assertTrue(InfinityJavaWriteBarrier.pending().contains("canceled_during_close"));
    }finally{free.countDown();pool.shutdownNow();}
  }
  @Test public void completedProcessCanNeverReuseItsOldProof(){
    begin();String proof=seal();InfinityJavaWriteBarrier.cancel(ticket);assertFalse(InfinityJavaWriteBarrier.authorized(ticket,proof));
    assertTrue(InfinityJavaWriteBarrier.begin(ticket));assertNotEquals(proof,seal());
  }
}
