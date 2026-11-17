"""Selected real ARM64/JNI/MediaCodec/EGL probe. No Kodi or SDK/DEX rebuild.

The CI software injection is private, exact-package gated and <=640x360 input.
It demonstrates media correctness only, never physical hardware throughput.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED
import hashlib,json,os,subprocess,sys,types
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'cast506-pipeline-work'
CAST=ROOT/'repairs/infinity-movies-continue-cast-2103486-20261112/cast'
NATIVE=ROOT/'repairs/infinity-six-repairs-2103502-20261116/cast'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def run(*args,**kw):subprocess.run(list(map(str,args)),check=True,**kw)
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
 OUT.mkdir();native_work=OUT/'native-verification';native_work.mkdir()
 recipe=ROOT/'repairs/infinity-cast-mkv-2103494-20261113/build.py';old_argv=sys.argv[:];sys.argv=[str(recipe),'native',str(native_work),str(apk)]
 scope={'__file__':str(recipe),'__name__':'_retained_native_recipe'};exec(compile(recipe.read_text(),str(recipe),'exec'),scope)
 scope.update(HERE=NATIVE,ROOT=ROOT,BASE=r['baseline']['APK_sha256'],ENGINE='b3d8d96aa55bf0e48f6cf7c995b2c2ebf9c53720b94f2a9e791dd039d64bf1e7')
 scope['native']();sys.argv=old_argv
 native=json.loads((native_work/'CAST-MKV-NATIVE.json').read_bytes());native.update(status='PASS_CAST506_HARDWARE_PIPELINE_ARM64_LINK',baseline=2103506,engine_rebuilt=False,source_hashes=r['inputs'])
 exports=set(native['exports']);old_exports={'open','inspect','init','segment','cancel','close','active'}
 assert exports=={'Java_com_projectinfinity_kodi_InfinityCastRemuxNative_'+n for n in old_exports|{'configureVideo'}}
 (OUT/'ARM64.json').write_text(json.dumps(native,indent=2)+'\n')
 fixtures=OUT/'fixtures';fixtures.mkdir()
 # Explicit SDR709: neither Main10 nor an absent transfer field implies HDR.
 run('ffmpeg','-nostdin','-v','error','-y','-f','lavfi','-i','testsrc2=size=320x180:rate=24','-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','6.02','-c:v','libx265','-preset','ultrafast','-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-color_range','tv','-x265-params','open-gop=0:pools=1:frame-threads=1:log-level=error:keyint=48:min-keyint=48:bframes=2:scenecut=0','-c:a','eac3','-b:a','192k',fixtures/'hevc-eac3.mkv')
 sdk=Path(os.environ['ANDROID_HOME']);bt=sdk/'build-tools/35.0.0';android=sdk/'platforms/android-35/android.jar';classes=OUT/'classes';classes.mkdir();dex=OUT/'dex';dex.mkdir()
 names=['InfinityCastRemux','InfinityCastRemuxNative','InfinityCastReceiverPolicy','InfinityCastDiagnostics','InfinityCastHardwareVideo','InfinityCastGpuSurface','InfinityCastVideoContract']
 sources=[CAST/'java/com/projectinfinity/kodi'/ (n+'.java') for n in names]+list((HERE/'android').glob('*.java'))+[ROOT/'repairs/infinity-cast-end-to-end-2103504-20261116/tests/android/MkvHlsPlayerProbe.java']
 run('javac','-source','8','-target','8','-bootclasspath',str(android)+':'+str(bt/'core-lambda-stubs.jar'),'-d',classes,*sources)
 jar=OUT/'pipeline-probe.jar'
 with ZipFile(jar,'w',ZIP_DEFLATED) as z:
  for p in classes.rglob('*.class'):z.write(p,p.relative_to(classes))
 run('java','-cp',bt/'lib/d8.jar','com.android.tools.r8.D8','--min-api','30','--lib',android,'--output',dex,jar)
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
  z.write(native_work/'native/libinfinitycastremux.so','lib/arm64-v8a/libinfinitycastremux.so');z.write(loader,'lib/arm64-v8a/libinfinitycastqaloader.so');z.write(dex/'classes.dex','classes'+str(max(indices)+1)+'.dex');z.write(fixtures/'hevc-eac3.mkv','assets/hevc-eac3.mkv')
 aligned=OUT/'aligned.apk';run(bt/'zipalign','-p','-f','4',unsigned,aligned);key=OUT/'CI-ONLY.keystore'
 run('keytool','-genkeypair','-alias','CI-only','-keyalg','RSA','-keystore',key,'-storepass','android','-keypass','android','-dname','CN=Disposable Cast Pipeline CI','-validity','2')
 run(bt/'apksigner','sign','--ks',key,'--ks-key-alias','CI-only','--ks-pass','pass:android','--key-pass','pass:android','--out',OUT/'CI-ONLY.apk',aligned)
 run(bt/'zipalign','-c','4',OUT/'CI-ONLY.apk')
 (OUT/'BUILD.json').write_text(json.dumps({'status':'SEPARATE_PACKAGE_PIPELINE_READY','foundation':r['baseline'],'native':native_hashes,'source':os.environ['GITHUB_SHA'],'engine_rebuilt':False,'SDK_rebuilt':False,'production_DEX_rebuilt':False,'owner_installer':False,'new_Cast_library_sha256':native['new_library_sha256']},indent=2)+'\n')
if __name__=='__main__':main()
