"""Read-only, bounded source proofs for reviewed search-routing structures.

This module never imports or executes an add-on. Its output grants Search
only; playback, title recovery, identity lookup and saved-route memory are
separate capabilities. The caller must rehash every returned source at dispatch.
"""
from __future__ import annotations
import ast
from copy import deepcopy
import hashlib
import xml.etree.ElementTree as ET

API=1
MAX_SOURCE=512*1024
MAX_NODES=60000


class Unverified(ValueError):pass


def tree(raw):
    if not isinstance(raw,bytes) or len(raw)>MAX_SOURCE:raise Unverified('Source size or type')
    try:result=ast.parse(raw)
    except (SyntaxError,ValueError,RecursionError,UnicodeError) as error:raise Unverified('Unparseable source') from error
    if sum(1 for _ in ast.walk(result))>MAX_NODES:raise Unverified('Source complexity')
    return result


def shape(node):return ast.dump(node,include_attributes=False)


def reviewed_shape(node,addon_id=''):
    """Ignore comments/docstrings and branding, never executable statements."""
    class Normalize(ast.NodeTransformer):
        def visit_Constant(self,node):
            if addon_id and isinstance(node.value,str):
                node.value=node.value.replace(addon_id,'$PROVIDER')
            return node
        def generic_visit(self,node):
            node=super().generic_visit(node);body=getattr(node,'body',None)
            if isinstance(body,list) and body and isinstance(body[0],ast.Expr) and isinstance(body[0].value,ast.Constant) and isinstance(body[0].value.value,str):
                del body[0]
            return node
    value=Normalize().visit(deepcopy(node))
    for item in ast.walk(value):
        if hasattr(item,'type_params'):
            if item.type_params:raise Unverified('Unsupported provider Python generic syntax')
            item._fields=tuple(field for field in item._fields if field!='type_params')
    return hashlib.sha256(shape(value).encode()).hexdigest()


def expr(text):return ast.parse(text,mode='eval').body


def same(node,text):return shape(node)==shape(expr(text))


def literal(node):
    try:return ast.literal_eval(node)
    except (ValueError,TypeError,SyntaxError,RecursionError) as error:raise Unverified('Dynamic value') from error


def function(nodes,name):
    found=[n for n in nodes if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]
    if len(found)!=1 or isinstance(found[0],ast.AsyncFunctionDef):raise Unverified('Ambiguous function')
    return found[0]


def contains(node,expression):return any(same(n,expression) for n in ast.walk(node) if isinstance(n,ast.expr))


def assignments(nodes):
    values={}
    for node in nodes:
        if isinstance(node,ast.Assign):
            for target in node.targets:
                if isinstance(target,ast.Name):
                    if target.id in values:raise Unverified('Reassigned routing value')
                    values[target.id]=node.value
    return values


def parameter_reader(node):
    """The actual URL query dictionary, not an arbitrary provider variable."""
    return same(node,"dict(parse_qsl(sys.argv[2][1:], keep_blank_values=True))")


def mode_test(node,value):
    """Evaluate only literal routing predicates. No eval or provider calls."""
    if isinstance(node,ast.Compare) and len(node.ops)==len(node.comparators)==1:
        left=node.left;right=node.comparators[0];op=node.ops[0]
        if isinstance(left,ast.Name) and left.id=='mode':
            constant=literal(right)
            if isinstance(op,ast.Eq):return value==constant
            if isinstance(op,ast.NotEq):return value!=constant
            if isinstance(op,ast.In):return value in constant
            if isinstance(op,ast.NotIn):return value not in constant
        if isinstance(right,ast.Name) and right.id=='mode':
            constant=literal(left)
            if isinstance(op,ast.In):return constant in value
            if isinstance(op,ast.NotIn):return constant not in value
    if (isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and
        isinstance(node.func.value,ast.Name) and node.func.value.id=='mode' and
        node.func.attr in ('startswith','endswith') and len(node.args)==1 and not node.keywords):
        argument=literal(node.args[0])
        if not isinstance(argument,(str,tuple)):raise Unverified('Dynamic mode predicate')
        return getattr(value,node.func.attr)(argument)
    raise Unverified('Unknown routing predicate')


