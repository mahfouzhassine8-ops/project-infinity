"""Source-matched native ownership review only. No original diagnostics or app execution."""
from pathlib import Path
import hashlib,importlib.util,json,os,shutil,subprocess,sys,tarfile
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUT=ROOT/'native-ownership-review'
BASE='86d5b5e2b65acb878632d407c3a3a07dd1af3b6d'
BRANCH='work/infinity-native-keyboard-scaling-462-20261107'
WORKFLOW='.github/workflows/infinity-master-controlled-native.yml'
PREFIX='repairs/infinity-native-keyboard-scaling-462-20261107/'
MAP_SHA='8a4baedfa0f978a7eedfc332b935deef3572a9deb2d78d8cd488bf02ce7e740a'
ASSETS=[
 (13274901825,41726452356,51385496,'89646188945e35032c8eb5977882923b3293de4111421fbb32adfb0b77595bfc'),
 (13493978721,42199527560,189571167,'807af5ff2808cfd30eadbab0a23aa28c3be2951de1ad9e3890566fbebc29f5c7')]
def sha(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(name,value):
 OUT.mkdir(exist_ok=True);(OUT/name).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def metadata():
 assert os.environ['GITHUB_REPOSITORY']=='mahfouzhassine8-ops/project-infinity'
 assert os.environ['GITHUB_REF']=='refs/heads/'+BRANCH
 names=subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],text=True,cwd=ROOT).splitlines()
 assert names and all(n==WORKFLOW or n.startswith(PREFIX) for n in names),names
 request=json.loads((HERE/'REVIEW-REQUEST.json').read_text())
 assert request['source_base']==BASE and request['native_changes'] is False
 stage=request.get('stage','restore-review')
 assert stage in ('restore-review','review-callbacks','probe-keyboard','verify-keyboard','compile-keyboard','probe-graphics','verify-compiled-keyboard','review-graphics-lifetime','closeout-native')
 if os.environ.get('GITHUB_OUTPUT'):
  with open(os.environ['GITHUB_OUTPUT'],'a') as f:f.write('stage='+stage+'\n')
 assets=ASSETS if stage=='restore-review' else [ASSETS[0],(13571276665,42364232328,886694,'9cd229acfcf0c8bd30b52ed083fa77ab640888fc04950a1e85f11465c79999c7')]
 evidence=[]
 for aid,run,size,digest in assets:
  row=json.loads(subprocess.check_output(['gh','api',f'repos/mahfouzhassine8-ops/project-infinity/actions/artifacts/{aid}'],text=True))
  assert row['id']==aid and row['workflow_run']['id']==run and row['size_in_bytes']==size
  assert row['digest']=='sha256:'+digest and row['expired'] is False
  evidence.append(dict(artifact=aid,run=run,sha256=digest,size=size))
 save('INPUT-AND-SCOPE.json',dict(source=os.environ['GITHUB_SHA'],base=BASE,files=names,inputs=evidence,native_changed=False,signing=False,APK=False))
 print('PASS exact isolated source-review scope and original input metadata; no compilation or app test selected')
