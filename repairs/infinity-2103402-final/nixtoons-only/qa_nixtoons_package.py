#!/usr/bin/env python3
"""Exact WatchNixtoons2-only 2103402 QA package from locked signed reference.

Never updates unrelated application/source state. Native ELF has only two
existing read-only SHA256 owner literals swapped; no executable instructions or
Cobra/native behaviors can change. All component pins remain fully enforced.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import shutil
import struct
from pathlib import Path
from zipfile import ZipFile

APK='Infinity-2103402-Continue-Context-Favourites-QA.apk'
NEW='Infinity-2103402-WatchNixtoons2-Universal-Trakt-QA.apk'
PREFIX='assets/addons/'
CC='script.infinity.commandcenter/'
UR='script.infinity.uirepair/'
WB='script.infinity.watchedbridge/'
SO='lib/arm64-v8a/libkodi.so'
MEMBERS=[CC+'context.py',CC+'plugin.py',UR+'CONTROLLER-PREIMAGES.json',WB+'CONTROLLER-PREIMAGES.json',SO]
OLD_APK_SHA='9279f41ce82c15bd437acc359f40ea71cf0878939a44d5e336b848a3fbaf1c94'
OLD_NATIVE_SHA='4359f4589c6a4aef9138a98c274d7d054610fec7e0f32adf466f23cb29bfc2fb'
NEW_NATIVE_SHA='7de346f0eb9186044bef7668880dc0515054a8fd1607c1dfd7035cf6414d6e35'
OLD_CC={'context.py':'6b22050d7e6c0c320d18e34370b9fd48261f982b181899702e3a7f65b9b0e319',
        'plugin.py':'380dc998e10419b957337a7337719808ada2c946657b3953a63e81ab18f60c84'}
NEW_CC={'context.py':'96e4216c67d6a5a61c7e085da753089ac459373a30240f6acc6bb51a440a4b64',
        'plugin.py':'3077359ad65afa86ca23edd303fc18683f94f6e0a42a75f37e6b6cbaf27bcc4f'}
OLD_PINS_SHA='292f17b456102db915311cfc44120ef743a623a681919e2765e73db8159799f7'
OLD_PINS=25
SIGNATURE={'META-INF/INFINITY.RSA','META-INF/INFINITY.SF','META-INF/MANIFEST.MF'}
COMPONENTS={
 'script.infinity.commandcenter-0.3.5.35-FIXED-QA.zip':'script.infinity.commandcenter-0.3.5.35-NIXTOONS-QA.zip',
 'script.infinity.watchedbridge-1.0.16-FIXED-QA.zip':'script.infinity.watchedbridge-1.0.16-NIXTOONS-QA.zip',
 'script.infinity.uirepair-0.1.18-FIXED-QA.zip':'script.infinity.uirepair-0.1.18-NIXTOONS-QA.zip',
 'skin.infinity.diggz-1.0.5.243.zip':'skin.infinity.diggz-1.0.5.243.zip'}

def check(ok,reason):
    if not ok:raise RuntimeError(reason)

def sha(blob):return hashlib.sha256(blob).hexdigest()

def sha_file(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()

def section_at(raw,offset):
    check(raw[:4]==b'\x7fELF' and raw[4:6]==b'\x02\x01' and raw[18:20]==b'\xb7\x00','ARM64 ELF expected')
    start=struct.unpack_from('<Q',raw,0x28)[0]
    size,count,names=struct.unpack_from('<HHH',raw,0x3a)
    check(size==64 and names<count and start+size*count<=len(raw),'Invalid ELF section header')
    sections=[struct.unpack_from('<IIQQQQIIQQ',raw,start+size*i) for i in range(count)]
    s=sections[names]
    names_blob=raw[s[4]:s[4]+s[5]]
    for sect in sections:
        if sect[4]<=offset and offset+64<=sect[4]+sect[5]:
            i=sect[0];j=names_blob.find(b'\0',i)
            check(j>i,'Invalid ELF section name');return names_blob[i:j].decode(),sect[2]
    raise RuntimeError('SHA is not located inside an ELF section')

def native_patch(original):
    check(sha(original)==OLD_NATIVE_SHA,'Native source is not exact signed 2103402')
    updated=original
    locations={}
    for name in ('context.py','plugin.py'):
        old,new=OLD_CC[name].encode(),NEW_CC[name].encode()
        check(updated.count(old)==1,'Owner literal not unique: '+name)
        offset=updated.index(old)
        section,flags=section_at(updated,offset)
        check(section=='.rodata' and (flags&2) and not (flags&1),'Owner literal not isolated in read-only .rodata')
        check(updated[offset-1]==0 and updated[offset+64]==0,'Owner literal not null-terminated')
        updated=updated[:offset]+new+updated[offset+64:]
        check(len(updated)==len(original),'Native binary length changed')
        locations[name]=offset
    reverted=updated
    for name in ('context.py','plugin.py'):
        offset=locations[name]
        check(updated[offset:offset+64]==NEW_CC[name].encode(),'New ELF owner literal mismatch')
        reverted=reverted[:offset]+OLD_CC[name].encode()+reverted[offset+64:]
    check(reverted==original,'Native image changed beyond two exact owner hash constants')
    check(sha(updated)==NEW_NATIVE_SHA,'Unexpected new native image identity')
    return updated,locations

def new_pins(old,ccbytes,component):
    check(sha(old)==OLD_PINS_SHA,'Input '+component+' 25-file pins were not verified')
    pins=json.loads(old)
    check(isinstance(pins,dict) and len(pins)==OLD_PINS,'Must preserve all 25 original pins')
    for name,oldhash in OLD_CC.items():check(pins.get(name)==oldhash,'Unexpected old component pin: '+name)
    for name,newhash in NEW_CC.items():pins[name]=newhash
    for name,want in pins.items():
        check(sha(ccbytes[name])==want,'Mismatched pinned Command Center file: '+name)
    return (json.dumps(pins,indent=2,ensure_ascii=False)+'\n').encode()

def copy_zip(original,dest,edits,skip_signature=False):
    with ZipFile(original) as source:
        filenames=source.namelist()
        check(len(filenames)==len(set(filenames)) and set(edits).issubset(filenames),'Source duplicate or missing ZIP member')
        with ZipFile(dest,'w',allowZip64=True) as output:
            for info in source.infolist():
                if skip_signature and info.filename in SIGNATURE:continue
                with output.open(copy.copy(info),'w',force_zip64=info.file_size>=2**31) as target:
                    if info.filename in edits:
                        target.write(edits[info.filename])
                    else:
                        with source.open(info) as stream:shutil.copyfileobj(stream,target,4*1024*1024)

def member_diff(before,after,edits,ignore_signature=True):
    with ZipFile(before) as a,ZipFile(after) as b:
        aa,bb=set(a.namelist()),set(b.namelist())
        check(len(aa)==len(a.namelist()) and len(bb)==len(b.namelist()),'Duplicate ZIP member')
        check((aa^bb).issubset(SIGNATURE if ignore_signature else set()),'Unexpected members inserted/removed')
        changed=[]
        for name in sorted(aa&bb):
            if ignore_signature and name in SIGNATURE:continue
            left=hashlib.sha256();right=hashlib.sha256()
            for z,h in ((a,left),(b,right)):
                with z.open(name) as f:
                    for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
            if left.digest()!=right.digest():
                check(name in edits and right.hexdigest()==(edits[name] if isinstance(edits[name],str) else sha(edits[name])),'Unapproved member changed: '+name)
                changed.append(name)
        check(set(changed)==set(edits),'Missing modified member: '+str(set(edits)-set(changed)))
        for protected in ['AndroidManifest.xml','classes.dex',PREFIX+'skin.infinity.diggz/unified/Home.xml']:
            check(a.read(protected)==b.read(protected),'Protected original change: '+protected)
    return changed

def stage(args):
    root=args.input;out=args.output
    check(not out.exists(),'Refusing stale output; use a new staging directory')
    out.mkdir(parents=True)
    parent=root/APK
    check(sha_file(parent)==OLD_APK_SHA,'Wrong signed 2103402 parent reference')
    ccupdates={name:(args.patched/name).read_bytes() for name in OLD_CC}
    for name,want in NEW_CC.items():check(sha(ccupdates[name])==want,'Unreviewed '+name+' changes')
    with ZipFile(parent) as signed:
        check(len(signed.namelist())==len(set(signed.namelist())),'Parent APK inventory duplicated')
        for name,old in OLD_CC.items():check(sha(signed.read(PREFIX+CC+name))==old,'Wrong original '+name)
        cc_names=json.loads(signed.read(PREFIX+UR+'CONTROLLER-PREIMAGES.json'))
        check(len(cc_names)==25,'Unexpected original Command Center pin coverage')
        all_cc={name:ccupdates.get(name,signed.read(PREFIX+CC+name)) for name in cc_names}
        changed={PREFIX+CC+name:blob for name,blob in ccupdates.items()}
        changed[PREFIX+UR+'CONTROLLER-PREIMAGES.json']=new_pins(signed.read(PREFIX+UR+'CONTROLLER-PREIMAGES.json'),all_cc,'UI Repair')
        changed[PREFIX+WB+'CONTROLLER-PREIMAGES.json']=new_pins(signed.read(PREFIX+WB+'CONTROLLER-PREIMAGES.json'),all_cc,'Watched Bridge')
        native,offsets=native_patch(signed.read(SO))
        changed[SO]=native
    copy_zip(parent,out/'unsigned-nixtoons.apk',changed,skip_signature=True)
    altered=member_diff(parent,out/'unsigned-nixtoons.apk',changed)
    check(set(altered)==set(PREFIX+x for x in MEMBERS[:-1])|{SO},'Changed file inventory differs')
    copied=[]
    for original,dest in COMPONENTS.items():
        zip_old=root/original
        with ZipFile(zip_old) as archive:
            # Staged ZIP content must match the exact signed 2103402 APK
            with ZipFile(parent) as signed:
                for name in archive.namelist():
                    if name.endswith('/'):continue
                    check(archive.read(name)==signed.read(PREFIX+name),'Original component differs from signed APK: '+name)
            edits={n[len(PREFIX):]:raw for n,raw in changed.items() if n.startswith(PREFIX) and
                   n[len(PREFIX):].startswith(original.split('-')[0]+'/')}
        if edits:copy_zip(zip_old,out/dest,edits)
        else:shutil.copyfile(zip_old,out/dest)
        with ZipFile(out/dest) as archive:
            with ZipFile(out/'unsigned-nixtoons.apk') as staged:
                for name in archive.namelist():
                    if name.endswith('/'):continue
                    check(archive.read(name)==staged.read(PREFIX+name),'New ZIP/APK mismatch: '+name)
        copied.append(dest)
    report={
      'baseline_run':40158384817,
      'baseline_apk_sha256':OLD_APK_SHA,
      'native_engine_original_sha256':OLD_NATIVE_SHA,
      'native_engine_new_sha256':sha(changed[SO]),
      'native_engine_recompiled':False,
      'native_patch':'Only two existing 64-byte read-only SHA owner constants; all instructions unchanged',
      'native_offsets':offsets,
      'changed_app_members':altered,
      'preserved':'Every other APK member byte-identical, including the entire skin, Cobra, Continue Playing, Otaku, Favorites and the five visual fixes',
      'verification':'Both UI Repair and Watched Bridge still require all 25 exact CC file hashes',
      'protection':'No user profile, data, service, provider, native gesture, or playback files written',
      'user_fold_validation':'PENDING',
      'components':copied,
      'search_crash':'NOT IN SCOPE',
      'known_home_reload':'NOT IN SCOPE',
    }
    (out/'NIXTOONS-SCOPE-RECEIPT.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: exact five-member WatchNixtoons2-only candidate staged; no native recompilation')

def verify(args):
    parent=args.input/APK
    check(sha_file(parent)==OLD_APK_SHA,'Wrong original reference')
    target=args.signed
    with ZipFile(target) as z:
        check(len(z.namelist())==len(set(z.namelist())),'Duplicated signed APK members')
        for name,want in NEW_CC.items():check(sha(z.read(PREFIX+CC+name))==want,'Wrong new '+name)
        for pin in [UR+'CONTROLLER-PREIMAGES.json',WB+'CONTROLLER-PREIMAGES.json']:
            table=json.loads(z.read(PREFIX+pin))
            check(len(table)==25,'Missing mandatory exact pins')
            for name,want in table.items():check(sha(z.read(PREFIX+CC+name))==want,'Mismatch CC '+name)
        with z.open(SO) as native:
            digest=hashlib.sha256()
            for part in iter(lambda:native.read(4*1024*1024),b''):
                digest.update(part)
        check(digest.hexdigest()==NEW_NATIVE_SHA,'Final signed native image unexpectedly changed')
        edits={name:z.read(name) for name in [PREFIX+m for m in MEMBERS[:-1]]}
        edits[SO]=NEW_NATIVE_SHA
    changed=member_diff(parent,target,edits)
    check(set(changed)==set(edits),'Not all scoped members changed')
    print('PASS: signed APK has exact five approved changes, retained signer must also be confirmed using apksigner')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('command',choices=['stage','verify'])
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--patched',type=Path)
    p.add_argument('--output',type=Path)
    p.add_argument('--signed',type=Path)
    a=p.parse_args()
    if a.command=='stage':
        if not a.patched or not a.output:p.error('stage needs --patched and --output')
        stage(a)
    else:
        if not a.signed:p.error('verify needs --signed')
        verify(a)
