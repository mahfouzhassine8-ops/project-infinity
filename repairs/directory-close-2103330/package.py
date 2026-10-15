#!/usr/bin/env python3
"""Package 3330 on accepted 3327; reuse parser, remove the extra UI task entirely."""
import argparse,ast,importlib.util,json,os,re,shutil,sys,tarfile,xml.etree.ElementTree as ET,zipfile
from pathlib import Path
import android_repair
import make_tests
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
for directory in ('mobile-regressions-2103304','chooser-close-owner-2103324','jobmanager-close-2103327'):
    sys.path.insert(0,str(HERE.parent/directory))
from packaging_checks import require,sha,run,resource_ids,verify_manifest_pair
spec=importlib.util.spec_from_file_location('base327',HERE.parent/'jobmanager-close-2103327/package.py')
base327=importlib.util.module_from_spec(spec);spec.loader.exec_module(base327)
BASE='02449fea9c76ad6a370f2ca26a88fdee3a681f83bdc3efa73f8e213f22d4c4d5'
BASE_NATIVE=android_repair.OLD_NATIVE
BASE_COMMIT='2bb8f12f700ee69fe5d86629e6639bc0b1a0b79e'
VERSION=2103330;RELEASE='1.0.9-Directory-Close-RC1'
base327.BASE_NATIVE=BASE_NATIVE
EXPECTED=dict(base327.EXPECTED_SUITES,ClosingInfinity328Test=2,LiveClosing330Test=24)
EXPECTED['ShutdownDiagnostics330ExportTest']=EXPECTED.pop('ShutdownDiagnostics327ExportTest')

def parent(base):
    require(sha(base.read_bytes())==BASE,'Wrong accepted 3327 APK')
    r=json.loads((ROOT/'parent3327/APK-VERIFICATION.json').read_text())
    require(r['candidate']==2103327 and r['source_commit']==BASE_COMMIT and r['validation_run']=='37687616440','Wrong 3327 source/run')
    require(r['apk_sha256']==BASE and r['native_sha256']==BASE_NATIVE and r['signer_certificate_sha256']==base327.parent.parent.CERT,'Wrong parent content/signer')
    with zipfile.ZipFile(base) as z:require(sha(z.read(base327.ENGINE))==BASE_NATIVE,'Wrong parent engine')
    return r

def native(engine,out):
    p=json.loads((engine/'ENGINE-PROOF.json').read_text())
    require(p['candidate']==VERSION and p['apk_parent']==2103327 and p['source_commit']==os.environ['INFINITY_NATIVE_SOURCE_COMMIT'],'Wrong 3330 native run/source')
    require(p['result_wait_cancellation'] and p['final_worker_join_preserved'] and p['script_owner_cleanup_preserved'] and not p['worker_force_stop_added'],'Wrong native behavior proof')
    receipt=json.loads((engine/'source-manifest.json').read_text());delta=json.loads((HERE/'native-delta.json').read_text())
    require(sha(json.dumps(receipt['before'],sort_keys=True,separators=(',',':')).encode())==delta['parent_map'],'Wrong complete native parent map')
    changed={n for n in receipt['before'].keys()|receipt['after'].keys() if receipt['before'].get(n)!=receipt['after'].get(n)}
    require(changed==set(delta['after'])==set(receipt['changed']) and receipt['before'].keys()==receipt['after'].keys(),'Unexpected native file delta')
    require({n:receipt['after'][n] for n in changed}==delta['after'],'Native postimages differ from tested delta')
    raw=engine/'libkodi.so';require(sha(raw.read_bytes())==p['native_sha256'],'Raw native mismatch')
    require(b'infinity-shutdown-2103330-v1' in raw.read_bytes(),'Missing native identity')
    identity=base327.factory.elf_identity(raw,out/'unstripped-elf-identity.txt')
    final=out/'libkodi.so';shutil.copy2(raw,final)
    strip=Path(os.environ['ANDROID_HOME'])/'ndk'/os.environ.get('NDK_VER','21.4.7075529')/'toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip'
    run(strip,'--strip-unneeded',final)
    packaged=base327.factory.elf_identity(final,out/'packaged-elf-identity.txt')
    require(identity[0]==packaged[0] and (identity[0]!='build-id' or identity==packaged),'Native ELF identity changed')
    for f in ('ENGINE-PROOF.json','source-manifest.json'):
        shutil.copy2(engine/f,out/('native-source-manifest.json' if f=='source-manifest.json' else f))
    return final

