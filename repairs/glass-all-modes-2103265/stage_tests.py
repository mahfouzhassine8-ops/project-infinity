from pathlib import Path
import argparse,shutil,sys
p=argparse.ArgumentParser();p.add_argument('--build-dir',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);a=p.parse_args()
here=Path(__file__).resolve().parent
out=a.build_dir/'xbmc/src/test/java/com/projectinfinity/kodi'
shutil.copytree('source264/staged-tests/java/com/projectinfinity/kodi',out,dirs_exist_ok=True)
shutil.copy2(here/'PhoneGlassTest.java',out/'PhoneGlassTest.java')
# Keep existing Pro action harness and chooser/settings regressions exactly as before.
fixture=Path('source264/screenshots/pro/test-video-fixture.webp')
if not fixture.exists():
    import base64,lzma,json
    bundle=here.parent/'pro-visual-2103262';raw=lzma.decompress(base64.b64decode(''.join((bundle/('bundle'+str(i)+'.b64')).read_text().strip() for i in range(4))))
    fixture=a.evidence/'test-video-fixture.webp';fixture.parent.mkdir(parents=True,exist_ok=True);fixture.write_bytes(base64.b64decode(json.loads(raw)['test-video-fixture.webp']))
with (a.build_dir/'xbmc/build.gradle').open('a') as f:
    f.write('''
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
