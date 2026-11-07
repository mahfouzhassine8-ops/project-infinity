"""Exact official preparation review and existing owner-authority admission.

No APK signing implementation. The original release_gate and assemble.sign
remain the only APK-signing implementation in the sole retained workflow.
Engineering authority is separate from public release and Fold acceptance.
"""
from pathlib import Path
from zipfile import ZipFile
import argparse
import copy
import json
import os
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
ISO=ROOT/'repairs/dual-experience-isolation-2103420'
sys.path[:0]=[str(ISO),str(HERE)]
from inventory import canonical,digest,file_sha,load,save,SIGNATURE,validate_names
from component_bundles import read_bundle,combine
from release_gate import require,normalize_manifest
from release_authority import AUTHORITY_PATH,transition,verify_evidence
from prepare_release import PARENT,CERT,ENGINE,OLD_ENGINE,CC,SKIN,SOURCE_PINS,SEARCH

BRANCH='work/infinity-final-release-462-20261107'
CANONICAL='work/infinity-2103460-nine-corrections-20261106'
PREPARED_RUN=42425522122
PREPARED_SOURCE='de5bf4643a647659d772f96ebc28680a8cf7a58c'
TARGETS=['INFINITY','CHOOSER_SHELL']
ARTIFACTS={
  2103464:dict(id=13595626273,digest='sha256:fd350c9806d9314401c0ce932d3eb2f93424bfd903b6258bcac970b3d474299f',size_in_bytes=316024607),
  2103465:dict(id=13594949809,digest='sha256:3ced53b6eb5033d5589aa5d1897c4ec25db95537349b721281f34245aa0c0d6c',size_in_bytes=316006598),
}

def cmd(*args):
    result=subprocess.run(list(map(str,args)),capture_output=True,text=True)
    require(result.returncode==0,'TOOL:'+str(args[0])+':'+result.stderr[-2400:])
    return result.stdout.strip()

def gh(path):return json.loads(cmd('gh','api','repos/mahfouzhassine8-ops/project-infinity/'+path))

def bindings():
    paths=[HERE/n for n in ('prepare_release.py','final_release.py','register_engineering.py','verify_module_upgrade.py','PACKAGING-SCOPE.json','SEARCH-REVIEW-SELECTION.json','WORKFLOW-REVIEW.json')]
    paths += [SEARCH/n for n in SOURCE_PINS]
    paths += [ROOT/'repairs/infinity-final-closure-2103407'/n for n in ('SignInfinityModules.java','ORIGINAL-INFINITY-PUBLIC-KEY.pem','InfinityInstalledModules.java.in','module_dex.py','module_bundle.py')]
    return {str(p.relative_to(ROOT)):file_sha(p) for p in paths}

