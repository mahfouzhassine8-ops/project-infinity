from pathlib import Path
import shutil
build=Path('build279');out=build/'xbmc/src/androidTest/java/com/projectinfinity/kodi';out.mkdir(parents=True,exist_ok=True)
shutil.copy2(Path(__file__).with_name('CobraRuntime279Test.java'),out/'CobraRuntime279Test.java')
with (build/'xbmc/build.gradle').open('a') as f:f.write('''
android { testBuildType "release"; defaultConfig { testInstrumentationRunner "androidx.test.runner.AndroidJUnitRunner" } }
dependencies { androidTestImplementation "androidx.test:runner:1.6.2"; androidTestImplementation "androidx.test.ext:junit:1.2.1" }
''')
