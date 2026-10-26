"""Sign411 from exact410: two coordinator DEX instructions and typed version only."""
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
from zipfile import ZipFile

from package_candidate import command,member_sha,only,sha,SIGNATURE
import coordinator_dex as correction

PARENT_SHA='7de8ada4774d39c80c3251e21b1750874fbbfdbdfb08b7468dd25151d92a7a34'
PARENT_BUILD=40305746524
PARENT_SOURCE='925b475f4e4c1c1862817c13167285ebec06894a'
CERTIFICATE='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
APK_NAME='Infinity-2103411-Coordinator-Corrective-INTERNAL-VERIFICATION.apk'
COMPONENTS={
 'script.infinity.commandcenter-0.3.5.41-2103410-QA.zip':'45730c2b59d457f137cb046e6f55aaca929879352d2d5b431ef8e474ba617298',
 'script.infinity.rails-0.2.8-2103410-QA.zip':'bf11b80ceed4b2f488c374d0767aba0491788cfb1456cc7cbdb32a3ddfea11f4',
 'script.infinity.uirepair-0.1.23-2103410-QA.zip':'b160213db7399f51f55d9dc76e715c7d982bb2fb61700a54c875cfe4d6af114c',
 'script.infinity.watchedbridge-1.0.21-2103410-QA.zip':'e216d775e673cb7737ea3fafcabffcb616a0f454303b85cb49e0926ea63f435a',
 'skin.infinity.diggz-1.0.5.243.zip':'0adfed89f1d5384a3fa3a023152c7c2a094ef2edb6dd60129f336fe3b7cb9ef9',
}


def manifest(raw):
    old=struct.pack('<I',2103410);new=struct.pack('<I',2103411)
    if raw.count(old)!=1 or new in raw:raise ValueError('Exact410 versionCode required')
    at=raw.index(old)
    if raw[at-4:at]!=b'\x08\x00\x00\x10':raise ValueError('Typed AXML versionCode required')
    return raw[:at]+new+raw[at+4:]


def compare(before,after,changes):
    old=before.namelist();new=after.namelist()
    if len(old)!=len(set(old)) or len(new)!=len(set(new)):raise ValueError('Duplicate APK member')
    if set(old)-SIGNATURE!=set(new)-SIGNATURE:raise ValueError('Unowned APK member added or removed')
    differences={};preserved=0
    for name in sorted(set(old)-SIGNATURE):
        a=member_sha(before,name);b=member_sha(after,name)
        if a==b:preserved+=1;continue
        if name not in changes or hashlib.sha256(changes[name]).hexdigest()!=b:raise ValueError('Unexplained APK member difference: '+name)
        differences[name]=dict(before=a,after=b)
    if set(differences)!=set(changes):raise ValueError('Required exact APK changes absent')
    return dict(preserved_from_signed410_members=preserved,explained_differences=differences,unexpected_differences=[],
        native_members_byte_identical=True,classes_delta="Only the audited two-instruction coordinator dispatch",Cobra_specific_members_changed=[])


