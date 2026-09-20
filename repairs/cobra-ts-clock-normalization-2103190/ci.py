#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,re,shutil,subprocess,zipfile,xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
BASE_COMMIT='af44c82189b37312abf5f75d9237eef1e3d89dc8'
OLD='1.0.9-Cobra-TS-Timeline-Fingerprint-RC1'
NEW='1.0.9-Cobra-TS-Clock-Normalization-RC1'
VERSION=2103190
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
ACT='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
GRADLE='tools/android/packaging/xbmc/build.gradle.in'

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(v,msg):
    if not v: raise RuntimeError(msg)
def run(*args): subprocess.run(list(map(str,args)),check=True)
def replace(path,old,new):
    p=Path(path); s=p.read_text(); require(s.count(old)==1,'identity anchor drift: '+old); p.write_text(s.replace(old,new,1))

def upgrade():
    receipt=Path('engine/background-resume-source.json'); data=json.loads(receipt.read_text())
    require(data.get('version_code')==2103189 and data.get('version_name')==OLD,'Expected exact passed 2103189 source receipt')
    for rel,row in data.get('files',{}).items():
        require(sha(Path('kodi')/rel)==row['after'],'2103189 source drift: '+rel)
    run('python3',ROOT/'apply.py','--source','kodi','--receipt',receipt,'--out','audit190/patch')
    patch=json.loads(Path('audit190/patch/patch.json').read_text()); data['files'][ACT]['after']=patch['files'][ACT]['after']

    gradle=Path('kodi')/GRADLE
    replace(gradle,'versionCode 2103189',f'versionCode {VERSION}')
    replace(gradle,'versionName "'+OLD+'"','versionName "'+NEW+'"')
    runtime=Path('scripts/infinity_background_resume.py')
    replace(runtime,'VERSION_CODE = 2103189',f'VERSION_CODE = {VERSION}')
    replace(runtime,"RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'")
    pack=Path('scripts/package_background_resume.py'); s=pack.read_text(); needle='Infinity-'+OLD
    require(s.count(needle)>=2,'2103189 packager identity drift'); pack.write_text(s.replace(needle,'Infinity-'+NEW))

    data['files'][GRADLE]['after']=sha(gradle)
    data.update(version_code=VERSION,version_name=NEW,source_parent=2103189,source_parent_locked=True,locked_parent_commit=BASE_COMMIT,candidate_locked=False,
      ts_extractor_profile='DETECT_ACCESS_UNITS+ALLOW_NON_IDR_KEYFRAMES',ts_detect_access_units=True,ts_allow_non_idr_keyframes=True,
      playback_behavior_changed=True,network_selection_changed=False,timeshift_ownership_changed=False,buffer_policy_changed=False,parser_flags_changed=False,
      stream_fingerprint_schema=5,cadence_diagnostics_preserved=True,frozen_live_snapshot=True,seamless_live_proxy=True,
      timeline_probe_only=False,pat_pmt_probe=True,video_pts_probe=True,video_dts_probe=True,audio_pts_probe=True,av_drift_probe=True,h264_nal_probe=True,intra_cadence_probe=True,rebuffer_timeline_correlation=True,
      conditional_clock_normalization=True,activation_min_wall_ms=5000,activation_rate_permille=[450,800],activation_track_delta_permille=35,normalizes_pcr=True,normalizes_pts=True,normalizes_dts=True,preserves_good_stream_raw_proxy_until_detection=True,normalizes_rewind_segments_after_activation=True,
      happy_eyeballs_style_auto=True,manual_ipv4_ipv6_preserved=True,native_engine_recompiled=False,theme_zip_changed=False,physical_device_verified=False)
    receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')

    for rel,row in data['files'].items():
        require(sha(Path('kodi')/rel)==row['after'],'Final 2103190 source drift: '+rel)
    run('python3',ROOT/'source_audit.py','--source','kodi','--patch','audit190/patch/patch.json','--out','audit190/source-audit')
    with Path('audit190/native-after.patch').open('wb') as out:
        subprocess.run(['git','-C','kodi','diff','--binary','--','xbmc'],stdout=out,check=True)
    require(Path('audit190/native-after.patch').read_bytes()==Path('engine/native-before.patch').read_bytes(),'Native source changed')
    print('PASS: exact 2103189 -> 2103190 conditional TS clock normalization; native tree preserved')

