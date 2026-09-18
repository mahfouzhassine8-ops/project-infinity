#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,subprocess,zipfile,xml.etree.ElementTree as ET,shutil,importlib.util
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
 original=json.loads(Path('baseline162/background-resume-source.json').read_text())
 current=json.loads(Path('engine/background-resume-source.json').read_text())
 require(original['version_code']==current['version_code']==2103162,'Candidate 14 receipt identity drift')
 require(original['files'].keys()==current['files'].keys(),'Candidate 14 source inventory drift')
 require(sha('baseline162/Infinity-'+OLD+'.apk')=='c1558fdb0f2716c4b538c45e327103b02b5a423ceb4593cae548703d9a70e18b','Wrong Candidate 14 signed APK')
 for rel,row in original['files'].items():require(sha(Path('kodi')/rel)==row['after']==current['files'][rel]['after'],'Candidate 14 source drift: '+rel)
 rollback=Path('audit163/candidate14-source-rollback');rollback.mkdir(parents=True,exist_ok=True)
 for rel in original['files']:
  target=rollback/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(Path('kodi')/rel,target)
 shutil.copy2('engine/background-resume-source.json',rollback/'background-resume-source.json')
 run('python3',ROOT/'tests/source_tests.py','--source','kodi','--out','audit163/source-pre','--phase','pre')
 run('python3',ROOT/'apply.py','--source','kodi','--receipt','audit163/patch.json')
 run('python3',ROOT/'refine.py','--source','kodi','--receipt','audit163/patch.json','--out','audit163/refinement')
 run('python3',ROOT/'tests/source_tests.py','--source','kodi','--out','audit163/source-post','--phase','post')
 replace('kodi/tools/android/packaging/xbmc/build.gradle.in','versionCode 2103162',f'versionCode {VERSION}')
 replace('kodi/tools/android/packaging/xbmc/build.gradle.in','versionName "'+OLD+'"','versionName "'+NEW+'"')
 replace('scripts/infinity_background_resume.py','VERSION_CODE = 2103162',f'VERSION_CODE = {VERSION}')
 replace('scripts/infinity_background_resume.py',"RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'")
 p=Path('scripts/package_background_resume.py');s=p.read_text();old='Infinity-'+OLD
 require(s.count(old)==2,'packager release-name anchors changed');s=s.replace(old,'Infinity-'+NEW)
 guard_old="""    permissions=[n for n in new['children'] if n['tag']=='uses-permission' and
                 'android.permission.FOREGROUND_SERVICE_SPECIAL_USE' in n['attrs'].get('android:name','')]
    require(len(permissions)==1,'Exactly one background service permission required')
    new['children'].remove(permissions[0])"""
 guard_new="""    special=[n for n in new['children'] if n['tag']=='uses-permission' and
             'android.permission.FOREGROUND_SERVICE_SPECIAL_USE' in n['attrs'].get('android:name','')]
    media=[n for n in new['children'] if n['tag']=='uses-permission' and
           'android.permission.FOREGROUND_SERVICE_MEDIA_PLAYBACK' in n['attrs'].get('android:name','')]
    wake=[n for n in new['children'] if n['tag']=='uses-permission' and
          'android.permission.WAKE_LOCK' in n['attrs'].get('android:name','')]
    require(len(special)==len(media)==len(wake)==1,'Exactly one special-use, media-playback and wake-lock permission required')
    new['children'].remove(special[0]);new['children'].remove(media[0]);new['children'].remove(wake[0])"""
 require(s.count(guard_old)==1,'packager permission guard drift');s=s.replace(guard_old,guard_new,1)
 type_old="""    require(svc['attrs'].get('android:foregroundServiceType','').endswith('0x40000000'),'Wrong compiled foreground service type')"""
 type_new="""    require(svc['attrs'].get('android:foregroundServiceType','').endswith('0x40000002'),'Wrong compiled foreground service type; expected specialUse|mediaPlayback')"""
 require(s.count(type_old)==1,'packager foreground-type guard drift');s=s.replace(type_old,type_new,1);p.write_text(s)
 run('python3',ROOT/'tests/manifest_guards.py','--packager','scripts/package_background_resume.py','--baseline','baseline162','--out','audit163/manifest-guard-tests.json')
 receipt=Path('engine/background-resume-source.json');data=json.loads(receipt.read_text());patch=json.loads(Path('audit163/patch.json').read_text())
 require(data.get('version_code')==2103162,'Expected exact Candidate 14 source receipt')
 for rel,row in patch['files'].items():
  if rel in data['files']:data['files'][rel]['after']=row['after']
  else:data['files'][rel]={'before':row['before'],'after':row['after']}
 data['files']['tools/android/packaging/xbmc/build.gradle.in']['after']=sha('kodi/tools/android/packaging/xbmc/build.gradle.in')
 data.update(version_code=VERSION,version_name=NEW,locked_commit=BASE162,locked_parent=2103162,source_parent=2103162,source_parent_locked=True,candidate_locked=False,
             candidate14_preserved=True,player_settings_geometry_fix=True,complete_channel_groups=True,mini_background_native_media=True,
             fullscreen_pip_preserved=True,experience_compact_height=True,file_picker_choice=True,mixplorer_device_verified=False,native_engine_unchanged=True,physical_device_verified=False)
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
 require(len(cases)==count and all(int(root.get(k,'0'))==0 for k in ('failures','errors','skipped')),'Test suite incomplete '+str(p));require(all(c.find(k) is None for c in cases for k in ('failure','error','skipped')),'Failed/skipped testcase '+str(p));return len(cases)

