#!/usr/bin/env python3
"""Hash-protected runtime overlays over the exact recovered preservation parent.

Capture is a developer operation. Apply/verify are build gates; neither accepts
an unreviewed preimage or resets a source tree to upstream Kodi.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
GROUPS = ("native", "android", "commandcenter")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def snapshot(root):
    return {p.relative_to(root).as_posix(): sha(p.read_bytes())
            for p in sorted(root.rglob("*")) if p.is_file()
            and not any(x in (".git", "__pycache__", "tests") for x in p.relative_to(root).parts)
            and p.suffix != ".pyc"}


def checked_path(root, name):
    path = Path(name)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError("Unsafe manifest path: " + name)
    return root / path


def verify(root, expected):
    wrong = [name for name, digest in expected.items()
             if not checked_path(root, name).is_file()
             or sha(checked_path(root, name).read_bytes()) != digest]
    if wrong:
        raise ValueError("Source hash mismatch: " + repr(wrong[:20]))


def capture(group, parent, source, native_manifest=None):
    recovered = snapshot(parent)
    current = snapshot(source)
    missing = recovered.keys() - current.keys()
    if missing:
        raise ValueError("Runtime overlay may not remove preserved source: " + repr(sorted(missing)))
    before = (json.loads(native_manifest.read_text())["after"]
              if native_manifest else recovered)
    for name, digest in recovered.items():
        if before.get(name) != digest:
            raise ValueError("Recovered parent differs from compiled manifest: " + name)
    changes = {name: digest for name, digest in current.items() if before.get(name) != digest}
    after = dict(before, **changes)
    folder = HERE / "runtime" / group
    overlay = folder / "overlay"
    # Only replace this script's generated overlay; never touch caller sources.
    if overlay.exists():
        shutil.rmtree(overlay)
    for name in changes:
        target = checked_path(overlay, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(checked_path(source, name), target)
    manifest = {"schema": 1, "group": group, "parent": "2103334-native/2103335-shell/CC-0.3.5.19",
                "before": before, "after": after, "changed": sorted(changes),
                "added": sorted(current.keys() - before.keys()),
                "deleted": [], "device_accepted": False, "locked": False}
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"CAPTURE {group}: {len(changes)} enumerated source deltas, {len(before)} protected parent files")


def apply(group, source):
    folder = HERE / "runtime" / group
    manifest = json.loads((folder / "manifest.json").read_text())
    verify(source, manifest["before"])
    for name in manifest["added"]:
        if checked_path(source, name).exists():
            raise ValueError("Unexpected preexisting overlay path: " + name)
    # Validate the complete payload before the first source mutation.
    verify(folder / "overlay", {name: manifest["after"][name] for name in manifest["changed"]})
    for name in manifest["changed"]:
        target = checked_path(source, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(checked_path(folder / "overlay", name), target)
    verify(source, manifest["after"])
    print(f"PASS {group}: reviewed overlay applied; every protected source postimage verified")


def materialize_commandcenter(source):
    if source.exists():
        raise ValueError("Command Center materialization requires a new directory")
    folder = HERE / "runtime" / "commandcenter"
    manifest = json.loads((folder / "manifest.json").read_text())
    for name, digest in manifest["after"].items():
        origin = checked_path(folder / ("overlay" if name in manifest["changed"] else "unchanged"), name)
        if not origin.is_file() or sha(origin.read_bytes()) != digest:
            raise ValueError("Candidate Command Center input mismatch: " + name)
    for name in manifest["after"]:
        origin = checked_path(folder / ("overlay" if name in manifest["changed"] else "unchanged"), name)
        target = checked_path(source, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(origin, target)
    verify(source, manifest["after"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("capture", "apply", "verify", "materialize"))
    parser.add_argument("--group", choices=GROUPS, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--parent", type=Path)
    parser.add_argument("--native-parent-manifest", type=Path)
    args = parser.parse_args()
    if args.mode == "capture":
        if args.parent is None:
            parser.error("capture requires --parent")
        capture(args.group, args.parent, args.source, args.native_parent_manifest)
    elif args.mode == "apply":
        apply(args.group, args.source)
    elif args.mode == "materialize":
        if args.group != "commandcenter":
            parser.error("Only the exact captured Command Center source can be materialized")
        materialize_commandcenter(args.source)
    else:
        manifest = json.loads((HERE / "runtime" / args.group / "manifest.json").read_text())
        verify(args.source, manifest["after"])
        print("PASS: all reviewed source postimages preserved")


if __name__ == "__main__":
    main()
