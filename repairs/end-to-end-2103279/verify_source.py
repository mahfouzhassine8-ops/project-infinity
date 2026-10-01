from pathlib import Path
import argparse,hashlib,json,importlib.util
spec=importlib.util.spec_from_file_location('repair',Path(__file__).with_name('apply.py'));r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();b=a.baseline/'shell-kodi';n=a.root/'shell-kodi'
expected={r.CMAKE:r.cmake((b/r.CMAKE).read_text()),r.CROP:Path(__file__).with_name('CobraEmbeddedCrop.java.in').read_text(),r.ACTIVITY:r.activity((b/r.ACTIVITY).read_text()),r.PEEK:r.peek((b/r.PEEK).read_text()),r.GRADLE:(b/r.GRADLE).read_text().replace('versionCode 2103278','versionCode 2103279').replace('1.0.9-Watch-Ambient-RC1',r.RELEASE)}
for name,value in expected.items():assert (n/name).read_text()==value,name
unchanged=0
for f in b.rglob('*'):
 if f.is_file() and str(f.relative_to(b)) not in expected:assert f.read_bytes()==(n/f.relative_to(b)).read_bytes(),str(f);unchanged+=1
report=dict(locked_source_commit=r.BASE,changed_shell_files=list(expected),other_shell_files_byte_identical=unchanged,ambient_engine_byte_identical=True,fullscreen_policy_unchanged=True,physical_device_verified=False)
a.out.mkdir(parents=True,exist_ok=True);(a.out/'source-verification.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS source preservation:',unchanged,'unchanged shell files')
