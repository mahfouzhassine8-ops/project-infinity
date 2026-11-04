"""Exact 453 -> UI454 / functional453 recovery455, original signer only."""
import argparse
import base64
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
REPO=HERE.parents[1]
ISO=REPO/'repairs/dual-experience-isolation-2103420'
FIRST=REPO/'repairs/infinity-final-closure-2103407'
UI=REPO/'repairs/infinity-kodi-2103453-ui-navigation'
sys.path[:0]=[str(ISO),str(FIRST)]
from inventory import canonical,digest,file_sha,load,save,CERT_SHA,SIGNATURE,validate_names
from release_gate import normalize_manifest,require,component_digest
from component_bundles import read_bundle,record,combine
from release_authority import transition,verify_evidence
import module_bundle

BASE='cb7c6214807b79661e397cccb0740fc91fab3e24'
SOURCE='1cc7684bd05581c21f31682cdb0f2d4e156a585e'
READY='fd8a7dbace118a908508f324a5a8ba0a70d765aa'
BRANCH='work/infinity-kodi-ui-2103454-2103455-packaging-20261104'
APK_SHA='08ca19e9ff01e3830253980028dbcdbfb36056fd71b06a18cbfb922158ceaac8'
NATIVE='lib/arm64-v8a/libkodi.so'
NATIVE_SHA='d0b6f115e839fbe39e764e2fecad47418c501ab1ece853294578652cd0b80b98'
CC='assets/addons/script.infinity.commandcenter/'
SKIN='assets/addons/skin.infinity.diggz/'
LABEL='assets/experience-component-updates.properties'
AUTH=ISO/'release-authority.json'
TARGETS=['INFINITY','CHOOSER_SHELL']
RUNTIME='PENDING_NO_CONNECTED_COMPATIBLE_ANDROID_TARGET'
VERSIONS=(2103454,2103455)
META={LABEL,CC+'addon.xml',CC+'INFINITY-MODULES.v1',CC+'INFINITY-MODULES.v1.sig',SKIN+'addon.xml',SKIN+'infinity-skin.json',SKIN+'Infinity-Protected-Manifest.json'}
CONTROLS={'.github/workflows/infinity-combined-release.yml','repairs/dual-experience-isolation-2103420/release_gate.py','repairs/dual-experience-isolation-2103420/release-authority.json'}
ASSETS={
 'baseline':(13301200085,41783963413,'Infinity-Combined-Original-Signer-41783963413',328422749,'3b336697af5a9ff309c2f32d94a2305688a540cdd05b5f03c8646f8ff2a74516'),
 'components':(13301010393,41783963413,'Infinity-Combined-Owner-Components-41783963413',319128584,'20c691a4a6837b53dc9288b2ad24f5c9b47bf7c6eaa6d72841e5ba95eeadfa4e')}

def cmd(*args,**kw):
    return subprocess.check_output(list(map(str,args)),text=True,**kw)

def baseline_authority():
    return json.loads(cmd('git','show',BASE+':'+str(AUTH.relative_to(REPO))))

def original(path,commit=READY):
    return subprocess.check_output(['git','show',commit+':'+str(path.relative_to(REPO))])

def source_bindings():
    paths=[HERE/n for n in ('release_ui.py','recovery_checks.py','test_packaging.py','AUTHORIZATION.md')]
    paths += [UI/'SOURCE-PLAN.json',UI/'release-readiness/PROPOSED-MEMBER-ALLOWLIST.json',
              UI/'release-readiness/BASELINE-PROTECTED-MEMBER-HASHES.json']
    paths += [UI/'overlay'/n for n in load(UI/'SOURCE-PLAN.json')['changes']]
    return {str(p.relative_to(REPO)):file_sha(p) for p in sorted(paths)}

