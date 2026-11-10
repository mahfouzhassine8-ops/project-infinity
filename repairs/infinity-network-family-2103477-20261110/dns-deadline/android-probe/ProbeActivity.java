package com.projectinfinity.dnsprobe;

import android.app.Activity;
import android.net.ConnectivityManager;
import android.net.Network;
import android.os.Bundle;
import android.widget.TextView;
import java.io.File;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import org.json.JSONArray;
import org.json.JSONObject;

/** Disposable test application. Never an Infinity/Cobra installer. */
public final class ProbeActivity extends Activity {
  static { System.loadLibrary("dnsprobe"); }
  private static native String runNative(String path, int cancellationMs, int repetitions);
  @Override public void onCreate(Bundle state) {
    super.onCreate(state);
    TextView text = new TextView(this);
    text.setText("DNS resource and deadline feasibility test");
    setContentView(text);
    new Thread(() -> {
      JSONObject report = new JSONObject();
      try {
        String base = getApplicationInfo().nativeLibraryDir;
        String helper = base + "/libinfinity_dns_helper.so";
        String stalled = base + "/libinfinity_dns_stalled_fixture.so";
        report.put("test_package", getPackageName());
        report.put("sdk", android.os.Build.VERSION.SDK_INT);
        report.put("helper_executable", new File(helper).canExecute());
        report.put("helper_writable", new File(helper).canWrite());
        report.put("scope", "Isolated DNS helper feasibility; no Infinity or Cobra installation");
        boolean resourceOnly = getIntent().getBooleanExtra("resource_only", false);
        report.put("resource_only", resourceOnly);
        if (resourceOnly) {
          report.put("completed_lookup_resources", new JSONArray(runNative(helper, -1, 10)));
        } else {
          JSONArray normal = new JSONArray(runNative(helper, -1, 1));
          report.put("normal", normal);
          // Retain strict host acceptance. Collect remaining diagnostics after a
          // fully reaped invalid reply; do not hide other cases behind that result.
          if (normal.length() == 0 || normal.getJSONObject(0).getInt("wait_error") != 0 ||
              normal.getJSONObject(0).getInt("outcome") == 3)
            throw new IllegalStateException("NATIVE_CAPABILITY_OR_OWNERSHIP_FAILED");
          ConnectivityManager connectivity = getSystemService(ConnectivityManager.class);
          Network network = connectivity.getActiveNetwork();
          boolean bound = network != null && connectivity.bindProcessToNetwork(network);
          report.put("bound_probe_process", bound);
          try {
            if (bound) report.put("explicit_binding", new JSONArray(runNative(helper, -1, 1)));
          } finally { connectivity.bindProcessToNetwork(null); }
          report.put("deadline", new JSONArray(runNative(stalled, -1, 1)));
          report.put("cancel", new JSONArray(runNative(stalled, 150, 1)));
          report.put("repeated_cancel", new JSONArray(runNative(stalled, 10, 25)));
          report.put("missing_helper", new JSONArray(runNative(base + "/missing-helper", -1, 1)));
        }
        report.put("status", "EXECUTED_REQUIRES_HOST_ASSERTIONS");
      } catch (Throwable error) {
        try {
          report.put("status", "FAIL");
          report.put("error", error.getClass().getSimpleName() + ":" + error.getMessage());
        } catch (Exception ignored) {}
      }
      try (FileOutputStream out = new FileOutputStream(new File(getFilesDir(), "report.json"))) {
        out.write(report.toString(2).getBytes(StandardCharsets.UTF_8));
      } catch (Exception ignored) {}
    }, "DnsFeasibilityOwner").start();
  }
}
