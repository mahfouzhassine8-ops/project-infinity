"""Read-only native movie/TV Search recognition for compatible provider updates.

Fallback only after the existing reviewed whole-file source contracts fail.
Only the provider's own *search* operation is granted. Every file participating
in this proof remains sha256-pinned to the original installed bytes and is
rechecked at dispatch by infinity_search.route. No provider code is executed.
"""
from __future__ import annotations

import ast
from copy import deepcopy
import hashlib

MAX_SOURCE = 512 * 1024
MAX_AST_NODES = 60000


class Unverified(ValueError):
    pass


def _shape(node):
    return ast.dump(node, include_attributes=False)


def _expr(text):
    return ast.parse(text, mode="eval").body


def _same(node, text):
    return _shape(node) == _shape(_expr(text))


def _contains(node, text):
    return any(_same(n, text) for n in ast.walk(node) if isinstance(n, ast.expr))


def _method(nodes, name):
    hits = [n for n in nodes if isinstance(n, ast.FunctionDef) and n.name == name]
    if len(hits) != 1:
        raise Unverified("Missing or ambiguous native search method")
    return hits[0]


def _class(nodes, name):
    hits = [n for n in nodes if isinstance(n, ast.ClassDef) and n.name == name]
    if len(hits) != 1:
        raise Unverified("Missing or ambiguous native search receiver")
    return hits[0]


def _branch(fn, text):
    hits = [n for n in ast.walk(fn) if isinstance(n, ast.If) and _same(n.test, text)]
    if len(hits) != 1:
        raise Unverified("Missing or ambiguous native search action")
    return hits[0]


def _reading(reader):
    pins = {}
    parsed = {}

    def get(name):
        if (not isinstance(name, str) or not name or name.startswith("/") or
                ".." in name.split("/") or len(name) > 220):
            raise Unverified("Unowned provider source")
        if name not in parsed:
            raw = reader(name)  # Original bounded, link-safe reader; not an import.
            if not isinstance(raw, bytes) or len(raw) > MAX_SOURCE:
                raise Unverified("Invalid provider source length")
            try:
                tree = ast.parse(raw.decode("utf-8-sig"))
            except (SyntaxError, UnicodeError, RecursionError) as error:
                raise Unverified("Unparseable provider source") from error
            if sum(1 for _ in ast.walk(tree)) > MAX_AST_NODES:
                raise Unverified("Provider AST exceeds maximum")
            parsed[name] = tree
            pins[name] = hashlib.sha256(raw).hexdigest()
        return parsed[name]

    return get, pins


def _umbrella(get, contract, media):
    """Prove the original native action dispatch and query name, not full menus."""
    if contract.get("query_key") != "name":
        raise Unverified("Unverified native query parameter")
    action = contract.get("params", {}).get("action")
    expected = {"movie": "movieSearchterm", "tv": "tvSearchterm"}.get(media)
    if action != expected:
        raise Unverified("Unreviewed native action")

    entry = get("umbrella.py")
    if not _contains(entry, "router.router(sys.argv[2])"):
        raise Unverified("Original native entrypoint no longer dispatches")
    router = _method(get("resources/lib/modules/router.py").body, "router")
    if not _contains(router, "params.get('action')") or not _contains(router, "params.get('name')"):
        raise Unverified("Native action/query origin changed")
    # The query string is parsed from the plugin's own original argument.
    if not any(isinstance(n, ast.Call) and _same(n, "dict(parse_qsl(argv2.replace('?', '')))")
               for n in ast.walk(router)):
        raise Unverified("Original native URL parser changed")

    module, cls = (("movies", "Movies") if media == "movie" else ("tvshows", "TVshows"))
    body = _branch(router, "action == " + repr(action)).body
    if len(body) != 2:
        raise Unverified("Native search branch changed")
    required_import = "resources.lib.menus"
    source_import = body[0]
    if (not isinstance(source_import, ast.ImportFrom) or
            source_import.module != required_import or len(source_import.names) != 1 or
            source_import.names[0].name != module or
            source_import.names[0].asname is not None):
        raise Unverified("Native search target import changed")
    if not (isinstance(body[1], ast.Expr) and
            _same(body[1].value, module+"."+cls+"().search_term(name)")):
        raise Unverified("Native search target/query forwarding changed")
    menu = _class(get("resources/lib/menus/"+module+".py").body, cls)
    method = _method(menu.body, "search_term")
    if len(method.args.args) < 2 or method.args.args[0].arg != "self":
        raise Unverified("Native search receiver signature changed")


