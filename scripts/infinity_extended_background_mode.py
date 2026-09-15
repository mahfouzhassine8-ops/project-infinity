#!/usr/bin/env python3
"""Install and verify Infinity's opt-in Extended Background Mode.

This transform is intentionally layered after the accepted Cobra Candidate 2
source reconstruction. It changes no protected skin/player/browser baseline and
keeps the feature OFF by default. When enabled by the user it runs a visible,
low-importance Android foreground service without a wake lock.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE_TEMPLATE = ROOT / "patches/infinity-cobra-v2/InfinityExtendedBackgroundService.java.in"
GRADLE = Path("tools/android/packaging/xbmc/build.gradle.in")
MANIFEST = Path("tools/android/packaging/xbmc/AndroidManifest.xml.in")
INSTALL = Path("cmake/scripts/android/Install.cmake")
ACTIVITY = Path("tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in")
SERVICE = Path("tools/android/packaging/xbmc/src/InfinityExtendedBackgroundService.java.in")

BASE_VERSION_CODE = 2103134
BASE_RELEASE = "1.0.9-Cobra-Full-Feature-Candidate-2"
VERSION_CODE = 2103135
RELEASE = "1.0.9-Cobra-Full-Feature-Candidate-2-Extended-Background"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def apply(source: Path, receipt: Path) -> None:
    source = source.resolve()
    gradle = source / GRADLE
    manifest = source / MANIFEST
    install = source / INSTALL
    activity = source / ACTIVITY
    service = source / SERVICE
    for path in (gradle, manifest, install, activity):
        if not path.is_file():
            raise RuntimeError(f"Extended Background Mode source input missing: {path}")
    if not SERVICE_TEMPLATE.is_file():
        raise RuntimeError(f"Extended Background Mode template missing: {SERVICE_TEMPLATE}")

    before = {
        str(rel): sha(source / rel)
        for rel in (GRADLE, MANIFEST, INSTALL, ACTIVITY)
    }

    text = gradle.read_text(encoding="utf-8")
    text = once(
        text,
        f"versionCode {BASE_VERSION_CODE}",
        f"versionCode {VERSION_CODE}",
        "Extended Background versionCode",
    )
    text = once(
        text,
        f'versionName "{BASE_RELEASE}"',
        f'versionName "{RELEASE}"',
        "Extended Background versionName",
    )
    gradle.write_text(text, encoding="utf-8")

    service.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SERVICE_TEMPLATE, service)

    text = install.read_text(encoding="utf-8")
    if "src/InfinityExtendedBackgroundService.java" not in text:
        anchor = "                  src/InfinityCobraBootReceiver.java\n"
        text = once(
            text,
            anchor,
            anchor + "                  src/InfinityExtendedBackgroundService.java\n",
            "Extended Background Java install",
        )
    install.write_text(text, encoding="utf-8")

    text = manifest.read_text(encoding="utf-8")
    special_permission = (
        '<uses-permission android:name="android.permission.FOREGROUND_SERVICE_SPECIAL_USE" />\n'
    )
    if "android.permission.FOREGROUND_SERVICE_SPECIAL_USE" not in text:
        anchor = '<uses-permission android:name="android.permission.FOREGROUND_SERVICE_DATA_SYNC" />\n'
        text = once(
            text,
            anchor,
            anchor + special_permission,
            "Extended Background special-use permission",
        )
    if 'android:name=".InfinityExtendedBackgroundService"' not in text:
        service_component = '''        <service
            android:name=".InfinityExtendedBackgroundService"
            android:exported="false"
            android:stopWithTask="false"
            android:foregroundServiceType="specialUse">
            <property
                android:name="android.app.PROPERTY_SPECIAL_USE_FGS_SUBTYPE"
                android:value="User-enabled Infinity media-center session continuity and quicker resume." />
        </service>

'''
        anchor = '        <service\n            android:name=".InfinityCobraRecordingService"\n'
        text = once(
            text,
            anchor,
            service_component + anchor,
            "Extended Background service component",
        )
    manifest.write_text(text, encoding="utf-8")

    java = activity.read_text(encoding="utf-8")
    sync_line = "    InfinityExtendedBackgroundService.sync(this);\n"
    if sync_line not in java:
        anchor = "    mPrefs = getSharedPreferences(PREFS, MODE_PRIVATE);\n"
        java = once(
            java,
            anchor,
            anchor + sync_line,
            "Extended Background launch sync",
        )

    if "EXTENDED BACKGROUND MODE • ON" not in java:
        button_block = '''    Button extendedBackground = action(
        InfinityExtendedBackgroundService.isEnabled(this)
            ? "EXTENDED BACKGROUND MODE • ON"
            : "EXTENDED BACKGROUND MODE • OFF");
    extendedBackground.setOnClickListener(v -> {
      boolean enabled = !InfinityExtendedBackgroundService.isEnabled(this);
      InfinityExtendedBackgroundService.setEnabled(this, enabled);
      toast(enabled
          ? "Extended Background Mode on • visible notification active"
          : "Extended Background Mode off • normal Android behavior restored");
      showSettings();
    });

'''
        anchor = "    TextView themeInfo = text(\n"
        java = once(
            java,
            anchor,
            button_block + anchor,
            "Extended Background settings button",
        )
        list_anchor = '''    list.addView(themeInfo, new LinearLayout.LayoutParams(
        LinearLayout.LayoutParams.MATCH_PARENT, dp(160)));
'''
        list_new = '''    list.addView(extendedBackground, new LinearLayout.LayoutParams(
        LinearLayout.LayoutParams.MATCH_PARENT, dp(56)));
''' + list_anchor
        java = once(
            java,
            list_anchor,
            list_new,
            "Extended Background settings row",
        )
    activity.write_text(java, encoding="utf-8")

    verify(source)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    files = {}
    for rel in (GRADLE, MANIFEST, INSTALL, ACTIVITY, SERVICE):
        files[str(rel)] = {
            "before": before.get(str(rel)),
            "after": sha(source / rel),
        }
    data = {
        "schema": 1,
        "release": RELEASE,
        "version_code": VERSION_CODE,
        "base_release": BASE_RELEASE,
        "base_version_code": BASE_VERSION_CODE,
        "extended_background_mode": True,
        "default_enabled": False,
        "foreground_service": True,
        "foreground_service_type": "specialUse",
        "persistent_visible_notification": True,
        "start_sticky": True,
        "wake_lock": False,
        "screen_wake_lock": False,
        "android_may_reclaim_process": True,
        "protected_baselines_modified_in_place": False,
        "files": files,
    }
    receipt.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS: Infinity Extended Background Mode installed (default OFF)")


def verify(source: Path) -> None:
    source = source.resolve()
    gradle = (source / GRADLE).read_text(encoding="utf-8")
    manifest = (source / MANIFEST).read_text(encoding="utf-8")
    install = (source / INSTALL).read_text(encoding="utf-8")
    activity = (source / ACTIVITY).read_text(encoding="utf-8")
    service_path = source / SERVICE
    if not service_path.is_file():
        raise RuntimeError("Extended Background service source missing")
    service = service_path.read_text(encoding="utf-8")

    required_gradle = (
        f"versionCode {VERSION_CODE}",
        f'versionName "{RELEASE}"',
    )
    for needle in required_gradle:
        if needle not in gradle:
            raise RuntimeError("Extended Background identity missing: " + needle)
    for needle in (
        'android.permission.FOREGROUND_SERVICE_SPECIAL_USE',
        'android:name=".InfinityExtendedBackgroundService"',
        'android:foregroundServiceType="specialUse"',
        'android.app.PROPERTY_SPECIAL_USE_FGS_SUBTYPE',
        'android:stopWithTask="false"',
    ):
        if needle not in manifest:
            raise RuntimeError("Extended Background manifest contract missing: " + needle)
    if "src/InfinityExtendedBackgroundService.java" not in install:
        raise RuntimeError("Extended Background service missing from Android Java install")
    for needle in (
        "InfinityExtendedBackgroundService.sync(this);",
        "EXTENDED BACKGROUND MODE • ON",
        "EXTENDED BACKGROUND MODE • OFF",
        "InfinityExtendedBackgroundService.setEnabled(this, enabled);",
    ):
        if needle not in activity:
            raise RuntimeError("Extended Background settings contract missing: " + needle)
    for needle in (
        'getBoolean(KEY_ENABLED, false)',
        'START_STICKY',
        'FOREGROUND_SERVICE_TYPE_SPECIAL_USE',
        'Infinity • Extended Background Mode',
        'Turn off',
    ):
        if needle not in service:
            raise RuntimeError("Extended Background runtime contract missing: " + needle)
    for forbidden in (
        "PowerManager.WakeLock",
        "PARTIAL_WAKE_LOCK",
        "FULL_WAKE_LOCK",
        "ACQUIRE_CAUSES_WAKEUP",
        "android.permission.WAKE_LOCK",
    ):
        if forbidden in service:
            raise RuntimeError("Extended Background must not use a wake lock: " + forbidden)
    print("PASS: Infinity Extended Background Mode source verification")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("apply")
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    p = sub.add_parser("verify")
    p.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    if args.cmd == "apply":
        apply(args.source, args.receipt)
    else:
        verify(args.source)


if __name__ == "__main__":
    main()
