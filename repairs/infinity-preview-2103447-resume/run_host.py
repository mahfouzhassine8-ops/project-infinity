"""New resume-storage tests using the already installed pinned host dependencies."""
import argparse,json,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
H=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--owner',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--boundaries',action='store_true');a=p.parse_args();a.out.mkdir(parents=True)
receipt=Path('/tmp/infinity-external-host/target/surefire-reports/TEST-com.projectinfinity.kodi.ExternalVideoIntentPolicyTest.xml')
props={n.attrib['name']:n.attrib['value'] for n in ET.parse(receipt).findall('.//property')}
paths=[v for v in props['java.class.path'].split(':') if v.startswith('/home/agent/.m2/') and v.endswith('.jar')]
paths += [str(p) for p in Path('/tmp/infinity-external-host/android-test-libs').glob('*.jar')]
paths.insert(0,str(a.owner/'feature.jar'));assert all(Path(p).is_file() for p in paths)
cp=':'.join(paths);classes=a.out/'classes';classes.mkdir()
test='PreviewResumeBoundaryTest' if a.boundaries else 'PreviewResumeTest';count=3 if a.boundaries else 12
subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-cp',cp,'-d',str(classes),str(H/(test+'.java'))],check=True)
r=subprocess.run(['java','--add-opens','java.base/sun.nio.ch=ALL-UNNAMED','-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2','-cp',str(classes)+':'+cp,'org.junit.runner.JUnitCore','com.projectinfinity.kodi.'+test],text=True,capture_output=True)
(a.out/'OUTPUT.txt').write_text(r.stdout+r.stderr);print(r.stdout+r.stderr)
assert r.returncode==0 and f'OK ({count} tests)' in r.stdout
(a.out/'HOST-RESULT.json').write_text(json.dumps(dict(status='PASS',tests=count,runtime='Robolectric API35 private resume SQLite/scheduling; not Android decoding'),indent=2)+'\n')
