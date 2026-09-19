#!/usr/bin/env python3
"""Package/gate 2103181 timeshift transport integrity over exact passed 2103180."""
from pathlib import Path
import argparse,hashlib,json,re,shutil,subprocess,zipfile,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent
BASE_COMMIT='c7a52ef5553152d75f54b713e8975c8e2794e09b'
OLD='1.0.9-Cobra-Playback-Finalization-RC1'
NEW='1.0.9-Cobra-Timeshift-Transport-Integrity-RC1'
VERSION=2103181
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
 require(data.get('version_code')==2103180 and data.get('version_name')==OLD,'Expected exact passed 2103180 source receipt')
 for rel,row in data.get('files',{}).items():require(sha(Path('kodi')/rel)==row['after'],'2103180 source receipt drift: '+rel)
 run('python3',ROOT/'apply.py','--source','kodi','--receipt',receipt,'--out','audit181/patch')
 patch=json.loads(Path('audit181/patch/patch.json').read_text());data['files'][ACT]['after']=patch['files'][ACT]['after']
 gradle=Path('kodi/tools/android/packaging/xbmc/build.gradle.in');replace(gradle,'versionCode 2103180',f'versionCode {VERSION}');replace(gradle,'versionName "'+OLD+'"','versionName "'+NEW+'"')
 runtime=Path('scripts/infinity_background_resume.py');replace(runtime,'VERSION_CODE = 2103180',f'VERSION_CODE = {VERSION}');replace(runtime,"RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'")
 pack=Path('scripts/package_background_resume.py');s=pack.read_text();needle='Infinity-'+OLD;require(s.count(needle)>=2,'2103180 packager identity drift');pack.write_text(s.replace(needle,'Infinity-'+NEW))
 data['files']['tools/android/packaging/xbmc/build.gradle.in']['after']=sha(gradle)
 data.update(version_code=VERSION,version_name=NEW,source_parent=2103180,source_parent_locked=True,locked_parent_commit=BASE_COMMIT,candidate_locked=False,
   provider_read_timeout_ms=5000,live_reserve_ms=15000,segment_target_ms=3000,max_published_segment_ms=4500,
   segment_duration_excludes_network_idle=True,discontinuity_sequence_stable=True,retains_removed_segments_for_prior_snapshots=True,
   segment_404_diagnostics=True,provider_packet_age_diagnostics=True,latest_segment_age_diagnostics=True,
   unified_blue_timeline_preserved=True,phone_call_video_continuity_preserved=True,pro_buffer_safeguards_preserved=True,
   native_engine_recompiled=False,theme_zip_changed=False,physical_device_verified=False)
 receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
 for rel,row in data['files'].items():require(sha(Path('kodi')/rel)==row['after'],'Final 2103181 source receipt drift: '+rel)
 run('python3',ROOT/'source_audit.py','--source','kodi','--patch','audit181/patch/patch.json','--out','audit181/source-audit')
 with Path('audit181/native-after.patch').open('wb') as out:subprocess.run(['git','-C','kodi','diff','--binary','--','xbmc'],stdout=out,check=True)
 require(Path('audit181/native-after.patch').read_bytes()==Path('engine/native-before.patch').read_bytes(),'Native source changed')
 print('PASS: exact 2103180 -> 2103181 transport integrity; native tree preserved')
def verify():
 base=Path('baseline180/Infinity-'+OLD+'.apk');final=Path('signed181/Infinity-'+NEW+'.apk');require(base.is_file() and final.is_file(),'Baseline/final APK missing')
 bv=json.loads(Path('baseline180/2103180-verification.json').read_text());require(bv['apk_sha256']==sha(base),'Wrong exact passed 2103180 APK')
 audit=json.loads(Path('signed181/background-resume-apk-audit.json').read_text());require(audit['version_code']==VERSION and audit['version_name']==NEW,'Final 2103181 identity mismatch');require(audit['signer_certificate_sha256']==CERT and audit['apk_sha256']==sha(final),'Signer/hash mismatch');require(not audit['native_recompiled'],'Native engine was rebuilt')
 with zipfile.ZipFile(base) as old,zipfile.ZipFile(final) as new:
  old_native={n for n in old.namelist() if n.startswith('lib/') and not n.endswith('/')};new_native={n for n in new.namelist() if n.startswith('lib/') and not n.endswith('/')};require(old_native==new_native,'Native inventory changed')
  for n in old_native:require(old.read(n)==new.read(n),'Native entry changed: '+n)
  protected={n for n in old.namelist() if n.startswith(('assets/','res/')) or n=='resources.arsc'};require(protected=={n for n in new.namelist() if n.startswith(('assets/','res/')) or n=='resources.arsc'},'Protected resource inventory changed')
  for n in protected:require(old.read(n)==new.read(n),'Protected resource changed: '+n)
  dex=b''.join(new.read(n) for n in new.namelist() if re.fullmatch(r'classes\d*\.dex',n))
  for token in (b'EXT-X-DISCONTINUITY-SEQUENCE',b'publishedSegmentDurationMs',b'segment_404s',b'provider_packet_age_ms',b'cobra_unified_live_timeline',b'CobraCallAudioPolicy',b'buffer_observed_no_restart'):
   require(token in dex,'Combined 2103181 contract missing: '+repr(token))
 badging=Path('signed181/badging.txt').read_text();require("package: name='com.projectinfinity.kodi'" in badging and "versionCode='2103181'" in badging,'Final APK not forward-installable')
 result={'build':VERSION,'base_build':2103180,'base_commit':BASE_COMMIT,'base_apk_sha256':sha(base),'apk_sha256':sha(final),'signer':CERT,
   'native_entries':len(old_native),'protected_resource_entries':len(protected),'provider_read_timeout_ms':5000,'live_reserve_ms':15000,
   'segment_duration_excludes_network_idle':True,'discontinuity_sequence_stable':True,'retains_removed_segments_for_prior_snapshots':True,
   'unified_blue_timeline_preserved':True,'phone_call_video_continuity_preserved':True,'pro_buffer_safeguards_preserved':True,
   'native_engine_recompiled':False,'theme_zip_changed':False,'physical_device_verified':False}
 Path('audit181/final-verification.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS: signed 2103181 preserves exact 2103180 native/resources/signer')
