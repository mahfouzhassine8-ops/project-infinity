"""Integrate exact tested407 successors; audit every APK member, then sign.

Internal candidate for separately selected Android17 journeys. This producer
does not run application/shutdown tests or promote a release/acceptance lock.
"""
from __future__ import annotations
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

import compose_firstparty
import inspect_signed407
import module_bundle
import module_dex

ROOT=Path(__file__).parent.resolve()
PREFIX='assets/addons/'
NATIVE='lib/arm64-v8a/libkodi.so'
SIGNATURE={'META-INF/INFINITY.SF','META-INF/INFINITY.RSA','META-INF/MANIFEST.MF'}
APK_NAME='Infinity-2103409-Integrated-INTERNAL-VERIFICATION.apk'


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as source:
        for raw in iter(lambda:source.read(4*1024*1024),b''):digest.update(raw)
    return digest.hexdigest()


def member_sha(archive,name):
    digest=hashlib.sha256()
    with archive.open(name) as source:
        for raw in iter(lambda:source.read(4*1024*1024),b''):digest.update(raw)
    return digest.hexdigest()


def only(root,name):
    paths=list(Path(root).rglob(name))
    if len(paths)!=1:raise ValueError('Exactly one '+name+' required')
    return paths[0]


def command(args,env=None):
    result=subprocess.run(list(map(str,args)),env=env,text=True,capture_output=True)
    if result.returncode:raise RuntimeError(result.stdout+result.stderr)
    return result.stdout


def manifest(raw):
    old=struct.pack('<I',2103407);new=struct.pack('<I',2103409)
    if raw.count(old)!=1 or new in raw:raise ValueError('Exact407versionCode required')
    at=raw.index(old)
    if raw[at-4:at]!=b'\x08\x00\x00\x10':raise ValueError('Typed integerAXMLversionCode required')
    return raw[:at]+new+raw[at+4:]


def native_abi(parent,native):
    def exports(path):
        result={}
        for line in command(['readelf','-W','--dyn-syms',path]).splitlines():
            fields=line.split()
            if len(fields)>=8 and fields[0].endswith(':') and fields[6]!='UND' and fields[4] in ('GLOBAL','WEAK'):
                result[fields[7]]=tuple(fields[3:6])
        return result
    with tempfile.TemporaryDirectory(prefix='infinity-original-native-abi-') as temp:
        original=Path(temp)/'libkodi.so'
        with ZipFile(parent) as archive,archive.open(NATIVE) as source,original.open('wb') as output:
            shutil.copyfileobj(source,output,4*1024*1024)
        old=exports(original);new=exports(native)
    missing=sorted(set(old)-set(new));changed=sorted(n for n in set(old)&set(new) if old[n]!=new[n])
    added=sorted(set(new)-set(old))
    if missing or changed or any('cobra' in name.lower() for name in added):
        raise ValueError('Unowned native ABI difference')
    if new.get('InfinityCommandCenterIdentityV1')!=('FUNC','GLOBAL','DEFAULT'):
        raise ValueError('Required immutable identity ABI unavailable')
    return dict(original_export_count=len(old),candidate_export_count=len(new),
        missing_original_exports=missing,changed_type_binding_visibility=changed,added_exports=added,
        original_native_symbols_preserved=True,Android17='NOT RUN',physical_Fold='NOT RUN')


