"""Quality443 preparation through the existing original-key owner release protocol."""
import argparse
import base64
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
import tempfile
from zipfile import ZipFile

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
ISO=REPO/'repairs/dual-experience-isolation-2103420'
FIRST=REPO/'repairs/infinity-final-closure-2103407'
sys.path[:0]=[str(ISO),str(HERE),str(FIRST)]
from inventory import canonical,digest,file_sha,load,save,CERT_SHA,SIGNATURE,validate_names
from component_bundles import read_bundle,record,combine
from release_gate import component_digest,normalize_manifest,require
from release_authority import transition,verify_evidence

BASE='2e88f85250ef2e46952192cf0fdb42ac5af7c9c8'
BRANCH='work/cobra-2103442-end-to-end-quality-refresh-20261101'
VERSION=2103443
APK_SHA='88f968c53eb3d306db57de72419744f427554f7146f4f86e147b192f4f5e0bf5'
LABEL='assets/experience-component-updates.properties'
AUTH=ISO/'release-authority.json'
AUTHORITY_BASE=BASE

def cmd(*args,env=None):return subprocess.check_output(list(map(str,args)),text=True,env=env,stderr=subprocess.STDOUT)
def previous():return json.loads(cmd('git','show',AUTHORITY_BASE+':'+str(AUTH.relative_to(REPO))))
def head_check():
    head=os.environ['GITHUB_SHA']
    require(os.environ.get('GITHUB_WORKFLOW')=='Infinity combined release | owner gate before original signing','SOLE_SIGNER_WORKFLOW')
    require(os.environ.get('GITHUB_REF')=='refs/heads/'+BRANCH,'EXACT_BRANCH')
    require(cmd('git','rev-parse','HEAD').strip()==head,'HEAD')
    require(cmd('git','ls-remote','origin','refs/heads/'+BRANCH).split()[0]==head,'REMOTE_HEAD_RACE')
    require(not cmd('git','status','--porcelain','--untracked-files=no').strip(),'DIRTY_SOURCE')
    return head

def repack(path,row,out,changes,version,source):
    old=read_bundle(path,row);meta=copy.deepcopy(old)
    require(set(changes)<=set(meta['members']),'NO_UNDECLARED_NEW_MEMBERS')
    meta.update(version=version,approved_source=source)
    with ZipFile(path) as z,ZipFile(out,'w') as dest:
        for name in z.namelist():
            if name=='component.json':continue
            member=name.removeprefix('payload/')
            raw=changes[member] if name.startswith('payload/') and member in changes else z.read(name)
            if name.startswith('payload/') and member in changes:
                meta['members'][member]['sha256']=digest(raw)
                meta['payload']['member:'+member]['sha256']=digest(raw)
            dest.writestr(record(name),raw)
        meta['digest']=component_digest(meta['payload'],meta['owner'])
        dest.writestr(record('component.json'),canonical(meta))
    result=dict(file=out.name,sha256=file_sha(out),**{k:meta[k] for k in ('version','digest','approved_source','settings_schema')})
    actual=read_bundle(out,result)
    require(actual['dex']==old['dex'],'ALL_DEX_FROZEN')
    require({k for k in old['payload'] if actual['payload'][k]!=old['payload'][k]}=={'member:'+n for n in changes},'EXACT_OWNER_DELTA')
    return result

def certificate(apk,sdk):
    text=cmd(sdk/'apksigner','verify','--verbose','--print-certs',apk)
    match=re.search(r'Signer #1 certificate SHA-256 digest: ([0-9a-f]+)',text)
    require(match is not None and match.group(1)==CERT_SHA,'ORIGINAL_CERTIFICATE')
    return text

