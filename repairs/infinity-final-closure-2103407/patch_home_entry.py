"""Remove only redundant Home interpreter dispatch, preserving actual actions."""
import ast
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import xml.etree.ElementTree as ET

ROOT=Path(__file__).parent
CC='script.infinity.commandcenter'
SKIN='skin.infinity.diggz'
VIEW='RunScript(script.infinity.commandcenter,view-mode,normal)'
SYNC='RunScript(script.infinity.commandcenter,runtime-sync,true)'
REQUEST='SetProperty(Infinity.Home.RuntimeSync.Pending,true,Home)'
VIEW_OPEN='<onload condition="[System.HasAddon(script.infinity.commandcenter)] + [String.IsEqual(Skin.String(Infinity.VisualMode),normal)]">'
SYNC_OPEN='<onload condition="System.HasAddon(script.infinity.commandcenter)">'

CONSUMER='''_home_runtime_sync_after = 0.0
_home_runtime_commands = None


def _consume_home_runtime_sync(now):
    """Coalesce only a read-only refresh request into the existing resident."""
    global _home_runtime_sync_after, _home_runtime_commands
    if (now < _home_runtime_sync_after or xbmc.getSkinDir() != 'skin.infinity.diggz' or
            xbmcgui.getCurrentWindowId() != 10000 or
            HOME.getProperty('Infinity.Home.RuntimeSync.Pending') != 'true'):
        return False
    _home_runtime_sync_after = now + 1.0
    HOME.clearProperty('Infinity.Home.RuntimeSync.Pending')
    try:
        # Same original quiet function, authenticated by the active CC manifest.
        # It reads current runtime files and publishes UI properties; no new
        # writer, thread, service or alternate setting owner is introduced.
        from module_contract import require_current, source_module
        require_current()
        if _home_runtime_commands is None:
            _home_runtime_commands = source_module(_infinity_contract,
                'infinity_home_runtime_commands', 'script.infinity.commandcenter/default.py')
        _home_runtime_commands.runtime_sync(quiet=True)
        return True
    except Exception as error:
        HOME.setProperty('Infinity.Home.RuntimeSync.Pending', 'true')
        log('Home runtime refresh deferred: ' + type(error).__name__)
        return False


'''


def digest(raw):return hashlib.sha256(raw).hexdigest()


def require_preimage(name,raw):
    plan=json.loads((ROOT/'HOME-ENTRY-413-PLAN.json').read_text())
    if digest(raw)!=plan['source_preimages'].get('assets/addons/'+name):
        raise ValueError('Exact signed412 source required: '+name)


def normal_actions(default_raw):
    require_preimage(CC+'/default.py',default_raw)
    node=next(n for n in ast.parse(default_raw).body if isinstance(n,ast.FunctionDef) and n.name=='direct_command')
    actions=[]
    home=SimpleNamespace(clearProperty=lambda name:actions.append('ClearProperty('+name+',Home)'),
                         setProperty=lambda name,value:actions.append('SetProperty('+name+','+value+',Home)'))
    namespace=dict(xbmc=SimpleNamespace(executebuiltin=actions.append),
                   xbmcgui=SimpleNamespace(Window=lambda ident:home))
    exec(compile(ast.Module(body=[node],type_ignores=[]),'actual-signed412-normal-command','exec'),namespace)
    if namespace['direct_command'](['default.py','view-mode','normal']) is not True:
        raise ValueError('Original Normal command did not resolve')
    if len(actions)!=17 or any(not value.startswith(('Skin.SetString(','ClearProperty(','SetProperty(')) for value in actions):
        raise ValueError('Original Normal action set changed')
    return actions


def python_edits(name):
    if name=='service.py':
        return [('def main():\n',CONSUMER+'def main():\n'),
                ('        hub.observe_visible_cards()\n',
                 '        _consume_home_runtime_sync(now)\n        hub.observe_visible_cards()\n')]
    if name=='default.py':
        return [('def _read_refresh_state() -> tuple[str, str]:\n    try:\n',
                 "def _read_refresh_state() -> tuple[str, str]:\n    try:\n"
                 "        if not xbmc.getCondVisibility('System.HasAddon(service.infinity.refresh)'):\n"
                 "            return 'auto', 'auto'\n")]
    if name=='addon.xml':return [('version="0.3.5.42"','version="0.3.5.43"')]
    raise ValueError('Unowned Home-entry source')


