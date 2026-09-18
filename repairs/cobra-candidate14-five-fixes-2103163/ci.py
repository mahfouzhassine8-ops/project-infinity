#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,subprocess,zipfile,xml.etree.ElementTree as ET,shutil
ROOT=Path(__file__).resolve().parent
BASE162='1465eabb045badad56142642c48292df94caaa12'
OLD='1.0.9-Cobra-Theme-Switch-Player-Rotation-RC1'
NEW='1.0.9-Cobra-Candidate14-Five-Fixes-RC1'
VERSION=2103163
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(v,msg):
 if not v:raise RuntimeError(msg)
def run(*args):subprocess.run(list(map(str,args)),check=True)
def replace(path,old,new,count=1):
 p=Path(path);s=p.read_text();require(s.count(old)==count,f'identity anchor mismatch: {path} :: {old} ({s.count(old)})');p.write_text(s.replace(old,new,count) if count==1 else s.replace(old,new))

def upgrade():
 run('python3',ROOT/'tests/source_tests.py','--source','kodi','--out','audit163/source-pre','--phase','pre')
 run('python3',ROOT/'apply.py','--source','kodi','--receipt','audit163/patch.json')
 run('python3',ROOT/'tests/source_tests.py','--source','kodi','--out','audit163/source-post','--phase','post')
 replace('kodi/tools/android/packaging/xbmc/build.gradle.in','versionCode 2103162',f'versionCode {VERSION}')
 replace('kodi/tools/android/packaging/xbmc/build.gradle.in','versionName "'+OLD+'"','versionName "'+NEW+'"')
 replace('scripts/infinity_background_resume.py','VERSION_CODE = 2103162',f'VERSION_CODE = {VERSION}')
 replace('scripts/infinity_background_resume.py',"RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'")
 p=Path('scripts/package_background_resume.py');s=p.read_text();old='Infinity-'+OLD
 require(s.count(old)==2,'packager release-name anchors changed');p.write_text(s.replace(old,'Infinity-'+NEW))
 receipt=Path('engine/background-resume-source.json');data=json.loads(receipt.read_text());patch=json.loads(Path('audit163/patch.json').read_text())
 require(data.get('version_code')==2103162,'Expected exact Candidate 14 source receipt')
 for rel,row in patch['files'].items():
  if rel in data['files']:data['files'][rel]['after']=row['after']
  else:data['files'][rel]={'before':row['before'],'after':row['after']}
 data['files']['tools/android/packaging/xbmc/build.gradle.in']['after']=sha('kodi/tools/android/packaging/xbmc/build.gradle.in')
 data.update(version_code=VERSION,version_name=NEW,locked_commit=BASE162,locked_parent=2103162,source_parent=2103162,source_parent_locked=True,candidate_locked=False,
             candidate14_preserved=True,player_settings_geometry_fix=True,complete_channel_groups=True,mini_background_native_media=True,
             fullscreen_pip_preserved=True,experience_compact_height=True,file_picker_choice=True,mixplorer_compatible=True,native_engine_unchanged=True,physical_device_verified=False)
 receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
 with Path('audit163/native-after.patch').open('wb') as f:subprocess.run(['git','-C','kodi','diff','--binary','--','xbmc'],stdout=f,check=True)
 require(Path('audit163/native-after.patch').read_bytes()==Path('engine/native-before.patch').read_bytes(),'Native source changed')
 print('PASS: exact Candidate 14 -> 2103163 five-fix delta; native tree unchanged')

def verify():
 apk=Path('signed163/Infinity-'+NEW+'.apk');require(apk.is_file(),'Signed APK missing')
 audit=json.loads(Path('signed163/background-resume-apk-audit.json').read_text())
 require(audit['apk_sha256']==sha(apk) and audit['version_code']==VERSION and audit['signer_certificate_sha256']==CERT and not audit['native_recompiled'],'APK identity/native/signer mismatch')
 base=Path('baseline162/Infinity-'+OLD+'.apk');require(base.is_file(),'Candidate 14 baseline APK missing')
 with zipfile.ZipFile(apk) as new,zipfile.ZipFile(base) as old:
  protected={n for n in old.namelist() if n.startswith(('lib/','assets/','res/')) or n=='resources.arsc'}
  require(protected=={n for n in new.namelist() if n.startswith(('lib/','assets/','res/')) or n=='resources.arsc'},'Protected APK inventory changed')
  for name in protected:require(old.read(name)==new.read(name),'Protected APK entry changed: '+name)
  dex=b''.join(new.read(n) for n in new.namelist() if n.startswith('classes') and n.endswith('.dex'))
  for token in (b'PLAY IN BACKGROUND',b'MiXplorer',b'MINI_BACKGROUND_START',b'Files app chooser',b'cobra_mini_background_playback'):
   require(token in dex,'Missing compiled 2103163 contract: '+repr(token))
 Path('audit163/apk-verification.json').write_text(json.dumps({'apk_sha256':sha(apk),'protected_entries':len(protected),'signer':CERT,'native_recompiled':False,'base_candidate14':BASE162},indent=2)+'\n')
 print('PASS: signed 2103163; signer/native/assets/resources preserved from Candidate 14')

def suite(path,count):
 p=Path(path);require(p.is_file(),'Missing test suite '+str(p));root=ET.parse(p).getroot();cases=root.findall('testcase')
 require(len(cases)==count and all(int(root.get(k,'0'))==0 for k in ('failures','errors','skipped')),'Test suite incomplete '+str(p));return len(cases)

def deliver():
 inherited=0
 for name,count,folder in [('CobraNavigationUiTest',4,'cobra-regression'),('CobraHealthUiTest',7,'cobra-regression'),('Cobra2103159UiTest',2,'experience'),('ExperienceChooserUiTest',6,'experience')]:
  inherited+=suite(Path('audit159/android')/folder/'test-results'/('TEST-com.projectinfinity.kodi.'+name+'.xml'),count)
 inherited+=suite('audit160/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualRuntimeTest.xml',17)
 inherited+=suite('audit160/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualLayoutTest.xml',10)
 targeted=suite('audit163/theme-rotation/test-results/TEST-com.projectinfinity.kodi.Cobra2103162ThemeRotationTest.xml',16)
 require(json.loads(Path('audit163/source-post/source-tests.json').read_text())['passed'],'2103163 source acceptance failed')
 require(sha('signed163/Infinity-'+NEW+'.apk')==json.loads(Path('audit163/apk-verification.json').read_text())['apk_sha256'],'APK changed after verification')
 acceptance={'build':VERSION,'locked_parent':BASE162,'candidate14_untouched':True,'inherited_android_tests':inherited,'candidate14_targeted_tests':targeted,
             'fixes':['player settings sheet anchored uniformly','provider channel groups normalized and channel cap expanded','mini-player-only native Android background media presence','compact-height experience chooser','system or installed Files app picker including MiXplorer-compatible chooser'],
             'fullscreen_pip_preserved':True,'native_recompiled':False,'physical_device_verified':False,'candidate_locked':False,'status':'TEST CANDIDATE - device acceptance required'}
 Path('signed163/ACCEPTANCE.json').write_text(json.dumps(acceptance,indent=2)+'\n')
 shutil.copy2('audit163/apk-verification.json','signed163/2103163-verification.json');shutil.copy2('audit163/source-post/source-tests.json','signed163/2103163-source-tests.json')
 print('PASS:',inherited+targeted,'Android tests plus 2103163 source gates; candidate ready for device acceptance')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['upgrade','verify','deliver']);a=p.parse_args();globals()[a.phase]()
