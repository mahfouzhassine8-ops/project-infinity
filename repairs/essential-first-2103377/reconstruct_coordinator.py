#!/usr/bin/env python3
"""Reconstruct only the exact locked coordinator; verify each published hash.

No substitute upstream Kodi tree and no disabled lineage assertions. This
source subset is for a controlled host harness, not an ARM64 build input.
"""
import ast
import hashlib
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
REL = "xbmc/platform/android/activity/InfinityAndroidCheckpoint.cpp"
FINAL = "13b492e2fd4b1885fa2127ebf1ea8bd2ed31fd3cbf35ebe82d3a3044383fa04b"

def require_sha(text, expected):
    actual = hashlib.sha256(text.encode()).hexdigest()
    if actual != expected:
        raise ValueError("Locked native coordinator mismatch: " + actual)

def once(text, old, new):
    assert text.count(old) == 1, old[:80]
    return text.replace(old, new, 1)

def reconstruct(destination):
    sys.path.insert(0, str(ROOT / "repairs/shutdown-wide-trace-2103377"))
    import extend_trace
    overlay = ROOT / "repairs/android-checkpoint-shutdown/runtime/native/overlay"
    text = extend_trace.additional(REL, (overlay / REL).read_text())
    require_sha(text, "d86a695c950674b92cc5fd9ba0f18ec067899e61dd26e25224a2ae4cef70d746")
    tree = ast.parse((ROOT / "repairs/shutdown-drain-2103377/prune_optional_jobs.py").read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) and ast.unparse(node.targets[0]) == "text[CHECKPOINT]":
            text = once(text, ast.literal_eval(node.value.args[1]), ast.literal_eval(node.value.args[2]))
    require_sha(text, "723f680401a31b36c21ee7b2cfa673feb48f622cb96e31d9c6365e3b44c52bcf")
    target = Path(destination) / REL
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    spec = importlib.util.spec_from_file_location("locked_early_snapshot", ROOT / "repairs/shutdown-rc3-2103377/early_local_snapshot.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.apply(destination)  # Original preimage check remains active.
    text = target.read_text()
    require_sha(text, "c92712dc37edac14b321bc1a5aa287228b598b1ec79ee005b5d519c661f812c2")
    tree = ast.parse((ROOT / "repairs/shutdown-rc3-2103377/early_retirement.py").read_text())
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) and
            isinstance(node.targets[0], ast.Name) and node.targets[0].id == "c" and
            isinstance(node.value.func, ast.Name) and node.value.func.id == "once"):
            text = once(text, ast.literal_eval(node.value.args[1]), ast.literal_eval(node.value.args[2]))
    require_sha(text, "972d07e9301da0badd0bf04f995bf5c40cfb147d38bcc23da70ecb5b253c9c77")
    text = once(text, '#include "InfinityAndroidCheckpoint.h"',
                '#include "InfinityAndroidCheckpoint.h"\n#if defined(TARGET_ANDROID)\n#include "threads/InfinityStabilityProbe.h"\n#endif\n')
    text = once(text, '  const auto unresolved = CScriptInvocationManager::GetInstance().AndroidCheckpointUnresolvedWriters();',
                '  InfinityStabilityProbe::CloseRequested();\n  const auto unresolved = CScriptInvocationManager::GetInstance().AndroidCheckpointUnresolvedWriters();')
    require_sha(text, FINAL)
    target.write_text(text)
    return target

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    print(reconstruct(args.destination))
