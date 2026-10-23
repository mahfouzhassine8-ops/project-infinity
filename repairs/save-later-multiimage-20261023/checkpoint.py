"""Record exact experimental source deltas, never an APK/release acceptance."""
import argparse
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native-delta',type=Path,required=True)
    p.add_argument('--component-delta',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    native=json.loads(a.native_delta.read_text());components=json.loads(a.component_delta.read_text())
    tests={name:json.loads((HERE/'qualification'/name).read_text()) for name in
           ('HOST-NATIVE-BASELINE.json','HOST-NATIVE-CANDIDATE.json','HOST-NAVIGATION.json')}
    if not all(value['passed'] for value in tests.values()):raise RuntimeError('Host tests failed')
    for value in native.values():value['test_result']='PASS: 32 candidate production-source host cases; Android/Fold PENDING'
    for value in components.values():value['test_result']='PASS: 12 navigation host test methods with mocked directory responses; actual provider/Android/Fold PENDING'
    owned={}
    for path in sorted(HERE.rglob('*')):
        if not path.is_file() or '__pycache__' in path.parts or path.resolve()==a.out.resolve():continue
        owned[path.relative_to(ROOT).as_posix()]=dict(original_sha256=None,
             final_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
             defect='Two authorized corrective areas; isolated experimental implementation and evidence',
             justification='New task-local source/host test/provenance only; does not alter an installed application',
             test_result='Host checkpoint only; not an accepted integrated build')
    result=dict(schema=1,base_commit='8df2e26f481eb7ff2d791c8cab39548de949d030',
        parent_apk_sha256='4c3e465eb78ebbba14df02b810b1851188dc8fbcb20fe17b4cc41f84dc824879',
        state='EXPERIMENTAL CHECKPOINT; NOT RELEASE READY',repository_added_files=owned,
        proposed_native_overlay=native,proposed_component_overlay=components,
        applied_to_installed_app=False,apk_built_or_signed=False,apk_member_delta=None,
        exact_installed_pov_source_verified=False,original_physical_exception_reproduced=False,
        real_provider_runtime_verified=False,android17_verified=False,physical_fold_verified=False,
        cobra_modified=False,source_binding_and_deployment_review_pending=True,
        checkpoint_inventory_self_hash='Anchored by repository commit; excluded from recursive self-inventory')
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')


if __name__=='__main__':main()
