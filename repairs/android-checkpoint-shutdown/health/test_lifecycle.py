#!/usr/bin/env python3
"""Actual patched collector, dashboard, scoped recovery and strict receipt validation."""
import argparse,ast,copy,hashlib,json,os,re,shutil,tempfile,time,types,zipfile
from pathlib import Path
import build
import khc_lifecycle as lifecycle

def main():
 p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--fixture',type=Path,required=True);a=p.parse_args()
 with zipfile.ZipFile(a.baseline) as z:source=build.patch(z.read('script.kodihealthcenter/default.py').decode())
 names={'_runtime_findings','_latest_marker_state','_scan_collect','_publish_dashboard_state'}
 functions=ast.Module(body=[x for x in ast.parse(source).body if isinstance(x,ast.FunctionDef) and x.name in names],type_ignores=[])
 props={};window=types.SimpleNamespace(setProperty=lambda k,v:props.update({k:v}))
 with tempfile.TemporaryDirectory(prefix='health-lifecycle-') as tmp:
  tmp=Path(tmp);home=tmp/'.kodi';home.mkdir();logs=[];old=['ERROR historical unhandled exception']
  env={'re':re,'os':os,'json':json,'time':time,'shutil':shutil,'HOME':str(home),'ADDON_ID':'script.kodihealthcenter','PROFILE':str(home),'SCAN_STATE_FILE':str(tmp/'stale.json'),'CRASH_PATTERNS':('unhandled exception',),'NOISY':(),
   'log_lines':lambda **kw:logs,'old_log_lines':lambda:old,'detect_issues':lambda x:[], '_authorization_health':lambda x:{'needs_attention_count':int(lifecycle.marker_state(x,('invalid_grant',),('trakt token refreshed successfully',))=='REFRESH / AUTH FAILURE')},
   'xbmcvfs':types.SimpleNamespace(translatePath=lambda x:str(tmp/'addon_data')),'installed':lambda x:False,'folder_size':lambda x:0,'fmt_bytes':str,'_known_tweak_leftovers':lambda:[],
   'xbmcaddon':types.SimpleNamespace(Addon=lambda *a:types.SimpleNamespace(getAddonInfo=lambda k:'2.5.18')),'xbmcgui':types.SimpleNamespace(Window=lambda x:window)}
  exec(compile(functions,'actual-health-functions','exec'),env)
  fail='ERROR [plugin.video.thecrew] invalid_grant unhandled exception'
  success='INFO [plugin.video.thecrew] trakt token refreshed successfully'
  other='INFO [plugin.video.pov] trakt token refreshed successfully'
  for lines,expected in [([fail],True),([fail,other],True),([fail,success],False),([fail,success,fail],True),(['ERROR invalid_grant',success],True)]:
   logs[:]=lines;scan=env['_scan_collect']();assert bool(scan['runtime_findings'])==expected
   assert (scan['status']=='NEEDS ATTENTION')==expected
   if not expected:assert scan['resolved_errors']==[fail] and not scan['likely_crashes_script_failures']
   assert scan['historical_errors']==old
  # Dashboard must ignore stale saved issue keys and recompute current operation status.
  (tmp/'stale.json').write_text('["old-repaired-issue"]');logs[:]=[fail,success];env['_publish_dashboard_state']();assert props['KHC.Status']=='Healthy'
  logs[:]=[fail];env['_publish_dashboard_state']();assert props['KHC.Status']=='Needs attention'
  logs.clear();native=json.loads(a.fixture.read_text());raw=json.dumps(native,separators=(',',':'))
  receipt={'schema':1,'phase':'COMPLETE','checkpoint_saved':True,'authorization_consumed':True,'engine_death_epoch_ms':123,'engine_death_elapsed_ms':456,'native_json':raw,'native_receipt':native,'native_proof_sha256':hashlib.sha256(raw.encode()).hexdigest(),**{k:native[k] for k in ('session','owner','pid','generation')}}
  assert lifecycle.checkpoint_state(receipt)['state']=='RESOLVED'
  for field,value in [('checkpoint_saved',False),('authorization_consumed',False),('engine_death_epoch_ms',0),('native_proof_sha256','0'*64),('generation',0)]:
   invalid=copy.deepcopy(receipt);invalid[field]=value;assert lifecycle.checkpoint_state(invalid)['active']
  failed={'phase':'CHECKPOINT_FAILED','error':'python_services: write_failed','session':native['session']}
  path=tmp/'infinity-checkpoint-close.json';path.write_text(json.dumps(failed));scan=env['_scan_collect']();assert scan['shutdown_checkpoint']['state']=='ACTIVE' and scan['status']=='NEEDS ATTENTION'
  path.write_text(json.dumps(receipt));scan=env['_scan_collect']();assert scan['shutdown_checkpoint']['state']=='RESOLVED' and scan['status']=='GOOD'
  with zipfile.ZipFile(a.baseline) as oldzip:
   output=tmp/'update.zip';files=build.build(a.baseline,output)
   for name in oldzip.namelist():
    if not name.endswith('/') and name not in ('script.kodihealthcenter/default.py','script.kodihealthcenter/addon.xml'):assert files[name]==oldzip.read(name)
 print('PASS: scoped recovery, recurrence, unscoped uncertainty, fresh dashboard, original historical evidence, complete/failed/tampered receipt, untouched add-on files')
if __name__=='__main__':main()
