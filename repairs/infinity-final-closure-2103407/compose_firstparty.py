"""Compose exact signed407 functions into CC modules and stable Kodi ID shims.

Staging only. No user data, installed provider, APK or signing input is mutated.
All preimages must match the recorded complete first-party source inventories.
"""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

from patch_checkpoint_protocol import patch as checkpoint_patch
from patch_search_lifetime import patch as search_patch

ROOT=Path(__file__).parent
CC='script.infinity.commandcenter'
PACKAGES={'script.infinity.uirepair':'uirepair',
          'script.infinity.watchedbridge':'watchedbridge','script.infinity.rails':'rails'}
VERSION='0.3.5.40'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def replace_function(text,name,replacement):
    nodes=[n for n in ast.parse(text).body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==name]
    if len(nodes)!=1:raise ValueError('Expected one function/class: '+name)
    n=nodes[0];lines=text.splitlines(keepends=True)
    return ''.join(lines[:n.lineno-1])+replacement+'\n'+''.join(lines[n.end_lineno:])


def replace_once(text,old,new):
    if text.count(old)!=1:raise ValueError('Missing/nonunique composition anchor: '+old[:80])
    return text.replace(old,new,1)


def bootstrap(helper_sha):
    return '''# INFINITY_AUTHENTICATED_MODULE_BOOTSTRAP_V1
import sys as _infinity_sys
import xbmcaddon as _infinity_addon
import xbmcvfs as _infinity_vfs
_infinity_cc = _infinity_addon.Addon('script.infinity.commandcenter')
_infinity_root = _infinity_vfs.translatePath(_infinity_cc.getAddonInfo('path')).rstrip('/')
_infinity_base = _infinity_root.rsplit('/', 1)[0] + '/'
_infinity_prefixes = tuple(_infinity_base + name for name in (
    'script.infinity.commandcenter', 'script.infinity.uirepair',
    'script.infinity.watchedbridge', 'script.infinity.rails'))
_infinity_paths = _infinity_sys.path[:]
try:
    # The trust helper's standard-library imports cannot be shadowed by an
    # unlisted source file in an owned component before its guard is active.
    _infinity_sys.path[:] = [p for p in _infinity_paths if p.startswith('/') and not any(
        p == root or p.startswith(root + '/') for root in _infinity_prefixes)]
    import hashlib as _infinity_hash
    import types as _infinity_types
    with open(_infinity_root + '/module_contract.py', 'rb') as _infinity_stream:
        _infinity_raw = _infinity_stream.read(4 * 1024 * 1024 + 1)
    if _infinity_hash.sha256(_infinity_raw).hexdigest() != 'HELPER_HASH':
        raise RuntimeError('The trusted Infinity module bootstrap changed. Install the matching native package.')
    _infinity_contract_module = _infinity_sys.modules.get('module_contract')
    if _infinity_contract_module is None:
        _infinity_contract_module = _infinity_types.ModuleType('module_contract')
        _infinity_contract_module.__file__ = _infinity_root + '/module_contract.py'
        _infinity_sys.modules['module_contract'] = _infinity_contract_module
        exec(compile(_infinity_raw, _infinity_contract_module.__file__, 'exec', dont_inherit=True),
             _infinity_contract_module.__dict__)
finally:
    _infinity_sys.path[:] = _infinity_paths
_infinity_sys.path.insert(0, _infinity_root)
_infinity_contract = _infinity_contract_module.active_contract(
    _infinity_root, _infinity_cc.getAddonInfo('version'))
del _infinity_raw, _infinity_paths
# END_INFINITY_AUTHENTICATED_MODULE_BOOTSTRAP_V1
'''.replace('HELPER_HASH',helper_sha)


def prepend(text,code):
    nodes=ast.parse(text).body;line=0
    for n in nodes:
        if isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str):line=n.end_lineno
        elif isinstance(n,ast.ImportFrom) and n.module=='__future__':line=n.end_lineno
        else:break
    lines=text.splitlines(keepends=True)
    return ''.join(lines[:line])+'\n'+code+'\n'+''.join(lines[line:])


