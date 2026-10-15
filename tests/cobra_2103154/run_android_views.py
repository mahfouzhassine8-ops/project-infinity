#!/usr/bin/env python3
"""Run actual generated Android view code with native Robolectric graphics, never in the release APK."""
from pathlib import Path
import argparse,os,shutil,subprocess
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();build=a.build.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
app=build/'xbmc';test=app/'src/test/java/com/projectinfinity/kodi';test.mkdir(parents=True,exist_ok=True);shutil.copy2(Path(__file__).with_name('CobraModesUiTest.java'),test/'CobraModesUiTest.java')
with (app/'build.gradle').open('a') as stream:
    stream.write('''
// Host-only acceptance tests; no production dependency is changed.
android.testOptions.unitTests.includeAndroidResources = true
android.testOptions.unitTests.all {
  maxHeapSize = "3g"
  systemProperty "cobra.screenshots", System.getenv("COBRA_SCREENSHOTS")
}
dependencies {
  testImplementation 'junit:junit:4.13.2'
  testImplementation 'org.robolectric:robolectric:4.14.1'
}
''')
env=dict(os.environ);env.update(COBRA_SCREENSHOTS=str(out/'screenshots'),KODI_ANDROID_KEY_ALIAS='androiddebugkey',KODI_ANDROID_KEY_PASSWORD='android',KODI_ANDROID_STORE_PASSWORD='android',KODI_ANDROID_STORE_FILE=str(Path.home()/'.android/debug.keystore'))
try:subprocess.run(['./gradlew','--no-daemon',':xbmc:testReleaseUnitTest','--tests','com.projectinfinity.kodi.CobraModesUiTest','--stacktrace'],cwd=build,env=env,check=True)
finally:
    for rel in ('build/test-results/testReleaseUnitTest','build/reports/tests/testReleaseUnitTest'):
        source=app/rel
        if source.exists():shutil.copytree(source,out/source.parent.name,dirs_exist_ok=True)
