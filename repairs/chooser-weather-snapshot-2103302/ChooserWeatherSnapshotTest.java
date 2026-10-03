package com.projectinfinity.kodi;
import android.content.Context;
import android.widget.TextView;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.*;
import org.json.JSONObject;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class) @Config(sdk=35) @LooperMode(LooperMode.Mode.PAUSED)
public class ChooserWeatherSnapshotTest {
  Context app;File file;
  static final String REAL="{\"Weather.Location\":\"Configured city\",\"Weather.Temperature\":\"15°C\",\"Weather.Conditions\":\"Cloudy\"}";
  @Before public void setup(){app=RuntimeEnvironment.getApplication();Main.MainActivity=null;app.getSharedPreferences("infinity_chooser_weather",0).edit().clear().commit();file=InfinityChooserWeather.snapshotFile(app);file.delete();file.getParentFile().mkdirs();}
  @After public void cleanup(){file.delete();Main.MainActivity=null;}
  String envelope(long observed)throws Exception{return new JSONObject().put("schema",1).put("source","Kodi.Weather").put("captured_at_ms",observed).put("result",new JSONObject(REAL)).toString();}
  void write(String data)throws Exception{try(FileOutputStream out=new FileOutputStream(file)){out.write(data.getBytes(StandardCharsets.UTF_8));}}
  @Test public void coldChooserReadsActualSnapshotWithoutKodiOrWebService()throws Exception{
    long observed=System.currentTimeMillis()-60000;write(envelope(observed));TextView label=new TextView(app);
    InfinityChooserWeather w=new InfinityChooserWeather(app,label);assertNull(Main.MainActivity);assertTrue(w.accept(new InfinityChooserWeather.LocalReader(app).read()));w.renderCached();
    assertTrue(label.getText().toString().contains("Configured city"));assertTrue(label.getText().toString().contains("15°C"));assertTrue(label.getText().toString().contains("Cloudy"));assertTrue(label.getText().toString().contains("last known"));assertEquals(observed,w.cache.getLong("timestamp",0));
  }
  @Test public void staleOrFutureObservationIsRefused()throws Exception{
    InfinityChooserWeather.LocalReader r=new InfinityChooserWeather.LocalReader(app);
    write(envelope(System.currentTimeMillis()-25*60*60*1000L));assertNull(r.read());write(envelope(System.currentTimeMillis()+60000));assertNull(r.read());
  }
  @Test public void malformedOrOversizedSnapshotIsRefused()throws Exception{
    InfinityChooserWeather.LocalReader r=new InfinityChooserWeather.LocalReader(app);write("{bad json");assertNull(r.read());write(new String(new char[17000]).replace('\0','x'));assertNull(r.read());
  }
  @Test public void missingOrForeignSnapshotIsRefused()throws Exception{
    InfinityChooserWeather.LocalReader r=new InfinityChooserWeather.LocalReader(app);assertNull(r.read());write(envelope(System.currentTimeMillis()).replace("Kodi.Weather","Other.Source"));assertNull(r.read());
    write(envelope(System.currentTimeMillis()).replace("\"schema\":1","\"schema\":2"));assertNull(r.read());
  }
  @Test public void incompleteProviderReadingKeepsPreviousCache()throws Exception{
    InfinityChooserWeather w=new InfinityChooserWeather(app,null);assertTrue(w.accept(new JSONObject().put("result",new JSONObject(REAL)).toString()));long before=w.cache.getLong("timestamp",0);
    write(envelope(System.currentTimeMillis()).replace("15°C","N/A"));assertFalse(w.accept(new InfinityChooserWeather.LocalReader(app).read()));assertEquals(before,w.cache.getLong("timestamp",0));assertEquals("Configured city",w.cache.getString("location",""));
  }
  @Test public void reimportDoesNotTurnOldWeatherIntoFreshWeather()throws Exception{
    long observed=System.currentTimeMillis()-60*60*1000L;write(envelope(observed));InfinityChooserWeather w=new InfinityChooserWeather(app,null);String data=new InfinityChooserWeather.LocalReader(app).read();assertTrue(w.accept(data));assertTrue(w.accept(data));assertEquals(observed,w.cache.getLong("timestamp",0));
  }
  File home()throws Exception{File h=new File(app.getCacheDir(),"weather-test-home");File manifest=new File(h,"assets/system/addon-manifest.xml");manifest.getParentFile().mkdirs();InfinityChooserWeather.atomicWrite(manifest,"<?xml version=\"1.0\"?><addons>\n  <addon>xbmc.python</addon>\n  <addon optional=\"true\">existing.service</addon>\n</addons>\n");return h;}
  String read(File f)throws Exception{return new String(InfinityChooserWeather.LocalReader.bounded(new FileInputStream(f),300000),StandardCharsets.UTF_8);}
  @Test public void bridgeRegistrationIsOptionalIdempotentAndPreservesExistingManifest()throws Exception{
    File h=home(),manifest=new File(h,"assets/system/addon-manifest.xml");String original=read(manifest);InfinityChooserWeather.prepareSnapshotBridge(app,h);String added=read(manifest);
    String registration="  <addon optional=\"true\">"+InfinityChooserWeather.BRIDGE_ID+"</addon>\n";assertEquals(original,added.replace(registration,""));InfinityChooserWeather.prepareSnapshotBridge(app,h);assertEquals(added,read(manifest));
    File addon=new File(h,"assets/addons/"+InfinityChooserWeather.BRIDGE_ID);assertEquals(InfinityChooserWeather.PRODUCER,read(new File(addon,"weather_snapshot.py")));assertTrue(read(new File(addon,"snapshot_config.py")).contains(file.getAbsolutePath()));
  }
  @Test public void malformedManifestCannotBeRewritten()throws Exception{
    File h=home(),manifest=new File(h,"assets/system/addon-manifest.xml");InfinityChooserWeather.atomicWrite(manifest,"<addons>broken");try{InfinityChooserWeather.prepareSnapshotBridge(app,h);fail();}catch(Exception expected){}assertEquals("<addons>broken",read(manifest));
  }
  @Test public void stalePendingSnapshotCannotBeImported()throws Exception{
    File pending=new File(file.getParentFile(),file.getName()+".pending");try{InfinityChooserWeather.atomicWrite(pending,envelope(System.currentTimeMillis()));assertNull(new InfinityChooserWeather.LocalReader(app).read());}finally{pending.delete();}
  }
  @Test public void lateWorkerAfterStopCannotUpdateCache()throws Exception{
    CountDownLatch began=new CountDownLatch(1),release=new CountDownLatch(1),done=new CountDownLatch(1);String response=envelope(System.currentTimeMillis());
    InfinityChooserWeather.Reader r=new InfinityChooserWeather.Reader(){public String read(){began.countDown();try{release.await();}catch(InterruptedException ignored){}done.countDown();return response;}public void cancel(){release.countDown();}};
    InfinityChooserWeather w=new InfinityChooserWeather(app,null,r);w.start();assertTrue(began.await(2,TimeUnit.SECONDS));w.stop();assertTrue(done.await(2,TimeUnit.SECONDS));org.robolectric.Shadows.shadowOf(android.os.Looper.getMainLooper()).idle();assertEquals(0,w.cache.getLong("timestamp",0));assertNull(w.worker);
  }
}
