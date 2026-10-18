#!/usr/bin/env python3
"""Native-target-backed optional write errors, layered onto TEST3/2103383.

Only an operation actually recorded by Infinity's native mutation ledger can
prove the precise failed path. Unknown, spoofed, essential or concurrently
ambiguous failures stay fatal to Essential-First sealing. Python/provider text
alone is NEVER a permission to waive a protected save.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path

SCRIPT = "xbmc/platform/android/activity/InfinityScriptPersistence.h"
WRITES = "xbmc/platform/android/activity/InfinityProtectedWrites.h"
PINNED_TEST3_SCRIPT_SHA256 = "69f722917abd3aba5e86293b083b3ae6c32acbd06325faf0ed0585eddad7e62e"
PINNED_TEST3_STAGEFIX_SHA256 = "580a884e002bd95cbdd10a5c439b9052b7bdebebaf9473613da588c11f50cc9e"


def sha(value):
    return hashlib.sha256(value).hexdigest()


def once(text, old, replacement, name):
    if text.count(old) != 1:
        raise RuntimeError("Unverified original Infinity code anchor: " + name +
                           " (matches=" + str(text.count(old)) + ")")
    return text.replace(old, replacement, 1)


def patch_script(text):
    old = """  unsigned count{1};
  bool blocking{true};
};
struct Namespace"""
    new = """  unsigned count{1};
  bool blocking{true};
  // Captured ONLY from one active native mutation lease on the failing writer
  // thread. Never accept an add-on's path string as trusted provenance.
  std::vector<std::string> nativeFailureTargets;
  bool nativeFailureTargetVerified{false};
};
struct Namespace"""
    text = once(text, old, new, "Blocker native operation proof")

    anchor = "inline void AddBlockerLocked(State& s,int id,const std::string& writer,"
    helper = r'''// Error-to-operation mapping has an exact, bounded scope. Unsupported write
// errors intentionally have NO exemption. The lease must still be active at
// the point where the interpreter reports the failure.
inline const char* NativeIOOperationForError(const std::string& reason)
{
  if (reason == "vfs_write_exception" || reason == "vfs_write_failed") return "vfs.write";
  if (reason == "vfs_close_failed") return "vfs.close";
  if (reason == "buffered_write_failed" || reason == "short_buffered_write") return "file.write";
  if (reason == "buffer_truncate_failed") return "file.truncate";
  if (reason == "buffer_flush_failed") return "file.flush";
  if (reason == "buffer_close_failed") return "file.close";
  if (reason == "raw_file_write_failed") return "descriptor.write";
  if (reason == "raw_file_writev_failed") return "descriptor.writev";
  if (reason == "raw_file_pwrite_failed") return "descriptor.pwrite";
  if (reason == "raw_file_pwritev_failed") return "descriptor.pwritev";
  if (reason == "raw_file_ftruncate_failed") return "descriptor.ftruncate";
  if (reason == "raw_file_sendfile_failed") return "descriptor.sendfile";
  if (reason == "raw_file_copy_file_range_failed") return "descriptor.copy_file_range";
  if (reason == "namespace_open_failed") return "namespace.open";
  if (reason == "namespace_rename_failed") return "namespace.rename";
  if (reason == "namespace_replace_failed") return "namespace.replace";
  if (reason == "namespace_remove_failed") return "namespace.remove";
  if (reason == "namespace_unlink_failed") return "namespace.unlink";
  if (reason == "namespace_mkdir_failed") return "namespace.mkdir";
  if (reason == "namespace_rmdir_failed") return "namespace.rmdir";
  if (reason == "namespace_truncate_failed") return "namespace.truncate";
  if (reason == "vfs_open_for_write_failed") return "vfs.open";
  if (reason == "vfs_copy_failed" || reason == "vfs_copy_exception") return "vfs.copy";
  if (reason == "vfs_rename_failed" || reason == "vfs_rename_exception") return "vfs.rename";
  if (reason == "vfs_delete_failed" || reason == "vfs_delete_exception") return "vfs.delete";
  if (reason == "vfs_mkdir_failed" || reason == "vfs_mkdir_exception") return "vfs.mkdir";
  if (reason == "vfs_mkdirs_failed" || reason == "vfs_mkdirs_exception") return "vfs.mkdirs";
  if (reason == "vfs_rmdir_failed" || reason == "vfs_rmdir_exception") return "vfs.rmdir";
  return nullptr;
}
'''
    text = once(text, anchor, helper + "\n" + anchor, "native error-operation allowlist")

    old = """inline void AddBlockerLocked(State& s,int id,const std::string& writer,
                             const std::string& reason,const std::string& detail,
                             bool blocking=true)
{
  const auto safeWriter=writer.substr(0,512),safeReason=reason.substr(0,384),safeDetail=detail.substr(0,2048);
  for(auto& blocker:s.blockers)
    if(blocker.writerId==id && blocker.writer==safeWriter &&
       blocker.reason==safeReason && blocker.detail==safeDetail && blocker.blocking==blocking) {
      if(blocker.count<UINT_MAX)++blocker.count;
      return;
    }
  if(s.blockers.size()>=128){s.blockerOverflow=true;if(blocking)s.blockingOverflow=true;return;}
  s.blockers.push_back({id,safeWriter,safeReason,safeDetail,1,blocking});
}"""
    new = """inline void AddBlockerLocked(State& s,int id,const std::string& writer,
                             const std::string& reason,const std::string& detail,
                             bool blocking=true,
                             const std::vector<std::string>& nativeTargets={},
                             bool nativeProof=false)
{
  const auto safeWriter=writer.substr(0,512),safeReason=reason.substr(0,384),safeDetail=detail.substr(0,2048);
  for(auto& blocker:s.blockers)
    if(blocker.writerId==id && blocker.writer==safeWriter &&
       blocker.reason==safeReason && blocker.detail==safeDetail && blocker.blocking==blocking &&
       blocker.nativeFailureTargetVerified==nativeProof &&
       blocker.nativeFailureTargets==nativeTargets) {
      if(blocker.count<UINT_MAX)++blocker.count;
      return;
    }
  if(s.blockers.size()>=128){s.blockerOverflow=true;if(blocking)s.blockingOverflow=true;return;}
  s.blockers.push_back({id,safeWriter,safeReason,safeDetail,1,blocking,nativeTargets,nativeProof});
}"""
    text = once(text, old, new, "native-target-owned blocker records")

    old = """  std::string writer;
  if(found!=s.writers.end() && !found->second.admissions.empty())
    writer=found->second.admissions.begin()->first.substr(0,512);
  AddBlockerLocked(s,id,writer,reason,detail,blocking);
  if(blocking && s.failure.empty()) {"""
    new = """  std::string writer;
  if(found!=s.writers.end() && !found->second.admissions.empty())
    writer=found->second.admissions.begin()->first.substr(0,512);
  // At the actual native error callback, observe the exact live operation.
  // A path written in detail, a previous write, a different writer/thread, or
  // multiple overlapping matching leases can NEVER authorize an exemption.
  std::vector<std::string> actualTargets;
  bool nativeProof=false;
  const char* expected=NativeIOOperationForError(reason);
  if(blocking && found!=s.writers.end() && expected!=nullptr)
  {
    unsigned matches=0;
    for(const auto& lease:s.protection.operations)
    {
      const auto& operation=lease.second;
      if(operation.writer!=id || operation.thread!=std::this_thread::get_id() ||
         operation.operation!=expected) continue;
      ++matches;
      if(matches==1) actualTargets=operation.paths;
    }
    nativeProof=matches==1 && !actualTargets.empty() && actualTargets.size()<=2 &&
      std::all_of(actualTargets.begin(),actualTargets.end(),[](const std::string& path) {
        return !path.empty() && path.front()=='/' &&
               path.find('\\0')==std::string::npos;
      });
    if(!nativeProof) actualTargets.clear();
  }
  AddBlockerLocked(s,id,writer,reason,detail,blocking,actualTargets,nativeProof);
  if(blocking && s.failure.empty()) {"""
    text = once(text, old, new, "native operation capture before error lease retires")
    return text


def patch_writes(text):
    old = """    bool privateOnly = bounded;
    const auto paths = p.writerPaths.find(blocker.writerId);
    if (paths == p.writerPaths.end() || paths->second.empty()) privateOnly = false;
    else for (const auto& path : paths->second) if (!OptionalPathLocked(p, path)) privateOnly = false;
    if (!privateOnly) proof.blockers.push_back("unverified_protected_writer:" + blocker.writer + ":" + reason);"""
    new = """    bool privateOnly = false;
    if (blocker.nativeFailureTargetVerified)
    {
      // Only ONE exact live native operation can establish these paths. The
      // writer identity, path, thread and operation were bound before the
      // failed call; an add-on's exception text is not evidence.
      privateOnly = NativeIOOperationForError(reason) != nullptr &&
                    p.participants.count(blocker.writerId) == 0 &&
                    !blocker.nativeFailureTargets.empty();
      for (const auto& path : blocker.nativeFailureTargets)
        if (!OptionalPathLocked(p, path)) privateOnly = false;
    }
    else if (bounded)
    {
      // Retain the original strict rules for previously reviewed bounded
      // buffered/SQLite errors with the COMPLETE writer path inventory.
      privateOnly = true;
      const auto paths = p.writerPaths.find(blocker.writerId);
      if (paths == p.writerPaths.end() || paths->second.empty()) privateOnly = false;
      else for (const auto& path : paths->second)
        if (!OptionalPathLocked(p, path)) privateOnly = false;
    }
    // Every unknown, ambiguous or protected write remains fatal, and the
    // separate open-transaction/dirty-buffer/native-child blockers are checked
    // below even when this one optional error was fully attributed.
    if (!privateOnly) proof.blockers.push_back("unverified_protected_writer:" + blocker.writer + ":" + reason);"""
    return once(text, old, new, "fail-closed optional native-target classification")


def apply(source, build, manifest_path, *, require_pins=True):
    source, build, manifest_path = Path(source), Path(build), Path(manifest_path)
    files = {SCRIPT: source / SCRIPT, WRITES: source / WRITES}
    before = {k: sha(v.read_bytes()) for k,v in files.items()}
    if require_pins:
        expected = {SCRIPT: PINNED_TEST3_SCRIPT_SHA256,
                    WRITES: PINNED_TEST3_STAGEFIX_SHA256}
        if before != expected:
            raise RuntimeError("Not exact built Infinity 2103383 source: " + repr(before))
    old_script = files[SCRIPT].read_text()
    old_writes = files[WRITES].read_text()
    new_script = patch_script(old_script)
    new_writes = patch_writes(old_writes)
    after = {SCRIPT: sha(new_script.encode()), WRITES: sha(new_writes.encode())}
    if any(before[k] == after[k] for k in files):
        raise RuntimeError("Targeted native correction did not change expected source")

    manifest = json.loads(manifest_path.read_text())
    proof_path = build / "FINAL-SHUTDOWN-SOURCE-PRESERVATION.json"
    proof = json.loads(proof_path.read_text())
    for name in files:
        if manifest["after"].get(name) != before[name] or proof["after"].get(name) != before[name]:
            raise RuntimeError("Native preservation map differs for " + name)
    prior = json.loads((build / "INFINITY-INDEPENDENT-SHUTDOWN-SOURCE-DELTA.json").read_text())
    if prior["changed"] != [WRITES] or prior["after"][WRITES] != before[WRITES]:
        raise RuntimeError("Prior 2103383 installer-stage correction missing")

    # Apply TWO and only two verified native files after restoring the exact
    # TEST3/2103383 compiled lineage. All existing feature changes remain.
    files[SCRIPT].write_text(new_script)
    files[WRITES].write_text(new_writes)
    for name in files:
        if sha(files[name].read_bytes()) != after[name]:
            raise RuntimeError("Mismatch after staging " + name)
    for dest in (manifest, proof):
        dest["after"].update(after)
        dest["changed"] = sorted(set(dest["changed"]) | set(files))
    proof.update(optional_writer_path_provenance_v1=True,
                 true_essential_saves_remain_fail_closed=True,
                 original_test4_untouched=True,
                 physical_fold_verified=False, locked=False)
    manifest_path.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    proof_path.write_text(json.dumps(proof,indent=2,sort_keys=True)+"\n")
    receipt = dict(schema=1, native_source_commit=os.environ.get("GITHUB_SHA","host"),
                   changed=sorted(files), before=before, after=after,
                   proven_path_source="one active native mutation lease on same writer/thread",
                   provider_strings_do_not_authorize_optional_writes=True,
                   unknown_unverified_and_essential_failures_fatal=True,
                   retains_existing_essential_first_close=True,
                   physical_fold_verified=False, apk_signed=False)
    (build / "OPTIONAL-WRITE-PROVENANCE-SOURCE-DELTA.json").write_text(
        json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    return receipt


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    for key in ("source","build","manifest"):
        parser.add_argument("--"+key,required=True,type=Path)
    args=parser.parse_args()
    print(json.dumps(apply(args.source,args.build,args.manifest),indent=2))
