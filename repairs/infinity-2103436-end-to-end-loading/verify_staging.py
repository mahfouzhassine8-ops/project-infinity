"""Round-trip unsigned Infinity staging only; never a release/signing gate PASS."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_STORED
from baseline_contract import EXPECTED, SKIN, CC

def sha(data):return hashlib.sha256(data).hexdigest()

def verify(component,stage,out):
    assert not out.exists();out.mkdir(parents=True)
    with component.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==EXPECTED
    plan=json.loads((stage/'PLAN.json').read_text());assert plan['baseline_component']==EXPECTED
    assert plan['status']=='UNAUTHENTICATED_STAGING_ONLY_NOT_INSTALLABLE'
    candidate=out/'INFINITY-UNAUTHENTICATED-STAGING.zip'
    allowed=set(plan['changes']);seen=set();before_hashes={};after_hashes={}
    with ZipFile(component) as source,ZipFile(candidate,'w',compression=ZIP_STORED) as target:
        for info in source.infolist():
            name=info.filename;raw=source.read(name);before_hashes[name]=sha(raw)
            rel=name.removeprefix('payload/')
            if rel in allowed:
                assert name.startswith(SKIN+'unified/') or name==CC+'action_loading.py'
                revised=(stage/'members'/rel).read_bytes()
                assert sha(raw)==plan['changes'][rel]['before'] and sha(revised)==plan['changes'][rel]['after']
                raw=revised;seen.add(rel)
            target.writestr(name,raw)
    assert seen==allowed
    with ZipFile(candidate) as archive:
        assert set(archive.namelist())==set(before_hashes)
        for name in archive.namelist():after_hashes[name]=sha(archive.read(name))
    changed={name:dict(before=before,after=after_hashes[name],owner='INFINITY') for name,before in before_hashes.items() if before!=after_hashes[name]}
    assert {n.removeprefix('payload/') for n in changed}==allowed
    report=dict(status='PASS_UNSIGNED_STAGING_MEMBER_ROUNDTRIP_ONLY',baseline_component_sha256=EXPECTED,
                members=len(before_hashes),changed=changed,unchanged=len(before_hashes)-len(changed),added=[],removed=[],
                module_authentication='NOT_REGENERATED; staging is deliberately not installable',
                candidate_apk_comparison='NOT_RUN; no candidate APK exists',
                Cobra='No candidate owner built or changed; signed-APK equality gate still pending',
                signing='NOT_RUN',shutdown='NOT_CHANGED_NOT_TESTED')
    (out/'PRESERVATION.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','members','unchanged','added','removed')}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--component',type=Path,required=True);p.add_argument('--stage',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    verify(**vars(p.parse_args()))
