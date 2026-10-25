#!/usr/bin/env python3
"""Exact signed 2103402 -> 2103403 QA, preserving all unrelated APK bytes.

This script wraps the audited 2103402 APK delta builder. It modifies only three
Command Center files, two controller pin tables, two controller addon versions,
three native read-only owner hash literals, and the typed manifest versionCode.
No executable native instruction, DEX, skin or Cobra file is changed.
"""
import argparse, hashlib, importlib.util, json, struct
from pathlib import Path
from zipfile import ZipFile

P=Path(__file__).resolve().parents[1]
ORIGINAL=P/'infinity-2103402-final'/'nixtoons-only'/'qa_nixtoons_package.py'
spec=importlib.util.spec_from_file_location('_qa2103402',ORIGINAL)
base=importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
OLD_APK='Infinity-2103402-WatchNixtoons2-Universal-Trakt-QA.apk'
FINAL_APK='Infinity-2103403-Tracking-Search-Stabilization-QA.apk'
OLD_APK_SHA='a6beccee8a055dc64eb86ba6dd89f5bef0d7da0e7a635fe45ca65de8be3d77a9'
OLD_NATIVE_SHA='7de346f0eb9186044bef7668880dc0515054a8fd1607c1dfd7035cf6414d6e35'
NEW_NATIVE_SHA='88817f2a552bd7302b7323602f35453eda10ee996c187a7e1b430c0fc29c7b6b'
OLD_PINS_SHA='058d6e45df76f41b3f4413500186fe04f94007a2783f1babdca8b4e082b83b99'
NEW_PINS_SHA='6105ff3f488120c67350a105b2ec85349ab448b55fc400248f0d002d768032e9'
OLD_CC={
 'context.py':'96e4216c67d6a5a61c7e085da753089ac459373a30240f6acc6bb51a440a4b64',
 'infinity_search.py':'fb469b20cea3fd86e7eec454aba7ae25d14472d9ebddea36120841925c170be0',
 'addon.xml':'f6021a3f3c556a0a5377d462552a01c7f6fab463c495e7070c9a916451b379d2'}
NEW_CC={
 'context.py':'aec101d4c9ba7b38eb7b98876fd91fa5042b70f17ae0ca33d4832df6cb73e14f',
 'infinity_search.py':'a5640a725d07440e914fd5f8d83a29196ea9cbb1104686f1929b5140040b2c44',
 'addon.xml':'1b0b2ae9da31cd4772463799d4a3d44d0fce0639ef514221d506f25d09efc10b'}
PFX='assets/addons/'
CC='script.infinity.commandcenter/'
UR='script.infinity.uirepair/'
WB='script.infinity.watchedbridge/'
NATIVE='lib/arm64-v8a/libkodi.so'
MANIFEST='AndroidManifest.xml'
COMPONENTS={
 'script.infinity.commandcenter-0.3.5.35-NIXTOONS-QA.zip':'script.infinity.commandcenter-0.3.5.36-2103403-QA.zip',
 'script.infinity.uirepair-0.1.18-NIXTOONS-QA.zip':'script.infinity.uirepair-0.1.19-2103403-QA.zip',
 'script.infinity.watchedbridge-1.0.16-NIXTOONS-QA.zip':'script.infinity.watchedbridge-1.0.17-2103403-QA.zip',
 'skin.infinity.diggz-1.0.5.243.zip':'skin.infinity.diggz-1.0.5.243.zip'}
VERSIONS={CC:('0.3.5.35','0.3.5.36'),UR:('0.1.18','0.1.19'),WB:('1.0.16','1.0.17')}
APP_CHANGES={PFX+CC+k for k in NEW_CC}|{
 PFX+UR+'CONTROLLER-PREIMAGES.json',PFX+WB+'CONTROLLER-PREIMAGES.json',
 PFX+UR+'addon.xml',PFX+WB+'addon.xml',NATIVE,MANIFEST}

