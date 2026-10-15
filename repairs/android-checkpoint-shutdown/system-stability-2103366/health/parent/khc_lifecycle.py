"""Read-only operation scopes and checkpoint evidence; never authorizes termination."""
import hashlib
import json
import os
import re

OWNER_NAMES=set('native_admission,python_services,background_jobs,playback,command_center,compat,kodi_settings,profiles,skin_settings,addon_settings,favourites,peripherals,audio_policy,deferred_dialog_state,xml_files,native_databases,pvr'.split(','))

def scope(line):
    # A timestamp/thread/component alone cannot identify an add-on operation.
    ids=set(re.findall(r'\b(?:plugin|script|service|repository)\.[A-Za-z0-9_.-]+',str(line)))
    return next(iter(ids)) if len(ids)==1 else None

def marker_state(lines,failures,successes):
    failed={};succeeded={}
    for i,line in enumerate(lines or []):
        low=str(line).lower();owner=scope(line)
        if any(x in low for x in failures):failed[owner]=i
        if owner and any(x in low for x in successes):succeeded[owner]=i
    if not failed:return 'RECENT SUCCESS' if succeeded else 'NO RECENT MARKER'
    if any(owner is None or succeeded.get(owner,-1)<=index for owner,index in failed.items()):return 'REFRESH / AUTH FAILURE'
    return 'RECOVERED / SUCCESS AFTER ERROR'

def read_checkpoint(home):
    path=os.path.join(os.path.dirname(os.path.normpath(home)),'infinity-checkpoint-close.json')
    try:
        with open(path,'rb') as f:
            data=f.read(262145)
        if len(data)>262144:raise ValueError('oversize')
        return checkpoint_state(json.loads(data))
    except FileNotFoundError:return {'state':'UNAVAILABLE','active':False,'detail':'No checkpoint receipt available; shutdown is unverified.'}
    except (OSError,ValueError,TypeError):return {'state':'UNVERIFIED','active':True,'detail':'Checkpoint receipt could not be verified.'}

def require(value):
    if not value:raise ValueError("unconfirmed checkpoint")

def checkpoint_state(row):
    result={'state':'UNVERIFIED','active':True,'detail':'Latest checkpoint has no verified completion.'}
    if not isinstance(row,dict):return result
    phase=row.get('phase');result['phase']=phase;result['session']=row.get('session')
    if phase=='CHECKPOINT_FAILED':
        result.update(state='ACTIVE',detail=str(row.get('error') or 'Checkpoint failed'))
        return result
    if phase!='COMPLETE':return result
    try:
        raw=row['native_json'];native=json.loads(raw)
        require(row['schema']==1 and native['schema']==1)
        require(type(row['pid']) is int and row['pid']>0)
        require(type(row['generation']) is int)
        require(all(isinstance(row[k],str) and re.fullmatch(r'[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}',row[k]) for k in ('session','owner')))
        require(row['checkpoint_saved'] is True and row['authorization_consumed'] is True)
        require(row['engine_death_epoch_ms']>0 and row['engine_death_elapsed_ms']>0)
        require(row['native_proof_sha256']==hashlib.sha256(raw.encode()).hexdigest())
        require(native==row['native_receipt'] and native['phase']=='SAFE_TO_TERMINATE')
        require(native['admission_sealed'] is True and native['active_native_writers']==0)
        require(native['required_jobs']==0 and native['unknown_job_owners']==0)
        require(native['blocker_count']==0 and native['blocker_overflow'] is False and not native['error'])
        require(native['script_persistence']['durable'] is True and native['script_persistence']['blocking_count']==0 and native['script_persistence']['blocking_overflow'] is False)
        require(native['generation']==row['generation'] and row['generation']>0)
        require(all(native[k]==row[k] for k in ('session','owner','pid')))
        require(set(native['required_owners'])==OWNER_NAMES and len(native['required_owners'])==len(OWNER_NAMES))
        require(len(native['owners'])==len(OWNER_NAMES))
        require({x['owner'] for x in native['owners']}==OWNER_NAMES)
        for x in native['owners']:
            require(x['required_writes_finished'] is True and x['dirty'] is False and x['dirty_remaining'] is False)
            require(x['checkpoint_generation']==native['generation'])
            require(x['generation']==x['durable_generation'] and x['generation']>=0)
            require(x['result']==('COMMITTED' if x['dirty_before'] else 'ALREADY_DURABLE'))
    except (KeyError,ValueError,TypeError,AssertionError):return result
    result.update(state='RESOLVED',active=False,detail='Latest normal close saved every required owner, consumed authorization and verified native process death. Earlier evidence remains historical.')
    return result
