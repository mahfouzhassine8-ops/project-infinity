#!/usr/bin/env python3
"""Source-built diagnostic candidate over exact locked 2103324. Never locks itself."""
import argparse,copy,importlib.util,json,os,re,shutil,subprocess,sys,tarfile
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile
import android_apply,native_patch
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE='5af58f2e700e636cdc798cbde0acc89e8091153cfcf1e17c792375fe285dd8c3'
BASE_NATIVE='b4b2630e37abd56a6e522ca633649a65b255b44bd6b39bcb9f8b84866b822aa6'
BASE_COMMIT='9f621f34e3ded845e1c3e9c2a49d98158b6e31b3'
VERSION=2103325
RELEASE='1.0.9-Shutdown-Diagnostics-RC1'
ENGINE='lib/arm64-v8a/libkodi.so'
sys.path.insert(0,str(HERE.parent/'mobile-regressions-2103304'))
sys.path.insert(0,str(HERE.parent/'chooser-close-owner-2103324'))
from packaging_checks import DEX,SIGNATURE,require,resource_ids,run,sha,verify_manifest_pair,dex_contract
spec=importlib.util.spec_from_file_location('locked3324',HERE.parent/'chooser-close-owner-2103324/package.py')
parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)
factory=parent.parent.factory
EXPECTED_SUITES=dict(parent.EXPECTED_SUITES,ShutdownDiagnostics325Test=8)

def bound_native(engine,out):
    proof=json.loads((engine/'ENGINE-PROOF.json').read_text())
    require(proof['candidate']==VERSION and proof['locked_apk_parent']==2103324,'Wrong native candidate parent')
    require(proof['source_commit']==os.environ['INFINITY_NATIVE_SOURCE_COMMIT'],'Wrong immutable native source commit')
    require(proof['baseline_kodi_commit']=='a3a448d26b8d560a65655dab2cd122994dc4e146','Wrong Kodi baseline')
    require(proof['diagnostics_only'] is True and proof['shutdown_behavior_changed'] is False,'Not a diagnostic native build')
    source=json.loads((engine/'source-manifest.json').read_text())
    require(sha(json.dumps(source['before'],sort_keys=True,separators=(',',':')).encode())==native_patch.PARENT_MAP,'Wrong complete native map')
    changed={n for n in source['before'].keys()|source['after'].keys() if source['before'].get(n)!=source['after'].get(n)}
    require(changed==native_patch.ALLOWED and set(source['changed'])==changed,'Unexpected native delta')
    require(set(source['after'])-set(source['before'])=={native_patch.HEADER},'Unexpected native source additions')
    original=engine/'libkodi.so'
    require(sha(original.read_bytes())==proof['native_sha256'],'Raw native build does not match receipt')
    data=original.read_bytes()
    require(all(token in data for token in (b'infinity-shutdown-2103325-v1',b'infinity-shutdown-native.jsonl',b'_infinityHeartbeat',b'/InfinityAndroidKeyboard')),'Native trace or preserved JNI registration missing')
    identity=factory.elf_identity(original,out/'unstripped-elf-identity.txt')
    native=out/'libkodi.so';shutil.copy2(original,native)
    strip=Path(os.environ['ANDROID_HOME'])/'ndk'/os.environ.get('NDK_VER','21.4.7075529')/'toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip'
    run(strip,'--strip-unneeded',native)
    final_identity=factory.elf_identity(native,out/'packaged-elf-identity.txt')
    require(final_identity[0]==identity[0],'ELF identity kind changed')
    if identity[0]=='build-id':require(final_identity==identity,'ELF build ID changed')
    require(sha(native.read_bytes())!=BASE_NATIVE,'Diagnostic engine was not replaced')
    shutil.copy2(engine/'source-manifest.json',out/'native-source-manifest.json')
    shutil.copy2(engine/'ENGINE-PROOF.json',out/'ENGINE-PROOF.json')
    return native,{'unstripped_native_sha256':proof['native_sha256'],'packaged_native_sha256':sha(native.read_bytes()),
                   'native_source_commit':proof['source_commit'],'native_build_id':identity[1] if identity[0]=='build-id' else None}