def sha(raw):return hashlib.sha256(raw).hexdigest()

def configure():
    base.APK=OLD_APK
    base.NEW=FINAL_APK
    base.OLD_APK_SHA=OLD_APK_SHA
    base.OLD_NATIVE_SHA=OLD_NATIVE_SHA
    base.NEW_NATIVE_SHA=NEW_NATIVE_SHA
    base.OLD_PINS_SHA=OLD_PINS_SHA
    base.OLD_CC=OLD_CC
    base.NEW_CC=NEW_CC
    base.MEMBERS=[CC+k for k in NEW_CC]+[
        UR+'CONTROLLER-PREIMAGES.json',WB+'CONTROLLER-PREIMAGES.json',NATIVE]
    base.COMPONENTS=COMPONENTS
    base.native_patch=native_patch_three_verified_owners

def version_change(raw,old,new):
    a=('version="'+old+'"').encode();b=('version="'+new+'"').encode()
    assert len(a)==len(b) and raw.count(a)==1,'Unexpected addon.xml input version'
    return raw.replace(a,b,1)

def manifest_change(raw):
    old=struct.pack('<I',2103402);new=struct.pack('<I',2103403)
    assert raw.count(old)==1 and raw.count(new)==0,'Unexpected binary manifest version'
    offset=raw.index(old)
    assert raw[offset-4:offset]==b'\x08\x00\x00\x10','Not a binary AXML integer value'
    return raw[:offset]+new+raw[offset+4:]

def verify_scope(parent,candidate):
    assert len(APP_CHANGES)==9
    with ZipFile(parent) as a,ZipFile(candidate) as b:
        pa,pb=a.namelist(),b.namelist()
        assert len(pa)==len(set(pa)) and len(pb)==len(set(pb)),'Duplicate APK entries'
        assert (set(pa)^set(pb)).issubset(base.SIGNATURE),'Unexpected changed ZIP inventory'
        differences=[]
        for name in sorted(set(pa)&set(pb)):
            if name in base.SIGNATURE:continue
            digests=[]
            for archive in (a,b):
                h=hashlib.sha256()
                with archive.open(name) as f:
                    for part in iter(lambda:f.read(4*1024*1024),b''):h.update(part)
                digests.append(h.digest())
            if digests[0]!=digests[1]:differences.append(name)
        assert set(differences)==APP_CHANGES, 'Unapproved APK contents: '+str(set(differences)^APP_CHANGES)
        assert b.read(MANIFEST)==manifest_change(a.read(MANIFEST))
        assert sha(b.read(NATIVE))==NEW_NATIVE_SHA
        for name,digest in NEW_CC.items():
            assert sha(b.read(PFX+CC+name))==digest
        for dirname in (CC,UR,WB):
            old,new=VERSIONS[dirname]
            assert b.read(PFX+dirname+'addon.xml')==version_change(a.read(PFX+dirname+'addon.xml'),old,new)
        for dirname in (UR,WB):
            pins=b.read(PFX+dirname+'CONTROLLER-PREIMAGES.json')
            assert sha(pins)==NEW_PINS_SHA
            obj=json.loads(pins);assert len(obj)==25
            for name,digest in obj.items():
                assert sha(b.read(PFX+CC+name))==digest, 'Owner pin differs: '+name
        for protected in ('classes.dex',PFX+'skin.infinity.diggz/unified/Home.xml'):
            assert a.read(protected)==b.read(protected),'Protected user component changed: '+protected
    print('PASS: exact nine-member scope, 25 controller pin contracts, manifest and native SHA')

def verify_components(apk,directory):
    with ZipFile(apk) as app:
        for filename in COMPONENTS.values():
            with ZipFile(directory/filename) as part:
                for name in part.namelist():
                    if not name.endswith('/'):
                        assert part.read(name)==app.read(PFX+name), 'ZIP/APK mismatch '+name
    print('PASS: every matching component ZIP equals signed APK bytes')

