#!/usr/bin/env python3
"""Ship the 3334 message-gate repair on exact 3333, without UI or persistence changes."""
import argparse
import ast
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
import android_identity

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
for directory in ('mobile-regressions-2103304','chooser-close-owner-2103324','jobmanager-close-2103327'):
    sys.path.insert(0,str(HERE.parent/directory))
from packaging_checks import require,sha,run,resource_ids,verify_manifest_pair

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

core=load('packaging327',HERE.parent/'jobmanager-close-2103327/package.py')
make_tests=load('tests330',HERE.parent/'directory-close-2103330/make_tests.py')
BASE='fb7c5c61257647d3565a55b9760bad592e0dd0608683f2f1c0ffbec641b56448'
BASE_COMMIT='bbfbe8817cd65056dbbacf592dcb3e0de4c209ef'
BASE_RUN='37720581322'
BASE_NATIVE=android_identity.OLD_NATIVE
VERSION=2103334
RELEASE='1.0.9-Script-Exit-RC1'
FILENAME='Infinity-2103334-Script-Exit-RC1.apk'
NATIVE_COMMIT='927e7a8be98a440a53759ef976463fe824e2fb28'
NATIVE_REVIEW_COMMIT='82a8a039726e4587fcfd36b8fa8c1c07a081f984'
NATIVE_RUN='37730777127'
core.BASE_NATIVE=BASE_NATIVE
EXPECTED=dict(core.EXPECTED_SUITES,ClosingInfinity328Test=2,LiveClosing334Test=24)
EXPECTED['ShutdownDiagnostics334ExportTest']=EXPECTED.pop('ShutdownDiagnostics327ExportTest')


def verify_parent(base):
    require(sha(base.read_bytes())==BASE,'Not exact installed 3333 parent APK')
    receipt=json.loads((ROOT/'parent3333/APK-VERIFICATION.json').read_text())
    require(receipt['candidate']==2103333 and receipt['source_commit']==BASE_COMMIT and
            receipt['validation_run']==BASE_RUN and receipt['apk_sha256']==BASE,'3333 run/source/APK mismatch')
    require(receipt['native_sha256']==BASE_NATIVE and receipt['signer_certificate_sha256']==core.parent.parent.CERT,
            '3333 engine or permanent signer mismatch')
    require(receipt['native_engine_source_candidate']==2103330 and
            receipt['native_engine_source_run']=='37709784725','3330 directory repair missing from parent')
    with zipfile.ZipFile(base) as z:
        require(sha(z.read(core.ENGINE))==BASE_NATIVE and z.testzip() is None,'Invalid parent native/ZIP')
    return receipt


