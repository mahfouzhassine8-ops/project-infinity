"""Original-owner release preparation/registration; no alternate APK signer."""
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
import module_bundle

BASE='7bbe08363b493146ca7ed67cb872e9a98b1d888b'
BRANCH='work/infinity-only-from-2103436-20261031'
VERSION=2103437
APK_SHA='ff8e7ec16cb10028aef50579161de92b205e97ca8131195098753fb3821bdbc6'
LABEL='assets/experience-component-updates.properties'
AUTH=ISO/'release-authority.json'

def cmd(*args,env=None):return subprocess.check_output(list(map(str,args)),text=True,env=env,stderr=subprocess.STDOUT)
def previous():return json.loads(cmd('git','show',BASE+':'+str(AUTH.relative_to(REPO))))
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
    require(file_sha(baseline)==APK_SHA,'EXACT_SIGNED436_APK')
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
        require(all(before[n]==after[n] for n in an if n.startswith('lib/') or re.fullmatch(r'classes\d*\.dex',n) or n.startswith('res/') or n=='resources.arsc'),'COMPILED_AND_NATIVE_FROZEN')
    report=dict(status='PASS_EXACT436_APK_MEMBER_COMPARISON',baseline_sha256=APK_SHA,candidate_sha256=file_sha(candidate),
                changed_members=changes,unchanged_members=len(an)-len(changes),added=[],removed=[],
                native_libraries_unchanged=sum(n.startswith('lib/') and n.endswith('.so') for n in an),all_DEX_identical=True,
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
    source=head_check();prior=previous()
    require(prior['candidate_versionCode']==2103436,'PROTECTED_PREDECESSOR')
    require(not out.exists(),'FRESH_PREPARATION');out.mkdir(parents=True)
    require(file_sha(baseline)==APK_SHA,'BASELINE_APK')
    (out/'BASELINE-SIGNATURE.txt').write_text(certificate(baseline,sdk))
    for owner,row in prior['bundle_catalog']['bundles'].items():read_bundle(bundles/row['file'],row)
    # Source tests execute before module-key access. Existing native evidence is
    # source-bound; no Android result is inferred from it.
    spec=importlib.util.spec_from_file_location('loading437_stage',HERE/'stage.py');stager=importlib.util.module_from_spec(spec);spec.loader.exec_module(stager)
    stage=out/'stage';stager.stage(bundles/'INFINITY.zip',stage)
    review=load(HERE/'results/MEMBER-SCOPE-REVIEW.json')
    staged=load(stage/'PLAN.json')['changes']
    require(review['status']=='PASS_90_MEMBER_SOURCE_SCOPE' and {r['member']:{k:r[k] for k in ('before','after','owner')} for r in review['members']}==staged,'INDIVIDUAL_MEMBER_REVIEW')
    env=os.environ.copy();env.update(BASELINE_COMPONENT=str(bundles/'INFINITY.zip'),LOADING_STAGE=str(stage),PYTHONDONTWRITEBYTECODE='1')
    require(file_sha(HERE/'overlay/script.infinity.commandcenter/action_loading.py')==load(HERE/'results/PYTHON-PRESERVATION.json')['candidate_sha256'],'REUSED_HOST_STATE_SOURCE')
    for leaf in ('test_coverage.py',):
        text=cmd(sys.executable,HERE/'tests'/leaf,env=env);(out/(leaf+'.log')).write_text(text)
    native=load(HERE/'results/FINAL-FULL-SKIN.json')
    require(native['status']=='PASS_REVIEWED_FULL_SKIN_LOADING' and native['android']=='NOT_TESTED_FOLD_PENDING','FULL_SKIN_EVIDENCE')
    require(native['definitions_sha256']==file_sha(stage/'members/assets/addons/skin.infinity.diggz/unified/Includes_InfinityActionLoading.xml'),'FULL_SKIN_EXACT_DEFINITION')
    require(native['busy_xml_sha256']==file_sha(stage/'members/assets/addons/skin.infinity.diggz/unified/DialogBusy.xml'),'FULL_SKIN_EXACT_BUSY')
    changes={str(p.relative_to(stage/'members')):p.read_bytes() for p in (stage/'members').rglob('*') if p.is_file()}
    candidate=out/'candidate-addons';candidate.mkdir()
    with ZipFile(bundles/'INFINITY.zip') as z:
        for name in z.namelist():
            if name.startswith('payload/assets/addons/') and name.split('/')[3] in module_bundle.IDS:
                p=candidate/name.removeprefix('payload/assets/addons/');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(name))
        old_manifest,_=module_bundle.build(candidate)
        require(old_manifest==(candidate/module_bundle.CC/module_bundle.MANIFEST).read_bytes(),'ORIGINAL_MODULE_MANIFEST')
        cmd('openssl','dgst','-sha256','-verify',FIRST/'ORIGINAL-INFINITY-PUBLIC-KEY.pem','-signature',candidate/module_bundle.CC/(module_bundle.MANIFEST+'.sig'),candidate/module_bundle.CC/module_bundle.MANIFEST)
        (candidate/module_bundle.CC/'action_loading.py').write_bytes(changes['assets/addons/'+module_bundle.CC+'/action_loading.py'])
        addon=candidate/module_bundle.CC/'addon.xml';raw=addon.read_bytes();revised=raw.replace(b'version="0.3.5.53"',b'version="0.3.5.54"',1);require(raw!=revised,'MODULE_VERSION');addon.write_bytes(revised)
        changes['assets/addons/'+module_bundle.CC+'/addon.xml']=revised
        for name in ('INFINITY-MODULES.v1','INFINITY-MODULES.v1.sig'):(candidate/module_bundle.CC/name).unlink()
        module_bundle.prepare(candidate)
        skin='assets/addons/skin.infinity.diggz/'
        key=skin+'addon.xml';raw=z.read('payload/'+key)
        revised=raw.replace(b'version="1.0.5.250"',b'version="1.0.5.251"',1).replace(b'addon="script.infinity.commandcenter" version="0.3.5.53"',b'addon="script.infinity.commandcenter" version="0.3.5.54"',1)
        require(raw!=revised,'SKIN_VERSION');changes[key]=revised
        for leaf in ('infinity-skin.json','Infinity-Protected-Manifest.json'):
            key=skin+leaf;meta=json.loads(z.read('payload/'+key));meta['candidate']=251
            for k in ('version','candidate_version','skin_version'):
                if k in meta:meta[k]='1.0.5.251'
            for rel in meta.get('protected_files',{}):
                if skin+rel in changes:meta['protected_files'][rel]=digest(changes[skin+rel])
            changes[key]=(json.dumps(meta,indent=2,sort_keys=True)+'\n').encode()
    # Original module authenticator, source-frozen against signed436.
    for leaf in ('SignInfinityModules.java','verify_module_bundle.cpp','isolated-native/InfinityModuleManifest.cpp','isolated-native/InfinityModuleManifest.h','ORIGINAL-INFINITY-PUBLIC-KEY.pem','module_bundle.py'):
        require((FIRST/leaf).read_bytes()==subprocess.check_output(['git','show',BASE+':'+str((FIRST/leaf).relative_to(REPO))]),'AUTHENTICATOR_FROZEN:'+leaf)
    from signer_policy import check
    routes=check(load(ISO/'signer-policy.json'));head_check()
    verifier=out/'module-verifier'
    cmd('g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',FIRST/'verify_module_bundle.cpp',FIRST/'isolated-native/InfinityModuleManifest.cpp','-lcrypto','-o',verifier)
    manifest=candidate/module_bundle.CC/module_bundle.MANIFEST
    with tempfile.TemporaryDirectory(prefix='loading437-auth-') as temp:
        t=Path(temp);classes=t/'classes';classes.mkdir()
        cmd('javac','--release','8','-g:none','-d',classes,FIRST/'SignInfinityModules.java')
        key=t/'original.jks';key.touch(mode=0o600);key.write_bytes(base64.b64decode(os.environ['INFINITY_KEYSTORE_B64'],validate=True))
        auth_env={n:os.environ[n] for n in ('PATH','JAVA_HOME','INFINITY_STORE_PASSWORD','INFINITY_KEY_PASSWORD','INFINITY_KEY_ALIAS')}
        text=cmd('java','-cp',classes,'SignInfinityModules',key,manifest,env=auth_env)
    text+=cmd(verifier,candidate,FIRST/'ORIGINAL-INFINITY-PUBLIC-KEY.pem')
    require('NATIVE_VERIFIED package=0.3.5.54 protocol=1 files=76' in text,'AUTHENTICATED_ORIGINAL_MODULES')
    (out/'MODULE-AUTHENTICATION.txt').write_text(text)
    for leaf in ('INFINITY-MODULES.v1','INFINITY-MODULES.v1.sig'):changes['assets/addons/'+module_bundle.CC+'/'+leaf]=(candidate/module_bundle.CC/leaf).read_bytes()
    dest=out/'components';dest.mkdir();catalog=copy.deepcopy(prior['bundle_catalog']);catalog['source']=source
    for owner in ('COBRA','MINIMAL_ANDROID_CONTRACT'):
        shutil.copyfile(bundles/(owner+'.zip'),dest/(owner+'.zip'))
        require(file_sha(dest/(owner+'.zip'))==prior['bundle_catalog']['bundles'][owner]['sha256'],'FROZEN_OWNER:'+owner)
    catalog['bundles']['INFINITY']=repack(bundles/'INFINITY.zip',catalog['bundles']['INFINITY'],dest/'INFINITY.zip',changes,'2103437.infinity.loading.2',source)
    labels=b'infinity.last_updated_in=2103437\ncobra.last_updated_in=2103436\n'
    catalog['bundles']['CHOOSER_SHELL']=repack(bundles/'CHOOSER_SHELL.zip',catalog['bundles']['CHOOSER_SHELL'],dest/'CHOOSER_SHELL.zip',{LABEL:labels},'2103437.version-metadata.1',source)
    save(dest/'catalog.json',catalog)
    proof=dict(status='PASS_AUTHENTICATED437_OWNER_PREPARATION',source=source,run_id=int(os.environ['GITHUB_RUN_ID']),
               baseline=BASE,baseline_apk_sha256=APK_SHA,changed_members=sorted(changes),
               source_files={str(p.relative_to(REPO)):file_sha(p) for p in HERE.rglob('*') if p.is_file() and p.suffix in ('.py','.json')},
               Android='NOT_TESTED_USER_AUTHORIZED_FOLD_ACCEPTANCE',accepted_pointer_updated=False)
    save(out/'PREPARATION.json',proof)
    combine(dest,catalog,out/'combined-unsigned.apk',VERSION)
    compare(baseline,out/'combined-unsigned.apk',out/'PREPARATION.json',out/'preservation')
    head_check();require(check(load(ISO/'signer-policy.json'))==routes,'SIGNER_POLICY_RACE')
    publish=out/'publish';publish.mkdir()
    shutil.copytree(dest,publish/'components')
    shutil.copytree(out/'preservation',publish/'preservation')
    for leaf in ('PREPARATION.json','MODULE-AUTHENTICATION.txt','BASELINE-SIGNATURE.txt','test_coverage.py.log'):
        shutil.copyfile(out/leaf,publish/leaf)
    print('PASS authenticated Infinity437 owner preparation; no APK signature created')

