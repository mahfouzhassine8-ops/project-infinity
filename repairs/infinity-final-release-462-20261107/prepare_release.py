"""Exact462 + authenticated current268 + reviewed native/Search consolidation.

Build tooling only. Original APK signing remains in the existing owner-gated
workflow and assembler. No production installer, DEX, provider or setting edit.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from zipfile import ZipFile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
ISO=ROOT/'repairs/dual-experience-isolation-2103420'
FIRST=ROOT/'repairs/infinity-final-closure-2103407'
sys.path[:0]=[str(ISO),str(FIRST)]
from inventory import canonical,digest,file_sha,load,save,SIGNATURE,validate_names
from component_bundles import read_bundle,record,combine
from release_gate import require,component_digest,normalize_manifest
import module_bundle
import module_dex

PARENT='a24ffafd056db23aa9d433552e17d4362cc9dbc9dd568b086d84cabadae8c619'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
ENGINE='6fc35b8718621ef2e941540b8c858d7d7cd7f408c810ed2fd0d14f7031e8fbb7'
OLD_ENGINE='fadfb1a08e3d125958a77d393c1d66453ec3e9c91aac3349ec5806c67c17694d'
CC='script.infinity.commandcenter'
SKIN='skin.infinity.diggz'
LABEL='assets/experience-component-updates.properties'
NATIVE='lib/arm64-v8a/libkodi.so'
SEARCH=ROOT/'repairs/infinity-master-corrective-20261105/overlay/assets/addons'/CC
SOURCE_PINS={'infinity_search.py':'a5949485c723cd56f727feec40f3be66eb60976af255ede431040511c145dc44',
             'plugin.py':'a61290fe791e264e82f00aebb7c5b6173226639edca3bee15d17dccdda82fc8e'}
VERSIONS=(2103464,2103465)


def cmd(*args):
    result=subprocess.run(list(map(str,args)),capture_output=True,text=True)
    require(result.returncode==0,'TOOL:'+str(args[0])+':'+result.stderr[-2500:])
    return result.stdout


def extract(z,root,prefix=''):
    for name in validate_names(z):
        if name.endswith('/') or not name.startswith(prefix):continue
        target=root/name.removeprefix(prefix)
        require('..' not in target.parts and not target.is_symlink(),'SAFE_INPUT_MEMBER')
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(name))


def module_root(addons,out):
    out.mkdir()
    for aid in module_bundle.IDS:shutil.copytree(addons/aid,out/aid)
    return out


def snapshot(root):
    return {str(p.relative_to(root)):file_sha(p) for p in root.rglob('*') if p.is_file()}


def versions(out):
    """Read actual official signer history before allocating this exact pair."""
    require(load(HERE/'PACKAGING-SCOPE.json')['candidate_versionCode']==VERSIONS[0],'EXACT_SELECTED_VERSIONS')
    authority=load(ISO/'release-authority.json')
    require(authority['candidate_versionCode']==2103463 and authority['generation']==49,'CURRENT_ISSUED_AUTHORITY_REQUIRES_REVIEW')
    refs=cmd('git','ls-remote','--heads','--tags','origin')
    codes=[int(n) for n in re.findall(r'(?<!\d)(210\d{4})(?!\d)',refs)]
    require(not codes or max(codes)<VERSIONS[0],'NEWER_VERSION_REF_REQUIRES_REVIEW')
    issued=[];repo='repos/mahfouzhassine8-ops/project-infinity/'
    for page in range(1,21):
        runs=json.loads(cmd('gh','api',repo+'actions/workflows/397702717/runs?per_page=100&page='+str(page)))['workflow_runs']
        for row in runs:
            if row['id']==int(os.environ['GITHUB_RUN_ID']):continue
            require(row['status']=='completed','CONCURRENT_ORIGINAL_SIGNER')
            if row['conclusion']!='success':continue
            artifacts=json.loads(cmd('gh','api',repo+'actions/runs/'+str(row['id'])+'/artifacts?per_page=100'))['artifacts']
            if not any(a['name']=='Infinity-Combined-Original-Signer-'+str(row['id']) for a in artifacts):continue
            previous=json.loads(cmd('git','show',row['head_sha']+':repairs/dual-experience-isolation-2103420/release-authority.json'))
            issued.append(dict(run=row['id'],version=previous['candidate_versionCode']))
        if len(runs)<100:break
    else:raise RuntimeError('VERSION_HISTORY_PAGINATION_LIMIT')
    require(not any(r['version']>=VERSIONS[0] for r in issued),'VERSION_ALREADY_ISSUED_OR_NEWER')
    save(out,dict(status='PASS_OFFICIAL_UNUSED_CANDIDATE_AND_FORWARD_RECOVERY_CODES',versions=VERSIONS,issued=issued))


def inputs(apk,bundles,current,native,review,sdk,out):
    require(not out.exists(),'FRESH_OUTPUT');out.mkdir(parents=True)
    require(file_sha(apk)==PARENT,'EXACT_SIGNED462_PARENT')
    cert=cmd(sdk/'apksigner','verify','--verbose','--print-certs',apk)
    require(re.findall(r'certificate SHA-256 digest: ([0-9a-f]+)',cert)==[CERT],'ORIGINAL_PARENT_CERT')
    (out/'PARENT-SIGNATURE.txt').write_text(cert)
    prior=load(ROOT/'repairs/infinity-2103460-nine-corrections-20261106/native-packaging/ISSUED462-AUTHORITY.json')
    catalog=load(bundles/'catalog.json');require(catalog==prior['bundle_catalog'],'EXACT462_OWNER_CATALOG')
    for owner,row in catalog['bundles'].items():read_bundle(bundles/row['file'],row)
    require(file_sha(native/'libkodi.so')==ENGINE,'EXACT_REUSED_NATIVE_ENGINE')
    proof=load(native/'GRAPHICS-ENGINE-INTERNAL.json')
    require(proof['source_commit']=='4ee6a5f7346077900f09114439db947a02fa2737' and proof['native_sha256']==ENGINE,'NATIVE_BUILD_SOURCE')
    require(file_sha(review/'NATIVE-SOURCE-MAP.json')=='8a4baedfa0f978a7eedfc332b935deef3572a9deb2d78d8cd488bf02ce7e740a','ORIGINAL462_MAP')
    a,b=load(review/'NATIVE-SOURCE-MAP.json'),load(native/'NATIVE-SOURCE-MAP.json')
    changed={n for n in a if a[n]!=b.get(n)}
    require(len(a)==9411 and a.keys()==b.keys() and changed=={'xbmc/guilib/GUIKeyboardFactory.cpp','xbmc/guilib/GUIWindowManager.cpp','xbmc/windowing/GraphicContext.h','xbmc/input/touch/generic/GenericTouchActionHandler.cpp'},'ONLY_FOUR_REVIEWED_NATIVE_FILES')
    cmd('openssl','dgst','-sha256','-verify',FIRST/'ORIGINAL-INFINITY-PUBLIC-KEY.pem','-signature',current/'INFINITY-QUICK-UPDATE.v1.sig',current/'INFINITY-QUICK-UPDATE.v1')
    envelope=(current/'INFINITY-QUICK-UPDATE.v1').read_text().splitlines()
    require(envelope[:4]==['INFINITY-QUICK-UPDATE/1','base\t2103460','commandcenter\t0.3.5.61','skin\t1.0.5.268'],'EXACT_CURRENT268_ENVELOPE')
    for line in envelope[4:]:
        kind,want,name=line.split('\t');require(kind=='artifact' and file_sha(current/name)==want,'CURRENT_SIGNED_COMPONENT:'+name)
    addons=out/'baseline-addons';addons.mkdir()
    with ZipFile(apk) as z:
        for aid in module_bundle.IDS:
            for n in validate_names(z):
                if n.startswith('assets/addons/'+aid+'/') and not n.endswith('/'):
                    t=addons/n.removeprefix('assets/addons/');t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(z.read(n))
    for aid,name in [(CC,CC+'-0.3.5.61-2103460-corrective.zip'),(SKIN,SKIN+'-1.0.5.268-2103460-corrective.zip')]:
        if (addons/aid).exists():shutil.rmtree(addons/aid)
        with ZipFile(current/name) as z:extract(z,addons)
    signed_root=module_root(addons,out/'baseline-module-root')
    require(module_bundle.build(signed_root)[0]==(addons/CC/module_bundle.MANIFEST).read_bytes(),'CURRENT268_FULL_SOURCE_AND_SHIMS')
    cmd('openssl','dgst','-sha256','-verify',FIRST/'ORIGINAL-INFINITY-PUBLIC-KEY.pem','-signature',addons/CC/(module_bundle.MANIFEST+'.sig'),addons/CC/module_bundle.MANIFEST)
    baseline=snapshot(addons)
    for leaf,want in SOURCE_PINS.items():require(file_sha(SEARCH/leaf)==want,'REVIEWED_SEARCH_SOURCE:'+leaf)
    source=cmd('git','rev-parse','HEAD').strip()
    for version,cc_version,skin_version in [(VERSIONS[0],'0.3.5.62','1.0.5.270'),(VERSIONS[1],'0.3.5.63','1.0.5.271')]:
        work=out/str(version);work.mkdir();shutil.copytree(addons,work/'addons')
        staged=work/'addons';controller=staged/CC
        if version==VERSIONS[0]:
            for leaf in SOURCE_PINS:shutil.copyfile(SEARCH/leaf,controller/leaf)
        xml=controller/'addon.xml';raw=xml.read_bytes();require(raw.count(b'version="0.3.5.61"')==1,'CC_VERSION_METADATA_ONLY');xml.write_bytes(raw.replace(b'version="0.3.5.61"',('version="'+cc_version+'"').encode(),1))
        skin=staged/SKIN;xml=skin/'addon.xml';raw=xml.read_bytes();require(raw.count(b'version="1.0.5.268"')==1,'SKIN_VERSION_METADATA_ONLY');xml.write_bytes(raw.replace(b'version="1.0.5.268"',('version="'+skin_version+'"').encode(),1))
        for leaf in ('infinity-skin.json','Infinity-Protected-Manifest.json'):
            data=load(skin/leaf);data.update(candidate=int(skin_version.rsplit('.',1)[1]),candidate_locked=False)
            if 'physical_device_verified' in data:data['physical_device_verified']=False
            for key in ('version','candidate_version','skin_version'):
                if key in data:data[key]=skin_version
            if 'protected_files' in data:
                for name in data['protected_files']:data['protected_files'][name]=file_sha(skin/name)
            save(skin/leaf,data)
        modules=module_root(staged,work/'module-root')
        payload,files=module_bundle.build(modules);require(len(files)==78,'EXACT_MODULE_FILE_SET')
        (controller/module_bundle.MANIFEST).write_bytes(payload)
        (controller/(module_bundle.MANIFEST+'.sig')).unlink()
        (modules/CC/module_bundle.MANIFEST).write_bytes(payload)
        (modules/CC/(module_bundle.MANIFEST+'.sig')).unlink()
        actual=snapshot(staged);allowed={CC+'/'+n for n in ('addon.xml','INFINITY-MODULES.v1','INFINITY-MODULES.v1.sig')}|{SKIN+'/'+n for n in ('addon.xml','infinity-skin.json','Infinity-Protected-Manifest.json')}
        if version==VERSIONS[0]:allowed|={CC+'/'+n for n in SOURCE_PINS}
        require(set(actual)==set(baseline)-{CC+'/INFINITY-MODULES.v1.sig'},'NO_UNDECLARED_MODULE_MEMBERS')
        require({n for n in actual if actual[n]!=baseline[n]}<=allowed,'CURRENT_COMPONENT_PRESERVATION')
        save(work/'INPUTS.json',dict(source=source,versionCode=version,CC=cc_version,skin=skin_version,source_files=actual,permitted_differences=sorted(allowed),native_sha256=ENGINE if version==VERSIONS[0] else OLD_ENGINE))
    save(out/'INPUTS-VERIFIED.json',dict(source=source,parent_sha256=PARENT,current_component_source='0a0ab8573d41c807d71814220a567ed93318bc19',native_sha256=ENGINE,source_files_unchanged=9407,status='PASS_EXACT_AUTHENTICATED_INPUTS_AND_BOUNDED_GENERATED_METADATA',signing=False,APK=False))


def finish(apk,bundles,native,out):
    require(load(out/'INPUTS-VERIFIED.json')['source']==cmd('git','rev-parse','HEAD').strip(),'SAME_SOURCE_BEFORE_ASSEMBLY')
    base=load(bundles/'catalog.json');source=cmd('git','rev-parse','HEAD').strip()
    for version in VERSIONS:
        work=out/str(version);staged=work/'addons';pin=load(work/'INPUTS.json')
        require({n:h for n,h in snapshot(staged).items() if not n.endswith('INFINITY-MODULES.v1.sig')}==pin['source_files'],'STAGED_SOURCE_CHANGED_AFTER_PREFLIGHT')
        cmd('openssl','dgst','-sha256','-verify',FIRST/'ORIGINAL-INFINITY-PUBLIC-KEY.pem','-signature',staged/CC/(module_bundle.MANIFEST+'.sig'),staged/CC/module_bundle.MANIFEST)
        changes={LABEL:('infinity.last_updated_in='+str(version)+'\ncobra.last_updated_in=2103445\n').encode()}
        if version==VERSIONS[0]:changes[NATIVE]=(native/'libkodi.so').read_bytes()
        with ZipFile(apk) as z:
            for p in staged.rglob('*'):
                if p.is_file():
                    name='assets/addons/'+str(p.relative_to(staged));raw=p.read_bytes()
                    require(name in z.namelist(),'NO_NEW_APK_MEMBER:'+name)
                    if raw!=z.read(name):changes[name]=raw
        dest=work/'publish/components';dest.mkdir(parents=True)
        catalog=copy.deepcopy(base);catalog['source']=source
        metas={}
        for owner,row in base['bundles'].items():
            meta=read_bundle(bundles/row['file'],row);old_meta=copy.deepcopy(meta)
            if owner not in ('INFINITY','CHOOSER_SHELL'):
                shutil.copyfile(bundles/row['file'],dest/row['file']);metas[owner]=meta;continue
            selected={n:raw for n,raw in changes.items() if (n==LABEL)==(owner=='CHOOSER_SHELL')}
            require(set(selected)<=set(meta['members']),'EXACT_EXISTING_OWNER_MEMBERS')
            meta.update(version=str(version)+'.'+owner.lower()+'.1',approved_source=source)
            for n,raw in selected.items():
                meta['members'][n]['sha256']=digest(raw);meta['payload']['member:'+n]=dict(owner=owner,sha256=digest(raw))
            meta['digest']=component_digest(meta['payload'],owner)
            path=dest/row['file']
            with ZipFile(bundles/row['file']) as old,ZipFile(path,'w') as z:
                for n in old.namelist():
                    if n!='component.json':z.writestr(record(n),selected.get(n.removeprefix('payload/'),old.read(n)))
                z.writestr(record('component.json'),canonical(meta))
            catalog['bundles'][owner]=dict(file=path.name,sha256=file_sha(path),**{k:meta[k] for k in ('version','digest','approved_source','settings_schema')})
            require(read_bundle(path,catalog['bundles'][owner])['dex']==old_meta['dex'],'ALL_DEX_PRESERVED');metas[owner]=meta
        save(dest/'catalog.json',catalog)
        unsigned=work/'combined-unsigned.apk';combine(dest,catalog,unsigned,version)
        compared={};changed=[]
        with ZipFile(apk) as a,ZipFile(unsigned) as b:
            names=set(validate_names(a))-SIGNATURE;require(names==set(validate_names(b)),'EXACT_APK_MEMBER_SET')
            for n in sorted(names):
                before,after=a.read(n),b.read(n)
                if before==after:continue
                if n=='AndroidManifest.xml':require(normalize_manifest(after)==(normalize_manifest(before)[0],version),'ONLY_TYPED_MANIFEST_VERSION')
                else:require(n in changes and after==changes[n],'UNAUTHORIZED_PAYLOAD:'+n)
                changed.append(n);compared[n]=digest(after)
        require(set(changed)==set(changes)|{'AndroidManifest.xml'},'EXACT_CHANGED_PAYLOAD_SET')
        report=dict(status='PASS_EXACT462_AND_AUTHENTICATED_CURRENT_COMPONENT_CONSOLIDATION',source=source,versionCode=version,run_id=int(os.environ['GITHUB_RUN_ID']),baseline_sha256=PARENT,unsigned_sha256=file_sha(unsigned),changed_members=compared,native_sha256=pin['native_sha256'],CC=pin['CC'],skin=pin['skin'],all_DEX_preserved=True,Cobra_bundle_byte_identical=True,minimal_contract_bundle_byte_identical=True,Android='NOT_RUN_FOR_SUCCESSOR',Fold='NOT_RUN',accepted_pointer_updated=False)
        save(work/'publish/PREPARATION.json',report)
        save(work/'publish/INPUTS.json',pin)
        save(work/'publish/COMPONENT-METADATA.json',metas)
    print('PASS consolidated and forward-recovery owner bundles prepared; APK signing and successor Android verification NOT_RUN')


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='versions':
        versions(Path(sys.argv[2]));raise SystemExit(0)
    p=argparse.ArgumentParser();p.add_argument('operation',choices=['inputs','finish'])
    for name in ('apk','bundles','native','out'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('current','review','sdk'):p.add_argument('--'+name,type=Path)
    args=vars(p.parse_args());op=args.pop('operation')
    if op=='finish':args={k:v for k,v in args.items() if k not in ('current','review','sdk')}
    globals()[op](**args)
