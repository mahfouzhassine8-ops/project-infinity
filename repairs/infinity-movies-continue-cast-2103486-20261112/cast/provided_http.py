"""Compile-only API jars for the HTTP implementation already in signed86.

No OkHttp/Okio implementation is packaged. Actual referenced classes/members
must exist in the immutable baseline DEX or the component audit rejects it.
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
