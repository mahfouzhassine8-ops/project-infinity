#!/usr/bin/env python3
"""Exact baseline reconstruction, complete rollback, Android-only candidate and honest acceptance."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,shutil,subprocess,zipfile,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent
BASE='7d95f8dd1696e340bde82cb73ce4e04a0bc2ac98'
APK_SHA='3e8cda1e8587080802dca1129b5e05c12f881f69efae8f5221103c67948658e3'
UI_SHA='88ada1fded508fede9368bf9dc4259c60220a4f067b9ba5ae2b45ffdb6b2a81a'
OLD='1.0.9-Cobra-TV-Navigation-Appearance-RC1'
NEW='1.0.9-Cobra-Health-Preferences-Recovery-RC1'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
REL='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
def require(ok,message):
 if not ok:raise RuntimeError(message)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(*args):subprocess.run(list(args),check=True)
def ledger(root):
 (root/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(root))+'\n' for p in sorted(root.rglob('*')) if p.is_file() and p.name!='SHA256SUMS'))
def source_receipt():return json.loads(Path('engine/background-resume-source.json').read_text())
def reconstruct():
 import yaml
 require(subprocess.check_output(['git','-C','view-delta','rev-parse','HEAD']).decode().strip()==BASE,'Locked 2103157 recipe drift')
 require(sha('baseline157/Infinity-'+OLD+'.apk')==APK_SHA,'Wrong locked 2103157 APK')
 require(sha('baseline157/Infinity-Cobra-UI-1.3.9.zip')==UI_SHA,'Wrong matching UI')
 workflow=yaml.safe_load(Path('view-delta/.github/workflows/cobra-2103157-tv-navigation-appearance.yml').read_text())
 names=['Reconstruct verified 2103156 and preserve both rollback baselines','Reproduce navigation defects and test final layout and dark policy','Apply scoped repair and rerun final guide and inherited algorithms'];done=[]
 for step in workflow['jobs']['audit-and-package']['steps']:
  if step.get('name') in names:run('bash','-e','-o','pipefail','-c',step['run']);done.append(step['name'])
 require(done==names,'Incomplete exact baseline reconstruction')
 original=json.loads(Path('baseline157/background-resume-source.json').read_text());receipt=source_receipt()
 require(receipt['version_code']==2103157 and original['version_code']==2103157,'Wrong reconstructed version')
 require(set(receipt['files'])==set(original['files']),'Source inventory changed')
 for name,row in original['files'].items():require(sha(Path('kodi')/name)==row['after'],'2103157 source differs: '+name)
 rollback=Path('rollback158');rollback.mkdir(exist_ok=False)
 for name in ('Infinity-'+OLD+'.apk','Infinity-Cobra-UI-1.3.9.zip','background-resume-source.json','background-resume-apk-audit.json','ACCEPTANCE.json','signing-verification.txt'):shutil.copy2(Path('baseline157')/name,rollback/name)
 shutil.copy2(Path('kodi')/REL,rollback/'2103157-activity.java.in')
 shutil.copy2('engine/native-before.patch',rollback/'protected-native-source.patch')
 with (rollback/'2103157-exact-repository.zip').open('wb') as out:subprocess.run(['git','-C','view-delta','archive','--format=zip','HEAD'],stdout=out,check=True)
 with zipfile.ZipFile(rollback/'2103157-generated-android-source.zip','w',zipfile.ZIP_DEFLATED) as archive:
  for p in sorted(Path('kodi/tools/android/packaging').rglob('*')):
   if p.is_file():archive.write(p,str(p.relative_to('kodi')))
  archive.write('kodi/cmake/scripts/android/Install.cmake','cmake/scripts/android/Install.cmake')
 shutil.copytree('rollback157',rollback/'retained2103155-2103156')
 (rollback/'README.txt').write_text('Exact locked 2103157 APK/UI/generated Android source/repository/receipts; 2103155 and 2103156 rollback retained. DEVICE USERDATA IS NOT BACKED UP. Do not uninstall, clear data, or force a downgrade. Android may reject a lower versionCode. The locked branch is never changed.\n')
 ledger(rollback);print('PASS: exact 2103157 rebuilt in staging; complete source/APK/UI rollback preserved before new mutation')
def apply():
 run('python3',str(ROOT/'tests/run.py'),'--baseline','rollback158/2103157-activity.java.in','--out','audit158/host')
 source=Path('kodi')/REL;require(source.read_bytes()==Path('rollback158/2103157-activity.java.in').read_bytes(),'Baseline drift before apply')
 shutil.copy2('audit158/host/InfinityLiveActivity.java.in',source)
 receipt=source_receipt();receipt['files'][REL]['after']=sha(source)
 substitutions={
  'kodi/tools/android/packaging/xbmc/build.gradle.in':[('versionCode 2103157','versionCode 2103158'),('versionName "'+OLD+'"','versionName "'+NEW+'"')],
  'scripts/infinity_background_resume.py':[('VERSION_CODE = 2103157','VERSION_CODE = 2103158'),("RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'")],
  'scripts/package_background_resume.py':[('Infinity-'+OLD,'Infinity-'+NEW)]}
 for path,pairs in substitutions.items():
  text=Path(path).read_text()
  for old,new in pairs:
   require(old in text,'Promotion preimage missing: '+path)
   if path!='scripts/package_background_resume.py':require(text.count(old)==1,'Ambiguous promotion anchor')
   text=text.replace(old,new)
  Path(path).write_text(text)
 receipt['files']['tools/android/packaging/xbmc/build.gradle.in']['after']=sha('kodi/tools/android/packaging/xbmc/build.gradle.in')
 receipt.update(version_code=2103158,version_name=NEW,source_parent=2103157,locked_parent=2103157,source_parent_locked=True,candidate_locked=False,native_engine_unchanged=True,device_playback_verified=False,cobra_health_center=True,channel_playback_preferences=True,bounded_surface_recovery=True,drawer_view_selector=True)
 Path('engine/background-resume-source.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
 original=json.loads(Path('baseline157/background-resume-source.json').read_text())
 for name,row in original['files'].items():
  if name not in (REL,'tools/android/packaging/xbmc/build.gradle.in'):require(sha(Path('kodi')/name)==row['after'],'Non-target source changed: '+name)
 with Path('audit158/native-after.patch').open('wb') as out:subprocess.run(['git','-C','kodi','diff','--binary','--','xbmc'],check=True,stdout=out)
 require(Path('audit158/native-after.patch').read_bytes()==Path('engine/native-before.patch').read_bytes(),'Native source delta changed')
 run('python3',str(ROOT/'tests/inherited.py'),'--source',str(source),'--out','audit158/inherited','--mode-harness','audit157/host/modes/CobraModesHarness.java','--repository',str(ROOT.parents[1]))
 run('python3',str(ROOT.parent/'cobra-diagnostics-2103156/tests/runtime_host.py'),'--out','audit158/diagnostic-runtime')
 print('PASS: Health Center, preferences, bounded recovery, branding and View selector integrated; no native or provider mutations')
def verify():
 apk=Path('signed158/Infinity-'+NEW+'.apk');audit=json.loads(Path('signed158/background-resume-apk-audit.json').read_text())
 require(audit['apk_sha256']==sha(apk) and audit['version_code']==2103158 and audit['native_recompiled'] is False and audit['signer_certificate_sha256']==CERT,'Identity, signer or native audit failure')
 with zipfile.ZipFile('baseline157/Infinity-'+OLD+'.apk') as baseline,zipfile.ZipFile(apk) as new:
  protected={n for n in baseline.namelist() if n.startswith(('lib/','assets/','res/')) or n=='resources.arsc'}
  require(protected=={n for n in new.namelist() if n.startswith(('lib/','assets/','res/')) or n=='resources.arsc'},'Native/assets/resource inventory changed')
  for name in protected:require(baseline.read(name)==new.read(name),'Protected payload changed: '+name)
  dex=b''.join(new.read(n) for n in new.namelist() if n.startswith('classes') and n.endswith('.dex'))
  for token in (b'CobraPlaybackChoice',b'CobraSurfaceRecovery',b'CobraRecoveryBudget',b'Cobra Health Center',b'cobra_drawer_view',b'cobra_channel_playback_v1',b'cobra_health_center',b'InfinityCobraDiagnostics',b'CobraBroadcastRow',b'CobraMobileChannelRow',b'CobraCompactChannelRow',b'CobraPosterChannelCard',b'CobraFocusQueueRow'):require(token in dex,'Missing compiled feature: '+repr(token))
  for token in (b'RecoveryHost',b'CobraNavigationUiTest',b'CobraModesUiTest',b'ArchiveTest'):require(token not in dex,'Test code in APK')
 result={'apk_sha256':sha(apk),'compared_to_build':2103157,'protected_entries':len(protected),'signer_certificate_sha256':CERT,'native_recompiled':False,'physical_device_verified':False,'official':False}
 Path('audit158/apk-verification.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS: actual APK payload and signer matched to locked 2103157')
def deliver():
 acceptance=json.loads(Path('audit158/android/acceptance.json').read_text());require(acceptance['tests']==12 and acceptance['inherited_tests_unchanged'],'Incomplete Android suite')
 host=json.loads(Path('audit158/host/results.json').read_text());require(host['host_checks_passed'] and host['outside_listed_members_byte_identical'],'Incomplete source or recovery gate')
 data=json.loads(Path('audit158/inherited/epg/results.json').read_text());require(data['tests']==66 and data['passed']==66 and data['test_result']==0,'Full-guide cases did not all pass')
 short=json.loads(Path('audit158/inherited/short/results.json').read_text());rows=[line.split('\t') for line in Path('audit158/inherited/short/results.tsv').read_text().splitlines()];require(short['exit_code']==0 and len(rows)==9 and all(r[1]=='PASS' for r in rows),'Short-guide cases did not all pass')
 diagnostic=json.loads(Path('audit158/diagnostic-runtime/results.json').read_text());require(diagnostic['exit_code']==0,'Diagnostic runtime failed')
 report=json.loads(Path('audit158/apk-verification.json').read_text());require(report['apk_sha256']==sha('signed158/Infinity-'+NEW+'.apk'),'APK changed after audit')
 require(host['after_sha256']==sha(Path('kodi')/REL),'Tested source differs from final source')
 images=sorted(Path('audit158/android/screenshots').glob('*.png'));require(len(images)>=10 and all(p.stat().st_size>100 for p in images),'Missing baseline/new UI screenshots')
 shutil.copy2('baseline157/Infinity-Cobra-UI-1.3.9.zip','signed158/Infinity-Cobra-UI-1.3.9.zip');require(sha('signed158/Infinity-Cobra-UI-1.3.9.zip')==UI_SHA,'Matching UI changed')
 shutil.copy2(ROOT/'AUDIT.md','signed158/AUDIT-AND-DEVICE-CHECKS.md')
 (Path('signed158')/'ACCEPTANCE.json').write_text(json.dumps({'build':2103158,'locked_baseline':2103157,'locked_commit':BASE,'source_commit':os.environ.get('GITHUB_SHA','unknown'),'apk_sha256':report['apk_sha256'],'host_guards_passed':True,'android_view_tests':12,'inherited_epg_cases':75,'rendered_screenshots':len(images),'signer_verified':True,'native_and_assets_unchanged':True,'matching_ui':'1.3.9','candidate_locked':False,'official':False,'physical_video_decoder_verified':False,'real_provider_playback_verified':False,'final_user_visual_acceptance':False,'device_userdata_backed_up':False,'release_decision':'CANDIDATE ONLY - physical playback, recovery and rollback acceptance required'},indent=2)+'\n');ledger(Path('signed158'))
 print('PASS: signed test candidate deliverable; official release and new lock remain HOLD pending device acceptance')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['reconstruct','apply','verify','deliver']);a=p.parse_args();globals()[a.phase]()
