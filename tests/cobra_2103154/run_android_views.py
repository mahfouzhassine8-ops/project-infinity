#!/usr/bin/env python3
"""Run actual generated Android view/layout code with native Robolectric graphics, never in the release APK."""
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
  maxParallelForks = 1
  systemProperty "cobra.layoutEvidence", System.getenv("COBRA_LAYOUT_EVIDENCE")
  testLogging {
    events "passed", "failed", "skipped"
    showStandardStreams = true
    exceptionFormat = "full"
  }
}
dependencies {
  testImplementation 'junit:junit:4.13.2'
  testImplementation 'org.robolectric:robolectric:4.14.1'
}
''')
env=dict(os.environ);env.update(COBRA_LAYOUT_EVIDENCE=str(out/'layout-evidence'),KODI_ANDROID_KEY_ALIAS='androiddebugkey',KODI_ANDROID_KEY_PASSWORD='android',KODI_ANDROID_STORE_PASSWORD='android',KODI_ANDROID_STORE_FILE=str(Path.home()/'.android/debug.keystore'))
command=['./gradlew','--no-daemon','--console=plain',':xbmc:testReleaseUnitTest','--tests','com.projectinfinity.kodi.CobraModesUiTest','--stacktrace']
try:
    # JUnit has per-test timeouts too. This outer bound prevents a wedged Gradle/Robolectric
    # worker from consuming the entire Actions job and hiding which acceptance gate stalled.
    subprocess.run(command,cwd=build,env=env,check=True,timeout=900)
except subprocess.TimeoutExpired as error:
    raise SystemExit('Cobra Android layout acceptance exceeded 15 minutes; worker terminated deterministically') from error
finally:
    for rel in ('build/test-results/testReleaseUnitTest','build/reports/tests/testReleaseUnitTest'):
        source=app/rel
        if source.exists():shutil.copytree(source,out/source.parent.name,dirs_exist_ok=True)