def restore_review():
 spec=importlib.util.spec_from_file_location('exact_downloads_restoration',ROOT/'repairs/infinity-2103460-nine-corrections-20261106/downloads-native/build_native.py')
 recipe=importlib.util.module_from_spec(spec);spec.loader.exec_module(recipe)
 recipe.OUT=OUT;recipe.restore.OUT=OUT
 recipe.restore_sources()
 expected_path=ROOT/'compiled462/NATIVE-SOURCE-MAP.json'
 assert sha(expected_path)==MAP_SHA
 expected=json.loads(expected_path.read_text())
 actual=recipe.restore.hashes(ROOT/'kodi')
 assert actual==expected and len(actual)==9411,'RESTORED_TREE_MUST_EQUAL_EXACT_COMPILED_APK462_MAP'
 selected=set()
 for name in actual:
  if any(name.endswith('/'+x) for x in (
   'GUIKeyboardFactory.cpp','GUIKeyboardFactory.h','GUIKeyboard.cpp','GUIKeyboard.h',
   'GUIDialogKeyboardTouch.cpp','GUIDialogKeyboardTouch.h',
   'GUIKeyboardTouch.cpp','GUIKeyboardTouch.h','GUIDialogKeyboardGeneric.cpp','GUIDialogKeyboardGeneric.h',
   'AndroidTouch.cpp','AndroidTouch.h','GenericTouchActionHandler.cpp','GenericTouchActionHandler.h',
   'GraphicContext.cpp','GraphicContext.h','GUIWindow.cpp','GUIWindow.h')):
   selected.add(name)
 assert any(n.endswith('/GUIKeyboardFactory.cpp') for n in selected)
 assert any(n.endswith('/GraphicContext.cpp') for n in selected)
 for name in sorted(selected):
  target=OUT/'sources'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/'kodi'/name,target)
  assert sha(target)==expected[name]
 # Print source, not private runtime data. Do not repeat ELF symbolication.
 for name in sorted(selected):
  if name.endswith(('GUIKeyboardFactory.cpp','GUIDialogKeyboardTouch.cpp','GUIKeyboardTouch.cpp','GenericTouchActionHandler.cpp','AndroidTouch.cpp')):
   print('SOURCE_BEGIN '+name+' sha256='+expected[name])
   for i,line in enumerate((ROOT/'kodi'/name).read_text().splitlines(),1):print(f'{i:04d}: {line}')
   print('SOURCE_END '+name)
 save('EXACT462-SOURCE-REVIEW.json',dict(status='PASS_EXACT_9411_FILE_MAP',source=os.environ['GITHUB_SHA'],native_map_sha256=MAP_SHA,
      selected_sources={n:expected[n] for n in sorted(selected)},original_engine_sha256='fadfb1a08e3d125958a77d393c1d66453ec3e9c91aac3349ec5806c67c17694d',
      native_patch=False,compilation='NOT_RUN',Android='NOT_RUN',shutdown='NOT_RUN',signing=False,APK=False,
      causal_keyboard_fix='NOT_PROVEN',causal_scaling_fix='NOT_PROVEN'))
 print('PASS exact9411-file APK462 source binding; selected native ownership source exposed; no fix or runtime acceptance claimed')