def official(prepared,version):
    require(version in ARTIFACTS,'EXACT_SELECTED_VERSION')
    run=gh('actions/runs/'+str(PREPARED_RUN))
    require(run['status']=='completed' and run['conclusion']=='success' and run['head_sha']==PREPARED_SOURCE and run['head_branch']==BRANCH and run['path']=='.github/workflows/infinity-combined-release.yml','OFFICIAL_COMPLETED_PREPARATION')
    proof=load(prepared/'PREPARATION.json')
    require(proof['source']==PREPARED_SOURCE and proof['versionCode']==version and proof['run_id']==PREPARED_RUN and proof['baseline_sha256']==PARENT,'EXACT_PREPARATION_IDENTITY')
    require(proof['status']=='PASS_EXACT462_AND_AUTHENTICATED_CURRENT_COMPONENT_CONSOLIDATION','PREPARATION_MUST_PASS')
    require(proof['native_sha256']==(ENGINE if version==2103464 else OLD_ENGINE),'EXACT_REVIEWED_ENGINE')
    require(proof['CC']==('0.3.5.62' if version==2103464 else '0.3.5.63') and proof['skin']==('1.0.5.270' if version==2103464 else '1.0.5.271'),'MONOTONIC_COMPONENT_VERSIONS')
    name='Infinity'+str(version)+'-Prepared-'+str(PREPARED_RUN)
    rows=gh('actions/runs/'+str(PREPARED_RUN)+'/artifacts?per_page=100')['artifacts']
    selected=[r for r in rows if r['name']==name and not r['expired']]
    require(len(selected)==1,'ONE_OFFICIAL_PREPARATION_ARTIFACT')
    row=selected[0];require(all(row[k]==v for k,v in ARTIFACTS[version].items()),'EXACT_REVIEWED_OFFICIAL_ARCHIVE')
    archive=prepared.parent/(str(row['id'])+'.zip')
    if not archive.exists():
        with archive.open('wb') as output:subprocess.run(['gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/artifacts/'+str(row['id'])+'/zip'],stdout=output,check=True)
    require(file_sha(archive)==row['digest'].removeprefix('sha256:'),'OFFICIAL_ARCHIVE_DIGEST')
    with ZipFile(archive) as z:
        names={n for n in validate_names(z) if not n.endswith('/')}
        require(names=={str(p.relative_to(prepared)) for p in prepared.rglob('*') if p.is_file()},'EXACT_OFFICIAL_FILE_SET')
        for n in names:
            import hashlib
            with z.open(n) as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
            require(actual==file_sha(prepared/n),'OFFICIAL_MEMBER:'+n)
    # Prepared artifacts cannot substitute changed build tooling after review.
    path=str((HERE/'prepare_release.py').relative_to(ROOT))
    require((HERE/'prepare_release.py').read_bytes()==subprocess.check_output(['git','show',PREPARED_SOURCE+':'+path]),'REUSED_PREPARATION_IMPLEMENTATION')
    for n,h in SOURCE_PINS.items():require(file_sha(SEARCH/n)==h,'EXACT_REVIEWED_SEARCH_SOURCE:'+n)
    return {k:row[k] for k in ('id','name','digest','size_in_bytes')}

def proposed(prepared,version,audit,previous=None):
    artifact=official(prepared,version);proof=load(prepared/'PREPARATION.json')
    previous=previous or load(ROOT/AUTHORITY_PATH)
    require(previous['generation']==(49 if version==2103464 else 50) and previous['candidate_versionCode']==version-1,'EXACT_AUTHORITY_PREDECESSOR')
    report=load(audit)
    require(report['status']=='PASS_NINE_FOCUSED_REAL_JAVA_UPGRADE_AND_RECOVERY_CASES' and len(report['cases'])==9 and report['original_installer_changed'] is False,'ACTUAL_JAVA_INSTALL_OVER_AND_RECOVERY_REQUIRED')
    catalog=load(prepared/'components/catalog.json')
    metas={o:read_bundle(prepared/'components'/r['file'],r) for o,r in catalog['bundles'].items()}
    for owner in ('COBRA','MINIMAL_ANDROID_CONTRACT'):
        require(catalog['bundles'][owner]==previous['bundle_catalog']['bundles'][owner],'PROTECTED_OWNER_BUNDLE:'+owner)
    a=copy.deepcopy(previous)
    a.update(generation=previous['generation']+1,last_issued_versionCode=version-1,candidate_versionCode=version,target_owners=TARGETS,update_kind='owner_update',previous_authority_sha256=digest(canonical(previous)),payload={k:v for meta in metas.values() for k,v in meta['payload'].items()},bundle_catalog=catalog,experience_version_labels={'INFINITY':version,'COBRA':2103445})
    for owner in TARGETS:
        a['components'][owner]={k:metas[owner][k] for k in ('version','digest','approved_source','settings_schema')}
        a['components'][owner]['revision']=previous['components'][owner]['revision']+1
        a['bundle_sources'][owner]=dict(run_id=PREPARED_RUN,build_source=PREPARED_SOURCE,artifact=artifact['name'],path='components/'+owner+'.zip')
    a['source_files']={n:file_sha(ROOT/n) for n in previous['source_files']}
    a['workflow_sha256']=file_sha(ROOT/'.github/workflows/infinity-combined-release.yml')
    a['owner_update_evidence']=dict(owner='INFINITY_FINAL462_SCOPED_CONSOLIDATION' if version==2103464 else 'INFINITY_AUTHENTICATED268_FORWARD_RECOVERY',producer_run=PREPARED_RUN,producer_source=PREPARED_SOURCE,source_files=bindings(),artifact=artifact,preparation_sha256=file_sha(prepared/'PREPARATION.json'),native_sha256=proof['native_sha256'],module_upgrade_recovery_sha256=file_sha(audit),Android='PENDING_SUCCESSOR_ENGINEERING_EXECUTION',physical_Fold='PENDING_ONE_FINAL_USER_ACCEPTANCE',public_release='BLOCKED_UNTIL_SELECTED_ANDROID_GATES_PASS',accepted_pointer_updated=False,settings_policy='Fresh native replies allow meaningful settings writes and ABA; no immutable settings consistency claimed; loss of existing settings refuses')
    transition(previous,a,TARGETS);verify_evidence(a,lambda n:(ROOT/n).read_bytes())
    return a

