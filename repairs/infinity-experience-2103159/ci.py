#!/usr/bin/env python3
"""Exact locked 2103158 -> 2103159 experience ZIP bridge, rollback and delivery gates."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,xml.etree.ElementTree as ET,zipfile
LOCKED='fd2af59bab2edcaea6be9e5046720715e25e64e0'
APK158='3f173d2aad6a7a23faf5433c9edb316b9915f5d659b59dc4e635ebdf76533608'
ACTIVITY158='60b3a483b8dc11ec8f0280da63fc1892852cf95d30e2f182566830a6962d91b6'
SPLASH158='1ef9e88ec974aef5f88ab51d50de7d28105fa4b3496437694883322ec66dcf44'
UI139='88ada1fded508fede9368bf9dc4259c60220a4f067b9ba5ae2b45ffdb6b2a81a'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
OLD='1.0.9-Cobra-Health-Playback-RC1'
NEW='1.0.9-Infinity-Experience-Zip-Bridge-RC1'
ACT='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
SPLASH='tools/android/packaging/xbmc/src/Splash.java.in'
ROOT=Path('experience-delta/repairs/infinity-experience-2103159')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(ok,message):
 if not ok:raise RuntimeError(message)
def run(*args):subprocess.run(list(args),check=True)
def head(path):return subprocess.check_output(['git','-C',path,'rev-parse','HEAD']).decode().strip()
def baseline_apk():return Path('baseline158/Infinity-'+OLD+'.apk')
def ledger(root):
 (root/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(root))+'\n' for p in sorted(root.rglob('*')) if p.is_file() and p.name!='SHA256SUMS'))
def reconstruct():
 require(head('health-delta')==LOCKED,'Locked 2103158 checkout drift')
 for key,value in {'NDK_VER':'21.4.7075529','RUNTIME_COMMIT':'b42760a25a27d23baa5db5770824cb8d32ec2290','GITHUB_REPOSITORY':'mahfouzhassine8-ops/project-infinity'}.items():require(os.environ.get(key)==value,'Missing/wrong input: '+key)
 require(sha(baseline_apk())==APK158,'Wrong locked 2103158 APK')
 require(sha('baseline158/Infinity-Cobra-UI-1.3.9.zip')==UI139,'Wrong locked 2103158 matching UI')
 rollback=Path('rollback159');rollback.mkdir(exist_ok=False)
 shutil.copy2(baseline_apk(),rollback/'Infinity-Cobra-2103158.apk');shutil.copy2('baseline158/Infinity-Cobra-UI-1.3.9.zip',rollback/'Infinity-Cobra-UI-1.3.9.zip')
 shutil.copy2('baseline158/background-resume-source.json',rollback/'2103158-source-receipt.json')
 with (rollback/'2103158-exact-repository.zip').open('wb') as out:subprocess.run(['git','-C','health-delta','archive','--format=zip',LOCKED],stdout=out,check=True)
 (rollback/'README.txt').write_text('Exact locked 2103158 APK/UI/source before the experience ZIP bridge. Userdata is NOT included. Do not uninstall or clear data to force a downgrade; Android can reject a lower versionCode.\n')
 run('python3','health-delta/repairs/cobra-health-2103158/ci.py','reconstruct')
 run('python3','health-delta/repairs/cobra-health-2103158/tests/run.py','--baseline','rollback158/2103157-activity.java.in','--out','audit159/parent-health-host')
 run('python3','health-delta/repairs/cobra-health-2103158/apply.py','--source','kodi','--receipt','audit158/patch.json')
 run('python3','health-delta/repairs/cobra-health-2103158/ci.py','promote')
 original=json.loads(Path('baseline158/background-resume-source.json').read_text());current=json.loads(Path('engine/background-resume-source.json').read_text())
 require(original['version_code']==2103158 and current['version_code']==2103158,'Wrong reconstructed parent identity')
 require(set(original['files'])==set(current['files']),'2103158 receipt inventory drift')
 for name,row in original['files'].items():require(sha(Path('kodi')/name)==row['after']==current['files'][name]['after'],'2103158 source differs: '+name)
 require(sha(Path('kodi')/ACT)==ACTIVITY158,'Locked 2103158 Activity drift');require(sha(Path('kodi')/SPLASH)==SPLASH158,'Locked 2103158 Splash drift')
 shutil.copy2(Path('kodi')/SPLASH,rollback/'2103158-splash.java.in');shutil.copy2(Path('kodi')/ACT,rollback/'2103158-activity.java.in');shutil.copy2('engine/native-before.patch',rollback/'protected-native-source.patch')
 with zipfile.ZipFile(rollback/'2103158-generated-android-source.zip','w',zipfile.ZIP_DEFLATED) as archive:
  for p in sorted(Path('kodi/tools/android/packaging').rglob('*')):
   if p.is_file():archive.write(p,str(p.relative_to('kodi')))
  archive.write('kodi/cmake/scripts/android/Install.cmake','cmake/scripts/android/Install.cmake')
 ledger(rollback);print('PASS: exact locked 2103158 reconstructed; full pre-change rollback preserved')
def promote():
 patch=json.loads(Path('audit159/patch.json').read_text());require(sha(Path('kodi')/SPLASH)==patch['after_sha256'],'Splash differs from tested bridge')
 pairs={
  'kodi/tools/android/packaging/xbmc/build.gradle.in':[
   ('versionCode 2103158','versionCode 2103159'),
   ('versionName "'+OLD+'"','versionName "'+NEW+'"')],
  'scripts/infinity_background_resume.py':[
   ('VERSION_CODE = 2103158','VERSION_CODE = 2103159'),
   ("RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'")]
 }
 for name,edits in pairs.items():
  p=Path(name);text=p.read_text()
  for old,new in edits:require(text.count(old)==1,'Wrong promotion preimage: '+name);text=text.replace(old,new,1)
  p.write_text(text)
 p=Path('scripts/package_background_resume.py');text=p.read_text();require('Infinity-'+OLD in text,'Wrong packager identity');p.write_text(text.replace('Infinity-'+OLD,'Infinity-'+NEW))
 p=Path('engine/background-resume-source.json');data=json.loads(p.read_text());require(data['version_code']==2103158,'Wrong bridge parent receipt')
 data['files']['tools/android/packaging/xbmc/build.gradle.in']['after']=sha('kodi/tools/android/packaging/xbmc/build.gradle.in')
 data.update(version_code=2103159,version_name=NEW,locked_parent=2103158,source_parent=2103158,source_parent_locked=True,locked_commit=LOCKED,candidate_locked=False,experience_theme_bridge=1,experience_ui_zip='1.4.0',physical_device_verified=False,native_engine_unchanged=True)
 p.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
 with Path('engine/native-after-2103159.patch').open('wb') as out:subprocess.run(['git','-C','kodi','diff','--binary','--','xbmc'],stdout=out,check=True)
 require(Path('engine/native-before.patch').read_bytes()==Path('engine/native-after-2103159.patch').read_bytes(),'Native source delta changed')
 original=json.loads(Path('baseline158/background-resume-source.json').read_text())
 for name,row in original['files'].items():
  if name!='tools/android/packaging/xbmc/build.gradle.in':require(sha(Path('kodi')/name)==row['after'],'Locked 2103158 source changed: '+name)
 require(sha(Path('kodi')/ACT)==ACTIVITY158,'Cobra 2103158 Activity changed');print('PASS: 2103159 identity promoted; Splash bridge only; 2103158 Cobra runtime/native delta preserved')
def verify():
 apk=Path('signed159/Infinity-'+NEW+'.apk');ui=Path('signed159/Infinity-Cobra-UI-1.4.0-Experience.zip')
 with zipfile.ZipFile(apk) as new,zipfile.ZipFile(baseline_apk()) as old:
  protected={n for n in old.namelist() if n.startswith(('lib/','assets/')) and not n.endswith('/')};require(protected=={n for n in new.namelist() if n.startswith(('lib/','assets/')) and not n.endswith('/')},'Native/asset inventory changed')
  for name in protected:require(new.read(name)==old.read(name),'Protected APK bytes changed: '+name)
  dex=b''.join(new.read(n) for n in new.namelist() if n.startswith('classes') and n.endswith('.dex'))
  for token in (b'infinity-experience-chooser',b'experience-themed-root',b'experience-initials',b'INFINITY BY HASSINE MAHFOUZ',b'YOUR HOME FOR MOVIES, SHOWS AND MORE',b'FOCUSED. FAST. POWERFUL.',b'CobraRecoveryPolicy',b'InfinityCobraDiagnostics'):require(token in dex,'Runtime contract missing from APK: '+repr(token))
  for token in (b'ExperienceChooserUiTest',b'CobraHealthUiTest',b'CobraNavigationUiTest'):require(token not in dex,'Test class entered release APK')
 audit=json.loads(Path('signed159/background-resume-apk-audit.json').read_text());require(audit['version_code']==2103159 and audit['native_recompiled'] is False and audit['signer_certificate_sha256']==CERT,'APK identity/signer/native gate mismatch');require(audit['apk_sha256']==sha(apk),'APK hash mismatch')
 receipt=json.loads(Path('engine/background-resume-source.json').read_text());require(receipt['files'][SPLASH]['after']==sha(Path('kodi')/SPLASH),'Splash receipt mismatch');require(receipt['files'][ACT]['after']==ACTIVITY158,'Cobra Activity receipt changed');require(ui.is_file(),'Experience UI ZIP missing')
 Path('audit159/apk-verification.json').write_text(json.dumps({'apk_sha256':sha(apk),'ui_zip_sha256':sha(ui),'native_files':sum(n.startswith('lib/') for n in protected),'assets':sum(n.startswith('assets/') for n in protected),'locked_parent':2103158,'splash_bridge':1,'physical_device_verified':False},indent=2)+'\n');print('PASS: signed 2103159, exact locked native/assets/Cobra Activity, permanent signer and experience ZIP present')
def suite(path,expected):
 root=ET.parse(path).getroot();cases=root.findall('testcase');require(len(cases)==expected and all(int(root.get(k,'0'))==0 for k in ('failures','errors','skipped')),'Android suite incomplete: '+str(path));return len(cases)
def deliver():
 counts={'CobraNavigationUiTest':suite(Path('audit159/android/locked2103158/test-results/TEST-com.projectinfinity.kodi.CobraNavigationUiTest.xml'),4),'CobraHealthUiTest':suite(Path('audit159/android/locked2103158/test-results/TEST-com.projectinfinity.kodi.CobraHealthUiTest.xml'),7),'ExperienceChooserUiTest':suite(Path('audit159/android/experience/test-results/TEST-com.projectinfinity.kodi.ExperienceChooserUiTest.xml'),6)}
 parent=list(Path('audit159/android/locked2103158/screenshots').glob('*.png'));experience=list(Path('audit159/android/experience/screenshots').glob('*.png'));require(len(parent)>=16 and len(experience)>=3 and all(p.stat().st_size>100 for p in parent+experience),'Missing Android screenshot evidence')
 apk=Path('signed159/Infinity-'+NEW+'.apk');ui=Path('signed159/Infinity-Cobra-UI-1.4.0-Experience.zip');proof=json.loads(Path('audit159/apk-verification.json').read_text());require(sha(apk)==proof['apk_sha256'] and sha(ui)==proof['ui_zip_sha256'],'Test phase changed staged delivery')
 shutil.copy2(ROOT/'AUDIT.md','signed159/AUDIT-AND-DEVICE-CHECKS.md')
 Path('signed159/ACCEPTANCE.json').write_text(json.dumps({'build':2103159,'locked_parent':2103158,'locked_commit':LOCKED,'candidate_locked':False,'apk_sha256':sha(apk),'experience_ui_version':'1.4.0','experience_ui_sha256':sha(ui),'zip_installable_by_locked_2103158_cobra_ui_installer':True,'zip_effect_on_2103158':'stored but startup chooser ignores adjunct until bridge APK is installed','native_recompiled':False,'android_test_counts':counts,'screenshots':len(parent)+len(experience),'approved_copy_present':True,'live_tv_removed_from_infinity_card':True,'hm_present':True,'real_device_installation_verified':False,'physical_visual_acceptance':False},indent=2)+'\n');ledger(Path('signed159'));print('PASS: APK + ZIP delivery allowed after all 17 Android cases; user/device visual acceptance still pending')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['reconstruct','promote','verify','deliver']);a=p.parse_args();globals()[a.phase]()
