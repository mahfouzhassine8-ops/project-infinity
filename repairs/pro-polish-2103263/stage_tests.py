#!/usr/bin/env python3
"""Reuse exact parent regression harnesses; replace only the Pro visual tests."""
from pathlib import Path
import argparse, shutil
from java_members import member

p = argparse.ArgumentParser()
p.add_argument('--build-dir', type=Path, required=True)
p.add_argument('--evidence', type=Path, required=True)
a = p.parse_args()
here = Path(__file__).resolve().parent
out = a.build_dir.resolve() / 'xbmc/src/test/java/com/projectinfinity/kodi'
shutil.copytree(Path('source262/staged-tests/java/com/projectinfinity/kodi'), out, dirs_exist_ok=True)
shutil.copy2(here/'ProVisualTest.java', out/'ProVisualTest.java')
live = Path('shell-kodi/tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in').read_text()
harness = (out/'ProActionHarness.java').read_text()
for name in ['cobraProPreview','cobraProUnmute','cobraProPauseAndMute','cobraProFilter','cobraProControl','cobraAddProSlot','cobraProSourceForSelection']:
    assert member(live,name) == member(harness,name), 'Stale action harness: '+name
with (a.build_dir/'xbmc/build.gradle').open('a') as f:
    f.write('''
android.testOptions.unitTests.includeAndroidResources = true
android.testOptions.unitTests.all {
    maxHeapSize = "3g"
    systemProperty "glass.evidence", "'''+str((a.evidence/'protected').resolve())+'''"
    systemProperty "pro.evidence", "'''+str((a.evidence/'pro').resolve())+'''"
    systemProperty "pro.fixture", "'''+str(Path('source262/repair-source/test-video-fixture.webp').resolve())+'''"
    testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" }
}
dependencies {
    testImplementation 'junit:junit:4.13.2'
    testImplementation 'org.robolectric:robolectric:4.14.1'
}
''')
