#!/usr/bin/env python3
"""Package/gate 2103180 playback finalization over exact passed 2103179 without rebuilding native."""
from pathlib import Path
import argparse,hashlib,json,re,shutil,subprocess,zipfile,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent
BASE_COMMIT='0560b18c497e9861864126d96f9b784e488ebe32'
OLD='1.0.9-Cobra-Buffer-Resilience-RC1'
NEW='1.0.9-Cobra-Playback-Finalization-RC1'
VERSION=2103180
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
ACT='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(v,msg):
 if not v:raise RuntimeError(msg)
def replace(path,old,new,count=1):
 p=Path(path);s=p.read_text();require(s.count(old)==count,f'identity anchor drift {path}: {old} count={s.count(old)}');p.write_text(s.replace(old,new,count) if count==1 else s.replace(old,new))
def run(*args):subprocess.run(list(map(str,args)),check=True)
def upgrade():
 receipt=Path('engine/background-resume-source.json');data=json.loads(receipt.read_text())
 require(data.get('version_code')==2103179 and data.get('version_name')==OLD,'Expected exact passed 2103179 source receipt')
 for rel,row in data.get('files',{}).items():require(sha(Path('kodi')/rel)==row['after'],'2103179 source receipt drift: '+rel)
 run('python3',ROOT/'apply.py','--source','kodi','--receipt',receipt,'--out','audit180/patch')
 patch=json.loads(Path('audit180/patch/patch.json').read_text());data['files'][ACT]['after']=patch['files'][ACT]['after']
 gradle=Path('kodi/tools/android/packaging/xbmc/build.gradle.in');replace(gradle,'versionCode 2103179',f'versionCode {VERSION}');replace(gradle,'versionName "'+OLD+'"','versionName "'+NEW+'"')
 runtime=Path('scripts/infinity_background_resume.py');replace(runtime,'VERSION_CODE = 2103179',f'VERSION_CODE = {VERSION}');replace(runtime,"RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'")
 pack=Path('scripts/package_background_resume.py');s=pack.read_text();needle='Infinity-'+OLD;require(s.count(needle)>=2,'2103179 packager identity drift');pack.write_text(s.replace(needle,'Infinity-'+NEW))
 data['files']['tools/android/packaging/xbmc/build.gradle.in']['after']=sha(gradle)
 data.update(version_code=VERSION,version_name=NEW,source_parent=2103179,source_parent_locked=True,locked_parent_commit=BASE_COMMIT,candidate_locked=False,
   provider_read_timeout_ms=15000,live_reserve_ms=15000,live_target_min_ms=12000,live_target_max_ms=24000,
   single_unified_blue_timeline=True,yellow_scrubber_removed=True,phone_call_video_continuity=True,transient_focus_mutes_without_pause=True,
   media3_managed_focus_disabled=True,pro_buffer_safeguards_preserved=True,native_engine_recompiled=False,theme_zip_changed=False,physical_device_verified=False)
 receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
 for rel,row in data['files'].items():require(sha(Path('kodi')/rel)==row['after'],'Final 2103180 source receipt drift: '+rel)
 run('python3',ROOT/'source_audit.py','--source','kodi','--patch','audit180/patch/patch.json','--out','audit180/source-audit')
 with Path('audit180/native-after.patch').open('wb') as out:subprocess.run(['git','-C','kodi','diff','--binary','--','xbmc'],stdout=out,check=True)
 require(Path('audit180/native-after.patch').read_bytes()==Path('engine/native-before.patch').read_bytes(),'Native source changed')
 print('PASS: exact 2103179 -> 2103180 playback finalization; native tree preserved')