def prepare(base,build,out,engine):
    parent(base);lib=native(engine,out)
    with tarfile.open(ROOT/'parent3327/repaired-shell-source.tar.gz') as t:t.extractall(out/'parent-extracted',filter='data')
    source=out/'android-source';shutil.copytree(out/'parent-extracted/shell-kodi',source)
    android_repair.apply(source,ROOT/'parent3327/SOURCE-PRESERVATION.json',out/'SOURCE-PRESERVATION.json',sha(lib.read_bytes()))
    android_repair.verify(source,out/'SOURCE-PRESERVATION.json')
    factory=base327.factory;factory.BASE_APK_SHA256=BASE;factory.VERSION_CODE=VERSION;factory.RELEASE=RELEASE
    factory.prepare(source.resolve(),base.resolve(),build.resolve(),out.resolve())
    tests=build/'xbmc/src/test/java/com/projectinfinity/kodi';tests.mkdir(parents=True)
    # Inherit the exact 327 test list, including helper classes used by suites.
    tree=ast.parse((HERE.parent/'jobmanager-close-2103327/package.py').read_text())
    function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='prepare')
    names=ast.literal_eval(next(n.value for n in ast.walk(function) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='names' for t in n.targets)))
    require(len(names)==19,'Inherited test list changed')
    for name in names:
        data=(ROOT/name).read_text();filename=Path(name).name
        if filename=='ShutdownDiagnostics327ExportTest.java':
            data=data.replace('ShutdownDiagnostics327ExportTest','ShutdownDiagnostics330ExportTest').replace('infinity-shutdown-2103327-v1','infinity-shutdown-2103330-v1')
            filename='ShutdownDiagnostics330ExportTest.java'
        (tests/filename).write_text(data)
    shutil.copy2(HERE.parent/'closing-infinity-2103328/ClosingInfinity328Test.java',tests/'ClosingInfinity328Test.java')
    (tests/'LiveClosing330Test.java').write_text(make_tests.generate(HERE.parent/'live-closing-2103329/LiveClosing329Test.java'))
    resource=build/'xbmc/src/test/resources';resource.mkdir(parents=True)
    shutil.copy2(HERE.parent/'live-closing-2103329/trace-fixtures.json',resource/'closing-trace-fixtures.json')
    shutil.copy2(HERE.parent/'cobra-pro-season-2103317/schedule-fixtures.json',resource/'schedule-fixtures.json')
    p=tests/'ProTeams312Test.java';p.write_text(p.read_text().replace('@Test public void proDrawerSportsOpensSameHubAndSelectionSurvivesRerender()',
      '/* Sports drawer destination intentionally removed in 317; Pro tab is tested instead. */ public void proDrawerSportsOpensSameHubAndSelectionSurvivesRerender()'))
    with (build/'xbmc/build.gradle').open('a') as f:f.write('''
android { testOptions { unitTests.includeAndroidResources = true; unitTests.all { maxHeapSize = "3g"; systemProperty "cobra.evidence", rootProject.file("../evidence3330/screenshots").absolutePath; testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" } } } }
configurations { preservationTools }
dependencies { testImplementation 'junit:junit:4.13.2'; testImplementation 'org.robolectric:robolectric:4.14.1'; preservationTools 'org.smali:baksmali:2.5.2' }
tasks.register('exportPreservationTools') { doLast { rootProject.file('preservation-classpath.txt').text = configurations.preservationTools.asPath } }
''')

