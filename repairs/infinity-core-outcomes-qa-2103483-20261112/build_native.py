#!/usr/bin/env python3
"""Actual83 plus Core outcome observation only; original compiler/ABI retained."""
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
OUT=ROOT/'core-outcomes-native'
NATIVE=ROOT/'kodi'
BASE='c302a9f3884902cd023894daac6ac4582bddab41'
BRANCH='work/infinity-core-outcomes-qa-20261112'
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
 assert all(n in allowed or n.startswith('repairs/infinity-core-outcomes-qa-2103483-20261112/') for n in changed),changed
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
 generator=load(HERE/'make_overlay.py','coreqa_generator');data=generator.files(NATIVE)
 binding={};expected=dict(old)
 for name,raw in data.items():
  before=old.get(name);assert before==generator.PINS.get(name)
  expected[name]=hashlib.sha256(raw).hexdigest();binding[name]={'before':before,'after':expected[name]}
  dest=NATIVE/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
 hasher=load(ROOT/'repairs/infinity-native-touch-2103451-20261105/compile_only.py','retained_hasher')
 assert hasher.hashes(NATIVE)==expected and len(expected)==9414
 save('NATIVE-SOURCE-MAP.json',expected)
 save('CORE-OUTCOMES-SOURCE-PRESERVATION.json',dict(status='PASS_EXACT83_PLUS_THREE_DIAGNOSTIC_FILES_TWO_HEADERS',source_commit=os.environ['GITHUB_SHA'],baseline83_native_sha256=BASE_ENGINE,changed=binding,unchanged83_native_sources=9409,Core_source_changed=False,Core_path_correction_activated=False,Cobra_changed=False,admission_or_durability_waivers=False,diagnostic_only=True,Android='NOT_RUN',signed=False))


def dependencies():
 scope();previous().dependencies()


def compile_native():
 scope();expected=json.loads((OUT/'NATIVE-SOURCE-MAP.json').read_text());assert len(expected)==9414
 compiler=load(ROOT/'repairs/universal-persistence-2103401/build.py','retained_arm64_compiler');compiler.OUT=OUT;original=compiler.checked_sources
 def checked(root,pins,allow_generated=False):
  extra=original(root,pins,allow_generated=True)
  if not allow_generated:
   assert Path(root)==NATIVE and pins==expected
   assert all(n.startswith('tools/depends/') for n in extra),extra
  return extra
 compiler.checked_sources=checked;proof=compiler.compile_engine()
 assert proof['complete_native_engine_compiled'] and proof['reviewed_file_count']==9414
 library=OUT/'libkodi.so';assert sha(library)==proof['native_sha256']
 with library.open('rb') as stream:
  data=stream.read()
  assert all(marker in data for marker in (b'InfinityCoreQA',b'core.load.returned',b'core.load.error',b'operation.return',b'native_call.progressed'))
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
 save('CORE-OUTCOMES-ARM64.json',dict(status='PASS_FULL_ARM64_CORE_OUTCOMES_LINK_AND_BASELINE_ABI',source_commit=os.environ['GITHUB_SHA'],native_sha256=sha(library),baseline83_native_sha256=BASE_ENGINE,exports_preserved=len(after[0]),dependencies=sorted(after[1]),diagnostic_only=True,Core_path_correction_activated=False,Android='NOT_RUN',signed=False))


if __name__=='__main__':
 assert len(sys.argv)==2 and sys.argv[1] in ('prepare','dependencies','compile')
 {'prepare':prepare,'dependencies':dependencies,'compile':compile_native}[sys.argv[1]]()
