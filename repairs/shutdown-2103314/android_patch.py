#!/usr/bin/env python3
"""Extend existing Health Center; no chooser/lifecycle behavior changes."""
from pathlib import Path
import hashlib,json
PREFIX='tools/android/packaging/xbmc/src/'
ALLOWED={PREFIX+x+'.java.in' for x in ['InfinityHealthExport','InfinityExitDiagnostics','Splash']}
def digest(data):return hashlib.sha256(data).hexdigest()
def once(s,a,b):
 assert s.count(a)==1,a[:100]
 return s.replace(a,b,1)
def transform(name,s,engine_sha):
 if name.endswith('InfinityExitDiagnostics.java.in'):
  return once(s,'c7976ce0adb45b9264f2092a27111be4e05bde4220be2b26b1ea0e2cc74f1e2d',engine_sha)
 if name.endswith('Splash.java.in'):
  return once(s,'+InfinityExitCompletion.report(this)+"\\n"+InfinityResponsiveness.report(this)', '+InfinityExitCompletion.report(this)+"\\n"+InfinityHealthExport.shutdownReport(this)+"\\n"+InfinityResponsiveness.report(this)')
 if name.endswith('InfinityHealthExport.java.in'):
  s=once(s,'      JSONArray records = new JSONArray();','''      attach(context, zip, diagnostics, "infinity-native-shutdown.jsonl", "native-shutdown.jsonl", TRACE_LIMIT);
      attach(context, zip, diagnostics, "infinity-native-shutdown.jsonl.previous", "native-shutdown.previous.jsonl", TRACE_LIMIT);
      JSONArray records = new JSONArray();''')
  return once(s,'  private static void put(',REPORT+'\n  private static void put(')
 raise ValueError(name)
REPORT=r'''  /** Read on the existing report worker. These are observed call boundaries,
   * not native thread stacks or a claim that an unfinished call is deadlocked. */
  static String shutdownReport(Context context) {
    StringBuilder result = new StringBuilder("Native shutdown stages\n======================\n");
    java.io.File source = new java.io.File(context.getFilesDir(), "infinity-native-shutdown.jsonl");
    if (!source.isFile()) return result.append("No native shutdown stage capture. This is not a pass.\n").toString();
    java.util.LinkedHashMap<Long, JSONObject> active = new java.util.LinkedHashMap<>();
    java.util.ArrayList<JSONObject> slow = new java.util.ArrayList<>();
    JSONObject latest = null;
    int malformed = 0;
    boolean limited = false;
    long session = -1;
    try (java.io.BufferedReader reader = new java.io.BufferedReader(
        new java.io.InputStreamReader(new java.io.FileInputStream(source), StandardCharsets.UTF_8))) {
      String line; int consumed = 0;
      while ((line = reader.readLine()) != null) {
        consumed += line.length() + 1;
        if (consumed > TRACE_LIMIT) { limited = true; break; }
        try {
          JSONObject row = new JSONObject(line);
          if (row.optInt("schema", -1) != 1) { malformed++; continue; }
          long currentSession = row.getLong("session");
          if (session != currentSession) { session = currentSession; active.clear(); slow.clear(); }
          latest = row;
          long span = row.optLong("span", 0);
          if ("begin".equals(row.optString("event"))) active.put(span, row);
          else if ("end".equals(row.optString("event"))) {
            active.remove(span);
            if (row.optLong("duration_ms", 0) >= 1000) {
              slow.add(row); if (slow.size() > 24) slow.remove(0);
            }
          }
        } catch (Exception unavailable) { malformed++; }
      }
      if (latest == null) return result.append("No complete native stage row.\n").toString();
      InfinityKodiShutdown.Snapshot owner = InfinityKodiShutdown.state();
      result.append("Captured build=").append(latest.getInt("build"))
          .append(" pid=").append(latest.getInt("pid")).append(" session=").append(session).append('\n');
      result.append("Chooser owner sample: pid=").append(owner.pid).append(" alive=").append(owner.alive)
          .append(" phase=").append(owner.phase).append(". Different PIDs must not be conflated.\n");
      result.append("Latest event: ").append(latest.optString("event")).append(' ')
          .append(latest.optString("stage")).append(" at ").append(latest.optLong("epoch_ms")).append('\n');
      result.append("Calls entered with no end row observed:\n");
      long now = android.os.SystemClock.elapsedRealtime();
      for (JSONObject row : active.values()) {
        long age = now - row.optLong("boottime_ms", now);
        result.append("  ").append(row.optString("stage")).append(" tid=").append(row.optLong("tid"))
            .append(" invoker=").append(row.optInt("invoker_id", -1)).append(" observed_age_ms=")
            .append(age >= 0 ? Long.toString(age) : "clock-or-boot-mismatch").append('\n');
      }
      if (active.isEmpty()) result.append("  None in this captured session.\n");
      result.append("Recent completed calls taking at least 1000ms:\n");
      for (JSONObject row : slow) result.append("  ").append(row.optString("stage"))
          .append(" tid=").append(row.optLong("tid")).append(" invoker=").append(row.optInt("invoker_id", -1))
          .append(" duration_ms=").append(row.optLong("duration_ms")).append('\n');
      result.append("Malformed rows=").append(malformed).append(" read_limit_reached=").append(limited).append('\n');
      result.append("The ZIP retains the current and previous native stage files. An unfinished span can reflect an active call, abrupt process exit, or missing evidence; it is not an ANR verdict.\n");
    } catch (Exception unavailable) { result.append("Native stage capture could not be read: ").append(unavailable.getClass().getSimpleName()).append('\n'); }
    return result.toString();
  }
'''
def apply(root,engine_sha):
 before={p.relative_to(root).as_posix():digest(p.read_bytes()) for p in root.rglob('*') if p.is_file()}
 for name in ALLOWED:
  p=root/name;p.write_text(transform(name,p.read_text(),engine_sha))
 after={p.relative_to(root).as_posix():digest(p.read_bytes()) for p in root.rglob('*') if p.is_file()}
 assert {n for n in before if before[n]!=after[n]}==ALLOWED
 return {'before':before,'after':after,'changed':sorted(ALLOWED),'engine_sha256':engine_sha}
