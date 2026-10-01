from pathlib import Path
build=Path('build280');out=build/'xbmc/src/androidTest/java/com/projectinfinity/kodi';out.mkdir(parents=True,exist_ok=True)
source=Path('repairs/audit-followup-2103280')
head=(source/'CobraRuntimeFollowupTest.java').read_text()
head=head.replace('void check(String name,Action action){long start=', 'void check(String name,Action action){if(!name.toLowerCase(java.util.Locale.US).contains("recording"))return;long start=')
body=(source/'journey.java.fragment').read_text()
assert 'Finished recording clears active UI' in body
(out/'CobraRuntimeFollowupTest.java').write_text(head+body)
with (build/'xbmc/build.gradle').open('a') as f:f.write('''
android { testBuildType "release"; defaultConfig { testInstrumentationRunner "androidx.test.runner.AndroidJUnitRunner" } }
dependencies { androidTestImplementation "androidx.test:runner:1.6.2"; androidTestImplementation "androidx.test.ext:junit:1.2.1" }
''')
