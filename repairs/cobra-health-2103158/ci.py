#!/usr/bin/env python3
"""Reproduce locked 2103157 exactly, then build a scoped Android-only health candidate."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,xml.etree.ElementTree as ET,zipfile
LOCKED='7d95f8dd1696e340bde82cb73ce4e04a0bc2ac98'
APK157='3e8cda1e8587080802dca1129b5e05c12f881f69efae8f5221103c67948658e3'
JAVA157='b5d25a639b0c2eb09cf2503b5af40f4d9c5ed4545db9406e8bc7413ef0aa2943'
UI='88ada1fded508fede9368bf9dc4259c60220a4f067b9ba5ae2b45ffdb6b2a81a'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
OLD='1.0.9-Cobra-TV-Navigation-Appearance-RC1'
NEW='1.0.9-Cobra-Health-Playback-RC1'
REL='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
ROOT=Path('health-delta/repairs/cobra-health-2103158')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(ok,message):
 if not ok:raise RuntimeError(message)
def run(*args):subprocess.run(list(args),check=True)
def ledger(root):
 (root/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(root))+'\n' for p in sorted(root.rglob('*')) if p.is_file() and p.name!='SHA256SUMS'))
def original_apk():return Path('baseline157/Infinity-'+OLD+'.apk')
def reconstruct():
 require(subprocess.check_output(['git','-C','view-delta','rev-parse','HEAD']).decode().strip()==LOCKED,'Wrong locked 2103157 checkout')
 require(sha(original_apk())==APK157,'Wrong locked 2103157 APK')
 require(sha('baseline157/Infinity-Cobra-UI-1.3.9.zip')==UI,'Wrong matching UI')
 rollback=Path('rollback158');rollback.mkdir(exist_ok=False)
 shutil.copy2(original_apk(),rollback/'Infinity-Cobra-2103157.apk')
 shutil.copy2('baseline157/Infinity-Cobra-UI-1.3.9.zip',rollback/'Infinity-Cobra-UI-1.3.9.zip')
 with (rollback/'2103157-exact-repository.zip').open('wb') as out:subprocess.run(['git','archive','--format=zip',LOCKED],stdout=out,check=True)
 (rollback/'README.txt').write_text('Exact locked 2103157 pre-change APK/UI/source. Device userdata is NOT backed up. Keep the lock unchanged. Do not uninstall or clear data to force a downgrade: Android can refuse a lower versionCode. A reviewed higher-version rollback or separate device-data backup is required.\n')
 ledger(rollback)
 # Run the immutable parent recipes, including their original source/diagnostic/integrity checks.
 run('python3','view-delta/repairs/cobra-navigation-2103157/ci.py','reconstruct')
 run('python3','view-delta/repairs/cobra-navigation-2103157/tests/run.py','--baseline','rollback157/2103156-activity.java.in','--out','audit158/parent-host')
 run('python3','view-delta/repairs/cobra-navigation-2103157/apply.py','--source','kodi','--receipt','audit157/patch.json')
 require(sha(Path('kodi')/REL)==JAVA157,'Generated 2103157 Activity differs from locked build')
 run('python3','view-delta/repairs/cobra-navigation-2103157/ci.py','promote')
 original=json.loads(Path('baseline157/background-resume-source.json').read_text())
 receipt=json.loads(Path('engine/background-resume-source.json').read_text())
 require(receipt['version_code']==2103157 and original['version_code']==2103157,'Wrong parent version')
 require(set(receipt['files'])==set(original['files']),'Parent source inventory changed')
 for name,row in original['files'].items():require(sha(Path('kodi')/name)==row['after'],'Parent source drift: '+name)
 shutil.copy2(Path('kodi')/REL,rollback/'2103157-activity.java.in')
 shutil.copy2('engine/background-resume-source.json',rollback/'2103157-source-receipt.json')
 shutil.copy2('engine/native-before.patch',rollback/'protected-native-source.patch')
 with zipfile.ZipFile(rollback/'2103157-generated-android-source.zip','w',zipfile.ZIP_DEFLATED) as archive:
  for p in sorted(Path('kodi/tools/android/packaging').rglob('*')):
   if p.is_file():archive.write(p,str(p.relative_to('kodi')))
  archive.write('kodi/cmake/scripts/android/Install.cmake','cmake/scripts/android/Install.cmake')
 ledger(rollback);print('PASS: exact locked 2103157 reconstructed; complete pre-change rollback preserved')
def promote():
 patch=json.loads(Path('audit158/patch.json').read_text());require(sha(Path('kodi')/REL)==patch['after_sha256'],'Activity differs from tested patch')
 pairs={
 'kodi/tools/android/packaging/xbmc/build.gradle.in':[('versionCode 2103157','versionCode 2103158'),('versionName "'+OLD+'"','versionName "'+NEW+'"')],
 'scripts/infinity_background_resume.py':[('VERSION_CODE = 2103157','VERSION_CODE = 2103158'),("RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'")]}
 for name,edits in pairs.items():
  p=Path(name);text=p.read_text()
  for old,new in edits:require(text.count(old)==1,'Wrong promotion preimage: '+name);text=text.replace(old,new,1)
  p.write_text(text)
 p=Path('scripts/package_background_resume.py');text=p.read_text();require('Infinity-'+OLD in text,'Wrong packager identity');p.write_text(text.replace('Infinity-'+OLD,'Infinity-'+NEW))
 p=Path('engine/background-resume-source.json');data=json.loads(p.read_text());require(data['version_code']==2103157,'Wrong source receipt version')
 data['files']['tools/android/packaging/xbmc/build.gradle.in']['after']=sha('kodi/tools/android/packaging/xbmc/build.gradle.in')
 data.update(version_code=2103158,version_name=NEW,locked_parent=2103157,source_parent=2103157,source_parent_locked=True,locked_commit=LOCKED,candidate_locked=False,physical_device_verified=False,health_center=True,per_channel_preferences=True,guarded_surface_recovery=True,view_drawer_chooser=True)
 p.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
 with Path('engine/native-after-2103158.patch').open('wb') as out:subprocess.run(['git','-C','kodi','diff','--binary','--','xbmc'],stdout=out,check=True)
 require(Path('engine/native-before.patch').read_bytes()==Path('engine/native-after-2103158.patch').read_bytes(),'Native source delta changed')
 for name,row in json.loads(Path('baseline157/background-resume-source.json').read_text())['files'].items():
  if name not in (REL,'tools/android/packaging/xbmc/build.gradle.in'):require(sha(Path('kodi')/name)==row['after'],'Unrelated parent source changed: '+name)
 print('PASS: 2103158 identity; only Activity and version metadata changed; native delta/diagnostics helpers unchanged')
def verify():
 apk=Path('signed158/Infinity-'+NEW+'.apk')
 with zipfile.ZipFile(apk) as new,zipfile.ZipFile(original_apk()) as old:
  protected={n for n in old.namelist() if n.startswith(('lib/','assets/')) and not n.endswith('/')}
  require(protected=={n for n in new.namelist() if n.startswith(('lib/','assets/')) and not n.endswith('/')},'Protected APK inventory changed')
  for name in protected:require(new.read(name)==old.read(name),'Protected bytes changed: '+name)
  dex=b''.join(new.read(n) for n in new.namelist() if n.startswith('classes') and n.endswith('.dex'))
  for token in (b'CobraRecoveryPolicy',b'CobraSessionVitals',b'CobraChannelPreferences',b'CobraCaptionOverlay',b'cobra-drawer-view',b'cobra-health-export',b'cobra.channel.v1.',b'CobraModeLayout',b'InfinityCobraDiagnostics',b'cobraEpgSnapshotFile'):
   require(token in dex,'New or inherited runtime contract missing: '+repr(token))
  for token in (b'CobraHealthUiTest',b'CobraNavigationUiTest',b'PolicyTest',b'ArchiveTest'):require(token not in dex,'Test class entered release APK')
 audit=json.loads(Path('signed158/background-resume-apk-audit.json').read_text())
 require(audit['version_code']==2103158 and audit['native_recompiled'] is False and audit['signer_certificate_sha256']==CERT,'APK identity/signer/native gate mismatch')
 require(audit['apk_sha256']==sha(apk),'APK hash mismatch')
 Path('audit158/apk-verification.json').write_text(json.dumps({'apk_sha256':sha(apk),'native_files':sum(n.startswith('lib/') for n in protected),'assets':sum(n.startswith('assets/') for n in protected),'locked_parent':2103157,'physical_device_verified':False},indent=2)+'\n')
 print('PASS: compiled/signed 2103158 with exact locked native/assets and permanent signer; no test classes')
def deliver():
 counts={};expected={'CobraNavigationUiTest':4,'CobraHealthUiTest':7}
 for name,count in expected.items():
  suite=ET.parse(Path('health-build/xbmc/build/test-results/testReleaseUnitTest')/('TEST-com.projectinfinity.kodi.'+name+'.xml')).getroot();cases=suite.findall('testcase')
  require(len(cases)==count and all(int(suite.get(k,'0'))==0 for k in ('failures','errors','skipped')),'Android gate incomplete: '+name)
  for case in cases:require(not any(case.find(k) is not None for k in ('failure','error','skipped')),'Failed/skipped Android case')
  counts[name]=len(cases)
 images=sorted(Path('audit158/android/screenshots').glob('*.png'));require(len(images)>=14 and all(p.stat().st_size>100 for p in images),'Missing rendered UI evidence')
 apk=Path('signed158/Infinity-'+NEW+'.apk');proof=json.loads(Path('audit158/apk-verification.json').read_text());require(sha(apk)==proof['apk_sha256'],'Test phase changed release APK')
 shutil.copy2('baseline157/Infinity-Cobra-UI-1.3.9.zip','signed158/Infinity-Cobra-UI-1.3.9.zip');require(sha('signed158/Infinity-Cobra-UI-1.3.9.zip')==UI,'Matching UI changed')
 shutil.copy2(ROOT/'AUDIT.md','signed158/AUDIT-AND-DEVICE-CHECKS.md')
 Path('signed158/ACCEPTANCE.json').write_text(json.dumps({'build':2103158,'locked_parent':2103157,'locked_commit':LOCKED,'candidate_locked':False,'apk_sha256':sha(apk),'matching_ui_sha256':UI,'matching_ui_version':'1.3.9','native_recompiled':False,'android_test_counts':counts,'screenshots':len(images),'new_test_player':'explicit ExoPlayer double; production adapter/view code executes','real_provider_playback_verified':False,'physical_gpu_surface_recovery_verified':False,'real_device_installation_verified':False,'final_branding_visual_acceptance':False},indent=2)+'\n')
 ledger(Path('signed158'));print('PASS: candidate delivery after all 11 Android cases; device and final official acceptance remain open')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['reconstruct','promote','verify','deliver']);a=p.parse_args();globals()[a.phase]()
