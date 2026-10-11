package com.projectinfinity.kodi;
import static org.junit.Assert.*;
import android.content.Context;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import org.json.JSONObject;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.annotation.Config;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=28)
public final class InstalledCodeEvidenceTest {
  @Test public void observedCodeDoesNotReadSettingsOrProveHealth() throws Exception {
    Context context=RuntimeEnvironment.getApplication();
    File addon=new File(context.getExternalFilesDir(null), ".kodi/addons/script.kodihealthcenter");
    assertTrue(addon.isDirectory()||addon.mkdirs());
    Files.write(new File(addon,"addon.xml").toPath(), "<addon id='script.kodihealthcenter' version='2.5.18'/>".getBytes(StandardCharsets.UTF_8));
    Files.write(new File(addon,"default.py").toPath(), "reviewed code".getBytes(StandardCharsets.UTF_8));
    Files.write(new File(addon,"settings.xml").toPath(), "PRIVATE AUTHORIZATION".getBytes(StandardCharsets.UTF_8));
    JSONObject report=InfinityInstalledCodeEvidence.collect(context);
    JSONObject row=report.getJSONArray("addons").getJSONObject(1);
    assertEquals("OBSERVED_CODE", row.getString("state"));
    assertEquals("2.5.18", row.getString("version"));
    assertEquals(64,row.getJSONObject("code_sha256").getString("default.py").length());
    assertFalse(report.toString().contains("PRIVATE"));
    assertFalse(report.getBoolean("proves_shutdown_or_health"));
  }
  @Test public void traceAttributionKeepsMixedHistorySeparate() throws Exception {
    Context context=RuntimeEnvironment.getApplication();
    JSONObject receipt=new JSONObject().put("schema",1).put("pid",19842)
        .put("started_epoch_ms",1000).put("engine_death_epoch_ms",2000);
    Files.write(new File(context.getFilesDir(),InfinityCheckpointProtocol.RECEIPT).toPath(),receipt.toString().getBytes(StandardCharsets.UTF_8));
    String matched=new JSONObject().put("engine","infinity-checkpoint-system-stability-2103366-v1")
        .put("pid",19842).put("epoch_ns",1500000000L).toString()+"\n";
    String old=new JSONObject().put("engine","infinity-checkpoint-system-stability-2103366-v1")
        .put("pid",19842).put("epoch_ns",500000000L).toString()+"\n";
    assertTrue(InfinityHealthExport.nativeTraceScope(context,matched).startsWith("MATCHED PREVIOUS"));
    assertTrue(InfinityHealthExport.nativeTraceScope(context,old).startsWith("HISTORICAL"));
    assertTrue(InfinityHealthExport.nativeTraceScope(context,old+matched).startsWith("MIXED"));
    assertTrue(InfinityHealthExport.nativeTraceScope(context,matched+"partial").startsWith("MIXED"));
    assertTrue(InfinityHealthExport.nativeTraceScope(context,"{\"pid\":19842}").startsWith("UNVERIFIED"));
  }

}
