"""Exact frozen451 controlled456 and forward457 through the sole original signer."""
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
ROOT=HERE.parents[2]
ISO=ROOT/'repairs/dual-experience-isolation-2103420'
FIRST=ROOT/'repairs/infinity-final-closure-2103407'
UI=ROOT/'repairs/infinity-kodi-2103453-ui-navigation'
sys.path[:0]=[str(ISO),str(FIRST),str(ROOT/'repairs/infinity-kodi-ui-2103454-2103455-packaging')]
from inventory import canonical,digest,file_sha,load,save,CERT_SHA,SIGNATURE,validate_names
from component_bundles import read_bundle,record,combine
from release_gate import require,normalize_manifest,component_digest
from release_authority import transition,verify_evidence
import module_bundle
import release_ui as retained_ui
sys.modules.setdefault('release_controlled',sys.modules[__name__])

BRANCH='work/infinity-browser-visual-correction-from-2103456-20261105'
SOURCE='924fd6e593c4f0fcc7cf96bcd5f9b3347b3a295d'
AUTH_BASE='9471113e0b6762dcd05a0785863126ca49cdadc8'
BASE='0b3450433adc3349056167a6697dae92dad63d86'
APK_SHA='d77c31c458c4571212022bea7cea1e76c1d415cd5792b780b3c655fba97c6399'
NATIVE='lib/arm64-v8a/libkodi.so'
FROZEN_NATIVE='151128c176b6094f28bb3fc716cc07c3985a9aa38f1fe41e1bb1424f0285a47e'
CC='assets/addons/script.infinity.commandcenter/'
SKIN='assets/addons/skin.infinity.diggz/'
LABEL='assets/experience-component-updates.properties'
AUTH=ISO/'release-authority.json'
VERSIONS=(2103458,2103459)
TARGETS=['INFINITY','CHOOSER_SHELL']
RUNTIME='NOT_RUN_NO_CONNECTED_COMPATIBLE_ANDROID_TARGET'
META={LABEL,CC+'addon.xml',CC+'INFINITY-MODULES.v1',CC+'INFINITY-MODULES.v1.sig',SKIN+'addon.xml',SKIN+'infinity-skin.json',SKIN+'Infinity-Protected-Manifest.json'}
CONTROL={'.github/workflows/infinity-combined-release.yml','.github/workflows/infinity-master-controlled-native.yml',str((ISO/'release_gate.py').relative_to(ROOT)),str((ISO/'signer-policy.json').relative_to(ROOT)),str(AUTH.relative_to(ROOT))}
ASSETS={
 'baseline':(13200361701,41568721264,'Infinity-Combined-Original-Signer-41568721264',328005311,'7e2eb67204ecc24e1a9d27007e90050b40683f0442bd8c32aec9b3bac32a9c41'),
 'previous456':(13397163155,41988386798,'Infinity-Combined-Original-Signer-41988386798',329133157,'bf51d707e7596fa78b09b210a02dd0e9165918d380f3e8c98597c1885f9ac3ac'),
 'components':(13200925524,41568721264,'Infinity-Combined-Owner-Components-41568721264',319074381,'e5f3017e5154625561103580c86020eab0176cc4d1f6ca033f0c1bb8726baedd')}

def cmd(*args,**kw):return subprocess.check_output(list(map(str,args)),text=True,**kw)
def verify_module(verifier,root):return retained_ui.verify_module(verifier,root)
def original(path,commit=SOURCE):return subprocess.check_output(['git','show',commit+':'+str(path.relative_to(ROOT))])
def authority_at(commit):return json.loads(original(AUTH,commit))
def engine_record():return load(HERE/'ENGINE-INPUT.json')
def plan():return {row['member']:row for row in load(HERE.parent/'CONSOLIDATED-SOURCE-PLAN.json')['overlay_members']}

def source_bindings():
    paths=[HERE/n for n in ('release_controlled.py','recovery_checks.py','test_release.py','AUTHORIZATION.md','ENGINE-INPUT.json')]
    paths += [HERE.parent/'CONSOLIDATED-SOURCE-PLAN.json']
    paths += [ROOT/row['source'] for row in plan().values()]
    paths += [ROOT/'repairs/infinity-native-touch-2103451-20261105'/n for n in ('APPLIED-SOURCE-DELTA.json','native/xbmc/input/InputManager.cpp','native/xbmc/guilib/GUIBaseContainer.cpp')]
    return {str(p.relative_to(ROOT)):file_sha(p) for p in sorted(paths)}

