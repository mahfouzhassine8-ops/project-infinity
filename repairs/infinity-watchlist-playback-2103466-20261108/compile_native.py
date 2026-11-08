"""Existing signed466 restoration plus six scoped Watchlist observation files.

Build tooling only: exact source admission, real ARM64 objects/full engine link,
unchanged strong ABI. No signing, APK assembly, device or shutdown tests.
"""
import argparse
import builtins
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / 'watchlist-native-evidence'
BRANCH = 'refs/heads/work/infinity-watchlist-phase-b-20261108'
BASE = '5ee1c7ae0bbe295c311aa34c02f6b62688ccb5a7'
BASE_MAP_SHA = 'f48df24caabdf36fee25d69d47b0a2ad3c98df3936949c8dcd6d07a92e2f0412'
BASE_NATIVE = 'ee3be7c7a95b86f8357539001fcd50bedbd80217b02f130d649f7f57e6075794'
NAMES = {'xbmc/guilib/InfinitySavedNavigation.h', 'xbmc/guilib/InfinitySavedNavigationState.h',
         'xbmc/filesystem/PluginDirectory.cpp', 'xbmc/interfaces/json-rpc/PlayerOperations.cpp',
         'xbmc/interfaces/generic/ScriptInvocationManager.cpp', 'xbmc/interfaces/legacy/Player.cpp'}


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def save(name, value):
    OUT.mkdir(exist_ok=True)
    (OUT/name).write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')


def load(path, name):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s);s.loader.exec_module(m)
    return m


def scope():
    assert os.environ['GITHUB_REPOSITORY'] == 'mahfouzhassine8-ops/project-infinity'
    assert os.environ['GITHUB_REF'] == BRANCH
    assert subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip() == os.environ['GITHUB_SHA']
    assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=no'], text=True).strip()
    request = json.loads((HERE/'ARM64-REQUEST.json').read_text())
    assert request['native_sources'] == sorted(NAMES)
    assert request['APK'] is False and request['signing'] is False and request['application_tests'] is False
    assert request['base_APK'] == 2103466 and request['shutdown_tests'] is False
    pins = json.loads((HERE/'RUNTIME-SOURCE-PINS.json').read_text())
    assert set(pins['native']) == NAMES
    for name, digest in pins['native'].items():
        assert sha(HERE/'native'/name) == digest
    baseline = HERE/'contract-evidence/BASE466-NATIVE-SOURCE-MAP.json'
    assert sha(baseline) == BASE_MAP_SHA
    for name in ('compile_native.py','native/xbmc/interfaces/legacy/ModuleXbmc.cpp'):
        old = ROOT/'repairs/infinity-three-corrections-20261108'/name
        assert old.read_bytes() == subprocess.check_output(['git','show',BASE+':'+old.relative_to(ROOT).as_posix()])
    changed = subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],text=True).splitlines()
    assert all(n.startswith(HERE.relative_to(ROOT).as_posix()+'/') or n == '.github/workflows/infinity-combined-release.yml' for n in changed)
    return pins


def retained():
    r = load(ROOT/'repairs/infinity-three-corrections-20261108/compile_native.py', 'frozen_signed466_native_recipe')
    r.OUT = OUT
    r.scope = scope  # Replace branch admission with the stronger Watchlist-only admission above.
    return r


def prepare():
    pins = scope()
    r = retained();r.prepare()
    (OUT/'baseline-libkodi.so').unlink()  # Old464 comparison input already verified by the retained recipe.
    expected = json.loads((HERE/'contract-evidence/BASE466-NATIVE-SOURCE-MAP.json').read_text())
    assert json.loads((OUT/'NATIVE-SOURCE-MAP.json').read_text()) == expected
    rmap = load(ROOT/'repairs/infinity-native-touch-2103451-20261105/compile_only.py','frozen_source_hasher')
    assert rmap.hashes(ROOT/'kodi') == expected
    for name in sorted(NAMES):
        assert sha(ROOT/'kodi'/name) == expected[name]
        shutil.copyfile(HERE/'native'/name, ROOT/'kodi'/name)
    proposed = dict(expected, **pins['native'])
    assert rmap.hashes(ROOT/'kodi') == proposed
    save('BASE466-NATIVE-SOURCE-MAP.json', expected)
    save('NATIVE-SOURCE-MAP.json', proposed)
    save('SOURCE-PRESERVATION.json', dict(status='PASS_EXACT466_PLUS_SIX_SCOPED_OBSERVATION_SOURCES',
        source_commit=os.environ['GITHUB_SHA'], baseline_native_sha256=BASE_NATIVE,
        changed={n:dict(before=expected[n],after=proposed[n]) for n in sorted(NAMES)},
        unchanged_native_sources=len(expected)-len(NAMES), Search_getInfoLabel_source_unchanged=True,
        protected_baseline=2103466, APK=False, signing=False, application_tests=False, shutdown_tests=False))


