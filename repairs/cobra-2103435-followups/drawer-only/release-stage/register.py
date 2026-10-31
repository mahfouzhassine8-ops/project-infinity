"""Register exact official drawer-only owner preparation; never accept/lock.

Original APK signing remains in the existing sole guarded workflow. This
validator also runs there before keys, on independently downloaded evidence.
"""
import argparse
import copy
import subprocess
from pathlib import Path
from zipfile import ZipFile
from prepare import *
from release_authority import transition,verify_evidence

BRANCH='work/cobra-only-from-2103435-20261031'
REPO_NAME='mahfouzhassine8-ops/project-infinity'
AUTHORITY=ISO/'release-authority.json'

def api(path):return json.loads(subprocess.check_output(['gh','api','repos/'+REPO_NAME+'/'+path]))
def previous():return json.loads(subprocess.check_output(['git','-C',str(REPO),'show',BASE+':repairs/dual-experience-isolation-2103420/release-authority.json']))
def artifact(run_id,name):
    values=[r for r in api('actions/runs/'+str(run_id)+'/artifacts?per_page=100')['artifacts'] if r['name']==name and not r['expired']]
    assert len(values)==1 and re.fullmatch('sha256:[0-9a-f]{64}',values[0]['digest'])
    return {k:values[0][k] for k in ['id','name','digest','size_in_bytes']}

def bind_archive(row,folder):
    cache=Path(os.environ.get('DRAWER_ARTIFACT_CACHE',str(folder.parent/'official-archives')));cache.mkdir(parents=True,exist_ok=True)
    path=cache/('artifact-'+str(row['id'])+'.zip')
    if not path.exists():
        with path.open('wb') as out:subprocess.run(['gh','api','repos/'+REPO_NAME+'/actions/artifacts/'+str(row['id'])+'/zip'],stdout=out,check=True)
    assert file_sha(path)==row['digest'].removeprefix('sha256:'),'Official artifact bytes must match before any extraction trust'
    with ZipFile(path) as z:
        names=validate_names(z);assert set(names)=={p.name for p in folder.iterdir() if p.is_file()}
        for n in names:assert Path(n).name==n and digest(z.read(n))==file_sha(folder/n)

def payload(catalog,bundles,prior):
    assert set(catalog['bundles'])==set(prior['bundle_catalog']['bundles'])
    assert catalog['package']==prior['package'] and catalog['certificate_sha256']==CERT_SHA and catalog['release_approved'] is False
    metas={o:read_bundle(bundles/r['file'],r) for o,r in catalog['bundles'].items()}
    actual={}
    for o,m in metas.items():
        assert not actual.keys()&m['payload'].keys();actual.update(m['payload'])
        assert m['settings_schema']==prior['components'][o]['settings_schema']
        if o in ['INFINITY','MINIMAL_ANDROID_CONTRACT']:assert catalog['bundles'][o]==prior['bundle_catalog']['bundles'][o]
        else:assert m['approved_source']==catalog['source']
    old=prior['payload'];assert old.keys()<=actual.keys()
    expected={'class:Lcom/projectinfinity/kodi/InfinityLiveActivity;','class:Lcom/projectinfinity/kodi/CobraCardsLayout$State;','class:'+COMPONENT,'member:'+LABEL}
    assert {k for k in old if old[k]!=actual[k]}==expected
    assert actual.keys()-old.keys()=={'class:Lcom/projectinfinity/kodi/CobraCardsDrawerViewport;','class:Lcom/projectinfinity/kodi/CobraCardsDrawerViewport$Journey;'}
    assert all(actual[n]['owner']=='COBRA' for n in expected-{'member:'+LABEL}|(actual.keys()-old.keys()))
    assert metas['COBRA']['version']=='2103436.cobra.1' and metas['CHOOSER_SHELL']['version']=='2103436.version-metadata.1'
    with ZipFile(bundles/'CHOOSER_SHELL.zip') as z:assert z.read('payload/'+LABEL)==b'infinity.last_updated_in=2103435\ncobra.last_updated_in=2103436\n'
    return actual,metas

