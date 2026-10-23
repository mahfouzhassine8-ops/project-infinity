"""Build only the two authorized repairs over exact RC8 inputs."""
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
import tempfile
import urllib.request
from zipfile import ZipFile,ZIP_DEFLATED

import component_contract
import native_contract
import navigation_native
import owner_binding
import provider_contracts

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OUT=ROOT/'checkpoint-targeted'
PARENT='4c3e465eb78ebbba14df02b810b1851188dc8fbcb20fe17b4cc41f84dc824879'
SOURCE='0f1b28feb7cff502a9c3714583d1785d6e6eb7e909fe11f96fd72f463f6f7f8b'
MAP='a520d539329a3b95c5f868836a5ae8e06e3bea0d21b622089d7ff9c7aefa657f'
ENGINE='lib/arm64-v8a/libkodi.so';RECORDER='lib/arm64-v8a/libinfinitycrash.so'
SIGNATURE=re.compile(r'META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))',re.I)
NAME='Infinity-2103401-Saved-Navigation-MultiImage-EXPERIMENTAL.apk'


def sha(raw):return hashlib.sha256(raw).hexdigest()
def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def save(path,value):path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def parent_apk(folder):
    files=list(folder.glob('*.apk'))
    if len(files)!=1 or digest(files[0])!=PARENT:raise RuntimeError('Exact permanently signed RC8 APK required')
    return files[0]


def prepare(parent,modes):
    apk=parent_apk(parent)
    if digest(parent/'Infinity-Universal-Source-and-Evidence.zip')!=SOURCE or digest(parent/'NATIVE-SOURCE-MAP.json')!=MAP:
        raise RuntimeError('Exact RC8 source receipts required')
    expected=json.loads((parent/'NATIVE-SOURCE-MAP.json').read_text())
    if len(expected)!=9404:raise RuntimeError('Complete original native inventory required')
    native=ROOT/'kodi';baseline=ROOT/'baseline-native'
    for path in (OUT,native,baseline,ROOT/'targeted-component-base',ROOT/'targeted-component-overlay',ROOT/'targeted-native-overlay'):
        if path.exists():raise RuntimeError('Refusing stale build output: '+str(path))
    OUT.mkdir();base=ROOT/'targeted-component-base'
    with ZipFile(apk) as archive:
        if len(archive.namelist())!=len(set(archive.namelist())) or archive.testzip():raise RuntimeError('Invalid input APK')
        for n in archive.namelist():
            if not n.startswith('assets/addons/') or n.endswith('/'):continue
            relative=n[len('assets/addons/'):]
            if relative.split('/')[0] not in component_contract.VERSIONS:continue
            path=base/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(archive.read(n))
    # RC8's rearchived source content has neutral ZIP permissions. The unchanged
    # RC7 native source supplies its original file modes and the two build links;
    # every one of its 9,404 bytestrings MUST equal the RC8 source map.
    rc7=json.loads((modes/'CANDIDATE.json').read_text())
    if rc7['source_commit']!='d9edecbe843eb92457e26cbeab712f0264c55192' or rc7['apk_sha256']!='5b4519fa570ef80c0fbb9287c8cb09bd635f1e7babcbb82370e860de0c69643d':
        raise RuntimeError('Unverified source mode reference')
    with ZipFile(modes/'Infinity-Universal-Source-and-Evidence.zip') as archive:
        for name,pin in expected.items():
            if Path(name).is_absolute() or '..' in Path(name).parts:raise RuntimeError('Invalid source path')
            info=archive.getinfo('native/'+name);raw=archive.read(info)
            if sha(raw)!=pin:raise RuntimeError('Native RC7/RC8 content differs: '+name)
            path=native/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
            path.chmod((info.external_attr>>16)&0o777)
        links=json.loads(archive.read('receipts/SOURCE-DELTA.json'))['original_links']
    if set(links)!={'system/settings/freebsd.xml','xbmc/platform/darwin/tvos/Assets.xcassets/LaunchImage.launchimage/applaunch_screen.png'}:
        raise RuntimeError('Original build link inventory changed')
    for n,record in links.items():
        path=native/n;path.unlink();path.symlink_to(record['target'])
        if not path.resolve().is_relative_to(native.resolve()) or digest(path)!=expected[n]:raise RuntimeError('Original link target changed')
    shutil.copytree(native,baseline,symlinks=True)
    providers=ROOT/'verified-navigation-providers';providers.mkdir()
    for proof in provider_contracts.PROOFS:
        path=providers/proof['archive']
        with urllib.request.urlopen(proof['url'],timeout=90) as stream:raw=stream.read()
        if sha(raw)!=proof['sha256']:raise RuntimeError('Provider distribution differs: '+proof['archive'])
        path.write_bytes(raw)
        with ZipFile(path) as z:
            for n in z.namelist():
                if Path(n).is_absolute() or '..' in Path(n).parts:raise RuntimeError('Unsafe provider archive')
            z.extractall(providers/proof['archive'][:-4])
    contracts=OUT/'NAVIGATION-CONTRACTS.json';save(contracts,provider_contracts.build(providers))
    components=ROOT/'targeted-component-overlay'
    component_delta=component_contract.stage(base,components,contracts)
    overlay=ROOT/'targeted-native-overlay'
    delta=native_contract.apply(native,overlay)
    delta.update(navigation_native.apply(native,overlay))
    delta.update(owner_binding.bind(native,base,components,overlay))
    for n,v in delta.items():
        path=native/n;path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(overlay/n,path)
    final=dict(expected,**{n:v['final_sha256'] for n,v in delta.items()})
    if len(final)!=9407 or len(delta)!=13:raise RuntimeError('Native delta exceeded its reviewed scope')
    save(OUT/'BASE-NATIVE-SOURCE-MAP.json',expected);save(OUT/'NATIVE-SOURCE-MAP.json',final)
    save(OUT/'SOURCE-DELTA.json',dict(native=delta,components=component_delta,
         original_links=links,parent_apk_sha256=PARENT,source_commit=os.environ.get('GITHUB_SHA'),
         all_other_native_sources_identical=True,provider_code_changed=False,user_data_changed=False,cobra_changed=False))
    return dict(native_sources=len(final),native_delta=len(delta),component_delta=len(component_delta))