def audit(parent,candidate,plan,components):
    if sha(parent)!=plan['baseline_APK_sha256']:raise ValueError('Protected signed407APK differs')
    ledger=plan['member_ledger']
    with ZipFile(parent) as before,ZipFile(candidate) as after:
        old=before.namelist();new=after.namelist()
        if len(old)!=len(set(old)) or len(new)!=len(set(new)):raise ValueError('Duplicate APK member')
        differences={};preserved=0
        for name in sorted((set(old)|set(new))-SIGNATURE):
            a=member_sha(before,name) if name in old else None
            b=member_sha(after,name) if name in new else None
            if a==b:preserved+=1;continue
            if name not in ledger or ledger[name]['before']!=a or ledger[name]['after']!=b:
                raise ValueError('Unexplained or mismatched APK member: '+name)
            differences[name]={'before':a,'after':b,'reason':ledger[name]['reason']}
        if set(differences)!=set(ledger):raise ValueError('Expected owned APK delta was not applied')
        if after.read('AndroidManifest.xml')!=manifest(before.read('AndroidManifest.xml')):
            raise ValueError('Unrelated package/manifest field changed')
        for archive in components.glob('*.zip'):
            with ZipFile(archive) as component:
                names=component.namelist()
                if len(names)!=len(set(names)):raise ValueError('Duplicate component member')
                for name in names:
                    if name.endswith('/'):continue
                    if not name.startswith(('script.infinity.','skin.infinity.diggz/')):
                        raise ValueError('Unowned component member')
                    if hashlib.sha256(component.read(name)).hexdigest()!=member_sha(after,PREFIX+name):
                        raise ValueError('Component/APK mismatch: '+name)
        return dict(baseline_APK_sha256=sha(parent),candidate_APK_sha256=sha(candidate),
            preserved_unowned_and_unchanged_members=preserved,explained_differences=differences,
            unexpected_differences=[],Cobra_specific_members_changed=[],
            classes2_preserved=member_sha(before,'classes2.dex')==member_sha(after,'classes2.dex'),
            primary_DEX='Onlyownedinstallerclass; exact7864otherclassdefinitions/stringindices inDEX-MODULE-PRESERVATION.json',
            native='Full9411sourcecompiledengine;9ownedchanges4newverifiers,9398otherexistingfiles preserved; no legacyhash-onlyengine substitute',
            Android17='NOT RUN',physical_Fold='NOT RUN',release_ready=False,final_lock=False)


