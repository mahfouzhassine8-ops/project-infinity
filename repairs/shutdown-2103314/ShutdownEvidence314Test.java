package com.projectinfinity.kodi;
import android.content.Context;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.zip.*;
import org.json.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.annotation.Config;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class) @Config(sdk=28)
public final class ShutdownEvidence314Test {
  Context app;
  @Before public void setup(){app=RuntimeEnvironment.getApplication();
    new File(app.getFilesDir(),"infinity-native-shutdown.jsonl").delete();
    new File(app.getFilesDir(),"infinity-native-shutdown.jsonl.previous").delete();}
  void file(String name,String data)throws Exception {
    try(FileOutputStream out=new FileOutputStream(new File(app.getFilesDir(),name))){out.write(data.getBytes(StandardCharsets.UTF_8));}}
  String row(String event,String stage,int span,int pid,long session,long duration)throws Exception {
    JSONObject r=new JSONObject();r.put("schema",1);r.put("build",2103314);r.put("pid",pid);r.put("tid",48);r.put("session",session);
    r.put("event",event);r.put("stage",stage);r.put("span",span);r.put("invoker_id",77);r.put("duration_ms",duration);
    r.put("epoch_ms",1000);r.put("boottime_ms",android.os.SystemClock.elapsedRealtime());return r.toString()+"\n";}
  @Test public void reportShowsUnfinishedInnerCallAndCompletedDurationWithoutGuessing()throws Exception {
    file("infinity-native-shutdown.jsonl",row("begin","application.pre_destroy",1,42,123,-1)+
        row("begin","python.abort.gil_acquire",2,42,123,-1)+row("begin","test.finished",3,42,123,-1)+
        row("end","test.finished",3,42,123,5000));
    String report=InfinityHealthExport.shutdownReport(app);
    assertTrue(report.contains("Captured build=2103314 pid=42 session=123"));
    assertTrue(report.contains("python.abort.gil_acquire tid=48 invoker=77"));assertTrue(report.contains("duration_ms=5000"));
    assertTrue(report.contains("not an ANR verdict"));assertFalse(report.contains("hang resolved"));
  }
  @Test public void exportRetainsCurrentAndPreviousNativeStages()throws Exception {
    String current=row("begin","python.abort.gil_acquire",1,42,123,-1),previous=row("end","application.cleanup",1,40,122,2000);
    file("infinity-native-shutdown.jsonl",current);file("infinity-native-shutdown.jsonl.previous",previous);
    ByteArrayOutputStream data=new ByteArrayOutputStream();InfinityHealthExport.write(app,data,"report");
    Map<String,String> entries=new HashMap<>();
    try(ZipInputStream zip=new ZipInputStream(new ByteArrayInputStream(data.toByteArray()))){ZipEntry e;while((e=zip.getNextEntry())!=null){
      ByteArrayOutputStream bytes=new ByteArrayOutputStream();byte[] b=new byte[4096];int n;while((n=zip.read(b))!=-1)bytes.write(b,0,n);
      entries.put(e.getName(),new String(bytes.toByteArray(),StandardCharsets.UTF_8));}}
    assertEquals(current,entries.get("native-shutdown.jsonl"));assertEquals(previous,entries.get("native-shutdown.previous.jsonl"));
  }
  @Test public void missingEvidenceAndMixedSessionsAreExplicit()throws Exception {
    assertTrue(InfinityHealthExport.shutdownReport(app).contains("not a pass"));
    file("infinity-native-shutdown.jsonl",row("begin","old.wait",1,40,122,-1)+row("begin","new.wait",1,42,123,-1)+"incomplete\n");
    String report=InfinityHealthExport.shutdownReport(app);assertFalse(report.contains("old.wait"));assertTrue(report.contains("new.wait"));
    assertTrue(report.contains("Malformed rows=1"));
  }
}