def head_check():
    require(os.environ.get('GITHUB_WORKFLOW')=='Infinity combined release | owner gate before original signing','SOLE_ORIGINAL_SIGNER_WORKFLOW')
    require(os.environ.get('GITHUB_REF')=='refs/heads/'+BRANCH,'EXACT_CONTROLLED_BRANCH')
    head=os.environ['GITHUB_SHA'];require(cmd('git','rev-parse','HEAD').strip()==head,'SOURCE_HEAD')
    require(cmd('git','ls-remote','origin','refs/heads/'+BRANCH).split()[0]==head,'REMOTE_HEAD_RACE')
    require(not cmd('git','status','--porcelain','--untracked-files=no').strip(),'DIRTY_TRACKED_SOURCE')
    changed=cmd('git','diff','--name-only',SOURCE,'HEAD').splitlines()
    require(changed and all(n.startswith(str(HERE.parent.relative_to(ROOT))+'/') or n in CONTROL for n in changed),'UNRELATED_SOURCE_CHANGE')
    require(len(plan())==15,'FIFTEEN_EXACT_CORRECTIVE_SOURCE_MEMBERS')
    for n,row in plan().items():
        p=ROOT/row['source'];require(p.read_bytes()==original(p) and file_sha(p)==row['candidate_source_sha256'],'EXACT_COMPLETED_SOURCE:'+n)
    for p in list(FIRST.glob('*.py'))+[FIRST/'SignInfinityModules.java',FIRST/'ORIGINAL-INFINITY-PUBLIC-KEY.pem',FIRST/'InfinityInstalledModules.java.in',FIRST/'isolated-native/InfinityModuleManifest.cpp',FIRST/'isolated-native/InfinityModuleManifest.h']:
        require(p.read_bytes()==original(p),'TRUST_SOURCE_FROZEN:'+str(p))
    for name in ('assemble.py','inventory.py','component_bundles.py','release_authority.py','signer_policy.py','accepted-combined-release.json'):
        require((ISO/name).read_bytes()==original(ISO/name),'ORIGINAL_SECURITY_IMPLEMENTATION:'+name)
    return head

def metadata(out):
    head_check();pins=dict(ASSETS,native=tuple(engine_record()['artifact_identity']));rows={}
    for label,(aid,run,title,size,sha) in pins.items():
        row=json.loads(cmd('gh','api',f'repos/mahfouzhassine8-ops/project-infinity/actions/artifacts/{aid}'))
        require(row['id']==aid and row['workflow_run']['id']==run and row['name']==title and row['size_in_bytes']==size and row['digest']=='sha256:'+sha and row['expired'] is False,'EXACT_ARTIFACT:'+label)
        rows[label]={k:row[k] for k in ('id','name','size_in_bytes','digest')}
    save(out,rows)

def versions(version,out):
    require(version in VERSIONS,'ONLY_CONTROLLED_AND_RECOVERY_VERSIONS')
    require(not any(n>max(VERSIONS) for n in retained_ui.ref_versions(cmd('git','ls-remote','--heads','--tags','origin'))),'NEWER_VERSION_REF')
    rows=json.loads(cmd('gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/workflows/397702717/runs?per_page=100'))
    require(rows['total_count']<=100,'PAGINATED_VERSION_AUDIT_REQUIRED')
    current=int(os.environ.get('GITHUB_RUN_ID','0'));issued=[]
    for row in rows['workflow_runs']:
        if row['id']==current:continue
        require(row['status']=='completed','CONCURRENT_ORIGINAL_SIGNER')
        if row['conclusion']!='success':continue
        artifacts=json.loads(cmd('gh','api',f'repos/mahfouzhassine8-ops/project-infinity/actions/runs/{row["id"]}/artifacts?per_page=100'))['artifacts']
        if any(a['name']=='Infinity-Combined-Original-Signer-'+str(row['id']) for a in artifacts):
            a=json.loads(cmd('gh','api','repos/mahfouzhassine8-ops/project-infinity/contents/'+str(AUTH.relative_to(ROOT))+'?ref='+row['head_sha'],'-H','Accept: application/vnd.github.raw+json'))
            issued.append(dict(run=row['id'],version=a['candidate_versionCode'],source=row['head_sha']))
    require(not any(r['version']>=version for r in issued),'VERSION_ALREADY_ISSUED_OR_NEWER')
    save(out,dict(status='PASS_CURRENT_OFFICIAL_VERSION_AVAILABILITY',target=version,issued=issued,device_version='UNVERIFIED_NO_INSTALL_AUTHORIZED'))

