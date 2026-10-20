#!/usr/bin/env python3
"""Integration adapters for the reviewed 2103392 source set.

These adapters do not submit workflows, rebuild an engine, sign or install an
APK. They connect staged identities to real compiler input ledgers and reject
mixed components. Original source receipts and APKs are never overwritten.
A successful preparation is NOT Android or physical-Fold qualification.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
from zipfile import ZipFile
import release as r

ORIGINAL_NATIVE_COMMIT='7bd9b1085d598789e9e803b4b76ee1429e1df7e3'
ORIGINAL_CLASSIFIER='8ceb3b60518dc2ab48c0aed480b78e81585ef7c0f66a47b214975e0fac8d6c02'
EXPECTED_FILES=9404
TARGET_CLASS='com/projectinfinity/kodi/InfinityInstalledCheckpointInstaller.smali'
NATIVE_PATHS={r.CONTRACT_PATH,r.COORDINATOR_PATH}
FINAL_NATIVE={r.CONTRACT_PATH:'116d0677d8530dc84afbf9646fcbff9ca58ecfee9efc16542eaecfb1039bc8f6',
              r.COORDINATOR_PATH:'a17e43f22ac1716ad14fb8e7635888d2e10d3d0ee11a35b7798e3b38c62c122e'}
FINAL_JAVA='7cef1dfb1c1fce521e4c27788f293ea85f494ec6ff9edb4014cce72b7de88194'
SIGNATURE=re.compile(r'META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))',re.I)
DEX=re.compile(r'classes(?:[2-9]|[1-9][0-9]+)?\.dex')

class IntegrationError(ValueError): pass

def require(value, reason):
    if not value: raise IntegrationError(reason)

def read_json(path: Path): return json.loads(path.read_text())
def json_bytes(value): return (json.dumps(value,indent=2,sort_keys=True)+'\n').encode()

def safe_path(root: Path, name: str) -> Path:
    part=PurePosixPath(name)
    require(name and not part.is_absolute() and '\\' not in name and
            all(p not in ('','..','.') for p in name.split('/')), 'Unsafe source member')
    path=root/part
    require(path.absolute()==path.resolve(), 'Symlinked input/output is not allowed')
    require(path.resolve().is_relative_to(root.resolve()), 'Source member escapes root')
    return path

def snapshot(root: Path) -> dict[str,str]:
    require(root.is_dir() and root.absolute()==root.resolve(),'Missing or symlinked source tree')
    result={}
    for path in root.rglob('*'):
        rel=path.relative_to(root)
        if '.git' in rel.parts: continue
        require(not path.is_symlink(),'Symlinked source member')
        if path.is_file(): result[rel.as_posix()]=r.sha(path.read_bytes())
    return result

def verified_stage(apk: Path, stage: Path) -> tuple[dict,dict[str,bytes]]:
    """Regenerate all reviewed bytes, never trust a caller-supplied green flag."""
    original=r.read_original(apk); final=r.components(original)
    expected_native={r.CONTRACT_PATH:r.contracts((r.NATIVE_BASE/r.CONTRACT_PATH).read_bytes(),final),
                     r.COORDINATOR_PATH:r.coordinator(r.original_coordinator())}
    expected_java=r.java_router((r.JAVA_BASE/r.JAVA_PATH).read_bytes(),final)
    require({n:r.sha(b) for n,b in expected_native.items()}==FINAL_NATIVE,'Reviewed native output drift')
    require(r.sha(expected_java)==FINAL_JAVA,'Reviewed Java output drift')
    expected={**{'addons/'+n:b for n,b in final.items()},
              **{'native/'+n:b for n,b in expected_native.items()},
              'java/'+r.JAVA_PATH:expected_java}
    actual=snapshot(stage)
    require(set(actual)==set(expected)|{'COHERENT92-SOURCE.json'},'Missing or extra staged members')
    for name,body in expected.items():
        require(safe_path(stage,name).read_bytes()==body,'Staged bytes do not match reviewed source: '+name)
    receipt=read_json(stage/'COHERENT92-SOURCE.json')
    require(receipt['source_apk_sha256']==r.APK_SHA and receipt['component_versions']=={a:v for a,_,v in r.PACKAGES},'Stage identity mismatch')
    for key in ('physical_fold_verified','final_lock','android_native_library_compiled','original_apk_modified'):
        require(receipt.get(key) is False,'Source preparation cannot claim '+key)
    return receipt, expected

def prepare(apk: Path, destination: Path) -> dict:
    require(not destination.exists(),'Refusing to overwrite integration directory')
    require(not apk.resolve().is_relative_to(destination.resolve()),'Output would contain original APK')
    destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.infinity-integration-',dir=destination.parent) as temporary:
        stage=Path(temporary)/'source'
        r.stage(apk,stage)
        receipt,expected=verified_stage(apk,stage)
        plan=dict(schema=1,state='SOURCE_INPUTS_PREPARED_NOT_COMPILED_OR_INSTALLABLE',
          source_apk_sha256=r.APK_SHA,original_native_source_commit=ORIGINAL_NATIVE_COMMIT,
          native_base_reconstruction='Use immutable original 2103391 producer, then bind reviewed delta. Do not reconstruct locked source from modified overlays.',
          required_native_source_count=EXPECTED_FILES,
          native_paths=sorted(NATIVE_PATHS),java_source=r.JAVA_PATH,
          permitted_java_runtime_class=TARGET_CLASS,
          required_addon_member_changes=sorted('assets/addons/'+n for n in r.CHANGED_ADDON_MEMBERS),
          required_binary_changes=['AndroidManifest.xml','lib/arm64-v8a/libkodi.so','lib/arm64-v8a/libinfinitycrash.so'],
          dex_change_policy='Only the DEX shard owning the exact reviewed Java class; every other class instruction and DEX shard unchanged.',
          original_apk_modified=False,android_native_library_compiled=False,android_dex_compiled=False,
          signed_apk_created=False,installable_zip_set_created=False,physical_fold_verified=False,final_lock=False,
          full_seven_group_scope_retained=True,component_versions=receipt['component_versions'],
          source_hashes={n:r.sha(b) for n,b in sorted(expected.items())})
        (Path(temporary)/'INTEGRATION-INPUTS.json').write_bytes(json_bytes(plan))
        os.rename(temporary,destination)
    return plan

def native_plan(actual: dict[str,str], locked: dict[str,str], delta: dict,
                compiler_maps: list[dict], source_commit: str) -> tuple[dict,dict,list[dict],dict]:
    """Pure planning step; tests can exercise rejection without a full rebuild."""
    require(bool(re.fullmatch('[0-9a-f]{40}',source_commit)),'Full integration source commit required')
    require(len(locked)==EXPECTED_FILES and len(actual)==EXPECTED_FILES,'Complete 9404-source inventory required')
    expected=dict(locked,**delta['after'])
    require(actual==expected,'Prepared native tree differs from recorded original source')
    require(delta.get('group7_extra_native_delta') and len(delta['group7_extra_native_delta'])==8,'Original seven-group native integration missing')
    require(actual.get(r.CONTRACT_PATH)==ORIGINAL_CLASSIFIER,'Wrong original native classifier lineage')
    require(actual.get(r.COORDINATOR_PATH)==r.FINAL_COORDINATOR_PREIMAGE,'Wrong Essential-First coordinator lineage')
    require(len(compiler_maps)>=2,'Both compiler and final preservation maps required')
    updated_maps=[]
    for original in compiler_maps:
        require(isinstance(original.get('after'),dict) and len(original['after'])>=4500,'Incomplete compiler source map')
        require(all(actual.get(n)==h for n,h in original['after'].items()),'Compiler input map is not the recorded source tree')
        require(NATIVE_PATHS.issubset(original['after']),'Compiler map omits changed native source')
        updated=copy.deepcopy(original)
        updated['after'].update(FINAL_NATIVE)
        updated['changed']=sorted(set(updated.get('changed',()))|NATIVE_PATHS)
        updated_maps.append(updated)
    after=dict(actual,**FINAL_NATIVE)
    change=copy.deepcopy(delta)
    change['after'].update(FINAL_NATIVE)
    change['changed']=sorted(set(change.get('changed',()))|NATIVE_PATHS)
    change['source_commit']=source_commit
    change['coherent92_native_delta']=sorted(NATIVE_PATHS)
    report=dict(source_commit=source_commit,base_source_commit=ORIGINAL_NATIVE_COMMIT,
        original_source_count=len(actual),final_source_count=len(after),
        before={n:actual[n] for n in sorted(NATIVE_PATHS)},after=FINAL_NATIVE,
        protected_source_count=len(actual)-len(NATIVE_PATHS),
        all_other_sources_byte_identical=True,old_group7_native_paths=delta['group7_extra_native_delta'],
        native_compiled=False,physical_fold_verified=False,final_lock=False)
    return after,change,updated_maps,report

def bind_native(apk: Path, stage: Path, native_root: Path, checkpoint: Path,
                compiler_manifest: Path, source_commit: str) -> dict:
    """Bind exactly two files AFTER the original 2103391 reconstruction.

    All checks precede mutation. Save rollback input bytes separately. No compiler
    is invoked, and none of the original receipt files is erased or waived.
    """
    verified_stage(apk,stage)
    delta_path=checkpoint/'FOUR-REPAIR-INPUT-DELTA.json'
    locked_path=checkpoint/'LOCKED-2103384-SOURCE-MAP.json'
    final_path=checkpoint/'FINAL-SHUTDOWN-SOURCE-PRESERVATION.json'
    paths=[delta_path,compiler_manifest,final_path]
    require(len({p.resolve() for p in paths})==3,'Compiler receipt paths must be distinct')
    require(all(p.is_file() and p.absolute()==p.resolve() for p in paths+[locked_path]),'Missing/symlinked native receipts')
    original=snapshot(native_root)
    after,delta,maps,report=native_plan(original,read_json(locked_path),read_json(delta_path),
                                      [read_json(compiler_manifest),read_json(final_path)],source_commit)
    rollback=checkpoint/'COHERENT92-ORIGINAL-INPUTS'
    require(not rollback.exists(),'Native binding already attempted; original rollback must remain intact')
    replacements={safe_path(native_root,n):safe_path(stage,'native/'+n).read_bytes() for n in NATIVE_PATHS}
    replacements.update({delta_path:json_bytes(delta),compiler_manifest:json_bytes(maps[0]),final_path:json_bytes(maps[1])})
    backup={p:p.read_bytes() for p in replacements}
    rollback.mkdir()
    for index,(path,body) in enumerate(backup.items()):
        (rollback/(str(index)+'.original')).write_bytes(body)
    (rollback/'INDEX.json').write_bytes(json_bytes({str(i):dict(path=str(p),sha256=r.sha(b)) for i,(p,b) in enumerate(backup.items())}))
    try:
        for path,body in replacements.items(): path.write_bytes(body)
        require(snapshot(native_root)==after,'Unexpected source change during native binding')
        (checkpoint/'COHERENT92-NATIVE-SOURCE-MAP.json').write_bytes(json_bytes(after))
        (checkpoint/'COHERENT92-NATIVE-BINDING.json').write_bytes(json_bytes(report))
    except BaseException:
        for path,body in backup.items(): path.write_bytes(body)
        raise
    return report

def verify_dex_class_maps(original: dict[str,str], candidate: dict[str,str]) -> dict:
    require(set(original)==set(candidate),'Added/removed Java classes are forbidden')
    changed={n for n in original if original[n]!=candidate[n]}
    require(changed=={TARGET_CLASS},'Java change exceeds exact startup-router class')
    return dict(changed_class=TARGET_CLASS,protected_classes=len(original)-1,
                protected_class_instructions_identical=True,android_process_tested=False)

def verify_addon_delta(apk: Path, candidate: Path, stage: Path) -> dict:
    """Candidate audit only; separate DEX/ELF/signature proofs remain mandatory."""
    _,expected=verified_stage(apk,stage)
    addon_targets={'assets/addons/'+n for n in r.CHANGED_ADDON_MEMBERS}
    with ZipFile(apk) as old,ZipFile(candidate) as new:
        before=old.namelist();after=new.namelist()
        require(len(before)==len(set(before)) and len(after)==len(set(after)),'Duplicate APK members')
        require(new.testzip() is None,'Candidate ZIP integrity failed')
        names={n for n in before if not SIGNATURE.fullmatch(n)}
        require(names=={n for n in after if not SIGNATURE.fullmatch(n)},'APK member added or removed')
        changed={n for n in names if old.read(n)!=new.read(n)}
        dex_changes={n for n in changed if DEX.fullmatch(n)}
        require(len(dex_changes)==1,'Exactly one verified startup-router DEX shard required')
        binaries={'AndroidManifest.xml','lib/arm64-v8a/libkodi.so','lib/arm64-v8a/libinfinitycrash.so'}
        require(changed==addon_targets|binaries|dex_changes,'Unexpected/missing integration APK delta')
        for n in names:
            if n.startswith('assets/addons/'):
                relative=n[len('assets/'):]
                if relative in expected:
                    require(new.read(n)==expected[relative],'Candidate component differs from staged source: '+n)
    return dict(changed_members=sorted(changed),dex_shard=next(iter(dex_changes)),
                apk_member_scope_verified=True,signature_verified=False,
                native_compile_proven=False,dex_instruction_preservation_proven=False,
                android_process_tested=False,physical_fold_verified=False,final_lock=False)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('mode',choices=['prepare','bind-native','audit-apk'])
    p.add_argument('--apk',type=Path,required=True);p.add_argument('--out',type=Path)
    p.add_argument('--stage',type=Path);p.add_argument('--native-root',type=Path)
    p.add_argument('--checkpoint',type=Path);p.add_argument('--compiler-manifest',type=Path)
    p.add_argument('--source-commit');p.add_argument('--candidate',type=Path)
    a=p.parse_args()
    if a.mode=='prepare':
        require(a.out is not None,'--out is required');result=prepare(a.apk,a.out)
    elif a.mode=='bind-native':
        require(all(x is not None for x in (a.stage,a.native_root,a.checkpoint,a.compiler_manifest,a.source_commit)),'Native binding arguments incomplete')
        result=bind_native(a.apk,a.stage,a.native_root,a.checkpoint,a.compiler_manifest,a.source_commit)
    else:
        require(a.stage is not None and a.candidate is not None,'--stage and --candidate required')
        result=verify_addon_delta(a.apk,a.candidate,a.stage)
    print(json.dumps(result,indent=2,sort_keys=True))