def package(base,build,out,engine):
    parent(base);android_repair.verify(out/'android-source',out/'SOURCE-PRESERVATION.json')
    lib=native(engine,out);source=json.loads((out/'SOURCE-PRESERVATION.json').read_text())
    require(source['native_sha256']==sha(lib.read_bytes()),'Bound runtime native hash mismatch')
    bt=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0';donor=build/'xbmc/build/outputs/apk/release/xbmc-release.apk'
    require(resource_ids(bt/'aapt2',base,out/'base-resources.txt')==resource_ids(bt/'aapt2',donor,out/'donor-resources.txt'),'Resource IDs changed')
    unsigned=out/'candidate-unsigned.apk';base327.merge(base,donor,lib,unsigned)
    verify_manifest_pair(run(bt/'aapt','dump','xmltree',base,'AndroidManifest.xml',output=out/'base-manifest.txt'),run(bt/'aapt','dump','xmltree',unsigned,'AndroidManifest.xml',output=out/'candidate-manifest.txt'))
    final=out/'Infinity-2103330-Directory-Close-RC1.apk';run('bash',ROOT/'scripts/sign-infinity71.sh',unsigned,final)
    certificate=run(bt/'apksigner','verify','--verbose','--print-certs',final,output=out/'signing-verification.txt')
    require(base327.parent.parent.CERT in certificate.lower(),'Permanent signer changed')
    badging=run(bt/'aapt','dump','badging',final,output=out/'badging.txt')
    require(f"package: name='com.projectinfinity.kodi' versionCode='{VERSION}' versionName='{RELEASE}'" in badging and 'application-debuggable' not in badging,'Wrong installable identity')
    recording=base327.dex_equivalence.verify(base,final,build,out,base327.DEX,require)
    allowed=re.compile(r'com/projectinfinity/kodi/(?:InfinityCloseGuardService|InfinityCloseProgress|InfinityHealthExport|InfinityExitDiagnostics|BuildConfig)(?:\$[^/]*)?\.smali$|com/projectinfinity/kodi/InfinityCobraRecordingService(?:\$\$ExternalSyntheticLambda\d+)?\.smali$')
    import bridge_preservation
    base327.parent.ALLOWED_DEX=allowed;bridge_preservation.ALLOWED=allowed
    dex=base327.parent.compare_dex(base,final,build,out)
    require(dex['all_other_classes_behavior_identical'] and dex['api_bridge_renumbering_verified'],'Unrelated DEX change')
    dex.pop('normal_close_and_native_cleanup_behavior_preserved',None)
    dex['cobra_recording_compiler_equivalence']=recording
    suites=[]
    for f in sorted((build/'xbmc/build/test-results/testReleaseUnitTest').glob('TEST-*.xml')):
        a=ET.parse(f).getroot().attrib;suites.append(dict(suite=a['name'],**{k:int(a.get(k,0)) for k in ('tests','failures','errors','skipped')}))
    require({s['suite'] for s in suites}=={'com.projectinfinity.kodi.'+n for n in EXPECTED},'Missing regression suite')
    require(all(s['tests']>=EXPECTED[s['suite'].rsplit('.',1)[-1]] and s['failures']==s['errors']==s['skipped']==0 for s in suites),'Reduced, failed or skipped tests')
    report=dict(candidate=VERSION,version_name=RELEASE,apk_parent=2103327,locked_rollback=2103327,
      source_commit=os.environ['GITHUB_SHA'],validation_run=os.environ['GITHUB_RUN_ID'],
      base_apk_sha256=BASE,base_source_commit=BASE_COMMIT,apk_sha256=sha(final.read_bytes()),native_sha256=sha(lib.read_bytes()),
      native_source_commit=os.environ['INFINITY_NATIVE_SOURCE_COMMIT'],native_validation_run=os.environ['INFINITY_NATIVE_RUN_ID'],
      signer_certificate_sha256=base327.parent.parent.CERT,skin_parent='1.0.5.201',skin_candidate='1.0.5.204',
      native_recompiled=True,extra_closing_activity=False,chooser_source_unchanged=True,data_reset=False,
      physical_device_verified=False,locked=False,test_suites=suites,test_total=sum(s['tests'] for s in suites),
      android_source_delta=source['changed'],**base327.verify_payload(base,final,lib),**dex)
    (out/'APK-VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'DEX-PRESERVATION.json').write_text(json.dumps(dex,indent=2)+'\n')
    with tarfile.open(out/'repaired-shell-source.tar.gz','w:gz') as t:t.add(out/'android-source',arcname='shell-kodi')
    unsigned.unlink();print('PASS: 3330 signed candidate; protected payload/owners checked; Fold acceptance pending')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','package'])
    for n in ('base','build','out','engine'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);(prepare if a.mode=='prepare' else package)(a.base,a.build,a.out,a.engine)
