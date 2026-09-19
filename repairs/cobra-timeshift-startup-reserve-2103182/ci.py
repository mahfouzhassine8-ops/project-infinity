#!/usr/bin/env python3
"""Package/gate 2103182 startup reserve over exact passed 2103181."""
from pathlib import Path
import argparse,hashlib,json,re,shutil,subprocess,zipfile,xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
BASE_COMMIT='bfc69d84552dd64ef39946bdd2b368e7ff1def52'
OLD='1.0.9-Cobra-Timeshift-Transport-Integrity-RC1'
NEW='1.0.9-Cobra-Timeshift-Startup-Reserve-RC1'
VERSION=2103182
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
ACT='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(v,msg):
    if not v:raise RuntimeError(msg)
def replace(path,old,new,count=1):
    p=Path(path);s=p.read_text();actual=s.count(old);require(actual==count,f'identity anchor drift {path}: {old} count={actual}')
    p.write_text(s.replace(old,new,count) if count==1 else s.replace(old,new))
def run(*args):subprocess.run(list(map(str,args)),check=True)

def upgrade():
    receipt=Path('engine/background-resume-source.json');data=json.loads(receipt.read_text())
    require(data.get('version_code')==2103181 and data.get('version_name')==OLD,'Expected exact passed 2103181 source receipt')
    for rel,row in data.get('files',{}).items():
        require(sha(Path('kodi')/rel)==row['after'],'2103181 source receipt drift: '+rel)

    run('python3',ROOT/'apply.py','--source','kodi','--receipt',receipt,'--out','audit182/patch')
    patch=json.loads(Path('audit182/patch/patch.json').read_text())
    data['files'][ACT]['after']=patch['files'][ACT]['after']

    gradle=Path('kodi/tools/android/packaging/xbmc/build.gradle.in')
    replace(gradle,'versionCode 2103181',f'versionCode {VERSION}')
    replace(gradle,'versionName "'+OLD+'"','versionName "'+NEW+'"')

    runtime=Path('scripts/infinity_background_resume.py')
    replace(runtime,'VERSION_CODE = 2103181',f'VERSION_CODE = {VERSION}')
    replace(runtime,"RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'")

    pack=Path('scripts/package_background_resume.py');s=pack.read_text();needle='Infinity-'+OLD
    require(s.count(needle)>=2,'2103181 packager identity drift')
    pack.write_text(s.replace(needle,'Infinity-'+NEW))

    data['files']['tools/android/packaging/xbmc/build.gradle.in']['after']=sha(gradle)
    data.update(
        version_code=VERSION,version_name=NEW,source_parent=2103181,source_parent_locked=True,
        locked_parent_commit=BASE_COMMIT,candidate_locked=False,
        startup_reserve_ms=21000,startup_wait_ms=32000,provider_read_timeout_ms=5000,live_reserve_ms=15000,
        readiness_uses_actual_window_duration=True,premature_nine_second_start_removed=True,
        segment_duration_excludes_network_idle=True,discontinuity_sequence_stable=True,
        retains_removed_segments_for_prior_snapshots=True,
        unified_blue_timeline_preserved=True,phone_call_video_continuity_preserved=True,
        pro_buffer_safeguards_preserved=True,dns_pin_or_custom_resolver_added=False,
        native_engine_recompiled=False,theme_zip_changed=False,physical_device_verified=False)
    receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')

    for rel,row in data['files'].items():
        require(sha(Path('kodi')/rel)==row['after'],'Final 2103182 source receipt drift: '+rel)

    run('python3',ROOT/'source_audit.py','--source','kodi','--patch','audit182/patch/patch.json','--out','audit182/source-audit')
    with Path('audit182/native-after.patch').open('wb') as out:
        subprocess.run(['git','-C','kodi','diff','--binary','--','xbmc'],stdout=out,check=True)
    require(Path('audit182/native-after.patch').read_bytes()==Path('engine/native-before.patch').read_bytes(),'Native source changed')
    print('PASS: exact 2103181 -> 2103182 startup reserve; native tree preserved')