def review_callbacks(emit=True):
 prior=ROOT/'previous-review'
 proof=json.loads((prior/'EXACT462-SOURCE-REVIEW.json').read_text())
 assert proof['source']=='a6902706d6db77335516990956791c128acb07fc'
 assert proof['status']=='PASS_EXACT_9411_FILE_MAP' and proof['native_map_sha256']==MAP_SHA
 assert sha(prior/'NATIVE-SOURCE-MAP.json')==MAP_SHA
 expected=json.loads((prior/'NATIVE-SOURCE-MAP.json').read_text())
 assert sha(ROOT/'verified-inputs/verified-p0-native-source.tar.gz')=='b147411ef39a5a76250bc17ca41907866f5df684faa9397c84a3ce99c50ac213'
 wanted=['xbmc/platform/android/activity/AndroidKeyboard.cpp','xbmc/platform/android/activity/AndroidKeyboard.h',
         'xbmc/guilib/GUIWindowManager.cpp','xbmc/guilib/GUIWindowManager.h',
         'xbmc/guilib/GUIKeyboard.cpp','xbmc/guilib/GUIKeyboard.h',
         'xbmc/guilib/GUIWindow.cpp','xbmc/windowing/GraphicContext.cpp',
         'xbmc/dialogs/GUIDialogKeyboardTouch.h']
 required={'xbmc/platform/android/activity/AndroidKeyboard.cpp','xbmc/platform/android/activity/AndroidKeyboard.h',\
           'xbmc/guilib/GUIWindowManager.cpp'}
 assert required.issubset(expected),'REQUIRED_NATIVE_BRIDGE_SOURCE_MISSING'
 absent_optional=[name for name in wanted if name not in expected]
 wanted=[name for name in wanted if name in expected]
 extracted={}
 with tarfile.open(ROOT/'verified-inputs/verified-p0-native-source.tar.gz','r:gz') as archive:
  for member in archive:
   name=member.name.removeprefix('./')
   if name in wanted:
    assert member.isfile() and member.size<512*1024
    raw=archive.extractfile(member).read()
    if hashlib.sha256(raw).hexdigest()==expected[name]:extracted[name]=raw
 for name in wanted:
  if name not in extracted:
   p=prior/'sources'/name
   assert p.is_file() and sha(p)==expected[name], 'MISSING_OR_DIFFERENT_SOURCE:'+name
   extracted[name]=p.read_bytes()
 for name,raw in extracted.items():
  target=OUT/'sources'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
  assert sha(target)==expected[name]
  if emit:print('SOURCE_BEGIN '+name+' sha256='+expected[name])
  lines=raw.decode().splitlines()
  if name.endswith(('GUIWindowManager.cpp','GUIWindow.cpp','GraphicContext.cpp')):
   selected=set()
   markers={'GUIWindowManager.cpp':('::SendMessage(', '::ProcessRenderLoop(', '::Render('),
            'GUIWindow.cpp':('::OnMouseAction(', 'case GUI_MSG_GESTURE_NOTIFY'),
            'GraphicContext.cpp':('::SetOrigin(', '::RestoreOrigin(', '::SetScalingResolution(', '::SetRenderingResolution(')}
   for i,line in enumerate(lines):
    if any(m in line for m in markers[Path(name).name]):
     for j in range(max(0,i-2),min(len(lines),i+75)):selected.add(j)
  else:selected=range(len(lines))
  if emit:
   for i in sorted(selected):print(f'{i+1:04d}: {lines[i]}')
  if emit:print('SOURCE_END '+name)
 save('CALLBACK-SOURCE-BINDING.json',dict(status='PASS_SELECTED_SOURCES_MATCH_REUSED_EXACT462_MAP',
      reused_full_map_run=42364232328,reused_full_map_artifact=13571276665,absent_optional_sources=absent_optional,
      source=os.environ['GITHUB_SHA'],selected_sources={n:expected[n] for n in wanted},
      native_patch=False,compilation='NOT_RUN',Android='NOT_RUN',signing=False,APK=False))
 print('PASS callback/locking source binding; reused9411-file proof; no unchanged tests or symbolication repeated')


def probe_keyboard():
 review_callbacks(emit=False)
 import probe_keyboard as probe
 probe.run(ROOT,OUT)
def verify_keyboard():
 review_callbacks(emit=False)
 import verify_keyboard as probe
 probe.run(ROOT,OUT)


def review_graphics():
 review_callbacks(emit=False)
 expected=json.loads((ROOT/'previous-review/NATIVE-SOURCE-MAP.json').read_text())
 names=['xbmc/guilib/GUIWindow.cpp','xbmc/guilib/GUIControl.cpp','xbmc/guilib/GUIControlGroup.cpp',
 'xbmc/guilib/GUIWindowManager.cpp','xbmc/windowing/GraphicContext.cpp','xbmc/windowing/GraphicContext.h',
 'xbmc/platform/android/activity/XBMCApp.cpp','xbmc/platform/android/activity/android_main.cpp',
 'xbmc/platform/android/activity/android_native_app_glue.c','xbmc/windowing/android/WinEventsAndroid.cpp',
 'xbmc/application/AppInboundProtocol.cpp']
 names=[n for n in names if n in expected];raws={}
 with tarfile.open(ROOT/'verified-inputs/verified-p0-native-source.tar.gz','r:gz')as archive:
  for member in archive:
   n=member.name.removeprefix('./')
   if n in names:
    assert member.isfile() and member.size<2*1024*1024
    raw=archive.extractfile(member).read()
    if hashlib.sha256(raw).hexdigest()==expected[n]:raws[n]=raw
 for n in names:
  if n not in raws:
   p=ROOT/'previous-review/sources'/n
   assert p.is_file() and sha(p)==expected[n],'UNBOUND_GRAPHICS_SOURCE:'+n
   raws[n]=p.read_bytes()
  p=OUT/'sources'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raws[n])
  lines=raws[n].decode().splitlines();selected=set()
  markers=('::DoRender(', '::RenderPass(', '::Render(', '::OnInputEvent(', '::onInputEvent(', '::OnEvent(',
    '::MessagePump(', '::ProcessQueue(', 'AInputQueue_getEvent(', 'AInputQueue_attachLooper(', 'onInputEvent(',
    'm_origins','CSingleExit')
  for i,line in enumerate(lines):
   if any(m in line for m in markers):
    for j in range(max(0,i-4),min(len(lines),i+100)):selected.add(j)
  print('GRAPHICS_SOURCE_BEGIN '+n+' sha256='+expected[n])
  for i in sorted(selected):print(f'{i+1:04d}: {lines[i]}')
  print('GRAPHICS_SOURCE_END '+n)
 save('GRAPHICS-SOURCE-BINDING.json',dict(status='PASS_BOUND_EXACT462_READ_ONLY_GRAPHICS_DEPENDENCIES',source=os.environ['GITHUB_SHA'],sources={n:expected[n]for n in names},native_patch=False,graphics_cause='NOT_PROVEN'))
 print('PASS exact462 graphics dependency source exposed; no speculative scaling patch')