def head_check():
    require(os.environ.get('GITHUB_WORKFLOW')=='Infinity combined release | owner gate before original signing','SOLE_SIGNER_WORKFLOW')
    require(os.environ.get('GITHUB_REF')=='refs/heads/'+BRANCH,'EXACT_PACKAGING_BRANCH')
    head=os.environ['GITHUB_SHA']
    require(cmd('git','rev-parse','HEAD').strip()==head,'SOURCE_HEAD')
    require(cmd('git','ls-remote','origin','refs/heads/'+BRANCH).split()[0]==head,'REMOTE_HEAD_RACE')
    require(not cmd('git','status','--porcelain','--untracked-files=no').strip(),'DIRTY_TRACKED_SOURCE')
    changed=cmd('git','diff','--name-only',READY,'HEAD').splitlines()
    require(changed and all(n.startswith(str(HERE.relative_to(REPO))+'/') or n in CONTROLS for n in changed),'UNRELATED_SOURCE_CHANGE')
    for n in load(UI/'SOURCE-PLAN.json')['changes']:
        p=UI/'overlay'/n
        require(p.read_bytes()==original(p,SOURCE),'EXACT_UI_CHECKPOINT:'+n)
    for p in list(FIRST.glob('*.py'))+[FIRST/'SignInfinityModules.java',FIRST/'ORIGINAL-INFINITY-PUBLIC-KEY.pem',FIRST/'InfinityInstalledModules.java.in',FIRST/'isolated-native/InfinityModuleManifest.cpp',FIRST/'isolated-native/InfinityModuleManifest.h']:
        require(p.read_bytes()==original(p),'TRUST_IMPLEMENTATION_FROZEN:'+str(p))
    require((ISO/'accepted-combined-release.json').read_bytes()==original(ISO/'accepted-combined-release.json'),'ACCEPTED_POINTER_FROZEN')
    return head

def metadata(out):
    head_check();rows={}
    for name,(ident,run,title,size,sha) in ASSETS.items():
        row=json.loads(cmd('gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/artifacts/'+str(ident)))
        require(row['id']==ident and row['workflow_run']['id']==run and row['name']==title and row['size_in_bytes']==size and row['digest']=='sha256:'+sha and not row['expired'],'EXACT_ORIGINAL_ARTIFACT')
        rows[name]={k:row[k] for k in ('id','name','digest','size_in_bytes')}
    save(out,rows)

def certificate(apk,sdk):
    result=cmd(sdk/'apksigner','verify','--verbose','--print-certs',apk)
    require(re.findall(r'Signer #\d+ certificate SHA-256 digest: ([a-f0-9]{64})',result)==[CERT_SHA],'ORIGINAL_CERTIFICATE')
    for scheme in ('v1','v2','v3'):
        require(re.search('Verified using '+scheme+r' scheme[^\n]*: true',result) is not None,'SIGNATURE_'+scheme)
    return result

def version_check(version,out):
    require(version in VERSIONS,'ONLY_AUTHORIZED_VERSIONS')
    refs=cmd('git','ls-remote','--heads','--tags','origin')
    require(not any(int(n)>2103455 for n in re.findall(r'210\d{4}',refs)),'NEWER_VERSION_REF_REVIEW_REQUIRED')
    rows=json.loads(cmd('gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/runs?per_page=100'))['workflow_runs']
    current=int(os.environ.get('GITHUB_RUN_ID','0'));issued=[]
    for row in rows:
        if row['id']==current or row.get('path')!='.github/workflows/infinity-combined-release.yml':continue
        require(row['status']=='completed','CONCURRENT_SIGNER_OR_PREPARATION')
        if row['conclusion']!='success':continue
        # Every recent official signer run is inspected, not inferred from a stale registry.
        artifacts=json.loads(cmd('gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/runs/'+str(row['id'])+'/artifacts?per_page=100'))['artifacts']
        if any(a['name']=='Infinity-Combined-Original-Signer-'+str(row['id']) for a in artifacts):
            raw=json.loads(cmd('gh','api','repos/mahfouzhassine8-ops/project-infinity/contents/'+str(AUTH.relative_to(REPO))+'?ref='+row['head_sha'],'-H','Accept: application/vnd.github.raw+json'))
            issued.append(dict(run=row['id'],version=raw['candidate_versionCode'],source=row['head_sha']))
    require(not any(r['version']>=version for r in issued),'VERSION_ALREADY_ISSUED_OR_NEWER')
    save(out,dict(status='PASS_CURRENT_OFFICIAL_VERSION_AVAILABILITY',target=version,issued=issued,reserved_by_authority_only=True,physical_device_queried=False))