def compile_objects():
    scope()
    r = load(ROOT/'repairs/infinity-native-touch-2103451-20261105/compile_only.py','frozen_selected_arm64_compiler')
    r.OUT = OUT
    code = inspect.getsource(r.compile_objects)
    original = "wanted={'xbmc/guilib/GUIBaseContainer.cpp','xbmc/input/InputManager.cpp'}"
    selected = sorted(n for n in NAMES if n.endswith('.cpp'))
    assert code.count(original) == 1 and code.count('len(selected)==2') == 1
    code = code.replace(original, 'wanted='+repr(set(selected))).replace('len(selected)==2', 'len(selected)==4')
    code = code.replace('Two real ARM64 Android translation units compiled','Four real ARM64 Android Watchlist translation units compiled')
    exec(builtins.compile(code,'<retained-four-selected-Watchlist-objects>','exec'),r.__dict__)
    r.compile_objects()
    rows = json.loads((OUT/'SELECTED-COMPILE-COMMANDS.json').read_text())
    assert len(rows) == 4
    for row in rows:
        args=row.get('arguments') or shlex.split(row['command'])
        obj=Path(args[args.index('-o')+1]);obj=obj if obj.is_absolute() else Path(row['directory'])/obj
        shutil.copyfile(obj, OUT/(Path(row['file']).name+'.o'))


def link():
    scope()
    sys.path.insert(0,str(ROOT/'repairs/universal-persistence-2103401'))
    r = load(ROOT/'repairs/universal-persistence-2103401/build.py','frozen_native_owning_target')
    r.OUT = OUT
    expected = json.loads((OUT/'NATIVE-SOURCE-MAP.json').read_text())
    objects = json.loads((OUT/'COMPILE-RESULT.json').read_text())
    assert set(r.checked_sources(ROOT/'kodi',expected,allow_generated=True)) == set(objects['generated_native_paths'])
    build=Path(os.environ['BUILD_DIR']);cache={}
    for line in (build/'CMakeCache.txt').read_text().splitlines():
        if '=' in line:
            key,val=line.split('=',1);cache[key]=val
    subprocess.run([cache['CMAKE_COMMAND:INTERNAL'],'--build',str(build),'--target','kodi','--parallel',str(os.cpu_count() or 1)],check=True)
    generated=r.checked_sources(ROOT/'kodi',expected,allow_generated=True)
    libraries=list(build.rglob('libkodi.so'));assert len(libraries)==1 and not list(ROOT.glob('*.apk'))
    shutil.copyfile(libraries[0],OUT/'libkodi.so')
    tool=Path(os.environ['ANDROID_HOME'])/'ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readelf'
    # The independently signed466 linked engine is the comparison baseline.
    native=ROOT/'watchlist-baseline-native/libkodi.so'
    assert sha(native)==BASE_NATIVE
    evidence={}
    for label,path in [('baseline',native),('candidate',OUT/'libkodi.so')]:
        header=subprocess.check_output([str(tool),'-h',str(path)],text=True)
        assert all(x in header for x in ('ELF64','AArch64','DYN'))
        symbols=subprocess.check_output([str(tool),'--dyn-syms','--wide',str(path)],text=True)
        dynamic=subprocess.check_output([str(tool),'-d',str(path)],text=True)
        exports=[]
        for line in symbols.splitlines():
            f=line.split()
            if len(f)>=8 and f[4]=='GLOBAL' and f[5] in ('DEFAULT','PROTECTED') and f[6]!='UND':
                exports.append((f[7],f[3],f[4],f[5]))
        evidence[label]=dict(exports=sorted(exports),needed=sorted(re.findall(r'Shared library: \[([^\]]+)\]',dynamic)))
        (OUT/(label+'-ELF-HEADER.txt')).write_text(header)
    assert evidence['baseline']==evidence['candidate'],'ORIGINAL_STRONG_NATIVE_ABI_OR_DEPENDENCIES_CHANGED'
    before=json.loads((OUT/'BASE466-NATIVE-SOURCE-MAP.json').read_text())
    assert {n for n in before if before[n]!=expected[n]}==NAMES
    save('ARM64-LINK-VERIFIED.json',dict(status='PASS_REAL_FOUR_ARM64_OBJECTS_FULL_NATIVE_LINK_UNCHANGED_ABI',
        source_commit=os.environ['GITHUB_SHA'],native_sha256=sha(OUT/'libkodi.so'),native_bytes=(OUT/'libkodi.so').stat().st_size,
        changed_native_sources=sorted(NAMES),unchanged_native_source_count=len(before)-len(NAMES),
        preserved_strong_exports=len(evidence['candidate']['exports']),needed=evidence['candidate']['needed'],
        generated_native_paths=generated,APK=False,signing=False,Android='NOT_RUN',physical_Fold='NOT_RUN'))
    print('PASS real ARM64 link/source/ABI; Android and Fold remain separate',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('operation',choices=['prepare','compile','link']);args=p.parse_args()
    {'prepare':prepare,'compile':compile_objects,'link':link}[args.operation]()
