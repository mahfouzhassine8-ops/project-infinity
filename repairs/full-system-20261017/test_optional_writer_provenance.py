#!/usr/bin/env python3
"""Exercise the REAL revised native ledger: one process per fault scenario.

No fake C++ shims, mocked VFS decisions, bypassed save receipts or stock-Kodi
substitute. This host test compiles the actual Infinity persistence headers
after the same two verified source transforms used by the ARM64 producer.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
SOURCE=ROOT/"repairs/essential-first-2103377/runtime/xbmc/platform/android/activity/InfinityScriptPersistence.h"
WRITES=HERE/"InfinityProtectedWrites.stagefix.h"
TEST=HERE/"test_optional_writer_provenance.cpp"
SCENARIOS=(
    "optional_vfs_error","optional_vfs_false","optional_buffer_error",
    "essential_pending","optional_sqlite_pending","optional_corrupt_path",
    "native_ambiguous","essential_participant","essential_vfs",
    "settings_vfs","command_center_vfs","symlink_vfs",
    "spoofed_path","wrong_operation","unknown_error","no_native_path",
)

def run():
    spec=importlib.util.spec_from_file_location("optional_writer_patch",HERE/"optional_writer_provenance_patch.py")
    tool=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    with tempfile.TemporaryDirectory(prefix="infinity-native-optional-writer-") as directory:
        temp=Path(directory)
        old=SOURCE.read_text()
        stage=WRITES.read_text()
        script=tool.patch_script(old)
        writes=tool.patch_writes(stage)
        assert script!=old and writes!=stage
        (temp/"InfinityScriptPersistence.h").write_text(script)
        (temp/"InfinityProtectedWrites.h").write_text(writes)
        binary=temp/"native-writer-provenance"
        compile=subprocess.run(["g++","-std=c++17","-O2","-Wall","-Wextra","-Werror",
            "-pthread","-I",str(temp),str(TEST),"-o",str(binary)],
            capture_output=True,text=True,timeout=75)
        if compile.returncode:
            raise RuntimeError("Production header compilation failed:\n"+
                               compile.stdout+"\n"+compile.stderr)
        rows=[]
        for name in SCENARIOS:
            completed=subprocess.run([str(binary),name],
                capture_output=True,text=True,timeout=8)
            if completed.returncode:
                raise RuntimeError(f"Native scenario {name} failed code={completed.returncode}:\n"
                                   f"{completed.stdout}\n{completed.stderr}")
            rows.append({"scenario":name,"result":"passed"})
        return {"scope":"real Infinity persistence source and stagefix, native operation ownership",
                "scenarios":rows,"compiled_cpp":True,"all_cases_passed":True,
                "original_test4_source_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                "native_stagefix_sha256":hashlib.sha256(WRITES.read_bytes()).hexdigest(),
                "hardware_fold_verified":False,"signed_apk_produced":False}

if __name__=="__main__":
    result=run()
    print(json.dumps(result,indent=2))
