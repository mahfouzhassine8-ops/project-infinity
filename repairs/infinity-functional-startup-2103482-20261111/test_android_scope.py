"""Focused workflow preservation and selected-test admission; no device execution."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import yaml

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
WORKFLOW='.github/workflows/infinity-saved-navigation-android.yml'
old=yaml.load(subprocess.check_output(['git','show','93d025b6:'+WORKFLOW],cwd=ROOT,text=True),Loader=yaml.BaseLoader)
new=yaml.load((ROOT/WORKFLOW).read_text(),Loader=yaml.BaseLoader)
feature='startup82-local-python'
assert new['on']['push']==old['on']['push']
assert new['on']['workflow_dispatch']['inputs']['feature']['options']==old['on']['workflow_dispatch']['inputs']['feature']['options']+[feature,'startup-internal-qa']
before=old['jobs'];after=new['jobs']
assert set(after)-set(before)=={'selected-startup82-local-python','selected-startup-internal-qa'}
for name,job in before.items():
    expected=dict(job)
    if name=='android17':expected['if']="inputs.feature != 'startup-internal-qa' && inputs.feature != 'startup82-local-python' && "+expected['if']
    assert after[name]==expected,'Unrelated workflow job changed: '+name
job=after['selected-startup82-local-python']
assert job['if']=="github.event_name == 'workflow_dispatch' && inputs.feature == 'startup82-local-python' && github.ref == 'refs/heads/work/infinity-2103482-functional-startup-20261111'"
assert not any(k in job for k in ('needs','strategy','continue-on-error'))
assert new['permissions']==old['permissions']=={'contents':'read','actions':'read'}
for step in job['steps']:
    assert 'continue-on-error' not in step
    if "python - <<'PY'\n" in step.get('run',''):
        ast.parse(step['run'].split("python - <<'PY'\n",1)[1].split('\nPY',1)[0])
candidate=after['selected-startup-internal-qa']
assert candidate['if']==job['if'].replace("'startup82-local-python'","'startup-internal-qa'")
assert candidate['strategy']=={'fail-fast':'false','matrix':{'include':[{'cold_start':'1','network':'normal'},{'cold_start':'2','network':'offline'}]}}
assert candidate['env']['STARTUP_NETWORK_CASE']=='${{ matrix.network }}'
assert 'needs' not in candidate and 'continue-on-error' not in candidate
for step in candidate['steps']:
    assert 'continue-on-error' not in step
    for marker in ('PY','PYQA'):
        token="python - <<'"+marker+"'\n"
        if token in step.get('run',''):ast.parse(step['run'].split(token,1)[1].split('\n'+marker,1)[0])
spec=importlib.util.spec_from_file_location('startup_qa',HERE/'android_startup_probe.py')
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
selection=probe.selected();ast.parse(probe.OBSERVER)
for name in ('android_internal_qa.py','verify_android_native_trace.py'):ast.parse((HERE/name).read_text())
source=(HERE/'android_startup_probe.py').read_text()
for forbidden in ('force-stop','pm clear','Application.Quit','Quit()','Shutdown()','Player.Stop','stop_once','base.run('):
    assert forbidden not in source,forbidden
assert 'Startup' not in probe.Device.METHODS and 'Application.Quit' not in probe.Device.METHODS
proof=dict(status='PASS_SELECTED_SCOPE_AND_UNCHANGED_OTHER_WORKFLOW_JOBS_ONLY',
    application_executed=False,legacy_policy_test='NOT_EXECUTED_IMPORT_BLOCKED; historical single-job assertions predate current workflow; no alteration to old test',
    selected_feature=feature,candidate_feature='startup-internal-qa',candidate_application_executed=False,
    candidate_scope='Two independent fresh-VM cold starts, normal/offline; normal shell disables VM Wi-Fi/data with actual no-default-network check. Unlaunched82 install-over and synthetic sentinel only; no shutdown/reopen or owner-profile claim',
    protected_jobs=len(before),shutdown_selected=False,
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/WORKFLOW,HERE/'android_startup_probe.py',HERE/'ANDROID-STARTUP-SELECTION.json',HERE/'android_internal_qa.py',HERE/'verify_android_native_trace.py')})
(HERE/'ANDROID-SCOPE-HOST.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof,indent=2))