def verify_native(folder):
    pins=engine_record();paths=list(folder.rglob('libkodi.so'));require(len(paths)==1,'ONE_ENGINE')
    library=paths[0];root=library.parent
    require(file_sha(library)==pins['native_sha256'],'EXACT_VERIFIED_ENGINE_BYTES')
    proof=load(root/'CONTROLLED-ENGINE-VERIFIED.json');mapping=load(root/'NATIVE-SOURCE-MAP.json')
    require(proof['status']=='PASS_FULL_ARM64_FROZEN451_PLUS_TWO_APPROVED_TOUCH_FILES' and proof['source_commit']==pins['source_commit'] and proof['native_sha256']==pins['native_sha256'] and proof['reviewed_count']==9411 and proof['protected_native_source_count']==9409,'COMPLETE_ENGINE_SOURCE_BINDING')
    require(file_sha(root/'NATIVE-SOURCE-MAP.json')==pins['source_map_sha256'],'EXACT_FULL_SOURCE_MAP')
    approved=load(ROOT/'repairs/infinity-native-touch-2103451-20261105/APPLIED-SOURCE-DELTA.json')
    require(proof['changed_native_sources']==approved['changed_files'] and len(mapping)==9411,'TWO_APPROVED_NATIVE_FILES_ONLY')
    require(all(mapping[n]==r['after_sha256'] for n,r in approved['changed_files'].items()),'TOUCH_SOURCE_HASHES')
    abi=(root/'ELF-ABI.txt').read_text();require('ELF64' in abi and 'AArch64' in abi and 'InfinityCommandCenterIdentityV1' in abi,'ORIGINAL_MODULE_ABI')
    return library

def native_compatibility(baseline,library,out):
    # Read ELF only. Do not load or execute either native engine.
    with tempfile.TemporaryDirectory(prefix='controlled-native-ABI-') as tmp:
        old=Path(tmp)/'original451.so'
        with ZipFile(baseline) as z:old.write_bytes(z.read(NATIVE))
        require(file_sha(old)==FROZEN_NATIVE,'FROZEN451_NATIVE_PREIMAGE')
        def inspect(path):
            header=cmd('readelf','-h',path);dynamic=cmd('readelf','-d',path)
            symbols=cmd('readelf','--dyn-syms','--wide',path)
            strong=set()
            for line in symbols.splitlines():
                fields=line.split()
                if len(fields)>=8 and fields[4]=='GLOBAL' and fields[5] in ('DEFAULT','PROTECTED') and fields[6]!='UND':strong.add(fields[7])
            return dict(ELF64='ELF64' in header,AArch64='AArch64' in header,
                        needed=sorted(re.findall(r'\(NEEDED\).*\[([^]]+)\]',dynamic)),
                        soname=re.findall(r'\(SONAME\).*\[([^]]+)\]',dynamic),strong_exports=sorted(strong))
        a,b=inspect(old),inspect(library)
        require(a['ELF64'] and b['ELF64'] and a['AArch64'] and b['AArch64'],'INSTALL_TARGET_ARCHITECTURE')
        require(a['needed']==b['needed'] and a['soname']==b['soname'],'ORIGINAL_NATIVE_LINK_CONTRACT')
        require(a['strong_exports']==b['strong_exports'],'ORIGINAL_NATIVE_STRONG_ABI')
        proof=dict(status='PASS_NATIVE_TARGET_DEPENDENCIES_AND_STRONG_ABI',original_sha256=FROZEN_NATIVE,candidate_sha256=file_sha(library),original=a,candidate=b,native_executed=False)
        save(out,proof)
        return proof

