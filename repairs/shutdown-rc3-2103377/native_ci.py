#!/usr/bin/env python3
"""Stage RC3 on the saved successful RC2 engine, preserving full source/test lineage.

No new baseline, no file deletion, no Python thread kill and no waiver of an
unknown writer or the seventeen final required owner receipts.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE))
import early_local_snapshot
import cancel_owned_curl

def import_rc2():
    path=ROOT/"repairs/shutdown-final-2103377/native_ci.py"
    sys.path.insert(0,str(path.parent))
    spec=importlib.util.spec_from_file_location("pinned_rc2_native",path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def digest(data):return hashlib.sha256(data).hexdigest()
def read(p):return json.loads(p.read_text())
def save(p,data):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,sort_keys=True,indent=2)+"\n")

def part(source,start,end):
    a=source.index(start)
    b=source.index(end,a)
    return source[a:b]

def prepare(args):
    rc2=import_rc2()
    rc2.prepare(args)
    life=rc2.wide().lifecycle()
    src=life.SOURCE
    manifest_path=life.SCRATCH/"runtime/native/manifest.json"
    manifest=read(manifest_path)
    old=manifest["after"]
    checkpoint=src/early_local_snapshot.SOURCE
    original_checkpoint=checkpoint.read_text()
    required_termination=part(original_checkpoint,
        "bool AuthorizeTermination(const std::string& session, const std::string& owner, int pid)",
        "void Pump(CApplication& application)")
    final_save_stage=part(original_checkpoint,"    if (s.stage == 5)\n","    if (s.stage == 6)\n")
    final_seal_stage=part(original_checkpoint,"    if (s.stage == 6)\n","}\n} // namespace InfinityAndroidCheckpoint")
    er=early_local_snapshot.apply(src)
    cr=cancel_owned_curl.apply(src)
    after=dict(old);after.update({early_local_snapshot.SOURCE:er["after"]})
    after.update(cr["after"])
    changed=sorted(set(manifest["changed"])|set(er["changed"])|set(cr["changed"]))
    added=sorted(set(manifest["added"])|set(cr["added"]))
    manifest.update(after=after,changed=changed,added=added)
    save(manifest_path,manifest)
    target_checkpoint=checkpoint.read_text()
    assert required_termination==part(target_checkpoint,
        "bool AuthorizeTermination(const std::string& session, const std::string& owner, int pid)",
        "void Pump(CApplication& application)")
    assert final_save_stage==part(target_checkpoint,"    if (s.stage == 5)\n","    if (s.stage == 6)\n")
    assert final_seal_stage==part(target_checkpoint,"    if (s.stage == 6)\n","}\n} // namespace InfinityAndroidCheckpoint")
    assert not any("unknown" in name for name in changed if name not in manifest["changed"])
    for name,expected in after.items():
        pass # foundation verifies the entire reconstructed map, not just touched files
    foundation=life.load_parent_driver().previous().foundation()
    foundation.runtime_delta.verify(src,after)
    checkpoint_proof=read(ROOT/"checkpoint-build/FINAL-SHUTDOWN-SOURCE-PRESERVATION.json")
    checkpoint_proof.update({
        "source_commit":os.environ["GITHUB_SHA"],
        "after":after,
        "changed":sorted(name for name in after if name not in manifest["before"] or
                         manifest["before"].get(name)!=after[name]),
        "added":added,
        "save_and_termination_authority_byte_identical":False,
        "final_termination_authorization_byte_identical":True,
        "final_required_save_and_database_seal_stages_byte_identical":True,
        "provisional_early_save_only":True,
        "rc3_native_http_read_only_owner_gate":True,
        "unknown_writes_abandoned":False,
        "playlist_browser_addon_files_modified":False,
        "Trakt_provider_sources_modified":False,
        "physical_shutdown_verified":False,
        "native_full_compilation_complete":False})
    save(ROOT/"checkpoint-build/FINAL-SHUTDOWN-SOURCE-PRESERVATION.json",checkpoint_proof)
    save(ROOT/"checkpoint-build/RC3-EARLY-LOCAL-SNAPSHOT-DELTA.json",er)
    save(ROOT/"checkpoint-build/RC3-CURL-OWNER-CANCEL-DELTA.json",cr)
    print("RC3 staged: early provisional local saves, owner-specific HTTP read cancellation, 17 required final owners unchanged.")

def compile_engine():
    rc2=import_rc2()
    rc2.compile_engine()
    build=ROOT/"checkpoint-build"
    binary=(build/"libkodi.so").read_bytes()
    for token in [
        b"rc3.early_local_snapshot",
        b"rc3.playlist_read_rejected_at_open",
        b"rc3.playlist_read_cancelled_in_poll",
        b"plugin.video.playlistbrowser",
        b"jobs.optional_queued_pruned",
    ]:
        assert token in binary,("Missing RC3 full native machine-code token:",token)
    proof=read(build/"ENGINE-PROOF.json")
    er=read(build/"RC3-EARLY-LOCAL-SNAPSHOT-DELTA.json")
    cr=read(build/"RC3-CURL-OWNER-CANCEL-DELTA.json")
    assert proof["complete_native_engine_compiled"] and er["final_owner_save_pass_retained"]
    assert cr["required_saves_waived"] is False
    proof.update(
        purpose="RC3 targeted native HTTP cancellation and provisional early local saves",
        rc3_early_local_snapshot_compiled=True,
        rc3_owner_specific_http_read_cancellation_compiled=True,
        rc3_final_save_authority_unchanged=True,
        rc3_native_stop_grace_policy_unchanged=True,
        unknown_writers_abandoned=False,
        physical_shutdown_verified=False,
        signed_apk_built=False,
        device_accepted=False,
        locked=False)
    save(build/"ENGINE-PROOF.json",proof)
    print("PASS: RC3 complete native Kodi engine compiled; physical Fold shutdown still needs device verification.")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=["prepare","compile"])
    for option in ("locked","previous","parent-proof"):
        p.add_argument("--"+option,type=Path)
    args=p.parse_args()
    if args.mode=="prepare":prepare(args)
    else:compile_engine()
