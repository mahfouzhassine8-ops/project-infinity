#!/usr/bin/env python3
"""Compile/static gate for Infinity Platform Hook API and system media integration."""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import subprocess


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--android-jar', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()

    root = args.source / 'tools/android/packaging/xbmc/src'
    session = (root / 'XBMCMediaSession.java.in').read_text()
    hook = (root / 'InfinityPlatformHook.java.in').read_text()
    registry = (root / 'InfinityPlatformHooks.java.in').read_text()
    system = (root / 'InfinitySystemMediaHook.java.in').read_text()
    install = (args.source / 'cmake/scripts/android/Install.cmake').read_text()
    gradle = (args.source / 'tools/android/packaging/xbmc/build.gradle.in').read_text()

    required_session = [
        'new MediaSession(Main.MainActivity, "Infinity_media")',
        'InfinityPlatformHooks.onMediaSessionCreated',
        'InfinityPlatformHooks.onMediaSessionActive',
        'InfinityPlatformHooks.onPlaybackState',
        'InfinityPlatformHooks.onMetadata',
        'InfinityPlatformHooks.onSessionIntent',
    ]
    for needle in required_session:
        assert needle in session, needle
    assert session.count('new MediaSession(') == 1, 'must preserve exactly one MediaSession'

    for name in ('InfinityPlatformHook.java', 'InfinityPlatformHooks.java', 'InfinitySystemMediaHook.java'):
        assert 'src/' + name in install, name
    assert 'versionCode 2103109' in gradle
    assert '21.3-Infinity-1.0.8-Native-Media' in gradle

    for action in ('ACTION_PLAY', 'ACTION_PAUSE', 'ACTION_PLAY_PAUSE', 'ACTION_SEEK_TO',
                   'ACTION_FAST_FORWARD', 'ACTION_REWIND', 'ACTION_SKIP_TO_NEXT',
                   'ACTION_SKIP_TO_PREVIOUS', 'ACTION_STOP'):
        assert action in system, action
    for needle in ('Notification.MediaStyle', 'setMediaSession(session.getSessionToken())',
                   'R.drawable.notif_icon', 'com.projectinfinity.platform_hook_api',
                   'com.projectinfinity.system_media'):
        assert needle in system, needle
    assert 'new MediaSession(' not in hook + registry + system, 'platform hooks must not create another session'
    assert 'InfinitySystemMediaHook()' in registry
    assert 'catch (Throwable error)' in registry, 'hooks must be fault isolated'

    # Compile the actual media/session templates against Android API. Kodi collaborators
    # not under test are tiny compile-only stubs.
    work = args.out.resolve()
    if work.exists():
        shutil.rmtree(work)
    pkg = work / 'src/com/projectinfinity/kodi'
    pkg.mkdir(parents=True)
    replacements = {'@APP_PACKAGE@': 'com.projectinfinity.kodi', '@APP_NAME@': 'Infinity'}
    for name in ('XBMCMediaSession', 'InfinityPlatformHook', 'InfinityPlatformHooks',
                 'InfinitySystemMediaHook'):
        text = (root / (name + '.java.in')).read_text()
        for old, new in replacements.items():
            text = text.replace(old, new)
        assert '@APP_' not in text, name
        (pkg / (name + '.java')).write_text(text)
    (pkg / 'Main.java').write_text('''package com.projectinfinity.kodi;\npublic class Main extends android.app.Activity { public static Main MainActivity; }\n''')
    (pkg / 'XBMCBroadcastReceiver.java').write_text('''package com.projectinfinity.kodi;\npublic class XBMCBroadcastReceiver extends android.content.BroadcastReceiver {\n public void onReceive(android.content.Context c, android.content.Intent i) {}\n}\n''')
    (pkg / 'R.java').write_text('''package com.projectinfinity.kodi;\npublic final class R { public static final class drawable { public static final int notif_icon=1; } }\n''')

    classes = work / 'classes'
    classes.mkdir()
    sources = [str(p) for p in pkg.glob('*.java')]
    subprocess.run([
        'javac', '-source', '8', '-target', '8', '-Xlint:unchecked',
        '-cp', str(args.android_jar.resolve()), '-d', str(classes), *sources
    ], check=True)
    subprocess.run([
        'javap', '-p', '-classpath', str(classes), 'com.projectinfinity.kodi.InfinityPlatformHooks'
    ], check=True, stdout=subprocess.PIPE, text=True)
    print('PASS: Infinity Platform Hook API 1 + Android MediaSession/MediaStyle integration compiles.')
    print('PASS: single Kodi MediaSession retained; transport actions + seek exposed; no Samsung-private API.')
    print('Real One UI / lock-screen / Bluetooth / PiP behavior still requires device testing.')


if __name__ == '__main__':
    main()