def check_registered(prepared,version,audit,out):
    current=load(ROOT/AUTHORITY_PATH)
    path=cmd('git','log','-1','--format=%H','--',AUTHORITY_PATH)
    previous=json.loads(cmd('git','show',path+'^:'+AUTHORITY_PATH))
    require(proposed(prepared,version,audit,previous)==current,'EXACT_OFFICIAL_REGISTERED_CONSOLIDATION')
    save(out,dict(status='PASS_EXACT_OFFICIAL_REGISTERED_ENGINEERING_PAYLOAD',versionCode=version,source=cmd('git','rev-parse','HEAD'),accepted_pointer_updated=False,public_release=False))

def compare(parent,candidate,prepared,out,sdk=None):
    proof=load(prepared/'PREPARATION.json');version=proof['versionCode']
    require(file_sha(parent)==PARENT and version in ARTIFACTS,'EXACT_SIGNED462_REFERENCE')
    differences={};members={}
    with ZipFile(parent) as before,ZipFile(candidate) as after:
        names=set(validate_names(before))-SIGNATURE
        require(names==set(validate_names(after))-SIGNATURE,'EXACT_APK_MEMBER_SET')
        for n in sorted(names):
            a,b=before.read(n),after.read(n);members[n]=dict(before=digest(a),after=digest(b))
            if a==b:continue
            require(n in proof['changed_members'] and digest(b)==proof['changed_members'][n],'EXACT_PREPARED_CHANGED_MEMBER:'+n)
            if n=='AndroidManifest.xml':require(normalize_manifest(b)==(normalize_manifest(a)[0],version),'TYPED_MANIFEST_VERSION_ONLY')
            differences[n]=digest(b)
    require(differences==proof['changed_members'],'NO_MISSING_OR_UNDECLARED_PAYLOAD_CHANGES')
    out.mkdir(parents=True,exist_ok=True)
    if sdk:
        cert=cmd(sdk/'apksigner','verify','--verbose','--print-certs',candidate)
        import re
        require(re.findall(r'certificate SHA-256 digest: ([0-9a-f]+)',cert)==[CERT],'ORIGINAL_PERMANENT_CERTIFICATE')
        (out/'SIGNATURE.txt').write_text(cert+'\n')
    save(out/'ALL-APK-MEMBER-HASHES.json',members)
    result=dict(status='PASS_SIGNED462_EXACT_CONSOLIDATION_MEMBER_PRESERVATION',versionCode=version,baseline_sha256=PARENT,candidate_sha256=file_sha(candidate),changed_members=differences,unchanged_members=len(names)-len(differences),all_DEX_unchanged=True,Cobra_bundle_unchanged=True,Android='NOT_RUN_BY_PACKAGING',Fold='NOT_RUN',public_release=False,accepted_pointer_updated=False)
    save(out/'APK-PRESERVATION.json',result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='op',required=True)
    for op in ('propose','check_registered'):
        a=sub.add_parser(op)
        for n in ('prepared','audit','out'):a.add_argument('--'+n,type=Path,required=True)
        a.add_argument('--version',type=int,required=True)
    a=sub.add_parser('compare')
    for n in ('parent','candidate','prepared','out'):a.add_argument('--'+n,type=Path,required=True)
    a.add_argument('--sdk',type=Path)
    d=vars(p.parse_args());op=d.pop('op')
    if op=='propose':save(d.pop('out'),proposed(**d))
    else:globals()[op](**d)
