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
        if ':' not in source:
            source = '9ce852ebb044a82853ef93af24e34a07ed96daff:' + source
        before = subprocess.check_output(['git', 'show', source], cwd=ROOT)
        assert hashlib.sha256(before).hexdigest() == row['baseline_sha256'], source
        after = (ROOT / row['path']).read_bytes()
        evidence.append(dict(path=row['path'], before=row['baseline_sha256'], after=hashlib.sha256(after).hexdigest()))
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
