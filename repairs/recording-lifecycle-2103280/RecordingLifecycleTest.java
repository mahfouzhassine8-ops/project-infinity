package com.projectinfinity.kodi;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.Config;
import org.robolectric.shadows.ShadowSystemClock;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=android.app.Application.class,manifest=Config.NONE)
public class RecordingLifecycleTest {
 @Test public void anUnstartedRequestExpiresInsteadOfLeavingAStuckRecordingState(){
  InfinityCobraFeatureRuntime f=new InfinityCobraFeatureRuntime(RuntimeEnvironment.getApplication());
  String id="pending-expiry";InfinityCobraFeatureRuntime.recordingRequested(id);assertTrue(f.recordingActive(id));
  ShadowSystemClock.advanceBy(java.time.Duration.ofSeconds(31));assertFalse(f.recordingActive(id));
 }
 @Test public void anOlderWorkerCannotClearTheReplacementRecordingOwner(){
  InfinityCobraFeatureRuntime f=new InfinityCobraFeatureRuntime(RuntimeEnvironment.getApplication());
  String id="recording-owner";Object old=new Object(),current=new Object();
  InfinityCobraFeatureRuntime.recordingRequested(id);InfinityCobraFeatureRuntime.recordingStarted(id,old);
  InfinityCobraFeatureRuntime.recordingStarted(id,current);InfinityCobraFeatureRuntime.recordingFinished(id,old);
  assertTrue(f.recordingActive(id));InfinityCobraFeatureRuntime.recordingFinished(id,current);assertFalse(f.recordingActive(id));
 }
 @Test public void stoppingAnAlreadyFinishedSessionDoesNotStartAnIdleForegroundService(){
  android.app.Application app=RuntimeEnvironment.getApplication();
  InfinityCobraFeatureRuntime f=new InfinityCobraFeatureRuntime(app);f.stopRecording("no-active-session");
  assertNull(Shadows.shadowOf(app).getNextStartedService());
 }
}
