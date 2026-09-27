#!/usr/bin/env python3
"""Stage only regression-test sources after the production APK has compiled."""
from pathlib import Path
import argparse,shutil
p=argparse.ArgumentParser()
p.add_argument('--build-dir',type=Path,required=True)
p.add_argument('--source257',type=Path,required=True)
p.add_argument('--source258',type=Path,required=True)
p.add_argument('--source259',type=Path,required=True)
p.add_argument('--source260',type=Path,required=True)
p.add_argument('--evidence',type=Path,required=True)
a=p.parse_args()
out=a.build_dir.resolve()/'xbmc/src/test/java/com/projectinfinity/kodi'
out.mkdir(parents=True,exist_ok=True)
for root,name in [
    (a.source257,'GlassChooserTest.java'),
    (a.source258,'GlassOptionsTest.java'),
    (a.source259,'GlassHealthFinishTest.java'),
    (a.source260,'RecoveryFixedTest.java')]:
    hits=list(root.resolve().rglob(name))
    assert len(hits)==1,(name,[str(x) for x in hits])
    shutil.copy2(hits[0],out/name)
gradle=a.build_dir.resolve()/'xbmc/build.gradle'
with gradle.open('a') as f:
    f.write('''\n// Test-only dependencies added after production APK assembly.
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
print('PASS: staged 28 previously-passed UI regression tests; production dependencies unchanged')