def xml_replace(raw,old,new):
    require(raw.count(old)==1,'EXACT_SINGLE_VERSION_FIELD');return raw.replace(old,new,1)

def generate(baseline,version,root):
    require(version in VERSIONS,'ONLY_AUTHORIZED_VERSIONS')
    v=55 if version==2103454 else 56;skin=252 if version==2103454 else 253
    plan=load(UI/'SOURCE-PLAN.json')['changes'];changes={}
    with ZipFile(baseline) as z:
        for n,row in plan.items():
            require((digest(z.read(n)) if n in z.namelist() else None)==row['before'],'SOURCE_PREIMAGE:'+n)
            p=UI/'overlay'/n;require(digest(p.read_bytes())==row['after'],'SOURCE_POSTIMAGE:'+n)
            if version==2103454:changes[n]=p.read_bytes()
        for n in z.namelist():
            if n.startswith('assets/addons/') and n.split('/')[2] in module_bundle.IDS:
                p=root/n.removeprefix('assets/addons/');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(n))
        marker=root/module_bundle.CC/module_bundle.MANIFEST
        require(module_bundle.build(root)[0]==marker.read_bytes(),'EXACT_BASE_MODULE_INVENTORY')
        cmd('openssl','dgst','-sha256','-verify',FIRST/'ORIGINAL-INFINITY-PUBLIC-KEY.pem','-signature',str(marker)+'.sig',marker)
        for n,raw in changes.items():
            if n.startswith(CC):(root/n.removeprefix('assets/addons/')).write_bytes(raw)
        changes[CC+'addon.xml']=xml_replace(z.read(CC+'addon.xml'),b'version="0.3.5.54"',('version="0.3.5.'+str(v)+'"').encode())
        (root/module_bundle.CC/'addon.xml').write_bytes(changes[CC+'addon.xml'])
        manifest,files=module_bundle.build(root)
        require(len(files)==(77 if version==2103454 else 76),'EXACT_MODULE_COUNT')
        marker.write_bytes(manifest);Path(str(marker)+'.sig').unlink()
        changes[CC+'INFINITY-MODULES.v1']=manifest
        changes[SKIN+'addon.xml']=xml_replace(xml_replace(z.read(SKIN+'addon.xml'),b'version="1.0.5.251"',('version="1.0.5.'+str(skin)+'"').encode()),b'addon="script.infinity.commandcenter" version="0.3.5.54"',('addon="script.infinity.commandcenter" version="0.3.5.'+str(v)+'"').encode())
        for leaf in ('infinity-skin.json','Infinity-Protected-Manifest.json'):
            obj=json.loads(z.read(SKIN+leaf));obj['candidate']=skin
            for k in ('version','candidate_version','skin_version'):
                if k in obj:obj[k]='1.0.5.'+str(skin)
            if 'protected_files' in obj:
                for n,raw in changes.items():
                    if n.startswith(SKIN):obj['protected_files'][n[len(SKIN):]]=digest(raw)
                require(len(obj['protected_files'])==(948 if version==2103454 else 942),'EXACT_SKIN_INVENTORY')
            changes[SKIN+leaf]=(json.dumps(obj,indent=2,sort_keys=True)+'\n').encode()
        changes[LABEL]=('infinity.last_updated_in='+str(version)+'\ncobra.last_updated_in=2103445\n').encode()
    require(set(changes)==((set(plan) if version==2103454 else set())|META)-{CC+'INFINITY-MODULES.v1.sig'},'EXACT_UNSIGNED_METADATA_SET')
    return changes

