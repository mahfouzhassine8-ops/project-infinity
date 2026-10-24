"""Health export source adapter. Original signed DEX binding remains a packaging gate."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).parent
GATE=json.loads((ROOT/'FILE-AUTHORIZATION-LEDGER.json').read_text())['health_source_gate']
HELPER='''  private static final class Snapshot {
    final java.io.ByteArrayOutputStream data = new java.io.ByteArrayOutputStream();
    boolean truncated; String error;
  }
  private static Snapshot snapshot(InputStream input, int limit) {
    Snapshot result = new Snapshot();
    try (InputStream source = input) {
      result.truncated = copyBounded(source, result.data, limit);
    } catch (Exception unavailable) {
      result.error = unavailable.getClass().getSimpleName();
    }
    return result;
  }

'''
ATTACH='''  private static void attachShutdown(Context context, ZipOutputStream zip, JSONArray diagnostics,
      String sourceName, String name, int limit) throws Exception {
    JSONObject row = new JSONObject();
    row.put("path", name); row.put("limit_bytes", limit); row.put("available", false);
    row.put("snapshot_only", true); diagnostics.put(row);
    java.io.File source = new java.io.File(context.getFilesDir(), sourceName);
    InputStream input;
    try {
      if (!source.isFile()) { row.put("status", "not_present"); return; }
      if (!source.getCanonicalFile().equals(new java.io.File(context.getFilesDir().getCanonicalFile(), sourceName))) {
        row.put("status", "noncanonical_path_rejected"); return;
      }
      input = new java.io.FileInputStream(source);
    } catch (java.io.IOException | SecurityException unavailable) {
      row.put("status", "not_readable"); return;
    }
    Snapshot captured = snapshot(input, limit);
    row.put("bytes", captured.data.size()); row.put("truncated", captured.truncated);
    if (captured.error != null) row.put("error_type", captured.error);
    if (captured.data.size() == 0) {
      row.put("status", captured.error == null ? "empty_no_evidence" : "read_failed"); return;
    }
    row.put("available", true);
    row.put("status", captured.error == null ? "snapshot_collected_not_diagnosed" : "partial_read_failure");
    // Read first: an input failure must not leave an open/incomplete ZIP member.
    // Destination failures still propagate; never claim a damaged ZIP was saved.
    put(zip, name, captured.data.toByteArray());
  }

'''
API='''  private static final class Api30 {
    static void collect(Context context, ZipOutputStream zip, JSONArray records) throws Exception {
      java.util.List<android.app.ApplicationExitInfo> exits;
      try {
        android.app.ActivityManager manager = (android.app.ActivityManager)
            context.getSystemService(Context.ACTIVITY_SERVICE);
        if (manager == null) {
          records.put(new JSONObject().put("status", "exit_service_unavailable")); return;
        }
        exits = manager.getHistoricalProcessExitReasons(context.getPackageName(), 0, 12);
      } catch (RuntimeException unavailable) {
        records.put(new JSONObject().put("status", "exit_history_unavailable")
            .put("error_type", unavailable.getClass().getSimpleName())); return;
      }
      if (exits == null) return;
      int attempts = 0, inspected = 0;
      for (android.app.ApplicationExitInfo exit : exits) {
        if (inspected++ >= 12) break;
        JSONObject row = new JSONObject();
        int reason;
        try {
          String process = exit.getProcessName();
          if (process == null || !(process.equals(context.getPackageName()) ||
              process.startsWith(context.getPackageName() + ":"))) continue;
          reason = exit.getReason();
          row.put("timestamp_ms", exit.getTimestamp()); row.put("pid", exit.getPid());
          row.put("reason", reason); row.put("exit_status", exit.getStatus());
          row.put("process", process); row.put("producer_apk_version", JSONObject.NULL);
        } catch (RuntimeException unavailable) {
          records.put(new JSONObject().put("status", "exit_record_unavailable")
              .put("error_type", unavailable.getClass().getSimpleName())); continue;
        }
        // Metadata is retained for signal/Java/resource exits too. A signal exit
        // is not automatically a native-crash tombstone or a failed Close.
        records.put(row); row.put("available", false);
        // OS-retained samples describe this exit, not the current process and
        // not its faulting allocation. Android's zero means unavailable here.
        row.put("pss_kb", JSONObject.NULL); row.put("rss_kb", JSONObject.NULL);
        row.put("importance", JSONObject.NULL);
        try {
          long pss = exit.getPss(), rss = exit.getRss();
          row.put("pss_kb", pss > 0 ? pss : JSONObject.NULL);
          row.put("rss_kb", rss > 0 ? rss : JSONObject.NULL);
          row.put("importance", exit.getImportance());
          row.put("resource_context_status", "os_snapshot_not_fault_cause");
        } catch (RuntimeException unavailable) {
          row.put("resource_context_status", "unavailable");
          row.put("resource_error_type", unavailable.getClass().getSimpleName());
        }
        boolean nativeCrash = reason == android.app.ApplicationExitInfo.REASON_CRASH_NATIVE;
        boolean anr = reason == android.app.ApplicationExitInfo.REASON_ANR;
        if (!nativeCrash && !anr) { row.put("status", "metadata_only_no_supported_trace"); continue; }
        row.put("format", nativeCrash ? "android-native-tombstone-protobuf" : "android-anr-text");
        if (nativeCrash && Build.VERSION.SDK_INT < 31) { row.put("status", "trace_api_unavailable"); continue; }
        if (attempts >= MAX_TRACES) { row.put("status", "trace_budget_exhausted"); continue; }
        attempts++;
        InputStream trace;
        try { trace = exit.getTraceInputStream(); }
        catch (Exception unavailable) {
          row.put("status", "trace_unavailable"); row.put("error_type", unavailable.getClass().getSimpleName()); continue;
        }
        if (trace == null) { row.put("status", "trace_not_provided"); continue; }
        Snapshot captured = snapshot(trace, TRACE_LIMIT);
        row.put("bytes", captured.data.size()); row.put("truncated", captured.truncated);
        if (captured.error != null) row.put("error_type", captured.error);
        if (captured.data.size() == 0) {
          row.put("status", captured.error == null ? "empty_no_evidence" : "read_failed"); continue;
        }
        String name = "traces/" + attempts + "-" + exit.getTimestamp() +
            (nativeCrash ? ".tombstone.pb" : ".anr.txt");
        row.put("path", name); row.put("available", true);
        row.put("status", captured.error == null ? "snapshot_collected_not_diagnosed" : "partial_read_failure");
        put(zip, name, captured.data.toByteArray());
      }
    }
  }
'''

def transform(data):
    if hashlib.sha256(data).hexdigest()!=GATE['sha256']:raise ValueError('Exact Health export source required')
    text=data.decode();start=text.index('  private static void attachShutdown(');end=text.index('  private static String reportWithNativeShutdownEvidence',start)
    original_attach=text[start:end]
    api_start=text.index('  private static final class Api30 {');original_api=text[api_start:text.rfind('\n}')]
    revised=text[:start]+HELPER+ATTACH+text[end:api_start]+API+text[text.rfind('\n}'):]
    if revised.replace(HELPER+ATTACH,original_attach,1).replace(API,original_api,1)!=text:raise ValueError('Unrelated Java edit')
    return revised.encode()
