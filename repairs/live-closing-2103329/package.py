#!/usr/bin/env python3
"""Package live closing UI over 328; retain locked 327 native bytes."""
import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tarfile
import xml.etree.ElementTree as ET
import zipfile

import live_apply as android_polish

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE='f74f0f30047da89bd4d196f54ddd46b6be2ad972ab71346a0e42b4e1805bdcc6'
BASE_NATIVE='a3f95a64b4433a999df37c18ecc48a3a43876c0cc49ae6c5433e82c98835764c'
BASE_COMMIT='b659037704e603cc5163db92d90b0cff377e33cc'
BASE_RUN='37699829878'
VERSION=2103329
RELEASE='1.0.9-Live-Closing-RC1'
ENGINE='lib/arm64-v8a/libkodi.so'

sys.path.insert(0,str(HERE.parent/'mobile-regressions-2103304'))
sys.path.insert(0,str(HERE.parent/'chooser-close-owner-2103324'))
sys.path.insert(0,str(HERE.parent/'jobmanager-close-2103327'))

from packaging_checks import DEX,SIGNATURE,dex_contract,require,resource_ids,run,sha,manifest_tree

spec=importlib.util.spec_from_file_location('parent327',HERE.parent/'jobmanager-close-2103327/package.py')
parent327=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent327)
factory=parent327.factory
EXPECTED_SUITES=dict(parent327.EXPECTED_SUITES,ClosingInfinity328Test=2,LiveClosing329Test=24)

def verify_manifest_pair(original,compiled):
    old,new=manifest_tree(original),manifest_tree(compiled)
    apps=[n for n in new['children'] if n['tag']=='application'];require(len(apps)==1,'Unexpected applications')
    app=apps[0];retained=[];found=[]
    for node in app['children']:
        if node['tag']=='activity' and 'InfinityClosingActivity' in node['attrs'].get('android:name',''):
            found.append(node)
        else:retained.append(node)
    require(len(found)==1,'Missing/duplicate independent closing activity')
    n=found[0];a=n['attrs'];require(not n['children'],'Unexpected activity intent filters')
    require(set(a)=={'android:name','android:exported','android:excludeFromRecents','android:noHistory','android:launchMode','android:resizeableActivity','android:taskAffinity','android:configChanges','android:theme'},'Unexpected activity attributes')
    require(a['android:exported']=='(type 0x12)0x0','Closing activity exported')
    for flag in ('android:excludeFromRecents','android:noHistory','android:resizeableActivity'):
        require(a[flag]=='(type 0x12)0xffffffff','Closing activity flag changed: '+flag)
    require('com.projectinfinity.kodi.closing' in a['android:taskAffinity'],'Wrong task affinity')
    require(a['android:theme'].lower()=='@0x0103023c','Wrong platform dialog theme')
    require(a['android:launchMode']=='(type 0x10)0x1','Closing activity must be singleTop')
    require(a['android:configChanges']=='(type 0x11)0x40001f80','Unexpected handled configuration flags')
    app['children']=retained
    for tree in (old,new):
        for key in ('android:versionCode','android:versionName'):tree['attrs'].pop(key,None)
    require(old==new,'Manifest changed beyond single private closing activity/version')

def verify_parent(base:Path,evidence:Path)->dict:
    require(sha(base.read_bytes())==BASE,'Not exact passed 2103328 APK')
    receipt=json.loads((evidence/'APK-VERIFICATION.json').read_text())
    require(receipt['candidate']==2103328 and receipt['apk_sha256']==BASE,
            'Wrong 2103328 parent receipt')
    require(receipt['source_commit']==BASE_COMMIT and receipt['validation_run']==BASE_RUN,
            'Wrong 2103328 source/run association')
    require(receipt['native_sha256']==BASE_NATIVE and receipt['skin_parent']=='1.0.5.201',
            'Wrong 2103327 native/skin pairing')
    require(receipt['signer_certificate_sha256']==parent327.parent.parent.CERT,
            'Wrong permanent signer in 2103328 receipt')
    with zipfile.ZipFile(base) as z:
        require(sha(z.read(ENGINE))==BASE_NATIVE,'2103327 packaged native mismatch')
        require(z.testzip() is None,'2103328 base APK CRC failure')
    return receipt