def _pov(get, contract, media):
    """Prove POV's native mode->Menu->action/query chain, not unrelated routes."""
    expected = {
        "movie": ("build_movie_list", "tmdb_movies_search", "menus.movies"),
        "tv": ("build_tvshow_list", "tmdb_tv_search", "menus.tvshows")
    }.get(media)
    if expected is None:
        raise Unverified("Unreviewed media type")
    mode, action, module = expected
    if (contract.get("query_key") != "query" or
            contract.get("params") != {"mode": mode, "action": action}):
        raise Unverified("Native mode/action/search arguments changed")

    entry = get("resources/lib/router.py")
    if not _contains(entry, "Router()()"):
        raise Unverified("Native entrypoint no longer uses Router")
    source = get("resources/lib/modules/entry.py")
    assignment = [n for n in source.body if isinstance(n, ast.Assign) and
                  len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and
                  n.targets[0].id == "POV_ROUTES"]
    if len(assignment) != 1 or not isinstance(assignment[0].value, ast.Dict):
        raise Unverified("Native mode table changed")
    table = assignment[0].value
    entries = [(k.value, v) for k,v in zip(table.keys,table.values) if
               isinstance(k, ast.Constant) and isinstance(k.value, str)]
    if len(entries) != len(table.keys) or len(set(k for k,v in entries)) != len(entries):
        raise Unverified("Native mode table uses dynamic or duplicate routes")
    targets = [v for k,v in entries if k == mode]
    if (len(targets) != 1 or
            not _same(targets[0], "lambda p: _import("+repr(module)+", 'Menu')(p).run()")):
        raise Unverified("Native mode target changed")

    routing = _method(source.body, "routing")
    for required in ("kodi_utils.parsed_query(sys_obj.argv[2])",
                     "params.get('mode', 'navigator.main')",
                     "mode in POV_ROUTES",
                     "POV_ROUTES[mode](params)"):
        if not _contains(routing, required):
            raise Unverified("Native router no longer forwards mode and query")
    if not _contains(_method(_class(source.body, "Router").body, "__call__"),
                     "routing(__import__('sys'))"):
        raise Unverified("Native router owner changed")

    menu = _class(get("resources/lib/"+module.replace(".", "/")+".py").body, "Menu")
    init = _method(menu.body, "__init__")
    if not _contains(init, "self.params.get('action')"):
        raise Unverified("Native menu action origin changed")
    handler = _method(menu.body, "run")
    branch = _branch(handler, "self.action == "+repr(action))
    if not _contains(branch, "self.params['query']"):
        raise Unverified("Original query not passed to native menu")


def recognize(addon_id, root, specs, reader):
    """Return Search-only operations for reviewed native route families.

    The caller has already checked that addon.xml identifies this installed
    enabled provider and that spec.entrypoint equals the actual manifest.
    Unsupported sources simply remain unavailable. Other capabilities never
    inherit Search-only acceptance.
    """
    results = {}
    for spec in specs:
        family = spec.get("family")
        entry = spec.get("entrypoint")
        if (family, entry) not in (("action-list-v1", "umbrella.py"),
                                   ("mode-list-v1", "resources/lib/router.py")):
            continue
        for media in ("movie", "tv"):
            contract = spec.get("search", {}).get(media)
            if not isinstance(contract, dict):
                continue
            get, pins = _reading(reader)
            try:
                if family == "action-list-v1":
                    _umbrella(get, contract, media)
                else:
                    _pov(get, contract, media)
            except (Unverified, OSError, KeyError, ValueError, UnicodeError, RecursionError):
                continue
            # An actual reviewed route, with only the source files needed to
            # prove it. The installed exact bytes are pinned until dispatch.
            result = dict(deepcopy(contract), pins=dict(pins))
            results[(media, "search")] = dict(
                id=addon_id, root=str(root), family=family, contract=result,
                category_scope=spec.get("category_scope", {}).get(media, ""))
        if results:
            break
    return results
