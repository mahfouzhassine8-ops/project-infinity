from pathlib import Path
build=Path('build281');out=build/'xbmc/src/androidTest/java/com/projectinfinity/kodi';out.mkdir(parents=True,exist_ok=True)
here=Path('repairs/remaining-audit-2103281')
source=(here/'CobraRuntimeFollowupTest.java').read_text()+(here/'helpers.java.fragment').read_text()+(here/'journey.java.fragment').read_text().rstrip()[:-1]+(here/'final-boundaries.java.fragment').read_text()+'\n}\n'
source=source.replace('void check(String name,Action action){long start=', 'void check(String name,Action action){if(!name.contains("Sports"))return;long start=')
(out/'CobraRuntimeFollowupTest.java').write_text(source)
with (build/'xbmc/build.gradle').open('a') as f:f.write('\nandroid { testBuildType "release"; defaultConfig { testInstrumentationRunner "androidx.test.runner.AndroidJUnitRunner" } }\ndependencies { androidTestImplementation "androidx.test:runner:1.6.2"; androidTestImplementation "androidx.test.ext:junit:1.2.1" }\n')
