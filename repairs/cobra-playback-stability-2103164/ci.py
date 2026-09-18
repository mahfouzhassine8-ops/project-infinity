#!/usr/bin/env python3
"""Reconstruct -> exact delta -> host tests -> Android shell -> immutable payload gates."""
from pathlib import Path
import argparse,hashlib,json,subprocess,zipfile,shutil,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent
BASE='8f2c9c7b0fdd7bfcaa0d903f8df997a139c23261'
LOCK='1465eabb045badad56142642c48292df94caaa12'
OLD='1.0.9-Cobra-Candidate14-Five-Fixes-RC1'
NEW='1.0.9-Cobra-Playback-Stability-RC1'
VERSION=2103164
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
BASE_APK_SHA='501781d42d87839d8f1f64f3791bee32a6feae023321286f73437e12107b5df3'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(v,message):
 if not v:raise RuntimeError(message)
def run(*args):subprocess.run(list(map(str,args)),check=True)
def replace(p,old,new,count=1):
 p=Path(p);s=p.read_text();require(s.count(old)==count,'Identity anchor drift: '+str(p)+' '+old);p.write_text(s.replace(old,new))
def upgrade():
 base=Path('baseline163/Infinity-'+OLD+'.apk');require(sha(base)==BASE_APK_SHA,'Not exact passed 2103163 APK')
 out=Path('audit164');out.mkdir(exist_ok=True)
 shutil.copy2('engine/background-resume-source.json',out/'source-receipt-before.json')
 run('python3',ROOT/'apply.py','--source','kodi','--out',out/'patch')
 run('python3',ROOT/'tests/host_tests.py','--source','kodi','--out',out/'host')
 replace('kodi/tools/android/packaging/xbmc/build.gradle.in','versionCode 2103163','versionCode 2103164')
 replace('kodi/tools/android/packaging/xbmc/build.gradle.in','versionName "'+OLD+'"','versionName "'+NEW+'"')
 replace('scripts/infinity_background_resume.py','VERSION_CODE = 2103163','VERSION_CODE = 2103164')
 replace('scripts/infinity_background_resume.py',"RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'")
 replace('scripts/package_background_resume.py','Infinity-'+OLD,'Infinity-'+NEW,2)
 receipt=Path('engine/background-resume-source.json');data=json.loads(receipt.read_text());require(data['version_code']==2103163,'Source parent changed')
 patch=json.loads((out/'patch/patch.json').read_text())
 for rel,row in patch['files'].items():
  require(data['files'][rel]['after']==row['before'],'Source receipt mismatch '+rel);data['files'][rel]['after']=row['after']
 data['files']['tools/android/packaging/xbmc/build.gradle.in']['after']=sha('kodi/tools/android/packaging/xbmc/build.gradle.in')
 data.update(version_code=VERSION,version_name=NEW,source_parent=2103163,source_parent_commit=BASE,source_parent_locked=False,locked_commit=LOCK,locked_parent=2103162,
   candidate_locked=False,candidate14_preserved=True,native_engine_unchanged=True,physical_device_verified=False,
   pip_background_exclusive=True,mini_media_controls=True,preview_options_anchored=True,playback_retry_generation=True)
 receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
 with (out/'native-after.patch').open('wb') as f:subprocess.run(['git','-C','kodi','diff','--binary','--','xbmc'],stdout=f,check=True)
 require((out/'native-after.patch').read_bytes()==Path('engine/native-before.patch').read_bytes(),'Native source changed')
 dest=out/'source-after';dest.mkdir(exist_ok=True)
 for rel in patch['files']:shutil.copy2(Path('kodi')/rel,dest/Path(rel).name)
 shutil.copy2(receipt,out/'source-receipt-after.json')
 print('PASS: exact 2103163 -> isolated 2103164 Android-only delta')
