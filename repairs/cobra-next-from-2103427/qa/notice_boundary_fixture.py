import sys,importlib.util,pathlib,tempfile,unittest.mock as M,types,json,xml.etree.ElementTree as E,hashlib
root=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('android_probe',root/'android_probe.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
b=root/'results/runtime/candidate31-notice-recurrence'
modal=(b/'probe/android-compatibility-notice.xml').read_text();welcome=(b/'probe/last-ui.xml').read_text();png=(b/'probe/android-compatibility-notice.png').read_bytes()
paths={n for n in __import__('re').findall(r'lib/arm64-v8a/[A-Za-z0-9_.+-]+\.so',modal)}
launch='Starting: Intent { cmp=com.projectinfinity.kodi/.InfinityLiveActivity }\nStatus: ok\nActivity: com.projectinfinity.kodi/.InfinityLiveActivity\n'
results=[]
def case(name,frames,expect,expected_taps,allowed=paths,start=launch,pngbytes=png):
 calls=[];queue=iter(frames)
 def adb(*args,**kwargs):
  calls.append(list(args))
  if args[:2]==('shell','cat'):return next(queue)
  return ''
 with tempfile.TemporaryDirectory() as td,M.patch.object(p,'adb',side_effect=adb),M.patch.object(p.subprocess,'run',return_value=types.SimpleNamespace(returncode=0,stdout=pngbytes)):
  out=pathlib.Path(td)/'boundary'
  error=None
  try:r=p.acknowledge_known_notice_after_launch(start,out,allowed)
  except Exception as exc:error=str(exc)
  taps=[a for a in calls if a[:3]==['shell','input','tap']]
  assert len(taps)==expected_taps,(name,taps)
  if expect is None:assert error,(name,'unexpected success')
  else:assert error is None and r['status']==expect,(name,error,r)
  assert all(a[3:]==['547','1733'] for a in taps),(name,taps)
  record={'case':name,'result':'PASS','expected_status':expect or 'REJECTED','injected_OK_presses':len(taps),'observed_error':error}
  if out.exists():record['evidence_files']=sorted(q.name for q in out.iterdir())
  results.append(record)
case('actual_modal_once_then_actual_welcome',[modal,modal,welcome],'KNOWN_NOTICE_ACKNOWLEDGED_ONCE',1)
case('actual_welcome_no_dialog',[welcome],'NO_KNOWN_NOTICE_OBSERVED',0)
case('missing_authenticated_native_paths',[modal],None,0,allowed=None)
case('unrecognized_title',[modal.replace('Android App Compatibility','Other Warning')],None,0)
case('unrecognized_message',[modal.replace('LOAD segment and RELRO segment alignment checks failed.','Other failure.')],None,0)
case('wrong_OK_identity',[modal.replace('text="OK"','text="Continue"')],None,0)
case('unknown_native_library',[modal.replace('libkodi.so','unknown-extra.so')],None,0)
case('repeated_notice_after_one_OK',[modal,modal,modal],None,1)
case('unexpected_dialog_after_OK',[modal,modal,modal.replace('Android App Compatibility','Other Warning')],None,1)
case('fresh_bounds_change_no_press',[modal,modal.replace('[463,1662][631,1804]','[400,1662][600,1804]')],None,0)
case('non_PNG_capture_no_press',[modal],None,0,pngbytes=b'not a screenshot')
case('wrong_launch_no_observation',[],None,0,start='Status: ok\nActivity: other.package/.Main')
case('unsuccessful_launch_no_observation',[],None,0,start=launch.replace('Status: ok','Status: failed'))
record={'scope':'QA_ONLY_ACTUAL_SAVED_XML_WITH_MOCKED_ADB; NO_APP_EXECUTION','fixture_modal_sha256':hashlib.sha256(modal.encode()).hexdigest(),'fixture_welcome_sha256':hashlib.sha256(welcome.encode()).hexdigest(),'cases':results}
out=root/'results/runtime/return-boundary-preflight/NOTICE-FIXTURES.json';out.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
