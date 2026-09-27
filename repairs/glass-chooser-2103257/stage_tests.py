#!/usr/bin/env python3
"""Test-only Gradle additions AFTER production assembly; never included in signed DEX."""
from pathlib import Path
import argparse,shutil
p=argparse.ArgumentParser();p.add_argument('--build-dir',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);a=p.parse_args()
root=a.build_dir.resolve();here=Path(__file__).resolve().parent
out=root/'xbmc/src/test/java/com/projectinfinity/kodi';out.mkdir(parents=True,exist_ok=True);shutil.copy2(here/'GlassChooserTest.java',out/'GlassChooserTest.java')
with (root/'xbmc/build.gradle').open('a') as f:
 f.write('''\n// Instrument the isolated chooser on the JVM, without loading Kodi or production native code.
android.testOptions.unitTests.includeAndroidResources = true
android.testOptions.unitTests.all {
    maxHeapSize = "3g"
    systemProperty "glass.evidence", "'''+str(a.evidence.resolve())+'''"
    testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" }
}
dependencies {
    testImplementation 'junit:junit:4.13.2'
    testImplementation 'org.robolectric:robolectric:4.14.1'
}
''')
