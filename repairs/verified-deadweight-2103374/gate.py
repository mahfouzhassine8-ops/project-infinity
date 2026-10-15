#!/usr/bin/env python3
"""Isolated Category A cleanup from exact locked 2103373, retaining its native APK."""
import argparse
import difflib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'repairs/cobra-clean-restart'))
import stage, package_test, delivery_gate
sys.path.insert(0,str(HERE))
import dex_guard
spec=importlib.util.spec_from_file_location('verified_removal',HERE/'apply.py')
removal=importlib.util.module_from_spec(spec);spec.loader.exec_module(removal)
RULES=removal.RULES
VERSION=2103374
RELEASE='1.0.9-Verified-Deadweight-RC1'
NAME='Cobra-2103374-Verified-Deadweight-RC1.apk'
EXTRA='CobraVerifiedDeadweightTest'

def require(ok,message):
    if not ok:raise RuntimeError(message)
def write(p,value):p.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def one(root,name):
    paths=list(root.rglob(name));require(len(paths)==1,'Missing/ambiguous '+name);return paths[0]
def extract(archive,dest):
    with tarfile.open(archive) as t:
        for m in t.getmembers():
            p=Path(m.name);require(not p.is_absolute() and '..' not in p.parts and (m.isfile() or m.isdir()),'Unsafe archive entry')
        t.extractall(dest)

def member_review(args):
    before=args.out/'parent-source/source';after=args.out/'source'
    a=stage.snapshot(before);b=stage.snapshot(after)
    require(len(a)==264 and a.keys()==b.keys(),'Source membership changed')
    require([k for k in a if a[k]!=b[k]]==[RULES['source_path']],'Unapproved runtime file change')
    require(a[RULES['source_path']]==RULES['before_sha256'] and b[RULES['source_path']]==RULES['after_sha256'],'Exact source hashes differ')
    maps=[]
    for label,root in [('before',before),('after',after)]:
        p=args.out/('MEMBERS-'+label+'.json')
        subprocess.run(['java',str(ROOT/'repairs/cobra-clean-restart/MemberInventory.java'),str(root/RULES['source_path']),str(p)],check=True)
        maps.append(json.loads(p.read_text()))
    old,new=maps
    require({k:old[k] for k in old.keys()-new.keys()}==RULES['removed_members'],'Wrong removed member set')
    require(new.keys()<=old.keys() and all(old[k]==v for k,v in new.items()),'Surviving source member changed')
    result={'source_commit':os.environ.get('GITHUB_SHA','local'),'parent_commit':RULES['parent_commit'],
            'removed_members':RULES['removed_members'],'surviving_named_members_unchanged':len(new),
            'other_source_files_unchanged':263,'physical_acceptance':False}
    write(args.out/'CHANGED-MEMBERS.json',result)
    write(args.out/'SOURCE-PRESERVATION.json',{'before':a,'after':b,'changed':[RULES['source_path']],'source_commit':os.environ.get('GITHUB_SHA','local')})
    return result

def prepare(args):
    require(sha(args.base)==RULES['parent_apk_sha256'],'Wrong locked APK input')
    args.out.mkdir(parents=True,exist_ok=True)
    archive=one(args.parent,'runtime-source.tar.gz');tests=one(args.parent,'test-source.tar.gz')
    require(sha(archive)==RULES['runtime_archive_sha256'],'Wrong runtime source archive')
    require(sha(tests)==RULES['test_archive_sha256'],'Wrong preserved test archive')
    extract(archive,args.out/'parent-source')
    before=args.out/'parent-source/source'
    parent_proof=json.loads(one(args.parent,'SOURCE-PRESERVATION.json').read_text())
    require(stage.snapshot(before)==parent_proof['after'],'Parent source/evidence mismatch')
    source=args.out/'source';shutil.copytree(before,source)
    removal.apply(source)
    member_review(args)
    (args.out/'removals.patch').write_text(''.join(difflib.unified_diff(
        (before/RULES['source_path']).read_text().splitlines(True),
        (source/RULES['source_path']).read_text().splitlines(True),
        '2103373/'+RULES['source_path'],'2103374/'+RULES['source_path'])))
    sys.path.insert(0,str(ROOT/'repairs/mobile-regressions-2103304'))
    spec=importlib.util.spec_from_file_location('unchanged_android_factory',ROOT/'repairs/mobile-regressions-2103304/package_candidate.py')
    factory=importlib.util.module_from_spec(spec);spec.loader.exec_module(factory)
    factory.BASE_APK_SHA256=RULES['parent_apk_sha256'];factory.VERSION_CODE=VERSION;factory.RELEASE=RELEASE
    factory.prepare(source.resolve(),args.base.resolve(),args.build.resolve(),args.out.resolve())
    extract(tests,args.build/'xbmc/src')
    test_root=args.build/'xbmc/src/test'
    original=stage.snapshot(test_root)
    shutil.copy2(HERE/(EXTRA+'.java'),test_root/'java/com/projectinfinity/kodi'/(EXTRA+'.java'))
    saved=json.loads(one(args.parent,'RUNTIME-RESULTS.json').read_text())
    require(saved['totals']=={'tests':206,'failures':0,'errors':0,'skipped':0},'Parent test evidence changed')
    write(args.out/'SAVED-TEST-SOURCE.json',original)
    expected={k:v['tests'] for k,v in saved['suites'].items()};expected[EXTRA]=1
    write(args.out/'EXPECTED-TESTS.json',expected)
    with (args.build/'xbmc/build.gradle').open('a') as f:
        f.write('''
android { testOptions { unitTests.includeAndroidResources = true; unitTests.all {
 maxHeapSize = "3g";
 systemProperty "cobra.evidence", rootProject.file("../cleanup-evidence/screenshots").absolutePath;
 systemProperty "cobra.clean.evidence", rootProject.file("../cleanup-evidence/runtime").absolutePath;
 testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" }
} } }
configurations { preservationTools }
dependencies { testImplementation 'junit:junit:4.13.2'; testImplementation 'org.robolectric:robolectric:4.14.1'; preservationTools 'org.smali:baksmali:2.5.2' }
tasks.register('exportPreservationTools') { doLast { rootProject.file('preservation-classpath.txt').text = configurations.preservationTools.asPath } }
tasks.withType(Test).configureEach { filter {
''')
        for name in expected:f.write(" includeTestsMatching 'com.projectinfinity.kodi."+name+"'\n")
        f.write('} }\n')

