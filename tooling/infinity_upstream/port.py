#!/usr/bin/env python3
"""Source-only Infinity port lab. Never builds, signs, installs or pushes an APK.

Generate patches on the EXACT old Kodi base using the EXACT shipped RC3 recipe.
Replay those patches (not old search/replace scripts) on a verified upstream tag.
Every checkout is disposable. Textual replay is NOT a compatibility certificate.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def command(argv, cwd=None, check=True, env=None):
    result = subprocess.run([str(x) for x in argv], cwd=cwd, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=900)
    if check and result.returncode:
        raise RuntimeError('Command failed: ' + ' '.join(map(str, argv)) + '\n' +
                           result.stderr.decode('utf-8', errors='replace')[-6000:])
    return result


def git(root: Path, *args, check=True) -> bytes:
    return command(['git', '-c', 'core.hooksPath=/dev/null', '-c', 'commit.gpgsign=false',
                    *args], cwd=root, check=check).stdout


def revision(root: Path, ref='HEAD') -> str:
    return git(root, 'rev-parse', '--verify', ref).decode().strip()


def changed_paths(root: Path, old: str, new: str) -> list[str]:
    # No REST compare-files cap. Renames deliberately appear as D+A, retaining both paths.
    raw = git(root, 'diff', '--name-only', '--no-renames', '-z', old, new, '--')
    return sorted(set(x.decode('utf-8', errors='strict') for x in raw.split(b'\0') if x))


def safe_new_directory(path: Path) -> Path:
    path = path.resolve()
    require(not path.exists(), 'Refusing to reuse/erase existing workspace: ' + str(path))
    path.mkdir(parents=True)
    (path / 'SOURCE_ONLY_SANDBOX').write_text('No build/install/push permissions.\n')
    return path


def clone_at(url: str, sha: str, dest: Path) -> None:
    require(re.fullmatch(r'[0-9a-f]{40}', sha) is not None, 'Invalid full commit SHA')
    dest.mkdir()
    git(dest, 'init', '-q')
    git(dest, 'remote', 'add', 'origin', url)
    git(dest, 'fetch', '--no-tags', '--depth=1', 'origin', sha)
    git(dest, 'checkout', '--detach', '-q', 'FETCH_HEAD')
    require(revision(dest) == sha, 'Checkout identity mismatch')
    git(dest, 'config', 'user.name', 'Infinity source port lab')
    git(dest, 'config', 'user.email', 'infinity-port-lab@users.noreply.github.com')


def classify(path: str) -> str:
    if path.startswith(('tools/android/', 'cmake/platform/android/', 'cmake/scripts/android/')):
        return 'android-runtime-and-packaging'
    if path.startswith(('xbmc/', 'lib/')):
        return 'native-engine-delta'
    if path.startswith(('tools/depends/', 'cmake/')) or path in ('CMakeLists.txt', 'version.txt'):
        return 'build-and-dependencies'
    if path.startswith(('media/', 'addons/', 'system/', 'userdata/')):
        return 'bundled-resources-not-external-skin-lock'
    return 'other-source-review-required'


def risk_domains(paths: list[str]) -> list[str]:
    prefixes = {
        'android-lifecycle-manifest-jni': ('tools/android/', 'xbmc/platform/android/', 'cmake/platform/android/'),
        'toolchain-and-dependencies': ('tools/depends/', 'cmake/', 'CMakeLists.txt'),
        'renderer-font-cache': ('xbmc/guilib/', 'xbmc/rendering/', 'xbmc/windowing/'),
        'player-audio-video': ('xbmc/cores/', 'xbmc/application/ApplicationPlayer'),
        'skin-window-input-contract': ('xbmc/input/', 'xbmc/windows/', 'addons/xbmc.gui/'),
        'python-and-binary-addons': ('xbmc/interfaces/python/', 'xbmc/addons/', 'addons/xbmc.python/'),
        'database-profile-migration': ('xbmc/dbwrappers/', 'xbmc/profiles/', 'xbmc/video/VideoDatabase', 'xbmc/music/MusicDatabase'),
        'upstream-version': ('version.txt',),
    }
    return [domain for domain, starts in prefixes.items() if any(p.startswith(starts) for p in paths)]


def checkpoint(source: Path, label: str, patches: Path) -> dict:
    before = revision(source)
    git(source, 'add', '-A', '--', '.')
    require(bool(git(source, 'diff', '--cached', '--name-only')), 'Empty recipe stage: ' + label)
    git(source, 'commit', '-q', '-m', label)
    after = revision(source)
    patch = patches / (label + '.patch')
    patch.write_bytes(git(source, 'diff', '--binary', '--full-index', before, after, '--'))
    paths = changed_paths(source, before, after)
    return {'stage': label, 'before': before, 'after': after, 'patch': patch.name,
            'sha256': digest(patch), 'paths': paths}


def invoke_recipe(recipe: Path, source: Path, out: Path) -> list[dict]:
    """Same source transforms/order as the shipped RC3 workflow, without compilation.

    The pinned recipe checkout itself is disposable: its RC2/RC3 wrappers also
    change local packager metadata. Nothing is copied back to the real repository.
    """
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    patches = out / 'patches'; patches.mkdir()
    receipts = out / 'receipts'; receipts.mkdir()
    stages = []
    def run(script, *args):
        result = command([sys.executable, recipe/'scripts'/script, *args], cwd=recipe, env=env)
        with (out/'recipe.log').open('ab') as log:
            log.write((script+'\n').encode()+result.stdout+result.stderr)
    def save(name):
        stages.append(checkpoint(source, name, patches))

    run('infinity_audio_policy_source.py', source, '--receipts', receipts/'audio')
    # Exact extra refresh-controller verification used by the accepted preflight.
    spec = importlib.util.spec_from_file_location('infinity_refresh_recipe', recipe/'scripts/infinity-responsive-v5.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    module.install_refresh_controller(source); module.verify_refresh_controller(source)
    save('01-cumulative-audited-native-audio-responsive')
    run('infinity_1_0_8_deep_rebrand_preimage.py', '--source', source)
    run('infinity_1_0_8_deep_audio_rebrand.py', 'source', '--source', source, '--receipt', receipts/'branding.json')
    run('infinity_1_0_8_deep_audio_rebrand.py', 'verify-source', '--source', source)
    save('02-android-branding')
    run('infinity_player_rotation.py', 'apply', '--source', source, '--receipt', receipts/'rotation.json')
    run('infinity_player_rotation.py', 'verify', '--source', source)
    save('03-player-rotation')
    run('infinity_1_0_9_live_release.py', 'source', '--source', source, '--receipt', receipts/'live.json')
    run('infinity_touch_startup_guard.py', 'apply', '--source', source, '--receipt', receipts/'touch.json')
    run('infinity_touch_startup_guard.py', 'verify', '--source', source)
    save('04-live-identity-and-touch-startup-guard')
    run('infinity_1_0_9_cobra_full_runner.py', 'source', '--source', source, '--receipt', receipts/'cobra.json')
    run('infinity_1_0_9_cobra_full_runner.py', 'verify-source', '--source', source)
    save('05-cobra-full-feature-device-parity')
    run('infinity_background_resume.py', '--source', source, '--receipt', receipts/'background.json')
    save('06-background-resume-service')
    run('infinity_background_control_bridge.py', '--source', source, '--receipt', receipts/'background.json',
        '--packager', recipe/'scripts/package_background_resume.py')
    save('07-infinity-normal-extended-control')
    # Exact predecessor input required by the existing RC3 regression harness.
    previous = out/'rc2-before'
    for relative in ('tools/android/packaging/xbmc', 'cmake/scripts/android'):
        shutil.copytree(source/relative, previous/relative)
    run('infinity_async_lifecycle_repair.py', '--source', source, '--receipt', receipts/'background.json')
    save('08-rc3-late-callback-lifecycle-repair')
    test = command([sys.executable, recipe/'tests/infinity_background/test_async_lifecycle.py',
                    '--before', previous, '--after', source, '--out', out/'rc3-host-tests'], cwd=recipe, env=env)
    (out/'rc3-host-tests.log').write_bytes(test.stdout+test.stderr)
    return stages


def replay(source: Path, target: str, stages: list[dict], out: Path) -> dict:
    """Replay a linear series. Stop at FIRST conflict; never ours/theirs over it."""
    candidate = source.parent/'candidate'
    git(source, 'worktree', 'add', '--detach', str(candidate), target)
    results = []
    for row in stages:
        patch = out/'patches'/row['patch']
        require(digest(patch) == row['sha256'], 'Patch integrity mismatch')
        process = command(['git', '-c', 'core.hooksPath=/dev/null', 'apply', '--3way', '--index', str(patch)],
                          cwd=candidate, check=False)
        (out/('replay-'+row['stage']+'.log')).write_bytes(process.stdout+process.stderr)
        if process.returncode:
            conflicts = git(candidate, 'diff', '--name-only', '--diff-filter=U', '-z').split(b'\0')
            results.append({'stage': row['stage'], 'result': 'conflict',
                            'conflict_files': [p.decode() for p in conflicts if p]})
            # No candidate source ZIP on conflict. Preserve reject diagnostics only.
            return {'result': 'blocked_on_conflict', 'stages': results,
                    'remaining_stages': [s['stage'] for s in stages[len(results):]],
                    'build_allowed': False}
        git(candidate, 'commit', '--allow-empty', '-q', '-m', 'PORT ONLY: '+row['stage'])
        results.append({'stage': row['stage'], 'result': 'textual_replay_only'})
    tree = revision(candidate, 'HEAD^{tree}')
    # Source archive only; no APK contents or build invocation. Keep .github code inert in ZIP.
    (out/'candidate-source.zip').write_bytes(git(candidate, 'archive', '--format=zip', 'HEAD'))
    return {'result': 'textual_replay_complete_review_required', 'stages': results,
            'candidate_tree': tree, 'candidate_source_sha256': digest(out/'candidate-source.zip'),
            'build_allowed': False, 'runtime_tested': False}


def analyze(baseline: dict, target: dict, workspace: Path, out: Path, selftest=False) -> dict:
    require(re.fullmatch(r'[0-9a-f]{40}', target['commit']) is not None, 'Target needs verified full SHA')
    workspace = safe_new_directory(workspace)
    out = out.resolve(); out.mkdir(parents=True, exist_ok=True)
    recipe = workspace/'recipe'
    source = workspace/'kodi'
    clone_at('https://github.com/'+baseline['runtime']['repository']+'.git',
             baseline['runtime']['source_commit'], recipe)
    clone_at('https://github.com/xbmc/xbmc.git', baseline['upstream']['commit'], source)
    stages = invoke_recipe(recipe, source, out)
    # Independent golden hashes from the ACTUALLY shipped RC3 build artifact.
    for path, expected in baseline['runtime']['source_receipt_sha256'].items():
        require(digest(source/path) == expected, 'RC3 source reconstruction drift: '+path)
    owned = changed_paths(source, baseline['upstream']['commit'], 'HEAD')
    inventory = {p: {'owner': classify(p), 'sha256': digest(source/p) if (source/p).is_file() else None,
                     'stages': [r['stage'] for r in stages if p in r['paths']]}
                 for p in owned}
    write_json(out/'ownership.json', inventory)
    write_json(out/'patch-series.json', stages)
    old_tree = revision(source, 'HEAD^{tree}')
    if target['commit'] != baseline['upstream']['commit']:
        git(source, 'fetch', '--no-tags', '--depth=1', 'origin', target['commit'])
        require(revision(source, 'FETCH_HEAD') == target['commit'], 'Fetched target changed')
    upstream_changed = changed_paths(source, baseline['upstream']['commit'], target['commit'])
    report = {'schema': 1, 'baseline_id': baseline['id'], 'runtime_source_commit': baseline['runtime']['source_commit'],
              'upstream_base': baseline['upstream'], 'target': target, 'upstream_changed_files': upstream_changed,
              'upstream_changed_count': len(upstream_changed), 'owned_files': len(owned),
              'direct_overlap': sorted(set(owned)&set(upstream_changed)), 'risk_domains': risk_domains(upstream_changed),
              'rc3_golden_source_checks': 'passed', 'existing_rc3_lifecycle_host_tests': 'passed',
              'native_compiled': False, 'skin_modified': False, 'apk_created': False,
              'production_modified': False, 'required_device_gates': baseline['device_acceptance']}
    report['replay'] = replay(source, target['commit'], stages, out)
    if selftest:
        require(target['commit'] == baseline['upstream']['commit'], 'Selftest must use exact baseline')
        require(report['replay'].get('candidate_tree') == old_tree, 'Same-base patch replay changed source tree')
        report['same_base_tree_roundtrip'] = 'passed'
    report['gate'] = 'BLOCKED: release-specific build adapter and device acceptance not approved'
    write_json(out/'impact.json', report)
    lines = ['# Infinity Kodi upstream impact report', '',
             '**Source analysis only. No APK built, installed or promoted.**', '',
             '- Target: `'+target['tag']+'` / `'+target['commit']+'`',
             '- Base: `'+baseline['upstream']['tag']+'`',
             '- Upstream files changed: '+str(len(upstream_changed)),
             '- Files with direct Infinity overlap: '+str(len(report['direct_overlap'])),
             '- Patch replay: '+report['replay']['result'],
             '- Build gate: **BLOCKED pending reviewed release adapter**', '',
             'A clean Git patch is not proof that JNI, Python, skin, binary add-ons or playback are compatible.', '',
             '## Review domains', *('- '+d for d in report['risk_domains']), '',
             '## Direct overlap', *('- `'+p+'`' for p in report['direct_overlap']), '',
             '## Protected working stack', 'Skin 1.0.5.141 + Health Center 2.5.6 + exact shipped RC3.',
             'No old-engine hash equality is expected for a real NEW engine. Build and verify it separately.', '']
    (out/'SUMMARY.md').write_text('\n'.join(lines))
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline', type=Path, default=HERE/'baseline.json')
    p.add_argument('--target-file', type=Path)
    p.add_argument('--selftest', action='store_true')
    p.add_argument('--workspace', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    baseline = json.loads(a.baseline.read_text())
    if a.selftest:
        target = dict(baseline['upstream'])
    else:
        require(a.target_file is not None, 'Resolve target through watch.py first')
        target = json.loads(a.target_file.read_text())
        # Re-resolve immediately to reject tag movement between discovery and replay.
        from watch import resolve_target
        resolved = resolve_target(target['tag'], allow_prerelease=target.get('prerelease') is True)
        require(resolved['commit'] == target['commit'], 'Upstream tag moved: manual investigation required')
    analyze(baseline, target, a.workspace, a.out, a.selftest)


if __name__ == '__main__':
    main()