def prepare(base,build,out,engine):
    require(sha(base.read_bytes())==BASE,'Not exact locked 2103324 APK')
    evidence=ROOT/'parent3324'
    receipt=json.loads((evidence/'APK-VERIFICATION.json').read_text())
    require(receipt['candidate']==2103324 and receipt['source_commit']==BASE_COMMIT and receipt['apk_sha256']==BASE,'Wrong parent source/APK association')
    require(receipt['native_sha256']==BASE_NATIVE and receipt['skin_parent']=='1.0.5.201' and receipt['signer_certificate_sha256']==parent.parent.CERT,'Wrong native, skin or signer parent')
    native,native_report=bound_native(engine,out)
    with tarfile.open(evidence/'repaired-shell-source.tar.gz') as archive:
        archive.extractall(out/'parent-extracted',filter='data')
    dest=out/'android-source';shutil.copytree(out/'parent-extracted/shell-kodi',dest)
    metadata=json.loads((HERE.parent/'cobra-pro-season-2103317/parent-metadata.json').read_text())
    for name,text in metadata.items():
        p=dest/name
        if not p.exists():p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    delta=android_apply.apply(dest,evidence/'SOURCE-PRESERVATION.json',sha(native.read_bytes()))
    (out/'SOURCE-PRESERVATION.json').write_text(json.dumps(delta,indent=2)+'\n')
    (out/'NATIVE-ASSOCIATION.json').write_text(json.dumps(native_report,indent=2)+'\n')
    factory.BASE_APK_SHA256=BASE;factory.VERSION_CODE=VERSION;factory.RELEASE=RELEASE
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
      'repairs/shutdown-diagnostics-2103325/ShutdownDiagnostics325Test.java']
    for name in names:shutil.copy2(ROOT/name,tests/Path(name).name)
    resources=build/'xbmc/src/test/resources';resources.mkdir(parents=True)
    shutil.copy2(HERE.parent/'cobra-pro-season-2103317/schedule-fixtures.json',resources/'schedule-fixtures.json')
    p=tests/'ProTeams312Test.java'
    p.write_text(p.read_text().replace('@Test public void proDrawerSportsOpensSameHubAndSelectionSurvivesRerender()',
      '/* Sports drawer destination intentionally removed in 317; Pro tab is tested instead. */ public void proDrawerSportsOpensSameHubAndSelectionSurvivesRerender()'))
    with (build/'xbmc/build.gradle').open('a') as f:f.write('''
android { testOptions { unitTests.includeAndroidResources = true; unitTests.all { maxHeapSize = "3g"; systemProperty "cobra.evidence", rootProject.file("../evidence3325/screenshots").absolutePath; testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" } } } }
configurations { preservationTools }
dependencies { testImplementation 'junit:junit:4.13.2'; testImplementation 'org.robolectric:robolectric:4.14.1'; preservationTools 'org.smali:baksmali:2.5.2' }
tasks.register('exportPreservationTools') { doLast { rootProject.file('preservation-classpath.txt').text = configurations.preservationTools.asPath } }
''')

def merge(base,donor,native,output):
    with zipfile.ZipFile(base) as a,zipfile.ZipFile(donor) as b,zipfile.ZipFile(output,'w') as z:
        require(len(a.namelist())==len(set(a.namelist())) and len(b.namelist())==len(set(b.namelist())),'Duplicate APK entries')
        require(a.testzip() is None and b.testzip() is None,'Bad APK CRC')
        require(sha(a.read(ENGINE))==BASE_NATIVE,'Wrong parent native payload')
        require(dex_contract(a)[0]==dex_contract(b)[0],'JNI declarations changed')
        require(not any(n.startswith(('lib/','assets/')) and not n.endswith('/') for n in b.namelist()),'Unexpected donor assets or native code')
        for info in a.infolist():
            if info.filename not in ('AndroidManifest.xml',ENGINE) and not DEX.fullmatch(info.filename) and not SIGNATURE.fullmatch(info.filename):z.writestr(copy.copy(info),a.read(info.filename))
        for info in b.infolist():
            if info.filename=='AndroidManifest.xml' or DEX.fullmatch(info.filename):z.writestr(copy.copy(info),b.read(info.filename))
        z.write(native,ENGINE,compress_type=zipfile.ZIP_STORED)

def verify_payload(base,final,native):
    with zipfile.ZipFile(base) as a,zipfile.ZipFile(final) as b:
        kept={n for n in a.namelist() if n not in ('AndroidManifest.xml',ENGINE) and not DEX.fullmatch(n) and not SIGNATURE.fullmatch(n)}
        expected=kept|{'AndroidManifest.xml',ENGINE}|{n for n in b.namelist() if DEX.fullmatch(n) or SIGNATURE.fullmatch(n)}
        require(set(b.namelist())==expected and len(b.namelist())==len(expected),'Unexpected final payload')
        for n in kept:require(a.read(n)==b.read(n),'Protected entry changed: '+n)
        require(b.read(ENGINE)==native.read_bytes(),'Native payload differs from validated engine')
        require(dex_contract(a)[0]==dex_contract(b)[0],'Final JNI contract changed')
        require(b.testzip() is None,'Bad final APK CRC')
        return {'protected_entries':len(kept),'skin_and_assets_byte_identical':True,'android_resources_byte_identical':True,'other_native_libraries_byte_identical':True,'jni_contract_unchanged':True}

