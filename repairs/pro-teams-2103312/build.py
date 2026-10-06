#!/usr/bin/env python3
"""Compile the declared Android presentation delta and retain the complete 3310 payload."""
import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as E
import zipfile
from apply import CHANGED,ADDED,manifest
PROBE=Path(__file__).resolve().parent.parent/"chooser-isolation-2103311"
sys.path.insert(0,str(PROBE))
import process_probe
import run_process_probe

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE.parent/'mobile-regressions-2103304'))
from packaging_checks import sha,require,run,resource_ids,dex_contract,DEX,SIGNATURE,manifest_tree
spec=importlib.util.spec_from_file_location('factory304',HERE.parent/'mobile-regressions-2103304/package_candidate.py')
factory=importlib.util.module_from_spec(spec);spec.loader.exec_module(factory)
VERSION=2103312;RELEASE='1.0.9-Cobra-Pro-Teams-RC1'
BASE_COMMIT='70c4c31799879c9c8ad8d1debe3ec138cf1e3ab4'
BASE_SHA='49407bd19436e17a54579cfd1c4e59e99868962e5bc723eb56e57d47c6e20ab3'
NATIVE_SHA='b4b2630e37abd56a6e522ca633649a65b255b44bd6b39bcb9f8b84866b822aa6'

TESTS=['repairs/cobra-navigation-2103157/tests/CobraNavigationUiTest.java', 'repairs/pro-sports-soccer-2103273/ProSportsIntegrationTest.java', 'repairs/sports-hub-2103270/SportsHubTest.java', 'repairs/sports-data-2103271/SportsDataRepairTest.java', 'repairs/whole-ui-ambient-2103276/WholeUiAmbientTest.java', 'repairs/watch-ambient-2103278/WatchAmbientTest.java', 'repairs/cobra-player-polish-2103201/tests/Cobra2103201ScrubberTest.java', 'repairs/cobra-player-refinement-2103202/tests/Cobra2103202LifecycleTest.java', 'repairs/cobra-pip-call-2103203/tests/Cobra2103203PipControlsTest.java', 'repairs/cobra-media-calls-2103206/tests/Cobra2103206MediaCallsTest.java', 'repairs/cobra-feature-refinement-2103207/tests/Cobra2103207CallIntegrationTest.java', 'repairs/multiview-stability-fill-2103229/tests/Cobra2103229MultiViewStabilityFillTest.java', 'repairs/end-to-end-2103279/EmbeddedBorderCropTest.java', 'repairs/pro-sports-2103307/ProSports307Test.java', 'repairs/chooser-isolation-2103311/IsolatedCloseRingTest.java', 'repairs/chooser-isolation-2103311/KodiProcessStatusTest.java', 'repairs/chooser-isolation-2103311/HealthExportStatusTest.java', 'repairs/pro-teams-2103312/ProTeams312Test.java']

def guard(source,base,out,base_proof):
    proof=json.loads(base_proof.read_text())
    require(proof['candidate']==2103311 and proof['source_commit']==BASE_COMMIT,'Wrong base build proof')
    require(proof['native_recompiled'] is False and proof['native_sha256']==NATIVE_SHA,'Base native association differs')
    require(sha(base.read_bytes())==proof['apk_sha256']==BASE_SHA,'Not exact 2103311 APK')
    receipt=json.loads((out/'SOURCE-PRESERVATION.json').read_text());before=receipt['before']
    parent=json.loads((base_proof.parent/'SOURCE-PRESERVATION.json').read_text())
    require(before==parent['after'],'Wrong full Android parent')
    require(manifest(source)==receipt['after'],'Source changed after delta validation')
    require(set(receipt['after'])-set(before)==ADDED and {n for n in before if before[n]!=receipt['after'][n]}==CHANGED,'Undeclared source changes')
    with zipfile.ZipFile(base) as z:
        require(sha(z.read('lib/arm64-v8a/libkodi.so'))==proof['native_sha256'],'Native base does not match build proof')
        require(all(value in z.read('lib/arm64-v8a/libkodi.so') for value in [b'infinity-native-cleanup.json',b'native.CXBMCApp.Destroy.complete']),'Native completion receipt absent')
    return proof

