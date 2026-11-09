import copy,hashlib,importlib.util,json,os,subprocess
from pathlib import Path
from unittest.mock import patch
import yaml
root=Path('/workspace/infinity-tracking-integration');task=root/'repairs/infinity-tracking-integration-2103469-20261108'
spec=importlib.util.spec_from_file_location('fixture_guard',task/'tracking_module_fixture.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
real_load=f.load;real_git=f.git;request=real_load(f.REQUEST);head=real_git('rev-parse','HEAD').decode().strip()
state={'request':request,'authority':f.AUTHORITY,'baseline':'success'}
def local_load(path):return state['request'] if Path(path)==f.REQUEST else real_load(path)
def local_git(*args):return b'' if args[0]=='status' else real_git(*args)
def api(path):
 if path=='actions/runs/999':return dict(head_sha=head,workflow_id=397702717,path=f.WORKFLOW)
 if path=='git/ref/heads/work/infinity-2103460-nine-corrections-20261106':return {'object':{'sha':state['authority']}}
 if path=='git/ref/heads/locks/infinity-2103469-protected-recovery-20261108':return {'object':{'sha':f.AUTHORITY}}
 if path=='actions/runs/42542862696':return dict(workflow_id=393886994,head_sha='3d32dfa90510011701c11c49a763774ce3428200',status='completed',conclusion=state['baseline'])
 raise AssertionError(path)
env=dict(GITHUB_ACTIONS='true',GITHUB_REPOSITORY=f.REPO,GITHUB_REF='refs/heads/'+f.BRANCH,GITHUB_SHA=head,GITHUB_RUN_ID='999')
cases=[]
with patch.dict(os.environ,env),patch.object(f,'load',local_load),patch.object(f,'git',local_git),patch.object(f,'api',api):
 f.check_sources();cases.append(dict(case='bound_actual_files_and_unchanged_original_workflow_jobs',status='PASS_HOST_GUARD_ONLY'))
 controls=[('wrong_branch','EXACT_AUTHORIZED_INTERNAL_BRANCH'),('missing_binding','EXACT_MANDATORY_SOURCE_BINDING_SET'),('changed_binding','FROZEN_REVIEWED_INPUT:'),('APK_build','MODULE_FIXTURE_ONLY'),('authority_advanced','LIVE_VERSION_AUTHORITY_ADVANCED'),('baseline_failed','ACTUAL_UNCHANGED69_API36_STARTUP_PASS')]
 for case,want in controls:
  state.update(request=copy.deepcopy(request),authority=f.AUTHORITY,baseline='success');os.environ.update(env)
  if case=='wrong_branch':os.environ['GITHUB_REF']='refs/heads/unselected'
  if case=='missing_binding':state['request']['source_bindings'].pop(next(iter(state['request']['source_bindings'])))
  if case=='changed_binding':state['request']['source_bindings'][next(iter(state['request']['source_bindings']))]='0'*64
  if case=='APK_build':state['request']['APK_build']=True
  if case=='authority_advanced':state['authority']='0'*40
  if case=='baseline_failed':state['baseline']='failure'
  try:f.check_sources()
  except RuntimeError as e:assert str(e).startswith(want),(case,str(e),want)
  else:raise AssertionError('Guard accepted '+case)
  cases.append(dict(case=case,status='PASS_EXPECTED_HOST_REFUSAL'))
w=yaml.safe_load((root/f.WORKFLOW).read_text());condition=w['jobs']['prepare-tracking-modules']['if']
values={'github.repository':f.REPO,'github.ref':'refs/heads/'+f.BRANCH,'github.event_name':'push','github.event.head_commit.message':'Prepare tracking modules: selected','inputs.operation':''}
def selected(values):
 expression=condition
 for k,v in sorted(values.items(),key=lambda kv:-len(kv[0])):expression=expression.replace(k,repr(v))
 expression=expression.replace('&&',' and ').replace('||',' or ')
 return eval(expression,{'__builtins__':{}},{'startsWith':lambda s,p:s.startswith(p)})
for name,changes,want in [('selected_push',{},True),('unselected_prefix',{'github.event.head_commit.message':'Record evidence'},False),('wrong_branch',{'github.ref':'refs/heads/elsewhere'},False),('wrong_repo',{'github.repository':'elsewhere/repo'},False),('selected_manual',{'github.event_name':'workflow_dispatch','inputs.operation':'prepare-tracking-modules'},True),('wrong_manual',{'github.event_name':'workflow_dispatch','inputs.operation':'final-combined'},False)]:
 v=dict(values,**changes);assert selected(v) is want,name;cases.append(dict(case=name,status='PASS_HOST_ROUTING_ONLY'))
receipt=dict(status='PASS_SELECTED_MODULE_SOURCE_AND_ROUTING_HOST_GUARDS_ONLY',cases=cases,application_execution=False,signing=False,CI_admission=False,scope='Live API responses and clean CI status simulated for guard controls only; actual CI must independently enforce them. Actual bound file hashes and original workflow prefix checked.',source_hashes={n:hashlib.sha256((task/n).read_bytes()).hexdigest() for n in ('tracking_module_fixture.py','prepare_tracking_release.py','verify_tracking_modules.py')},workflow_sha256=hashlib.sha256((root/f.WORKFLOW).read_bytes()).hexdigest(),selection_sha256=hashlib.sha256((task/'MODULE-GUARD-SELECTION.json').read_bytes()).hexdigest(),test_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),original40_rerun=False)
(task/'MODULE-GUARD-HOST.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(receipt['status'],len(cases),'selected checks')
