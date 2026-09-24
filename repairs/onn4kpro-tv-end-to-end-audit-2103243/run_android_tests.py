#!/usr/bin/env python3
"""Production Android-view tests with a validated focus bridge; not physical TV certification."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,shutil,subprocess,xml.etree.ElementTree as ET
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
FOCUS_BRIDGE='''package com.projectinfinity.kodi;
/** Robolectric 4.14 ShadowActivity.getCurrentFocus returns a manually stored stub.
 * Delegate to the actual Android View hierarchy instead. No expected target is injected. */
@org.robolectric.annotation.Implements(android.app.Activity.class)
public class TvFocusActivityShadow extends org.robolectric.shadows.ShadowActivity {
 @org.robolectric.annotation.RealObject private android.app.Activity activity;
 @org.robolectric.annotation.Implementation
 @Override protected android.view.View getCurrentFocus(){
  android.view.Window window=activity.getWindow();
  return window==null?null:window.getDecorView().findFocus();
 }
}
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--base-apk',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--baseline',action='store_true');a=p.parse_args()
 source,base,build,out=[x.resolve() for x in (a.source,a.base_apk,a.build,a.out)];out.mkdir(parents=True,exist_ok=True)
 spec=importlib.util.spec_from_file_location('rc22_package',ROOT/'repairs/onn4kpro-tv-final-product-audit-2103242/package.py');pack=importlib.util.module_from_spec(spec);spec.loader.exec_module(pack)
 pack.BASE_APK_SHA256=BASE_APK_SHA
 if not a.baseline:
  receipt=json.loads((ROOT/'engine/background-resume-source.json').read_text());pack.VERSION=receipt['version_code'];pack.RELEASE=receipt['version_name']
  def preservation(folder):
   assert receipt['version_code']==2103243
   for name,row in receipt['files'].items():assert pack.sha((folder/name).read_bytes())==row['after'],name
  pack.source_preservation=preservation
 pack.prepare(source,base,build,out)
 test=build/'xbmc/src/test/java/com/projectinfinity/kodi';test.mkdir(parents=True,exist_ok=True)
 fixture=(ROOT/'repairs/cobra-navigation-2103157/tests/CobraNavigationUiTest.java').read_text()
 anchor='call(a,"buildShell");controller.visible();return a;'
 assert fixture.count(anchor)==1,'Fixture setup anchor drift'
 replacement='''call(a,"buildShell");controller.visible().windowFocusChanged(true);
    ViewGroup decor=(ViewGroup)a.getWindow().getDecorView();
    android.widget.Button probe=new android.widget.Button(a);probe.setText("Remote focus precondition");probe.setFocusable(true);
    decor.addView(probe,new ViewGroup.LayoutParams(64,64));
    int width=a.getResources().getDisplayMetrics().widthPixels,height=a.getResources().getDisplayMetrics().heightPixels;
    decor.measure(View.MeasureSpec.makeMeasureSpec(width,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(height,View.MeasureSpec.EXACTLY));decor.layout(0,0,width,height);
    assertTrue("FIXTURE_REMOTE_FOCUS_UNAVAILABLE",probe.requestFocusFromTouch());
    assertSame("FIXTURE_ACTIVITY_FOCUS_UNAVAILABLE",probe,a.getCurrentFocus());
    assertFalse("FIXTURE_STILL_IN_TOUCH_MODE",probe.isInTouchMode());decor.removeView(probe);return a;'''
 fixture=fixture.replace(anchor,replacement,1)
 (test/'CobraNavigationUiTest.java').write_text(fixture)
 suite_source=(HERE/'tests/Cobra2103243TvAuditTest.java').read_text()
 assert suite_source.count('@Config(sdk=34,')==1
 suite_source=suite_source.replace('@Config(sdk=34,','@Config(shadows=TvFocusActivityShadow.class,sdk=34,',1)
 (test/'Cobra2103243TvAuditTest.java').write_text(suite_source)
 (test/'TvFocusActivityShadow.java').write_text(FOCUS_BRIDGE)
 harness={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(test.glob('*.java'))}
 harness_sha=hashlib.sha256(json.dumps(harness,sort_keys=True).encode()).hexdigest()
 (out/'harness-hashes.json').write_text(json.dumps({'files':harness,'harness_sha256':harness_sha,'remote_window_precondition':True,'activity_focus':'actual decor View.findFocus'},indent=2)+'\n')
 shutil.copytree(test,out/'executed-test-sources',dirs_exist_ok=True)
 if not a.baseline:
  prior=json.loads((ROOT/'audit243/baseline-android/android-test-summary.json').read_text())
  assert prior.get('harness_sha256')==harness_sha,'Re-run the baseline with this exact validated test harness before candidate testing'
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
  known=bool(failures) and name in MARKERS and MARKERS[name] in message and 'FIXTURE_' not in message
  row={'name':name,'status':status,'source_defect_reproduced':known,'seconds':case.get('time'),'failure':message[:5000]};cases.append(row)
  print('RC23 TEST',name,status,'expected-baseline-defect' if known else '')
  if failures and (not a.baseline or not known):unexpected.append(name)
 report={'mode':'locked-rc22-negative-control' if a.baseline else 'rc23-candidate','tests':len(cases),'passed':sum(x['status']=='passed' for x in cases),'reproduced_defects':sum(x['source_defect_reproduced'] for x in cases),'unexpected_failures':unexpected,'cases':cases,'harness_sha256':harness_sha,'remote_window_precondition':True,'activity_focus':'actual decor View.findFocus','physical_device_tested':False,'real_provider_or_decoder_tested':False}
 (out/'android-test-summary.json').write_text(json.dumps(report,indent=2)+'\n')
 assert len(cases)==20,'Missing executed cases'
 assert not any(x['status']=='skipped' for x in cases),'Skipped cases are not a pass'
 if unexpected:raise RuntimeError('Unexpected Android test failures: '+repr(unexpected))
 if a.baseline:
  assert report['reproduced_defects']>0,'Negative control failed to reproduce any defect'
  print('BASELINE CONTROL COMPLETE:',report['reproduced_defects'],'assertion-specific defects; validated real focus; baseline APK unchanged')
 else:
  assert result.returncode==0 and report['passed']==20
  print('PASS: 20 actual Android-view regression cases; physical TV/decoder acceptance pending')
if __name__=='__main__':main()
