"""Close historical original-key signing routes without editing locked refs."""
import argparse,json,subprocess
from pathlib import Path
from inventory import HERE,load,save
from release_gate import require

REPO='mahfouzhassine8-ops/project-infinity'

def api(path,method='GET'):
    result=subprocess.check_output(['gh','api','--method',method,'repos/'+REPO+'/'+path],text=True)
    return json.loads(result) if result.strip() else None

def workflows():
    rows=[];page=1
    while True:
        data=api('actions/workflows?per_page=100&page='+str(page))['workflows'];rows.extend(data)
        if len(data)<100:return {r['id']:r for r in rows}
        page+=1

def check(policy):
    actual=workflows()
    for row in policy['retired_original_key_workflows']:
        require(row['id'] in actual and actual[row['id']]['state']!='active','LEGACY_SIGNER_ACTIVE:'+row['path'])
    require(actual[policy['sole_original_key_workflow_id']]['state']=='active','COMBINED_SIGNER_DISABLED')
    known=set(policy['reviewed_workflow_ids'])
    require(not [i for i,r in actual.items() if r['state']=='active' and i not in known],'UNREVIEWED_NEW_WORKFLOW')
    retired={r['id'] for r in policy['retired_original_key_workflows']}
    for state in ('queued','in_progress','waiting'):
        data=api('actions/runs?per_page=100&status='+state)['workflow_runs']
        require(not [r for r in data if r['workflow_id'] in retired],'LEGACY_SIGNER_STILL_RUNNING')
    return {'status':'ONLY_REVIEWED_COMBINED_ORIGINAL_KEY_ROUTE_ACTIVE',
            'retired_original_key_workflows':len(retired),'locked_branch_edited':False}

def retire(policy):
    actual=workflows();done=0
    for row in policy['retired_original_key_workflows']:
        if actual[row['id']]['state']=='active':api('actions/workflows/'+str(row['id'])+'/disable','PUT')
        done+=1
        if done%50==0:print('Retired original-key workflows:',done,flush=True)
    return check(policy)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['check','retire'])
    p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    save(args.out,(check if args.command=='check' else retire)(load(HERE/'signer-policy.json')))
