#!/usr/bin/env python3
"""Apply Infinity 1.0.8 adaptive high-refresh wiring after the 1.0.7 source stack."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected one match, found {count}')
    return text.replace(old, new, 1)


def replace_exact_count(text: str, old: str, new: str, expected: int, label: str) -> str:
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f'{label}: expected {expected} matches, found {count}')
    return text.replace(old, new)


def apply(source: Path) -> dict:
    source = source.resolve()
    main = source / 'tools/android/packaging/xbmc/src/Main.java.in'
    install = source / 'cmake/scripts/android/Install.cmake'
    gradle = source / 'tools/android/packaging/xbmc/build.gradle.in'
    controller = source / 'tools/android/packaging/xbmc/src/InfinityRefreshController.java.in'
    for p in (main, install, gradle):
        if not p.is_file():
            raise FileNotFoundError(p)
    if controller.exists():
        raise RuntimeError('InfinityRefreshController.java.in already exists')

    before = {str(p.relative_to(source)): sha(p) for p in (main, install, gradle)}

    text = install.read_text()
    text = replace_once(text,
        '                  src/InfinityExitDiagnostics.java\n',
        '                  src/InfinityExitDiagnostics.java\n                  src/InfinityRefreshController.java\n',
        'Install refresh controller')
    install.write_text(text)

    text = main.read_text()
    text = replace_once(text,
        '  private InfinityCoreBridge mInfinityBridge;\n',
        '  private InfinityCoreBridge mInfinityBridge;\n  private InfinityRefreshController mInfinityRefresh;\n',
        'Refresh field')
    text = replace_once(text,
        '    mInfinityBridge.attach();\n',
        '    mInfinityBridge.attach();\n    mInfinityRefresh = new InfinityRefreshController(this);\n    mInfinityRefresh.apply("attach");\n',
        'Refresh attach')
    text = replace_once(text,
        '    if (mInfinityBridge != null) mInfinityBridge.onResume();\n',
        '    if (mInfinityBridge != null) mInfinityBridge.onResume();\n    if (mInfinityRefresh != null) mInfinityRefresh.apply("resume");\n',
        'Refresh resume')
    text = replace_once(text,
        '    mInfinityBridge = null;\n',
        '    mInfinityBridge = null;\n    mInfinityRefresh = null;\n',
        'Refresh destroy')
    text = replace_exact_count(text,
        '    if (mInfinityBridge != null) mInfinityBridge.onWindowChanged();\n',
        '    if (mInfinityBridge != null) mInfinityBridge.onWindowChanged();\n    if (mInfinityRefresh != null) mInfinityRefresh.apply("window");\n',
        3,
        'Refresh window callbacks')
    text = replace_once(text,
        '    if (hasFocus && mInfinityBridge != null) mInfinityBridge.onWindowChanged();\n',
        '    if (hasFocus && mInfinityBridge != null) mInfinityBridge.onWindowChanged();\n    if (hasFocus && mInfinityRefresh != null) mInfinityRefresh.apply("focus");\n',
        'Refresh focus')
    text = replace_once(text,
        '          mInfinityBridge.updatePictureInPictureParams();\n',
        '          mInfinityBridge.updatePictureInPictureParams();\n        if (!mInfinityDestroyed && mInfinityRefresh != null)\n          mInfinityRefresh.apply("playback");\n',
        'Refresh playback')
    main.write_text(text)

    text = gradle.read_text()
    text = replace_once(text, 'versionCode 2103107', 'versionCode 2103108', 'versionCode')
    text = replace_once(text, 'versionName "21.3-Infinity-1.0.7-Candidate-1"',
                        'versionName "21.3-Infinity-1.0.8-Candidate-1"', 'versionName')
    gradle.write_text(text)

    controller.write_bytes((ROOT / 'patches/infinity-refresh/InfinityRefreshController.java.in').read_bytes())

    final_main = main.read_text()
    for needle in ('InfinityRefreshController mInfinityRefresh', 'mInfinityRefresh.apply("attach")',
                   'mInfinityRefresh.apply("resume")', 'mInfinityRefresh.apply("playback")'):
        if needle not in final_main:
            raise RuntimeError('Missing 1.0.8 refresh wiring: ' + needle)
    if final_main.count('mInfinityRefresh.apply("window")') != 3:
        raise RuntimeError('Expected refresh re-evaluation on all three window callbacks')

    return {
        'schema': 1,
        'release': '1.0.8 Candidate 1',
        'versionCode': 2103108,
        'base': '1.0.7 Candidate 1 source stack',
        'ui_policy_default': 'high_refresh',
        'video_policy_default': 'match_video',
        'battery_saver_default': True,
        'thermal_protection_default': True,
        'device_tested': False,
        'files': {
            **{k: {'before': v, 'after': sha(source / k)} for k, v in before.items()},
            'tools/android/packaging/xbmc/src/InfinityRefreshController.java.in': {'after': sha(controller)},
        },
    }


def main_cli():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('--receipt', required=True, type=Path)
    a = p.parse_args()
    receipt = apply(a.source)
    a.receipt.parent.mkdir(parents=True, exist_ok=True)
    a.receipt.write_text(json.dumps(receipt, indent=2) + '\n')
    print('Infinity 1.0.8 adaptive refresh wiring applied.')


if __name__ == '__main__':
    main_cli()
