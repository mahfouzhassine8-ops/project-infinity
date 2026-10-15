#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,subprocess,zipfile,xml.etree.ElementTree as ET,shutil

ROOT=Path(__file__).resolve().parent
BASE161='0ff8b5463ae6adf26ef0f20d64bc1b10f6c5a593'
OLD='1.0.9-Cobra-Settings-Theme-Background-RC1'
NEW='1.0.9-Cobra-Theme-Switch-Player-Rotation-RC1'
VERSION=2103162
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(v,msg):
 if not v:raise RuntimeError(msg)
def run(*args):subprocess.run(list(map(str,args)),check=True)
def replace(path,old,new,count=1):
 p=Path(path);s=p.read_text();require(s.count(old)==count,f'identity anchor mismatch: {path} :: {old} ({s.count(old)})');p.write_text(s.replace(old,new,count) if count==1 else s.replace(old,new))

def upgrade():
 run('python3',ROOT/'tests/source_tests.py','--source','kodi','--out','audit162/source')
 run('python3',ROOT/'apply.py','--source','kodi','--receipt','audit162/patch.json')
 run('python3',ROOT/'harden.py','--source','kodi','--receipt','audit162/patch.json','--out','audit162/hardening')

 replace('kodi/tools/android/packaging/xbmc/build.gradle.in','versionCode 2103161',f'versionCode {VERSION}')
 replace('kodi/tools/android/packaging/xbmc/build.gradle.in','versionName "'+OLD+'"','versionName "'+NEW+'"')
 replace('scripts/infinity_background_resume.py','VERSION_CODE = 2103161',f'VERSION_CODE = {VERSION}')
 replace('scripts/infinity_background_resume.py',"RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'")
 p=Path('scripts/package_background_resume.py');s=p.read_text();old='Infinity-'+OLD
 require(s.count(old)==2,'packager release-name anchors changed');p.write_text(s.replace(old,'Infinity-'+NEW))

 receipt=Path('engine/background-resume-source.json');data=json.loads(receipt.read_text());patch=json.loads(Path('audit162/patch.json').read_text())
 require(data.get('version_code')==2103161,'Expected exact 2103161 source receipt')
 for rel,row in patch['files'].items():data['files'][rel]={'before':row['before'],'after':row['after']}
 data['files']['tools/android/packaging/xbmc/build.gradle.in']['after']=sha('kodi/tools/android/packaging/xbmc/build.gradle.in')
 data.update(version_code=VERSION,version_name=NEW,locked_commit=BASE161,locked_parent=2103161,source_parent=2103161,source_parent_locked=True,
             candidate_locked=False,theme_setting_consolidated=True,cobra_player_rotation=True,
             infinity_rotation_contract_reused=True,global_rotation_setting_mutated=False,native_engine_unchanged=True,
             physical_device_verified=False,single_cobra_rotation_owner=True)
 receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
 with Path('audit162/native-after.patch').open('wb') as f:subprocess.run(['git','-C','kodi','diff','--binary','--','xbmc'],stdout=f,check=True)
 require(Path('audit162/native-after.patch').read_bytes()==Path('engine/native-before.patch').read_bytes(),'Native source changed')
 print('PASS: exact locked 2103161 -> 2103162 theme/rotation delta; native tree unchanged')

