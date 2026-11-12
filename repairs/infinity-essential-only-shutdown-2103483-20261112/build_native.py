#!/usr/bin/env python3
"""Actual83 plus functional metadata/load accounting; original compiler/ABI retained."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=ROOT/'essential-only-native'
NATIVE=ROOT/'kodi'
BASE='3638eb1d95634a2d8d0b20db1319fcacf5b56d43'
BRANCH='work/infinity-essential-only-shutdown-2103483-20261112'
BASE_ENGINE='f14ff78865158337eb6fd19dfe549912d57f2a6a912e5b3440ed28880ee0cb0c'


def sha(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
 sys.path.insert(0,str(path.parent))
 try:spec.loader.exec_module(module)
 finally:sys.path.pop(0)
 return module


def save(name,value):
 OUT.mkdir(exist_ok=True);(OUT/name).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')


def scope():
 assert os.environ['GITHUB_REPOSITORY']=='mahfouzhassine8-ops/project-infinity'
 assert os.environ['GITHUB_REF']=='refs/heads/'+BRANCH
 assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==os.environ['GITHUB_SHA']
 policy='repairs/dual-experience-isolation-2103420/signer-policy.json'
 allowed={'.github/workflows/infinity-core-outcomes-qa-native.yml','.github/workflows/infinity-core-outcomes-qa-stage.yml','.github/workflows/infinity-saved-navigation-android.yml',policy}
 changed=subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],text=True).splitlines()
 assert all(n in allowed or n.startswith('repairs/infinity-essential-only-shutdown-2103483-20261112/') for n in changed),changed
 assert (ROOT/policy).read_bytes()==subprocess.check_output(['git','show','3d9709bb1226a2ffa3a474cf04b3d3842b084611:'+policy]),'Exact original83 authority policy snapshot required'
 assert json.loads((HERE/'SCOPE.json').read_text())['Cobra_changes'] is False
 for path in ('repairs/infinity-functional-startup-2103482-20261111/build_diagnostic.py','repairs/infinity-close-startup-2103480-20261110/build_candidate/native_build.py','repairs/infinity-native-writer-shutdown-2103483-20261112/SERVICE-CANDIDATE.patch'):
  assert (ROOT/path).read_bytes()==subprocess.check_output(['git','show',BASE+':'+path]),path


def previous():
 module=load(ROOT/'repairs/infinity-functional-startup-2103482-20261111/build_diagnostic.py','retained83_builder')
 module.scope=scope;module.OUT=OUT
 return module


def prepare():
 scope();previous().prepare()
 old=json.loads((OUT/'NATIVE-SOURCE-MAP.json').read_text());assert len(old)==9412
 expected=dict(old);binding={}
 assert old==json.loads((HERE/'BASE83-NATIVE-SOURCE-MAP.json').read_text())
 pins=json.loads((HERE/'BASELINE-SOURCE.json').read_text())
 for name,pin in pins.items():
  assert old[name]==pin and sha(NATIVE/name)==pin
  raw=(HERE/'native/overlay'/name).read_bytes();after=hashlib.sha256(raw).hexdigest()
  if after!=pin:
   (NATIVE/name).write_bytes(raw);expected[name]=after;binding[name]={'before':pin,'after':after}
 assert len(binding)==3 and len(expected)==9412
 hasher=load(ROOT/'repairs/infinity-native-touch-2103451-20261105/compile_only.py','retained_hasher')
 assert hasher.hashes(NATIVE)==expected
 save('NATIVE-SOURCE-MAP.json',expected)
 save('ESSENTIAL-ONLY-SOURCE-PRESERVATION.json',dict(status='PASS_EXACT83_PLUS_THREE_SHUTDOWN_HEADERS',source_commit=os.environ['GITHUB_SHA'],baseline83_native_sha256=BASE_ENGINE,changed=binding,unchanged83_native_sources=9409,Core_source_changed=False,Core_path_correction_activated=False,Cobra_changed=False,essential_admission_or_durability_waivers=False,functional_shutdown_repair=True,Android='NOT_RUN',signed=False))


def dependencies():
 scope();previous().dependencies()


def compile_native():
 scope();expected=json.loads((OUT/'NATIVE-SOURCE-MAP.json').read_text());assert len(expected)==9412
 compiler=load(ROOT/'repairs/universal-persistence-2103401/build.py','retained_arm64_compiler');compiler.OUT=OUT;original=compiler.checked_sources
 def checked(root,pins,allow_generated=False):
  extra=original(root,pins,allow_generated=True)
  if not allow_generated:
   assert Path(root)==NATIVE and pins==expected
   assert all(n.startswith('tools/depends/') for n in extra),extra
  return extra
 compiler.checked_sources=checked;proof=compiler.compile_engine()
 assert proof['complete_native_engine_compiled'] and proof['reviewed_file_count']==9412
 library=OUT/'libkodi.so';assert sha(library)==proof['native_sha256']
 with library.open('rb') as stream:
  data=stream.read()
  assert all(marker in data for marker in (b'outcome=loaded;native_drain=unverified',b'checked_dlopen',b'Original native loader binding unavailable'))
 readelf=Path(os.environ['ANDROID_HOME'])/'ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readelf'
 def abi(path):
  head=subprocess.check_output([str(readelf),'-h',str(path)],text=True);assert all(v in head for v in ('ELF64','AArch64','DYN'))
  symbols=subprocess.check_output([str(readelf),'--dyn-syms','--wide',str(path)],text=True);dynamic=subprocess.check_output([str(readelf),'-d',str(path)],text=True)
  exports=set()
  for line in symbols.splitlines():
   fields=line.split()
   if len(fields)>=8 and fields[4]=='GLOBAL' and fields[5] in ('DEFAULT','PROTECTED') and fields[6]!='UND':exports.add(fields[7])
  return exports,set(re.findall(r'Shared library: \[([^\]]+)\]',dynamic))
 before=abi(OUT/'baseline80-libkodi.so');after=abi(library);assert before==after
 save('ESSENTIAL-ONLY-ARM64.json',dict(status='PASS_FULL_ARM64_ESSENTIAL_ONLY_LINK_AND_BASELINE_ABI',source_commit=os.environ['GITHUB_SHA'],native_sha256=sha(library),baseline83_native_sha256=BASE_ENGINE,exports_preserved=len(after[0]),dependencies=sorted(after[1]),functional_shutdown_repair=True,Core_path_correction_activated=False,Android='NOT_RUN',signed=False))


if __name__=='__main__':
 assert len(sys.argv)==2 and sys.argv[1] in ('prepare','dependencies','compile')
 {'prepare':prepare,'dependencies':dependencies,'compile':compile_native}[sys.argv[1]]()