def prepare(base:Path,build:Path,out:Path)->None:
    evidence=ROOT/'parent3328'
    verify_parent(base,evidence)
    with tarfile.open(evidence/'repaired-shell-source.tar.gz') as archive:
        archive.extractall(out/'parent-extracted',filter='data')
    dest=out/'android-source'
    shutil.copytree(out/'parent-extracted/shell-kodi',dest)
    delta=android_polish.apply(
        dest,evidence/'SOURCE-PRESERVATION.json',out/'SOURCE-PRESERVATION.json')

    factory.BASE_APK_SHA256=BASE
    factory.VERSION_CODE=VERSION
    factory.RELEASE=RELEASE
    factory.prepare(dest.resolve(),base.resolve(),build.resolve(),out.resolve())

    tests=build/'xbmc/src/test/java/com/projectinfinity/kodi';tests.mkdir(parents=True)
    names=[
      'repairs/cobra-navigation-2103157/tests/CobraNavigationUiTest.java',
      'repairs/sports-hub-2103270/SportsHubTest.java',
      'repairs/cobra-pro-preview-2103321/ProTeams312Test.java',
      'repairs/cobra-pro-season-2103317/CobraProSeason317Test.java',
      'repairs/cobra-pro-refinement-2103322/CobraProHandoffTest.java',
      'repairs/cobra-power-audit-2103199/tests/Cobra2103199TimeshiftRegressionTest.java',
      'repairs/whole-ui-ambient-2103276/WholeUiAmbientTest.java',
      'repairs/multiview-stability-fill-2103229/tests/Cobra2103229MultiViewStabilityFillTest.java',
      'repairs/cobra-pro-refinement-2103322/CobraProRefinementTest.java',
      'repairs/cobra-pro-refinement-2103322/CobraProControlsRefinementTest.java',
      'repairs/cobra-pro-refinement-2103322/CobraProPausedReturnTest.java',
      'repairs/cobra-sports-live-2103323/CobraSportsLiveFeedTest.java',
      'repairs/chooser-close-owner-2103324/KodiProcessStatusTest.java',
      'repairs/chooser-close-owner-2103324/CloseProgress316Test.java',
      'repairs/chooser-close-owner-2103324/CobraCloseIsolation316Test.java',
      'repairs/chooser-close-owner-2103324/AndroidTaskRemoval315Test.java',
      'repairs/chooser-close-owner-2103324/KodiOwnerLeaseTest.java',
      'repairs/cooperative-close-2103326/CooperativeClose326Test.java',
      'repairs/jobmanager-close-2103327/ShutdownDiagnostics327ExportTest.java',
      'repairs/closing-infinity-2103328/ClosingInfinity328Test.java',
      'repairs/live-closing-2103329/LiveClosing329Test.java',
    ]
    for name in names: shutil.copy2(ROOT/name,tests/Path(name).name)
    resources=build/'xbmc/src/test/resources';resources.mkdir(parents=True)
    shutil.copy2(HERE/'trace-fixtures.json',resources/'closing-trace-fixtures.json')
    shutil.copy2(HERE.parent/'cobra-pro-season-2103317/schedule-fixtures.json',
                 resources/'schedule-fixtures.json')
    previous=tests/'ProTeams312Test.java'
    previous.write_text(previous.read_text().replace(
      '@Test public void proDrawerSportsOpensSameHubAndSelectionSurvivesRerender()',
      '/* Sports drawer destination intentionally removed in 317; Pro tab is tested instead. */ public void proDrawerSportsOpensSameHubAndSelectionSurvivesRerender()'))
    with (build/'xbmc/build.gradle').open('a') as gradle:
        gradle.write('''
android { testOptions { unitTests.includeAndroidResources = true; unitTests.all { maxHeapSize = "3g"; systemProperty "cobra.evidence", rootProject.file("../evidence3329/screenshots").absolutePath; testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" } } } }
configurations { preservationTools }
dependencies { testImplementation 'junit:junit:4.13.2'; testImplementation 'org.robolectric:robolectric:4.14.1'; preservationTools 'org.smali:baksmali:2.5.2' }
tasks.register('exportPreservationTools') { doLast { rootProject.file('preservation-classpath.txt').text = configurations.preservationTools.asPath } }
''')
    (out/'PREPARE.json').write_text(json.dumps({
      'candidate':VERSION,'parent':2103328,'locked_rollback':2103327,'native_recompiled':False,
      'native_sha256':BASE_NATIVE,'changed':delta['changed']},indent=2)+'\n')