def generate(baseline,version,root,native_bytes=None):
    require(version in VERSIONS,'ONLY_CONTROLLED_AND_RECOVERY_VERSIONS')
    candidate=version==VERSIONS[0];v=59 if candidate else 60;skin=256 if candidate else 257;changes={}
    with ZipFile(baseline) as z:
        for n,row in plan().items():
            require((digest(z.read(n)) if n in z.namelist() else None)==row['baseline451_sha256'],'SOURCE_PREIMAGE:'+n)
            p=ROOT/row['source'];require(file_sha(p)==row['candidate_source_sha256'],'SOURCE_POSTIMAGE:'+n)
            if candidate:changes[n]=p.read_bytes()
        for n in z.namelist():
            if n.startswith('assets/addons/') and n.split('/')[2] in module_bundle.IDS:
                p=root/n.removeprefix('assets/addons/');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(n))
        marker=root/module_bundle.CC/module_bundle.MANIFEST
        require(module_bundle.build(root)[0]==marker.read_bytes(),'EXACT_FROZEN_MODULE_INVENTORY')
        cmd('openssl','dgst','-sha256','-verify',FIRST/'ORIGINAL-INFINITY-PUBLIC-KEY.pem','-signature',str(marker)+'.sig',marker)
        for n,raw in changes.items():
            if n.startswith(CC):(root/n.removeprefix('assets/addons/')).write_bytes(raw)
        changes[CC+'addon.xml']=retained_ui.xml_replace(z.read(CC+'addon.xml'),b'version="0.3.5.54"',('version="0.3.5.'+str(v)+'"').encode())
        (root/module_bundle.CC/'addon.xml').write_bytes(changes[CC+'addon.xml'])
        manifest,files=module_bundle.build(root);require(len(files)==(78 if candidate else 76),'EXACT_MODULE_FILE_COUNT')
        marker.write_bytes(manifest);Path(str(marker)+'.sig').unlink();changes[CC+'INFINITY-MODULES.v1']=manifest
        changes[SKIN+'addon.xml']=retained_ui.xml_replace(retained_ui.xml_replace(z.read(SKIN+'addon.xml'),b'version="1.0.5.251"',('version="1.0.5.'+str(skin)+'"').encode()),b'addon="script.infinity.commandcenter" version="0.3.5.54"',('addon="script.infinity.commandcenter" version="0.3.5.'+str(v)+'"').encode())
        for leaf in ('infinity-skin.json','Infinity-Protected-Manifest.json'):
            obj=json.loads(z.read(SKIN+leaf));obj['candidate']=skin
            for k in ('version','candidate_version','skin_version'):
                if k in obj:obj[k]='1.0.5.'+str(skin)
            if 'protected_files' in obj:
                for n,raw in changes.items():
                    if n.startswith(SKIN):obj['protected_files'][n[len(SKIN):]]=digest(raw)
                require(len(obj['protected_files'])==(948 if candidate else 942),'EXACT_SKIN_FILE_COUNT')
            changes[SKIN+leaf]=(json.dumps(obj,indent=2,sort_keys=True)+'\n').encode()
        changes[LABEL]=('infinity.last_updated_in='+str(version)+'\ncobra.last_updated_in=2103445\n').encode()
        if candidate:
            require(native_bytes is not None,'VERIFIED_ENGINE_REQUIRED');changes[NATIVE]=native_bytes
    expected=(set(plan())|META|{NATIVE} if candidate else META)-{CC+'INFINITY-MODULES.v1.sig'}
    require(set(changes)==expected,'EXACT_UNSIGNED_SOURCE_METADATA_ALLOWLIST')
    return changes

def repack(owner,bundles,dest,row,source,version,changes):
    old=read_bundle(bundles/row['file'],row);meta=copy.deepcopy(old);meta.update(version=str(version)+'.'+owner.lower()+'.1',approved_source=source)
    selected={n:v for n,v in changes.items() if (owner=='CHOOSER_SHELL')==(n==LABEL)}
    require(owner in TARGETS,'EXACT_OWNER')
    for n,raw in selected.items():
        require(n==LABEL if owner=='CHOOSER_SHELL' else n.startswith((CC,SKIN)) or n==NATIVE,'EXACT_PAYLOAD_OWNER')
        info=meta['members'].get(n,dict(compress_type=8,external_attr=0o100644<<16))
        meta['members'][n]={**info,'sha256':digest(raw)};meta['payload']['member:'+n]=dict(owner=owner,sha256=digest(raw))
    meta['digest']=component_digest(meta['payload'],owner);path=dest/row['file']
    with ZipFile(bundles/row['file']) as z,ZipFile(path,'w') as out:
        for n in z.namelist():
            if n!='component.json':out.writestr(record(n),selected.get(n.removeprefix('payload/'),z.read(n)))
        for n in sorted(set(selected)-set(old['members'])):out.writestr(record('payload/'+n),selected[n])
        out.writestr(record('component.json'),canonical(meta))
    result=dict(file=path.name,sha256=file_sha(path),**{k:meta[k] for k in ('version','digest','approved_source','settings_schema')})
    require(read_bundle(path,result)['dex']==old['dex'],'ALL_OWNER_DEX_FROZEN')
    require({k:v for k,v in meta['payload'].items() if k not in {'member:'+n for n in selected}}=={k:v for k,v in old['payload'].items() if k not in {'member:'+n for n in selected}},'UNRELATED_OWNER_PAYLOAD')
    return result