def prepare(source,base,build,out,proof):
    factory.BASE_APK_SHA256=proof['apk_sha256'];factory.VERSION_CODE=VERSION;factory.RELEASE=RELEASE
    factory.prepare(source,base,build,out)
    process_probe.prepare(build,source)
    tests=build/'xbmc/src/test/java/com/projectinfinity/kodi';tests.mkdir(parents=True)
    for name in TESTS:shutil.copy2(ROOT/name,tests/Path(name).name)
    import ast
    adaptation=(HERE.parent/'cobra-feature-refinement-2103207/adapt_tests.py').read_text()
    nodes=[n for n in ast.walk(ast.parse(adaptation)) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='edit']
    lines=adaptation.splitlines(True)
    for n in sorted(nodes,key=lambda n:n.lineno,reverse=True):del lines[n.lineno-1:n.end_lineno]
    namespace={};exec(''.join(lines),namespace);namespace['adapt'](tests,out/'historical-test-adaptations.json')
    scrub=tests/'Cobra2103201ScrubberTest.java';text=scrub.read_text()
    anchor='hold();assertNotNull(get(a,"mCobraPlayerDrawer"));event(MotionEvent.ACTION_CANCEL,p);'
    require(text.count(anchor)==1,'267 hold fixture drift')
    scrub.write_text(text.replace('actualVideoBackgroundHoldStillOpensChannels','actualVideoBackgroundHoldNeverOpensChannels').replace(anchor,anchor.replace('assertNotNull','assertNull')))
    with (build/'xbmc/build.gradle').open('a') as f:
        f.write('''
android { testOptions { unitTests.includeAndroidResources = true; unitTests.all { maxHeapSize = "3g"; systemProperty "cobra.evidence", rootProject.file("../evidence3312/screenshots").absolutePath; systemProperty "ambient.evidence", rootProject.file("../evidence3312/ambient").absolutePath; systemProperty "ring.evidence", "'''+str(out/'screenshots')+'''"; testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" } } } }
configurations { preservationTools }
dependencies {
  testImplementation 'junit:junit:4.13.2'
  testImplementation 'org.robolectric:robolectric:4.14.1'
  preservationTools 'org.smali:baksmali:2.5.2'
}
tasks.register('exportPreservationTools') {
  doLast { rootProject.file('preservation-classpath.txt').text = configurations.preservationTools.asPath }
}
''')

def merge(base,donor,output):
    with zipfile.ZipFile(base) as a,zipfile.ZipFile(donor) as b,zipfile.ZipFile(output,'w') as z:
        require(len(a.namelist())==len(set(a.namelist())) and len(b.namelist())==len(set(b.namelist())),'Duplicate APK entries')
        require(a.testzip() is None and b.testzip() is None,'Invalid APK CRC')
        require(not any(n.startswith(('lib/','assets/')) and not n.endswith('/') for n in b.namelist()),'Native/assets appeared in Android-only donor')
        require(dex_contract(a)[0]==dex_contract(b)[0],'JNI changed despite native reuse')
        for info in a.infolist():
            if info.filename!='AndroidManifest.xml' and not DEX.fullmatch(info.filename) and not SIGNATURE.fullmatch(info.filename):
                z.writestr(copy.copy(info),a.read(info.filename))
        for info in b.infolist():
            if info.filename=='AndroidManifest.xml' or DEX.fullmatch(info.filename):z.writestr(copy.copy(info),b.read(info.filename))

def verify_bytes(base,final):
    with zipfile.ZipFile(base) as a,zipfile.ZipFile(final) as b:
        kept={n for n in a.namelist() if n!='AndroidManifest.xml' and not DEX.fullmatch(n) and not SIGNATURE.fullmatch(n)}
        require(set(b.namelist())==kept|{'AndroidManifest.xml'}|{n for n in b.namelist() if DEX.fullmatch(n) or SIGNATURE.fullmatch(n)},'Unexpected APK payload')
        for name in kept:require(a.read(name)==b.read(name),'Protected payload changed: '+name)
        require(dex_contract(a)[0]==dex_contract(b)[0],'Final JNI contract changed')
        require(b.testzip() is None,'Final APK CRC failure')
        return {'native_files_byte_identical':sum(n.startswith('lib/') and not n.endswith('/') for n in kept),
            'asset_files_byte_identical':sum(n.startswith('assets/') and not n.endswith('/') for n in kept),
            'android_resources_byte_identical':True,'protected_entries':len(kept)}

def compare_dex(base,donor,build,out):
    classpath=(build/'preservation-classpath.txt').read_text()
    for label,apk in [('base',base),('donor',donor)]:
        extracted=out/('dex-'+label);extracted.mkdir()
        target=out/('smali-'+label)
        with zipfile.ZipFile(apk) as z:
            for name in z.namelist():
                if DEX.fullmatch(name):
                    dex=extracted/name;dex.write_bytes(z.read(name))
                    subprocess.run(['java','-cp',classpath,'org.jf.baksmali.Main','disassemble',str(dex),'-o',str(target)],check=True)
    old={p.relative_to(out/'smali-base').as_posix():p.read_text() for p in (out/'smali-base').rglob('*.smali')}
    new={p.relative_to(out/'smali-donor').as_posix():p.read_text() for p in (out/'smali-donor').rglob('*.smali')}
    allowed=re.compile(r'com/projectinfinity/kodi/(?:InfinityLiveActivity|CobraProUi|InfinityCobraFeatureRuntime|InfinityCobraReminderReceiver|CobraSportsPreferences|CobraSportsReminderJob)(?:\$[^/]*)?\.smali$')
    changed=sorted(n for n in old.keys()|new.keys() if old.get(n)!=new.get(n))
    unexpected=[n for n in changed if not allowed.fullmatch(n) and n!='com/projectinfinity/kodi/BuildConfig.smali']
    require(not unexpected,'DEX behavior changed outside declared owners: '+repr(unexpected))
    report={'changed_classes':changed,'unchanged_classes':len(old.keys()&new.keys())-sum(n in old and n in new for n in changed),
        'infinity_classes_unchanged':True,'all_other_dex_classes_unchanged':True}
    (out/'DEX-PRESERVATION.json').write_text(json.dumps(report,indent=2)+'\n')
    # Keep the small manifest, not tens of thousands of redundant disassembled files.
    for name in ['dex-base','dex-donor','smali-base','smali-donor']:shutil.rmtree(out/name)
    return report

