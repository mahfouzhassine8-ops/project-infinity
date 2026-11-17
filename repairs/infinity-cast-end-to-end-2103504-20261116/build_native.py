"""Exact signed504 engine reused; compile only the reviewed Cast JNI library."""
from pathlib import Path
import hashlib,json,os,re,subprocess,sys,types
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
WORK=ROOT/'cast504-audio-work'
BASE='ab9104471c729751d6127cc4dfc6e98d8bb4c916212c356ce9c0295b2a0c5234'
ENGINE='b3d8d96aa55bf0e48f6cf7c995b2c2ebf9c53720b94f2a9e791dd039d64bf1e7'
PRIOR='86a34a4976813f24280345561170b1dee47e96fb9c3b34642190ced2c2fe9ffd'
SOURCE='repairs/infinity-six-repairs-2103502-20261116/cast'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 assert os.environ['GITHUB_ACTIONS']=='true'
 assert os.environ['GITHUB_REPOSITORY']=='mahfouzhassine8-ops/project-infinity'
 assert os.environ['GITHUB_REF']=='refs/heads/work/infinity-2103504-cast-end-to-end-20261116'
 request=json.loads((HERE/'CI-NATIVE.json').read_bytes())
 assert request['case']=='Cast_EAC3_AAC_ARM64_only' and request['Kodi_build'] is False
 assert request['APK_build'] is False and request['baseline']==2103504
 for name,wanted in request['inputs'].items():assert sha(ROOT/name)==wanted,name
 changed=subprocess.check_output(['git','diff','--name-only',request['source_commit'],os.environ['GITHUB_SHA']],text=True).splitlines()
 assert changed==[str((HERE/'CI-NATIVE.json').relative_to(ROOT))],changed
 helper='repairs/infinity-movies-continue-cast-2103486-20261112/release/common_release.py'
 raw=subprocess.check_output(['git','show','21616dfa94bf7ca9ec52e40119edf95df5e64073:'+helper])
 scope_helper={'__file__':str(ROOT/helper),'__name__':'_pinned_artifact_reader'}
 exec(compile(raw,str(ROOT/helper),'exec'),scope_helper)
 common=types.SimpleNamespace(**scope_helper)
 signed=common.obtain(request['baseline_artifact'],'cast504-exact-signed-baseline')
 apk=common.unique(signed,'Infinity-2103504-Combined-Original-Signer.apk')
 assert sha(apk)==BASE
 prior=ROOT/'repairs/infinity-cast-mkv-2103494-20261113/build.py'
 WORK.mkdir()
 sys.argv=[str(prior),'native',str(WORK),str(apk)]
 scope={'__file__':str(prior),'__name__':'_retained_cast_only_recipe'}
 exec(compile(prior.read_bytes(),str(prior),'exec'),scope)
 scope.update(HERE=ROOT/SOURCE,ROOT=ROOT,BASE=BASE,ENGINE=ENGINE)
 scope['native']()
 old=WORK/'base-native/libinfinitycastremux.so';new=WORK/'native/libinfinitycastremux.so'
 assert sha(old)==PRIOR and sha(WORK/'base-native/libkodi.so')==ENGINE
 tool=Path(os.environ['ANDROID_HOME'])/'ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readelf'
 def abi(p):
  raw=subprocess.check_output([tool,'--dyn-syms','--wide','-d',p],text=True)
  exports=[]
  for line in raw.splitlines():
   fields=line.split()
   if len(fields)>=8 and fields[4] in ('GLOBAL','WEAK') and fields[5] in ('DEFAULT','PROTECTED') and fields[6]!='UND':exports.append((fields[3],fields[4],fields[5],fields[7]))
  return {'exports':sorted(exports),'dependencies':sorted(re.findall(r'Shared library: \[([^\]]+)\]',raw))}
 assert abi(old)==abi(new),'CAST_ABI_CHANGED'
 symbols=subprocess.check_output([tool,'--dyn-syms','--wide',WORK/'base-native/libkodi.so'],text=True)
 audio=(HERE/'native/CastAudioAdapter.h').read_text()
 required=sorted(set(re.findall(r'F\((\w+)\)',audio)))
 defined=set()
 for line in symbols.splitlines():
  f=line.split()
  if len(f)>=8 and f[3] in ('FUNC','IFUNC') and f[4] in ('GLOBAL','WEAK') and f[5] in ('DEFAULT','PROTECTED') and f[6]!='UND':defined.add(f[7].split('@')[0])
 assert required and set(required)<=defined,'EXISTING_ENGINE_AUDIO_EXPORT_MISSING'
 proof=json.loads((WORK/'CAST-MKV-NATIVE.json').read_bytes())
 proof.update(status='PASS_CAST_AUDIO_ARM64_LINK_AND_EXACT504_ABI',baseline=2103504,source=os.environ['GITHUB_SHA'],
              baseline_artifact=request['baseline_artifact'],new_audio_symbols=required,ABI=abi(new),
              reviewed_inputs=request['inputs'],Kodi_build=False,DEX_build=False,APK_build=False,
              Android_execution='NOT_RUN',physical_TV='NOT_TESTED')
 (WORK/'CAST-AUDIO-ARM64.json').write_text(json.dumps(proof,indent=2,sort_keys=True)+'\n')
 print('PASS_CAST_AUDIO_ARM64_ONLY_NO_KODI_BUILD')
if __name__=='__main__':main()
