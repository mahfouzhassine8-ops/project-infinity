#!/usr/bin/env python3
import argparse,hashlib,importlib.util,json,os,re,shutil,subprocess,sys,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE.parent/'mobile-regressions-2103304'))
from packaging_checks import require,sha,run,resource_ids,verify_manifest_pair
spec=importlib.util.spec_from_file_location('parent316',HERE.parent/'close-progress-isolation-2103316/package_candidate.py');parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)
BASE='576b60dfd63cd41b8b901db2424a34cc422ba1b991641336a6e00d9c9035ce40';VERSION=2103320;RELEASE='1.0.9-Cobra-Pro-Carousel-RC1'
parent.BASE_SHA=BASE
def snapshot(root):return {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in root.rglob('*') if p.is_file()}
def prepare(base,build,out):
    require(sha(base.read_bytes())==BASE,'Wrong 2103319 working APK')
    proof=Path('parent3319/evidence3319/SOURCE-PRESERVATION.json')
    require(proof.exists(),'Missing working 319 source receipt')
    expected=json.loads(proof.read_text())['after']
    require(len(expected)==254 and sha(json.dumps(expected,sort_keys=True,separators=(',',':')).encode())=='f6dacc77367ed42bd9afa533e4feccc611d2933c1622664f4b286604f21649c1','Wrong working 319 source map')
    source=proof.parent/'android-source'
    metadata=json.loads((HERE.parent/'cobra-pro-season-2103317/parent-metadata.json').read_text())
    for name,content in metadata.items():
        target=source/name
        if not target.exists():target.parent.mkdir(parents=True,exist_ok=True);target.write_text(content)
    require(snapshot(source)==expected,'Exact working 319 source unavailable')
    parent_receipt=json.loads((proof.parent/'APK-VERIFICATION.json').read_text())
    require(parent_receipt['candidate']==2103319 and parent_receipt['apk_sha256']==BASE,'Locked source/APK association mismatch')
    dest=out/'android-source';shutil.copytree(source,dest);subprocess.run([sys.executable,str(HERE/'apply.py'),str(dest)],check=True)
    actual=snapshot(dest);changed=sorted(n for n in expected if expected[n]!=actual.get(n))
    allowed=sorted('tools/android/packaging/xbmc/src/'+n+'.java.in' for n in ['CobraProUi','InfinityLiveActivity'])
    require(changed==allowed and actual.keys()==expected.keys(),'Source changes outside the two declared Cobra presentation families')
    (out/'SOURCE-PRESERVATION.json').write_text(json.dumps({'before':expected,'after':actual,'changed':changed,'base':2103319},indent=2)+'\n')
    parent.factory.BASE_APK_SHA256=BASE;parent.factory.VERSION_CODE=VERSION;parent.factory.RELEASE=RELEASE
    parent.factory.prepare(dest.resolve(),base.resolve(),build.resolve(),out.resolve())
    tests=build/'xbmc/src/test/java/com/projectinfinity/kodi';tests.mkdir(parents=True)
    for name in ['repairs/cobra-navigation-2103157/tests/CobraNavigationUiTest.java','repairs/sports-hub-2103270/SportsHubTest.java','repairs/cobra-pro-carousel-2103320/ProTeams312Test.java','repairs/cobra-pro-season-2103317/CobraProSeason317Test.java','repairs/cobra-pro-carousel-2103320/CobraProHandoffTest.java','repairs/cobra-power-audit-2103199/tests/Cobra2103199TimeshiftRegressionTest.java','repairs/whole-ui-ambient-2103276/WholeUiAmbientTest.java','repairs/multiview-stability-fill-2103229/tests/Cobra2103229MultiViewStabilityFillTest.java']:
        shutil.copy2(ROOT/name,tests/Path(name).name)
    resources=build/'xbmc/src/test/resources';resources.mkdir(parents=True);shutil.copy2(HERE.parent/'cobra-pro-season-2103317/schedule-fixtures.json',resources/'schedule-fixtures.json')
    previous=tests/'ProTeams312Test.java';s=previous.read_text();s=s.replace('@Test public void proDrawerSportsOpensSameHubAndSelectionSurvivesRerender()', '/* Sports drawer destination intentionally removed in 317; Pro tab is tested instead. */ public void proDrawerSportsOpensSameHubAndSelectionSurvivesRerender()');previous.write_text(s)
    with (build/'xbmc/build.gradle').open('a') as f:f.write('''
android { testOptions { unitTests.includeAndroidResources = true; unitTests.all { maxHeapSize = "3g"; systemProperty "cobra.evidence", rootProject.file("../evidence3320/screenshots").absolutePath; testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" } } } }
configurations { preservationTools }
dependencies { testImplementation 'junit:junit:4.13.2'; testImplementation 'org.robolectric:robolectric:4.14.1'; preservationTools 'org.smali:baksmali:2.5.2' }
tasks.register('exportPreservationTools') { doLast { rootProject.file('preservation-classpath.txt').text = configurations.preservationTools.asPath } }
''')
def package(base,build,out):
    receipt=json.loads((out/'SOURCE-PRESERVATION.json').read_text());require(snapshot(out/'android-source')==receipt['after'],'Source changed after testing')
    bt=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0';donor=build/'xbmc/build/outputs/apk/release/xbmc-release.apk'
    require(resource_ids(bt/'aapt2',base,out/'base-resources.txt')==resource_ids(bt/'aapt2',donor,out/'donor-resources.txt'),'Resource IDs changed')
    unsigned=out/'candidate-unsigned.apk';parent.merge(base,donor,unsigned)
    verify_manifest_pair(run(bt/'aapt','dump','xmltree',base,'AndroidManifest.xml',output=out/'base-manifest.txt'),run(bt/'aapt','dump','xmltree',unsigned,'AndroidManifest.xml',output=out/'candidate-manifest.txt'))
    final=out/f'Infinity-{VERSION}-Cobra-Pro-Carousel-RC1.apk';run('bash',ROOT/'scripts/sign-infinity71.sh',unsigned,final)
    cert=run(bt/'apksigner','verify','--verbose','--print-certs',final,output=out/'signing-verification.txt');require(parent.CERT in cert.lower(),'Signer changed')
    badging=run(bt/'aapt','dump','badging',final,output=out/'badging.txt');require(f"package: name='{parent.PACKAGE}' versionCode='{VERSION}' versionName='{RELEASE}'" in badging,'Wrong identity')
    # Reuse the strict smali comparison with exactly the declared presentation families.
    import inspect
    code=inspect.getsource(parent.compare_dex).replace('InfinityExitCompletion|InfinityGlassChooser|Splash|BuildConfig','InfinityLiveActivity|CobraProUi|CobraVisualRenderer|BuildConfig').replace("'cobra_classes_unchanged':True", "'infinity_kodi_classes_unchanged':True")
    # Retain exact protected-class compiler differences before the strict guard.
    code=code.replace("    changed=sorted(n for n in old.keys()|new.keys() if old.get(n)!=new.get(n))","    import sys;sys.path.insert(0,str(HERE.parent/'cobra-pro-season-2103317'))\n    from bridge_preservation import verify\n    old,new,bridge_report=verify(old,new,out)\n    changed=sorted(n for n in old.keys()|new.keys() if old.get(n)!=new.get(n))")
    code=code.replace("'all_other_classes_bytecode_identical':True","'all_other_classes_behavior_identical':True, 'api_bridge_renumbering_verified':True").replace("'infinity_kodi_classes_unchanged':True","'infinity_kodi_source_and_behavior_preserved':True")
    code=code.replace("    require(not unexpected,",'''    diagnostic=out/'compiler-diffs';diagnostic.mkdir(exist_ok=True)
    for name in unexpected:
        import difflib
        (diagnostic/(Path(name).name+'.diff')).write_text(''.join(difflib.unified_diff(old.get(name,'').splitlines(True),new.get(name,'').splitlines(True),fromfile='base/'+name,tofile='candidate/'+name)))
    for name in sorted(old.keys()|new.keys()):
        if 'ExternalSyntheticApiModelOutline' in name and name.startswith('com/projectinfinity/kodi/'):
            for label,classes in [('base',old),('candidate',new)]:
                if name in classes:(diagnostic/(label+'-'+Path(name).name)).write_text(classes[name])
    require(not unexpected,''')
    ns=parent.__dict__.copy();exec(code,ns);dex=ns['compare_dex'](base,final,build,out)
    report={'candidate':VERSION,'apk_parent':2103319,'base_apk_sha256':BASE,'apk_sha256':sha(final.read_bytes()),'native_sha256':parent.BASE_NATIVE,'source_commit':os.environ['GITHUB_SHA'],'signer_certificate_sha256':parent.CERT,'skin_parent':'1.0.5.201','skin_changed':False,'native_recompiled':False,'data_reset':False,'physical_device_verified':False,'locked':False,'android_source_delta':receipt['changed'],**parent.verify_payload(base,final),**dex}
    import xml.etree.ElementTree as ET
    suites=[]
    for result in sorted((build/'xbmc/build/test-results/testReleaseUnitTest').glob('TEST-*.xml')):
        suite=ET.parse(result).getroot();suites.append({'suite':suite.attrib['name'],**{key:int(suite.attrib.get(key,0)) for key in ['tests','failures','errors','skipped']}})
    require(suites and all(s['failures']==s['errors']==s['skipped']==0 for s in suites),'Tests missing, failed, or skipped')
    report['test_suites']=suites;report['test_total']=sum(s['tests'] for s in suites);report['runtime_environment']='GitHub Actions ubuntu-22.04, Java 17, Android API 35 Robolectric controlled fixtures'
    (out/'APK-VERIFICATION.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    with tarfile.open(out/'repaired-shell-source.tar.gz','w:gz') as tar:tar.add(out/'android-source',arcname='shell-kodi')
    unsigned.unlink()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','package']);p.add_argument('--base',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(exist_ok=True)
    (prepare if a.mode=='prepare' else package)(a.base,a.build,a.out)