def compare(baseline,candidate,plan,out,sdk=None):
    require(file_sha(baseline)==APK_SHA,'EXACT_SIGNED442_APK')
    expected=set(load(plan)['changed_members'])|{LABEL,'AndroidManifest.xml'}
    before={};after={};changes={}
    with ZipFile(baseline) as a,ZipFile(candidate) as b:
        an=set(validate_names(a))-set(SIGNATURE);bn=set(validate_names(b))-set(SIGNATURE)
        require(an==bn,'EXACT_APK_MEMBER_SET')
        for n in sorted(an):
            x=a.read(n);y=b.read(n);before[n]=digest(x);after[n]=digest(y)
            if x!=y:
                changes[n]=dict(before=before[n],after=after[n])
                if n=='AndroidManifest.xml':
                    require(normalize_manifest(x)[0]==normalize_manifest(y)[0] and normalize_manifest(y)[1]==VERSION,'TYPED_VERSION_ONLY')
        require(set(changes)==expected,'EXACT_APK_DELTA:'+str(set(changes)^expected))
        require(all(before[n]==after[n] for n in an if n.startswith('lib/') or n in ('classes.dex','classes2.dex','classes3.dex') or n.startswith('res/') or n=='resources.arsc'),'COMPILED_AND_NATIVE_FROZEN')
    report=dict(status='PASS_EXACT442_APK_MEMBER_COMPARISON',baseline_sha256=APK_SHA,candidate_sha256=file_sha(candidate),
                changed_members=changes,unchanged_members=len(an)-len(changes),added=[],removed=[],
                native_libraries_unchanged=sum(n.startswith('lib/') and n.endswith('.so') for n in an),Infinity_shared_chooser_DEX_identical=True,
                user_data='NO_ACCESS',shutdown='UNCHANGED_NOT_TESTED',physical_Fold='PENDING')
    out.mkdir(parents=True,exist_ok=True)
    if sdk:
        (out/'BASELINE-SIGNATURE.txt').write_text(certificate(baseline,sdk))
        (out/'CANDIDATE-SIGNATURE.txt').write_text(certificate(candidate,sdk))
        report['original_certificate_sha256']=CERT_SHA
    save(out/'APK-PRESERVATION.json',report)
    save(out/'ALL-APK-MEMBERS.json',{n:dict(before=before[n],after=after[n]) for n in before})
    return report

def prepare(bundles,baseline,sdk,out):
    bundles,baseline,sdk,out=[p.resolve() for p in (bundles,baseline,sdk,out)]
    source=head_check();prior=previous();require(prior['candidate_versionCode']==2103442,'EXACT_PRIOR442_AUTHORITY')
    require(not out.exists(),'FRESH_OUTPUT');out.mkdir(parents=True)
    require(file_sha(baseline)==APK_SHA,'EXACT_BASELINE_APK');certificate(baseline,sdk)
    catalog=copy.deepcopy(json.loads(cmd('git','show',BASE+':'+str(AUTH.relative_to(REPO))))['bundle_catalog'])
    for owner,row in catalog['bundles'].items():read_bundle(bundles/row['file'],row)
    for name,pin in load(HERE/'final-evidence/OWNER-BUILD.json')['sources'].items():require(file_sha(REPO/name)==pin,'HOST_TESTED_SOURCE:'+name)
    require(load(HERE/'final-evidence/TEST-RESULTS.json')['status']=='PASS_COBRA_QUALITY_FOCUSED_HOST','FOCUSED_HOST')
    import build_owner
    env_old=os.environ.get('CARDS_BASELINE_BUNDLE');os.environ['CARDS_BASELINE_BUNDLE']=str(bundles/'COBRA.zip')
    build_owner.build(out/'owner')
    observed=load(out/'owner/OWNER-BUILD.json')
    expected=load(HERE/'final-evidence/OWNER-BUILD.json')
    print('OWNER_RECEIPT_DIFFERENCES', {k:dict(expected=expected.get(k),actual=observed.get(k)) for k in expected.keys()|observed.keys() if expected.get(k)!=observed.get(k)},flush=True)
    require(observed==expected,'EXACT_HOST_TESTED_OWNER_BUILD')
    require(load(out/'owner/CLASS-HASHES.json')==load(HERE/'final-evidence/CLASS-HASHES.json'),'EXACT_HOST_TESTED_CLASS_DEFINITIONS')
    import verify_owner
    verify_owner.verify(out/'owner',out/'owner-preservation')
    preservation=load(out/'owner-preservation/OWNER-PRESERVATION.json');reviewed=load(HERE/'final-evidence/OWNER-PRESERVATION.json')
    print('OWNER_PRESERVATION_DIFFERENCES',{k:dict(expected=reviewed.get(k),actual=preservation.get(k)) for k in reviewed.keys()|preservation.keys() if reviewed.get(k)!=preservation.get(k)},flush=True)
    require(preservation==reviewed,'EXACT_REVIEWED_OWNER_PRESERVATION')
    require(observed['dex']['part-1.dex']==read_bundle(bundles/'COBRA.zip',catalog['bundles']['COBRA'])['dex']['dex/part-1.dex'],'UNRELATED_SECOND_DEX_FROZEN')
    require(observed['unchanged']==7172,'EXACT_QUALITY_AND_METADATA_BOUNDARY')
    dest=out/'components';dest.mkdir();catalog['source']=source
    for owner in ('INFINITY','MINIMAL_ANDROID_CONTRACT'):shutil.copyfile(bundles/(owner+'.zip'),dest/(owner+'.zip'))
    row=catalog['bundles']['COBRA'];old=read_bundle(bundles/'COBRA.zip',row);meta=copy.deepcopy(old)
    meta.update(version='2103443.cobra.1',approved_source=source)
    for n in observed['changed']+observed['added']:
        matches=list((out/'owner').glob('verify-part-*/'+n[1:-1]+'.smali'));require(len(matches)==1,'CLASS_DEFINITION')
        meta['payload']['class:'+n]={'owner':'COBRA','sha256':file_sha(matches[0])}
    meta['dex']={'dex/'+n:pin for n,pin in observed['dex'].items()};meta['digest']=component_digest(meta['payload'],'COBRA')
    with ZipFile(bundles/'COBRA.zip') as z,ZipFile(dest/'COBRA.zip','w') as target:
        for n in z.namelist():
            if n not in old['dex'] and n!='component.json':target.writestr(record(n),z.read(n))
        for n,pin in meta['dex'].items():target.writestr(record(n),(out/'owner/owner-dex/COBRA'/Path(n).name).read_bytes())
        target.writestr(record('component.json'),canonical(meta))
    catalog['bundles']['COBRA']=dict(file='COBRA.zip',sha256=file_sha(dest/'COBRA.zip'),**{k:meta[k] for k in ('version','digest','approved_source','settings_schema')})
    read_bundle(dest/'COBRA.zip',catalog['bundles']['COBRA'])
    labels=b'infinity.last_updated_in=2103437\ncobra.last_updated_in=2103443\n'
    catalog['bundles']['CHOOSER_SHELL']=repack(bundles/'CHOOSER_SHELL.zip',catalog['bundles']['CHOOSER_SHELL'],dest/'CHOOSER_SHELL.zip',{LABEL:labels},'2103443.version-metadata.1',source)
    save(dest/'catalog.json',catalog)
    proof=dict(status='PASS_COBRA_QUALITY_OWNER_PREPARATION',source=source,run_id=int(os.environ['GITHUB_RUN_ID']),baseline=BASE,baseline_apk_sha256=APK_SHA,changed_members=['classes4.dex'],source_files={str(p.relative_to(REPO)):file_sha(p) for p in HERE.rglob('*') if p.is_file() and p.suffix in ('.py','.java','.json')},Android='PHYSICAL_FOLD_PENDING',accepted_pointer_updated=False)
    for n,pin in observed['sources'].items():proof['source_files'][n]=pin
    save(out/'PREPARATION.json',proof)
    combine(dest,catalog,out/'combined-unsigned.apk',VERSION);compare(baseline,out/'combined-unsigned.apk',out/'PREPARATION.json',out/'preservation')
    head_check();publish=out/'publish';publish.mkdir();shutil.copytree(dest,publish/'components');shutil.copytree(out/'preservation',publish/'preservation')
    for leaf in ('PREPARATION.json',):shutil.copyfile(out/leaf,publish/leaf)
    print('PASS measured Cobra presentation owners; no APK signature created')

