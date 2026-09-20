#!/usr/bin/env python3
"""Package/gate 2103195 presentation polish and motion audit over exact passed 2103194."""
from pathlib import Path
import argparse,hashlib,json,re,shutil,subprocess,zipfile,xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
BASE_COMMIT='8c4a993afac76aafc295d482fe32e240e407ae14'
OLD='1.0.9-Cobra-Fold-Adaptive-Aspect-RC1'
NEW='1.0.9-Cobra-Presentation-Polish-Motion-RC1'
VERSION=2103195
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
ACT='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
GRADLE='tools/android/packaging/xbmc/build.gradle.in'

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(v,msg):
    if not v: raise RuntimeError(msg)
def run(*args): subprocess.run(list(map(str,args)),check=True)
def replace(path,old,new):
    p=Path(path);s=p.read_text();require(s.count(old)==1,'identity anchor drift: '+old);p.write_text(s.replace(old,new,1))

def upgrade():
    receipt=Path('engine/background-resume-source.json');data=json.loads(receipt.read_text())
    require(data.get('version_code')==2103194 and data.get('version_name')==OLD,'Expected exact passed 2103194 source receipt')
    for rel,row in data.get('files',{}).items():
        require(sha(Path('kodi')/rel)==row['after'],'2103194 source receipt drift: '+rel)

    run('python3',ROOT/'apply.py','--source','kodi','--receipt',receipt,'--out','audit195/patch')
    patch=json.loads(Path('audit195/patch/patch.json').read_text());data['files'][ACT]['after']=patch['files'][ACT]['after']

    gradle=Path('kodi')/GRADLE
    replace(gradle,'versionCode 2103194',f'versionCode {VERSION}')
    replace(gradle,'versionName "'+OLD+'"','versionName "'+NEW+'"')
    runtime=Path('scripts/infinity_background_resume.py')
    replace(runtime,'VERSION_CODE = 2103194',f'VERSION_CODE = {VERSION}')
    replace(runtime,"RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'")
    pack=Path('scripts/package_background_resume.py');s=pack.read_text();needle='Infinity-'+OLD
    require(s.count(needle)>=2,'2103194 packager identity drift');pack.write_text(s.replace(needle,'Infinity-'+NEW))

    data['files'][GRADLE]['after']=sha(gradle)
    data.update(
      version_code=VERSION,version_name=NEW,source_parent=2103194,source_parent_locked=True,locked_parent_commit=BASE_COMMIT,candidate_locked=False,
      stream_fingerprint_schema=7,provider_route_fingerprint=True,provider_pace_limit_classifier=True,timeline_normalizer_rewrite_enabled=False,
      clock_rewrite_suppressed_by_evidence=True,source_manager_route_restored=True,source_manager_label='TV SOURCES',fold_adaptive_aspect=True,fold_adaptive_mode=12,tivimate_inspired_player_hub=True,motion_polish=True,
      playback_behavior_changed=False,network_selection_changed=False,timeshift_ownership_changed=False,buffer_policy_changed=False,
      parser_flags_changed=False,native_engine_recompiled=False,theme_zip_changed=False,physical_device_verified=False)
    receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')

    for rel,row in data['files'].items():
        require(sha(Path('kodi')/rel)==row['after'],'Final 2103195 source receipt drift: '+rel)
    run('python3',ROOT/'source_audit.py','--source','kodi','--patch','audit195/patch/patch.json','--out','audit195/source-audit')
    with Path('audit195/native-after.patch').open('wb') as out:
        subprocess.run(['git','-C','kodi','diff','--binary','--','xbmc'],stdout=out,check=True)
    require(Path('audit195/native-after.patch').read_bytes()==Path('engine/native-before.patch').read_bytes(),'Native source changed')
    print('PASS: exact 2103194 -> 2103195 presentation polish + motion audit; protected stack preserved')

