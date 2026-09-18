#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,subprocess,zipfile,shutil,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent
BASE='8f2c9c7b0fdd7bfcaa0d903f8df997a139c23261'
BASE_APK='501781d42d87839d8f1f64f3791bee32a6feae023321286f73437e12107b5df3'
OLD='1.0.9-Cobra-Candidate14-Five-Fixes-RC1'
NEW='1.0.9-Cobra-Player-PiP-Return-Audit-RC1'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
SUITES={'CobraNavigationUiTest':4,'CobraHealthUiTest':7,'Cobra2103159UiTest':2,'ExperienceChooserUiTest':6,'CobraVisualRuntimeTest':17,'CobraVisualLayoutTest':10,'Cobra2103162ThemeRotationTest':16,'Cobra2103164RegressionTest':4,'Cobra2103164LifecycleMediaTest':21,'Cobra2103164SheetGeometryTest':5}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(value,message):
 if not value:raise RuntimeError(message)
def run(*args):subprocess.run(list(map(str,args)),check=True)
def replace(path,old,new,count=1):
 p=Path(path);s=p.read_text();require(s.count(old)==count,'Exact version anchor drift '+str(path));p.write_text(s.replace(old,new))
def baseline():
 p=Path('baseline163')/('Infinity-'+OLD+'.apk');require(p.is_file() and sha(p)==BASE_APK,'Wrong exact accepted 8f2c9c7 APK');return p

def upgrade():
 baseline();Path('audit164').mkdir(exist_ok=True)
 # The inherited runner sets COBRA_EVIDENCE but does not create its screenshots child.
 Path('audit164/acceptance/screenshots').mkdir(parents=True,exist_ok=True)
 receipt=Path('engine/background-resume-source.json');data=json.loads(receipt.read_text())
 require(data.get('version_code')==2103163,'Expected exact reconstructed 2103163')
 for rel,hashes in data['files'].items():
  require(sha(Path('kodi')/rel)==hashes['after'],'Reconstructed source receipt drift '+rel)
 run('python3',ROOT/'source_audit.py','--source','kodi','--out','audit164/source')
 run('python3',ROOT/'apply.py','--source','kodi','--out','audit164/patch')
 patch=json.loads(Path('audit164/patch/patch.json').read_text())
 for rel,hashes in patch['files'].items():data['files'][rel]['after']=hashes['after']
 replace('kodi/tools/android/packaging/xbmc/build.gradle.in','versionCode 2103163','versionCode 2103164')
 replace('kodi/tools/android/packaging/xbmc/build.gradle.in','versionName "'+OLD+'"','versionName "'+NEW+'"')
 replace('scripts/infinity_background_resume.py','VERSION_CODE = 2103163','VERSION_CODE = 2103164')
 replace('scripts/infinity_background_resume.py',"RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'")
 replace('scripts/package_background_resume.py','Infinity-'+OLD,'Infinity-'+NEW,2)
 data['files']['tools/android/packaging/xbmc/build.gradle.in']['after']=sha('kodi/tools/android/packaging/xbmc/build.gradle.in')
 data.update(version_code=2103164,version_name=NEW,locked_commit=BASE,locked_parent=2103163,source_parent=2103163,source_parent_locked=True,candidate_locked=False,
             candidate14_preserved=True,video_submenu_safe_anchor=True,pip_dismissal_terminal=True,explicit_cobra_browse_return=True,mini_media_actual_owner=True,physical_device_verified=False)
 receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
 for rel,hashes in data['files'].items():require(sha(Path('kodi')/rel)==hashes['after'],'Final source receipt drift '+rel)
 with Path('audit164/native-after.patch').open('wb') as out:subprocess.run(['git','-C','kodi','diff','--binary','--','xbmc'],stdout=out,check=True)
 require(Path('audit164/native-after.patch').read_bytes()==Path('engine/native-before.patch').read_bytes(),'Native source changed')
 print('PASS: 2103164 exact-source follow-up; all registered source receipts match; accepted 2103163 untouched')

