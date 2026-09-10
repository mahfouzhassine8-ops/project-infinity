#!/usr/bin/env python3
"""Add the Infinity Platform Hook API and Android system-media integration after 1.0.8."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCHES = ROOT / 'patches/infinity-media'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected one match, found {count}')
    return text.replace(old, new, 1)


def apply(source: Path) -> dict:
    source = source.resolve()
    install = source / 'cmake/scripts/android/Install.cmake'
    gradle = source / 'tools/android/packaging/xbmc/build.gradle.in'
    session = source / 'tools/android/packaging/xbmc/src/XBMCMediaSession.java.in'
    targets = [
        source / 'tools/android/packaging/xbmc/src/InfinityPlatformHook.java.in',
        source / 'tools/android/packaging/xbmc/src/InfinityPlatformHooks.java.in',
        source / 'tools/android/packaging/xbmc/src/InfinitySystemMediaHook.java.in',
    ]
    for path in (install, gradle, session):
        if not path.is_file():
            raise FileNotFoundError(path)
    for path in targets:
        if path.exists():
            raise RuntimeError(f'Native media hook target already exists: {path}')

    before = {str(p.relative_to(source)): sha(p) for p in (install, gradle, session)}

    text = install.read_text()
    text = replace_once(
        text,
        '                  src/InfinityRefreshController.java\n',
        '                  src/InfinityRefreshController.java\n'
        '                  src/InfinityPlatformHook.java\n'
        '                  src/InfinityPlatformHooks.java\n'
        '                  src/InfinitySystemMediaHook.java\n',
        'Install platform media hooks')
    install.write_text(text)

    text = session.read_text()
    text = replace_once(
        text,
        '    this.mSession = new MediaSession(Main.MainActivity, "XBMC_session");\n',
        '    this.mSession = new MediaSession(Main.MainActivity, "Infinity_media");\n'
        '    InfinityPlatformHooks.onMediaSessionCreated(this.mSession);\n',
        'Register Infinity platform hook')
    text = replace_once(
        text,
        '  public void activate(boolean state)\n  {\n    mSession.setActive(state);\n  }\n',
        '  public void activate(boolean state)\n  {\n    mSession.setActive(state);\n'
        '    InfinityPlatformHooks.onMediaSessionActive(mSession, state);\n  }\n',
        'Publish active state')
    text = replace_once(
        text,
        '  private void updatePlaybackState(PlaybackState mystate)\n  {\n    mSession.setPlaybackState(mystate);\n  }\n',
        '  private void updatePlaybackState(PlaybackState mystate)\n  {\n'
        '    PlaybackState state = InfinityPlatformHooks.onPlaybackState(mSession, mystate);\n'
        '    mSession.setPlaybackState(state);\n  }\n',
        'Decorate playback state')
    text = replace_once(
        text,
        '  private void updateMetadata(MediaMetadata myData)\n  {\n    mSession.setMetadata(myData);\n  }\n',
        '  private void updateMetadata(MediaMetadata myData)\n  {\n'
        '    MediaMetadata data = InfinityPlatformHooks.onMetadata(mSession, myData);\n'
        '    mSession.setMetadata(data);\n  }\n',
        'Decorate metadata')
    text = replace_once(
        text,
        '    mSession.setSessionActivity(pi);\n',
        '    mSession.setSessionActivity(pi);\n    InfinityPlatformHooks.onSessionIntent(mSession, intent);\n',
        'Publish session intent')
    session.write_text(text)

    text = gradle.read_text()
    text = replace_once(text, 'versionCode 2103108', 'versionCode 2103109', 'versionCode')
    text = replace_once(
        text,
        'versionName "21.3-Infinity-1.0.8-Candidate-1"',
        'versionName "21.3-Infinity-1.0.8-Native-Media"',
        'versionName')
    gradle.write_text(text)

    names = ('InfinityPlatformHook.java.in', 'InfinityPlatformHooks.java.in',
             'InfinitySystemMediaHook.java.in')
    for name, target in zip(names, targets):
        target.write_bytes((PATCHES / name).read_bytes())

    final_session = session.read_text()
    required = (
        'new MediaSession(Main.MainActivity, "Infinity_media")',
        'InfinityPlatformHooks.onMediaSessionCreated',
        'InfinityPlatformHooks.onMediaSessionActive',
        'InfinityPlatformHooks.onPlaybackState',
        'InfinityPlatformHooks.onMetadata',
        'InfinityPlatformHooks.onSessionIntent',
    )
    for needle in required:
        if needle not in final_session:
            raise RuntimeError('Missing native media integration: ' + needle)
    if final_session.count('new MediaSession(') != 1:
        raise RuntimeError('Infinity must reuse Kodi single MediaSession, not create a second session')

    files = {k: {'before': v, 'after': sha(source / k)} for k, v in before.items()}
    for target in targets:
        files[str(target.relative_to(source))] = {'after': sha(target)}

    return {
        'schema': 1,
        'release': 'Infinity 1.0.8 Native Media Update',
        'versionCode': 2103109,
        'base': '1.0.8 Candidate 1 source stack',
        'platform_hook_api': 1,
        'media_session': 'android.media.session.MediaSession',
        'media_style_notification': True,
        'system_media_controls': ['play', 'pause', 'play_pause', 'seek', 'previous', 'next',
                                  'rewind', 'fast_forward', 'stop'],
        'samsung_private_api': False,
        'single_media_session': True,
        'device_tested': False,
        'files': files,
    }


def main_cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--receipt', required=True, type=Path)
    args = parser.parse_args()
    receipt = apply(args.source)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + '\n')
    print('Infinity Platform Hook API 1 + native Android media integration applied.')


if __name__ == '__main__':
    main_cli()
