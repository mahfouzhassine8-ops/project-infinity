#!/usr/bin/env python3
"""Package/gate 2103192 provider pace guard over exact passed 2103191."""
from pathlib import Path
import argparse,hashlib,json,re,shutil,subprocess,zipfile,xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
BASE_COMMIT='23fab77d21e97e6f74f04f397d3fa0a63a24bc2e'
OLD='1.0.9-Cobra-Provider-Route-Fingerprint-RC1'
NEW='1.0.9-Cobra-Provider-Pace-Guard-RC1'
VERSION=2103192
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
    require(data.get('version_code')==2103191 and data.get('version_name')==OLD,'Expected exact passed 2103191 source receipt')
    for rel,row in data.get('files',{}).items():
        require(sha(Path('kodi')/rel)==row['after'],'2103191 source receipt drift: '+rel)

    run('python3',ROOT/'apply.py','--source','kodi','--receipt',receipt,'--out','audit192/patch')
    patch=json.loads(Path('audit192/patch/patch.json').read_text());data['files'][ACT]['after']=patch['files'][ACT]['after']

    gradle=Path('kodi')/GRADLE
    replace(gradle,'versionCode 2103191',f'versionCode {VERSION}')
    replace(gradle,'versionName "'+OLD+'"','versionName "'+NEW+'"')
    runtime=Path('scripts/infinity_background_resume.py')
    replace(runtime,'VERSION_CODE = 2103191',f'VERSION_CODE = {VERSION}')
    replace(runtime,"RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'")
    pack=Path('scripts/package_background_resume.py');s=pack.read_text();needle='Infinity-'+OLD
    require(s.count(needle)>=2,'2103191 packager identity drift');pack.write_text(s.replace(needle,'Infinity-'+NEW))

    data['files'][GRADLE]['after']=sha(gradle)
    data.update(
      version_code=VERSION,version_name=NEW,source_parent=2103191,source_parent_locked=True,locked_parent_commit=BASE_COMMIT,candidate_locked=False,
      stream_fingerprint_schema=7,provider_route_fingerprint=True,provider_pace_limit_classifier=True,timeline_normalizer_rewrite_enabled=False,
      clock_rewrite_suppressed_by_evidence=True,raw_provider_url_logged=False,raw_remote_ip_logged=False,
      playback_behavior_changed=False,network_selection_changed=False,timeshift_ownership_changed=False,buffer_policy_changed=False,
      parser_flags_changed=False,native_engine_recompiled=False,theme_zip_changed=False,physical_device_verified=False)
    receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')

    for rel,row in data['files'].items():
        require(sha(Path('kodi')/rel)==row['after'],'Final 2103192 source receipt drift: '+rel)
    run('python3',ROOT/'source_audit.py','--source','kodi','--patch','audit192/patch/patch.json','--out','audit192/source-audit')
    with Path('audit192/native-after.patch').open('wb') as out:
        subprocess.run(['git','-C','kodi','diff','--binary','--','xbmc'],stdout=out,check=True)
    require(Path('audit192/native-after.patch').read_bytes()==Path('engine/native-before.patch').read_bytes(),'Native source changed')
    print('PASS: exact 2103191 -> 2103192 provider pace guard; protected stack preserved')

