package com.projectinfinity.kodi;
import android.app.Application;
import android.content.Intent;
import android.net.Uri;
import android.os.*;
import java.lang.reflect.*;
import java.time.Duration;
import java.util.*;
import org.junit.*;
import static org.junit.Assert.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.util.ReflectionHelpers;

/** Actual signed Main$3 callback; native endpoint records dispatch, never decodes. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,instrumentedPackages={"com.projectinfinity.kodi"})
@LooperMode(LooperMode.Mode.PAUSED)
public class BaselineExternalIntentOrderTest {
 public static class Endpoint extends Main {
  final List<String> delivered=new ArrayList<>();
  @Override void _onNewIntent(Intent value){delivered.add(value.getData().getLastPathSegment());}
 }
 static Intent video(String name){return new Intent(Intent.ACTION_VIEW).setDataAndType(Uri.parse("content://synthetic.qa/"+name),"video/mp4").addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);}
 static Object delayed(Main a,Intent intent,int delay)throws Exception {
  Constructor<?> c=Class.forName("com.projectinfinity.kodi.Main$DelayedIntent").getDeclaredConstructor(Main.class,Intent.class,int.class);c.setAccessible(true);return c.newInstance(a,intent,delay);
 }
 static Runnable callback(Main a,Object delayed)throws Exception{
  Constructor<?> c=Class.forName("com.projectinfinity.kodi.Main$3").getDeclaredConstructor(Main.class,delayed.getClass());c.setAccessible(true);return (Runnable)c.newInstance(a,delayed);
 }
 @Test public void reproduceOldColdRequestAfterNewerImmediateRequest()throws Exception{
  Endpoint a=Robolectric.buildActivity(Endpoint.class).get();ReflectionHelpers.setField(a,"mPaused",false);
  Runnable cold=callback(a,delayed(a,video("A.mp4"),5000));new Handler(Looper.getMainLooper()).postDelayed(cold,5000);
  a._onNewIntent(video("B.mp4"));Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(5000));
  assertEquals("Baseline defect: the old cold request is delivered after the newer file",Arrays.asList("B.mp4","A.mp4"),a.delivered);
 }
 @Test public void reproduceMultiplePendingVideosDispatchedOnResume()throws Exception{
  Endpoint a=Robolectric.buildActivity(Endpoint.class).get();ReflectionHelpers.setField(a,"mPaused",true);
  callback(a,delayed(a,video("A.mp4"),500)).run();callback(a,delayed(a,video("B.mp4"),500)).run();
  List<?> queue=ReflectionHelpers.getField(a,"mDelayedIntents");assertEquals(2,queue.size());assertTrue(a.delivered.isEmpty());
  for(Object d:new ArrayList<>(queue))new Handler(Looper.getMainLooper()).postDelayed(callback(a,d),500);
  queue.clear();ReflectionHelpers.setField(a,"mPaused",false);Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(500));
  assertEquals(Arrays.asList("A.mp4","B.mp4"),a.delivered);
 }
}
