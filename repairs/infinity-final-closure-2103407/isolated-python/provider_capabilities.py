"""Read-only operation-level recognition for reviewed static router families.

Compatibility is distinct from provider trust. Never import provider code or
grant navigation/persistence from a Search proof. Raw source and dependency
identities are pinned again by the dispatcher before every request.
"""
from __future__ import annotations
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET


def _tree(raw):
    if len(raw) > 512*1024:
        raise ValueError('Provider source exceeds the recognition limit')
    tree = ast.parse(raw.decode('utf-8-sig'))
    if sum(1 for _ in ast.walk(tree)) > 100000:
        raise ValueError('Provider AST exceeds the recognition limit')
    return tree


def _digest(node, addon_id=''):
    class Normalize(ast.NodeTransformer):
        def visit_Constant(self, node):
            if addon_id and isinstance(node.value,str):
                node.value=node.value.replace(addon_id,'$PROVIDER')
            return node
        def generic_visit(self,node):
            node=super().generic_visit(node)
            body=getattr(node,'body',None)
            if isinstance(body,list) and body and isinstance(body[0],ast.Expr) and \
                    isinstance(body[0].value,ast.Constant) and isinstance(body[0].value.value,str):
                del body[0]
            return node
    value=Normalize().visit(deepcopy(node))
    for item in ast.walk(value):
        if hasattr(item,'type_params'):
            if item.type_params:raise ValueError('Unsupported provider Python generic syntax')
            item._fields=tuple(field for field in item._fields if field!='type_params')
    return hashlib.sha256(ast.dump(value,include_attributes=False).encode()).hexdigest()


def map_router(raw):
    """Preserve every dispatch/helper statement; only lazy map entries vary.

    Map construction may not evaluate arbitrary calls, dict expansions, lambda
    defaults or duplicate keys. The selected lambda is verified separately.
    Thus adding an unrelated lazy action need not invalidate a Search family.
    """
    tree=_tree(raw)
    routers=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='router']
    if len(routers)!=1:raise ValueError('Ambiguous provider router')
    router=routers[0]
    maps=[n for n in ast.walk(router) if isinstance(n,ast.Assign) and
          any(isinstance(t,ast.Name) and t.id=='action_map' for t in n.targets)]
    if len(maps)!=1 or not isinstance(maps[0].value,ast.Dict):
        raise ValueError('No reviewed static action map')
    mapping={}
    for key,value in zip(maps[0].value.keys,maps[0].value.values):
        if not isinstance(key,ast.Constant) or not isinstance(key.value,str) or key.value in mapping:
            raise ValueError('Dynamic or ambiguous provider action map')
        if isinstance(value,ast.Lambda):
            args=value.args
            if args.args or args.posonlyargs or args.kwonlyargs or args.vararg or args.kwarg or args.defaults or args.kw_defaults:
                raise ValueError('Action map evaluates a dynamic lambda')
        elif not isinstance(value,ast.Name):
            raise ValueError('Action map evaluates a non-lazy value')
        mapping[key.value]=value
    maps[0].value=ast.Dict(keys=[],values=[])
    return _digest(tree),mapping


def receiver(raw, class_name, methods):
    tree=_tree(raw)
    classes=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==class_name]
    if len(classes)!=1:raise ValueError('Ambiguous Search receiver')
    result={}
    for name in methods:
        nodes=[n for n in classes[0].body if isinstance(n,ast.FunctionDef) and n.name==name]
        if len(nodes)!=1:raise ValueError('Search receiver method unavailable')
        result[name]=_digest(nodes[0])
    return result