def native_patch_three_verified_owners(original):
    """Extend the existing .rodata-only owner update without touching ARM64 instructions."""
    base.check(sha(original)==OLD_NATIVE_SHA,'Wrong original ARM64 image hash')
    updated=original
    locations={}
    for name in OLD_CC:
        previous,current=OLD_CC[name].encode(),NEW_CC[name].encode()
        base.check(updated.count(previous)==1,'Owner literal not unique: '+name)
        offset=updated.index(previous)
        section,flags=base.section_at(updated,offset)
        base.check(section=='.rodata' and (flags&2) and not(flags&1),
                   'Owner literal not in immutable .rodata: '+name)
        base.check(updated[offset-1]==0 and updated[offset+64]==0,
                   'Hash constant not delimited by nulls')
        updated=updated[:offset]+current+updated[offset+64:]
        base.check(len(updated)==len(original),'Native binary length changed')
        locations[name]=offset
    rollback=updated
    for name,offset in locations.items():
        base.check(rollback[offset:offset+64]==NEW_CC[name].encode(),
                   'Patched native owner digest mismatch: '+name)
        rollback=rollback[:offset]+OLD_CC[name].encode()+rollback[offset+64:]
    base.check(rollback==original,'Native code or unapproved content changed')
    base.check(sha(updated)==NEW_NATIVE_SHA,'Unexpected ARM64 output digest')
    return updated,locations


def stage(args):
    configure()
    for name,digest in NEW_CC.items():
        assert sha((args.patched/name).read_bytes())==digest,'Unreviewed patch input '+name
    # Audited original builder validates parent signing SHA, native .rodata
    # section flags, reversibility, source hashes and immutable APK content.
    base.stage(args)
    original=args.output/'unsigned-nixtoons.apk'
    interim=args.output/'unsigned-2103403.apk'
    with ZipFile(original) as z:
        extra={MANIFEST:manifest_change(z.read(MANIFEST))}
        for dirname in (UR,WB):
            old,new=VERSIONS[dirname]
            extra[PFX+dirname+'addon.xml']=version_change(z.read(PFX+dirname+'addon.xml'),old,new)
    base.copy_zip(original,interim,extra)
    original.unlink();interim.rename(original)
    for dirname in (UR,WB):
        filename=next(v for k,v in COMPONENTS.items() if k.startswith(dirname.rstrip('/')))
        current=args.output/filename
        temporary=args.output/('update-'+filename)
        base.copy_zip(current,temporary,{dirname+'addon.xml':extra[PFX+dirname+'addon.xml']})
        current.unlink();temporary.rename(current)
    (args.output/'NIXTOONS-SCOPE-RECEIPT.json').unlink()
    verify_scope(args.input/OLD_APK,original)
    verify_components(original,args.output)
    receipt={'candidate':FINAL_APK,'baseline_sha256':OLD_APK_SHA,
        'native_previous_sha256':OLD_NATIVE_SHA,'native_new_sha256':NEW_NATIVE_SHA,
        'native_executable_code_modified':False,'changed_APK_members':sorted(APP_CHANGES),
        'version_code':2103403,'components':list(COMPONENTS.values()),
        'Search_crash_root_cause':'NOT YET PROVEN; keyboard and Search worker lifecycle hardened',
        'Cobra_modified':False,'user_data_modified':False,'physical_Fold_acceptance':'PENDING'}
    (args.output/'INFINITY-2103403-QA-RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('PASS: matching QA package staged for original release signing')

def verify(args):
    configure()
    assert base.sha_file(args.input/OLD_APK)==OLD_APK_SHA
    verify_scope(args.input/OLD_APK,args.signed)
    verify_components(args.signed,args.output)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['stage','verify'])
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--patched',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--signed',type=Path)
    args=parser.parse_args()
    if args.action=='stage':
        assert args.patched is not None
        stage(args)
    else:
        assert args.signed is not None
        verify(args)
