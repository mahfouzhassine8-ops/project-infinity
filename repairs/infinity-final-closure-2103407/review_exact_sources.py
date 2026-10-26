"""Build-only exact-byte fast paths, each bound to an existing reviewed AST.

No provider ID grants a capability. A changed exact byte hash simply takes the
existing structural verification path; dispatch source checks stay unchanged.
"""
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def fingerprint(raw,addon_id,python312=False):
    # Keep the same signed407 canonicalization as saved_navigation.fingerprint.
    tree=ast.parse(raw.decode('utf-8-sig'))
    class Canonical(ast.NodeTransformer):
        def visit_Constant(self,node):
            if isinstance(node.value,str):node.value=node.value.replace(addon_id,'$PROVIDER')
            return node
        def generic_visit(self,node):
            node=super().generic_visit(node);body=getattr(node,'body',None)
            if isinstance(body,list) and body and isinstance(body[0],ast.Expr):
                value=body[0].value
                if isinstance(value,ast.Constant) and isinstance(value.value,str):del body[0]
            return node
    tree=Canonical().visit(tree)
    for node in list(ast.walk(tree)):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
            if getattr(node,'type_params',[]):raise ValueError('Unsupported Python generic syntax')
            node._fields=tuple(field for field in node._fields if field!='type_params')
            if python312:
                node.type_params=[];node._fields+=('type_params',)
    return hashlib.sha256(ast.dump(tree,include_attributes=False).encode()).hexdigest()


def review(contracts,source_roots):
    result=deepcopy(contracts);reviewed=[]
    for root in source_roots:
        root=Path(root).resolve()
        manifest=ET.fromstring((root/'addon.xml').read_bytes())
        addon_id=manifest.get('id','')
        entry=manifest.find('extension[@point="xbmc.python.pluginsource"]')
        if entry is None:continue
        for index,spec in enumerate(result['contracts']):
            if spec['entrypoint']!=entry.get('library'):continue
            pins={};target_shapes={}
            try:
                for name,expected in spec['sources'].items():
                    path=root/name
                    if not path.resolve().is_relative_to(root) or path.is_symlink() or path.stat().st_size>512*1024:
                        raise ValueError('Unsafe reviewed source')
                    raw=path.read_bytes()
                    target=fingerprint(raw,addon_id)
                    if expected not in (target,fingerprint(raw,addon_id,python312=True)):
                        raise ValueError('Unreviewed executable shape')
                    target_shapes[name]=target
                    pins[name]=hashlib.sha256(raw).hexdigest()
            except (OSError,ValueError,SyntaxError,UnicodeError):continue
            if spec.get('exact_sources') and spec['exact_sources']!=pins:
                # An existing reviewed exact set is retained. No new interface
                # or arbitrary provider update replaces it by filename.
                continue
            spec['exact_sources']=pins
            spec['sources']=target_shapes
            reviewed.append(dict(contract=index,observed_provider=addon_id,
                                 observed_version=manifest.get('version'),source_pins=pins))
    return result,reviewed


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--contracts',type=Path,required=True)
    p.add_argument('--sources',type=Path,nargs='+',required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();value,proof=review(json.loads(a.contracts.read_text()),a.sources)
    a.out.write_text(json.dumps(dict(contracts=value,reviewed=proof),indent=2)+'\n')
