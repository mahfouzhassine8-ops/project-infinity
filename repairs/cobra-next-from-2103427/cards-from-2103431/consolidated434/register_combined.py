"""Register/check one coordinated owner vector, without release acceptance.

All three official artifacts, original-key source authentication and exact
selected tests are rechecked. The guarded original APK signer remains separate.
"""
import argparse
import copy
import json
from pathlib import Path
import subprocess
from zipfile import ZipFile
from combined_owners import *
from release_authority import transition,verify_evidence


def extract(path,target):
    require(not target.exists(),'FRESH_OFFICIAL_EVIDENCE_EXTRACTION');target.mkdir(parents=True)
    with ZipFile(path) as z:validate_names(z);z.extractall(target)
    return target

def inspect(auth_run,work,bundles=None):
    require(not work.exists(),'FRESH_COORDINATED_EVIDENCE_WORK');work.mkdir(parents=True)
    run=successful_run(auth_run,BRANCH,'.github/workflows/infinity-combined-release.yml')
    art=artifact(auth_run,'Coordinated434-Prepared-Owners-'+str(auth_run))
    official=archive(art,work/'coordinated-owners.zip');prepared=extract(official,work/'prepared')
    expected={'COORDINATED-OWNERS.json','INFINITY-SOURCE-PLAN.json','MODULE-AUTHENTICATION.txt','components/catalog.json'}|{'components/'+owner+'.zip' for owner in OWNED}
    with ZipFile(official) as z:require(set(z.namelist())==expected,'EXACT_PREPARED_OWNER_ARTIFACT_NO_APK_OR_KEYS')
    receipt=load(prepared/'COORDINATED-OWNERS.json');catalog=load(prepared/'components/catalog.json')
    require(receipt['status']=='PASS_COORDINATED434_PREPARED_OWNERS' and receipt['source']==run['head_sha'] and
            receipt['run_id']==auth_run and receipt['baseline_source']==BASE_SOURCE,'SUCCESSFUL_COORDINATED_PREPARATION')
    require(file_sha(prepared/'components/catalog.json')==receipt['catalog_sha256'] and
            file_sha(prepared/'INFINITY-SOURCE-PLAN.json')==receipt['source_plan_sha256'] and
            file_sha(prepared/'MODULE-AUTHENTICATION.txt')==receipt['module_authentication_sha256'],'COMPLETE_COORDINATED_RECEIPT_BINDING')
    required_sources={str((HERE/name).relative_to(REPO)) for name in ('combined_owners.py','prepare_combined.py','register_combined.py','verify_delivery.py','test_release_protocol.py','RELEASE-SCOPE.json')}|{'.github/workflows/infinity-combined-release.yml'}
    require(set(receipt['release_source_files'])==required_sources,'COMPLETE_COORDINATED_RELEASE_SOURCE_MANIFEST')
    for name,pin in receipt['release_source_files'].items():
        require(file_sha(REPO/name)==pin==digest(subprocess.check_output(['git','-C',str(REPO),'show',receipt['source']+':'+name])),'COORDINATED_RELEASE_SOURCE_CHANGED:'+name)
    c=receipt['cobra'];arts=cobra.producer_artifacts(c['producer_run'],c['producer_source'])
    require(arts==c['artifacts'],'OFFICIAL_COBRA_ARTIFACTS_CHANGED')
    cb=extract(archive(arts['Cobra-Cards-Prepared-Owners-'+str(c['producer_run'])],work/'cobra-owners.zip'),work/'cobra-components')
    ce=extract(archive(arts['Cobra-Cards-Host-Evidence-'+str(c['producer_run'])],work/'cobra-host.zip'),work/'cobra-evidence')
    require(check_cobra(cb,ce,c['producer_run'],work)==c,'EXACT_RECORDED_COBRA_PRODUCER_EVIDENCE')
    l=receipt['loading'];la=artifact(l['producer_run'],'Infinity-Seamless-Loading-Host-Evidence-'+str(l['producer_run']))
    require(la==l['artifact'],'OFFICIAL_LOADING_ARTIFACT_CHANGED')
    le=extract(archive(la,work/'loading-host.zip'),work/'loading-evidence')
    require(check_loading(le,l['producer_run'],work)==l,'EXACT_RECORDED_SEPARATE_LOADING_PRODUCER')
    auth=receipt['infinity_authentication']
    require(auth['source']==receipt['source'] and auth['run_id']==auth_run and
            auth['owner_producer_source']==l['producer_source'] and auth['owner_producer_run']==l['producer_run'] and
            auth['host_result_sha256']==l['host_result_sha256'] and auth['tested_source_files']==l['tested_source_files'] and
            auth['original_module_authentication']=='JCA_AND_ORIGINAL_NATIVE_VERIFIER','EXACT_ORIGINAL_KEY_INFINITY_AUTHENTICATION_RECORD')
    plan=load(prepared/'INFINITY-SOURCE-PLAN.json')
    require(file_sha(prepared/'INFINITY-SOURCE-PLAN.json')==l['source_plan_sha256'],'EXACT_CI_TESTED_PLAN')
    payload,metas,changed,added,integrity=validate_combined(catalog,prepared/'components',receipt,plan)
    require(sorted(changed)==receipt['changed_payload'] and sorted(added)==receipt['added_payload'] and
            integrity==receipt['module_integrity'],'COORDINATED_PAYLOAD_PROOF_UNCHANGED')
    if bundles is not None:
        require(load(bundles/'catalog.json')==catalog,'ACTUAL_ASSEMBLY_USES_EXACT_COORDINATED_CATALOG')
        for row in catalog['bundles'].values():require(file_sha(bundles/row['file'])==row['sha256'],'ACTUAL_ASSEMBLED_OWNER_BYTES:'+row['file'])
    return dict(receipt=receipt,catalog=catalog,payload=payload,metas=metas,changed=changed,added=added,
                artifact=art,prepared=prepared,receipt_sha256=file_sha(prepared/'COORDINATED-OWNERS.json'))