def verify():
 apk=Path('signed164/Infinity-'+NEW+'.apk');audit=json.loads(Path('signed164/background-resume-apk-audit.json').read_text())
 require(audit['apk_sha256']==sha(apk) and audit['version_code']==VERSION,'APK identity mismatch')
 require(audit['signer_certificate_sha256']==CERT and not audit['native_recompiled'],'Signer/native mismatch')
 proof={}
 with zipfile.ZipFile(apk) as new:
  for folder,name in [('baseline163',OLD),('baseline162','1.0.9-Cobra-Theme-Switch-Player-Rotation-RC1')]:
   base=Path(folder)/('Infinity-'+name+'.apk')
   if folder=='baseline163':require(sha(base)==BASE_APK_SHA,'Pre-audit APK changed')
   with zipfile.ZipFile(base) as old:
    protected={n for n in old.namelist() if n.startswith(('lib/','assets/','res/')) or n=='resources.arsc'}
    require(protected=={n for n in new.namelist() if n.startswith(('lib/','assets/','res/')) or n=='resources.arsc'},'Protected inventory mismatch')
    for n in protected:require(old.read(n)==new.read(n),'Protected bytes changed: '+n)
    proof[folder]={'apk_sha256':sha(base),'protected_entries':len(protected)}
  dex=b''.join(new.read(n) for n in new.namelist() if n.startswith('classes') and n.endswith('.dex'))
  for token in (b'CobraPlaybackPolicy',b'CobraSheetGeometry',b'MiniPlaybackOwner',b'MINI_MEDIA_COMMAND',b'cobra_preview_options_anchor',b'PLAY IN BACKGROUND',b'MiXplorer'):
   require(token in dex,'Missing compiled contract '+repr(token))
 proof.update(apk_sha256=sha(apk),version_code=VERSION,signer=CERT,native_recompiled=False)
 Path('audit164/apk-verification.json').write_text(json.dumps(proof,indent=2)+'\n');print('PASS: native/assets/resources identical to 2103163 and protected Candidate 14')
def suite(path,count):
 p=Path(path);require(p.is_file(),'Missing Android evidence '+str(p));r=ET.parse(p).getroot()
 require(len(r.findall('testcase'))==count and all(int(r.get(k,'0'))==0 for k in ('failures','errors','skipped')),'Incomplete Android suite '+str(p));return count
def deliver():
 total=0
 for name,count,folder in [('CobraNavigationUiTest',4,'cobra-regression'),('CobraHealthUiTest',7,'cobra-regression'),('Cobra2103159UiTest',2,'experience'),('ExperienceChooserUiTest',6,'experience')]:
  total+=suite(Path('audit159/android')/folder/'test-results'/('TEST-com.projectinfinity.kodi.'+name+'.xml'),count)
 for name,count in [('CobraVisualRuntimeTest',17),('CobraVisualLayoutTest',10)]:
  total+=suite(Path('audit164/android/runtime/test-results')/('TEST-com.projectinfinity.kodi.'+name+'.xml'),count)
 total+=suite('audit164/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103162ThemeRotationTest.xml',16)
 new=suite('audit164/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103164PlaybackStabilityTest.xml',26)
 host=json.loads(Path('audit164/host/host-tests.json').read_text());require(host['passed'] and host['cases']==25,'Host gate failed')
 proof=json.loads(Path('audit164/apk-verification.json').read_text());require(proof['apk_sha256']==sha('signed164/Infinity-'+NEW+'.apk'),'APK changed after verification')
 report={'build':VERSION,'base_commit':BASE,'protected_candidate14':LOCK,'candidate_locked':False,'inherited_android_tests':total,'new_android_tests':new,
   'host_scenarios':host['cases'],'random_geometry_cases':host['random_geometry_cases'],'source_wiring_checks':len(host['source_wiring_checks']),
   'native_recompiled':False,'physical_device_verified':False,'status':'TEST CANDIDATE - physical-device acceptance required'}
 Path('signed164/ACCEPTANCE.json').write_text(json.dumps(report,indent=2)+'\n')
 shutil.copy2('audit164/apk-verification.json','signed164/2103164-verification.json');shutil.copy2('audit164/host/host-tests.json','signed164/2103164-host-tests.json')
 shutil.copy2(ROOT/'AUDIT.md','signed164/AUDIT-2103164.md')
 # Replace the packager's inherited device checklist with the actual candidate acceptance contract.
 shutil.copy2(ROOT/'DEVICE-TEST.md','signed164/DEVICE-TEST.md')
 print('PASS:',total+new,'Android tests; Candidate 14 preserved; physical-device acceptance outstanding')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['upgrade','verify','deliver']);a=p.parse_args();globals()[a.phase]()