def official(prepared,run_id):
    run=json.loads(cmd('gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/runs/'+str(run_id)))
    proof=load(prepared/'PREPARATION.json')
    require(run['status']=='completed' and run['conclusion']=='success' and run['head_sha']==proof['source'] and run['head_branch']==BRANCH and run['path']=='.github/workflows/infinity-combined-release.yml','OFFICIAL_PRODUCER')
    require(proof['run_id']==run_id and proof['status']=='PASS_COBRA_QUALITY_OWNER_PREPARATION' and proof['baseline']==BASE and proof['baseline_apk_sha256']==APK_SHA,'PRODUCER_IDENTITY')
    rows=json.loads(cmd('gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/runs/'+str(run_id)+'/artifacts?per_page=100'))['artifacts']
    rows=[r for r in rows if r['name']=='Infinity443-Prepared-'+str(run_id) and not r['expired']]
    require(len(rows)==1,'ONE_OFFICIAL_ARTIFACT');row={k:rows[0][k] for k in ('id','name','digest','size_in_bytes')}
    require(re.fullmatch('sha256:[0-9a-f]{64}',row['digest']) is not None,'OFFICIAL_ARTIFACT_DIGEST')
    cache=Path(os.environ.get('LOADING_ARTIFACT_CACHE','/tmp/infinity443-official'));cache.mkdir(parents=True,exist_ok=True)
    archive=cache/(str(row['id'])+'.zip')
    if not archive.exists():
        with archive.open('wb') as f:subprocess.run(['gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/artifacts/'+str(row['id'])+'/zip'],stdout=f,check=True)
    require(file_sha(archive)==row['digest'][7:],'OFFICIAL_ARCHIVE_BYTES')
    with ZipFile(archive) as z:
        names=set(validate_names(z));names={n for n in names if not n.endswith('/')}
        require(names=={str(p.relative_to(prepared)) for p in prepared.rglob('*') if p.is_file()},'OFFICIAL_ARTIFACT_FILE_SET')
        for n in names:
            with z.open(n) as f:require(hashlib.file_digest(f,'sha256').hexdigest()==file_sha(prepared/n),'OFFICIAL_FILE:'+n)
    for n,pin in proof['source_files'].items():
        require(file_sha(REPO/n)==pin and digest(subprocess.check_output(['git','show',proof['source']+':'+n]))==pin,'TESTED_SOURCE_CHANGED:'+n)
    return row