def verify_native(engine,out):
    require(os.environ['INFINITY_NATIVE_SOURCE_COMMIT']==NATIVE_COMMIT and
            os.environ['INFINITY_NATIVE_RUN_ID']==NATIVE_RUN,'Native workflow association changed')
    p=json.loads((engine/'ENGINE-PROOF.json').read_text())
    require(p['candidate']==VERSION and p['apk_parent']==2103333 and p['native_parent']==2103330 and
            p['source_commit']==NATIVE_COMMIT and p['parent_packaged_native_sha256']==BASE_NATIVE,
            'Wrong native candidate or parent')
    for key in ('late_message_gate_fixed','python_abort_policy_unchanged','script_finalizers_unchanged',
                'directory_repair_preserved','final_joins_preserved','timeouts_unchanged'):
        require(p[key] is True,'Missing native preservation/repair proof: '+key)
    privacy=p.get('python_locals_or_arguments_recorded')
    if privacy is None:
        require(p.get('exact_dependency_cache_run')==37724566406 and
                p.get('preservation_rule')=='all reviewed pre-existing source files byte-identical; generated build outputs ignored',
                'Fast-retry proof missing privacy provenance')
    else:
        require(privacy is False,'Native evidence unexpectedly records Python locals or arguments')
    require(p['locked'] is False,'Unexpected native lock policy')
    source=json.loads((engine/'source-manifest.json').read_text())
    delta=json.loads((HERE/'native-delta.json').read_text())
    parent_source=json.loads((ROOT/'parent3333/native-source-manifest.json').read_text())
    require(source['before']==parent_source['after'] and android_identity.digest(source['before'])==delta['parent_map'],
            'Not exact complete native source installed in 3333')
    changed={n for n in source['before'].keys()|source['after'].keys() if source['before'].get(n)!=source['after'].get(n)}
    added={'xbmc/interfaces/python/InfinityPythonExitEvidence.h'}
    require(changed==set(delta['after'])==set(source['changed']) and
            source['after'].keys()-source['before'].keys()==added and
            not source['before'].keys()-source['after'].keys(),'Unexpected native file delta')
    require({n:source['after'][n] for n in changed}==delta['after'],'Untested native postimage')
    # Evidence from the host prerequisite of the same immutable native run.
    py=json.loads((ROOT/'host3334/python/ABORT-TESTS.json').read_text())
    msg=json.loads((ROOT/'host3334/messenger/MESSENGER-TESTS.json').read_text())
    require(py['python']=='3.11.7' and py['real_interpreters'] and py['abort_change_not_shipped'] and
            py['matching_runtime_disproves_initial_hypothesis'] and len(py['tests'])==12 and
            all(t['passed'] for t in py['tests']),'Missing exact-runtime Python tests')
    require(py['evidence_helper_sha256']==sha((HERE/'InfinityPythonExitEvidence.h').read_bytes()),
            'Shipping evidence helper differs from real Python tests')
    require(msg['exact_function_bodies'] and msg['parent_orphaned_wait_reproduced'] and
            len(msg['tests'])==18 and all(t['passed'] for t in msg['tests']), 'Missing message-race tests')
    raw=engine/'libkodi.so';data=raw.read_bytes()
    require(sha(data)==p['native_sha256'],'Raw native bytes do not match build proof')
    for token in (b'infinity-shutdown-2103334-v1',b'scripts.late_message_rejected',
                  b'directory.result_wait_cancelled',b'python.exit_frame',b'thread.std_join_fallback'):
        require(token in data,'Missing required native token: '+repr(token))
    identity=core.factory.elf_identity(raw,out/'unstripped-elf-identity.txt')
    final=out/'libkodi.so';shutil.copy2(raw,final)
    strip=Path(os.environ['ANDROID_HOME'])/'ndk'/os.environ.get('NDK_VER','21.4.7075529')/'toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip'
    run(strip,'--strip-unneeded',final)
    packaged=core.factory.elf_identity(final,out/'packaged-elf-identity.txt')
    require(identity[0]==packaged[0] and (identity[0]!='build-id' or identity==packaged),
            'Native ELF identity changed during stripping')
    require(sha(final.read_bytes())!=BASE_NATIVE,'Old engine silently retained')
    shutil.copy2(engine/'ENGINE-PROOF.json',out/'ENGINE-PROOF.json')
    shutil.copy2(engine/'source-manifest.json',out/'native-source-manifest.json')
    shutil.copy2(ROOT/'host3334/python/ABORT-TESTS.json',out/'PYTHON-TESTS.json')
    shutil.copy2(ROOT/'host3334/messenger/MESSENGER-TESTS.json',out/'MESSENGER-TESTS.json')
    return final


