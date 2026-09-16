#!/usr/bin/env python3
"""Reconstruct pinned Infinity; export owned patches; replay into a DISPOSABLE tree.

Never changes a remote ref. Never builds, signs, installs, merges or publishes an
APK. A clean replay is only source preparation: a target-specific build adapter
and explicit review/device acceptance are required before any engine upgrade.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from watch import ROOT, SHA, UPSTREAM, read_official_tags, require, stable_version

WATCH_AREAS = {
    'android_lifecycle_manifest': ('tools/android/', 'xbmc/platform/android/', 'xbmc/platform/posix/'),
    'toolchain_dependencies_abi': ('tools/depends/', 'cmake/', 'CMakeLists.txt', 'version.txt'),
    'renderer_fonts_graphics': ('xbmc/guilib/', 'xbmc/rendering/', 'xbmc/windowing/'),
    'playback_audio': ('xbmc/cores/', 'xbmc/application/'),
    'skin_python_addon_api': ('xbmc/addons/', 'xbmc/interfaces/', 'xbmc/GUIInfoManager', 'addons/'),
    'remote_touch_input': ('xbmc/input/', 'system/keymaps/'),
    'userdata_migration': ('xbmc/dbwrappers/', 'xbmc/video/VideoDatabase', 'xbmc/music/MusicDatabase'),
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def command(args, cwd=None, check=True):
    # The pinned source transforms have no need for API/signing credentials.
    env = {k: v for k, v in os.environ.items()
           if k not in ('GH_TOKEN', 'GITHUB_TOKEN') and not k.startswith('INFINITY_')}
    env.update({'GIT_TERMINAL_PROMPT': '0', 'GIT_AUTHOR_NAME': 'Infinity Source Audit',
                'GIT_AUTHOR_EMAIL': 'source-audit@invalid',
                'GIT_COMMITTER_NAME': 'Infinity Source Audit',
                'GIT_COMMITTER_EMAIL': 'source-audit@invalid',
                'GIT_AUTHOR_DATE': '2000-01-01T00:00:00Z',
                'GIT_COMMITTER_DATE': '2000-01-01T00:00:00Z'})
    p = subprocess.run([str(a) for a in args], cwd=cwd, env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600)
    if check and p.returncode:
        raise RuntimeError('Command failed (%s): %s\n%s' % (
            p.returncode, ' '.join(str(x) for x in args[:4]),
            p.stderr.decode('utf-8', 'replace')[-4000:]))
    return p


def git(repo, *args, check=True):
    return command(['git', '-c', 'core.hooksPath=/dev/null', '-c', 'commit.gpgSign=false',
                    '-c', 'diff.external=', '-C', repo, *args], check=check)


def text(repo, *args):
    return git(repo, *args).stdout.decode().strip()


def classify(path):
    if path.startswith('tools/android/') or path.startswith('cmake/') or path in ('CMakeLists.txt', 'version.txt'):
        return 'android_runtime' if '/src/' in path else 'build_and_android_resources'
    if path.startswith('xbmc/'):
        return 'native_engine_delta'
    return 'assets_or_other_source_delta'


def diff_names(repo, before, after):
    # Full local diff, NOT the GitHub compare endpoint's file-list limits.
    raw = git(repo, 'diff', '--no-renames', '--name-only', '-z', before, after, '--').stdout
    return [s.decode('utf-8') for s in raw.split(b'\0') if s]


def file_at(repo, ref, name):
    p = git(repo, 'show', ref + ':' + name, check=False)
    return None if p.returncode else digest(p.stdout)


def impact_report(changed_upstream, owned):
    changed = set(changed_upstream)
    return {'changed_upstream_files': sorted(changed),
            'owned_file_intersections': sorted(changed.intersection(owned)),
            'watch_areas': {area: sorted(p for p in changed if any(p.startswith(prefix) for prefix in prefixes))
                            for area, prefixes in WATCH_AREAS.items()},
            'note': 'No direct file intersection does NOT prove semantic compatibility.'}


def snapshot(repo, phase, patches):
    # Include generated source/assets even if upstream .gitignore excludes them.
    # This is an isolated, credential-free source tree, not the user's checkout.
    git(repo, 'add', '-A', '-f', '--', '.')
    patch = git(repo, 'diff', '--cached', '--binary', '--full-index', '--no-ext-diff', '--no-renames').stdout
    if not patch:
        return {'name': phase, 'patch': None, 'files': []}
    filename = phase + '.patch'
    (patches/filename).write_bytes(patch)
    files = git(repo, 'diff', '--cached', '--name-only', '-z').stdout
    git(repo, 'commit', '--no-verify', '-m', 'Migration snapshot: ' + phase)
    return {'name': phase, 'patch': filename, 'sha256': digest(patch),
            'files': [p.decode() for p in files.split(b'\0') if p]}


def replay(repo, phases, patches, logs):
    results = []
    for phase in phases:
        if phase['patch'] is None:
            results.append({'phase': phase['name'], 'status': 'empty'})
            continue
        patch = patches/phase['patch']
        require(patch.parent.resolve() == patches.resolve(), 'Unsafe patch path')
        require(digest(patch.read_bytes()) == phase['sha256'], 'Patch content does not match manifest')
        process = git(repo, 'apply', '--3way', '--index', '--whitespace=nowarn', patch, check=False)
        (logs/(phase['name']+'.txt')).write_bytes(process.stdout + process.stderr)
        if process.returncode:
            conflicts = git(repo, 'diff', '--name-only', '--diff-filter=U', '-z').stdout
            results.append({'phase': phase['name'], 'status': 'conflict_or_rejected',
                            'conflicts': [n.decode() for n in conflicts.split(b'\0') if n],
                            'details': 'See phase log. Later dependent phases were NOT applied.'})
            return results, False
        # Empty tree after applying an already-upstream change is acceptable, but no
        # claim is made that it is semantically identical to the required feature.
        if git(repo, 'diff', '--cached', '--quiet', check=False).returncode:
            git(repo, 'commit', '--no-verify', '-m', 'Source-only replay: ' + phase['name'])
        results.append({'phase': phase['name'], 'status': 'applied'})
    return results, True


def ensure_recipe(recipe_root, baseline):
    expected = baseline['runtime']['source_commit']
    require(text(recipe_root, 'rev-parse', 'HEAD') == expected, 'Wrong Infinity source lineage')
    require(not text(recipe_root, 'status', '--porcelain'), 'Recipe checkout must be pristine')
    # The checkout is pinned to the exact delivered RC3 commit and must be clean.
    # Git object identity + a pristine worktree protects the complete tracked recipe
    # without maintaining a second 300+ file hash inventory that can drift separately.
    # These scripts run only on Kodi 21.3, never blindly on a future release with
    # preimage gates bypassed.


def reconstruct(recipe_root, source, evidence, baseline):
    phases = json.loads((ROOT/'recipe.json').read_text())['phases']
    values = {'source': str(source), 'evidence': str(evidence), 'recipe': str(recipe_root),
              'python': sys.executable}
    patchdir = evidence/'patches'; patchdir.mkdir()
    logs = evidence/'reconstruction'; logs.mkdir()
    receipts = evidence/'receipts'; receipts.mkdir()
    exported = []
    for phase in phases:
        args = [v.format_map(values) for v in phase['argv']]
        p = command(args, cwd=recipe_root, check=False)
        (logs/(phase['name']+'.txt')).write_bytes(p.stdout + p.stderr)
        require(p.returncode == 0, 'Pinned source reconstruction failed at ' + phase['name'] + '; see evidence log')
        row = snapshot(source, phase['name'], patchdir)
        row['reason'] = phase['reason']
        # Background/bridge/RC3 fixes must never change C++ during reconstruction.
        if phase.get('android_only'):
            require(all(not name.startswith('xbmc/') for name in row['files']),
                    'Unexpected native edit in Android-only phase')
        exported.append(row)
    expected_files = json.loads((ROOT/'rc3-source-checks.json').read_text())['files']
    for name, expected_hash in expected_files.items():
        require(digest((source/name).read_bytes()) == expected_hash, 'RC3 published source mismatch: ' + name)
    (evidence/'patch-series.json').write_text(json.dumps(exported, indent=2)+'\n')
    return exported


def review_gates():
    return {'automatic_build_allowed': False, 'automatic_install_allowed': False,
            'release_ready': False, 'native_compile': 'not_run', 'device_tests': 'not_run',
            'required_before_build': [
                'Review upstream changes, conflicts, toolchain/dependency/API changes and already-upstream patches',
                'Review and commit a target-specific native build recipe; do not reuse the RC3 APK repacker for a new Kodi engine',
                'Rebuild JNI/native/binary add-ons and Android resources as a coherent matched set',
                'Choose a separate test app/userdata profile or disposable TV/device; no in-place production database migration',
                'Allocate a forward versionCode and verify correct permanent signer without exposing keys to analysis'],
            'required_before_promotion': [
                'Build, JNI, manifest, ABI, signer, skin and companion compatibility checks',
                'RC3 lifecycle crash regression, Normal/Extended, playback/audio, PiP and Fold/rotation',
                'D-pad/remote-only TV pass, providers, System Hub, Power, Health Center and Start Fresh',
                'User acceptance and verified backup; database upgrades can prevent simple APK downgrade']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recipe-root', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--target-tag', default='21.3-Omega')
    parser.add_argument('--target-sha', default='')
    args = parser.parse_args()
    baseline = json.loads((ROOT/'baseline.json').read_text())
    require(stable_version(args.target_tag) is not None, 'Only stable Kodi source tags accepted')
    require(stable_version(args.target_tag) >= stable_version(baseline['upstream']['tag']), 'Downgrade target refused')
    require(not args.target_sha or SHA.fullmatch(args.target_sha), 'Malformed expected commit')
    recipe = args.recipe_root.resolve()
    workspace, output = args.workspace.resolve(), args.output.resolve()
    require(not workspace.exists(), 'Workspace must be a NEW disposable directory')
    require(not output.exists(), 'Output must be a NEW evidence directory')
    require(not workspace.is_relative_to(recipe) and not recipe.is_relative_to(workspace), 'Keep workspace separate from pinned recipe')
    require(not output.is_relative_to(recipe) and not output.is_relative_to(workspace), 'Keep evidence separate from source trees')
    ensure_recipe(recipe, baseline)
    tags = read_official_tags()
    base_sha = baseline['upstream']['commit']
    require(tags.get(baseline['upstream']['tag']) == base_sha, 'Pinned upstream tag changed')
    require(args.target_tag in tags, 'Tag is not in official xbmc/xbmc')
    target = tags[args.target_tag]
    require(not args.target_sha or target == args.target_sha, 'Target tag changed after detection; stopped')
    # Prerelease metadata check as well as name check, including manual analysis.
    from watch import API
    import urllib.parse
    release = API(os.environ.get('GH_TOKEN','')).request(
        '/repos/' + UPSTREAM + '/releases/tags/' + urllib.parse.quote(args.target_tag, safe=''), allow_404=True)
    require(release is None or (not release.get('draft') and not release.get('prerelease')), 'Not a stable published/source-tag target')
    workspace.mkdir(); output.mkdir()
    source = workspace/'original'; source.mkdir()
    git(source, 'init', '--quiet')
    git(source, 'fetch', '--depth=1', '--no-tags', 'https://github.com/'+UPSTREAM+'.git', base_sha)
    git(source, 'checkout', '--detach', 'FETCH_HEAD')
    require(text(source, 'rev-parse', 'HEAD') == base_sha, 'Wrong pristine Kodi commit')
    if target != base_sha:
        git(source, 'fetch', '--depth=1', '--no-tags', 'https://github.com/'+UPSTREAM+'.git', target)
    # Explicit SHA checkout; no commands from the downloaded new upstream are run.
    upstream_changes = diff_names(source, base_sha, target)
    phases = reconstruct(recipe, source, output, baseline)
    final_sha = text(source, 'rev-parse', 'HEAD')
    owned = diff_names(source, base_sha, final_sha)
    inventory = {name: {'layer': classify(name), 'before_sha256': file_at(source, base_sha, name),
                         'after_sha256': file_at(source, final_sha, name),
                         'phases': [p['name'] for p in phases if name in p['files']]} for name in owned}
    (output/'ownership-manifest.json').write_text(json.dumps(inventory, indent=2)+'\n')
    (output/'complete-infinity-delta.patch').write_bytes(
        git(source, 'diff', '--binary', '--full-index', '--no-ext-diff', '--no-renames', base_sha, final_sha).stdout)
    impact = impact_report(upstream_changes, owned)
    candidate = workspace/'candidate'
    git(source, 'worktree', 'add', '--detach', candidate, target)
    logs = output/'replay'; logs.mkdir()
    results, clean = replay(candidate, phases, output/'patches', logs)
    if clean:
        (output/'candidate-delta.patch').write_bytes(git(candidate, 'diff', '--binary', '--full-index',
            '--no-ext-diff', '--no-renames', target, 'HEAD').stdout)
    same_base = target == base_sha
    roundtrip = clean and same_base and text(source, 'rev-parse', 'HEAD^{tree}') == text(candidate, 'rev-parse', 'HEAD^{tree}')
    if same_base:
        require(roundtrip, 'Same-base replay failed exact tree equivalence')
    report = {'schema': 1, 'baseline': baseline, 'target': {'tag': args.target_tag, 'commit': target},
              'impact': impact, 'owned_files': len(owned), 'phases': results,
              'replay_clean': clean, 'same_base_self_test': same_base,
              'same_base_exact_tree_match': roundtrip if same_base else None,
              'status': 'source_prepared_review_required' if clean else 'blocked_source_conflicts',
              'gates': review_gates(), 'production_modified': False,
              'caveat': 'Local patch applicability is not a successful compile or proof of runtime compatibility.'}
    (output/'port-report.json').write_text(json.dumps(report, indent=2)+'\n')
    summary = (f"# Infinity Kodi port analysis\n\n**{report['status']}**\n\n"
               f"Base: {baseline['upstream']['tag']}; target: {args.target_tag} (`{target}`).\n\n"
               f"{len(upstream_changes)} upstream changed files; {len(owned)} Infinity-owned files; "
               f"{len(impact['owned_file_intersections'])} direct intersections.\n\n"
               f"Replay clean: {clean}. Same-base exact-tree check: {report['same_base_exact_tree_match']}.\n\n"
               "**No APK compiled, signed, installed or promoted. Production remains untouched.**\n\n"
               "Review `port-report.json`, `ownership-manifest.json`, phase logs and patches. "
               "A reviewed target build recipe and device acceptance are still required.\n")
    (output/'SUMMARY.md').write_text(summary)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        Path(os.environ['GITHUB_STEP_SUMMARY']).write_text(summary)
    # A shallow Git bundle is not necessarily independently cloneable. Export a
    # complete source archive instead; regeneration of the patch object graph
    # uses the pinned recipe and official base again, without expired CI artifacts.
    if clean:
        git(candidate, 'archive', '--format=tar.gz',
            '--output=' + str(output/'candidate-source-NOT-AN-APK.tar.gz'), 'HEAD')
    hashes = {p.relative_to(output).as_posix(): digest(p.read_bytes()) for p in output.rglob('*') if p.is_file()}
    (output/'SHA256SUMS.json').write_text(json.dumps(hashes, indent=2)+'\n')
    print(summary)


if __name__ == '__main__':
    main()
