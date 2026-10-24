#!/usr/bin/env python3
"""Layer an Infinity-owned Normal/Extended control bridge over Background Resume RC1.

Run *after* infinity_background_resume.py.  This modifies only the generated Android
presentation source/package metadata.  Kodi/libkodi.so is never rebuilt or patched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANDROID = Path("tools/android/packaging/xbmc")
LIVE = ANDROID / "src/InfinityLiveActivity.java.in"
CONTROL = ANDROID / "src/InfinityBackgroundControlActivity.java.in"
SERVICE = ANDROID / "src/InfinityExtendedBackgroundService.java.in"
MANIFEST = ANDROID / "AndroidManifest.xml.in"
GRADLE = ANDROID / "build.gradle.in"
INSTALL = Path("cmake/scripts/android/Install.cmake")
RC1 = "1.0.9-Cobra-Background-Resume-RC1"
RC2 = "1.0.9-Infinity-Background-Control-RC2"
RC1_CODE = "2103136"
RC2_CODE = "2103137"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"Unexpected {label} preimage: expected 1 occurrence, got {text.count(old)}")
    return text.replace(old, new, 1)


def patch_generated_source(source: Path, receipt: Path) -> None:
    live_path = source / LIVE
    service_path = source / SERVICE
    manifest_path = source / MANIFEST
    gradle_path = source / GRADLE
    install_path = source / INSTALL
    control_path = source / CONTROL

    # This control belongs to Infinity. Remove the temporary Cobra-settings entry that
    # RC1 inserted, while retaining the safer scrolling settings container.
    live = live_path.read_text()
    block = re.compile(
        r"\n    Button extendedBackground = action\(.*?\n    \}\);\n\n",
        re.S,
    )
    live, removed = block.subn("\n", live, count=1)
    if removed != 1:
        raise RuntimeError("Expected one Cobra Extended Background button block")
    live = once(
        live,
        "    list.addView(extendedBackground, new LinearLayout.LayoutParams(\n"
        "        LinearLayout.LayoutParams.MATCH_PARENT, dp(56)));\n",
        "",
        "Cobra settings addView",
    )
    live_path.write_text(live)

    # Keep notification language Infinity-owned rather than Cobra-owned.
    service = service_path.read_text()
    service = once(
        service,
        'channel.setDescription("User-enabled session continuity. Turn off here or in Cobra Settings.");',
        'channel.setDescription("User-enabled Infinity session continuity. Turn off here or in Infinity Performance & Display.");',
        "background notification description",
    )
    service_path.write_text(service)

    # Install the tiny exported control Activity.  The service itself remains private.
    control_path.write_text(
        (ROOT / "patches/infinity-background/InfinityBackgroundControlActivity.java.in").read_text()
    )
    install = install_path.read_text()
    install = once(
        install,
        "                  src/InfinityExtendedBackgroundService.java\n",
        "                  src/InfinityExtendedBackgroundService.java\n"
        "                  src/InfinityBackgroundControlActivity.java\n",
        "Java source registration",
    )
    install_path.write_text(install)

    manifest = manifest_path.read_text()
    activity = '''        <activity
            android:name=".InfinityBackgroundControlActivity"
            android:exported="true"
            android:excludeFromRecents="true"
            android:noHistory="true">
            <intent-filter>
                <action android:name="com.projectinfinity.kodi.action.BACKGROUND_MODE_NORMAL" />
                <action android:name="com.projectinfinity.kodi.action.BACKGROUND_MODE_EXTENDED" />
                <category android:name="android.intent.category.DEFAULT" />
            </intent-filter>
        </activity>
'''
    manifest = once(
        manifest,
        '        <service android:name=".InfinityExtendedBackgroundService"\n',
        activity + '        <service android:name=".InfinityExtendedBackgroundService"\n',
        "background service manifest anchor",
    )
    manifest_path.write_text(manifest)

    gradle = gradle_path.read_text()
    gradle = once(gradle, f"versionCode {RC1_CODE}", f"versionCode {RC2_CODE}", "versionCode")
    gradle = once(gradle, f'versionName "{RC1}"', f'versionName "{RC2}"', "versionName")
    gradle_path.write_text(gradle)

    # Update the source receipt so the packaging preservation gate covers this layer too.
    row = json.loads(receipt.read_text())
    row["version_code"] = int(RC2_CODE)
    row["version_name"] = RC2
    row["infinity_background_control_bridge"] = True
    row["cobra_settings_control_removed"] = True
    row["control_actions"] = [
        "com.projectinfinity.kodi.action.BACKGROUND_MODE_NORMAL",
        "com.projectinfinity.kodi.action.BACKGROUND_MODE_EXTENDED",
    ]
    for rel in (LIVE, SERVICE, MANIFEST, GRADLE, INSTALL, CONTROL):
        path = source / rel
        before = row.get("files", {}).get(str(rel), {}).get("before")
        row.setdefault("files", {})[str(rel)] = {"before": before, "after": sha(path.read_bytes())}
    receipt.write_text(json.dumps(row, indent=2, sort_keys=True) + "\n")


def patch_packager(packager: Path) -> None:
    text = packager.read_text()

    # package_background_resume imports these constants when it starts, so update the
    # module only after RC1 source reconstruction has completed.
    module = ROOT / "scripts/infinity_background_resume.py"
    module_text = module.read_text()
    module_text = once(module_text, "VERSION_CODE = 2103136", "VERSION_CODE = 2103137", "packaging VERSION_CODE")
    module_text = once(
        module_text,
        "RELEASE = '1.0.9-Cobra-Background-Resume-RC1'",
        "RELEASE = '1.0.9-Infinity-Background-Control-RC2'",
        "packaging RELEASE",
    )
    module.write_text(module_text)

    # Allow exactly one additional exported control Activity in the structural manifest
    # comparison, then remove it before comparing against the run-40 baseline.
    anchor = "    app['children'].remove(svc)\n    require(old==new,'Compiled manifest drift outside version and new background service; inspect both manifest reports')"
    replacement = """    app['children'].remove(svc)
    controls=[n for n in app['children'] if n['tag']=='activity' and
              'InfinityBackgroundControlActivity' in n['attrs'].get('android:name','')]
    require(len(controls)==1,'Exactly one Infinity background control Activity required')
    app['children'].remove(controls[0])
    require(old==new,'Compiled manifest drift outside version/background service/control bridge; inspect both manifest reports')"""
    text = once(text, anchor, replacement, "manifest verifier")

    text = once(
        text,
        "b'InfinityExtendedBackgroundService',b'EXTENDED BACKGROUND MODE',b'InfinityCoreBridge'",
        "b'InfinityExtendedBackgroundService',b'InfinityBackgroundControlActivity',b'BACKGROUND_MODE_NORMAL',b'BACKGROUND_MODE_EXTENDED',b'InfinityCoreBridge'",
        "DEX bridge token gate",
    )
    text = once(
        text,
        "('InfinityExtendedBackgroundService','FOREGROUND_SERVICE_SPECIAL_USE','PROPERTY_SPECIAL_USE_FGS_SUBTYPE','action.OPEN_LIVE')",
        "('InfinityExtendedBackgroundService','InfinityBackgroundControlActivity','BACKGROUND_MODE_NORMAL','BACKGROUND_MODE_EXTENDED','FOREGROUND_SERVICE_SPECIAL_USE','PROPERTY_SPECIAL_USE_FGS_SUBTYPE','action.OPEN_LIVE')",
        "manifest bridge token gate",
    )
    text = text.replace("Infinity-1.0.9-Cobra-Background-Resume-RC1", "Infinity-1.0.9-Infinity-Background-Control-RC2")
    text = text.replace("docs/background-resume-rc1.md", "docs/infinity-background-control-rc2.md")
    packager.write_text(text)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--packager", type=Path, required=True)
    args = parser.parse_args()
    patch_generated_source(args.source, args.receipt)
    patch_packager(args.packager)
    print("PASS: Infinity Normal/Extended background bridge layered over RC1; Kodi native engine untouched")


if __name__ == "__main__":
    main()