def repack(owner,bundles,dest,row,source,version,changes):
    old=read_bundle(bundles/row['file'],row);meta=copy.deepcopy(old)
    meta.update(version=str(version)+'.'+owner.lower()+'.1',approved_source=source)
    selected={n:v for n,v in changes.items() if (owner=='CHOOSER_SHELL')==(n==LABEL)}
    require(owner in TARGETS,'EXACT_OWNER')
    for n,raw in selected.items():
        require((n==LABEL if owner=='CHOOSER_SHELL' else n.startswith((CC,SKIN))),'OWNER_SCOPE')
        info=meta['members'].get(n,dict(compress_type=8,external_attr=0o100644<<16))
        meta['members'][n]={**info,'sha256':digest(raw)}
        meta['payload']['member:'+n]=dict(owner=owner,sha256=digest(raw))
    meta['digest']=component_digest(meta['payload'],owner);path=dest/row['file']
    with ZipFile(bundles/row['file']) as z,ZipFile(path,'w') as output:
        for n in z.namelist():
            if n=='component.json':continue
            output.writestr(record(n),selected.get(n.removeprefix('payload/'),z.read(n)))
        for n in sorted(set(selected)-set(old['members'])):output.writestr(record('payload/'+n),selected[n])
        output.writestr(record('component.json'),canonical(meta))
    result=dict(file=path.name,sha256=file_sha(path),**{k:meta[k] for k in ('version','digest','approved_source','settings_schema')})
    verified=read_bundle(path,result)
    require(verified['dex']==old['dex'],'ALL_DEX_FROZEN')
    require({k:v for k,v in meta['payload'].items() if k not in {'member:'+n for n in selected}}=={k:v for k,v in old['payload'].items() if k not in {'member:'+n for n in selected}},'UNRELATED_OWNER_PAYLOAD')
    return result

def compare(baseline,candidate,version,expected,out,sdk=None):
    require(file_sha(baseline)==APK_SHA,'EXACT_BASE_APK')
    require(version in VERSIONS,'EXACT_VERSION');out.mkdir(parents=True,exist_ok=True)
    plan=load(UI/'SOURCE-PLAN.json')['changes']
    allowed=(set(plan) if version==2103454 else set())|META|{'AndroidManifest.xml'}
    members={};changed=[];added=[]
    with ZipFile(baseline) as a,ZipFile(candidate) as b:
        old=set(validate_names(a))-SIGNATURE;new=set(validate_names(b))-SIGNATURE
        require(old<=new,'MEMBER_DELETION')
        require(new-old==({n for n,r in plan.items() if r['before'] is None} if version==2103454 else set()),'EXACT_ADDITIONS')
        for n in sorted(new):
            raw=b.read(n);before=a.read(n) if n in old else None
            if raw!=before:
                require(n in allowed,'UNEXPECTED_APK_MEMBER:'+n)
                if n=='AndroidManifest.xml':require(normalize_manifest(raw)==(normalize_manifest(before)[0],version),'VERSION_ONLY_MANIFEST')
                else:require(digest(raw)==expected[n],'EXACT_APPROVED_BYTES:'+n)
                (changed if before is not None else added).append(n)
            members[n]=dict(before=digest(before) if before is not None else None,after=digest(raw))
        require(set(changed+added)==allowed,'MISSING_OR_UNEXPECTED_AUTHORIZED_CHANGE')
        require(members[NATIVE]['after']==NATIVE_SHA,'EXACT_NATIVE453')
        for n,h in load(UI/'release-readiness/BASELINE-PROTECTED-MEMBER-HASHES.json').items():
            require(members[n]['after']==h,'7602_PROTECTED_MEMBER:'+n)
    proof=dict(status='PASS_EXACT_SIGNED453_MEMBER_PRESERVATION',baseline_sha256=APK_SHA,candidate_sha256=file_sha(candidate),versionCode=version,changed_existing=changed,new_members=added,protected_7602_verified=True,all_DEX_unchanged=5,all_native_unchanged=47,native_sha256=NATIVE_SHA,expected_member_hashes=expected,Android=RUNTIME,physical_Fold='PENDING',accepted_pointer_updated=False,Scudo='UNRESOLVED_NOT_CHANGED')
    save(out/'APK-PRESERVATION.json',proof);save(out/'ALL-APK-MEMBER-HASHES.json',members)
    if sdk:(out/'SIGNATURE.txt').write_text(certificate(candidate,sdk))
    return proof

