"""CI only. Compile only scoped498 Cast metadata/relay changes; audit all immutable APIs."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,sys,json
ROOT=Path(__file__).resolve().parents[2];OLD=ROOT/'repairs/infinity-movies-continue-cast-2103486-20261112/cast';work=Path(sys.argv[1]).resolve();apk=Path(sys.argv[2]).resolve()
s=(OLD/'build_sdk_component.py').read_text();assert 'fa0da5675443803ff2af42526243f81b9a1be774f7deeecdaf7e7557fff2a36c' in s
assert 'from audit_sdk_component import verify' in s
s=s.replace('from audit_sdk_component import verify','from audit_component import verify')
s=s.replace('fa0da5675443803ff2af42526243f81b9a1be774f7deeecdaf7e7557fff2a36c','2fd158bbdd26d47f4204c8c474f15c9ca69cfef00fcecdb62c866b42559d3004');sys.path.insert(0,str(OLD));exec(compile(s,str(OLD/'build_sdk_component.py'),'exec'),{'__file__':str(OLD/'build_sdk_component.py'),'__name__':'__main__'})
