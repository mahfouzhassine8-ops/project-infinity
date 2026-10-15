#!/usr/bin/env python3
"""Compile/test isolated Android presentation from exact reconstructed shell; no native build."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ap=argparse.ArgumentParser()
ap.add_argument('--root',type=Path,required=True)
ap.add_argument('--build',type=Path,required=True)
ap.add_argument('--evidence',type=Path,required=True)
a=ap.parse_args()
root=a.root.resolve();build=a.build.resolve();evidence=a.evidence.resolve();here=Path(__file__).resolve().parent
src=root/'shell-kodi';pack=src/'tools/android/packaging'
build.mkdir(parents=True,exist_ok=False);evidence.mkdir(parents=True,exist_ok=True)
for name in ('build.gradle','settings.gradle','gradle.properties','gradlew'):
    shutil.copy2(pack/name,build/name)
shutil.copytree(pack/'gradle',build/'gradle');(build/'gradlew').chmod(0o755)
app=build/'xbmc';app.mkdir()
values={'APP_PACKAGE':'com.projectinfinity.kodi','APP_NAME':'Kodi','APP_NAME_LC':'kodi',
        'APP_VERSION':'1.0.9-Cosmic-Chooser-Diagnostics','APP_VERSION_CODE_ANDROID':'2103296',
        'TARGET_MINSDK':'21','TARGET_SDK':'35'}
def config(text):
    for key,value in values.items():text=text.replace('@'+key+'@',value)
    return text
protected={str(p.relative_to(src)):hashlib.sha256(p.read_bytes()).hexdigest() for p in src.rglob('*') if p.is_file()}
original=pack/'xbmc/src'
assert (original/'Main.java.in').read_text().count('InfinityResumeHubInstaller.apply(this);')==1
assert 'cb6a2de4ecf9a47b3953d06ab8eccdf8cfbbcb4fb3a209b87f2ccc41f71c6688' in (original/'InfinityResumeHubInstaller.java.in').read_text()
for p in original.rglob('*.java.in'):
    dest=app/'java/com/projectinfinity/kodi'/str(p.relative_to(original))[:-3]
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(config(p.read_text()))
for name in ('InfinityGlassChooser.java.in','InfinityChooserWeather.java.in','InfinityCosmicArt.java.in'):
    (app/'java/com/projectinfinity/kodi'/name[:-3]).write_text(config((here/name).read_text()))
shutil.copytree(pack/'xbmc/res',app/'res')
for name,dest in (('strings.xml','values'),('colors.xml','values'),('searchable.xml','xml')):
    target=app/'res'/dest/name;target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(config((pack/'xbmc'/(name+'.in')).read_text()))
copies={'drawable/applaunch_screen.png':src/'media/applaunch_screen.png',
        'drawable-xxxhdpi/applaunch_screen.png':src/'media/applaunch_screen.png',
        'drawable/ic_recommendation_80dp.png':src/'media/icon80x80.png',
        'drawable-xhdpi/banner.png':pack/'media/drawable-xhdpi/banner.png'}
for density in ('ldpi','mdpi','hdpi','xhdpi','xxhdpi','xxxhdpi'):
    name='drawable-'+density+'/ic_launcher.png';copies[name]=pack/'media'/name
for name,origin in copies.items():
    target=app/'res'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(origin,target)
(app/'AndroidManifest.xml').write_text('<manifest xmlns:android="http://schemas.android.com/apk/res/android"><application android:theme="@android:style/Theme.Material.NoActionBar" android:label="Chooser diagnostics"/></manifest>\n')
(app/'build.gradle').write_text('''apply plugin: 'com.android.application'
android {
  namespace 'com.projectinfinity.kodi'
  compileSdk 35
  defaultConfig { applicationId 'com.projectinfinity.kodi'; minSdk 21; targetSdk 35; versionCode 2103296; versionName 'chooser-diagnostics' }
  sourceSets { main { manifest.srcFile 'AndroidManifest.xml'; java.srcDirs=['java']; res.srcDirs=['res'] } }
  testOptions { unitTests.includeAndroidResources = true; unitTests.all {
    maxHeapSize = "3g"
    systemProperty "chooser.evidence", "'''+str(evidence)+'''"
    testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" }
  } }
}
dependencies {
  implementation 'androidx.tvprovider:tvprovider:1.1.0-alpha01'
  implementation 'com.google.code.gson:gson:2.10.1'
  implementation 'androidx.media3:media3-exoplayer:1.7.1'
  implementation 'androidx.media3:media3-exoplayer-hls:1.7.1'
  implementation 'androidx.media3:media3-datasource-okhttp:1.7.1'
  implementation 'androidx.media3:media3-exoplayer-rtsp:1.7.1'
  testImplementation 'junit:junit:4.13.2'
  testImplementation 'org.robolectric:robolectric:4.14.1'
}
''')
tests=app/'src/test/java/com/projectinfinity/kodi';tests.mkdir(parents=True)
shutil.copy2(here/'CosmicChooserTest.java',tests/'CosmicChooserTest.java')
after={str(p.relative_to(src)):hashlib.sha256(p.read_bytes()).hexdigest() for p in src.rglob('*') if p.is_file()}
assert protected==after,'Protected reconstructed source modified by diagnostics'
(evidence/'PROTECTED-SOURCE-MANIFEST.json').write_text(json.dumps(protected,indent=2,sort_keys=True)+'\n')
(evidence/'DIAGNOSTIC-SCOPE.json').write_text(json.dumps({'native_compiled':False,'parent_source_modified':False,'production_apk_produced':False,
    'classes_changed':['InfinityGlassChooser'],'new_classes':['InfinityChooserWeather','InfinityCosmicArt'],'physical_test_passed':False},indent=2)+'\n')
print('Prepared actual full Android shell compilation plus isolated chooser JVM tests; native/skin untouched')
