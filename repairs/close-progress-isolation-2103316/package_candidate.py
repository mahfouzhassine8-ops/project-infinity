#!/usr/bin/env python3
"""Build Infinity busy arc / independent Cobra dispatch over exact locked 3312."""
import argparse,copy,hashlib,importlib.util,json,os,re,shutil,subprocess,sys,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE.parent/'mobile-regressions-2103304'))
from packaging_checks import DEX,SIGNATURE,dex_contract,require,resource_ids,run,sha,verify_manifest_pair
spec=importlib.util.spec_from_file_location('pack304',HERE.parent/'mobile-regressions-2103304/package_candidate.py')
factory=importlib.util.module_from_spec(spec);spec.loader.exec_module(factory)
BASE_SHA='6d6543dda3d54fd8b4ff12cdf79995c198a399839a29e71e1bf741789332deed'
BASE_NATIVE='b4b2630e37abd56a6e522ca633649a65b255b44bd6b39bcb9f8b84866b822aa6'
SOURCE_MAP='8c4786d60f02d67a860f923729b7556543319fe1e9311aa068571385d2b1ac42'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
VERSION=2103316; RELEASE='1.0.9-Close-Progress-Isolation-RC1'; PACKAGE='com.projectinfinity.kodi'
ENGINE='lib/arm64-v8a/libkodi.so'

def source_guard(source,proof,base):
    parent=json.loads((proof.parent/'APK-VERIFICATION.json').read_text())
    require(parent.get('candidate')==2103312 and parent.get('source_commit')=='1df07a46469040bbeee6bae34b13b4b3f8a7970d','Wrong locked 3312 proof')
    require(parent.get('apk_sha256')==BASE_SHA and parent.get('native_sha256')==BASE_NATIVE,'Wrong locked APK/native association')
    require(sha(base.read_bytes())==BASE_SHA,'Not exact locked 2103312 APK')
    expected=json.loads(proof.read_text())['after']
    require(len(expected)==254 and sha(json.dumps(expected,sort_keys=True,separators=(',',':')).encode())==SOURCE_MAP,'Wrong 3312 source map')
    actual={p.relative_to(source).as_posix():sha(p.read_bytes()) for p in source.rglob('*') if p.is_file()}
    require(actual==expected,'Android/Cobra source differs from locked 2103312')

def append_test_support(build):
    tests=build/'xbmc/src/test/java/com/projectinfinity/kodi';tests.mkdir(parents=True,exist_ok=True)
    for name in ('AndroidTaskRemoval315Test.java','KodiProcessStatusTest.java','CloseProgress316Test.java','CobraCloseIsolation316Test.java'):
        shutil.copy2(HERE/name,tests)
    with (build/'xbmc/build.gradle').open('a') as f:
        f.write("""
android { testOptions { unitTests.includeAndroidResources = true; unitTests.all { maxHeapSize = "3g"; testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" } } } }
configurations { preservationTools }
dependencies {
  testImplementation 'junit:junit:4.13.2'
  testImplementation 'org.robolectric:robolectric:4.14.1'
  preservationTools 'org.smali:baksmali:2.5.2'
}
tasks.register('exportPreservationTools') {
  doLast { rootProject.file('preservation-classpath.txt').text = configurations.preservationTools.asPath }
}
""")

def merge(base,donor,out):
    with zipfile.ZipFile(base) as a,zipfile.ZipFile(donor) as b,zipfile.ZipFile(out,'w') as z:
        require(a.testzip() is None and b.testzip() is None,'Parent or donor APK CRC failure')
        require(len(a.namelist())==len(set(a.namelist())) and len(b.namelist())==len(set(b.namelist())),'Duplicate APK entries')
        require(sha(a.read(ENGINE))==BASE_NATIVE,'Parent Kodi engine changed')
        require(not any(n.startswith(('lib/','assets/')) and not n.endswith('/') for n in b.namelist()),'Unexpected native or asset in Android donor')
        old_native,_=dex_contract(a);new_native,_=dex_contract(b)
        require(new_native==old_native,'JNI/native method contract changed')
        for info in a.infolist():
            n=info.filename
            if n=='AndroidManifest.xml' or DEX.fullmatch(n) or SIGNATURE.fullmatch(n):continue
            z.writestr(copy.copy(info),a.read(n))
        for info in b.infolist():
            if info.filename=='AndroidManifest.xml' or DEX.fullmatch(info.filename):z.writestr(copy.copy(info),b.read(info.filename))

def verify_payload(base,candidate):
    with zipfile.ZipFile(base) as a,zipfile.ZipFile(candidate) as b:
        kept={n for n in a.namelist() if n!='AndroidManifest.xml' and not DEX.fullmatch(n) and not SIGNATURE.fullmatch(n)}
        expected=kept|{'AndroidManifest.xml'}|{n for n in b.namelist() if DEX.fullmatch(n) or SIGNATURE.fullmatch(n)}
        require(set(b.namelist())==expected and len(b.namelist())==len(expected),'Unexpected APK payload delta')
        for name in kept:require(a.read(name)==b.read(name),'Protected APK entry changed: '+name)
        require(a.read(ENGINE)==b.read(ENGINE) and sha(a.read(ENGINE))==BASE_NATIVE,'Kodi engine is not byte-identical to locked APK')
        require(dex_contract(a)[0]==dex_contract(b)[0],'JNI contract changed')
        require(b.testzip() is None,'Final APK CRC failure')
        return {'preserved_entries':len(kept),'assets_resources_and_native_engine_byte_identical':True,
                'other_native_libraries_byte_identical':sum(n.startswith('lib/') and not n.endswith('/') and n!=ENGINE for n in kept)}