def prepare(bundles,baseline,sdk,out):
    source=head_check();prior=baseline_authority()
    require(file_sha(baseline)==APK_SHA,'EXACT_SIGNED453')
    require(load(bundles/'catalog.json')==prior['bundle_catalog'],'EXACT_BASE_CATALOG')
    require(not out.exists(),'FRESH_PREPARATION');out.mkdir()
    (out/'BASELINE-SIGNATURE.txt').write_text(certificate(baseline,sdk))
    for row in prior['bundle_catalog']['bundles'].values():read_bundle(bundles/row['file'],row)
    all_changes={}
    for version in VERSIONS:
        work=out/str(version);work.mkdir();root=work/'modules';root.mkdir()
        all_changes[version]=generate(baseline,version,root)
        save(work/'UNSIGNED-SOURCE-GATE.json',dict(status='PASS_EXACT_UI_METADATA_BEFORE_ORIGINAL_KEY',version=version,source=source,files={n:digest(v) for n,v in all_changes[version].items()},APK_built=False))
    # Host verifier is the frozen original verifier, not a native engine rebuild.
    verifier=out/'module-verifier'
    cmd('g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',FIRST/'verify_module_bundle.cpp',FIRST/'isolated-native/InfinityModuleManifest.cpp','-lcrypto','-o',verifier)
    from signer_policy import check
    check(load(ISO/'signer-policy.json'));head_check()
    # Check all source boundaries above before a signing credential is decoded.
    with tempfile.TemporaryDirectory(prefix='infinity-ui-module-auth-') as tmp:
        tmp=Path(tmp);classes=tmp/'classes';classes.mkdir()
        cmd('javac','--release','8','-g:none','-d',classes,FIRST/'SignInfinityModules.java')
        key=tmp/'original.jks';key.touch(mode=0o600);key.write_bytes(base64.b64decode(os.environ['INFINITY_KEYSTORE_B64'],validate=True))
        env={n:os.environ[n] for n in ('PATH','JAVA_HOME','INFINITY_STORE_PASSWORD','INFINITY_KEY_PASSWORD','INFINITY_KEY_ALIAS')}
        for version in VERSIONS:
            work=out/str(version);root=work/'modules';marker=root/module_bundle.CC/module_bundle.MANIFEST
            require(module_bundle.build(root)[0]==marker.read_bytes(),'MANIFEST_SOURCE_RACE')
            text=cmd('java','-cp',classes,'SignInfinityModules',key,marker,env=env)
            text+=cmd(verifier,root,FIRST/'ORIGINAL-INFINITY-PUBLIC-KEY.pem')
            (work/'MODULE-AUTHENTICATION.txt').write_text(text)
            all_changes[version][CC+'INFINITY-MODULES.v1.sig']=Path(str(marker)+'.sig').read_bytes()
    head_check()
    from recovery_checks import verify_recovery
    recovery=verify_recovery(baseline,out,verifier)
    save(out/'RECOVERY-VERIFICATION.json',recovery)
    for version in VERSIONS:
        work=out/str(version);changes=all_changes[version]
        catalog=copy.deepcopy(prior['bundle_catalog']);catalog['source']=source
        dest=work/'components';dest.mkdir()
        for frozen in ('COBRA','MINIMAL_ANDROID_CONTRACT'):
            row=catalog['bundles'][frozen];shutil.copyfile(bundles/row['file'],dest/row['file'])
        for owner in TARGETS:catalog['bundles'][owner]=repack(owner,bundles,dest,catalog['bundles'][owner],source,version,changes)
        save(dest/'catalog.json',catalog)
        expected={n:digest(raw) for n,raw in changes.items()}
        combine(dest,catalog,work/'combined-unsigned.apk',version)
        compare(baseline,work/'combined-unsigned.apk',version,expected,work/'preservation')
        proof=dict(status='PASS_UI454_RECOVERY455_PREPARATION',source=source,run_id=int(os.environ['GITHUB_RUN_ID']),versionCode=version,baseline=BASE,baseline_apk_sha256=APK_SHA,UI_checkpoint=SOURCE,readiness_checkpoint=READY,source_files=source_bindings(),expected_members=expected,native_sha256=NATIVE_SHA,Android=RUNTIME,physical_Fold='PENDING',accepted_pointer_updated=False,recovery_verification_sha256=file_sha(out/'RECOVERY-VERIFICATION.json'))
        save(work/'PREPARATION.json',proof)
        publish=work/'publish';publish.mkdir()
        shutil.copytree(dest,publish/'components');shutil.copytree(work/'preservation',publish/'preservation')
        for n in ('PREPARATION.json','MODULE-AUTHENTICATION.txt','UNSIGNED-SOURCE-GATE.json'):shutil.copyfile(work/n,publish/n)
        shutil.copyfile(out/'RECOVERY-VERIFICATION.json',publish/'RECOVERY-VERIFICATION.json')
    head_check()

