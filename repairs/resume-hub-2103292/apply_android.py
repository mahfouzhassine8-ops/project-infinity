#!/usr/bin/env python3
"""2103292 package-only Android delta over locked 2103291.

No native source is compiled or changed. The Android shell only installs the approved
Command Center Resume Hub files from one checksummed APK asset. Command Center performs the
guarded 1.0.5.181 -> 1.0.5.182 skin transaction on first start.
"""
from __future__ import annotations
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil

VC = 2103292
REL = "1.0.9-Resume-Hub-2-RC1"
PARENT_SOURCE = "9205bf2d508194102667e3048b0bb59e6c08fe1e"
GRADLE = Path("tools/android/packaging/xbmc/build.gradle.in")
MAIN = Path("tools/android/packaging/xbmc/src/Main.java.in")
INSTALL = Path("cmake/scripts/android/Install.cmake")
JAVA = Path("tools/android/packaging/xbmc/src/InfinityResumeHubInstaller.java.in")

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"{label}: expected one anchor, got {n}")
    return text.replace(old, new, 1)

def regex_once(text: str, pattern: str, replacement: str, label: str) -> str:
    out, n = re.subn(pattern, replacement, text, count=1)
    if n != 1:
        raise RuntimeError(f"{label}: expected one regex anchor, got {n}")
    return out

def apply(root: Path, controller_sha: str, parent_apk_sha: str, native_sha: str, proof: Path) -> None:
    shell = root / "shell-kodi"
    template = root / "repairs/resume-hub-2103292/InfinityResumeHubInstaller.java.in"
    java = template.read_text()
    if not re.fullmatch(r"[0-9a-f]{64}", controller_sha):
        raise RuntimeError("invalid controller SHA")
    java = java.replace("@CONTROLLER_ASSET_SHA256@", controller_sha)
    (shell / JAVA).write_text(java, encoding="utf-8")

    p = shell / MAIN
    text = p.read_text()
    text = once(
        text,
        "    InfinityExtendedBackgroundService.sync(this);\n",
        "    InfinityExtendedBackgroundService.sync(this);\n    InfinityResumeHubInstaller.apply(this);\n",
        "Main Resume Hub install hook",
    )
    p.write_text(text, encoding="utf-8")

    p = shell / INSTALL
    text = p.read_text()
    text = once(
        text,
        "                  src/InfinityExtendedBackgroundService.java\n",
        "                  src/InfinityExtendedBackgroundService.java\n                  src/InfinityResumeHubInstaller.java\n",
        "Install.cmake Resume Hub source",
    )
    p.write_text(text, encoding="utf-8")

    p = shell / GRADLE
    text = p.read_text()
    text = once(text, "versionCode 2103291", f"versionCode {VC}", "version code")
    text = once(
        text,
        'versionName "1.0.9-InPlace-Responsive-Reflow-RC1"',
        f'versionName "{REL}"',
        "version name",
    )
    p.write_text(text, encoding="utf-8")

    p = root / "scripts/infinity_background_resume.py"
    text = p.read_text()
    text = once(text, "VERSION_CODE = 2103291", f"VERSION_CODE = {VC}", "packager version")
    text = once(
        text,
        "RELEASE = '1.0.9-InPlace-Responsive-Reflow-RC1'",
        f"RELEASE = '{REL}'",
        "packager release",
    )
    text = once(
        text,
        "BASE_COMMIT = '9888c81c2fd99f50212855aa8fb68149950b8f80'",
        f"BASE_COMMIT = '{PARENT_SOURCE}'",
        "packager parent source",
    )
    text = regex_once(
        text,
        r"BASE_APK_SHA256 = '[0-9a-f]{64}'",
        f"BASE_APK_SHA256 = '{parent_apk_sha}'",
        "parent APK hash",
    )
    text = regex_once(
        text,
        r"BASE_ENGINE_SHA256 = '[0-9a-f]{64}'",
        f"BASE_ENGINE_SHA256 = '{native_sha}'",
        "native hash",
    )
    p.write_text(text, encoding="utf-8")

    p = root / "scripts/package_background_resume.py"
    text = p.read_text()
    text = once(
        text,
        "Infinity-2103291-InPlace-Responsive-Reflow-RC1-unsigned.apk",
        "Infinity-2103292-Resume-Hub-2-RC1-unsigned.apk",
        "unsigned filename",
    )
    text = once(
        text,
        "Infinity-2103291-InPlace-Responsive-Reflow-RC1.apk",
        "Infinity-2103292-Resume-Hub-2-RC1.apk",
        "final filename",
    )
    text = text.replace(
        "ROOT/'repairs/inplace-reflow-2103291/DEVICE-TEST.md'",
        "ROOT/'repairs/resume-hub-2103292/DEVICE-TEST.md'",
    )
    p.write_text(text, encoding="utf-8")

    receipt = root / "engine/background-resume-source.json"
    data = json.loads(receipt.read_text())
    data.update(
        base_source_commit=PARENT_SOURCE,
        base_apk_sha256=parent_apk_sha,
        native_engine_sha256=native_sha,
        version_code=VC,
        release=REL,
        candidate_locked=False,
        physical_device_verified=False,
        native_engine_recompiled=False,
        resume_hub_api="2.0",
        resume_hub_controller="0.3.5.19",
        resume_hub_skin="1.0.5.182",
        companion_install="checksummed-apk-asset",
        provider_data_modified=False,
        accounts_modified=False,
    )
    for name in (GRADLE, MAIN, INSTALL, JAVA):
        q = shell / name
        data.setdefault("files", {}).setdefault(str(name), {})["after"] = sha(q)
    receipt.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")

    result = {
        "schema": 1,
        "version_code": VC,
        "version_name": REL,
        "parent_source": PARENT_SOURCE,
        "parent_apk_sha256": parent_apk_sha,
        "native_engine_sha256": native_sha,
        "controller_asset_sha256": controller_sha,
        "native_recompiled": False,
        "native_changed": False,
        "android_installer_added": True,
        "controller_target": "0.3.5.19",
        "skin_target": "1.0.5.182",
        "trakt_preserved": True,
        "providers_modified": False,
        "accounts_modified": False,
        "files": {str(x): sha(shell / x) for x in (GRADLE, MAIN, INSTALL, JAVA)},
    }
    proof.parent.mkdir(parents=True, exist_ok=True)
    proof.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("PASS: 2103292 Android-only Resume Hub installer applied")