def verify():
    base=Path('baseline181/Infinity-'+OLD+'.apk')
    final=Path('signed182/Infinity-'+NEW+'.apk')
    require(base.is_file() and final.is_file(),'Baseline/final APK missing')

    bv=json.loads(Path('baseline181/2103181-verification.json').read_text())
    require(bv['apk_sha256']==sha(base),'Wrong exact passed 2103181 APK')

    audit=json.loads(Path('signed182/background-resume-apk-audit.json').read_text())
    require(audit['version_code']==VERSION and audit['version_name']==NEW,'Final 2103182 identity mismatch')
    require(audit['signer_certificate_sha256']==CERT and audit['apk_sha256']==sha(final),'Signer/hash mismatch')
    require(not audit['native_recompiled'],'Native engine was rebuilt')

    with zipfile.ZipFile(base) as old,zipfile.ZipFile(final) as new:
        old_native={n for n in old.namelist() if n.startswith('lib/') and not n.endswith('/')}
        new_native={n for n in new.namelist() if n.startswith('lib/') and not n.endswith('/')}
        require(old_native==new_native,'Native inventory changed')
        for n in old_native:require(old.read(n)==new.read(n),'Native entry changed: '+n)

        protected={n for n in old.namelist() if n.startswith(('assets/','res/')) or n=='resources.arsc'}
        require(protected=={n for n in new.namelist() if n.startswith(('assets/','res/')) or n=='resources.arsc'},'Protected resource inventory changed')
        for n in protected:require(old.read(n)==new.read(n),'Protected resource changed: '+n)

        dex=b''.join(new.read(n) for n in new.namelist() if re.fullmatch(r'classes\d*\.dex',n))
        for token in (
            b'EXT-X-DISCONTINUITY-SEQUENCE',b'publishedSegmentDurationMs',b'segment_404s',
            b'provider_packet_age_ms',b'cobra_unified_live_timeline',b'CobraCallAudioPolicy',
            b'buffer_observed_no_restart',b'STARTUP_RESERVE_MS',b'startup_target_s',
            b'timeshift_startup_reserve_ms'):
            require(token in dex,'Combined 2103182 contract missing: '+repr(token))
        require(b'Cobra2103182TimeshiftStartupReserveTest' not in dex,'2103182 test code packaged in release APK')

    badging=Path('signed182/badging.txt').read_text()
    require("package: name='com.projectinfinity.kodi'" in badging and "versionCode='2103182'" in badging,
            'Final APK not forward-installable')

    result={
        'build':VERSION,'base_build':2103181,'base_commit':BASE_COMMIT,
        'base_apk_sha256':sha(base),'apk_sha256':sha(final),'signer':CERT,
        'native_entries':len(old_native),'protected_resource_entries':len(protected),
        'startup_reserve_ms':21000,'startup_wait_ms':32000,'provider_read_timeout_ms':5000,'live_reserve_ms':15000,
        'readiness_uses_actual_window_duration':True,'premature_nine_second_start_removed':True,
        'segment_duration_excludes_network_idle':True,'discontinuity_sequence_stable':True,
        'retains_removed_segments_for_prior_snapshots':True,
        'unified_blue_timeline_preserved':True,'phone_call_video_continuity_preserved':True,
        'pro_buffer_safeguards_preserved':True,'dns_pin_or_custom_resolver_added':False,
        'native_engine_recompiled':False,'theme_zip_changed':False,'physical_device_verified':False}
    Path('audit182/final-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: signed 2103182 preserves exact 2103181 native/resources/signer')

def suite(path,count):
    p=Path(path);require(p.is_file(),'Missing test evidence '+str(p))
    root=ET.parse(p).getroot();cases=root.findall('testcase')
    require(len(cases)==count,f'Unexpected test count {p}: {len(cases)} != {count}')
    require(all(int(root.get(k,'0'))==0 for k in ('failures','errors','skipped')),'Failed/incomplete suite '+str(p))
    require(all(c.find(k) is None for c in cases for k in ('failure','error','skipped')),'Failed/skipped testcase '+str(p))
    return count

def deliver():
    inherited=0
    for name,count,folder in [
        ('CobraNavigationUiTest',4,'cobra-regression'),('CobraHealthUiTest',7,'cobra-regression'),
        ('Cobra2103159UiTest',2,'experience'),('ExperienceChooserUiTest',6,'experience')]:
        inherited+=suite(Path('audit159/android')/folder/'test-results'/('TEST-com.projectinfinity.kodi.'+name+'.xml'),count)
    inherited+=suite('audit182/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualRuntimeTest.xml',17)
    inherited+=suite('audit182/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualLayoutTest.xml',10)

    targeted=0
    for name,count in [
        ('Cobra2103162ThemeRotationTest',15),('Cobra2103164PlaybackStabilityTest',26),
        ('Cobra2103165InsetsPipPlayerTest',6),('Cobra2103166EndToEndUiAuditTest',8),
        ('Cobra2103170StatusBarRestoreSupersessionTest',5),('Cobra2103170StatusBarEdgeTest',7),
        ('Cobra2103175FullscreenBackgroundTest',12),('Cobra2103176LiveRewindTest',5),
        ('Cobra2103177FinalFeatureFreezeTest',10),('Cobra2103178TimeshiftMiniPlayerTest',10),
        ('Cobra2103179BufferResilienceTest',11),('Cobra2103180PlaybackFinalizationTest',6),
        ('Cobra2103181TimeshiftTransportIntegrityTest',6),('Cobra2103182TimeshiftStartupReserveTest',6)]:
        targeted+=suite(Path('audit182/targeted/test-results')/('TEST-com.projectinfinity.kodi.'+name+'.xml'),count)

    total=inherited+targeted
    require(total==179,f'Expected 179 Android tests, got {total}')

    source=json.loads(Path('audit182/source-audit/source-audit.json').read_text())
    final=json.loads(Path('audit182/final-verification.json').read_text())
    require(source.get('passed') and not source.get('failed'),'2103182 source audit failed')

    result={
        'build':VERSION,'locked_parent':2103181,'locked_parent_commit':BASE_COMMIT,
        'android_tests':total,'new_startup_reserve_tests':6,
        'startup_reserve_ms':21000,'startup_wait_ms':32000,
        'readiness_uses_actual_window_duration':True,'premature_nine_second_start_removed':True,
        'segment_duration_excludes_network_idle':True,'discontinuity_sequence_stable':True,
        'unified_blue_timeline_preserved':True,'phone_call_video_continuity_preserved':True,
        'pro_buffer_safeguards_preserved':True,'dns_pin_or_custom_resolver_added':False,
        'native_engine_recompiled':False,'theme_zip_changed':False,'apk_sha256':final['apk_sha256'],
        'physical_device_verified':False,'candidate_locked':False,
        'status':'TEST CANDIDATE - VPN-off startup/buffering physical verification required before lock'}
    Path('signed182/ACCEPTANCE.json').write_text(json.dumps(result,indent=2)+'\n')
    shutil.copy2('audit182/final-verification.json','signed182/2103182-verification.json')
    shutil.copy2('audit182/source-audit/source-audit.json','signed182/2103182-source-audit.json')
    print('PASS:',total,'Android tests + 2103182 startup-reserve gates')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['upgrade','verify','deliver']);a=p.parse_args();globals()[a.phase]()
