from pathlib import Path

def prepare(build,source):
    module=build/'processprobe';module.mkdir()
    (module/'build.gradle').write_text('''apply plugin: 'com.android.application'
android {
 namespace 'com.projectinfinity.kodi.processprobe'
 compileSdk 35
 defaultConfig { applicationId 'com.projectinfinity.kodi.processprobe'; minSdk 26; targetSdk 35; testInstrumentationRunner 'androidx.test.runner.AndroidJUnitRunner' }
 compileOptions { sourceCompatibility JavaVersion.VERSION_1_8; targetCompatibility JavaVersion.VERSION_1_8 }
}
dependencies { androidTestImplementation 'androidx.test:runner:1.6.2'; androidTestImplementation 'androidx.test.ext:junit:1.2.1' }
''')
    src=module/'src/main/java/com/projectinfinity/kodi';src.mkdir(parents=True)
    helper=source/'tools/android/packaging/xbmc/src/InfinityKodiShutdown.java.in'
    (src/'InfinityKodiShutdown.java').write_text(helper.read_text().replace('@APP_PACKAGE@','com.projectinfinity.kodi'))
    (src/'InfinityExitCompletion.java').write_text('''package com.projectinfinity.kodi;
final class InfinityExitCompletion {static final String FORCE="force";static final class Plan {enum Phase {RUNNING,WAITING_FOR_STOP,QUIT_QUEUED,DESTROYING,COMPLETE,FORCED} Phase value=Phase.RUNNING; Phase phase(){return value;}}}
''')
    (src/'InfinityPowerControlActivity.java').write_text('package com.projectinfinity.kodi; public class InfinityPowerControlActivity extends android.app.Activity {}')
    (src/'Main.java').write_text('''package com.projectinfinity.kodi;
public final class Main extends android.app.Activity {
 static Main MainActivity; final InfinityExitCompletion.Plan mInfinityExitPlan=new InfinityExitCompletion.Plan();boolean live;
 static Main infinityLiveActivity(){return MainActivity!=null&&MainActivity.live?MainActivity:null;}
 @Override public void onCreate(android.os.Bundle b){super.onCreate(b);MainActivity=this;live=true;
   InfinityKodiShutdown.publish(this,"probe");
   android.os.Handler h=new android.os.Handler();
   h.postDelayed(()->{live=false;mInfinityExitPlan.value=InfinityExitCompletion.Plan.Phase.WAITING_FOR_STOP;InfinityKodiShutdown.publish(this,null);},700);
   h.postDelayed(()->{mInfinityExitPlan.value=InfinityExitCompletion.Plan.Phase.QUIT_QUEUED;InfinityKodiShutdown.publish(this,null);},1400);
   h.postDelayed(()->{mInfinityExitPlan.value=InfinityExitCompletion.Plan.Phase.DESTROYING;InfinityKodiShutdown.publish(this,null);},2100);
   h.postDelayed(()->{
     try(java.io.FileOutputStream out=new java.io.FileOutputStream(new java.io.File(getFilesDir(),"infinity-native-cleanup.json"))){
       String receipt="{\\"pid\\":"+android.os.Process.myPid()+",\\"epoch_ms\\":"+System.currentTimeMillis()+",\\"milestone\\":\\"native.CXBMCApp.Destroy.complete\\"}";
       out.write(receipt.getBytes(java.nio.charset.StandardCharsets.UTF_8));out.getFD().sync();
     }catch(Exception failure){throw new RuntimeException(failure);}
     System.exit(0);
   },2800);
 }
}
''')
    (src/'ProbeChooser.java').write_text('''package com.projectinfinity.kodi;
public final class ProbeChooser extends android.app.Activity {
 InfinityKodiShutdown.Watch watch; final java.util.List<String> stages=new java.util.concurrent.CopyOnWriteArrayList<>();volatile boolean completed,ended;
 @Override public void onCreate(android.os.Bundle b){super.onCreate(b);android.widget.TextView label=new android.widget.TextView(this);label.setText("Chooser remains open");setContentView(label);
   watch=new InfinityKodiShutdown.Watch(this,status->{stages.add(status.phase.name());if(status.complete){completed=true;label.setText("Ready — native owner ended, chooser alive");}});
 }
 void launch(){startActivity(new android.content.Intent(this,Main.class));}
 @Override protected void onDestroy(){ended=true;if(watch!=null)watch.close();super.onDestroy();}
}
''')
    (module/'src/main/AndroidManifest.xml').write_text('''<manifest xmlns:android="http://schemas.android.com/apk/res/android"><application android:theme="@android:style/Theme.Material.Light.NoActionBar">
 <activity android:name="com.projectinfinity.kodi.ProbeChooser" android:exported="false" />
 <activity android:name="com.projectinfinity.kodi.Main" android:process=":kodi" android:exported="false" android:launchMode="singleInstance" />
 </application></manifest>''')
    test=module/'src/androidTest/java/com/projectinfinity/kodi';test.mkdir(parents=True)
    (test/'ProcessExitInstrumentedTest.java').write_text('''package com.projectinfinity.kodi;
@org.junit.runner.RunWith(androidx.test.ext.junit.runners.AndroidJUnit4.class)
public final class ProcessExitInstrumentedTest {
 @org.junit.Test public void chooserSurvivesRealSeparateProcessExitAndSeesConfirmedCompletion()throws Exception {
  android.app.Instrumentation instrumentation=androidx.test.platform.app.InstrumentationRegistry.getInstrumentation();
  int chooserPid=android.os.Process.myPid();android.content.Context app=instrumentation.getTargetContext();
  new java.io.File(app.getFilesDir(),InfinityKodiShutdown.STATE).delete();new java.io.File(app.getFilesDir(),"infinity-native-cleanup.json").delete();
  ProbeChooser chooser=(ProbeChooser)instrumentation.startActivitySync(new android.content.Intent(app,ProbeChooser.class).addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK));
  instrumentation.runOnMainSync(chooser::launch);
  long deadline=android.os.SystemClock.elapsedRealtime()+12000;
  while(!chooser.completed&&android.os.SystemClock.elapsedRealtime()<deadline)Thread.sleep(100);
  org.junit.Assert.assertTrue("Receipt and separate process death not observed",chooser.completed);
  org.junit.Assert.assertFalse("Chooser was destroyed by Kodi exit",chooser.ended);
  org.junit.Assert.assertEquals(chooserPid,android.os.Process.myPid());
  org.junit.Assert.assertNotEquals(chooserPid,InfinityKodiShutdown.state().pid);
  org.junit.Assert.assertFalse(InfinityKodiShutdown.state().alive);
  org.junit.Assert.assertTrue(chooser.stages.contains("QUIT_QUEUED"));org.junit.Assert.assertTrue(chooser.stages.contains("DESTROYING"));org.junit.Assert.assertTrue(chooser.stages.contains("COMPLETE"));
  instrumentation.runOnMainSync(chooser::finish);
 }
}
''')
    with (build/'settings.gradle').open('a') as out:out.write('\ninclude ":processprobe"\n')
