from pathlib import Path
import sys, shutil
sys.path.insert(0, str(Path('scripts').resolve()))
from package_background_resume import prepare

build=Path('build-followup').resolve()
out=Path('compile-evidence').resolve();out.mkdir(exist_ok=True)
prepare(Path('shell-kodi').resolve(),Path('parent279/Infinity-2103279-End-to-End-Repair-RC1.apk').resolve(),build,out)
tests=build/'xbmc/src/androidTest/java/com/projectinfinity/kodi';tests.mkdir(parents=True)
here=Path(__file__).parent
source=(here/'CobraRuntimeFollowupTest.java').read_text()+(here/'helpers.java.fragment').read_text()+(here/'journey.java.fragment').read_text()
(tests/'CobraRuntimeFollowupTest.java').write_text(source)
with (build/'xbmc/build.gradle').open('a') as f:
 f.write('''
android { testBuildType "release"; defaultConfig { testInstrumentationRunner "androidx.test.runner.AndroidJUnitRunner" } }
dependencies { androidTestImplementation "androidx.test:runner:1.6.2"; androidTestImplementation "androidx.test.ext:junit:1.2.1" }
''')
