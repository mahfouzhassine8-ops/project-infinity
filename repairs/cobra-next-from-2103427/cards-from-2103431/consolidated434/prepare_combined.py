"""Join separately verified owners through the existing combined release job.

Preparation emits matching owner ZIPs only. APK creation/signing happens later
through the unchanged hard owner gate and original guarded APK signer.
"""
import argparse
import copy
import os
from pathlib import Path
import shutil
import subprocess
from combined_owners import *


def head():
    expected=os.environ['GITHUB_SHA']
    require(os.environ.get('GITHUB_WORKFLOW')=='Infinity combined release | owner gate before original signing' and
            os.environ.get('GITHUB_REF')=='refs/heads/'+BRANCH and os.environ.get('LOADING_OPERATION')=='authenticate-infinity-owner','EXISTING_SOLE_AUTHENTICATION_JOB')
    require(subprocess.check_output(['git','remote','get-url','origin'],text=True).strip().removesuffix('.git')=='https://github.com/'+REPOSITORY,'EXPECTED_ORIGIN')
    require(subprocess.check_output(['git','ls-remote','origin','refs/heads/'+BRANCH],text=True).split()[0]==expected,'COMBINED_PREPARATION_HEAD_RACE')
    require(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==expected and
            not subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],text=True).strip(),'EXACT_CLEAN_CURRENT_SOURCE')
    require(load(ISO/'release-authority.json')==previous(),'EXACT_UNMODIFIED433_AUTHORITY_DURING_PREPARATION')
    return expected

def release_sources(source):
    paths=[HERE/name for name in ('combined_owners.py','prepare_combined.py','register_combined.py','verify_delivery.py','test_release_protocol.py','RELEASE-SCOPE.json')]
    paths+=[REPO/'.github/workflows/infinity-combined-release.yml']
    result={str(p.relative_to(REPO)):file_sha(p) for p in paths}
    for name,pin in result.items():require(digest(subprocess.check_output(['git','show',source+':'+name]))==pin,'COMMITTED_COORDINATED_RELEASE_SOURCE:'+name)
    return result

def precheck(cobra_components,cobra_evidence,cobra_run,loading_evidence,loading_run,out):
    source=head();require(not out.exists(),'FRESH_COMBINED_PRECHECK');out.mkdir(parents=True)
    files=release_sources(source)
    c=check_cobra(cobra_components,cobra_evidence,cobra_run,out)
    loading=check_loading(loading_evidence,loading_run,out)
    for ancestor in (c['producer_source'],loading['producer_source']):
        require(subprocess.run(['git','merge-base','--is-ancestor',ancestor,source],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0,'INTEGRATED_VERIFIED_OWNER_ANCESTRY')
    save(out/'PRECHECK.json',dict(status='PASS_TWO_VERIFIED_OWNERS_BEFORE_MODULE_KEY',source=source,
        run_id=int(os.environ['GITHUB_RUN_ID']),cobra=c,loading=loading,release_source_files=files,APK='NOT_BUILT',shutdown='NOT_RUN'))
    head();print('PASS separately bound Cobra and Infinity evidence; module key not accessed by precheck')

def finish(precheck,authenticated,loading_evidence,cobra_components,out):
    source=head();before=load(precheck/'PRECHECK.json');auth=load(authenticated/'AUTHENTICATED-OWNER.json')
    require(before['status']=='PASS_TWO_VERIFIED_OWNERS_BEFORE_MODULE_KEY' and before['source']==source and before['run_id']==int(os.environ['GITHUB_RUN_ID']),'EXACT_SAME_JOB_PRECHECK')
    require(release_sources(source)==before['release_source_files'],'RELEASE_SOURCE_CHANGED_AFTER_PRECHECK')
    require(auth['status']=='PASS_AUTHENTICATED_INFINITY_LOADING_OWNER' and auth['source']==source and auth['run_id']==before['run_id'],'ACTUAL_SAME_JOB_AUTHENTICATED_INFINITY')
    require(auth['owner_producer_run']==before['loading']['producer_run'] and auth['host_result_sha256']==before['loading']['host_result_sha256'],'EXACT_VERIFIED_LOADING_OWNER')
    require(file_sha(authenticated/'INFINITY.zip')==auth['bundle']['sha256'],'AUTHENTICATED_OWNER_BYTES')
    require(file_sha(cobra_components/'catalog.json')==digest(canonical(before['cobra']['catalog'])),'EXACT_VERIFIED_COBRA_CATALOG')
    require(not out.exists(),'FRESH_PREPARED_COMBINED_OWNER_OUTPUT');out.mkdir(parents=True)
    dest=out/'components';dest.mkdir();catalog=copy.deepcopy(before['cobra']['catalog']);catalog['source']=source
    for owner,row in catalog['bundles'].items():
        target=dest/row['file']
        if owner=='INFINITY':shutil.copyfile(authenticated/'INFINITY.zip',target);catalog['bundles'][owner]=auth['bundle']
        elif owner=='CHOOSER_SHELL':catalog['bundles'][owner]=metadata_bundle(cobra_components/row['file'],row,target,source)
        else:shutil.copyfile(cobra_components/row['file'],target);require(file_sha(target)==row['sha256'],'EXACT_TESTED_OR_FROZEN_OWNER:'+owner)
    save(dest/'catalog.json',catalog)
    plan=load(loading_evidence/'stage/SOURCE-PLAN.json');require(file_sha(loading_evidence/'stage/SOURCE-PLAN.json')==before['loading']['source_plan_sha256'],'TESTED_LOADING_PLAN_UNCHANGED')
    shutil.copyfile(loading_evidence/'stage/SOURCE-PLAN.json',out/'INFINITY-SOURCE-PLAN.json')
    shutil.copyfile(authenticated/'MODULE-AUTHENTICATION.txt',out/'MODULE-AUTHENTICATION.txt')
    receipt=dict(status='PASS_COORDINATED434_PREPARED_OWNERS',source=source,run_id=int(os.environ['GITHUB_RUN_ID']),baseline_source=BASE_SOURCE,
       cobra=before['cobra'],loading=before['loading'],infinity_authentication=auth,
       catalog_sha256=file_sha(dest/'catalog.json'),release_source_files=before['release_source_files'],
       module_authentication_sha256=file_sha(out/'MODULE-AUTHENTICATION.txt'),source_plan_sha256=file_sha(out/'INFINITY-SOURCE-PLAN.json'),
       all_three_corrections_present=True,APK='NOT_BUILT_OR_SIGNED',shutdown='NOT_CHANGED_NOT_RUN',physical_Fold='PENDING',accepted_pointer_updated=False)
    _,_,changed,added,integrity=validate_combined(catalog,dest,receipt,plan)
    receipt.update(changed_payload=sorted(changed),added_payload=sorted(added),module_integrity=integrity)
    save(out/'COORDINATED-OWNERS.json',receipt)
    head();print('PASS coordinated434 exact owner ZIPs, original source authentication, native/chooser protections; no APK')

if __name__=='__main__':
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='phase',required=True)
    a=sub.add_parser('precheck')
    for name in ('cobra-components','cobra-evidence','loading-evidence','out'):a.add_argument('--'+name,type=Path,required=True)
    for name in ('cobra-run','loading-run'):a.add_argument('--'+name,type=int,required=True)
    a=sub.add_parser('finish')
    for name in ('precheck','authenticated','loading-evidence','cobra-components','out'):a.add_argument('--'+name,type=Path,required=True)
    args=vars(parser.parse_args());phase=args.pop('phase');(precheck if phase=='precheck' else finish)(**args)
