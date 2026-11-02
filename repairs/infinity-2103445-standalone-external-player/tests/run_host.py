"""Use the installed pinned Robolectric/JUnit jars; no old application sources."""
import argparse,json,os,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
H=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--owner',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True)
receipt=Path('/tmp/infinity-external-host/target/surefire-reports/TEST-com.projectinfinity.kodi.ExternalVideoIntentPolicyTest.xml')
properties={n.attrib['name']:n.attrib['value'] for n in ET.parse(receipt).findall('.//property')}
paths=[v for v in properties['java.class.path'].split(':') if v.startswith('/home/agent/.m2/') and v.endswith('.jar')]
paths += [str(p) for p in Path('/tmp/infinity-external-host/android-test-libs').glob('*.jar')]
paths.insert(0,str(a.owner/'feature.jar'))
assert paths and all(Path(p).is_file() for p in paths)
classpath=':'.join(paths);out=a.out/'classes';out.mkdir()
subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-cp',classpath,'-d',str(out),str(H/'tests/ExternalPlayerContractTest.java')],check=True)
result=subprocess.run(['java','--add-opens','java.base/sun.nio.ch=ALL-UNNAMED','-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2','-cp',str(out)+':'+classpath,'org.junit.runner.JUnitCore','com.projectinfinity.kodi.ExternalPlayerContractTest'],capture_output=True,text=True)
(a.out/'HOST-OUTPUT.txt').write_text(result.stdout+result.stderr)
print(result.stdout+result.stderr)
assert result.returncode==0 and 'OK (14 tests)' in result.stdout
(a.out/'HOST-RESULT.json').write_text(json.dumps({'status':'PASS','tests':14,'runtime':'Robolectric API35, request/state contracts only','actual_decoding':False},indent=2)+'\n')
