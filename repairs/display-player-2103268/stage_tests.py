#!/usr/bin/env python3
from pathlib import Path
import argparse,shutil
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--inherited',action='store_true');a=p.parse_args();here=Path(__file__).resolve().parent
out=a.build/'xbmc/src/test/java/com/projectinfinity/kodi';out.mkdir(parents=True,exist_ok=True)
paths=['cobra-navigation-2103157/tests/CobraNavigationUiTest.java','cobra-player-refinement-2103202/tests/Cobra2103202LifecycleTest.java','cobra-player-polish-2103201/tests/Cobra2103201ScrubberTest.java','cobra-player-polish-2103201/tests/Cobra2103201SubtitleTest.java','cobra-player-polish-2103201/tests/Cobra2103201MenuPolishTest.java','cobra-power-audit-2103199/tests/Cobra2103199DisplayRegressionTest.java','cobra-pip-call-2103203/tests/Cobra2103203PipControlsTest.java','cobra-media-calls-2103206/tests/Cobra2103206MediaCallsTest.java','multiview-stability-fill-2103229/tests/Cobra2103229MultiViewStabilityFillTest.java']
for n in paths:shutil.copy2(here.parent/n,out/Path(n).name)
shutil.copy2(here/'Cobra2103268ProductAuditTest.java',out/'Cobra2103268ProductAuditTest.java')
# Replace the pre-2103267 hold expectation with the explicitly device-passed 2103267 oracle.
t=out/'Cobra2103201ScrubberTest.java';s=t.read_text();old='actualVideoBackgroundHoldStillOpensChannels';assert s.count(old)==1;s=s.replace(old,'actualVideoBackgroundHoldNeverOpensChannels').replace('hold();assertNotNull(get(a,"mCobraPlayerDrawer"));event(MotionEvent.ACTION_CANCEL,p);','hold();assertNull(get(a,"mCobraPlayerDrawer"));event(MotionEvent.ACTION_CANCEL,p);');t.write_text(s)
if a.inherited:shutil.copytree('source267/staged-tests/java/com/projectinfinity/kodi',out,dirs_exist_ok=True)
fixture=Path('source265/screenshots/test-video-fixture.webp')
a.evidence.mkdir(parents=True,exist_ok=True)
with (a.build/'xbmc/build.gradle').open('a') as f:f.write('''
android.testOptions.unitTests.includeAndroidResources = true
android.testOptions.unitTests.all {
 maxHeapSize = "3g"
 systemProperty "cobra.evidence", "'''+str(a.evidence.resolve())+'''"
 systemProperty "glass.evidence", "'''+str((a.evidence/'protected').resolve())+'''"
 systemProperty "pro.evidence", "'''+str((a.evidence/'pro').resolve())+'''"
 systemProperty "glass.phone.evidence", "'''+str((a.evidence/'phone').resolve())+'''"
 systemProperty "pro.fixture", "'''+str(fixture.resolve())+'''"
 testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" }
}
dependencies { testImplementation 'junit:junit:4.13.2'; testImplementation 'org.robolectric:robolectric:4.14.1' }
''')
