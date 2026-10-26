"""Direct Home Search dispatch through the already-admitted test invoker."""
import json
from pathlib import Path
import shutil
from android17_reference_observation import OLD,FIXTURE_SHA
import hashlib
from android_stress_dispatcher import MAX_REQUESTS,ACTIONS

ADDON='service.future.persistence.7fa29'
BUILTIN='RunScript(script.infinity.commandcenter,universal-search,movie)'
TAIL="\nimport android_stress_dispatcher\nandroid_stress_dispatcher.serve(root,os.getpid())\n"
_context=None


def stage(folder,args,report,device,aid):
    from android17_candidate_probe import require_disposable
    require_disposable(device)
    if args.case not in ('final-search-all-enter','final-participant') or aid!=ADDON or Path(folder).resolve()!=args.out.resolve()/'fixture':
        raise ValueError('Only exact disposable Search stress stage permitted')
    raw=(OLD/'tracking/final-eight/android_selected.py').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=FIXTURE_SHA or raw.count(('xbmc.executebuiltin('+repr(BUILTIN)+')').encode())!=1:
        raise ValueError('Original Home Search builtin differs')
    target=Path(folder)/ADDON;service=target/'service.py'
    expected="import os,xbmcaddon,xbmcvfs\nfrom pathlib import Path\nimport android_selected\nroot=xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))\nPath(root).mkdir(parents=True,exist_ok=True)\nandroid_selected.run(root,str(os.getpid()),"+repr(args.case)+")\n"
    if service.is_symlink() or service.read_text()!=expected:raise ValueError('Exact original test service required')
    controller=target/'android_stress_dispatcher.py'
    if controller.exists() or controller.is_symlink():raise ValueError('Existing dispatcher refused')
    shutil.copyfile(Path(__file__).with_name(controller.name),controller)
    service.write_text(expected+TAIL)
    if service.read_text().replace(TAIL,'',1)!=expected:raise ValueError('Original test service changed')
    report['stress_script_bridge']=dict(addon=ADDON,builtin=BUILTIN,extra_invokers_per_request=0,
        existing_observer_only=True,production_changes=False)


def initialize(device,out,owner):
    global _context
    target=device.PROFILE+'/addon_data/'+ADDON
    def ready():
        value=device.read_json(target+'/stress-dispatch-ready.json')
        return value if value.get('pid')==owner['pid'] and value.get('max_requests')==MAX_REQUESTS and value.get('first_actual_feature_passed') is True and value.get('source')=='admitted-native-home-actions' and value.get('selected_mode') in ('final-search-all-enter','final-participant') else None
    admitted=device.until(ready,15)
    _context=dict(selected_mode=admitted['selected_mode'],out=Path(out),owner=owner,target=target,sequence=0)


def launch(device,action='home-search'):
    if _context is None:raise ValueError('Admitted existing dispatcher required')
    current=device.running_engine();owner=_context['owner']
    if not current or current.get('pid')!=owner['pid'] or current.get('owner')!=owner['owner']:
        raise ValueError('Actual dispatch process changed')
    if action not in ACTIONS:raise ValueError('Unknown fixed dispatcher action')
    if _context['selected_mode']=='final-participant' and action=='home-search':
        raise ValueError('Home-only admission does not select Search')
    _context['sequence']+=1;sequence=_context['sequence'];_context['action']=action
    if sequence>MAX_REQUESTS:raise ValueError('Dispatcher request budget exceeded')
    path=_context['out']/'dispatch-request.json'
    path.write_text(json.dumps(dict(pid=owner['pid'],sequence=sequence,action=action)))
    return device.adb('push',path,_context['target']+'/stress-open-request-'+str(owner['pid'])+'.json')


def verify_dispatch(device):
    if _context is None:raise ValueError('Dispatcher absent')
    ack=device.read_json(_context['target']+'/stress-dispatch-ack.json')
    if ack!={'pid':_context['owner']['pid'],'sequence':_context['sequence'],'action':_context['action']}:
        raise ValueError('Actual Home Search dispatch not acknowledged')
