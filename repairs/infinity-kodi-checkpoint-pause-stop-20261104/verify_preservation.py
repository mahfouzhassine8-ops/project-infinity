#!/usr/bin/env python3
"""Read-only source/recovery preservation comparison, not application execution."""
from pathlib import Path
import hashlib
import json
import subprocess
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
NATIVE = Path('/tmp/kodi451-restored-native')
PROOF = Path('/tmp/kodi451-restored-proof')
MAP = PROOF / 'CANDIDATE-NATIVE-SOURCE-MAP.json'


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def main():
    parent = json.loads(MAP.read_text())
    baseline = json.loads((PROOF / 'BASELINE-NATIVE-SOURCE-MAP.json').read_text())
    mismatches = [name for name, digest in parent.items() if sha(NATIVE / name) != digest]
    assert not mismatches, mismatches
    overlay = {str(path.relative_to(HERE / 'candidate')): sha(path)
               for path in (HERE / 'candidate').rglob('*') if path.is_file()}
    delta = json.loads((HERE / 'SOURCE-DELTA.json').read_text())
    assert overlay == delta['after']
    assert {name: parent[name] for name in overlay} == delta['before']
    previous = {name: {'signed451_source': baseline.get(name), 'retained452_source': parent.get(name)}
                for name in sorted(set(baseline) | set(parent)) if baseline.get(name) != parent.get(name)}
    main_repo = Path('/workspace/project-infinity')
    original_status = json.loads((HERE / 'SELECTED-TESTS.json').read_text())['main_status']
    main_status = subprocess.check_output(['git', 'status', '--short'], cwd=main_repo, text=True)
    assert main_status == original_status
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=main_repo, text=True).strip() == '8b25b7d425e644d5af559580665d2499c61814b9'
    prior_worktrees = {}
    for directory, expected in [
        ('/tmp/infinity-settings-diagnostic-20261104', '7ea3f0b99f553e2a788ed520a9f0628783f23b6a'),
        ('/tmp/infinity-settings-retirement-proof-20261104', '8c54e2cf3bbe98ec4512721802d1011a73c82eb2'),
        ('/tmp/infinity-settings-retirement-final-proof-20261104', 'cdbaa5abc86675094229171746a8c627a7f367e8'),
    ]:
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=directory, text=True).strip()
        status = subprocess.check_output(['git', 'status', '--short'], cwd=directory, text=True)
        assert head == expected and not status, (directory, head, status)
        prior_worktrees[directory] = {'head': head, 'clean': True}
    apks = {}
    for name, digest in [
        ('/tmp/kodi451-signed-baseline/Infinity-2103451-Combined-Original-Signer.apk',
         'd77c31c458c4571212022bea7cea1e76c1d415cd5792b780b3c655fba97c6399'),
        ('/tmp/kodi452-published-signed/Infinity-2103452-Combined-Original-Signer.apk',
         'efc24cc53e25675360bb70a2c8c0122cfc107f99035d04c957265d08206f6729'),
    ]:
        actual = sha(Path(name))
        assert actual == digest, name
        apks[name] = actual
    result = {
        'checked_utc': datetime.now(timezone.utc).isoformat(),
        'native_mapped_files': len(parent), 'native_tree_mismatches': mismatches,
        'native_parent_map_sha256': sha(MAP),
        'new_source_overlay': overlay,
        'previous_452_vs_451_changes_retained_not_reapproved': previous,
        'main_worktree_status_unchanged': True,
        'prior_checkpoints': prior_worktrees, 'signed_apks_unchanged': apks,
        'new_engine_or_apk': None,
        'new_apk_member_comparison': 'NOT APPLICABLE: source-only; no candidate APK created',
        'retirement': 'BLOCKED decision at cdbaa5ab preserved; no retirement source/test changes',
    }
    (HERE / 'PRESERVATION.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'mapped_files_unchanged': len(parent), 'overlay_files': list(overlay),
                      'previous_changes_retained': list(previous), 'signed_apks_unchanged': True,
                      'prior_worktrees_unchanged': True}, indent=2))


if __name__ == '__main__':
    main()