def proposed(prepared,run_id):
    artifact=official(prepared,run_id)
    proof=load(prepared/'PREPARATION.json');catalog=load(prepared/'components/catalog.json');prior=previous()
    run=json.loads(cmd('gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/runs/'+str(run_id)))
    require(run['conclusion']=='success' and run['head_sha']==proof['source'] and run['head_branch']==BRANCH and run['path']=='.github/workflows/infinity-combined-release.yml','OFFICIAL_PRODUCER')
    for n,pin in proof['source_files'].items():require(file_sha(REPO/n)==pin,'TESTED_SOURCE_CHANGED:'+n)
    metas={o:read_bundle(prepared/'components'/row['file'],row) for o,row in catalog['bundles'].items()}
    payload={k:v for m in metas.values() for k,v in m['payload'].items()}
    authority=copy.deepcopy(prior)
    authority.update(generation=30,last_issued_versionCode=2103442,candidate_versionCode=VERSION,target_owners=['COBRA','CHOOSER_SHELL'],
                     update_kind='owner_update',previous_authority_sha256=digest(canonical(prior)),payload=payload,bundle_catalog=catalog,
                     experience_version_labels={'INFINITY':2103437,'COBRA':VERSION})
    for o in ('COBRA','CHOOSER_SHELL'):
        authority['components'][o]={k:metas[o][k] for k in ('version','digest','approved_source','settings_schema')}
        authority['components'][o]['revision']=prior['components'][o]['revision']+1
        authority['bundle_sources'][o]=dict(run_id=run_id,build_source=proof['source'],artifact='Infinity443-Prepared-'+str(run_id),path='components/'+o+'.zip')
    authority['source_files']={n:file_sha(REPO/n) for n in prior['source_files']}
    authority['workflow_sha256']=file_sha(REPO/'.github/workflows/infinity-combined-release.yml')
    authority['owner_update_evidence']=dict(owner='COBRA_QUALITY_PRESENTATION_REFRESH',producer_run=run_id,producer_source=proof['source'],source_files=proof['source_files'],
        artifact=artifact,preparation_sha256=file_sha(prepared/'PREPARATION.json'),Android='DEFERRED_TO_USER_FOLD_BY_EXPLICIT_AUTHORIZATION',frozen_owners=['INFINITY','MINIMAL_ANDROID_CONTRACT'],accepted_pointer_updated=False)
    transition(prior,authority,['COBRA','CHOOSER_SHELL']);verify_evidence(authority,lambda n:(REPO/n).read_bytes())
    return authority

def register(prepared,run_id):
    authority=proposed(prepared,run_id)
    require(load(AUTH)==previous(),'AUTHORITY_PREDECESSOR');save(AUTH,authority)

def check_registered(prepared,run_id,out):
    require(proposed(prepared,run_id)==load(AUTH),'REGISTERED_EXACT_OFFICIAL_PREPARATION')
    save(out,dict(status='PASS_OFFICIAL_SOURCE_AND_OWNER_PREPARATION',run_id=run_id,Android='FOLD_PENDING'))

if __name__=='__main__':
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='op',required=True)
    a=sub.add_parser('prepare')
    for n in ('bundles','baseline','sdk','out'):a.add_argument('--'+n,type=Path,required=True)
    a=sub.add_parser('register');a.add_argument('--prepared',type=Path,required=True);a.add_argument('--run-id',type=int,required=True)
    a=sub.add_parser('check_registered');a.add_argument('--prepared',type=Path,required=True);a.add_argument('--run-id',type=int,required=True);a.add_argument('--out',type=Path,required=True)
    a=sub.add_parser('compare')
    for n in ('baseline','candidate','plan','out','sdk'):a.add_argument('--'+n,type=Path,required=True)
    args=vars(p.parse_args());op=args.pop('op');globals()[op](**args)
