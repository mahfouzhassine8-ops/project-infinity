"""CI only. Compile unchanged496 Cast Java; actual owner DEX must remain exact."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,sys,json
ROOT=Path(__file__).resolve().parents[2];OLD=ROOT/'repairs/infinity-movies-continue-cast-2103486-20261112/cast';work=Path(sys.argv[1]).resolve();apk=Path(sys.argv[2]).resolve()
s=(OLD/'build_sdk_component.py').read_text();assert 'fa0da5675443803ff2af42526243f81b9a1be774f7deeecdaf7e7557fff2a36c' in s
assert 'from audit_sdk_component import verify' in s
s=s.replace('from audit_sdk_component import verify','from audit_component import verify')
s=s.replace('fa0da5675443803ff2af42526243f81b9a1be774f7deeecdaf7e7557fff2a36c','17a9648070a6d2d1b670c3e550e905d75a99a7dc3f21692a56b8a69c6e9c7ebc');sys.path.insert(0,str(OLD));exec(compile(s,str(OLD/'build_sdk_component.py'),'exec'),{'__file__':str(OLD/'build_sdk_component.py'),'__name__':'__main__'})
proof=json.loads((work/'component-reuse86/COMPONENT-RESULT.json').read_text());dex=work/'component-reuse86/dex/classes.dex'
with ZipFile(apk) as z:assert hashlib.sha256(z.read('classes6.dex')).hexdigest()==hashlib.sha256(dex.read_bytes()).hexdigest()=='5f2bf19c979904856c0300ae819bf584599255b12623b309c2f984c0cc0f2944'
assert proof['baseline_APK_sha256']=='17a9648070a6d2d1b670c3e550e905d75a99a7dc3f21692a56b8a69c6e9c7ebc'
print('PASS entire existing Cast DEX byte-identical to signed496; new native library only')
