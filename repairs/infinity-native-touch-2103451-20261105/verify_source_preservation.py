"""Read-only comparison of isolated touch source and protected parent sources."""
from pathlib import Path
import hashlib
import json
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PARENT='55c993e31709f317bf1f31acf460f5641bc31420'
NATIVE=Path('/tmp/infinity-native-touch-2103451')
MAP=Path('/tmp/kodi451-restored-proof/BASELINE-NATIVE-SOURCE-MAP.json')
sha=lambda data:hashlib.sha256(data).hexdigest()

def main():
    assert sha(MAP.read_bytes())=='20f901cf5780aebff6eff45e4f21248904f8a8ff72d4acdcd5ea72e783c829c3'
    expected=json.loads(MAP.read_text())
    applied=json.loads((HERE/'APPLIED-SOURCE-DELTA.json').read_text())
    actual={p.relative_to(NATIVE).as_posix():sha(p.read_bytes()) for p in NATIVE.rglob('*') if p.is_file()}
    assert actual.keys()==expected.keys()
    delta={n for n in actual if actual[n]!=expected[n]}
    assert delta==set(applied['changed_files']) and len(delta)==2
    for name in delta:assert actual[name]==sha((HERE/'native'/name).read_bytes())==applied['changed_files'][name]['after_sha256']
    original=Path('/tmp/kodi451-restored-native')
    prior=json.loads(Path('/tmp/kodi451-restored-proof/NATIVE-INTEGRATION.json').read_text())
    original_map={p.relative_to(original).as_posix():sha(p.read_bytes()) for p in original.rglob('*') if p.is_file()}
    assert original_map==dict(expected,**prior['after'])
    parent_files=subprocess.check_output(['git','ls-tree','-r','--name-only',PARENT,'repairs/infinity-master-corrective-20261105'],cwd=ROOT,text=True).splitlines()
    protected={}
    for name in parent_files:
        p=ROOT/name
        assert p.read_bytes()==subprocess.check_output(['git','show',PARENT+':'+name],cwd=ROOT)
        protected[name]=sha(p.read_bytes())
    changed=subprocess.check_output(['git','diff','--name-only',PARENT,'HEAD'],cwd=ROOT,text=True).splitlines()
    assert all(n.startswith('repairs/infinity-native-touch-2103451-20261105/') or n=='.github/workflows/infinity-native-touch-451-objects.yml' for n in changed)
    report=dict(status='SOURCE_ONLY_NOT_APK_PRESERVATION',baseline=2103451,native_source_count=len(expected),changed_native_sources=sorted(delta),protected_native_sources_byte_identical=len(expected)-len(delta),existing_P0_workspace_unchanged=True,parent_master_source_and_evidence_files_preserved=len(protected),parent_checkpoint=PARENT,parent_source_hashes=protected,Search_acceptance='2 FAIL, retained without waiver',Android='NOT_RUN',APK_built=False,signing=False,installation=False,release_lock_changed=False)
    (HERE/'SOURCE-PRESERVATION.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='parent_source_hashes'},indent=2))

if __name__=='__main__':main()
