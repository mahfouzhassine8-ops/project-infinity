"""Build-time addition of the reviewed mode/class Search family to CC41.

Invoke after the existing lazy-map capability patch, before manifest generation.
No provider or saved-route source is modified.
"""
import hashlib
from pathlib import Path
import shutil

ROOT=Path(__file__).parent
OLD="    return recognize(addon_id, root, manifest_raw, _resolve_search_dependency, profiles['profiles'])\n"
NEW="""    operations = recognize(addon_id, root, manifest_raw, _resolve_search_dependency, profiles['profiles'])
    if operations:
        return operations
    from structural_search import recognize_mode_class, Unverified
    policy = json.loads(_source(cc, 'MODE-CLASS-SEARCH-POLICY.json').decode('utf-8'))
    try:
        return recognize_mode_class(addon_id, root, manifest_raw, policy)
    except Unverified:
        return {}  # An unfamiliar executable structure stays unsupported.
"""

DEPENDENCIES='''def _capability_dependency_stamp(operations):
    # Cheap cache invalidation only. Search dispatch still hashes raw sources.
    dependencies = {}
    for provider in operations.values():
        for dep in provider.get('contract', {}).get('dependencies', []):
            identity = dep['id']
            row = (dep['root'], dep['version'], tuple(sorted(dep['pins'])))
            if identity in dependencies and dependencies[identity] != row:
                raise ValueError('Inconsistent Search dependency proof.')
            dependencies[identity] = row
    result = []
    for identity, (_, _, names) in sorted(dependencies.items()):
        root, version = _resolve_search_dependency(identity)
        result.append((identity, str(root), version, _stamp(root, names)))
    return tuple(result)


'''


def cache_edits():
    return [
        ('def _scan(rows, specs, digest, prior_proofs):\n',DEPENDENCIES+'def _scan(rows, specs, digest, prior_proofs):\n'),
        ('                prior = prior_proofs.get(aid)\n'
         '                if prior and any(p.get("contract", {}).get("dependencies") for p in prior[1].values()):\n'
         '                    prior = None  # Dependency updates must not reuse a stale family proof.\n',
         '                prior = prior_proofs.get(aid)\n'),
        ('signature = (*basis, _stamp(root, names))\n                if prior',
         'signature = (*basis, _stamp(root, names), _capability_dependency_stamp(prior[1]))\n                if prior'),
        ('                    operations = _verify(aid, root, candidates, manifest_raw)\n',
         '                    operations = _verify(aid, root, candidates, manifest_raw)\n'
         '                    names = frozenset(names) | frozenset(name for provider in operations.values()\n'
         '                        for name in provider.get("contract", {}).get("pins", {}))\n'
         '                    signature = (*basis, _stamp(root, names), _capability_dependency_stamp(operations))\n'),
    ]

def finalize(cc):
    cc=Path(cc)
    file=cc/'provider_inventory.py';before=file.read_bytes();text=before.decode()
    if text.count(OLD)!=1:raise ValueError('Expected exactly one prior structural Search boundary')
    text=text.replace(OLD,NEW,1)
    # HasAddon means installed in Kodi, including disabled modules. A disabled
    # dependency cannot satisfy a currently eligible Search operation.
    old="xbmc.getCondVisibility('System.HasAddon(' + addon_id + ')')"
    new="xbmc.getCondVisibility('System.AddonIsEnabled(' + addon_id + ')')"
    if text.count(old)!=1:raise ValueError('Expected one dependency availability check')
    text=text.replace(old,new,1)
    for previous,revised in cache_edits():
        if text.count(previous)!=1:raise ValueError('Unexpected source/dependency cache boundary')
        text=text.replace(previous,revised,1)
    inverse=text
    for previous,revised in reversed(cache_edits()):inverse=inverse.replace(revised,previous,1)
    if inverse.replace(new,old,1).replace(NEW,OLD,1).encode()!=before:raise ValueError('Unrelated capability code changed')
    compile(text,str(file),'exec',dont_inherit=True);file.write_text(text)
    copied={}
    for name in ('structural_search.py','MODE-CLASS-SEARCH-POLICY.json'):
        shutil.copyfile(ROOT/name,cc/name);copied[name]=hashlib.sha256((cc/name).read_bytes()).hexdigest()
    return dict(provider_inventory_before=hashlib.sha256(before).hexdigest(),provider_inventory_after=hashlib.sha256(file.read_bytes()).hexdigest(),added=copied)
