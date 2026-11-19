"""Stage the exact scoped Python bytes and unsigned module manifests for QA."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
PREFIX = "assets/addons/"
CC = "script.infinity.commandcenter"
MANIFEST = CC + "/INFINITY-MODULES.v1"
KEY_SHA256 = "bc883be4515d328935b1f3e28294bfc0fe0f2614083274db63b1d24d4da172e8"
EXPECTED = {PREFIX + CC + "/" + name for name in (
    "experience.py", "plugin.py", "saved_navigation.py", "infinity_modules/uirepair/runtime.py"
)}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def inventory(root):
    return {p.relative_to(root).as_posix(): sha(p.read_bytes())
            for p in root.rglob("*") if p.is_file()}


def stage(baseline, out, public_key):
    addons = baseline / PREFIX
    baseline_manifest = addons / MANIFEST
    sign = addons / (MANIFEST + ".sig")
    require(sha(public_key.read_bytes()) == KEY_SHA256, "Original module public key changed")
    subprocess.run(["openssl", "dgst", "-sha256", "-verify", str(public_key),
                    "-signature", str(sign), str(baseline_manifest)], check=True)
    old_lines = baseline_manifest.read_text(encoding="ascii").splitlines()
    require(old_lines[:3] == ["INFINITY-MODULES/1", "package\t0.3.5.84", "protocol\t1"],
            "Wrong 2103514 signed module generation")
    old_pins = {name: digest for _, digest, name in
                (row.split("\t") for row in old_lines if row.startswith("file\t"))}
    before = inventory(addons)
    require(before == {
        **old_pins, MANIFEST: sha(baseline_manifest.read_bytes()), MANIFEST + ".sig": sha(sign.read_bytes())
    }, "The 2103514 baseline module bytes and signed inventory disagree")
    scope = json.loads((HERE / "CONTINUE-SCOPE.json").read_bytes())
    patch = HERE / "continue-navigation.patch"
    require(scope["base_VERSION"] == 2103514 and set(scope["changed"]) == EXPECTED and
            sha(patch.read_bytes()) == scope["patch_sha256"], "Wrong Continue Playing member delta")
    require(all(before[path.removeprefix(PREFIX)] == pins["before_sha256"]
                for path, pins in scope["changed"].items()), "Reviewed source preimage differs")
    out.mkdir()
    report = {}
    for name, version in (("candidate", "0.3.5.85"), ("forward-recovery", "0.3.5.86")):
        root = out / name
        shutil.copytree(addons, root / PREFIX)
        if name == "candidate":
            subprocess.run(["patch", "--batch", "--forward", "--fuzz=0", "--no-backup-if-mismatch",
                            "-p1", "-i", str(patch)], cwd=root, check=True)
            for path, pins in scope["changed"].items():
                payload = (root / path).read_bytes()
                require(sha(payload) == pins["after_sha256"], "Wrong reviewed result: " + path)
                compile(payload, path, "exec")
        target_addons = root / PREFIX
        addon = target_addons / CC / "addon.xml"
        raw = addon.read_bytes()
        require(raw.count(b'version="0.3.5.84"') == 1, "Wrong controller install metadata")
        addon.write_bytes(raw.replace(b'version="0.3.5.84"', ('version="' + version + '"').encode("ascii"), 1))
        after = inventory(target_addons)
        changed_sources = {key for key in after if after[key] != before.get(key)}
        expected = {CC + "/addon.xml"}
        if name == "candidate":
            expected.update(path.removeprefix(PREFIX) for path in EXPECTED)
        require(set(before) == set(after) and changed_sources == expected, "Unexpected Python or resource changes")
        new_lines = ["package\t" + version if row.startswith("package\t") else row for row in old_lines]
        for index, row in enumerate(new_lines):
            if row.startswith("file\t"):
                _, _, path = row.split("\t")
                new_lines[index] = "file\t" + after[path] + "\t" + path
        manifest = target_addons / MANIFEST
        manifest.write_text("\n".join(new_lines) + "\n", encoding="ascii")
        # The original signature authenticated the baseline only. Remove its
        # staged copy so these changed bytes cannot masquerade as signed.
        (target_addons / (MANIFEST + ".sig")).unlink()
        after = inventory(target_addons)
        report[name] = dict(
            command_center_version=version, signed=False,
            manifest_sha256=after[MANIFEST],
            changes={path: {"before": before[path], "after": after[path]}
                     for path in sorted(changed_sources | {MANIFEST})},
            removed_signature=MANIFEST + ".sig",
            unchanged=len(before) - len(changed_sources) - 2)
    (out / "MODULE-PRESERVATION.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--baseline", type=Path, required=True)
    cli.add_argument("--public-key", type=Path, required=True)
    cli.add_argument("--out", type=Path, required=True)
    args = cli.parse_args()
    stage(args.baseline.resolve(), args.out.resolve(), args.public_key.resolve())
