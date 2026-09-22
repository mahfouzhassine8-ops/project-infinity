#!/usr/bin/env python3
"""2103218 onn. 4K Pro / Google TV ARMv7 source identity.

Parent: exact locked 2103217 Android source.
No UI/feature redesign. The only source delta is the TV-variant build identity;
the native engine is rebuilt separately for armeabi-v7a.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

VERSION=2103218
OLD_VERSION=2103217
OLD_NAME='1.0.9-Cobra-Media-Return-Context-RC1'
NEW_NAME='1.0.9-Cobra-Onn4KPro-TV-ARMv7-RC1'
SOURCE='tools/android/packaging/xbmc/'
NATIVE_MOBILE='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'

def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def sha(path):return sha_bytes(Path(path).read_bytes())
def require(v,m):
 if not v:raise RuntimeError(m)
def once(text,old,new,label):
 require(text.count(old)==1,f'{label} anchor drift ({text.count(old)})')
 return text.replace(old,new,1)

def apply(shell:Path):
 receipt_path=Path('engine/background-resume-source.json')
 receipt=json.loads(receipt_path.read_text())
 require(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,
         'Expected exact locked 2103217 source replay')
 require(receipt.get('native_engine_sha256')==NATIVE_MOBILE,
         'Locked 2103217 mobile native receipt drift')

 gradle=shell/(SOURCE+'build.gradle.in')
 manifest=shell/(SOURCE+'AndroidManifest.xml.in')
 live=shell/(SOURCE+'src/InfinityLiveActivity.java.in')
 smart=shell/(SOURCE+'src/CobraSmartReturn.java.in')
 for p in (gradle,manifest,live,smart):require(p.is_file(),'Missing TV source input: '+str(p))

 m=manifest.read_text()
 for token in (
   'android.intent.category.LEANBACK_LAUNCHER',
   'android:banner="@drawable/banner"',
   'android:name="android.hardware.touchscreen"',
   'android:name="android.software.leanback"',
   'android:name="android.hardware.type.television"',
 ):
  require(token in m,'Android TV manifest contract missing: '+token)
 require('android:name="android.hardware.touchscreen"\n        android:required="false"' in m,
         'Touchscreen unexpectedly required')
 require('android:name="android.software.leanback"\n        android:required="false"' in m,
         'Leanback compatibility contract drift')

 java=live.read_text()
 for token in (
   'cobra_smart_return_experience_display',
   'cobraRestoreVodLandingReturn()',
   'LIVE TV AMBIENT BLUE',
   'Play Next Episode',
   'Infinity Health Center',
 ):
  require(token in java or token in (shell/(SOURCE+'src/Splash.java.in')).read_text(),
          'Locked 2103217 feature missing before TV build: '+token)
 require('getBoolean(ENABLED,true)' in smart.read_text(),'Smart Return default-ON contract lost')

 g=gradle.read_text()
 g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','TV versionCode')
 g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','TV versionName')
 gradle.write_text(g)

 rel=SOURCE+'build.gradle.in'
 require(rel in receipt['files'],'Gradle missing from source receipt')
 receipt['files'][rel]['after']=sha(gradle)
 receipt.update(
   version_code=VERSION,
   version_name=NEW_NAME,
   source_parent=OLD_VERSION,
   candidate_locked=False,
   physical_device_verified=False,
   runtime_device_tested=False,
   tv_variant=True,
   tv_target='onn. 4K Pro / Google TV',
   tv_target_abi='armeabi-v7a',
   tv_native_host='arm-linux-androideabi',
   native_engine_rebuilt=True,
   native_engine_sha256='pending-armv7-build',
   mobile_parent_native_sha256=NATIVE_MOBILE,
   mobile_parent_untouched=True,
   same_package=True,
   same_signer_required=True,
   leanback_launcher_preserved=True,
   tv_banner_preserved=True,
   touchscreen_not_required=True,
   smart_return_location='Cobra Settings > Experience & Display',
   media_return_context_preserved=True,
   live_tv_blue_ambient_preserved=True,
   health_center_preserved=True,
   playback_feature_set_preserved=True,
 )
 receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
 for name,row in receipt['files'].items():
  require(sha(shell/name)==row['after'],'Final TV source receipt drift: '+name)

 Path('audit218').mkdir(exist_ok=True)
 Path('audit218/tv-source.json').write_text(json.dumps({
   'build':VERSION,'version_name':NEW_NAME,'parent_build':OLD_VERSION,
   'target':'onn. 4K Pro / Google TV','target_abi':'armeabi-v7a',
   'native_host':'arm-linux-androideabi','native_rebuild_required':True,
   'mobile_parent_native_sha256':NATIVE_MOBILE,'mobile_parent_untouched':True,
   'package':'com.projectinfinity.kodi','same_signer_required':True,
   'leanback_launcher':True,'banner':'@drawable/banner','touchscreen_required':False,
   'feature_scope':'same Infinity/Cobra feature set as locked 2103217',
   'physical_device_verified':False,
 },indent=2)+'\n')
 print('PASS: 2103218 TV identity applied; locked 2103217 features preserved for ARMv7 native build')

def main():
 p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);a=p.parse_args();apply(a.shell)
if __name__=='__main__':main()
