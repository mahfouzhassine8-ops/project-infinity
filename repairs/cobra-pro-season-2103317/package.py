#!/usr/bin/env python3
import argparse,hashlib,importlib.util,json,os,re,shutil,subprocess,sys,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE.parent/'mobile-regressions-2103304'))
from packaging_checks import require,sha,run,resource_ids,verify_manifest_pair
spec=importlib.util.spec_from_file_location('parent316',HERE.parent/'close-progress-isolation-2103316/package_candidate.py');parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)
BASE='8a9884f872e454cba178facd92e638cb76919334de9bf77b67f1f447d38d154b';VERSION=2103317;RELEASE='1.0.9-Cobra-Pro-Season-OLED-RC1'
parent.BASE_SHA=BASE
def snapshot(root):return {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in root.rglob('*') if p.is_file()}
def prepare(base,build,out):
    require(sha(base.read_bytes())==BASE,'Wrong locked 316 APK')
    proofs=list(Path('parent3316').rglob('ANDROID-SOURCE-DELTA.json'));require(bool(proofs),'Missing parent source receipt')
    proof=json.loads(proofs[0].read_text());expected=proof['after'];require(len(expected)==254 and sha(json.dumps(expected,sort_keys=True,separators=(',',':')).encode())=='44d687c75f63fce4bc7ccd2bba344074a53d6f253f45ebc52bac1014e3d5e9ca','Wrong locked 316 source map')
    sources=[p.parents[3] for p in Path('parent3316').rglob('Install.cmake') if p.parent.name=='android']
    metadata=json.loads((HERE/'parent-metadata.json').read_text())
    for candidate in sources:
        for name,content in metadata.items():
            target=candidate/name
            if not target.exists():target.parent.mkdir(parents=True,exist_ok=True);target.write_text(content)
    source=next((p for p in sources if snapshot(p)==expected),None);require(source is not None,'Exact locked 316 source unavailable')
    dest=out/'android-source';shutil.copytree(source,dest);subprocess.run([sys.executable,str(HERE/'apply.py'),str(dest)],check=True)
    actual=snapshot(dest);changed=sorted(n for n in expected if expected[n]!=actual.get(n));allowed=['tools/android/packaging/xbmc/src/'+n+'.java.in' for n in ['CobraProUi','CobraVisualRenderer','InfinityLiveActivity']]
    require(changed==allowed and actual.keys()==expected.keys(),'Source changes outside the three Cobra UI families')
    (out/'SOURCE-PRESERVATION.json').write_text(json.dumps({'before':expected,'after':actual,'changed':changed,'base':2103316},indent=2)+'\n')
    parent.factory.BASE_APK_SHA256=BASE;parent.factory.VERSION_CODE=VERSION;parent.factory.RELEASE=RELEASE
    parent.factory.prepare(dest.resolve(),base.resolve(),build.resolve(),out.resolve())
    tests=build/'xbmc/src/test/java/com/projectinfinity/kodi';tests.mkdir(parents=True)
    for name in ['repairs/cobra-navigation-2103157/tests/CobraNavigationUiTest.java','repairs/sports-hub-2103270/SportsHubTest.java','repairs/pro-teams-2103312/ProTeams312Test.java','repairs/cobra-pro-season-2103317/CobraProSeason317Test.java']:
        shutil.copy2(ROOT/name,tests/Path(name).name)
    previous=tests/'ProTeams312Test.java';s=previous.read_text();s=s.replace('@Test public void proDrawerSportsOpensSameHubAndSelectionSurvivesRerender()', '/* Sports drawer destination intentionally removed in 317; Pro tab is tested instead. */ public void proDrawerSportsOpensSameHubAndSelectionSurvivesRerender()');previous.write_text(s)
    with (build/'xbmc/build.gradle').open('a') as f:f.write('''
android { testOptions { unitTests.includeAndroidResources = true; unitTests.all { maxHeapSize = "3g"; systemProperty "cobra.evidence", rootProject.file("../evidence3317/screenshots").absolutePath; testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" } } } }
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
    final=out/f'Infinity-{VERSION}-Cobra-Pro-Season-OLED-RC1.apk';run('bash',ROOT/'scripts/sign-infinity71.sh',unsigned,final)
    cert=run(bt/'apksigner','verify','--verbose','--print-certs',final,output=out/'signing-verification.txt');require(parent.CERT in cert.lower(),'Signer changed')
    badging=run(bt/'aapt','dump','badging',final,output=out/'badging.txt');require(f"package: name='{parent.PACKAGE}' versionCode='{VERSION}' versionName='{RELEASE}'" in badging,'Wrong identity')
    # Reuse the strict smali comparison with exactly the declared presentation families.
    import inspect
    code=inspect.getsource(parent.compare_dex).replace('InfinityExitCompletion|InfinityGlassChooser|Splash|BuildConfig','InfinityLiveActivity|CobraProUi|CobraVisualRenderer|BuildConfig').replace("'cobra_classes_unchanged':True", "'infinity_kodi_classes_unchanged':True")
    ns=parent.__dict__.copy();exec(code,ns);dex=ns['compare_dex'](base,final,build,out)
    report={'candidate':VERSION,'apk_parent':2103316,'base_apk_sha256':BASE,'apk_sha256':sha(final.read_bytes()),'native_sha256':parent.BASE_NATIVE,'source_commit':os.environ['GITHUB_SHA'],'signer_certificate_sha256':parent.CERT,'skin_parent':'1.0.5.201','skin_changed':False,'native_recompiled':False,'data_reset':False,'physical_device_verified':False,'locked':False,'android_source_delta':receipt['changed'],**parent.verify_payload(base,final),**dex}
    (out/'APK-VERIFICATION.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    with tarfile.open(out/'repaired-shell-source.tar.gz','w:gz') as tar:tar.add(out/'android-source',arcname='shell-kodi')
    unsigned.unlink()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','package']);p.add_argument('--base',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(exist_ok=True)
    (prepare if a.mode=='prepare' else package)(a.base,a.build,a.out)
