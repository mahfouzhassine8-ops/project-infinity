#!/usr/bin/env python3
"""Verify exact 2103384 binary and full source map from a RED post-link run.

The original workflow remains FAILED. No recompile, forged native success,
user data modification, unsafe write waiver or physical Fold acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path

SOURCE="3795b1b03731cba567e091913299c1888805373c"
BINARY="803552debcb883a46778e7c84bf25fa8dbd51e90d5c5025f8145dbf66560d405"
CHANGED={
 "xbmc/interfaces/python/InfinityPythonPersistence.h":"5cb7f53e2fffe92255db1acff08d2fb11279956f8adabdc9ca5aff5219cf9d40",
 "xbmc/interfaces/python/InfinityPythonPersistenceSource.h":"06bc4abcc5cbf592290e95ab20288586f8e624b4fdd5187d4fa91533bd54eb7d",
 "xbmc/platform/android/activity/InfinityProtectedWrites.h":"0446665ee568f5b15f28a0e2a09c421e08ff4bbe3cb73e9deb6d48cdd1d527ad",
 "xbmc/platform/android/activity/InfinityScriptPersistence.h":"f7b241da7d0f6643afc1f8c1e10ab3f8ad0b999823cd1c223693bf6ff586037c"
}
BEFORE={
 "xbmc/interfaces/python/InfinityPythonPersistence.h":"abf7ee47395a998bd983dc95fbe66deeb8f91d79be0ebb7db8224191098d754e",
 "xbmc/interfaces/python/InfinityPythonPersistenceSource.h":"f2ef91219be97cb9c2eacc9d0517483d03f4ab952246fd98a2d5e77211f8f53b",
 "xbmc/platform/android/activity/InfinityProtectedWrites.h":"580a884e002bd95cbdd10a5c439b9052b7bdebebaf9473613da588c11f50cc9e",
 "xbmc/platform/android/activity/InfinityScriptPersistence.h":"69f722917abd3aba5e86293b083b3ae6c32acbd06325faf0ed0585eddad7e62e"
}

def check(condition,message):
    if not condition:raise RuntimeError("RECOVERED COMPILED APK INPUT REJECTED: "+message)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(4*1024*1024),b""):h.update(block)
    return h.hexdigest()

def verify(folder,destination):
    folder=Path(folder);destination=Path(destination)
    def obj(name):return json.loads((folder/name).read_text())
    engine=folder/"libkodi.so"
    check(engine.is_file() and engine.stat().st_size>100_000_000,"No compiled Infinity engine")
    with engine.open("rb") as f:prefix=f.read(20)
    check(prefix[:5]==b"\x7fELF\x02" and int.from_bytes(prefix[18:20],"little")==183,"Engine is not ARM64 ELF")
    digest=sha(engine)
    check(digest==BINARY,"Engine differs from exact compiled artifact")
    raw=obj("ENGINE-PROOF.json")
    changed=obj("INFINITY-WRITE-ERROR-SCOPE-DELTA.json")
    base=obj("LOCKED-TEST4-SOURCE-PRESERVATION.json")
    final=obj("FINAL-SHUTDOWN-SOURCE-PRESERVATION.json")
    fold=obj("FOLD-DEADLOCK-SOURCE-DELTA.json")
    watched=obj("WATCHED-TOUCH-SOURCE-DELTA.json")
    stage=obj("INFINITY-INDEPENDENT-SHUTDOWN-SOURCE-DELTA.json")
    check(raw.get("native_sha256")==digest and raw.get("source_commit")==SOURCE and
          changed.get("source_provenance")==SOURCE,"Original compilation identity mismatch")
    for flag in ("complete_native_engine_compiled","fold_callback_retirement_compiled",
                 "watched_presentation_bridge_compiled","browse_touch_preselection_compiled"):
        check(raw.get(flag) is True,"Missing original linked engine proof: "+flag)
    check(raw.get("shutdown_policy")=="essential_first_process_exit_v1" and
          raw.get("locked") is False and raw.get("physical_device_verified") is False,
          "Native proof falsely changes shutdown/approval policy")
    check(set(changed["changed"])==set(CHANGED) and
          changed["after"]==CHANGED and changed["before"]==BEFORE,
          "Not the four exact reviewed source-file changes")
    for flag in ("actual_native_vfs_write_lease_required",
                 "no_class_wide_advisory_exemptions","opaque_fatal_writes_remain_fatal",
                 "native_sqlite_and_essential_protection_unchanged","coordinator_unchanged"):
        check(changed.get(flag) is True,"Missing fail-closed VFS invariant: "+flag)
    check(stage["after"]["xbmc/platform/android/activity/InfinityProtectedWrites.h"]==
          BEFORE["xbmc/platform/android/activity/InfinityProtectedWrites.h"],
          "Prior 2103383 installer durability correction not preserved")
    check(watched.get("native_shutdown_and_write_admission_unchanged") is True and
          fold.get("shutdown_coordinator_unchanged") is True,
          "Existing watched/touch/deadlock native work lost")
    coordinator="xbmc/platform/android/activity/InfinityAndroidCheckpoint.cpp"
    check(base["after"].get(coordinator)==final["after"].get(coordinator) and
          final.get("original_test4_source_untouched") is True and
          final.get("essential_first_coordinator_unchanged") is True and
          final.get("global_write_error_suppression") is False,
          "Original protected Essential-First coordinator/source compromised")
    for path,expected in CHANGED.items():
        check(final["after"].get(path)==expected,"Unexpected actual native source: "+path)
    allowed=set(changed["changed"])|set(watched["changed"])|set(fold["changed"])
    differences={k for k in set(base["after"])|set(final["after"])
                 if base["after"].get(k)!=final["after"].get(k)}
    check(differences==allowed,"Unreviewed native source changes: "+repr(differences^allowed))
    check(len(base["after"])==9402 and len(final["after"])==9404,
          "Complete native source map cardinality changed")
    compiler=(folder/"RAILS-HANDOFF-NATIVE-COMPILE.log").read_text(errors="replace")
    check("100%] Built target libkodi" in compiler and
          "PASS: full native engine linked and native entry exports verified" in compiler,
          "Linker never finished its native build")
    check("RuntimeError: Native source not compiled from reviewed correction" in compiler,
          "Previous failure was NOT the reviewed post-link stale check")
    receipt={"schema":1,
       "original_native_run":39088898437,
       "original_run_conclusion":"failure",
       "original_run_failure":"stale post-link 2103383 single-header SHA assertion",
       "validation":"actual linked native binary and source preservation independently verified",
       "native_source_commit":SOURCE,
       "compiled_engine_sha256":digest,
       "reviewed_native_changes":CHANGED,
       "compile_and_link_finished":True,
       "compiled_native_artifact_reused_without_rebuild":True,
       "original_failed_run_remains_failed":True,
       "signed_apk_published":False,
       "emulator_shutdown_verified":False,
       "physical_fold_verified":False,
       "final_lock_authorized":False}
    destination.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,indent=2))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--native",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    x=p.parse_args()
    verify(x.native,x.out)
