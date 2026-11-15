"""Selected500 source gate; never modifies or reads an installed profile."""
from pathlib import Path
import ast
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ANCESTOR = '5cdb593ae1f78d2e4565c1576e6f15a6d7a8f81d'


def main():
    scope = json.loads((HERE / 'SCOPE.json').read_bytes())
    allowed = {row['path'] for row in scope['production_allowlist']}
    changed = subprocess.check_output(['git', 'diff', '--name-only', ANCESTOR], cwd=ROOT, text=True).splitlines()
    prefix = HERE.relative_to(ROOT).as_posix() + '/'
    workflows = {'.github/workflows/infinity-500-focused-verification.yml',
                 '.github/workflows/infinity-500-native-integration.yml',
                 '.github/workflows/infinity-500-native-bridge.yml'}
    assert all(name in allowed or name.startswith(prefix) or name in workflows for name in changed), changed
    evidence = []
    for row in scope['production_allowlist']:
        source = row['baseline_source']
        if source == 'NEW_AUTHORIZED_SILENT_POLICY_HEADER':
            assert row['baseline_sha256'] is None
            assert row['native_path'] == 'xbmc/interfaces/legacy/InfinityPromotionalDialog.h'
        elif source.startswith('authenticated500-native:'):
            name = source.split(':', 1)[1]
            before = (HERE / 'native/baseline' / name).read_bytes()
            assert hashlib.sha256(before).hexdigest() == row['baseline_sha256'], source
            # Full map equality is checked again against the authenticated
            # native producer artifact by build_native.py before mutation.
        else:
            if ':' not in source:
                source = '9ce852ebb044a82853ef93af24e34a07ed96daff:' + source
            before = subprocess.check_output(['git', 'show', source], cwd=ROOT)
            assert hashlib.sha256(before).hexdigest() == row['baseline_sha256'], source
        after = (ROOT / row['path']).read_bytes()
        evidence.append(dict(path=row['path'], before=row['baseline_sha256'], after=hashlib.sha256(after).hexdigest()))
    review = json.loads((HERE / 'SILENT-PROMOTION-REVIEW.json').read_text())
    assert review['status'] == 'PASS_SOURCE_AND_HOST_RECEIPT_REVIEW_NOT_APPLICATION_ACCEPTANCE'
    for name, digest in review['files'].items():
        assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest, 'Policy source no longer matches independent review'
    # The embedded Python source must compile before any native build consumes it.
    header = (HERE / 'native/overlay/xbmc/interfaces/python/InfinityPythonPersistenceSource.h').read_bytes()
    source = header.split(b'R"infinity_source(', 1)[1].rsplit(b')infinity_source";', 1)[0]
    compile(source, '<candidate embedded observer>', 'exec')
    result = dict(status='PASS_SELECTED_SOURCE_SCOPE', baseline=2103500, production=evidence,
                  Cobra='UNCHANGED', original_APK='NOT_MODIFIED', user_data='NOT_ACCESSED',
                  APK_preservation='NOT_YET_PACKAGED', owner_acceptance='NOT_CLAIMED')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
