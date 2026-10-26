"""Integrate reviewed structural Search proof without changing old capabilities."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).parent
CC='script.infinity.commandcenter'

RESOLVER='''def _resolve_search_dependency(addon_id):
    if not re.fullmatch(r'script\\.module\\.[A-Za-z0-9._-]{1,90}', addon_id):
        raise ValueError('Invalid provider dependency identity.')
    if not xbmc.getCondVisibility('System.AddonIsEnabled(' + addon_id + ')'):
        raise RuntimeError('Provider dependency is unavailable.')
    addon = xbmcaddon.Addon(addon_id)
    return (Path(xbmcvfs.translatePath(addon.getAddonInfo('path'))).resolve(),
            addon.getAddonInfo('version'))


def _automatic_search(addon_id, root, manifest_raw):
    from provider_capabilities import recognize
    from saved_navigation import _source
    cc = Path(xbmcvfs.translatePath(xbmcaddon.Addon(CC).getAddonInfo('path'))).resolve()
    profiles = json.loads(_source(cc, 'SEARCH-STRUCTURES.json').decode('utf-8'))
    if profiles.get('schema') != 1 or not isinstance(profiles.get('profiles'), list):
        raise ValueError('Unknown Search recognition policy.')
    operations = recognize(addon_id, root, manifest_raw, _resolve_search_dependency, profiles['profiles'])
    from structural_search import recognize_mode_class
    policy = json.loads(_source(cc, 'MODE-CLASS-SEARCH-POLICY.json').decode('utf-8'))
    manifest = ET.fromstring(manifest_raw)
    extension = manifest.find('extension[@point="xbmc.python.pluginsource"]')
    if extension is not None and extension.get('library') == policy.get('entrypoint'):
        operations.update(recognize_mode_class(addon_id, root, manifest_raw, policy))
    return operations


'''


DEPENDENCY_STAMP="def _capability_dependency_stamp(operations):\n    dependencies = {}\n    for provider in operations.values():\n        for dep in provider.get('contract', {}).get('dependencies', []):\n            identity = dep['id']\n            if identity not in dependencies:\n                dependencies[identity] = (dep['root'], dep['version'], dict(dep['pins']))\n            else:\n                root, version, pins = dependencies[identity]\n                if root != dep['root'] or version != dep['version']:\n                    raise ValueError('Inconsistent Search dependency identity.')\n                for name, pin in dep['pins'].items():\n                    if name in pins and pins[name] != pin:\n                        raise ValueError('Inconsistent Search dependency source.')\n                    pins[name] = pin\n    result = []\n    for identity, (_, _, pins) in sorted(dependencies.items()):\n        root, version = _resolve_search_dependency(identity)\n        result.append((identity, str(root), version, _stamp(root, pins)))\n    return tuple(result)\n\n\n"

def edits(name):
    if name=='provider_inventory.py':
        return [
            ('def _verify(addon_id, root, specs, manifest_raw=None):\n',
             RESOLVER+DEPENDENCY_STAMP+'def _verify(addon_id, root, specs, manifest_raw=None):\n'),
            ('    return operations\n\n\ndef _scan',
             '    if not operations:\n'
             '        operations = _automatic_search(addon_id, root, manifest_raw)\n'
             '    return operations\n\n\ndef _scan'),
            ("        entry = dict(id=aid, name=str(row.get('name') or aid)[:100],",
             "        label = re.sub(r'\\[(?:/?(?:B|I)|/?COLOR(?: [^\\]]*)?)\\]', '', str(row.get('name') or aid), flags=re.I)\n"
             "        entry = dict(id=aid, name=label[:100],"),
            ('                    operations = _verify(aid, root, candidates, manifest_raw)\n',
             '                    operations = _verify(aid, root, candidates, manifest_raw)\n'
             '                    names = frozenset(set(names) | {name for p in operations.values() for name in p["contract"]["pins"]})\n'
             '                    signature = (*basis, _stamp(root, names), _capability_dependency_stamp(operations))\n'),
            ('signature = (*basis, _stamp(root, names))\n                if prior',
             'signature = (*basis, _stamp(root, names), _capability_dependency_stamp(prior[1]))\n                if prior'),
        ]
    if name=='infinity_search.py':
        return [
            ("    for name,pin in contract['pins'].items():\n",
             "    from provider_capabilities import verify_dependencies\n"
             "    from provider_inventory import _resolve_search_dependency\n"
             "    verify_dependencies(contract, _resolve_search_dependency)\n"
             "    for name,pin in contract['pins'].items():\n"),
        ]
    raise ValueError('Unowned provider source: '+name)


def patch(name,raw,require_preimage=True):
    if require_preimage:
        plan=json.loads((ROOT/'FIRSTPARTY-COMPOSITION-PLAN.json').read_text())
        if hashlib.sha256(raw).hexdigest()!=plan['plan'][CC]['signed407_all_file_preimages'][name]:
            raise ValueError('Wrong signed407 provider preimage: '+name)
    text=raw.decode()
    for old,new in edits(name):
        if text.count(old)!=1:raise ValueError('Provider recognition boundary differs: '+name)
        text=text.replace(old,new,1)
    restored=text
    for old,new in reversed(edits(name)):restored=restored.replace(new,old,1)
    if restored.encode()!=raw:raise ValueError('Unrelated provider source change')
    compile(text,name,'exec',dont_inherit=True)
    return text.encode()