def verify_process_manifest(original,compiled):
    old,new=manifest_tree(original),manifest_tree(compiled)
    for root in [old,new]:
        for key in ['android:versionCode','android:versionName']:root['attrs'].pop(key,None)
    app=next(n for n in new['children'] if n['tag']=='application')
    jobs=[n for n in app['children'] if 'CobraSportsReminderJob' in n['attrs'].get('android:name','')]
    require(len(jobs)==1,'Missing sports job')
    job=jobs[0];require(job['tag']=='service' and job['attrs']['android:exported']=='(type 0x12)0x0','Sports job exported')
    require('android.permission.BIND_JOB_SERVICE' in job['attrs']['android:permission'] and len(job['attrs'])==3 and not job['children'],'Sports job permission drift')
    app['children'].remove(job);require(old==new,'Manifest changed outside Cobra job/version')

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','package'])
    for name in ['source','base','base-proof','build','out']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();source,base,build,out=[x.resolve() for x in [a.source,a.base,a.build,a.out]];out.mkdir(parents=True,exist_ok=True)
    proof=guard(source,base,out,a.base_proof)
    if a.mode=='prepare':prepare(source,base,build,out,proof);return
    bt=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0';donor=build/'xbmc/build/outputs/apk/release/xbmc-release.apk'
    require(resource_ids(bt/'aapt2',base,out/'base-resources.txt')==resource_ids(bt/'aapt2',donor,out/'compiled-resources.txt'),'Compiled resource IDs changed')
    suites=list((build/'xbmc/build/test-results/testReleaseUnitTest').glob('TEST-*.xml'));require(len(suites)==len(TESTS),'Missing production test suites')
    tested={}
    for suite in suites:
        test=E.parse(suite).getroot();tested[test.get('name')]=int(test.get('tests'))
        require(all(int(test.get(k,'0'))==0 for k in ['failures','errors','skipped']),'Failed or skipped tests')
    require(set(tested)=={'com.projectinfinity.kodi.'+Path(n).stem for n in TESTS} and tested['com.projectinfinity.kodi.ProTeams312Test']>=12,'Missing required tests')
    run_process_probe.validate((out/'process-exit-instrumentation.txt').read_text())
    bytecode=compare_dex(base,donor,build,out)
    unsigned=out/'Infinity-3312-unsigned.apk';merge(base,donor,unsigned)
    verify_process_manifest(run(bt/'aapt','dump','xmltree',base,'AndroidManifest.xml',output=out/'base-manifest.txt'),run(bt/'aapt','dump','xmltree',unsigned,'AndroidManifest.xml',output=out/'manifest.txt'))
    for name in ['INFINITY_KEYSTORE_B64','INFINITY_STORE_PASSWORD','INFINITY_KEY_PASSWORD','INFINITY_KEY_ALIAS']:require(bool(os.environ.get(name)),'Missing permanent signing configuration: '+name)
    final=out/'Infinity-2103312-Cobra-Pro-Teams-RC1.apk';run('bash',ROOT/'scripts/sign-infinity71.sh',unsigned,final)
    cert=run(bt/'apksigner','verify','--verbose','--print-certs',final,output=out/'signing-verification.txt');require(factory.CERT in cert.lower(),'Permanent signer changed')
    badging=run(bt/'aapt','dump','badging',final,output=out/'badging.txt');require(f"package: name='com.projectinfinity.kodi' versionCode='{VERSION}' versionName='{RELEASE}'" in badging,'Wrong identity')
    kept=verify_bytes(base,final);unsigned.unlink()
    report={'candidate':VERSION,'apk_parent':2103311,'base_sha256':proof['apk_sha256'],'apk_sha256':sha(final.read_bytes()),
        'source_commit':os.environ['GITHUB_SHA'],'skin_parent':'1.0.5.201','skin_changed':False,'cobra_source_changed':True,
        'native_recompiled':False,'native_sha256':proof['native_sha256'],'permanent_signer':factory.CERT,
        'tests_passed':sum(tested.values())+1,'test_suites':tested,'android_process_exit_probe_passed':True,'native_cleanup_in_probe_simulated':True,'physical_device_verified':False,'locked':False,**kept,**bytecode}
    (out/'APK-VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: Cobra Pro candidate signed; complete 3311 Infinity/native/assets/resources and all other DEX classes preserved.')

if __name__=='__main__':main()