def verify():
    base=Path('baseline194/Infinity-'+OLD+'.apk')
    final=Path('signed195/Infinity-'+NEW+'.apk')
    require(base.is_file() and final.is_file(),'Baseline/final APK missing')
    bv=json.loads(Path('baseline194/2103194-verification.json').read_text())
    require(bv['apk_sha256']==sha(base),'Wrong exact passed 2103194 APK')
    audit=json.loads(Path('signed195/background-resume-apk-audit.json').read_text())
    require(audit['version_code']==VERSION and audit['version_name']==NEW,'Final 2103195 identity mismatch')
    require(audit['signer_certificate_sha256']==CERT and audit['apk_sha256']==sha(final),'Signer/hash mismatch')
    require(not audit['native_recompiled'],'Native engine was rebuilt')

    with zipfile.ZipFile(base) as old,zipfile.ZipFile(final) as new:
        old_native={n for n in old.namelist() if n.startswith('lib/') and not n.endswith('/')}
        new_native={n for n in new.namelist() if n.startswith('lib/') and not n.endswith('/')}
        require(old_native==new_native,'Native inventory changed')
        for n in old_native: require(old.read(n)==new.read(n),'Native entry changed: '+n)
        protected={n for n in old.namelist() if n.startswith(('assets/','res/')) or n=='resources.arsc'}
        require(protected=={n for n in new.namelist() if n.startswith(('assets/','res/')) or n=='resources.arsc'},'Protected resource inventory changed')
        for n in protected: require(old.read(n)==new.read(n),'Protected resource changed: '+n)
        dex=b''.join(new.read(n) for n in new.namelist() if re.fullmatch(r'classes\d*\.dex',n))
        for token in (
          b'timeshift_provider_remote_hash',b'timeshift_provider_dns_hashes',b'timeshift_provider_protocol',
          b'timeshift_provider_proxy',b'timeshift_provider_final_host_hash',b'timeshift_provider_response_header_hash',
          b'routeFingerprint',b'timeshift_timeline_normalizer_active',b'timeshift_timeline_normalizer_scale_ppm',b'timeshift_provider_pace_limited',b'timeshift_timeline_normalizer_rewrite_enabled',
          b'DETECT_ACCESS_UNITS+ALLOW_NON_IDR_KEYFRAMES',b'last_live_before_navigation',
          b'cobra_unified_live_timeline',b'CobraCallAudioPolicy',b'buffer_observed_no_restart',b'TV SOURCES',b'cobra_tv_sources',b'Fold Adaptive',b'Player options',b'RECENT CHANNELS',b'Video & display',b'cobra-player-hub-video',b'CobraMotionSpec'):
            require(token in dex,'2103195 contract missing: '+repr(token))
        require(b'Cobra2103195PresentationPolishTest' not in dex,'2103194 test code packaged in release APK')

    badging=Path('signed195/badging.txt').read_text()
    require("package: name='com.projectinfinity.kodi'" in badging and "versionCode='2103195'" in badging,'Final APK not forward-installable')
    result={'build':VERSION,'base_build':2103194,'base_commit':BASE_COMMIT,'base_apk_sha256':sha(base),'apk_sha256':sha(final),'signer':CERT,
      'stream_fingerprint_schema':7,'provider_route_fingerprint':True,'provider_pace_limit_classifier':True,'timeline_normalizer_rewrite_enabled':False,
      'clock_rewrite_suppressed_by_evidence':True,'source_manager_route_restored':True,'source_manager_label':'TV SOURCES','fold_adaptive_aspect':True,'fold_adaptive_mode':12,'tivimate_inspired_player_hub':True,'motion_polish':True,
      'playback_behavior_changed':False,'network_selection_changed':False,'timeshift_ownership_changed':False,'buffer_policy_changed':False,
      'parser_flags_changed':False,'native_engine_recompiled':False,'theme_zip_changed':False,'physical_device_verified':False}
    Path('audit195/final-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: signed 2103195 preserves exact 2103194 native/resources/signer and adds presentation polish/motion only')

def suite(path,count):
    p=Path(path);require(p.is_file(),'Missing test evidence '+str(p));root=ET.parse(p).getroot();cases=root.findall('testcase')
    require(len(cases)==count,f'Unexpected test count {p}: {len(cases)} != {count}')
    require(all(int(root.get(k,'0'))==0 for k in ('failures','errors','skipped')),'Failed/incomplete suite '+str(p))
    require(all(c.find(k) is None for c in cases for k in ('failure','error','skipped')),'Failed/skipped testcase '+str(p))
    return count

