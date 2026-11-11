"""Validate observed native stages against actual Android Python reply threads.

No simulated success, lifecycle changes, or claim of NULL-path injection.
Worker request IDs are thread-local; use native TID/invoker/monotonic time.
"""
import re

ROW=re.compile(r'InfinityStartupTrace stage=([a-z_.]+) request=(\d+) invoker=(-?\d+) tid=(\d+) us=(\d+) value=(-?\d+) flags=(\d+) tracked=(\d+)')

def verify(log,cases):
    rows=[]
    for line in log.splitlines():
        if 'InfinityStartupTrace stage=' not in line:continue
        match=ROW.search(line);assert match,'Malformed native event'
        value=match.groups();row=dict(zip(('request','invoker','tid','us','value','flags','tracked'),map(int,value[1:])))
        row['stage']=value[0];rows.append(row)
    assert rows and not any(r['stage']=='trace.overflow' for r in rows),'Native trace absent or incomplete'
    assert any(r['stage']=='runtime.initialized' for r in rows),'No actual native runtime initialization'
    required=('execute.enter','handler.ready','gil.acquired','interpreter.created','kodi.initialized','observer.returned','bytecode.enter')
    result=[]
    for case in cases:
        assert case['python_version']==[3,11,7],'Actual embedded CPython differs from source-bound failure proof'
        tid=case['native_tid'];entered=case['body_enter_us']
        starts=[r for r in rows if r['tid']==tid and r['stage']=='bytecode.enter' and r['us']<=entered]
        assert len(starts)==1,'Missing or ambiguous observed invocation'
        invoker=starts[0]['invoker'];assert invoker>=0
        actual=[r for r in rows if r['tid']==tid and r['invoker']==invoker]
        stamps=[]
        for stage in required:
            found=[r for r in actual if r['stage']==stage and r['us']<=entered]
            assert len(found)==1,'Missing or ambiguous native stage: '+stage
            stamps.append(found[0]['us'])
        assert stamps==sorted(stamps),'Native initialization sequence out of order'
        returned=[r for r in actual if r['stage']=='bytecode.returned' and r['us']>=entered]
        finished=[r for r in actual if r['stage']=='execution.finished' and r['us']>=entered]
        assert len(returned)==len(finished)==1 and returned[0]['us']<=finished[0]['us'],'Selected body has not returned through native execution'
        result.append(dict(action=case['action'],sequence=case['sequence'],tid=tid,invoker=invoker,
                           body_enter_us=entered,observed_stages=list(required)+['bytecode.returned','execution.finished'],
                           native_return_value=returned[0]['value'],native_finished_value=finished[0]['value']))
    assert any(r['stage']=='builtin.result' and r['value']>=0 for r in rows),'No successful actual RunScript admission observed'
    return dict(status='PASS_OBSERVED_ANDROID_NATIVE_INITIALIZATION_AND_SELECTED_BODY_EXECUTION',event_count=len(rows),cases=result,
                builtin_results=[{k:r[k] for k in ('request','invoker','value','us')} for r in rows if r['stage']=='builtin.result'],
                builtin_individual_addon_attribution='Not claimed; events deliberately exclude add-on paths and arguments',
                Android_NULL_path='NOT_INJECTED',Fold_cause_established=False)
