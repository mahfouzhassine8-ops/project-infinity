"""Pin unmodified public provider/dependency inputs for disposable Android tests.

Nothing here is packaged into Infinity or applied to a user installation.
"""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from provider_contracts import PROOFS

HERE=Path(__file__).resolve().parent
INDEX='https://mirrors.kodi.tv/addons/omega/addons.xml.gz'
CONTEXT='https://raw.githubusercontent.com/deklica/repo.dexe/824cbcaddf0ca88230300805f5b78744b0297eea/zips/context.seren/context.seren-2.2.0.zip'

def sha(raw):return hashlib.sha256(raw).hexdigest()
def fetch(url):
    # Run39935367720/provider-pov lost its input-download network route.
    # Retry only transport/transient HTTP failures before executing the APK.
    # Integrity failures and application/runtime assertions are never retried.
    for attempt in range(1,4):
        try:
            with urllib.request.urlopen(url,timeout=90) as stream:return stream.read()
        except (urllib.error.URLError,TimeoutError) as error:
            if isinstance(error,urllib.error.HTTPError) and error.code not in (408,429,500,502,503,504):
                raise
            print('Input download failed (attempt '+str(attempt)+'/3): '+url+'; '+str(error),flush=True)
            if attempt==3:raise
            time.sleep(2*attempt)
def manifest(raw,aid):
    with ZipFile(io.BytesIO(raw)) as z:
        if len(z.namelist())!=len(set(z.namelist())) or z.testzip():raise RuntimeError('Invalid input archive')
        return ET.fromstring(z.read(aid+'/addon.xml'))

def lock(out):
    index_raw=fetch(INDEX)
    index={a.get('id'):a for a in ET.fromstring(gzip.decompress(index_raw))}
    pending=[(p['addon'],p['url'],p['sha256']) for p in PROOFS]
    pending.append(('context.seren',CONTEXT,None));seen={};rows=[]
    while pending:
        aid,url,expected=pending.pop(0)
        if aid in seen:continue
        raw=fetch(url)
        if expected and sha(raw)!=expected:raise RuntimeError('Pinned distribution changed: '+aid)
        a=manifest(raw,aid)
        if a.get('id')!=aid:raise RuntimeError('Wrong add-on identity')
        seen[aid]=True
        rows.append(dict(addon=aid,version=a.get('version'),url=url,sha256=sha(raw)))
        for dep in a.findall('requires/import'):
            name=dep.get('addon')
            if name.startswith('xbmc.') or dep.get('optional')=='true' or name in seen:continue
            if any(x[0]==name for x in pending):continue
            entry=index.get(name)
            if entry is None:raise RuntimeError('Missing unmodified dependency: '+name)
            version=entry.get('version')
            pending.append((name,'https://mirrors.kodi.tv/addons/omega/'+name+'/'+name+'-'+version+'.zip',None))
    out.write_text(json.dumps(dict(scope='disposable emulator only; no production modifications',
        index=dict(url=INDEX,sha256=sha(index_raw)),archives=rows),indent=2,sort_keys=True)+'\n')

def stage(out):
    if out.exists():raise RuntimeError('Refusing stale fixture inputs')
    out.mkdir(parents=True)
    pins=json.loads((HERE/'ANDROID-INPUT-PINS.json').read_text())
    for row in pins['archives']:
        raw=fetch(row['url'])
        if sha(raw)!=row['sha256']:raise RuntimeError('Android test input drift: '+row['addon'])
        with ZipFile(io.BytesIO(raw)) as z:
            for name in z.namelist():
                p=Path(name)
                if p.is_absolute() or '..' in p.parts or p.parts[0]!=row['addon']:
                    raise RuntimeError('Unsafe fixture member')
                if (z.getinfo(name).external_attr>>16)&0o170000==0o120000:raise RuntimeError('Unexpected fixture symlink')
            z.extractall(out)
    (out/'INPUTS.json').write_text(json.dumps(pins,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('lock','stage'))
    p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    (lock if a.mode=='lock' else stage)(a.out)
