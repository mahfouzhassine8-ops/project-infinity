"""Original-key install-over413 from exact412; native/DEX remain exact."""
import argparse
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import tempfile
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED

import module_bundle
import module_dex
import patch_home_entry as correction
from package_candidate import command,member_sha,only,sha,SIGNATURE

ROOT=Path(__file__).parent
PARENT_SHA='106e212a91ab68d028e5c39b2fcd87d1fa5102ef99be766e7fb8daf0d0656657'
PARENT_SOURCE='e39d7cb8e61a593f5268be050589111139121744'
PARENT_BUILD=40331713692
CERTIFICATE='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
APK_NAME='Infinity-2103413-Home-Entry-Corrective-VERIFICATION.apk'
PREFIX='assets/addons/'
OWNED=set(json.loads((ROOT/'HOME-ENTRY-413-PLAN.json').read_text())['source_preimages'])|{
    PREFIX+correction.CC+'/'+module_bundle.MANIFEST,
    PREFIX+correction.CC+'/'+module_bundle.MANIFEST+'.sig','AndroidManifest.xml'}


def manifest(raw):
    before=struct.pack('<I',2103412);after=struct.pack('<I',2103413)
    if raw.count(before)!=1 or after in raw:raise ValueError('Exact412 typed version required')
    at=raw.index(before)
    if raw[at-4:at]!=b'\x08\x00\x00\x10':raise ValueError('AXML typed version required')
    return raw[:at]+after+raw[at+4:]


def compare(before,after,changes):
    old=before.namelist();new=after.namelist()
    if len(old)!=len(set(old)) or len(new)!=len(set(new)) or set(old)-SIGNATURE!=set(new)-SIGNATURE:
        raise ValueError('Unowned APK member addition/removal or duplicate')
    differences={};preserved=0
    for name in sorted(set(old)-SIGNATURE):
        a=member_sha(before,name);b=member_sha(after,name)
        if a==b:preserved+=1;continue
        if name not in OWNED or name not in changes or b!=hashlib.sha256(changes[name]).hexdigest():
            raise ValueError('Unexplained member difference: '+name)
        differences[name]=dict(before=a,after=b)
    if set(differences)!=OWNED or set(changes)!=OWNED:raise ValueError('Exact declared Home-entry member change budget required')
    return dict(preserved_parent_members=preserved,explained_differences=differences,unexpected_differences=[],
        all_native_and_DEX_members_byte_identical=True,helper_members_byte_identical=True,skin_layout_geometry_player_resources_unchanged=True,
        chooser_and_Cobra_members_changed=[],user_data_modified=False)


def stage(parent,out):
    if sha(parent)!=PARENT_SHA:raise ValueError('Exact signed412 parent required')
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    addons=out/'assets/addons';addons.mkdir(parents=True)
    with ZipFile(parent) as z:
        for name in z.namelist():
            if not name.startswith(PREFIX) or name.endswith('/'):continue
            rel=name[len(PREFIX):]
            if rel.split('/')[0] not in module_bundle.IDS:continue
            if not module_bundle.safe(rel):raise ValueError('Unsafe parent first-party path')
            file=addons/rel;file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(z.read(name))
    # Recreate the exact old authenticated inventory before applying any edit.
    payload,_=module_bundle.build(addons)
    if (addons/correction.CC/module_bundle.MANIFEST).read_bytes()!=payload:
        raise ValueError('Parent source and authenticated inventory disagree')
    command(['openssl','dgst','-sha256','-verify',ROOT/'ORIGINAL-INFINITY-PUBLIC-KEY.pem',
             '-signature',addons/correction.CC/(module_bundle.MANIFEST+'.sig'),addons/correction.CC/module_bundle.MANIFEST])
    for name in ('service.py','default.py','addon.xml'):
        file=addons/correction.CC/name;file.write_bytes(correction.patch(name,file.read_bytes()))
    for name in (module_bundle.MANIFEST,module_bundle.MANIFEST+'.sig'):(addons/correction.CC/name).unlink()
    with ZipFile(parent) as archive:
        prefix=PREFIX+correction.SKIN+'/'
        before={name[len(prefix):]:archive.read(name) for name in archive.namelist()
                if name.startswith(prefix) and not name.endswith('/')}
        default_raw=archive.read(PREFIX+correction.CC+'/default.py')
    revised,proof=correction.skin_sources(before,default_raw)
    for name,raw in revised.items():
        file=out/'skin'/correction.SKIN/name;file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(raw)
    (out/'SKIN-ENTRY-PRESERVATION.json').write_text(json.dumps(proof,indent=2)+'\n')
    return addons,module_bundle.prepare(addons)