def proposed(result):
    prior=previous();r=result['receipt'];catalog=result['catalog'];metas=result['metas']
    authority=copy.deepcopy(prior)
    authority.update(generation=GENERATION,last_issued_versionCode=2103433,candidate_versionCode=VERSION,
        update_kind='owner_update',target_owners=list(TARGETS),previous_authority_sha256=digest(canonical(prior)),
        payload=result['payload'],bundle_catalog=catalog,experience_version_labels={'INFINITY':VERSION,'COBRA':VERSION})
    for owner in TARGETS:
        authority['components'][owner]={k:metas[owner][k] for k in ('version','settings_schema','approved_source','digest')}
        authority['components'][owner]['revision']=prior['components'][owner]['revision']+1
        authority['bundle_sources'][owner]=dict(run_id=r['run_id'],build_source=r['source'],artifact=result['artifact']['name'],path='components/'+owner+'.zip')
    authority['source_files']={name:file_sha(REPO/name) for name in prior['source_files']}
    authority['workflow_sha256']=file_sha(REPO/'.github/workflows/infinity-combined-release.yml')
    authority['owner_update_evidence']=dict(owner='COORDINATED_COBRA_INFINITY',changed_owners=list(TARGETS),
        authenticated_owner_run=r['run_id'],authenticated_owner_source=r['source'],authenticated_owner_artifact=result['artifact'],
        prepared_receipt_sha256=result['receipt_sha256'],cobra=r['cobra'],loading=r['loading'],infinity_authentication=r['infinity_authentication'],
        release_source_files=r['release_source_files'],changed_payload=sorted(result['changed']|result['added']),
        frozen_owners=['MINIMAL_ANDROID_CONTRACT'],chooser_change='Genuine Infinity/Cobra434 labels only; exact433 executable and UI members',
        authorization=str((HERE/'SCOPE.json').relative_to(REPO)),protected_contract='EXACT433',shutdown_tests='NOT_RUN',
        runtime_limits='Host/native-framework and source/authentication gates; Infinity Android constructor blocked; physical Fold acceptance pending',
        physical_Fold='PENDING',accepted_pointer_updated=False)
    transition(prior,authority,TARGETS);verify_evidence(authority,lambda name:(REPO/name).read_bytes())
    return authority

def register(auth_run,work,out,apply=False):
    require(load(ISO/'release-authority.json')==previous(),'EXACT433_AUTHORITY_BEFORE_REGISTRATION')
    require(not out.exists(),'FRESH_REVIEWABLE_AUTHORITY_PROPOSAL')
    result=inspect(auth_run,work);authority=proposed(result);save(out,authority)
    if apply:
        require(load(ISO/'release-authority.json')==previous(),'AUTHORITY_RACE_BEFORE_REGISTRATION')
        save(ISO/'release-authority.json',authority)
        save(HERE/'REGISTERED434.json',dict(versionCode=VERSION,generation=GENERATION,prepared_owner_run=auth_run,
            prepared_owner_source=result['receipt']['source'],component_catalog=result['catalog'],
            accepted_pointer_updated=False,physical_Fold='PENDING',lock_promoted=False))
    print('PASS reviewed coordinated434 owner vector '+('registered' if apply else 'proposal saved')+'; no acceptance or lock')

def check_registered(bundles,work):
    current=load(ISO/'release-authority.json')
    require(current['generation']==GENERATION and current['candidate_versionCode']==VERSION and set(current['target_owners'])==set(TARGETS),'REGISTERED_COORDINATED434_REQUIRED')
    result=inspect(current['owner_update_evidence']['authenticated_owner_run'],work,bundles)
    require(proposed(result)==current,'CURRENT_REGISTERED_VECTOR_AND_ALL_SOURCE_EVIDENCE_EXACT')
    save(work/'REGISTERED434-CHECK.json',dict(status='PASS_COORDINATED434_REGISTERED_OWNER_EVIDENCE',
        generation=GENERATION,versionCode=VERSION,receipt_sha256=result['receipt_sha256'],source=result['receipt']['source'],
        actual_component_zip_sha256={row['file']:row['sha256'] for row in result['catalog']['bundles'].values()},
        original_module_signature='VERIFIED',Cobra_selected_tests=19,Infinity_selected_tests=24,
        APK_signing='NOT_ACCESSED',shutdown='NOT_CHANGED_NOT_RUN',physical_Fold='PENDING'))
    print('PASS official source/test/authenticated owners and actual assembled ZIPs before APK key access')

if __name__=='__main__':
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='phase',required=True)
    a=sub.add_parser('register');a.add_argument('--auth-run',type=int,required=True);a.add_argument('--work',type=Path,required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--apply',action='store_true')
    a=sub.add_parser('check-registered');a.add_argument('--bundles',type=Path,required=True);a.add_argument('--work',type=Path,required=True)
    args=vars(p.parse_args());phase=args.pop('phase');(register if phase=='register' else check_registered)(**args)
