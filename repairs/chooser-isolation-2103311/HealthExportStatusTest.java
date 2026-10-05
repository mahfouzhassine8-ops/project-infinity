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
public final class HealthExportStatusTest {
  Context app;
  @Before public void setup(){app=RuntimeEnvironment.getApplication();}
  void file(String name,byte[] data)throws Exception {
    try(FileOutputStream out=new FileOutputStream(new File(app.getFilesDir(),name))){out.write(data);}
  }
  Map<String,byte[]> export()throws Exception {
    ByteArrayOutputStream output=new ByteArrayOutputStream();
    InfinityHealthExport.write(app,output,"test report");
    Map<String,byte[]> result=new HashMap<>();
    try(ZipInputStream zip=new ZipInputStream(new ByteArrayInputStream(output.toByteArray()))){
      ZipEntry entry;byte[] buffer=new byte[1024];
      while((entry=zip.getNextEntry())!=null){ByteArrayOutputStream bytes=new ByteArrayOutputStream();int n;
        while((n=zip.read(buffer))!=-1)bytes.write(buffer,0,n);
        result.put(entry.getName(),bytes.toByteArray());
      }
    }return result;
  }
  @Test public void exportPreservesProcessAndNativeReceiptEvidence()throws Exception {
    byte[] state="{\"pid\":42,\"owner\":\"a\"}".getBytes(StandardCharsets.UTF_8);
    byte[] receipt="{\"pid\":42,\"milestone\":\"native.CXBMCApp.Destroy.complete\"}".getBytes(StandardCharsets.UTF_8);
    file("infinity-kodi-process.json",state);file("infinity-native-cleanup.json",receipt);
    Map<String,byte[]> entries=export();
    assertArrayEquals(state,entries.get("kodi-process-state.json"));
    assertArrayEquals(receipt,entries.get("native-cleanup.json"));
    JSONArray records=new JSONObject(new String(entries.get("exit-manifest.json"),StandardCharsets.UTF_8)).getJSONArray("diagnostic_files");
    assertEquals(2,records.length());assertFalse(records.getJSONObject(0).getBoolean("truncated"));
    assertFalse(records.getJSONObject(1).getBoolean("truncated"));
  }
  @Test public void malformedOversizeEvidenceIsBoundedAndMarked()throws Exception {
    file("infinity-kodi-process.json",new byte[20000]);file("infinity-native-cleanup.json",new byte[10000]);
    Map<String,byte[]> entries=export();
    assertEquals(8192,entries.get("kodi-process-state.json").length);
    assertEquals(4096,entries.get("native-cleanup.json").length);
    JSONArray records=new JSONObject(new String(entries.get("exit-manifest.json"),StandardCharsets.UTF_8)).getJSONArray("diagnostic_files");
    assertTrue(records.getJSONObject(0).getBoolean("truncated"));assertTrue(records.getJSONObject(1).getBoolean("truncated"));
  }
}
