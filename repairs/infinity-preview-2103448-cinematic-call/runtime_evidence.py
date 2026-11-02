"""Admit only complete, byte-bound selected Android chrome results."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
CHECKS={'actual_video_decoded','actual_media_clock_advances','real_mute_toggle',
 'existing_audio_choice','subtitle_actually_rendered','display_modes_preserved',
 'rotation_preserved','original_volume_dialog_preserved','actual_video_tap_hide_and_show',
 'new_chrome_resume_and_start_over_preserved','rapid_replacement_still_latest_request',
 'error_and_retry_preserved','source_resumed_and_decoder_released','selected_chrome_journey_complete'}
def need(value,message):
 if not value:raise RuntimeError(message)
def read(p):return json.loads(p.read_text())
def summarize(root=H):
 path=root/'final-evidence/ANDROID-RAW.json';raw=read(path);binding=read(root/'final-evidence/RUNTIME-BINDING.json')
 need(raw['status']=='PASS' and binding['conclusion']=='success','Selected Android run must pass')
 need(binding['result_sha256']==hashlib.sha256(path.read_bytes()).hexdigest(),'Exact downloaded result bytes')
 need(binding['head_sha']==raw['source_build']['source'],'Exact tested source revision')
 need(raw['source_build']['baseline_sha256']=='2c20613f9056e84fea402cf67729939a205b7d9afb87ec1b6fab800a641efbd3','Exact signed448 baseline')
 need(CHECKS<={c['check'] for c in raw['checks']},'Missing selected Android checks')
 need(raw['shutdown']=='NOT_RUN' and raw['physical_Fold']=='NOT_TESTED','Preserve physical/shutdown evidence limits')
 need(all(not c['kodi_pid'] for c in raw['checks'] if c['check']=='no_kodi_process'),'Unexpected Kodi engine launch')
 themes={c['name'] for c in raw['checks'] if c['check']=='actual_theme_geometry'}
 need(themes=={v+'-'+t for v in ('1080x2520','1600x1680','2520x1080','1080x960') for t in ('light','dark')}|{'system-night-yes','system-night-no'},'Every selected theme and viewport required')
 runtime_call={c['check'] for c in raw['checks'] if c['check'].startswith(('call_','synthetic_call_'))}
 need(runtime_call in ({'synthetic_call_platform_limit'},{'call_default_muted_video','call_manual_unmute_video','call_end_keeps_video'}),'Call observation must be complete or explicitly unsupported')
 return dict(status='PASS_SELECTED_PREVIEW_CHROME_CHECKS',source_build=raw['source_build'],
  selected_checks=sorted(CHECKS),rendered_themes=sorted(themes),runtime_call=sorted(runtime_call),
  run=binding,physical_Fold='NOT_TESTED',shutdown='NOT_RUN',
  prior_448_resume_storage='REUSED_ONLY_WHEN_ENGINE_AND_RESUME_CLASSES_BYTE_IDENTICAL')
if __name__=='__main__':print(json.dumps(summarize(),indent=2))
