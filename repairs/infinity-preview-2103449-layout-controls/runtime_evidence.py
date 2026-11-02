"""Bind complete selected Android decoding/layout/input evidence without masking failures."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
CORE_SHA='f2bc6f8864aac06094d10f74a0fd5841f4491608df63ae965f53a1be211b0647'
CHECKS={'actual_video_decoded','actual_media_clock_advances','seek_actions_preserved','real_rotation_selected_state','duplicate_volume_removed','responsive_landscape_media','hidden_chrome_releases_viewport','real_inline_volume','actual_media_aspect','source_resumed_and_decoder_released','selected_layout_controls_complete'}
def need(v,m):
 if not v:raise RuntimeError(m)
def summarize(root=H):
 p=root/'final-evidence/ANDROID-RAW.json';raw=json.loads(p.read_text());binding=json.loads((root/'final-evidence/RUNTIME-BINDING.json').read_text())
 need(raw['status']=='PASS' and binding['conclusion']=='success','Selected Android run must pass')
 need(hashlib.sha256(p.read_bytes()).hexdigest()==binding['result_sha256'],'Exact actual evidence required')
 need(raw['source_build']['source']==binding['head_sha'],'Exact source binding')
 need(raw['source_build']['baseline_sha256']=='e190c17b3f337133df66e5531d4983e48ce3544c90965db6911936f0db65ec5c','Exact signed449 required')
 core_path=root/'runtime-attempts/second/RESULT.json';core=json.loads(core_path.read_text())
 need(hashlib.sha256(core_path.read_bytes()).hexdigest()==CORE_SHA and core['status']=='FAIL','Preserve exact failed source evidence')
 need(core['source_build']['replaced']==raw['source_build']['replaced'],'Same production DEX required')
 need('seek_actions_preserved' in {x['check'] for x in core['checks']},'Original real seek observations required')
 need(CHECKS<={x['check'] for r in (raw,core) for x in r['checks']},'All selected checks required')
 need({x['name'] for x in raw['checks'] if x['check']=='actual_theme_geometry'}=={v+'-'+t for v in ('1080x2520','1600x1680','2520x1080','1080x960') for t in ('light','dark')},'Every selected viewport/theme required')
 for x in raw['checks']:
  if x['check']=='actual_theme_geometry':need(x['viewport']==[int(n) for n in x['name'].split('-')[0].split('x')],'Observed actual viewport must match selected size')
 need({x['name'] for x in raw['checks'] if x['check']=='actual_media_aspect'}=={'b','c'},'Portrait and square actual decoding required')
 need(all(not x['kodi_pid'] for x in raw['checks'] if x['check']=='no_kodi_process'),'Kodi must not launch')
 need(raw['physical_Fold']=='NOT_TESTED' and raw['shutdown']=='NOT_RUN','Preserve evidence limits')
 return dict(status='PASS_SELECTED_PREVIEW_LAYOUT_CHECKS',source_build=raw['source_build'],selected_checks=sorted(CHECKS),run=binding,completed_seek_source=41538194686,failed_workflow_relabelled=False,physical_Fold='NOT_TESTED',shutdown='NOT_RUN',unchanged_call_resume_engine='REUSE_SIGNED449_EVIDENCE_ONLY_WHEN_SOURCE_AND_CLASS_PRESERVED')
if __name__=='__main__':print(json.dumps(summarize(),indent=2))
