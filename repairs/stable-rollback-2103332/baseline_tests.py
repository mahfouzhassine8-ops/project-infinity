#!/usr/bin/env python3
"""Validation only: rerun original 327 Android suites, never use their build as delivery."""
import ast,importlib.util,json,os,shutil,subprocess,sys,tarfile
from pathlib import Path
import xml.etree.ElementTree as ET
from restore import APK_SHA,NATIVE_SHA,CERT,file_digest,digest,require
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
BASE=ROOT/'parent327/Infinity-2103327-JobManager-Close-RC1.apk'
EVID=ROOT/'source327';OUT=ROOT/'baseline-evidence';BUILD=ROOT/'baseline-build'
SOURCE=OUT/'source/shell-kodi'
def snapshot(p):return {f.relative_to(p).as_posix():file_digest(f) for f in p.rglob('*') if f.is_file()}
def main():
    OUT.mkdir(exist_ok=True)
    require(file_digest(BASE)==APK_SHA,'Wrong 327 baseline APK')
    proof=json.loads((EVID/'APK-VERIFICATION.json').read_text())
    require(proof['candidate']==2103327 and proof['apk_sha256']==APK_SHA and proof['native_sha256']==NATIVE_SHA and proof['signer_certificate_sha256']==CERT,'Wrong baseline association')
    require(proof['source_commit']=='2bb8f12f700ee69fe5d86629e6639bc0b1a0b79e' and proof['validation_run']=='37687616440','Wrong baseline source/run')
    with tarfile.open(EVID/'repaired-shell-source.tar.gz') as t:t.extractall(OUT/'source',filter='data')
    expected=json.loads((EVID/'SOURCE-PRESERVATION.json').read_text())['after']
    require(digest(json.dumps(expected,sort_keys=True,separators=(',',':')).encode())=='7a40be4f2515ed1304af01debb25529298b1db043c1af20fce7397b368c31e15','Wrong baseline map')
    require(snapshot(SOURCE)==expected,'Baseline source files changed')
    for d in ['mobile-regressions-2103304','chooser-close-owner-2103324','jobmanager-close-2103327']:sys.path.insert(0,str(HERE.parent/d))
    origin=HERE.parent/'jobmanager-close-2103327/package.py'
    spec=importlib.util.spec_from_file_location('original327',origin);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    m.factory.BASE_APK_SHA256=APK_SHA;m.factory.VERSION_CODE=2103327;m.factory.RELEASE='1.0.9-JobManager-Close-RC1'
    m.factory.prepare(SOURCE,BASE,BUILD,OUT)
    func=next(n for n in ast.parse(origin.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='prepare')
    names=ast.literal_eval(next(n.value for n in ast.walk(func) if isinstance(n,ast.Assign) and any(isinstance(a,ast.Name) and a.id=='names' for a in n.targets)))
    require(len(names)==19,'Original test source list changed')
    tests=BUILD/'xbmc/src/test/java/com/projectinfinity/kodi';tests.mkdir(parents=True)
    for n in names:shutil.copy2(ROOT/n,tests/Path(n).name)
    res=BUILD/'xbmc/src/test/resources';res.mkdir(parents=True)
    shutil.copy2(HERE.parent/'cobra-pro-season-2103317/schedule-fixtures.json',res/'schedule-fixtures.json')
    p=tests/'ProTeams312Test.java';old='@Test public void proDrawerSportsOpensSameHubAndSelectionSurvivesRerender()'
    require(p.read_text().count(old)==1,'Original inherited test adjustment changed')
    p.write_text(p.read_text().replace(old,'/* Original 327 harness: destination removed in 317; Pro tab tested instead. */ public void proDrawerSportsOpensSameHubAndSelectionSurvivesRerender()'))
    with (BUILD/'xbmc/build.gradle').open('a') as f:f.write('''
android { testOptions { unitTests.includeAndroidResources = true; unitTests.all { maxHeapSize = "3g"; systemProperty "cobra.evidence", rootProject.file("../baseline-evidence/screenshots").absolutePath; testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" } } } }
dependencies { testImplementation 'junit:junit:4.13.2'; testImplementation 'org.robolectric:robolectric:4.14.1' }
''')
    args=['./gradlew','--no-daemon','--console=plain',':xbmc:testReleaseUnitTest']
    for name in sorted(m.EXPECTED_SUITES):args+=['--tests','com.projectinfinity.kodi.'+name]
    subprocess.run(args,cwd=BUILD,check=True)
    suites=[]
    for p in sorted((BUILD/'xbmc/build/test-results/testReleaseUnitTest').glob('TEST-*.xml')):
        a=ET.parse(p).getroot().attrib;suites.append({'suite':a['name'],**{k:int(a.get(k,0)) for k in ('tests','failures','errors','skipped')}})
    require({s['suite'] for s in suites}=={'com.projectinfinity.kodi.'+n for n in m.EXPECTED_SUITES},'Missing original suite')
    require(all(s['tests']>=m.EXPECTED_SUITES[s['suite'].rsplit('.',1)[-1]] and s['failures']==s['errors']==s['skipped']==0 for s in suites),'Failed/reduced/skipped original tests')
    require(sum(s['tests'] for s in suites)==239 and len(suites)==17,'Unexpected baseline test total')
    require(snapshot(SOURCE)==expected,'Source changed during validation')
    guard=(SOURCE/'tools/android/packaging/xbmc/src/InfinityCloseGuardService.java.in').read_text()
    for token in ['CHANNEL="infinity_normal_close"','IMPORTANCE_LOW','setContentTitle("Closing Infinity")','setContentText("Finishing Kodi cleanup")','MAX_PROTECTION_MS=150000','stopForeground(true)']:
        require(token in guard,'Original notification/guard contract missing')
    require(not (SOURCE/'tools/android/packaging/xbmc/src/InfinityClosingActivity.java.in').exists(),'Experimental Activity source present')
    r={'tested_source_apk':2103327,'delivery_apk':2103332,'source_unchanged':True,'native_recompiled':False,'delivery_uses_test_build':False,'suite_count':len(suites),'tests':sum(s['tests'] for s in suites),'suites':suites,'physical_device_verified':False,'locked':False}
    (OUT/'BASELINE-TESTS.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
if __name__=='__main__':main()
