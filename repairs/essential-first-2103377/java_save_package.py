#!/usr/bin/env python3
"""Matched Java producer/Close verification over the preserved Android donor.

Reuses the locked APK factory; every non-shutdown producer edit is an audited
source-range adapter. The exact native build is reused without recompiling it.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
NATIVE='a543811a0b3b54ad6a0b1cdd2940a5e7d33aba83'
PARSER_SHA='3e3e0c65d57d12797dbead3df1ebb28e7583737d0cd1f2a898dba6febd50ab88'
EXTRA=('InfinityCloseNativeLease','InfinityJavaWriteBarrier','InfinityJavaPersistence')
TEST='InfinityJavaPersistence2103377Test'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):Path(path).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
def native_scope():
    subprocess.run(['git','diff','--exit-code',NATIVE,'--',
        'repairs/essential-first-2103377/runtime/xbmc',
        'repairs/essential-first-2103377/runtime/observer.py',
        'repairs/essential-first-2103377/apply_runtime.py',
        'repairs/essential-first-2103377/stage_experiment.py',
        'repairs/essential-first-2103377/InfinityEssentialScriptFence.h'],cwd=ROOT,check=True)

def instrument(root,jar,out):
    assert sha(jar)==PARSER_SHA,'Unpinned Java source parser'
    before={str(p.relative_to(root)):p.read_text() for p in root.rglob('*.java')}
    classes=out/'instrumentation-tool';classes.mkdir()
    subprocess.run(['java','com.sun.tools.javac.Main','-cp',str(jar),'-d',str(classes),str(HERE/'InstrumentJavaWrites.java')],check=True)
    report=out/'JAVA-PRODUCER-TRANSFORMATIONS.json'
    subprocess.run(['java','-cp',str(classes)+os.pathsep+str(jar),'InstrumentJavaWrites',str(root),str(report)],check=True)
    proof=json.loads(report.read_text());edited={row['path']:row for row in proof['files']}
    assert len(edited)==len(proof['files']) and edited
    for rel,original in before.items():
        expected=original.encode('utf-16-le')
        edits=edited.get(rel,{}).get('edits',[])
        for edit in reversed(edits):
            start,end=edit['start']*2,edit['end']*2
            assert expected[start:end]==edit['before'].encode('utf-16-le'),rel
            expected=expected[:start]+edit['after'].encode('utf-16-le')+expected[end:]
        assert expected.decode('utf-16-le')==(root/rel).read_text(),rel
    assert set(before)=={str(p.relative_to(root)) for p in root.rglob('*.java')}
    proof.update(source_range_reconstruction_verified=True,
        before={rel:hashlib.sha256(text.encode()).hexdigest() for rel,text in before.items()},
        after={str(p.relative_to(root)):sha(p) for p in root.rglob('*.java')},
        parser_sha256=sha(jar),instrumenter_sha256=sha(HERE/'InstrumentJavaWrites.java'),
        added_classes=list(EXTRA[1:]),shutdown_overlays=['InfinityCheckpointProtocol','InfinityCloseGuardService','InfinityCloseNativeLease'])
    save(report,proof)
    return proof

def stage_tests(args):
    archive=args.green/'tested-tests.tar.gz'
    assert sha(archive)=='75cba87f3de1c13fec4129c4e4be30cbe81798b2247ef7f5daacf444d24a0511'
    with tarfile.open(archive) as stream:
        for item in stream.getmembers():
            path=Path(item.name);assert not path.is_absolute() and '..' not in path.parts and (item.isfile() or item.isdir())
        stream.extractall(args.gradle_dir/'xbmc/src')
    tests=args.gradle_dir/'xbmc/src/test'
    expected=json.loads((args.source.parent/'GREEN-TEST-HASHES.json').read_text())
    assert {str(p.relative_to(tests)):sha(p) for p in tests.rglob('*') if p.is_file()}==expected
    extra=ROOT/'repairs/shutdown-recents-2103377/lifecycle/tests/InfinityCloseLifecycle2103377Test.java'
    subprocess.run(['git','diff','--exit-code','5a1a427cb5bdcc248b0e2a7887f9d6682ca53877','--',str(extra.relative_to(ROOT))],cwd=ROOT,check=True)
    shutil.copyfile(extra,tests/'java/com/projectinfinity/kodi'/extra.name)
    expected['java/com/projectinfinity/kodi/'+extra.name]=sha(extra)
    shutil.copyfile(HERE/'tests'/(TEST+'.java'),tests/'java/com/projectinfinity/kodi'/(TEST+'.java'))
    names=set(json.loads((args.source.parent/'ANDROID-VERIFICATION.json').read_text())['suites'])
    names.add('com.projectinfinity.kodi.'+TEST)
    save(args.out/'JAVA-UNCHANGED-TEST-SOURCES.json',expected)
    save(args.out/'JAVA-EXPECTED-SUITES.json',sorted(names))
    with (args.gradle_dir/'xbmc/build.gradle').open('a') as f:
        f.write('''
android { testOptions { unitTests.includeAndroidResources = true; unitTests.all {
 maxHeapSize = "3g";
 systemProperty "cobra.evidence", rootProject.file("../android-donor-evidence/screenshots").absolutePath;
 systemProperty "cobra.clean.evidence", rootProject.file("../android-donor-evidence/runtime").absolutePath;
 testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" }
} } }
dependencies { testImplementation 'junit:junit:4.13.2'; testImplementation 'org.robolectric:robolectric:4.14.1' }
tasks.withType(Test).configureEach { filter {
''')
        for name in sorted(names):f.write("includeTestsMatching '"+name+"'\n")
        f.write('} }\n')

def verify_tests(args):
    expected=json.loads((args.android/'JAVA-UNCHANGED-TEST-SOURCES.json').read_text())
    testroot=args.gradle_dir/'xbmc/src/test'
    for rel,digest in expected.items():assert sha(testroot/rel)==digest,rel
    suites={}
    for path in (args.gradle_dir/'xbmc/build/test-results/testReleaseUnitTest').glob('TEST-*.xml'):
        xml=ET.parse(path).getroot();name=xml.get('name');assert name not in suites
        suites[name]={key:int(xml.get(key,'0')) for key in ('tests','failures','errors','skipped')}
    assert set(suites)==set(json.loads((args.android/'JAVA-EXPECTED-SUITES.json').read_text())),suites
    original={k:v for k,v in suites.items() if k!='com.projectinfinity.kodi.'+TEST}
    totals={key:sum(row[key] for row in original.values()) for key in ('tests','failures','errors','skipped')}
    assert totals==dict(tests=274,failures=0,errors=0,skipped=0),totals
    new=suites['com.projectinfinity.kodi.'+TEST]
    assert new['tests']>=12 and not any(new[k] for k in ('failures','errors','skipped')),new
    save(args.out/'JAVA-REGRESSION-VERIFICATION.json',dict(original_274=totals,new_save_cases=new,suites=suites,
        original_test_sources_unchanged=True,physical_fold_verified=False))

def verify_sources(args):
    proof=json.loads((args.android/'JAVA-PRODUCER-TRANSFORMATIONS.json').read_text())
    root=args.gradle_dir/'xbmc/java'
    assert proof['source_range_reconstruction_verified'] and proof['instrumenter_sha256']==sha(HERE/'InstrumentJavaWrites.java')
    assert proof['after']=={str(p.relative_to(root)):sha(p) for p in root.rglob('*.java')},'Compiled source differs from audited transforms'
    return proof

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=('java','verify-java','package'))
    for name in ('parent','source','gradle-dir','donor','native','android','out','parser','green'):
        p.add_argument('--'+name,type=Path,required=name in ('parent','gradle-dir','out'))
    args=p.parse_args();native_scope()
    factory=module('java_save_signed_factory',HERE/'package_signed_fold_test.py')
    factory.PINNED_NATIVE_COMMIT=NATIVE;factory.NEW_NAME='1.0.9-Essential-First-TEST2-RC01'
    if args.mode=='java':
        factory.prepared_java(args)
        root=args.gradle_dir/'xbmc/java'
        for name in EXTRA:
            src=HERE/'runtime/android/tools/android/packaging/xbmc/src'/(name+'.java.in')
            (root/'com/projectinfinity/kodi'/(name+'.java')).write_text(src.read_text().replace('@APP_PACKAGE@','com.projectinfinity.kodi'))
        proof=instrument(root,args.parser,args.out)
        donor=args.out/'ANDROID-DONOR-SOURCE.json';row=json.loads(donor.read_text())
        row.update(java_source_changes_count=len(proof['files'])+5,other_kodi_sources_unchanged=False,
                   producer_source_adapters_verified=True,java_save_proof='JAVA-PRODUCER-TRANSFORMATIONS.json')
        save(donor,row);stage_tests(args)
        with (args.gradle_dir/'xbmc/build.gradle').open('a') as f:
            f.write("\nconfigurations { preservationTools }\ndependencies { preservationTools 'org.smali:baksmali:2.5.2' }\ntasks.register('exportPreservationTools') { doLast { rootProject.file('preservation-classpath.txt').text = configurations.preservationTools.asPath } }\n")
    else:
        assert args.android;proof=verify_sources(args);args.out.mkdir(exist_ok=True)
        verify_tests(args)
        guard=module('java_save_bytecode_guard',ROOT/'repairs/cobra-clean-restart/bytecode_guard.py')
        allowed={'com/projectinfinity/kodi/'+name for name in proof['shutdown_overlays']+proof['added_classes']}
        allowed.update(row['path'].removesuffix('.java') for row in proof['files'])
        guard.ALLOWED=re.compile(r'(?:'+ '|'.join(re.escape(n) for n in sorted(allowed))+r')(?:\$[^/]*)?\.smali$')
        normalize=guard.normalize;guard.normalize=lambda text:normalize(re.sub(r'(?m)^\s*\.line \d+\s*$','',text))
        guard.compare(args.parent,args.donor,(args.gradle_dir/'preservation-classpath.txt').read_text(),args.out)
        if args.mode=='verify-java':return
        factory.signed_package(args)
        old=args.out/'Infinity-2103377-Essential-First-Signed-Fold-TEST1.apk'
        final=args.out/'Infinity-2103377-Essential-First-Internal-Probe.apk';old.rename(final)
        receipt=args.out/'ESSENTIAL-FIRST-SIGNED-TEST-PRESERVATION.json';row=json.loads(receipt.read_text())
        row.update(status='INTERNAL JAVA/NATIVE SHUTDOWN PROBE; NOT LOCKED',file=final.name,
                   java_regressions_verified=True,java_producer_adapters_verified=True,apk_deliverable=False)
        row.pop('known_fail_closed_native_encoder_route',None);row.pop('unverified_other_native_descriptor_aliases',None)
        save(receipt,row);(args.out/'SHA256SUMS').write_text(row['apk_sha256']+'  '+final.name+'\n')

if __name__=='__main__':main()
