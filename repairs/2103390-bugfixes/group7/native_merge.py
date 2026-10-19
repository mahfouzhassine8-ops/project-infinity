#!/usr/bin/env python3
"""Exact 2103391 native Group2+3+6 source merger atop reconstructed 2103385.

Prerequisite (CI): the EXISTING exact-source four-repair/native_ci.py prepare
has reconstructed the locked 2103384 source plus approved 2103385 UI input.

No source archives, shutdown owners or Cobra files are changed. A matched
native inventory and preserved compiler's own manifest are mandatory before
attempting the original complete Android Kodi engine compile.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
GROUPS=HERE.parent
for group in ("group2","group3","group6"):
    sys.path.insert(0,str(GROUPS/group))
import native_addonbrowser_patch as addon
import native_option_b_patch as option
import silent_mode_patch as silent

NATIVE_ALLOWLIST=set(addon.FILES)|set(option.NATIVE_FILES)|{silent.NATIVE_FILE}
EXPECTED_COUNT=8
REQUIRED_OLD_HOLD="OnInfinityRailLongPress"
REQUIRED_NEW_HOLD="OnInfinityOptionBLongPress"


def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(path,data):
    Path(path).write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")


def integrate(native_root:Path,checkpoint:Path)->dict:
    native_root=Path(native_root).resolve()
    checkpoint=Path(checkpoint).resolve()
    paths=sorted(NATIVE_ALLOWLIST)
    if len(paths)!=EXPECTED_COUNT or not all(p.startswith("xbmc/") for p in paths):
        raise RuntimeError("Unexpected Group7 native source allowlist")
    originals={name:(native_root/name).read_bytes() for name in paths}
    current=dict(originals)
    for name in addon.FILES:
        current[name]=addon.patch_member(name,originals[name])
    option_inputs={name:current[name] for name in option.NATIVE_FILES}
    option_outputs=option.patch_sources(option_inputs)
    current.update(option_outputs)
    toast=silent.NATIVE_FILE
    current[toast]=silent.patch_toast_cpp(originals[toast])

    modified={p for p in paths if current[p]!=originals[p]}
    if modified!=NATIVE_ALLOWLIST:raise RuntimeError("Original matched eight native patches not all applied")
    if b"RunScript(script.infinity.uirepair,option-b," not in current["xbmc/guilib/GUIBaseContainer.cpp"]:
        raise RuntimeError("Top release Option B hold command missing")
    if current["xbmc/input/InputManager.cpp"].count(b"for (const int railID : {9200, 8820, 8720, 19601})")!=1:
        raise RuntimeError("Original four Rails hold paths were overwritten")
    if b"GROUP6_SILENT_MODE_V1" not in current[toast]:
        raise RuntimeError("Isolated passive KaiToast route missing")
    if b"Disable add-on?" not in current["xbmc/addons/gui/GUIDialogAddonInfo.cpp"]:
        raise RuntimeError("Browser-scoped native Disable safeguard missing")
    for forbidden in ("xbmc/platform/android/activity/","xbmc/interfaces/python/",
                      "xbmc/windowing/","xbmc/cores/"):
        if any(name.startswith(forbidden) for name in modified):
            raise RuntimeError("Protected playback, Cobra or shutdown source changed")

    delta_path=checkpoint/"FOUR-REPAIR-INPUT-DELTA.json"
    old_map_path=checkpoint/"LOCKED-2103384-SOURCE-MAP.json"
    if not delta_path.is_file() or not old_map_path.is_file():
        raise RuntimeError("Missing previously verified 2103384/2103385 native source ledgers")
    delta=read(delta_path)
    baseline=read(old_map_path)
    if len(baseline)!=9404 or not delta.get("all_other_sources_byte_identical"):
        raise RuntimeError("Unrecognised original compiled native source provenance")
    for name in paths:
        if sha(originals[name])!=delta["after"].get(name,baseline.get(name)):
            raise RuntimeError("Source diverges from approved reconstructed 2103385: "+name)

    # Stage only AFTER the full eight-member preimage and after-byte checks.
    # This is an ephemeral CI working tree, not the user's original GitHub source.
    for name in paths:
        (native_root/name).write_bytes(current[name])
    after_hashes={name:sha(current[name]) for name in paths}
    delta["after"].update(after_hashes)
    delta["changed"]=sorted(set(delta.get("changed",()))|modified)
    delta["source_commit"]=os.environ.get("GITHUB_SHA","")
    if len(delta["source_commit"])!=40:
        raise RuntimeError("Current exact source commit not set")
    delta["group7_extra_native_delta"]=sorted(modified)
    delta["group7_original_four_addon_rails_preserved"]=True
    delta["group7_cobra_and_shutdown_files_untouched"]=True
    delta["group7_source_delta_proven_but_android_not_yet_compiled"]=True
    save(delta_path,delta)

    # The original native producer also validates its own manifest. Never
    # disable those checks; update only the permitted eight SHA entries.
    import importlib.util
    driver=ROOT/"repairs/four-repair-20261018/native_ci.py"
    spec=importlib.util.spec_from_file_location("g7_exact_parent_ci",driver)
    nativeci=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=nativeci
    spec.loader.exec_module(nativeci)
    ancestor=nativeci.parent.parent.parent.parent.parent.parent.parent
    manifest_path=ancestor.native_manifest(ancestor.stable())
    for proof_path in (manifest_path,checkpoint/"FINAL-SHUTDOWN-SOURCE-PRESERVATION.json"):
        proof=read(proof_path)
        if len(proof["after"])<4500:
            raise RuntimeError("Native compiler source manifest incomplete")
        for name in paths:
            if proof["after"].get(name)!=sha(originals[name]):
                raise RuntimeError("Unmatched native compiler source manifest "+name)
        proof["after"].update(after_hashes)
        proof["changed"]=sorted(set(proof.get("changed",()))|modified)
        save(proof_path,proof)

    snapshot=nativeci.digests()
    expected=dict(baseline,**delta["after"])
    if snapshot!=expected:
        bad=sorted(name for name in expected.keys()|snapshot.keys()
                   if expected.get(name)!=snapshot.get(name))
        raise RuntimeError("Unexpected source delta after native patch: "+repr(bad[:20]))
    proof=dict(
        base="RECONSTRUCTED_2103384_PLUS_APPROVED_2103385_UI",
        original_files=9404,
        additional_modified_native_sources=sorted(modified),
        before={n:sha(originals[n]) for n in paths},
        after=after_hashes,
        final_source_map_entries=len(snapshot),
        current_commit=os.environ["GITHUB_SHA"],
        prior_2103390_installed_engine_sha256="6e82e18868345ce919714364466e6473b15ed00abb68f6d09eebd7f5ef33f3f8",
        native_source_stage_green=True,
        native_compilation_finished=False,
        android_physical_fold_pass=False,
        group5_sigsegv_139_root_cause_fixed=False,
        original_cobra_addon_rail_ids_preserved=[9200,8820,8720,19601],
        new_top_release_ids=[8101,8102],
        notification_gate="Skin.HasSetting(Infinity.SilentMode)",
    )
    save(checkpoint/"GROUP7-NATIVE-SOURCE-ALLOWLIST.json",proof)
    return proof


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--native-root",type=Path,default=ROOT/"kodi")
    p.add_argument("--checkpoint",type=Path,default=ROOT/"checkpoint-build")
    a=p.parse_args()
    print(json.dumps(integrate(a.native_root,a.checkpoint),indent=2))