def build(parent_root,sdk,out):
    parent_root=Path(parent_root).resolve();sdk=Path(sdk).resolve();out=Path(out).absolute()
    parent=only(parent_root,'Infinity-2103412-Resume-Render-Corrective-VERIFICATION.apk')
    prior_path=only(parent_root,'APK-PRESERVATION.json');prior=json.loads(prior_path.read_text())
    if (prior.get('candidate_APK_sha256')!=PARENT_SHA or prior.get('source_commit')!=PARENT_SOURCE or
            str(prior.get('build'))!=str(PARENT_BUILD) or prior.get('unexpected_differences')!=[] or
            prior.get('original_certificate_sha256')!=CERTIFICATE):
        raise ValueError('Exact412 source/build/member binding required')
    cert=re.compile(r'Signer #1 certificate SHA-256 digest:\s*([0-9a-fA-F]{64})')
    original_signature=command([sdk/'apksigner','verify','--verbose','--print-certs',parent])
    match=cert.search(original_signature)
    if not match or match[1].lower()!=CERTIFICATE:raise ValueError('Original permanent signer required')
    for name,pin in prior['component_sha256'].items():
        if sha(only(parent_root,name))!=pin:raise ValueError('Parent component differs: '+name)
    addons,bundle=stage(parent,out)
    java=Path(os.environ['JAVA_HOME'])/'bin/java';javac=java.with_name('javac')
    with tempfile.TemporaryDirectory(prefix='infinity413-original-key-') as temp:
        work=Path(temp);classes=work/'classes';classes.mkdir()
        key=work/'original.jks'
        key.write_bytes(base64.b64decode(os.environ['INFINITY_KEYSTORE_B64'],validate=True));key.chmod(0o600)
        command([javac,'--release','8','-g:none','-Xlint:all,-options','-Werror','-d',classes,ROOT/'SignInfinityModules.java'])
        env={k:os.environ[k] for k in ('PATH','JAVA_HOME','INFINITY_STORE_PASSWORD','INFINITY_KEY_PASSWORD','INFINITY_KEY_ALIAS')}
        proof=command([java,'-cp',classes,'SignInfinityModules',key,addons/correction.CC/module_bundle.MANIFEST],env)
        (out/'ORIGINAL-MODULE-SIGNATURE.txt').write_text(proof)
    verifier=out/'verify-native-bundle'
    command(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',ROOT/'verify_module_bundle.cpp',
             ROOT/'isolated-native/InfinityModuleManifest.cpp','-lcrypto','-o',verifier])
    (out/'MODULE-NATIVE-AUTHENTICATION.txt').write_text(command([verifier,addons,ROOT/'ORIGINAL-INFINITY-PUBLIC-KEY.pem']))
    # Run the production Java migration algorithm against actual signed42->43,
    # using disposable host filesystem transport. No Android acceptance claim.
    with tempfile.TemporaryDirectory(prefix='infinity413-upgrade42-43-') as temp:
        work=Path(temp);source=work/'InfinityInstalledCheckpointInstaller.java';source.write_text(module_dex.source())
        classes=work/'classes';classes.mkdir()
        command([javac,'--release','8','-g:none','-Xlint:all,-options','-Werror','-d',classes,source,*sorted((ROOT/'host-java').rglob('*.java'))])
        storage=work/'storage';installed=storage/'.kodi/addons';installed.mkdir(parents=True)
        with ZipFile(parent) as z:
            for name in z.namelist():
                if not name.startswith(PREFIX) or name.endswith('/'):continue
                rel=name[len(PREFIX):]
                if rel.split('/')[0] in module_bundle.IDS:
                    file=installed/rel;file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(z.read(name))
        sentinel=storage/'.kodi/userdata/addon_data/script.infinity.commandcenter/continue-watching.json'
        sentinel.parent.mkdir(parents=True);raw=b'{"test_only":"41-to-42 preserve existing data","position":417.125}'
        sentinel.write_bytes(raw)
        proof=command([java,'-cp',classes,'com.projectinfinity.kodi.Main',storage,out/'assets'])
        if 'VERIFIED_VERSION=0.3.5.43' not in proof or sentinel.read_bytes()!=raw:
            raise ValueError('Actual original-key42->43 migration or data sentinel failed')
        proof+=command([verifier,installed,ROOT/'ORIGINAL-INFINITY-PUBLIC-KEY.pem'])
        (out/'JCA42-43-HOST-MIGRATION.txt').write_text(proof+'Host transport only; Android17/Fold acceptance separate.\n')
    components=out/'components';checksums=module_bundle.archive(addons,components)
    for name in list(checksums):
        file=components/name;file.rename(components/name.replace('-2103409-QA.zip','-2103413-QA.zip'))
    skin_root=out/'skin'
    target=components/'skin.infinity.diggz-1.0.5.244.zip'
    with ZipFile(target,'w',compression=ZIP_DEFLATED,compresslevel=9) as archive:
        for file in sorted(skin_root.rglob('*')):
            if not file.is_file():continue
            info=ZipInfo(file.relative_to(skin_root).as_posix(),date_time=(2026,10,26,0,0,0))
            info.compress_type=ZIP_DEFLATED;info.external_attr=0o100644<<16
            archive.writestr(info,file.read_bytes())
    with ZipFile(parent) as original:
        changes={}
        for name in OWNED:
            if not name.startswith(PREFIX):continue
            relative=name[len(PREFIX):]
            root=out/'skin' if relative.startswith(correction.SKIN+'/') else addons
            changes[name]=(root/relative).read_bytes()
        changes['AndroidManifest.xml']=manifest(original.read('AndroidManifest.xml'))
        unsigned=out/'unsigned.apk'
        with ZipFile(unsigned,'w',allowZip64=True) as writer:
            for info in original.infolist():
                if info.filename in SIGNATURE:continue
                with writer.open(copy.copy(info),'w',force_zip64=info.file_size>=2**31) as target:
                    if info.filename in changes:target.write(changes[info.filename])
                    else:
                        with original.open(info) as source:shutil.copyfileobj(source,target,4*1024*1024)
        with ZipFile(unsigned) as candidate:compare(original,candidate,changes)
    aligned=out/'aligned.apk';command([sdk/'zipalign','-P','16','-f','4',unsigned,aligned])
    final=out/APK_NAME
    with tempfile.TemporaryDirectory(prefix='infinity413-apk-sign-') as temp:
        key=Path(temp)/'original.jks'
        key.write_bytes(base64.b64decode(os.environ['INFINITY_KEYSTORE_B64'],validate=True));key.chmod(0o600)
        env={k:os.environ[k] for k in ('PATH','JAVA_HOME','INFINITY_STORE_PASSWORD','INFINITY_KEY_PASSWORD')}
        command([sdk/'apksigner','sign','--ks',key,'--ks-key-alias',os.environ['INFINITY_KEY_ALIAS'],
                 '--ks-pass','env:INFINITY_STORE_PASSWORD','--key-pass','env:INFINITY_KEY_PASSWORD',
                 '--v1-signing-enabled','true','--v2-signing-enabled','true','--v3-signing-enabled','true',
                 '--out',final,aligned],env)
    signature=command([sdk/'apksigner','verify','--verbose','--print-certs',final])
    match=cert.search(signature)
    if not match or match[1].lower()!=CERTIFICATE:raise ValueError('Permanent signer changed')
    command([sdk/'zipalign','-c','-P','16','4',final])
    badging=command([sdk/'aapt','dump','badging',final])
    if not re.search(r"^package: name='com.projectinfinity.kodi' versionCode='2103413'",badging,re.M) or "native-code: 'arm64-v8a'" not in badging:
        raise ValueError('Install-over identity/ABI differs')
    with ZipFile(parent) as original,ZipFile(final) as candidate:
        report=compare(original,candidate,changes)
        for file in components.glob('*.zip'):
            with ZipFile(file) as component:
                for name in component.namelist():
                    if not name.endswith('/') and hashlib.sha256(component.read(name)).hexdigest()!=member_sha(candidate,PREFIX+name):
                        raise ValueError('Component/APK mismatch: '+name)
    report.update(source_commit=os.environ.get('GITHUB_SHA'),build=os.environ.get('GITHUB_RUN_ID'),
        baseline_APK_sha256=PARENT_SHA,candidate_APK_sha256=sha(final),original_certificate_sha256=CERTIFICATE,
        ARM64=True,page_alignment=16384,component_sha256={p.name:sha(p) for p in components.iterdir()},
        runtime_verification='NOT RUN by packaging',physical_Fold='NOT RUN',release_ready=False,final_lock=False)
    (out/'APK-PRESERVATION.json').write_text(json.dumps(report,indent=2)+'\n')
    shutil.copyfile(prior_path,out/'PARENT412-APK-PRESERVATION.json')
    for name in ('NATIVE-ABI-PRESERVATION.json','DEX-MODULE-PRESERVATION.json','ENGINE-PROOF.json','NATIVE-MODULE-INTEGRATION.json'):
        shutil.copyfile(only(parent_root,name),out/name)
    (out/'NEW-SIGNATURE.txt').write_text(signature);(out/'ORIGINAL-SIGNATURE.txt').write_text(original_signature)
    (out/'SHA256SUMS').write_text(sha(final)+'  '+final.name+'\n'+''.join(sha(p)+'  components/'+p.name+'\n' for p in sorted(components.iterdir())))
    (out/'VERIFICATION-STATUS.txt').write_text('Infinity2103413 corrective verification candidate. Home interpreter fan-out reduced; measured Android17 and physical Fold acceptance pending. Not locked.\n')
    unsigned.unlink();aligned.unlink()
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('parent_root','sdk','out'):parser.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    result=build(**vars(parser.parse_args()))
    print(json.dumps({k:v for k,v in result.items() if k!='explained_differences'},indent=2))
