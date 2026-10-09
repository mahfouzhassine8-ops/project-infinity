#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Permanently signed test APK: exact approved 3327 payload plus the new engine.
Reuse the existing Android factory and preservation gates; no new saving/lifecycle code.
"""
from pathlib import Path
import argparse, importlib.util, json, os, re, shutil, sys, tarfile, xml.etree.ElementTree as ET
import native

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE='02449fea9c76ad6a370f2ca26a88fdee3a681f83bdc3efa73f8e213f22d4c4d5'
BASE_NATIVE='a3f95a64b4433a999df37c18ecc48a3a43876c0cc49ae6c5433e82c98835764c'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
ANDROID_MAP='7a40be4f2515ed1304af01debb25529298b1db043c1af20fce7397b368c31e15'
VERSION=2103339
RELEASE='1.0.9-Kodi22-Selective-Shutdown-RC1'
HEALTH='tools/android/packaging/xbmc/src/InfinityHealthExport.java.in'
EXIT='tools/android/packaging/xbmc/src/InfinityExitDiagnostics.java.in'
ALLOWED={HEALTH,EXIT}
PARENT=ROOT/'parent3327'

sys.path.insert(0,str(HERE.parent/'jobmanager-close-2103327'))
spec=importlib.util.spec_from_file_location('verified_packager3327',HERE.parent/'jobmanager-close-2103327/package.py')
legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
legacy.BASE=BASE;legacy.BASE_NATIVE=BASE_NATIVE
require=legacy.require
run=legacy.run

def write(path,value):
    path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')

def verify_parent(base):
    require(native.file_digest(base)==BASE,'Not the exact approved 3327 APK')
    p=json.loads((PARENT/'APK-VERIFICATION.json').read_text())
    require(p['candidate']==2103327 and p['source_commit']==native.BASE_COMMIT and
        p['validation_run']=='37687616440' and p['apk_sha256']==BASE and
        p['native_sha256']==BASE_NATIVE and p['signer_certificate_sha256']==CERT and
        p['skin_parent']=='1.0.5.201','Parent identity/skin/signing mismatch')
    require(legacy.parent.parent.CERT==CERT,'Signing contract changed')
    return p

def bound_native(engine,out):
    p=json.loads((engine/'ENGINE-PROOF.json').read_text())
    m=json.loads((engine/'source-manifest.json').read_text())
    require(p['candidate']==VERSION and p['native_parent']==2103327 and
        p['apk_parent']==2103327 and p['locked_rollback']==2103327,'Wrong new engine parent')
    require(p['source_commit']==os.environ['INFINITY_NATIVE_SOURCE_COMMIT'] and
        p['build_run']==os.environ['INFINITY_NATIVE_RUN_ID'],'New engine run/commit mismatch')
    require(p['upstream_commit']==native.UPSTREAM and p['player_guard_forwardport'] is True and
        p['final_joins_preserved'] is True and p['python_unchanged'] is True and
        p['scanner_order_unchanged'] is True and p['no_new_persistence'] is True and
        p['trace_engine']==native.NEW_TAG,'Unexpected engine behavior contract')
    require(native.map_digest(m['before'])==native.PARENT_MAP,'Wrong full native source map')
    changed={n for n in m['before'].keys()|m['after'].keys() if m['before'].get(n)!=m['after'].get(n)}
    require(changed=={native.APP,native.TRACE} and set(m['changed'])==changed and
        m['before'].keys()==m['after'].keys(),'Native allowlist violated')
    tests=json.loads((engine/'HOST-TESTS.json').read_text())
    require(tests['actual_kodi_posix_locks'] is True and tests['exact_generated_method_tested'] is True and
        len(tests['repetitions'])==6 and all(r['scenarios']==6 for r in tests['repetitions']),
        'Native host-test evidence missing')
    source=engine/'libkodi.so'
    require(native.file_digest(source)==p['native_sha256'],'Native binary hash mismatch')
    before=legacy.factory.elf_identity(source,out/'unstripped-elf-identity.txt')
    packaged=out/'libkodi.so';shutil.copy2(source,packaged)
    strip=Path(os.environ['ANDROID_HOME'])/'ndk'/os.environ.get('NDK_VER','21.4.7075529')/'toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip'
    run(strip,'--strip-unneeded',packaged)
    after=legacy.factory.elf_identity(packaged,out/'packaged-elf-identity.txt')
    require(before[0]==after[0] and (before[0]!='build-id' or before==after),'ELF identity changed')
    new_hash=native.file_digest(packaged)
    require(new_hash!=BASE_NATIVE,'Old engine substituted')
    for name in ('ENGINE-PROOF.json','HOST-TESTS.json'):
        shutil.copy2(engine/name,out/name)
    shutil.copy2(engine/'source-manifest.json',out/'native-source-manifest.json')
    return packaged,dict(native_sha256=new_hash,packaged_native_sha256=new_hash,
        unstripped_native_sha256=p['native_sha256'],native_source_commit=p['source_commit'],
        native_validation_run=p['build_run'],native_build_id=before[1] if before[0]=='build-id' else None)

def update_identity(source,out,native_hash):
    expected=json.loads((PARENT/'SOURCE-PRESERVATION.json').read_text())['after']
    require(native.map_digest(expected)==ANDROID_MAP,'Wrong complete Android parent map')
    before=native.snapshot(source);require(before==expected,'Android source differs from exact approved parent')
    for name in ALLOWED:
        p=source/name;t=p.read_text()
        require(t.count(BASE_NATIVE)==1,'Native identity preimage missing: '+name)
        t=t.replace(BASE_NATIVE,native_hash,1)
        if name==HEALTH:
            require(t.count(native.OLD_TAG)==1,'Diagnostic tag preimage missing')
            t=t.replace(native.OLD_TAG,native.NEW_TAG,1)
        p.write_text(t)
    after=native.snapshot(source)
    require(before.keys()==after.keys() and {n for n in before if before[n]!=after[n]}==ALLOWED,'Undeclared Android source delta')
    write(out/'SOURCE-PRESERVATION.json',dict(candidate=VERSION,parent=2103327,
        before=before,after=after,changed=sorted(ALLOWED),native_sha256=native_hash,
        shutdown_trace_engine=native.NEW_TAG,physical_device_verified=False,locked=False))

def stage_tests(build):
    tests=build/'xbmc/src/test/java/com/projectinfinity/kodi';tests.mkdir(parents=True)
    # Same suite sources as the verified 3327 build. No test is removed or skipped.
    paths=[
      'cobra-navigation-2103157/tests/CobraNavigationUiTest.java',
      'sports-hub-2103270/SportsHubTest.java',
      'cobra-pro-preview-2103321/ProTeams312Test.java',
      'cobra-pro-season-2103317/CobraProSeason317Test.java',
      'cobra-pro-refinement-2103322/CobraProHandoffTest.java',
      'cobra-power-audit-2103199/tests/Cobra2103199TimeshiftRegressionTest.java',
      'whole-ui-ambient-2103276/WholeUiAmbientTest.java',
      'multiview-stability-fill-2103229/tests/Cobra2103229MultiViewStabilityFillTest.java',
      'cobra-pro-refinement-2103322/CobraProRefinementTest.java',
      'cobra-pro-refinement-2103322/CobraProControlsRefinementTest.java',
      'cobra-pro-refinement-2103322/CobraProPausedReturnTest.java',
      'cobra-sports-live-2103323/CobraSportsLiveFeedTest.java',
      'chooser-close-owner-2103324/KodiProcessStatusTest.java',
      'chooser-close-owner-2103324/CloseProgress316Test.java',
      'chooser-close-owner-2103324/CobraCloseIsolation316Test.java',
      'chooser-close-owner-2103324/AndroidTaskRemoval315Test.java',
      'chooser-close-owner-2103324/KodiOwnerLeaseTest.java',
      'cooperative-close-2103326/CooperativeClose326Test.java',
      'jobmanager-close-2103327/ShutdownDiagnostics327ExportTest.java']
    for name in paths:shutil.copy2(HERE.parent/name,tests/Path(name).name)
    resource=build/'xbmc/src/test/resources';resource.mkdir(parents=True)
    shutil.copy2(HERE.parent/'cobra-pro-season-2103317/schedule-fixtures.json',resource/'schedule-fixtures.json')
    p=tests/'ProTeams312Test.java'
    p.write_text(p.read_text().replace(
        '@Test public void proDrawerSportsOpensSameHubAndSelectionSurvivesRerender()',
        '/* Sports drawer destination intentionally removed in 317; Pro tab is tested instead. */ public void proDrawerSportsOpensSameHubAndSelectionSurvivesRerender()'))
    # Only expected engine identity changes in this inherited exporter test.
    p=tests/'ShutdownDiagnostics327ExportTest.java';t=p.read_text()
    require(t.count(native.OLD_TAG)==1,'Exporter test identity drift')
    p.write_text(t.replace(native.OLD_TAG,native.NEW_TAG,1))
    with (build/'xbmc/build.gradle').open('a') as gradle:
        gradle.write('''
android { testOptions { unitTests.includeAndroidResources = true; unitTests.all { maxHeapSize = "3g"; systemProperty "cobra.evidence", rootProject.file("../evidence3339/screenshots").absolutePath; testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" } } } }
configurations { preservationTools }
dependencies { testImplementation 'junit:junit:4.13.2'; testImplementation 'org.robolectric:robolectric:4.14.1'; preservationTools 'org.smali:baksmali:2.5.2' }
tasks.register('exportPreservationTools') { doLast { rootProject.file('preservation-classpath.txt').text = configurations.preservationTools.asPath } }
''')

def prepare(base,build,out,engine):
    verify_parent(base)
    lib,info=bound_native(engine,out)
    with tarfile.open(PARENT/'repaired-shell-source.tar.gz') as archive:
        archive.extractall(out/'extracted',filter='data')
    source=out/'android-source';shutil.copytree(out/'extracted/shell-kodi',source)
    metadata=json.loads((HERE.parent/'cobra-pro-season-2103317/parent-metadata.json').read_text())
    for name,text in metadata.items():
        dest=source/name
        if not dest.exists():dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)
    update_identity(source,out,info['native_sha256'])
    legacy.factory.BASE_APK_SHA256=BASE
    legacy.factory.VERSION_CODE=VERSION
    legacy.factory.RELEASE=RELEASE
    legacy.factory.prepare(source.resolve(),base.resolve(),build.resolve(),out.resolve())
    stage_tests(build)
    write(out/'NATIVE-ASSOCIATION.json',info)

def assemble(base,build,out,engine):
    verify_parent(base)
    delta=json.loads((out/'SOURCE-PRESERVATION.json').read_text())
    require(native.snapshot(out/'android-source')==delta['after'],'Source changed after Android tests')
    lib,info=bound_native(engine,out)
    require(delta['native_sha256']==info['native_sha256'],'Android/native association mismatch')
    bt=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0'
    donor=build/'xbmc/build/outputs/apk/release/xbmc-release.apk'
    require(legacy.resource_ids(bt/'aapt2',base,out/'base-resources.txt')==
        legacy.resource_ids(bt/'aapt2',donor,out/'donor-resources.txt'),'Resource IDs changed')
    unsigned=out/'candidate-unsigned.apk';legacy.merge(base,donor,lib,unsigned)
    legacy.verify_manifest_pair(run(bt/'aapt','dump','xmltree',base,'AndroidManifest.xml',output=out/'base-manifest.txt'),
        run(bt/'aapt','dump','xmltree',unsigned,'AndroidManifest.xml',output=out/'candidate-manifest.txt'))
    final=out/'Infinity-2103339-Kodi22-Selective-Shutdown-RC1.apk'
    run('bash',ROOT/'scripts/sign-infinity71.sh',unsigned,final)
    cert=run(bt/'apksigner','verify','--verbose','--print-certs',final,output=out/'signing-verification.txt')
    require(CERT in cert.lower(),'Permanent signing identity changed')
    badging=run(bt/'aapt','dump','badging',final,output=out/'badging.txt')
    require(f"package: name='com.projectinfinity.kodi' versionCode='{VERSION}' versionName='{RELEASE}'" in badging,
        'Wrong APK package/version')
    require('application-debuggable' not in badging,'Release became debuggable')
    recording=legacy.dex_equivalence.verify(base,final,build,out,legacy.DEX,require)
    allowed=re.compile(r'com/projectinfinity/kodi/(?:InfinityHealthExport|InfinityExitDiagnostics|BuildConfig)(?:\$[^/]*)?\.smali$|com/projectinfinity/kodi/InfinityCobraRecordingService(?:\$\$ExternalSyntheticLambda\d+)?\.smali$')
    import bridge_preservation
    legacy.parent.ALLOWED_DEX=allowed;bridge_preservation.ALLOWED=allowed
    dex=legacy.parent.compare_dex(base,final,build,out)
    require(dex['all_other_classes_behavior_identical'] is True and dex['api_bridge_renumbering_verified'] is True,
        'DEX preservation failed')
    write(out/'DEX-PRESERVATION.json',dict(dex,recording=recording))
    suites=[]
    for path in sorted((build/'xbmc/build/test-results/testReleaseUnitTest').glob('TEST-*.xml')):
        a=ET.parse(path).getroot().attrib
        suites.append(dict(suite=a['name'],**{k:int(a.get(k,0)) for k in ('tests','failures','errors','skipped')}))
    expected=legacy.EXPECTED_SUITES
    require({s['suite'] for s in suites}=={'com.projectinfinity.kodi.'+n for n in expected},'Missing inherited suites')
    require(all(s['tests']>=expected[s['suite'].rsplit('.',1)[-1]] and s['failures']==s['errors']==s['skipped']==0 for s in suites),
        'Tests failed, reduced or skipped')
    payload=legacy.verify_payload(base,final,lib)
    report=dict(candidate=VERSION,version_name=RELEASE,apk_parent=2103327,locked_rollback=2103327,
        base_apk_sha256=BASE,apk_sha256=native.file_digest(final),base_source_commit=native.BASE_COMMIT,
        base_validation_run=37687616440,source_commit=os.environ['GITHUB_SHA'],validation_run=os.environ['GITHUB_RUN_ID'],
        signer_certificate_sha256=CERT,skin_parent='1.0.5.201',skin_changed=False,data_reset=False,
        native_recompiled=True,upstream_commit=native.UPSTREAM,player_guard_forwardport=True,
        scanner_order_changed=False,python_runtime_changed=False,new_saving_system=False,
        shutdown_hang_resolved=False,physical_device_verified=False,locked=False,
        android_source_delta=delta['changed'],test_suites=suites,test_total=sum(s['tests'] for s in suites),
        **info,**payload)
    write(out/'APK-VERIFICATION.json',report)
    with tarfile.open(out/'repaired-shell-source.tar.gz','w:gz') as archive:
        archive.add(out/'android-source',arcname='shell-kodi')
    unsigned.unlink()
    print('PASS: permanently signed selective upstream TEST candidate; payload preserved; NOT locked or device accepted')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('prepare','package'))
    for n in ('base','build','out','engine'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    (prepare if a.mode=='prepare' else assemble)(a.base,a.build,a.out,a.engine)