def verify(root: Path, controller_sha: str) -> None:
    shell = root / "shell-kodi"
    blob = "\n".join((shell / p).read_text() for p in (GRADLE, MAIN, INSTALL, JAVA))
    for token in (
        "versionCode 2103292",
        "1.0.9-Resume-Hub-2-RC1",
        "InfinityResumeHubInstaller.apply(this)",
        "src/InfinityResumeHubInstaller.java",
        "resume-hub-controller.zip",
        controller_sha,
        "0.3.5.19",
        "1.0.5.182",
    ):
        if token not in blob:
            raise RuntimeError("missing 2103292 shell contract: " + token)
    if "versionCode 2103291" in (shell / GRADLE).read_text():
        raise RuntimeError("old version code remains")
    print("PASS: 2103292 Android-only Resume Hub shell verified")

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("apply", "verify"))
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--controller-sha", required=True)
    ap.add_argument("--parent-apk-sha")
    ap.add_argument("--native-sha")
    ap.add_argument("--proof", type=Path)
    a = ap.parse_args()
    root = a.root.resolve()
    if a.mode == "apply":
        if not a.parent_apk_sha or not a.native_sha or not a.proof:
            ap.error("apply requires parent/native/proof")
        apply(root, a.controller_sha, a.parent_apk_sha, a.native_sha, a.proof.resolve())
    else:
        verify(root, a.controller_sha)

if __name__ == "__main__":
    main()
