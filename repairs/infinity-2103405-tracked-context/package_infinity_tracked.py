#!/usr/bin/env python3
"""Exact scoped unsigned packaging from locked signed Infinity 2103404.

Only WatchNixtoons2 context-item XML and matching versions, read-only
native hash ownership literals and Android version code change. Sign using the
original permanent keystore through the separately gated GitHub workflow.
"""
from pathlib import Path
from zipfile import ZipFile
import argparse,ast,copy,hashlib,json,re,struct,sys

PARENT_NAME='Infinity-2103404-WatchNixtoons2-Source-Location-QA.apk'
OUT_NAME='Infinity-2103405-WatchNixtoons2-Infinity-Tracked-Context-QA.apk'
PARENT_SHA='f3198f929b8e5d031648720ab0dd3bf47dd966b3828f86282f9c4a1c678bb8d4'
PREFIX='assets/addons/'
CC='script.infinity.commandcenter/'
WB='script.infinity.watchedbridge/'
UI='script.infinity.uirepair/'
NATIVE='lib/arm64-v8a/libkodi.so'
SIGNATURE={'META-INF/INFINITY.RSA','META-INF/INFINITY.SF','META-INF/MANIFEST.MF'}
V={'script.infinity.commandcenter':('0.3.5.37','0.3.5.38'),
   'script.infinity.watchedbridge':('1.0.18','1.0.19'),
   'script.infinity.uirepair':('0.1.20','0.1.21')}
COMPONENTS={'script.infinity.commandcenter':'script.infinity.commandcenter-0.3.5.37-2103404-QA.zip',
            'script.infinity.watchedbridge':'script.infinity.watchedbridge-1.0.18-2103404-QA.zip',
            'script.infinity.uirepair':'script.infinity.uirepair-0.1.20-2103404-QA.zip',
            'skin.infinity.diggz':'skin.infinity.diggz-1.0.5.243.zip'}

def sha(blob):return hashlib.sha256(blob).hexdigest()

def checked(condition,message):
    if not condition:raise AssertionError(message)

def replacement(original,old,new):
    checked(original.count(old)==1,'Expected exactly one occurrence of: '+repr(old[:80]))
    return original.replace(old,new,1)

def addon_version(blob,old,new):
    pattern=('version="'+old+'"').encode()
    desired=('version="'+new+'"').encode()
    checked(len(pattern)==len(desired),'Version length must remain constant')
    return replacement(blob,pattern,desired)

def manifest_version(blob):
    old=struct.pack('<I',2103404);new=struct.pack('<I',2103405)
    checked(blob.count(old)==1 and new not in blob,'Unexpected Android versionCode inventory')
    i=blob.find(old)
    checked(blob[i-4:i]==b'\x08\x00\x00\x10','Binary AXML versionCode must be typed integer')
    return blob[:i]+new+blob[i+4:]

def native_locations(raw,old):
    sections_start=struct.unpack_from('<Q',raw,0x28)[0]
    section_size,count,strings=struct.unpack_from('<HHH',raw,0x3a)
    checked(section_size==64 and strings<count,'Unexpected native ELF layout')
    sections=[struct.unpack_from('<IIQQQQIIQQ',raw,sections_start+section_size*i) for i in range(count)]
    names_section=sections[strings]
    table=raw[names_section[4]:names_section[4]+names_section[5]]
    locations=[];offset=0
    while True:
        i=raw.find(old,offset)
        if i<0:break
        match=[]
        for sec in sections:
            if sec[4]<=i and i+64<=sec[4]+sec[5]:
                name_index=sec[0]; name_end=table.find(b'\0',name_index)
                match=[table[name_index:name_end],sec[2]];break
        checked(match and match[0]==b'.rodata' and match[1]&2 and not match[1]&1,
                'Native owner value outside immutable .rodata')
        checked(raw[i-1]==0 and raw[i+64]==0,'Native owner literal missing null boundaries')
        locations.append(i);offset=i+64
    return locations

def copy_zip(src,dst,updates,remove_signatures=False):
    with ZipFile(src) as reader,ZipFile(dst,'w',allowZip64=True) as writer:
        names=set(reader.namelist())
        checked(set(updates).issubset(names),'Updates not present in exact signed archive')
        checked(len(names)==len(reader.namelist()),'Duplicate parent members')
        for info in reader.infolist():
            if remove_signatures and info.filename in SIGNATURE:continue
            with writer.open(copy.copy(info),'w',force_zip64=info.file_size>=2**31) as out:
                if info.filename in updates:
                    out.write(updates[info.filename])
                else:
                    with reader.open(info) as src: 
                        while True:
                            b=src.read(4*1024*1024)
                            if not b:break
                            out.write(b)

