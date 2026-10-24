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
          'script.infinity.uirepair':('0.1.12','0.1.14'),
          'skin.infinity.diggz':('1.0.5.238','1.0.5.238')}

BASE_VERSIONS={k:(v[0], {'script.infinity.commandcenter':'0.3.5.32', 'script.infinity.watchedbridge':'1.0.13', 'script.infinity.uirepair':'0.1.15', 'skin.infinity.diggz':'1.0.5.239'}[k]) for k,v in PARENT_VERSIONS.items()}

FINAL_EIGHT_VERSIONS={k:(v[0], {'script.infinity.commandcenter':'0.3.5.33', 'script.infinity.watchedbridge':'1.0.14', 'script.infinity.uirepair':'0.1.16', 'skin.infinity.diggz':'1.0.5.240'}[k]) for k,v in BASE_VERSIONS.items()}

VERSIONS={k:(v[0], {'script.infinity.commandcenter':'0.3.5.34', 'script.infinity.watchedbridge':'1.0.15', 'script.infinity.uirepair':'0.1.17', 'skin.infinity.diggz':'1.0.5.241'}[k]) for k,v in FINAL_EIGHT_VERSIONS.items()}
NEW_CONTROLLER_FILES={'provider_inventory.py','title_metadata.py','information.py','selection_contract.py','resources/skins/Default/1080i/InfinityInformation.xml'}

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
    files={p.relative_to(overlay).as_posix():p for p in overlay.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    if set(files)!=set(preimages):raise RuntimeError('Unreviewed tracking overlay file')
    for name,p in files.items():
        if hashlib.sha256(current(name)).hexdigest()!=preimages[name]:
            raise RuntimeError('Tracking overlay preimage mismatch: '+name)
        changed[name]=p.read_bytes()
    for addon,(_,new) in BASE_VERSIONS.items():
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
    # Preserve the exact signed CC32 admission before adding the coordinated
    # final-eight release. Never relabel modified CC32 bytes as the old release.
    final_dir=HERE/'tracking/final-eight'
    baseline32=json.loads((final_dir/'BASE32-CONTROLLER-PINS.json').read_text())
    if pins != baseline32:raise RuntimeError('Signed CC32 reconstruction drifted')
    final_overlay=final_dir/'overlay'
    preimages=json.loads((final_dir/'OVERLAY-PREIMAGES.json').read_text())
    final_files={p.relative_to(final_overlay).as_posix():p for p in final_overlay.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    if set(final_files)!=set(preimages):raise RuntimeError('Unreviewed final-eight component file')
    for name,p in final_files.items():
        if hashlib.sha256(current(name)).hexdigest()!=preimages[name]:
            raise RuntimeError('Final-eight preimage mismatch: '+name)
        changed[name]=p.read_bytes()
    for addon,(_,new) in FINAL_EIGHT_VERSIONS.items():
        name=addon+'/addon.xml';old=BASE_VERSIONS[addon][1]
        changed[name]=once(current(name),('version="'+old+'"').encode(),('version="'+new+'"').encode())
    name='script.infinity.commandcenter/checkpoint_runtime.py'
    changed[name]=once(current(name),b'ADDON_VERSION = "0.3.5.32"',b'ADDON_VERSION = "0.3.5.33"')
    name='script.infinity.watchedbridge/controller.py'
    changed[name]=once(current(name),b'"0.3.5.32"',b'"0.3.5.33"')
    name='script.infinity.commandcenter/infinity_trakt.py'
    changed[name]=once(once(current(name),b"'1.0.13'",b"'1.0.14'"),b"'0.3.5.32'",b"'0.3.5.33'")
    trakt=current(name)
    assignment=next(n for n in ast.parse(trakt).body if isinstance(n,ast.Assign) and
        any(isinstance(t,ast.Name) and t.id=='BRIDGE_PINS' for t in n.targets))
    bridge=ast.literal_eval(assignment.value)
    for file in bridge:bridge[file]=hashlib.sha256(current('script.infinity.watchedbridge/'+file)).hexdigest()
    lines=trakt.splitlines(keepends=True)
    changed[name]=once(trakt,b''.join(lines[assignment.lineno-1:assignment.end_lineno]),
        ('BRIDGE_PINS = '+repr(dict(sorted(bridge.items())))+'\n').encode())
    pins={name:hashlib.sha256(current('script.infinity.commandcenter/'+name)).hexdigest() for name in baseline32}
    for consumer in ('script.infinity.watchedbridge','script.infinity.uirepair'):
        changed[consumer+'/CONTROLLER-PREIMAGES.json']=(json.dumps(pins,indent=2,sort_keys=True)+'\n').encode()
    # The exact CC33 signed reference must be reconstructed before applying the
    # new layer. Older installed-code admissions remain valid, never relabelled.
    universal=HERE/'universal'
    baseline33=json.loads((universal/'BASE33-CONTROLLER-PINS.json').read_text())
    if pins!=baseline33:raise RuntimeError('Signed CC33 reconstruction drifted')
    universal_overlay=universal/'overlay'
    preimages=json.loads((universal/'OVERLAY-PREIMAGES.json').read_text())
    universal_files={p.relative_to(universal_overlay).as_posix():p for p in universal_overlay.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    if set(universal_files)!=set(preimages):raise RuntimeError('Unreviewed universal component file')
    additions={'script.infinity.commandcenter/'+n for n in NEW_CONTROLLER_FILES}
    if {n for n,h in preimages.items() if h is None}!=additions:
        raise RuntimeError('Unexpected universal source additions')
    for name,p in universal_files.items():
        relative=Path(name)
        if relative.is_absolute() or '..' in relative.parts or 'cobra' in name.lower():
            raise RuntimeError('Invalid universal component path: '+name)
        if relative.parts[0] not in VERSIONS:raise RuntimeError('Unapproved universal component: '+name)
        if preimages[name] is None:
            if name in changed or (source/name).exists():raise RuntimeError('New universal source already exists: '+name)
        elif hashlib.sha256(current(name)).hexdigest()!=preimages[name]:
            raise RuntimeError('Universal source preimage mismatch: '+name)
        changed[name]=p.read_bytes()
    for addon,(_,new) in VERSIONS.items():
        name=addon+'/addon.xml';old=FINAL_EIGHT_VERSIONS[addon][1]
        changed[name]=once(current(name),('version="'+old+'"').encode(),('version="'+new+'"').encode())
    name='script.infinity.commandcenter/checkpoint_runtime.py'
    changed[name]=once(current(name),b'ADDON_VERSION = "0.3.5.33"',b'ADDON_VERSION = "0.3.5.34"')
    name='script.infinity.watchedbridge/controller.py'
    changed[name]=once(current(name),b'"0.3.5.33"',b'"0.3.5.34"')
    name='script.infinity.commandcenter/infinity_trakt.py'
    changed[name]=once(once(current(name),b"'1.0.14'",b"'1.0.15'"),b"'0.3.5.33'",b"'0.3.5.34'")
    trakt=current(name)
    assignment=next(n for n in ast.parse(trakt).body if isinstance(n,ast.Assign) and
        any(isinstance(t,ast.Name) and t.id=='BRIDGE_PINS' for t in n.targets))
    bridge=ast.literal_eval(assignment.value)
    for file in bridge:bridge[file]=hashlib.sha256(current('script.infinity.watchedbridge/'+file)).hexdigest()
    lines=trakt.splitlines(keepends=True)
    changed[name]=once(trakt,b''.join(lines[assignment.lineno-1:assignment.end_lineno]),
        ('BRIDGE_PINS = '+repr(dict(sorted(bridge.items())))+'\n').encode())
    required=set(baseline33)|NEW_CONTROLLER_FILES
    if len(baseline33)!=19 or len(required)!=24:raise RuntimeError('CC34 named source inventory drifted')
    pins={name:hashlib.sha256(current('script.infinity.commandcenter/'+name)).hexdigest() for name in required}
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
