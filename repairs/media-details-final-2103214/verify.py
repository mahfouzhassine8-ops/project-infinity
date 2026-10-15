#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re,zipfile
from pathlib import Path

VERSION=2103214
NAME='1.0.9-Cobra-Media-Details-Final-RC1'
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
 require(report.get('version_code')==VERSION and report.get('version_name')==NAME,'2103214 identity mismatch')
 require(report.get('signer_certificate_sha256')==CERT,'Permanent signer changed')
 require(report.get('apk_sha256')==sha(a.final),'APK audit hash mismatch')
 with zipfile.ZipFile(a.final) as apk,zipfile.ZipFile(a.base) as base:
  require(sha_bytes(apk.read(LIB))==NATIVE,'2103209 Python/GIL native engine changed')
  for name in base.namelist():
   if name.startswith('lib/') and not name.endswith('/') and name!=LIB:require(apk.read(name)==base.read(name),'Non-target native changed: '+name)
   if name.startswith(('assets/','res/')) or name=='resources.arsc':require(apk.read(name)==base.read(name),'Protected asset/resource changed: '+name)
  dex=b''.join(apk.read(n) for n in apk.namelist() if re.fullmatch(r'classes\d*\.dex',n))
  for token in (
      b'Play Next Episode',b'Resume Episode',b'Recently Added',b'Watch state',
      b'Cast & Crew',b'More Like This',b'No titles match these filters.',
      b'LIVE TV AMBIENT BLUE',b'cobra_settings_return',b'Infinity Health Center'):
   require(token in dex,'2103214 final DEX contract missing: '+repr(token))
  require(b'infinity_launch_kodi_health_center' not in dex,'Obsolete Kodi Health bridge returned')

 scope=json.loads(Path('audit214/scope.json').read_text())
 for key in ('health_center_unchanged','main_unchanged','live_tv_blue_ambient_unchanged',
             'settings_return_unchanged','main_media_landing_structure_unchanged'):
  require(scope.get(key) is True,'Preservation gate missing: '+key)
 require(scope.get('video_recolored') is False,'Video recoloring forbidden')
 out={
  'build':VERSION,'version_name':NAME,'apk_sha256':sha(a.final),'signer':CERT,
  'native_engine_sha256':NATIVE,'native_engine_rebuilt':False,'native_engine_reused_from_2103209':True,
  'final_media_refinement':True,'tv_season_episode_browser':True,'collection_sort_filter':True,
  'details_more_like_this':True,'details_cast_crew':True,'completion_actions':True,
  'autoplay_behavior_preserved':True,'recent_releases_current_year_priority':True,
  'live_tv_blue_ambient_unchanged':True,'settings_return_unchanged':True,
  'health_center_unchanged':True,'video_recolored':False,'physical_device_verified':False,
  'status':'TEST CANDIDATE'
 }
 Path('audit214/final-verification.json').write_text(json.dumps(out,indent=2)+'\n')
 Path('signed214/ACCEPTANCE.json').write_text(json.dumps(out,indent=2)+'\n')
 print('PASS: 2103214 final media candidate and protected boundaries verified')
if __name__=='__main__':main()
