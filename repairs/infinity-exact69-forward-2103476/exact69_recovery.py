#!/usr/bin/env python3
"""Prepare or verify an exact-original-2103469 functional recovery.
Only APK/module version and signature metadata may change. APK private key
is never available to this script; signing runs in the original CI workflow.
"""
import argparse
import hashlib
import json
import struct
import subprocess
from pathlib import Path
from zipfile import ZipFile

BASE_SHA = '804eebc57af2e4ef4e5418b56994bda64eb7fd7e7f2c0653b5c6e2a9f7833058'
BASE_VERSION = 2103469
NEW_VERSION = 2103476
BASE_CC = '0.3.5.67'
NEW_CC = '0.3.5.74'
CERT = 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
PREFIX = 'assets/addons/script.infinity.commandcenter/'
MANIFEST = PREFIX + 'INFINITY-MODULES.v1'
SIGNATURE = MANIFEST + '.sig'
ADDON = PREFIX + 'addon.xml'
ANDROID = 'AndroidManifest.xml'
LABELS = 'assets/experience-component-updates.properties'
BASE_SCRIPT_HASHES = {
    PREFIX+'plugin.py': 'a61290fe791e264e82f00aebb7c5b6173226639edca3bee15d17dccdda82fc8e',
    PREFIX+'resume_hub.py': '1c38df4f68201dc209d309f31bebf051e24baf0e45f4cb7318828af2212780d5',
    PREFIX+'service.py': '1844b2b217ccc7f3adef4d82bc825588fb2d561a87d6447f32ebedf3295e927d',
}
ALLOWED = {ADDON, MANIFEST, SIGNATURE, ANDROID, LABELS}
APK_SIGNERS = {'META-INF/INFINITY.SF','META-INF/INFINITY.RSA','META-INF/MANIFEST.MF'}

def h(data): return hashlib.sha256(data).hexdigest()

