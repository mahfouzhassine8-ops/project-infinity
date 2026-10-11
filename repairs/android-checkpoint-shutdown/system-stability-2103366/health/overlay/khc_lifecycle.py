"""Read-only operation scopes and checkpoint evidence; never authorizes termination."""
import hashlib
import json
import os
import re
import time

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
        # A positive marker must never override a failure on the same line.
        negative = re.search(r'\b(?:failed?|failure|unauthori[sz]ed|invalid|denied|error|expired|unsuccessful|cannot|couldn.t|not|not\s+(?:authorized|authenticated))\b', low)
        if owner and not negative and not any(x in low for x in failures) and any(x in low for x in successes):succeeded[owner]=i
    if not failed:return 'RECENT SUCCESS' if succeeded else 'NO RECENT MARKER'
    if any(owner is None or succeeded.get(owner,-1)<=index for owner,index in failed.items()):return 'REFRESH / AUTH FAILURE'
    return 'RECOVERED / SUCCESS AFTER ERROR'

def read_checkpoint(home):
    root=os.path.dirname(os.path.realpath(home))
    path=os.path.join(root,'infinity-checkpoint-close.json')
    try:
        if os.path.realpath(path)!=path:raise ValueError('linked receipt')
        with open(path,'rb') as f:
            data=f.read(262145)
        if len(data)>262144:raise ValueError('oversize')
        row=json.loads(data);require(isinstance(row,dict));result=checkpoint_state(row)
        metadata=os.path.join(root,'infinity-checkpoint-mirror.json')
        if os.path.realpath(metadata)!=metadata:raise ValueError('linked provenance')
        with open(metadata,'rb') as f:raw=f.read(8193)
        if len(raw)>8192:raise ValueError('oversize provenance')
        mirror=json.loads(raw);require(isinstance(mirror,dict))
        require(type(mirror['schema']) is int and mirror['schema']==1 and mirror['read_only'] is True)
        require(mirror['source']=='private-coordinator-receipt')
        require(mirror['receipt_sha256']==hashlib.sha256(data).hexdigest())
        require(mirror['session']==row.get('session','') and mirror['receipt_pid']==row.get('pid',0) and mirror['phase']==row.get('phase',''))
        require(mirror['publication'] in ('startup_snapshot','coordinator_write'))
        require(all(type(mirror[k]) is int and mirror[k]>0 for k in ('captured_epoch_ms','source_modified_epoch_ms','collector_pid')))
        now=int(time.time()*1000);require(mirror['captured_epoch_ms']<=now+60000)
        result.update(receipt_epoch_ms=row.get('engine_death_epoch_ms') or row.get('started_epoch_ms'),
                      mirror_captured_epoch_ms=mirror['captured_epoch_ms'],
                      freshness='CURRENT_PUBLICATION' if mirror['publication']=='coordinator_write' and now-mirror['captured_epoch_ms']<=86400000 else 'SAVED_RECEIPT',
                      current_process_health='UNVERIFIED')
        return result
    except FileNotFoundError:return {'state':'UNAVAILABLE','active':False,'current_process_health':'UNVERIFIED','detail':'Current receipt/provenance unavailable; shutdown is unverified.'}
    except (OSError,ValueError,TypeError,KeyError):return {'state':'UNVERIFIED','active':True,'current_process_health':'UNVERIFIED','detail':'Checkpoint receipt/provenance could not be verified.'}

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
        require(type(row['schema']) is int and row['schema']==1 and type(native['schema']) is int and native['schema']==1)
        require(type(row['pid']) is int and row['pid']>0)
        require(type(row['generation']) is int)
        require(all(isinstance(row[k],str) and re.fullmatch(r'[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}',row[k]) for k in ('session','owner')))
        require(row['checkpoint_saved'] is True and row['authorization_consumed'] is True)
        # Mirror Android confirmedComplete's ordered monotonic milestones.
        times = [row[k] for k in ('started_elapsed_ms', 'safe_elapsed_ms',
            'terminate_requested_elapsed_ms', 'authorization_consumed_elapsed_ms', 'engine_death_elapsed_ms')]
        require(all(type(x) is int for x in times) and times[0] >= 0)
        require(all(x > 0 for x in times[1:]) and times == sorted(times))
        require(all(type(row[k]) is int and row[k] > 0 for k in
            ('safe_epoch_ms', 'authorization_consumed_epoch_ms', 'engine_death_epoch_ms')))
        epochs=[row[k] for k in ('safe_epoch_ms','authorization_consumed_epoch_ms','engine_death_epoch_ms')]
        require(epochs==sorted(epochs))
        require(row['native_proof_sha256']==hashlib.sha256(raw.encode()).hexdigest())
        require(native==row['native_receipt'] and native['phase']=='SAFE_TO_TERMINATE')
        require(native['admission_sealed'] is True and native['active_native_writers']==0)
        require(native['required_jobs']==0 and native['unknown_job_owners']==0)
        require(native['blocker_count']==0 and native['blocker_overflow'] is False and not native['error'])
        require(not row.get('error') and not native.get('errors', 0))
        require(native['script_persistence']['durable'] is True and native['script_persistence']['blocking_count']==0 and native['script_persistence']['blocking_overflow'] is False)
        require(native['generation']==row['generation'] and row['generation']>0)
        require(all(native[k]==row[k] for k in ('session','owner','pid')))
        require(set(native['required_owners'])==OWNER_NAMES and len(native['required_owners'])==len(OWNER_NAMES))
        require(len(native['owners'])==len(OWNER_NAMES))
        require({x['owner'] for x in native['owners']}==OWNER_NAMES)
        for x in native['owners']:
            require(not x.get('error') and not x.get('errors', 0))
            require(x['required_writes_finished'] is True and x['dirty'] is False and x['dirty_remaining'] is False)
            require(x['checkpoint_generation']==native['generation'])
            require(x['generation']==x['durable_generation'] and x['generation']>=0)
            require(x['result']==('COMMITTED' if x['dirty_before'] else 'ALREADY_DURABLE'))
    except (KeyError,ValueError,TypeError,AssertionError):return result
    result.update(state='RESOLVED',active=False,evidence_scope='previous_close',current_process_health='UNVERIFIED',detail='Latest normal close saved every required owner, consumed authorization and verified native process death. Earlier evidence remains historical.')
    return result
