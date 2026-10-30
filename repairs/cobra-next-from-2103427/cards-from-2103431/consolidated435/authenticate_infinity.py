"""Authenticate the reviewed Infinity UI owner in the existing sole signer.

No APK signing, authority mutation, installation, runtime or shutdown execution.
Original-key access is confined to the existing approved signing workflow.
"""
import argparse
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from zipfile import ZipFile

RELEASE=Path(__file__).resolve().parent
REPO=RELEASE.parents[3]
HERE=REPO/'repairs/infinity-seamless-loading-2103433'
sys.path.insert(0,str(HERE))
ISO=REPO/'repairs/dual-experience-isolation-2103420'
sys.path.insert(0,str(ISO))
from inventory import canonical,file_sha,load,save
from component_bundles import read_bundle,record
from release_gate import require,component_digest
from signer_policy import check
from stage import generate,BASE_ZIP,CC,PREFIX

BRANCH='work/cobra-only-from-2103427-20261028'
OWNER_BRANCH='work/infinity-only-seamless-loading-from-2103433-20261030'
BASE_SOURCE='6f6abe78fae65046e1ef475c558957eae873130f'
VERSION='2103435.infinity.loading.1'

def command(args,env=None):return subprocess.check_output(list(map(str,args)),text=True,env=env)

def remote_head(expected):
    origin=command(['git','remote','get-url','origin']).strip().removesuffix('.git')
    require(origin=='https://github.com/mahfouzhassine8-ops/project-infinity','EXPECTED_ORIGIN')
    ref='refs/heads/'+BRANCH
    require(command(['git','ls-remote','origin',ref]).split()[0]==expected,'MODULE_PREPARATION_HEAD_RACE')
    require(command(['git','rev-parse','HEAD']).strip()==expected,'LOCAL_HEAD')
    require(not command(['git','status','--porcelain','--untracked-files=no']).strip(),'DIRTY_TRACKED_SOURCE')

