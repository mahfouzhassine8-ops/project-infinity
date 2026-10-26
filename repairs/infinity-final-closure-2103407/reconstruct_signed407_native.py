"""Recover the exact signed407 engine heritage before applying new native code.

Replays the checked-in producers, proves all 9,407 original source hashes against
the successful final pre407 native build, then reconstructs only the immutable
hash-string edits demonstrated by comparing that ELF with signed407. No source
from an older engine may silently substitute for the accepted Favourites repair.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
import mmap
from pathlib import Path
import shutil
import struct
import sys
import tempfile
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[2]
REPAIRS=ROOT/'repairs/infinity-2103402-final'
NATIVE_BASE='4359f4589c6a4aef9138a98c274d7d054610fec7e0f32adf466f23cb29bfc2fb'
NATIVE_407='a7e0d2e7f314af197c486eb674ecf7e4b61649801829ec10ba4a0b1968ef36b7'
APK_407='3616c4e69c976bd63b36170d4dbbd9b190a7ec2eace4bc0c34c3c72f7f9e8578'
SOURCE_ZIP='bc55f659aadf2a806297abdd6104ddd362906179e96b9c2b391eee8556a4f0a8'
SOURCE_MAP='df545f4b03e56a9b212c9a7cf34a900fe594b153b8ee2b655dff6fd84195c801'


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def load(name):
    sys.path.insert(0,str(REPAIRS))
    spec=importlib.util.spec_from_file_location('retained_'+name,REPAIRS/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def prove_literals(compiled,signed407):
    if sha(compiled)!=NATIVE_BASE or sha(signed407)!=NATIVE_407:
        raise ValueError('Wrong actual compiled/signed407 ARM64 inputs')
    with Path(compiled).open('rb') as a,Path(signed407).open('rb') as b:
        original=mmap.mmap(a.fileno(),0,access=mmap.ACCESS_READ)
        current=mmap.mmap(b.fileno(),0,access=mmap.ACCESS_READ)
        if len(original)!=len(current):raise ValueError('Native size differs; not the retained compiled engine')
        offset=struct.unpack_from('<Q',current,0x28)[0]
        width,count,strings=struct.unpack_from('<HHH',current,0x3a)
        if width!=64 or strings>=count:raise ValueError('Invalid ELF section inventory')
        sections=[struct.unpack_from('<IIQQQQIIQQ',current,offset+width*i) for i in range(count)]
        table=sections[strings];names=current[table[4]:table[4]+table[5]]
        rodata=next(s for s in sections if names[s[0]:names.find(b'\0',s[0])]==b'.rodata')
        slots={}
        for start in range(0,len(original),1024*1024):
            before,after=original[start:start+1024*1024],current[start:start+1024*1024]
            if before==after:continue
            for local,(x,y) in enumerate(zip(before,after)):
                if x==y:continue
                at=start+local
                if not rodata[4]<=at<rodata[4]+rodata[5]:raise ValueError('Executable or unrelated native bytes differ')
                begin=current.rfind(b'\0',rodata[4],at)+1;end=current.find(b'\0',at)
                old,new=original[begin:end],current[begin:end]
                if (len(old)!=64 or len(new)!=64 or
                    any(c not in b'0123456789abcdef' for c in old+new) or
                    not rodata[4]<=begin<end<=rodata[4]+rodata[5] or
                    not rodata[2]&2 or rodata[2]&1):
                    raise ValueError('A native difference is not a bounded immutable hash slot')
                slots[begin]={'before':old.decode(),'after':new.decode()}
        if len(slots)!=8:raise ValueError('Expected exact eight retained407 readonly updates')
        for at,value in slots.items():
            if original[at-1]!=0 or current[at-1]!=0:raise ValueError('Missing native literal boundary')
        original.close();current.close()
    mapping={v['before']:v['after'] for v in slots.values()}
    if len(mapping)!=8:raise ValueError('Ambiguous literal update lineage')
    return mapping,slots


def reconstruct(foundation,owner,compiled,signed407,target,evidence):
    foundation,owner,compiled,target,evidence=map(Path,(foundation,owner,compiled,target,evidence))
    if target.exists() or evidence.exists():raise ValueError('Refuse an existing reconstructed source/evidence target')
    if sha(foundation/'Infinity-Targeted-Source-and-Evidence.zip')!=SOURCE_ZIP or sha(foundation/'NATIVE-SOURCE-MAP.json')!=SOURCE_MAP:
        raise ValueError('Unverified complete source foundation')
    if sha(signed407)!=APK_407:raise ValueError('Exact protected signed407 APK required')
    proof=json.loads((compiled/'ENGINE-PROOF.json').read_text())
    expected=json.loads((compiled/'NATIVE-SOURCE-MAP.json').read_text())
    if (proof.get('native_sha256')!=NATIVE_BASE or proof.get('complete_native_engine_compiled') is not True or
            proof.get('reviewed_file_count')!=9407 or len(expected)!=9407 or
            proof.get('source_commit')!='8595cd8238c9e6973a671f88d68d7f4707d0a105'):
        raise ValueError('Missing exact final pre407 native compilation/source binding')
    evidence.mkdir(parents=True)
    with tempfile.TemporaryDirectory(dir=evidence) as work:
        work=Path(work)
        oldapk=foundation/'Infinity-2103401-Universal-Performance-QA.apk'
        ownerapk=next(owner.glob('*.apk'))
        owner_patch=load('native_ownership_qa')
        overlay=work/'retained-owner-overlay'
        owner_patch.stage(foundation/'Infinity-Targeted-Source-and-Evidence.zip',foundation/'NATIVE-SOURCE-MAP.json',oldapk,ownerapk,overlay)
        restore=load('restore_reviewed_engine')
        restore.restore(foundation/'Infinity-Targeted-Source-and-Evidence.zip',foundation/'NATIVE-SOURCE-MAP.json',
                        foundation/'SOURCE-DELTA.json',overlay,target,work/'retained-map')
        holds=load('qa_component_holds')
        with ZipFile(ownerapk) as archive:
            original=archive.read('assets/addons/script.infinity.commandcenter/context.py')
            context=holds.change_context(original)
            # This is the original retained CC35 source set required by the
            # existing Favourites producer, not a new application package.
            mini=work/'retained-CC35-source-input.zip'
            with ZipFile(mini,'w') as out:
                for name in archive.namelist():
                    if name.startswith('assets/addons/script.infinity.commandcenter/') and not name.endswith('/'):
                        data=archive.read(name)
                        if name.endswith('/addon.xml'):
                            if data.count(b'version="0.3.5.36"')!=1:raise ValueError('Wrong retained CC36 manifest')
                            data=data.replace(b'version="0.3.5.36"',b'version="0.3.5.35"',1)
                        out.writestr(name,data)
        favourites=load('qa_native_favourites')
        favourites.apply(target,work/'retained-map/NATIVE-SOURCE-MAP.json',mini,context,work/'retained-favourites')
        actual={p.relative_to(target).as_posix():sha(p) for p in target.rglob('*') if p.is_file()}
        if actual!=expected:raise ValueError('Source reconstruction differs from the successful final pre407 9407-file native map')
        native407=work/'signed407-native.so'
        with ZipFile(signed407) as z,z.open('lib/arm64-v8a/libkodi.so') as src,native407.open('wb') as out:
            shutil.copyfileobj(src,out,4*1024*1024)
        mapping,slots=prove_literals(compiled/'libkodi.so',native407)
    counts={value:0 for value in mapping};changes={};final=dict(expected)
    for name in sorted(expected):
        path=target/name
        if path.is_symlink():continue
        data=path.read_bytes();after=data
        for old,new in mapping.items():
            quoted=('"'+old+'"').encode();replacement=('"'+new+'"').encode()
            counts[old]+=after.count(quoted)
            after=after.replace(quoted,replacement)
        if after!=data:
            changes[name]={'compiled_source_sha256':expected[name],'signed407_source_sha256':hashlib.sha256(after).hexdigest()}
            path.write_bytes(after);final[name]=hashlib.sha256(after).hexdigest()
    if set(changes)!={'xbmc/platform/android/activity/InfinityScriptCheckpointContracts.cpp'} or not all(counts.values()):
        raise ValueError('Unexplained source hash lineage outside exact407 owner table')
    result={'source_count':9407,'compiled_native_build':40158384817,'compiled_native_sha256':NATIVE_BASE,
            'signed407_native_sha256':NATIVE_407,'signed407_apk_sha256':APK_407,'readonly_native_hash_slots':slots,
            'all_native_bytes_outside_eight_hash_slots_identical':True,
            'retained_Favourites_header_input_and_hit_dispatch':True,
            'compiled_source_map_exact_match_before_pin_updates':True,
            'signed407_source_hash_updates':changes,'hash_update_source_occurrences':counts,
            'Cobra_and_unowned_sources_changed':False,'new_native_repair_applied':False}
    (evidence/'SIGNED407-NATIVE-RECONSTRUCTION.json').write_text(json.dumps(result,indent=2)+'\n')
    (evidence/'SIGNED407-NATIVE-SOURCE-MAP.json').write_text(json.dumps(final,sort_keys=True,indent=2)+'\n')
    return result


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser()
    for name in ('foundation','owner','compiled','signed407','target','evidence'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(reconstruct(a.foundation,a.owner,a.compiled,a.signed407,a.target,a.evidence),indent=2))
