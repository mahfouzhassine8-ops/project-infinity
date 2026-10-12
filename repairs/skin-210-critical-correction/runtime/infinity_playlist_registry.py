"""Resolve skin presets against an installed provider's read-only source registry.

No provider imports, execution, downloads, playlist parsing or profile writes.
Unknown provider contracts keep explicit browsing available without guessing IDs.
"""
import ast
import hashlib
import json
from urllib.parse import urlencode

PROVIDER = 'plugin.video.playlistbrowser'
ROOT = 'plugin://' + PROVIDER + '/'
CONTRACTS = {'729c2b23d66a52e13d15e91263fcbb4188f50a8cf9074d1806d0079e07980c4a': 'stable', 'f79a28ac639d944d6dc470f6f1cac374e76be0f3d14c077b4446a48061a20813': 'sequential'}
FUNCTIONS = ('load_baked_in_sources', 'load_sources', 'list_channels_by_group', 'router')


def canonical(node):
    # Python 3.12 added an empty type_params field; it is irrelevant to these
    # ordinary functions. Avoid interpreter-version-dependent ast.dump hashes.
    if isinstance(node, ast.AST):
        return [type(node).__name__, [[name, canonical(value)] for name, value in ast.iter_fields(node)
                                    if name != 'type_params']]
    if isinstance(node, list):
        return [canonical(value) for value in node]
    return node


def contract(code):
    if not isinstance(code, str) or len(code) > 1024 * 1024:
        return ''
    tree = ast.parse(code)
    functions = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in FUNCTIONS:
            if node.name in functions:
                return ''
            functions[node.name] = canonical(node)
    if set(functions) != set(FUNCTIONS):
        return ''
    payload = json.dumps(functions, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def pick(item, *keys):
    return next((item[key] for key in keys if item.get(key)), '')


def registry(data, mode):
    if not isinstance(data, list) or len(data) > 512:
        return []
    reserved, used, result = set(), set(), []
    if mode == 'stable':
        for item in data:
            if not isinstance(item, dict) or 'source_id' not in item:
                continue
            try:
                number = int(item['source_id'])
                if number >= 100:
                    reserved.add(number)
            except (ValueError, TypeError):
                pass
            except OverflowError:
                return []
    next_id = 100
    for item in data:
        if not isinstance(item, dict):
            continue
        if mode == 'stable' and 'source_id' in item:
            try:
                number = int(item['source_id'])
            except (ValueError, TypeError):
                continue
            except OverflowError:
                return []
            if number < 100 or number in used:
                continue
        else:
            if mode == 'stable':
                while next_id in reserved or next_id in used:
                    next_id += 1
            number = next_id
            if mode == 'stable':
                next_id += 1
        media = pick(item, 'm3u', 'm3u_url', 'M3U', 'M3U_URL', 'json', 'json_url', 'JSON', 'JSON_URL')
        alias = pick(item, 'alias_source') if mode == 'stable' else ''
        group = pick(item, 'alias_group') if mode == 'stable' else ''
        if not (media or (alias and group)):
            continue
        name = pick(item, 'name', 'Name', 'display_name') or 'Baked ' + str(number)
        result.append({'id': number, 'name': name, 'alias': alias, 'group': group})
        used.add(number)
        if mode == 'sequential':
            next_id += 1
    return result


def path(number, group):
    return ROOT + '?' + urlencode({'action': 'channels_by_group', 'src': str(number), 'group': group})


def resolve(code, raw):
    result = {'tv': '', 'sports': '', 'status': 'unsupported', 'contract': ''}
    try:
        identity = contract(code)
        result['contract'] = identity
        mode = CONTRACTS.get(identity)
        if not mode:
            return result
        if not isinstance(raw, str) or len(raw) > 256 * 1024:
            return dict(result, status='invalid-registry')
        sources = registry(json.loads(raw), mode)
        # Keep existing, still-valid 100 routes on older installations. Retire
        # the assumption that every provider release assigns that number.
        if any(source['id'] == 100 for source in sources):
            return dict(result, tv=path(100, 'TV'), sports=path(100, 'Live Events'), status='legacy-valid')
        for key, group, prefix in [('tv', 'TV', 'For TV Widget'),
                                   ('sports', 'Live Events', 'For Sports Widget')]:
            matches = []
            for source in sources:
                if (not isinstance(source['name'], str) or not source['name'].startswith(prefix) or
                        not isinstance(source['group'], str) or source['group'].strip() != group):
                    continue
                # Mirror the provider's alias-target rule; no alias chaining.
                target = next((other for other in sources
                               if other['name'] == source['alias'] and other['id'] != source['id']), None)
                if target and not target['alias']:
                    matches.append(source)
            if len(matches) == 1:
                result[key] = path(matches[0]['id'], group)
        result['status'] = 'resolved' if result['tv'] and result['sports'] else 'browse-required'
    except (ValueError, TypeError, SyntaxError, RecursionError, OverflowError):
        result['status'] = 'invalid-registry'
    return result
