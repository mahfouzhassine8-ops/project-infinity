from pathlib import Path
import base64,hashlib,io,tarfile
folder=Path(__file__).resolve().parent
raw=base64.b64decode(''.join((folder/f'payload.{i:02d}.b64').read_text().strip() for i in range(4)),validate=True)
assert hashlib.sha256(raw).hexdigest()=='df30f27c3d8be9857a2e9a7f92471eac83cc7cf022a05b394211c1652eee42ad','Source payload mismatch'
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:xz') as archive:
    for member in archive.getmembers():
        assert member.isfile() and member.name.startswith('repairs/infinity-ambient-surface-2103284/') and '..' not in Path(member.name).parts,member.name
    archive.extractall('.',filter='data')
# Test-harness-only correction: inherited staging assigns its own `here`.
# Isolate that script's globals so our additional test is copied from this repair.
stage=folder/'stage.py'
source=stage.read_text()
before="exec(compile(source,filename,'exec'))"
after="exec(compile(source,filename,'exec'), {'__name__':'__main__','__file__':str(Path('repairs/remaining-repair-2103281',filename))})"
assert source.count(before)==1,'Staging scope anchor mismatch'
stage.write_text(source.replace(before,after,1))
print('Exact tested production payload verified; inherited test staging globals isolated')
