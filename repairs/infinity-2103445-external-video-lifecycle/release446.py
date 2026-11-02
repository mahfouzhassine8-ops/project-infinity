"""Scoped external-intent446 preparation through the existing sole original signer."""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
ISO=REPO/'repairs/dual-experience-isolation-2103420'
sys.path[:0]=[str(ISO),str(HERE),str(REPO/'repairs/cobra-2103444-rotation-audio')]
from inventory import canonical,digest,file_sha,load,save,CERT_SHA,SIGNATURE,validate_names
from component_bundles import read_bundle,record,combine
from release_gate import component_digest,normalize_manifest,require
from release_authority import transition,verify_evidence
from release445 import certificate,repack

BASE='6cf75639a46ec6b0c858ae32abc102450fdc0974'
BRANCH='work/infinity-2103445-external-video-lifecycle-20261101'
VERSION=2103446
GENERATION=33
APK_SHA='b7e78393ade7e52d8653823a0ad72ae99614a5a8e0b6cdedf5d5d15a9e643400'
DEX_SHA='d4f5f5003afe9e890d947505515f54d2ad507bf4b4fd3126ed5e2cdab751afe6'
LABEL='assets/experience-component-updates.properties'
AUTH=ISO/'release-authority.json'
WORKFLOW='.github/workflows/infinity-combined-release.yml'
LIMITATIONS=['Actual MiXplorer MIME/URI not captured; scoped video-MIME local ACTION_VIEW applicability unverified',
 'Loading overlay owner and automatic dismissal not repaired or verified',
 'Native Stop/ANR and separate SIGSEGV remain unresolved, historical producer versions unbound',
 'Android observation stopped at first-launch prompts; no real playback PASS',
 'Physical Fold acceptance pending; no lock or promotion']

def cmd(*args):return subprocess.check_output(list(map(str,args)),text=True,stderr=subprocess.STDOUT)
def previous():return json.loads(cmd('git','show',BASE+':'+str(AUTH.relative_to(REPO))))
def head_check():
    source=os.environ['GITHUB_SHA']
    require(os.environ.get('GITHUB_WORKFLOW')=='Infinity combined release | owner gate before original signing','SOLE_WORKFLOW')
    require(os.environ.get('GITHUB_REF')=='refs/heads/'+BRANCH,'EXACT_BRANCH')
    require(cmd('git','rev-parse','HEAD').strip()==source,'SOURCE_HEAD')
    require(cmd('git','ls-remote','origin','refs/heads/'+BRANCH).split()[0]==source,'REMOTE_HEAD_RACE')
    require(not cmd('git','status','--porcelain','--untracked-files=no').strip(),'DIRTY_SOURCE')
    return source

def reused_receipts():
    owner=load(HERE/'evidence/OWNER-PRESERVATION.json')
    for name,pin in owner['sources'].items():require(file_sha(REPO/name)==pin,'HOST_TESTED_SOURCE:'+name)
    require(owner['candidate_dex_sha256']==DEX_SHA and owner['unchanged_classes']==576,'EXACT_REVIEWED_OWNER')
    root=ET.parse(HERE/'evidence/CORRECTED-POLICY.xml').getroot()
    require(root.tag=='testsuite' and int(root.get('tests'))==9 and int(root.get('errors'))==0 and int(root.get('failures'))==0,'NINE_HOST_TESTS')
    tests=load(HERE/'evidence/TEST-RESULTS.json')['source_test_inputs']
    require(file_sha(HERE/'ExternalVideoIntentPolicyTest.java')==tests['candidate_test_source'],'TESTED_POLICY_SOURCE')
    require(file_sha(HERE/'BaselineExternalIntentOrderTest.java')==tests['baseline_test_source'],'BASELINE_TEST_SOURCE')
    return owner

