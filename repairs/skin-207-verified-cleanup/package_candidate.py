#!/usr/bin/env python3
"""Skin 208 test candidate: remove desktop.ini only; preserve every UI payload."""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile

PARENT='fdf7ea2b6e4409735f19718b0e16bf2c965a596f2578cd5f513d564985559ad0'
ROLLBACK='4238c9eaf341d921b319fd421bae5c47e3ed51925bed63033a558ae898787b47'
REMOVE='skin.infinity.diggz/desktop.ini'
ADDON='skin.infinity.diggz/addon.xml'
HERE=Path(__file__).resolve().parent

def sha(data):return hashlib.sha256(data).hexdigest()
def compressed(path,info):
    with path.open('rb') as f:
        f.seek(info.header_offset);header=f.read(30)
        if header[:4]!=b'PK\x03\x04':raise ValueError('Bad local ZIP header')
        n,e=struct.unpack_from('<HH',header,26);f.seek(n+e,1)
        return f.read(info.compress_size)

def build(parent,rollback,out):
    assert sha(parent.read_bytes())==PARENT,'Wrong exact skin 207'
    assert sha(rollback.read_bytes())==ROLLBACK,'Wrong skin 204 rollback'
    out.mkdir(parents=True,exist_ok=True)
    candidate=out/'skin.infinity.diggz-1.0.5.208-Verified-Packaging-Cleanup-RC1.zip'
    with zipfile.ZipFile(parent) as a:
        assert a.testzip() is None and len(a.namelist())==len(set(a.namelist()))
        assert a.read(REMOVE)==b'[ViewState]\r\nMode=\r\nVid=\r\nFolderType=Generic\r\n'
        old=a.read(ADDON);identity=ET.fromstring(old)
        assert identity.get('id')=='skin.infinity.diggz' and identity.get('version')=='1.0.5.207'
        new=old.replace(b'version="1.0.5.207"',b'version="1.0.5.208"')
        assert old.count(b'version="1.0.5.207"')==1
        source_delta=HERE.parent/'infinity-ui-stabilization-2103365/skin-delta'
        for p in source_delta.rglob('*'):
            if p.is_file():assert a.read('skin.infinity.diggz/'+p.relative_to(source_delta).as_posix())==p.read_bytes()
    shutil.copyfile(parent,candidate)
    subprocess.run(['zip','-q','-d',str(candidate.resolve()),REMOVE],check=True)
    with tempfile.TemporaryDirectory(prefix='infinity-skin-cleanup-') as temp:
        p=Path(temp)/ADDON;p.parent.mkdir(parents=True);p.write_bytes(new)
        p.chmod(0o644);os.utime(p,(1791763200,1791763200))
        subprocess.run(['zip','-q','-X','-9',str(candidate.resolve()),ADDON],cwd=temp,env=dict(os.environ,TZ='UTC'),check=True)
    with zipfile.ZipFile(parent) as a,zipfile.ZipFile(candidate) as b:
        assert b.testzip() is None and len(b.namelist())==len(set(b.namelist()))
        assert set(a.namelist())-set(b.namelist())=={REMOVE}
        assert not (set(b.namelist())-set(a.namelist()))
        changed=[n for n in b.namelist() if a.read(n)!=b.read(n)]
        assert changed==[ADDON]
        preserved=[n for n in b.namelist() if n!=ADDON]
        for n in preserved:
            assert a.read(n)==b.read(n),n
            assert compressed(parent,a.getinfo(n))==compressed(candidate,b.getinfo(n)),n
        xml=0
        for n in b.namelist():
            if n.endswith('.xml'):ET.fromstring(b.read(n));xml+=1
        final=ET.fromstring(b.read(ADDON));assert final.get('id')=='skin.infinity.diggz' and final.get('version')=='1.0.5.208'
        assert ET.tostring(identity.find('requires'))==ET.tostring(final.find('requires'))
        payload_inventory={n:sha(b.read(n)) for n in b.namelist() if not n.endswith('/')}
    (out/'skin-addon-metadata.patch').write_text(''.join(difflib.unified_diff(old.decode().splitlines(True),new.decode().splitlines(True),'207/addon.xml','208/addon.xml')))
    report={'parent_version':'1.0.5.207','parent_sha256':PARENT,'prior_parent_rollback_204_sha256':ROLLBACK,
            'immediate_candidate_rollback':'Exact original skin 1.0.5.207',
            'file':candidate.name,'sha256':sha(candidate.read_bytes()),'version':'1.0.5.208',
            'removed':[REMOVE],'modified':[ADDON],'modification':'Release version only',
            'preserved_payload_entries':len(preserved),'preserved_compressed_entries':len(preserved),
            'all_xml_documents_parsed':xml,'dependency_manifest_unchanged':True,
            'parent_bytes':parent.stat().st_size,'candidate_bytes':candidate.stat().st_size,
            'bytes_saved':parent.stat().st_size-candidate.stat().st_size,
            'removed_file_payload_bytes':46,'device_tested':False,'locked':False,'production_promoted':False,
            'source_parent_commit':'46ff3dbb76216b5e12f8a884e8cf0e6457efaea9'}
    (out/'SKIN-PRESERVATION.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'SKIN-CANDIDATE-FILES.json').write_text(json.dumps(payload_inventory,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ['parent','rollback','out']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();build(a.parent,a.rollback,a.out)
