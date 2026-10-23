"""Stage ONLY the Infinity Save for Later hook and its exact identity contracts."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import shutil

HERE=Path(__file__).resolve().parent
PLUGIN_SHA='47ce816e00ca30d8eb77ea4d6e034bdbd40b2a5d6c51bfd4eda8d6c75545edb8'
PARENT_VERSIONS={'script.infinity.commandcenter':('0.3.5.29','0.3.5.31'),
          'script.infinity.watchedbridge':('1.0.10','1.0.12'),
          'script.infinity.uirepair':('0.1.12','0.1.14')}

VERSIONS={k:(v[0], {'script.infinity.commandcenter':'0.3.5.32', 'script.infinity.watchedbridge':'1.0.13', 'script.infinity.uirepair':'0.1.15'}[k]) for k,v in PARENT_VERSIONS.items()}

def once(source,before,after):
    if source.count(before)!=1:raise RuntimeError('Plugin preimage occurrence mismatch')
    return source.replace(before,after)


def plugin(raw):
    if hashlib.sha256(raw).hexdigest()!=PLUGIN_SHA:raise RuntimeError('Exact RC8 plugin required')
    value=raw.decode()
    value=once(value,"    if action == 'play-saved':\n",
        "    if action == 'saved-fallback':\n"
        "        from saved_navigation import recover_saved\n"
        "        recover_saved(PROFILE, PARAMS.get('key', ''), PARAMS.get('token', ''), _target); return\n"
        "    if action == 'play-saved':\n")
    return value.encode()


def stage(source,output,contracts):
    if output.exists():raise RuntimeError('Component stage already exists')
    cc=source/'script.infinity.commandcenter'
    output.mkdir(parents=True)
    if b'version="0.3.5.31"' in (cc/'addon.xml').read_bytes():
        changed={}
        pins=json.loads((source/'script.infinity.uirepair/CONTROLLER-PREIMAGES.json').read_text())
        for name,digest in pins.items():
            if hashlib.sha256((cc/name).read_bytes()).hexdigest()!=digest:
                raise RuntimeError('Signed parent component preimage drift: '+name)
    else:
        changed={'script.infinity.commandcenter/plugin.py':plugin((cc/'plugin.py').read_bytes()),
                 'script.infinity.commandcenter/saved_navigation.py':(HERE/'tracking/parent_saved_navigation.py').read_bytes(),
                 'script.infinity.commandcenter/NAVIGATION-CONTRACTS.json':contracts.read_bytes()}
        for addon,(old,new) in PARENT_VERSIONS.items():
            changed[addon+'/addon.xml']=once((source/addon/'addon.xml').read_bytes(),
                ('version="'+old+'"').encode(),('version="'+new+'"').encode())
        changed['script.infinity.commandcenter/checkpoint_runtime.py']=once((cc/'checkpoint_runtime.py').read_bytes(),
            b'ADDON_VERSION = "0.3.5.29"',b'ADDON_VERSION = "0.3.5.31"')
        changed['script.infinity.watchedbridge/controller.py']=once(
            (source/'script.infinity.watchedbridge/controller.py').read_bytes(),b'"0.3.5.29"',b'"0.3.5.31"')
        trakt=(cc/'infinity_trakt.py').read_bytes()
        assignment=next(n for n in ast.parse(trakt).body if isinstance(n,ast.Assign) and
            any(isinstance(t,ast.Name) and t.id=='BRIDGE_PINS' for t in n.targets))
        bridge=ast.literal_eval(assignment.value)
        for name in ('addon.xml','controller.py'):
            bridge[name]=hashlib.sha256(changed['script.infinity.watchedbridge/'+name]).hexdigest()
        lines=trakt.splitlines(keepends=True)
        old=b''.join(lines[assignment.lineno-1:assignment.end_lineno])
        changed['script.infinity.commandcenter/infinity_trakt.py']=once(trakt,old,
            ('BRIDGE_PINS = '+repr(dict(sorted(bridge.items())))+'\n').encode())
        # The existing controller verification is kept strict: update its dependent
        # metadata to the exact new sources, without changing either consumer.
        pins=json.loads((source/'script.infinity.watchedbridge/CONTROLLER-PREIMAGES.json').read_text())
        if pins.get('plugin.py')!=PLUGIN_SHA:raise RuntimeError('Unexpected controller binding')
        for name,data in changed.items():
            if name.startswith('script.infinity.commandcenter/'):
                pins[name.split('/',1)[1]]=hashlib.sha256(data).hexdigest()
        if len(pins)!=19:raise RuntimeError('Unexpected complete controller source inventory')
        for consumer in ('script.infinity.watchedbridge','script.infinity.uirepair'):
            old=json.loads((source/consumer/'CONTROLLER-PREIMAGES.json').read_text())
            if old.get('plugin.py')!=PLUGIN_SHA:raise RuntimeError('Unexpected dependent controller')
            changed[consumer+'/CONTROLLER-PREIMAGES.json']=(json.dumps(pins,indent=2,sort_keys=True)+'\n').encode()
    parent_pins=json.loads((HERE/'tracking/PARENT-CONTROLLER-PINS.json').read_text())
    if pins != parent_pins:raise RuntimeError('Signed CC31 release reconstruction drifted')
    changed['script.infinity.commandcenter/saved_navigation.py']=(HERE/'saved_navigation.py').read_bytes()
    overlay=HERE/'tracking/overlay'
    preimages=json.loads((HERE/'tracking/OVERLAY-PREIMAGES.json').read_text())
    def current(name):return changed[name] if name in changed else (source/name).read_bytes()
    files={p.relative_to(overlay).as_posix():p for p in overlay.rglob('*') if p.is_file()}
    if set(files)!=set(preimages):raise RuntimeError('Unreviewed tracking overlay file')
    for name,p in files.items():
        if hashlib.sha256(current(name)).hexdigest()!=preimages[name]:
            raise RuntimeError('Tracking overlay preimage mismatch: '+name)
        changed[name]=p.read_bytes()
    for addon,(_,new) in VERSIONS.items():
        name=addon+'/addon.xml';old=PARENT_VERSIONS[addon][1]
        changed[name]=once(current(name),('version="'+old+'"').encode(),('version="'+new+'"').encode())
    name='script.infinity.commandcenter/checkpoint_runtime.py'
    changed[name]=once(current(name),b'ADDON_VERSION = "0.3.5.31"',b'ADDON_VERSION = "0.3.5.32"')
    name='script.infinity.commandcenter/infinity_trakt.py';trakt=current(name)
    assignment=next(n for n in ast.parse(trakt).body if isinstance(n,ast.Assign) and
        any(isinstance(t,ast.Name) and t.id=='BRIDGE_PINS' for t in n.targets))
    bridge=ast.literal_eval(assignment.value)
    for file in bridge:bridge[file]=hashlib.sha256(current('script.infinity.watchedbridge/'+file)).hexdigest()
    lines=trakt.splitlines(keepends=True)
    changed[name]=once(trakt,b''.join(lines[assignment.lineno-1:assignment.end_lineno]),
        ('BRIDGE_PINS = '+repr(dict(sorted(bridge.items())))+'\n').encode())
    pins={name:hashlib.sha256(current('script.infinity.commandcenter/'+name)).hexdigest() for name in parent_pins}
    for consumer in ('script.infinity.watchedbridge','script.infinity.uirepair'):
        changed[consumer+'/CONTROLLER-PREIMAGES.json']=(json.dumps(pins,indent=2,sort_keys=True)+'\n').encode()
    ledger={}
    for name,data in changed.items():
        path=output/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        old=source/name
        ledger[name]=dict(original_sha256=hashlib.sha256(old.read_bytes()).hexdigest() if old.exists() else None,
                          final_sha256=hashlib.sha256(data).hexdigest(),
                          defect='Authorized tracking and navigation correction',
                          justification='Exact scoped overlay from signed CC31, consistent release bindings, original data owner and protections retained')
    return ledger


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--contracts',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();a.out.write_text(json.dumps(stage(a.source,a.output,a.contracts),indent=2,sort_keys=True)+'\n')
