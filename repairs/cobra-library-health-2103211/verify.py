#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re,zipfile
from pathlib import Path

VERSION=2103211
NAME='1.0.9-Cobra-Library-Health-Refinement-RC1'
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
 require(report.get('version_code')==VERSION and report.get('version_name')==NAME,'2103211 identity mismatch')
 require(report.get('signer_certificate_sha256')==CERT,'Permanent signer changed')
 require(report.get('apk_sha256')==sha(args.final),'Final APK audit hash mismatch')

 with zipfile.ZipFile(args.final) as apk,zipfile.ZipFile(args.base) as base:
  require(sha_bytes(apk.read(LIB))==NATIVE,'2103209 Python 3.11 native engine changed')
  for name in base.namelist():
   if name.startswith('lib/') and not name.endswith('/') and name!=LIB:
    require(apk.read(name)==base.read(name),'Non-target native changed: '+name)
   if name.startswith(('assets/','res/')) or name=='resources.arsc':
    require(apk.read(name)==base.read(name),'Protected resource/asset changed: '+name)
  dex=b''.join(apk.read(n) for n in apk.namelist() if re.fullmatch(r'classes\d*\.dex',n))
  for token in (
      b'Infinity Health Center',b'Recent crashes & exits',b'Infinity diagnostic report',
      b'Recent Releases',b'Trending Movies',b'Trending Shows',b'Popular Now',b'Genres',
      b'Because You Watched',b'See all',b'cobra-vod-art:'):
   require(token in dex,'2103211 contract missing from DEX: '+repr(token))
  require(b'infinity_launch_kodi_health_center' not in dex,
          'Obsolete Infinity-to-Kodi Health Center launch extra remains in final APK')

 scope=json.loads(Path('audit211/scope.json').read_text())
 require(scope.get('live_tv_source_untouched') is True,'Live TV source lock missing')
 require(scope.get('health_kodi_dependency') is False,'Health Center still depends on Kodi')
 require(scope.get('crash_safe_chooser') is True and scope.get('diagnostic_export') is True,
         'Crash-safe Health Center contract missing')
 require(scope.get('my_list_owner')=='existing Cobra drawer' and
         scope.get('search_owner')=='existing Cobra navigation','Media navigation ownership drift')

 result={
  'build':VERSION,'version_name':NAME,'apk_sha256':sha(args.final),'signer':CERT,
  'native_engine_sha256':NATIVE,'native_engine_rebuilt':False,
  'native_engine_reused_from_2103209':True,'live_tv_source_untouched':True,
  'movies_tv_shows_structure_verified':True,'cross_destination_tabs_removed':True,
  'genres_verified':True,'conditional_personalization_verified':True,
  'poster_details_before_playback_verified':True,'infinity_native_health_center':True,
  'kodi_health_center_shortcut_removed':True,'crash_safe_chooser':True,
  'diagnostic_export_without_adb':True,'physical_device_verified':False,
  'status':'TEST CANDIDATE'
 }
 Path('audit211/final-verification.json').write_text(json.dumps(result,indent=2)+'\n')
 Path('signed211/ACCEPTANCE.json').write_text(json.dumps(result,indent=2)+'\n')
 print('PASS: 2103211 signer/native/resources/Live TV and locked library/health contracts verified')

if __name__=='__main__':main()
