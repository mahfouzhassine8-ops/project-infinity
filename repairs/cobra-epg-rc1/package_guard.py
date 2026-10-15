#!/usr/bin/env python3
"""Fail-closed packaging inputs and matching UI delivery; never edits app/native code."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
import zipfile

REPOSITORY = 'mahfouzhassine8-ops/project-infinity'
BASE = 'cce2de3042cca22b531fa8ed9e13659c19dab8a4'
REFINEMENT = '06f7dffa4b23af03030042bc057cfe1a8b672189'
ADAPTIVE = 'a1166a505696e90cd5032c06877b0bce36dc3c42'
PRECHANGE = '34caead6889c476bf89eb7421f2f907f93b1d962'
RUNTIME = 'b42760a25a27d23baa5db5770824cb8d32ec2290'
NDK = '21.4.7075529'
ADDON = 'script.infinity.cobra.theme'
RUNTIME_BLOBS = {
    'infinity_1_0_9_cobra_approved_ui.py': '226cfe65f2bbc65cef831e9a01ade19578fc7f2e',
    'infinity_1_0_9_cobra_zip_ui_runtime.py': 'e2186cc6f82c098e02206f1c0ccc1b2dc57dd79f',
    'infinity_1_0_9_cobra_zip_ui_runtime_matcher_fix.py': 'a87ecfc95ad2ad9c69546bbbab97b3f85e30137f',
    'apply_cobra_approved_ui.py': '99bdbf317b07039364e26422eb67853f39728a98',
}
ARTIFACT_FILES = {
    'run40/candidate/Infinity-1.0.9-Cobra-Full-Feature-Candidate-2.apk': '8ef45e9c54a79e2295e295ce1fcdd3430322a0049c7ff5227804c15aed6b4c57',
    'rollback2103152/background-candidate/Infinity-1.0.9-Cobra-Player-Reboot-Lock.apk': 'ff54c3f0c54fa73184319592c63be75df3e216121417789de8fcf250d93b92df',
    'rollback2103153/background-candidate/Infinity-1.0.9-Cobra-Guide-Player-Refinement.apk': 'dff23c9488ff38790ad116fe6fa0d93f68c7a788e4b78fcffc88a38e247088b6',
    'rollback2103153/ui-package/Infinity-Cobra-UI-1.3.8.zip': 'a3cc416ff8a98bf7fea6efc185cc02062656651f7d6dfdf0af973983145fd527',
}


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)


def sha(path: Path) -> str:
    with path.open('rb') as stream:
        digest = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def check_file(path: Path, expected: str) -> str:
    require(path.is_file() and not path.is_symlink(), f'Required regular file missing: {path}')
    actual = sha(path)
    require(actual == expected, f'Pinned input hash mismatch: {path}; expected {expected}, got {actual}')
    return actual


def validate_environment(env: dict[str, str]) -> None:
    # No default pin and no mutable branch fallback: omitted/empty inputs fail now.
    for key, expected in (('GITHUB_REPOSITORY', REPOSITORY), ('RUNTIME_COMMIT', RUNTIME), ('NDK_VER', NDK)):
        require(env.get(key) == expected, f'{key} must be exactly {expected}; missing or different build input')


def git(*args: str) -> bytes:
    return subprocess.check_output(['git', *args])


def save_json(path: str, value: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def inputs() -> None:
    import yaml
    validate_environment(dict(os.environ))
    require(git('rev-parse', 'HEAD').decode().strip() == BASE, 'Wrong reconstruction checkout')
    workflow = yaml.safe_load(git('show', REFINEMENT + ':.github/workflows/infinity-cobra-2103153-audited-build.yml'))
    for key, value in workflow['jobs']['android-update']['env'].items():
        require(os.environ.get(key) == str(value), f'Historical reconstruction environment missing/drifted: {key}')
    delta = Path('refinement-delta')
    require(delta.is_dir(), 'Separate candidate checkout missing')
    inherited = git('ls-tree', '-r', '--name-only', ADAPTIVE, '--',
                    'patches/cobra-2103153', 'tests/cobra_2103153',
                    'scripts/infinity_cobra_2103153_refinement.py',
                    'patches/cobra-2103154', 'tests/cobra_2103154',
                    'scripts/infinity_cobra_2103154_modes.py', 'scripts/cobra_2103154_ci.py').decode().splitlines()
    require(len(inherited) > 10, 'Incomplete immutable adaptive source inventory')
    for name in inherited:
        path = delta / name
        require(path.is_file(), f'Missing inherited input: {name}')
        require(path.read_bytes() == git('show', ADAPTIVE + ':' + name), f'Inherited source drift: {name}')
    for name in ('apply_epg_repair.py', 'guide-repair.java.inc', 'preimages.json',
                 'tests/run_tests.py', 'tests/run_short.py', 'tests/run_guards.py'):
        path = delta / 'repairs/cobra-epg-rc1' / name
        require(path.is_file(), f'Missing EPG repair input: {path}')
        require(path.read_bytes() == git('show', PRECHANGE + ':repairs/cobra-epg-rc1/' + name), f'EPG repair changed: {name}')
    for name, expected in RUNTIME_BLOBS.items():
        data = git('show', RUNTIME + ':scripts/' + name)
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        require(blob == expected, f'Unexpected pinned runtime blob: {name}')
        compile(data, name, 'exec')
    # Preserve the complete pre-change branch tree before any reconstruction changes.
    rollback = Path('pipeline-rollback'); rollback.mkdir(exist_ok=False)
    target = rollback / 'epg-repair-before-packaging-fix.zip'
    with target.open('wb') as stream:
        subprocess.run(['git', 'archive', '--format=zip', PRECHANGE], stdout=stream, check=True)
    (rollback / 'SHA256SUMS').write_text(sha(target) + '  ' + target.name + '\n')
    (rollback / 'README.txt').write_text(
        'Exact repository tree before this packaging-only fix: ' + PRECHANGE + '\n'
        'Device userdata is NOT included. This is source rollback, not an Android downgrade.\n')
    save_json('work/packaging-inputs.json', {'repository': REPOSITORY, 'base': BASE, 'runtime_commit': RUNTIME,
              'adaptive_commit': ADAPTIVE, 'prechange_commit': PRECHANGE, 'inherited_files_verified': len(inherited),
              'runtime_git_blobs': RUNTIME_BLOBS, 'native_rebuild_requested': False})
    print('PASS: explicit runtime environment, immutable sources and full pre-change source rollback')


def artifacts() -> None:
    verified = {name: check_file(Path(name), expected) for name, expected in ARTIFACT_FILES.items()}
    save_json('work/packaging-artifacts.json', {'sha256': verified})
    print('PASS: exact run40, 2103152, 2103153 APKs and protected UI hashes verified before reconstruction')


def validate_ui(addon: bytes, ui_bytes: bytes, theme_bytes: bytes) -> dict:
    meta = ET.fromstring(addon)
    ui = json.loads(ui_bytes)
    theme = json.loads(theme_bytes)
    require(meta.get('id') == ADDON and meta.get('version') == '1.3.9', 'Wrong matching UI addon identity/version')
    require(ui.get('schema') == 1 and ui.get('version') == '1.3.9', 'Wrong UI contract version')
    require(ui.get('runtime', {}).get('minimum_runtime') == 3, 'Wrong Cobra UI runtime')
    require(ui['runtime'].get('minimum_build') == 2103154, 'UI must retain the exact 2103154 minimum build')
    require(theme.get('schema') == 2, 'Wrong theme token schema')
    require(ui.get('presentation', {}).get('adaptive_mode_layouts') is True, 'Adaptive UI contract missing')
    modes = ui['views']['tv_guide']['view_modes']
    require(modes == {'grid': 'broadcast_duration_timeline_all_orientations',
                     'compact': 'dense_channel_directory', 'cards': 'responsive_channel_identity_wall',
                     'focus': 'watch_first_channel_or_schedule_queue'}, 'Matching five-mode contract drift')
    require(ui['views']['mobile'].get('renderer') == 'touch_dashboard', 'Mobile renderer contract missing')
    return ui


def package_ui(root: Path, output: Path) -> dict:
    # Use the fully promoted addon, never the earlier candidate/ historical theme ZIP.
    files = [p for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc']
    require(bool(files), 'Matching UI source missing')
    for path in files:
        require(not path.is_symlink(), f'Unexpected UI symlink: {path}')
        require(path.suffix.lower() not in ('.apk', '.dex', '.so', '.jks', '.keystore'), f'Unexpected UI payload: {path}')
    validate_ui((root/'addon.xml').read_bytes(), (root/'resources/cobra-ui.json').read_bytes(), (root/'resources/cobra-theme.json').read_bytes())
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'x', zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, ADDON + '/' + path.relative_to(root).as_posix())
    with zipfile.ZipFile(output) as archive:
        require(archive.testzip() is None, 'UI ZIP failed CRC verification')
        require(len(archive.namelist()) == len(set(archive.namelist())), 'Duplicate UI ZIP entries')
        for path in files:
            require(archive.read(ADDON + '/' + path.relative_to(root).as_posix()) == path.read_bytes(), 'UI ZIP source mismatch')
        validate_ui(*(archive.read(ADDON + '/' + name) for name in ('addon.xml','resources/cobra-ui.json','resources/cobra-theme.json')))
    output.with_suffix('.zip.sha256').write_text(sha(output) + '  ' + output.name + '\n')
    return {'version': '1.3.9', 'minimum_build': 2103154, 'tested_candidate_build': 2103155,
            'sha256': sha(output), 'files': len(files), 'content_matches_promoted_source': True,
            'device_visual_acceptance': False}


def ui() -> None:
    report = package_ui(Path('addons') / ADDON, Path('ui-package/Infinity-Cobra-UI-1.3.9.zip'))
    save_json('work/matching-ui.json', report)
    print('PASS: matching UI 1.3.9 ZIP verified; old reconstruction theme excluded from delivery')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('inputs', 'artifacts', 'ui'))
    args = parser.parse_args()
    {'inputs': inputs, 'artifacts': artifacts, 'ui': ui}[args.phase]()