def verify():
    base=Path('baseline189/Infinity-'+OLD+'.apk'); final=Path('signed190/Infinity-'+NEW+'.apk')
    require(base.is_file() and final.is_file(),'APK missing')
    bv=json.loads(Path('baseline189/2103189-verification.json').read_text())
    require(bv['apk_sha256']==sha(base),'Wrong exact passed 2103189 APK')
    audit=json.loads(Path('signed190/background-resume-apk-audit.json').read_text())
    require(audit['version_code']==VERSION and audit['version_name']==NEW,'2103190 identity mismatch')
    require(audit['signer_certificate_sha256']==CERT and audit['apk_sha256']==sha(final),'Signer/hash mismatch')
    require(not audit['native_recompiled'],'Native rebuilt')

    with zipfile.ZipFile(base) as old,zipfile.ZipFile(final) as new:
        native={n for n in old.namelist() if n.startswith('lib/') and not n.endswith('/')}
        require(native=={n for n in new.namelist() if n.startswith('lib/') and not n.endswith('/')},'Native inventory changed')
        for n in native: require(old.read(n)==new.read(n),'Native changed: '+n)
        protected={n for n in old.namelist() if n.startswith(('assets/','res/')) or n=='resources.arsc'}
        require(protected=={n for n in new.namelist() if n.startswith(('assets/','res/')) or n=='resources.arsc'},'Resource inventory changed')
        for n in protected: require(old.read(n)==new.read(n),'Protected resource changed: '+n)
        dex=b''.join(new.read(n) for n in new.namelist() if re.fullmatch(r'classes\d*\.dex',n))
        for token in (
          b'DETECT_ACCESS_UNITS+ALLOW_NON_IDR_KEYFRAMES',b'ts_access_unit_detection',b'ts_extractor_profile',
          b'timeshift_provider_max_gap_ms',b'timeshift_proxy_max_gap_ms',b'rebuffer_buffer_ahead_last_ms',
          b'timeshift_video_pts_rate_permille',b'timeshift_video_dts_rate_permille',b'timeshift_audio_pts_rate_permille',
          b'timeshift_video_non_idr_intra_frames',b'timeshift_av_drift_max_abs_ms',b'video_pts_age_at_rebuffer_last_ms',
          b'timeshift_timeline_normalizer_active',b'timeshift_timeline_normalizer_scale_ppm',b'timeshift_timeline_normalizer_rewritten_pts',
          b'last_live_before_navigation',b'CobraHappyEyeballs',b'IPv4 only',b'IPv6 only',
          b'cobra_unified_live_timeline',b'CobraCallAudioPolicy'):
            require(token in dex,'2103190 contract missing: '+repr(token))
        require(b'Cobra2103187TsAccessUnitCompatibilityTest' not in dex and b'Cobra2103188TsKeyframeCompatibilityTest' not in dex and b'Cobra2103189TsTimelineFingerprintTest' not in dex and b'Cobra2103190TsClockNormalizationTest' not in dex,'Test code packaged')

    badging=Path('signed190/badging.txt').read_text()
    require("package: name='com.projectinfinity.kodi'" in badging and "versionCode='2103190'" in badging,'Not forward-installable')
    result={'build':VERSION,'base_build':2103189,'base_commit':BASE_COMMIT,'base_apk_sha256':sha(base),'apk_sha256':sha(final),'signer':CERT,
      'ts_extractor_profile':'DETECT_ACCESS_UNITS+ALLOW_NON_IDR_KEYFRAMES','ts_detect_access_units':True,'ts_allow_non_idr_keyframes':True,
      'stream_fingerprint_schema':5,'cadence_diagnostics_preserved':True,'frozen_live_snapshot':True,'timeline_probe_only':False,
      'pat_pmt_probe':True,'video_pts_probe':True,'video_dts_probe':True,'audio_pts_probe':True,'av_drift_probe':True,'h264_nal_probe':True,'intra_cadence_probe':True,'rebuffer_timeline_correlation':True,
      'conditional_clock_normalization':True,'activation_min_wall_ms':5000,'activation_rate_permille':[450,800],'activation_track_delta_permille':35,'normalizes_pcr':True,'normalizes_pts':True,'normalizes_dts':True,'preserves_good_stream_raw_proxy_until_detection':True,'normalizes_rewind_segments_after_activation':True,
      'playback_behavior_changed':True,'network_selection_changed':False,'timeshift_ownership_changed':False,'buffer_policy_changed':False,'parser_flags_changed':False,
      'native_engine_recompiled':False,'theme_zip_changed':False,'physical_device_verified':False}
    Path('audit190/final-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: signed 2103190 preserves exact 2103189 native/resources/signer')

def suite(path,count):
    p=Path(path); require(p.is_file(),'Missing '+str(p)); root=ET.parse(p).getroot(); cases=root.findall('testcase')
    require(len(cases)==count,f'Unexpected test count {p}: {len(cases)} != {count}')
    require(all(int(root.get(k,'0'))==0 for k in ('failures','errors','skipped')),'Failed suite '+str(p))
    return count

