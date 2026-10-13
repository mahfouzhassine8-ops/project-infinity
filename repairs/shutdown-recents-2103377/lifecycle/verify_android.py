#!/usr/bin/env python3
"""Compile staged lifecycle coordination; preserve the exact previous 234 tests.

Consumes pinned green evidence. Never builds, signs, installs or locks an APK.
The native admission wrapper and full engine still need matched native validation.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile
import xml.etree.ElementTree as ET
from apply_candidate import apply_android, snapshot, digest, JAVA

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
GREEN_COMMIT = '5997df50aa00e3cb6876e1d9444e0ace923a1572'
APK_SHA = '8e8e139929592daedb63e0e41040258d655f132fd025b236de7dee1e88b47649'
PINS = {
 'tested-runtime-source.tar.gz':'ba5a7c59659e4796c16358332b4fd99dcf84a8bde5ff71b291079b9afbcff9b3',
 'tested-tests.tar.gz':'75cba87f3de1c13fec4129c4e4be30cbe81798b2247ef7f5daacf444d24a0511',
 'SOURCE-PRESERVATION.json':'8912879e0fcedc198a8b4432544c56e730ac8a64b70ca4aefaa61de2ce6b77a0',
 'ANDROID-VERIFICATION.json':'b99ba167647a6923f2042b298cb25e0e6f96d672b4285cb66ed5ddd6204aa925',
}
EXTRA = 'InfinityCloseLifecycle2103377Test'
EXTRA_COUNT = 40
FACTORY_PINS = {
    'package_candidate.py': '4e1fe39bc4bb6c4b1c7dd780a9234dfdc3f491770f9434f313417cd4a6a1a94b',
    'packaging_checks.py': '367b0ae81330fea175b0f25da9f1cd0842c3ea778b1c9f2c91bc52334344bb36',
}


def require(value, message):
    if not value: raise RuntimeError(message)


def unique(root, name):
    found = list(root.rglob(name))
    require(len(found) == 1, 'Missing/ambiguous evidence '+name)
    path=found[0]
    if name in PINS: require(digest(path)==PINS[name], 'Pinned evidence changed '+name)
    return path


def write(path, value):
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')


def extract(path, root):
    with tarfile.open(path) as stream:
        for member in stream.getmembers():
            name=Path(member.name)
            require(not name.is_absolute() and '..' not in name.parts and (member.isfile() or member.isdir()),'Unsafe archive member')
        stream.extractall(root)


def cases(root):
    result=set()
    for path in root.rglob('TEST-*.xml'):
        for case in ET.parse(path).getroot().findall('testcase'):
            key=(case.get('classname'),case.get('name'))
            require(key not in result,'Duplicate JUnit case')
            result.add(key)
    return result


def prepare(args):
    require(digest(args.apk)==APK_SHA,'Not the locked 2103376 APK')
    args.out.mkdir(parents=True,exist_ok=False)
    report=json.loads(unique(args.green,'ANDROID-VERIFICATION.json').read_text())
    require(report['source_commit']==GREEN_COMMIT,'Not the verified green source')
    require(report['locked_totals']=={'tests':207,'failures':0,'errors':0,'skipped':0},'Original 207 not preserved')
    require(report['targeted_results']=={'tests':27,'failures':0,'errors':0,'skipped':0},'Prior 27 not preserved')
    original_cases=cases(args.green)
    require(len(original_cases)==234,'Incomplete green JUnit membership')
    extract(unique(args.green,'tested-runtime-source.tar.gz'),args.out/'green-source')
    original=args.out/'green-source/source'
    proof=json.loads(unique(args.green,'SOURCE-PRESERVATION.json').read_text())['after']
    require(len(proof)==264 and snapshot(original)==proof,'Green runtime source changed')
    source=args.out/'source';shutil.copytree(original,source)
    delta=apply_android(source,proof)
    delta.update(source_commit=os.environ['GITHUB_SHA'],parent_source_commit=GREEN_COMMIT)
    write(args.out/'SOURCE-PRESERVATION.json',delta)
    for filename, expected in FACTORY_PINS.items():
        require(digest(ROOT/'repairs/mobile-regressions-2103304'/filename) == expected,
                'Approved Android factory input changed: ' + filename)
    sys.path.insert(0,str(ROOT/'repairs/mobile-regressions-2103304'))
    spec=importlib.util.spec_from_file_location('pinned_android_factory',ROOT/'repairs/mobile-regressions-2103304/package_candidate.py')
    factory=importlib.util.module_from_spec(spec);spec.loader.exec_module(factory)
    factory.BASE_APK_SHA256=APK_SHA;factory.VERSION_CODE=2103377;factory.RELEASE='1.0.9-Close-Recents-RC1'
    factory.prepare(source.resolve(),args.apk.resolve(),args.build.resolve(),args.out.resolve())
    extract(unique(args.green,'tested-tests.tar.gz'),args.build/'xbmc/src')
    tests=args.build/'xbmc/src/test'
    write(args.out/'GREEN-TEST-HASHES.json',snapshot(tests))
    write(args.out/'GREEN-CASE-NAMES.json',sorted(original_cases))
    shutil.copyfile(HERE/'tests'/(EXTRA+'.java'),tests/'java/com/projectinfinity/kodi'/(EXTRA+'.java'))
    names={key[0] for key in original_cases}|{'com.projectinfinity.kodi.'+EXTRA}
    with (args.build/'xbmc/build.gradle').open('a') as output:
        output.write('''
android { testOptions { unitTests.includeAndroidResources = true; unitTests.all {
 maxHeapSize = "3g";
 systemProperty "cobra.evidence", rootProject.file("../recents-evidence/screenshots").absolutePath;
 systemProperty "cobra.clean.evidence", rootProject.file("../recents-evidence/runtime").absolutePath;
 testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" }
} } }
dependencies { testImplementation 'junit:junit:4.13.2'; testImplementation 'org.robolectric:robolectric:4.14.1' }
tasks.withType(Test).configureEach { filter {
''')
        for name in sorted(names):output.write(" includeTestsMatching '"+name+"'\n")
        output.write('} }\n')
    print('STAGED: exact 234 previous tests, 40 added lifecycle tests, 259 unchanged runtime inputs. No APK or native-engine build.')


def review(args):
    before=json.loads((args.out/'GREEN-TEST-HASHES.json').read_text())
    now=snapshot(args.build/'xbmc/src/test')
    extra='java/com/projectinfinity/kodi/'+EXTRA+'.java'
    preserved=set(now)==set(before)|{extra} and all(now.get(k)==v for k,v in before.items())
    old_cases={tuple(case) for case in json.loads((args.out/'GREEN-CASE-NAMES.json').read_text())}
    results=args.build/'xbmc/build/test-results/testReleaseUnitTest'
    actual=cases(results);new_class='com.projectinfinity.kodi.'+EXTRA
    original_cases={case for case in actual if case[0]!=new_class}
    additional={case for case in actual if case[0]==new_class}
    suites={}
    for path in results.glob('TEST-*.xml'):
        xml=ET.parse(path).getroot();name=xml.get('name')
        require(name not in suites,'Duplicate test suite')
        suites[name]={k:int(xml.get(k,'0')) for k in ('tests','failures','errors','skipped')}
    totals={k:sum(v[k] for v in suites.values()) for k in ('tests','failures','errors','skipped')}
    delta=json.loads((args.out/'SOURCE-PRESERVATION.json').read_text())
    source=args.out/'source';runtime_same=snapshot(source)==delta['after']
    java_matches=True
    for template in (source/JAVA).rglob('*.java.in'):
        target=args.build/'xbmc/java/com/projectinfinity/kodi'/str(template.relative_to(source/JAVA)).removesuffix('.in')
        expected=template.read_text()
        for name,value in {'APP_PACKAGE':'com.projectinfinity.kodi','APP_NAME':'Kodi','APP_NAME_LC':'kodi'}.items():
            expected=expected.replace('@'+name+'@',value)
        java_matches &= target.exists() and target.read_text()==expected
    new_test_matches=digest(args.build/'xbmc/src/test'/extra)==digest(HERE/'tests'/(EXTRA+'.java'))
    no_apk=not list((args.build/'xbmc/build/outputs').rglob('*.apk'))
    status={'source_commit':os.environ['GITHUB_SHA'],'parent_source_commit':GREEN_COMMIT,
      'totals':totals,'previous_234_case_names_preserved':original_cases==old_cases,
      'previous_234_test_sources_unchanged':preserved,'new_test_matches':new_test_matches,
      'new_lifecycle_cases':len(additional),'suites':suites,'runtime_source_matches_candidate':runtime_same,
      'compiled_java_inputs_match_candidate':java_matches,'unchanged_runtime_files':delta['unchanged_runtime_files'],
      'complete_native_engine_compiled':False,'native_admission_wrapper_mandatory':True,
      'shutdown_backend_fixed':False,'physical_device_verified':False,'apk_packaged_or_signed':False}
    write(args.out/'ANDROID-VERIFICATION.json',status)
    require(preserved and original_cases==old_cases and runtime_same and java_matches and new_test_matches,'Preservation gate failed')
    require(len(additional)==EXTRA_COUNT,'Missing added lifecycle case')
    require(totals=={'tests':234+EXTRA_COUNT,'failures':0,'errors':0,'skipped':0},'Android test gate failed')
    require(no_apk,'Unexpected APK output in verification-only job')
    print('PASS: 234 unchanged previous regressions plus 40 new lifecycle tests. Host Android tests only; no full native/device/shutdown claim.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=['prepare','review'])
    for name in ('green','apk','build','out'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();globals()[args.mode](args)
