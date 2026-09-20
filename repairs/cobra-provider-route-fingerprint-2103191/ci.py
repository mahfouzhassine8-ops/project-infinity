#!/usr/bin/env python3
"""Package/gate 2103191 provider-route fingerprint over exact passed 2103190."""
from pathlib import Path
import argparse,hashlib,json,re,shutil,subprocess,zipfile,xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
BASE_COMMIT='f31d1208be0357856a80b59b7118be093212c8a6'
OLD='1.0.9-Cobra-TS-Clock-Normalization-RC1'
NEW='1.0.9-Cobra-Provider-Route-Fingerprint-RC1'
VERSION=2103191
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
    require(data.get('version_code')==2103190 and data.get('version_name')==OLD,'Expected exact passed 2103190 source receipt')
    for rel,row in data.get('files',{}).items():
        require(sha(Path('kodi')/rel)==row['after'],'2103190 source receipt drift: '+rel)

    run('python3',ROOT/'apply.py','--source','kodi','--receipt',receipt,'--out','audit191/patch')
    patch=json.loads(Path('audit191/patch/patch.json').read_text());data['files'][ACT]['after']=patch['files'][ACT]['after']

    gradle=Path('kodi')/GRADLE
    replace(gradle,'versionCode 2103190',f'versionCode {VERSION}')
    replace(gradle,'versionName "'+OLD+'"','versionName "'+NEW+'"')
    runtime=Path('scripts/infinity_background_resume.py')
    replace(runtime,'VERSION_CODE = 2103190',f'VERSION_CODE = {VERSION}')
    replace(runtime,"RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'")
    pack=Path('scripts/package_background_resume.py');s=pack.read_text();needle='Infinity-'+OLD
    require(s.count(needle)>=2,'2103190 packager identity drift');pack.write_text(s.replace(needle,'Infinity-'+NEW))

    data['files'][GRADLE]['after']=sha(gradle)
    data.update(
      version_code=VERSION,version_name=NEW,source_parent=2103190,source_parent_locked=True,locked_parent_commit=BASE_COMMIT,candidate_locked=False,
      stream_fingerprint_schema=6,provider_route_fingerprint=True,provider_remote_hash=True,provider_dns_hashes=True,
      provider_final_host_hash=True,provider_response_header_hash=True,raw_provider_url_logged=False,raw_remote_ip_logged=False,
      playback_behavior_changed=False,network_selection_changed=False,timeshift_ownership_changed=False,buffer_policy_changed=False,
      parser_flags_changed=False,clock_normalization_changed=False,native_engine_recompiled=False,theme_zip_changed=False,physical_device_verified=False)
    receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')

    for rel,row in data['files'].items():
        require(sha(Path('kodi')/rel)==row['after'],'Final 2103191 source receipt drift: '+rel)
    run('python3',ROOT/'source_audit.py','--source','kodi','--patch','audit191/patch/patch.json','--out','audit191/source-audit')
    with Path('audit191/native-after.patch').open('wb') as out:
        subprocess.run(['git','-C','kodi','diff','--binary','--','xbmc'],stdout=out,check=True)
    require(Path('audit191/native-after.patch').read_bytes()==Path('engine/native-before.patch').read_bytes(),'Native source changed')
    print('PASS: exact 2103190 -> 2103191 provider-route fingerprint; playback/network behavior preserved')