def probe_graphics():
 import graphics_research
 graphics_research.run(ROOT,OUT)


def verify_existing_compile():
 prior=ROOT/'compiled-keyboard'
 artifact=json.loads(subprocess.check_output(['gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/artifacts/13571623548'],text=True))
 assert (artifact['workflow_run']['id'],artifact['size_in_bytes'],artifact['digest'],artifact['expired'])==(42365858072,841723,'sha256:42d598f8e203b6529328e9d15fbb068e85bb1108be9b4ef7cf0b3e94a4218213',False)
 run=json.loads(subprocess.check_output(['gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/runs/42365858072'],text=True))
 assert run['head_sha']=='bcb0c4d598b31fd74489eaa50bc2666388501b3c' and run['conclusion']=='failure'
 proof=json.loads((prior/'COMPILE-RESULT.json').read_text())
 assert proof['source_commit']==run['head_sha'] and proof['reviewed_native_inputs_unchanged'] is True
 objects=proof['actual_ARM64_translation_units_compiled']
 assert set(objects)=={'xbmc/guilib/GUIKeyboardFactory.cpp'}
 obj=objects['xbmc/guilib/GUIKeyboardFactory.cpp']
 assert obj['source_sha256']=='fdef3763a10d981649d4312d5f1646514b1e621829153ab9a0fa3900b8418df5'
 assert (obj['ELF_class'],obj['machine'],obj['type'])==('ELF64','AArch64','REL')
 scope=json.loads((prior/'KEYBOARD-SOURCE-PRESERVATION.json').read_text())
 assert scope['protected_native_source_files_unchanged']==9410 and len(scope['changed'])==1
 logs=subprocess.check_output(['gh','api','--allow-escape-sequences','repos/mahfouzhassine8-ops/project-infinity/actions/jobs/128383699532/logs'],text=True)
 assert 'One real ARM64 Android keyboard translation unit compiled' in logs
 assert 'AssertionError:' in logs and 'pthread_mutex_trylock' in logs
 required=[' b (anonymous namespace)::keyboardModalMutex',
           ' U std::__ndk1::recursive_mutex::try_lock()',' U std::__ndk1::recursive_mutex::unlock()',
           'std::__ndk1::unique_lock<std::__ndk1::recursive_mutex>::owns_lock() const']
 for marker in required:assert marker in logs,marker
 selected=[line for line in logs.splitlines() if any(m in line for m in (' b (anonymous namespace)::keyboardModalMutex',' U std::__ndk1::recursive_mutex::',' W std::__ndk1::unique_lock<std::__ndk1::recursive_mutex>::'))]
 (OUT/'ACTUAL-ARM64-LIBCXX-SYMBOLS.txt').write_text('\n'.join(selected)+'\n')
 import difflib
 name='xbmc/guilib/GUIKeyboardFactory.cpp'
 before=ROOT/'previous-review/sources'/name
 after=HERE/'native'/name
 assert sha(before)=='964e3c943a11f1bbed87c4529bedcd08c0111152954ff5b7140fb96c87ef3fb2'
 assert sha(after)==obj['source_sha256']
 delta=''.join(difflib.unified_diff(before.read_text().splitlines(keepends=True),after.read_text().splitlines(keepends=True),fromfile='a/'+name,tofile='b/'+name))
 (OUT/'KEYBOARD-NATIVE-CHANGE.patch').write_text(delta)
 save('KEYBOARD-ARM64-VERIFIED.json',dict(status='PASS_EXISTING_REAL_ARM64_COMPILATION_RECONCILED_WITH_CORRECT_NDK_LIBCXX_ABI',
   source=os.environ['GITHUB_SHA'],compile_source=run['head_sha'],compile_run=42365858072,compile_job=128383699532,
   original_run_result='FAIL_POST_COMPILE_SYMBOL_ASSERTION_NOT_COMPILE_FAILURE',compiled_object=obj,
   protected_native_sources_unchanged=9410,corrected_expectation='NDK_LIBCXX_RECURSIVE_MUTEX_TRY_LOCK_UNLOCK_NOT_DIRECT_PTHREAD',
   code_recompiled=False,original_failure_preserved=True,object_retained_in_artifact=False,
   native_engine_linked=False,Android='NOT_RUN',Fold='NOT_RUN',APK=False,signing=False))
 print('PASS original actual ARM64 object evidence and correct NDK libc++ ownership symbols verified; no recompilation; original post-compile assertion failure retained')
 print(json.dumps(obj,sort_keys=True))


