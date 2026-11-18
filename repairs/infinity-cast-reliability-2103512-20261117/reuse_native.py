"""Reuse exact successful ARM64 compilation from the failed probe-stub run.

Authenticate the entire archive, but extract only the bounded proof/library;
large media fixtures are not native build inputs and are not extracted here.
"""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json,os,re,stat,subprocess

def reuse(c,row,work):
 producer=c.api('actions/runs/'+str(row['run']));assert producer['status']=='completed' and producer['conclusion']=='failure' and producer['head_sha']==row['source'] and producer['workflow_id']==row['workflow_id']
 artifact=c.api('actions/artifacts/'+str(row['id']));assert not artifact['expired'] and artifact['workflow_run']['id']==row['run'] and all(artifact[k]==row[k] for k in ('name','digest','size_in_bytes'))
 archive=work/'verified-compiled-input.zip'
 with archive.open('xb')as f:subprocess.run(['gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/artifacts/'+str(row['id'])+'/zip'],stdout=f,check=True)
 assert archive.stat().st_size==row['size_in_bytes'] and 'sha256:'+hashlib.sha256(archive.read_bytes()).hexdigest()==row['digest']
 prefix='cast512-reliability-work/';expected={prefix+'ARM64.json':9780,prefix+'fixtures/hevc-eac3.mkv':747404,prefix+'fixtures/direct-hevc.mkv':718093,prefix+'fixtures/high-sparse.mkv':42989977,prefix+'native-verification/native/libinfinitycastremux.so':312360}
 with ZipFile(archive)as z:
  assert len(z.namelist())==len(set(z.namelist())) and set(z.namelist())==set(expected)
  for info in z.infolist():assert info.file_size==expected[info.filename] and not stat.S_ISLNK(info.external_attr>>16)
  proof=json.loads(z.read(prefix+'ARM64.json'));library=z.read(prefix+'native-verification/native/libinfinitycastremux.so')
 assert proof['status']=='PASS_CAST512_INTEGRATED_ARM64_LINK' and proof['baseline']==2103512 and proof['engine_rebuilt'] is False
 root=Path(__file__).resolve().parents[2]
 for p in ['repairs/infinity-six-repairs-2103502-20261116/cast/native/InfinityCastRemux.cpp','repairs/infinity-cast-hardware-pipeline-2103506-20261117/native/CastVideoAdapter.h','repairs/infinity-cast-end-to-end-2103504-20261116/native/CastAudioAdapter.h']:
  assert hashlib.sha256((root/p).read_bytes()).hexdigest()==proof['source_hashes'][p],p
 assert hashlib.sha256(library).hexdigest()==proof['new_library_sha256']=='adb23e4b49be9bdb7bc487a8be7f8c3735c9877be077ec3451ed43474bd5df91'
 target=work/'native';target.mkdir();path=target/'libinfinitycastremux.so';path.write_bytes(library)
 tool=Path(os.environ['ANDROID_HOME'])/'ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readelf';elf=subprocess.check_output([tool,'-h','-d','--dyn-syms','--wide',path],text=True)
 assert 'AArch64' in elf and all(x in elf for x in proof['exports'])
 proof['reused_compilation']=row;proof['historical_run_outcome']='Nativecompile/linkPASS; actualAndroidNOT_RUN_due_CI_probe_stub_overload_error; notafunctionalpass'
 return proof
