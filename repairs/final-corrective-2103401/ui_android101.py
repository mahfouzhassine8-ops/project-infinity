"""Execute the integrated candidate DEX dialog on real Android 17 emulator UI."""
from pathlib import Path
import subprocess,shutil,json,re,zipfile
import components101 as c,java95

def prepare(out,android,tools,dex,second):
 root=out/'ui-test';root.mkdir();src=root/'src';src.mkdir();classes=root/'classes';classes.mkdir()
 stub=java95.STUB.replace('final Activity owner=null; final Dialog dialog=null; final EditText input=null;final int kind=0;', 'Activity owner; Dialog dialog; EditText input; int kind;')
 stub=stub.replace(' static final class Editor {',' static Editor show(Activity a,long t,String i,String h,boolean hidden,boolean search,int k,Sink s){return null;}\n static final class Editor {')
 (src/'InfinityAndroidKeyboard.java').write_text(stub)
 for name in ('Infinity101Test.java','Infinity101TestActivity.java'):shutil.copyfile(c.HERE/name,src/name)
 subprocess.run(['javac','--release','8','-g:none','-cp',str(android),'-d',str(classes)]+[str(p) for p in src.glob('*.java')],check=True)
 testdex=root/'test-dex';testdex.mkdir();produced=[p for p in classes.rglob('*.class') if p.name.startswith('Infinity101Test')]
 subprocess.run([str(tools/'d8'),'--release','--min-api','26','--lib',str(android),'--output',str(testdex)]+[str(p) for p in produced],check=True)
 manifest=root/'AndroidManifest.xml';manifest.write_text('''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.projectinfinity.corrective101test"><uses-sdk android:minSdkVersion="26" android:targetSdkVersion="34"/><application android:theme="@android:style/Theme.Material.Light.NoActionBar" android:debuggable="true" android:label="Infinity Search execution test"><activity android:name="com.projectinfinity.kodi.Infinity101TestActivity" android:exported="true"/></application><instrumentation android:name="com.projectinfinity.kodi.Infinity101Test" android:targetPackage="com.projectinfinity.corrective101test"/></manifest>''')
 unsigned=root/'unsigned.apk';subprocess.run([str(tools/'aapt'),'package','-f','-M',str(manifest),'-I',str(android),'-F',str(unsigned)],check=True)
 with zipfile.ZipFile(unsigned,'a') as z:
  z.write(dex,'classes.dex');z.write(second,'classes2.dex');z.write(testdex/'classes.dex','classes3.dex')
 key=root/'test-only.jks';subprocess.run(['keytool','-genkeypair','-keystore',str(key),'-storepass','android','-keypass','android','-alias','test','-keyalg','RSA','-validity','3','-dname','CN=Disposable Component Test'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 apk=root/'test.apk';subprocess.run([str(tools/'apksigner'),'sign','--ks',str(key),'--ks-pass','pass:android','--out',str(apk),str(unsigned)],check=True)

def run(out,adb,device):
 apk=out/'ui-test/test.apk';subprocess.run([adb,'-s',device,'install','-r',str(apk)],check=True)
 scenarios=[('default',None,None),('folded','1080x2520','420'),('unfolded','2160x2160','480'),('landscape','2520x1080','420')]
 results=[]
 try:
  for label,size,density in scenarios:
   if size:
    subprocess.run([adb,'-s',device,'shell','wm','size',size],check=True)
    subprocess.run([adb,'-s',device,'shell','wm','density',density],check=True)
   subprocess.run([adb,'-s',device,'shell','am','force-stop','com.projectinfinity.corrective101test'],check=True)
   result=subprocess.run([adb,'-s',device,'shell','am','instrument','-w','com.projectinfinity.corrective101test/com.projectinfinity.kodi.Infinity101Test'],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
   (out/('integrated-search-ui-'+label+'.log')).write_text(result.stdout);print(result.stdout,flush=True)
   # Preserve captured images even if an assertion fails, then enforce the gate.
   captured=subprocess.check_output([adb,'-s',device,'shell','run-as','com.projectinfinity.corrective101test','ls','files'],text=True).splitlines()
   for filename in captured:
    if re.fullmatch(r'[a-z-]+\.png',filename):
     with (out/(label+'-'+filename)).open('wb') as f:subprocess.run([adb,'-s',device,'exec-out','run-as','com.projectinfinity.corrective101test','cat','files/'+filename],stdout=f,check=True)
   match=re.search(r'INFINITY101_UI_PASS=(\d+)',result.stdout)
   c.require(result.returncode==0 and match and int(match[1])>=200 and 'INFINITY101_UI_FAILED' not in result.stdout,'actual Android Search UI execution failed: '+label)
   results.append(dict(viewport=label,size=size or 'emulator default',density=density or 'emulator default',assertions=int(match[1]),passed=True))
 finally:
  subprocess.run([adb,'-s',device,'shell','wm','size','reset'],check=False)
  subprocess.run([adb,'-s',device,'shell','wm','density','reset'],check=False)
 return {'passed':True,'assertions':sum(r['assertions'] for r in results),'viewports':results,'production_dex_used':True,'emulator':True,'api':37,'physical_fold_verified':False,'whole_app_tested':False}
