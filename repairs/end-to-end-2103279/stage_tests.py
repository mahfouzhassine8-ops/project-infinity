from pathlib import Path
import argparse,shutil,json
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);a=p.parse_args();out=a.build/'xbmc/src/test/java/com/projectinfinity/kodi';out.mkdir(parents=True,exist_ok=True)
for f in Path('source278/staged-tests').rglob('*.java'):shutil.copy2(f,out/f.name)
extras={
 'cobra-final-features-2103205':['Cobra2103205QuickPeekSessionTest','Cobra2103205NetworkPolicyTest','Cobra2103205SessionPolicyTest','Cobra2103205SessionUiTest'],
 'cobra-feature-refinement-2103207':['Cobra2103207QuickPeekIntegrationTest','Cobra2103207RefinementUiTest'],
 'cobra-integration-polish-2103208':['Cobra2103208QuickPeekLayoutTest','Cobra2103208StateOwnershipReviewTest','Cobra2103208PresentationUiTest','Cobra2103208RewindWarmupPresentationTest','Cobra2103208PickerTest','Cobra2103208BrandingTest','Cobra2103208ChooserBrandingTest','Cobra2103208PlaybackPresentationTest'],
 'cobra-provider-boundary-2103200':['Cobra2103200ProviderBoundaryTest'],
 'cobra-complete-product-audit-2103198':['Cobra2103198CompleteProductAuditTest'],
 'cobra-timeshift-transport-integrity-2103181':['Cobra2103181TimeshiftTransportIntegrityTest'],
 'cobra-ts-access-unit-compatibility-2103187':['Cobra2103187TsAccessUnitCompatibilityTest'],
 'cobra-ts-keyframe-compatibility-2103188':['Cobra2103188TsKeyframeCompatibilityTest'],
 'cobra-ts-clock-normalization-2103190':['Cobra2103190TsClockNormalizationTest'],
}
for folder,names in extras.items():
 for name in names:shutil.copy2(Path('repairs')/folder/'tests'/(name+'.java'),out/(name+'.java'))
for name in ['SurfaceRuntimeRegressionTest']:shutil.copy2(Path(__file__).parent/(name+'.java'),out/(name+'.java'))
# Reuse fixture helpers transitively without selecting their historical assertions.
import re
index={}
for f in Path('repairs').rglob('*.java'):index.setdefault(f.stem,[]).append(f)
while True:
 missing=set()
 for f in out.glob('*.java'):
  missing.update(n for n in re.findall(r'\b([A-Z][A-Za-z0-9_]*(?:Test|Harness))\b',f.read_text()) if n in index and not (out/(n+'.java')).exists())
 if not missing:break
 for name in sorted(missing):shutil.copy2(sorted(index[name],key=lambda p:str(p))[-1],out/(name+'.java'))
evidence=Path('audit279/screenshots').resolve();evidence.mkdir(parents=True,exist_ok=True)
props={'cobra.evidence':evidence,'glass.evidence':evidence/'protected','pro.evidence':evidence/'pro','glass.phone.evidence':evidence/'phone','responsive.evidence':evidence/'responsive','pro.fixture':Path('source278/screenshots/test-video-fixture.webp').resolve()}
with (a.build/'xbmc/build.gradle').open('a') as f:
 f.write('\nandroid.testOptions.unitTests.includeAndroidResources = true\nandroid.testOptions.unitTests.all {\n maxHeapSize = "3g"\n')
 for k,v in props.items():f.write(' systemProperty "'+k+'", "'+str(v)+'"\n')
 f.write(' testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" }\n}\ndependencies { testImplementation "junit:junit:4.13.2"; testImplementation "org.robolectric:robolectric:4.14.1" }\n')
locked=json.loads(Path('parent278/CANDIDATE-VERIFICATION.json').read_text())['test_methods']
names=list(locked)+['com.projectinfinity.kodi.'+n for v in extras.values() for n in v]+['com.projectinfinity.kodi.SurfaceRuntimeRegressionTest']
Path('audit279/test-classes.json').write_text(json.dumps(names,indent=2))
