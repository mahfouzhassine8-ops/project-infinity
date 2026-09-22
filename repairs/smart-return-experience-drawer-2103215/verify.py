#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re,zipfile
from pathlib import Path

VERSION=2103215
NAME='1.0.9-Cobra-Smart-Return-Experience-Drawer-RC1'
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
 require(report.get('version_code')==VERSION and report.get('version_name')==NAME,'2103215 identity mismatch')
 require(report.get('signer_certificate_sha256')==CERT,'Permanent signer changed')
 require(report.get('apk_sha256')==sha(a.final),'APK audit hash mismatch')
 with zipfile.ZipFile(a.final) as apk,zipfile.ZipFile(a.base) as base:
  require(sha_bytes(apk.read(LIB))==NATIVE,'2103209 Python/GIL native engine changed')
  for name in base.namelist():
   if name.startswith('lib/') and not name.endswith('/') and name!=LIB:require(apk.read(name)==base.read(name),'Non-target native changed: '+name)
   if name.startswith(('assets/','res/')) or name=='resources.arsc':require(apk.read(name)==base.read(name),'Protected asset/resource changed: '+name)
  dex=b''.join(apk.read(n) for n in apk.namelist() if re.fullmatch(r'classes\d*\.dex',n))
  for token in (
      b'Smart Return  ',b'cobra_smart_return',b'infinity_cobra_live',
      b'cobra_settings_drawer_header',b'Open Cobra navigation drawer',
      b'Play Next Episode',b'Resume Episode',b'LIVE TV AMBIENT BLUE',
      b'Infinity Health Center',b'More Like This'):
   require(token in dex,'2103215 final DEX contract missing: '+repr(token))
  for forbidden in (b'cobra_settings_return',b'Return to previous Cobra screen'):
   require(forbidden not in dex,'Obsolete inline Settings back survived: '+repr(forbidden))
  require(b'infinity_launch_kodi_health_center' not in dex,'Obsolete Kodi Health bridge returned')

 scope=json.loads(Path('audit215/scope.json').read_text())
 for key in ('smart_return_default_on','smart_return_full_settings_row_removed','settings_inline_back_removed',
             'settings_top_left_drawer','locked_2103214_media_unchanged','live_tv_blue_ambient_unchanged',
             'health_center_unchanged','playback_unchanged','providers_unchanged'):
  require(scope.get(key) is True,'2103215 preservation gate missing: '+key)
 require(scope.get('smart_return_location')=='Cobra Experience options','Wrong Smart Return location')
 require(scope.get('video_recolored') is False,'Video recoloring forbidden')

 out={
  'build':VERSION,'version_name':NAME,'apk_sha256':sha(a.final),'signer':CERT,
  'native_engine_sha256':NATIVE,'native_engine_rebuilt':False,'native_engine_reused_from_2103209':True,
  'smart_return_default_on':True,'smart_return_location':'Cobra Experience options',
  'settings_inline_back_removed':True,'settings_top_left_drawer':True,
  'locked_2103214_media_unchanged':True,'live_tv_blue_ambient_unchanged':True,
  'health_center_unchanged':True,'playback_unchanged':True,'providers_unchanged':True,
  'physical_device_verified':False,'status':'TEST CANDIDATE'
 }
 Path('audit215/final-verification.json').write_text(json.dumps(out,indent=2)+'\n')
 Path('signed215/ACCEPTANCE.json').write_text(json.dumps(out,indent=2)+'\n')
 print('PASS: 2103215 Experience Smart Return + Settings drawer navigation verified')
if __name__=='__main__':main()
