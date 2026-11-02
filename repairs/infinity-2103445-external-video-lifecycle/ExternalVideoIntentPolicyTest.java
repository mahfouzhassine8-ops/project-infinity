package com.projectinfinity.kodi;
import android.app.Application;import android.content.*;import android.net.Uri;import android.os.*;import java.time.Duration;import java.util.*;
import org.junit.*;import static org.junit.Assert.*;import org.junit.runner.RunWith;import org.robolectric.*;import org.robolectric.annotation.*;import org.robolectric.util.ReflectionHelpers;
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,instrumentedPackages={"com.projectinfinity.kodi"})
@LooperMode(LooperMode.Mode.PAUSED)
public class ExternalVideoIntentPolicyTest {
 public static class Receiver extends Main {
  final List<Intent> nativeCalls=new ArrayList<>();boolean nativeMissing;
  @Override void _onNewIntent(Intent i){if(nativeMissing)throw new UnsatisfiedLinkError("controlled JNI endpoint");nativeCalls.add(i);}
 }
 static Receiver receiver(){Receiver a=Robolectric.buildActivity(Receiver.class).get();ReflectionHelpers.setField(a,"mPaused",false);return a;}
 static Intent video(String name){return BaselineExternalIntentOrderTest.video(name);}
 static Runnable callback(Main a,Intent i,int delay)throws Exception{return BaselineExternalIntentOrderTest.callback(a,BaselineExternalIntentOrderTest.delayed(a,i,delay));}
 @Test public void newestVideoSurvivesOlderColdCallback()throws Exception{
  Receiver a=receiver();Intent cold=InfinityExternalVideoIntents.accept(a,video("A.mp4"));new Handler(Looper.getMainLooper()).postDelayed(callback(a,cold,5000),5000);
  Intent newer=InfinityExternalVideoIntents.accept(a,video("B.mp4"));InfinityExternalVideoIntents.dispatch(a,newer);Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(5000));
  assertEquals(1,a.nativeCalls.size());assertEquals("B.mp4",a.nativeCalls.get(0).getData().getLastPathSegment());
 }
 @Test public void onlyLatestOfThreePausedFilesReachesNative()throws Exception{
  Receiver a=receiver();ReflectionHelpers.setField(a,"mPaused",true);
  for(String file:new String[]{"A.mp4","B.mp4","C.mp4"})callback(a,InfinityExternalVideoIntents.accept(a,video(file)),500).run();
  List<?> pending=ReflectionHelpers.getField(a,"mDelayedIntents");assertEquals(3,pending.size());assertTrue(a.nativeCalls.isEmpty());
  ReflectionHelpers.setField(a,"mPaused",false);for(Object d:new ArrayList<>(pending))BaselineExternalIntentOrderTest.callback(a,d).run();pending.clear();
  assertEquals(1,a.nativeCalls.size());assertEquals("C.mp4",a.nativeCalls.get(0).getData().getLastPathSegment());
 }
 @Test public void duplicateCallbackForOneRequestDispatchesOnce()throws Exception{
  Receiver a=receiver();Intent i=InfinityExternalVideoIntents.accept(a,video("A.mp4"));callback(a,new Intent(i),500).run();callback(a,new Intent(i),500).run();assertEquals(1,a.nativeCalls.size());
 }
 @Test public void explicitSameFileReselectionIsNotDeduplicated(){
  Receiver a=receiver();for(int n=0;n<3;n++)InfinityExternalVideoIntents.dispatch(a,InfinityExternalVideoIntents.accept(a,video("A.mp4")));assertEquals(3,a.nativeCalls.size());
 }
 @Test public void originalGrantClipMimeActionAndExtrasReachNativeUnchanged(){
  Receiver a=receiver();Intent input=video("granted.mp4").putExtra("caller_marker","retained").addFlags(Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);input.setClipData(ClipData.newRawUri("synthetic",input.getData()));input.addCategory(Intent.CATEGORY_DEFAULT);
  Intent prepared=InfinityExternalVideoIntents.accept(a,input);assertNotSame(input,prepared);assertEquals(1,input.getExtras().size());InfinityExternalVideoIntents.dispatch(a,prepared);Intent delivered=a.nativeCalls.get(0);
  assertEquals(input.getAction(),delivered.getAction());assertEquals(input.getData(),delivered.getData());assertEquals(input.getType(),delivered.getType());assertEquals(input.getFlags(),delivered.getFlags());assertEquals(input.getCategories(),delivered.getCategories());assertEquals(input.getClipData().getItemCount(),delivered.getClipData().getItemCount());assertEquals(input.getClipData().getDescription().getLabel().toString(),delivered.getClipData().getDescription().getLabel().toString());assertEquals(input.getClipData().getDescription().getMimeType(0),delivered.getClipData().getDescription().getMimeType(0));assertEquals(input.getClipData().getItemAt(0).getUri(),delivered.getClipData().getItemAt(0).getUri());assertEquals(input.getExtras().keySet(),delivered.getExtras().keySet());assertEquals("retained",delivered.getStringExtra("caller_marker"));
 }
 @Test public void unrelatedIntentsKeepOriginalReferenceAndSemantics(){
  Receiver a=receiver();Intent[] others={new Intent(Intent.ACTION_MAIN),new Intent(Intent.ACTION_VIEW).setDataAndType(Uri.parse("https://provider.invalid/movie"),"video/mp4"),new Intent(Intent.ACTION_VIEW).setDataAndType(Uri.parse("content://synthetic.qa/audio"),"audio/mp4"),new Intent(Intent.ACTION_VIEW,Uri.parse("file:///synthetic/no-mime.mp4")),new Intent(Intent.ACTION_GET_CONTENT).setType("video/*")};
  for(Intent i:others){assertSame(i,InfinityExternalVideoIntents.accept(a,i));InfinityExternalVideoIntents.dispatch(a,i);assertSame(i,a.nativeCalls.get(a.nativeCalls.size()-1));}
 }
 @Test public void fileUriAndWildcardVideoMimeAreSupported(){
  Receiver a=receiver();Intent i=new Intent(Intent.ACTION_VIEW).setDataAndType(Uri.parse("file:///synthetic/A.mp4"),"video/*");Intent token=InfinityExternalVideoIntents.accept(a,i);assertNotSame(i,token);InfinityExternalVideoIntents.dispatch(a,token);assertEquals(i.getData(),a.nativeCalls.get(0).getData());
 }
 @Test public void activityOwnershipAndLegacyUnstampedRoutesArePreserved(){
  Receiver a=receiver(),b=receiver();Intent forA=InfinityExternalVideoIntents.accept(a,video("A.mp4"));InfinityExternalVideoIntents.dispatch(b,forA);assertTrue(b.nativeCalls.isEmpty());InfinityExternalVideoIntents.dispatch(a,forA);assertEquals(1,a.nativeCalls.size());Intent legacy=video("legacy.mp4");InfinityExternalVideoIntents.dispatch(b,legacy);assertSame(legacy,b.nativeCalls.get(0));
 }
 @Test public void missingNativeCallerPolicyRemainsOriginalAndFreshRequestCanRetry()throws Exception{
  Receiver a=receiver();a.nativeMissing=true;callback(a,InfinityExternalVideoIntents.accept(a,video("A.mp4")),500).run();assertTrue(a.nativeCalls.isEmpty());a.nativeMissing=false;callback(a,InfinityExternalVideoIntents.accept(a,video("A.mp4")),500).run();assertEquals(1,a.nativeCalls.size());
 }
}
