#!/usr/bin/env python3
"""Build, gate and package Cobra 2103198 complete-product audit cleanup over exact passed 2103197."""
from pathlib import Path
import argparse,hashlib,json,re,shutil,subprocess,zipfile,xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
BASE_COMMIT='b5fa21731a1662cc7206ac6dc45cb6d6682612cd'
OLD='1.0.9-Cobra-Original-Player-Menu-RC1'
NEW='1.0.9-Cobra-Complete-Product-Audit-RC1'
VERSION=2103198
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
ACT='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
MANIFEST='tools/android/packaging/xbmc/AndroidManifest.xml.in'
GRADLE='tools/android/packaging/xbmc/build.gradle.in'

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(v,msg):
    if not v: raise RuntimeError(msg)
def run(*args): subprocess.run(list(map(str,args)),check=True)
def replace(path,old,new):
    p=Path(path);s=p.read_text();require(s.count(old)==1,'identity anchor drift: '+old);p.write_text(s.replace(old,new,1))

def upgrade():
    receipt=Path('engine/background-resume-source.json')
    data=json.loads(receipt.read_text())
    require(data.get('version_code')==2103197 and data.get('version_name')==OLD,'Expected exact passed 2103197 source receipt')
    for rel,row in data.get('files',{}).items():
        require(sha(Path('kodi')/rel)==row['after'],'2103197 source receipt drift: '+rel)

    run('python3',ROOT/'apply.py','--source','kodi','--receipt',receipt,'--out','audit198/patch')
    patch=json.loads(Path('audit198/patch/patch.json').read_text())
    data['files'][MANIFEST]['after']=patch['files'][MANIFEST]['after']

    gradle=Path('kodi')/GRADLE
    replace(gradle,'versionCode 2103197',f'versionCode {VERSION}')
    replace(gradle,'versionName "'+OLD+'"','versionName "'+NEW+'"')
    runtime=Path('scripts/infinity_background_resume.py')
    replace(runtime,'VERSION_CODE = 2103197',f'VERSION_CODE = {VERSION}')
    replace(runtime,"RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'")

    pack=Path('scripts/package_background_resume.py')
    s=pack.read_text()
    require(s.count('Infinity-'+OLD)>=2,'2103197 packager identity drift')
    s=s.replace('Infinity-'+OLD,'Infinity-'+NEW)
    anchor="""    for tree in (old,new):
        for key in ('android:versionCode','android:versionName'): tree['attrs'].pop(key,None)
    permissions=[n for n in new['children'] if n['tag']=='uses-permission' and
"""
    replacement="""    for tree in (old,new):
        for key in ('android:versionCode','android:versionName'): tree['attrs'].pop(key,None)
    old_boot=[n for n in old['children'] if n['tag']=='uses-permission' and
              'android.permission.RECEIVE_BOOT_COMPLETED' in n['attrs'].get('android:name','')]
    new_boot=[n for n in new['children'] if n['tag']=='uses-permission' and
              'android.permission.RECEIVE_BOOT_COMPLETED' in n['attrs'].get('android:name','')]
    require(len(old_boot)==2,'Inherited base must contain exactly two boot permissions')
    require(len(new_boot)==1,'Audited manifest must contain exactly one boot permission')
    old['children'].remove(old_boot[0])
    permissions=[n for n in new['children'] if n['tag']=='uses-permission' and
"""
    require(s.count(anchor)==1,'Manifest comparator anchor drift')
    pack.write_text(s.replace(anchor,replacement,1))

    data['files'][GRADLE]['after']=sha(gradle)
    data.update(
      version_code=VERSION,version_name=NEW,
      source_parent=2103197,source_parent_commit=BASE_COMMIT,source_parent_locked=True,
      locked_parent=2103197,locked_parent_commit=BASE_COMMIT,candidate_locked=False,
      complete_product_audit=True,release_metadata_reconciled=True,
      manifest_duplicate_boot_permission_removed=True,device_test_guide_current=True,
      tivimate_inspired_player_hub=False,recent_channel_strip=False,video_display_submenu=False,
      original_player_settings_restored=True,original_four_button_toolbar_restored=True,non_menu_polish_preserved=True,motion_polish=True,
      playback_behavior_changed=False,network_selection_changed=False,timeshift_ownership_changed=False,buffer_policy_changed=False,
      parser_flags_changed=False,native_engine_recompiled=False,theme_zip_changed=False,
      physical_device_verified=False,runtime_device_tested=False)

    receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    for rel,row in data['files'].items():
        require(sha(Path('kodi')/rel)==row['after'],'Final 2103198 source receipt drift: '+rel)

    run('python3',ROOT/'source_audit.py','--source','kodi','--receipt',receipt,
        '--patch','audit198/patch/patch.json','--packager',pack,'--out','audit198/source-audit')
    with Path('audit198/native-after.patch').open('wb') as out:
        subprocess.run(['git','-C','kodi','diff','--binary','--','xbmc'],stdout=out,check=True)
    require(Path('audit198/native-after.patch').read_bytes()==Path('engine/native-before.patch').read_bytes(),'Native source changed')
    print('PASS: exact 2103197 -> 2103198 complete-product audit cleanup; runtime/native/playback stack preserved')