def compare(baseline,candidate,version,expected,out,sdk=None,previous456=None):
    require(file_sha(baseline)==APK_SHA and version in VERSIONS,'EXACT_FROZEN451_AND_VERSION');out.mkdir(parents=True,exist_ok=True)
    testing=version==VERSIONS[0];allowed=(set(plan())|{NATIVE} if testing else set())|META|{'AndroidManifest.xml'}
    members={};changed=[];added=[]
    with ZipFile(baseline) as a,ZipFile(candidate) as b:
        old=set(validate_names(a))-SIGNATURE;new=set(validate_names(b))-SIGNATURE
        require(old<=new,'MEMBER_DELETION')
        require(new-old==({n for n,r in plan().items() if r['baseline451_sha256'] is None} if testing else set()),'EXACT_ADDITIONS')
        for n in sorted(new):
            raw=b.read(n);before=a.read(n) if n in old else None
            if raw!=before:
                require(n in allowed,'UNEXPECTED_MEMBER:'+n)
                if n=='AndroidManifest.xml':require(normalize_manifest(raw)==(normalize_manifest(before)[0],version),'VERSION_ONLY_MANIFEST')
                else:require(digest(raw)==expected[n],'EXACT_BYTES:'+n)
                (changed if before is not None else added).append(n)
            members[n]=dict(before=digest(before) if before is not None else None,after=digest(raw))
        require(set(changed+added)==allowed,'EXACT_COMPLETE_ALLOWLIST')
        require(members[NATIVE]['after']==(engine_record()['native_sha256'] if testing else FROZEN_NATIVE),'EXACT_NATIVE_ENGINE')
    proof=dict(status='PASS_EXACT_SIGNED451_CONTROLLED_MEMBER_PRESERVATION',baseline_sha256=APK_SHA,candidate_sha256=file_sha(candidate),versionCode=version,changed_existing=changed,new_members=added,protected_existing_members=len(old)-len(changed),all_DEX_unchanged=5,native_libraries_unchanged=46 if testing else 47,expected_member_hashes=expected,Android=RUNTIME,physical_Fold='PENDING',accepted_pointer_updated=False,Search_required_tests='2 FAIL, not waived',browser_design='INCOMPLETE',Favorites_attribution='UNCONFIRMED',Scudo='UNRESOLVED_NOT_CHANGED')
    save(out/'APK-PRESERVATION.json',proof);save(out/'ALL-APK-MEMBER-HASHES.json',members)
    if testing:
        require(previous456 is not None,'ACTUAL_SIGNED456_COMPARISON_REQUIRED')
        compare_previous456(previous456,candidate,expected,out)
    if sdk:(out/'SIGNATURE.txt').write_text(retained_ui.certificate(candidate,sdk))
    return proof

def compare_previous456(previous,candidate,expected,out):
    require(file_sha(previous)=='81aed468bcdf4031f3186fa7c5aa73e396a38f27837581fbcc54f56cbbc94696','EXACT_ACTUAL_SIGNED456')
    delta=set(load(HERE.parent/'results/SOURCE-DELTA.json')['runtime_changes'])
    require(len(delta)==7,'EXACT_SEVEN_BROWSER_NAVIGATION_SOURCE_DELTA')
    allowed=delta|META|{'AndroidManifest.xml'};changed=[];added=[];unchanged=0
    with ZipFile(previous) as a,ZipFile(candidate) as b:
        old=set(validate_names(a))-SIGNATURE;new=set(validate_names(b))-SIGNATURE
        require(old<=new and new-old=={CC+'library_navigation.py'},'ONLY_NEW_AUTHENTICATED_NAVIGATION_HELPER')
        for n in sorted(new):
            raw=b.read(n);before=a.read(n) if n in old else None
            if before==raw:unchanged+=1;continue
            require(n in allowed,'UNAUTHORIZED_VS_SIGNED456:'+n)
            if n=='AndroidManifest.xml':require(normalize_manifest(raw)==(normalize_manifest(before)[0],VERSIONS[0]),'VERSION_ONLY_VS456')
            else:require(digest(raw)==expected[n],'EXPECTED_BYTES_VS456:'+n)
            (changed if before is not None else added).append(n)
        require(set(changed+added)==allowed,'EXACT_COMPLETE_VS456_DELTA')
        require(all(a.read(n)==b.read(n) for n in old if n.startswith('lib/') or re.fullmatch(r'classes[0-9]*\.dex',n)),'ALL47_NATIVE_AND_ALL5_DEX_FROZEN_VS456')
    save(out/'SIGNED456-PRESERVATION.json',dict(status='PASS_ACTUAL_SIGNED456_EXACT_MEMBER_COMPARISON',
        baseline_sha256=file_sha(previous),candidate_sha256=file_sha(candidate),changed_existing=changed,new_members=added,
        protected_existing=unchanged,all_DEX_unchanged=5,all_native_libraries_unchanged=47,
        Android=RUNTIME,device_installed_version='UNVERIFIED',accepted_pointer_updated=False))

