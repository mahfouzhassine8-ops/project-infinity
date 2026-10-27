"""Create the scoped bootstrap candidate after concrete boundary proofs exist.

This never changes accepted-combined-release.json and is not an acceptance or
general owner-approval command. Later proposals must pass transition() against
the previous remote authority and select exact immutable component bundles.
"""
import argparse
from pathlib import Path
from inventory import HERE,ROOT,PACKAGE,CERT_SHA,load,save,file_sha
from component_bundles import OWNED,read_bundle
from release_authority import guarded,validate,verify_evidence
from release_gate import require

def create(bundles,out):
    require(not out.exists(),'BOOTSTRAP_ALREADY_EXISTS')
    catalog=load(bundles/'catalog.json')
    metas={o:read_bundle(bundles/r['file'],r) for o,r in catalog['bundles'].items()}
    require(set(metas)==set(OWNED),'COMPLETE_OWNER_VECTOR')
    payload={k:v for m in metas.values() for k,v in m['payload'].items()}
    proof_names=('RUNTIME-PRESERVATION.json','OWNER-CONTRACT.json','PRODUCTION-BOUNDARIES.json',
                 'OWNERSHIP.json','COMBINATION-CONTROLS.json')
    proof_dir=HERE/'results/scoped-correction/final'
    paths=list(HERE.glob('*.py'))+list(HERE.glob('*.java'))+list((HERE/'runtime').glob('*.java'))
    paths += [HERE/n for n in ('ownership-reviewed-roots.json','SCOPED-CORRECTION-AUTHORIZATION.json',
                              'SCOPED-CORRECTION-TESTS.json','signer-policy.json')]
    authority={'schema':2,'status':'ENGINEERING_REVIEWED_FOLD_PENDING','generation':2,
      'package':PACKAGE,'certificate_sha256':CERT_SHA,'last_issued_versionCode':2103420,
      'candidate_versionCode':2103421,'accepted_registry_sha256':file_sha(HERE/'accepted-combined-release.json'),
      'bootstrap_authorization':'SCOPED-CORRECTION-AUTHORIZATION.json',
      'assembly_mode':'scoped_baseline_rebuild','bundle_catalog':catalog,
      'accepted_pointer_updated':False,'release_blockers':[],'payload':payload,
      'components':{o:{k:metas[o][k] for k in ('version','settings_schema','approved_source','digest')}|{'revision':1} for o in OWNED},
      'protected_contract':{k:v['sha256'] for k,v in payload.items() if guarded(k)},
      'proofs':{n:file_sha(proof_dir/n) for n in proof_names},
      'source_files':{str(p.relative_to(ROOT)):file_sha(p) for p in sorted(paths)},
      'workflow_sha256':file_sha(ROOT/'.github/workflows/infinity-combined-release.yml'),
      'resolved_blockers':{
        'SHARED_PERSISTENCE_CLOSE_BARRIER':['SCOPED-CORRECTION-AUTHORIZATION.json','OWNER-CONTRACT.json','PRODUCTION-BOUNDARIES.json','RUNTIME-PRESERVATION.json'],
        'SHARED_EXTENDED_BACKGROUND_SERVICE':['PRODUCTION-BOUNDARIES.json','RUNTIME-PRESERVATION.json','OWNERSHIP.json'],
        'UNRESOLVED_BINARY_OWNERSHIP':['OWNERSHIP.json','CLASSES.json.gz','CROSS-OWNER-EDGES.json.gz','NATIVE-OWNERS.json.gz','PYTHON-OWNERS.json.gz','DYNAMIC-SITES.json','DATA-AND-LIFECYCLE-CONTRACT.md']}}
    validate(authority);verify_evidence(authority,lambda name:(ROOT/name).read_bytes())
    save(out,authority)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--bundles',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    create(**vars(p.parse_args()))
