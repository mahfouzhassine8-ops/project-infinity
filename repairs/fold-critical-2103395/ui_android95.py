"""Execute the integrated candidate DEX dialog on real Android 17 emulator UI."""
from pathlib import Path
import subprocess,shutil,json,re,zipfile
import components95 as c,java95

def prepare(out,android,tools,dex,second):
 root=out/'ui-test';root.mkdir();src=root/'src';src.mkdir();classes=root/'classes';classes.mkdir()
 stub=java95.STUB.replace('final Activity owner=null; final Dialog dialog=null; final EditText input=null;final int kind=0;', 'Activity owner; Dialog dialog; EditText input; int kind;')
 stub=stub.replace(' static final class Editor {',' static Editor show(Activity a,long t,String i,String h,boolean hidden,boolean search,int k,Sink s){return null;}\n static final class Editor {')
 (src/'InfinityAndroidKeyboard.java').write_text(stub)
 for name in ('Infinity95Test.java','Infinity95TestActivity.java'):shutil.copyfile(c.HERE/name,src/name)
 subprocess.run(['javac','--release','8','-g:none','-cp',str(android),'-d',str(classes)]+[str(p) for p in src.glob('*.java')],check=True)
 testdex=root/'test-dex';testdex.mkdir();produced=[p for p in classes.rglob('*.class') if p.name.startswith('Infinity95Test')]
 subprocess.run([str(tools/'d8'),'--release','--min-api','26','--lib',str(android),'--output',str(testdex)]+[str(p) for p in produced],check=True)
 manifest=root/'AndroidManifest.xml';manifest.write_text('''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.projectinfinity.corrective95test"><uses-sdk android:minSdkVersion="26" android:targetSdkVersion="34"/><application android:theme="@android:style/Theme.Material.Light.NoActionBar" android:debuggable="true" android:label="Infinity Search execution test"><activity android:name="com.projectinfinity.kodi.Infinity95TestActivity" android:exported="true"/></application><instrumentation android:name="com.projectinfinity.kodi.Infinity95Test" android:targetPackage="com.projectinfinity.corrective95test"/></manifest>''')
 unsigned=root/'unsigned.apk';subprocess.run([str(tools/'aapt'),'package','-f','-M',str(manifest),'-I',str(android),'-F',str(unsigned)],check=True)
 with zipfile.ZipFile(unsigned,'a') as z:
  z.write(dex,'classes.dex');z.write(second,'classes2.dex');z.write(testdex/'classes.dex','classes3.dex')
 key=root/'test-only.jks';subprocess.run(['keytool','-genkeypair','-keystore',str(key),'-storepass','android','-keypass','android','-alias','test','-keyalg','RSA','-validity','3','-dname','CN=Disposable Component Test'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 apk=root/'test.apk';subprocess.run([str(tools/'apksigner'),'sign','--ks',str(key),'--ks-pass','pass:android','--out',str(apk),str(unsigned)],check=True)

def run(out,adb,device):
 apk=out/'ui-test/test.apk';subprocess.run([adb,'-s',device,'install','-r',str(apk)],check=True)
 result=subprocess.run([adb,'-s',device,'shell','am','instrument','-w','com.projectinfinity.corrective95test/com.projectinfinity.kodi.Infinity95Test'],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
 (out/'integrated-search-ui.log').write_text(result.stdout);print(result.stdout,flush=True)
 match=re.search(r'INFINITY95_UI_PASS=(\d+)',result.stdout);c.require(result.returncode==0 and match and int(match[1])>=30 and 'INFINITY95_UI_FAILED' not in result.stdout,'actual Android Search UI execution failed')
 for theme in ('light','dark','oled'):
  with (out/('search-'+theme+'.png')).open('wb') as f:subprocess.run([adb,'-s',device,'exec-out','run-as','com.projectinfinity.corrective95test','cat','files/search-'+theme+'.png'],stdout=f,check=True)
 return {'passed':True,'assertions':int(match[1]),'production_dex_used':True,'emulator':True,'api':37,'physical_fold_verified':False,'whole_app_tested':False}
