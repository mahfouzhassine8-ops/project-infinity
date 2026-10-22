"""Disposable actual-observer reproduction of Android O_TMPFILE EACCES."""
import os,sys,tempfile,types,json
from pathlib import Path
from zipfile import ZipFile
native,apk,mode=Path(sys.argv[1]),Path(sys.argv[2]),sys.argv[3]
root=Path(tempfile.mkdtemp());executable=root/'logcat';executable.write_text('fixture')
raw=(native/'xbmc/interfaces/python/InfinityPythonPersistenceSource.h').read_text();source=raw.split('R"infinity_source(',1)[1].rsplit(')infinity_source"',1)[0]
ns={'__name__':'actual_observer_fixture'};exec(compile(source,'actual_observer.py','exec'),ns)
original=os.open
def android_open(path,flags,*args,**kwargs):
 if hasattr(os,'O_TMPFILE') and flags&os.O_TMPFILE==os.O_TMPFILE:raise PermissionError(13,'Android emulated storage rejects unnamed temporary files')
 return original(path,flags,*args,**kwargs)
os.open=android_open
errors=[]
# Capture initialization is performed before mutation observation to avoid
# unrelated interpreter bootstrap I/O in the test fixture.
with ZipFile(apk) as z:diagnostics=z.read('assets/addons/script.kodihealthcenter/khc_diagnostics.py')
mod=types.ModuleType('khc_diagnostics');sys.modules[mod.__name__]=mod;exec(compile(diagnostics,'khc_diagnostics.py','exec'),mod.__dict__)
if mode=='baseline':
 with ZipFile(apk) as z:code=z.read('assets/addons/script.kodihealthcenter/khc_android.py')
else:code=(Path(__file__).parent/'overlay/script.kodihealthcenter/khc_android.py').read_bytes()
module=types.ModuleType('khc_android');exec(compile(code,'khc_android.py','exec'),module.__dict__)
observer=ns['Observer'](lambda *a:errors.append(a),lambda *a:None,host_probe=True)
def runner(command,stdout,stderr,**kw):
 stdout.write(b'fixture crash-buffer record\n');stdout.flush();return types.SimpleNamespace(returncode=0)
result=module.collect_logcat(root,executable=str(executable),runner=runner)
print(json.dumps(dict(write_failure_observed=any(v[0] in ('namespace_open_failed','file_open_for_write_failed') for v in errors),diagnostic_capture_retained=result['status']=='snapshot_collected_not_diagnosed',errors=errors)))
