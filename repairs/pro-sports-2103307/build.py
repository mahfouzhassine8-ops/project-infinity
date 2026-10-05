#!/usr/bin/env python3
"""Reuse the protected APK payload, compile Cobra changes, verify before permanent signing."""
import argparse,importlib.util,json,os,shutil,sys,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE.parent/'mobile-regressions-2103304'))
from packaging_checks import sha,require,run,resource_ids,verify_manifest_pair
spec=importlib.util.spec_from_file_location('pack305',HERE.parent/'mobile-followup-2103305/package_candidate.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
BASE='55f1d47bb3ec647b92a5dfbb9de0c0b926027404d9bfecd75a761fd1ed749bc0';NATIVE='6ef69b123ebfd6c956280ab02463d299959671860803f937af883a7c2f86456a'
VERSION=2103307;RELEASE='1.0.9-Cobra-Pro-Sports-RC1'
TESTS=[
'repairs/cobra-navigation-2103157/tests/CobraNavigationUiTest.java',
'repairs/pro-sports-soccer-2103273/ProSportsIntegrationTest.java',
'repairs/sports-hub-2103270/SportsHubTest.java',
'repairs/sports-data-2103271/SportsDataRepairTest.java',
'repairs/whole-ui-ambient-2103276/WholeUiAmbientTest.java',
'repairs/watch-ambient-2103278/WatchAmbientTest.java',
'repairs/cobra-player-polish-2103201/tests/Cobra2103201ScrubberTest.java',
 'repairs/cobra-player-refinement-2103202/tests/Cobra2103202LifecycleTest.java',
'repairs/cobra-pip-call-2103203/tests/Cobra2103203PipControlsTest.java',
'repairs/cobra-media-calls-2103206/tests/Cobra2103206MediaCallsTest.java',
'repairs/cobra-feature-refinement-2103207/tests/Cobra2103207CallIntegrationTest.java',
'repairs/multiview-stability-fill-2103229/tests/Cobra2103229MultiViewStabilityFillTest.java',
'repairs/end-to-end-2103279/EmbeddedBorderCropTest.java',
'repairs/pro-sports-2103307/ProSports307Test.java']
def main():
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','package']);p.add_argument('--source',type=Path,required=True);p.add_argument('--base',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 source,base,build,out=[x.resolve() for x in [a.source,a.base,a.build,a.out]];out.mkdir(parents=True,exist_ok=True)
 require(sha(base.read_bytes())==BASE,'Wrong base APK');old.BASE_NATIVE_SHA=NATIVE
 proof=json.loads((out/'SOURCE-PRESERVATION.json').read_text())
 actual={p.relative_to(source).as_posix():sha(p.read_bytes()) for p in source.rglob('*') if p.is_file()}
 require(actual==proof['after'],'Source changed after validation')
 bt=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0'
 if a.mode=='prepare':
  old.package304.BASE_APK_SHA256=BASE;old.package304.VERSION_CODE=VERSION;old.package304.RELEASE=RELEASE
  old.package304.prepare(source,base,build,out)
  tests=build/'xbmc/src/test/java/com/projectinfinity/kodi';tests.mkdir(parents=True)
  for name in TESTS:shutil.copy2(ROOT/name,tests/Path(name).name)
  with (build/'xbmc/build.gradle').open('a') as f:
   f.write('''\nandroid { testOptions { unitTests.includeAndroidResources = true; unitTests.all { maxHeapSize = "3g"; systemProperty "cobra.evidence", "'''+str(out/'screenshots')+'''"; systemProperty "ambient.evidence", "'''+str(out/'ambient')+'''"; testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" } } } }
dependencies { testImplementation 'junit:junit:4.13.2'; testImplementation 'org.robolectric:robolectric:4.14.1' }
''')
  return
 donor=build/'xbmc/build/outputs/apk/release/xbmc-release.apk'
 require(resource_ids(bt/'aapt2',base,out/'base-resources.txt')==resource_ids(bt/'aapt2',donor,out/'compiled-resources.txt'),'Resource IDs changed')
 unsigned=out/'Cobra-Pro-3307-unsigned.apk';old.merge(base,donor,unsigned)
 verify_manifest_pair(run(bt/'aapt','dump','xmltree',base,'AndroidManifest.xml'),run(bt/'aapt','dump','xmltree',unsigned,'AndroidManifest.xml'))
 final=out/f'Infinity-{VERSION}-Cobra-Pro-Sports-RC1.apk';run('bash',ROOT/'scripts/sign-infinity71.sh',unsigned,final)
 cert=run(bt/'apksigner','verify','--verbose','--print-certs',final,output=out/'signing-verification.txt');require(old.CERT in cert.lower(),'Permanent signer mismatch')
 evidence=old.verify_bytes(base,final)
 badging=run(bt/'aapt','dump','badging',final,output=out/'badging.txt');require(f"versionCode='{VERSION}' versionName='{RELEASE}'" in badging,'Wrong identity')
 import xml.etree.ElementTree as E
 results={}
 for file in (build/'xbmc/build/test-results/testReleaseUnitTest').glob('TEST-*.xml'):
  root=E.parse(file).getroot();require(all(int(root.get(k,'0'))==0 for k in ('failures','errors','skipped')),'Failed or skipped test: '+str(file));results[root.get('name')]=int(root.get('tests'))
 require(len(results)==len(TESTS),'Missing test suites')
 evidence.update(base_apk=2103306,skin_base='1.0.5.201',skin_payload_changed=False,native_recompiled=False,apk_sha256=sha(final.read_bytes()),version_code=VERSION,tests=results,physical_device_verified=False,locked=False)
 (out/'APK-VERIFICATION.json').write_text(json.dumps(evidence,indent=2)+'\n');unsigned.unlink()
 print('Candidate packaged and signed. Device acceptance remains pending.')
if __name__=='__main__':main()