def relative_imports(text,names):
    # Change only import ownership; all original function bodies remain intact.
    import re
    for name in names:
        text=re.sub(r'(?m)^(\s*)from '+re.escape(name)+r' import ',r'\1from .'+name+' import ',text)
        text=re.sub(r'(?m)^(\s*)import '+re.escape(name)+r'( as [A-Za-z_]+)?$',
                    lambda m:m[1]+'from . import '+name+(m[2] or ''),text)
    return text


UI_LOAD='''def load():
    import xbmcaddon
    import xbmcvfs
    from module_contract import active_contract, source_module
    addon = xbmcaddon.Addon('script.infinity.commandcenter')
    root = Path(xbmcvfs.translatePath(addon.getAddonInfo('path'))).absolute()
    contract = active_contract(root, addon.getAddonInfo('version'))
    for name in ('common', 'experience', 'resume_hub', 'checkpoint_runtime', 'persistence_participant'):
        mod = importlib.import_module(name)
        if Path(mod.__file__).absolute() != root / (name + '.py'):
            raise RuntimeError('A conflicting Command Center module is loaded. No changes were made.')
    before = sys.argv[:]
    try:
        sys.argv = ['plugin://script.infinity.commandcenter/', '-1', '']
        plugin = source_module(contract, 'infinity_verified_resume_plugin',
                               'script.infinity.commandcenter/plugin.py')
    finally:
        sys.argv = before
    return plugin
'''
WB_VERIFY='''def verify(root):
    import xbmcaddon
    from module_contract import active_contract
    root = Path(root).absolute()
    addon = xbmcaddon.Addon('script.infinity.commandcenter')
    active_contract(root, addon.getAddonInfo('version'))
    return root
'''
UI_RAILS='''def rails_supported():
    if not xbmc.getCondVisibility('System.AddonIsEnabled(script.infinity.rails)'):
        return False
    from module_contract import active_contract
    cc = xbmcaddon.Addon('script.infinity.commandcenter')
    root = Path(xbmcvfs.translatePath(cc.getAddonInfo('path'))).absolute()
    contract = active_contract(root, cc.getAddonInfo('version'))
    return contract.entries.get('script.infinity.rails/context_add.py') == 'command_center_client'
'''
CC_BRIDGE='''def _bridge():
    from module_contract import active_contract
    cc=xbmcaddon.Addon('script.infinity.commandcenter')
    ccroot=Path(xbmcvfs.translatePath(cc.getAddonInfo('path'))).absolute()
    active_contract(ccroot,cc.getAddonInfo('version'))
    if Path(__file__).absolute()!=ccroot/'infinity_trakt.py' or Path(hub.__file__).absolute()!=ccroot/'resume_hub.py':
        raise RuntimeError('A conflicting Infinity controller is loaded. No saved data was changed.')
    from infinity_modules.watchedbridge import context as module
    return module,module.controller.load(str(ccroot))
'''


def publisher(text):
    """Lift the original loop's existing work into one scheduled, stateful tick."""
    tree=ast.parse(text);run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run')
    loop=next(n for n in run.body if isinstance(n,ast.While))
    body=loop.body[:-1]  # Last statement is the old Monitor.waitForAbort(1.0).
    if ast.unparse(loop.body[-1].test)!='monitor.waitForAbort(1.0)':raise ValueError('Publisher wait changed')
    text=replace_function(text,'run','')
    # Remove only the old executable main entry; the CC scheduler now owns it.
    main=next(n for n in ast.parse(text).body if isinstance(n,ast.If) and '__name__' in ast.unparse(n.test))
    lines=text.splitlines(keepends=True);text=''.join(lines[:main.lineno-1])+''.join(lines[main.end_lineno:])
    work='\n'.join(ast.unparse(n) for n in body)
    node=ast.parse(work)
    class State(ast.NodeTransformer):
        def visit_Name(self,n):
            if n.id in ('signature','verified','next_check','next_publish','home'):
                return ast.copy_location(ast.Attribute(ast.Name('self',ast.Load()),n.id,n.ctx),n)
            return n
    work=ast.unparse(ast.fix_missing_locations(State().visit(node)))
    text+='''\nclass Publisher:
    def __init__(self):
        self.home = xbmcgui.Window(10000)
        self.signature, self.verified = None, {}
        self.next_check = self.next_publish = self.next_tick = 0.0

    def tick(self, now):
        if now < self.next_tick:
            return
        self.next_tick = now + 1.0
'''+''.join('        '+line+'\n' for line in work.splitlines())
    return text


