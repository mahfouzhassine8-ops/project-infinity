"""Verify retention under post-Close floods, including the existing 2 MiB export."""
from pathlib import Path
import argparse,json,subprocess,hashlib
HERE=Path(__file__).resolve().parent
def verify(include,out):
    out.mkdir(parents=True,exist_ok=True);exe=out/'overflow-harness'
    subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-pthread','-O2',
                    '-I',str(include),str(HERE/'overflow_harness.cpp'),'-o',str(exe)],check=True)
    cases=[]
    for test in ['late_after_noise','lanes_independent','native_slow_after_noise']:
        folder=out/test
        subprocess.run([str(exe),test,str(folder)],check=True,timeout=45)
        path=folder/'infinity-shutdown-native.jsonl.critical';data=path.read_bytes()
        assert len(data)<2*1024*1024,'Existing exporter would truncate terminal evidence'
        rows=[json.loads(line) for line in data.decode().splitlines()]
        if test=='late_after_noise':
            assert any(r.get('phase')=='capture.lane_limit' for r in rows)
            assert any(r.get('phase')=='vfs.backend.callback_return' for r in rows)
            returned=next(r for r in rows if r.get('phase')=='vfs.shutdown_operation_return')
            assert returned['backend_category']=='curl' and returned['outcome']=='false'
            assert returned['cancellation_outcome_bits']&8
            assert any(r.get('phase')=='vfs.python.interpreter_retired' and r['outcome']=='no_durability_receipt' for r in rows)
            assert any(r.get('phase')=='vfs.checkpoint.result' and r['outcome']=='CHECKPOINT_FAILED' for r in rows)
            assert any(r.get('phase')=='vfs.checkpoint.owner' and r['target_thread']=='native_databases' for r in rows)
            assert any(r.get('phase')=='vfs.diagnostic.fast_scope_summary' for r in rows)
            assert not any(r.get('outcome')=='SAFE_TO_TERMINATE' for r in rows)
        elif test=='lanes_independent':
            limits=[r for r in rows if r.get('phase')=='capture.lane_limit']
            assert len(limits)==6 and {r['lane'] for r in limits}==set(range(6))
        else:
            pending=next(r for r in rows if r.get('phase')=='vfs.native.scope_pending')
            returned=next(r for r in rows if r.get('phase')=='vfs.native.scope_return')
            assert pending['operation_id']==returned['operation_id'] and returned['backend_category']=='sqlite'
            assert returned['operation_end_monotonic_ns']>returned['operation_start_monotonic_ns']
        cases.append({'case':test,'passed':True,'critical_bytes':len(data),
                      'trace_sha256':hashlib.sha256(data).hexdigest()})
    receipt={'passed':True,'count':len(cases),'cases':cases,'existing_export_cap_bytes':2*1024*1024,
      'shutdown_timeouts_changed':False,'shutdown_repaired':False,'host_evidence_only':True}
    (out/'OVERFLOW-VERIFICATION.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--include',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();verify(a.include,a.out)
