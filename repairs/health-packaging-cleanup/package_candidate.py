#!/usr/bin/env python3
"""Packaging-only Health Center 2.5.20 revision; retain all runtime code and version."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import zipfile
import xml.etree.ElementTree as ET

PARENT='24cef2a75ac8e2bb853540bb75db30dbdc714f1c1a84e10fa3fe7919d201317f'
PREFIX='script.kodihealthcenter/'
TEST='tests/test_native_incident_correlation.py'
MANIFEST='KHC_RELEASE.json'

def sha(b):return hashlib.sha256(b).hexdigest()
def compressed(path,info):
    with path.open('rb') as f:
        f.seek(info.header_offset);h=f.read(30);assert h[:4]==b'PK\x03\x04'
        n,e=struct.unpack_from('<HH',h,26);f.seek(n+e,1);return f.read(info.compress_size)

def build(parent,test_source,results,out):
    assert sha(parent.read_bytes())==PARENT,'Wrong exact Health Center parent'
    test=json.loads(results.read_text())
    assert test['tests_run']==82 and test['successful'] and test['failures']==test['errors']==0
    assert len(test['checks'])==82 and all(x['passed'] for x in test['checks']),'Missing/skipped host check'
    out.mkdir(parents=True,exist_ok=True)
    target=out/'Infinity-Health-Center-2.5.20-Packaging-Cleanup-RC1.zip'
    with zipfile.ZipFile(parent) as a:
        assert a.testzip() is None and a.read(PREFIX+TEST)==test_source.read_bytes(),'Host test not retained exactly'
        original_manifest=json.loads(a.read(PREFIX+MANIFEST))
        release=dict(original_manifest);release['files']=dict(release['files']);del release['files'][TEST]
        release['packaging_revision']='Verified Packaging Cleanup RC1'
        release['packaging_parent_sha256']=PARENT
        release['packaging_removed_files']=[TEST]
        release['host_test_preserved_sha256']=sha(test_source.read_bytes())
        release['runtime_source_and_version_unchanged']=True
        metadata=(json.dumps(release,indent=2,sort_keys=True)+'\n').encode()
    shutil.copyfile(parent,target)
    subprocess.run(['zip','-q','-d',str(target.resolve()),PREFIX+TEST],check=True)
    with tempfile.TemporaryDirectory(prefix='infinity-health-package-') as temp:
        p=Path(temp)/PREFIX/MANIFEST;p.parent.mkdir(parents=True);p.write_bytes(metadata)
        p.chmod(0o644);os.utime(p,(1791763200,1791763200))
        subprocess.run(['zip','-q','-X','-9',str(target.resolve()),PREFIX+MANIFEST],cwd=temp,env=dict(os.environ,TZ='UTC'),check=True)
    with zipfile.ZipFile(parent) as a,zipfile.ZipFile(target) as b:
        assert b.testzip() is None and len(b.namelist())==len(set(b.namelist()))
        assert set(a.namelist())-set(b.namelist())=={PREFIX+TEST}
        assert not(set(b.namelist())-set(a.namelist()))
        assert [n for n in b.namelist() if a.read(n)!=b.read(n)]==[PREFIX+MANIFEST]
        protected=[n for n in b.namelist() if n!=PREFIX+MANIFEST]
        for n in protected:
            assert a.read(n)==b.read(n),n
            assert compressed(parent,a.getinfo(n))==compressed(target,b.getinfo(n)),n
        assert set(release['files'])=={n.removeprefix(PREFIX) for n in protected}
        for n,meta in release['files'].items():assert sha(b.read(PREFIX+n))==meta['sha256']
        py=xml=0
        for n in b.namelist():
            if n.endswith('.py'):ast.parse(b.read(n).decode(),filename=n);py+=1
            if n.endswith('.xml'):ET.fromstring(b.read(n));xml+=1
        identity=ET.fromstring(b.read(PREFIX+'addon.xml'))
        assert identity.get('id')=='script.kodihealthcenter' and identity.get('version')=='2.5.20'
    report={'file':target.name,'parent_sha256':PARENT,'sha256':sha(target.read_bytes()),
            'addon_version':'2.5.20','packaging_revision':'RC1','version_unchanged_reason':'No runtime/source/digest-contract change; manual ZIP candidate only',
            'removed':[PREFIX+TEST],'modified':[PREFIX+MANIFEST],'all_runtime_code_byte_identical':True,
            'host_test_preserved_sha256':sha(test_source.read_bytes()),'host_tests':82,'host_failures':0,'host_errors':0,'host_skipped':0,
            'preserved_entries':len(protected),'preserved_compressed_entries':len(protected),
            'parsed_python_files':py,'parsed_xml_files':xml,'manifest_hashes_verified':len(release['files']),
            'parent_bytes':parent.stat().st_size,'candidate_bytes':target.stat().st_size,
            'bytes_saved':parent.stat().st_size-target.stat().st_size,'removed_compressed_payload_bytes':692,
            'physical_install_acceptance':False,'locked':False,'production_promoted':False,
            'rollback':'Exact original Health Center 2.5.20 ZIP; no user data deletion'}
    (out/'HEALTH-PRESERVATION.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2));return report

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ['parent','test-source','results','out']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();build(a.parent,a.test_source,a.results,a.out)
