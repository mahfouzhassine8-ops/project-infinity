"""Bounded test-only dispatcher in the existing admitted observation invoker."""
import json
from pathlib import Path
import time

BUILTIN='RunScript(script.infinity.commandcenter,universal-search,movie)'
MAX_REQUESTS=55
LIFETIME_SECONDS=90*60


def require_ready(value,pid):
    if (value.get('passed') is not True or value.get('pid')!=pid or
            value.get('selected_mode')!='final-search-all-enter'):
        raise ValueError('Original actual Search must pass before dispatch')


def accept(value,pid,sequence):
    return (set(value)=={'pid','sequence','action'} and type(value.get('pid')) is int and
            value['pid']==pid and type(value.get('sequence')) is int and
            value['sequence']==sequence and 1<=sequence<=MAX_REQUESTS and value.get('action')=='home-search')


def serve(root,pid):
    import xbmc
    root=Path(root);pid=int(pid)
    if root.is_symlink():raise ValueError('Linked fixture refused')
    ready=root/('navigation-ready-'+str(pid)+'.json')
    require_ready(json.loads(ready.read_text()),pid)
    def output(name,value):
        path=root/name
        if path.is_symlink():raise ValueError('Linked dispatcher file refused')
        pending=path.with_suffix('.tmp');pending.write_text(json.dumps(value));pending.replace(path)
    output('stress-dispatch-ready.json',dict(pid=pid,max_requests=MAX_REQUESTS,source='exact-home-search',first_actual_feature_passed=True))
    request=root/('stress-open-request-'+str(pid)+'.json');monitor=xbmc.Monitor();sequence=1
    deadline=time.monotonic()+LIFETIME_SECONDS
    while sequence<=MAX_REQUESTS and time.monotonic()<deadline and not monitor.abortRequested():
        if request.exists():
            if request.is_symlink() or request.stat().st_size>4096:raise ValueError('Invalid dispatcher request file')
            try:value=json.loads(request.read_text())
            except ValueError:value={}
            if accept(value,pid,sequence):
                # Same Home builtin as the retained original selected case.
                xbmc.executebuiltin(BUILTIN)
                output('stress-dispatch-ack.json',dict(pid=pid,sequence=sequence,action='home-search'))
                sequence+=1
        monitor.waitForAbort(.1)
