#!/usr/bin/env python3
"""Narrow, provenance-bound audit of Kodi-native failed-write classification.

Preserves historical TEST4/TEST3/2103383. This is NOT a new shutdown owner
and MUST NOT suppress unscoped VFS, SQLite, native, or essential write errors.
A claimed optional failure only becomes eligible for optional handling when
the actual file is bound to an in-flight native VFS write lease.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NATIVE = {
    "script": "xbmc/platform/android/activity/InfinityScriptPersistence.h",
    "writes": "xbmc/platform/android/activity/InfinityProtectedWrites.h",
    "bridge": "xbmc/interfaces/python/InfinityPythonPersistence.h",
    "source": "xbmc/interfaces/python/InfinityPythonPersistenceSource.h",
}
# Verified *reconstructed* native 2103383 source, from the passed native run
# 39083031276. Historical input header files are never modified here.
SOURCE_HASHES = {
    "script": "69f722917abd3aba5e86293b083b3ae6c32acbd06325faf0ed0585eddad7e62e",
    "writes": "580a884e002bd95cbdd10a5c439b9052b7bdebebaf9473613da588c11f50cc9e",
    "bridge": "abf7ee47395a998bd983dc95fbe66deeb8f91d79be0ebb7db8224191098d754e",
    "source": "f2ef91219be97cb9c2eacc9d0517483d03f4ab952246fd98a2d5e77211f8f53b",
}
ORIGINAL_NATIVE_RUN = 39083031276
ORIGINAL_NATIVE_COMMIT = "3e5e5e4f8d65464153243de9179dd24fb090d05e"

def once(body, old, new):
    count = body.count(old)
    if count != 1:
        raise RuntimeError(f"Protected native source anchor mismatch: {old[:72]!r}, found {count}")
    return body.replace(old, new, 1)

def patch_script(text):
    text=once(text,'''  bool blocking{true};
};
struct Namespace''','''  bool blocking{true};
  // Captured ONLY by an in-flight, real native VFS write lease; never
  // serialized in diagnostics (paths may include private account material).
  std::string verifiedWriteTarget;
};
struct Namespace''')
    text=once(text,'''                             bool blocking=true)
{''','''                             bool blocking=true,
                             const std::string& verifiedWriteTarget={})
{''')
    text=once(text,'''    blocker.reason==safeReason && blocker.detail==safeDetail && blocker.blocking==blocking) {''','''    blocker.reason==safeReason && blocker.detail==safeDetail && blocker.blocking==blocking &&
    blocker.verifiedWriteTarget==verifiedWriteTarget) {''')
    text=once(text,'''  s.blockers.push_back({id,safeWriter,safeReason,safeDetail,1,blocking});''','''  s.blockers.push_back({id,safeWriter,reason,safeDetail,1,blocking,verifiedWriteTarget});''')
    text=once(text,'''inline void Fail(int id, const std::string& reason, const std::string& detail={})
{''','''inline void Fail(int id, const std::string& reason, const std::string& detail={},
                 const std::string& verifiedWriteTarget={})
{''')
    text=once(text,'''  AddBlockerLocked(s,id,writer,reason,detail,blocking);''','''  AddBlockerLocked(s,id,writer,reason,detail,blocking,verifiedWriteTarget);''')
    return text

def patch_writes(text):
    marker='''inline bool OptionalBasePathLocked(const WriteProtection& p, const std::string& raw)
{'''
    trace='''// A VFS write error is path-scoped only when the native ledger holds the
// matching, live, same-thread writer lease. Python-supplied paths and add-on IDs
// alone NEVER establish optionality. This check works before Close is requested:
// the optionality decision occurs later under the actual protected profile map.
inline std::string VerifiedVfsWriteFailureTarget(int writer,
                                                  const std::string& operation,
                                                  const std::string& raw)
{
  if (operation != "vfs.write" || raw.empty() || raw.front() != '/')
    return {};
  const auto canonical = ProtectedCanonical(raw);
  if (canonical.empty()) return {};
  auto& state = Get();
  std::lock_guard<std::mutex> lock(state.mutex);
  if (!state.writers.count(writer)) return {};
  for (const auto& entry : state.protection.operations)
  {
    const auto& live = entry.second;
    if (live.writer != writer || live.operation != operation ||
        live.thread != std::this_thread::get_id() ||
        live.paths.size() != 1) continue;
    const auto leasePath = ProtectedCanonical(live.paths.front());
    if (leasePath == canonical) return canonical;
  }
  return {};
}

'''
    text=once(text,marker,trace+marker)
    anchor='''    bool privateOnly = bounded;
    const auto paths = p.writerPaths.find(blocker.writerId);
    if (paths == p.writerPaths.end() || paths->second.empty()) privateOnly = false;
    else for (const auto& path : paths->second) if (!OptionalPathLocked(p, path)) privateOnly = false;
    if (!privateOnly) proof.blockers.push_back("unverified_protected_writer:" + blocker.writer + ":" + reason);'''
    change='''    bool privateOnly = bounded;
    const auto paths = p.writerPaths.find(blocker.writerId);
    if (paths == p.writerPaths.end() || paths->second.empty()) privateOnly = false;
    else for (const auto& path : paths->second) if (!OptionalPathLocked(p, path)) privateOnly = false;
    // Only exact VFS WRITE outcomes can inherit their own verified target.
    // A failed optional write is not an essential save receipt. Recheck
    // canonical path, aliases, required-participant classification and genuine
    // tracked mutation under the FINAL trusted profile roots. Every other
    // failure remains unchanged, and the independently tracked operations,
    // unflushed buffers, and SQLite transactions below still block Close.
    if (!privateOnly &&
        (reason == "vfs_write_exception" || reason == "vfs_write_failed") &&
        !blocker.verifiedWriteTarget.empty() &&
        !p.participants.count(blocker.writerId) &&
        OptionalPathLocked(p, blocker.verifiedWriteTarget) &&
        paths != p.writerPaths.end())
    {
      bool allWriterPathsOptional = true;
      bool targetWasInventoried = false;
      for (const auto& written : paths->second)
      {
        // A writer that ALSO touched an essential/unknown path must not
        // assert the failed native VFS handle could affect optional data
        // only. This protects against mutable Python handle attributes.
        if (!OptionalPathLocked(p, written))
        {
          allWriterPathsOptional = false;
          break;
        }
        if (ProtectedCanonical(written) == blocker.verifiedWriteTarget)
          targetWasInventoried = true;
      }
      privateOnly = allWriterPathsOptional && targetWasInventoried;
    }
    if (!privateOnly) proof.blockers.push_back("unverified_protected_writer:" + blocker.writer + ":" + reason);'''
    text=once(text,anchor,change)
    return text

def patch_bridge(text):
    original='''  auto* context=Capsule(self);const char* reason=nullptr;const char* detail="";
  if(!context || !PyArg_ParseTuple(args,"s|s",&reason,&detail))return nullptr;
  InfinityScriptPersistence::Fail(context->id,reason,detail);Py_RETURN_NONE;'''
    replacement='''  auto* context=Capsule(self);const char* reason=nullptr;const char* detail="";
  const char* target=nullptr;
  if(!context || !PyArg_ParseTuple(args,"s|sz",&reason,&detail,&target))return nullptr;
  std::string verified;
  if (target && (std::strcmp(reason,"vfs_write_exception")==0 ||
                 std::strcmp(reason,"vfs_write_failed")==0))
    verified=InfinityScriptPersistence::VerifiedVfsWriteFailureTarget(
        context->id,"vfs.write",target);
  // Bad/forged/absent path or wrong operation leaves the error fatal.
  // Never send the path itself to the diagnostic Error() detail.
  InfinityScriptPersistence::Fail(context->id,reason,detail,verified);
  Py_RETURN_NONE;'''
    return once(text,original,replacement)

def patch_python_source(text):
    original='''    def error(self, operation, detail=''):
        # Native admission rejected the call BEFORE it could mutate anything.'''
    replacement='''    def error(self, operation, detail='', target=None):
        # Native admission rejected the call BEFORE it could mutate anything.'''
    text=once(text,original,replacement)
    original='''        if detail:
            self.fail(operation, detail)
        else:
            self.fail(operation)

    def sqlite_error'''
    replacement='''        if target is not None and self.protect is not None and operation in (
                'vfs_write_exception', 'vfs_write_failed'):
            # Target is NOT a permission waiver. The native Error callback
            # must prove a matching active VFS-write lease before recording
            # source provenance; otherwise this remains an unknown blocker.
            self.fail(operation, detail, target)
        elif detail:
            self.fail(operation, detail)
        else:
            self.fail(operation)

    def sqlite_error'''
    text=once(text,original,replacement)
    text=once(text,'''            if result is not True: self.observer.error('vfs_write_failed')''',
              '''            if result is not True: self.observer.error(
                'vfs_write_failed', target=self._infinity_path)''')
    text=once(text,'''            self.observer.error('vfs_write_exception')''',
              '''            self.observer.error(
                'vfs_write_exception', target=self._infinity_path)''')
    return text

PATCHES = {
    "script": patch_script,
    "writes": patch_writes,
    "bridge": patch_bridge,
    "source": patch_python_source,
}

def sha(value):
    return hashlib.sha256(value).hexdigest()

def apply(source, build, manifest_path):
    source=Path(source);build=Path(build);manifest_path=Path(manifest_path)
    old_manifest=json.loads(manifest_path.read_text())
    preserve_path=build/"FINAL-SHUTDOWN-SOURCE-PRESERVATION.json"
    preserve=json.loads(preserve_path.read_text())
    old_map=preserve["after"].copy()
    for kind,path in NATIVE.items():
        actual=sha((source/path).read_bytes())
        if not (actual==SOURCE_HASHES[kind]==old_manifest["after"].get(path)==old_map.get(path)):
            raise RuntimeError("Refusing write-scope correction: previous TEST3/2103383 source changed: "+path)
    for kind,path in NATIVE.items():
        current=(source/path).read_text()
        changed=PATCHES[kind](current)
        if changed==current: raise RuntimeError("No write-scope change: "+path)
        (source/path).write_text(changed)
    after={}
    for kind,path in NATIVE.items():
        digest=sha((source/path).read_bytes())
        if digest == SOURCE_HASHES[kind]: raise RuntimeError("Write scope overlay did not land: "+path)
        after[path]=digest
    # Original TEST4 source and the existing 2103383 durability-only overlay
    # must not be modified. The coordinator and all prior watched/ANR/touch
    # source hashes remain identical to the real signed candidate.
    coordinator="xbmc/platform/android/activity/InfinityAndroidCheckpoint.cpp"
    if sha((source/coordinator).read_bytes())!=old_map[coordinator]:
        raise RuntimeError("Essential-First shutdown coordinator changed")
    for path in NATIVE.values():
        preserve["after"][path]=after[path]
        old_manifest["after"][path]=after[path]
    old_manifest["changed"]=sorted(set(old_manifest["changed"])|set(NATIVE.values()))
    preserve["changed"]=sorted(set(preserve["changed"])|set(NATIVE.values()))
    preserve.update(scoped_native_vfs_write_error_provenance=True,
                    global_write_error_suppression=False,
                    essential_profile_and_database_writes_still_blocking=True,
                    original_test4_source_untouched=True,
                    physical_fold_verified=False,locked=False)
    manifest_path.write_text(json.dumps(old_manifest,sort_keys=True,indent=2)+"\n")
    preserve_path.write_text(json.dumps(preserve,sort_keys=True,indent=2)+"\n")
    receipt={
        "schema":1,"source_provenance":os.environ.get("GITHUB_SHA","local"),
        "preimage_commit":ORIGINAL_NATIVE_COMMIT,"preimage_run":ORIGINAL_NATIVE_RUN,
        "changed":sorted(NATIVE.values()),
        "before":{name:SOURCE_HASHES[kind] for kind,name in NATIVE.items()},
        "after":after,
        "no_class_wide_advisory_exemptions":True,
        "actual_native_vfs_write_lease_required":True,
        "path_not_serialized_to_health_diagnostics":True,
        "opaque_fatal_writes_remain_fatal":True,
        "native_sqlite_and_essential_protection_unchanged":True,
        "coordinator_unchanged":True,
        "signed_apk_created":False,
        "physical_fold_verified":False,
        "final_lock_authorized":False,
    }
    (build/"INFINITY-WRITE-ERROR-SCOPE-DELTA.json").write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
    return receipt

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",required=True,type=Path)
    p.add_argument("--build",required=True,type=Path)
    p.add_argument("--manifest",required=True,type=Path)
    args=p.parse_args()
    print(json.dumps(apply(args.source,args.build,args.manifest),indent=2))
