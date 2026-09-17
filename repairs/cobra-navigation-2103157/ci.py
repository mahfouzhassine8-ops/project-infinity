#!/usr/bin/env python3
"""Exact 2103156 -> 2103157 recipe, rollback, Android-only promotion and verified delivery."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,xml.etree.ElementTree as ET,zipfile
PARENT='b3bcb619b08205dcfc1451424b2d41e05fd37633'
LOCKED='4d1ed032df7e13fd27cc2170fc5e028f5059ec32'
APK156='fa13db18df0555f0148e7cc935b61d8e45284183c3424829f8c487935d66fe33'
JAVA156='766238af35d0bdddd80acb6c5c7e3e1c1cf4c38e493d365e0e777d883206079b'
UI='88ada1fded508fede9368bf9dc4259c60220a4f067b9ba5ae2b45ffdb6b2a81a'
OLD='1.0.9-Cobra-Diagnostics-Audit-RC1'
NEW='1.0.9-Cobra-TV-Navigation-Appearance-RC1'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
REL='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
ROOT=Path('view-delta/repairs/cobra-navigation-2103157')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(ok,message):
 if not ok:raise RuntimeError(message)
def run(*args):subprocess.run(list(args),check=True)
def head(path):return subprocess.check_output(['git','-C',path,'rev-parse','HEAD']).decode().strip()
def baseline_apk():return Path('baseline156/Infinity-'+OLD+'.apk')
def ledger(root):
 (root/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(root))+'\n' for p in sorted(root.rglob('*')) if p.is_file() and p.name!='SHA256SUMS'))
def reconstruct():
 require(head('audit-delta')==PARENT,'Diagnostics parent checkout drift')
 require(head('refinement-delta')==LOCKED,'Locked 2103155 recipe drift')
 for key,value in {'NDK_VER':'21.4.7075529','RUNTIME_COMMIT':'b42760a25a27d23baa5db5770824cb8d32ec2290','GITHUB_REPOSITORY':'mahfouzhassine8-ops/project-infinity'}.items():require(os.environ.get(key)==value,'Missing or wrong input: '+key)
 require(sha(baseline_apk())==APK156,'Wrong 2103156 rollback APK')
 require(sha('baseline156/Infinity-Cobra-UI-1.3.9.zip')==UI,'Wrong matching UI')
 rollback=Path('rollback157');rollback.mkdir(exist_ok=False)
 shutil.copy2(baseline_apk(),rollback/'Infinity-Cobra-2103156.apk')
 shutil.copy2('baseline156/Infinity-Cobra-UI-1.3.9.zip',rollback/'Infinity-Cobra-UI-1.3.9.zip')
 with (rollback/'2103156-exact-repository.zip').open('wb') as out:subprocess.run(['git','archive','--format=zip',PARENT],stdout=out,check=True)
 (rollback/'README.txt').write_text('Exact pre-change 2103156 plus retained locked 2103155 rollback. Device userdata is NOT backed up. Do not uninstall or clear data to force a downgrade. Android can reject a lower versionCode.\n')
 ledger(rollback)
 # Execute the SAME immutable reconstruction, observer patch and promotion that built 2103156.
 run('python3','audit-delta/repairs/cobra-diagnostics-2103156/ci.py','reconstruct')
 run('python3','audit-delta/repairs/cobra-diagnostics-2103156/tests/run.py','--baseline','rollback156/2103155-activity.java.in','--out','audit157/inherited-diagnostics')
 run('python3','audit-delta/repairs/cobra-diagnostics-2103156/tests/runtime_host.py','--out','audit157/inherited-diagnostic-runtime')
 run('python3','audit-delta/repairs/cobra-diagnostics-2103156/apply.py','--source','kodi','--receipt','audit157/parent-diagnostics-receipt.json')
 run('python3','audit-delta/repairs/cobra-diagnostics-2103156/ci.py','promote')
 require(sha(Path('kodi')/REL)==JAVA156,'Generated 2103156 Activity differs from passing artifact')
 original=json.loads(Path('baseline156/background-resume-source.json').read_text())
 receipt=json.loads(Path('engine/background-resume-source.json').read_text())
 require(receipt['version_code']==2103156 and original['version_code']==2103156,'Wrong parent version')
 require(set(receipt['files'])==set(original['files']),'Parent source receipt inventory drift')
 for name,row in original['files'].items():require(sha(Path('kodi')/name)==row['after'],'Parent source mismatch: '+name)
 shutil.copy2(Path('kodi')/REL,rollback/'2103156-activity.java.in')
 shutil.copy2('engine/background-resume-source.json',rollback/'2103156-source-receipt.json')
 shutil.copytree('rollback156',rollback/'locked2103155')
 with zipfile.ZipFile(rollback/'2103156-generated-android-source.zip','w',zipfile.ZIP_DEFLATED) as archive:
  for p in sorted(Path('kodi/tools/android/packaging').rglob('*')):
   if p.is_file():archive.write(p,str(p.relative_to('kodi')))
  archive.write('kodi/cmake/scripts/android/Install.cmake','cmake/scripts/android/Install.cmake')
 shutil.copy2('engine/native-before.patch',rollback/'protected-native-source.patch');ledger(rollback)
 print('PASS: all generated 2103156 receipt hashes match; complete 2103155/2103156 rollback preserved')
def promote():
 patch=json.loads(Path('audit157/patch.json').read_text());require(sha(Path('kodi')/REL)==patch['after_sha256'],'Final Activity differs from tested patch')
 changes={}
 for name,pairs in {
 'kodi/tools/android/packaging/xbmc/build.gradle.in':[('versionCode 2103156','versionCode 2103157'),('versionName "'+OLD+'"','versionName "'+NEW+'"')],
 'scripts/infinity_background_resume.py':[('VERSION_CODE = 2103156','VERSION_CODE = 2103157'),("RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'")]}.items():
  text=Path(name).read_text()
  for old,new in pairs:require(text.count(old)==1,'Wrong promotion preimage: '+name);text=text.replace(old,new,1)
  changes[name]=text
 name='scripts/package_background_resume.py';text=Path(name).read_text();require('Infinity-'+OLD in text,'Wrong APK filename contract');changes[name]=text.replace('Infinity-'+OLD,'Infinity-'+NEW)
 for name,text in changes.items():Path(name).write_text(text)
 p=Path('engine/background-resume-source.json');data=json.loads(p.read_text())
 data['files']['tools/android/packaging/xbmc/build.gradle.in']['after']=sha('kodi/tools/android/packaging/xbmc/build.gradle.in')
 data.update(version_code=2103157,version_name=NEW,locked_parent=2103155,source_parent=2103156,source_parent_locked=False,candidate_locked=False,diagnostic_export=True,native_engine_unchanged=True,device_playback_verified=False)
 p.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
 with Path('engine/native-after-2103157.patch').open('wb') as out:subprocess.run(['git','-C','kodi','diff','--binary','--','xbmc'],stdout=out,check=True)
 require(Path('engine/native-before.patch').read_bytes()==Path('engine/native-after-2103157.patch').read_bytes(),'Native source delta changed')
 # The four other renderers and complete diagnostic helper source remain protected independently.
 original=json.loads(Path('baseline156/background-resume-source.json').read_text())
 for name,row in original['files'].items():
  if name not in (REL,'tools/android/packaging/xbmc/build.gradle.in'):require(sha(Path('kodi')/name)==row['after'],'Non-targeted parent source changed: '+name)
 print('PASS: only Activity presentation/navigation and Android version changed; native delta and diagnostic helpers preserved')
def verify():
 apk=Path('signed157/Infinity-'+NEW+'.apk')
 with zipfile.ZipFile(apk) as new:
  protected={n for n in new.namelist() if n.startswith(('lib/','assets/')) and not n.endswith('/')};require(bool(protected),'No native/assets inventory')
  for baseline in (baseline_apk(),Path('baseline155/signed-candidate/Infinity-1.0.9-Cobra-Adaptive-Views-EPG-Repair-RC1.apk')):
   with zipfile.ZipFile(baseline) as old:
    require(protected=={n for n in old.namelist() if n.startswith(('lib/','assets/')) and not n.endswith('/')},'Native/asset inventory drift')
    for name in protected:require(new.read(name)==old.read(name),'Protected payload changed: '+name)
  dex=b''.join(new.read(n) for n in new.namelist() if n.startswith('classes') and n.endswith('.dex'))
  for token in (b'CobraNavigationEpoch',b'CobraAppearancePolicy',b'cobra_system_dark_variant',b'cobra_tv_directory_overlay',b'CobraModeLayout',b'CobraBroadcastRow',b'CobraMobileChannelRow',b'CobraCompactChannelRow',b'CobraPosterChannelCard',b'CobraFocusQueueRow',b'InfinityCobraDiagnostics',b'CobraDiagnosticArchive',b'cobraEpgSnapshotFile'):
   require(token in dex,'Missing runtime contract: '+repr(token))
  for token in (b'CobraNavigationUiTest',b'CobraModesUiTest',b'RuntimeTest',b'ArchiveTest'):require(token not in dex,'Test class in release APK')
 audit=json.loads(Path('signed157/background-resume-apk-audit.json').read_text())
 require(audit['version_code']==2103157 and audit['native_recompiled'] is False and audit['signer_certificate_sha256']==CERT,'Wrong APK identity or signer')
 require(audit['apk_sha256']==sha(apk),'APK checksum mismatch')
 Path('audit157/apk-verification.json').write_text(json.dumps({'apk_sha256':sha(apk),'native_files':sum(n.startswith('lib/') for n in protected),'asset_files':sum(n.startswith('assets/') for n in protected),'compared_to':[2103155,2103156],'device_verified':False},indent=2)+'\n')
 print('PASS: signed 2103157 identity, native/assets identical to 2103155 and 2103156; no test classes in APK')
def deliver():
 # Never equate Gradle starting, screenshots existing, or skipped cases to acceptance.
 results=Path('navigation-build/xbmc/build/test-results/testReleaseUnitTest/TEST-com.projectinfinity.kodi.CobraNavigationUiTest.xml')
 suite=ET.parse(results).getroot();cases=suite.findall('testcase')
 require(len(cases)==4 and int(suite.get('failures','0'))==0 and int(suite.get('errors','0'))==0 and int(suite.get('skipped','0'))==0,'Android view/navigation acceptance did not pass all four tests')
 for case in cases:require(case.find('skipped') is None and case.find('failure') is None and case.find('error') is None,'Skipped or failed Android case')
 images=sorted(Path('audit157/android/screenshots').glob('*.png'));require(len(images)>=6 and all(p.stat().st_size>100 for p in images),'Missing rendered layout evidence')
 apk=Path('signed157/Infinity-'+NEW+'.apk');audit=json.loads(Path('audit157/apk-verification.json').read_text());require(sha(apk)==audit['apk_sha256'],'Test phase changed staged release APK')
 shutil.copy2('baseline156/Infinity-Cobra-UI-1.3.9.zip','signed157/Infinity-Cobra-UI-1.3.9.zip');require(sha('signed157/Infinity-Cobra-UI-1.3.9.zip')==UI,'Wrong matching UI delivered')
 shutil.copy2(ROOT/'AUDIT.md','signed157/AUDIT-AND-DEVICE-CHECKS.md')
 acceptance={'build':2103157,'source_parent':2103156,'parent_commit':PARENT,'locked_baseline':2103155,'locked_commit':LOCKED,'candidate_locked':False,'native_recompiled':False,'apk_sha256':sha(apk),'matching_ui_version':'1.3.9','matching_ui_sha256':UI,'android_view_tests':len(cases),'rendered_screenshots':len(images),'same_size_drawer_return_tested':True,'stale_movies_shows_callbacks_tested':True,'real_provider_playback_verified':False,'physical_video_decoder_verified':False,'final_user_visual_acceptance':False}
 Path('signed157/ACCEPTANCE.json').write_text(json.dumps(acceptance,indent=2)+'\n');ledger(Path('signed157'))
 print('PASS: installable candidate delivery allowed after actual Android view/navigation gate; physical video acceptance pending')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['reconstruct','promote','verify','deliver']);a=p.parse_args();globals()[a.phase]()