def verify():
 base=Path('baseline179/Infinity-'+OLD+'.apk');final=Path('signed180/Infinity-'+NEW+'.apk');require(base.is_file() and final.is_file(),'Baseline/final APK missing')
 bv=json.loads(Path('baseline179/2103179-verification.json').read_text());require(bv['apk_sha256']==sha(base),'Wrong exact passed 2103179 APK')
 audit=json.loads(Path('signed180/background-resume-apk-audit.json').read_text());require(audit['version_code']==VERSION and audit['version_name']==NEW,'Final 2103180 identity mismatch');require(audit['signer_certificate_sha256']==CERT and audit['apk_sha256']==sha(final),'Signer/hash mismatch');require(not audit['native_recompiled'],'Native engine was rebuilt')
 with zipfile.ZipFile(base) as old,zipfile.ZipFile(final) as new:
  old_native={n for n in old.namelist() if n.startswith('lib/') and not n.endswith('/')};new_native={n for n in new.namelist() if n.startswith('lib/') and not n.endswith('/')};require(old_native==new_native,'Native inventory changed')
  for n in old_native:require(old.read(n)==new.read(n),'Native entry changed: '+n)
  protected={n for n in old.namelist() if n.startswith(('assets/','res/')) or n=='resources.arsc'};require(protected=={n for n in new.namelist() if n.startswith(('assets/','res/')) or n=='resources.arsc'},'Protected resource inventory changed')
  for n in protected:require(old.read(n)==new.read(n),'Protected resource changed: '+n)
  dex=b''.join(new.read(n) for n in new.namelist() if re.fullmatch(r'classes\d*\.dex',n))
  for token in (b'TIME-OFFSET=-15.0',b'LIVE_RESERVE_MS',b'cobra_unified_live_timeline',b'Live TV timeline',b'CobraCallAudioPolicy',b'video_preserved=true',b'buffer_observed_no_restart',b'MAX_AUTO_LIVE_EDGE_ATTEMPTS'):
   require(token in dex,'Combined 2103180 contract missing: '+repr(token))
  require(b'Cobra2103180PlaybackFinalizationTest' not in dex,'2103180 test code packaged in release APK')
 badging=Path('signed180/badging.txt').read_text();require("package: name='com.projectinfinity.kodi'" in badging and "versionCode='2103180'" in badging,'Final APK is not installable forward update')
 result={'build':VERSION,'base_build':2103179,'base_commit':BASE_COMMIT,'base_apk_sha256':sha(base),'apk_sha256':sha(final),'signer':CERT,'native_entries':len(old_native),'protected_resource_entries':len(protected),'provider_read_timeout_ms':15000,'live_reserve_ms':15000,'single_unified_blue_timeline':True,'yellow_scrubber_removed':True,'phone_call_video_continuity':True,'pro_buffer_safeguards_preserved':True,'native_engine_recompiled':False,'theme_zip_changed':False,'physical_device_verified':False}
 Path('audit180/final-verification.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS: signed 2103180 preserves exact 2103179 native/resources/signer')
def suite(path,count):
 p=Path(path);require(p.is_file(),'Missing test evidence '+str(p));root=ET.parse(p).getroot();cases=root.findall('testcase');require(len(cases)==count,f'Unexpected test count {p}: {len(cases)} != {count}');require(all(int(root.get(k,'0'))==0 for k in ('failures','errors','skipped')),'Failed/incomplete suite '+str(p));return count
def deliver():
 inherited=0
 for name,count,folder in [('CobraNavigationUiTest',4,'cobra-regression'),('CobraHealthUiTest',7,'cobra-regression'),('Cobra2103159UiTest',2,'experience'),('ExperienceChooserUiTest',6,'experience')]:inherited+=suite(Path('audit159/android')/folder/'test-results'/('TEST-com.projectinfinity.kodi.'+name+'.xml'),count)
 inherited+=suite('audit180/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualRuntimeTest.xml',17);inherited+=suite('audit180/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualLayoutTest.xml',10)
 targeted=0
 for name,count in [('Cobra2103162ThemeRotationTest',15),('Cobra2103164PlaybackStabilityTest',26),('Cobra2103165InsetsPipPlayerTest',6),('Cobra2103166EndToEndUiAuditTest',8),('Cobra2103170StatusBarRestoreSupersessionTest',5),('Cobra2103170StatusBarEdgeTest',7),('Cobra2103175FullscreenBackgroundTest',12),('Cobra2103176LiveRewindTest',5),('Cobra2103177FinalFeatureFreezeTest',10),('Cobra2103178TimeshiftMiniPlayerTest',10),('Cobra2103179BufferResilienceTest',11),('Cobra2103180PlaybackFinalizationTest',6)]:targeted+=suite(Path('audit180/targeted/test-results')/('TEST-com.projectinfinity.kodi.'+name+'.xml'),count)
 total=inherited+targeted;require(total==167,f'Expected 167 Android tests, got {total}')
 source=json.loads(Path('audit180/source-audit/source-audit.json').read_text());final=json.loads(Path('audit180/final-verification.json').read_text());require(source.get('passed') and not source.get('failed'),'2103180 source audit failed')
 result={'build':VERSION,'locked_parent':2103179,'locked_parent_commit':BASE_COMMIT,'android_tests':total,'new_playback_finalization_tests':6,'provider_read_timeout_ms':15000,'live_reserve_ms':15000,'single_unified_blue_timeline':True,'yellow_scrubber_removed':True,'phone_call_video_continuity':True,'pro_buffer_safeguards_preserved':True,'native_engine_recompiled':False,'theme_zip_changed':False,'apk_sha256':final['apk_sha256'],'physical_device_verified':False,'candidate_locked':False,'status':'TEST CANDIDATE - VPN-off buffering, call-continuity, unified-timeline physical verification required before lock'}
 Path('signed180/ACCEPTANCE.json').write_text(json.dumps(result,indent=2)+'\n');shutil.copy2('audit180/final-verification.json','signed180/2103180-verification.json');shutil.copy2('audit180/source-audit/source-audit.json','signed180/2103180-source-audit.json');print('PASS:',total,'Android tests + 2103180 integrity gates')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['upgrade','verify','deliver']);a=p.parse_args();globals()[a.phase]()