def suite(path,count):
 p=Path(path);require(p.is_file(),'Missing test evidence '+str(p));root=ET.parse(p).getroot();cases=root.findall('testcase');require(len(cases)==count,f'Unexpected test count {p}: {len(cases)} != {count}');require(all(int(root.get(k,'0'))==0 for k in ('failures','errors','skipped')),'Failed/incomplete suite '+str(p));return count
def deliver():
 inherited=0
 for name,count,folder in [('CobraNavigationUiTest',4,'cobra-regression'),('CobraHealthUiTest',7,'cobra-regression'),('Cobra2103159UiTest',2,'experience'),('ExperienceChooserUiTest',6,'experience')]:inherited+=suite(Path('audit159/android')/folder/'test-results'/('TEST-com.projectinfinity.kodi.'+name+'.xml'),count)
 inherited+=suite('audit181/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualRuntimeTest.xml',17);inherited+=suite('audit181/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualLayoutTest.xml',10)
 targeted=0
 for name,count in [('Cobra2103162ThemeRotationTest',15),('Cobra2103164PlaybackStabilityTest',26),('Cobra2103165InsetsPipPlayerTest',6),('Cobra2103166EndToEndUiAuditTest',8),('Cobra2103170StatusBarRestoreSupersessionTest',5),('Cobra2103170StatusBarEdgeTest',7),('Cobra2103175FullscreenBackgroundTest',12),('Cobra2103176LiveRewindTest',5),('Cobra2103177FinalFeatureFreezeTest',10),('Cobra2103178TimeshiftMiniPlayerTest',10),('Cobra2103179BufferResilienceTest',11),('Cobra2103180PlaybackFinalizationTest',6),('Cobra2103181TimeshiftTransportIntegrityTest',6)]:targeted+=suite(Path('audit181/targeted/test-results')/('TEST-com.projectinfinity.kodi.'+name+'.xml'),count)
 total=inherited+targeted;require(total==173,f'Expected 173 Android tests, got {total}')
 source=json.loads(Path('audit181/source-audit/source-audit.json').read_text());final=json.loads(Path('audit181/final-verification.json').read_text());require(source.get('passed') and not source.get('failed'),'2103181 source audit failed')
 result={'build':VERSION,'locked_parent':2103180,'locked_parent_commit':BASE_COMMIT,'android_tests':total,'new_transport_integrity_tests':6,
   'segment_duration_excludes_network_idle':True,'discontinuity_sequence_stable':True,'retains_removed_segments_for_prior_snapshots':True,
   'unified_blue_timeline_preserved':True,'phone_call_video_continuity_preserved':True,'pro_buffer_safeguards_preserved':True,
   'native_engine_recompiled':False,'theme_zip_changed':False,'apk_sha256':final['apk_sha256'],'physical_device_verified':False,'candidate_locked':False,
   'status':'TEST CANDIDATE - VPN-off sustained playback and diagnostics required before lock'}
 Path('signed181/ACCEPTANCE.json').write_text(json.dumps(result,indent=2)+'\n');shutil.copy2('audit181/final-verification.json','signed181/2103181-verification.json');shutil.copy2('audit181/source-audit/source-audit.json','signed181/2103181-source-audit.json');print('PASS:',total,'Android tests + 2103181 integrity gates')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['upgrade','verify','deliver']);a=p.parse_args();globals()[a.phase]()