def review_graphics_lifetime():
 expected=json.loads((ROOT/'previous-review/NATIVE-SOURCE-MAP.json').read_text())
 assert sha(ROOT/'previous-review/NATIVE-SOURCE-MAP.json')==MAP_SHA
 spec=importlib.util.spec_from_file_location('exact462_lifetime',ROOT/'repairs/infinity-2103460-nine-corrections-20261106/downloads-native/build_native.py')
 r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r);r.OUT=OUT;r.restore.OUT=OUT;r.restore_sources()
 assert r.restore.hashes(ROOT/'kodi')==expected
 names=['xbmc/ServiceBroker.cpp','xbmc/ServiceBroker.h','xbmc/application/Application.cpp',
 'xbmc/messaging/ApplicationMessenger.cpp','xbmc/messaging/ApplicationMessenger.h',
 'xbmc/platform/android/activity/android_main.cpp','xbmc/platform/android/activity/XBMCApp.cpp',
 'xbmc/guilib/GUIWindowManager.cpp']
 names.extend(n for n in expected if n.endswith('/ThreadMessage.h'))
 for n in names:
  p=ROOT/'kodi'/n;assert sha(p)==expected[n]
  raw=p.read_text();target=OUT/'sources'/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes())
  lines=raw.splitlines();selected=set()
  markers={'ServiceBroker.cpp':('GetWinSystem(', 'RegisterWinSystem(', 'UnregisterWinSystem('),
   'ServiceBroker.h':('GetWinSystem(', 'RegisterWinSystem(', 'UnregisterWinSystem('),
   'Application.cpp':('::Cleanup(', '::Destroy(', 'UnregisterWinSystem(', '->Cleanup(', '::Run(', 'ProcessWindowMessages(', 'checkpoint_poll', 'Checkpoint', 'IsExit'),
   'ApplicationMessenger.cpp':('::Cleanup(', 'CApplicationMessenger::CApplicationMessenger(', '::~CApplicationMessenger('),
   'ApplicationMessenger.h':('struct ThreadMessage','~ThreadMessage'),
   'XBMCApp.cpp':('GetWinSystem(', 'UnregisterWinSystem(', '::~CXBMCApp(', '::run('),
   'GUIWindowManager.cpp':('case TMSG_GUI_MESSAGE:',)}
  if Path(n).name not in markers: selected=set(range(len(lines)))
  else:
   for i,line in enumerate(lines):
    if any(m in line for m in markers[Path(n).name]):
     for j in range(max(0,i-5),min(len(lines),i+130)):selected.add(j)
  print('LIFETIME_SOURCE_BEGIN '+n+' sha256='+expected[n])
  for i in sorted(selected):print(f'{i+1:04d}: {lines[i]}')
  print('LIFETIME_SOURCE_END '+n)
 sites=[]
 for p in (ROOT/'kodi/xbmc').rglob('*.cpp'):
  for i,line in enumerate(p.read_text(errors='replace').splitlines()):
   if 'UnregisterWinSystem(' in line:sites.append((p.relative_to(ROOT/'kodi').as_posix(),i+1,line.strip()))
 save('GRAPHICS-LIFETIME-SOURCES.json',dict(status='PASS_EXACT_SOURCE_BINDING_ONLY',sources={n:expected[n]for n in names},unregister_call_sites=sites,native_patch=False,Android='NOT_RUN'))
 print('UNREGISTER_WINSYSTEM_CALLS '+json.dumps(sites))


