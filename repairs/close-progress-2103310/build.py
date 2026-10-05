#!/usr/bin/env python3
"""Compile the declared Android presentation delta and retain the complete 3309 payload."""
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
from apply import SOURCE_MAP,PREIMAGES,manifest

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE.parent/'mobile-regressions-2103304'))
from packaging_checks import sha,require,run,resource_ids,dex_contract,DEX,SIGNATURE,verify_manifest_pair
spec=importlib.util.spec_from_file_location('factory304',HERE.parent/'mobile-regressions-2103304/package_candidate.py')
factory=importlib.util.module_from_spec(spec);spec.loader.exec_module(factory)
VERSION=2103310;RELEASE='1.0.9-Infinity-Close-Progress-RC1'
BASE_COMMIT='995c893facfe8a09484627ca24cc8db6e962bd05'
BASE_SHA='8061316733b660d6fa4107f56b4c5dc46c4d7cff810c670a0f979dc58e0ad072'
NATIVE_SHA='b4b2630e37abd56a6e522ca633649a65b255b44bd6b39bcb9f8b84866b822aa6'

def guard(source,base,out,base_proof):
    proof=json.loads(base_proof.read_text())
    require(proof['candidate']==2103309 and proof['source_commit']==BASE_COMMIT,'Wrong base build proof')
    require(proof['native_recompiled'] is False and proof['native_sha256']==NATIVE_SHA,'Base native association differs')
    require(sha(base.read_bytes())==proof['apk_sha256']==BASE_SHA,'Not exact 2103309 APK')
    receipt=json.loads((out/'SOURCE-PRESERVATION.json').read_text());before=receipt['before']
    require(sha(json.dumps(before,sort_keys=True,separators=(',',':')).encode())==SOURCE_MAP,'Wrong full Android parent')
    require(manifest(source)==receipt['after'],'Source changed after delta validation')
    require(before.keys()==receipt['after'].keys() and {n for n in before if before[n]!=receipt['after'][n]}==set(PREIMAGES),'Undeclared source changes')
    with zipfile.ZipFile(base) as z:
        require(sha(z.read('lib/arm64-v8a/libkodi.so'))==proof['native_sha256'],'Native base does not match build proof')
    return proof

def prepare(source,base,build,out,proof):
    factory.BASE_APK_SHA256=proof['apk_sha256'];factory.VERSION_CODE=VERSION;factory.RELEASE=RELEASE
    factory.prepare(source,base,build,out)
    tests=build/'xbmc/src/test/java/com/projectinfinity/kodi';tests.mkdir(parents=True)
    shutil.copy2(HERE/'CloseProgressRingTest.java',tests/'CloseProgressRingTest.java')
    with (build/'xbmc/build.gradle').open('a') as f:
        f.write('''
android { testOptions { unitTests.includeAndroidResources = true; unitTests.all { maxHeapSize = "3g"; systemProperty "ring.evidence", "'''+str(out/'screenshots')+'''"; testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" } } } }
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
    allowed=re.compile(r'com/projectinfinity/kodi/(?:InfinityGlassChooser)(?:\$[^/]*)?\.smali$')
    changed=sorted(n for n in old.keys()|new.keys() if old.get(n)!=new.get(n))
    unexpected=[n for n in changed if not allowed.fullmatch(n) and n!='com/projectinfinity/kodi/BuildConfig.smali']
    require(not unexpected,'DEX behavior changed outside declared owners: '+repr(unexpected))
    report={'changed_classes':changed,'unchanged_classes':len(old.keys()&new.keys())-sum(n in old and n in new for n in changed),
        'cobra_classes_unchanged':True,'all_other_dex_classes_unchanged':True}
    (out/'DEX-PRESERVATION.json').write_text(json.dumps(report,indent=2)+'\n')
    # Keep the small manifest, not tens of thousands of redundant disassembled files.
    for name in ['dex-base','dex-donor','smali-base','smali-donor']:shutil.rmtree(out/name)
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','package'])
    for name in ['source','base','base-proof','build','out']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();source,base,build,out=[x.resolve() for x in [a.source,a.base,a.build,a.out]];out.mkdir(parents=True,exist_ok=True)
    proof=guard(source,base,out,a.base_proof)
    if a.mode=='prepare':prepare(source,base,build,out,proof);return
    bt=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0';donor=build/'xbmc/build/outputs/apk/release/xbmc-release.apk'
    require(resource_ids(bt/'aapt2',base,out/'base-resources.txt')==resource_ids(bt/'aapt2',donor,out/'compiled-resources.txt'),'Compiled resource IDs changed')
    suites=list((build/'xbmc/build/test-results/testReleaseUnitTest').glob('TEST-*.xml'));require(len(suites)==1,'Missing ring test suite')
    test=E.parse(suites[0]).getroot();require(test.get('name')=='com.projectinfinity.kodi.CloseProgressRingTest' and int(test.get('tests'))==10,'Missing required tests')
    require(all(int(test.get(k,'0'))==0 for k in ['failures','errors','skipped']),'Failed or skipped tests')
    bytecode=compare_dex(base,donor,build,out)
    unsigned=out/'Infinity-3310-unsigned.apk';merge(base,donor,unsigned)
    verify_manifest_pair(run(bt/'aapt','dump','xmltree',base,'AndroidManifest.xml',output=out/'base-manifest.txt'),run(bt/'aapt','dump','xmltree',unsigned,'AndroidManifest.xml',output=out/'manifest.txt'))
    for name in ['INFINITY_KEYSTORE_B64','INFINITY_STORE_PASSWORD','INFINITY_KEY_PASSWORD','INFINITY_KEY_ALIAS']:require(bool(os.environ.get(name)),'Missing permanent signing configuration: '+name)
    final=out/'Infinity-2103310-Close-Progress-RC1.apk';run('bash',ROOT/'scripts/sign-infinity71.sh',unsigned,final)
    cert=run(bt/'apksigner','verify','--verbose','--print-certs',final,output=out/'signing-verification.txt');require(factory.CERT in cert.lower(),'Permanent signer changed')
    badging=run(bt/'aapt','dump','badging',final,output=out/'badging.txt');require(f"package: name='com.projectinfinity.kodi' versionCode='{VERSION}' versionName='{RELEASE}'" in badging,'Wrong identity')
    kept=verify_bytes(base,final);unsigned.unlink()
    report={'candidate':VERSION,'apk_parent':2103309,'base_sha256':proof['apk_sha256'],'apk_sha256':sha(final.read_bytes()),
        'source_commit':os.environ['GITHUB_SHA'],'skin_parent':'1.0.5.201','skin_changed':False,'cobra_source_changed':False,
        'native_recompiled':False,'native_sha256':proof['native_sha256'],'permanent_signer':factory.CERT,
        'tests_passed':10,'physical_device_verified':False,'locked':False,**kept,**bytecode}
    (out/'APK-VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: filling close ring candidate signed; complete 3309 native/assets/resources and all other DEX classes preserved.')

if __name__=='__main__':main()