def lambda_target(node):
    if not isinstance(node,ast.Lambda) or not isinstance(node.body,ast.Call):return None
    call=node.body
    if not isinstance(call.func,ast.Name) or call.func.id!='call_module' or call.keywords or len(call.args)!=5:return None
    first=call.args[:4]
    if not all(isinstance(v,ast.Constant) for v in first):return None
    module,cls,instantiate,method=(v.value for v in first)
    if instantiate is not True or method!='search_term' or not isinstance(module,str) or not isinstance(cls,str):return None
    tail=call.args[4]
    if not isinstance(tail,ast.Starred) or not isinstance(tail.value,ast.Tuple) or len(tail.value.elts)!=1:return None
    query=tail.value.elts[0]
    if not isinstance(query,ast.Call) or not isinstance(query.func,ast.Name) or query.func.id!='p' or query.keywords or len(query.args)!=1:return None
    key=query.args[0]
    if not isinstance(key,ast.Constant) or not isinstance(key.value,str) or not re.fullmatch(r'[a-z_]{1,32}',key.value):return None
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*){1,8}',module):return None
    return module,cls,key.value


def recognize(addon_id, root, manifest_raw, resolve_addon, profiles):
    """Resolve only declared Python modules, never arbitrary filesystem roots."""
    from saved_navigation import _source
    manifest=ET.fromstring(manifest_raw)
    extension=manifest.find('extension[@point="xbmc.python.pluginsource"]')
    if manifest.get('id')!=addon_id or extension is None:return {}
    entrypoint=extension.get('library','')
    if not entrypoint.endswith('.py'):return {}
    entry=_source(root,entrypoint)
    entry_shape=_digest(_tree(entry),addon_id)
    result={}
    dependencies=[n.get('addon','') for n in manifest.findall('requires/import') if n.get('addon','').startswith('script.module.')]
    for profile in profiles[:16]:
        if profile.get('family')!='static-lazy-action-map-v1' or profile.get('entry_shape')!=entry_shape:continue
        expected_dependency=profile.get('declared_dependency')
        if expected_dependency not in dependencies:continue
        dep_root,version=resolve_addon(expected_dependency)
        dep_root=Path(dep_root).resolve()
        dep_xml=_source(dep_root,'addon.xml')
        if b'<!DOCTYPE' in dep_xml:continue
        dep_manifest=ET.fromstring(dep_xml)
        module_ext=dep_manifest.find('extension[@point="xbmc.python.module"]')
        if dep_manifest.get('id')!=expected_dependency or dep_manifest.get('version')!=version or module_ext is None or module_ext.get('library')!=profile['library']:continue
        router_path=profile['router'];router_raw=_source(dep_root,router_path)
        shape,actions=map_router(router_raw)
        if shape!=profile['router_shape']:continue
        common_pins={'addon.xml':hashlib.sha256(dep_xml).hexdigest(),router_path:hashlib.sha256(router_raw).hexdigest()}
        for media,reviewed in profile['receivers'].items():
            if media not in ('movie','tv'):continue
            matches=[]
            for action,node in actions.items():
                target=lambda_target(node)
                if target is not None and target[:2]==(reviewed['module'],reviewed['class']):matches.append((action,target[2]))
            if len(matches)!=1:continue
            raw=_source(dep_root,reviewed['path'])
            if _digest(_tree(raw))!=reviewed['source_shape']:continue
            if receiver(raw,reviewed['class'],reviewed['methods'])!=reviewed['methods']:continue
            action,key=matches[0]
            pins=dict(common_pins);pins[reviewed['path']]=hashlib.sha256(raw).hexdigest()
            contract=dict(params={'action':action},query_key=key,
                pins={'addon.xml':hashlib.sha256(manifest_raw).hexdigest(),entrypoint:hashlib.sha256(entry).hexdigest()},
                dependencies=[dict(id=expected_dependency,root=str(dep_root),version=version,pins=pins)],
                recognition='static-lazy-action-map-v1')
            result[(media,'search')]=dict(id=addon_id,root=str(root),family='static-lazy-action-map-v1',contract=contract)
    return result


def verify_dependencies(contract,resolve_addon):
    from saved_navigation import _source
    for dep in contract.get('dependencies',[]):
        root,version=resolve_addon(dep['id'])
        if str(Path(root).resolve())!=dep['root'] or version!=dep['version']:
            raise RuntimeError('Provider dependency changed. Reopen Search to verify its interface.')
        for name,pin in dep['pins'].items():
            if hashlib.sha256(_source(Path(root).resolve(),name)).hexdigest()!=pin:
                raise RuntimeError('Provider dependency source changed. Reopen Search to verify its interface.')
