
"""Compile only the proven native keyboard ownership candidate using pinned APK462 inputs."""
from pathlib import Path
import hashlib,importlib.util,json,os,shutil,subprocess,sys,inspect,shlex,builtins
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'native-ownership-review'
NAME='xbmc/guilib/GUIKeyboardFactory.cpp'
BEFORE='964e3c943a11f1bbed87c4529bedcd08c0111152954ff5b7140fb96c87ef3fb2'
AFTER='fdef3763a10d981649d4312d5f1646514b1e621829153ab9a0fa3900b8418df5'
MAP_SHA='8a4baedfa0f978a7eedfc332b935deef3572a9deb2d78d8cd488bf02ce7e740a'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(n,v):OUT.mkdir(exist_ok=True);(OUT/n).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def restore():
 assert sha(ROOT/'previous-review/NATIVE-SOURCE-MAP.json')==MAP_SHA
 expected=json.loads((ROOT/'previous-review/NATIVE-SOURCE-MAP.json').read_text())
 proof=json.loads((ROOT/'keyboard-after/HOST-KEYBOARD-AFTER.json').read_text())
 assert proof['source']=='9173df8c812ead816ed7149ae794de9719130a0d' and proof['status']=='PASS_HOST_NATIVE_MODAL_OWNER_AFTER_ASAN'
 assert (ROOT/'keyboard-after/host-keyboard-after/AFTER.txt').is_file()
 recipe=load(ROOT/'repairs/infinity-2103460-nine-corrections-20261106/downloads-native/build_native.py','exact_apk462_restoration')
 recipe.OUT=OUT;recipe.restore.OUT=OUT;recipe.restore_sources()
 actual=recipe.restore.hashes(ROOT/'kodi');assert actual==expected and len(actual)==9411
 for p in ('scripts/infinity_live_app_ci_2.sh','repairs/android-checkpoint-shutdown/native_ci.py','repairs/android-checkpoint-shutdown/install_ndk.sh'):
  assert (ROOT/p).read_bytes()==subprocess.check_output(['git','show','86d5b5e2b65acb878632d407c3a3a07dd1af3b6d:'+p])
 candidate=HERE/'native'/NAME;assert sha(candidate)==AFTER and actual[NAME]==BEFORE
 shutil.copyfile(candidate,ROOT/'kodi'/NAME)
 actual=recipe.restore.hashes(ROOT/'kodi')
 assert set(actual)==set(expected) and {n for n in actual if actual[n]!=expected[n]}=={NAME}
 save('NATIVE-SOURCE-MAP.json',actual)
 save('KEYBOARD-SOURCE-PRESERVATION.json',dict(source=os.environ['GITHUB_SHA'],base='EXACT_APK462_9411_SOURCE_MAP',changed={NAME:dict(before=BEFORE,after=AFTER)},protected_native_source_files_unchanged=9410,host_after_evidence_reused=42365578534,APK=False,signing=False))
 print('PASS exact APK4629411 sources restored; only Android-only GUIKeyboardFactory.cpp ownership candidate differs;9410 native source files preserved')
def compile():
 recipe=load(ROOT/'repairs/infinity-native-touch-2103451-20261105/compile_only.py','original_selected_compiler')
 recipe.OUT=OUT
 original=inspect.getsource(recipe.compile_objects)
 old="wanted={'xbmc/guilib/GUIBaseContainer.cpp','xbmc/input/InputManager.cpp'}"
 assert original.count(old)==1 and original.count('len(selected)==2')==1
 modified=original.replace(old,"wanted={'xbmc/guilib/GUIKeyboardFactory.cpp'}").replace('len(selected)==2','len(selected)==1').replace('Two real ARM64 Android translation units compiled','One real ARM64 Android keyboard translation unit compiled')
 namespace=recipe.__dict__
 exec(builtins.compile(modified,'<same-original-selected-compile-single-keyboard-target>','exec'),namespace)
 namespace['compile_objects']()
 rows=json.loads((OUT/'SELECTED-COMPILE-COMMANDS.json').read_text());assert len(rows)==1
 row=rows[0];args=row.get('arguments')or shlex.split(row['command'])
 obj=Path(args[args.index('-o')+1]);obj=obj if obj.is_absolute() else Path(row['directory'])/obj
 tool=Path(os.environ['ANDROID_HOME'])/'ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin'
 symbols=subprocess.check_output([str(tool/'llvm-nm'),'-C',str(obj)],text=True)
 assert 'keyboardModalMutex' in symbols and 'pthread_mutex_trylock' in symbols and 'pthread_mutex_unlock' in symbols,symbols
 (OUT/'KEYBOARD-OBJECT-SYMBOLS.txt').write_text(symbols)
 shutil.copyfile(obj,OUT/'GUIKeyboardFactory.cpp.o')
 result=json.loads((OUT/'COMPILE-RESULT.json').read_text())
 save('KEYBOARD-ARM64-VERIFIED.json',dict(status='PASS_REAL_ARM64_KEYBOARD_OBJECT',source=os.environ['GITHUB_SHA'],candidate_source_sha256=AFTER,object_sha256=sha(obj),try_lock_and_unlock_symbols_verified=True,source_preservation='9410_NATIVE_FILES_UNCHANGED',
  reused_host_before_run=42365055708,reused_host_after_run=42365578534,native_engine_linked=False,APK=False,signing=False,Android_runtime='NOT_RUN',Fold='NOT_RUN',graphics_crash='UNRESOLVED_SEPARATE',search_settings='UNRESOLVED_SEPARATE',original_compile_recipe='PROTECTED86D_TWO_TARGET_RECIPE_ONLY_TARGET_SET_CHANGED'))
 print('PASS actual ARM64 ELF64 keyboard object; compiled ownership mutex/trylock/unlock verified; engine link/Android/Fold NOT_RUN')
if __name__=='__main__':{'restore':restore,'compile':compile}[sys.argv[1]]()