def compose(sources,destination):
    sources,destination=Path(sources),Path(destination)
    if destination.exists():raise ValueError('Refuse to replace an existing candidate stage')
    plan=json.loads((ROOT/'FIRSTPARTY-COMPOSITION-PLAN.json').read_text())['plan']
    for aid,meta in plan.items():
        actual={p.relative_to(sources/aid).as_posix():sha(p.read_bytes()) for p in (sources/aid).rglob('*') if p.is_file()}
        if actual!=meta['signed407_all_file_preimages']:raise ValueError('Signed407 component source drift: '+aid)
    destination.mkdir(parents=True)
    for aid in plan:shutil.copytree(sources/aid,destination/aid)
    cc=destination/CC
    (cc/'module_contract.py').write_bytes((ROOT/'isolated-python/module_contract.py').read_bytes())
    code=bootstrap(sha((cc/'module_contract.py').read_bytes()))
    modules=cc/'infinity_modules';modules.mkdir();(modules/'__init__.py').write_text('"""Authenticated first-party modules; no independent workers or data owner."""\n')
    for aid,package in PACKAGES.items():
        internal=modules/package;internal.mkdir();(internal/'__init__.py').write_text('')
        if package=='rails':
            for source in (sources/aid/'resources/lib').glob('*.py'):shutil.copyfile(source,internal/source.name)
            for source in (destination/aid/'resources/lib').glob('*.py'):source.unlink()
        else:
            names=[p.stem for p in (sources/aid).glob('*.py')]
            for source in (sources/aid).glob('*.py'):
                text=relative_imports(source.read_text(),names)
                if source.name=='controller_access.py':text=replace_function(text,'load',UI_LOAD)
                if package=='uirepair' and source.name=='runtime.py':text=replace_function(text,'rails_supported',UI_RAILS)
                if package=='watchedbridge' and source.name=='controller.py':text=replace_function(text,'verify',WB_VERIFY)
                if package=='watchedbridge' and source.name=='service.py':text=publisher(text)
                (internal/source.name).write_text(text)
            for source in (destination/aid).glob('*.py'):source.unlink()
            if package=='watchedbridge':
                shutil.copyfile(sources/aid/'PROVIDER-CONTRACTS.json',internal/'PROVIDER-CONTRACTS.json')
        entries={'uirepair':{'default.py':'from infinity_modules.uirepair.runtime import main\nmain(_infinity_sys.argv[1:])',
                            'plugin.py':'from infinity_modules.uirepair.plugin import main\nmain()'},
                 'watchedbridge':{'default.py':'from infinity_modules.watchedbridge.default import main\nmain()',
                                  'context.py':'from infinity_modules.watchedbridge.context import main\nmain()'},
                 'rails':{'default.py':'from infinity_modules.rails.runtime import main\nmain()',
                          'plugin.py':'from infinity_modules.rails.runtime import plugin\nplugin()',
                          'context_add.py':"from infinity_modules.rails.runtime import context_add\ncontext_add(getattr(_infinity_sys, 'listitem', None))"}}[package]
        for name,body in entries.items():(destination/aid/name).write_text(code+'\n'+body+'\n')
        # Old integrity tables are obsolete code-discovery metadata, not user state.
        pinfile=destination/aid/'CONTROLLER-PREIMAGES.json'
        if pinfile.exists():pinfile.unlink()
    (cc/'checkpoint_runtime.py').write_bytes(checkpoint_patch((cc/'checkpoint_runtime.py').read_bytes()))
    path=cc/'checkpoint_runtime.py';text=path.read_text()
    text=replace_once(text,'def write_scope(profile, session=None):\n    store = store_for(profile)',
        'def write_scope(profile, session=None):\n    from module_contract import require_current\n    require_current()\n    store = store_for(profile)')
    path.write_text(text)
    (cc/'infinity_search.py').write_bytes(search_patch((cc/'infinity_search.py').read_bytes()))
    path=cc/'infinity_trakt.py';text=replace_function(path.read_text(),'_bridge',CC_BRIDGE)
    lines=text.splitlines(keepends=True)
    text=''.join(line for line in lines if not line.startswith('BRIDGE_PINS = '))
    path.write_text(text)
    path=cc/'service.py';text=path.read_text()
    text=replace_once(text,'    monitor = CheckpointMonitor(checkpoint)\n',
        '    monitor = CheckpointMonitor(checkpoint)\n    try:\n        from infinity_modules.watchedbridge.service import Publisher\n        watched_publisher = Publisher()\n    except Exception as error:\n        watched_publisher = None\n        log("Watched presentation unavailable: " + type(error).__name__)\n')
    text=replace_once(text,'        player.poll()\n        hub.poll_kodi_sync(profile)\n',
        '        player.poll()\n        hub.poll_kodi_sync(profile)\n        if watched_publisher is not None:\n            try:\n                watched_publisher.tick(time.monotonic())\n            except Exception as error:\n                log("Watched presentation deferred: " + type(error).__name__)\n')
    path.write_text(text)
    # Keep native context metadata and all existing IDs/extension routes. Only
    # the duplicate WB startup service is removed; it now runs within CC's gate.
    versions={CC:VERSION,'script.infinity.uirepair':'0.1.23','script.infinity.watchedbridge':'1.0.21','script.infinity.rails':'0.2.8'}
    for aid,version in versions.items():
        path=destination/aid/'addon.xml';raw=path.read_text();old=ET.fromstring(raw).get('version')
        raw=replace_once(raw,'version="'+old+'"','version="'+version+'"')
        # Existing metadata defaults to fresh invokers. Make that ownership
        # requirement explicit for the authenticated first-party bootstrap.
        raw=replace_once(raw,'<extension point="xbmc.addon.metadata">',
                        '<extension point="xbmc.addon.metadata">\n    <reuselanguageinvoker>false</reuselanguageinvoker>')
        if aid=='script.infinity.watchedbridge':
            import re
            raw,count=re.subn(r'  <extension point="xbmc.service" library="service.py" start="startup" />\n','',raw)
            if count!=1:raise ValueError('Expected one WB service extension')
        path.write_text(raw)
    for name in plan[CC]['entries']:
        path=cc/name;path.write_text(prepend(path.read_text(),code))
    for path in destination.rglob('*.py'):compile(path.read_bytes(),str(path),'exec',dont_inherit=True)
    before={aid+'/'+name:digest for aid,meta in plan.items() for name,digest in meta['signed407_all_file_preimages'].items()}
    after={p.relative_to(destination).as_posix():sha(p.read_bytes()) for p in destination.rglob('*') if p.is_file()}
    return {'source_inventory':after,'removed_members':sorted(set(before)-set(after)),
            'added_members':sorted(set(after)-set(before)),
            'changed_members':sorted(n for n in set(before)&set(after) if before[n]!=after[n]),
            'preserved_members':sum(before[n]==after[n] for n in set(before)&set(after)),
            'user_data_mutation':False,'apk_produced':False,'Cobra_modified':False}


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('sources',type=Path);parser.add_argument('destination',type=Path)
    args=parser.parse_args();report=compose(args.sources,args.destination)
    (args.destination.parent/'FIRSTPARTY-COMPOSITION.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='source_inventory'},indent=2))
