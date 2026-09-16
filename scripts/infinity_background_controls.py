#!/usr/bin/env python3
"""Add the real Extended Background control surface over Background Resume RC1.

This is still Android-shell-only work. It does not rebuild or modify Kodi native
code, native libraries, skin assets, or the accepted rotation implementation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ANDROID = Path('tools/android/packaging/xbmc')
LIVE = ANDROID / 'src/InfinityLiveActivity.java.in'
SETTINGS = ANDROID / 'src/InfinityBackgroundSettingsActivity.java.in'
MANIFEST = ANDROID / 'AndroidManifest.xml.in'
GRADLE = ANDROID / 'build.gradle.in'
INSTALL = Path('cmake/scripts/android/Install.cmake')
VERSION_CODE = 2103137
RELEASE = '1.0.9-Cobra-Background-Controls-RC2'
ACTION = 'com.projectinfinity.kodi.action.OPEN_BACKGROUND_SETTINGS'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError('Unexpected RC1 preimage: ' + repr(old[:120]))
    return text.replace(old, new, 1)


def apply(source: Path, receipt: Path, rc2_receipt: Path) -> None:
    live = (source / LIVE).read_text()
    manifest = (source / MANIFEST).read_text()
    gradle = (source / GRADLE).read_text()
    install = (source / INSTALL).read_text()

    # RC1 exposed the switch inside Cobra. RC2 deliberately removes that duplicate
    # control; the drawer opens the dedicated Infinity settings activity instead.
    start = live.index('    Button extendedBackground = action(\n')
    end = live.index('    TextView themeInfo = text(\n', start)
    live = live[:start] + live[end:]
    live = once(live,
        '    list.addView(extendedBackground, new LinearLayout.LayoutParams(\n'
        '        LinearLayout.LayoutParams.MATCH_PARENT, dp(56)));\n', '')
    live = once(live,
        '    ScrollView settingsScroll = new ScrollView(this);\n'
        '    settingsScroll.setFillViewport(true);\n'
        '    settingsScroll.addView(list);\n'
        '    mStage.addView(settingsScroll, new LinearLayout.LayoutParams(\n'
        '        LinearLayout.LayoutParams.MATCH_PARENT, 0, 1));',
        '    mStage.addView(list, new LinearLayout.LayoutParams(\n'
        '        LinearLayout.LayoutParams.MATCH_PARENT, 0, 1));')

    gradle = once(gradle, 'versionCode 2103136', f'versionCode {VERSION_CODE}')
    gradle = once(gradle,
        'versionName "1.0.9-Cobra-Background-Resume-RC1"',
        f'versionName "{RELEASE}"')

    install = once(install,
        '                  src/InfinityExtendedBackgroundService.java\n',
        '                  src/InfinityExtendedBackgroundService.java\n'
        '                  src/InfinityBackgroundSettingsActivity.java\n')

    activity = '''        <activity
            android:name=".InfinityBackgroundSettingsActivity"
            android:exported="true"
            android:excludeFromRecents="true"
            android:launchMode="singleTop"
            android:theme="@android:style/Theme.Material.NoActionBar"
            android:configChanges="keyboard|keyboardHidden|orientation|screenSize|screenLayout|smallestScreenSize|density|uiMode">
            <intent-filter>
                <action android:name="com.projectinfinity.kodi.action.OPEN_BACKGROUND_SETTINGS" />
                <category android:name="android.intent.category.DEFAULT" />
            </intent-filter>
        </activity>
'''
    manifest = once(manifest,
        '        <service android:name=".InfinityExtendedBackgroundService"\n',
        activity + '        <service android:name=".InfinityExtendedBackgroundService"\n')
    ET.fromstring(manifest)

    settings = (ROOT / 'patches/infinity-background/InfinityBackgroundSettingsActivity.java.in').read_text()
    outputs = {LIVE: live, SETTINGS: settings, MANIFEST: manifest, GRADLE: gradle, INSTALL: install}
    for path, text in outputs.items():
        target = source / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')

    data = json.loads(receipt.read_text())
    data['schema'] = 2
    data['version_code'] = VERSION_CODE
    data['version_name'] = RELEASE
    data['background_settings_action'] = ACTION
    data['dedicated_settings_activity'] = True
    data['cobra_settings_duplicate_removed'] = True
    data['native_source_modified'] = False
    data['skin_modified'] = False
    data['rotation_policy_preserved'] = True
    for path, text in outputs.items():
        key = str(path)
        prior = data.get('files', {}).get(key, {})
        data.setdefault('files', {})[key] = {
            'before': prior.get('after'),
            'after': sha(text.encode('utf-8')),
        }
    encoded = json.dumps(data, indent=2, sort_keys=True) + '\n'
    receipt.write_text(encoded)
    rc2_receipt.parent.mkdir(parents=True, exist_ok=True)
    rc2_receipt.write_text(encoded)
    print('PASS: real background settings activity added; Cobra duplicate removed; native engine/rotation untouched')


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--receipt', type=Path, required=True)
    p.add_argument('--rc2-receipt', type=Path, required=True)
    a = p.parse_args()
    apply(a.source, a.receipt, a.rc2_receipt)


if __name__ == '__main__':
    main()