def closeout_native():
 prior=ROOT/'previous-review';expected=json.loads((prior/'NATIVE-SOURCE-MAP.json').read_text())
 assert sha(prior/'NATIVE-SOURCE-MAP.json')==MAP_SHA
 name='xbmc/platform/android/activity/InfinityAndroidCheckpoint.cpp'
 source=ROOT/'repairs/android-checkpoint-shutdown/runtime/native/overlay'/name
 assert sha(source)==expected[name],('CHECKPOINT_SOURCE_NOT_EXACT462',sha(source),expected[name])
 text=source.read_text();start=text.index('void Pump(CApplication& application)')
 pump=text[start:text.index('\nvoid ',start+1)] if '\nvoid ' in text[start+1:] else text[start:]
 assert 's.phase == "CHECKPOINT_FAILED"' in pump
 assert 'ProcessWindowMessages(' not in pump
 save('GRAPHICS-CHECKPOINT-BOUNDARY.json',dict(status='EXACT462_PROTECTED_PUMP_HAS_NO_WINDOW_QUERY_DRAIN',source=os.environ['GITHUB_SHA'],
  native_source=name,source_sha256=expected[name],failed_checkpoint_returns_before_work=True,
  application_source_sha256=expected['xbmc/application/Application.cpp'],
  application_binding_run=42366550095,
  dependency='Application::Process returns after protected Pump when checkpoint active; direct synchronous GUI query marshalling would have no guaranteed failure acknowledgement',
  production_graphics_patch=False,checkpoint_source_modified=False,Android='NOT_RUN',Fold='NOT_RUN'))
 print('PASS exact462 checkpoint-source binding; protected failed Pump returns without ProcessWindowMessages')
 for i,line in enumerate(text.splitlines(),1):
  if start<=len('\n'.join(text.splitlines()[:i])) and i<text[:start].count('\n')+23:print(f'{i:04d}: {line}')
 for branch,head in [('work/infinity-2103460-nine-corrections-20261106','86d5b5e2b65acb878632d407c3a3a07dd1af3b6d'),
 ('work/infinity-search-unified-native-candidate-20261107','72fefa8fe2554eb3fa7181027d6b9b2f05d7dd75')]:
  current=json.loads(subprocess.check_output(['gh','api','repos/mahfouzhassine8-ops/project-infinity/git/ref/heads/'+branch],text=True))['object']['sha']
  assert current==head,('PRESERVED_REFERENCE_MOVED_EXTERNALLY',branch,current)
 save('PRESERVED-CHECKPOINTS.json',dict(protected='86d5b5e2b65acb878632d407c3a3a07dd1af3b6d',search_candidate='72fefa8fe2554eb3fa7181027d6b9b2f05d7dd75',source=os.environ['GITHUB_SHA'],unchanged=True,
 native_candidate={'xbmc/guilib/GUIKeyboardFactory.cpp':sha(HERE/'native/xbmc/guilib/GUIKeyboardFactory.cpp')},APK=False,signing=False))
 print('PASS protected correction/Search branches unchanged; no Cobra/Preview/signing/runtime changes')

if __name__=='__main__':
 mode=sys.argv[1]
 {'metadata':metadata,'restore-review':restore_review,'review-callbacks':review_callbacks,
  'probe-keyboard':probe_keyboard,'verify-keyboard':verify_keyboard,'compile-keyboard':review_graphics,'probe-graphics':probe_graphics,'verify-compiled-keyboard':verify_existing_compile,'review-graphics-lifetime':review_graphics_lifetime,'closeout-native':closeout_native}[mode]()
