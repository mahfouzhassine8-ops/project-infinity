"""Exercise exact trace/header code; host evidence, never a phone verdict."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import tempfile

HERE=Path(__file__).resolve().parent

def verify(include,out):
    out.mkdir(parents=True,exist_ok=True)
    executable=out/'trace-harness'
    subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-pthread',
                    '-I',str(include),str(HERE/'trace_harness.cpp'),'-o',str(executable)],check=True)
    cases=[]
    for case in ['preclose','cancel','nested','inactive','exception','capacity','reuse','curl_result','stale_cancel','stress',
                 'multiple_children','callback_after_return','native_preclose','cache_worker','support_unknown','history_gap','limits','native_scope_preclose']:
        folder=out/case
        run=subprocess.run([str(executable),case,str(folder)],capture_output=True,text=True,timeout=15)
        assert run.returncode==0,(case,run.stdout,run.stderr)
        data=(folder/'infinity-shutdown-native.jsonl').read_text()
        rows=[json.loads(l) for l in data.splitlines()]
        events=[r for r in rows if r.get('phase','').startswith('vfs.')]
        assert 'PRIVATE_URL_PASSWORD' not in data and 'https://' not in data
        for e in events:
            if e['invoker_id']==5:assert e['addon_id']=='plugin.video.playlistbrowser'
            if e.get('operation_id'):
                assert e['operation_id']==e['span_id']>0
                assert e['operation_start_monotonic_ns']<=e['monotonic_ns']
                assert e['backend_category'] and e['operation_stage'] and e['resource_category']
                assert e['operation_kind'] and e['cancellation_support']
                assert e['operation_start_monotonic_ns']<=e['stage_start_monotonic_ns']<=e['monotonic_ns']
                if e['phase']=='vfs.open.return':
                    assert e['operation_start_monotonic_ns']<=e['operation_end_monotonic_ns']<=e['monotonic_ns']
        if case in ('preclose','cancel'):
            request=next(e for e in events if e['phase']=='vfs.shutdown.request')
            returned=next(e for e in events if e['phase']=='vfs.open.return')
            retirement=next(e for e in events if e['phase']=='vfs.python.interpreter_retired')
            assert request['operation_id']==returned['operation_id']==retirement['operation_id']
            assert request['backend_category']=='curl' and request['operation_stage']=='curl_multi_poll'
            assert request['operation_start_monotonic_ns']<request['monotonic_ns']
            assert returned['outcome']=='false'
            assert returned['backend_cancel_callback_observed']==(1 if case=='cancel' else 0)
            assert not any(e['phase']=='vfs.open.start' for e in events)
        elif case=='nested':
            starts=[e for e in events if e['phase']=='vfs.open.start']
            assert len(starts)==2 and starts[1]['operation_parent_id']==starts[0]['operation_id']
            assert next(e for e in events if e['phase']=='vfs.python.interpreter_retired')['outcome']=='no_durability_receipt'
        elif case=='inactive':assert not events
        elif case=='exception':assert next(e for e in events if e['phase']=='vfs.open.return')['outcome']=='exception_unwound'
        elif case=='capacity':assert any(e['phase']=='vfs.capture_limit' for e in events)
        elif case=='reuse':
            returned=[e for e in events if e['phase']=='vfs.open.return']
            assert [e['backend_cancel_callback_observed'] for e in returned]==[1,0]
            assert returned[0]['operation_id']!=returned[1]['operation_id']
        elif case=='curl_result':assert any(e['outcome']=='curl_result_code_28' for e in events)
        elif case=='stale_cancel':assert not events
        elif case=='stress':
            operations={e['operation_id']:e['operation_start_monotonic_ns'] for e in events if 'operation_id' in e}
            assert len(operations)==100
            assert all(operations[e['operation_id']]==e['operation_start_monotonic_ns'] for e in events if 'operation_id' in e)
        elif case=='multiple_children':
            active=[e for e in events if e['phase']=='vfs.checkpoint.active_operation']
            assert len(active)==3 and {e['invoker_id'] for e in active}=={20,21,22}
            assert {e['addon_id'] for e in active}=={'plugin.video.seren','script.artistslideshow','plugin.video.themoviedb.helper'}
            assert len({e['operation_worker_tid'] for e in active})==3
            assert all(e['checkpoint_generation']==7 and e['operation_kind']=='CFile.Read' for e in active)
            assert not any(e['outcome']=='SAFE_TO_TERMINATE' for e in events)
            assert sum(e['phase']=='vfs.python.interpreter_retired' for e in events)==3
            assert any(e['cancellation_support']=='no_public_cancel_private_unknown' for e in active)
        elif case=='callback_after_return':
            returned=next(e for e in events if e['phase']=='vfs.open.return')
            callback=next(e for e in events if e['phase']=='vfs.backend.callback_return')
            assert callback['operation_id']==returned['operation_id']
            assert callback['outcome']=='callback_returned_operation_no_longer_active'
            assert returned['cancellation_outcome_bits']&8 and callback['cancellation_outcome_bits']&4
            assert callback['monotonic_ns']>=returned['operation_end_monotonic_ns']
        elif case=='native_preclose':
            active=next(e for e in events if e['phase']=='vfs.checkpoint.active_operation')
            assert active['invoker_id']==-1 and active['operation_kind']=='CFile.Stat' and active['backend_category']=='nfs'
            assert active['cancellation_support']=='no_generic_IFile_cancel_API'
            owners=[e for e in events if e['phase']=='vfs.checkpoint.owner']
            assert len(owners)==2 and owners[1]['outcome'].endswith('error_1_active_writes_1')
            assert next(e for e in events if e['phase']=='vfs.checkpoint.result')['outcome']=='CHECKPOINT_FAILED'
        elif case=='cache_worker':
            worker=next(e for e in events if e.get('operation_kind')=='CFileCache.Process' and e['phase']=='vfs.open.return')
            assert worker['operation_parent_id']>0 and worker['invoker_id']==5
            assert worker['cancellation_support']=='worker_StopThread_only' and worker['outcome']=='void_return'
        elif case=='support_unknown':
            assert all(e['cancellation_support']=='unobservable' for e in events)
        elif case=='history_gap':assert any(e['phase']=='vfs.history_gap' for e in events)
        elif case=='limits':
            critical=[json.loads(l) for l in (folder/'infinity-shutdown-native.jsonl.critical').read_text().splitlines()]
            assert any(e['phase']=='capture.event_limit' for e in critical)
            assert any(e['phase']=='checkpoint.result' for e in critical)
        elif case=='native_scope_preclose':
            active=next(e for e in events if e['phase']=='vfs.native.scope_pending')
            returned=next(e for e in events if e['phase']=='vfs.native.scope_return')
            assert active['operation_id']==returned['operation_id'] and active['backend_category']=='sqlite'
            assert active['target_thread']=='sqlite.commit' and returned['outcome']=='scope_returned_not_success'
            assert active['operation_start_monotonic_ns']<active['monotonic_ns']<=returned['operation_end_monotonic_ns']
        cases.append({'case':case,'passed':True,'events':len(events),'trace_sha256':hashlib.sha256(data.encode()).hexdigest()})
    result={'scope':'Exact observation headers with real concurrent host threads and append-only evidence; no Kodi backend execution or Galaxy Fold proof.',
            'cases':cases,'passed':True,'count':len(cases),'shutdown_corrected':False,
            'capabilities':{'backend_identity':True,'operation_timing':True,
              'cancellation_observation':True,'retirement_checkpoint_correlation':True},
            'trace_header_sha256':hashlib.sha256((include/'InfinityVfsOpenTrace.h').read_bytes()).hexdigest(),
            'logger_header_sha256':hashlib.sha256((include/'InfinityShutdownTrace.h').read_bytes()).hexdigest()}
    (out/'VFS-TRACE-TESTS.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--include',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();verify(a.include,a.out)