def verify():
 apk=Path('signed162/Infinity-'+NEW+'.apk');require(apk.is_file(),'Signed APK missing')
 audit=json.loads(Path('signed162/background-resume-apk-audit.json').read_text())
 require(audit['apk_sha256']==sha(apk),'APK audit digest mismatch')
 require(audit['version_code']==VERSION,'Wrong version code')
 require(audit['version_name']==NEW,'Wrong version name')
 require(audit['signer_certificate_sha256']==CERT,'Signer changed')
 require(not audit['native_recompiled'],'Native engine was rebuilt')

 base=Path('baseline161/Infinity-'+OLD+'.apk');require(base.is_file(),'Locked 2103161 baseline APK missing')
 with zipfile.ZipFile(base) as old,zipfile.ZipFile(apk) as new:
  protected={n for n in old.namelist() if n.startswith(('lib/','assets/','res/')) or n=='resources.arsc'}
  current={n for n in new.namelist() if n.startswith(('lib/','assets/','res/')) or n=='resources.arsc'}
  require(protected==current,'Protected APK inventory changed')
  for name in protected:require(old.read(name)==new.read(name),'Protected APK payload changed: '+name)
  dex=b''.join(new.read(n) for n in new.namelist() if n.startswith('classes') and n.endswith('.dex'))
  # Java inlines ActivityInfo orientation constants as integers. Actual Android
  # acceptance below proves FULL_SENSOR -> UNSPECIFIED behavior directly.
  for token in (b'cobra_player_rotation',b'infinity_player_rotation',b'Installed visual theme',
                b'Built-in appearance',b'Player rotation',b'setPlayerRotationEligible'):
   require(token in dex,'Missing compiled 2103162 contract: '+repr(token))
  for forbidden in (b'Cobra2103162ThemeRotationTest',b'ACCELEROMETER_ROTATION'):
   require(forbidden not in dex,'Forbidden/test token packaged: '+repr(forbidden))

 result={'build':VERSION,'apk_sha256':sha(apk),'baseline_2103161_sha256':sha(base),
         'protected_entries':len(protected),'signer':CERT,'native_recompiled':False,
         'global_auto_rotate_mutated':False,'official':False}
 Path('audit162/apk-verification.json').write_text(json.dumps(result,indent=2)+'\n')
 print('PASS: signed 2103162; exact signer/native/assets/resources preserved from locked 2103161')

def suite(path,count):
 root=ET.parse(path).getroot();cases=root.findall('testcase')
 require(len(cases)==count,f'Unexpected test count {path}: {len(cases)}')
 require(all(int(root.get(k,'0'))==0 for k in ('failures','errors','skipped')),f'Failed/skipped tests: {path}')
 require(all(c.find('failure') is None and c.find('error') is None and c.find('skipped') is None for c in cases),f'Case failure: {path}')
 return len(cases)

def deliver():
 inherited=suite('audit159/android/cobra-regression/test-results/TEST-com.projectinfinity.kodi.CobraNavigationUiTest.xml',4)
 inherited+=suite('audit159/android/cobra-regression/test-results/TEST-com.projectinfinity.kodi.CobraHealthUiTest.xml',7)
 inherited+=suite('audit159/android/experience/test-results/TEST-com.projectinfinity.kodi.Cobra2103159UiTest.xml',2)
 inherited+=suite('audit159/android/experience/test-results/TEST-com.projectinfinity.kodi.ExperienceChooserUiTest.xml',6)
 inherited+=suite('audit162/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualRuntimeTest.xml',17)
 inherited+=suite('audit162/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualLayoutTest.xml',10)
 require(inherited==46,'Inherited Android count drift')
 new=suite('audit162/theme-rotation/test-results/TEST-com.projectinfinity.kodi.Cobra2103162ThemeRotationTest.xml',16)

 result={'build':VERSION,'base_build':2103161,'base_commit':BASE161,
         'inherited_android_tests':inherited,'new_or_updated_android_tests':new,
         'total_android_tests':inherited+new,
         'theme_management':'one Theme row: built-in / same installed theme / install-replace ZIP',
         'rotation':'Cobra player button delegates to the existing InfinityCobraDeviceBridge',
         'single_cobra_rotation_owner':True,'background_mode_preserved':True,'chooser_safe_area_preserved':True,
         'native_recompiled':False,'physical_device_verified':False,'official':False,
         'status':'SIGNED TEST CANDIDATE - device acceptance pending'}
 Path('signed162/ACCEPTANCE.json').write_text(json.dumps(result,indent=2)+'\n')
 shutil.copy2('audit162/apk-verification.json','signed162/2103162-verification.json')
 shutil.copy2('audit162/source/source-tests.json','signed162/2103162-source-tests.json')
 shutil.copy2('audit162/hardening/source-audit.json','signed162/2103162-hardening-audit.json')
 rollback=Path('rollback162');rollback.mkdir(exist_ok=True)
 shutil.copytree('baseline161',rollback/'locked-2103161-artifact',dirs_exist_ok=True)
 (rollback/'README.txt').write_text('Exact locked 2103161 signed artifact preserved before 2103162. HM Theme 2.0.3 remains separately locked. Do not uninstall or clear data to force downgrade.\n')
 print('PASS:',inherited+new,'Android tests; signed 2103162 candidate ready for device acceptance')

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['upgrade','verify','deliver']);args=parser.parse_args();globals()[args.phase]()
