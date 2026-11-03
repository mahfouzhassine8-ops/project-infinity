"""Selected actual-view/call-policy fixtures, reusing pinned installed host tools."""
import argparse,json,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
H=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--owner',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--method');a=p.parse_args();a.out.mkdir(parents=True)
receipt=Path('/tmp/infinity-external-host/target/surefire-reports/TEST-com.projectinfinity.kodi.ExternalVideoIntentPolicyTest.xml')
props={n.attrib['name']:n.attrib['value'] for n in ET.parse(receipt).findall('.//property')}
paths=[v for v in props['java.class.path'].split(':') if v.startswith('/home/agent/.m2/') and v.endswith('.jar')]
paths += [str(p) for p in Path('/tmp/infinity-external-host/android-test-libs').glob('*.jar')]
paths.insert(0,str(a.owner/'feature.jar'));assert all(Path(p).is_file() for p in paths)
cp=':'.join(paths);classes=a.out/'classes';classes.mkdir()
subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-cp',cp,'-d',str(classes),str(H/'PreviewFullscreenDisplayTest.java')],check=True)
runner=H/'PreviewFullscreenDisplayTest.java'
entry=['com.projectinfinity.kodi.PreviewFullscreenDisplayTest']
if a.method:
 source=a.out/'OneMethod.java';source.write_text('import org.junit.runner.*; public class OneMethod { public static void main(String[] a) throws Exception { Result r=new JUnitCore().run(Request.method(Class.forName(a[0]),a[1])); for(Object f:r.getFailures())System.out.println(f); System.out.println("Tests run: "+r.getRunCount()+", failures: "+r.getFailureCount()); System.exit(r.wasSuccessful()?0:1); }}')
 subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-cp',str(classes)+':'+cp,'-d',str(classes),str(source)],check=True)
 entry=['OneMethod','com.projectinfinity.kodi.PreviewFullscreenDisplayTest',a.method]
else:entry=['org.junit.runner.JUnitCore']+entry
r=subprocess.run(['java','--add-opens','java.base/sun.nio.ch=ALL-UNNAMED','-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2','-Dpreview.render.out='+str(a.out/'renders'),'-cp',str(classes)+':'+cp]+entry,text=True,capture_output=True)
(a.out/'OUTPUT.txt').write_text(r.stdout+r.stderr);print(r.stdout+r.stderr)
assert r.returncode==0
(a.out/'HOST-RESULT.json').write_text(json.dumps(dict(status='PASS',tests=1 if a.method else 15,selected=a.method or 'all selected fullscreen/display fixtures',runtime='Robolectric API35 actual Activity/View input and native Canvas; decoder terminal spy, not actual media decoding'),indent=2)+'\n')
