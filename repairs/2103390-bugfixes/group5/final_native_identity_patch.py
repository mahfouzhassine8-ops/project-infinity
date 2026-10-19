#!/usr/bin/env python3
"""Group #5 crash-recorder identity correction, sourced from actual libkodi.so.

Does NOT claim SIGSEGV/139 root-cause repair. It replaces ONE historical
64-character SHA string in the existing companion ELF .rodata with the actual
final engine SHA. Zero functional code changes; no ABI/exports/offset changes.
Prepared source only until Group #7 full native build and package acceptance.

The native engine may be Group2/3 rebuilt for the final APK. Derive identity
from its actual final bytes, NOT precompile sources or historical APK metadata.
"""
from __future__ import annotations
from pathlib import Path
import hashlib
import struct
import json
from zipfile import ZipFile

BASE_APK_SHA="778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb"
HISTORICAL_ENGINE_SHA="db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375"
BASE_PACKAGED_ENGINE_SHA="6e82e18868345ce919714364466e6473b15ed00abb68f6d09eebd7f5ef33f3f8"
BASE_RECORDER_SHA="19f017612d9447503ef8957d2ad82266631150c98454359789bdf6f547f4b3df"
LIBKODI="lib/arm64-v8a/libkodi.so"
RECORDER="lib/arm64-v8a/libinfinitycrash.so"
FIELD=b"native_engine_sha256="+HISTORICAL_ENGINE_SHA.encode("ascii")+b"\n"


def sha(value:bytes)->str:
    return hashlib.sha256(value).hexdigest()


def elf_sections(raw:bytes)->dict[str,tuple[int,int]]:
    """Bounded AArch64 ELF64 little-endian section parser; no external tooling."""
    if len(raw)<64 or raw[:4]!=b"\x7fELF" or raw[4]!=2 or raw[5]!=1:
        raise ValueError("Not an ELF64 little-endian engine")
    if struct.unpack_from("<H",raw,0x12)[0]!=183:
        raise ValueError("Not the approved ARM64 engine architecture")
    start=struct.unpack_from("<Q",raw,0x28)[0]
    each=struct.unpack_from("<H",raw,0x3a)[0]
    count=struct.unpack_from("<H",raw,0x3c)[0]
    strings=struct.unpack_from("<H",raw,0x3e)[0]
    if not (0<count<2048 and each==64 and strings<count and start+count*each<=len(raw)):
        raise ValueError("ELF section table bounds invalid")
    sections=[]
    for i in range(count):
        base=start+i*each
        name,stype,flags,address,offset,size,link,info,align,ent=struct.unpack_from("<IIQQQQIIQQ",raw,base)
        if offset+size>len(raw):raise ValueError("ELF segment out of bounds")
        sections.append((name,stype,offset,size))
    _,_,name_off,name_size=sections[strings]
    names=raw[name_off:name_off+name_size]
    result={}
    for ix,(name,stype,offset,size) in enumerate(sections):
        if name>=len(names):raise ValueError("ELF section name index invalid")
        end=names.find(b"\x00",name)
        if end<0:raise ValueError("Unterminated ELF section name")
        section=names[name:end].decode("ascii","replace")
        result[section]=(offset,size)
    if ".text" not in result:raise ValueError("ELF executable .text missing")
    return result


def receipt(engine:bytes,original_recorder:bytes)->dict:
    _=elf_sections(original_recorder)
    sections=elf_sections(engine)
    offset,size=sections[".text"]
    if size<1000:raise ValueError("Unexpected tiny native engine .text")
    return {
        "final_native_engine_sha256":sha(engine),
        "final_native_text_sha256":sha(engine[offset:offset+size]),
        "final_native_text_offset":offset,
        "final_native_text_size":size,
        "elf_gnu_build_id_present":".note.gnu.build-id" in sections,
        "crash_symbol_mapping_requires_runtime_maps":True,
        "crash_root_cause_proven":False,
        "root_cause_fix_implemented":False
    }


def patch(engine:bytes,recorder:bytes)->bytes:
    engine_hash=sha(engine)
    if engine_hash==HISTORICAL_ENGINE_SHA:
        raise ValueError("Refusing historical native binary identity")
    _=receipt(engine,recorder)
    if sha(recorder)!=BASE_RECORDER_SHA:
        raise ValueError("Unknown collector preimage: protect signal handling")
    if recorder.count(FIELD)!=1:
        raise ValueError("Historical collector SHA not found exactly once")
    field=b"native_engine_sha256="+engine_hash.encode("ascii")+b"\n"
    if len(field)!=len(FIELD):raise ValueError("Offset-changing native patch rejected")
    new=recorder.replace(FIELD,field,1)
    if len(new)!=len(recorder) or sha(new)==sha(recorder):
        raise ValueError("Native collector remained unchanged")
    # This is the only allowed binary delta. No instruction/ABI/export changes.
    ix=recorder.index(FIELD)
    if new[:ix]!=recorder[:ix] or new[ix+len(FIELD):]!=recorder[ix+len(FIELD):]:
        raise ValueError("Patch crossed the fixed rodata identity field")
    return new


def staged_inventory(signed_original:Path,final_engine:Path|None=None)->dict:
    data=Path(signed_original).read_bytes()
    if sha(data)!=BASE_APK_SHA:
        raise ValueError("Wrong original protected 2103390")
    with ZipFile(signed_original) as apk:
        names=apk.namelist()
        if len(names)!=7430 or len(set(names))!=7430:
            raise ValueError("Unexpected immutable original APK inventory")
        original_engine=apk.read(LIBKODI)
        collector=apk.read(RECORDER)
        if sha(original_engine)!=BASE_PACKAGED_ENGINE_SHA:
            raise ValueError("Original native producer differs")
        if sha(collector)!=BASE_RECORDER_SHA:
            raise ValueError("Original recorder differs")
    native=Path(final_engine).read_bytes() if final_engine else original_engine
    repaired=patch(native,collector)
    report=receipt(native,collector)
    report.update({
        "protected_signed_base_sha256":BASE_APK_SHA,
        "original_recorder_sha256":sha(collector),
        "patched_recorder_sha256":sha(repaired),
        "original_recorder_bytes_unchanged_except_one_sha_field":True,
        "original_recorder_size":len(collector),
        "patched_recorder_size":len(repaired),
        "collector_field_after":sha(native),
        "historical_field_invalidated":True,
        "source_only":True,
        "actual_apk_built":False,
        "fold_verified":False,
        "changed_apk_members_if_staged":[RECORDER],
        "original_native_engine_modified":False
    })
    return report


def stage(signed_original:Path,dest:Path,final_engine:Path|None=None)->dict:
    signed_original=Path(signed_original).resolve()
    dest=Path(dest).resolve()
    if dest==signed_original.parent or signed_original.is_relative_to(dest):
        raise ValueError("Do not write over immutable signed 2103390")
    report=staged_inventory(signed_original,final_engine)
    with ZipFile(signed_original) as apk:
        collector=apk.read(RECORDER)
        native=Path(final_engine).read_bytes() if final_engine else apk.read(LIBKODI)
    after=patch(native,collector)
    output=dest/RECORDER
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(after)
    return report


if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("original_2103390",type=Path)
    p.add_argument("--final-engine",type=Path,default=None)
    p.add_argument("--stage-to",type=Path,default=None)
    args=p.parse_args()
    print(json.dumps(stage(args.original_2103390,args.stage_to,args.final_engine)
                     if args.stage_to else staged_inventory(args.original_2103390,args.final_engine),
                     indent=2))
