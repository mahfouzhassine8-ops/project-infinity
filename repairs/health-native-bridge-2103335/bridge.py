#!/usr/bin/env python3
"""2103335: expose existing bounded native shutdown evidence in Health Center report.txt."""
from pathlib import Path
import hashlib, json

REL = "tools/android/packaging/xbmc/src/InfinityHealthExport.java.in"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def snapshot(root):
    return {p.relative_to(root).as_posix(): sha(p.read_bytes())
            for p in root.rglob("*") if p.is_file() and ".git" not in p.relative_to(root).parts}

def require(ok, message):
    if not ok:
        raise ValueError(message)

def transform(text):
    report = '      put(zip, "report.txt", report.getBytes(StandardCharsets.UTF_8));'
    require(text.count(report) == 1, "Health exporter report anchor changed")
    text = text.replace(
        report,
        '      put(zip, "report.txt", reportWithNativeShutdownEvidence(context, report).getBytes(StandardCharsets.UTF_8));',
        1)

    anchor = "  private static void put(ZipOutputStream zip, String name, byte[] bytes) throws Exception {"
    require(text.count(anchor) == 1, "Health exporter helper anchor changed")
    helper = r'''  private static String reportWithNativeShutdownEvidence(Context context, String report)
  {
    StringBuilder output = new StringBuilder(report == null ? "" : report);
    appendNativeShutdownEvidence(output, context, "Previous / failed native shutdown critical timeline",
        "infinity-shutdown-native.jsonl.critical.previous");
    appendNativeShutdownEvidence(output, context, "Current native shutdown critical timeline",
        "infinity-shutdown-native.jsonl.critical");
    return output.toString();
  }

  private static void appendNativeShutdownEvidence(
      StringBuilder output, Context context, String title, String fileName)
  {
    java.io.File source = new java.io.File(context.getFilesDir(), fileName);
    output.append("\n\n").append(title).append("\n")
        .append("========================================\n");
    if (!source.isFile()) {
      output.append("[not present — absence is not a clean-exit verdict]\n");
      return;
    }
    try (java.io.InputStream input = new java.io.FileInputStream(source);
         java.io.ByteArrayOutputStream bytes = new java.io.ByteArrayOutputStream()) {
      final int limit = 512 * 1024;
      boolean truncated = copyBounded(input, bytes, limit);
      output.append(new String(bytes.toByteArray(), StandardCharsets.UTF_8));
      if (truncated)
        output.append("\n[critical timeline truncated to ").append(limit).append(" bytes]\n");
    } catch (Exception failure) {
      output.append("[could not read native timeline: ")
          .append(failure.getClass().getSimpleName()).append("]\n");
    }
  }

'''
    return text.replace(anchor, helper + anchor, 1)

def apply(source, parent_proof, receipt):
    parent = json.loads(parent_proof.read_text())
    before = snapshot(source)
    require(before == parent["after"], "Not exact 2103334 Android source")
    path = source / REL
    original = path.read_text()
    path.write_text(transform(original))
    after = snapshot(source)
    changed = sorted(name for name in before.keys() | after.keys()
                     if before.get(name) != after.get(name))
    require(changed == [REL] and before.keys() == after.keys(),
            "Diagnostic bridge changed undeclared source: " + repr(changed))
    result = {
        "candidate": 2103335,
        "parent": 2103334,
        "before": before,
        "after": after,
        "changed": changed,
        "shutdown_behavior_changed": False,
        "native_recompiled": False,
        "diagnostics_only": True,
        "physical_device_verified": False,
        "locked": False,
    }
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

def verify(source, receipt):
    proof = json.loads(receipt.read_text())
    actual = snapshot(source)
    require(actual == proof["after"], "2103335 diagnostic source changed after preparation")
    require(proof["changed"] == [REL], "Unexpected diagnostic bridge scope")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["apply", "verify"])
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--parent-proof", type=Path)
    p.add_argument("--receipt", type=Path, required=True)
    a = p.parse_args()
    if a.mode == "apply":
        apply(a.source, a.parent_proof, a.receipt)
    else:
        verify(a.source, a.receipt)
    print("PASS: Health Center native critical timeline bridge; shutdown behavior untouched")
