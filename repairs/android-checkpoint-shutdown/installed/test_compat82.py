#!/usr/bin/env python3
"""Exercise the shipped 0.8.2 checkpoint: identity, parking and callback exclusion."""
import importlib.util,json,os,tempfile,threading,time
from pathlib import Path
SOURCE=Path(__file__).parent/'overlay/service.infinity.compat/checkpoint_runtime.py'
spec=importlib.util.spec_from_file_location('compat82',SOURCE);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
with tempfile.TemporaryDirectory() as name:
    root=Path(name);owner='00000000-0000-0000-0000-000000000001';session='00000000-0000-0000-0000-000000000002'
    engine=dict(schema=1,native_api=1,pid=os.getpid(),owner=owner)
    (root/'engine.json').write_text(json.dumps(engine))
    checkpoint=module.CompatCheckpoint(root)
    assert not checkpoint.poll()
    active=json.loads((root/'compat-active.json').read_text());assert active['addon_version']=='0.8.2' and active['global_safe_to_terminate'] is False
    request=dict(schema=1,pid=os.getpid(),owner='foreign-owner-000000',session=session,phase='PREPARE')
    (root/'request.json').write_text(json.dumps(request));assert not checkpoint.poll() and not (root/'compat-response.json').exists()
    request['owner']=owner;(root/'request.json').write_text(json.dumps(request))
    began=threading.Event();completed=threading.Event()
    def poll():
        began.set();checkpoint.poll();completed.set()
    with checkpoint.lock:
        thread=threading.Thread(target=poll);thread.start();assert began.wait(1)
        assert not completed.wait(.05), 'checkpoint passed an active publication callback'
    thread.join(2);assert completed.is_set() and checkpoint.parked
    response=json.loads((root/'compat-response.json').read_text())
    assert response['session']==session and response['owner']==owner and response['status']=='PARTICIPANT_COMPLETE'
    assert response['guard_frozen'] is True and response['global_safe_to_terminate'] is False
    assert all(op['ok'] for op in response['operations'])
    original=(root/'compat-response.json').read_bytes();assert checkpoint.poll() and (root/'compat-response.json').read_bytes()==original
    bad=module.CompatCheckpoint(root);request['session']='invalid';(root/'request.json').write_text(json.dumps(request))
    try:bad.poll()
    except ValueError:pass
    else:raise AssertionError('invalid current-owner request accepted')
    assert bad.parked
print('PASS actual compatibility 0.8.2: exact identity, foreign request, publication exclusion, parking, no termination authorization')
