"""Admit complete actual Preview fullscreen/scaling evidence, preserving limits."""
import hashlib,json,re
from pathlib import Path
H=Path(__file__).resolve().parent
CHECKS={'actual_fullscreen_edge_pixels','actual_display_mode_restored','actual_video_decoded','actual_media_clock_advances','actual_hidden_video_progress','actual_window_bar_observation','fullscreen_reversible_without_restart','fullscreen_back_exits_only_mode','actual_viewport_fullscreen_fit','actual_bestfit_fill_stretch_decoding','existing_resume_retained','source_resumed_and_decoder_released','selected_fullscreen_display_functional_complete'}
def need(v,m):
 if not v:raise RuntimeError(m)
def summarize(root=H):
 p=root/'final-evidence/ANDROID-RAW.json';raw=json.loads(p.read_text());binding=json.loads((root/'final-evidence/RUNTIME-BINDING.json').read_text())
 need(raw['status']=='PASS' and binding['conclusion']=='success','Selected Android run must pass')
 need(hashlib.sha256(p.read_bytes()).hexdigest()==binding['result_sha256'],'Exact actual result bytes')
 need(raw['source_build']['source']==binding['head_sha'],'Actual source binding')
 need(raw['source_build']['baseline_sha256']=='01cb1b35ded45ca4124a1e0feed5029554fee51ca0f14c1b3d72bf9e50460161','Exact signed450 baseline')
 need(CHECKS<={c['check'] for c in raw['checks']},'All selected fullscreen/scaling checks required')
 hidden=[c for c in raw['checks'] if c['check']=='actual_fullscreen_chrome_hidden']
 need(len(hidden)>=10 and all(c['consecutive_frames']>=2 and 0<c['seconds']<3.5 for c in hidden),'Actual stable hidden chrome must meet existing short input deadline')
 need({c['mode'] for c in raw['checks'] if c['check']=='actual_display_mode_restored'}=={'Best Fit','Fill (crop)','Stretch'},'Every previous Display mode must be restored after fullscreen')
 need(all(c['matches']>=12 for c in raw['checks'] if c['check']=='actual_fullscreen_edge_pixels'),'Decoded video must reach viewport edges')
 need({c['viewport'] for c in raw['checks'] if c['check']=='actual_viewport_fullscreen_fit'}=={'1080x2520','1600x1680','2520x1080','1680x1600'},'Every selected cover/inner/orientation viewport required')
 patches={c['name']:c['ratio'] for c in raw['checks'] if c['check']=='actual_decoded_patch_ratio'}
 need(set(patches)=={'actual-scale-Best-Fit','actual-scale-Fill-(crop)','actual-scale-Stretch'},'Every real decoded scale proof required')
 need(.65<patches['actual-scale-Best-Fit']<1.5 and .65<patches['actual-scale-Fill-(crop)']<1.5 and patches['actual-scale-Stretch']>3,'Only explicit Stretch may distort actual decoded patch')
 windows={}
 for name,pin in binding['window_evidence'].items():
  p=root/'final-evidence'/name;need(hashlib.sha256(p.read_bytes()).hexdigest()==pin,'Exact OS window evidence')
  rows=[x for x in re.split(r'(?m)^  Window #\d+ ',p.read_text()) if 'InfinityExternalPlayerActivity}' in x.split('\n')[0] and 'ty=BASE_APPLICATION' in x and 'isOnScreen=true' in x]
  need(len(rows)==1,'One actual Preview base window required');row=rows[0];line=re.search(r'Requested non-default-visibility types: ([^\n]+)',row);value=line[1] if line else ''
  # Android37 default-visible status/nav types appear in the non-default mask
  # when explicitly hidden. Both actual snapshots and this mask are retained.
  hidden='statusBars' in value and 'navigationBars' in value
  need(hidden if name.startswith('immersive-') else not hidden,'Actual OS status/navigation request does not match mode')
  windows[name]=dict(hidden_system_bars=hidden,non_default_visibility=value)
 need(any(n.startswith('immersive-') for n in windows) and any(n.startswith('restored-') for n in windows),'Entry and restoration OS evidence required')
 need('initial-normal-window.txt' in windows,'Initial normal system-bar request evidence required')
 initial=set(windows['initial-normal-window.txt']['non_default_visibility'].split())
 need(all(set(v['non_default_visibility'].split())==initial for n,v in windows.items() if n.startswith('restored-')),'Every system-bar request, including caption/overlays, must restore the initial normal policy')
 need(raw['physical_Fold']=='NOT_TESTED' and raw['shutdown']=='NOT_RUN','Preserve evidence limits')
 need(all(not x['kodi_pid'] for x in raw['checks'] if x['check']=='no_kodi_process'),'Unwanted Kodi startup')
 return dict(status='PASS_SELECTED_PREVIEW_FULLSCREEN_DISPLAY_CHECKS',source_build=raw['source_build'],selected_checks=sorted(CHECKS),actual_scaling=patches,window_observations=windows,run=binding,approved_visual_reference='NOT_ACCESSIBLE_MATCH_UNVERIFIED; IMPLEMENTED_FROM_FROZEN_WRITTEN_DESIGN',physical_Fold='NOT_TESTED',shutdown='NOT_RUN',preserved_resume_and_call='SOURCE_AND_CLASS_FROZEN; prior evidence retained')
if __name__=='__main__':print(json.dumps(summarize(),indent=2))
