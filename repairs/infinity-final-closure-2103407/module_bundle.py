"""Build the bounded first-party payload consumed by the compiled native verifier.

This is a build tool, never shipped as an application entry. It neither signs
with a substitute key nor changes installed code or user data.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import stat
import subprocess
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT=Path(__file__).parent
CC='script.infinity.commandcenter'
IDS=(CC,'script.infinity.rails','script.infinity.uirepair','script.infinity.watchedbridge')
MANIFEST='INFINITY-MODULES.v1'
CAPABILITIES=('checkpoint-v1','dialog-reflow-v1','first-party-modules-v1','title-actions-v1')
REQUIRED=('addon.xml','checkpoint_runtime.py','common.py','context.py','default.py',
          'module_contract.py','persistence_participant.py','plugin.py','service.py')
FILE_LIMIT=256
FILE_BYTES=4*1024*1024
TOTAL_BYTES=32*1024*1024
PAYLOAD_BYTES=128*1024


def safe(path):
    parts=path.split('/')
    return (len(path)<=240 and re.fullmatch(r'[A-Za-z0-9/._-]+',path) is not None and
            len(parts)>=2 and parts[0] in IDS and not any(p in ('','.','..') for p in parts)
            and 'cobra' not in path.lower())


def source_files(root):
    root=Path(root).absolute()
    if root.is_symlink() or root.resolve()!=root:raise ValueError('Canonical source root required')
    if {p.name for p in root.iterdir()}!=set(IDS):raise ValueError('Exactly four owned code directories required')
    files={};total=0
    for p in sorted(root.rglob('*')):
        relative=p.relative_to(root).as_posix()
        mode=p.lstat().st_mode
        if stat.S_ISLNK(mode):raise ValueError('Linked code member')
        if stat.S_ISDIR(mode):continue
        if not stat.S_ISREG(mode) or not safe(relative):raise ValueError('Unsafe code member')
        if relative in (CC+'/'+MANIFEST,CC+'/'+MANIFEST+'.sig'):continue
        if p.suffix.lower() in ('.pyc','.pyo','.so','.dex','.jar') or '__pycache__' in p.parts:
            raise ValueError('Only reviewed source and resources may be packaged')
        raw=p.read_bytes()
        total+=len(raw)
        if len(raw)>FILE_BYTES or total>TOTAL_BYTES:raise ValueError('Source byte budget exceeded')
        files[relative]=raw
        if len(files)>FILE_LIMIT:raise ValueError('Source file budget exceeded')
    for name in REQUIRED:
        if CC+'/'+name not in files:raise ValueError('Missing mandatory controller source: '+name)
    return files


def baseline_inventory():
    plan=json.loads((ROOT/'FIRSTPARTY-COMPOSITION-PLAN.json').read_text())
    if plan['baseline_commit']!='0e8739d2d0e1be0ab8f127519b526556426fb160':
        raise ValueError('Exact signed407 baseline required')
    rows={aid+'/'+path:digest for aid,item in plan['plan'].items()
          for path,digest in item['signed407_all_file_preimages'].items()}
    if set(plan['plan'])!=set(IDS) or len(rows)>FILE_LIMIT or any(not safe(n) for n in rows):
        raise ValueError('Unsafe baseline inventory')
    return ('INFINITY-INSTALL-BASELINE/1\nsource\t'+plan['baseline_commit']+'\n'+
            ''.join('file\t'+digest+'\t'+name+'\n' for name,digest in sorted(rows.items()))).encode('ascii')


def build(root,extra=None):
    files=source_files(root)
    for name,raw in (extra or {}).items():
        if not safe(name) or (name in files and files[name]!=raw):raise ValueError('Metadata generation differs')
        files[name]=raw
    if len(files)>FILE_LIMIT or sum(map(len,files.values()))>TOTAL_BYTES or any(len(v)>FILE_BYTES for v in files.values()):
        raise ValueError('Source budget exceeded')
    entries=[]
    plan=json.loads((ROOT/'FIRSTPARTY-COMPOSITION-PLAN.json').read_text())['plan']
    version=None
    for aid in IDS:
        node=ET.fromstring(files[aid+'/addon.xml'])
        if node.get('id')!=aid:raise ValueError('Wrong registered addon identity')
        if aid==CC:version=node.get('version','')
        if node.findtext("extension[@point='xbmc.addon.metadata']/reuselanguageinvoker")!='false':
            raise ValueError('Fresh first-party invoker contract required')
        expected={aid+'/'+name for name in plan[aid]['entries']}
        registered={aid+'/'+n.get('library') for n in node.iter() if n.get('library')}
        if not registered<=expected:raise ValueError('Unverified registered entry')
        for path in sorted(expected):
            if path not in files or not path.endswith('.py'):raise ValueError('Entry source missing')
            text=files[path].decode('utf-8')
            if '# INFINITY_AUTHENTICATED_MODULE_BOOTSTRAP_V1' not in text:
                raise ValueError('Native-authenticated entry bootstrap required')
            entries.append((path,'command_center' if path==CC+'/service.py' else 'command_center_client'))
    if not version or len(version)>48 or not re.fullmatch(r'\d+\.\d+\.\d+(?:\.\d+)?',version):
        raise ValueError('Invalid Command Center package version')
    if len(entries)>16:raise ValueError('Entry budget exceeded')
    lines=['INFINITY-MODULES/1','package\t'+version,'protocol\t1']
    lines+=['capability\t'+name for name in CAPABILITIES]
    lines+=['file\t'+hashlib.sha256(raw).hexdigest()+'\t'+path for path,raw in sorted(files.items())]
    lines+=['entry\t'+owner+'\t'+path for path,owner in sorted(entries)]
    payload=('\n'.join(lines)+'\n').encode('ascii')
    if len(payload)>PAYLOAD_BYTES:raise ValueError('Manifest budget exceeded')
    return payload,files


def prepare(root):
    root=Path(root)
    if (root/CC/MANIFEST).exists() or (root/CC/(MANIFEST+'.sig')).exists():
        raise ValueError('Existing manifest generation must not be overwritten')
    baseline=baseline_inventory()
    payload,files=build(root,{CC+'/INSTALL-BASELINE.v1':baseline})
    (root/CC/'INSTALL-BASELINE.v1').write_bytes(baseline)
    (root/CC/MANIFEST).write_bytes(payload)
    return dict(package=ET.fromstring(files[CC+'/addon.xml']).get('version'),protocol=1,
                manifest_sha256=hashlib.sha256(payload).hexdigest(),file_count=len(files),
                total_source_bytes=sum(map(len,files.values())),signed=False,
                user_data_modified=False,APK_produced=False)


def archive(root,out):
    """Call only after the original-key native verification gate has passed."""
    root=Path(root);out=Path(out)
    payload,files=build(root)
    if (root/CC/MANIFEST).read_bytes()!=payload:raise ValueError('Manifest differs from source generation')
    signature=(root/CC/(MANIFEST+'.sig')).read_bytes()
    if len(signature) not in (256,384,512):raise ValueError('Detached RSA signature required')
    key=ROOT/'ORIGINAL-INFINITY-PUBLIC-KEY.pem'
    if hashlib.sha256(key.read_bytes()).hexdigest()!='bc883be4515d328935b1f3e28294bfc0fe0f2614083274db63b1d24d4da172e8':
        raise ValueError('Original immutable public key required')
    verified=subprocess.run(['openssl','dgst','-sha256','-verify',str(key),'-signature',
        str(root/CC/(MANIFEST+'.sig')),str(root/CC/MANIFEST)],capture_output=True)
    if verified.returncode:raise ValueError('Original permanent RSA signature required')
    files[CC+'/'+MANIFEST]=payload;files[CC+'/'+MANIFEST+'.sig']=signature
    out.mkdir(parents=True,exist_ok=False)
    checksums={}
    for aid in IDS:
        version=ET.fromstring(files[aid+'/addon.xml']).get('version')
        target=out/(aid+'-'+version+'-2103409-QA.zip')
        with ZipFile(target,'w',compression=ZIP_DEFLATED,compresslevel=9) as z:
            for name,raw in sorted(files.items()):
                if not name.startswith(aid+'/'):continue
                info=ZipInfo(name,date_time=(2026,10,25,0,0,0))
                info.compress_type=ZIP_DEFLATED;info.external_attr=0o100644<<16
                z.writestr(info,raw)
        checksums[target.name]=hashlib.sha256(target.read_bytes()).hexdigest()
    return checksums


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('root',type=Path)
    args=parser.parse_args();print(json.dumps(prepare(args.root),indent=2))
