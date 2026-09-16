#!/usr/bin/env python3
"""Static/SDK contract checks for the real Extended Background control surface."""
import argparse
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET

ACTION = 'com.projectinfinity.kodi.action.OPEN_BACKGROUND_SETTINGS'
PACKAGE = 'com.projectinfinity.kodi'


def run(source: Path, out: Path, android_jar: Path | None) -> None:
    java_root = source / 'tools/android/packaging/xbmc/src'
    settings_path = java_root / 'InfinityBackgroundSettingsActivity.java.in'
    service_path = java_root / 'InfinityExtendedBackgroundService.java.in'
    assert settings_path.is_file(), 'settings activity source missing'
    settings = settings_path.read_text()
    service = service_path.read_text()
    live = (java_root / 'InfinityLiveActivity.java.in').read_text()
    install = (source / 'cmake/scripts/android/Install.cmake').read_text()
    gradle = (source / 'tools/android/packaging/xbmc/build.gradle.in').read_text()

    assert 'InfinityExtendedBackgroundService.setEnabled(this, checked)' in settings
    assert 'InfinityExtendedBackgroundService.isEnabled(this)' in settings
    assert 'InfinityExtendedBackgroundService.isRunning()' in settings
    assert 'Battery & Background Access' in settings
    assert 'Notification Access' in settings
    assert 'Resume Playback' not in settings
    assert 'Preserve Manual Pause' not in settings
    assert 'Picture-in-Picture Support' not in settings
    assert 'EXTENDED BACKGROUND MODE' not in live, 'duplicate Cobra control retained'
    assert 'src/InfinityBackgroundSettingsActivity.java' in install
    assert 'versionCode 2103137' in gradle
    assert 'versionName "1.0.9-Cobra-Background-Controls-RC2"' in gradle

    manifest = ET.fromstring((source / 'tools/android/packaging/xbmc/AndroidManifest.xml.in').read_text())
    ns = '{http://schemas.android.com/apk/res/android}'
    activities = [a for a in manifest.findall('./application/activity')
                  if a.get(ns + 'name') == '.InfinityBackgroundSettingsActivity']
    assert len(activities) == 1, 'settings activity manifest entry missing/duplicated'
    activity = activities[0]
    assert activity.get(ns + 'exported') == 'true'
    actions = [a.get(ns + 'name') for a in activity.findall('./intent-filter/action')]
    categories = [c.get(ns + 'name') for c in activity.findall('./intent-filter/category')]
    assert actions == [ACTION], actions
    assert 'android.intent.category.DEFAULT' in categories

    if android_jar:
        sdk = out / 'sdk/com/projectinfinity/kodi'
        sdk.mkdir(parents=True, exist_ok=True)
        (sdk / 'InfinityExtendedBackgroundService.java').write_text(
            service.replace('@APP_PACKAGE@', PACKAGE))
        (sdk / 'InfinityBackgroundSettingsActivity.java').write_text(
            settings.replace('@APP_PACKAGE@', PACKAGE))
        (sdk / 'Splash.java').write_text(
            'package com.projectinfinity.kodi; public class Splash extends android.app.Activity {}')
        classes = out / 'sdk/classes'
        classes.mkdir(parents=True, exist_ok=True)
        subprocess.run([
            'javac', '-source', '8', '-target', '8', '-cp', str(android_jar),
            '-d', str(classes), *[str(p) for p in sdk.glob('*.java')]
        ], check=True)
        print('PASS: background settings activity + service compile against real Android SDK')

    print('PASS: dedicated Infinity background action is real, exported, minimal, and not duplicated in Cobra')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--android-jar', type=Path)
    a = p.parse_args()
    run(a.source, a.out, a.android_jar)
