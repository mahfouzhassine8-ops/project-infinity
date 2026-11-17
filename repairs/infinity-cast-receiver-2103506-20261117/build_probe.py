"""One selected key-free native/Android hardware inventory. No Kodi/DEX rebuild."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import hashlib,json,os,subprocess,types,sys,re
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'cast506-hardware-work'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def run(*args):subprocess.run(list(map(str,args)),check=True)
def main():
 assert os.environ['GITHUB_ACTIONS']=='true' and os.environ['GITHUB_REPOSITORY']=='mahfouzhassine8-ops/project-infinity' and os.environ['GITHUB_REF']=='refs/heads/work/infinity-2103506-receiver-compatibility-20261117'
 r=json.loads((HERE/'CI-HARDWARE.json').read_bytes())
 for n,h in r['inputs'].items():assert sha(ROOT/n)==h,n
 changed=subprocess.check_output(['git','diff','--name-only',r['source_commit'],os.environ['GITHUB_SHA']],text=True).splitlines();assert changed==[str((HERE/'CI-HARDWARE.json').relative_to(ROOT))]
 helper='repairs/infinity-movies-continue-cast-2103486-20261112/release/common_release.py';raw=subprocess.check_output(['git','show','21616dfa94bf7ca9ec52e40119edf95df5e64073:'+helper]);scope={'__file__':str(ROOT/helper),'__name__':'_retained_reader'};exec(compile(raw,str(ROOT/helper),'exec'),scope);c=types.SimpleNamespace(**scope)
 base=c.unique(c.obtain(r['baseline'],'receiver506-authenticated-baseline'),'Infinity-2103506-Combined-Original-Signer.apk');assert sha(base)==r['baseline']['APK_sha256']
 OUT.mkdir()
 # Retain the reviewed compile/link recipe; configure headers only, never FFmpeg/Kodi.
 recipe='repairs/infinity-cast-mkv-2103494-20261113/build.py'
 raw=subprocess.check_output(['git','show','1529c250:'+recipe]);assert raw==(ROOT/recipe).read_bytes()
 work=OUT/'native-verification';work.mkdir();sys.argv=[str(ROOT/recipe),'native',str(work),str(base)]
 scope={'__file__':str(ROOT/recipe),'__name__':'_retained_cast_native_recipe'};exec(compile(raw,str(ROOT/recipe),'exec'),scope)
 scope.update(BASE=r['baseline']['APK_sha256'],ENGINE='b3d8d96aa55bf0e48f6cf7c995b2c2ebf9c53720b94f2a9e791dd039d64bf1e7',HERE=ROOT/'repairs/infinity-six-repairs-2103502-20261116/cast',ROOT=ROOT);scope['native']()
 sdk=Path(os.environ['ANDROID_HOME']);tool=sdk/'ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readelf'
 def abi(path):
  raw=subprocess.check_output([tool,'--dyn-syms','--wide','-d',path],text=True);exports=[]
  for line in raw.splitlines():
   f=line.split()
   if len(f)>=8 and f[4] in ('GLOBAL','WEAK') and f[5] in ('DEFAULT','PROTECTED') and f[6]!='UND':exports.append(f[7])
  return sorted(exports),sorted(re.findall(r'Shared library: \[([^\]]+)\]',raw))
 assert sha(work/'base-native/libinfinitycastremux.so')=='934bb1dab8d0cfd8ede7fc8cb692aefc887cf34df89b75875d7d81b1d1095a52'
 assert abi(work/'base-native/libinfinitycastremux.so')==abi(work/'native/libinfinitycastremux.so')
 proof=json.loads((work/'CAST-MKV-NATIVE.json').read_bytes());proof.update(status='PASS_CAST506_METADATA_ARM64_ABI',baseline=2103506,scope='New sourcevideo facts only; AAC conversion/header and all nonCast engine unchanged; NOT a video transcode',reviewed_inputs=r['inputs']);(work/'CAST506-METADATA-ARM64.json').write_text(json.dumps(proof,indent=2)+'\n')
 sdk=Path(os.environ['ANDROID_HOME']);bt=sdk/'build-tools/35.0.0';android=sdk/'platforms/android-35/android.jar';classes=OUT/'classes';classes.mkdir();dex=OUT/'dex';dex.mkdir();jar=OUT/'probe.jar'
 run('javac','-source','8','-target','8','-bootclasspath',str(android)+':'+str(bt/'core-lambda-stubs.jar'),'-d',classes,HERE/'android/ReceiverHardwareProbe.java')
 with ZipFile(jar,'w',ZIP_DEFLATED) as z:
  for p in classes.rglob('*.class'):z.write(p,p.relative_to(classes))
 run('java','-cp',bt/'lib/d8.jar','com.android.tools.r8.D8','--min-api','29','--lib',android,'--output',dex,jar)
 ndk=sdk/'ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin';loader=OUT/'libcastreceiverqaloader.so';run(ndk/'aarch64-linux-android21-clang++','-shared','-fPIC','-std=c++17',HERE/'android/loader.cpp','-ldl','-Wl,-z,max-page-size=16384','-o',loader)
 manifest=OUT/'AndroidManifest.xml';manifest.write_text('''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.projectinfinity.castqa.receiver" android:versionCode="1" android:versionName="CI-only"><uses-sdk android:minSdkVersion="29" android:targetSdkVersion="35"/><application android:extractNativeLibs="true" android:label="Cast receiver CI only" android:theme="@android:style/Theme.Material.NoActionBar"><activity android:name="com.projectinfinity.castqa.ReceiverHardwareProbe" android:exported="true"/></application></manifest>''');shell=OUT/'shell.apk';run(bt/'aapt2','link','--manifest',manifest,'-I',android,'-o',shell)
 unsigned=OUT/'CI-ONLY-UNSIGNED.apk';native={}
 with ZipFile(unsigned,'w',ZIP_DEFLATED) as z,ZipFile(shell) as s,ZipFile(base) as baseline:
  for name in s.namelist():z.writestr(name,s.read(name))
  for lib in ('libkodi.so','libc++_shared.so','libshairplay.so'):
   name='lib/arm64-v8a/'+lib;data=baseline.read(name);z.writestr(name,data);native[lib]=hashlib.sha256(data).hexdigest()
  assert native['libkodi.so']=='b3d8d96aa55bf0e48f6cf7c995b2c2ebf9c53720b94f2a9e791dd039d64bf1e7'
  z.write(loader,'lib/arm64-v8a/libcastreceiverqaloader.so');z.write(dex/'classes.dex','classes.dex')
 aligned=OUT/'aligned.apk';run(bt/'zipalign','-p','-f','4',unsigned,aligned);key=OUT/'CI-ONLY.keystore';run('keytool','-genkeypair','-alias','CI-only','-keyalg','RSA','-keystore',key,'-storepass','android','-keypass','android','-dname','CN=Disposable Cast receiver CI','-validity','2');run(bt/'apksigner','sign','--ks',key,'--ks-key-alias','CI-only','--ks-pass','pass:android','--key-pass','pass:android','--out',OUT/'CI-ONLY.apk',aligned)
 (OUT/'BUILD.json').write_text(json.dumps({'status':'SEPARATE_PACKAGE_HARDWARE_INVENTORY_READY','baseline':r['baseline'],'native':native,'source':os.environ['GITHUB_SHA'],'production_DEX_rebuilt':False,'engine_rebuilt':False,'owner_installer':False},indent=2)+'\n')
if __name__=='__main__':main()