def verify():
    base=Path('baseline190/Infinity-'+OLD+'.apk')
    final=Path('signed191/Infinity-'+NEW+'.apk')
    require(base.is_file() and final.is_file(),'Baseline/final APK missing')
    bv=json.loads(Path('baseline190/2103190-verification.json').read_text())
    require(bv['apk_sha256']==sha(base),'Wrong exact passed 2103190 APK')
    audit=json.loads(Path('signed191/background-resume-apk-audit.json').read_text())
    require(audit['version_code']==VERSION and audit['version_name']==NEW,'Final 2103191 identity mismatch')
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
          b'routeFingerprint',b'timeshift_timeline_normalizer_active',b'timeshift_timeline_normalizer_scale_ppm',
          b'DETECT_ACCESS_UNITS+ALLOW_NON_IDR_KEYFRAMES',b'last_live_before_navigation',
          b'cobra_unified_live_timeline',b'CobraCallAudioPolicy',b'buffer_observed_no_restart'):
            require(token in dex,'2103191 contract missing: '+repr(token))
        require(b'Cobra2103191ProviderRouteFingerprintTest' not in dex,'2103191 test code packaged in release APK')

    badging=Path('signed191/badging.txt').read_text()
    require("package: name='com.projectinfinity.kodi'" in badging and "versionCode='2103191'" in badging,'Final APK not forward-installable')
    result={'build':VERSION,'base_build':2103190,'base_commit':BASE_COMMIT,'base_apk_sha256':sha(base),'apk_sha256':sha(final),'signer':CERT,
      'stream_fingerprint_schema':6,'provider_route_fingerprint':True,'provider_remote_hash':True,'provider_dns_hashes':True,
      'provider_final_host_hash':True,'provider_response_header_hash':True,'raw_provider_url_logged':False,'raw_remote_ip_logged':False,
      'playback_behavior_changed':False,'network_selection_changed':False,'timeshift_ownership_changed':False,'buffer_policy_changed':False,
      'parser_flags_changed':False,'clock_normalization_changed':False,'native_engine_recompiled':False,'theme_zip_changed':False,'physical_device_verified':False}
    Path('audit191/final-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: signed 2103191 preserves exact 2103190 native/resources/signer and adds diagnostics only')

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
    total+=suite('audit191/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualRuntimeTest.xml',17)
    total+=suite('audit191/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualLayoutTest.xml',10)
    for name,count in [
      ('Cobra2103162ThemeRotationTest',15),('Cobra2103164PlaybackStabilityTest',26),('Cobra2103165InsetsPipPlayerTest',6),
      ('Cobra2103166EndToEndUiAuditTest',8),('Cobra2103170StatusBarRestoreSupersessionTest',5),('Cobra2103170StatusBarEdgeTest',7),
      ('Cobra2103175FullscreenBackgroundTest',12),('Cobra2103176LiveRewindTest',5),('Cobra2103177FinalFeatureFreezeTest',10),
      ('Cobra2103178TimeshiftMiniPlayerTest',10),('Cobra2103179BufferResilienceTest',11),('Cobra2103180PlaybackFinalizationTest',6),
      ('Cobra2103181TimeshiftTransportIntegrityTest',6),('Cobra2103182TimeshiftStartupReserveTest',6),('Cobra2103183NetworkFamilyControlTest',6),
      ('Cobra2103184StreamNetworkOptimizationTest',7),('Cobra2103185LiveDiagnosticsFreezeTest',5),('Cobra2103186StreamCadenceFingerprintTest',5),
      ('Cobra2103187TsAccessUnitCompatibilityTest',5),('Cobra2103188TsKeyframeCompatibilityTest',5),('Cobra2103189TsTimelineFingerprintTest',5),
      ('Cobra2103190TsClockNormalizationTest',5),('Cobra2103191ProviderRouteFingerprintTest',5)]:
        total+=suite(Path('audit191/targeted/test-results')/('TEST-com.projectinfinity.kodi.'+name+'.xml'),count)
    require(total==227,f'Expected 227 Android tests, got {total}')
    source=json.loads(Path('audit191/source-audit/source-audit.json').read_text())
    final=json.loads(Path('audit191/final-verification.json').read_text())
    require(source.get('passed') and not source.get('failed'),'2103191 source audit failed')
    result={'build':VERSION,'locked_parent':2103190,'locked_parent_commit':BASE_COMMIT,'android_tests':total,'new_provider_route_tests':5,
      'stream_fingerprint_schema':6,'provider_route_fingerprint':True,'raw_provider_url_logged':False,'raw_remote_ip_logged':False,
      'playback_behavior_changed':False,'network_selection_changed':False,'buffer_policy_changed':False,'parser_flags_changed':False,
      'clock_normalization_changed':False,'native_engine_recompiled':False,'theme_zip_changed':False,'apk_sha256':final['apk_sha256'],
      'physical_device_verified':False,'candidate_locked':False,
      'status':'TEST CANDIDATE - run Problem Nicktoons once VPN OFF and once VPN ON; export diagnostics from each and compare provider DNS/remote/final-host/response hashes before any routing change'}
    Path('signed191/ACCEPTANCE.json').write_text(json.dumps(result,indent=2)+'\n')
    shutil.copy2('audit191/final-verification.json','signed191/2103191-verification.json')
    shutil.copy2('audit191/source-audit/source-audit.json','signed191/2103191-source-audit.json')
    print('PASS:',total,'Android tests + 2103191 provider-route fingerprint gates')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['upgrade','verify','deliver']);a=p.parse_args();globals()[a.phase]()
