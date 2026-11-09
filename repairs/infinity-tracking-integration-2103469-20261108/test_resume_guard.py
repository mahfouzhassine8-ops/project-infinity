"""Pure evidence-validator controls. No Kodi/player/provider is executed."""
import copy
import hashlib
import json
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import verify_tracking_android as f
route = 'plugin://plugin.video.watchnixtoons2/?action=actionResolve&url=%2Fhost-validator-control'
item = dict(media_type='episode', season=-1, episode=4, ids={}, original_listitem_url=route, path=route)
original = dict(item=copy.deepcopy(item))
current = dict(playing=True, item=copy.deepcopy(item), time=102.0, clock_monotonic=502.0,
               events=[dict(event='AVStarted', sequence=2, monotonic=500.0)])
assert f.exact_resume_observation(current, original, {'position': 100.0}, 1) is current
rows = [dict(case='in_bound_same_source_validator_control',status='PASS_HOST_VALIDATOR_ONLY')]
for case,reason in [('late_offset','EXACT_RESUME_UPPER_OFFSET_BOUND'),('wrong_source','RESUMED_ACTUAL_SOURCE_URI_CONTINUITY'),
                    ('wrong_episode','RESUMED_ACTUAL_TYPED_ITEM_CONTINUITY'),('no_fresh_AV','NEW_ACTUAL_AV_EVENT_REQUIRED')]:
    value=copy.deepcopy(current)
    if case=='late_offset':value['time']=1000
    if case=='wrong_source':value['item'].update(original_listitem_url=route+'x',path=route+'x')
    if case=='wrong_episode':value['item']['episode']=5
    if case=='no_fresh_AV':value['events']=[]
    try:f.exact_resume_observation(value,original,{'position':100.0},1)
    except RuntimeError as error:assert str(error).startswith(reason),(case,str(error))
    else:raise AssertionError('Unsafe evidence accepted: '+case)
    rows.append(dict(case=case,status='PASS_EXPECTED_HOST_REFUSAL'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=dict(status='PASS_FIVE_SELECTED_PURE_RESUME_VALIDATOR_CONTROLS_ONLY',cases=rows,
    verifier_sha256=sha(HERE/'verify_tracking_android.py'),test_sha256=sha(Path(__file__)),
    selection_sha256=sha(HERE/'TRACKING-RESUME-GUARD-SELECTION.json'),application_execution=False,
    actual_player_callback_or_source_acceptance=False,prior17_rerun=False,prior40_rerun=False,Android='NOT_RUN')
(HERE/'TRACKING-RESUME-GUARD-HOST.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(receipt['status'])