def stage_tests(build):
    tests=build/'xbmc/src/test/java/com/projectinfinity/kodi';tests.mkdir(parents=True)
    tree=ast.parse((HERE.parent/'jobmanager-close-2103327/package.py').read_text())
    function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='prepare')
    names=ast.literal_eval(next(n.value for n in ast.walk(function) if isinstance(n,ast.Assign) and
          any(isinstance(t,ast.Name) and t.id=='names' for t in n.targets)))
    require(len(names)==19,'Inherited test-source list changed')
    for name in names:
        data=(ROOT/name).read_text();filename=Path(name).name
        if filename=='ShutdownDiagnostics327ExportTest.java':
            data=data.replace('ShutdownDiagnostics327ExportTest','ShutdownDiagnostics334ExportTest')
            data=data.replace('infinity-shutdown-2103327-v1','infinity-shutdown-2103334-v1')
            filename='ShutdownDiagnostics334ExportTest.java'
        (tests/filename).write_text(data)
    shutil.copy2(HERE.parent/'closing-infinity-2103328/ClosingInfinity328Test.java',tests/'ClosingInfinity328Test.java')
    text=make_tests.generate(HERE.parent/'live-closing-2103329/LiveClosing329Test.java')
    require(text.count('@Test')==24 and text.count('infinity-shutdown-2103330-v1')==1,
            'Original reader test suite changed')
    (tests/'LiveClosing334Test.java').write_text(text.replace('LiveClosing330Test','LiveClosing334Test')
        .replace('infinity-shutdown-2103330-v1','infinity-shutdown-2103334-v1'))
    resources=build/'xbmc/src/test/resources';resources.mkdir(parents=True)
    shutil.copy2(HERE.parent/'live-closing-2103329/trace-fixtures.json',resources/'closing-trace-fixtures.json')
    shutil.copy2(HERE.parent/'cobra-pro-season-2103317/schedule-fixtures.json',resources/'schedule-fixtures.json')
    p=tests/'ProTeams312Test.java';p.write_text(p.read_text().replace(
        '@Test public void proDrawerSportsOpensSameHubAndSelectionSurvivesRerender()',
        '/* Sports drawer destination intentionally removed in 317; Pro tab is tested instead. */ public void proDrawerSportsOpensSameHubAndSelectionSurvivesRerender()'))
    with (build/'xbmc/build.gradle').open('a') as f:f.write('''
android { testOptions { unitTests.includeAndroidResources = true; unitTests.all { maxHeapSize = "3g"; systemProperty "cobra.evidence", rootProject.file("../evidence3334/screenshots").absolutePath; testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" } } } }
configurations { preservationTools }
dependencies { testImplementation 'junit:junit:4.13.2'; testImplementation 'org.robolectric:robolectric:4.14.1'; preservationTools 'org.smali:baksmali:2.5.2' }
tasks.register('exportPreservationTools') { doLast { rootProject.file('preservation-classpath.txt').text = configurations.preservationTools.asPath } }
''')


def prepare(base,build,out,engine):
    verify_parent(base);lib=verify_native(engine,out)
    with tarfile.open(ROOT/'parent3333/repaired-shell-source.tar.gz') as t:
        t.extractall(out/'parent-extracted',filter='data')
    source=out/'android-source';shutil.copytree(out/'parent-extracted/shell-kodi',source)
    android_identity.apply(source,ROOT/'parent3333/SOURCE-PRESERVATION.json',out/'SOURCE-PRESERVATION.json',sha(lib.read_bytes()))
    android_identity.verify(source,out/'SOURCE-PRESERVATION.json')
    core.factory.BASE_APK_SHA256=BASE;core.factory.VERSION_CODE=VERSION;core.factory.RELEASE=RELEASE
    core.factory.prepare(source.resolve(),base.resolve(),build.resolve(),out.resolve())
    stage_tests(build)