def chosen_return(statements,mode):
    """Follow only proven literal mode branches; unknown returning branches veto."""
    for statement in statements:
        if isinstance(statement,ast.Return):return statement.value
        if isinstance(statement,ast.If):
            try:chosen=statement.body if mode_test(statement.test,mode) else statement.orelse
            except Unverified:
                if any(isinstance(n,ast.Return) for n in ast.walk(statement)):
                    raise Unverified('An unknown condition can change the destination')
                continue # Initialization may fail; it cannot grant another route.
            answer=chosen_return(chosen,mode)
            if answer is not None:return answer
    return None


def class_receiver(module,class_name,action):
    classes=[n for n in module.body if isinstance(n,ast.ClassDef) and n.name==class_name]
    if len(classes)!=1:raise Unverified('Ambiguous title receiver')
    cls=classes[0];constants=assignments(cls.body)
    special=literal(constants.get('special',ast.Constant(None)))
    if not isinstance(special,(tuple,list)) or action not in special:raise Unverified('Search not accepted by receiver')
    for key in ('main','personal','most_watched'):
        if key in constants and action in literal(constants[key]):raise Unverified('Ambiguous search category')
    init=function(cls.body,'__init__')
    if not (contains(init,'params') and contains(init,'self.params.get') and
        contains(init,"self.params_get('action', None)")):
        raise Unverified('Query dictionary is not forwarded')
    fetch=function(cls.body,'fetch_list')
    if not contains(fetch,"self.params_get('key_id') or self.params_get('query')"):
        # Explicit None defaults are equivalent but still parsed as data.
        if not contains(fetch,"self.params_get('key_id', None) or self.params_get('query')"):
            raise Unverified('Query parameter is not forwarded')
    branches=[n for n in ast.walk(fetch) if isinstance(n,ast.If) and same(n.test,'self.action in self.special')]
    if len(branches)!=1:raise Unverified('Ambiguous special-search branch')
    branch=branches[0]
    if not (contains(branch,'function(key_id, page_no)') and contains(branch,"data['results']")):
        raise Unverified('Search result receiver changed')
    if not contains(fetch,"'apis.%s_api' % self.action.split('_')[0]"):
        raise Unverified('Dynamic API module mapping')
    if not contains(fetch,'manual_function_import(var_module, import_function)'):
        raise Unverified('API function mapping changed')
    # Check the exact assignment which connects action to imported function.
    if not any(isinstance(n,ast.Assign) and len(n.targets)==1 and
        isinstance(n.targets[0],ast.Tuple) and all(isinstance(x,ast.Name) for x in n.targets[0].elts) and
        [x.id for x in n.targets[0].elts]==['var_module','import_function'] and
        same(n.value,"('apis.%s_api' % self.action.split('_')[0], self.action)") for n in ast.walk(fetch)):
        raise Unverified('API action is not the supplied literal')


def api_searches(module):
    """Derive media type from an actual search URI and query argument position."""
    found={}
    for fn in module.body:
        if not isinstance(fn,ast.FunctionDef) or len(fn.args.args)!=2:continue
        query,page=(arg.arg for arg in fn.args.args)
        for node in fn.body:
            if not isinstance(node,ast.Assign) or not any(isinstance(t,ast.Name) and t.id=='url' for t in node.targets):continue
            value=node.value
            if not (isinstance(value,ast.BinOp) and isinstance(value.op,ast.Mod) and
                isinstance(value.left,ast.Constant) and isinstance(value.left.value,str) and isinstance(value.right,ast.Tuple)):
                continue
            template=value.left.value
            media='movie' if template.startswith('https://api.themoviedb.org/3/search/movie?') else 'tv' if template.startswith('https://api.themoviedb.org/3/search/tv?') else None
            if not media or template.count('query=%s')!=1:continue
            position=template.split('query=%s')[0].count('%s')
            values=value.right.elts
            if position>=len(values) or not isinstance(values[position],ast.Name) or values[position].id!=query:continue
            if not contains(fn,'tmdb_lists_get(string, url)'):continue
            if media in found:raise Unverified('More than one search action for a category')
            found[media]=fn.name
    return found