def package(base,build,out,engine):
    require(sha(base.read_bytes())==BASE,'Wrong locked APK at packaging')
    delta=json.loads((out/'SOURCE-PRESERVATION.json').read_text())
    require(android_apply.snapshot(out/'android-source')==delta['after'] and delta['changed']==android_apply.ALLOWED,'Android source changed after tests')
    native,native_report=bound_native(engine,out)
    require(delta['native_engine_sha256']==sha(native.read_bytes()),'Java runtime native identity mismatch')
    bt=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0';donor=build/'xbmc/build/outputs/apk/release/xbmc-release.apk'
    require(resource_ids(bt/'aapt2',base,out/'base-resources.txt')==resource_ids(bt/'aapt2',donor,out/'donor-resources.txt'),'Resource IDs changed')
    unsigned=out/'candidate-unsigned.apk';merge(base,donor,native,unsigned)
    verify_manifest_pair(run(bt/'aapt','dump','xmltree',base,'AndroidManifest.xml',output=out/'base-manifest.txt'),run(bt/'aapt','dump','xmltree',unsigned,'AndroidManifest.xml',output=out/'candidate-manifest.txt'))
    final=out/'Infinity-2103325-Shutdown-Diagnostics-RC1.apk'
    run('bash',ROOT/'scripts/sign-infinity71.sh',unsigned,final)
    cert=run(bt/'apksigner','verify','--verbose','--print-certs',final,output=out/'signing-verification.txt')
    require(parent.parent.CERT in cert.lower(),'Permanent signer changed')
    badging=run(bt/'aapt','dump','badging',final,output=out/'badging.txt')
    require(f"package: name='com.projectinfinity.kodi' versionCode='{VERSION}' versionName='{RELEASE}'" in badging,'Wrong APK identity')
    require('application-debuggable' not in badging,'Release is debuggable')
    diagnostic_dex=re.compile(r'com/projectinfinity/kodi/(?:InfinityExitCompletion|Main|InfinityHealthExport|InfinityExitDiagnostics|BuildConfig)(?:\$[^/]*)?\.smali$')
    # The inherited 2103324 bridge guard has a second allow-list. Keep that
    # exact-body protection enabled for every unrelated class while declaring
    # only the four Android diagnostic families intentionally changed here.
    import bridge_preservation as bridge_guard
    parent.ALLOWED_DEX=diagnostic_dex
    bridge_guard.ALLOWED=diagnostic_dex
    dex=parent.compare_dex(base,final,build,out)
    require(dex['all_other_classes_behavior_identical'] is True and
            dex['api_bridge_renumbering_verified'] is True,
            'Diagnostic DEX preservation guard did not prove unrelated behavior unchanged')
    suites=[]
    for path in sorted((build/'xbmc/build/test-results/testReleaseUnitTest').glob('TEST-*.xml')):
        a=ET.parse(path).getroot().attrib
        suites.append({'suite':a['name'],**{k:int(a.get(k,0)) for k in ('tests','failures','errors','skipped')}})
    require({s['suite'] for s in suites}=={'com.projectinfinity.kodi.'+n for n in EXPECTED_SUITES},'A locked or diagnostic suite is missing')
    require(all(s['tests']>=EXPECTED_SUITES[s['suite'].rsplit('.',1)[-1]] and s['failures']==s['errors']==s['skipped']==0 for s in suites),'A test failed, was omitted or skipped')
    report={'candidate':VERSION,'version_name':RELEASE,'apk_parent':2103324,'base_apk_sha256':BASE,'base_source_commit':BASE_COMMIT,
            'apk_sha256':sha(final.read_bytes()),'native_sha256':sha(native.read_bytes()),'source_commit':os.environ['GITHUB_SHA'],'validation_run':os.environ.get('GITHUB_RUN_ID'),
            'signer_certificate_sha256':parent.parent.CERT,'skin_parent':'1.0.5.201','skin_changed':False,'data_reset':False,
            'native_recompiled':True,'diagnostics_only':True,'shutdown_hang_resolved':False,'physical_device_verified':False,'locked':False,
            'android_source_delta':delta['changed'],'test_suites':suites,'test_total':sum(s['tests'] for s in suites),
            **native_report,**verify_payload(base,final,native),**dex}
    (out/'APK-VERIFICATION.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    with tarfile.open(out/'repaired-shell-source.tar.gz','w:gz') as archive:archive.add(out/'android-source',arcname='shell-kodi')
    unsigned.unlink()
    print('PASS: permanently signed diagnostic APK, preserved locked payload and passing suites. Not device accepted or locked.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['prepare','package'])
    for name in ('base','build','out','engine'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    (prepare if a.mode=='prepare' else package)(a.base,a.build,a.out,a.engine)
