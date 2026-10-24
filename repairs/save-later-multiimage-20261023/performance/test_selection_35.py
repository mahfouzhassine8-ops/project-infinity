"""Exact CC35 admission plus retained34 common native handler behavior."""
import hashlib,importlib.util,json,os,subprocess,sys,tempfile
from pathlib import Path
import selection_native as change
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('retained_selection_fixture',HERE.parent/'universal/test_selection_native.py')
fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
source=Path(os.environ['INFINITY_REFERENCE_NATIVE'])
sha=lambda b:hashlib.sha256(b).hexdigest()
with tempfile.TemporaryDirectory() as temp:
 out=Path(temp)/'overlay';fixture.native.apply(source,out)
 before=(out/change.PATH).read_bytes();updated=change.patch(before)
 assert updated.decode().replace(change.NEW,change.OLD,1).encode()==before
 helper=fixture.native.HELPER.replace(change.OLD,change.NEW,1)
 assert helper in updated.decode()
 body=fixture.method(updated.decode()).replace('std::chrono::steady_clock::now()','testNow')
 for version in ('0.3.5.34','0.3.5.35'):
  shim=fixture.SHIM.replace('version="0.3.5.34"','version="'+version+'"')
  cpp=Path(temp)/(version+'.cpp');cpp.write_text(shim+helper+body+'\n'+fixture.CASES)
  binary=Path(temp)/version
  subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-Wno-unused-parameter',str(cpp),'-o',str(binary)],check=True,timeout=60)
  subprocess.run([str(binary)],check=True,timeout=10)
 report=dict(host='PASS',scope='Actual helper and selection method compiled with controlled native APIs for exact CC34 and CC35',versions=['0.3.5.34','0.3.5.35'],patch_sha256=sha(Path(change.__file__).read_bytes()),test_sha256=sha(Path(__file__).read_bytes()),retained_sha256=sha(before),updated_sha256=sha(updated),android17='NOT RUN',physical_fold='NOT RUN',shutdown='NOT RUN')
 (HERE/'SELECTION-35-HOST.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report))