def verify():
    base=Path('baseline191/Infinity-'+OLD+'.apk')
    final=Path('signed192/Infinity-'+NEW+'.apk')
    require(base.is_file() and final.is_file(),'Baseline/final APK missing')
    bv=json.loads(Path('baseline191/2103191-verification.json').read_text())
    require(bv['apk_sha256']==sha(base),'Wrong exact passed 2103191 APK')
    audit=json.loads(Path('signed192/background-resume-apk-audit.json').read_text())
    require(audit['version_code']==VERSION and audit['version_name']==NEW,'Final 2103192 identity mismatch')
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
          b'cobra_unified_live_timeline',b'CobraCallAudioPolicy',b'buffer_observed_no_restart'):
            require(token in dex,'2103192 contract missing: '+repr(token))
        require(b'Cobra2103192ProviderPaceReserveTest' not in dex,'2103192 test code packaged in release APK')

    badging=Path('signed192/badging.txt').read_text()
    require("package: name='com.projectinfinity.kodi'" in badging and "versionCode='2103191'" in badging,'Final APK not forward-installable')
    result={'build':VERSION,'base_build':2103191,'base_commit':BASE_COMMIT,'base_apk_sha256':sha(base),'apk_sha256':sha(final),'signer':CERT,
      'stream_fingerprint_schema':7,'provider_route_fingerprint':True,'provider_pace_limit_classifier':True,'timeline_normalizer_rewrite_enabled':False,
      'clock_rewrite_suppressed_by_evidence':True,'raw_provider_url_logged':False,'raw_remote_ip_logged':False,
      'playback_behavior_changed':False,'network_selection_changed':False,'timeshift_ownership_changed':False,'buffer_policy_changed':False,
      'parser_flags_changed':False,'native_engine_recompiled':False,'theme_zip_changed':False,'physical_device_verified':False}
    Path('audit192/final-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: signed 2103192 preserves exact 2103191 native/resources/signer and adds evidence-driven pace guard only')

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
    total+=suite('audit192/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualRuntimeTest.xml',17)
    total+=suite('audit192/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualLayoutTest.xml',10)
    for name,count in [
      ('Cobra2103162ThemeRotationTest',15),('Cobra2103164PlaybackStabilityTest',26),('Cobra2103165InsetsPipPlayerTest',6),
      ('Cobra2103166EndToEndUiAuditTest',8),('Cobra2103170StatusBarRestoreSupersessionTest',5),('Cobra2103170StatusBarEdgeTest',7),
      ('Cobra2103175FullscreenBackgroundTest',12),('Cobra2103176LiveRewindTest',5),('Cobra2103177FinalFeatureFreezeTest',10),
      ('Cobra2103178TimeshiftMiniPlayerTest',10),('Cobra2103179BufferResilienceTest',11),('Cobra2103180PlaybackFinalizationTest',6),
      ('Cobra2103181TimeshiftTransportIntegrityTest',6),('Cobra2103182TimeshiftStartupReserveTest',6),('Cobra2103183NetworkFamilyControlTest',6),
      ('Cobra2103184StreamNetworkOptimizationTest',7),('Cobra2103185LiveDiagnosticsFreezeTest',5),('Cobra2103186StreamCadenceFingerprintTest',5),
      ('Cobra2103187TsAccessUnitCompatibilityTest',5),('Cobra2103188TsKeyframeCompatibilityTest',5),('Cobra2103189TsTimelineFingerprintTest',5),
      ('Cobra2103190TsClockNormalizationTest',5),('Cobra2103191ProviderRouteFingerprintTest',5),('Cobra2103192ProviderPaceReserveTest',5)]:
        total+=suite(Path('audit192/targeted/test-results')/('TEST-com.projectinfinity.kodi.'+name+'.xml'),count)
    require(total==232,f'Expected 232 Android tests, got {total}')
    source=json.loads(Path('audit192/source-audit/source-audit.json').read_text())
    final=json.loads(Path('audit192/final-verification.json').read_text())
    require(source.get('passed') and not source.get('failed'),'2103192 source audit failed')
    result={'build':VERSION,'locked_parent':2103191,'locked_parent_commit':BASE_COMMIT,'android_tests':total,'new_provider_pace_tests':5,
      'stream_fingerprint_schema':7,'provider_route_fingerprint':True,'provider_pace_limit_classifier':True,'raw_provider_url_logged':False,'raw_remote_ip_logged':False,
      'playback_behavior_changed':False,'network_selection_changed':False,'buffer_policy_changed':False,'parser_flags_changed':False,
      'timeline_normalizer_rewrite_enabled':False,'native_engine_recompiled':False,'theme_zip_changed':False,'apk_sha256':final['apk_sha256'],
      'physical_device_verified':False,'candidate_locked':False,
      'status':'TEST CANDIDATE - evidence guard only: Problem Nicktoons direct path should classify as provider pace limited; no timestamp rewrite, no buffer/network/parser change'}
    Path('signed192/ACCEPTANCE.json').write_text(json.dumps(result,indent=2)+'\n')
    shutil.copy2('audit192/final-verification.json','signed192/2103192-verification.json')
    shutil.copy2('audit192/source-audit/source-audit.json','signed192/2103192-source-audit.json')
    print('PASS:',total,'Android tests + 2103192 provider pace guard gates')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['upgrade','verify','deliver']);a=p.parse_args();globals()[a.phase]()