def package(base,build,out,engine):
    prior=verify_parent(base)
    android_identity.verify(out/'android-source',out/'SOURCE-PRESERVATION.json')
    lib=verify_native(engine,out);source=json.loads((out/'SOURCE-PRESERVATION.json').read_text())
    require(source['native_sha256']==sha(lib.read_bytes()),'Runtime diagnostic/native binding mismatch')
    bt=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0'
    donor=build/'xbmc/build/outputs/apk/release/xbmc-release.apk'
    require(resource_ids(bt/'aapt2',base,out/'base-resources.txt')==resource_ids(bt/'aapt2',donor,out/'donor-resources.txt'),
            'Protected Android resource IDs changed')
    unsigned=out/'candidate-unsigned.apk';core.merge(base,donor,lib,unsigned)
    verify_manifest_pair(run(bt/'aapt','dump','xmltree',base,'AndroidManifest.xml',output=out/'base-manifest.txt'),
                         run(bt/'aapt','dump','xmltree',unsigned,'AndroidManifest.xml',output=out/'candidate-manifest.txt'))
    final=out/FILENAME;run('bash',ROOT/'scripts/sign-infinity71.sh',unsigned,final)
    certificate=run(bt/'apksigner','verify','--verbose','--print-certs',final,output=out/'signing-verification.txt')
    require(core.parent.parent.CERT in certificate.lower(),'Permanent install-over signer changed')
    badging=run(bt/'aapt','dump','badging',final,output=out/'badging.txt')
    require(f"package: name='com.projectinfinity.kodi' versionCode='{VERSION}' versionName='{RELEASE}'" in badging and
            'application-debuggable' not in badging,'Wrong release identity')
    recording=core.dex_equivalence.verify(base,final,build,out,core.DEX,require)
    allowed=re.compile(r'com/projectinfinity/kodi/(?:InfinityCloseProgress|InfinityHealthExport|InfinityExitDiagnostics|BuildConfig)(?:\$[^/]*)?\.smali$|com/projectinfinity/kodi/InfinityCobraRecordingService(?:\$\$ExternalSyntheticLambda\d+)?\.smali$')
    import bridge_preservation
    core.parent.ALLOWED_DEX=allowed;bridge_preservation.ALLOWED=allowed
    dex=core.parent.compare_dex(base,final,build,out)
    require(dex['all_other_classes_behavior_identical'] and dex['api_bridge_renumbering_verified'],
            'Unexpected unrelated Android behavior change')
    # That inherited diagnostic label would incorrectly claim no native delta.
    dex.pop('normal_close_and_native_cleanup_behavior_preserved',None)
    dex['cobra_recording_compiler_equivalence']=recording
    suites=[]
    for f in sorted((build/'xbmc/build/test-results/testReleaseUnitTest').glob('TEST-*.xml')):
        a=ET.parse(f).getroot().attrib
        suites.append(dict(suite=a['name'],**{k:int(a.get(k,0)) for k in ('tests','failures','errors','skipped')}))
    require({s['suite'] for s in suites}=={'com.projectinfinity.kodi.'+n for n in EXPECTED},'Required suite missing')
    require(all(s['tests']>=EXPECTED[s['suite'].rsplit('.',1)[-1]] and
                s['failures']==s['errors']==s['skipped']==0 for s in suites),'Reduced/failed/skipped regression tests')
    require(sum(s['tests'] for s in suites)>=prior['test_total'],'Regression coverage decreased from 3333')
    report=dict(candidate=VERSION,version_name=RELEASE,apk_filename=FILENAME,apk_parent=2103333,locked_rollback=2103327,
        base_apk_sha256=BASE,base_source_commit=BASE_COMMIT,base_validation_run=BASE_RUN,
        source_commit=os.environ['GITHUB_SHA'],validation_run=os.environ['GITHUB_RUN_ID'],
        apk_sha256=sha(final.read_bytes()),native_sha256=sha(lib.read_bytes()),
        native_source_commit=NATIVE_COMMIT,native_review_source_commit=NATIVE_REVIEW_COMMIT,native_validation_run=NATIVE_RUN,native_retry_from_run='37724566406',native_parent=2103330,
        signer_certificate_sha256=core.parent.parent.CERT,skin_parent='1.0.5.201',installed_skin_pairing='1.0.5.204',
        skin_changed=False,native_recompiled=True,directory_repair_preserved=True,python_abort_policy_changed=False,
        late_message_gate_fixed=True,targeted_exit_evidence=True,shutdown_timeouts_changed=False,
        android_identity_only=True,ui_changed=False,data_reset=False,automatic_process_kill_added=False,
        physical_device_verified=False,shutdown_hang_resolved=False,locked=False,
        test_suites=suites,test_total=sum(s['tests'] for s in suites),android_source_delta=source['changed'],
        **core.verify_payload(base,final,lib),**dex)
    (out/'APK-VERIFICATION.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (out/'DEX-PRESERVATION.json').write_text(json.dumps(dex,indent=2)+'\n')
    with tarfile.open(out/'repaired-shell-source.tar.gz','w:gz') as t:t.add(out/'android-source',arcname='shell-kodi')
    unsigned.unlink()
    print('PASS: signed 3334 native message-gate candidate on exact 3333; UI/data preserved; Fold acceptance pending')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['prepare','package'])
    for n in ('base','build','out','engine'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);(prepare if a.mode=='prepare' else package)(a.base,a.build,a.out,a.engine)