def official(prepared,run_id):
    run=json.loads(cmd('gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/runs/'+str(run_id)))
    proof=load(prepared/'PREPARATION.json')
    require(run['status']=='completed' and run['conclusion']=='success' and run['head_sha']==proof['source'] and run['head_branch']==BRANCH and run['path']=='.github/workflows/infinity-combined-release.yml','OFFICIAL_PRODUCER')
    require(proof['run_id']==run_id and proof['status']=='PASS_AUTHENTICATED437_OWNER_PREPARATION' and proof['baseline']==BASE and proof['baseline_apk_sha256']==APK_SHA,'PRODUCER_IDENTITY')
    rows=json.loads(cmd('gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/runs/'+str(run_id)+'/artifacts?per_page=100'))['artifacts']
    rows=[r for r in rows if r['name']=='Infinity437-Prepared-'+str(run_id) and not r['expired']]
    require(len(rows)==1,'ONE_OFFICIAL_ARTIFACT');row={k:rows[0][k] for k in ('id','name','digest','size_in_bytes')}
    require(re.fullmatch('sha256:[0-9a-f]{64}',row['digest']) is not None,'OFFICIAL_ARTIFACT_DIGEST')
    cache=Path(os.environ.get('LOADING_ARTIFACT_CACHE','/tmp/infinity437-official'));cache.mkdir(parents=True,exist_ok=True)
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
    authority.update(generation=22,last_issued_versionCode=2103436,candidate_versionCode=VERSION,target_owners=['INFINITY','CHOOSER_SHELL'],
                     update_kind='owner_update',previous_authority_sha256=digest(canonical(prior)),payload=payload,bundle_catalog=catalog,
                     experience_version_labels={'INFINITY':VERSION,'COBRA':2103436})
    for o in ('INFINITY','CHOOSER_SHELL'):
        authority['components'][o]={k:metas[o][k] for k in ('version','digest','approved_source','settings_schema')}
        authority['components'][o]['revision']=prior['components'][o]['revision']+1
        authority['bundle_sources'][o]=dict(run_id=run_id,build_source=proof['source'],artifact='Infinity437-Prepared-'+str(run_id),path='components/'+o+'.zip')
    authority['source_files']={n:file_sha(REPO/n) for n in prior['source_files']}
    authority['workflow_sha256']=file_sha(REPO/'.github/workflows/infinity-combined-release.yml')
    authority['owner_update_evidence']=dict(owner='INFINITY_LOADING_ONLY',producer_run=run_id,producer_source=proof['source'],source_files=proof['source_files'],
        artifact=artifact,preparation_sha256=file_sha(prepared/'PREPARATION.json'),Android='DEFERRED_TO_USER_FOLD_BY_EXPLICIT_AUTHORIZATION',frozen_owners=['COBRA','MINIMAL_ANDROID_CONTRACT'],accepted_pointer_updated=False)
    transition(prior,authority,['INFINITY','CHOOSER_SHELL']);verify_evidence(authority,lambda n:(REPO/n).read_bytes())
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