def owner_builder():
    # Historical release helpers also import a module named build_owner. Bind
    # this preparation to the reviewed Infinity file, independent of sys.path.
    spec=importlib.util.spec_from_file_location('_infinity_external_owner446',HERE/'build_owner.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    require(Path(module.__file__).resolve()==HERE/'build_owner.py','EXACT_INFINITY_BUILDER')
    return module

def compare(baseline,candidate,plan,out,sdk=None):
    require(file_sha(baseline)==APK_SHA,'EXACT_SIGNED445_APK')
    expected={'classes3.dex',LABEL,'AndroidManifest.xml'}
    p=load(plan)
    require(p['changed_members']==['classes3.dex'] and p['candidate_dex_sha256']==DEX_SHA,'EXACT_REQUEST_RACE_PLAN')
    before={};after={};changed={}
    with ZipFile(baseline) as a,ZipFile(candidate) as b:
        an=set(validate_names(a))-set(SIGNATURE);bn=set(validate_names(b))-set(SIGNATURE)
        require(an==bn,'EXACT_APK_MEMBER_SET')
        require(normalize_manifest(a.read('AndroidManifest.xml'))[1]==2103445,'BASELINE_VERSION')
        for n in sorted(an):
            x=a.read(n);y=b.read(n);before[n]=digest(x);after[n]=digest(y)
            if x!=y:
                changed[n]={'before':before[n],'after':after[n]}
                if n=='AndroidManifest.xml':
                    require(normalize_manifest(x)[0]==normalize_manifest(y)[0] and normalize_manifest(y)[1]==VERSION,'TYPED_VERSION_ONLY')
        require(set(changed)==expected,'EXACT_APK_DELTA:'+str(set(changed)^expected))
        require(after['classes3.dex']==DEX_SHA,'EXACT_HOST_VERIFIED_DEX')
        require(b.read(LABEL)==b'infinity.last_updated_in=2103446\ncobra.last_updated_in=2103445\n','TRUTHFUL_COMPONENT_LABELS')
        frozen=[n for n in an if n.startswith(('lib/','res/')) or n=='resources.arsc' or re.fullmatch(r'classes\d*\.dex',n) and n!='classes3.dex']
        require(all(before[n]==after[n] for n in frozen),'PROTECTED_COMPILED_PAYLOAD_CHANGED')
    report={'status':'PASS_EXACT445_APK_MEMBER_COMPARISON','baseline_sha256':APK_SHA,'candidate_sha256':file_sha(candidate),
        'changed_members':changed,'unchanged_members':len(an)-3,'added':[],'removed':[],
        'native_libraries_unchanged':sum(n.startswith('lib/') and n.endswith('.so') for n in an),
        'Cobra_shared_chooser_DEX_identical':True,'all_nonversion_assets_resources_identical':True,
        'user_data':'NO_ACCESS','shutdown':'UNCHANGED_NOT_TESTED','physical_Fold':'PENDING','limitations':LIMITATIONS}
    out.mkdir(parents=True,exist_ok=True)
    if sdk:
        (out/'BASELINE-SIGNATURE.txt').write_text(certificate(baseline,sdk))
        (out/'CANDIDATE-SIGNATURE.txt').write_text(certificate(candidate,sdk))
        report['original_certificate_sha256']=CERT_SHA
    save(out/'APK-PRESERVATION.json',report)
    save(out/'ALL-APK-MEMBERS.json',{n:{'before':before[n],'after':after[n]} for n in before})
    return report

def prepare(bundles,baseline,sdk,out):
    bundles,baseline,sdk,out=[p.resolve() for p in (bundles,baseline,sdk,out)]
    source=head_check();prior=previous()
    require(prior['candidate_versionCode']==2103445 and prior['generation']==32,'EXACT_PRIOR445_AUTHORITY')
    require(not out.exists(),'FRESH_OUTPUT');out.mkdir(parents=True)
    require(file_sha(baseline)==APK_SHA,'EXACT_BASELINE_APK');certificate(baseline,sdk)
    catalog=copy.deepcopy(prior['bundle_catalog'])
    for owner,row in catalog['bundles'].items():read_bundle(bundles/row['file'],row)
    expected=reused_receipts()
    owner_builder().build(out/'owner')
    require(load(out/'owner/OWNER-PRESERVATION.json')==expected,'EXACT_HOST_TESTED_OWNER_REBUILD')
    require(file_sha(out/'owner/candidate.dex')==DEX_SHA,'EXACT_OWNER_DEX')
    dest=out/'components';dest.mkdir();catalog['source']=source
    for owner in ('COBRA','MINIMAL_ANDROID_CONTRACT'):
        shutil.copyfile(bundles/(owner+'.zip'),dest/(owner+'.zip'))
        require(file_sha(dest/(owner+'.zip'))==prior['bundle_catalog']['bundles'][owner]['sha256'],'FROZEN_OWNER_ZIP:'+owner)
    row=catalog['bundles']['INFINITY'];old=read_bundle(bundles/'INFINITY.zip',row);meta=copy.deepcopy(old)
    meta.update(version='2103446.infinity.external-request-race.1',approved_source=source)
    for n in sorted(set(expected['changed_methods'])|set(expected['new_classes'])):
        path=out/'owner/verified'/(n[1:-1]+'.smali')
        meta['payload']['class:'+n]={'owner':'INFINITY','sha256':file_sha(path)}
    require(set(old['dex'])=={'dex/part-0.dex'},'EXACT_INFINITY_PARTITION')
    meta['dex']={'dex/part-0.dex':DEX_SHA};meta['digest']=component_digest(meta['payload'],'INFINITY')
    with ZipFile(bundles/'INFINITY.zip') as z,ZipFile(dest/'INFINITY.zip','w') as target:
        for n in z.namelist():
            if n not in old['dex'] and n!='component.json':target.writestr(record(n),z.read(n))
        target.writestr(record('dex/part-0.dex'),(out/'owner/candidate.dex').read_bytes())
        target.writestr(record('component.json'),canonical(meta))
    catalog['bundles']['INFINITY']={'file':'INFINITY.zip','sha256':file_sha(dest/'INFINITY.zip'),**{k:meta[k] for k in ('version','digest','approved_source','settings_schema')}}
    read_bundle(dest/'INFINITY.zip',catalog['bundles']['INFINITY'])
    labels=b'infinity.last_updated_in=2103446\ncobra.last_updated_in=2103445\n'
    catalog['bundles']['CHOOSER_SHELL']=repack(bundles/'CHOOSER_SHELL.zip',catalog['bundles']['CHOOSER_SHELL'],dest/'CHOOSER_SHELL.zip',{LABEL:labels},'2103446.version-metadata.1',source)
    save(dest/'catalog.json',catalog)
    sources=[p for p in HERE.rglob('*') if p.is_file() and p.suffix in ('.py','.java','.json','.xml','.md') and '__pycache__' not in p.parts]
    sources += [REPO/WORKFLOW,REPO/'repairs/cobra-2103444-rotation-audio/release445.py']
    proof={'status':'PASS_INFINITY_EXTERNAL_REQUEST_OWNER_PREPARATION','source':source,'run_id':int(os.environ['GITHUB_RUN_ID']),
        'baseline':BASE,'baseline_apk_sha256':APK_SHA,'changed_members':['classes3.dex'],'candidate_dex_sha256':DEX_SHA,
        'source_files':{str(p.relative_to(REPO)):file_sha(p) for p in sources},'reused_host_tests':9,
        'Android':'OBSERVATION_BLOCKED_AT_SETUP_NOT_PLAYBACK_PASS','limitations':LIMITATIONS,'accepted_pointer_updated':False}
    save(out/'PREPARATION.json',proof)
    combine(dest,catalog,out/'combined-unsigned.apk',VERSION)
    compare(baseline,out/'combined-unsigned.apk',out/'PREPARATION.json',out/'preservation')
    head_check();publish=out/'publish';publish.mkdir()
    shutil.copytree(dest,publish/'components');shutil.copytree(out/'preservation',publish/'preservation')
    shutil.copyfile(out/'PREPARATION.json',publish/'PREPARATION.json')
    shutil.copyfile(out/'owner/OWNER-PRESERVATION.json',publish/'OWNER-PRESERVATION.json')
    print('PASS_SCOPED446_PREPARATION_NO_RELEASE_SIGNATURE')

def official(prepared,run_id):
    run=json.loads(cmd('gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/runs/'+str(run_id)))
    proof=load(prepared/'PREPARATION.json')
    require(run['status']=='completed' and run['conclusion']=='success' and run['head_sha']==proof['source'] and run['head_branch']==BRANCH and run['path']==WORKFLOW,'OFFICIAL_PRODUCER')
    require(proof['run_id']==run_id and proof['status']=='PASS_INFINITY_EXTERNAL_REQUEST_OWNER_PREPARATION' and proof['baseline']==BASE and proof['baseline_apk_sha256']==APK_SHA,'PRODUCER_IDENTITY')
    rows=json.loads(cmd('gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/runs/'+str(run_id)+'/artifacts?per_page=100'))['artifacts']
    rows=[r for r in rows if r['name']=='Infinity446-Prepared-'+str(run_id) and not r['expired']]
    require(len(rows)==1,'ONE_OFFICIAL_ARTIFACT');row={k:rows[0][k] for k in ('id','name','digest','size_in_bytes')}
    require(re.fullmatch('sha256:[0-9a-f]{64}',row['digest']) is not None,'OFFICIAL_ARTIFACT_DIGEST')
    cache=Path(os.environ.get('INFINITY446_ARTIFACT_CACHE','/tmp/infinity446-official'));cache.mkdir(parents=True,exist_ok=True)
    archive=cache/(str(row['id'])+'.zip')
    if not archive.exists():
        with archive.open('wb') as f:subprocess.run(['gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/artifacts/'+str(row['id'])+'/zip'],stdout=f,check=True)
    require(file_sha(archive)==row['digest'][7:],'OFFICIAL_ARCHIVE_BYTES')
    with ZipFile(archive) as z:
        names={n for n in validate_names(z) if not n.endswith('/')}
        require(names=={str(p.relative_to(prepared)) for p in prepared.rglob('*') if p.is_file()},'OFFICIAL_ARTIFACT_FILE_SET')
        for n in names:
            with z.open(n) as f:require(hashlib.file_digest(f,'sha256').hexdigest()==file_sha(prepared/n),'OFFICIAL_FILE:'+n)
    for n,pin in proof['source_files'].items():
        require(file_sha(REPO/n)==pin and digest(subprocess.check_output(['git','show',proof['source']+':'+n]))==pin,'TESTED_SOURCE_CHANGED:'+n)
    return row

def proposed(prepared,run_id):
    artifact=official(prepared,run_id)
    proof=load(prepared/'PREPARATION.json');catalog=load(prepared/'components/catalog.json');prior=previous()
    metas={o:read_bundle(prepared/'components'/row['file'],row) for o,row in catalog['bundles'].items()}
    payload={k:v for m in metas.values() for k,v in m['payload'].items()}
    authority=copy.deepcopy(prior)
    authority.update(generation=GENERATION,last_issued_versionCode=2103445,candidate_versionCode=VERSION,target_owners=['INFINITY','CHOOSER_SHELL'],
        update_kind='owner_update',previous_authority_sha256=digest(canonical(prior)),payload=payload,bundle_catalog=catalog,
        experience_version_labels={'INFINITY':VERSION,'COBRA':2103445})
    for o in ('INFINITY','CHOOSER_SHELL'):
        authority['components'][o]={k:metas[o][k] for k in ('version','digest','approved_source','settings_schema')}
        authority['components'][o]['revision']=prior['components'][o]['revision']+1
        authority['bundle_sources'][o]={'run_id':run_id,'build_source':proof['source'],'artifact':'Infinity446-Prepared-'+str(run_id),'path':'components/'+o+'.zip'}
    authority['source_files']={n:file_sha(REPO/n) for n in prior['source_files']}
    authority['workflow_sha256']=file_sha(REPO/WORKFLOW)
    authority['owner_update_evidence']={'owner':'INFINITY_EXTERNAL_REQUEST_RACE','producer_run':run_id,'producer_source':proof['source'],
        'source_files':proof['source_files'],'artifact':artifact,'preparation_sha256':file_sha(prepared/'PREPARATION.json'),
        'Android':'UNVERIFIED_SCOPED_TESTING_CANDIDATE_EXPLICITLY_AUTHORIZED','frozen_owners':['COBRA','MINIMAL_ANDROID_CONTRACT'],
        'reused_host_tests':9,'limitations':LIMITATIONS,'accepted_pointer_updated':False}
    transition(prior,authority,['INFINITY','CHOOSER_SHELL']);verify_evidence(authority,lambda n:(REPO/n).read_bytes())
    return authority

def register(prepared,run_id):
    authority=proposed(prepared,run_id)
    require(load(AUTH)==previous(),'AUTHORITY_PREDECESSOR');save(AUTH,authority)

def check_registered(prepared,run_id,out):
    require(proposed(prepared,run_id)==load(AUTH),'REGISTERED_EXACT_OFFICIAL_PREPARATION')
    save(out,{'status':'PASS_OFFICIAL_SOURCE_AND_OWNER_PREPARATION','run_id':run_id,'physical_Fold':'PENDING','limitations':LIMITATIONS})

if __name__=='__main__':
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='op',required=True)
    a=sub.add_parser('prepare')
    for n in ('bundles','baseline','sdk','out'):a.add_argument('--'+n,type=Path,required=True)
    for op in ('register','check_registered'):
        a=sub.add_parser(op);a.add_argument('--prepared',type=Path,required=True);a.add_argument('--run-id',type=int,required=True)
        if op=='check_registered':a.add_argument('--out',type=Path,required=True)
    a=sub.add_parser('compare')
    for n in ('baseline','candidate','plan','out','sdk'):a.add_argument('--'+n,type=Path,required=True)
    args=vars(p.parse_args());op=args.pop('op');globals()[op](**args)
