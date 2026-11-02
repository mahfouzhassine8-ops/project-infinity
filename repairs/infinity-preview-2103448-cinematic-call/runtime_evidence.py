"""Admit only complete, byte-bound selected Android chrome results."""
import hashlib,json,re
from pathlib import Path
H=Path(__file__).resolve().parent
CORE_SHA='3eb0090128d5d2be2c68c9cbe723e376b559d6d66c612926744a27656d5c6ca5'
CHECKS={'actual_video_decoded','actual_media_clock_advances','real_mute_toggle',
 'existing_audio_choice','subtitle_actually_rendered','display_modes_preserved',
 'rotation_preserved','original_volume_dialog_preserved','actual_video_tap_hide_and_show',
 'new_chrome_resume_and_start_over_preserved','rapid_replacement_still_latest_request',
 'error_and_retry_preserved'}
CALL_CHECKS={'actual_video_decoded','call_default_muted_video','call_manual_unmute_video',
 'call_end_keeps_video','source_resumed_and_decoder_released','selected_call_journey_complete'}
def need(value,message):
 if not value:raise RuntimeError(message)
def read(p):return json.loads(p.read_text())
def summarize(root=H):
 path=root/'final-evidence/ANDROID-RAW.json';tail=read(path);binding=read(root/'final-evidence/RUNTIME-BINDING.json')
 core_path=root/'runtime-attempts/third/RESULT.json';core=read(core_path);provenance=read(root/'runtime-attempts/third/PROVENANCE.json')
 need(hashlib.sha256(core_path.read_bytes()).hexdigest()==CORE_SHA,'Exact completed core evidence must remain intact')
 need(core['status']=='FAIL' and provenance['conclusion']=='failure' and provenance['run']==41471747914,'Never relabel the failed full workflow')
 need(tail['status']=='PASS' and tail['segment']=='call' and binding['conclusion']=='success','Selected call run must pass')
 need(binding['result_sha256']==hashlib.sha256(path.read_bytes()).hexdigest(),'Exact downloaded result bytes')
 need(binding['head_sha']==tail['source_build']['source'],'Exact tested source revision')
 need(core['source_build']['replaced']==tail['source_build']['replaced'],'Both runs must execute identical production DEX')
 for raw,required in ((core,CHECKS),(tail,CALL_CHECKS)):
  need(raw['source_build']['baseline_sha256']=='2c20613f9056e84fea402cf67729939a205b7d9afb87ec1b6fab800a641efbd3','Exact signed448 baseline')
  need(required<={c['check'] for c in raw['checks']},'Missing selected Android checks')
  need(raw['shutdown']=='NOT_RUN' and raw['physical_Fold']=='NOT_TESTED','Preserve physical/shutdown evidence limits')
  need(all(not c['kodi_pid'] for c in raw['checks'] if c['check']=='no_kodi_process'),'Unexpected Kodi engine launch')
 themes={c['name'] for c in core['checks'] if c['check']=='actual_theme_geometry'}
 need(themes=={v+'-'+t for v in ('1080x2520','1600x1680','2520x1080','1080x960') for t in ('light','dark')}|{'system-night-yes','system-night-no'},'Every selected theme and viewport required')
 runtime_call={c['check'] for c in tail['checks'] if c['check'].startswith(('call_','synthetic_call_'))}
 need(runtime_call=={'call_default_muted_video','call_manual_unmute_video','call_end_keeps_video'},'Call observation must be complete')
 audio={}
 for name,pin in binding['audio_evidence'].items():
  p=root/'final-evidence'/name;need(hashlib.sha256(p.read_bytes()).hexdigest()==pin,'Exact OS audio observation bytes');audio[name]=p.read_text()
 need(re.search(r'^- Actual mode = MODE_IN_CALL\s*$',audio['call-audio-policy.txt'],re.M),'Real Android call mode required')
 identities=[]
 for name,value in (('call-default-media.player.txt','0.000000'),('call-unmuted-media.player.txt','1.000000')):
  raw=audio[name];m=re.search(r'pid: (\d+), uid: (\d+).*packageName: com\.projectinfinity\.kodi,.*connId\((\d+)\)',raw)
  need(m is not None,'Actual Preview media-player identity');identities.append(m.groups())
  need('left - right volume('+value+', '+value+')' in raw,'Actual Android player volume did not match mute choice')
 need(identities[0]==identities[1],'Unmute must retain same actual player connection')
 return dict(status='PASS_SELECTED_PREVIEW_CHROME_CHECKS',source_build=tail['source_build'],
  selected_checks=sorted(CHECKS|CALL_CHECKS),rendered_themes=sorted(themes),runtime_call=sorted(runtime_call),
  observed_Android_audio=dict(default_volume=0.0,manual_unmute_volume=1.0,same_player_connection=True,audible_carrier_or_VoIP_sound='PHYSICAL_DEVICE_PENDING'),
  core=provenance,remaining=binding,failed_full_workflow_relabelled=False,physical_Fold='NOT_TESTED',shutdown='NOT_RUN',
  prior_448_resume_storage='REUSED_ONLY_WHEN_ENGINE_AND_RESUME_CLASSES_BYTE_IDENTICAL')
if __name__=='__main__':print(json.dumps(summarize(),indent=2))
