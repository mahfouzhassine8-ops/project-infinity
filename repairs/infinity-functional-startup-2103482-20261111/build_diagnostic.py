#!/usr/bin/env python3
"""Exact82 native instrumentation build. No key access or APK publication."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=ROOT/'functional-startup-native'
NATIVE=ROOT/'kodi'
BASE='93d025b65cf6d5b7e3912ce704d0bc98af4879fd'
BRANCH='work/infinity-2103482-functional-startup-20261111'
HEADER='xbmc/interfaces/generic/InfinityStartupTrace.h'
QA_PREFIX='#define INFINITY_STARTUP_TRACE_QA 1 // This native artifact is internal diagnostic QA only.\n'


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def save(name,data):
    OUT.mkdir(exist_ok=True);(OUT/name).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    sys.path.insert(0,str(path.parent))
    try:spec.loader.exec_module(module)
    finally:sys.path.pop(0)
    return module


def scope():
    assert os.environ['GITHUB_REPOSITORY']=='mahfouzhassine8-ops/project-infinity'
    assert os.environ['GITHUB_REF']=='refs/heads/'+BRANCH
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==os.environ['GITHUB_SHA']
    changed=subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],cwd=ROOT,text=True).splitlines()
    permitted={'.github/workflows/infinity-functional-startup-evidence.yml','.github/workflows/infinity-functional-startup-native.yml','.github/workflows/infinity-saved-navigation-android.yml'}
    assert all(p in permitted or p.startswith('repairs/infinity-functional-startup-2103482-20261111/') for p in changed),changed
    assert json.loads((HERE/'HOST-TRACE-RESULTS.json').read_text())['all_selected_assertions_passed']
    # Historical restoration/compiler/signing inputs are immutable; the new
    # branch guard replaces their old task-specific authorization, not hashes.
    old=ROOT/'repairs/infinity-close-startup-2103480-20261110/build_candidate/native_build.py'
    assert old.read_bytes()==subprocess.check_output(['git','show',BASE+':'+str(old.relative_to(ROOT))],cwd=ROOT)


def previous():
    old=load(ROOT/'repairs/infinity-close-startup-2103480-20261110/build_candidate/native_build.py','preserved82_builder')
    old.OUT=OUT;old.require_scope=scope
    return old


def prepare():
    scope();old=previous();old.prepare()
    before=json.loads((OUT/'NATIVE-SOURCE-MAP.json').read_text())
    assert len(before)==9411
    assert before['xbmc/platform/android/activity/InfinityAndroidCheckpoint.cpp']=='2273becee60a25e81b2c5844f052fe32eaa8d03335311672cd67b66bc3738648'
    bindings=json.loads((HERE/'native/SOURCE-BINDINGS.json').read_text())
    assert len(bindings)==4
    expected=dict(before)
    for name,pin in bindings.items():
        assert before[name]==pin['before'] and sha(NATIVE/name)==pin['before']
        candidate=HERE/'native/overlay'/name;assert sha(candidate)==pin['after']
        shutil.copyfile(candidate,NATIVE/name);expected[name]=pin['after']
    assert HEADER not in before
    (NATIVE/HEADER).write_text(QA_PREFIX+(HERE/'native/overlay'/HEADER).read_text())
    expected[HEADER]=sha(NATIVE/HEADER)
    hasher=load(ROOT/'repairs/infinity-native-touch-2103451-20261105/compile_only.py','retained_full_hasher')
    assert hasher.hashes(NATIVE)==expected
    save('NATIVE-SOURCE-MAP.json',expected)
    save('DIAGNOSTIC-SOURCE-PRESERVATION.json',dict(status='PASS_EXACT82_PLUS_FOUR_DIAGNOSTIC_CALLSITE_FILES_AND_ONE_QA_HEADER',
        source_commit=os.environ['GITHUB_SHA'],baseline82_engine='503f91109332ef050a604cf15ad604b16e156b55459bafd47c453c3f72de0437',
        changed=bindings,new_header={HEADER:expected[HEADER]},unchanged82_native_sources=9407,
        diagnostic_build_flag='INFINITY_STARTUP_TRACE_QA=1',runtime_gate='exact com.projectinfinity.kodi:kodi process',
        correction_implemented='CPython3.11.7 recoverable-NULL cleanup only; Fold attribution unresolved',signing=False,apk_built=False,Cobra='UNCHANGED'))


def dependencies():
    scope();previous().dependencies()


def compile_native():
    scope();old=previous()
    expected=json.loads((OUT/'NATIVE-SOURCE-MAP.json').read_text());assert len(expected)==9412
    compiler=old.load(ROOT/'repairs/universal-persistence-2103401/build.py','preserved_arm64_compiler')
    compiler.OUT=OUT;checker=compiler.checked_sources
    def checked(root,pins,allow_generated=False):
        additions=checker(root,pins,allow_generated=True)
        if not allow_generated:
            assert Path(root)==NATIVE and pins==expected
            assert all(p.startswith('tools/depends/') for p in additions),additions
        return additions
    compiler.checked_sources=checked
    proof=compiler.compile_engine()
    assert proof['complete_native_engine_compiled'] and proof['reviewed_file_count']==9412
    lib=OUT/'libkodi.so';assert sha(lib)==proof['native_sha256']
    data=lib.read_bytes();assert b'InfinityStartupTrace stage=' in data and b'interpreter.failed' in data
    readelf=Path(os.environ['ANDROID_HOME'])/'ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readelf'
    def abi(p):
        header=subprocess.check_output([str(readelf),'-h',str(p)],text=True)
        assert all(v in header for v in ('ELF64','AArch64','DYN'))
        symbols=subprocess.check_output([str(readelf),'--dyn-syms','--wide',str(p)],text=True)
        dynamic=subprocess.check_output([str(readelf),'-d',str(p)],text=True)
        exported=set()
        for line in symbols.splitlines():
            fields=line.split()
            if len(fields)>=8 and fields[4]=='GLOBAL' and fields[5] in ('DEFAULT','PROTECTED') and fields[6]!='UND':exported.add(fields[7])
        import re
        return exported,set(re.findall(r'Shared library: \[([^\]]+)\]',dynamic))
    original=abi(OUT/'baseline80-libkodi.so');candidate=abi(lib);assert original==candidate
    save('ARM64-DIAGNOSTIC-BUILD.json',dict(status='PASS_FULL_ARM64_LINK_AND_BASELINE_ABI',
        native_sha256=sha(lib),source_commit=os.environ['GITHUB_SHA'],diagnostic_only=True,
        original_exports_preserved=len(candidate[0]),dependencies=sorted(candidate[1]),
        production_cause_proven=False,Android_execution='NOT_RUN',apk_built=False,signed=False))


if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ('prepare','dependencies','compile')
    {'prepare':prepare,'dependencies':dependencies,'compile':compile_native}[sys.argv[1]]()