def deliver():
    total=0
    for name,count,folder in [('CobraNavigationUiTest',4,'cobra-regression'),('CobraHealthUiTest',7,'cobra-regression'),('Cobra2103159UiTest',2,'experience'),('ExperienceChooserUiTest',6,'experience')]:
        total+=suite(Path('audit159/android')/folder/'test-results'/('TEST-com.projectinfinity.kodi.'+name+'.xml'),count)
    total+=suite('audit195/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualRuntimeTest.xml',17)
    total+=suite('audit195/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualLayoutTest.xml',10)
    for name,count in [
      ('Cobra2103162ThemeRotationTest',15),('Cobra2103164PlaybackStabilityTest',26),('Cobra2103165InsetsPipPlayerTest',6),
      ('Cobra2103166EndToEndUiAuditTest',8),('Cobra2103170StatusBarRestoreSupersessionTest',5),('Cobra2103170StatusBarEdgeTest',7),
      ('Cobra2103175FullscreenBackgroundTest',12),('Cobra2103176LiveRewindTest',5),('Cobra2103177FinalFeatureFreezeTest',10),
      ('Cobra2103178TimeshiftMiniPlayerTest',10),('Cobra2103179BufferResilienceTest',11),('Cobra2103180PlaybackFinalizationTest',6),
      ('Cobra2103181TimeshiftTransportIntegrityTest',6),('Cobra2103182TimeshiftStartupReserveTest',6),('Cobra2103183NetworkFamilyControlTest',6),
      ('Cobra2103184StreamNetworkOptimizationTest',7),('Cobra2103185LiveDiagnosticsFreezeTest',5),('Cobra2103186StreamCadenceFingerprintTest',5),
      ('Cobra2103187TsAccessUnitCompatibilityTest',5),('Cobra2103188TsKeyframeCompatibilityTest',5),('Cobra2103189TsTimelineFingerprintTest',5),
      ('Cobra2103190TsClockNormalizationTest',5),('Cobra2103191ProviderRouteFingerprintTest',5),('Cobra2103192ProviderPaceReserveTest',5),('Cobra2103193SourceManagerRestoreTest',5),('Cobra2103194FoldAdaptiveAspectTest',6),('Cobra2103195PresentationPolishTest',7)]:
        total+=suite(Path('audit195/targeted/test-results')/('TEST-com.projectinfinity.kodi.'+name+'.xml'),count)
    require(total==250,f'Expected 250 Android tests, got {total}')
    source=json.loads(Path('audit195/source-audit/source-audit.json').read_text())
    final=json.loads(Path('audit195/final-verification.json').read_text())
    require(source.get('passed') and not source.get('failed'),'2103195 source audit failed')
    result={'build':VERSION,'locked_parent':2103194,'locked_parent_commit':BASE_COMMIT,'android_tests':total,'new_presentation_polish_tests':7,
      'stream_fingerprint_schema':7,'provider_route_fingerprint':True,'provider_pace_limit_classifier':True,'source_manager_route_restored':True,'fold_adaptive_aspect':True,'fold_adaptive_first_choice':True,'tivimate_inspired_player_hub':True,'recent_channel_strip':True,'motion_polish':True,
      'playback_behavior_changed':False,'network_selection_changed':False,'buffer_policy_changed':False,'parser_flags_changed':False,
      'timeline_normalizer_rewrite_enabled':False,'native_engine_recompiled':False,'theme_zip_changed':False,'apk_sha256':final['apk_sha256'],
      'physical_device_verified':False,'candidate_locked':False,
      'status':'TEST CANDIDATE - TiviMate-inspired player options, video/display menu and motion polish over exact 2103194; playback/network/timeshift/native contracts remain protected'}
    Path('signed195/ACCEPTANCE.json').write_text(json.dumps(result,indent=2)+'\n')
    shutil.copy2('audit195/final-verification.json','signed195/2103195-verification.json')
    shutil.copy2('audit195/source-audit/source-audit.json','signed195/2103195-source-audit.json')
    print('PASS:',total,'Android tests + 2103195 presentation polish gates')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['upgrade','verify','deliver']);a=p.parse_args();globals()[a.phase]()