def compare_dex(base,final,build,out):
    classpath=(build/'preservation-classpath.txt').read_text()
    for label,apk in [('base',base),('final',final)]:
        extracted=out/('dex-'+label);extracted.mkdir()
        target=out/('smali-'+label)
        with zipfile.ZipFile(apk) as z:
            for name in z.namelist():
                if DEX.fullmatch(name):
                    dex=extracted/name;dex.write_bytes(z.read(name))
                    subprocess.run(['java','-cp',classpath,'org.jf.baksmali.Main','disassemble',str(dex),'-o',str(target)],check=True)
    old={p.relative_to(out/'smali-base').as_posix():p.read_text() for p in (out/'smali-base').rglob('*.smali')}
    new={p.relative_to(out/'smali-final').as_posix():p.read_text() for p in (out/'smali-final').rglob('*.smali')}
    changed=sorted(n for n in old.keys()|new.keys() if old.get(n)!=new.get(n))
    allowed=re.compile(r'com/projectinfinity/kodi/(?:InfinityExitCompletion|InfinityGlassChooser|Splash|BuildConfig)(?:\$[^/]*)?\.smali$')
    unexpected=[n for n in changed if not allowed.fullmatch(n)]
    require(not unexpected,'Compiled behavior changed outside the declared close/gear/dispatch/version families: '+repr(unexpected))
    report={'changed_dex_classes':changed,'all_other_classes_bytecode_identical':True,
            'cobra_classes_unchanged':True,'unchanged_classes':len(old.keys()&new.keys())-sum(n in old and n in new for n in changed)}
    (out/'DEX-PRESERVATION.json').write_text(json.dumps(report,indent=2)+'\n')
    for label in ['dex-base','dex-final','smali-base','smali-final']:shutil.rmtree(out/label)
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['prepare','package'])
    for name in ('source','proof','base','build','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();source_guard(a.source,a.proof,a.base);a.out.mkdir(parents=True,exist_ok=True)
    bt=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0'
    factory.BASE_APK_SHA256=BASE_SHA;factory.VERSION_CODE=VERSION;factory.RELEASE=RELEASE
    if a.mode=='prepare':
        modified=a.out/'android-source';shutil.copytree(a.source,modified)
        import close_progress_isolation as android_task_close
        receipt=a.out/'ANDROID-SOURCE-DELTA.json'
        android_task_close.apply(modified,a.proof,receipt)
        android_task_close.verify(modified,receipt)
        factory.prepare(modified.resolve(),a.base.resolve(),a.build.resolve(),a.out.resolve())
        append_test_support(a.build);return
    import close_progress_isolation as android_task_close
    source_receipt=json.loads((a.out/'ANDROID-SOURCE-DELTA.json').read_text())
    android_task_close.verify(a.out/'android-source',a.out/'ANDROID-SOURCE-DELTA.json')
    donor=a.build/'xbmc/build/outputs/apk/release/xbmc-release.apk'
    require(resource_ids(bt/'aapt2',a.base,a.out/'base-resources.txt')==resource_ids(bt/'aapt2',donor,a.out/'donor-resources.txt'),'Android resource IDs changed')
    unsigned=a.out/f'Infinity-{VERSION}-unsigned.apk';merge(a.base,donor,unsigned)
    original_manifest=run(bt/'aapt','dump','xmltree',a.base,'AndroidManifest.xml',output=a.out/'base-manifest.txt')
    candidate_manifest=run(bt/'aapt','dump','xmltree',unsigned,'AndroidManifest.xml',output=a.out/'candidate-manifest.txt')
    verify_manifest_pair(original_manifest,candidate_manifest)
    for name in ('INFINITY_KEYSTORE_B64','INFINITY_STORE_PASSWORD','INFINITY_KEY_PASSWORD','INFINITY_KEY_ALIAS'):
        require(bool(os.environ.get(name)),'Missing permanent signing configuration: '+name)
    final=a.out/f'Infinity-{VERSION}-Close-Progress-Isolation-RC1.apk'
    run('bash',ROOT/'scripts/sign-infinity71.sh',unsigned,final)
    cert=run(bt/'apksigner','verify','--verbose','--print-certs',final,output=a.out/'signing-verification.txt')
    require(CERT in cert.lower(),'Permanent signer changed')
    badging=run(bt/'aapt','dump','badging',final,output=a.out/'badging.txt')
    require(f"package: name='{PACKAGE}' versionCode='{VERSION}' versionName='{RELEASE}'" in badging,'Wrong APK identity')
    preserved=verify_payload(a.base,final)
    dex=compare_dex(a.base,final,a.build,a.out)
    report={'candidate':VERSION,'apk_parent':2103312,'base_apk_sha256':BASE_SHA,'apk_sha256':sha(final.read_bytes()),
      'source_commit':os.environ['GITHUB_SHA'],'skin_parent':'1.0.5.201','skin_changed':False,
      'cobra_player_close_behavior_changed':False,'cobra_launch_gate_removed':True,
      'repair':'Retain tested 3315 task removal; show an Infinity-only indeterminate arc until matching native cleanup plus process exit; Cobra bypasses the Kodi close gate',
      'native_recompiled':False,'physical_device_verified':False,'locked':False,'data_reset':False,
      'android_source_delta':source_receipt['changed'],**preserved,**dex}
    (a.out/'APK-VERIFICATION.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (a.out/'DEVICE-TEST.txt').write_text((HERE/'DEVICE-TEST.txt').read_text())
    unsigned.unlink()
    print('PASS: signed close-progress/isolation candidate; locked 2103312 engine, Cobra player/close bytecode, resources and assets preserved; not device accepted or locked')

if __name__=='__main__':main()
