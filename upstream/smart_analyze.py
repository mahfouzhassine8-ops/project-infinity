#!/usr/bin/env python3
"""Turn source-port evidence into a compact Infinity Kodi compatibility report.

This tool does not build, sign, install, release, merge, or promote an APK.
It summarizes exactly what changed upstream, where Infinity/Cobra overlaps, and
which fast validation gates passed so a human can decide whether a full native
build is worth running.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path


def classify_file(path: str) -> str:
    if path.startswith(('tools/android/', 'xbmc/platform/android/')):
        return 'android'
    if path.startswith(('tools/depends/', 'cmake/')) or path in ('CMakeLists.txt', 'version.txt'):
        return 'build_toolchain'
    if path.startswith(('xbmc/guilib/', 'xbmc/rendering/', 'xbmc/windowing/')):
        return 'renderer_ui'
    if path.startswith(('xbmc/cores/', 'xbmc/application/')):
        return 'playback_audio'
    if path.startswith(('xbmc/addons/', 'xbmc/interfaces/', 'addons/')):
        return 'addons_python_api'
    if path.startswith(('xbmc/input/', 'system/keymaps/')):
        return 'input_remote_touch'
    if path.startswith(('xbmc/dbwrappers/', 'xbmc/video/', 'xbmc/music/')):
        return 'userdata_database'
    if path.startswith('xbmc/'):
        return 'native_engine_other'
    return 'other'


def suffix(path: str) -> str:
    name = Path(path).name
    if '.' not in name:
        return '(none)'
    return Path(path).suffix.lower() or '(none)'


def build_report(port_report: dict, ownership: dict, java_status: dict) -> dict:
    changed = port_report['impact']['changed_upstream_files']
    intersections = port_report['impact']['owned_file_intersections']
    category_counts = Counter(classify_file(p) for p in changed)
    extension_counts = Counter(suffix(p) for p in changed)
    watch_counts = {k: len(v) for k, v in port_report['impact']['watch_areas'].items()}

    native_or_toolchain = any(
        classify_file(p) in {
            'build_toolchain', 'renderer_ui', 'playback_audio', 'addons_python_api',
            'input_remote_touch', 'userdata_database', 'native_engine_other'
        }
        for p in changed
    )
    replay_clean = bool(port_report.get('replay_clean'))
    java_ok = java_status.get('status') == 'passed'

    if not replay_clean:
        state = 'analysis_blocked'
        next_action = 'Review source replay conflicts before any build.'
    elif intersections:
        state = 'review_required'
        next_action = 'Review direct Infinity/Cobra intersections before approving a full build.'
    elif native_or_toolchain:
        state = 'review_ready'
        next_action = 'Fast analysis passed; full native build is still required before adoption.'
    elif java_ok:
        state = 'fast_checks_passed'
        next_action = 'Fast checks passed; review the report before deciding on a full build.'
    else:
        state = 'review_required'
        next_action = 'Review targeted validation results before any full build.'

    baseline_tag = port_report['baseline']['upstream']['tag']
    target_tag = port_report['target']['tag']
    target_commit = port_report['target']['commit']

    return {
        'schema': 1,
        'state': state,
        'baseline': baseline_tag,
        'target': target_tag,
        'target_commit': target_commit,
        'update_available': target_tag != baseline_tag,
        'source_downloaded_and_compared': True,
        'upstream_changed_files': len(changed),
        'infinity_owned_files': len(ownership),
        'direct_infinity_intersections': intersections,
        'category_counts': dict(sorted(category_counts.items())),
        'extension_counts': dict(sorted(extension_counts.items())),
        'watch_area_counts': watch_counts,
        'targeted_checks': {
            'source_patch_replay': 'passed' if replay_clean else 'blocked',
            'infinity_android_java_compile': java_status.get('status', 'not_run'),
            'full_native_compile': 'deferred',
            'full_apk_build': 'not_started',
            'device_test': 'not_run',
        },
        'production_modified': False,
        'stop_gate': True,
        'next_action': next_action,
        'system_tray': {
            'title': 'Kodi Update',
            'state': state,
            'current_version': baseline_tag,
            'available_version': target_tag,
            'changed_files': len(changed),
            'direct_intersections': len(intersections),
            'action_label': 'View analysis',
            'summary': next_action,
        },
    }


def markdown(report: dict) -> str:
    cats = report['category_counts']
    lines = [
        '# Infinity Kodi Update Analysis',
        '',
        f"**Current:** {report['baseline']}",
        f"**Detected:** {report['target']} (`{report['target_commit']}`)",
        f"**Status:** {report['state']}",
        '',
        f"Upstream changed files: **{report['upstream_changed_files']}**",
        f"Direct Infinity/Cobra intersections: **{len(report['direct_infinity_intersections'])}**",
        f"Infinity-owned files tracked: **{report['infinity_owned_files']}**",
        '',
        '## Change areas',
    ]
    if cats:
        lines.extend(f"- {name}: {count}" for name, count in cats.items())
    else:
        lines.append('- No upstream file changes relative to the pinned baseline.')
    lines += [
        '',
        '## Fast validation',
        f"- Source replay: {report['targeted_checks']['source_patch_replay']}",
        f"- Infinity Android/Java compile: {report['targeted_checks']['infinity_android_java_compile']}",
        '- Full native compile: deferred',
        '- Full APK build: not started',
        '- Device test: not run',
        '',
        f"**Next:** {report['next_action']}",
        '',
        '**STOP:** no APK was built, signed, installed, released, merged, or promoted by this analysis.',
        '',
    ]
    if report['direct_infinity_intersections']:
        lines += ['## Direct intersections', *[f"- `{p}`" for p in report['direct_infinity_intersections']], '']
    return '\n'.join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port-report', type=Path, required=True)
    parser.add_argument('--ownership', type=Path, required=True)
    parser.add_argument('--java-status', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()

    port_report = json.loads(args.port_report.read_text())
    ownership = json.loads(args.ownership.read_text())
    java_status = json.loads(args.java_status.read_text())
    report = build_report(port_report, ownership, java_status)

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'smart-analysis.json').write_text(json.dumps(report, indent=2) + '\n')
    (args.output / 'SMART-ANALYSIS.md').write_text(markdown(report))
    (args.output / 'system-tray-status.json').write_text(json.dumps(report['system_tray'], indent=2) + '\n')
    print(markdown(report))


if __name__ == '__main__':
    main()
