#!/usr/bin/env python3
"""Fail-closed signed-2103401 -> user-tested-2103402 runtime ownership repair.

This updates FOUR Android-only native source files, never a provider, watched
record, shutdown policy, or any Cobra source. Earlier source contracts are
preserved. New contracts verify every byte of exactly the installed CC .36.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from zipfile import ZipFile

ENGINE_FILES = {
    "xbmc/platform/android/activity/InfinityScriptCheckpointContracts.cpp":
        "f934bdfe39180e131f4e59c6f1320236d6daf9cfcf37d5fe604e8a16ed696633",
    "xbmc/guilib/GUIBaseContainer.cpp":
        "319735f89a61a54715fadab22487a561647d454e36255e2588d92d5005da1e1f",
    "xbmc/interfaces/legacy/WindowXML.cpp":
        "1723a5defae3ba6b643b100b4917553e6c572d10a11a71e9be006bb1d1d83057",
    "xbmc/platform/android/activity/InfinityAndroidCheckpoint.cpp":
        "87cc60d6512c98999c3479afaa0245eb95ad43991d1f93d802c01e27a98a58e7",
}
QA_CHANGED_CC = {
    "script.infinity.commandcenter/addon.xml":
        "1b0b2ae9da31cd4772463799d4a3d44d0fce0639ef514221d506f25d09efc10b",
    "script.infinity.commandcenter/information.py":
        "8cf3cfcab461d73d4e8bb625039d905478ffb52688f729252002b292ea87c429",
    "script.infinity.commandcenter/resources/skins/Default/1080i/InfinityInformation.xml":
        "b9059729493751dfc0be65801f73e41a06b604f3fdaf099963821b84f2b2e443",
    "script.infinity.commandcenter/service.py":
        "51fc63f6922885c8473277398e6f3569274eb42afe06be0148501d6ddc65bb23",
}
SOURCE_RE = re.compile(
    r'\{"(script\.infinity\.commandcenter/[^"]+)",\s*"([0-9a-f]{64})"\}'
)
CONTRACT_RE = re.compile(
    r'    \{"(script\.infinity\.commandcenter/(?:service|plugin|context)\.py)",'
    r'\s*"script\.infinity\.commandcenter",\s*"(command_center(?:_client)?)",'
    r'\s*\{(.*?)\n    \}\},\n', re.S,
)
CONTRACT_ANCHOR = '  };\n  return *contracts;\n}'
EXPECTED_QA_VERSION = "0.3.5.36"


def digest(value):
    return hashlib.sha256(value).hexdigest()


def once(old, new, data, name):
    if data.count(old) != 1 or old == new:
        raise ValueError("Native source anchor absent/nonunique: " + name)
    out = data.replace(old, new, 1)
    if out.replace(new, old, 1) != data:
        raise ValueError("Native source reverse-diff failed: " + name)
    return out


def inspect_contracts(text, baseline, candidate):
    """Identify the three *matching* original contracts and require 25 QA hashes."""
    groups = []
    with ZipFile(baseline) as old, ZipFile(candidate) as qa:
        for match in CONTRACT_RE.finditer(text):
            pins = SOURCE_RE.findall(match.group(3))
            if len(pins) != 25 or len({p for p, _ in pins}) != 25:
                continue
            if any(digest(old.read("assets/addons/" + p)) != h for p, h in pins):
                continue
            original_paths = {p for p, _ in pins}
            if not QA_CHANGED_CC.keys() <= original_paths:
                raise ValueError("Exact baseline contract does not include every QA file")
            for name, old_hash in pins:
                qa_hash = digest(qa.read("assets/addons/" + name))
                expected = QA_CHANGED_CC.get(name, old_hash)
                if qa_hash != expected:
                    raise ValueError("Unsigned or unexpected Command Center source: " + name)
            groups.append(match)
    required = [
        ("script.infinity.commandcenter/service.py", "command_center"),
        ("script.infinity.commandcenter/plugin.py", "command_center_client"),
        ("script.infinity.commandcenter/context.py", "command_center_client"),
    ]
    if len(groups) != 3 or [(m.group(1), m.group(2)) for m in groups] != required:
        raise ValueError("Expected three exact matching 25-file baseline contracts")
    return groups


def patch_contracts(raw, baseline, candidate):
    text = raw.decode("utf-8")
    groups = inspect_contracts(text, baseline, candidate)
    added = []
    for group in groups:
        entry = group.group()
        for name, new_digest in QA_CHANGED_CC.items():
            original = re.search(
                r'\{"' + re.escape(name) + r'",\s*"([0-9a-f]{64})"\}', entry)
            if not original:
                raise ValueError("Absent reviewed pin " + name)
            before = original.group(0)
            after = before.replace(original.group(1), new_digest)
            entry = once(before, after, entry, name)
        if entry == group.group():
            raise ValueError("Empty generated ownership contract")
        added.append(entry)
    marker = ''.join(added)
    out = once(CONTRACT_ANCHOR, marker + CONTRACT_ANCHOR, text,
               "append-only protected Command Center contracts")
    if out.count('"script.infinity.commandcenter", "command_center_client"') != text.count('"script.infinity.commandcenter", "command_center_client"') + 2:
        raise ValueError("Wrong new owner labels")
    if out.count('"script.infinity.commandcenter", "command_center"') != text.count('"script.infinity.commandcenter", "command_center"') + 1:
        raise ValueError("Wrong new resident owner labels")
    return out.encode("utf-8")


def patch_titles(raw):
    s = raw.decode("utf-8")
    old = 'addon->Version().asString() == "0.3.5.35");'
    new = ('addon->Version().asString() == "0.3.5.35" ||\n'
           '       addon->Version().asString() == "0.3.5.36");')
    return once(old, new, s, "home long-press original title menu").encode("utf-8")


def patch_popup(raw):
    s = raw.decode("utf-8")
    old = 'responsiveOwner->Version().asString() == "0.3.5.35")'
    new = ('(responsiveOwner->Version().asString() == "0.3.5.35" ||\n'
           '                 responsiveOwner->Version().asString() == "0.3.5.36"))')
    return once(old, new, s, "owned popup resize").encode("utf-8")


def patch_shutdown_owner(raw):
    s = raw.decode("utf-8")
    old = 'active["addon_version"].asString() != "0.3.5.35"))'
    new = ('active["addon_version"].asString() != "0.3.5.35" && '
           'active["addon_version"].asString() != "0.3.5.36"))')
    return once(old, new, s, "exact resident version in Essential-First admission").encode("utf-8")


PATCHERS = {
    "xbmc/platform/android/activity/InfinityScriptCheckpointContracts.cpp": patch_contracts,
    "xbmc/guilib/GUIBaseContainer.cpp": patch_titles,
    "xbmc/interfaces/legacy/WindowXML.cpp": patch_popup,
    "xbmc/platform/android/activity/InfinityAndroidCheckpoint.cpp": patch_shutdown_owner,
}


def stage(native_source_zip, original_map, baseline, qa, destination):
    with ZipFile(native_source_zip) as z:
        actual = {n.removeprefix("native/") for n in z.namelist()
                  if n.startswith("native/") and not n.endswith("/")}
        if set(ENGINE_FILES) - actual:
            raise ValueError("Native base source missing protected members")
        if len(actual) != 9407:
            raise ValueError("Expected complete 9,407 source inventory")
        proofs = json.loads(original_map.read_text())
        if len(proofs) != 9407:
            raise ValueError("Source hash-map completeness failure")
        result = {}
        for name, correct in ENGINE_FILES.items():
            original = z.read("native/" + name)
            if digest(original) != correct or proofs[name] != correct:
                raise ValueError("Source preimage mismatch: " + name)
            method = PATCHERS[name]
            updated = (method(original, baseline, qa)
                       if name.endswith("InfinityScriptCheckpointContracts.cpp")
                       else method(original))
            if updated == original:
                raise ValueError("No narrow modification detected: " + name)
            result[name] = {
                "baseline_sha256": correct,
                "corrected_sha256": digest(updated),
                "changed": True,
            }
            dest = destination / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(updated)
    if set(result) != set(ENGINE_FILES):
        raise ValueError("Native owner repair file boundary changed")
    (destination / "EXACT-NATIVE-OWNER-REPAIR.json").write_text(
        json.dumps({
            "parent_build": 40089463702, "qa_build": 40144024130,
            "source_file_count": 9407,
            "allowed_native_changes": result,
            "new_command_center_version": EXPECTED_QA_VERSION,
            "source_contracts": "25 files pinned, 3 additive exact owner contracts",
            "prior_contracts_removed": 0,
            "Cobra": "UNCHANGED",
            "existing_provider_resolver": "UNCHANGED",
            "TV_continue_data": "NOT MODIFIED",
            "Home_cache": "NOT MODIFIED",
            "Search_SIGBUS_cause": "UNRESOLVED",
            "Android17_fold_acceptance": "NOT_YET_TESTED"
        }, indent=2) + "\n"
    )
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True, type=Path)
    p.add_argument("--map", required=True, type=Path)
    p.add_argument("--baseline", required=True, type=Path)
    p.add_argument("--qa", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    print(json.dumps(stage(args.source, args.map, args.baseline, args.qa, args.out), indent=2))