def patch(name,raw):
    require_preimage(CC+'/'+name,raw)
    text=raw.decode()
    for old,new in python_edits(name):
        if text.count(old)!=1:raise ValueError('Home-entry Python boundary differs: '+name)
        text=text.replace(old,new,1)
    restored=text
    for old,new in reversed(python_edits(name)):restored=restored.replace(new,old,1)
    if restored.encode()!=raw:raise ValueError('Unrelated Python source changed')
    if name.endswith('.py'):compile(text,name,'exec',dont_inherit=True)
    return text.encode()


def patch_home(name,raw,actions):
    require_preimage(SKIN+'/'+name,raw)
    text=raw.decode()
    old_view=VIEW_OPEN+VIEW+'</onload>'
    new_view='\n  '.join(VIEW_OPEN+action+'</onload>' for action in actions)
    old_sync=SYNC_OPEN+SYNC+'</onload>';new_sync=SYNC_OPEN+REQUEST+'</onload>'
    if text.count(old_view)!=1 or text.count(old_sync)!=1:
        raise ValueError('Only the original two Home onload commands may change: '+name)
    result=text.replace(old_view,new_view,1).replace(old_sync,new_sync,1)
    if result.replace(new_sync,old_sync,1).replace(new_view,old_view,1)!=text:
        raise ValueError('Unrelated Home XML changed')
    ET.fromstring(result)
    return result.encode()


def skin_sources(before,default_raw):
    """Input is the entire exact signed parent skin, never an installed tree."""
    result=dict(before);actions=normal_actions(default_raw)
    homes=[name for name in before if name.endswith('/Home.xml')]
    if len(homes)!=14:raise ValueError('All fourteen exact Home profiles required')
    for name in homes:result[name]=patch_home(name,before[name],actions)
    name='addon.xml';require_preimage(SKIN+'/'+name,before[name])
    text=before[name].decode()
    if text.count('version="1.0.5.243"')!=1:raise ValueError('Exact skin243 version required')
    dependency='<import addon="script.infinity.commandcenter" version="0.3.5.20" />'
    if text.count(dependency)!=1:raise ValueError('Original Command Center dependency differs')
    text=text.replace('version="1.0.5.243"','version="1.0.5.244"',1)
    result[name]=text.replace(dependency,dependency.replace('0.3.5.20','0.3.5.43'),1).encode()
    name='infinity-skin.json';require_preimage(SKIN+'/'+name,before[name])
    metadata=json.loads(before[name])
    metadata.update(version='1.0.5.244',skin_version='1.0.5.244',candidate=244,candidate_locked=False,
                    physical_device_verified=False,candidate_name='Infinity corrective verification candidate')
    result[name]=(json.dumps(metadata,indent=2,sort_keys=True)+'\n').encode()
    name='Infinity-Protected-Manifest.json';require_preimage(SKIN+'/'+name,before[name])
    protected=json.loads(before[name])
    if name in protected['protected_files']:raise ValueError('Self-referential protected manifest')
    # Repair stale old metadata using only exact original signed bytes plus the
    # explicitly budgeted changes; never bless an installed or unknown file.
    previous_mismatches=[]
    for member,pin in protected['protected_files'].items():
        if member not in before:raise ValueError('Missing signed protected member')
        if digest(before[member])!=pin:previous_mismatches.append(member)
        protected['protected_files'][member]=digest(result[member])
    protected.update(skin_version='1.0.5.244',candidate_version='1.0.5.244',candidate=244,candidate_locked=False)
    result[name]=(json.dumps(protected,indent=2,sort_keys=True)+'\n').encode()
    changed={name for name in result if result[name]!=before[name]}
    if changed!=set(homes)|{'addon.xml','infinity-skin.json','Infinity-Protected-Manifest.json'}:
        raise ValueError('Unowned skin member changed')
    return result,dict(changed_members=sorted(changed),preserved_members=len(before)-len(changed),
                       original_metadata_mismatches=previous_mismatches,
                       onload_commands_only=True,layouts_geometry_player_resources_unchanged=True)
