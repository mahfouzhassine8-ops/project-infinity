"""Join completed selected checks without relabeling a failed workflow run."""
import hashlib,json
from pathlib import Path

H=Path(__file__).resolve().parent
CORE_RUN=41436653854
CORE_SHA='b01e3ec781fe45005cb9ef1527f7d61aea12c309225d586f4ca4231af6bc783a'
CORE_CHECKS={
 'separate_A_B_A_B','two_authorities_same_granted_file_share_identity',
 'real_SAF_plain_and_tree_document_identity','periodic_real_decoder_checkpoint',
 'background_progress_preserved','process_restart_keeps_progress',
 'start_over_clears_all_video_aliases','reboot_keeps_private_resume_database',
 'source_resumed_and_decoder_released',
}
TAIL_CHECKS={
 'rapid_replacement_keeps_latest_video','near_end_resets_progress',
 'source_resumed_and_decoder_released','resume_journey_complete',
}
def need(value,message):
 if not value:raise RuntimeError(message)
def read(path):return json.loads(path.read_text())
def summarize(root=H):
 core_path=root/'runtime-attempts/fourth/RESULT.json'
 tail_path=root/'final-evidence/ANDROID-REMAINING.json'
 binding=read(root/'final-evidence/RUNTIME-BINDING.json')
 core=read(core_path);tail=read(tail_path)
 need(hashlib.sha256(core_path.read_bytes()).hexdigest()==CORE_SHA,'Original failed core evidence must remain exact')
 need(core['status']=='FAIL','Retain failed full-run status')
 need(tail['status']=='PASS' and tail['segment']=='remaining','Remaining runtime segment must pass')
 need(binding['core']['run_id']==CORE_RUN and binding['core']['conclusion']=='failure','Retain original workflow conclusion')
 need(binding['remaining']['conclusion']=='success','Remaining workflow must succeed')
 need(binding['remaining']['result_sha256']==hashlib.sha256(tail_path.read_bytes()).hexdigest(),'Exact remaining artifact result')
 need(core['source_build']['replaced']==tail['source_build']['replaced'],'Both runs must decode identical production DEX')
 need(core['source_build']['baseline_sha256']==tail['source_build']['baseline_sha256'],'Both runs must use the same signed baseline')
 for result,required in ((core,CORE_CHECKS),(tail,TAIL_CHECKS)):
  need(required<={c['check'] for c in result['checks']},'Missing selected runtime checkpoint')
  need(result['shutdown']=='NOT_RUN' and result['physical_Fold']=='NOT_TESTED','No shutdown or physical-acceptance claim')
  need(all(not c['kodi_pid'] for c in result['checks'] if c['check']=='no_kodi_process'),'External playback must not launch Kodi')
 themes={(c['viewport'],c['system_night']) for c in tail['checks'] if c['check']=='existing_dark_UI_controls_preserved_under_system_theme'}
 need(themes=={(v,t) for v in ('1080x2520','1600x1680','2520x1080') for t in ('yes','no')},'All selected viewport/theme controls required')
 need({'Denied A','Open BAD'}<={c.get('label') for c in tail['checks'] if c['check']=='real_touch'},'Actual permission/error inputs required')
 return dict(status='PASS_SELECTED_RESUME_CHECKS',
  source_build={'replaced':tail['source_build']['replaced'],'baseline_sha256':tail['source_build']['baseline_sha256']},
  core_checks=sorted(CORE_CHECKS),remaining_checks=sorted(TAIL_CHECKS),viewport_theme_checks=[list(x) for x in sorted(themes)],
  runs=binding,failed_full_run_relabelled=False,
  physical_Fold='NOT_TESTED',proprietary_file_managers='NOT_TESTED',shutdown='NOT_RUN')

if __name__=='__main__':print(json.dumps(summarize(),indent=2))
