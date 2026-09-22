#!/usr/bin/env python3
"""Build 2103209 over the exact successful 2103208 APK with only a rebuilt libkodi.so.

The native delta is Kodi upstream commit ddb60bd932b929724a9b0d2226043dc54d0d1912 layered on
top of the already-shipped PR #27320 backport. Android/Cobra source is taken byte-for-byte from
the exact 2103208 generated-source archive, except versionCode/versionName.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path

BASE_RUN = 35676573761
BASE_SOURCE_COMMIT = "a876bb6fd698635b55805f56ff5484cbb622736d"
BASE_APK_SHA = "9143271bb241290467f68aa922a0cf441ab2621575091857706ef97e1e46da2d"
BASE_ENGINE_SHA = "e230a498a716ce0b82acedfce494fc521457af646c2f504965b247dcb5ee9281"
BASE_SOURCE_ZIP_SHA = "ca3995f542412e2cb91809c21f61fc8361bedab2fd0f463b0fe2ed057c1d949c"
BASE_ACCEPTANCE_SHA = "6e5cd284eac64bac1bf66d1867220381ab7b292507b85253fd02c25575d3ef4a"
CERT = "d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7"
OLD = "1.0.9-Cobra-Integration-Polish-RC1"
NEW = "1.0.9-Cobra-Python311-GIL-Stability-RC1"
VERSION = 2103209
LIB = "lib/arm64-v8a/libkodi.so"
FOLLOWUP = "ddb60bd932b929724a9b0d2226043dc54d0d1912"
PRIMARY = "0186f895271d4ce7d240b4e9f40da03b4833539d"


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)


def safe_extract(archive: zipfile.ZipFile, target: Path) -> None:
    root = target.resolve()
    for info in archive.infolist():
        dest = (target / info.filename).resolve()
        require(dest == root or root in dest.parents, "Unsafe source archive member: " + info.filename)
    archive.extractall(target)


def exact_base(base_dir: Path) -> tuple[Path, Path, Path, dict]:
    apk = base_dir / ("Infinity-" + OLD + ".apk")
    source_zip = base_dir / "Cobra-2103208-Generated-Android-Source.zip"
    acceptance = base_dir / "ACCEPTANCE.json"
    receipt = base_dir / "background-resume-source.json"
    for path in (apk, source_zip, acceptance, receipt):
        require(path.is_file(), "Missing exact 2103208 artifact member: " + str(path))
    require(sha(apk) == BASE_APK_SHA, "Wrong 2103208 APK bytes")
    require(sha(source_zip) == BASE_SOURCE_ZIP_SHA, "Wrong 2103208 generated source archive")
    require(sha(acceptance) == BASE_ACCEPTANCE_SHA, "Wrong 2103208 acceptance record")
    accepted = json.loads(acceptance.read_text())
    require(accepted.get("build") == 2103208, "Wrong parent build")
    require(accepted.get("candidate_tests") == 740 and accepted.get("candidate_suites") == 77,
            "Exact 2103208 acceptance inventory did not pass")
    return apk, source_zip, receipt, accepted


def extract_shell(source_zip: Path, shell: Path) -> None:
    require(not shell.exists(), "Shell output already exists")
    shell.mkdir(parents=True)
    with zipfile.ZipFile(source_zip) as archive:
        require(len(archive.namelist()) == 226, "2103208 source inventory drift")
        require(not archive.testzip(), "2103208 generated source CRC failure")
        safe_extract(archive, shell)
    gradle = shell / "tools/android/packaging/xbmc/build.gradle.in"
    text = gradle.read_text()
    require(text.count("versionCode 2103208") == 1, "2103208 versionCode source drift")
    require(text.count('versionName "' + OLD + '"') == 1, "2103208 versionName source drift")
    gradle.write_text(text.replace("versionCode 2103208", f"versionCode {VERSION}", 1)
                      .replace('versionName "' + OLD + '"', 'versionName "' + NEW + '"', 1))


def controlled_base(base_apk: Path, native_apk: Path, output: Path) -> tuple[str, str]:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(base_apk) as old, zipfile.ZipFile(native_apk) as native:
        require(LIB in native.namelist(), "Rebuilt engine APK has no libkodi.so")
        before = old.read(LIB)
        after = native.read(LIB)
        require(sha_bytes(before) == BASE_ENGINE_SHA, "2103208 native engine identity drift")
        require(after != before, "Python 3.11 GIL repair did not change libkodi.so")
        with zipfile.ZipFile(output, "w") as new:
            for info in old.infolist():
                new.writestr(info, after if info.filename == LIB else old.read(info.filename))
    with zipfile.ZipFile(base_apk) as old, zipfile.ZipFile(output) as new:
        require(set(old.namelist()) == set(new.namelist()), "Controlled-base inventory changed")
        changed = [name for name in old.namelist() if old.read(name) != new.read(name)]
        require(changed == [LIB], "Controlled base changed more than libkodi.so: " + repr(changed))
    return sha_bytes(after), sha(output)


def patch_runtime_and_packager(controlled_sha: str, engine_sha: str) -> None:
    runtime = Path("scripts/infinity_background_resume.py")
    text = runtime.read_text()
    text = re.sub(r"VERSION_CODE = \d+", f"VERSION_CODE = {VERSION}", text, count=1)
    text = re.sub(r"RELEASE = '[^']+'", "RELEASE = '" + NEW + "'", text, count=1)
    text = re.sub(r"BASE_APK_SHA256 = '[0-9a-f]{64}'", "BASE_APK_SHA256 = '" + controlled_sha + "'", text, count=1)
    text = re.sub(r"BASE_ENGINE_SHA256 = '[0-9a-f]{64}'", "BASE_ENGINE_SHA256 = '" + engine_sha + "'", text, count=1)
    runtime.write_text(text)

    packager = Path("scripts/package_background_resume.py")
    ptext = packager.read_text()
    legacy_name = "Infinity-1.0.9-Cobra-Background-Resume-RC1"
    require(ptext.count(legacy_name) >= 2, "Packager output identity anchor drift")
    ptext = ptext.replace(legacy_name, "Infinity-" + NEW)
    require("'base_run':35044752997" in ptext, "Packager base-run anchor drift")
    ptext = ptext.replace("'base_run':35044752997", f"'base_run':{BASE_RUN}", 1)
    start = ptext.index("def verify_manifest_pair(original: str, compiled: str):")
    end = ptext.index("\n\ndef merge(", start)
    verifier = '''def verify_manifest_pair(original: str, compiled: str):
    old,new=manifest_tree(original),manifest_tree(compiled)
    for tree in (old,new):
        for key in ('android:versionCode','android:versionName'):
            tree['attrs'].pop(key,None)
    require(old==new,'Compiled manifest drift from exact 2103208 base outside version identity')
'''
    ptext = ptext[:start] + verifier + ptext[end:]
    packager.write_text(ptext)


def prepare(base_dir: Path, native_apk: Path, shell: Path, outdir: Path) -> None:
    base_apk, source_zip, parent_receipt, accepted = exact_base(base_dir)
    extract_shell(source_zip, shell)
    controlled = outdir / "Infinity-2103208-Python311-GIL-Patched-Base.apk"
    new_engine, controlled_sha = controlled_base(base_apk, native_apk, controlled)
    patch_runtime_and_packager(controlled_sha, new_engine)

    receipt = json.loads(parent_receipt.read_text())
    require(receipt.get("version_code") == 2103208 and receipt.get("version_name") == OLD,
            "Wrong 2103208 source receipt")
    gradle_rel = "tools/android/packaging/xbmc/build.gradle.in"
    require(gradle_rel in receipt.get("files", {}), "Gradle source missing from receipt")
    receipt["files"][gradle_rel]["after"] = sha(shell / gradle_rel)
    receipt.update(
        version_code=VERSION,
        version_name=NEW,
        source_parent=2103208,
        source_parent_commit=BASE_SOURCE_COMMIT,
        candidate_locked=False,
        physical_device_verified=False,
        runtime_device_tested=False,
        native_engine_rebuilt=True,
        previous_native_engine_sha256=BASE_ENGINE_SHA,
        native_engine_sha256=new_engine,
        pythoninvoker_upstream_primary=PRIMARY,
        pythoninvoker_python311_gil_followup=FOLLOWUP,
        pythoninvoker_python311_gil_fix=True,
    )
    Path("engine").mkdir(exist_ok=True)
    Path("engine/background-resume-source.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")

    for name, row in receipt["files"].items():
        require(sha(shell / name) == row["after"], "Final 2103209 shell receipt drift: " + name)

    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "promotion.json").write_text(json.dumps({
        "build": VERSION,
        "parent_build": 2103208,
        "parent_run": BASE_RUN,
        "parent_apk_sha256": BASE_APK_SHA,
        "parent_source_commit": BASE_SOURCE_COMMIT,
        "parent_tests_verified": accepted["candidate_tests"],
        "parent_suites_verified": accepted["candidate_suites"],
        "previous_native_engine_sha256": BASE_ENGINE_SHA,
        "native_engine_sha256": new_engine,
        "controlled_base_sha256": controlled_sha,
        "only_parent_apk_entry_changed_before_shell_compile": LIB,
        "upstream_primary": PRIMARY,
        "upstream_followup": FOLLOWUP,
        "physical_device_verified": False,
    }, indent=2) + "\n")
    print("PASS: exact 2103208 presentation/features promoted with only rebuilt libkodi.so")


def verify(final: Path, base_dir: Path, native_apk: Path, audit: Path) -> None:
    base_apk, _, _, accepted = exact_base(base_dir)
    require(final.is_file(), "2103209 final APK missing")
    report = json.loads(audit.read_text())
    require(report.get("version_code") == VERSION and report.get("version_name") == NEW,
            "Final 2103209 identity mismatch")
    require(report.get("signer_certificate_sha256") == CERT, "Permanent signer changed")
    require(report.get("apk_sha256") == sha(final), "Final APK hash receipt mismatch")

    with zipfile.ZipFile(base_apk) as old, zipfile.ZipFile(final) as new, zipfile.ZipFile(native_apk) as native:
        require(new.read(LIB) == native.read(LIB), "Final libkodi.so differs from rebuilt Python 3.11 engine")
        require(sha_bytes(old.read(LIB)) == BASE_ENGINE_SHA, "Parent engine identity drift")
        require(new.read(LIB) != old.read(LIB), "Final candidate still carries broken 2103208 engine")
        old_natives = {n for n in old.namelist() if n.startswith("lib/") and not n.endswith("/")}
        new_natives = {n for n in new.namelist() if n.startswith("lib/") and not n.endswith("/")}
        require(old_natives == new_natives, "Native inventory changed")
        for name in old_natives - {LIB}:
            require(new.read(name) == old.read(name), "Non-target native changed: " + name)
        protected = {n for n in old.namelist() if n.startswith(("assets/", "res/")) or n == "resources.arsc"}
        for name in protected:
            require(new.read(name) == old.read(name), "2103208 asset/resource changed: " + name)
        joined = b"".join(new.read(n) for n in new.namelist() if re.fullmatch(r"classes\d*\.dex", n))
        for token in (b"CobraQuickPeekSession", b"InfinityCobraFeatureRuntime", b"InfinitySystemMediaHook",
                      b"PLAY IN BACKGROUND", b"Ask every time"):
            require(token in joined, "2103208 contract lost: " + repr(token))

    badging = Path("signed209/badging.txt").read_text()
    require(f"versionCode='{VERSION}'" in badging and f"versionName='{NEW}'" in badging,
            "Badging identity mismatch")
    with zipfile.ZipFile(final) as archive:
        final_engine_sha = sha_bytes(archive.read(LIB))
    result = {
        "build": VERSION,
        "version_name": NEW,
        "apk_sha256": sha(final),
        "signer": CERT,
        "parent_build": 2103208,
        "parent_apk_sha256": BASE_APK_SHA,
        "parent_tests_verified_not_rerun": accepted["candidate_tests"],
        "parent_suites_verified_not_rerun": accepted["candidate_suites"],
        "native_engine_sha256": final_engine_sha,
        "pythoninvoker_upstream_primary": PRIMARY,
        "python311_gil_followup": FOLLOWUP,
        "only_native_target": LIB,
        "physical_device_verified": False,
    }
    Path("audit209/final-verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print("PASS: 2103209 keeps exact 2103208 feature/resource payload and replaces only target native engine")


def deliver() -> None:
    source_proof = json.loads(Path("engine/pythoninvoker-threadstate-v2-source.json").read_text())
    require(source_proof.get("upstream_followup") == FOLLOWUP, "Wrong Python 3.11 follow-up source proof")
    require(all(source_proof.get("checks", {}).values()), "Python 3.11 source proof failed")
    final = json.loads(Path("audit209/final-verification.json").read_text())
    acceptance = {
        "build": VERSION,
        "version_name": NEW,
        "parent_build": 2103208,
        "parent_run": BASE_RUN,
        "parent_apk_sha256": BASE_APK_SHA,
        "parent_android_tests_verified_not_rerun": 740,
        "parent_android_suites_verified_not_rerun": 77,
        "native_source_checks": len(source_proof["checks"]),
        "native_engine_rebuilt": True,
        "upstream_python311_gil_fix": FOLLOWUP,
        "apk_sha256": final["apk_sha256"],
        "candidate_locked": False,
        "physical_device_verified": False,
        "status": "TEST CANDIDATE - install over 2103208 and stress Python/add-on startup before promotion",
    }
    Path("signed209/ACCEPTANCE.json").write_text(json.dumps(acceptance, indent=2) + "\n")
    shutil.copy2("engine/pythoninvoker-threadstate-v2-source.json", "signed209/PYTHON311-GIL-NATIVE-REPAIR.json")
    shutil.copy2("audit209/final-verification.json", "signed209/2103209-verification.json")
    shutil.copy2("repairs/python311-gil-2103209/AUDIT.md", "signed209/AUDIT.md")
    print("PASS: 2103209 test candidate packaged; physical acceptance remains required")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("prepare")
    a.add_argument("--base-dir", type=Path, required=True)
    a.add_argument("--native-apk", type=Path, required=True)
    a.add_argument("--shell", type=Path, required=True)
    a.add_argument("--out", type=Path, required=True)
    a = sub.add_parser("verify")
    a.add_argument("--final", type=Path, required=True)
    a.add_argument("--base-dir", type=Path, required=True)
    a.add_argument("--native-apk", type=Path, required=True)
    a.add_argument("--audit", type=Path, required=True)
    sub.add_parser("deliver")
    args = parser.parse_args()
    if args.cmd == "prepare":
        prepare(args.base_dir, args.native_apk, args.shell, args.out)
    elif args.cmd == "verify":
        verify(args.final, args.base_dir, args.native_apk, args.audit)
    else:
        deliver()


if __name__ == "__main__":
    main()
