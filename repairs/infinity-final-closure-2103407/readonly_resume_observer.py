"""Copy only the actual pure projection functions into the disposable observer.

This grants no imports into production first-party code, writer authority,
checkpoint identity, service entry or provider permission.
"""
import ast
import hashlib
from pathlib import Path
from zipfile import ZipFile

PRELUDE='from copy import deepcopy\nimport hashlib,json,re,time\n'
CONSTANTS={'SCHEMA','KEY_RE','BUCKET_LIMITS'}
FORBIDDEN={'load','save','load_view','_view_data','atomic_json','read_json','persistence_scope',
           'sync_kodi_playcount','queue_kodi_sync','flush_kodi_sync','publish_home'}


def source(raw):
    tree=ast.parse(raw)
    functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    selected={'entries'}
    while True:
        referenced={n.id for name in selected for n in ast.walk(functions[name]) if isinstance(n,ast.Name)}
        needed=referenced & set(functions)
        if needed<=selected:break
        selected|=needed
    if selected & FORBIDDEN:raise ValueError('Projection gained a persistence or runtime dependency')
    nodes=[]
    for node in tree.body:
        if isinstance(node,ast.FunctionDef) and node.name in selected:nodes.append(node)
        elif isinstance(node,ast.Assign) and any(isinstance(n,ast.Name) and n.id in CONSTANTS for n in node.targets):
            nodes.append(node)
    for node in nodes:
        for call in ast.walk(node):
            if isinstance(call,ast.Call) and isinstance(call.func,ast.Attribute) and call.func.attr in {
                    'write_text','write_bytes','open','unlink','executeJSONRPC','executebuiltin','mkdir','replace','remove'}:
                raise ValueError('Projection gained an external effect')
    text=PRELUDE+ast.unparse(ast.Module(body=nodes,type_ignores=[]))+'\n'
    compile(text,'readonly_resume_view.py','exec',dont_inherit=True)
    return text,sorted(selected)


def stage(apk,expected_sha,fixture):
    from package_candidate import sha
    if sha(apk)!=expected_sha:raise ValueError('Exact candidate required for observer source')
    with ZipFile(apk) as z:raw=z.read('assets/addons/script.infinity.commandcenter/resume_hub.py')
    text,functions=source(raw)
    target=Path(fixture)/'readonly_resume_view.py'
    if target.exists() or target.is_symlink():raise ValueError('Observer source already exists')
    target.write_text(text)
    return dict(original_resume_source_sha256=hashlib.sha256(raw).hexdigest(),
                observer_source_sha256=hashlib.sha256(text.encode()).hexdigest(),functions=functions,
                writer_authority_granted=False,production_imports=False)
