package com.projectinfinity.kodi;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Bitmap;
import android.os.*;
import android.view.*;
import java.io.*;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.*;
import java.util.zip.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.shadows.ShadowEnvironment;
import org.robolectric.util.ReflectionHelpers;
import static org.junit.Assert.*;

/** Real Splash + Android looper tests; Kodi ARM64 and OEM process/task execution excluded. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class StartupReliabilityTest {
  static class Deferred implements Executor {
    final Queue<Runnable> jobs=new ArrayDeque<>();int count;
    public void execute(Runnable task){jobs.add(task);count++;}
    void complete() throws Exception {
      Runnable job=jobs.remove();FutureTask<Void> task=new FutureTask<>(job,null);
      Thread worker=new Thread(task,"TestStartupWorker");worker.start();task.get(5,TimeUnit.SECONDS);worker.join(1000);
    }
  }
  Deferred executor;
  InfinityStartupPreparation manager;
  @Before public void fixture() {
    Main.MainActivity=null;
    ShadowEnvironment.addExternalDir("primary");
    ShadowEnvironment.setExternalStorageState(Environment.MEDIA_MOUNTED);
    ShadowEnvironment.setIsExternalStorageManager(true);
    executor=new Deferred();
    manager=new InfinityStartupPreparation(executor,(app,trace)->{
      assertNotSame(Looper.getMainLooper(),Looper.myLooper());
      return new InfinityStartupPreparation.Result(new File(app.getCacheDir(),"apk"),new File(app.getCacheDir(),"fixture.apk"),null,0);
    });
    ReflectionHelpers.setStaticField(InfinityStartupPreparation.class,"shared",manager);
    System.setProperty("xbmc.proploaded","yes");
  }
  @After public void cleanup(){Main.MainActivity=null;for(String key:new String[]{"xbmc.home","xbmc.temp","xbmc.data"})System.clearProperty(key);}
  static void idle(){Shadows.shadowOf(Looper.getMainLooper()).idle();}
  ActivityController<Splash> create(int width,int height) {
    ActivityController<Splash> c=Robolectric.buildActivity(Splash.class,new Intent(Intent.ACTION_MAIN));
    c.get().getSharedPreferences("infinity_experience",0).edit().clear().commit();
    c.create().start().resume().visible();frame(c.get(),width,height);return c;
  }
  static View frame(Activity a,int width,int height) {
    View root=a.findViewById(android.R.id.content);
    root.measure(View.MeasureSpec.makeMeasureSpec(width,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(height,View.MeasureSpec.EXACTLY));
    root.layout(0,0,width,height);return root;
  }
  static void draw(Activity a,int width,int height){View v=frame(a,width,height);StartupLifecycleTest.draw(v).recycle();idle();}
  static void choose(Splash a) {
    ReflectionHelpers.callInstanceMethod(a,"launchInfinityExperience",
      ReflectionHelpers.ClassParameter.from(String.class,"infinity"),
      ReflectionHelpers.ClassParameter.from(boolean.class,true),
      ReflectionHelpers.ClassParameter.from(boolean.class,false));
  }
  static void dispose(ActivityController<Splash> c){c.pause().stop().destroy();idle();}

  @Test public void onCreateAndFirstFrameDoNotAwaitEnvironmentOrCache() throws Exception {
    ActivityController<Splash> c=create(420,936);Splash a=c.get();
    assertEquals("No preparation before first submitted frame",0,executor.count);
    Bitmap before=StartupLifecycleTest.draw(frame(a,420,936));assertNotEquals(0xff000000,before.getPixel(0,0));before.recycle();idle();
    assertEquals(1,executor.count);assertTrue(ReflectionHelpers.<Boolean>getField(a,"mInfinityChooserVisible"));
    assertFalse(ReflectionHelpers.<Boolean>getField(a,"mInfinityPreparationReady"));
    // A synthetic 26.5-second worker delay cannot hold Android's startup logo.
    Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(26500));
    assertFalse(a.isFinishing());assertTrue(ReflectionHelpers.<Boolean>getField(a,"mInfinityChooserVisible"));
    assertNull(Shadows.shadowOf(a).getNextStartedActivity());executor.complete();idle();dispose(c);
  }

  @Test public void selectedInfinityWaitsForReadinessThenLaunchesOnlyOnce() throws Exception {
    ActivityController<Splash> c=create(420,936);Splash a=c.get();draw(a,420,936);
    choose(a);choose(a);draw(a,420,936);assertNull(Shadows.shadowOf(a).getNextStartedActivity());
    executor.complete();idle();assertTrue(ReflectionHelpers.<Boolean>getField(a,"mInfinityPreparationReady"));
    draw(a,420,936);Intent next=Shadows.shadowOf(a).getNextStartedActivity();assertNotNull(next);
    assertEquals(Main.class.getName(),next.getComponent().getClassName());
    draw(a,420,936);assertNull(Shadows.shadowOf(a).getNextStartedActivity());assertTrue(a.isFinishing());dispose(c);
  }

  @Test public void homeDuringPendingPreparationCannotLaunchBehindOtherApps() throws Exception {
    ActivityController<Splash> c=create(420,936);Splash a=c.get();draw(a,420,936);choose(a);
    c.pause().stop();executor.complete();idle();assertNull(Shadows.shadowOf(a).getNextStartedActivity());
    Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMinutes(15));
    assertNull(Shadows.shadowOf(a).getNextStartedActivity());
    c.restart().start().resume().visible();draw(a,420,936);assertNotNull(Shadows.shadowOf(a).getNextStartedActivity());
    assertNull(Shadows.shadowOf(a).getNextStartedActivity());dispose(c);
  }

  @Test public void recreationJoinsSameWorkerAndNeverDeliversToDestroyedSplash() throws Exception {
    ActivityController<Splash> old=create(420,936);Splash stale=old.get();draw(stale,420,936);choose(stale);dispose(old);
    ActivityController<Splash> recreated=create(900,768);Splash current=recreated.get();draw(current,900,768);choose(current);
    assertEquals("One application-owned cache worker",1,executor.count);
    executor.complete();idle();draw(current,900,768);
    assertNull(Shadows.shadowOf(stale).getNextStartedActivity());assertNotNull(Shadows.shadowOf(current).getNextStartedActivity());
    assertNull(Shadows.shadowOf(current).getNextStartedActivity());dispose(recreated);
  }

  @Test public void repeatedExitRelaunchAcrossCoverInnerSplitFreeformHasNoStaleCompletion() throws Exception {
    for(int[] size:new int[][]{{420,936},{900,768},{360,640},{360,240}})for(int i=0;i<3;i++) {
      ActivityController<Splash> c=create(size[0],size[1]);Splash a=c.get();draw(a,size[0],size[1]);
      choose(a);executor.complete();idle();draw(a,size[0],size[1]);
      assertNotNull(Shadows.shadowOf(a).getNextStartedActivity());assertNull(Shadows.shadowOf(a).getNextStartedActivity());dispose(c);
    }
    assertEquals(12,executor.count);
  }

  @Test public void foldResizeWhileChooserVisibleDoesNotRestartPreparation() throws Exception {
    ActivityController<Splash> c=create(420,936);Splash a=c.get();draw(a,420,936);
    for(int[] size:new int[][]{{900,768},{360,240},{420,936},{900,768}})draw(a,size[0],size[1]);
    assertEquals(1,executor.count);assertTrue(ReflectionHelpers.<Boolean>getField(a,"mInfinityChooserVisible"));
    assertNull(Shadows.shadowOf(a).getNextStartedActivity());executor.complete();idle();dispose(c);
  }

  @Test public void trueLiveMainSkipsAllPreparationAndUsesInheritedSingleInstanceHandoff() {
    Main main=Robolectric.buildActivity(Main.class).get();ReflectionHelpers.setField(main,"mInfinityLaunchReady",true);
    ActivityController<Splash> c=create(420,936);Splash a=c.get();draw(a,420,936);draw(a,420,936);
    assertEquals(0,executor.count);Intent launch=Shadows.shadowOf(a).getNextStartedActivity();assertNotNull(launch);
    assertTrue((launch.getFlags()&Intent.FLAG_ACTIVITY_REORDER_TO_FRONT)!=0);dispose(c);
  }

  @Test public void ownerBeginningExitBetweenEnqueueAndDispatchRequiresFreshPreparation() throws Exception {
    Main main=Robolectric.buildActivity(Main.class).get();ReflectionHelpers.setField(main,"mInfinityLaunchReady",true);
    ActivityController<Splash> c=create(420,936);Splash a=c.get();draw(a,420,936);
    assertEquals(0,executor.count);assertNull(Shadows.shadowOf(a).getNextStartedActivity());
    main.finish();draw(a,420,936);
    assertEquals(1,executor.count);assertNull(Shadows.shadowOf(a).getNextStartedActivity());
    executor.complete();idle();draw(a,420,936);Intent launch=Shadows.shadowOf(a).getNextStartedActivity();assertNotNull(launch);
    assertEquals(0,launch.getFlags()&Intent.FLAG_ACTIVITY_REORDER_TO_FRONT);assertNull(Shadows.shadowOf(a).getNextStartedActivity());dispose(c);
  }

  @Test public void missingDisposablePathsResolveImmediatelyWithoutTwentySecondLoops() throws Exception {
    Activity a=Robolectric.buildActivity(Activity.class).setup().get();InfinityStartupTrace trace=new InfinityStartupTrace(a);
    File fallback=new File(a.getCacheDir(),"apk");
    System.setProperty("xbmc.home",new File(a.getCacheDir(),"absent-home").getPath());
    System.setProperty("xbmc.temp",new File(a.getCacheDir(),"absent-temp").getPath());
    long start=System.nanoTime();assertEquals(fallback,InfinityStartupPreparation.resolveDisposable("xbmc.home",fallback,trace));
    assertNull(InfinityStartupPreparation.resolveDisposable("xbmc.temp",null,trace));
    assertTrue("No 20s blocking retry",TimeUnit.NANOSECONDS.toMillis(System.nanoTime()-start)<1000);
    assertEquals("",System.getProperty("xbmc.home"));assertEquals("",System.getProperty("xbmc.temp"));
  }

  @Test public void missingCustomDataReportsErrorAndDoesNotSwitchUserProfiles() throws Exception {
    Activity a=Robolectric.buildActivity(Activity.class).setup().get();
    String missing=new File(a.getCacheDir(),"unavailable-user-data").getPath();System.setProperty("xbmc.data",missing);
    ExecutorService worker=Executors.newSingleThreadExecutor();
    try {
      Future<InfinityStartupPreparation.Result> result=worker.submit(()->ReflectionHelpers.callStaticMethod(InfinityStartupPreparation.class,"prepare",
          ReflectionHelpers.ClassParameter.from(android.content.Context.class,a.getApplicationContext()),
          ReflectionHelpers.ClassParameter.from(InfinityStartupTrace.class,new InfinityStartupTrace(a))));
      assertNotNull(result.get(3,TimeUnit.SECONDS).error);assertEquals(missing,System.getProperty("xbmc.data"));assertFalse(new File(missing).exists());
    }finally{worker.shutdownNow();}
  }

  @Test public void extractionPreservesUnrelatedFilesSkipsNativeAndRejectsTraversal() throws Exception {
    Activity a=Robolectric.buildActivity(Activity.class).setup().get();File home=new File(a.getCacheDir(),"extract-fixture");home.mkdirs();
    File sentinel=new File(home,"do-not-delete.txt");try(OutputStream out=new FileOutputStream(sentinel)){out.write(42);}
    File apk=new File(a.getCacheDir(),"fixture.zip");
    try(ZipOutputStream zip=new ZipOutputStream(new FileOutputStream(apk))) {
      for(String path:new String[]{"assets/test.txt","lib/arm64-v8a/test.so"}){zip.putNextEntry(new ZipEntry(path));zip.write(7);zip.closeEntry();}
    }
    InfinityStartupPreparation.extractAssets(apk,home);assertTrue(sentinel.isFile());assertTrue(new File(home,"assets/test.txt").isFile());
    assertFalse(new File(home,"lib").exists());
    try(ZipOutputStream zip=new ZipOutputStream(new FileOutputStream(apk))) {zip.putNextEntry(new ZipEntry("assets/../../outside.txt"));zip.write(7);zip.closeEntry();}
    try{InfinityStartupPreparation.extractAssets(apk,home);fail("Traversal must fail");}catch(IOException expected){}
    assertTrue(apk.isFile());assertTrue(sentinel.isFile());
  }

  @Test public void healthExportCatchesDelayedLaunchEvenWithoutCrashAndUsesCorrectUptimeLabel() {
    ActivityController<Splash> c=create(420,936);Splash a=c.get();
    InfinityStartupTrace trace=ReflectionHelpers.getField(a,"mInfinityStartupTrace");
    Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(6500));trace.event("chooser.firstFrame");
    String report=ReflectionHelpers.callInstanceMethod(a,"infinityHealthReport");
    assertTrue(report.contains("Android startup / relaunch timing"));assertTrue(report.contains("DELAYED_STARTUP"));
    assertTrue(report.contains("Device elapsed uptime:"));assertFalse(report.contains("Process uptime:"));dispose(c);
  }
}
