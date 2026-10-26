"""Bounded test-only dispatcher in the existing admitted observation invoker."""
import json
from pathlib import Path
import time

BUILTIN='RunScript(script.infinity.commandcenter,universal-search,movie)'
MAX_REQUESTS=110
LIFETIME_SECONDS=90*60
ACTIONS=frozenset(('home-search','home-resume-movie','home-resume-tv'))


def require_ready(value,pid):
    if (value.get('passed') is not True or value.get('pid')!=pid or
            value.get('selected_mode') not in ('final-search-all-enter','final-participant')):
        raise ValueError('Actual selected feature must pass before dispatch')
    return value['selected_mode']


def accept(value,pid,sequence):
    return (set(value)=={'pid','sequence','action'} and type(value.get('pid')) is int and
            value['pid']==pid and type(value.get('sequence')) is int and
            value['sequence']==sequence and 1<=sequence<=MAX_REQUESTS and value.get('action') in ACTIONS)


def select_resume_tab(media):
    import xbmc
    import xbmcgui
    if media not in ('movie','tv'):raise ValueError('Unknown fixed Home tab')
    if xbmcgui.getCurrentWindowId()!=10000:raise ValueError('Actual Home required before selecting resume tab')
    wanted='movies' if media=='movie' else 'tvshows'
    count=int(xbmc.getInfoLabel('Container(9000).NumItems') or 0)
    if not 1<=count<=50:raise ValueError('Actual bounded Home tabs unavailable')
    for index in range(count):
        xbmc.executebuiltin('SetFocus(9000,%d,absolute)'%index,True)
        if xbmc.getInfoLabel('Container(9000).ListItem.Property(section)')==wanted:
            return
    raise ValueError('Actual requested Home tab not found')


def serve(root,pid):
    import xbmc
    root=Path(root);pid=int(pid)
    if root.is_symlink():raise ValueError('Linked fixture refused')
    ready=root/('navigation-ready-'+str(pid)+'.json')
    mode=require_ready(json.loads(ready.read_text()),pid)
    def output(name,value):
        path=root/name
        if path.is_symlink():raise ValueError('Linked dispatcher file refused')
        pending=path.with_suffix('.tmp');pending.write_text(json.dumps(value));pending.replace(path)
    output('stress-dispatch-ready.json',dict(pid=pid,max_requests=MAX_REQUESTS,source='admitted-native-home-actions',selected_mode=mode,first_actual_feature_passed=True))
    request=root/('stress-open-request-'+str(pid)+'.json');monitor=xbmc.Monitor();sequence=1
    deadline=time.monotonic()+LIFETIME_SECONDS
    while sequence<=MAX_REQUESTS and time.monotonic()<deadline and not monitor.abortRequested():
        if request.exists():
            if request.is_symlink() or request.stat().st_size>4096:raise ValueError('Invalid dispatcher request file')
            try:value=json.loads(request.read_text())
            except ValueError:value={}
            if accept(value,pid,sequence):
                if mode=='final-participant' and value['action']=='home-search':
                    raise ValueError('Home-only admission does not select Search')
                # Same Home builtin as the retained original selected case.
                if value['action']=='home-search':xbmc.executebuiltin(BUILTIN)
                else:select_resume_tab('movie' if value['action']=='home-resume-movie' else 'tv')
                output('stress-dispatch-ack.json',dict(pid=pid,sequence=sequence,action=value['action']))
                sequence+=1
        monitor.waitForAbort(.1)