def merge(base:Path,donor:Path,output:Path)->None:
    with zipfile.ZipFile(base) as original,zipfile.ZipFile(donor) as compiled,zipfile.ZipFile(output,'w') as result:
        require(len(original.namelist())==len(set(original.namelist())) and
                len(compiled.namelist())==len(set(compiled.namelist())),
                'Duplicate APK entries')
        require(original.testzip() is None and compiled.testzip() is None,'Bad APK CRC')
        require(sha(original.read(ENGINE))==BASE_NATIVE,'Wrong base native payload')
        require(dex_contract(original)[0]==dex_contract(compiled)[0],'JNI declarations changed')
        require(not any(name.startswith(('lib/','assets/')) and not name.endswith('/')
                        for name in compiled.namelist()),
                'Unexpected donor assets or native code')
        for info in original.infolist():
            if info.filename!='AndroidManifest.xml' and not DEX.fullmatch(info.filename) and not SIGNATURE.fullmatch(info.filename):
                result.writestr(copy.copy(info),original.read(info.filename))
        for info in compiled.infolist():
            if info.filename=='AndroidManifest.xml' or DEX.fullmatch(info.filename):
                result.writestr(copy.copy(info),compiled.read(info.filename))

def verify_payload(base:Path,final:Path)->dict:
    with zipfile.ZipFile(base) as original,zipfile.ZipFile(final) as candidate:
        kept={name for name in original.namelist()
              if name!='AndroidManifest.xml' and not DEX.fullmatch(name) and not SIGNATURE.fullmatch(name)}
        expected=kept|{'AndroidManifest.xml'}|{name for name in candidate.namelist()
                                             if DEX.fullmatch(name) or SIGNATURE.fullmatch(name)}
        require(set(candidate.namelist())==expected and len(candidate.namelist())==len(expected),
                'Unexpected final APK payload')
        for name in kept:
            require(original.read(name)==candidate.read(name),'Protected entry changed: '+name)
        require(sha(candidate.read(ENGINE))==BASE_NATIVE,'2103327 native engine changed')
        require(dex_contract(original)[0]==dex_contract(candidate)[0],'Final JNI contract changed')
        require(candidate.testzip() is None,'Bad final APK CRC')
        return {
          'protected_entries':len(kept),
          'native_byte_identical_to_2103327':True,
          'skin_and_assets_byte_identical':True,
          'android_resources_byte_identical':True,
          'other_native_libraries_byte_identical':True,
          'jni_contract_unchanged':True,
        }

