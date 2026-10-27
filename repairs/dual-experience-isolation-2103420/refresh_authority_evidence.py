"""Refresh gate evidence while retaining the exact reserved APK payload/version.

The transition checker rejects any component or payload change through this
path. The accepted release pointer is never written.
"""
import argparse,copy
from pathlib import Path
from inventory import HERE,ROOT,load,save,file_sha,digest,canonical
from release_authority import guarded,transition,verify_evidence

def refresh(path):
    previous=load(path);proposed=copy.deepcopy(previous)
    proposed.update(generation=previous['generation']+1,guard_schema=2,
        update_kind='evidence_refresh',target_owners=[],previous_authority_sha256=digest(canonical(previous)))
    proposed['protected_contract']={k:v['sha256'] for k,v in proposed['payload'].items() if guarded(k)}
    proposed['proofs']={n:file_sha(HERE/'results/scoped-correction/final'/n) for n in proposed['proofs']}
    paths={ROOT/n for n in proposed['source_files']}|set(HERE.glob('*.py'))
    proposed['source_files']={str(p.relative_to(ROOT)):file_sha(p) for p in sorted(paths)}
    proposed['workflow_sha256']=file_sha(ROOT/'.github/workflows/infinity-combined-release.yml')
    transition(previous,proposed,set());verify_evidence(proposed,lambda n:(ROOT/n).read_bytes())
    save(path,proposed)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--authority',type=Path,required=True);args=p.parse_args();refresh(args.authority)
