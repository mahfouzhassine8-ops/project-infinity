from pathlib import Path
import argparse,shutil
p=argparse.ArgumentParser();p.add_argument('--build-dir',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);a=p.parse_args();here=Path(__file__).resolve().parent
out=a.build_dir/'xbmc/src/test/java/com/projectinfinity/kodi';shutil.copytree('source265/staged-tests/java/com/projectinfinity/kodi',out,dirs_exist_ok=True);shutil.copy2(here/'AmbientGlassTest.java',out/'AmbientGlassTest.java')
fixture=Path('source265/screenshots/pro/test-video-fixture.webp');assert fixture.exists()
with (a.build_dir/'xbmc/build.gradle').open('a') as f:f.write('''
android.testOptions.unitTests.includeAndroidResources = true
android.testOptions.unitTests.all {
 maxHeapSize = "3g"
 systemProperty "glass.evidence", "'''+str((a.evidence/'protected').resolve())+'''"
 systemProperty "pro.evidence", "'''+str((a.evidence/'pro').resolve())+'''"
 systemProperty "glass.phone.evidence", "'''+str((a.evidence/'phone').resolve())+'''"
 systemProperty "pro.fixture", "'''+str(fixture.resolve())+'''"
 testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" }
}
dependencies { testImplementation 'junit:junit:4.13.2'; testImplementation 'org.robolectric:robolectric:4.14.1' }
''')