def prepare(bundles,baseline,native,sdk,out,previous456):
    bundles,baseline,native,sdk,out=(p.resolve() for p in (bundles,baseline,native,sdk,out))
    require(file_sha(previous456)=='81aed468bcdf4031f3186fa7c5aa73e396a38f27837581fbcc54f56cbbc94696','SIGNED456_PREIMAGE')
    source=head_check();base=authority_at(BASE);latest=authority_at(AUTH_BASE)
    require(file_sha(baseline)==APK_SHA and load(bundles/'catalog.json')==base['bundle_catalog'],'EXACT_SIGNED451_COMPONENTS')
    require(not out.exists(),'FRESH_PREPARATION');out.mkdir()
    (out/'BASELINE-SIGNATURE.txt').write_text(retained_ui.certificate(baseline,sdk))
    (out/'SIGNED456-SIGNATURE.txt').write_text(retained_ui.certificate(previous456,sdk))
    for owner,row in base['bundle_catalog']['bundles'].items():
        read_bundle(bundles/row['file'],row)
        if owner not in TARGETS:require(row==latest['bundle_catalog']['bundles'][owner],'FROZEN_OWNER_LATEST_MATCH')
    engine=verify_native(native);native_compatibility(baseline,engine,out/'NATIVE-COMPATIBILITY.json');all_changes={}
    for version in VERSIONS:
        work=out/str(version);work.mkdir();root=work/'modules';root.mkdir()
        all_changes[version]=generate(baseline,version,root,engine.read_bytes() if version==VERSIONS[0] else None)
        save(work/'UNSIGNED-SOURCE-GATE.json',dict(status='PASS_EXACT_CONTROLLED_SOURCES_BEFORE_KEYS',versionCode=version,source=source,files={n:digest(v) for n,v in all_changes[version].items()}))
    verifier=out/'module-verifier';cmd('g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',FIRST/'verify_module_bundle.cpp',FIRST/'isolated-native/InfinityModuleManifest.cpp','-lcrypto','-o',verifier)
    from signer_policy import check
    check(load(ISO/'signer-policy.json'));head_check()
    with tempfile.TemporaryDirectory(prefix='infinity-controlled-original-module-key-') as tmp:
        tmp=Path(tmp);classes=tmp/'classes';classes.mkdir();cmd('javac','--release','8','-g:none','-d',classes,FIRST/'SignInfinityModules.java')
        key=tmp/'original.jks';key.touch(mode=0o600);key.write_bytes(base64.b64decode(os.environ['INFINITY_KEYSTORE_B64'],validate=True))
        env={n:os.environ[n] for n in ('PATH','JAVA_HOME','INFINITY_STORE_PASSWORD','INFINITY_KEY_PASSWORD','INFINITY_KEY_ALIAS')}
        for version in VERSIONS:
            work=out/str(version);root=work/'modules';marker=root/module_bundle.CC/module_bundle.MANIFEST
            require(module_bundle.build(root)[0]==marker.read_bytes(),'MODULE_SOURCE_RACE')
            text=cmd('java','-cp',classes,'SignInfinityModules',key,marker,env=env)
            text+=retained_ui.verify_module(verifier,root);(work/'MODULE-AUTHENTICATION.txt').write_text(text)
            all_changes[version][CC+'INFINITY-MODULES.v1.sig']=Path(str(marker)+'.sig').read_bytes()
    head_check()
    spec=importlib.util.spec_from_file_location('_controlled_original_installer_recovery',HERE/'recovery_checks.py')
    fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
    recovery=fixture.verify_recovery(baseline,out,verifier);save(out/'RECOVERY-VERIFICATION.json',recovery)
    for version in VERSIONS:
        work=out/str(version);changes=all_changes[version];catalog=copy.deepcopy(base['bundle_catalog']);catalog['source']=source
        dest=work/'components';dest.mkdir()
        for owner in ('COBRA','MINIMAL_ANDROID_CONTRACT'):shutil.copyfile(bundles/catalog['bundles'][owner]['file'],dest/catalog['bundles'][owner]['file'])
        for owner in TARGETS:catalog['bundles'][owner]=repack(owner,bundles,dest,catalog['bundles'][owner],source,version,changes)
        save(dest/'catalog.json',catalog);expected={n:digest(raw) for n,raw in changes.items()}
        combine(dest,catalog,work/'combined-unsigned.apk',version);compare(baseline,work/'combined-unsigned.apk',version,expected,work/'preservation',previous456=previous456)
        proof=dict(status='PASS_BROWSER458_FORWARD459_PREPARATION',source=source,run_id=int(os.environ['GITHUB_RUN_ID']),versionCode=version,baseline=BASE,baseline_apk_sha256=APK_SHA,source_files=source_bindings(),expected_members=expected,native_sha256=engine_record()['native_sha256'] if version==VERSIONS[0] else FROZEN_NATIVE,Android=RUNTIME,physical_Fold='PENDING',accepted_pointer_updated=False,recovery_verification_sha256=file_sha(out/'RECOVERY-VERIFICATION.json'),known_defects={'Search':'2 required FAIL','browser':'INCOMPLETE','Favorites':'UNCONFIRMED','Scudo':'UNRESOLVED'})
        save(work/'PREPARATION.json',proof);publish=work/'publish';publish.mkdir()
        shutil.copytree(dest,publish/'components');shutil.copytree(work/'preservation',publish/'preservation')
        for n in ('PREPARATION.json','MODULE-AUTHENTICATION.txt','UNSIGNED-SOURCE-GATE.json'):shutil.copyfile(work/n,publish/n)
        shutil.copyfile(out/'RECOVERY-VERIFICATION.json',publish/'RECOVERY-VERIFICATION.json')
        shutil.copyfile(out/'NATIVE-COMPATIBILITY.json',publish/'NATIVE-COMPATIBILITY.json')
    head_check()