def mode_class_search(read_source,entrypoint,policy,addon_id=''):
    """Return operation-only routes plus every byte pinned during recognition.

    read_source must be the existing canonical, bounded source reader. No
    installed/disabled state is inferred here; inventory and dispatch own it.
    """
    if policy.get('schema')!=1 or policy.get('family')!='mode-class-json-v1' or entrypoint!=policy.get('entrypoint'):
        raise Unverified('Unknown reviewed search family')
    pins={};parsed={}
    def load(name):
        if name.startswith('/') or '..' in name.split('/') or len(name)>240:raise Unverified('Unowned source path')
        if name not in parsed:
            raw=read_source(name);parsed[name]=tree(raw)
            # Dataflow recognition below is deliberately not a general Python
            # proof system. Every participating module must first match this
            # reviewed executable AST family, including early returns, import
            # aliases, decorators, helper replacement and query mutations.
            if reviewed_shape(parsed[name],addon_id)!=policy.get('shapes',{}).get(name):
                raise Unverified('Installed routing structure is not reviewed')
            pins[name]=hashlib.sha256(raw).hexdigest()
        return parsed[name]
    entry=load(entrypoint)
    if not any(isinstance(n,ast.ImportFrom) and n.module=='modules.router' and any(a.name=='routing' and a.asname is None for a in n.names) for n in entry.body):
        raise Unverified('Unsupported entrypoint family')
    if sum(1 for n in entry.body if isinstance(n,ast.Expr) and same(n.value,'routing(sys)'))!=1:
        raise Unverified('Entrypoint routing changed')
    prefix=entrypoint.rsplit('/',1)[0]+'/' if '/' in entrypoint else ''
    router=load(prefix+'modules/router.py');routing=function(router.body,'routing')
    values=assignments(routing.body)
    if 'params' not in values or not parameter_reader(values['params']) or not same(values.get('mode',ast.Constant(None)),"params.get('mode', 'navigator.main')"):
        raise Unverified('Mode or query origin changed')
    api=load(prefix+'apis/tmdb_api.py');searches=api_searches(api);operations={}
    branches=[n for n in ast.walk(routing) if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and
        len(n.test.ops)==1 and isinstance(n.test.ops[0],ast.Eq) and isinstance(n.test.left,ast.Name) and n.test.left.id=='mode' and
        len(n.test.comparators)==1 and isinstance(n.test.comparators[0],ast.Constant) and isinstance(n.test.comparators[0].value,str)]
    for media,action in searches.items():
        class_name='Movies' if media=='movie' else 'TVShows';module_name='indexers.movies' if media=='movie' else 'indexers.tvshows'
        modes=[]
        for branch in branches:
            mode=branch.test.comparators[0].value
            if not mode or any(c not in 'abcdefghijklmnopqrstuvwxyz_' for c in mode):continue
            try:call=chosen_return(routing.body,mode)
            except Unverified:continue
            if call is not None and same(call,class_name+'(params).fetch_list()') and any(
                isinstance(n,ast.ImportFrom) and n.module==module_name and any(a.name==class_name and a.asname is None for a in n.names)
                for n in branch.body):modes.append(mode)
        if len(modes)!=1:continue
        try:class_receiver(load(prefix+module_name.replace('.','/')+'.py'),class_name,action)
        except Unverified:continue # Verify each requested media category independently.
        operations[media]=dict(params={'mode':modes[0],'action':action},query_key='query',
            structural_family='mode-class-json-v1')
    if not operations:raise Unverified('No proven movie or TV search operation')
    for contract in operations.values():contract['pins']=dict(pins)
    return operations


def recognize_mode_class(addon_id,root,manifest_raw,policy):
    from saved_navigation import _source
    manifest=ET.fromstring(manifest_raw)
    extension=manifest.find('extension[@point="xbmc.python.pluginsource"]')
    if manifest.get('id')!=addon_id or extension is None:return {}
    entrypoint=extension.get('library','')
    if entrypoint!=policy.get('entrypoint'):return {}
    operations=mode_class_search(lambda name:_source(root,name),entrypoint,policy,addon_id)
    for contract in operations.values():
        contract['pins']['addon.xml']=hashlib.sha256(manifest_raw).hexdigest()
    return {(media,'search'):dict(id=addon_id,root=str(root),family='mode-class-json-v1',contract=contract)
            for media,contract in operations.items()}
