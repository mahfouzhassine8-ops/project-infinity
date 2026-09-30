from pathlib import Path
import argparse,shutil
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);a=p.parse_args()
out=a.build/'xbmc/src/test/java/com/projectinfinity/kodi';out.mkdir(parents=True,exist_ok=True)
for f in Path('source276/staged-tests').rglob('*.java'):shutil.copy2(f,out/f.name)
shutil.copy2(Path(__file__).parent/'MiniPlayerFillTest.java',out/'MiniPlayerFillTest.java')
evidence=Path('audit277/screenshots').resolve();evidence.mkdir(parents=True,exist_ok=True)
props={'cobra.evidence':evidence,'glass.evidence':evidence/'protected','pro.evidence':evidence/'pro','glass.phone.evidence':evidence/'phone','responsive.evidence':evidence/'responsive','pro.fixture':Path('source276/screenshots/test-video-fixture.webp').resolve()}
with (a.build/'xbmc/build.gradle').open('a') as f:
 f.write('\nandroid.testOptions.unitTests.includeAndroidResources = true\nandroid.testOptions.unitTests.all {\n maxHeapSize = "3g"\n')
 for k,v in props.items():f.write(' systemProperty "'+k+'", "'+str(v)+'"\n')
 f.write(' testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" }\n}\ndependencies { testImplementation "junit:junit:4.13.2"; testImplementation "org.robolectric:robolectric:4.14.1" }\n')
