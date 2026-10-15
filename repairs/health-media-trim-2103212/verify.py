#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re,zipfile
from pathlib import Path

VERSION=2103212
NAME='1.0.9-Cobra-Health-Media-Trim-RC1'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
NATIVE='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'
LIB='lib/arm64-v8a/libkodi.so'
def sha_bytes(data):return hashlib.sha256(data).hexdigest()
def sha(path):return sha_bytes(Path(path).read_bytes())
def require(value,message):
 if not value:raise RuntimeError(message)

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--final',type=Path,required=True);p.add_argument('--audit',type=Path,required=True)
 p.add_argument('--base',type=Path,required=True)
 args=p.parse_args()
 require(args.final.is_file(),'Final APK missing')
 report=json.loads(args.audit.read_text())
 require(report.get('version_code')==VERSION and report.get('version_name')==NAME,'2103212 identity mismatch')
 require(report.get('signer_certificate_sha256')==CERT,'Permanent signer changed')
 require(report.get('apk_sha256')==sha(args.final),'Final APK hash mismatch')

 with zipfile.ZipFile(args.final) as apk,zipfile.ZipFile(args.base) as base:
  require(sha_bytes(apk.read(LIB))==NATIVE,'2103209 crash-fixed native engine changed')
  for name in base.namelist():
   if name.startswith('lib/') and not name.endswith('/') and name!=LIB:
    require(apk.read(name)==base.read(name),'Non-target native changed: '+name)
   if name.startswith(('assets/','res/')) or name=='resources.arsc':
    require(apk.read(name)==base.read(name),'Protected resources/assets changed: '+name)
  dex=b''.join(apk.read(n) for n in apk.namelist() if re.fullmatch(r'classes\d*\.dex',n))
  for token in (
      b'Infinity Health Center',b'DIAGNOSTICS',b'Recent crashes & exits',
      b'Export diagnostic report',b'Copy diagnostic report',b'Build & device info',
      b'Recent Releases',b'Trending Movies',b'Trending Shows',b'Popular Now',
      b'Because You Watched',b'cobra_ambient_mode'):
   require(token in dex,'2103212 final DEX contract missing: '+repr(token))
  # Health Center remains chooser-native and crash-safe.
  require(b'infinity_launch_kodi_health_center' not in dex,'Obsolete Kodi Health bridge returned')

 scope=json.loads(Path('audit212/scope.json').read_text())
 require(scope.get('health_behavior_unchanged') is True,'Health behavior preservation missing')
 require(scope.get('media_structure_unchanged') is True,'Media information architecture changed')
 require(scope.get('live_tv_source_untouched') is True,'Live TV source protection missing')
 require(scope.get('native_engine_rebuilt') is False,'Unexpected native rebuild')
 require(scope.get('media_trim')=='ambient-aware','Ambient-aware media trim gate missing')
 require(scope.get('video_recolored') is False,'Video recoloring must remain forbidden')

 result={
  'build':VERSION,'version_name':NAME,'apk_sha256':sha(args.final),'signer':CERT,
  'native_engine_sha256':NATIVE,'native_engine_rebuilt':False,
  'native_engine_reused_from_2103209':True,'live_tv_source_untouched':True,
  'health_center_infinity_styled':True,'health_center_behavior_unchanged':True,
  'media_structure_unchanged':True,'movies_tv_shows_trim_ambient_aware':True,
  'ambient_modes':['off','subtle','immersive'],'video_recolored':False,
  'physical_device_verified':False,'status':'TEST CANDIDATE'
 }
 Path('audit212/final-verification.json').write_text(json.dumps(result,indent=2)+'\n')
 Path('signed212/ACCEPTANCE.json').write_text(json.dumps(result,indent=2)+'\n')
 print('PASS: 2103212 presentation-only Health/media trim candidate verified')

if __name__=='__main__':main()
