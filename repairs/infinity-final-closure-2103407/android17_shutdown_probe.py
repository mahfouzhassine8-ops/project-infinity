"""Independent original Power Close, real receipts, readback and three reopens.

Reuse the existing feature-only install/participant setup, then use the separate
retained shutdown transport. Nothing in a feature or packaging path imports or
calls this runner. Stop at the first failure and retain unavailable evidence.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import time

import android17_candidate_probe as candidate
from candidate_request import EXPECTED as CANDIDATE
from shutdown_request import AUTHORIZATION,EXPECTED

ROOT=Path(__file__).resolve().parents[2]
TRANSPORT=ROOT/'repairs/android-checkpoint-shutdown/runtime-tests/essential_android_probe.py'
BUCKETS=('items','watched','watchlist','collection','lists','sources','later','ratings','navigation_recovery')
FAVOURITE='Infinity final independent Close preservation'


def require(value,message):
    if not value:raise AssertionError(message)


def verify_receipt(receipt,owner):
    require(receipt.get('phase')=='COMPLETE','Actual Close did not complete: '+str(receipt.get('error','no terminal receipt')))
    require(receipt.get('pid')==owner['pid'] and receipt.get('owner')==owner['owner'],'Close PID/owner mismatch')
    require(all(receipt.get(k) is True for k in ('checkpoint_saved','authorization_consumed','process_death_confirmed')),'Missing save/authorization/death proof')
    require(receipt.get('exit_policy')=='essential_first_process_exit_v1','Unexpected termination policy')
    require(receipt.get('coordinator_termination_authorized') is True,'Coordinator termination not authorized')
    require(all(re.fullmatch(r'[0-9a-f-]{36}',receipt.get(k,'')) for k in ('engine_java_save_seal','coordinator_java_save_seal')),'Missing Java save seals')
    require(not receipt.get('engine_java_pending') and not receipt.get('coordinator_java_pending'),'Java save remains pending')
    native=receipt.get('native_receipt',{})
    require(native.get('pid')==owner['pid'] and native.get('owner')==owner['owner'],'Native receipt identity mismatch')
    require(isinstance(receipt.get('session'),str) and re.fullmatch(r'[0-9a-f-]{36}',receipt['session']) and native.get('session')==receipt['session'],'Native session mismatch')
    require(type(native.get('generation')) is int and native['generation']>0 and native.get('essential_write_generation')==native['generation'],'Native durable generation mismatch')
    require(native.get('admission_sealed') is True and native.get('inventory_complete') is True and native.get('blocker_count')==0 and not native.get('error'),'Native inventory/admission not complete')
    require(native.get('essential_writes_sealed') is True and native.get('essential_writes_durable') is True and native.get('essential_write_blockers')==[],'Essential writes not sealed/durable or blocked')
    owners=native.get('owners',[]);essential=native.get('essential_owners',[])
    require(len(owners)==17 and len(essential)==16 and len(set(essential))==16,'Essential owner inventory mismatch')
    mandatory=[x for x in owners if x.get('owner') in essential]
    require(len(mandatory)==16 and all(x.get('required_writes_finished') is True and not x.get('dirty_remaining') and x.get('result') in ('COMMITTED','ALREADY_DURABLE') for x in mandatory),'An essential owner did not finish durable writes')


def verify_records(before,after):
    for bucket in BUCKETS:
        require(before.get(bucket)==after.get(bucket),'Close/reopen changed protected bucket: '+bucket)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apk',type=Path,required=True)
    parser.add_argument('--expected-sha',required=True);parser.add_argument('--authorization',required=True)
    parser.add_argument('--out',type=Path,required=True);args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    require(args.authorization==AUTHORIZATION and args.expected_sha==CANDIDATE['candidate_apk_sha256'],'Exact independent shutdown selection required')
    report=dict(passed=False,scenario=EXPECTED['scenario'],apk_sha256=args.expected_sha,
        candidate_source_commit=CANDIDATE['candidate_source_commit'],test_source_commit=os.environ.get('GITHUB_SHA'),
        workflow_run=os.environ.get('GITHUB_RUN_ID'),cycles=[],physical_Fold='NOT RUN',release_accepted=False)
    save=lambda:(args.out/'INDEPENDENT-SHUTDOWN-RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
    spec=importlib.util.spec_from_file_location('retained_independent_close_transport',TRANSPORT)
    transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport)
    try:
        # The known-passing participant setup retains all fresh API37, original
        # signer/source, install-over, fixture identity and no-reset guards.
        setup=args.out/'participant-setup';previous=sys.argv
        try:
            sys.argv=[str(candidate.__file__),'--apk',str(args.apk),'--expected-sha',args.expected_sha,
                '--case','final-participant','--authorization',AUTHORIZATION,'--out',str(setup)]
            candidate.main(selected_case='final-participant')
        finally:sys.argv=previous
        startup=json.loads((setup/'FEATURE-RESULT.json').read_text())
        require(startup.get('passed') is True,'Actual native participant setup failed')
        require(startup.get('platform',{}).get('qemu')=='1' and startup['platform']['sdk']=='37','Fresh API37 required')
        transport.APP_UID=transport.shell('stat','-c','%u',transport.PRIVATE).strip()
        owner=startup['engine'];control=transport.CONTROL
        require(transport.rpc('Favourites.AddFavourite',dict(title=FAVOURITE,type='window',window='home'))=='OK','Could not add normal native test favourite')
        before=transport.read_json(transport.PROFILE+'/addon_data/script.infinity.commandcenter/continue-watching.json')
        require(isinstance(before.get('items'),dict) and before['items'],'Actual tracking fixture missing; no Close attempted')
        report['before_protected_records']=before
        for cycle in range(3):
            entry=dict(cycle=cycle,owner=owner,passed=False);report['cycles'].append(entry)
            folder=args.out/('cycle-'+str(cycle));folder.mkdir()
            active=transport.read_json(control+'/active.json');engine=transport.read_json(control+'/engine.json')
            require(active.get('pid')==engine.get('pid')==owner['pid'] and active.get('owner')==engine.get('owner')==owner['owner'] and active.get('status')=='ACTIVE','Reopen participant owner not active')
            entry['active']=active;entry['before_processes']=transport.processes();save()
            began=time.monotonic()
            entry['request']=transport.shell('am','start','-n',transport.PACKAGE+'/.InfinityPowerControlActivity','-a',transport.PACKAGE+'.action.CLOSE_KODI')
            receipt={};deadline=time.monotonic()+35
            while time.monotonic()<deadline:
                receipt=transport.read_json(transport.PRIVATE+'/files/infinity-checkpoint-close.json')
                if receipt.get('owner')==owner['owner'] and receipt.get('phase') in ('COMPLETE','CHECKPOINT_FAILED'):break
                time.sleep(.25)
            entry['close_seconds']=time.monotonic()-began;entry['receipt']=receipt;save()
            verify_receipt(receipt,owner)
            for _ in range(10):
                if not transport.processes():break
                time.sleep(.2)
            entry['after_processes']=transport.processes()
            require(not entry['after_processes'],'An application-UID process remained after authorized Close')
            after=transport.read_json(transport.PROFILE+'/addon_data/script.infinity.commandcenter/continue-watching.json')
            verify_records(before,after)
            transport.adb('pull',transport.PROFILE+'/Database',folder/'Database')
            databases=list((folder/'Database').glob('*.db'));require(databases,'No actual Kodi databases to verify')
            for database in databases:
                with sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True) as db:
                    require(db.execute('PRAGMA integrity_check').fetchone()==('ok',),'Database integrity failed: '+database.name)
            entry['database_integrity']=[p.name for p in databases]
            for leaf in ('request.json','response.json','participant.json','engine.json','active.json','compat-active.json'):
                transport.adb('pull',control+'/'+leaf,folder/leaf,check=False)
            entry['reopen_launch']=transport.shell('am','start','-W','-n',transport.PACKAGE+'/.Splash')
            def reopened():
                value=transport.read_json(transport.PRIVATE+'/files/infinity-kodi-process.json')
                resident=transport.read_json(control+'/active.json')
                return value if (value.get('phase')=='RUNNING' and value.get('owner')!=owner['owner'] and resident.get('owner')==value.get('owner') and resident.get('pid')==value.get('pid') and resident.get('status')=='ACTIVE') else None
            deadline=time.monotonic()+180;next_owner=None
            while time.monotonic()<deadline:
                next_owner=reopened()
                if next_owner:break
                time.sleep(.25)
            require(next_owner,'New native process/participant did not become ready')
            verify_records(before,transport.read_json(transport.PROFILE+'/addon_data/script.infinity.commandcenter/continue-watching.json'))
            transport.adb('forward','tcp:19090','tcp:9090')
            favourites=transport.rpc('Favourites.GetFavourites',{'properties':['window','windowparameter']})['favourites']
            require(any(row.get('title')==FAVOURITE for row in favourites),'Native favourite lost after reopening')
            entry.update(passed=True,reopened_owner=next_owner);owner=next_owner;save()
        report['passed']=True
    except BaseException as error:
        report['failure']=type(error).__name__+': '+str(error);report['traceback']=__import__('traceback').format_exc()
    finally:
        save()
        for source,name in [(transport.PRIVATE+'/files/infinity-checkpoint-close.json','actual-close-receipt.json'),
            (transport.PRIVATE+'/files/infinity-kodi-process.json','actual-engine.json'),
            (transport.PROFILE+'/../temp/kodi.log','kodi.log'),
            (transport.CONTROL+'/active.json','active.json'),(transport.CONTROL+'/compat-active.json','compat-active.json'),
            (transport.CONTROL+'/request.json','request.json'),(transport.CONTROL+'/response.json','response.json')]:
            try:transport.adb('pull',source,args.out/name,check=False)
            except Exception:pass
        try:(args.out/'logcat.txt').write_text(transport.adb('logcat','-d','-v','threadtime',check=False))
        except Exception:pass
    print(json.dumps(dict(passed=report['passed'],cycles_completed=sum(x['passed'] for x in report['cycles']),failure=report.get('failure'))))
    if not report['passed']:raise SystemExit(1)


if __name__=='__main__':main()
