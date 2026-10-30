"""Coordinated435 owner evidence and assembly helpers; never sign an APK.

Cobra keeps its separately verified DEX. Infinity keeps its original-key
source signature. Only genuine chooser version metadata joins the owners.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from zipfile import ZipFile

HERE=Path(__file__).resolve().parent
OWNER=HERE.parent
REPO=OWNER.parents[2]
ISO=REPO/'repairs/dual-experience-isolation-2103420'
sys.path[:0]=[str(OWNER),str(ISO)]
from inventory import canonical,digest,file_sha,load,save,validate_names
from component_bundles import read_bundle,record,OWNED
from release_gate import require,component_digest
import register_release as cobra
from consolidated434.verify_from433 import CHANGED,ADDED

REPOSITORY='mahfouzhassine8-ops/project-infinity'
BRANCH='work/cobra-only-from-2103427-20261028'
LOADING_BRANCH='work/infinity-only-seamless-loading-from-2103433-20261030'
BASE_SOURCE='6f6abe78fae65046e1ef475c558957eae873130f'
VERSION=2103435
GENERATION=20
TARGETS=('INFINITY','COBRA','CHOOSER_SHELL')
METADATA='assets/experience-component-updates.properties'
LABELS=b'infinity.last_updated_in=2103435\ncobra.last_updated_in=2103435\n'
BASE_INFINITY_DEX={'dex/part-0.dex':'7e18d8092de33a4d44e299305965e9b9eb943372a9643452f6f78afe209fb215'}


def api(path):return json.loads(subprocess.check_output(['gh','api','repos/'+REPOSITORY+'/'+path]))

PREVIOUS_SOURCE='7bf6f2bddceca6dbc90e696766d9f46e3d8a69b6'
LOADING_METHODS=(
 'test_current_window.CurrentWindowLoadingTest.test_video_drawer_uses_actual_frame_for_native_busy_without_service',
 'test_current_window.CurrentWindowLoadingTest.test_native_video_frame_keeps_window_focus_and_source_ownership',
 'test_current_window.CurrentWindowLoadingTest.test_centered_busy_panel_is_retained_only_as_hidden_native_control',
 'test_current_window.CurrentWindowLoadingTest.test_actual_favourites_context_uses_dialog_focus_and_frame_capability',
 'test_integration.SourceAndSkinIntegrationTest.test_actual_xml_retains_every_original_action_geometry_and_control',
 'test_integration.SourceAndSkinIntegrationTest.test_action_payload_owner_ids_and_frame_capabilities_match',
 'test_integration.SourceAndSkinIntegrationTest.test_service_protected_definitions_and_suffix_byte_exact')

def authority_at(source):
    return json.loads(subprocess.check_output(['git','-C',str(REPO),'show',source+':repairs/dual-experience-isolation-2103420/release-authority.json']))

def protected():
    value=authority_at(BASE_SOURCE)
    require(value['generation']==18 and value['candidate_versionCode']==2103433,'EXACT_PROTECTED433_SOURCE_BASE')
    return value

def previous():
    value=authority_at(PREVIOUS_SOURCE)
    require(value['generation']==19 and value['candidate_versionCode']==2103434,'EXACT_ISSUED434_PREDECESSOR_NOT_ACCEPTANCE')
    require(value['accepted_pointer_updated'] is False and value['accepted_registry_sha256']==protected()['accepted_registry_sha256'],'RECOVERY_POINTER_FROZEN')
    return value

def verify_loading_selection(proof,selection):
    require(proof['tests']==7 and proof['failures']==proof['errors']==proof['skipped']==0,'EXACT_LOADING7_CURRENT_WINDOW_METHODS')
    require(tuple(proof['selected_methods'])==tuple(selection['methods'])==LOADING_METHODS and selection['recorded_before_execution'] is True,'EXACT_CURRENT_WINDOW_METHOD_IDENTITIES')

def successful_run(run_id,branch,path):
    row=api('actions/runs/'+str(run_id))
    require(row['status']=='completed' and row['conclusion']=='success' and row['head_branch']==branch and row['path']==path,'SUCCESSFUL_OWNER_RUN:'+str(run_id))
    return row

def artifact(run_id,name):
    rows=api('actions/runs/'+str(run_id)+'/artifacts?per_page=100')['artifacts']
    rows=[r for r in rows if r['name']==name and not r['expired']]
    require(len(rows)==1,'EXACT_OFFICIAL_ARTIFACT:'+name)
    value={k:rows[0][k] for k in ('id','name','digest','size_in_bytes')}
    require(re.fullmatch('sha256:[0-9a-f]{64}',value['digest']) is not None,'OFFICIAL_ARTIFACT_DIGEST')
    return value

def archive(row,path):
    cached=os.environ.get('COORDINATED_ARTIFACT_CACHE')
    if not path.exists() and cached:
        candidate=Path(cached)/('artifact-'+str(row['id'])+'.zip')
        if candidate.is_file():
            try:os.link(candidate,path)
            except OSError:shutil.copyfile(candidate,path)
    if not path.exists():
        with path.open('wb') as stream:
            subprocess.run(['gh','api','repos/'+REPOSITORY+'/actions/artifacts/'+str(row['id'])+'/zip'],stdout=stream,check=True)
    require(file_sha(path)==row['digest'].removeprefix('sha256:'),'OFFICIAL_ARCHIVE_BYTES:'+row['name'])
    with ZipFile(path) as z:validate_names(z)
    return path

def bind_files(path,folder,names):
    with ZipFile(path) as z:
        for name in names:
            require(not Path(name).is_absolute() and '..' not in Path(name).parts,'SAFE_EVIDENCE_MEMBER')
            require((folder/name).is_file(),'EVIDENCE_MEMBER:'+name)
            with z.open(name) as stream:pin=hashlib.file_digest(stream,'sha256').hexdigest()
            require(file_sha(folder/name)==pin,'LOCAL_EVIDENCE_CHANGED:'+name)

def checked_catalog(path,raw_sha256,expected):
    # Producer JSON is intentionally preserved as published. Whitespace is not
    # reconstructed from an object: bind both official bytes and parsed values.
    require(file_sha(path)==raw_sha256,'EXACT_VERIFIED_COBRA_CATALOG_BYTES')
    require(load(path)==expected,'EXACT_VERIFIED_COBRA_CATALOG_VALUES')
    return expected

def check_cobra(components,evidence,run_id,work):
    row=successful_run(run_id,BRANCH,'.github/workflows/infinity-saved-navigation-android.yml')
    source=row['head_sha'];catalog=load(components/'catalog.json')
    require(catalog['source']==source,'EXACT_COBRA_PRODUCER_SOURCE')
    cobra.validate_payload(protected(),catalog,components)
    receipt,selections=cobra.validate_ci(evidence,components/'catalog.json',run_id,source,protected())
    artifacts=cobra.producer_artifacts(run_id,source)
    owners=artifacts['Cobra-Cards-Prepared-Owners-'+str(run_id)]
    proof=artifacts['Cobra-Cards-Host-Evidence-'+str(run_id)]
    bind_files(archive(owners,work/'cobra-owners.zip'),components,{'catalog.json'}|{r['file'] for r in catalog['bundles'].values()})
    bind_files(archive(proof,work/'cobra-host.zip'),evidence,{'PRODUCER-RESULT.json'}|set(receipt['files']))
    return dict(producer_run=run_id,producer_source=source,artifacts=artifacts,
                producer_result_sha256=file_sha(evidence/'PRODUCER-RESULT.json'),tested_source_files=receipt['tested_source_files'],
                compiler_source_files=receipt['compiler_source_files'],selected_checks=receipt['selected_checks'],selections=selections,
                evidence_files=receipt['files'],catalog=catalog,catalog_sha256=file_sha(components/'catalog.json'))

def check_loading(evidence,run_id,work):
    row=successful_run(run_id,LOADING_BRANCH,'.github/workflows/infinity-saved-navigation-android.yml')
    proof=load(evidence/'HOST-RESULT.json');selection=load(evidence/'SELECTION.json')
    require(proof['source']==row['head_sha'] and proof['branch']==LOADING_BRANCH and proof['status']=='PASS_FOCUSED_INFINITY_LOADING_HOST_ONLY','EXACT_LOADING_PRODUCER')
    verify_loading_selection(proof,selection)
    require(proof['selected_methods']==selection['methods'] and selection['recorded_before_execution'] is True and
            file_sha(evidence/'SELECTION.json')==proof['selection_sha256'],'EXACT_LOADING_SELECTION')
    require(selection['tested_source_files']==proof['tested_source_files'],'COMPLETE_LOADING_SOURCE_BINDING')
    for name,pin in proof['tested_source_files'].items():
        require(name.startswith('repairs/infinity-seamless-loading-2103433/') and '..' not in Path(name).parts,'LOADING_SOURCE_OWNERSHIP')
        require(file_sha(REPO/name)==pin==digest(subprocess.check_output(['git','-C',str(REPO),'show',proof['source']+':'+name])),'TESTED_LOADING_SOURCE_CHANGED:'+name)
    require(file_sha(evidence/'stage/STAGE.json')==proof['stage_sha256'] and file_sha(evidence/'stage/SOURCE-PLAN.json')==proof['source_plan_sha256'],'EXACT_LOADING_STAGE')
    art=artifact(run_id,'Infinity-Seamless-Loading-Host-Evidence-'+str(run_id))
    bind_files(archive(art,work/'loading-host.zip'),evidence,{'HOST-RESULT.json','SELECTION.json','stage/STAGE.json','stage/SOURCE-PLAN.json'})
    return dict(producer_run=run_id,producer_source=proof['source'],artifact=art,host_result_sha256=file_sha(evidence/'HOST-RESULT.json'),
                tested_source_files=proof['tested_source_files'],source_plan_sha256=proof['source_plan_sha256'],
                module_manifest_sha256=proof['module_manifest_sha256'],selected_methods=proof['selected_methods'])

def verify_infinity_signature(bundle):
    firstparty=REPO/'repairs/infinity-final-closure-2103407'
    sys.path.insert(0,str(firstparty));import module_bundle
    with tempfile.TemporaryDirectory(prefix='infinity435-owner-integrity-') as temporary:
        root=Path(temporary)
        with ZipFile(bundle) as z:
            for name in z.namelist():
                prefix='payload/assets/addons/'
                if name.startswith(prefix) and name[len(prefix):].split('/')[0] in module_bundle.IDS:
                    relative=name[len(prefix):];require('..' not in Path(relative).parts,'MODULE_MEMBER_PATH')
                    path=root/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(z.read(name))
        expected,_=module_bundle.build(root);manifest=root/'script.infinity.commandcenter/INFINITY-MODULES.v1'
        require(manifest.read_bytes()==expected,'EXACT_PACKAGED76_MODULE_SOURCE_MANIFEST')
        text=subprocess.check_output(['openssl','dgst','-sha256','-verify',str(firstparty/'ORIGINAL-INFINITY-PUBLIC-KEY.pem'),'-signature',str(manifest)+'.sig',str(manifest)],text=True)
        require(text.strip()=='Verified OK','ORIGINAL_KEY_SOURCE_AUTHENTICATION')
        return dict(original_key='VERIFIED_OPENSSL_AND_EXACT_RECOMPUTED_MODULE_MANIFEST',manifest_sha256=file_sha(manifest),signature_sha256=file_sha(Path(str(manifest)+'.sig')))

def validate_combined(catalog,bundles,receipt,loading_plan):
    prior=previous();require(set(catalog['bundles'])==set(OWNED),'EXACT_COMBINED_OWNER_VECTOR')
    require(catalog['schema']==1 and catalog['package']==prior['package'] and catalog['certificate_sha256']==prior['certificate_sha256'] and catalog['release_approved'] is False,'COMBINED_IDENTITY')
    payload={};metas={}
    for owner,row in catalog['bundles'].items():
        require(row['file']==owner+'.zip','CANONICAL_OWNER_NAME');meta=read_bundle(bundles/row['file'],row);metas[owner]=meta
        require(not set(payload)&set(meta['payload']),'OVERLAPPING_OWNERS');payload.update(meta['payload'])
        require(meta['settings_schema']==prior['components'][owner]['settings_schema'],'NO_SETTINGS_MIGRATION:'+owner)
    require(catalog['bundles']['MINIMAL_ANDROID_CONTRACT']==prior['bundle_catalog']['bundles']['MINIMAL_ANDROID_CONTRACT'],'EXACT433_SHARED_NATIVE_ICONS')
    require(catalog['bundles']['COBRA']==receipt['cobra']['catalog']['bundles']['COBRA'],'EXACT_TESTED_COBRA_OWNER')
    auth=receipt['infinity_authentication'];require(catalog['bundles']['INFINITY']==auth['bundle'],'EXACT_AUTHENTICATED_INFINITY_OWNER')
    require(auth['baseline_source']==BASE_SOURCE and auth['source_plan_sha256']==receipt['loading']['source_plan_sha256'] and auth['module_manifest_sha256']==receipt['loading']['module_manifest_sha256'],'EXACT_TESTED_INFINITY_PLAN_AND_MANIFEST')
    require(metas['INFINITY']['dex']==BASE_INFINITY_DEX,'INFINITY_JAVA_DEX_EXACT433')
    old=protected()['payload'];require(set(old)<=set(payload),'NO_PROTECTED433_FEATURE_PAYLOAD_REMOVAL')
    changed={k for k in old if old[k]!=payload[k]};added=set(payload)-set(old)
    planned_changed={'member:'+n for n,r in loading_plan.items() if r['before'] is not None}
    planned_added={'member:'+n for n,r in loading_plan.items() if r['before'] is None}
    signature='member:assets/addons/script.infinity.commandcenter/INFINITY-MODULES.v1.sig';planned_changed.add(signature)
    require(changed==CHANGED|planned_changed|{'member:'+METADATA} and added==ADDED|planned_added,'EXACT_THREE_CORRECTION_PAYLOAD_DELTA')
    for name,row in loading_plan.items():
        key='member:'+name;require(payload[key]=={'owner':'INFINITY','sha256':row['after']},'EXACT_TESTED_INFINITY_MEMBER:'+name)
        require((old.get(key) or {}).get('sha256')==row['before'],'EXACT433_INFINITY_PREIMAGE:'+name)
    require(payload[signature]=={'owner':'INFINITY','sha256':auth['module_signature_sha256']},'EXACT_ORIGINAL_KEY_MODULE_SIGNATURE')
    require(set(auth['changed_payload'])==planned_changed and set(auth['added_payload'])==planned_added,'AUTHENTICATED_EXACT_SOURCE_DELTA')
    chooser=metas['CHOOSER_SHELL'];require(chooser['version']=='2103435.version-metadata.1' and chooser['approved_source']==receipt['source'],'GENUINE_CURRENT_COMPONENT_LABELS')
    with ZipFile(bundles/'CHOOSER_SHELL.zip') as z:require(z.read('payload/'+METADATA)==LABELS,'BOTH_GENUINE_COMPONENT_LABELS435')
    for owner in TARGETS:
        require(metas[owner]['digest']!=prior['components'][owner]['digest'],'ALL_THREE_APPROVED_UPDATES_PRESENT:'+owner)
    integrity=verify_infinity_signature(bundles/'INFINITY.zip')
    require(integrity['manifest_sha256']==auth['module_manifest_sha256'] and integrity['signature_sha256']==auth['module_signature_sha256'],'EXACT_AUTHENTICATED_PACKAGED_MODULE')
    return payload,metas,changed,added,integrity

def metadata_bundle(source,row,target,source_commit):
    old=read_bundle(source,row);meta=copy.deepcopy(old)
    require(old['owner']=='CHOOSER_SHELL','VERSION_METADATA_CHOOSER_OWNER_ONLY')
    meta.update(version='2103435.version-metadata.1',approved_source=source_commit)
    with ZipFile(source) as before,ZipFile(target,'w') as out:
        for name in before.namelist():
            if name=='component.json':continue
            raw=before.read(name)
            if name=='payload/'+METADATA:
                require(raw==b'infinity.last_updated_in=2103427\ncobra.last_updated_in=2103435\n','EXACT_COBRA_ONLY_PREPARED_LABELS')
                raw=LABELS;meta['members'][METADATA]['sha256']=digest(raw);meta['payload']['member:'+METADATA]['sha256']=digest(raw)
            out.writestr(record(name),raw)
        meta['digest']=component_digest(meta['payload'],'CHOOSER_SHELL');out.writestr(record('component.json'),canonical(meta))
    result=dict(file=target.name,sha256=file_sha(target),**{k:meta[k] for k in ('version','digest','approved_source','settings_schema')})
    actual=read_bundle(target,result);require(actual['dex']==old['dex'],'CHOOSER_EXECUTABLES_FROZEN')
    require(set(actual['payload'])==set(old['payload']) and {k for k in old['payload'] if old['payload'][k]!=actual['payload'][k]}=={'member:'+METADATA},'CHOOSER_GENUINE_VERSION_METADATA_ONLY')
    return result
