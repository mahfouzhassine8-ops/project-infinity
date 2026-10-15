"""Apply a narrow forward delta to the verified archived 2103281 shell."""
from pathlib import Path
import hashlib,json,re,shutil
ROOT=Path('.');HERE=Path(__file__).resolve().parent
SHELL=ROOT/'shell-kodi';SRC=SHELL/'tools/android/packaging/xbmc/src'
def replace(path,old,new):
    s=path.read_text();assert s.count(old)==1,(str(path),old[:80],s.count(old));path.write_text(s.replace(old,new,1))
main=SRC/'Main.java.in'
replace(main,'    mPaused = false;','    mPaused = false;\n    InfinityKodiAmbientGate.update(true, Build.VERSION.SDK_INT >= 26 && isInPictureInPictureMode());')
replace(main,'    mPaused = true;','    mPaused = true;\n    InfinityKodiAmbientGate.update(false, false);')
replace(main,'    mInfinityDestroyed = true;','    mInfinityDestroyed = true;\n    InfinityKodiAmbientGate.update(false, false);')
replace(main,'    super.onPictureInPictureModeChanged(active, configuration);','    super.onPictureInPictureModeChanged(active, configuration);\n    InfinityKodiAmbientGate.update(!mPaused, active);')
replace(main,'    super.onPictureInPictureModeChanged(inPictureInPictureMode);','    super.onPictureInPictureModeChanged(inPictureInPictureMode);\n    InfinityKodiAmbientGate.update(!mPaused, inPictureInPictureMode);')
shutil.copy2(HERE/'InfinityKodiAmbientGate.java.in',SRC/'InfinityKodiAmbientGate.java.in')
cmake=SHELL/'cmake/scripts/android/Install.cmake'
replace(cmake,'                  src/CobraImmersiveAmbient.java','                  src/CobraImmersiveAmbient.java\n                  src/InfinityKodiAmbientGate.java')
with cmake.open('a') as f:f.write('\nconfigure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/xbmc/src/InfinityKodiAmbientGate.java.in\n               ${CMAKE_BINARY_DIR}/tools/android/packaging/xbmc/src/InfinityKodiAmbientGate.java @ONLY)\n')
gradle=SHELL/'tools/android/packaging/xbmc/build.gradle.in'
replace(gradle,'versionCode 2103281','versionCode 2103282');replace(gradle,'1.0.9-Remaining-Audit-RC1','1.0.9-Infinity-Native-Ambient-RC1')
base='bf9e70d68f696fae156c9f33dedf1224c37d7137';apk='4c119343d623be5c15233e7b1ed7fa82e3d1f92c3a5ec56f7d3f85b0707cbfe5'
p=ROOT/'scripts/infinity_background_resume.py';s=p.read_text()
for key,value in [('VERSION_CODE','2103282'),('RELEASE',repr('1.0.9-Infinity-Native-Ambient-RC1')),('BASE_COMMIT',repr(base)),('BASE_APK_SHA256',repr(apk))]:
    s,n=re.subn(r'^'+key+r' = .*$',key+' = '+value,s,flags=re.M);assert n==1
p.write_text(s)
p=ROOT/'scripts/package_background_resume.py';s=p.read_text()
s=s.replace('Infinity-2103281-Remaining-Audit-RC1','Infinity-2103282-Infinity-Native-Ambient-RC1')
native="{('Lcom/projectinfinity/kodi/InfinityKodiAmbientGate;', 'setActive', '(Z)V')}"
s=s.replace("require(original_native==compiled_native, 'JNI native descriptor inventory changed')",f"require(compiled_native==original_native | {native}, 'JNI changes exceed new observer gate')")
s=s.replace("require(native==dex_contract(a)[0],'Final JNI contract changed')",f"require(native==dex_contract(a)[0] | {native},'Final JNI contract exceeds observer gate')")
s=s.replace("expected=kept|{'AndroidManifest.xml',CRASH_RECORDER_APK_PATH}","expected=kept|{'AndroidManifest.xml',CRASH_RECORDER_APK_PATH,'lib/arm64-v8a/libinfinityambient.so'}")
s=s.replace('    return len(original_native),len(core)',"        z.write(ROOT/'engine/libinfinityambient.so', 'lib/arm64-v8a/libinfinityambient.so', compress_type=zipfile.ZIP_STORED)\n    return len(original_native),len(core)")
s=s.replace("'base_run':36818383789","'base_run':36823023157")
s=s.replace("'native_recompiled':False","'native_recompiled':False, 'added_presentation_library':'libinfinityambient.so'")
s=s.replace("ROOT/'repairs/end-to-end-2103279/DEVICE-TEST.md'","ROOT/'repairs/infinity-native-ambient-2103282/DEVICE-TEST.txt'")
s=s.replace('PASS: Display/player repair over exact locked 2103267; native/assets/resources preserved; permanent signer verified','PASS: Infinity presentation observer over exact 2103281; existing native/assets/resources preserved; permanent signer verified')
p.write_text(s)
manifest=ROOT/'engine/background-resume-source.json';m=json.loads(manifest.read_text());m.update(base_source_commit=base,base_apk_sha256=apk,version_code=2103282,release='1.0.9-Infinity-Native-Ambient-RC1',candidate_locked=False,physical_device_verified=False)
for p in [main,SRC/'InfinityKodiAmbientGate.java.in',cmake,gradle]:m['files'].setdefault(str(p.relative_to(SHELL)),{})['after']=hashlib.sha256(p.read_bytes()).hexdigest()
manifest.write_text(json.dumps(m,indent=2,sort_keys=True)+'\n')
print('Applied observer gate only; Cobra source and native engine untouched.')
