package com.projectinfinity.kodi;

import static org.junit.Assert.*;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.Intent;
import android.app.Service;
import android.media.session.PlaybackState;
import java.io.*;
import java.nio.file.Files;
import java.util.*;
import java.util.concurrent.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.Robolectric;
import org.robolectric.Shadows;
import org.robolectric.annotation.Config;
import org.robolectric.util.ReflectionHelpers;

/** Executes the transformed shipped DEX through a recorded dex2jar translation.
 * New Java boundary classes are compiled directly. No application close, kill,
 * data clearing, installation, or stress scenario occurs in this harness.
 */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,manifest=Config.NONE,shadows=HostFilesystemShadow.class)
public class ProductionBoundaryTest {
  Context app;
  @Before public void setup()throws Exception{
    app=RuntimeEnvironment.getApplication();
    HostFilesystemShadow.failDirectorySync=false;HostFilesystemShadow.directorySyncs=0;
    // Each test uses Robolectric's disposable application data. Drain test
    // workers before clearing only the prior test's injected failure fixture.
    for(Class<?> p:new Class<?>[]{InfinityJavaPersistence.class,CobraJavaPersistence.class,ShellJavaPersistence.class}){
      ExecutorService executor=ReflectionHelpers.getStaticField(p,"preferences");executor.submit(()->{}).get(10,TimeUnit.SECONDS);
    }
    CombinedDurability.cancel("combined");
    for(Class<?> b:new Class<?>[]{InfinityJavaWriteBarrier.class,CobraJavaWriteBarrier.class,ShellJavaWriteBarrier.class}){
      Map<?,?> active=ReflectionHelpers.getStaticField(b,"active");assertTrue("previous test left a writer",active.isEmpty());
      Map<?,?> failures=ReflectionHelpers.getStaticField(b,"failures");failures.clear();
    }
    InfinityJavaPersistence.userEntry(app);CobraJavaPersistence.userEntry(app);ShellJavaPersistence.userEntry(app);
  }
  @After public void restore(){HostFilesystemShadow.failDirectorySync=false;}
  @Test public void independentlyWrappedStoresKeepTheirExistingValues()throws Exception{
    SharedPreferences old=app.getSharedPreferences("infinity_cobra_live",0);
    assertTrue(old.edit().putLong("playback_position",123456).putString("profile","existing-user").commit());
    SharedPreferences cobra=CobraJavaPersistence.preferences(app,"infinity_cobra_live",0);
    assertEquals(123456,cobra.getLong("playback_position",0));assertEquals("existing-user",cobra.getString("profile",""));
    assertTrue(InfinityJavaWriteBarrier.begin("infinity"));
    assertTrue(cobra.edit().putLong("playback_position",123457).commit());
    assertTrue(InfinityJavaWriteBarrier.closing());assertEquals(0,InfinityJavaWriteBarrier.pendingCount());
    assertTrue(HostFilesystemShadow.directorySyncs>0);
  }
  @Test public void backgroundSnapshotPreservesOldValueAndThenSeparatesSettings(){
    SharedPreferences infinity=InfinityJavaPersistence.preferences(app,"infinity_runtime",0);
    assertTrue(infinity.edit().putBoolean("extended_background",true).putString("unrelated","keep").commit());
    CobraBackgroundSettings.initialize(app);
    SharedPreferences cobra=CobraBackgroundSettings.preferences(app);
    assertTrue(cobra.getBoolean("extended_background",false));
    assertTrue(cobra.edit().putBoolean("extended_background",false).commit());
    CobraBackgroundSettings.initialize(app);
    assertFalse(cobra.getBoolean("extended_background",true));
    assertTrue(infinity.getBoolean("extended_background",false));assertEquals("keep",infinity.getString("unrelated",""));
  }
  @Test public void snapshotFailureCannotClaimDurability(){
    app.getSharedPreferences("infinity_runtime",0).edit().putBoolean("extended_background",true).commit();
    HostFilesystemShadow.failDirectorySync=true;
    try{CobraBackgroundSettings.initialize(app);fail("failed snapshot accepted");}catch(IllegalStateException expected){}
    assertFalse(new File(app.getFilesDir(),"cobra-settings-isolation-v1.ready").exists());
    assertTrue(app.getSharedPreferences("infinity_runtime",0).getBoolean("extended_background",false));
    assertTrue(CobraJavaWriteBarrier.pending().contains("java_save_failed"));
  }
  @Test public void ownerOutputStillWaitsForActualFileAndDirectorySync()throws Exception{
    File saved=new File(app.getFilesDir(),"cobra-progress");
    CobraJavaPersistence.Output output=new CobraJavaPersistence.Output(saved);output.write(71);
    assertTrue(CombinedDurability.begin("combined"));assertEquals("",CombinedDurability.sealIfReady("combined"));
    output.close();assertArrayEquals(new byte[]{71},Files.readAllBytes(saved.toPath()));
    assertFalse(CombinedDurability.sealIfReady("combined").isEmpty());assertTrue(HostFilesystemShadow.directorySyncs>0);
  }
  @Test public void playerRotationStartsWithSavedValueAndThenHasOneOwner(){
    SharedPreferences infinity=InfinityJavaPersistence.preferences(app,"infinity_player_rotation",0);
    assertTrue(infinity.edit().putInt("mode",1).commit());
    CobraBackgroundSettings.initialize(app);
    SharedPreferences cobra=CobraJavaPersistence.preferences(app,CobraBackgroundSettings.ROTATION_STORE,0);
    assertEquals(1,cobra.getInt("mode",0));assertTrue(cobra.edit().putInt("mode",0).commit());
    CobraBackgroundSettings.initialize(app);assertEquals(0,cobra.getInt("mode",1));assertEquals(1,infinity.getInt("mode",0));
  }
  @Test public void chooserPortsReturnTheActualOwnerWrapper(){
    assertSame(CobraJavaPersistence.preferences(app,"infinity_cobra_live",0),CobraPreferencePort.preferences(app,"infinity_cobra_live",0));
    assertSame(ShellJavaPersistence.preferences(app,"infinity_experience",0),ExperienceLaunchPreferences.preferences(app,"infinity_experience",0));
  }
  @Test public void failedDirectorySyncRevokesCombinedSaveProof()throws Exception{
    CobraJavaPersistence.Output output=new CobraJavaPersistence.Output(new File(app.getFilesDir(),"cobra-failure"));output.write(1);
    assertTrue(CombinedDurability.begin("combined"));HostFilesystemShadow.failDirectorySync=true;
    try{output.close();fail("failed sync accepted");}catch(IOException expected){}
    assertEquals("",CombinedDurability.sealIfReady("combined"));assertTrue(CombinedDurability.pending().startsWith("java_save_failed:"));
  }
  @Test public void independentPreferenceQueuesCannotAcknowledgeEachOthersWrites()throws Exception{
    ExecutorService infinity=ReflectionHelpers.getStaticField(InfinityJavaPersistence.class,"preferences");
    ExecutorService cobra=ReflectionHelpers.getStaticField(CobraJavaPersistence.class,"preferences");
    ExecutorService shell=ReflectionHelpers.getStaticField(ShellJavaPersistence.class,"preferences");
    assertNotSame(infinity,cobra);assertNotSame(cobra,shell);assertNotSame(infinity,shell);
    CountDownLatch entered=new CountDownLatch(1),release=new CountDownLatch(1);
    cobra.execute(()->{entered.countDown();try{release.await();}catch(InterruptedException e){Thread.currentThread().interrupt();}});
    assertTrue(entered.await(5,TimeUnit.SECONDS));
    try {
      CobraJavaPersistence.preferences(app,"infinity_cobra_live",0).edit().putLong("position",200).apply();
      infinity.submit(()->{}).get(5,TimeUnit.SECONDS);
      assertTrue(CombinedDurability.begin("combined"));assertEquals("",CombinedDurability.sealIfReady("combined"));
    }finally{release.countDown();cobra.submit(()->{}).get(5,TimeUnit.SECONDS);}
    assertFalse(CombinedDurability.sealIfReady("combined").isEmpty());
  }
  @Test public void miniPlaybackCallbacksAndContinuityHaveSeparateOwners()throws Exception{
    Shadows.shadowOf(RuntimeEnvironment.getApplication()).grantPermissions("android.permission.POST_NOTIFICATIONS");
    CobraBackgroundSettings.initialize(app);
    assertTrue(InfinityJavaPersistence.preferences(app,"infinity_runtime",0).edit().putBoolean("extended_background",true).commit());
    final int[] commands={0},unavailable={0};
    CobraBackgroundService.MiniPlaybackOwner player=new CobraBackgroundService.MiniPlaybackOwner(){
      public boolean available(){return true;}
      public void command(int c){commands[0]=c;}
      public long position(){return 34567;}
      public int state(){return PlaybackState.STATE_PLAYING;}
      public void unavailable(){unavailable[0]++;}
    };
    assertTrue(CobraBackgroundService.startMiniPlayback(app,"Existing Cobra title",player));
    Intent request=Shadows.shadowOf(RuntimeEnvironment.getApplication()).getNextStartedService();
    assertEquals(CobraBackgroundService.class.getName(),request.getComponent().getClassName());
    assertEquals("com.projectinfinity.kodi.action.COBRA_MINI_BACKGROUND_START",request.getAction());
    long generation=request.getLongExtra("mini_generation",-1);assertTrue(generation>0);
    org.robolectric.android.controller.ServiceController<CobraBackgroundService> cobra=Robolectric.buildService(CobraBackgroundService.class).create();
    org.robolectric.android.controller.ServiceController<InfinityExtendedBackgroundService> infinity=Robolectric.buildService(InfinityExtendedBackgroundService.class).create();
    try {
      assertEquals(Service.START_NOT_STICKY,cobra.get().onStartCommand(request,0,1));
      assertEquals(Service.START_STICKY,infinity.get().onStartCommand(new Intent(),0,1));
      assertEquals(0x3ab4,Shadows.shadowOf(cobra.get()).getLastForegroundNotificationId());
      assertEquals(0x2ab4,Shadows.shadowOf(infinity.get()).getLastForegroundNotificationId());
      assertTrue(CobraBackgroundService.isMiniPlaybackRunning());
      assertFalse(InfinityExtendedBackgroundService.isMiniPlaybackRunning());
      assertNotSame(ReflectionHelpers.getStaticField(CobraBackgroundService.class,"sMiniGrant"),ReflectionHelpers.getStaticField(InfinityExtendedBackgroundService.class,"sMiniGrant"));
      ReflectionHelpers.callStaticMethod(CobraBackgroundService.class,"dispatchMiniCommand",ReflectionHelpers.ClassParameter.from(long.class,generation-1),ReflectionHelpers.ClassParameter.from(int.class,2));
      assertEquals(0,commands[0]);
      ReflectionHelpers.callStaticMethod(CobraBackgroundService.class,"dispatchMiniCommand",ReflectionHelpers.ClassParameter.from(long.class,generation),ReflectionHelpers.ClassParameter.from(int.class,2));
      assertEquals(2,commands[0]);
      InfinityExtendedBackgroundService.stopForExit(app);
      assertTrue(CobraBackgroundService.isMiniPlaybackRunning());assertEquals(0,unavailable[0]);
      CobraBackgroundService.stopMiniPlayback(app,player);
      assertFalse(CobraBackgroundService.isMiniPlaybackRunning());
      assertTrue(InfinityJavaPersistence.preferences(app,"infinity_runtime",0).getBoolean("extended_background",false));
    }finally{cobra.destroy();infinity.destroy();}
    assertFalse(CobraRuntimeLease.active());
  }
}
