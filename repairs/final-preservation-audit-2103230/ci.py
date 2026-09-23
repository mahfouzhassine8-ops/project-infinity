#!/usr/bin/env python3
"""Real Android compilation, unchanged red/green tests, and exact APK preservation gates."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,os,re,shutil,subprocess,sys,xml.etree.ElementTree as ET,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent.parent
ACT='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
PARENT_SHA='3a80480e300bafc6071aed7f494cc6b3a96a79f7e1e4dcb9ae87fe36c9a707f5'
NATIVE='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
PROOF='Cobra2103230RegressionProofTest'
RED={
 'peerPauseDoesNotCancelAnotherPlayersFallback',
 'endedBufferingEndedUsesSecondAttemptWithoutRequiringReady',
 'multiEndedErrorCannotBypassLiveEndedRecoveryBudget',
 'activeLoaderIsNotAbortedByEighteenSecondMultiWatchdog',
 'promotedFullscreenHonorsItsOwnNormalAspectWithFillSaved',
 'previewUnexpectedEndIsNotSilentlyExcluded',
}
def req(value,message):
 if not value:raise RuntimeError(message)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def stage(build,phase):
 manifest=json.loads((ROOT/'suites.json').read_text());selected=manifest['selected'][:]
 if phase=='baseline':selected.remove('Cobra2103230PolicyTest')
 directory=build/'xbmc/src/test/java/com/projectinfinity/kodi';directory.mkdir(parents=True,exist_ok=True)
 req(not list(directory.glob('*.java')),'Test directory must be empty; no stale/hidden test fixtures')
 hashes={};expected=set()
 for name,path in manifest['sources'].items():
  if phase=='baseline' and name=='Cobra2103230PolicyTest':continue
  source=REPO/path;target=directory/(name+'.java');shutil.copy2(source,target);hashes[name]=sha(target)
  if name in selected:
   methods=re.findall(r'@Test\b(?:(?!@Test).)*?public\s+void\s+(\w+)\s*\(',source.read_text(),re.S)
   req(methods,'No tests discovered in '+name)
   expected.update((name,method) for method in methods)
 resource=build/'xbmc/src/test/resources/cobra-approved-mark.png';resource.parent.mkdir(parents=True,exist_ok=True)
 shutil.copy2('shell-kodi/tools/android/packaging/xbmc/res/drawable-nodpi/infinity_splash_icon.png',resource)
 evidence=(REPO/'audit230'/phase/'screenshots').resolve();evidence.mkdir(parents=True,exist_ok=True)
 config='''\nandroid.testOptions.unitTests.includeAndroidResources = true
android.testOptions.unitTests.all {
    maxHeapSize = "3g"
    maxParallelForks = 1
    systemProperty "cobra.evidence", "%s"
    testLogging { events "started", "passed", "failed", "skipped"; exceptionFormat = "full" }
}
dependencies {
    testImplementation 'junit:junit:4.13.2'
    testImplementation 'org.robolectric:robolectric:4.14.1'
}
'''%evidence.as_posix()
 with (build/'xbmc/build.gradle').open('a') as out:out.write(config)
 write(REPO/'audit230'/phase/'fixture.json',dict(selected=selected,source_hashes=hashes,expected_cases=sorted(expected),approved_art_sha256=sha(resource)))
 return selected,expected,hashes

def tests(build,phase):
 selected,expected,hashes=stage(build,phase)
 command=['./gradlew','--no-daemon','--console=plain',':xbmc:testReleaseUnitTest']
 for name in selected:command+=['--tests','com.projectinfinity.kodi.'+name]
 command+=['--stacktrace']
 log=REPO/'audit230'/phase/'gradle.log';log.parent.mkdir(parents=True,exist_ok=True)
 with log.open('w') as out:
  process=subprocess.Popen(command,cwd=build,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
  for line in process.stdout:out.write(line);print(line,end='',flush=True)
  code=process.wait()
 reports=build/'xbmc/build/test-results/testReleaseUnitTest'
 actual=set();failures={};skipped=[]
 for report in sorted(reports.glob('TEST-*.xml')):
  doc=ET.parse(report)
  for case in doc.findall('.//testcase'):
   key=(case.attrib['classname'].rsplit('.',1)[-1],case.attrib['name'])
   req(key not in actual,'Duplicate test case '+str(key));actual.add(key)
   failure=case.find('failure');error=case.find('error')
   if failure is None:failure=error
   if failure is not None:failures[key]={'type':failure.get('type',''),'message':failure.get('message',''),'trace':failure.text or ''}
   if case.find('skipped') is not None:skipped.append(key)
 expected_fail={(PROOF,name) for name in RED} if phase=='baseline' else set()
 result=dict(phase=phase,gradle_exit_code=code,expected_count=len(expected),executed_count=len(actual),missing=sorted(expected-actual),unexpected=sorted(actual-expected),failures=[dict(suite=k[0],test=k[1],**v) for k,v in failures.items()],skipped=skipped,expected_failures=sorted(expected_fail),source_hashes=hashes,physical_device_verified=False)
 write(REPO/'audit230'/phase/'RESULT.json',result)
 req(actual==expected,'Missing/unexpected compiled test cases: '+str(result['missing'])+' / '+str(result['unexpected']))
 req(not skipped,'Skipped tests are not passes')
 req(set(failures)==expected_fail,'Unexpected test failures; inspect '+str(log))
 if phase=='baseline':
  req(code!=0,'Expected baseline regression tests did not reproduce')
  req(all('Assertion' in v['type'] or 'ComparisonFailure' in v['type'] for v in failures.values()),'Baseline failed on infrastructure/runtime exception, not regression assertion')
 else:
  req(code==0,'Gradle failed despite XML; do not claim test pass')
  previous=json.loads((REPO/'audit230/baseline/RESULT.json').read_text())
  for name,digest in previous['source_hashes'].items():req(hashes.get(name)==digest,'Fixture changed between red and green: '+name)
 result['gate_passed']=True;write(REPO/'audit230'/phase/'RESULT.json',result)
 print('PASS',phase,'executed',len(actual),'expected assertion failures',len(failures))

def baseline():
 out=REPO/'audit230/baseline-stage';out.mkdir(parents=True,exist_ok=True)
 sys.path.insert(0,str(REPO/'scripts'))
 import package_background_resume as pack
 pack.prepare((REPO/'shell-kodi').resolve(),(REPO/'rollback229/packaging-base.apk').resolve(),(REPO/'build230-baseline').resolve(),out)
 tests((REPO/'build230-baseline').resolve(),'baseline')

def verify():
 parent=REPO/'rollback229/accepted-apk/Infinity-1.0.9-Cobra-MultiView-Stability-Fill-RC1.apk'
 apk=REPO/'signed230/Infinity-1.0.9-Cobra-Final-Preservation-Audit-RC1.apk'
 req(sha(parent)==PARENT_SHA,'Rollback is not exact accepted 2103229')
 report=json.loads((REPO/'signed230/background-resume-apk-audit.json').read_text())
 req(report.get('version_code')==2103230,'Wrong versionCode')
 req(report.get('version_name')=='1.0.9-Cobra-Final-Preservation-Audit-RC1','Wrong version name')
 req(report.get('signer_certificate_sha256')==CERT,'Permanent signer drift')
 same=[]
 with zipfile.ZipFile(parent) as p,zipfile.ZipFile(apk) as z:
  req(z.testzip() is None and p.testzip() is None,'ZIP CRC error')
  for name in p.namelist():
   if name.startswith(('assets/','res/','lib/')) or name=='resources.arsc' or re.fullmatch(r'classes\d+\.dex',name):
    req(name in z.namelist() and p.read(name)==z.read(name),'Protected APK entry drift: '+name);same.append(name)
  protected=lambda n:n.startswith(('assets/','res/','lib/')) or n=='resources.arsc' or bool(re.fullmatch(r'classes\d+\.dex',n))
  req({n for n in p.namelist() if protected(n)}=={n for n in z.namelist() if protected(n)},'Protected entries added/removed')
  req(hashlib.sha256(z.read('lib/arm64-v8a/libkodi.so')).hexdigest()==NATIVE,'Native engine drift')
  dex=z.read('classes.dex')
  for token in [b'unexpected-live-ended',b'live-recovery-verified',b'audit_session',b'Multi-View layout',b'Fill Screen',b'Fold Fit',b'Fold Fill',b'COBRA \xe2\x80\xa2 MOVIE DETAILS',b'experience_options_ui_dialog']:
   req(token in dex,'Compiled contract missing '+repr(token))
 baseline_result=json.loads((REPO/'audit230/baseline/RESULT.json').read_text());candidate=json.loads((REPO/'audit230/candidate/RESULT.json').read_text())
 req(baseline_result.get('gate_passed') is True and candidate.get('gate_passed') is True,'Regression gates not passed')
 source=json.loads((REPO/'audit230/source-preservation.json').read_text())
 req(source['before']=='4af3fc3775fe0711b932bb664385a705f0fc5080deba63b3b21de47986a9146e','Wrong source parent')
 req(source['after']==sha(REPO/'shell-kodi'/ACT),'Unreviewed post-audit source mutation')
 allowed={ACT,'tools/android/packaging/xbmc/build.gradle.in'}
 for name,digest in source['files_before'].items():
  if name not in allowed:req(sha(REPO/'shell-kodi'/name)==digest,'Unreviewed file changed: '+name)
 actual_files={str(p.relative_to(REPO/'shell-kodi')) for p in (REPO/'shell-kodi').rglob('*') if p.is_file()}
 req(actual_files==set(source['files_before']),'Generated source files added/removed')
 req(source.get('unreviewed_activity_bytes_identical') is True,'Unreviewed Activity changes')
 output=dict(build=2103230,parent=2103229,apk_sha256=sha(apk),parent_apk_sha256=PARENT_SHA,signer_sha256=CERT,native_sha256=NATIVE,native_rebuilt=False,identical_protected_apk_entries=len(same),source_files_checked=len(actual_files),changed_members=source['changed_members'],baseline_assertion_regressions=len(baseline_result['failures']),candidate_test_cases=candidate['executed_count'],candidate_failures=0,candidate_skips=0,physical_device_verified=False,provider_live_termination_root_cause_confirmed=False,status='TEST CANDIDATE — automated audit passed; device verification required')
 write(REPO/'signed230/ACCEPTANCE.json',output);write(REPO/'audit230/ACCEPTANCE.json',output)
 print('PASS exact parent payload, native, signing, source and red/green tests:',json.dumps(output))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('command',choices=['baseline','candidate','verify']);args=parser.parse_args()
 if args.command=='baseline':baseline()
 elif args.command=='candidate':tests((REPO/'build230').resolve(),'candidate')
 else:verify()