def output_name(prefix):
    if prefix=='skin.infinity.diggz':return 'skin.infinity.diggz-1.0.5.243.zip'
    new=V[prefix][1]
    return prefix+'-'+new+'-2103405-QA.zip'

def stage(input_dir,patched,out):
    parent=input_dir/PARENT_NAME
    checked(sha(parent.read_bytes())==PARENT_SHA,'Wrong signed reference: 2103403 exact parent is required')
    checked(not out.exists(),'Staging directory exists; do not overwrite another build')
    out.mkdir(parents=True)
    cc_edits={name:(patched/name).read_bytes() for name in
              ('checkpoint_runtime.py','infinity_trakt.py')}
    with ZipFile(parent) as reference:
        cc_edits['addon.xml']=(patched/'addon.xml').read_bytes()
        expected_old=reference.read(PREFIX+CC+'addon.xml')
        checked(sha(expected_old)=='bb0ef93153402f1cfe62cfb7045689f78f4f623c8d420622fe1de110c5411dd7', 'Wrong signed addon registration')
        checked(sha(cc_edits['addon.xml'])=='987c512db6eceba9ec8d078dc6e962358bd58d4093fe1619c4319377b66bf2c4', 'Unreviewed Infinity Tracked menu registration')
        bridge={
            'addon.xml':addon_version(reference.read(PREFIX+WB+'addon.xml'),*V['script.infinity.watchedbridge']),
            'controller.py':replacement(reference.read(PREFIX+WB+'controller.py'),b'0.3.5.37',b'0.3.5.38')}
        # Bind the two currently installed Bridge source hashes into Trakt's
        # reciprocal integrity checks. No unverified source may override them.
        original=reference.read(PREFIX+CC+'infinity_trakt.py').decode()
        matches=re.search(r'BRIDGE_PINS\s*=\s*(\{[^\n]+\})',original)
        checked(matches is not None,'Cannot locate exact reciprocal bridge contract')
        old_pins=ast.literal_eval(matches.group(1))
        for bridge_name,new_body in bridge.items():
            # 2103403 incorrectly pins the earlier Bridge addon.xml, even
            # though it shipped 1.0.17. Replace the actual reviewed expected
            # constant instead of assuming the broken pin was already correct.
            before=old_pins[bridge_name].encode()
            after=sha(new_body).encode()
            cc_edits['infinity_trakt.py']=replacement(cc_edits['infinity_trakt.py'],before,after)
        for name,edited in cc_edits.items():
            compile(edited.decode(),'addon.xml' if name=='addon.xml' else name,'exec') if name.endswith('.py') else None
        # Both controller tables must have exactly 25 independently pinned CC files.
        pin_edits={}
        for helper in (WB,UI):
            old=reference.read(PREFIX+helper+'CONTROLLER-PREIMAGES.json')
            pins=json.loads(old);checked(len(pins)==25,'Expected 25 reviewed Command Center pins')
            for name,raw in cc_edits.items():
                checked(pins[name]==sha(reference.read(PREFIX+CC+name)),'Unexpected baseline CC pin '+name)
                pins[name]=sha(raw)
            for name,pin in pins.items():
                content=cc_edits.get(name,reference.read(PREFIX+CC+name))
                checked(sha(content)==pin,'Mismatch in pinned Command Center member '+name)
            pin_edits[helper]=(json.dumps(pins,indent=2,ensure_ascii=False)+'\n').encode()
        old_native=reference.read(NATIVE)
        raw=bytearray(old_native)
        all_offsets={}
        for name,new in cc_edits.items():
            old=sha(reference.read(PREFIX+CC+name)).encode()
            new_sha=sha(new).encode()
            offsets=native_locations(raw,old)
            expected=2 if name=='addon.xml' else 1
            checked(len(offsets)==expected,'Wrong number of native immutable owner hash slots for '+name)
            for i in offsets:raw[i:i+64]=new_sha
            all_offsets[name]=offsets
        for name,offsets in all_offsets.items():
            old=sha(reference.read(PREFIX+CC+name)).encode()
            for i in offsets:raw[i:i+64]=old
        checked(bytes(raw)==old_native,'Reversibility failed: native code or unrelated data changed')
        for name,offsets in all_offsets.items():
            new_sha=sha(cc_edits[name]).encode()
            for i in offsets:raw[i:i+64]=new_sha
        changed={PREFIX+CC+name:blob for name,blob in cc_edits.items()}
        changed.update({PREFIX+WB+name:blob for name,blob in bridge.items()})
        changed[PREFIX+UI+'addon.xml']=addon_version(reference.read(PREFIX+UI+'addon.xml'),*V['script.infinity.uirepair'])
        changed[PREFIX+WB+'CONTROLLER-PREIMAGES.json']=pin_edits[WB]
        changed[PREFIX+UI+'CONTROLLER-PREIMAGES.json']=pin_edits[UI]
        changed['AndroidManifest.xml']=manifest_version(reference.read('AndroidManifest.xml'))
        changed[NATIVE]=bytes(raw)
        print('Staging exact member scope:',list(changed))
    native_ref=sha(old_native);native_new=sha(changed[NATIVE]);del old_native,raw
    unsigned=out/'unsigned-2103405.apk'
    copy_zip(parent,unsigned,changed,remove_signatures=True)
    # All exact component ZIPs use the same bytes as the APK, including pins.
    for prefix,origin in COMPONENTS.items():
        source=input_dir/origin
        destination=out/output_name(prefix)
        edits={name[len(PREFIX):]:value for name,value in changed.items()
               if name.startswith(PREFIX+prefix+'/')}
        copy_zip(source,destination,edits)
        with ZipFile(unsigned) as app,ZipFile(destination) as addon:
            for name in addon.namelist():
                if not name.endswith('/'):
                    checked(app.read(PREFIX+name)==addon.read(name),'Component differs from unsigned APK: '+name)
    receipt=dict(baseline_sha256=PARENT_SHA,version_code=2103405,
                 native_old=native_ref,native_new=native_new,
                 native_executable_instructions_changed=False,
                 modified_app_members=sorted(changed),
                 preview_test='host only, Fold acceptance pending',
                 source_only_scope='WatchNixtoons2-only native context registration',
                 external_trakt_identity_verified=False,
                 original_cert_required=True)
    (out/'INFINITY-2103405-CONTEXT-RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('PASS scoped stage; signer required; native hash',native_new)

def verify(input_dir,candidate,stage_dir):
    parent=input_dir/PARENT_NAME
    scope=json.loads((stage_dir/'INFINITY-2103405-CONTEXT-RECEIPT.json').read_text())
    checked(sha(parent.read_bytes())==PARENT_SHA,'Parent changed')
    with ZipFile(parent) as a,ZipFile(candidate) as b:
        aa=set(a.namelist());bb=set(b.namelist())
        checked((aa^bb).issubset(SIGNATURE),'Unapproved ZIP member insertion/removal')
        actual=[]
        for name in sorted(aa&bb):
            if name in SIGNATURE:continue
            h1=hashlib.sha256();h2=hashlib.sha256()
            for z,h in ((a,h1),(b,h2)):
                with z.open(name) as s:
                    for part in iter(lambda:s.read(2*1024*1024),b''):h.update(part)
            if h1.digest()!=h2.digest():actual.append(name)
        checked(set(actual)==set(scope['modified_app_members']),
                'Unexpected modified member(s): '+str(set(actual)^set(scope['modified_app_members'])))
        checked(sha(b.read(NATIVE))==scope['native_new'],'Unexpected native ELF')
        checked(b.read('AndroidManifest.xml')==manifest_version(a.read('AndroidManifest.xml')),'Unexpected manifest change')
        for name in ['classes.dex',PREFIX+'skin.infinity.diggz/unified/Home.xml', PREFIX+CC+'context.py',PREFIX+CC+'plugin.py',PREFIX+CC+'resume_hub.py']:
            checked(a.read(name)==b.read(name),'Protected unrelated content modified: '+name)
        for helper in (WB,UI):
            pins=json.loads(b.read(PREFIX+helper+'CONTROLLER-PREIMAGES.json'))
            checked(len(pins)==25,'Pin inventory changed')
            for name,pin in pins.items():
                checked(sha(b.read(PREFIX+CC+name))==pin,'Pin mismatch: '+name)
    print('PASS diff & all protected baselines, 25+25 source hash pins')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('command',choices=['stage','verify'])
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--patched',type=Path)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--signed',type=Path)
    args=p.parse_args()
    if args.command=='stage':stage(args.input,args.patched,args.out)
    else:verify(args.input,args.signed,args.out)