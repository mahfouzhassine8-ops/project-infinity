"""Disposable separate-package JNI/relay probe. Never signs an owner installer."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED,ZIP_STORED
import hashlib,json,os,re,subprocess,sys,types,shutil
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];WORK=ROOT/'cast504-android-work'
BASE='ab9104471c729751d6127cc4dfc6e98d8bb4c916212c356ce9c0295b2a0c5234'
def run(args,**kw):return subprocess.run(list(map(str,args)),check=True,**kw)
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 assert os.environ['GITHUB_ACTIONS']=='true' and os.environ['GITHUB_REPOSITORY']=='mahfouzhassine8-ops/project-infinity'
 assert os.environ['GITHUB_REF']=='refs/heads/work/infinity-2103504-cast-end-to-end-20261116'
 request=json.loads((HERE/'CI-ANDROID.json').read_bytes())
 assert request['Kodi_build'] is False and request['shutdown'] is False and request['owner_APK'] is False
 for name,wanted in request['inputs'].items():assert sha(ROOT/name)==wanted,name
 changed=subprocess.check_output(['git','diff','--name-only',request['source_commit'],os.environ['GITHUB_SHA']],text=True).splitlines()
 assert changed==[str((HERE/'CI-ANDROID.json').relative_to(ROOT))],changed
 helper='repairs/infinity-movies-continue-cast-2103486-20261112/release/common_release.py'
 raw=subprocess.check_output(['git','show','21616dfa94bf7ca9ec52e40119edf95df5e64073:'+helper])
 scope={'__file__':str(ROOT/helper),'__name__':'_retained_artifact_reader'};exec(compile(raw,str(ROOT/helper),'exec'),scope);c=types.SimpleNamespace(**scope)
 native=c.obtain(request['native'],'cast504-android-native');proof=c.load(c.unique(native,'CAST-AUDIO-ARM64.json'))
 assert proof['status']=='PASS_CAST_AUDIO_ARM64_LINK_AND_EXACT504_ABI' and proof['baseline']==2103504
 for name in ('repairs/infinity-six-repairs-2103502-20261116/cast/native/InfinityCastRemux.cpp',str((HERE/'native/CastAudioAdapter.h').relative_to(ROOT))):assert sha(ROOT/name)==proof['reviewed_inputs'][name]
 library=c.unique(native,'libinfinitycastremux.so');assert sha(library)==proof['new_library_sha256']
 original=c.obtain(request['baseline'],'cast504-android-baseline');apk=c.unique(original,'Infinity-2103504-Combined-Original-Signer.apk');assert sha(apk)==BASE
 WORK.mkdir();fixtures=WORK/'fixtures';fixtures.mkdir()
 # Public synthetic media, generated in CI. No owner media, credentials or data.
 video=['ffmpeg','-nostdin','-v','error','-y','-f','lavfi','-i','testsrc2=size=320x180:rate=24']
 audio='aevalsrc=0.1*sin(2*PI*440*t)|0.1*sin(2*PI*550*t)|0.1*sin(2*PI*660*t)|0.05*sin(2*PI*80*t)|0.1*sin(2*PI*770*t)|if(lt(mod(t\\,0.17)\\,0.002)\\,0.7\\,0.1*sin(2*PI*880*t)):s=48000:c=5.1'
 run(video+['-f','lavfi','-i',audio,'-t','16','-c:v','libx264','-preset','ultrafast','-g','48','-bf','2','-pix_fmt','yuv420p','-c:a','eac3','-b:a','448k',fixtures/'transients51.mkv'])
 run(['ffmpeg','-nostdin','-v','error','-y','-i',fixtures/'transients51.mkv','-t','6.16','-c:v','copy','-c:a','eac3','-ar','32000','-b:a','384k',fixtures/'32000.mkv'])
 run(['ffmpeg','-nostdin','-v','error','-y','-i',fixtures/'transients51.mkv','-t','12.33','-c:v','copy','-c:a','eac3','-ar','44100','-b:a','448k',fixtures/'44100-odd.mkv'])
 run(video+['-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','4','-c:v','libx265','-pix_fmt','yuv420p10le','-preset','ultrafast','-x265-params','level-idc=5.1:high-tier=0:open-gop=0:pools=1:frame-threads=1:log-level=error:keyint=48:min-keyint=48','-c:a','eac3',fixtures/'main10-eac3.mkv'])
 sdk=Path(os.environ['ANDROID_HOME']);bt=sdk/'build-tools/35.0.0';android=sdk/'platforms/android-35/android.jar'
 stub=WORK/'stubs/com/projectinfinity/kodi';stub.mkdir(parents=True)
 (stub/'InfinityCastRelay.java').write_text('''package com.projectinfinity.kodi; import java.net.*; final class InfinityCastRelay {interface Ready{void ready(InfinityCastRelay r,String mime,String failure);}static InfinityCastRelay start(InetAddress a,InfinityCastSource s,Ready r){throw new AssertionError("compile-only");}static boolean busy(){throw new AssertionError();}String address(){throw new AssertionError();}long durationMs(){throw new AssertionError();}void closeWhenRetired(Runnable r){throw new AssertionError();}void close(){throw new AssertionError();}}''')
 (stub/'InfinityCastSource.java').write_text('package com.projectinfinity.kodi; final class InfinityCastSource {static InfinityCastSource parse(String s){throw new AssertionError("compile-only");}}')
 (stub/'InfinityCastRemuxNative.java').write_text('package com.projectinfinity.kodi; final class InfinityCastRemuxNative {static int active(){throw new AssertionError("compile-only");}}')
 stubclasses=WORK/'stubclasses';stubclasses.mkdir();classes=WORK/'classes';classes.mkdir()
 boot=os.pathsep.join(map(str,[android,bt/'core-lambda-stubs.jar']))
 run(['javac','-source','8','-target','8','-bootclasspath',boot,'-d',stubclasses,*stub.glob('*.java')])
 run(['javac','-source','8','-target','8','-bootclasspath',boot,'-classpath',stubclasses,'-d',classes,*sorted((HERE/'tests/android').glob('*.java'))])
 jar=WORK/'probe.jar';stubjar=WORK/'stubs.jar'
 for target,folder in ((jar,classes),(stubjar,stubclasses)):
  with ZipFile(target,'w',ZIP_DEFLATED) as z:
   for p in folder.rglob('*.class'):z.write(p,p.relative_to(folder))
 dex=WORK/'dex';dex.mkdir()
 run(['java','-cp',bt/'lib/d8.jar','com.android.tools.r8.D8','--min-api','30','--lib',android,'--classpath',stubjar,'--output',dex,jar])
 # Verify compiler stubs are absent from the shipped test DEX.
 sys.path.insert(0,str(ROOT/'repairs/infinity-movies-continue-cast-2103486-20261112/cast'))
 from dex_contract import Dex,class_contract
 original_classes={}
 with ZipFile(apk) as z:
  for name in z.namelist():
   if re.fullmatch(r'classes\d*\.dex',name):original_classes.update(Dex(z.read(name)).classes)
 for p in stubclasses.rglob('*.class'):
  name,contract=class_contract(p.read_bytes());assert name in original_classes,name
  assert {(n,d) for n,d in contract['methods'] if n not in ('<init>','<clinit>')}<=set(original_classes[name]['methods']),name+' API stub mismatch'
 for p in dex.glob('*.dex'):
  assert set(Dex(p.read_bytes()).classes).isdisjoint(original_classes),'Probe class shadowed production DEX'
  assert not any(n in Dex(p.read_bytes()).classes for n in ('Lcom/projectinfinity/kodi/InfinityCastRelay;','Lcom/projectinfinity/kodi/InfinityCastSource;','Lcom/projectinfinity/kodi/InfinityCastRemuxNative;'))
 manifest=WORK/'AndroidManifest.xml';manifest.write_text('''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.projectinfinity.castqa" android:versionCode="1" android:versionName="CI-only"><uses-sdk android:minSdkVersion="30" android:targetSdkVersion="35"/><uses-permission android:name="android.permission.INTERNET"/><uses-permission android:name="android.permission.ACCESS_NETWORK_STATE"/><application android:extractNativeLibs="true" android:label="Cast AAC CI only" android:theme="@android:style/Theme.Material.NoActionBar" android:usesCleartextTraffic="true"><activity android:name="com.projectinfinity.kodi.InfinityCastProbeActivity" android:exported="true"/></application></manifest>''')
 shell=WORK/'shell.apk';run([bt/'aapt2','link','--manifest',manifest,'-I',android,'-o',shell])
 ndk=sdk/'ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin';loader=WORK/'libinfinitycastqaloader.so'
 run([ndk/'aarch64-linux-android21-clang++','-shared','-fPIC',HERE/'tests/android/loader.cpp','-ldl','-Wl,-z,max-page-size=16384','-o',loader])
 unsigned=WORK/'CI-ONLY-NOT-OWNER-INSTALLER.apk'
 with ZipFile(unsigned,'w',ZIP_DEFLATED) as out,ZipFile(shell) as skeleton,ZipFile(apk) as baseline:
  for n in skeleton.namelist():
   if n!='resources.arsc':out.writestr(n,skeleton.read(n))
  indices=[]
  for n in baseline.namelist():
   if re.fullmatch(r'classes\d*\.dex',n):indices.append(int(re.search(r'\d+',n).group()) if re.search(r'\d+',n) else 1)
   if re.fullmatch(r'classes\d*\.dex',n) or n=='resources.arsc' or n.startswith('res/') or (n.startswith('lib/arm64-v8a/') and n.endswith('.so') and not n.endswith('/libinfinitycastremux.so')):out.writestr(n,baseline.read(n),compress_type=ZIP_STORED if n=='resources.arsc' else ZIP_DEFLATED)
  for i,p in enumerate(sorted(dex.glob('*.dex')),max(indices)+1):out.write(p,'classes'+str(i)+'.dex')
  out.write(loader,'lib/arm64-v8a/libinfinitycastqaloader.so');out.write(library,'lib/arm64-v8a/libinfinitycastremux.so')
  for p in fixtures.glob('*.mkv'):out.write(p,'assets/cast-fixtures/'+p.name)
 with ZipFile(unsigned) as z:assert z.getinfo('resources.arsc').compress_type==ZIP_STORED,'ANDROID_R_REQUIRES_STORED_RESOURCE_TABLE'
 aligned=WORK/'aligned.apk';run([bt/'zipalign','-p','-f','4',unsigned,aligned])
 # Ephemeral key is for this separate CI test package only. Never used by owner releases.
 key=WORK/'CI-ONLY.keystore';run(['keytool','-genkeypair','-alias','CI-only','-keyalg','RSA','-keystore',key,'-storepass','android','-keypass','android','-dname','CN=Disposable Cast CI','-validity','2'])
 run([bt/'apksigner','sign','--ks',key,'--ks-key-alias','CI-only','--ks-pass','pass:android','--key-pass','pass:android','--out',WORK/'CI-ONLY.apk',aligned])
 run([bt/'zipalign','-c','4',WORK/'CI-ONLY.apk'],stdout=subprocess.DEVNULL)
 (WORK/'BUILD.json').write_text(json.dumps({'status':'CI_ONLY_SEPARATE_PACKAGE_READY','original_signed504_sha256':BASE,'native_library_sha256':sha(library),'native_artifact':request['native'],'source':os.environ['GITHUB_SHA'],'baseline_DEX_recompiled':False,'owner_APK_built':False},indent=2)+'\n')
 print('CI_ONLY_ACTUAL504_DEX_AND_ENGINE_REUSED_NEW_CAST_JNI_NO_OWNER_APK')
if __name__=='__main__':main()
