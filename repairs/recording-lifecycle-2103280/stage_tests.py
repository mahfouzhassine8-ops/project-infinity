from pathlib import Path
import shutil,json
build=Path('build280');here=Path(__file__).parent
tests=build/'xbmc/src/test/java/com/projectinfinity/kodi';tests.mkdir(parents=True,exist_ok=True)
for f in Path('evidence279/staged-tests').rglob('*.java'):shutil.copy2(f,tests/f.name)
shutil.copy2(here/'RecordingLifecycleTest.java',tests/'RecordingLifecycleTest.java')
resources=build/'xbmc/src/test/resources';resources.mkdir(parents=True,exist_ok=True)
shutil.copy2('shell-kodi/tools/android/packaging/xbmc/res/drawable-nodpi/infinity_splash_icon.png',resources/'cobra-approved-mark.png')
shots=Path('audit280/screenshots').resolve();shots.mkdir(parents=True,exist_ok=True)
props={'cobra.evidence':shots,'glass.evidence':shots/'protected','pro.evidence':shots/'pro','glass.phone.evidence':shots/'phone','responsive.evidence':shots/'responsive','pro.fixture':Path('evidence279/screenshots/test-video-fixture.webp').resolve()}
with (build/'xbmc/build.gradle').open('a') as f:
 f.write('\nandroid.testOptions.unitTests.includeAndroidResources = true\nandroid.testOptions.unitTests.all {\n maxHeapSize = "3g"\n')
 for k,v in props.items():f.write(' systemProperty "'+k+'", "'+str(v)+'"\n')
 f.write(' testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" }\n}\ndependencies { testImplementation "junit:junit:4.13.2"; testImplementation "org.robolectric:robolectric:4.14.1" }\n')
names=json.loads(Path('evidence279/test-classes.json').read_text())+['com.projectinfinity.kodi.RecordingLifecycleTest']
Path('audit280/test-classes.json').write_text(json.dumps(names,indent=2))

