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
    for case in ['preclose','cancel','nested','inactive','exception','capacity','reuse','curl_result','stress']:
        folder=out/case
        run=subprocess.run([str(executable),case,str(folder)],capture_output=True,text=True,timeout=15)
        assert run.returncode==0,(case,run.stdout,run.stderr)
        data=(folder/'infinity-shutdown-native.jsonl').read_text()
        rows=[json.loads(l) for l in data.splitlines()]
        events=[r for r in rows if r.get('phase','').startswith('vfs.')]
        assert 'PRIVATE_URL_PASSWORD' not in data and 'https://' not in data
        for e in events:
            assert e['addon_id']=='plugin.video.playlistbrowser'
            if 'operation_id' in e:
                assert e['operation_id']==e['span_id']>0
                assert e['operation_start_monotonic_ns']<=e['monotonic_ns']
                assert e['backend_category'] and e['operation_stage'] and e['resource_category']
        if case in ('preclose','cancel'):
            request=next(e for e in events if e['phase']=='vfs.shutdown.request')
            returned=next(e for e in events if e['phase']=='vfs.open.return')
            retirement=next(e for e in events if e['phase']=='vfs.python.interpreter_retired')
            assert request['operation_id']==returned['operation_id']==retirement['operation_id']
            assert request['backend_category']=='curl' and request['operation_stage']=='curl_multi_poll'
            assert request['operation_start_monotonic_ns']<request['monotonic_ns']
            assert returned['outcome']=='false'
            assert returned['curl_cancel_callback_observed']==(1 if case=='cancel' else 0)
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
            assert [e['curl_cancel_callback_observed'] for e in returned]==[1,0]
            assert returned[0]['operation_id']!=returned[1]['operation_id']
        elif case=='curl_result':assert any(e['outcome']=='curl_result_code_28' for e in events)
        elif case=='stress':
            operations={e['operation_id']:e['operation_start_monotonic_ns'] for e in events if 'operation_id' in e}
            assert len(operations)==100
            assert all(operations[e['operation_id']]==e['operation_start_monotonic_ns'] for e in events if 'operation_id' in e)
        cases.append({'case':case,'passed':True,'events':len(events),'trace_sha256':hashlib.sha256(data.encode()).hexdigest()})
    result={'scope':'Exact observation headers with real concurrent host threads and append-only evidence; no Kodi backend execution or Galaxy Fold proof.',
            'cases':cases,'passed':True,'count':len(cases),'shutdown_corrected':False,
            'trace_header_sha256':hashlib.sha256((include/'InfinityVfsOpenTrace.h').read_bytes()).hexdigest(),
            'logger_header_sha256':hashlib.sha256((include/'InfinityShutdownTrace.h').read_bytes()).hexdigest()}
    (out/'VFS-TRACE-TESTS.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--include',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();verify(a.include,a.out)
