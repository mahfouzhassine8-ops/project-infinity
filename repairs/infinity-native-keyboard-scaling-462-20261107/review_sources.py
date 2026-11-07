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
 assert stage in ('restore-review','review-callbacks')
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

def review_callbacks():
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
  print('SOURCE_BEGIN '+name+' sha256='+expected[name])
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
  for i in sorted(selected):print(f'{i+1:04d}: {lines[i]}')
  print('SOURCE_END '+name)
 save('CALLBACK-SOURCE-BINDING.json',dict(status='PASS_SELECTED_SOURCES_MATCH_REUSED_EXACT462_MAP',
      reused_full_map_run=42364232328,reused_full_map_artifact=13571276665,absent_optional_sources=absent_optional,
      source=os.environ['GITHUB_SHA'],selected_sources={n:expected[n] for n in wanted},
      native_patch=False,compilation='NOT_RUN',Android='NOT_RUN',signing=False,APK=False))
 print('PASS callback/locking source binding; reused9411-file proof; no unchanged tests or symbolication repeated')

if __name__=='__main__':
 mode=sys.argv[1]
 {'metadata':metadata,'restore-review':restore_review,'review-callbacks':review_callbacks}[mode]()
