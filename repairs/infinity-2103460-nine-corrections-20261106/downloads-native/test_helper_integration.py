from pathlib import Path
import importlib.util,json,types
ROOT=Path(__file__).resolve().parents[3]
paths=['repairs/infinity-master-corrective-20261105/overlay/assets/addons/script.infinity.commandcenter/library_navigation.py','repairs/infinity-kodi-2103453-ui-navigation/overlay/assets/addons/skin.infinity.diggz/resources/lib/infinity_library_navigation.py']
cases=[]
for name in paths:
 s=importlib.util.spec_from_file_location('actual_downloads_helper',ROOT/name);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 calls=[];xb=types.SimpleNamespace(executeJSONRPC=lambda raw:(calls.append(json.loads(raw)) or '{"result":"OK"}'));gui=types.SimpleNamespace(Dialog=lambda:None)
 assert m.run('downloads',xb,gui);assert calls[-1]['params']=={'window':'videos','parameters':['files','return','infinity-downloads-only']};cases.append('scoped_downloads:'+name)
 assert m.run('browse',xb,gui);assert calls[-1]['params']=={'window':'videos','parameters':['files','return']};cases.append('ordinary_files:'+name)
 count=len(calls);assert m.activate(xb,gui,'plugin://anything/',downloads_only=True) is False;assert len(calls)==count;cases.append('reject_other_paths:'+name)
 if 'commandcenter' in name:
  for a,route in [('library-movies','movies'),('library-tv','tv')]:
   assert m.run(a,xb,gui);assert calls[-1]['params']=={'window':'videos','parameters':['plugin://script.infinity.commandcenter/?action='+route,'return','infinity-library-direct']};cases.append('existing_home:'+a)
report={'status':'PASS_ACTUAL_HELPER_IMPORTS','checks':len(cases),'cases':cases,'native_or_provider_execution':False,'Android':'NOT_RUN','shutdown_suite':False}
Path(__file__).with_name('HELPER-INTEGRATION-RESULT.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
