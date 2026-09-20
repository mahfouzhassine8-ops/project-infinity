#!/usr/bin/env python3
"""Build identity, preservation gates and evidence accounting for Cobra 2103199."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, re, shutil, subprocess, xml.etree.ElementTree as ET, zipfile

ROOT=Path(__file__).resolve().parent
VERSION=2103199
OLD='1.0.9-Cobra-Complete-Product-Audit-RC1'
NEW='1.0.9-Cobra-Power-Audit-Repairs-RC1'
PARENT='e6b4c0371aacc358ebd7eaff4e79b1bfc1de640b'
BASE='b5fa21731a1662cc7206ac6dc45cb6d6682612cd'
BASE_APK='b1197aae8456940210a7c99dbd20e849fb8148ebe3bc673ceb56ac1b7c6c660c'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
ACT='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
GRADLE='tools/android/packaging/xbmc/build.gradle.in'

def require(v,msg):
    if not v: raise RuntimeError(msg)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(*args): subprocess.run(list(map(str,args)),check=True)
def replace(path,old,new):
    p=Path(path);s=p.read_text();require(s.count(old)==1,'Identity anchor mismatch: '+old);p.write_text(s.replace(old,new,1))

def upgrade():
    receipt=Path('engine/background-resume-source.json')
    data=json.loads(receipt.read_text())
    require(data['version_code']==2103198 and data['version_name']==OLD,'Wrong reconstructed parent')
    run('python3',ROOT/'apply.py','--source','kodi','--receipt',receipt,'--out','audit199/patch')
    patch=json.loads(Path('audit199/patch/patch.json').read_text())
    for path,row in patch['files'].items(): data['files'][path]['after']=row['after']
    replace(Path('kodi')/GRADLE,'versionCode 2103198','versionCode 2103199')
    replace(Path('kodi')/GRADLE,'versionName "'+OLD+'"','versionName "'+NEW+'"')
    replace('scripts/infinity_background_resume.py','VERSION_CODE = 2103198','VERSION_CODE = 2103199')
    replace('scripts/infinity_background_resume.py',"RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'")
    pack=Path('scripts/package_background_resume.py');s=pack.read_text()
    require(s.count('Infinity-'+OLD)>=2,'Parent packager filename drift')
    pack.write_text(s.replace('Infinity-'+OLD,'Infinity-'+NEW))
    data['files'][GRADLE]['after']=sha(Path('kodi')/GRADLE)
    data.update(version_code=VERSION,version_name=NEW,source_parent=2103198,source_parent_commit=PARENT,
        protected_baseline=2103197,protected_baseline_commit=BASE,
        candidate_locked=False,physical_device_verified=False,runtime_device_tested=False,
        playback_behavior_changed=True,display_geometry_repaired=True,timeshift_controls_repaired=True,
        ui_defects_repaired=True,diagnostic_redaction_repaired=True,
        new_controls=False,network_selection_changed=False,buffer_policy_changed=False,
        parser_flags_changed=False,timeshift_architecture_changed=False,native_engine_recompiled=False,
        theme_zip_changed=False,complete_product_acceptance=False)
    receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    for path,row in data['files'].items(): require(sha(Path('kodi')/path)==row['after'],'Final source drift: '+path)
    text=(Path('kodi')/ACT).read_text()
    # These are preservation checks, not claims that rendered playback was verified.
    preserved={
      'four_button_toolbar':'String[] glyphs={"guide","aspect","multi","more"},labels={"Channels","Display","Multi-View","More"};' in text,
      'no_unrequested_player_hub':'showCobraPlayerOptionsHub' not in text and 'RECENT CHANNELS' not in text,
      'timestamp_rewrite_disabled':'REWRITE_ENABLED=false' in text,
      'watchdog_observation_only':'buffer_observed_no_restart' in text,
      'local_timeshift_architecture':all(x in text for x in ('CobraLocalTimeshiftSession','CobraTimeshiftIngest','CobraTimeshiftServer','/live.ts','/live.m3u8')),
      'existing_aspect_modes':all(x in text for x in ('Fold Adaptive','Custom','CobraFoldAspectPolicy')),
      'network_controls_preserved':'IPv4 only' in text and 'IPv6 only' in text,
      'sources_health_themes':all(x in text for x in ('TV SOURCES','Cobra Health Center','cobra_theme_management')),
    }
    require(all(preserved.values()),'Protected product contract missing: '+repr([k for k,v in preserved.items() if not v]))
    with Path('audit199/native-after.patch').open('wb') as out:
        subprocess.run(['git','-C','kodi','diff','--binary','--','xbmc'],stdout=out,check=True)
    require(Path('audit199/native-after.patch').read_bytes()==Path('engine/native-before.patch').read_bytes(),'Native source drift')
    Path('audit199/source-preservation.json').write_text(json.dumps({'checks':preserved,'passed':True,'source_receipt_files':len(data['files']),'physical_device_verified':False},indent=2)+'\n')
    print('PASS: 2103199 source identities and protected contracts; native source unchanged')

def verify():
    base=Path('baseline197/Infinity-1.0.9-Cobra-Original-Player-Menu-RC1.apk')
    final=Path('signed199/Infinity-'+NEW+'.apk')
    require(sha(base)==BASE_APK,'Not the exact protected 2103197 APK')
    audit=json.loads(Path('signed199/background-resume-apk-audit.json').read_text())
    require(audit['version_code']==VERSION and audit['version_name']==NEW,'Wrong candidate identity')
    require(audit['apk_sha256']==sha(final) and audit['signer_certificate_sha256']==CERT,'Signer/hash mismatch')
    require(audit['native_recompiled'] is False,'Native engine was rebuilt')
    with zipfile.ZipFile(base) as a,zipfile.ZipFile(final) as b:
        require(len(b.namelist())==len(set(b.namelist())) and b.testzip() is None,'Duplicate/corrupt APK members')
        keep={n for n in a.namelist() if n.startswith(('lib/','assets/','res/')) or n=='resources.arsc'}
        require(keep=={n for n in b.namelist() if n.startswith(('lib/','assets/','res/')) or n=='resources.arsc'},'Protected inventory changed')
        for n in keep: require(a.read(n)==b.read(n),'Protected APK bytes changed: '+n)
        dex=b''.join(b.read(n) for n in b.namelist() if re.fullmatch(r'classes\d*\.dex',n))
        require(b'Cobra2103199' not in dex,'Regression tests packaged in release')
    badging=Path('signed199/badging.txt').read_text()
    require("package: name='com.projectinfinity.kodi' versionCode='2103199'" in badging,'Update identity mismatch')
    require('application-debuggable' not in badging,'Debuggable release')
    result={'build':VERSION,'base_build':2103197,'base_commit':BASE,'base_apk_sha256':BASE_APK,
        'apk_sha256':sha(final),'signer':CERT,'protected_payload_entries':len(keep),
        'native_engine_recompiled':False,'native_assets_resources_byte_identical':True,
        'physical_device_verified':False,'installed_update_tested':False}
    Path('audit199/final-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: release identity, permanent signer and exact native/assets/resources preservation')

def deliver():
    results=[]
    locations=[Path('audit159/android/cobra-regression/test-results'),Path('audit159/android/experience/test-results'),
               Path('audit198/android/runtime/test-results'),Path('audit198/targeted/test-results')]
    # Gradle may retain unselected suites between passes. Deduplicate by class;
    # all result files must pass, and inherited/new test counts are separate.
    suites={}
    for folder in locations:
        require(folder.is_dir(),'Missing test evidence: '+str(folder))
        for p in folder.glob('TEST-*.xml'):
            root=ET.parse(p).getroot();name=root.get('name',p.stem)
            require(all(int(root.get(k,'0'))==0 for k in ('failures','errors','skipped')),'Failed/incomplete suite: '+str(p))
            cases=root.findall('testcase')
            require(all(c.find(k) is None for c in cases for k in ('failure','error','skipped')),'Failed/skipped test: '+str(p))
            suites[name]={'suite':name,'tests':len(cases),'evidence':str(p)}
    inherited=[v for k,v in suites.items() if 'Cobra2103199' not in k]
    new=[v for k,v in suites.items() if 'Cobra2103199' in k]
    require(sum(v['tests'] for v in inherited)==265,'Inherited 265-test inventory changed')
    expected_new={'com.projectinfinity.kodi.Cobra2103199TimeshiftRegressionTest':7,
                  'com.projectinfinity.kodi.Cobra2103199DisplayRegressionTest':13,
                  'com.projectinfinity.kodi.Cobra2103199UiRepairTest':7}
    require({v['suite']:v['tests'] for v in new}==expected_new,'New behavioral regression suite inventory changed')
    final=json.loads(Path('audit199/final-verification.json').read_text())
    require(final['apk_sha256']==sha(Path('signed199/Infinity-'+NEW+'.apk')),'Candidate changed after verification')
    result={'build':VERSION,'protected_baseline':2103197,'immediate_parent':2103198,
        'inherited_android_tests':sum(v['tests'] for v in inherited),'new_android_tests':sum(v['tests'] for v in new),
        'android_test_suites':list(suites.values()),'apk_sha256':final['apk_sha256'],
        'native_engine_recompiled':False,'new_controls':False,'redesign':False,
        'physical_device_verified':False,'installed_update_tested':False,'candidate_locked':False,
        'complete_product_acceptance':False,
        'status':'TEST CANDIDATE: automated repairs verified; real-device playback, buffering, decoder, Fold, PiP and SystemUI acceptance pending'}
    Path('signed199/ACCEPTANCE.json').write_text(json.dumps(result,indent=2)+'\n')
    shutil.copy2('audit199/final-verification.json','signed199/2103199-verification.json')
    shutil.copy2('audit199/source-preservation.json','signed199/2103199-source-preservation.json')
    shutil.copy2(ROOT/'DEVICE-TEST.md','signed199/DEVICE-TEST.md')
    shutil.copy2(ROOT/'AUDIT.md','signed199/AUDIT-2103199.md')
    print('PASS:',result['inherited_android_tests'],'inherited +',result['new_android_tests'],'new Android tests. Physical acceptance pending.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['upgrade','verify','deliver']);a=p.parse_args();globals()[a.phase]()
