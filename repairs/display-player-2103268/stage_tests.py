#!/usr/bin/env python3
from pathlib import Path
import argparse,shutil,ast,importlib.util
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--inherited',action='store_true');a=p.parse_args();here=Path(__file__).resolve().parent
out=a.build/'xbmc/src/test/java/com/projectinfinity/kodi';out.mkdir(parents=True,exist_ok=True)
paths=['cobra-navigation-2103157/tests/CobraNavigationUiTest.java','cobra-player-refinement-2103202/tests/Cobra2103202LifecycleTest.java','cobra-player-polish-2103201/tests/Cobra2103201ScrubberTest.java','cobra-player-polish-2103201/tests/Cobra2103201SubtitleTest.java','cobra-player-polish-2103201/tests/Cobra2103201MenuPolishTest.java','cobra-power-audit-2103199/tests/Cobra2103199DisplayRegressionTest.java','cobra-pip-call-2103203/tests/Cobra2103203PipControlsTest.java','cobra-media-calls-2103206/tests/Cobra2103206MediaCallsTest.java','multiview-stability-fill-2103229/tests/Cobra2103229MultiViewStabilityFillTest.java']
for n in paths:shutil.copy2(here.parent/n,out/Path(n).name)
for n in ['cobra-feature-refinement-2103207/tests/Cobra2103207CallIntegrationTest.java','cobra-feature-refinement-2103207/tests/Cobra2103207AudioStateTest.java','cobra-pip-call-2103203/tests/Cobra2103203SubtitleClarityTest.java']:shutil.copy2(here.parent/n,out/Path(n).name)
shutil.copy2(here/'Cobra2103268ProductAuditTest.java',out/'Cobra2103268ProductAuditTest.java')
# Replace the pre-2103267 hold expectation with the explicitly device-passed 2103267 oracle.
t=out/'Cobra2103201ScrubberTest.java';s=t.read_text();old='actualVideoBackgroundHoldStillOpensChannels';assert s.count(old)==1;s=s.replace(old,'actualVideoBackgroundHoldNeverOpensChannels').replace('hold();assertNotNull(get(a,"mCobraPlayerDrawer"));event(MotionEvent.ACTION_CANCEL,p);','hold();assertNull(get(a,"mCobraPlayerDrawer"));event(MotionEvent.ACTION_CANCEL,p);');t.write_text(s)
# Apply recorded 2103203 wording supersession, then recorded locked-2103207
# speaker/call and subtitle-label supersessions. Never infer oracles from 2103268.
spec=importlib.util.spec_from_file_location('historical203',here.parent/'cobra-pip-call-2103203/adapt_inherited_tests.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
t=out/'Cobra2103201SubtitleTest.java';t.write_text(m.adapt(t.name,t.read_text()))
source=(here.parent/'cobra-feature-refinement-2103207/adapt_tests.py').read_text();tree=ast.parse(source);unused=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='edit' and n.args and isinstance(n.args[0],ast.Constant) and n.args[0].value=='Cobra2103205PresentationEffectsTest.java'];assert len(unused)==1
lines=source.splitlines(True);del lines[unused[0].lineno-1:unused[0].end_lineno];namespace={};exec(''.join(lines),namespace);namespace['adapt'](out,a.evidence/'historical-expectation-adaptations.json')
# The later approved player speaker row means this bounded menu can already
# overflow before track discovery. Retain growth when there is room, but check
# scrollability/safe bounds when initially capped; keep focus/track/cue checks.
t=out/'Cobra2103201SubtitleTest.java';s=t.read_text();anchor='int originalHeight=panel.getHeight();ScrollView originalScroll=scroll(panel);';assert s.count(anchor)==1;s=s.replace(anchor,anchor+'boolean initiallyBounded=originalScroll.canScrollVertically(1);')
anchor='assertTrue("Panel must grow for discovered content when the viewport has room",panel.getHeight()>originalHeight);';assert s.count(anchor)==1;s=s.replace(anchor,'if(initiallyBounded){assertTrue("Capped sheet remains navigable and inside its parent",originalScroll.canScrollVertically(1)&&panel.getHeight()<=sheet.getHeight());}else '+anchor);t.write_text(s)
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
