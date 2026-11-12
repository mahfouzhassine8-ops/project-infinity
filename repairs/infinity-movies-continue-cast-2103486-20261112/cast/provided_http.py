"""Pinned official HTTP/Kotlin inputs for private Cast-only runtime definitions.

Cobra owns the already installed HTTP/Kotlin classes. Cast must not call or
replace them. R8 privately relocates these independent dependency definitions;
the final DEX audit rejects original Cobra namespaces and class collisions.
"""
from pathlib import Path
import hashlib,json,urllib.request
def obtain(work):
    lock=Path(__file__).resolve().parents[1]/'research/CAST-PROVIDED-HTTP-APIS.json'
    rows=json.loads(lock.read_text())['artifacts'];folder=Path(work)/'provided-http';folder.mkdir(exist_ok=True)
    result=[]
    for row in rows:
        group,artifact,version=row['coordinate'].split(':');p=folder/row['file']
        if not p.exists():
            with urllib.request.urlopen('https://repo.maven.apache.org/maven2/'+group.replace('.','/')+'/'+artifact+'/'+version+'/'+p.name,timeout=30) as stream:p.write_bytes(stream.read())
        assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'], 'Provided API changed'
        result.append(p)
    return result