def compile_engine():
    # Reuse the already-passed compiler recipe and dependency verifier unchanged.
    sys.path.insert(0,str(ROOT/'repairs/universal-persistence-2103401'))
    old=load('retained_universal_native_build',ROOT/'repairs/universal-persistence-2103401/build.py')
    old.OUT=OUT
    proof=old.compile_engine()
    data=(OUT/'libkodi.so').read_bytes()
    for marker in (b'multiimage-enumeration',b'multiimage_directory_backend_unverified',b'multiimage_operation_did_not_reach_verified_boundary',b'0.3.5.31',b'INFINITY_SAVED_ROUTE_FAILED'):
        if marker not in data:raise RuntimeError('Compiled correction missing: '+repr(marker))
    pins=json.loads((ROOT/'targeted-component-overlay/script.infinity.uirepair/CONTROLLER-PREIMAGES.json').read_text())
    if not all(pin.encode() in data for pin in pins.values()):raise RuntimeError('Compiled exact controller source pins absent')
    return proof


def member_delta(parent,final,targets):
    changed=[];same=[]
    with ZipFile(parent) as a,ZipFile(final) as b:
        if b.testzip() or len(b.namelist())!=len(set(b.namelist())):raise RuntimeError('Final APK is invalid')
        for n in sorted(set(a.namelist())|set(b.namelist())):
            old=a.read(n) if n in a.namelist() else None;new=b.read(n) if n in b.namelist() else None
            if old==new:same.append(dict(path=n,sha256=sha(new)));continue
            if n not in targets and not SIGNATURE.fullmatch(n):raise RuntimeError('Unexpected APK delta: '+n)
            if n in targets and new!=targets[n]:raise RuntimeError('Target payload drift: '+n)
            changed.append(dict(path=n,original_sha256=sha(old) if old is not None else None,final_sha256=sha(new) if new is not None else None))
        if {v['path'] for v in changed if not SIGNATURE.fullmatch(v['path'])}!=set(targets):raise RuntimeError('Missing intended APK delta')
        if any('cobra' in n.lower() for n in targets):raise RuntimeError('Cobra member modification forbidden')
    return dict(changed=changed,byte_identical_members=same)


