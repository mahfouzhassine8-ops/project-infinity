#!/usr/bin/env python3
"""Original owner's internal-QA admission; never signs or publishes itself.

Consumes one frozen reviewed request and exact successful producer artifacts.
Existing release_authority/release_gate/assemble.py remain the only authority
and signing implementation. No runtime acceptance is inferred from packaging.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
CORE=ROOT/'repairs/dual-experience-isolation-2103420'
sys.path.insert(0,str(CORE))
import component_bundles as cb
import release_authority as ra
from inventory import CERT_SHA,SIGNATURE,canonical,digest,file_sha,validate_names

REPO='mahfouzhassine8-ops/project-infinity'
CANONICAL='work/infinity-2103460-nine-corrections-20261106'
PARENT='4ed6e8a8bdc19f7bca50429e5bbb286f70eaf143'
BASE_APK='78b2a5dd878ea847f425f8bbf5b9c71e810d19e134fe4480588db55a7ea52a32'
BASE_ENGINE='503f91109332ef050a604cf15ad604b16e156b55459bafd47c453c3f72de0437'
VERSION=2103483
GENERATION=68
LIB='lib/arm64-v8a/libkodi.so'
LABEL='assets/experience-component-updates.properties'
MEMBERS={LIB,LABEL,'AndroidManifest.xml'}
OWNERS=['INFINITY','CHOOSER_SHELL']
OWNER='INFINITY_STARTUP83_INTERNAL_QA_NOT_ACCEPTED'

def require(value,reason):
    if not value:raise RuntimeError(reason)

def load(path):return json.loads(Path(path).read_text())
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def api(path):return json.loads(subprocess.check_output(['gh','api','repos/'+REPO+'/'+path],text=True,timeout=45))
def hash_member(z,name):
    import hashlib
    with z.open(name) as f:return hashlib.file_digest(f,'sha256').hexdigest()

def request():
    require(os.environ.get('GITHUB_REPOSITORY')==REPO and os.environ.get('GITHUB_REF')=='refs/heads/'+CANONICAL,'ORIGINAL_OWNER_BRANCH_REQUIRED')
    require(git('rev-parse','HEAD')==os.environ.get('GITHUB_SHA'),'HEAD_RACE')
    require(not git('status','--porcelain','--untracked-files=no'),'DIRTY_REVIEWED_SOURCE')
    r=load(HERE/'QA-SIGN-REQUEST.json')
    require(r['sign_operation']=='sign-startup-internal-qa','EXPLICIT_ORIGINAL_QA_OPERATION_REQUIRED')
    require(all(type(r[k]) is int and r[k]>0 for k in ('prepared_run','prepared_artifact_id','native_run')),'NUMERIC_FROZEN_PRODUCER_IDENTITIES')
    require(r['operation']=='original-owner-functional-startup-internal-QA' and r['versionCode']==VERSION and r['generation']==GENERATION,'EXACT_FROZEN_QA_REQUEST')
    require(r['original_signer_workflow_id']==397702717 and r['baseline_APK_sha256']==BASE_APK,'ORIGINAL_SIGNER_AND_BASELINE_REQUIRED')
    require(r['corrective_commit']=='679807f7a38173cae2b071d137ef28cf2d35fa37' and r['native_source']=='a7f890b1cdccebca7db6695fa3e6752d501cec9d','UNREVIEWED_NATIVE_SOURCE')
    require(r['Android_candidate']=='NOT_RUN' and r['Fold_cause_established'] is False and r['owner_delivery'] is False,'NO_FALSE_RUNTIME_OR_FOLD_ACCEPTANCE')
    require(r['baseline_Android_run']==43112968019 and r['baseline_error_cleanup_run']==43109315570,'RETAINED_BASELINE_PROOFS_REQUIRED')
    require(load(CORE/'signer-policy.json')['sole_original_key_workflow_id']==397702717,'SIGNER_OWNER_CHANGED')
    native=api('actions/runs/'+str(r['native_run']))
    require(native['status']=='completed' and native['conclusion']=='success' and native['head_sha']==r['native_source'],'ACTUAL_ARM64_PRODUCER_NOT_PASS')
    prepared=api('actions/runs/'+str(r['prepared_run']))
    require(prepared['status']=='completed' and prepared['conclusion']=='success' and prepared['head_sha']==r['prepared_source'] and prepared['workflow_id']!=397702717,'EXACT_KEYFREE_PREPARATION_REQUIRED')
    artifact=api('actions/artifacts/'+str(r['prepared_artifact_id']))
    require(not artifact['expired'] and artifact['workflow_run']['id']==r['prepared_run'] and artifact['digest']==r['prepared_artifact_digest'] and artifact['name']==r['prepared_artifact_name'],'EXACT_PREPARED_ARTIFACT_REQUIRED')
    baseline=api('actions/runs/43112968019')
    require(baseline['conclusion']=='success' and baseline['head_sha']=='85a3f9dbdb46d057928568cba40b77cfd519db0a','BASELINE_ANDROID_NOT_PASS')
    issued=api('actions/runs/42979187229')
    require(issued['conclusion']=='success' and issued['workflow_id']==397702717 and issued['head_sha']==PARENT,'ORIGINAL82_ISSUANCE_REQUIRED')
    return r

def compare(baseline,candidate,native_sha):
    require(file_sha(baseline)==BASE_APK,'EXACT_AUTHENTICATED82_REQUIRED')
    with ZipFile(baseline) as old,ZipFile(candidate) as new:
        names=set(validate_names(old))-set(SIGNATURE)
        require(names==set(validate_names(new))-set(SIGNATURE),'APK_MEMBER_SET_CHANGED')
        changes={n for n in names if hash_member(old,n)!=hash_member(new,n)}
        require(changes==MEMBERS,'UNRELATED_APK_MEMBER_CHANGED')
        require(hash_member(old,LIB)==BASE_ENGINE and hash_member(new,LIB)==native_sha,'EXACT_NATIVE_HASH_REQUIRED')
        require(new.read(LABEL)==b'infinity.last_updated_in=2103483\ncobra.last_updated_in=2103445\n','CROSS_OWNER_LABEL_CHANGED')
        a,av=cb.normalize_manifest(old.read('AndroidManifest.xml'));b,bv=cb.normalize_manifest(new.read('AndroidManifest.xml'))
        require(av==2103482 and bv==VERSION and a==b,'MANIFEST_CHANGED_BEYOND_VERSION')
        return len(names)-len(changes)

def prepared_inputs(r):
    prepared=ROOT/'startup-qa-prepared'
    archive=ROOT/'startup-qa-prepared.zip'
    require('sha256:'+file_sha(archive)==r['prepared_artifact_digest'],'DOWNLOADED_PREPARATION_ARCHIVE_DIGEST')
    consumed={'UNSIGNED-QA-PRESERVATION.json','components/catalog.json',
              'Infinity-2103483-Startup-UNSIGNED-NOT-INSTALLABLE.apk'}
    consumed.update('components/'+owner+'.zip' for owner in cb.OWNED)
    with ZipFile(archive) as z:
        names=set(validate_names(z));require(consumed<=names,'MISSING_AUTHENTICATED_PREPARATION_FILES')
        for name in consumed:
            require(hash_member(z,name)==file_sha(prepared/name),'LOCAL_PREPARATION_FILE_NOT_FROM_AUTHENTICATED_ARCHIVE:'+name)
    proof=load(prepared/'UNSIGNED-QA-PRESERVATION.json')
    require(proof['status']=='PASS_UNSIGNED_STARTUP_QA_THREE_MEMBER_PRESERVATION' and proof['source']==r['prepared_source'],'ACTUAL_STAGING_PRESERVATION_REQUIRED')
    require(proof['baseline_sha256']==BASE_APK and proof['native_sha256']==r['native_sha256'] and proof['native_source']==r['native_source'],'PREPARED_NATIVE_IDENTITY_MISMATCH')
    require(proof['versionCode']==VERSION and proof['signed'] is False and proof['owner_delivery'] is False and proof['root_cause_of_Fold']=='UNPROVEN','UNTRUE_PREPARATION_ACCEPTANCE')
    apk=prepared/'Infinity-2103483-Startup-UNSIGNED-NOT-INSTALLABLE.apk'
    require(file_sha(apk)==r['unsigned_sha256']==proof['unsigned_sha256'],'PREPARED_APK_HASH_MISMATCH')
    require(set(proof['changed_members'])==MEMBERS,'UNRELATED_STAGING_DELTA')
    baseline=ROOT/'signed82/Infinity-2103482-Combined-Original-Signer.apk'
    unchanged=compare(baseline,apk,r['native_sha256'])
    return prepared,proof,unchanged

def propose(out):
    r=request();folder,proof,unchanged=prepared_inputs(r)
    before=load(ROOT/ra.AUTHORITY_PATH)
    require(before==json.loads(git('show',PARENT+':'+ra.AUTHORITY_PATH)),'LIVE_AUTHORITY_ADVANCED')
    require(before['generation']==67 and before['candidate_versionCode']==2103482,'UNEXPECTED_REGISTRY_GENERATION')
    catalog=load(folder/'components/catalog.json')
    require(catalog['source']==r['prepared_source'] and catalog['release_approved'] is False and set(catalog['bundles'])==set(cb.OWNED),'UNREVIEWED_OWNER_CATALOG')
    require(all(catalog['bundles'][o]['file']==o+'.zip' for o in cb.OWNED),'OWNER_FILE_NOT_BOUND_TO_ARTIFACT')
    meta={owner:cb.read_bundle(folder/'components'/catalog['bundles'][owner]['file'],catalog['bundles'][owner]) for owner in cb.OWNED}
    for owner in ('COBRA','MINIMAL_ANDROID_CONTRACT'):
        require(catalog['bundles'][owner]==before['bundle_catalog']['bundles'][owner],'PROTECTED_OWNER_BUNDLE_CHANGED:'+owner)
    payload={k:v for owner in cb.OWNED for k,v in meta[owner]['payload'].items()}
    require(len(payload)==sum(len(meta[o]['payload']) for o in cb.OWNED),'DUPLICATE_OWNER_PAYLOAD')
    result=copy.deepcopy(before)
    result.update(generation=GENERATION,candidate_versionCode=VERSION,last_issued_versionCode=2103482,
        previous_authority_sha256=digest(canonical(before)),target_owners=OWNERS,update_kind='owner_update',
        payload=payload,bundle_catalog=catalog,experience_version_labels={'INFINITY':VERSION,'COBRA':2103445},
        workflow_sha256=file_sha(ROOT/'.github/workflows/infinity-combined-release.yml'))
    for owner in OWNERS:
        m=meta[owner];require(m['approved_source']==r['prepared_source'],'UNREVIEWED_OWNER_SOURCE')
        result['components'][owner]={k:m[k] for k in ('version','digest','approved_source','settings_schema')}
        result['components'][owner]['revision']=before['components'][owner]['revision']+1
        result['bundle_sources'][owner]={'run_id':r['prepared_run'],'build_source':r['prepared_source'],'artifact':r['prepared_artifact_name'],'path':'components/'+owner+'.zip'}
    # Only the reviewed routing inventory may change in the authority toolkit.
    for name in result['source_files']:
        actual=file_sha(ROOT/name)
        if actual!=result['source_files'][name]:
            require(name=='repairs/dual-experience-isolation-2103420/signer-policy.json','PROTECTED_AUTHORITY_TOOL_CHANGED:'+name)
            result['source_files'][name]=actual
    files=[Path(__file__),HERE/'QA-SIGN-REQUEST.json']
    result['owner_update_evidence']=dict(owner=OWNER,producer_run=r['prepared_run'],producer_source=r['prepared_source'],
        artifact={'id':r['prepared_artifact_id'],'name':r['prepared_artifact_name'],'digest':r['prepared_artifact_digest']},
        source_files={str(f.relative_to(ROOT)):file_sha(f) for f in files},preparation_sha256=file_sha(folder/'UNSIGNED-QA-PRESERVATION.json'),
        baseline_APK_sha256=BASE_APK,native_sha256=r['native_sha256'],native_build_commit=r['native_source'],corrective_commit=r['corrective_commit'],
        immutable_functional_base=2103482,protected_recovery_base=2103477,Cobra_changes=False,
        Android_baseline='PASS_SELECTED_LOCAL_FUNCTIONALITY_WITH_EXPLICIT_FRESH_PROFILE_HC_ENABLEMENT',Android='NOT_RUN',
        Fold_cause_established=False,physical_Fold='NOT_RUN',engineering_QA_only=True,experimental=True,
        publication=False,public_release=False,owner_delivery_cleared=False,accepted_pointer_updated=False,
        recovery='ORIGINAL_SIGNED77_AND82_PRESERVED_NOT_APPLIED',verification_toolchain=before['owner_update_evidence']['verification_toolchain'])
    ra.transition(before,result,OWNERS);ra.verify_evidence(result,lambda name:(ROOT/name).read_bytes())
    ra.verify(result,{k:v['sha256'] for k,v in payload.items()},VERSION,GENERATION)
    require(result['components']['COBRA']==before['components']['COBRA'] and result['protected_contract']==before['protected_contract'],'PROTECTED_COMPONENT_CHANGED')
    out.mkdir(parents=True,exist_ok=False)
    (out/'AUTHORITY-PROPOSAL.json').write_bytes(canonical(result))
    (out/'ADMISSION-RESULT.json').write_bytes(canonical(dict(status='PASS_INTERNAL_QA_AUTHORITY_PROPOSAL_ONLY',versionCode=VERSION,generation=GENERATION,
        unsigned_sha256=r['unsigned_sha256'],unchanged_APK_payload_members=unchanged,authority_sha256=digest(canonical(result)),signed=False,owner_delivery=False)))

def admit():
    r=request();a=load(ROOT/ra.AUTHORITY_PATH)
    require(a['generation']==GENERATION and a['candidate_versionCode']==VERSION and a['last_issued_versionCode']==2103482,'UNREGISTERED_EXACT_VERSION')
    require(a['status']=='ENGINEERING_REVIEWED_FOLD_PENDING' and a['target_owners']==OWNERS and a['update_kind']=='owner_update','UNREVIEWED_AUTHORITY_TRANSITION')
    require(a['experience_version_labels']=={'INFINITY':VERSION,'COBRA':2103445} and a['components']['COBRA']['version']=='2103445.cobra.1','CROSS_OWNER_CHANGE')
    require(a['accepted_pointer_updated'] is False,'ACCEPTED_BASELINE_CHANGED')
    e=a['owner_update_evidence']
    require(e['owner']==OWNER and e['producer_run']==r['prepared_run'] and e['artifact']['id']==r['prepared_artifact_id'],'WRONG_PREPARED_SOURCE')
    require(e['baseline_APK_sha256']==BASE_APK and e['native_sha256']==r['native_sha256'],'WRONG_NATIVE_PAYLOAD')
    require(e['Android']=='NOT_RUN' and e['Fold_cause_established'] is False and e['owner_delivery_cleared'] is False and e['publication'] is False,'NO_FALSE_ACCEPTANCE')
    for path,sha in e['source_files'].items():require(file_sha(ROOT/path)==sha,'UNREVIEWED_ADMISSION_SOURCE:'+path)
    require(a['payload']['member:'+LIB]=={'owner':'INFINITY','sha256':r['native_sha256']},'NATIVE_OWNER_CHANGED')
    ra.validate(a);ra.verify_evidence(a,lambda p:(ROOT/p).read_bytes())
    print('PASS exact internal-QA admission; no key used')
    return r

def inputs():
    r=admit();prepared_inputs(r);print('PASS exact baseline82 and three-member unsigned delta')

def post():
    r=admit();out=ROOT/'startup-qa-original-signed';apk=out/'Infinity-2103483-Combined-Original-Signer.apk'
    receipt=load(out/'BUILD-RECEIPT.json')
    require(file_sha(apk)==receipt['signed_apk_sha256'] and receipt['versionCode']==VERSION and receipt['certificate_sha256']==CERT_SHA,'SIGNED_IDENTITY_MISMATCH')
    signature=(out/'SIGNATURE.txt').read_text()
    for scheme in ('v1','v2','v3'):
        require(any(l.startswith('Verified using '+scheme+' scheme') and l.endswith(': true') for l in signature.splitlines()),'SIGNATURE_SCHEME_MISSING:'+scheme)
    unchanged=compare(ROOT/'signed82/Infinity-2103482-Combined-Original-Signer.apk',apk,r['native_sha256'])
    proof=dict(status='PASS_ORIGINAL_SIGNED_INTERNAL_QA_THREE_MEMBER_PRESERVATION',
        versionCode=VERSION,source=git('rev-parse','HEAD'),signed_apk_sha256=file_sha(apk),certificate_sha256=CERT_SHA,
        native_sha256=r['native_sha256'],changed_members=sorted(MEMBERS),unchanged_payload_members=unchanged,Cobra_changed=False,
        protected77_preservation='Inherited protection unchanged; original77 artifact not modified or freshly reverified here',Android_candidate='NOT_RUN',actual_installation='NOT_RUN',Fold='NOT_RUN',Fold_cause_established=False,
        owner_delivery=False,published_release=False,forward_recovery='NOT_ISSUED')
    (out/'QA-PRESERVATION.json').write_bytes(canonical(proof))
    print(json.dumps(proof,sort_keys=True))

def download():
    r=request()
    archive=ROOT/'startup-qa-prepared.zip';out=ROOT/'startup-qa-prepared'
    require(not archive.exists() and not out.exists(),'NO_REPLACE_OF_RETAINED_INPUTS')
    with archive.open('wb') as f:
        subprocess.run(['gh','api','repos/'+REPO+'/actions/artifacts/'+str(r['prepared_artifact_id'])+'/zip'],stdout=f,check=True,timeout=300)
    require('sha256:'+file_sha(archive)==r['prepared_artifact_digest'],'PREPARATION_ARCHIVE_DIGEST')
    with ZipFile(archive) as z:
        names=set(validate_names(z))
        consumed={'UNSIGNED-QA-PRESERVATION.json','components/catalog.json','Infinity-2103483-Startup-UNSIGNED-NOT-INSTALLABLE.apk'}
        consumed.update('components/'+owner+'.zip' for owner in cb.OWNED)
        require(consumed<=names,'REQUIRED_PREPARATION_CONTENTS')
        for name in consumed:z.extract(name,out)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['download','propose','admit','inputs','post']);p.add_argument('--out',type=Path);a=p.parse_args()
    if a.mode=='propose':require(a.out is not None,'PROPOSAL_DESTINATION_REQUIRED');propose(a.out)
    else:{'download':download,'admit':admit,'inputs':inputs,'post':post}[a.mode]()