def build(parent_root,module_root,native_root,out,sdk):
    parent_root=Path(parent_root).resolve();module_root=Path(module_root).resolve()
    native_root=Path(native_root).resolve();out=Path(out).absolute();sdk=Path(sdk).resolve()
    if out.exists():raise ValueError('Fresh internal package directory required')
    plan=json.loads((ROOT/'APK-PACKAGING-PLAN.json').read_text())
    parent=only(parent_root,'Infinity-2103407-Search-Single-Flight-SIGNED-QA.apk')
    if sha(parent)!=plan['baseline_APK_sha256']:raise ValueError('Original signed407APK required')
    module_report=only(module_root,'SIGNED-MODULE-BUNDLE.json')
    modules=module_report.parent
    report=json.loads(module_report.read_text())
    if (report['manifest_sha256']!=plan['source_inputs']['module_manifest_sha256'] or
        report['original_certificate_sha256']!=plan['original_certificate_sha256'] or
        report['native_original_key_verified'] is not True):raise ValueError('Completed original-key module binding differs')
    native=only(native_root,'final-native/libkodi.so') if list(native_root.rglob('final-native/libkodi.so')) else None
    if native is None:raise ValueError('Complete compiled native engine unavailable')
    proof=json.loads((native.parent/'ENGINE-PROOF.json').read_text())
    if (proof['source_commit']!='89300fa6690015f17378657f96230040bb4766ea' or
        proof['complete_native_engine_compiled'] is not True or proof['reviewed_file_count']!=9411 or
        proof['changed_or_missing_reviewed']!=[] or sha(native)!=plan['member_ledger'][NATIVE]['after'] or
        proof['native_sha256']!=sha(native)):raise ValueError('Complete matching9411sourceengine proof differs')
    with native.open('rb') as f:header=f.read(64)
    if header[:6]!=b'\x7fELF\x02\x01' or header[18:20]!=b'\xb7\x00':raise ValueError('ARM64ELF required')
    source_map=json.loads((native.parent/'NATIVE-SOURCE-MAP.json').read_text())
    for file in (ROOT/'isolated-native').iterdir():
        if file.suffix in ('.cpp','.h') and source_map.get('xbmc/platform/android/activity/'+file.name)!=sha(file):
            raise ValueError('Compiled verifier differs from current native source: '+file.name)
    dex_report=only(module_root,'DEX-MODULE-PRESERVATION.json');dex=dex_report.parent/'classes.dex'
    reviewed=json.loads(dex_report.read_text())
    if (sha(dex)!=plan['member_ledger']['classes.dex']['after'] or
        reviewed['runtime_adapter_template_sha256']!=sha(ROOT/'InfinityInstalledModules.java.in') or
        reviewed['generated_java_sha256']!=hashlib.sha256(module_dex.source().encode()).hexdigest() or
        reviewed['Cobra_classes_changed']!=[] or reviewed['all_other_disassemblies_byte_identical'] is not True):
        raise ValueError('Exact checked DEX adapter binding differs')
    out.mkdir(parents=True)
    (out/'NATIVE-ABI-PRESERVATION.json').write_text(json.dumps(native_abi(parent,native),indent=2)+'\n')
    baseline=out/'baseline';inspect_signed407.inspect(parent_root,baseline)
    addons=modules/'assets/addons'
    with tempfile.TemporaryDirectory(prefix='infinity-final-recipe-') as temp:
        expected=Path(temp)/'addons';compose_firstparty.compose(baseline/'sources',expected);module_bundle.prepare(expected)
        expected_files={p.relative_to(expected).as_posix():p.read_bytes() for p in expected.rglob('*') if p.is_file()}
        actual_files={p.relative_to(addons).as_posix():p.read_bytes() for p in addons.rglob('*') if p.is_file()}
        signature=module_bundle.CC+'/'+module_bundle.MANIFEST+'.sig'
        if set(actual_files)!=set(expected_files)|{signature} or any(actual_files[n]!=v for n,v in expected_files.items()):
            raise ValueError('Module source differs from exact current reviewed composition')
    verifier=out/'verify-native-bundle'
    command(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',ROOT/'verify_module_bundle.cpp',
        ROOT/'isolated-native/InfinityModuleManifest.cpp','-lcrypto','-o',verifier])
    (out/'MODULE-NATIVE-AUTHENTICATION.txt').write_text(command([verifier,addons,ROOT/'ORIGINAL-INFINITY-PUBLIC-KEY.pem']))
    components=out/'components';components.mkdir()
    for name,wanted in report['components'].items():
        source=modules/'components'/name
        if sha(source)!=wanted:raise ValueError('Matching module ZIP differs')
        shutil.copyfile(source,components/name)
    skin=only(parent_root,'skin.infinity.diggz-1.0.5.243.zip');shutil.copyfile(skin,components/skin.name)
    with ZipFile(parent) as original:
        axml=manifest(original.read('AndroidManifest.xml'))
        if hashlib.sha256(axml).hexdigest()!=plan['member_ledger']['AndroidManifest.xml']['after']:
            raise ValueError('AXMLversion delta differs from pre-edit ledger')
        changes={PREFIX+n:raw for n,raw in actual_files.items()}
        changes.update({'classes.dex':dex,NATIVE:native,'AndroidManifest.xml':axml})
        removed={n for n,item in plan['member_ledger'].items() if item['after'] is None}
        unsigned=out/'unsigned.apk'
        with ZipFile(unsigned,'w',allowZip64=True) as writer:
            names=set(original.namelist())
            for info in original.infolist():
                name=info.filename
                if name in SIGNATURE or name in removed:continue
                value=changes.get(name)
                with writer.open(copy.copy(info),'w',force_zip64=info.file_size>=2**31) as destination:
                    if isinstance(value,bytes):destination.write(value)
                    elif isinstance(value,Path):
                        with value.open('rb') as source:shutil.copyfileobj(source,destination,4*1024*1024)
                    else:
                        with original.open(info) as source:shutil.copyfileobj(source,destination,4*1024*1024)
            for name in sorted(set(changes)-names):
                value=changes[name]
                if not isinstance(value,bytes):raise ValueError('Unexpected new APK member type')
                info=ZipInfo(name,date_time=(2026,10,25,0,0,0));info.compress_type=ZIP_DEFLATED;info.external_attr=0o100644<<16
                writer.writestr(info,value)
    # A failed audit stops before access to the permanent signing credentials.
    audit(parent,unsigned,plan,components)
    aligned=out/'aligned.apk';command([sdk/'zipalign','-P','16','-f','4',unsigned,aligned])
    certificate=re.compile(r'Signer #1 certificate SHA-256 digest:\s*([0-9a-fA-F]{64})')
    original_signature=command([sdk/'apksigner','verify','--verbose','--print-certs',parent])
    found=certificate.search(original_signature)
    if not found or found.group(1).lower()!=plan['original_certificate_sha256']:raise ValueError('Original signer differs')
    final=out/APK_NAME
    with tempfile.TemporaryDirectory(prefix='infinity-final-apk-sign-') as temp:
        key=Path(temp)/'existing.jks';key.write_bytes(base64.b64decode(os.environ['INFINITY_KEYSTORE_B64'],validate=True));key.chmod(0o600)
        environment={name:os.environ[name] for name in ('PATH','JAVA_HOME','INFINITY_STORE_PASSWORD','INFINITY_KEY_PASSWORD')}
        command([sdk/'apksigner','sign','--ks',key,'--ks-key-alias',os.environ['INFINITY_KEY_ALIAS'],
            '--ks-pass','env:INFINITY_STORE_PASSWORD','--key-pass','env:INFINITY_KEY_PASSWORD',
            '--v1-signing-enabled','true','--v2-signing-enabled','true','--v3-signing-enabled','true',
            '--out',final,aligned],environment)
    signed=command([sdk/'apksigner','verify','--verbose','--print-certs',final]);found=certificate.search(signed)
    if not found or found.group(1).lower()!=plan['original_certificate_sha256']:raise ValueError('Permanent signer changed')
    command([sdk/'zipalign','-c','-P','16','4',final])
    badging=command([sdk/'aapt','dump','badging',final])
    if not re.search(r"^package: name='com.projectinfinity.kodi' versionCode='2103409'",badging,re.M) or "native-code: 'arm64-v8a'" not in badging:
        raise ValueError('Install-over package/version/ABI differs')
    final_report=audit(parent,final,plan,components)
    final_report.update(source_commit=os.environ.get('GITHUB_SHA'),build=os.environ.get('GITHUB_RUN_ID'),
        original_certificate_sha256=plan['original_certificate_sha256'],ARM64=True,page_alignment=16384,
        component_sha256={p.name:sha(p) for p in components.glob('*.zip')},native_proof=proof,
        source_inputs=plan['source_inputs'],candidate_stage='INTERNAL_ANDROID17_VERIFICATION_ONLY')
    (out/'APK-PRESERVATION.json').write_text(json.dumps(final_report,indent=2)+'\n')
    (out/'ORIGINAL-SIGNATURE.txt').write_text(original_signature);(out/'NEW-SIGNATURE.txt').write_text(signed)
    shutil.copyfile(dex_report,out/dex_report.name)
    for name in ('NATIVE-MODULE-INTEGRATION.json','ENGINE-PROOF.json'):shutil.copyfile(native.parent/name,out/name)
    (out/'SHA256SUMS').write_text(sha(final)+'  '+final.name+'\n'+''.join(sha(p)+'  components/'+p.name+'\n' for p in sorted(components.glob('*.zip'))))
    (out/'INTERNAL-NOT-FINAL.txt').write_text('Internal integrated Infinity2103409 for separately selected Android17 verification. No physicalFoldPASS, no releaseacceptance/final lock. Protected2103407unchanged. No userdiagnosticinstallationrequest.\n')
    unsigned.unlink();aligned.unlink()
    return {k:v for k,v in final_report.items() if k not in ('explained_differences','native_proof')}


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    for name in ('parent_root','module_root','native_root','out','sdk'):parser.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    args=parser.parse_args();print(json.dumps(build(**vars(args)),indent=2))