def package(parent,dex,out):
    apk=parent_apk(parent)
    sys.path.insert(0,str(ROOT/'repairs/2103390-bugfixes/group7/finish92'))
    import delivery92 as delivery
    if not all(os.environ.get(k) for k in delivery.KEYS):raise RuntimeError('Permanent signer required; no fallback')
    tools=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0'
    parent_signature=delivery.verify_signature(apk,tools);_,_,signer=delivery.adapters()
    proof=json.loads((OUT/'ENGINE-PROOF.json').read_text())
    dexproof=json.loads((dex/'DEX-PRESERVATION.json').read_text())
    for report in ('HOST-NAVIGATION.json','HOST-NATIVE-CANDIDATE.json','HOST-NATIVE-BASELINE.json','RETAINED-PERSISTENCE.json',
                   'HOST-NAVIGATION-NATIVE.json','HOST-FILE-DISPATCH.json','HOST-ARCHIVE-READERS.json'):
        if not json.loads((OUT/report).read_text())['passed']:raise RuntimeError('Required host gate failed: '+report)
    if not dexproof['passed'] or not proof['complete_native_engine_compiled']:raise RuntimeError('Build proofs did not pass')
    engine=(OUT/'libkodi.so').read_bytes();finaldex=(dex/'classes.dex').read_bytes()
    if sha(engine)!=proof['native_sha256'] or sha(finaldex)!=dexproof['final_dex_sha256']:raise RuntimeError('Compiler output drift')
    delta=json.loads((OUT/'SOURCE-DELTA.json').read_text())
    targets={'assets/addons/'+n:(ROOT/'targeted-component-overlay'/n).read_bytes() for n in delta['components']}
    # Keep the unchanged diagnostic reader's wire name and current candidate
    # inventory accurate. Historical duplicate manifests are retained verbatim.
    with ZipFile(apk) as a:
        abi=signer.native_export_compatibility(a.read(ENGINE),engine)
        recorder=delivery.replace_recorder_field(a.read(RECORDER),sha(a.read(ENGINE)),sha(engine),signer.nativeidentity.elf_sections(a.read(RECORDER)))
        for n in ('assets/infinity-2103395-components.json','assets/infinity-2103401-components.json'):
            inventory=json.loads(a.read(n))
            # Inventory shape is preserved; only entries for actual changed
            # components are rebound by the source-specific helper below.
            for path,record in delta['components'].items():
                addon,leaf=path.split('/',1)
                if addon not in inventory:raise RuntimeError('Unknown diagnostic component inventory')
                inventory[addon][leaf]=record['final_sha256']
            targets[n]=(json.dumps(inventory,indent=2,sort_keys=True)+'\n').encode()
        targets.update({ENGINE:engine,RECORDER:recorder,'classes.dex':finaldex})
        if out.exists():raise RuntimeError('Package output already exists')
        out.mkdir(parents=True)
        unsigned=out/'unsigned.apk';signed=out/NAME
        with ZipFile(unsigned,'w',allowZip64=True) as b:
            for info in a.infolist():
                if not SIGNATURE.fullmatch(info.filename):b.writestr(copy.copy(info),targets.get(info.filename,a.read(info)))
            for n in sorted(set(targets)-set(a.namelist())):b.writestr(n,targets[n],compress_type=ZIP_DEFLATED,compresslevel=9)
    member_delta(apk,unsigned,targets)
    subprocess.run(['bash',str(ROOT/'scripts/sign-infinity71.sh'),str(unsigned),str(signed)],check=True)
    signature=delivery.verify_signature(signed,tools);members=member_delta(apk,signed,targets)
    badging=delivery.command([tools/'aapt','dump','badging',signed])
    if "package: name='com.projectinfinity.kodi' versionCode='2103401'" not in badging or 'application-debuggable' in badging:
        raise RuntimeError('Install-over identity changed')
    with ZipFile(signed) as archive:
        if archive.read('AndroidManifest.xml')!=ZipFile(apk).read('AndroidManifest.xml'):raise RuntimeError('Android manifest changed')
        for addon,(_,version) in component_contract.VERSIONS.items():
            prefix='assets/addons/'+addon+'/'
            names=[n for n in archive.namelist() if n.startswith(prefix) and not n.endswith('/')]
            target=out/(addon+'-'+version+'.zip')
            with ZipFile(target,'w',ZIP_DEFLATED,compresslevel=9) as z:
                for n in names:z.writestr(n[len('assets/addons/'):],archive.read(n))
            with ZipFile(target) as z:
                if any(z.read(n)!=archive.read('assets/addons/'+n) for n in z.namelist()):raise RuntimeError('Component/APK mismatch')
    unsigned.unlink()
    receipt=dict(source_commit=os.environ['GITHUB_SHA'],build_run=os.environ['GITHUB_RUN_ID'],
        parent_apk_sha256=PARENT,apk_sha256=digest(signed),native_sha256=proof['native_sha256'],
        native_abi=abi,version_code=2103401,manifest_unchanged=True,
        permanent_certificate_sha256=delivery.CERT,signature_schemes_verified=[1,2,3],
        matching_component_versions={k:v[1] for k,v in component_contract.VERSIONS.items()},
        native_source_count=9407,original_native_files_changed=10,new_native_files=3,
        cobra_definitions_changed=[],provider_code_changed=False,user_profile_changed=False,
        rc8_receipt_and_universal_observer_sources_unchanged=True,
        actual_android_verified=False,physical_fold_verified=False,final_lock=False,
        distribution='INTERNAL QA; full Android/Fold acceptance gates pending')
    save(out/'CANDIDATE.json',receipt);save(out/'APK-DELTA.json',members)
    for group in ('native','components'):
        for record in delta[group].values():
            record['test_result']='PASS: focused host gates, retained persistence and compiled source binding; actual Android/Fold acceptance pending'
    save(out/'SOURCE-DELTA.json',delta)
    for n in ('NATIVE-SOURCE-MAP.json','ENGINE-PROOF.json','HOST-NAVIGATION.json','HOST-NATIVE-CANDIDATE.json','HOST-NATIVE-BASELINE.json','RETAINED-PERSISTENCE.json',
              'HOST-NAVIGATION-NATIVE.json','HOST-FILE-DISPATCH.json','HOST-ARCHIVE-READERS.json'):
        shutil.copyfile(OUT/n,out/n)
    shutil.copyfile(HERE/'qualification/CACHE-EVIDENCE.json',out/'CACHE-EVIDENCE.json')
    shutil.copyfile(HERE/'qualification/CACHE-SCHEMA-EVIDENCE.json',out/'CACHE-SCHEMA-EVIDENCE.json')
    shutil.copyfile(dex/'DEX-PRESERVATION.json',out/'DEX-PRESERVATION.json')
    (out/'PARENT-SIGNATURE.txt').write_text(parent_signature);(out/'FINAL-SIGNATURE.txt').write_text(signature)
    (out/'APK-BADGING.txt').write_text(badging)
    with ZipFile(out/'Infinity-Targeted-Source-and-Evidence.zip','w',ZIP_DEFLATED,compresslevel=9) as z:
        expected=json.loads((OUT/'NATIVE-SOURCE-MAP.json').read_text())
        for n,pin in expected.items():
            if digest(ROOT/'kodi'/n)!=pin:raise RuntimeError('Postcompile source changed: '+n)
            z.write(ROOT/'kodi'/n,'native/'+n)
        for file in HERE.rglob('*'):
            if file.is_file() and '__pycache__' not in file.parts:z.write(file,'repair/'+file.relative_to(HERE).as_posix())
        for file in out.iterdir():
            if file.suffix in ('.json','.txt'):z.write(file,'receipts/'+file.name)
    (out/'SHA256SUMS').write_text(''.join(digest(p)+'  '+p.name+'\n' for p in sorted(out.iterdir()) if p.is_file()))
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('prepare','compile','package'))
    for name in ('parent','modes','dex','out'):p.add_argument('--'+name,type=Path)
    a=p.parse_args()
    result=prepare(a.parent,a.modes) if a.mode=='prepare' else compile_engine() if a.mode=='compile' else package(a.parent,a.dex,a.out)
    print(json.dumps(result,indent=2))