def official(prepared,run_id,archive=None):
    proof=load(prepared/'PREPARATION.json');version=proof['versionCode'];require(version in VERSIONS,'EXACT_PREPARED_VERSION')
    run=json.loads(cmd('gh','api',f'repos/mahfouzhassine8-ops/project-infinity/actions/runs/{run_id}'))
    require(run['status']=='completed' and run['conclusion']=='success' and run['head_sha']==proof['source'] and run['head_branch']==BRANCH and run['path']=='.github/workflows/infinity-combined-release.yml','OFFICIAL_PREPARER')
    require(proof['status']=='PASS_BROWSER458_FORWARD459_PREPARATION' and proof['run_id']==run_id and proof['baseline']==BASE and proof['baseline_apk_sha256']==APK_SHA and proof['Android']==RUNTIME and proof['accepted_pointer_updated'] is False,'EXACT_PREPARATION')
    require(proof['source_files']==source_bindings(),'CURRENT_SOURCE_BINDING')
    for n,h in proof['source_files'].items():require(digest(subprocess.check_output(['git','show',proof['source']+':'+n]))==h,'OFFICIAL_SOURCE:'+n)
    require(file_sha(prepared/'RECOVERY-VERIFICATION.json')==proof['recovery_verification_sha256'],'RECOVERY_BINDING')
    require(load(prepared/'RECOVERY-VERIFICATION.json')['status']=='PASS_ORIGINAL_KEY_HOST_RECOVERY_AND_ENTRY_REACHABILITY','RECOVERY_GATE')
    rows=json.loads(cmd('gh','api',f'repos/mahfouzhassine8-ops/project-infinity/actions/runs/{run_id}/artifacts?per_page=100'))['artifacts']
    found=[r for r in rows if r['name']==f'Infinity{version}-Prepared-{run_id}' and not r['expired']];require(len(found)==1,'ONE_PREPARED_ARTIFACT')
    row={k:found[0][k] for k in ('id','name','digest','size_in_bytes')}
    if archive is None:
        archive=prepared.parent/(str(row['id'])+'.zip')
        if not archive.exists():
            with archive.open('wb') as stream:subprocess.run(['gh','api',f'repos/mahfouzhassine8-ops/project-infinity/actions/artifacts/{row["id"]}/zip'],stdout=stream,check=True)
    require(file_sha(archive)==row['digest'].removeprefix('sha256:'),'OFFICIAL_ARCHIVE_DIGEST')
    with ZipFile(archive) as z:
        names={n for n in validate_names(z) if not n.endswith('/')}
        require(names=={str(p.relative_to(prepared)) for p in prepared.rglob('*') if p.is_file()},'OFFICIAL_FILE_SET')
        for n in names:
            with z.open(n) as f:require(hashlib.file_digest(f,'sha256').hexdigest()==file_sha(prepared/n),'OFFICIAL_MEMBER:'+n)
    return row

