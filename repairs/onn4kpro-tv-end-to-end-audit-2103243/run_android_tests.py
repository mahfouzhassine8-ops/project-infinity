#!/usr/bin/env python3
"""Real Robolectric Android-view tests, not physical TV/decoder certification."""
from pathlib import Path
import argparse, importlib.util, json, os, shutil, subprocess, xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE_APK_SHA='2e0480ae719a319125ad9482840439e3e8406fe47c8181424469a719b44b9754'
MARKERS={
 'powerKeepsFocusAgainstDelayedDirectoryRestore':'DELAYED_DIRECTORY_STOLE_MODAL_FOCUS',
 'powerRestoreCannotStealFromNewModal':'STALE_POWER_RESTORE_STOLE_NEW_MODAL',
 'explicitChannelMenuLinksOverrideGeometry':'EXPLICIT_LINK_IGNORED',
 'separateFastDirectionalPressesAreNotDiscarded':'DISTINCT_FAST_PRESS_DROPPED',
 'heldTransportKeyTogglesOnce':'HELD_KEY_DOUBLE_TOGGLE',
 'systemRequestedPauseIsNotAutomaticallyUndone':'SYSTEM_PAUSE_OVERRIDDEN',
 'dotDoesNotClaimBufferingOrSuppressionIsPlaying':'BUFFERING_MARKED_PLAYING',
 'searchSubmitHandsFocusToCurrentResults':'IME_SUBMIT_LOST_RESULT_FOCUS',
 'searchCardMetadataFitsInsideCard':'SEARCH_CARD_CONTENT_CLIPPED',
 'repeatedQueriesReleaseOldTrimReferences':'DISCARDED_SEARCH_VIEWS_RETAINED',
 'delayedDetailsCannotReplaceNewSection':'STALE_DETAILS_OPENED_AFTER_NAVIGATION',
 'staleMultiFocusCannotSelectFromReplacedAdapter':'STALE_MULTI_SELECTION',
 'playingControlsResetInactivityDeadline':'ACTIVE_INPUT_DID_NOT_RESET_TIMEOUT'
}

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--base-apk',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--baseline',action='store_true');a=p.parse_args()
 source,base,build,out=[x.resolve() for x in (a.source,a.base_apk,a.build,a.out)];out.mkdir(parents=True,exist_ok=True)
 spec=importlib.util.spec_from_file_location('rc22_package',ROOT/'repairs/onn4kpro-tv-final-product-audit-2103242/package.py');pack=importlib.util.module_from_spec(spec);spec.loader.exec_module(pack)
 pack.BASE_APK_SHA256=BASE_APK_SHA
 if not a.baseline:
  receipt=json.loads((ROOT/'engine/background-resume-source.json').read_text());pack.VERSION=receipt['version_code'];pack.RELEASE=receipt['version_name']
  # Candidate audit owns changed contracts; do not pass a doctored receipt to an older validator.
  def preservation(folder):
   assert receipt['version_code']==2103243
   for name,row in receipt['files'].items():assert pack.sha((folder/name).read_bytes())==row['after'],name
  pack.source_preservation=preservation
 pack.prepare(source,base,build,out)
 test=build/'xbmc/src/test/java/com/projectinfinity/kodi';test.mkdir(parents=True,exist_ok=True)
 shutil.copy2(ROOT/'repairs/cobra-navigation-2103157/tests/CobraNavigationUiTest.java',test)
 shutil.copy2(HERE/'tests/Cobra2103243TvAuditTest.java',test)
 with (build/'xbmc/build.gradle').open('a') as f:f.write('''
android.testOptions.unitTests.includeAndroidResources = true
android.testOptions.unitTests.all {
 maxHeapSize = "3g"
 maxParallelForks = 1
 testLogging { events "started", "passed", "failed", "skipped"; showStandardStreams = true; exceptionFormat = "full" }
}
dependencies { testImplementation 'junit:junit:4.13.2'; testImplementation 'org.robolectric:robolectric:4.14.1' }
''')
 env=dict(os.environ,KODI_ANDROID_KEY_ALIAS='androiddebugkey',KODI_ANDROID_KEY_PASSWORD='android',KODI_ANDROID_STORE_PASSWORD='android',KODI_ANDROID_STORE_FILE=str(Path.home()/'.android/debug.keystore'))
 command=['./gradlew','--no-daemon','--console=plain',':xbmc:testReleaseUnitTest','--tests','com.projectinfinity.kodi.Cobra2103243TvAuditTest','--stacktrace']
 result=subprocess.run(command,cwd=build,env=env,timeout=900)
 xml=build/'xbmc/build/test-results/testReleaseUnitTest/TEST-com.projectinfinity.kodi.Cobra2103243TvAuditTest.xml'
 if not xml.is_file():raise RuntimeError('No test XML: compilation/setup failure, not a defect reproduction')
 shutil.copy2(xml,out/xml.name)
 for rel in ['test-results/testReleaseUnitTest','reports/tests/testReleaseUnitTest']:
  folder=build/'xbmc/build'/rel
  if folder.exists():shutil.copytree(folder,out/rel,dirs_exist_ok=True)
 suite=ET.parse(xml).getroot();cases=[];unexpected=[]
 for case in suite.findall('testcase'):
  failures=case.findall('failure')+case.findall('error');message='\n'.join((f.get('message','')+'\n'+(f.text or '')) for f in failures)
  name=case.get('name');status='failed' if failures else 'skipped' if case.find('skipped') is not None else 'passed'
  known=bool(failures) and name in MARKERS and MARKERS[name] in message
  row={'name':name,'status':status,'source_defect_reproduced':known,'seconds':case.get('time'),'failure':message[:5000]};cases.append(row)
  print('RC23 TEST',name,status,'expected-baseline-defect' if known else '')
  if failures and (not a.baseline or not known):unexpected.append(name)
 report={'mode':'locked-rc22-negative-control' if a.baseline else 'rc23-candidate','tests':len(cases),'passed':sum(x['status']=='passed' for x in cases),'reproduced_defects':sum(x['source_defect_reproduced'] for x in cases),'unexpected_failures':unexpected,'cases':cases,'physical_device_tested':False,'real_provider_or_decoder_tested':False}
 (out/'android-test-summary.json').write_text(json.dumps(report,indent=2)+'\n')
 assert len(cases)==20,'Missing executed cases'
 assert not any(x['status']=='skipped' for x in cases),'Skipped cases are not a pass'
 if unexpected:raise RuntimeError('Unexpected Android test failures: '+repr(unexpected))
 if a.baseline:
  assert report['reproduced_defects']>0,'Negative control failed to reproduce any defect'
  print('BASELINE CONTROL COMPLETE:',report['reproduced_defects'],'source defects reproduced; baseline APK unchanged')
 else:
  assert result.returncode==0 and report['passed']==20
  print('PASS: 20 actual Android-view regression cases; physical TV/decoder acceptance pending')
if __name__=='__main__':main()