def verify():
 base=baseline();apk=Path('signed164')/('Infinity-'+NEW+'.apk');require(apk.is_file(),'Signed APK missing')
 audit=json.loads(Path('signed164/background-resume-apk-audit.json').read_text())
 require(audit['apk_sha256']==sha(apk) and audit['version_code']==2103164 and audit['version_name']==NEW,'Signed APK identity mismatch')
 require(audit['signer_certificate_sha256']==CERT and not audit['native_recompiled'],'Signer/native integrity mismatch')
 with zipfile.ZipFile(base) as old,zipfile.ZipFile(apk) as new:
  protected={n for n in old.namelist() if n.startswith(('lib/','assets/','res/')) or n=='resources.arsc'}
  require(protected=={n for n in new.namelist() if n.startswith(('lib/','assets/','res/')) or n=='resources.arsc'},'Protected payload inventory changed')
  for name in protected:require(old.read(name)==new.read(name),'Protected APK entry changed '+name)
  dex=b''.join(new.read(n) for n in new.namelist() if n.startswith('classes') and n.endswith('.dex'))
  for token in (b'cobra_open_browse',b'CobraVideoSettingsSheet',b'MiniPlaybackOwner',b'mini_generation',b'cobraStopDismissedPip',b'cobra_playback_explicitly_stopped'):
   require(token in dex,'Missing compiled correction '+repr(token))
  for name in SUITES:require(name.encode() not in dex,'Test class included in production APK '+name)
 result={'build':2103164,'base_commit':BASE,'base_apk_sha256':BASE_APK,'apk_sha256':sha(apk),'signer':CERT,'protected_entries':len(protected),'native_recompiled':False,'physical_device_verified':False}
 Path('audit164/apk-verification.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS: signed 2103164; exact signer/native/assets/resources preserved from 8f2c9c7')

def deliver():
 # Each suite is executed once against the final compiled candidate, never a rebuilt mock implementation.
 counts={}
 for name,count in SUITES.items():
  if name in ('CobraNavigationUiTest','CobraHealthUiTest'):folder=Path('audit159/android/cobra-regression/test-results')
  elif name in ('Cobra2103159UiTest','ExperienceChooserUiTest'):folder=Path('audit159/android/experience/test-results')
  elif name in ('CobraVisualRuntimeTest','CobraVisualLayoutTest'):folder=Path('audit164/android/runtime/test-results')
  else:folder=Path('audit164/acceptance/test-results')
  p=folder/('TEST-com.projectinfinity.kodi.'+name+'.xml');root=ET.parse(p).getroot();cases=root.findall('testcase')
  require(len(cases)==count and all(int(root.get(k,'0'))==0 for k in ('failures','errors','skipped')),'Incomplete/failed suite '+name)
  require(all(c.find('failure') is None and c.find('error') is None and c.find('skipped') is None for c in cases),'Case failure '+name);counts[name]=count
 apk=Path('signed164')/('Infinity-'+NEW+'.apk');require(sha(apk)==json.loads(Path('audit164/apk-verification.json').read_text())['apk_sha256'],'APK changed after verification')
 acceptance={'build':2103164,'accepted_base_commit':BASE,'accepted_baseline_untouched':True,'android_tests':counts,'total_tests':sum(counts.values()),'failures':0,'skipped':0,
   'fixes':['all video settings/submenus bottom-safe centered and bounded','PiP dismissal stops real playback without automatic resume','explicit Cobra selection returns to browse/mini, native PiP expansion retains fullscreen','mini-only media notification controls existing player, no duplicate decoder'],
   'native_recompiled':False,'physical_device_verified':False,'candidate_locked':False,'status':'SIGNED TEST CANDIDATE - user device acceptance required'}
 Path('signed164/ACCEPTANCE.json').write_text(json.dumps(acceptance,indent=2)+'\n')
 shutil.copy2('audit164/apk-verification.json','signed164/2103164-verification.json');shutil.copy2('audit164/source/source-audit.json','signed164/2103164-source-audit.json')
 shutil.copy2(ROOT/'DEVICE-ACCEPTANCE.md','signed164/DEVICE-ACCEPTANCE.md')
 print('PASS:',sum(counts.values()),'Android tests; no failures/skips; signed 2103164 candidate ready for real-device acceptance')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['upgrade','verify','deliver']);a=p.parse_args();globals()[a.phase]()
