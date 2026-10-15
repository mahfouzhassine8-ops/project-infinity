#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, zipfile
from pathlib import Path
VERSION=2103210
NAME='1.0.9-Cobra-Media-Library-Health-RC1'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
NATIVE='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'
LIB='lib/arm64-v8a/libkodi.so'
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def sha(p):return sha_bytes(Path(p).read_bytes())
def require(v,m):
 if not v:raise RuntimeError(m)
def main():
 p=argparse.ArgumentParser();p.add_argument('--final',type=Path,required=True);p.add_argument('--audit',type=Path,required=True);p.add_argument('--base',type=Path,required=True);a=p.parse_args()
 require(a.final.is_file(),'Final APK missing');report=json.loads(a.audit.read_text())
 require(report.get('version_code')==VERSION and report.get('version_name')==NAME,'Successor identity mismatch')
 require(report.get('signer_certificate_sha256')==CERT,'Permanent signer changed');require(report.get('apk_sha256')==sha(a.final),'APK audit hash mismatch')
 with zipfile.ZipFile(a.final) as z,zipfile.ZipFile(a.base) as base:
  require(sha_bytes(z.read(LIB))==NATIVE,'2103209 Python/GIL native engine changed')
  for name in base.namelist():
   if name.startswith('lib/') and not name.endswith('/') and name!=LIB:require(z.read(name)==base.read(name),'Non-target native library changed: '+name)
   if name.startswith(('assets/','res/')) or name=='resources.arsc':require(z.read(name)==base.read(name),'Protected resource/asset changed: '+name)
  dex=b''.join(z.read(n) for n in z.namelist() if re.fullmatch(r'classes\d*\.dex',n))
  for token in (b'script.kodihealthcenter',b'Kodi Health Center',b'Continue Watching',b'cobra-vod-art:'):
   require(token in dex,'Successor UI contract missing: '+repr(token))
 scope=json.loads(Path('audit210/scope.json').read_text());require(scope.get('live_tv_source_untouched') is True,'Live TV source gate missing')
 out={'build':VERSION,'version_name':NAME,'apk_sha256':sha(a.final),'signer':CERT,'native_engine_sha256':NATIVE,'native_engine_rebuilt':False,'live_tv_source_untouched':True,'health_center_addon':'script.kodihealthcenter','physical_device_verified':False,'status':'TEST CANDIDATE'}
 Path('audit210/final-verification.json').write_text(json.dumps(out,indent=2)+'\n');Path('signed210/ACCEPTANCE.json').write_text(json.dumps(out,indent=2)+'\n')
 print('PASS: 2103210 native engine, resources, signer and Live TV protection verified')
if __name__=='__main__':main()