def deliver():
 # Execute the new behavioral suite on the same compiled shell as the signed APK.
 target=Path('rotation-build/xbmc/src/test/java/com/projectinfinity/kodi/Cobra2103163AuditTest.java')
 shutil.copy2(ROOT/'tests/Cobra2103163AuditTest.java',target)
 path=Path('experience-delta/repairs/infinity-experience-2103159/tests/android.py')
 spec=importlib.util.spec_from_file_location('runner159_behavior',path);runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
 out=Path('audit163/behavior');env=runner.test_environment(out)
 runner.run_ui_gate(['./gradlew','--no-daemon','--console=plain',':xbmc:testReleaseUnitTest','--tests','com.projectinfinity.kodi.Cobra2103163AuditTest','--stacktrace'],Path('rotation-build'),env,out)
 inherited=0
 for name,count,folder in [('CobraNavigationUiTest',4,'cobra-regression'),('CobraHealthUiTest',7,'cobra-regression'),('Cobra2103159UiTest',2,'experience'),('ExperienceChooserUiTest',6,'experience')]:
  inherited+=suite(Path('audit159/android')/folder/'test-results'/('TEST-com.projectinfinity.kodi.'+name+'.xml'),count)
 inherited+=suite('audit163/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualRuntimeTest.xml',17)
 inherited+=suite('audit163/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualLayoutTest.xml',10)
 targeted=suite('audit163/theme-rotation/test-results/TEST-com.projectinfinity.kodi.Cobra2103162ThemeRotationTest.xml',16)
 behavior=suite('audit163/behavior/test-results/TEST-com.projectinfinity.kodi.Cobra2103163AuditTest.xml',29)
 require(json.loads(Path('audit163/source-post/source-tests.json').read_text())['passed'],'2103163 source acceptance failed')
 require(sha('signed163/Infinity-'+NEW+'.apk')==json.loads(Path('audit163/apk-verification.json').read_text())['apk_sha256'],'APK changed after verification')
 acceptance={'build':VERSION,'locked_parent':BASE162,'candidate14_untouched':True,'inherited_android_tests':inherited,'candidate14_targeted_tests':targeted,'behavioral_tests':behavior,
             'physical_binder_verified':False,'mixplorer_device_verified':False,
             'fixes':['player settings sheet anchored uniformly','provider channel groups normalized and channel cap expanded','mini-player-only native Android background media presence','compact-height experience chooser','system or installed Files app picker including MiXplorer-compatible chooser'],
             'fullscreen_pip_preserved':True,'native_recompiled':False,'physical_device_verified':False,'candidate_locked':False,'status':'TEST CANDIDATE - device acceptance required'}
 Path('signed163/ACCEPTANCE.json').write_text(json.dumps(acceptance,indent=2)+'\n')
 shutil.copy2(ROOT/'AUDIT.md','signed163/AUDIT.md');shutil.copy2('audit163/refinement/proof.json','signed163/refinement-proof.json');shutil.copy2('audit163/apk-verification.json','signed163/2103163-verification.json');shutil.copy2('audit163/source-post/source-tests.json','signed163/2103163-source-tests.json')
 print('PASS:',inherited+targeted+behavior,'Android tests plus 2103163 source gates; candidate ready for device acceptance')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['upgrade','verify','deliver']);a=p.parse_args();globals()[a.phase]()
