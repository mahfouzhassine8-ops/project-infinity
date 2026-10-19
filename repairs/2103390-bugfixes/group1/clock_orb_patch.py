#!/usr/bin/env python3
"""Group #1/task 04 only: move the existing Infinity Home orb off the clock.

Fail closed unless every exact 2103390 skin-1.0.5.228 source member matches
its known original content hash. This does NOT edit user data, Cobra, clocks,
weather, menus, or other Home controls. It is a source-only staging tool;
permanently signed APK integration remains separately gated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

PREFIX = "skin.infinity.diggz/"
TARGET = "/Includes_InfinityHomeUnified.xml"
ORIGINAL_HASHES = {
    "16x9": "3f34302296ae3a3e389d0748aca43655ebed49cebbd1a898d9e67af7d137cb26",
    "fallback": "3f34302296ae3a3e389d0748aca43655ebed49cebbd1a898d9e67af7d137cb26",
    "responsive": "9a068bfbbfdcd56d51c1068d7f93806db165feb018b194a6d912d33debefa818",
    "unified": "acfc438ae58cf8f204f516fb4dfa3af23b4df5e7c09d20260836eadf2ac8140c",
}
BEFORE = (b'<include name="InfinityHomeStatusCluster">')
OLD = (b'<definition>\n      <control type="image">\n'
       b'        <left>$PARAM[timeleft]</left>\n'
       b'        <top>$PARAM[timetop]</top>')
NEW = (b'<definition>\n      <control type="image">\n'
       b'        <left>708</left>\n'
       b'        <top>$PARAM[timetop]</top>')


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def family(path: str) -> str:
    if not path.startswith(PREFIX) or not path.endswith(TARGET):
        return ""
    section = path[len(PREFIX):].split("/", 1)[0]
    return section if section in ORIGINAL_HASHES else ""


def modify(path: str, data: bytes) -> bytes:
    group = family(path)
    if not group or sha(data) != ORIGINAL_HASHES[group]:
        raise ValueError("Unexpected or modified original status-cluster source: " + path)
    if data.count(BEFORE) != 1 or data.count(OLD) != 1:
        raise ValueError("Ambiguous Home status orb anchor: " + path)
    changed = data.replace(OLD, NEW, 1)
    if changed.count(NEW) != 1 or changed.count(OLD) != 0:
        raise ValueError("Home orb-only replacement did not succeed: " + path)
    return changed


def patch_archive(source: Path, target: Path) -> dict:
    source, target = Path(source), Path(target)
    if source.resolve() == target.resolve():
        raise ValueError("Input must remain immutable; choose a different output path")
    with zipfile.ZipFile(source, "r") as zin:
        original = zin.infolist()
        matches = [x.filename for x in original if family(x.filename)]
        if len(matches) != 10 or len(set(matches)) != 10:
            raise ValueError("Expected exactly 10 Infinity Home status include variants")
        if not zin.read(PREFIX + "addon.xml").count(b'version="1.0.5.228"'):
            raise ValueError("Not the protected 1.0.5.228 source skin")
        # Verify all source hashes BEFORE writing any output.
        adjusted = {path: modify(path, zin.read(path)) for path in matches}
        changed = []
        target.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(target, "w") as zout:
            for info in original:
                before = zin.read(info.filename)
                after = adjusted.get(info.filename, before)
                if after != before:
                    changed.append({"path": info.filename, "before_sha256": sha(before),
                                    "after_sha256": sha(after)})
                zout.writestr(info, after)
    if len(changed) != 10:
        target.unlink(missing_ok=True)
        raise ValueError("Did not change exactly the 10 approved status include members")
    return {"source_members": len(original), "changed_members": changed,
            "unchanged_members": len(original) - len(changed),
            "source_archive_sha256": sha(source.read_bytes()),
            "candidate_archive_sha256": sha(target.read_bytes()),
            "status": "HOST_SOURCE_STAGING_ONLY_NOT_FOLD_APPROVED"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("candidate", type=Path)
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()
    result = patch_archive(args.source, args.candidate)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"changed_members": len(result["changed_members"]),
                      "untouched": result["unchanged_members"],
                      "status": result["status"]}))


if __name__ == "__main__":
    main()
