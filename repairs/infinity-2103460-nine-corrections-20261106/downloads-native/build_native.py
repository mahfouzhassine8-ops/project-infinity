"""Exact signed2103460 native map + four scoped Downloads files. No key/APK/runtime."""
import argparse, hashlib, importlib.util, json, os, shutil, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];OUT=ROOT/'controlled-native'
BRANCH='work/infinity-2103460-nine-corrections-20261106'
BASE_MAP='74031d22536937e851abb2c77c9d19b461932a221c54ea69fe422efe63658663'
BASE_ENGINE='febf0e0ed95ef33e906999b4a92c46e6b79bae1c555eaa89b4954d0b74fb3e41'
NAV='xbmc/video/windows/GUIWindowVideoNav.cpp'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,d):OUT.mkdir(exist_ok=True);(OUT/n).write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
restore=load(ROOT/'repairs/infinity-native-touch-2103451-20261105/compile_only.py','existing_verified_restoration');restore.OUT=OUT

def preflight():
 assert os.environ['GITHUB_REPOSITORY']=='mahfouzhassine8-ops/project-infinity'
 assert os.environ['GITHUB_REF']=='refs/heads/'+BRANCH
 assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==os.environ['GITHUB_SHA']
 rows=json.loads((HERE/'CANDIDATE.json').read_text());assert rows['native_sha256']==BASE_ENGINE and len(rows['files'])==4
 expected=json.loads((HERE/'SIGNED460-NATIVE-SOURCE-MAP.json').read_text());assert sha(HERE/'SIGNED460-NATIVE-SOURCE-MAP.json')==BASE_MAP
 for n,r in rows['files'].items():assert expected[n]==r['before_sha256'] and sha(ROOT/r['source'])==r['candidate_sha256'],n
 assert json.loads((HERE/'HOST-CONTRACT-RESULT.json').read_text())['old_source_dialog_overloads_preserved_byte_for_byte'] is True
 for n in ('scripts/infinity_live_app_ci_2.sh','repairs/android-checkpoint-shutdown/native_ci.py','repairs/android-checkpoint-shutdown/install_ndk.sh','repairs/universal-persistence-2103401/build.py'):
  assert (ROOT/n).read_bytes()==subprocess.check_output(['git','show',restore.PRODUCER+':'+n]),n
 proof={}
 for label,(aid,run,title,size,digest) in restore.ASSETS.items():
  row=json.loads(subprocess.check_output(['gh','api',f'repos/mahfouzhassine8-ops/project-infinity/actions/artifacts/{aid}'],text=True))
  assert (row['id'],row['workflow_run']['id'],row['name'],row['size_in_bytes'],row['digest'],row['expired'])==(aid,run,title,size,'sha256:'+digest,False)
  proof[label]=dict(id=aid,run=run,archive_sha256=digest,size=size)
 save('AUTHENTICATED-INPUTS.json',proof)

def restore_sources():
 restore.restore() # Original signed451 restoration + two previously approved touch files.
 expected=json.loads((HERE/'SIGNED460-NATIVE-SOURCE-MAP.json').read_text())
 rows=json.loads((HERE/'CANDIDATE.json').read_text())['files']
 old=ROOT/'repairs/infinity-2103458-six-corrections-20261105/integration-048/native'/NAV
 assert sha(old)==expected[NAV];shutil.copyfile(old,ROOT/'kodi'/NAV)
 assert restore.hashes(ROOT/'kodi')==expected,'EXACT_SIGNED460_MAP_REQUIRED_BEFORE_CANDIDATE'
 save('SIGNED460-NATIVE-SOURCE-MAP.json',expected);assert sha(OUT/'SIGNED460-NATIVE-SOURCE-MAP.json')==BASE_MAP
 for n,r in rows.items():shutil.copyfile(ROOT/r['source'],ROOT/'kodi'/n)
 after=restore.hashes(ROOT/'kodi');assert set(after)==set(expected) and {n for n in after if after[n]!=expected[n]}==set(rows)
 for n,r in rows.items():assert after[n]==r['candidate_sha256']
 save('NATIVE-SOURCE-MAP.json',after)
 save('SOURCE-BINDING.json',dict(base=2103460,base_engine_sha256=BASE_ENGINE,base_map_sha256=BASE_MAP,source_commit=os.environ['GITHUB_SHA'],changed_native_sources=rows,reviewed_count=len(after),protected_native_source_count=len(after)-4,APK=False,signing=False,Android='NOT_RUN'))

def compile_engine():
 sys.path.insert(0,str(ROOT/'repairs/universal-persistence-2103401'))
 p=load(ROOT/'repairs/universal-persistence-2103401/build.py','unchanged_engine_builder');p.OUT=OUT
 proof=p.compile_engine();assert proof['complete_native_engine_compiled'] and proof['reviewed_file_count']==9411
 lib=OUT/'libkodi.so';binary=lib.read_bytes()
 for marker in (b'infinity-downloads-only',b'Infinity.DownloadsSources.v1',b'downloads_source_save_failed',b'infinity-library-direct'):assert marker in binary,marker
 tool=Path(os.environ['ANDROID_HOME'])/'ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readelf'
 header=subprocess.check_output([str(tool),'-h',str(lib)],text=True);assert 'ELF64' in header and 'AArch64' in header
 symbols=subprocess.check_output([str(tool),'--dyn-syms','--wide',str(lib)],text=True)
 assert any('InfinityCommandCenterIdentityV1' in line and 'GLOBAL' in line and 'DEFAULT' in line for line in symbols.splitlines())
 (OUT/'ELF-ABI.txt').write_text(header);(OUT/'DYNAMIC-SYMBOLS.txt').write_text(symbols)
 before=json.loads((OUT/'SIGNED460-NATIVE-SOURCE-MAP.json').read_text());after=json.loads((OUT/'NATIVE-SOURCE-MAP.json').read_text());rows=json.loads((HERE/'CANDIDATE.json').read_text())['files']
 assert set(before)==set(after) and {n for n in after if before[n]!=after[n]}==set(rows)
 save('CONTROLLED-ENGINE-VERIFIED.json',dict(status='PASS_FULL_ARM64_SIGNED460_PLUS_SCOPED_DOWNLOADS',source_commit=os.environ['GITHUB_SHA'],native_sha256=sha(lib),native_bytes=lib.stat().st_size,source_reference=2103460,changed_native_sources={n:after[n] for n in rows},protected_native_source_count=9407,APK=False,signing=False,Android='NOT_RUN',Fold='NOT_RUN',Search_crash='UNRESOLVED_SEPARATE'))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['preflight','restore','compile']);a=p.parse_args();OUT.mkdir(exist_ok=True);{'preflight':preflight,'restore':restore_sources,'compile':compile_engine}[a.mode]()