def fh(path):
    with open(path, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()

def check(ok, why):
    if not ok: raise RuntimeError(why)

def check_original(source):
    check(fh(source) == BASE_SHA, 'ORIGINAL_SIGNED_2103469_SHA256_MISMATCH')
    with ZipFile(source) as z:
        names = z.namelist()
        check(len(names)==len(set(names)) and len(names)==7772, 'UNEXPECTED_ORIGINAL_APK_ENTRIES')
        check(z.read(ADDON).count(('version="'+BASE_CC+'"').encode())==1, 'ORIGINAL_CC_VERSION_NOT_UNIQUE')
        for path, sha in BASE_SCRIPT_HASHES.items():
            check(h(z.read(path))==sha, 'NOT_ORIGINAL69_PRODUCTION_FILE: '+path)
        content = z.read(MANIFEST).decode('ascii')
        check(content.startswith('INFINITY-MODULES/1\npackage\t'+BASE_CC+'\n'), 'ORIGINAL_MODULE_FORMAT')
        check(len([line for line in content.splitlines() if line.startswith('file\t')])==80, 'ORIGINAL_MODULE_COUNT')
        for line in content.splitlines():
            if line.startswith('file\t'):
                _,wanted,member=line.split('\t')
                check(h(z.read('assets/addons/'+member))==wanted, 'INVALID_BASE_MODULE_SHA: '+member)
        check(z.read(LABELS)==b'infinity.last_updated_in=2103469\ncobra.last_updated_in=2103445\n', 'ORIGINAL_LABELS')
        manifest = z.read(ANDROID)
        check(h(manifest) == '4d9f0f3f92d43992d9f7b7adcc182991e73804f8ab785e4df022a63fb4ccd543', 'ORIGINAL_ANDROID_MANIFEST')
    return True

def manifest_version(raw, old, new):
    oldval=struct.pack('<I',old)
    locations=[i for i in range(len(raw)-3) if raw[i:i+4]==oldval and i>=4 and raw[i-4:i]==b'\x08\x00\x00\x10']
    check(len(locations)==1, 'NOT_ONE_TYPED_VERSION_CODE')
    i=locations[0]
    updated=raw[:i]+struct.pack('<I',new)+raw[i+4:]
    check(updated[:i]+oldval+updated[i+4:]==raw, 'CHANGED_ANDROID_MANIFEST_OTHER_THAN_VERSION')
    return updated

def replacements(source):
    check_original(source)
    with ZipFile(source) as z:
        oldaddon=z.read(ADDON)
        newaddon=oldaddon.replace(('version="'+BASE_CC+'"').encode(),('version="'+NEW_CC+'"').encode(),1)
        text=z.read(MANIFEST).decode('ascii')
        text=text.replace('package\t'+BASE_CC+'\n','package\t'+NEW_CC+'\n',1)
        oldrecord='file\t'+h(oldaddon)+'\tscript.infinity.commandcenter/addon.xml'
        newrecord='file\t'+h(newaddon)+'\tscript.infinity.commandcenter/addon.xml'
        check(text.count(oldrecord)==1,'ORIGINAL_ADDON_FILE_RECORD')
        text=text.replace(oldrecord,newrecord,1)
        return {ADDON:newaddon, MANIFEST:text.encode('ascii'),
                ANDROID:manifest_version(z.read(ANDROID),BASE_VERSION,NEW_VERSION),
                LABELS:('infinity.last_updated_in='+str(NEW_VERSION)+'\ncobra.last_updated_in=2103445\n').encode()}

def stage(source, out):
    check(not out.exists(), 'OUTPUT_DIRECTORY_ALREADY_EXISTS')
    changes=replacements(source)
    out.mkdir(parents=True)
    for member,raw in changes.items():
        target=out/member
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(raw)
    proof={'operation':'original69-repackage-metadata-only', 'original_sha256':BASE_SHA,
           'original_version':BASE_VERSION,'next_version':NEW_VERSION,
           'original_cc':BASE_CC,'new_cc':NEW_CC,'signed_original_certificate':CERT,
           'module_count':80,'modified_content_members':sorted(ALLOWED),
           'staged_unsigned_sha256':{path:h(raw) for path,raw in changes.items()},
           'code_changes':0,'playback_changes':0,'tracking_changes':0,
           'apk_signing':'REQUIRED_ORIGINAL_PRIVATE_KEY_NOT_PRESENT',
           'no_new_installable_apk_yet':True}
    (out/'PREPARATION.json').write_text(json.dumps(proof,indent=2,sort_keys=True)+'\n')
    return proof

def validate_module_signature(public_key, manifest, signature):
    result=subprocess.run(['openssl','dgst','-sha256','-verify',str(public_key),'-signature',str(signature),str(manifest)],
                          text=True,capture_output=True,check=False)
    check(result.returncode==0 and 'Verified OK' in result.stdout, 'INVALID_ORIGINAL_MODULE_RSA_SIGNATURE: '+result.stdout+' '+result.stderr)

def assemble(source, staged, module_public_key, target):
    check(not target.exists(), 'NO_APK_OVERWRITE_ALLOWED')
    check_original(source)
    expected=replacements(source)
    for member,raw in expected.items():
        check((staged/member).read_bytes()==raw, 'STAGED_METADATA_CHANGED: '+member)
    sig=staged/SIGNATURE
    check(sig.is_file() and sig.stat().st_size==512,'ORIGINAL_RSA_4096_MODULE_SIGNATURE_MISSING')
    validate_module_signature(module_public_key,staged/MANIFEST,sig)
    expected[SIGNATURE]=sig.read_bytes()
    with ZipFile(source) as original, ZipFile(target,'w',allowZip64=True) as out:
        for info in original.infolist():
            if info.filename in APK_SIGNERS:continue
            out.writestr(info, expected.get(info.filename,original.read(info.filename)))
    verify_members(source,target)
    return {'unsigned_apk':str(target),'sha256':fh(target),'signed':False}

def verify_members(source, candidate):
    check_original(source)
    changes=replacements(source)
    with ZipFile(source) as original, ZipFile(candidate) as new:
        old=set(original.namelist())-APK_SIGNERS
        got=set(new.namelist())-APK_SIGNERS
        check(got==old, 'NON_SIGNATURE_MEMBERS_ADDED_REMOVED')
        found={}
        for name in sorted(old):
            left=original.read(name);right=new.read(name)
            if name in (ALLOWED-{SIGNATURE}):
                check(right==changes[name], 'INCORRECT_VERSION_OR_METADATA: '+name)
            elif name==SIGNATURE:
                check(len(right)==512, 'INVALID_MODULE_SIGNATURE_SIZE')
            else:
                check(left==right, 'OUT_OF_SCOPE_FUNCTIONAL_CHANGE: '+name)
            if left!=right:found[name]=[h(left),h(right)]
        check(set(found)==ALLOWED, 'EXPECTED_FIVE_METADATA_DIFFERENCES_ONLY: '+repr(sorted(found)))
    return {'passed':True,'content_differences':found,'functional_source_members_identical':True}

def main():
    p=argparse.ArgumentParser(description='Exact 2103469 functional APK under 2103476, no code changes')
    sub=p.add_subparsers(dest='command',required=True)
    for name in ('stage','assemble','verify'):
        q=sub.add_parser(name);q.add_argument('--source',required=True,type=Path)
        if name=='stage':q.add_argument('--out',required=True,type=Path)
        if name=='assemble':
            q.add_argument('--staged',required=True,type=Path)
            q.add_argument('--public-key',required=True,type=Path)
            q.add_argument('--target',required=True,type=Path)
        if name=='verify':q.add_argument('--candidate',required=True,type=Path)
    a=p.parse_args()
    v=(stage(a.source,a.out) if a.command=='stage' else assemble(a.source,a.staged,a.public_key,a.target)
       if a.command=='assemble' else verify_members(a.source,a.candidate))
    print(json.dumps(v,indent=2,sort_keys=True))

if __name__=='__main__':main()
