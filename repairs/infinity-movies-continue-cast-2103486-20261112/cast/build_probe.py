"""CI-only disposable component APK, not an owner installer or release signer."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import hashlib,json,os,re,subprocess,sys
from dex_contract import Dex
HERE=Path(__file__).resolve().parent
WORK=Path(sys.argv[1]).resolve();APK=Path(sys.argv[2]).resolve()
SDK=WORK/'tools';COMPONENT=WORK/'component-reuse86';OUT=WORK/'probe';OUT.mkdir(exist_ok=True)
def run(args):subprocess.run([str(x) for x in args],check=True)
proof=json.loads((COMPONENT/'COMPONENT-RESULT.json').read_text());assert proof['status']=='PASS_COMPONENT_COMPILE_AND_EXISTING_API_LINK_CONTRACT'
with APK.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==proof['baseline_APK_sha256']
classes=OUT/'classes';classes.mkdir(exist_ok=True)
inputs=list(COMPONENT.glob('*/classes.jar'))+list((COMPONENT/'jars').glob('*.jar'))+[COMPONENT/'feature.jar',COMPONENT/'baseline-api-compile-only.jar']
run(['java','com.sun.tools.javac.Main','-source','8','-target','8','-bootclasspath',os.pathsep.join(str(SDK/n) for n in ('android.jar','core-lambda-stubs.jar')),
     '-classpath',os.pathsep.join(str(x) for x in [SDK/'android.jar']+inputs),'-d',classes]+list((HERE/'android').glob('*.java')))
jar=OUT/'probe.jar'
with ZipFile(jar,'w',ZIP_DEFLATED) as z:
 for p in classes.rglob('*.class'):z.writestr(p.relative_to(classes).as_posix(),p.read_bytes())
dex=OUT/'dex';dex.mkdir(exist_ok=True)
run(['java','-cp',SDK/'d8.jar','com.android.tools.r8.D8','--min-api','21','--lib',SDK/'android.jar',
     '--classpath',COMPONENT/'feature.jar','--output',dex,jar])
shipped=set()
for p in (COMPONENT/'dex').glob('*.dex'):shipped.update(Dex(p.read_bytes()).classes)
probe=[Dex(p.read_bytes()) for p in dex.glob('*.dex')]
for value in probe:shipped.update(value.classes)
for value in probe:
 for name in value.types:
  if name.startswith('Lcom/google/android/gms/'):
   assert name in shipped,'CI probe references an SDK name relocated in the actual component: '+name
manifest=OUT/'AndroidManifest.xml';manifest.write_text('''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.projectinfinity.castqa" android:versionCode="1" android:versionName="CI-only">
<uses-sdk android:minSdkVersion="30" android:targetSdkVersion="35"/>
<uses-permission android:name="android.permission.INTERNET"/><uses-permission android:name="android.permission.ACCESS_NETWORK_STATE"/><uses-permission android:name="android.permission.FOREGROUND_SERVICE"/>
<queries><package android:name="com.google.android.gms.policy_cast_dynamite"/></queries>
<application android:label="Cast Component CI" android:theme="@android:style/Theme.Material.NoActionBar" android:usesCleartextTraffic="true">
<meta-data android:name="com.google.android.gms.version" android:value="12451000"/>
<meta-data android:name="com.google.android.gms.cast.framework.OPTIONS_PROVIDER_CLASS_NAME" android:value="com.projectinfinity.kodi.InfinityCastOptions"/>
<activity android:name="com.projectinfinity.kodi.InfinityCastProbeActivity" android:exported="true"><intent-filter><action android:name="android.intent.action.MAIN"/><category android:name="android.intent.category.LAUNCHER"/></intent-filter></activity></application></manifest>''')
shell=OUT/'shell.apk';run([SDK/'aapt2','link','--manifest',manifest,'-I',SDK/'android.jar','-o',shell])
unsigned=OUT/'CI-ONLY-UNSIGNED-NOT-OWNER-INSTALLER.apk'
with ZipFile(unsigned,'w',ZIP_DEFLATED) as out,ZipFile(shell) as stub,ZipFile(APK) as original:
 for n in stub.namelist():
  if n!='resources.arsc':out.writestr(n,stub.read(n))
 for n in original.namelist():
  if re.fullmatch(r'classes\d*\.dex',n) or n=='resources.arsc' or n.startswith('res/'):
   out.writestr(n,original.read(n),compress_type=0 if n=='resources.arsc' else ZIP_DEFLATED)
 next_dex=1+max(int(n[7:-4] or 1) for n in original.namelist() if re.fullmatch(r'classes\d*\.dex',n))
 for p in sorted((COMPONENT/'dex').glob('*.dex'))+sorted(dex.glob('*.dex')):
  out.writestr('classes'+str(next_dex)+'.dex',p.read_bytes());next_dex+=1
 for name in ('resources.apk','RESOURCE-IDENTITY.json'):out.write(COMPONENT/name,'assets/infinity/cast/'+name)
 for p in (COMPONENT/'private-resources').rglob('*'):
  if p.is_file():out.write(p,p.relative_to(COMPONENT/'private-resources').as_posix())
print('CI-only separate-package probe prepared; original installer/signature/data untouched')
with ZipFile(unsigned) as z:assert len(z.namelist())==len(set(z.namelist())), 'Duplicate probe ZIP members refused'
