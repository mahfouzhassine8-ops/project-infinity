"""Build only Infinity Search's existing helper family into its own DEX.

The original Search95 routing method and original keyboard/editor remain exact.
Search101 retains its existing binary name, so no shared call site is patched.
Every other primary class and the complete original string pool are compared
byte-for-byte after relocating this explicitly owned helper family.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from zipfile import ZipFile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PREFIX='com/projectinfinity/kodi/InfinitySearch101'


def helper(name):
    return name==PREFIX+'.smali' or name.startswith(PREFIX+'$') and name.endswith('.smali')


def run(args):
    result=subprocess.run([str(a) for a in args],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if result.returncode:raise RuntimeError(result.stdout)
    return result.stdout


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def raw(path):return {p.relative_to(path).as_posix():p.read_bytes() for p in path.rglob('*.smali')}


def strings(path):
    import struct
    data=Path(path).read_bytes();count,offset=struct.unpack_from('<II',data,56);values=[]
    for i in range(count):
        at=struct.unpack_from('<I',data,offset+4*i)[0]
        while data[at]&128:at+=1
        at+=1;values.append(data[at:data.index(b'\0',at)])
    return values


def prepare(apk,primary,jars,android,d8,out):
    apk,primary,jars,android,d8,out=map(Path,(apk,primary,jars,android,d8,out))
    pins=json.loads((ROOT/'repairs/universal-persistence-2103401/RECEIPT-TOOL-PINS.json').read_text())
    if {p.name:digest(p) for p in jars.glob('*.jar')}!=pins:raise RuntimeError('Unverified DEX tools')
    if out.exists():raise RuntimeError('Search DEX output already exists')
    out.mkdir(parents=True);cp=os.pathsep.join(str(p.resolve()) for p in sorted(jars.glob('*.jar')))
    original=out/'before';run(['java','-cp',cp,'org.jf.baksmali.Main','disassemble','--sequential-labels',primary,'-o',original])
    before=raw(original);moved={n for n in before if helper(n)}
    if len(moved)<2:raise RuntimeError('Existing Search101 family missing')
    secondary_names=[];outside=set(before)-moved
    with ZipFile(apk) as archive:
        for name in archive.namelist():
            if re.fullmatch(r'classes(?:[2-9]|[1-9][0-9]+)\.dex',name):
                secondary_names.append(name);target=out/name;target.write_bytes(archive.read(name))
                decoded=out/(name+'-original');run(['java','-cp',cp,'org.jf.baksmali.Main','disassemble','--sequential-labels',target,'-o',decoded])
                classes=set(raw(decoded))
                if any(helper(n) for n in classes) or outside&classes:raise RuntimeError('Original DEX class collision')
                outside.update(classes);target.unlink()
    next_index=max([1]+[int(n[7:-4]) for n in secondary_names])+1
    name='classes%d.dex'%next_index
    sources=out/'java';sources.mkdir();classes=out/'classes';classes.mkdir()
    spec=importlib.util.spec_from_file_location('search_compile_stubs',ROOT/'repairs/fold-critical-2103395/java95.py')
    # The stub is declarative and comes from the reviewed compile source. Do
    # not execute its module, which imports unrelated packaging machinery.
    import ast
    module=ast.parse(spec.origin and Path(spec.origin).read_text())
    stub=next(ast.literal_eval(n.value) for n in module.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='STUB' for t in n.targets))
    (sources/'InfinityAndroidKeyboard.java').write_text(stub)
    shutil.copyfile(ROOT/'repairs/fold-critical-2103395/InfinitySearch95.java',sources/'InfinitySearch95.java')
    shutil.copyfile(HERE/'InfinitySearch101.java',sources/'InfinitySearch101.java')
    run(['javac','--release','8','-g:none','-Xlint:all,-options','-Werror','-cp',android,'-d',classes,*sources.glob('*.java')])
    produced=[p for p in classes.rglob('*.class') if p.name.startswith('InfinitySearch101')]
    if not produced:raise RuntimeError('Search helper compilation empty')
    dex=out/'helper';dex.mkdir()
    run([d8,'--release','--min-api','21','--lib',android,'--output',dex,*produced])
    decoded=out/'helper-smali';run(['java','-cp',cp,'org.jf.baksmali.Main','disassemble','--sequential-labels',dex/'classes.dex','-o',decoded])
    added=set(raw(decoded))
    if not added or not all(helper(n) for n in added) or added&outside:raise RuntimeError('Unapproved helper class or collision')
    adapter=out/'adapter';adapter.mkdir()
    run(['javac','--release','8','-g:none','-cp',cp,'-d',adapter,HERE/'PreserveSearchPrimary.java'])
    final=out/'classes.dex'
    log=run(['java','-cp',str(adapter)+os.pathsep+cp,'org.jf.dexlib2.writer.pool.PreserveSearchPrimary',primary,final,'21'])
    (out/'SEARCH-PRIMARY-PRESERVATION.log').write_text(log)
    checked=out/'after';run(['java','-cp',cp,'org.jf.baksmali.Main','disassemble','--sequential-labels',final,'-o',checked])
    after=raw(checked)
    if set(after)!=set(before)-moved or any(after[n]!=before[n] for n in after):
        raise RuntimeError('Protected DEX encoding or class definition changed')
    if strings(primary)!=strings(final):raise RuntimeError('Original string inventory or indices changed')
    shutil.copyfile(dex/'classes.dex',out/name)
    report=dict(passed=True,source_baseline_apk_sha256=digest(apk),input_primary_sha256=digest(primary),final_primary_sha256=digest(final),
        secondary_name=name,secondary_sha256=digest(out/name),relocated_original_classes=sorted(moved),
        helper_classes=sorted(added),protected_class_count=len(after),protected_disassembly_byte_identical=True,
        original_string_pool_identical=True,search95_route_unchanged=True,keyboard_editor_unchanged=True,
        cobra_definitions_changed=[],physical_fold_verified=False,actual_android_verified=False,
        java_source_sha256=digest(HERE/'InfinitySearch101.java'),adapter_source_sha256=digest(HERE/'PreserveSearchPrimary.java'))
    (out/'SEARCH-DEX-PRESERVATION.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    return report


def verify_package(apk,primary,out,jars):
    """Re-decode actual package bytes, independently of saved PASS flags."""
    import tempfile
    apk,primary,out,jars=map(Path,(apk,primary,out,jars))
    pins=json.loads((ROOT/'repairs/universal-persistence-2103401/RECEIPT-TOOL-PINS.json').read_text())
    if {p.name:digest(p) for p in jars.glob('*.jar')}!=pins:raise RuntimeError('Unverified DEX tools')
    report=json.loads((out/'SEARCH-DEX-PRESERVATION.json').read_text());name=report['secondary_name']
    if not re.fullmatch(r'classes(?:[2-9]|[1-9][0-9]+)\.dex',name):raise RuntimeError('Invalid Search secondary name')
    if report['source_baseline_apk_sha256']!=digest(apk) or report['input_primary_sha256']!=digest(primary):raise RuntimeError('Search DEX input lineage changed')
    if report['final_primary_sha256']!=digest(out/'classes.dex') or report['secondary_sha256']!=digest(out/name):raise RuntimeError('Search DEX compiler outputs changed')
    if report['java_source_sha256']!=digest(HERE/'InfinitySearch101.java') or report['adapter_source_sha256']!=digest(HERE/'PreserveSearchPrimary.java'):raise RuntimeError('Search source changed after compilation')
    cp=os.pathsep.join(str(p.resolve()) for p in sorted(jars.glob('*.jar')))
    with tempfile.TemporaryDirectory(prefix='infinity-search-package-') as temporary:
        work=Path(temporary)
        def decode(source,label):
            dest=work/label;run(['java','-cp',cp,'org.jf.baksmali.Main','disassemble','--sequential-labels',source,'-o',dest]);return raw(dest)
        before=decode(primary,'before');after=decode(out/'classes.dex','after');added=decode(out/name,'helper')
        removed={n for n in before if helper(n)}
        if len(removed)<2 or set(after)!=set(before)-removed or any(before[n]!=after[n] for n in after):raise RuntimeError('Protected package DEX definition changed')
        if strings(primary)!=strings(out/'classes.dex'):raise RuntimeError('Protected string indices changed')
        if not added or not all(helper(n) for n in added):raise RuntimeError('Unexpected packaged helper class')
        all_names=set(after)|set(added)
        with ZipFile(apk) as archive:
            if name in archive.namelist():raise RuntimeError('Search secondary overwrites original APK member')
            for member in archive.namelist():
                if re.fullmatch(r'classes(?:[2-9]|[1-9][0-9]+)\.dex',member):
                    source=work/member;source.write_bytes(archive.read(member));other=decode(source,member+'-original')
                    if all_names&set(other):raise RuntimeError('Cross-DEX package class collision')
                    all_names.update(other)
        if sorted(removed)!=report['relocated_original_classes'] or sorted(added)!=report['helper_classes']:raise RuntimeError('Search class receipt mismatch')
    return dict(passed=True,protected_class_count=len(after),primary_sha256=digest(out/'classes.dex'),secondary_name=name,secondary_sha256=digest(out/name),protected_disassembly_byte_identical=True,original_string_pool_identical=True,cobra_definitions_changed=[])


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('apk','primary','jars','android','d8','out'):p.add_argument('--'+key,type=Path,required=True)
    print(json.dumps(prepare(**vars(p.parse_args())),indent=2))