def test_names(root):
    result=set()
    for p in root.rglob('TEST-*.xml'):
        for case in ET.parse(p).getroot().findall('testcase'):
            key=(case.get('classname'),case.get('name'));require(key not in result,'Duplicate JUnit case');result.add(key)
    return result

def gates(args):
    expected=json.loads((args.out/'EXPECTED-TESTS.json').read_text())
    root=args.build/'xbmc/build/test-results/testReleaseUnitTest'
    found={}
    for p in root.glob('TEST-*.xml'):
        r=ET.parse(p).getroot();name=r.get('name').rsplit('.',1)[-1]
        require(name not in found,'Duplicate suite')
        found[name]={k:int(r.get(k,0)) for k in ('tests','failures','errors','skipped')}
    totals={k:sum(v[k] for v in found.values()) for k in ('tests','failures','errors','skipped')}
    write(args.out/'RUNTIME-RESULTS.json',{'source_commit':os.environ['GITHUB_SHA'],'suites':found,'totals':totals,'physical_device_verified':False})
    require(set(found)==set(expected),'Test suite membership changed')
    require(all(found[n]['tests']==count for n,count in expected.items()),'Required test count changed')
    require(totals=={'tests':207,'failures':0,'errors':0,'skipped':0},'Tests failed/skipped; packaging prohibited')
    oldnames=test_names(args.parent);names=test_names(root)
    require(len(oldnames)==206 and oldnames<=names,'Original 206 cases missing/renamed')
    originals=json.loads((args.out/'SAVED-TEST-SOURCE.json').read_text())
    current=stage.snapshot(args.build/'xbmc/src/test')
    extra='java/com/projectinfinity/kodi/'+EXTRA+'.java'
    require(set(current)-set(originals)=={extra} and all(current.get(k)==v for k,v in originals.items()),'Saved test/fixture changed')
    write(args.out/'SAVED-TEST-PRESERVATION.json',{'original_test_names_preserved':206,'inherited_sources_unchanged':True,'new_cases':1,'failed_or_skipped_cases_waived':False})
    return totals

def review(args):
    require(sha(args.base)==RULES['parent_apk_sha256'],'Parent APK changed')
    counts=gates(args)
    proof=member_review(args)
    return proof,counts

def package(args):
    # Reuse unchanged payload/signature/resource/JNI checks. Tighten DEX comparison
    # to every class and surviving member, including the modified activity itself.
    stage.TRANSPORT=RULES['parent_apk_sha256']
    delivery_gate.VERSION=VERSION;delivery_gate.RELEASE=RELEASE
    package_test.review=review;package_test.bytecode_guard.compare=dex_guard.compare
    package_test.package(args)
    old=args.out/'Cobra-2103372-Six-Verified-RC1.apk';final=args.out/NAME;old.rename(final)
    receipt=json.loads((args.out/'DELIVERY.json').read_text())
    for key in ['approved_cobra_source','transport_source','original_185_preserved']:receipt.pop(key,None)
    receipt.update({'file':NAME,'parent_version':2103373,'parent_commit':RULES['parent_commit'],
                    'preserved_parent_test_cases':206,'removed_methods':[m['name'] for m in RULES['methods']],
                    'retired_dashboard_compiled_absence_verified':True,
                    'parent_bytes':args.base.stat().st_size,'bytes_saved':args.base.stat().st_size-final.stat().st_size,
                    'locked':False,'production_promoted':False})
    write(args.out/'DELIVERY.json',receipt)
    print('PASS signed isolated cleanup candidate:',NAME,receipt['bytes_saved'],'bytes saved')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','gates','review','package'])
    for name in ['parent','base','build','out']:p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args();globals()[args.mode](args)
