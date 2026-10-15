#!/usr/bin/env python3
"""Isolated runtime candidate, exact 2103159 rollback and preserved Android/native gates."""
from pathlib import Path
import argparse, hashlib, json, os, shutil, subprocess, zipfile, xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent
BASE='257a49d742890acf0c7d3e0220bded5a8aa80c57'
APK='980d1f45dc55d2e87b0c8712f2f59ef7626abbeb517c9f1d0bb772c77d2e4597'
UI='f88b0234de897a6350323c3100ca19adc445c4c767bd7eca9c73b3e5257cf143'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
OLD='1.0.9-Infinity-Experience-Zip-Bridge-RC1';NEW='1.0.9-Cobra-Visual-Theme-Runtime-v2-RC1'
def require(value,message):
 if not value:raise RuntimeError(message)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(*args):subprocess.run(list(map(str,args)),check=True)
def ledger(root):
 (root/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(root))+'\n' for p in sorted(root.rglob('*')) if p.is_file() and p.name!='SHA256SUMS'))
def reconstruct():
 import yaml
 require(subprocess.check_output(['git','-C','experience-delta','rev-parse','HEAD']).decode().strip()==BASE,'Locked 2103159 source drift')
 require(sha('baseline159/Infinity-'+OLD+'.apk')==APK,'Incorrect 2103159 APK');require(sha('baseline159/Infinity-Cobra-UI-1.4.0-Experience.zip')==UI,'Incorrect 2103159 UI')
 workflow=yaml.safe_load(Path('experience-delta/.github/workflows/infinity-2103159-experience-zip-bridge.yml').read_text())
 names=['Reconstruct exact locked 2103158 and preserve rollback','Test bridge and build exact UI 1.4.0 ZIP','Apply 2103159 bridge and scoped Cobra drawer/settings/power cleanup'];done=[]
 for step in workflow['jobs']['audit-and-package']['steps']:
  if step.get('name') in names:run('bash','-e','-o','pipefail','-c',step['run']);done.append(step['name'])
 require(done==names,'Incomplete immutable reconstruction')
 original=json.loads(Path('baseline159/background-resume-source.json').read_text());current=json.loads(Path('engine/background-resume-source.json').read_text())
 require(original['version_code']==current['version_code']==2103159,'Wrong source identity');require(original['files'].keys()==current['files'].keys(),'Source inventory differs')
 for name,row in original['files'].items():require(sha(Path('kodi')/name)==row['after']==current['files'][name]['after'],'Generated 2103159 differs: '+name)
 rollback=Path('rollback160');rollback.mkdir(exist_ok=False);shutil.copytree('baseline159',rollback/'apk-ui-receipts')
 with (rollback/'2103159-exact-repository.zip').open('wb') as f:subprocess.run(['git','-C','experience-delta','archive','--format=zip','HEAD'],stdout=f,check=True)
 with zipfile.ZipFile(rollback/'2103159-generated-android-source.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(Path('kodi/tools/android/packaging').rglob('*')):
   if p.is_file():z.write(p,str(p.relative_to('kodi')))
  z.write('kodi/cmake/scripts/android/Install.cmake','cmake/scripts/android/Install.cmake')
 for name in ('InfinityLiveActivity','Splash'):shutil.copy2('kodi/tools/android/packaging/xbmc/src/'+name+'.java.in',rollback/(name+'.java.in'))
 shutil.copy2('engine/native-before.patch',rollback/'protected-native-source.patch')
 (rollback/'README.txt').write_text('Exact locked 2103159 APK/UI/source before runtime v2. Device/userdata is NOT backed up. Do not uninstall or clear data to force downgrade; lower versionCode may be rejected. Runtime v2 theme Reset/Previous operate on private theme snapshots, not this APK rollback.\n');ledger(rollback)
 print('PASS: exact locked 2103159 verified and full pre-change rollback retained')
def apply():
 run('python3',ROOT/'tests/source_tests.py','--baseline','rollback160','--out','audit160/source')
 run('python3',ROOT/'apply.py','--source','kodi','--out','audit160')
 receipt=json.loads(Path('engine/background-resume-source.json').read_text());patch=json.loads(Path('audit160/patch.json').read_text())
 for name,row in patch['files'].items():receipt['files'][name]={'before':row['before'],'after':row['after']}
 for path,old,new in [('kodi/tools/android/packaging/xbmc/build.gradle.in','versionCode 2103159','versionCode 2103160'),('kodi/tools/android/packaging/xbmc/build.gradle.in','versionName "'+OLD+'"','versionName "'+NEW+'"'),('scripts/infinity_background_resume.py','VERSION_CODE = 2103159','VERSION_CODE = 2103160'),('scripts/infinity_background_resume.py',"RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'")]:
  p=Path(path);s=p.read_text();require(s.count(old)==1,'Version preimage mismatch');p.write_text(s.replace(old,new,1))
 p=Path('scripts/package_background_resume.py');s=p.read_text();require('Infinity-'+OLD in s,'Packager naming mismatch');p.write_text(s.replace('Infinity-'+OLD,'Infinity-'+NEW))
 receipt['files']['tools/android/packaging/xbmc/build.gradle.in']['after']=sha('kodi/tools/android/packaging/xbmc/build.gradle.in')
 receipt.update(version_code=2103160,version_name=NEW,locked_commit=BASE,locked_parent=2103159,source_parent=2103159,candidate_locked=False,visual_theme_runtime=2,physical_device_verified=False)
 Path('engine/background-resume-source.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
 # Protected algorithms are still tested against the generated release source, not a substitute.
 source=Path('kodi/tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
 run('python3','refinement-delta/repairs/cobra-epg-rc1/tests/run_tests.py','--source',source,'--out','audit160/epg-host')
 run('python3','refinement-delta/repairs/cobra-epg-rc1/tests/run_short.py','--source',source,'--host','audit160/epg-host','--out','audit160/epg-short')
 run('python3','refinement-delta/repairs/cobra-epg-rc1/tests/run_inherited.py','--source',source,'--repository','refinement-delta','--mode-harness','evidence158/audit158/inherited/CobraModesHarness.java','--out','audit160/inherited')
 with Path('audit160/native-after.patch').open('wb') as f:subprocess.run(['git','-C','kodi','diff','--binary','--','xbmc'],stdout=f,check=True)
 require(Path('audit160/native-after.patch').read_bytes()==Path('engine/native-before.patch').read_bytes(),'Native source changed')
 print('PASS: visual runtime installed in staged Android source; native delta unchanged')
def verify():
 apk=Path('signed160/Infinity-'+NEW+'.apk');audit=json.loads(Path('signed160/background-resume-apk-audit.json').read_text())
 require(audit['apk_sha256']==sha(apk) and audit['version_code']==2103160 and audit['signer_certificate_sha256']==CERT and not audit['native_recompiled'],'APK identity/native/signer mismatch')
 with zipfile.ZipFile(apk) as new,zipfile.ZipFile('baseline159/Infinity-'+OLD+'.apk') as old:
  protected={n for n in old.namelist() if n.startswith(('lib/','assets/','res/')) or n=='resources.arsc'}
  require(protected=={n for n in new.namelist() if n.startswith(('lib/','assets/','res/')) or n=='resources.arsc'},'Protected entry inventory changed')
  for name in protected:require(old.read(name)==new.read(name),'Protected APK entry changed: '+name)
  dex=b''.join(new.read(n) for n in new.namelist() if n.startswith('classes') and n.endswith('.dex'))
  for token in (b'CobraVisualTheme',b'CobraVisualRenderer',b'drawer.badge',b'visual-theme.json',b'cobra-visual-theme-controls'):require(token in dex,'Missing compiled visual feature')
  require(b'CobraVisualRuntimeTest' not in dex,'Test code packaged')
 Path('audit160/apk-verification.json').write_text(json.dumps({'apk_sha256':sha(apk),'protected_entries':len(protected),'signer':CERT,'native_recompiled':False,'official':False},indent=2)+'\n')
 print('PASS: signed 2103160 Android runtime; locked native/assets/resources retained')
def deliver():
 p=Path('audit160/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualRuntimeTest.xml');suite=ET.parse(p).getroot();cases=suite.findall('testcase')
 require(len(cases)==17 and all(int(suite.get(k,'0'))==0 for k in ('failures','errors','skipped')),'Visual runtime test suite incomplete')
 require(all(c.find(k) is None for c in cases for k in ('skipped','error','failure')),'Visual test skipped/failed')
 for name,count,folder in [('CobraNavigationUiTest',4,'cobra-regression'),('CobraHealthUiTest',7,'cobra-regression'),('Cobra2103159UiTest',2,'experience'),('ExperienceChooserUiTest',6,'experience')]:
  data=ET.parse(Path('audit159/android')/folder/'test-results'/('TEST-com.projectinfinity.kodi.'+name+'.xml')).getroot();require(len(data.findall('testcase'))==count and all(int(data.get(k,'0'))==0 for k in ('failures','errors','skipped')),'Inherited Android gate incomplete: '+name)
 layout=ET.parse(Path('audit160/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualLayoutTest.xml')).getroot();require(len(layout.findall('testcase'))==10 and all(int(layout.get(k,'0'))==0 for k in ('failures','errors','skipped')),'Layout/scene gate incomplete')
 require(sha('signed160/Infinity-'+NEW+'.apk')==json.loads(Path('audit160/apk-verification.json').read_text())['apk_sha256'],'APK changed after verification')
 shutil.copy2('audit160/visual-catalog.json','signed160/visual-catalog.json');shutil.copy2(ROOT/'AUDIT.md','signed160/AUDIT.md')
 result={'build':2103160,'base_commit':BASE,'visual_runtime':2,'visual_token_sites':len(json.loads(Path('audit160/visual-catalog.json').read_text())['slots']),'android_visual_tests':len(cases)+10,'inherited_android_tests':19,'native_recompiled':False,'physical_device_verified':False,'mockup_pixel_equivalence_verified':False,'all_possible_visual_edits_supported':False,'official':False,'candidate_locked':False,'status':'TEST CANDIDATE - not final visual acceptance'}
 Path('signed160/ACCEPTANCE.json').write_text(json.dumps(result,indent=2)+'\n');ledger(Path('signed160'));print('PASS: automated candidate gates. Physical/visual acceptance remains HOLD; no official lock.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['reconstruct','apply','verify','deliver']);a=p.parse_args();globals()[a.phase]()