def predecessor(version):
    return authority_at(AUTH_BASE) if version==VERSIONS[0] else load(HERE/'ISSUED458-AUTHORITY.json')

def proposed(prepared,run_id,archive=None):
    artifact=official(prepared,run_id,archive);proof=load(prepared/'PREPARATION.json');version=proof['versionCode'];prior=predecessor(version)
    require(prior['candidate_versionCode']==version-1,'EXACT_ISSUED_PREDECESSOR')
    catalog=load(prepared/'components/catalog.json');metas={o:read_bundle(prepared/'components'/r['file'],r) for o,r in catalog['bundles'].items()}
    authority=copy.deepcopy(prior)
    authority.update(generation=44 if version==VERSIONS[0] else 45,last_issued_versionCode=version-1,candidate_versionCode=version,target_owners=TARGETS,update_kind='owner_update',previous_authority_sha256=digest(canonical(prior)),payload={k:v for m in metas.values() for k,v in m['payload'].items()},bundle_catalog=catalog,experience_version_labels={'INFINITY':version,'COBRA':2103445})
    for owner in TARGETS:
        authority['components'][owner]={k:metas[owner][k] for k in ('version','digest','approved_source','settings_schema')};authority['components'][owner]['revision']=prior['components'][owner]['revision']+1
        authority['bundle_sources'][owner]=dict(run_id=run_id,build_source=proof['source'],artifact=f'Infinity{version}-Prepared-{run_id}',path='components/'+owner+'.zip')
    authority['source_files']={n:file_sha(ROOT/n) for n in prior['source_files']};authority['workflow_sha256']=file_sha(ROOT/'.github/workflows/infinity-combined-release.yml')
    authority['owner_update_evidence']=dict(owner='INFINITY_BROWSER_CONTROLLED_TEST' if version==VERSIONS[0] else 'INFINITY_BROWSER_FORWARD_RECOVERY',producer_run=run_id,producer_source=proof['source'],source_files=proof['source_files'],artifact=artifact,preparation_sha256=file_sha(prepared/'PREPARATION.json'),native_sha256=proof['native_sha256'],Android=RUNTIME,physical_Fold='PENDING',unknown_obligations='REMAIN_BLOCKING',frozen_owners=['COBRA','MINIMAL_ANDROID_CONTRACT'],accepted_pointer_updated=False,recovery_verification_sha256=proof['recovery_verification_sha256'],known_defects=proof['known_defects'])
    transition(prior,authority,TARGETS);verify_evidence(authority,lambda n:(ROOT/n).read_bytes());return authority

def register(prepared,run_id,archive=None):
    value=proposed(prepared,run_id,archive);require(load(AUTH)==predecessor(value['candidate_versionCode']),'ACTUAL_AUTHORITY_PREDECESSOR');save(AUTH,value)

def check_registered(prepared,run_id,out,archive=None):
    head_check();require(proposed(prepared,run_id,archive)==load(AUTH),'EXACT_REGISTERED_OFFICIAL_ARTIFACT');save(out,dict(status='PASS_CONTROLLED_OR_RECOVERY_AUTHORITY',Android=RUNTIME,accepted_pointer_updated=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='op',required=True)
    a=s.add_parser('metadata');a.add_argument('--out',type=Path,required=True)
    a=s.add_parser('versions');a.add_argument('--version',type=int,required=True);a.add_argument('--out',type=Path,required=True)
    a=s.add_parser('prepare')
    for n in ('bundles','baseline','native','sdk','out','previous456'):a.add_argument('--'+n,type=Path,required=True)
    a=s.add_parser('compare')
    for n in ('baseline','candidate','plan','out'):a.add_argument('--'+n,type=Path,required=True)
    a.add_argument('--sdk',type=Path);a.add_argument('--previous456',type=Path)
    for op in ('register','check_registered'):
        a=s.add_parser(op);a.add_argument('--prepared',type=Path,required=True);a.add_argument('--run-id',type=int,required=True);a.add_argument('--archive',type=Path)
        if op=='check_registered':a.add_argument('--out',type=Path,required=True)
    args=vars(p.parse_args());op=args.pop('op')
    if op=='compare':
        proof=load(args.pop('plan'));compare(version=proof['versionCode'],expected=proof['expected_members'],**args)
    else:{'metadata':metadata,'versions':versions,'prepare':prepare,'register':register,'check_registered':check_registered}[op](**args)
