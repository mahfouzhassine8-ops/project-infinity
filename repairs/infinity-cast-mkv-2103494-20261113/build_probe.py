"""Separate CI-only MKV probe, using actual original94 FFmpeg and new Cast JNI."""
from pathlib import Path
from zipfile import ZipFile
import os,subprocess,sys,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];CAST=ROOT/'repairs/infinity-movies-continue-cast-2103486-20261112/cast'
work=Path(sys.argv[1]).resolve();apk=Path(sys.argv[2]).resolve();sys.path.insert(0,str(CAST))
# Reuse original immutable packaging logic with only a different test Activity.
source=(CAST/'build_probe.py').read_text().replace("(HERE/'android').glob('*.java')",'Path('+repr(str(HERE/'tests/android'))+").glob('*.java')")
source=source.replace('<application android:label="Cast Component CI"','<application android:extractNativeLibs="true" android:label="Cast MKV Component CI"')
scope={'__file__':str(CAST/'build_probe.py'),'__name__':'__main__'};exec(compile(source,str(CAST/'build_probe.py'),'exec'),scope)
ndk=Path(os.environ['ANDROID_HOME'])/'ndk/21.4.7075529';compiler=ndk/'toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android21-clang++'
loader=work/'probe/libinfinitycastqaloader.so'
subprocess.run([str(compiler),'-shared','-fPIC',str(HERE/'tests/android/loader.cpp'),'-ldl','-Wl,-z,max-page-size=16384','-o',str(loader)],check=True)
unsigned=work/'probe/CI-ONLY-UNSIGNED-NOT-OWNER-INSTALLER.apk'
with ZipFile(unsigned,'a') as output,ZipFile(apk) as original:
 for n in original.namelist():
  if n.startswith('lib/arm64-v8a/') and n.endswith('.so'):output.writestr(n,original.read(n))
 output.write(loader,'lib/arm64-v8a/libinfinitycastqaloader.so')
 output.write(work/'mkv/libinfinitycastremux.so','lib/arm64-v8a/libinfinitycastremux.so')
 output.write(work/'mkv/h264-aac.mkv','assets/mkv-fixtures/h264-aac.mkv')
 output.write(work/'mkv/CAST-MKV-HOST.json','assets/mkv-fixtures/expected.json')
print('PASS actual engine/Cast bridge CI-only separate-package probe; no owner installer or Kodi lifecycle changes')