def official(prepared,run_id,archive=None):
    proof=load(prepared/'PREPARATION.json');version=proof['versionCode'];require(version in VERSIONS,'EXACT_PREPARED_VERSION')
    run=json.loads(cmd('gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/runs/'+str(run_id)))
    require(run['status']=='completed' and run['conclusion']=='success' and run['head_sha']==proof['source'] and run['head_branch']==BRANCH and run['path']=='.github/workflows/infinity-combined-release.yml','OFFICIAL_PRODUCER')
    require(proof['status']=='PASS_UI454_RECOVERY455_PREPARATION' and proof['run_id']==run_id and proof['baseline']==BASE and proof['baseline_apk_sha256']==APK_SHA and proof['UI_checkpoint']==SOURCE and proof['readiness_checkpoint']==READY and proof['native_sha256']==NATIVE_SHA and proof['Android']==RUNTIME and proof['accepted_pointer_updated'] is False,'EXACT_PREPARATION_SCOPE')
    require(proof['source_files']==source_bindings(),'SOURCE_BINDING_CURRENT')
    for n,h in proof['source_files'].items():require(digest(subprocess.check_output(['git','show',proof['source']+':'+n]))==h,'PRODUCER_SOURCE:'+n)
    require(file_sha(prepared/'RECOVERY-VERIFICATION.json')==proof['recovery_verification_sha256'],'RECOVERY_EVIDENCE_BINDING')
    require(load(prepared/'RECOVERY-VERIFICATION.json')['status']=='PASS_ORIGINAL_KEY_HOST_RECOVERY_AND_ENTRY_REACHABILITY','RECOVERY_GATE')
    artifacts=json.loads(cmd('gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/runs/'+str(run_id)+'/artifacts?per_page=100'))['artifacts']
    found=[r for r in artifacts if r['name']=='Infinity'+str(version)+'-Prepared-'+str(run_id) and not r['expired']]
    require(len(found)==1,'ONE_PREPARED_ARTIFACT');row={k:found[0][k] for k in ('id','name','digest','size_in_bytes')}
    if archive is None:
        archive=prepared.parent/(str(row['id'])+'.zip')
        if not archive.exists():
            with archive.open('wb') as stream:subprocess.run(['gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/artifacts/'+str(row['id'])+'/zip'],stdout=stream,check=True)
    require(file_sha(archive)==row['digest'].removeprefix('sha256:'),'OFFICIAL_ARCHIVE_DIGEST')
    with ZipFile(archive) as z:
        names={n for n in validate_names(z) if not n.endswith('/')}
        require(names=={str(p.relative_to(prepared)) for p in prepared.rglob('*') if p.is_file()},'OFFICIAL_FILE_SET')
        for n in names:
            with z.open(n) as f:require(hashlib.file_digest(f,'sha256').hexdigest()==file_sha(prepared/n),'OFFICIAL_MEMBER:'+n)
    return row