def package(base:Path,build:Path,out:Path)->None:
    evidence=ROOT/'parent3328';verify_parent(base,evidence)
    delta=json.loads((out/'SOURCE-PRESERVATION.json').read_text())
    android_polish.verify(out/'android-source',out/'SOURCE-PRESERVATION.json')
    require(set(delta['changed'])==set(json.loads((HERE/'android-delta.json').read_text())['after']),'Unexpected Android source delta')

    bt=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0'
    donor=build/'xbmc/build/outputs/apk/release/xbmc-release.apk'
    require(resource_ids(bt/'aapt2',base,out/'base-resources.txt')==
            resource_ids(bt/'aapt2',donor,out/'donor-resources.txt'),
            'Resource IDs changed')
    unsigned=out/'candidate-unsigned.apk';merge(base,donor,unsigned)
    verify_manifest_pair(
      run(bt/'aapt','dump','xmltree',base,'AndroidManifest.xml',output=out/'base-manifest.txt'),
      run(bt/'aapt','dump','xmltree',unsigned,'AndroidManifest.xml',output=out/'candidate-manifest.txt'))

    final=out/'Infinity-2103329-Live-Closing-RC1.apk'
    run('bash',ROOT/'scripts/sign-infinity71.sh',unsigned,final)
    cert=run(bt/'apksigner','verify','--verbose','--print-certs',final,
             output=out/'signing-verification.txt')
    require(parent327.parent.parent.CERT in cert.lower(),'Permanent signer changed')
    badging=run(bt/'aapt','dump','badging',final,output=out/'badging.txt')
    require(f"package: name='com.projectinfinity.kodi' versionCode='{VERSION}' versionName='{RELEASE}'" in badging,
            'Wrong APK identity')
    require('application-debuggable' not in badging,'Release is debuggable')

    recording=parent327.dex_equivalence.verify(base,final,build,out,DEX,require)
    allowed_dex=re.compile(
      r'com/projectinfinity/kodi/(?:InfinityCloseGuardService|InfinityCloseProgress|InfinityClosingActivity|InfinityPowerControlActivity|BuildConfig)(?:\$[^/]*)?\.smali$|'
      r'com/projectinfinity/kodi/InfinityCobraRecordingService'
      r'(?:\$\$ExternalSyntheticLambda\d+)?\.smali$')
    import bridge_preservation as bridge_guard
    parent327.parent.ALLOWED_DEX=allowed_dex
    bridge_guard.ALLOWED=allowed_dex
    dex=parent327.parent.compare_dex(base,final,build,out)
    dex['cobra_recording_compiler_equivalence']=recording
    dex['closing_notification_behavior_changed']=True
    dex['native_shutdown_behavior_preserved']=True
    require(dex['all_other_classes_behavior_identical'] is True and
            dex['api_bridge_renumbering_verified'] is True,
            'DEX preservation did not prove unrelated behavior unchanged')
    (out/'DEX-PRESERVATION.json').write_text(json.dumps(dex,indent=2)+'\n')

    suites=[]
    for path in sorted((build/'xbmc/build/test-results/testReleaseUnitTest').glob('TEST-*.xml')):
        attrs=ET.parse(path).getroot().attrib
        suites.append({'suite':attrs['name'],**{
          key:int(attrs.get(key,0)) for key in ('tests','failures','errors','skipped')}})
    expected={'com.projectinfinity.kodi.'+name for name in EXPECTED_SUITES}
    require({s['suite'] for s in suites}==expected,'An inherited or 2103329 suite is missing')
    require(all(s['tests']>=EXPECTED_SUITES[s['suite'].rsplit('.',1)[-1]] and
                s['failures']==s['errors']==s['skipped']==0 for s in suites),
            'Tests missing, reduced, failed or skipped')

    report={
      'candidate':VERSION,'version_name':RELEASE,'apk_parent':2103328,'locked_rollback':2103327,
      'base_apk_sha256':BASE,'base_source_commit':BASE_COMMIT,'base_validation_run':BASE_RUN,
      'apk_sha256':sha(final.read_bytes()),'native_sha256':BASE_NATIVE,
      'source_commit':os.environ['GITHUB_SHA'],'validation_run':os.environ.get('GITHUB_RUN_ID'),
      'signer_certificate_sha256':parent327.parent.parent.CERT,
      'skin_parent':'1.0.5.201','skin_candidate':'1.0.5.203','skin_changed_in_apk':False,
      'data_reset':False,'native_recompiled':False,'native_changed':False,
      'shutdown_algorithm_changed':False,'closing_notification_polish':True,
      'physical_device_verified':False,'locked':False,
      'android_source_delta':delta['changed'],'test_suites':suites,
      'test_total':sum(s['tests'] for s in suites),
      **verify_payload(base,final),**dex,
    }
    (out/'APK-VERIFICATION.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    with tarfile.open(out/'repaired-shell-source.tar.gz','w:gz') as archive:
        archive.add(out/'android-source',arcname='shell-kodi')
    unsigned.unlink()
    print('PASS: signed Android-only Closing Infinity candidate; exact 2103327 native retained. Not device accepted or locked.')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['prepare','package'])
    for name in ('base','build','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    (prepare if a.mode=='prepare' else package)(a.base,a.build,a.out)

if __name__=='__main__':main()
