"""Selected real ARM64/JNI/MediaCodec/EGL probe. No Kodi or SDK/DEX rebuild.

The CI software injection is private, exact-package gated and <=640x360 input.
It demonstrates media correctness only, never physical hardware throughput.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED
import hashlib,json,os,subprocess,sys,types,shutil,stat
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'cast506-pipeline-work'
CAST=ROOT/'repairs/infinity-movies-continue-cast-2103486-20261112/cast'
NATIVE=ROOT/'repairs/infinity-six-repairs-2103502-20261116/cast'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def run(*args,**kw):subprocess.run(list(map(str,args)),check=True,**kw)
def reuse_native(c,row,work):
 # The producer's compile passed but its new test fixture failed before loading
 # JNI. Authenticate that failed run explicitly; never claim the test passed.
 producer=c.api('actions/runs/'+str(row['run']));assert producer['status']=='completed' and producer['conclusion']=='failure' and producer['workflow_id']==row['workflow_id'] and producer['head_sha']==row['source']
 artifact=c.api('actions/artifacts/'+str(row['id']));assert not artifact['expired'] and artifact['workflow_run']['id']==row['run'] and all(artifact[k]==row[k] for k in ('name','digest','size_in_bytes'))
 archive=work/'compiled-input.zip'
 with archive.open('xb') as f:subprocess.run(['gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/artifacts/'+str(row['id'])+'/zip'],stdout=f,check=True)
 assert 'sha256:'+sha(archive)==row['digest'] and archive.stat().st_size==row['size_in_bytes']
 original=work/'compiled-input';original.mkdir()
 with ZipFile(archive) as z:
  assert len(z.namelist())==len(set(z.namelist())) and sum(i.file_size for i in z.infolist())<32*1024*1024
  for i in z.infolist():assert not Path(i.filename).is_absolute() and '..' not in Path(i.filename).parts and not stat.S_ISLNK(i.external_attr>>16)
  z.extractall(original)
 proof=json.loads(c.unique(original,'ARM64.json').read_bytes());assert proof['status']=='PASS_CAST506_HARDWARE_PIPELINE_ARM64_LINK' and proof['baseline']==2103506 and proof['engine_rebuilt'] is False
 for n in ('repairs/infinity-six-repairs-2103502-20261116/cast/native/InfinityCastRemux.cpp','repairs/infinity-cast-hardware-pipeline-2103506-20261117/native/CastVideoAdapter.h','repairs/infinity-cast-end-to-end-2103504-20261116/native/CastAudioAdapter.h'):assert sha(ROOT/n)==proof['source_hashes'][n],n
 library=c.unique(original,'libinfinitycastremux.so');assert sha(library)==proof['new_library_sha256'];target=work/'native';target.mkdir();shutil.copyfile(library,target/library.name)
 ndk=Path(os.environ['ANDROID_HOME'])/'ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin';elf=subprocess.check_output([ndk/'llvm-readelf','-h','-d','--dyn-syms','--wide',target/library.name],text=True);assert 'AArch64' in elf and all(n in elf for n in proof['exports']);proof['reused_compilation']=row;proof['historical_run_outcome']='FAIL_TEST_FIXTURE_BEFORE_JNI_LOAD; native compilation passed; no functional pass assumed'
 return proof
def main():
 assert os.environ['GITHUB_ACTIONS']=='true' and os.environ['GITHUB_REPOSITORY']=='mahfouzhassine8-ops/project-infinity'
 assert os.environ['GITHUB_REF']=='refs/heads/work/infinity-2103506-receiver-compatibility-20261117'
 r=json.loads((HERE/'CI-PIPELINE.json').read_bytes())
 assert r['engine_build'] is False and r['owner_APK'] is False and r['shutdown'] is False
 for n,h in r['inputs'].items():assert sha(ROOT/n)==h,n
 changed=subprocess.check_output(['git','diff','--name-only',r['source_commit'],os.environ['GITHUB_SHA']],text=True).splitlines()
 assert changed==[str((HERE/'CI-PIPELINE.json').relative_to(ROOT))],changed
 helper='repairs/infinity-movies-continue-cast-2103486-20261112/release/common_release.py'
 raw=subprocess.check_output(['git','show','21616dfa94bf7ca9ec52e40119edf95df5e64073:'+helper]);scope={'__file__':str(ROOT/helper),'__name__':'_retained_reader'};exec(compile(raw,str(ROOT/helper),'exec'),scope);c=types.SimpleNamespace(**scope)
 apk=c.unique(c.obtain(r['baseline'],'pipeline506-authenticated-baseline'),'Infinity-2103506-Combined-Original-Signer.apk');assert sha(apk)==r['baseline']['APK_sha256']
 c.signature(apk);OUT.mkdir();native_work=OUT/'native-verification';native_work.mkdir()
 if 'reuse_native' in r:native=reuse_native(c,r['reuse_native'],native_work)
 else:
  recipe=ROOT/'repairs/infinity-cast-mkv-2103494-20261113/build.py';old_argv=sys.argv[:];sys.argv=[str(recipe),'native',str(native_work),str(apk)]
  scope={'__file__':str(recipe),'__name__':'_retained_native_recipe'};exec(compile(recipe.read_text(),str(recipe),'exec'),scope)
  scope.update(HERE=NATIVE,ROOT=ROOT,BASE=r['baseline']['APK_sha256'],ENGINE='b3d8d96aa55bf0e48f6cf7c995b2c2ebf9c53720b94f2a9e791dd039d64bf1e7');scope['native']();sys.argv=old_argv
  native=json.loads((native_work/'CAST-MKV-NATIVE.json').read_bytes());native.update(status='PASS_CAST506_HARDWARE_PIPELINE_ARM64_LINK',baseline=2103506,engine_rebuilt=False,source_hashes=r['inputs'])
 exports=set(native['exports']);old_exports={'open','inspect','init','segment','cancel','close','active'}
 assert exports=={'Java_com_projectinfinity_kodi_InfinityCastRemuxNative_'+n for n in old_exports|{'configureVideo'}}
 (OUT/'ARM64.json').write_text(json.dumps(native,indent=2)+'\n')
 component=c.obtain(r['component'],'pipeline506-verified-production-component');compiled=json.loads(c.unique(component,'COMPONENT-RESULT.json').read_bytes());contract=json.loads(c.unique(component,'CAST506-COMPONENT.json').read_bytes());assert compiled['status']=='PASS_COMPONENT_COMPILE_AND_EXISTING_API_LINK_CONTRACT' and contract['status']=='PASS_CHANGED_CAST_COMPONENT_AND_EXTERNAL_API_CONTRACT'
 assert compiled['baseline_APK_sha256']==r['baseline']['APK_sha256']
 for name,digest in compiled['feature_Java_sha256'].items():assert sha(CAST/name)==digest,name
 cast_dex=c.unique(component,'classes.dex');assert sha(cast_dex)==compiled['dex']['classes.dex']
 sys.path.insert(0,str(HERE));from component_contract import verify as reverse_contract
 (OUT/'EXTERNAL-API.json').write_text(json.dumps(reverse_contract(apk,cast_dex.parent),indent=2)+'\n')
 fixtures=OUT/'fixtures';fixtures.mkdir()
 # Explicit SDR709: neither Main10 nor an absent transfer field implies HDR.
 run('ffmpeg','-nostdin','-v','error','-y','-f','lavfi','-i','testsrc2=size=320x180:rate=24','-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','6.02','-c:v','libx265','-preset','ultrafast','-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-color_range','tv','-x265-params','open-gop=0:pools=1:frame-threads=1:log-level=error:keyint=48:min-keyint=48:bframes=2:scenecut=0','-c:a','eac3','-b:a','192k',fixtures/'hevc-eac3.mkv')
 sdk=Path(os.environ['ANDROID_HOME']);bt=sdk/'build-tools/35.0.0';android=sdk/'platforms/android-35/android.jar';classes=OUT/'classes';classes.mkdir();dex=OUT/'dex';dex.mkdir()
 names=['InfinityCastRemux','InfinityCastRemuxNative','InfinityCastReceiverPolicy','InfinityCastDiagnostics','InfinityCastHardwareVideo','InfinityCastGpuSurface','InfinityCastVideoContract']
 stubs=OUT/'stubs/com/projectinfinity/kodi';stubs.mkdir(parents=True)
 (stubs/'InfinityCastSource.java').write_text('package com.projectinfinity.kodi; final class InfinityCastSource {static InfinityCastSource parse(String s){throw new AssertionError("compile only");}}')
 (stubs/'InfinityCastRelay.java').write_text('package com.projectinfinity.kodi; import java.io.*;import java.net.*; final class InfinityCastRelay {interface Ready {void ready(InfinityCastRelay r,String mime,String failure);}static InfinityCastRelay start(InetAddress a,InfinityCastSource s,InfinityCastReceiverPolicy.Receiver p,InfinityCastHardwareVideo.Factory f,Ready r)throws IOException{throw new AssertionError("compile only");}String address(){throw new AssertionError();}long durationMs(){throw new AssertionError();}static boolean busy(){throw new AssertionError();}void closeWhenRetired(Runnable r){throw new AssertionError();}void close(){throw new AssertionError();}}')
 sources=[CAST/'java/com/projectinfinity/kodi'/ (n+'.java') for n in names]+list((HERE/'android').glob('*.java'))+list(stubs.glob('*.java'))
 run('javac','-source','8','-target','8','-bootclasspath',str(android)+':'+str(bt/'core-lambda-stubs.jar'),'-d',classes,*sources)
 jar=OUT/'pipeline-probe.jar';stubjar=OUT/'compile-only.jar';test_roots=('InfinityCastProbeActivity','Origin','MkvHlsPlayerProbe','HlsServer')
 with ZipFile(jar,'w',ZIP_DEFLATED) as z,ZipFile(stubjar,'w',ZIP_DEFLATED) as compile_only:
  for p in classes.rglob('*.class'):
   root=p.name.split('$')[0].split('.')[0];(z if root in test_roots else compile_only).write(p,p.relative_to(classes))
 run('java','-cp',bt/'lib/d8.jar','com.android.tools.r8.D8','--min-api','30','--lib',android,'--classpath',stubjar,'--output',dex,jar)
 loader=OUT/'libinfinitycastqaloader.so';ndk=sdk/'ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin'
 run(ndk/'aarch64-linux-android21-clang++','-shared','-fPIC',ROOT/'repairs/infinity-cast-end-to-end-2103504-20261116/tests/android/loader.cpp','-ldl','-Wl,-z,max-page-size=16384','-o',loader)
 manifest=OUT/'AndroidManifest.xml';manifest.write_text('''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.projectinfinity.castqa.pipeline" android:versionCode="1" android:versionName="CI-only"><uses-sdk android:minSdkVersion="30" android:targetSdkVersion="35"/><uses-permission android:name="android.permission.INTERNET"/><application android:extractNativeLibs="true" android:label="Cast pipeline CI only" android:theme="@android:style/Theme.Material.NoActionBar" android:usesCleartextTraffic="true"><activity android:name="com.projectinfinity.kodi.InfinityCastProbeActivity" android:exported="true"/></application></manifest>''')
 shell=OUT/'shell.apk';run(bt/'aapt2','link','--manifest',manifest,'-I',android,'-o',shell)
 unsigned=OUT/'CI-ONLY-UNSIGNED.apk';native_hashes={}
 with ZipFile(unsigned,'w',ZIP_DEFLATED) as z,ZipFile(shell) as skeleton,ZipFile(apk) as base:
  for n in skeleton.namelist():
   if n!='resources.arsc':z.writestr(n,skeleton.read(n))
  # Reuse immutable baseline Media3 APIs for HLS playback, without invoking
  # any Cobra entry point. Exclude the original Cast DEX to avoid shadowing.
  sys.path.insert(0,str(CAST));from dex_contract import Dex
  import re
  indices=[];excluded=[]
  for n in base.namelist():
   if re.fullmatch(r'classes\d*\.dex',n):
    indices.append(int(re.search(r'\d+',n).group()) if re.search(r'\d+',n) else 1)
    raw=base.read(n)
    if 'Lcom/projectinfinity/kodi/InfinityCastRemux;' in Dex(raw).classes:excluded.append(n)
    else:z.writestr(n,raw)
   elif n=='resources.arsc' or n.startswith('res/'):z.writestr(n,base.read(n),compress_type=ZIP_STORED if n=='resources.arsc' else ZIP_DEFLATED)
  assert excluded==['classes6.dex'],excluded
  for lib in ('libkodi.so','libc++_shared.so','libshairplay.so'):
   n='lib/arm64-v8a/'+lib;data=base.read(n);z.writestr(n,data);native_hashes[lib]=hashlib.sha256(data).hexdigest()
  z.write(native_work/'native/libinfinitycastremux.so','lib/arm64-v8a/libinfinitycastremux.so');z.write(loader,'lib/arm64-v8a/libinfinitycastqaloader.so');z.write(cast_dex,excluded[0]);z.write(dex/'classes.dex','classes'+str(max(indices)+1)+'.dex');z.write(fixtures/'hevc-eac3.mkv','assets/hevc-eac3.mkv')
 with ZipFile(unsigned) as z:
  dex_names=[n for n in z.namelist() if re.fullmatch(r'classes\d*\.dex',n)]
  sequence=sorted(int(re.search(r'\d+',n).group()) if re.search(r'\d+',n) else 1 for n in dex_names)
  assert sequence==list(range(1,len(sequence)+1)),'Android multidex must have no gap'
  classes_seen=set()
  for n in dex_names:
   definitions=set(Dex(z.read(n)).classes);assert not definitions&classes_seen;classes_seen|=definitions
  assert 'Lcom/projectinfinity/kodi/InfinityCastProbeActivity;' in classes_seen
 aligned=OUT/'aligned.apk';run(bt/'zipalign','-p','-f','4',unsigned,aligned);key=OUT/'CI-ONLY.keystore'
 run('keytool','-genkeypair','-alias','CI-only','-keyalg','RSA','-keystore',key,'-storepass','android','-keypass','android','-dname','CN=Disposable Cast Pipeline CI','-validity','2')
 run(bt/'apksigner','sign','--ks',key,'--ks-key-alias','CI-only','--ks-pass','pass:android','--key-pass','pass:android','--out',OUT/'CI-ONLY.apk',aligned)
 run(bt/'zipalign','-c','4',OUT/'CI-ONLY.apk')
 (OUT/'BUILD.json').write_text(json.dumps({'status':'SEPARATE_PACKAGE_PIPELINE_READY','foundation':r['baseline'],'native':native_hashes,'source':os.environ['GITHUB_SHA'],'engine_rebuilt':False,'SDK_rebuilt':False,'production_DEX_rebuilt':False,'owner_installer':False,'new_Cast_library_sha256':native['new_library_sha256']},indent=2)+'\n')
if __name__=='__main__':main()