def proposed(prepared,run_id,archive=None):
    artifact=official(prepared,run_id,archive);proof=load(prepared/'PREPARATION.json');version=proof['versionCode']
    if version==2103454:prior=baseline_authority()
    else:
        # Immutable record of the issued454 authority; actual Git lineage is
        # independently rechecked by the unchanged remote authority gate.
        prior=load(HERE/'evidence/ISSUED454-AUTHORITY.json')
        require(prior['candidate_versionCode']==2103454 and prior['generation']==40,'ISSUED454_PREDECESSOR')
    catalog=load(prepared/'components/catalog.json')
    metas={o:read_bundle(prepared/'components'/r['file'],r) for o,r in catalog['bundles'].items()}
    authority=copy.deepcopy(prior)
    authority.update(generation=40 if version==2103454 else 41,last_issued_versionCode=version-1,candidate_versionCode=version,target_owners=TARGETS,update_kind='owner_update',previous_authority_sha256=digest(canonical(prior)),payload={k:v for m in metas.values() for k,v in m['payload'].items()},bundle_catalog=catalog,experience_version_labels={'INFINITY':version,'COBRA':2103445})
    for owner in TARGETS:
        authority['components'][owner]={k:metas[owner][k] for k in ('version','digest','approved_source','settings_schema')}
        authority['components'][owner]['revision']=prior['components'][owner]['revision']+1
        authority['bundle_sources'][owner]=dict(run_id=run_id,build_source=proof['source'],artifact='Infinity'+str(version)+'-Prepared-'+str(run_id),path='components/'+owner+'.zip')
    authority['source_files']={n:file_sha(REPO/n) for n in prior['source_files']}
    authority['workflow_sha256']=file_sha(REPO/'.github/workflows/infinity-combined-release.yml')
    authority['owner_update_evidence']=dict(owner='INFINITY_KODI_UI' if version==2103454 else 'INFINITY_KODI_UI_FORWARD_RECOVERY',producer_run=run_id,producer_source=proof['source'],source_files=proof['source_files'],artifact=artifact,preparation_sha256=file_sha(prepared/'PREPARATION.json'),native_sha256=NATIVE_SHA,Android=RUNTIME,physical_Fold='PENDING',unknown_obligations='REMAIN_BLOCKING',frozen_owners=['COBRA','MINIMAL_ANDROID_CONTRACT'],accepted_pointer_updated=False,recovery_verification_sha256=proof['recovery_verification_sha256'])
    transition(prior,authority,TARGETS);verify_evidence(authority,lambda n:(REPO/n).read_bytes())
    return authority

def register(prepared,run_id,archive=None):
    value=proposed(prepared,run_id,archive);prior=baseline_authority() if value['candidate_versionCode']==2103454 else load(HERE/'evidence/ISSUED454-AUTHORITY.json')
    require(load(AUTH)==prior,'AUTHORITY_PREDECESSOR');save(AUTH,value)

def check_registered(prepared,run_id,out,archive=None):
    head_check();require(proposed(prepared,run_id,archive)==load(AUTH),'EXACT_REGISTERED_OFFICIAL_PREPARATION')
    save(out,dict(status='PASS_EXACT_UI_OR_FORWARD_RECOVERY_AUTHORITY',run_id=run_id,Android=RUNTIME,physical_Fold='PENDING'))

if __name__=='__main__':
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='op',required=True)
    a=s.add_parser('metadata');a.add_argument('--out',type=Path,required=True)
    a=s.add_parser('versions');a.add_argument('--version',type=int,required=True);a.add_argument('--out',type=Path,required=True)
    a=s.add_parser('prepare')
    for n in ('bundles','baseline','sdk','out'):a.add_argument('--'+n,type=Path,required=True)
    a=s.add_parser('compare')
    for n in ('baseline','candidate','plan','out'):a.add_argument('--'+n,type=Path,required=True)
    a.add_argument('--sdk',type=Path)
    for op in ('register','check_registered'):
        a=s.add_parser(op);a.add_argument('--prepared',type=Path,required=True);a.add_argument('--run-id',type=int,required=True);a.add_argument('--archive',type=Path)
        if op=='check_registered':a.add_argument('--out',type=Path,required=True)
    args=vars(p.parse_args());op=args.pop('op')
    if op=='compare':
        proof=load(args.pop('plan'));compare(version=proof['versionCode'],expected=proof['expected_members'],**args)
    else:{'metadata':metadata,'versions':version_check,'prepare':prepare,'register':register,'check_registered':check_registered}[op](**args)
