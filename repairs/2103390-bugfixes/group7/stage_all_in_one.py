#!/usr/bin/env python3
"""Infinity 2103391: exact all-in-one SOURCE allowlist from signed 2103390.

Never edits the original APK, installed user data or developer's baselines.
Compiles no Kodi binaries and signs no APK. Final native packaging is separate.

Group #1 task #19 has NO FIX and MUST REMAIN LABELED DEFERRED. Group #5
only corrects stale crash-recorder native identity; SIGSEGV/139 unresolved.
No extra features beyond the approved groups, per user's final feature freeze.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
from xml.etree import ElementTree as ET
from zipfile import ZipFile

HERE=Path(__file__).resolve().parent
FAMILY=HERE.parent
for group in ("group1","group2","group3","group4","group5","group6"):
    sys.path.insert(0,str(FAMILY/group))

import continue_choice_patch as choice
import continue_horizontal_touch_patch as horizontal
import tv_episode_route_patch as episode
import movie_identity_patch as movie
import cc_preimage_contract_patch as cc
import clock_orb_patch as orb
import addon_browser_group2_patch as browser
import runtime_option_b_patch as option
import player_glass_patch as player
import silent_mode_patch as silent
import final_native_identity_patch as nativeidentity
import stage_option_b as option_stage

PARENT_SHA256="778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb"
ORIGINAL_COUNT=7430
EXPECTED_GROUP_COUNTS={"01":29,"02":42,"04":41,"06":13}
EXPECTED_ORIGINAL_CHANGED=sum(EXPECTED_GROUP_COUNTS.values()) # 125
EXPECTED_NEW_FILES=2
CC_PATH="assets/addons/script.infinity.commandcenter/"
AD="assets/addons/"
ENGINE="lib/arm64-v8a/libkodi.so"
RECORDER="lib/arm64-v8a/libinfinitycrash.so"
APK_VERSION=2103391

class ScopeError(ValueError):pass

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def refuse_if(cond,why):
    if cond:raise ScopeError(why)

def _insert(result, originals, group, path, value):
    refuse_if(path not in originals,"Unapproved original target "+path)
    refuse_if(path in result,"Cross-group overwrite collision on "+path)
    before=originals[path]
    refuse_if(value==before,"Expected source delta is absent on "+path)
    result[path]=(group,value)


def staged_sources(parent:Path) -> tuple[dict[str,tuple[str,bytes]],dict[str,bytes],dict]:
    parent=Path(parent)
    refuse_if(sha(parent.read_bytes())!=PARENT_SHA256,"Unexpected original signed 2103390")
    updates:dict[str,tuple[str,bytes]]={}
    with ZipFile(parent) as z:
        names=z.namelist()
        refuse_if(len(names)!=ORIGINAL_COUNT or len(set(names))!=ORIGINAL_COUNT,
                  "Signed original APK inventory differs")
        required=set(names)
        originals={name:z.read(name) for name in names
                   if (name.startswith("assets/addons/") and
                       (name.endswith("/Home.xml") or
                        name.endswith("/Includes_InfinityHomeUnified.xml") or
                        name.endswith("/CONTROLLER-PREIMAGES.json") or
                        name.endswith("/plugin.py") or
                        name.endswith("/resume_hub.py") or
                        name==choice.RUNTIME))}
        plugin=z.read(CC_PATH+"plugin.py")
        hub=z.read(CC_PATH+"resume_hub.py")
        # Group1 source-staged, task19 deliberately deferred and NOT patched.
        homes=[name for name in names if choice.home_type(name)]
        refuse_if(len(homes)!=14,"14 original Home variants required")
        for name in homes:
            original=z.read(name)
            updated=choice.patch_home(name,original)
            if name==horizontal.TARGET:
                # Original-only preimage check must run before combining two
                # independent modifications of the SAME protected Home file.
                verified=horizontal.patch_bytes(original)
                refuse_if(verified!=original.replace(
                    horizontal.ORIGINAL_LAYOUT,horizontal.FIXED_LAYOUT,4),
                    "Independent original Fold geometry proof changed")
                refuse_if(updated.count(horizontal.ORIGINAL_LAYOUT)!=4,
                          "Grouped Home popup changed horizontal layout")
                updated=updated.replace(horizontal.ORIGINAL_LAYOUT,
                                        horizontal.FIXED_LAYOUT,4)
            _insert(updates, {name:original},"01",name,updated)
        _insert(updates,{choice.RUNTIME:z.read(choice.RUNTIME)},"01",choice.RUNTIME,
                choice.patch_runtime(z.read(choice.RUNTIME)))
        for name,p in (("plugin.py",episode.patch_bytes),
                       ("resume_hub.py",movie.patch_bytes)):
            target=CC_PATH+name
            _insert(updates,{target:z.read(target)},"01",target,p(z.read(target)))
        for consumer in cc.CONSUMERS:
            target=AD+consumer+"/"+cc.CONTRACT_NAME
            before=z.read(target)
            _insert(updates,{target:before},"01",target,
                    cc.updated_contract(before,plugin,hub))
        for name in names:
            rel=name[len(AD):] if name.startswith(AD) else ""
            if orb.family(rel):
                original=z.read(name)
                _insert(updates,{name:original},"01",name,orb.modify(rel,original))

        # Group2 three browser XML resources across each of 14 layouts.
        b2=browser.candidate_map(parent)
        refuse_if(len(b2)!=42,"Group2 exact skin count")
        for name,data in b2.items():
            _insert(updates,{name:z.read(name)},"02",name,data)

        # Group3 shares Group1's runtime: exact two authorised dispatches
        # must BOTH survive (the originals and both new actions).
        before_combined=updates[choice.RUNTIME][1]
        combined=option.patch_runtime(before_combined)
        refuse_if(combined.count(b"elif action == 'home-choice':")!=1 or
                  combined.count(b"elif action == 'option-b':")!=1,
                  "Group1+3 runtime action composition failed")
        updates[choice.RUNTIME]=("01+03",combined)
        additions={}
        for name,source_name in option_stage.NEW_FILES.items():
            refuse_if(name in required or name in additions,
                      "Group3 additive file collides with signed baseline")
            additions[name]=(FAMILY/"group3"/source_name).read_bytes()
        refuse_if(set(additions)!=set(option_stage.NEW_FILES),
                  "Unapproved added first-party addon member")

        # Group4 glass menus: exact 41 original Infinity skin resources.
        b4=player.proposed(parent)
        refuse_if(len(b4)!=41,"Group4 exact skin count")
        for name,data in b4.items():
            _insert(updates,{name:z.read(name)},"04",name,data)

        # Group6 ONE existing System Hub Silent Mode toggle (13 XML variants).
        b6=silent.skin_inventory(parent)
        refuse_if(len(b6)!=13,"Group6 exact System Hub count")
        for name,data in b6.items():
            _insert(updates,{name:z.read(name)},"06",name,data)

        counts={group:sum(1 for tag,_ in updates.values()
                      if tag==group or (group=="01" and tag=="01+03"))
                for group in EXPECTED_GROUP_COUNTS}
        refuse_if(counts!=EXPECTED_GROUP_COUNTS,"Group source patch counts "+str(counts))
        refuse_if(len(updates)!=EXPECTED_ORIGINAL_CHANGED,
                  "Cross-group approved APK change count")
        refuse_if(len(additions)!=EXPECTED_NEW_FILES,
                  "Unexpected number of Option B additions")
        for name,(group,after) in updates.items():
            refuse_if("cobra" in name.lower() or name.startswith(("lib/","assets/system/"))
                      or name.startswith("assets/addons/plugin."),
                      "Unapproved original member changed: "+name)
            refuse_if(not isinstance(after,bytes) or not after,
                      "Unusable target bytes: "+name)
            if name.endswith(".xml") and name not in ("AndroidManifest.xml",):
                ET.fromstring(after)
            if name.endswith(".py"):compile(after,name,"exec")
        for name,body in additions.items():
            refuse_if("cobra" in name.lower() or not name.startswith(
                AD+"script.infinity.uirepair/"),"Unapproved added member")
            if name.endswith(".py"):compile(body,name,"exec")
            if name.endswith(".xml"):ET.fromstring(body)

        ledger={
            "source_parent_sha256":PARENT_SHA256,
            "original_members":ORIGINAL_COUNT,
            "approved_groups_source_staged":["01","02","03","04","05","06"],
            "source_modified_original_members":len(updates),
            "source_untouched_original_members":ORIGINAL_COUNT-len(updates),
            "source_added_first_party_members":len(additions),
            "per_group_original_counts":counts,
            "task19_movies_tv_reload":"DEFERRED_UNFIXED",
            "group5_sigsegv_139":"ROOT_CAUSE_UNPROVEN_NOT_FIXED",
            "new_features_after_this_release":"FREEZE_BUGFIXES_ONLY",
            "requires_source_matched_native_compile":True,
            "compiled_android_engine_in_this_step":False,
            "signed_apk_in_this_step":False,
            "physical_fold_verified":False,
            "changes":[
              {"path":name,"owner":group,
               "original_sha256":sha(z.read(name)),
               "staged_sha256":sha(data)}
              for name,(group,data) in sorted(updates.items())
            ],
            "added":[{"path":name,"sha256":sha(body)}
                     for name,body in sorted(additions.items())]
        }
        return updates,additions,ledger


def export_stage(parent:Path,out:Path)->dict:
    out=Path(out).resolve()
    refuse_if(out==Path(parent).resolve().parent or
              Path(parent).resolve().is_relative_to(out),
              "Never write staging over original signed APK")
    edits,extras,ledger=staged_sources(parent)
    for name,data in ((n,v) for n,(_,v) in edits.items()):
        path=out/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(data)
    for name,body in extras.items():
        path=out/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(body)
    (out/"GROUP7-SOURCE-SCOPE.json").write_text(json.dumps(ledger,indent=2)+"\n")
    return ledger

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("original",type=Path)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    info=export_stage(args.original,args.output) if args.output else staged_sources(args.original)[2]
    print(json.dumps({k:v for k,v in info.items() if k not in ("changes","added")},indent=2))
