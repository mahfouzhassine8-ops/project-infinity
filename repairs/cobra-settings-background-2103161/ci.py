#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,subprocess,zipfile,xml.etree.ElementTree as ET,shutil
ROOT=Path(__file__).resolve().parent
BASE160='42b1afc95a07b3ce0f534232e0f774c5159ddec1'
OLD='1.0.9-Cobra-Visual-Theme-Runtime-v2-RC1'
NEW='1.0.9-Cobra-Settings-Theme-Background-RC1'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(v,msg):
 if not v:raise RuntimeError(msg)
def run(*args):subprocess.run(list(map(str,args)),check=True)
def replace(path,old,new):
 p=Path(path);s=p.read_text();require(s.count(old)==1,'version/identity anchor mismatch: '+str(path)+' :: '+old);p.write_text(s.replace(old,new,1))
def upgrade():
 run('python3',ROOT/'tests/source_tests.py','--source','kodi','--out','audit161/source')
 run('python3',ROOT/'apply.py','--source','kodi','--receipt','audit161/patch.json')
 replace('kodi/tools/android/packaging/xbmc/build.gradle.in','versionCode 2103160','versionCode 2103161')
 replace('kodi/tools/android/packaging/xbmc/build.gradle.in','versionName "'+OLD+'"','versionName "'+NEW+'"')
 replace('scripts/infinity_background_resume.py','VERSION_CODE = 2103160','VERSION_CODE = 2103161')
 replace('scripts/infinity_background_resume.py',"RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'")
 replace('scripts/package_background_resume.py','Infinity-'+OLD,'Infinity-'+NEW)
 receipt=Path('engine/background-resume-source.json');data=json.loads(receipt.read_text());patch=json.loads(Path('audit161/patch.json').read_text())
 require(data.get('version_code')==2103160,'Expected exact 2103160 source receipt')
 for rel,row in patch['files'].items():data['files'][rel]={'before':row['before'],'after':row['after']}
 data['files']['tools/android/packaging/xbmc/build.gradle.in']['after']=sha('kodi/tools/android/packaging/xbmc/build.gradle.in')
 data.update(version_code=2103161,version_name=NEW,locked_commit=BASE160,locked_parent=2103160,source_parent=2103160,source_parent_locked=True,candidate_locked=False,cobra_settings_control_removed=False,background_mode_settings_restored=True,visible_visual_theme_recovery=True,visual_theme_safe_area=True,physical_device_verified=False)
 receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
 with Path('audit161/native-after.patch').open('wb') as f:subprocess.run(['git','-C','kodi','diff','--binary','--','xbmc'],stdout=f,check=True)
 require(Path('audit161/native-after.patch').read_bytes()==Path('engine/native-before.patch').read_bytes(),'Native source changed')
 print('PASS: exact 2103160 upgraded to 2103161; playback/native methods preserved')
def verify():
 apk=Path('signed161/Infinity-'+NEW+'.apk');require(apk.is_file(),'Signed APK missing')
 audit=json.loads(Path('signed161/background-resume-apk-audit.json').read_text())
 require(audit['apk_sha256']==sha(apk),'APK audit digest mismatch');require(audit['version_code']==2103161,'Wrong version code');require(audit['signer_certificate_sha256']==CERT,'Signer changed');require(not audit['native_recompiled'],'Native engine was rebuilt')
 base=Path('baseline160/Infinity-'+OLD+'.apk');require(base.is_file(),'Locked 2103160 baseline APK missing')
 with zipfile.ZipFile(base) as old,zipfile.ZipFile(apk) as new:
  protected={n for n in old.namelist() if n.startswith(('lib/','assets/','res/')) or n=='resources.arsc'}
  require(protected=={n for n in new.namelist() if n.startswith(('lib/','assets/','res/')) or n=='resources.arsc'},'Protected APK inventory changed')
  for name in protected:require(old.read(name)==new.read(name),'Protected APK payload changed: '+name)
  dex=b''.join(new.read(n) for n in new.namelist() if n.startswith('classes') and n.endswith('.dex'))
  for token in (b'BACKGROUND MODE',b'PREVIOUS VISUAL THEME',b'REMOVE VISUAL THEME',b'cobra-background-mode:extended',b'cobra-visual-theme-controls:previous'):
   require(token in dex,'Missing compiled 2103161 control: '+repr(token))
  require(b'Cobra2103161SettingsTest' not in dex,'Test code packaged')
 result={'build':2103161,'apk_sha256':sha(apk),'baseline_2103160_sha256':sha(base),'protected_entries':len(protected),'signer':CERT,'native_recompiled':False,'official':False}
 Path('audit161/apk-verification.json').write_text(json.dumps(result,indent=2)+'\n')
 print('PASS: signed 2103161; signer and protected native/assets/resources match locked 2103160')
def parse(path,count):
 root=ET.parse(path).getroot();cases=root.findall('testcase');require(len(cases)==count,'Unexpected test count '+str(path));require(all(int(root.get(k,'0'))==0 for k in ('failures','errors','skipped')),'Failed/skipped tests '+str(path));require(all(c.find('failure') is None and c.find('error') is None and c.find('skipped') is None for c in cases),'Case failed/skipped '+str(path));return len(cases)
def deliver():
 inherited=0
 inherited+=parse('audit159/android/cobra-regression/test-results/TEST-com.projectinfinity.kodi.CobraNavigationUiTest.xml',4)
 inherited+=parse('audit159/android/cobra-regression/test-results/TEST-com.projectinfinity.kodi.CobraHealthUiTest.xml',7)
 inherited+=parse('audit159/android/experience/test-results/TEST-com.projectinfinity.kodi.Cobra2103159UiTest.xml',2)
 inherited+=parse('audit159/android/experience/test-results/TEST-com.projectinfinity.kodi.ExperienceChooserUiTest.xml',6)
 inherited+=parse('audit161/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualRuntimeTest.xml',17)
 inherited+=parse('audit161/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualLayoutTest.xml',10)
 new=parse('audit161/settings/test-results/TEST-com.projectinfinity.kodi.Cobra2103161SettingsTest.xml',5)
 result={'build':2103161,'base_build':2103160,'base_commit':BASE160,'inherited_android_tests':inherited,'new_android_tests':new,'total_android_tests':inherited+new,'background_mode_contract':'NORMAL / EXTENDED using existing InfinityExtendedBackgroundService','theme_management':'visible Previous Visual Theme and Remove Visual Theme controls','chooser_safe_area':'system bar insets','native_recompiled':False,'physical_device_verified':False,'official':False,'status':'SIGNED TEST CANDIDATE - device acceptance pending'}
 Path('signed161/ACCEPTANCE.json').write_text(json.dumps(result,indent=2)+'\n')
 shutil.copy2('audit161/apk-verification.json','signed161/2103161-verification.json');shutil.copy2('audit161/source/source-tests.json','signed161/2103161-source-tests.json')
 rollback=Path('rollback161');rollback.mkdir(exist_ok=True);shutil.copytree('baseline160',rollback/'locked-2103160-artifact',dirs_exist_ok=True);(rollback/'README.txt').write_text('Exact locked 2103160 signed candidate artifact preserved before 2103161. Do not uninstall or clear app data to force downgrade. Visual theme 2.0.3 remains separately locked.\n')
 print('PASS:',inherited+new,'Android tests; candidate ready for device install, not yet official')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['upgrade','verify','deliver']);a=p.parse_args();globals()[a.phase]()