def verify():
    base=Path('baseline197/Infinity-'+OLD+'.apk')
    final=Path('signed198/Infinity-'+NEW+'.apk')
    require(base.is_file() and final.is_file(),'Baseline/final APK missing')
    bv=json.loads(Path('baseline197/2103197-verification.json').read_text())
    require(bv['apk_sha256']==sha(base),'Wrong exact passed 2103197 APK')
    audit=json.loads(Path('signed198/background-resume-apk-audit.json').read_text())
    require(audit['version_code']==VERSION and audit['version_name']==NEW,'Final 2103198 identity mismatch')
    require(audit['signer_certificate_sha256']==CERT and audit['apk_sha256']==sha(final),'Signer/hash mismatch')
    require(not audit['native_recompiled'],'Native engine was rebuilt')

    manifest=Path('signed198/manifest.txt').read_text()
    base_manifest=Path('signed198/base-manifest.txt').read_text()
    require(manifest.count('android.permission.RECEIVE_BOOT_COMPLETED')==1,'Final manifest still duplicates RECEIVE_BOOT_COMPLETED')
    require(base_manifest.count('android.permission.RECEIVE_BOOT_COMPLETED')==2,'Historical base duplicate proof changed unexpectedly')

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
          b'TV SOURCES',b'cobra_tv_sources',b'Fold Adaptive',b'Player settings',b'Channel playback',
          b'Health Center',b'Audio & subtitles',b'Aspect / Display',b'Cast / Route',b'Manage sources',
          b'Close player',b'CobraMotionSpec',b'cobra_unified_live_timeline',b'CobraCallAudioPolicy',
          b'buffer_observed_no_restart',b'timeshift_provider_pace_limited',b'DETECT_ACCESS_UNITS+ALLOW_NON_IDR_KEYFRAMES'):
            require(token in dex,'2103198 protected contract missing: '+repr(token))
        require(b'Cobra2103198CompleteProductAuditTest' not in dex,'2103198 test code packaged in release APK')

    badging=Path('signed198/badging.txt').read_text()
    require("package: name='com.projectinfinity.kodi'" in badging and "versionCode='2103198'" in badging,'Final APK not forward-installable')
    shutil.copy2(ROOT/'DEVICE-TEST.md','signed198/DEVICE-TEST.md')
    shutil.copy2(ROOT/'AUDIT.md','signed198/AUDIT-2103198.md')
    result={
      'build':VERSION,'base_build':2103197,'base_commit':BASE_COMMIT,'base_apk_sha256':sha(base),
      'apk_sha256':sha(final),'signer':CERT,'receive_boot_completed_declarations':1,
      'release_metadata_reconciled':True,'device_test_guide_current':True,
      'tivimate_inspired_player_hub':False,'recent_channel_strip':False,'video_display_submenu':False,
      'original_player_settings_restored':True,'original_four_button_toolbar_restored':True,'motion_polish':True,
      'playback_behavior_changed':False,'network_selection_changed':False,'timeshift_ownership_changed':False,
      'buffer_policy_changed':False,'parser_flags_changed':False,'native_engine_recompiled':False,
      'theme_zip_changed':False,'physical_device_verified':False
    }
    Path('audit198/final-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: signed 2103198 fixes manifest/release hygiene while preserving exact 2103197 native/assets/resources/signer and Cobra runtime contracts')

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
    total+=suite('audit198/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualRuntimeTest.xml',17)
    total+=suite('audit198/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualLayoutTest.xml',10)
    for name,count in [
      ('Cobra2103162ThemeRotationTest',15),('Cobra2103164PlaybackStabilityTest',26),('Cobra2103165InsetsPipPlayerTest',6),
      ('Cobra2103166EndToEndUiAuditTest',8),('Cobra2103170StatusBarRestoreSupersessionTest',5),('Cobra2103170StatusBarEdgeTest',7),
      ('Cobra2103175FullscreenBackgroundTest',12),('Cobra2103176LiveRewindTest',5),('Cobra2103177FinalFeatureFreezeTest',10),
      ('Cobra2103178TimeshiftMiniPlayerTest',10),('Cobra2103179BufferResilienceTest',11),('Cobra2103180PlaybackFinalizationTest',6),
      ('Cobra2103181TimeshiftTransportIntegrityTest',6),('Cobra2103182TimeshiftStartupReserveTest',6),('Cobra2103183NetworkFamilyControlTest',6),
      ('Cobra2103184StreamNetworkOptimizationTest',7),('Cobra2103185LiveDiagnosticsFreezeTest',5),('Cobra2103186StreamCadenceFingerprintTest',5),
      ('Cobra2103187TsAccessUnitCompatibilityTest',5),('Cobra2103188TsKeyframeCompatibilityTest',5),('Cobra2103189TsTimelineFingerprintTest',5),
      ('Cobra2103190TsClockNormalizationTest',5),('Cobra2103191ProviderRouteFingerprintTest',5),('Cobra2103192ProviderPaceReserveTest',5),
      ('Cobra2103193SourceManagerRestoreTest',5),('Cobra2103194FoldAdaptiveAspectTest',6),('Cobra2103197OriginalPlayerMenuTest',10),
      ('Cobra2103198CompleteProductAuditTest',12)]:
        total+=suite(Path('audit198/targeted/test-results')/('TEST-com.projectinfinity.kodi.'+name+'.xml'),count)
    require(total==265,f'Expected 265 Android tests, got {total}')
    source=json.loads(Path('audit198/source-audit/source-audit.json').read_text())
    final=json.loads(Path('audit198/final-verification.json').read_text())
    require(source.get('passed') and not source.get('failed'),'2103198 source audit failed')
    result={
      'build':VERSION,'parent_build':2103197,'parent_commit':BASE_COMMIT,'android_tests':total,
      'new_complete_product_tests':12,'source_checks':source.get('check_count'),
      'release_metadata_reconciled':True,'manifest_duplicate_permission_removed':True,'device_test_guide_current':True,
      'tivimate_inspired_player_hub':False,'recent_channel_strip':False,'video_display_submenu':False,
      'original_player_settings_restored':True,'original_four_button_toolbar_restored':True,'motion_polish':True,
      'source_manager_route_restored':True,'fold_adaptive_aspect':True,
      'playback_behavior_changed':False,'network_selection_changed':False,'timeshift_ownership_changed':False,
      'buffer_policy_changed':False,'parser_flags_changed':False,'native_engine_recompiled':False,'theme_zip_changed':False,
      'apk_sha256':final['apk_sha256'],'physical_device_verified':False,'candidate_locked':False,
      'status':'AUTOMATED COMPLETE-PRODUCT AUDIT PASS - physical Fold/provider/GPU/device acceptance pending'
    }
    Path('signed198/ACCEPTANCE.json').write_text(json.dumps(result,indent=2)+'\n')
    shutil.copy2('audit198/final-verification.json','signed198/2103198-verification.json')
    shutil.copy2('audit198/source-audit/source-audit.json','signed198/2103198-source-audit.json')
    print('PASS:',total,'Android tests +',source.get('check_count'),'source checks; release metadata and manifest hygiene reconciled')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['upgrade','verify','deliver']);a=p.parse_args();globals()[a.phase]()