def inspect(run_id,evidence,mutable,bundles):
    run=api('actions/runs/'+str(run_id))
    assert run['status']=='completed' and run['conclusion']=='success' and run['head_branch']==BRANCH and run['path']=='.github/workflows/infinity-saved-navigation-android.yml'
    arts={k:artifact(run_id,k+'-'+str(run_id)) for k in ['Cobra-Drawer436-Mutable-Owners','Cobra-Drawer436-Preparation-Evidence']}
    bind_archive(arts['Cobra-Drawer436-Mutable-Owners'],mutable);bind_archive(arts['Cobra-Drawer436-Preparation-Evidence'],evidence)
    proof=load(evidence/'PRODUCER.json');assert proof['status']=='PASS_DRAWER436_EXACT_OWNER_AND_UNSIGNED_APK_PREPARATION'
    assert proof['run_id']==run_id and proof['source']==run['head_sha'] and proof['baseline_source']==BASE and proof['baseline_APK_sha256']==APK_SHA
    assert proof['reused_host_tests']==5 and proof['host_tests_rerun'] is False and proof['original_key']=='NOT_ACCESSED' and proof['accepted_pointer_updated'] is False
    for n,pin in proof['files'].items():assert Path(n).name==n and file_sha(evidence/n)==pin
    for n,pin in proof['source_files'].items():
        assert file_sha(REPO/n)==pin and digest(subprocess.check_output(['git','show',proof['source']+':'+n]))==pin,n
    build=load(evidence/'OWNER-BUILD.json');pinned=load(TASK/'correction-host/OWNER-BUILD.json')
    for k in ['compiler_sources','changed_methods','new_classes','unchanged_classes','output_DEX']:assert build[k]==pinned[k],k
    prepared=load(evidence/'PREPARATION.json');comparison=load(evidence/'APK-PRESERVATION.json');catalog=load(mutable/'catalog.json')
    assert prepared['source']==proof['source'] and prepared['component_catalog']==catalog==proof['component_catalog']
    assert comparison['status']=='PASS_ACTUAL_UNSIGNED436_VS_ORIGINAL_SIGNED435_FULL_MEMBER_COMPARISON'
    assert comparison['baseline_signed_APK_sha256']==APK_SHA and comparison['baseline_original_certificate_sha256']==CERT_SHA
    assert comparison['unchanged_native_libraries']==47 and set(comparison['changed_unsigned_members'])=={'classes4.dex',LABEL,'AndroidManifest.xml'}
    assert comparison['all_members_inventory_sha256']==file_sha(evidence/'ALL-APK-MEMBERS.json')
    for o in ['COBRA','CHOOSER_SHELL']:assert file_sha(mutable/(o+'.zip'))==catalog['bundles'][o]['sha256']
    assert load(bundles/'catalog.json')==catalog
    current,metas=payload(catalog,bundles,previous())
    return dict(proof=proof,artifacts=arts,catalog=catalog,payload=current,metas=metas,comparison=comparison,producer_sha256=file_sha(evidence/'PRODUCER.json'))

def proposed(checked,run_id):
    prior=previous();authority=copy.deepcopy(prior);catalog=checked['catalog'];proof=checked['proof']
    authority.update(generation=21,last_issued_versionCode=2103435,candidate_versionCode=VERSION,target_owners=['COBRA','CHOOSER_SHELL'],update_kind='owner_update',previous_authority_sha256=digest(canonical(prior)),payload=checked['payload'],bundle_catalog=catalog,experience_version_labels={'INFINITY':2103435,'COBRA':VERSION})
    for o in ['COBRA','CHOOSER_SHELL']:
        m=checked['metas'][o];authority['components'][o]={k:m[k] for k in ['version','digest','approved_source','settings_schema']};authority['components'][o]['revision']=prior['components'][o]['revision']+1
        authority['bundle_sources'][o]=dict(run_id=run_id,build_source=proof['source'],artifact='Cobra-Drawer436-Mutable-Owners-'+str(run_id),path=o+'.zip')
    authority['source_files']={n:file_sha(REPO/n) for n in prior['source_files']}
    authority['workflow_sha256']=file_sha(REPO/'.github/workflows/infinity-combined-release.yml')
    authority['owner_update_evidence']=dict(owner='COBRA_DRAWER_ONLY',producer_run=run_id,producer_source=proof['source'],artifacts=checked['artifacts'],producer_sha256=checked['producer_sha256'],authorization=str((HERE/'SCOPE.json').relative_to(REPO)),functional_source=CORRECTION,host_tests_reused=5,source_files=proof['source_files'],frozen_owners=['INFINITY','MINIMAL_ANDROID_CONTRACT'],chooser='Version metadata only; executable/UI frozen',media_review='CONTACT_SHEETS_NOT_ACCESSIBLE; NOT_REVIEWED; user latest instruction is conditional on accessible bytes',Android_runtime='PENDING_ON_SAME_ONCE_SIGNED_CANDIDATE; do not deliver until PASS',physical_Fold='USER_ACCEPTANCE_PENDING',accepted_pointer_updated=False)
    transition(prior,authority,['COBRA','CHOOSER_SHELL']);verify_evidence(authority,lambda n:(REPO/n).read_bytes())
    return authority

def register(run_id,evidence,mutable,bundles,out,apply=False):
    assert load(AUTHORITY)==previous(),'Exact435 authority before436 registration'
    checked=inspect(run_id,evidence,mutable,bundles);authority=proposed(checked,run_id);assert not out.exists();save(out,authority)
    if apply:save(AUTHORITY,authority)
    print('PASS exact official436 preparation '+('registered' if apply else 'proposed')+'; physical acceptance/locks unchanged')

def check_registered(run_id,evidence,mutable,bundles,out):
    checked=inspect(run_id,evidence,mutable,bundles);authority=proposed(checked,run_id);assert authority==load(AUTHORITY)
    save(out,dict(status='PASS_OFFICIAL436_REGISTERED_SOURCE_OWNER_AND_VERSION_METADATA',run_id=run_id,producer_sha256=checked['producer_sha256'],source=checked['proof']['source'],APK_key='NOT_ACCESSED',shutdown='NOT_RUN'))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('operation',choices=['register','check-registered']);p.add_argument('--run-id',type=int,required=True)
    for n in ['evidence','mutable','bundles','out']:p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--apply',action='store_true');a=vars(p.parse_args());op=a.pop('operation')
    if op=='check-registered':assert not a.pop('apply');check_registered(**a)
    else:register(**a)