def build(parent_root,dex_root,sdk,out):
    parent_root=Path(parent_root);sdk=Path(sdk);out=Path(out)
    parent=only(parent_root,'Infinity-2103410-VersionCheck-Corrective-INTERNAL-VERIFICATION.apk')
    if sha(parent)!=PARENT_SHA:raise ValueError('Exact signed410 parent required')
    prior_path=only(parent_root,'APK-PRESERVATION.json');prior=json.loads(prior_path.read_text())
    if (prior.get('candidate_APK_sha256')!=PARENT_SHA or prior.get('source_commit')!=PARENT_SOURCE or
        str(prior.get('build'))!=str(PARENT_BUILD) or prior.get('unexpected_differences')!=[] or
        prior.get('original_certificate_sha256')!=CERTIFICATE or prior.get('component_sha256')!=COMPONENTS):
        raise ValueError('Prior signed source/member/component proof differs')
    cert=re.compile(r'Signer #1 certificate SHA-256 digest:\s*([0-9a-fA-F]{64})')
    original_signature=command([sdk/'apksigner','verify','--verbose','--print-certs',parent])
    found=cert.search(original_signature)
    if not found or found[1].lower()!=CERTIFICATE:raise ValueError('Original signer differs')
    out.mkdir(parents=True,exist_ok=False);components=out/'components';components.mkdir()
    for name,wanted in COMPONENTS.items():
        source=only(parent_root,name)
        if sha(source)!=wanted:raise ValueError('Matching component bytes differ: '+name)
        # The add-on versions and signed module bytes are unchanged. Rename
        # only the delivery suffix; archive content and SHA remain identical.
        shutil.copyfile(source,components/name.replace('-2103410-QA.zip','-2103411-QA.zip'))
    with ZipFile(parent) as original:
        changes={'AndroidManifest.xml':manifest(original.read('AndroidManifest.xml')),
                 'classes.dex':only(Path(dex_root),'classes.dex').read_bytes()}
        plan=json.loads((Path(__file__).parent/'COORDINATOR-2103411-PLAN.json').read_text())
        ledger=plan['member_ledger']
        proof=json.loads(only(Path(dex_root),'DEX-COORDINATOR-PRESERVATION.json').read_text())
        if (proof.get('status')!='PASS_EXACT_DEX_DEFINITIONS' or proof.get('protected_classes')!=7864 or
            proof.get('changed_instructions')!=2 or proof.get('added_classes')!=[] or
            proof.get('original_string_pool_and_indices_identical') is not True or
            proof.get('final_dex_sha256')!=ledger['classes.dex']['after']):
            raise ValueError('Actual exact DEX reconstruction proof required')
        if set(ledger)!=set(changes) or any(ledger[name]!={'before':member_sha(original,name),
                'after':hashlib.sha256(raw).hexdigest()} for name,raw in changes.items()):
            raise ValueError('Pre-build exact member ownership ledger differs')
        unsigned=out/'unsigned.apk'
        with ZipFile(unsigned,'w',allowZip64=True) as writer:
            for info in original.infolist():
                name=info.filename
                if name in SIGNATURE:continue
                with writer.open(copy.copy(info),'w',force_zip64=info.file_size>=2**31) as target:
                    if name in changes:target.write(changes[name])
                    else:
                        with original.open(info) as source:shutil.copyfileobj(source,target,4*1024*1024)
        with ZipFile(unsigned) as candidate:compare(original,candidate,changes)
    # Audit finishes before any permanent signing credential is read.
    aligned=out/'aligned.apk';command([sdk/'zipalign','-P','16','-f','4',unsigned,aligned])
    final=out/APK_NAME
    with tempfile.TemporaryDirectory(prefix='infinity411-sign-') as temp:
        key=Path(temp)/'original.jks';key.write_bytes(base64.b64decode(os.environ['INFINITY_KEYSTORE_B64'],validate=True));key.chmod(0o600)
        environment={k:os.environ[k] for k in ('PATH','JAVA_HOME','INFINITY_STORE_PASSWORD','INFINITY_KEY_PASSWORD')}
        command([sdk/'apksigner','sign','--ks',key,'--ks-key-alias',os.environ['INFINITY_KEY_ALIAS'],
            '--ks-pass','env:INFINITY_STORE_PASSWORD','--key-pass','env:INFINITY_KEY_PASSWORD',
            '--v1-signing-enabled','true','--v2-signing-enabled','true','--v3-signing-enabled','true','--out',final,aligned],environment)
    signed=command([sdk/'apksigner','verify','--verbose','--print-certs',final]);found=cert.search(signed)
    if not found or found[1].lower()!=CERTIFICATE:raise ValueError('Permanent signer changed')
    command([sdk/'zipalign','-c','-P','16','4',final])
    badging=command([sdk/'aapt','dump','badging',final])
    if not re.search(r"^package: name='com.projectinfinity.kodi' versionCode='2103411'",badging,re.M) or "native-code: 'arm64-v8a'" not in badging:
        raise ValueError('Install-over identity differs')
    with ZipFile(parent) as original,ZipFile(final) as candidate:report=compare(original,candidate,changes)
    report.update(source_commit=os.environ.get('GITHUB_SHA'),build=os.environ.get('GITHUB_RUN_ID'),
        baseline_APK_sha256=PARENT_SHA,candidate_APK_sha256=sha(final),original_certificate_sha256=CERTIFICATE,
        ARM64=True,page_alignment=16384,component_sha256={p.name:sha(p) for p in components.iterdir()},
        protected407_preservation='Retained signed410 proof plus exactly two new member changes; see PARENT410-APK-PRESERVATION.json',
        previous_native_and_signed_modules='Byte-identical to verified410; no new durability exclusion',
        runtime_verification='NOT RUN by packaging',physical_Fold='NOT RUN',final_lock=False)
    (out/'APK-PRESERVATION.json').write_text(json.dumps(report,indent=2)+'\n')
    shutil.copyfile(prior_path,out/'PARENT410-APK-PRESERVATION.json')
    shutil.copyfile(only(Path(dex_root),'DEX-COORDINATOR-PRESERVATION.json'),out/'DEX-COORDINATOR-PRESERVATION.json')
    shutil.copyfile(only(Path(dex_root),'COORDINATOR.patch'),out/'COORDINATOR.patch')
    for name in ('NATIVE-ABI-PRESERVATION.json','DEX-MODULE-PRESERVATION.json','ENGINE-PROOF.json','NATIVE-MODULE-INTEGRATION.json'):
        shutil.copyfile(only(parent_root,name),out/name)
    (out/'ORIGINAL-SIGNATURE.txt').write_text(original_signature);(out/'NEW-SIGNATURE.txt').write_text(signed)
    (out/'SHA256SUMS').write_text(sha(final)+'  '+final.name+'\n'+''.join(sha(p)+'  components/'+p.name+'\n' for p in sorted(components.iterdir())))
    (out/'INTERNAL-NOT-FINAL.txt').write_text('Infinity2103411 internalverification candidate. Android17 andphysicalFold acceptance outstanding. No final lock.\n')
    unsigned.unlink();aligned.unlink()
    return {k:v for k,v in report.items() if k!='explained_differences'}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('parent_root','dex_root','sdk','out'):parser.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    print(json.dumps(build(**vars(parser.parse_args())),indent=2))