def deliver():
    total=0
    for name,count,folder in [('CobraNavigationUiTest',4,'cobra-regression'),('CobraHealthUiTest',7,'cobra-regression'),('Cobra2103159UiTest',2,'experience'),('ExperienceChooserUiTest',6,'experience')]:
        total+=suite(Path('audit159/android')/folder/'test-results'/('TEST-com.projectinfinity.kodi.'+name+'.xml'),count)
    total+=suite('audit190/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualRuntimeTest.xml',17)
    total+=suite('audit190/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualLayoutTest.xml',10)
    for name,count in [
      ('Cobra2103162ThemeRotationTest',15),('Cobra2103164PlaybackStabilityTest',26),('Cobra2103165InsetsPipPlayerTest',6),
      ('Cobra2103166EndToEndUiAuditTest',8),('Cobra2103170StatusBarRestoreSupersessionTest',5),('Cobra2103170StatusBarEdgeTest',7),
      ('Cobra2103175FullscreenBackgroundTest',12),('Cobra2103176LiveRewindTest',5),('Cobra2103177FinalFeatureFreezeTest',10),
      ('Cobra2103178TimeshiftMiniPlayerTest',10),('Cobra2103179BufferResilienceTest',11),('Cobra2103180PlaybackFinalizationTest',6),
      ('Cobra2103181TimeshiftTransportIntegrityTest',6),('Cobra2103182TimeshiftStartupReserveTest',6),('Cobra2103183NetworkFamilyControlTest',6),
      ('Cobra2103184StreamNetworkOptimizationTest',7),('Cobra2103185LiveDiagnosticsFreezeTest',5),('Cobra2103186StreamCadenceFingerprintTest',5),
      ('Cobra2103187TsAccessUnitCompatibilityTest',5),('Cobra2103188TsKeyframeCompatibilityTest',5),('Cobra2103189TsTimelineFingerprintTest',5),('Cobra2103190TsClockNormalizationTest',5)]:
        total+=suite(Path('audit190/targeted/test-results')/('TEST-com.projectinfinity.kodi.'+name+'.xml'),count)
    require(total==222,f'Expected 222 Android tests, got {total}')
    source=json.loads(Path('audit190/source-audit/source-audit.json').read_text())
    require(source.get('passed') and not source.get('failed'),'2103190 source audit failed')
    final=json.loads(Path('audit190/final-verification.json').read_text())
    result={'build':VERSION,'locked_parent':2103189,'locked_parent_commit':BASE_COMMIT,'android_tests':total,'new_ts_clock_normalization_tests':5,
      'ts_extractor_profile':'DETECT_ACCESS_UNITS+ALLOW_NON_IDR_KEYFRAMES','ts_detect_access_units':True,'ts_allow_non_idr_keyframes':True,
      'stream_fingerprint_schema':5,'cadence_diagnostics_preserved':True,'frozen_live_snapshot':True,'timeline_probe_only':False,
      'pat_pmt_probe':True,'video_pts_probe':True,'video_dts_probe':True,'audio_pts_probe':True,'av_drift_probe':True,'h264_nal_probe':True,'intra_cadence_probe':True,'rebuffer_timeline_correlation':True,
      'conditional_clock_normalization':True,'activation_min_wall_ms':5000,'activation_rate_permille':[450,800],'activation_track_delta_permille':35,'normalizes_pcr':True,'normalizes_pts':True,'normalizes_dts':True,'preserves_good_stream_raw_proxy_until_detection':True,'normalizes_rewind_segments_after_activation':True,
      'playback_behavior_changed':True,'network_selection_changed':False,'timeshift_ownership_changed':False,'buffer_policy_changed':False,'parser_flags_changed':False,
      'native_engine_recompiled':False,'theme_zip_changed':False,'apk_sha256':final['apk_sha256'],'physical_device_verified':False,'candidate_locked':False,
      'status':'TEST CANDIDATE - Problem Nicktoons IPv4 Only acceptance: normalizer should activate near raw 559 permille and recurring ~9s rebuffers should stop without affecting normal-rate channels'}
    Path('signed190/ACCEPTANCE.json').write_text(json.dumps(result,indent=2)+'\n')
    shutil.copy2('audit190/final-verification.json','signed190/2103190-verification.json')
    shutil.copy2('audit190/source-audit/source-audit.json','signed190/2103190-source-audit.json')
    print('PASS:',total,'Android tests + 2103190 TS-clock-normalization gates')

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('phase',choices=['upgrade','verify','deliver']); a=p.parse_args(); globals()[a.phase]()