def authenticate(baseline,evidence,out,producer_run):
    baseline,evidence,out=[p.resolve() for p in (baseline,evidence,out)]
    expected=os.environ['GITHUB_SHA']
    require(os.environ.get('GITHUB_WORKFLOW')=='Infinity combined release | owner gate before original signing','SOLE_ORIGINAL_KEY_ROUTE')
    require(os.environ.get('GITHUB_REF')=='refs/heads/'+BRANCH and os.environ.get('LOADING_OPERATION')=='authenticate-infinity-owner','AUTHORIZED_OWNER_AUTHENTICATION')
    remote_head(expected)
    previous=json.loads(subprocess.check_output(['git','show',BASE_SOURCE+':repairs/dual-experience-isolation-2103420/release-authority.json']))
    from combined_owners import previous as issued_predecessor,verify_loading_selection
    require(load(ISO/'release-authority.json')==issued_predecessor() and previous['candidate_versionCode']==2103433,'EXACT434_AUTHORITY_AND_PROTECTED433_SOURCE_BASE')
    row=previous['bundle_catalog']['bundles']['INFINITY'];require(file_sha(baseline)==row['sha256']==BASE_ZIP,'EXACT433_INFINITY_ZIP')
    run=json.loads(command(['gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/runs/'+str(producer_run)]))
    proof=load(evidence/'HOST-RESULT.json');selection=load(evidence/'SELECTION.json')
    require(run['conclusion']=='success' and run['head_branch']==OWNER_BRANCH and run['path']=='.github/workflows/infinity-saved-navigation-android.yml','SUCCESSFUL_SEPARATE_INFINITY_OWNER_PRODUCER')
    require(proof['source']==run['head_sha'] and proof['branch']==OWNER_BRANCH and proof['status']=='PASS_FOCUSED_INFINITY_LOADING_HOST_ONLY','ACTUAL_INFINITY_PRODUCER_IDENTITY')
    verify_loading_selection(proof,selection)
    require(file_sha(evidence/'SELECTION.json')==proof['selection_sha256'],'LOADING_SELECTION_UNCHANGED')
    require(proof['tested_source_files']==selection['tested_source_files'],'COMPLETE_TESTED_SOURCE_MANIFEST')
    for relative,pin in proof['tested_source_files'].items():
        require(not Path(relative).is_absolute() and '..' not in Path(relative).parts and relative.startswith(str(HERE.relative_to(REPO))+'/'),'INFINITY_SOURCE_SCOPE')
        require(file_sha(REPO/relative)==pin==hashlib.sha256(subprocess.check_output(['git','show',proof['source']+':'+relative])).hexdigest(),'TESTED_INFINITY_SOURCE_CHANGED:'+relative)
    # Bind extracted evidence to the official immutable GitHub archive, not a
    # mutable local passing receipt. Workflow also downloads by this exact run.
    artifacts=json.loads(command(['gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/runs/'+str(producer_run)+'/artifacts']))['artifacts']
    matches=[a for a in artifacts if a['name']=='Infinity-Seamless-Loading-Host-Evidence-'+str(producer_run) and not a['expired']]
    require(len(matches)==1,'EXACT_INFINITY_HOST_ARTIFACT');artifact=matches[0]
    require(re.fullmatch('sha256:[0-9a-f]{64}',artifact['digest']) is not None,'OFFICIAL_INFINITY_EVIDENCE_DIGEST')
    require(not out.exists(),'FRESH_AUTHENTICATED_OWNER_OUTPUT');out.mkdir()
    archive=out/'official-host-evidence.zip'
    with archive.open('wb') as stream:subprocess.run(['gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/artifacts/'+str(artifact['id'])+'/zip'],stdout=stream,check=True)
    require(file_sha(archive)==artifact['digest'].removeprefix('sha256:'),'IMMUTABLE_INFINITY_EVIDENCE_ARCHIVE')
    with ZipFile(archive) as z:
        for name in ('HOST-RESULT.json','SELECTION.json','stage/STAGE.json','stage/SOURCE-PLAN.json'):
            require(z.read(name)==(evidence/name).read_bytes(),'EXACT_OFFICIAL_LOADING_PROOF:'+name)
    generate(baseline,out/'stage')
    require(file_sha(out/'stage/SOURCE-PLAN.json')==proof['source_plan_sha256'],'REPRODUCED_EXACT_TESTED_SKIN_AND_SOURCE_PLAN')
    candidate=out/'stage/candidate-addons';manifest=candidate/CC/'INFINITY-MODULES.v1'
    require(file_sha(manifest)==proof['module_manifest_sha256'],'REPRODUCED_EXACT_TESTED_MODULE_MANIFEST')
    firstparty=REPO/'repairs/infinity-final-closure-2103407';verifier=out/'verify-module-bundle'
    for leaf in ('SignInfinityModules.java','verify_module_bundle.cpp','isolated-native/InfinityModuleManifest.cpp',
                 'isolated-native/InfinityModuleManifest.h','ORIGINAL-INFINITY-PUBLIC-KEY.pem','module_bundle.py'):
        relative=str((firstparty/leaf).relative_to(REPO))
        require((firstparty/leaf).read_bytes()==subprocess.check_output(['git','show',BASE_SOURCE+':'+relative]),'ORIGINAL_AUTHENTICATION_SOURCE_FROZEN:'+leaf)
    command(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',firstparty/'verify_module_bundle.cpp',firstparty/'isolated-native/InfinityModuleManifest.cpp','-lcrypto','-o',verifier])
    routes=check(load(ISO/'signer-policy.json'))
    with tempfile.TemporaryDirectory(prefix='infinity435-original-module-') as temporary:
        temp=Path(temporary);classes=temp/'classes';classes.mkdir()
        command(['java','-m','jdk.compiler/com.sun.tools.javac.Main','--release','8','-g:none','-Xlint:all,-options','-Werror','-d',classes,firstparty/'SignInfinityModules.java'])
        remote_head(expected);require(check(load(ISO/'signer-policy.json'))==routes,'SIGNER_POLICY_RACE')
        key=temp/'original.jks';key.touch(mode=0o600);key.write_bytes(base64.b64decode(os.environ['INFINITY_KEYSTORE_B64'],validate=True))
        env={n:os.environ[n] for n in ('PATH','JAVA_HOME','INFINITY_STORE_PASSWORD','INFINITY_KEY_PASSWORD','INFINITY_KEY_ALIAS')}
        authentication=command(['java','-cp',classes,'SignInfinityModules',key,manifest],env)
    authentication+=command([verifier,candidate,firstparty/'ORIGINAL-INFINITY-PUBLIC-KEY.pem'])
    require('NATIVE_VERIFIED package=0.3.5.53 protocol=1 files=76' in authentication,'EXACT_ORIGINAL_KEY_NATIVE_MODULE_AUTHENTICATION')
    (out/'MODULE-AUTHENTICATION.txt').write_text(authentication)
    changes={str(p.relative_to(out/'stage/members')):p.read_bytes() for p in (out/'stage/members').rglob('*') if p.is_file()}
    changes[PREFIX+CC+'/INFINITY-MODULES.v1.sig']=(candidate/CC/'INFINITY-MODULES.v1.sig').read_bytes()
    old=read_bundle(baseline,row);meta=copy.deepcopy(old);meta.update(version=VERSION,approved_source=expected)
    dest=out/'INFINITY.zip'
    with ZipFile(baseline) as before,ZipFile(dest,'w') as target:
        for name in before.namelist():
            if name=='component.json':continue
            member=name.removeprefix('payload/');raw=changes.get(member,before.read(name)) if name.startswith('payload/') else before.read(name)
            if name.startswith('payload/') and member in changes:
                meta['members'][member]['sha256']=hashlib.sha256(raw).hexdigest();meta['payload']['member:'+member]['sha256']=hashlib.sha256(raw).hexdigest()
            target.writestr(record(name),raw)
        for member in sorted(set(changes)-set(old['members'])):
            require(member.startswith(('assets/addons/script.infinity.commandcenter/','assets/addons/skin.infinity.diggz/')),'NEW_INFINITY_UI_MEMBER_ONLY')
            raw=changes[member];pin=hashlib.sha256(raw).hexdigest()
            meta['members'][member]=dict(compress_type=0,external_attr=0o100644<<16,sha256=pin)
            meta['payload']['member:'+member]=dict(owner='INFINITY',sha256=pin);target.writestr(record('payload/'+member),raw)
        meta['digest']=component_digest(meta['payload'],'INFINITY');target.writestr(record('component.json'),canonical(meta))
    result=dict(file='INFINITY.zip',sha256=file_sha(dest),**{k:meta[k] for k in ('version','digest','approved_source','settings_schema')})
    actual=read_bundle(dest,result);require(actual['dex']==old['dex'],'INFINITY_JAVA_DEX_EXACT433')
    require(set(old['payload'])<=set(actual['payload']),'NO_INFINITY_FEATURE_REMOVAL')
    changed={k for k in old['payload'] if actual['payload'][k]!=old['payload'][k]};added=set(actual['payload'])-set(old['payload'])
    require(changed|added=={'member:'+k for k in changes},'EXACT_TESTED_INFINITY_UI_MEMBER_DELTA')
    remote_head(expected);require(check(load(ISO/'signer-policy.json'))==routes,'SIGNER_POLICY_FINAL_RACE')
    save(out/'AUTHENTICATED-OWNER.json',dict(status='PASS_AUTHENTICATED_INFINITY_LOADING_OWNER',source=expected,run_id=int(os.environ['GITHUB_RUN_ID']),
         owner_producer_run=producer_run,owner_producer_source=proof['source'],owner_producer_artifact={k:artifact[k] for k in ('id','name','digest','size_in_bytes')},
         tested_source_files=proof['tested_source_files'],host_result_sha256=file_sha(evidence/'HOST-RESULT.json'),source_plan_sha256=proof['source_plan_sha256'],
         module_manifest_sha256=file_sha(manifest),module_signature_sha256=file_sha(candidate/CC/'INFINITY-MODULES.v1.sig'),
         baseline_source=BASE_SOURCE,baseline_component_sha256=BASE_ZIP,bundle=result,changed_payload=sorted(changed),added_payload=sorted(added),
         original_module_authentication='JCA_AND_ORIGINAL_NATIVE_VERIFIER',Cobra='NOT_INCLUDED_OR_MODIFIED',chooser='NOT_INCLUDED_OR_MODIFIED',
         native='EXACT433',APK='NOT_BUILT',shutdown='NOT_CHANGED_NOT_RUN',physical_Fold='PENDING',accepted_pointer_updated=False))
    print('PASS original-key authenticated Infinity owner; APK not built or signed')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('baseline','evidence','out'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--producer-run',type=int,required=True);authenticate(**vars(p.parse_args()))
