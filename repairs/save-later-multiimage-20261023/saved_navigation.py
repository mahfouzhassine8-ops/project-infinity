"""Shared failure-only recovery and verified per-identity navigation memory.

Original working routes stay direct. Native observed results authorize a route
preference only after the exact selected media opens. Local tracking records and
provider data are never rewritten to hide a failed route.
"""
from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import threading
import time
import uuid
from urllib.parse import parse_qs, unquote, urlencode, urlsplit
import xml.etree.ElementTree as ET

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

import infinity_search as search
import resume_hub as hub
from common import persistence_scope

CC = 'script.infinity.commandcenter'
MAX_SOURCE = 512 * 1024


class Unavailable(RuntimeError):
    pass


class Cancelled(Unavailable):
    pass


def _trace(stage, **fields):
    # Existing timing export accepts only its established stage enum. Keep
    # navigation observations separate; never call them persistence receipts.
    row = dict(schema=1, stage=stage, epoch_ms=round(time.time()*1000),
               monotonic_ms=round(time.monotonic()*1000, 3), **fields)
    try:
        xbmc.log('INFINITY_SAVED_NAVIGATION ' + json.dumps(row, sort_keys=True), xbmc.LOGINFO)
    except Exception:
        pass


def fingerprint(raw, addon_id):
    """Reviewed API shape, independent of name, version, comments and docstrings.

    This is a compatibility contract, not an assertion about provider trust or
    persistence. Original raw bytes are also pinned for the whole invocation.
    No arbitrary declaration from an unfamiliar add-on grants compatibility.
    """
    tree = ast.parse(raw.decode('utf-8-sig'))
    class Canonical(ast.NodeTransformer):
        def visit_Constant(self, node):
            if isinstance(node.value, str):
                node.value = node.value.replace(addon_id, '$PROVIDER')
            return node
        def generic_visit(self, node):
            node = super().generic_visit(node)
            body = getattr(node, 'body', None)
            if isinstance(body, list) and body and isinstance(body[0], ast.Expr):
                value = body[0].value
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    del body[0]
            return node
    tree = Canonical().visit(tree)
    return hashlib.sha256(ast.dump(tree, include_attributes=False).encode()).hexdigest()


def _source(root, name):
    path = root / name
    if (Path(name).is_absolute() or '..' in Path(name).parts or
            not path.resolve().is_relative_to(root) or
            any(p.is_symlink() for p in (path, *path.parents) if p != root.parent)):
        raise ValueError('Provider source path is not verified.')
    with path.open('rb') as stream:
        raw = stream.read(MAX_SOURCE + 1)
    if len(raw) > MAX_SOURCE:
        raise ValueError('Provider source exceeds the verification limit.')
    return raw


def capability(addon_id, root, media, specs):
    """Match installed API behavior, not an add-on-name allowlist."""
    root = Path(root).resolve()
    manifest_raw = _source(root, 'addon.xml')
    if b'<!DOCTYPE' in manifest_raw:
        raise ValueError('Provider manifest is not supported.')
    manifest = ET.fromstring(manifest_raw)
    extension = manifest.find('extension[@point="xbmc.python.pluginsource"]')
    if manifest.get('id') != addon_id or extension is None:
        return None
    for spec in specs:
        if extension.get('library') != spec['entrypoint']:
            continue
        pins = {'addon.xml': hashlib.sha256(manifest_raw).hexdigest()}
        try:
            for name, pin in spec['sources'].items():
                raw = _source(root, name)
                if fingerprint(raw, addon_id) != pin:
                    raise ValueError('Navigation API differs from reviewed contract.')
                pins[name] = hashlib.sha256(raw).hexdigest()
        except (OSError, ValueError, SyntaxError, UnicodeError):
            continue
        query = dict(spec['search'][media], pins=pins)
        return dict(id=addon_id, root=str(root), family=spec['family'], contract=query)
    return None


def available(media):
    root = xbmcaddon.Addon(CC).getAddonInfo('path').rstrip('/')
    stream = xbmcvfs.File(root + '/NAVIGATION-CONTRACTS.json')
    try:
        raw = stream.readBytes(65537)
    finally:
        stream.close()
    if not raw or len(raw) > 65536:
        raise Unavailable('The saved navigation contracts could not be verified.')
    specs = json.loads(bytes(raw).decode('utf-8'))['contracts']
    response = search.rpc('Addons.GetAddons', dict(type='xbmc.addon.video', enabled=True,
                         properties=['name', 'path', 'version']))
    if 'error' in response:
        raise Unavailable('Kodi could not enumerate installed providers.')
    ready, unsupported = [], []
    for row in response.get('result', {}).get('addons', []):
        aid = row.get('addonid', '')
        if not re.fullmatch(r'plugin\.[A-Za-z0-9._-]{1,170}', aid):
            continue
        try:
            addon = xbmcaddon.Addon(aid)
            root = xbmcvfs.translatePath(addon.getAddonInfo('path'))
            provider = capability(aid, root, media, specs)
            if provider:
                provider['name'] = row.get('name') or aid
                ready.append(provider)
            else:
                unsupported.append(aid)
        except (OSError, RuntimeError, ValueError, ET.ParseError):
            unsupported.append(aid)
    return ready, unsupported


def _same_ids(left, right):
    left, right = hub.verified_ids(left), hub.verified_ids(right)
    common = set(left) & set(right)
    return bool(common) and all(left[k] == right[k] for k in common)


def _params(provider, path):
    if not isinstance(path, str) or len(path) > 65536 or any(ord(c) < 32 for c in path):
        raise Unavailable('Provider returned an invalid destination.')
    url = urlsplit(path)
    if (url.scheme != 'plugin' or url.netloc != provider['id'] or
            url.path not in ('', '/') or url.fragment or '|' in path):
        raise Unavailable('Provider returned an unrelated destination.')
    values = parse_qs(url.query, keep_blank_values=True)
    if any(len(v) != 1 for v in values.values()):
        raise Unavailable('Provider returned ambiguous destination parameters.')
    return {k: v[0] for k, v in values.items()}


def destination(provider, row):
    """Validate a FRESH producer result against its reviewed router and decoder."""
    path = row.get('file', '')
    p = _params(provider, path)
    kind, family = row.get('type'), provider['family']
    ids = row.get('uniqueid', {})
    if family == 'mode-list-v1':
        routes = {'tvshow': ('build_season_list', 'build_episode_list'),
                  'season': ('build_episode_list',), 'episode': ('play_media',),
                  'movie': ('play_media',)}
        route_ids = {'tmdb': p.get('tmdb_id')}
        good = p.get('mode') in routes.get(kind, ()) and _same_ids(ids, route_ids)
        if kind in ('episode', 'movie'):
            good = good and p.get('mediatype') == kind
        if kind == 'tvshow' and p.get('mode') == 'build_episode_list':
            good = good and p.get('season') == 'all'
        if kind in ('season', 'episode'):
            good = good and hub.episode_number(p.get('season')) == hub.episode_number(row.get('season'))
        if kind == 'episode':
            good = good and hub.episode_number(p.get('episode')) == hub.episode_number(row.get('episode'))
    elif family == 'action-list-v1':
        routes = {'tvshow': ('seasons', 'episodes'), 'season': ('episodes',),
                  'movie': ('play', 'play_Item'), 'episode': ('play', 'play_Item')}
        route_ids = {k: p[k] for k in ('tmdb', 'imdb', 'tvdb') if k in p}
        good = p.get('action') in routes.get(kind, ()) and _same_ids(ids, route_ids)
        if kind in ('season', 'episode'):
            good = good and hub.episode_number(p.get('season')) == hub.episode_number(row.get('season'))
        if kind == 'episode':
            good = good and hub.episode_number(p.get('episode')) == hub.episode_number(row.get('episode'))
        if kind == 'movie':
            good = good and not any(p.get(k) not in (None, '', 'None') for k in ('season', 'episode'))
    elif family == 'json-args-list-v1':
        routes = {'tvshow': ('showSeasons', 'flatEpisodes'), 'season': ('seasonEpisodes',),
                  'movie': ('getSources',), 'episode': ('getSources',)}
        try:
            args = json.loads(unquote(p.get('action_args', '')))
            good = (p.get('action') in routes.get(kind, ()) and isinstance(args, dict) and
                    args.get('mediatype') == kind and str(args.get('trakt_id', '')).isdigit())
        except (TypeError, ValueError):
            good = False
        # The pinned list builder/globals bind args and unique IDs to the SAME
        # item. A saved Trakt ID is never guessed from its title or a TMDb ID.
    else:
        good = False
    if not good:
        raise Unavailable('Provider destination does not match its verified navigation contract.')
    if (kind in ('tvshow', 'season')) != (row.get('filetype') == 'directory'):
        raise Unavailable('Provider returned an unexpected destination type.')
    return path


def _lookup_directory(path, home, progress):
    """Bound only failure-recovery lookups; retain the original native owner.

    Cold provider imports on Android exceeded Search's 20-second allowance.
    This separate intent uses the same three-slot lease, cancellation and real
    invocation retirement. The engine, not Python, owns its 60-second deadline.
    """
    if home.getProperty('Infinity.SavedNavigation.Lookup.Protocol') != '1':
        search._leased_directory('plugin://' + CC + '/?action=search-probe', home)
    if home.getProperty('Infinity.SavedNavigation.Lookup.Protocol') != '1':
        raise Unavailable('The installed engine lacks the required bounded navigation protocol.')
    monitor = xbmc.Monitor()
    if monitor.abortRequested() or progress.iscanceled():
        raise Cancelled('Navigation was cancelled; the saved entry was kept.')
    token = uuid.uuid4().hex
    proof = hashlib.sha256(path.encode('utf-8')).hexdigest()
    keys = ['Infinity.Search.' + part + token for part in ('Request.', 'Cancel.', 'Result.')]
    intent = 'Infinity.SavedNavigation.Lookup.' + token
    output = []
    def request():
        try:
            output.append(search.rpc('Files.GetDirectory', dict(
                directory=path + '|infinity_search=' + token, media='video',
                properties=search.PROPERTIES, limits={'start': 0, 'end': search.MAX_RESULTS})))
        except (ValueError, RuntimeError):
            output.append({'error': {'message': 'provider_failed'}})
    try:
        home.setProperty(keys[0], proof)
        home.setProperty(intent, proof)
        worker = threading.Thread(target=request, name='InfinitySavedNavigationResult')
        worker.start()
        while worker.is_alive():
            if monitor.abortRequested() or progress.iscanceled():
                home.setProperty(keys[1], '1')
            worker.join(.05)
        return home.getProperty(keys[2]), output[0] if output else {'error': {}}
    finally:
        for key in (*keys, intent):
            home.clearProperty(key)


def _directory(path, provider, query, home, progress):
    # Preserve the existing engine's bounded consumer protocol and Search limit.
    # Larger, unverified request envelopes remain explicit failures.
    if len(path.encode('utf-8')) + len('|infinity_search=') + 32 > 8192:
        raise Unavailable('Provider destination exceeds the supported navigation request limit.')
    _trace('saved_navigation_request', provider=provider['id'],
                     destination_sha256=hashlib.sha256(path.encode()).hexdigest())
    search.route(provider, query)  # Raw installed source and enabled-state recheck.
    status, answer = _lookup_directory(path, home, progress)
    search.route(provider, query)
    if progress.iscanceled() or xbmc.Monitor().abortRequested():
        raise Cancelled('Navigation was cancelled; the saved entry was kept.')
    if status != 'completed' or 'error' in answer:
        # Never include an opaque URL, account token, or full provider exception.
        raise Unavailable('Provider directory request did not complete (' + (status or 'no completion receipt')[:80] + ').')
    rows = answer.get('result', {}).get('files')
    if not isinstance(rows, list):
        raise Unavailable('Provider returned no verified directory result.')
    if any(not isinstance(row, dict) for row in rows):
        raise Unavailable('Provider returned malformed directory items.')
    _trace('saved_navigation_result', provider=provider['id'], items=len(rows), status=status)
    return rows


def resolve(entry, provider, home, progress):
    identity = hub.entry_identity(entry)
    if not identity:
        raise Unavailable('This saved entry has no verified media identity. Nothing was changed.')
    if identity['scope'] == 'episode':
        raise Unavailable('This episode has only episode-scoped IDs; its parent show identity is not verified.')
    query = str(entry.get('showtitle') or entry.get('title') or entry.get('label') or '').strip()
    if not query or len(query) > 160:
        raise Unavailable('The saved entry has no usable provider query. Its identity was kept.')
    wanted = identity['kind']
    base = 'movie' if wanted == 'movie' else 'tvshow'
    search_path = search.route(provider, query)
    rows = _directory(search_path, provider, query, home, progress)
    matches = [r for r in rows if r.get('type') == base and _same_ids(identity['ids'], r.get('uniqueid'))]
    targets = {destination(provider, r) for r in matches}
    if not targets:
        raise Unavailable('Provider returned no result with this exact saved media identity. No other title was opened.')
    if len(targets) != 1:
        raise Unavailable('Provider returned multiple destinations for the saved identity. Nothing was opened.')
    target = next(iter(targets))
    if wanted in ('movie', 'tvshow'):
        # The selected provider opens the returned item through Kodi's normal
        # path. Native observation reports its actual result. Do not execute a
        # successful show twice merely to predict that second invocation.
        return target
    # Verify the show directory actually opens. A failed invocation must never
    # become a silent selection or be called a successful navigation.
    rows = _directory(target, provider, query, home, progress)
    children = [r for r in rows if r.get('type') in ('season', 'episode') and
                _same_ids(identity['ids'], r.get('uniqueid'))]
    if not children:
        raise Unavailable('Provider opened no verified seasons or episodes for this saved show.')
    if wanted == 'tvshow':
        for row in children:
            destination(provider, row)
        return target
    # Season/episode destinations are selected by exact coordinates and parent
    # IDs, never a similarly named row. At most one additional season is opened.
    selected = [r for r in children if hub.episode_number(r.get('season')) == identity['season']]
    if wanted == 'season':
        seasons = [r for r in selected if r.get('type') == 'season']
        if len(seasons) == 1:
            return destination(provider, seasons[0])
        raise Unavailable('Provider has no distinct verified destination for the saved season.')
    episodes = [r for r in selected if r.get('type') == 'episode']
    if not episodes:
        seasons = [r for r in selected if r.get('type') == 'season']
        if len(seasons) != 1:
            raise Unavailable('The saved episode season is unavailable or ambiguous.')
        rows = _directory(destination(provider, seasons[0]), provider, query, home, progress)
        episodes = [r for r in rows if r.get('type') == 'episode' and
                    _same_ids(identity['ids'], r.get('uniqueid')) and
                    hub.episode_number(r.get('season')) == identity['season']]
    selected = [r for r in episodes if hub.episode_number(r.get('episode')) == identity['episode']]
    if len(selected) != 1:
        raise Unavailable('The exact saved episode is unavailable or ambiguous.')
    return destination(provider, selected[0])


def resolve_with_choices(entry, ready, preferred, choose, attempt):
    """User selects alternatives after a failure; every attempt verifies identity.

    A provider exception is never repaired by mutating its cache, disabling its
    service, changing its Python code, or rewriting the saved record.
    """
    remaining = list(ready)
    provider = next((p for p in remaining if p['id'] == preferred), None)
    reason = 'Saved provider unavailable — open with'
    while remaining:
        if xbmc.Monitor().abortRequested():
            raise Cancelled('Navigation was cancelled; the saved entry was kept.')
        if provider is None:
            index = choose(reason, remaining)
            if not isinstance(index, int) or index < 0 or index >= len(remaining):
                raise Cancelled('No alternative was selected. The saved entry was kept.')
            provider = remaining[index]
        remaining.remove(provider)
        try:
            return provider, attempt(entry, provider)
        except Cancelled:
            raise
        except (Unavailable, OSError, ValueError, RuntimeError, TypeError, KeyError,
                AttributeError, SyntaxError) as error:
            _trace('saved_navigation_provider_failed', provider=provider['id'],
                   error_type=type(error).__name__)
            # Original provider traceback and native persistence obligations
            # remain with their original owner. No success receipt is inferred.
            if xbmc.Monitor().abortRequested():
                raise Cancelled('Navigation was cancelled; the saved entry was kept.') from error
            reason = provider['name'] + ' could not open this saved identity — open with'
            if not remaining:
                raise Unavailable(provider['name'] + ': ' + str(error)) from error
            provider = None
    raise Unavailable('No enabled provider has a verified navigation API for this saved entry.')


def direct_destination(entry, provider):
    """Only reviewed ID-addressed show/season APIs; no title-based substitution."""
    identity = hub.entry_identity(entry)
    if not identity or identity['scope'] == 'episode':
        return None
    kind, ids = identity['kind'], identity['ids']
    if kind not in ('tvshow', 'season') or not ids.get('tmdb'):
        return None
    # Recheck all raw source pins and enabled state immediately before use.
    search.route(provider)
    if provider['family'] == 'mode-list-v1':
        params = dict(mode='build_season_list' if kind == 'tvshow' else 'build_episode_list',
                      tmdb_id=ids['tmdb'])
        if kind == 'season':
            params['season'] = identity['season']
    elif provider['family'] == 'action-list-v1' and kind == 'tvshow':
        # The actual router calls Seasons.get with these identifiers, and its
        # receiver fetches TMDb show seasons by tmdb ID. Title is display text.
        params = dict(action='seasons', tmdb=ids['tmdb'], imdb=ids.get('imdb', ''),
                      tvdb=ids.get('tvdb', ''),
                      tvshowtitle=str(entry.get('showtitle') or entry.get('title') or ''),
                      year=str(entry.get('year') or ''))
    else:
        return None
    target = 'plugin://' + provider['id'] + '/?' + urlencode(params)
    row = dict(type=kind, uniqueid=ids, file=target, filetype='directory',
               season=identity.get('season'))
    return destination(provider, row)


def failure_ticket(home, key, token, original, identity, bucket='later'):
    raw = home.getProperty('Infinity.SavedNavigation.Failure')
    if not raw or len(raw) > 8192:
        raise Unavailable('No current failed navigation result is available. The saved entry was kept.')
    value = json.loads(raw)
    if (not isinstance(value, dict) or value.get('schema') != 1 or
            value.get('key') != key or value.get('token') != token or
            not re.fullmatch(r'[A-Fa-f0-9-]{32,36}', token) or
            value.get('reason') not in ('provider_directory_failed', 'provider_resolution_failed', 'provider_identity_unverified') or
            not isinstance(value.get('epoch_ms'), int) or
            not 0 <= time.time()*1000-value['epoch_ms'] <= 300000 or
            value.get('bucket', 'later') != bucket or value.get('original_sha256') != hashlib.sha256(original.encode()).hexdigest() or
            value.get('folder') != (identity['kind'] in ('tvshow', 'season')) or
            not isinstance(value.get('attempted'), list) or
            not 1 <= len(value['attempted']) <= 8 or
            any(not isinstance(p, str) or not re.fullmatch(r'[A-Za-z0-9._-]{1,180}', p)
                for p in value['attempted'])):
        raise Unavailable('The failed navigation no longer matches this saved entry. Nothing was changed.')
    return value


MEMORY = 'navigation_recovery'
BUCKETS = {'later': 'later', 'watchlist': 'watchlist', 'continue': 'items'}


def _hash(path):
    return hashlib.sha256(path.encode('utf-8')).hexdigest()


def _saved(data, key, bucket):
    if bucket not in BUCKETS or not hub.KEY_RE.fullmatch(str(key)):
        return None
    value = data.get(BUCKETS[bucket], {}).get(key)
    return dict(value, key=key) if isinstance(value, dict) else None


def _identity(value):
    if not isinstance(value, dict):
        return None
    return hub.entry_identity(dict(identity=value,
        media='movie' if value.get('kind') == 'movie' else 'tv',
        season=value.get('season', -1), episode=value.get('episode', -1)))


def remembered(data, identity):
    """Equivalent typed IDs across lists; never a title or episode-to-show merge."""
    memory = data.get(MEMORY, {})
    if not identity or not isinstance(memory, dict):
        return None
    exact = memory.get(hub.identity_key(identity))
    if isinstance(exact, dict) and hub.same_identity(identity, _identity(exact.get('identity'))):
        return exact
    matches = [v for v in memory.values() if isinstance(v, dict) and
               hub.same_identity(identity, _identity(v.get('identity')))]
    return matches[0] if len(matches) == 1 else None


def _provider_current(record, render=None):
    proof = record.get('provider')
    if not isinstance(proof, dict) or not isinstance(proof.get('contract'), dict):
        return None
    pins = proof['contract'].get('pins', {})
    if not isinstance(pins, dict) or not 1 <= len(pins) <= 64 or 'addon.xml' not in pins:
        return None
    identity = proof.get('id', '')
    if not re.fullmatch(r'plugin\.[A-Za-z0-9._-]{1,170}', identity):
        return None
    cache = render.setdefault('navigation_providers', {}) if render is not None else {}
    cache_key = (identity, json.dumps(proof['contract'], sort_keys=True))
    if cache_key in cache:
        provider = cache[cache_key]
        if provider:
            try:_params(provider, record.get('route'))
            except (Unavailable, ValueError, TypeError):return None
        return provider
    try:
        provider = deepcopy(proof)
        provider['root'] = xbmcvfs.translatePath(xbmcaddon.Addon(identity).getAddonInfo('path'))
        for name, pin in pins.items():
            if not re.fullmatch(r'[a-f0-9]{64}', str(pin)):
                raise ValueError('Invalid provider source proof')
            if hashlib.sha256(_source(Path(provider['root']).resolve(), name)).hexdigest() != pin:
                raise ValueError('Provider source changed')
        # The exact bytes were checked above; do not read/hash them a second time.
        if not xbmc.getCondVisibility('System.AddonIsEnabled(' + identity + ')'):
            raise ValueError('Provider unavailable')
        _params(provider, record.get('route'))
        cache[cache_key] = provider
    except (OSError, ValueError, RuntimeError, TypeError, KeyError, AttributeError):
        cache[cache_key] = None
    return cache[cache_key]


def navigation_target(entry, data, original, bucket, render=None):
    """No provider discovery, lookup or chooser for an unchanged working route."""
    identity = hub.entry_identity(entry)
    if bucket not in BUCKETS or not identity:
        return original
    record = remembered(data, identity)
    if record and record.get('success_verified') is True and record.get('route'):
        if (record.get('failed') is not True and record.get('route_sha256') == _hash(record['route'])
                and _provider_current(record, render)):
            return record['route']
        # Keep the last verified choice intact, even when it becomes incompatible.
        return 'plugin://' + CC + '/?' + urlencode(dict(action='saved-recovery', key=entry['key'], bucket=bucket))
    failed = record.get('failed_routes', []) if record else []
    if original and not any(isinstance(v, dict) and v.get('sha256') == _hash(original) for v in failed):
        return original
    return 'plugin://' + CC + '/?' + urlencode(dict(action='saved-recovery', key=entry['key'], bucket=bucket))


def _change_memory(profile, entry, bucket, change, snapshot=None):
    """Use the existing admitted atomic store; do not trim/merge progress buckets."""
    with persistence_scope():
        path = Path(profile) / hub.CONTINUE_FILE
        if not path.is_file() or path.stat().st_size > 8 * 1024 * 1024:
            raise Unavailable('The existing local tracking file could not be verified. Its data was retained.')
        data = hub.read_json(path, None)
        if not isinstance(data, dict) or type(data.get('schema')) is not int or data['schema'] not in (1, 2):
            raise Unavailable('The existing local tracking schema could not be verified. Its data was retained.')
        current = _saved(data, entry['key'], bucket)
        identity = hub.entry_identity(entry)
        if not current or not hub.same_identity(identity, hub.entry_identity(current)):
            raise Cancelled('The saved item changed while navigation was in progress.')
        if snapshot is not None and _source_snapshot(current, data.get('sources', {})) != snapshot:
            raise Cancelled('The original saved action changed while navigation was in progress.')
        memory = data.get(MEMORY, {})
        if not isinstance(memory, dict):
            raise Unavailable('The navigation preference store is invalid. Existing records were retained.')
        data = deepcopy(data)
        data[MEMORY] = deepcopy(memory)
        previous = remembered(data, identity)
        record = deepcopy(previous) if previous else dict(schema=1, identity=identity, failed_routes=[])
        change(record)
        record['updated'] = int(time.time())
        # Reuse a matching alias key so partial IDs cannot create divergent choices.
        key = next((k for k, v in data[MEMORY].items() if v == previous), hub.identity_key(identity)) if previous else hub.identity_key(identity)
        if previous is None and key in data[MEMORY]:
            raise Unavailable('Conflicting verified media IDs require review. Existing choices were retained.')
        data[MEMORY][key] = record
        data['revision'] = int(time.time() * 1000)
        data['updated'] = int(time.time())
        hub.atomic_json(path, data)
        hub.publish_home(data)
        return record


def _source_snapshot(entry, sources=None):
    return dict({key: entry.get(key) for key in ('source', 'stable_source')},
                legacy_preference=deepcopy((sources or {}).get(entry.get('key'))))


def _mark_failed(profile, entry, bucket, path):
    if not path:
        return
    def change(record):
        rows = record.setdefault('failed_routes', [])
        if not isinstance(rows, list):
            raise Unavailable('The navigation failure history is invalid.')
        if not any(v.get('sha256') == _hash(path) for v in rows if isinstance(v, dict)):
            rows.append(dict(sha256=_hash(path), provider=urlsplit(path).netloc, epoch_ms=int(time.time()*1000)))
        if record.get('route') == path:
            record['failed'] = True  # Last successful choice itself is never overwritten by failure.
    _change_memory(profile, entry, bucket, change)


def _property(home, name, limit=70000):
    raw = home.getProperty('Infinity.SavedNavigation.' + name)
    if not raw or len(raw) > limit:
        return {}
    try:
        value = json.loads(raw)
        return value if isinstance(value, dict) else {}
    except ValueError:
        return {}


def _protocol(home):
    if home.getProperty('Infinity.SavedNavigation.Protocol') != '2':
        search._leased_directory('plugin://' + CC + '/?action=search-probe', home)
    if home.getProperty('Infinity.SavedNavigation.Protocol') != '2':
        raise Unavailable('Install the matching Infinity navigation release before using recovery. Saved records were retained.')


def confirm_saved(profile, key, token, playback=None):
    """Only an exact native success receipt can commit a selected alternative."""
    if xbmc.getSkinDir() != 'skin.infinity.diggz' or xbmc.Monitor().abortRequested():
        return False
    home = xbmcgui.Window(10000)
    pending = _property(home, 'Pending')
    success = _property(home, 'Success')
    if (not hub.KEY_RE.fullmatch(str(key)) or not re.fullmatch(r'[A-Fa-f0-9-]{32,36}', str(token)) or
            pending.get('key') != key or pending.get('token') != token or
            success.get('schema') != 2 or success.get('key') != key or success.get('token') != token or
            not isinstance(pending.get('source_snapshot'), dict) or
            set(pending['source_snapshot']) != {'source', 'stable_source', 'legacy_preference'} or
            pending.get('bucket') not in BUCKETS or success.get('bucket') != pending['bucket'] or
            success.get('identity_verified') is not True or
            not isinstance(success.get('epoch_ms'), int) or not 0 <= time.time()*1000-success['epoch_ms'] <= 300000 or
            success.get('original_sha256') != _hash(pending.get('original', '')) or
            success.get('destination_sha256') != _hash(pending.get('route', ''))):
        return False
    identity = _identity(pending.get('identity'))
    if not identity:
        return False
    folder = identity['kind'] in ('tvshow', 'season')
    if success.get('folder') != folder or success.get('phase') != ('directory_opened' if folder else 'media_resolved'):
        return False
    if not folder:
        # Resolving a stream is not actual playback. The same native-provenance
        # item must reach the existing playback-start callback, with no retry.
        if not isinstance(playback, dict) or playback.get('infinity_original_route') != pending['route'] or playback.get('type') != identity['kind']:
            return False
    record = dict(route=pending['route'], provider=pending.get('provider'))
    if not _provider_current(record):
        return False
    data = hub.load_view(profile)
    entry = _saved(data, key, pending['bucket'])
    if not entry or not hub.same_identity(identity, hub.entry_identity(entry)):
        return False
    def change(saved):
        saved.update(schema=1, identity=identity, route=pending['route'], provider=pending['provider'],
                     success_verified=True, failed=False, success_epoch_ms=success['epoch_ms'],
                     route_sha256=success['destination_sha256'])
        saved['failed_routes'] = [v for v in saved.get('failed_routes', [])
                                  if isinstance(v, dict) and v.get('sha256') != _hash(pending['route'])]
    _change_memory(profile, entry, pending['bucket'], change, pending.get('source_snapshot'))
    # A newer click may replace a receipt while the admitted write runs.
    if _property(home, 'Pending').get('token') == token:
        home.clearProperty('Infinity.SavedNavigation.Pending')
        home.clearProperty('Infinity.SavedNavigation.Success')
    _trace('saved_navigation_remembered', saved_key=key, media_identity=identity,
           provider=pending['provider']['id'], destination_sha256=_hash(pending['route']))
    return True


def confirm_playback(profile, playback):
    home = xbmcgui.Window(10000)
    pending = _property(home, 'Pending')
    if pending:
        try:
            return confirm_saved(profile, pending.get('key'), pending.get('token'), playback)
        except (Unavailable, OSError, ValueError, RuntimeError, TypeError, KeyError, AttributeError) as error:
            _trace('saved_navigation_memory_deferred', error_type=type(error).__name__)
    return False


def _choose_recovery(profile, entry, bucket, data, home, original_target, token='', failure=None, item_builder=None, resume_offset=0):
    identity = hub.entry_identity(entry)
    if not identity:
        raise Unavailable('The saved media identity is not verified. Nothing was changed.')
    _protocol(home)
    original = original_target(entry, data.get('sources', {}))
    initial = original
    attempted = []
    if failure is not None:
        record = remembered(data, identity) or {}
        pending = _property(home, 'Pending')
        choices = {original, record.get('route', '')}
        if pending.get('token') == token and pending.get('key') == entry['key']:
            choices.add(pending.get('original', ''))
        matches = [v for v in choices if _hash(v) == failure.get('original_sha256')]
        if len(matches) != 1:
            raise Cancelled('The failed navigation no longer matches this saved item.')
        initial = matches[0]
        failure = failure_ticket(home, entry['key'], token, initial, identity, bucket)
        failed_path = initial
        if pending.get('token') == token and _hash(pending.get('route', '')) == failure.get('failed_sha256'):
            failed_path = pending['route']
        if _hash(failed_path) != failure.get('failed_sha256', _hash(initial)):
            raise Cancelled('The failed destination no longer matches the selected route.')
        _mark_failed(profile, entry, bucket, failed_path)
        attempted = failure['attempted']
        resume_offset = failure.get('resume', 0)
    else:
        # Missing, incompatible or previously failed only. A valid original
        # destination cannot be turned into a provider prompt by this action.
        target = navigation_target(entry, data, original, bucket)
        if not target.startswith('plugin://' + CC + '/?action=saved-recovery&'):
            raise Cancelled('The saved destination remains available; its original action was retained.')
        token = uuid.uuid4().hex
    snapshot = _source_snapshot(entry, data.get('sources', {}))
    ready, _ = available('movie' if identity['kind'] == 'movie' else 'tv')
    ready = [p for p in ready if p['id'] not in attempted]
    def attempt(saved, provider):
        target = direct_destination(saved, provider)
        if target:
            return target
        progress = xbmcgui.DialogProgress()
        progress.create('Infinity saved item', 'Verifying identity with ' + provider['name'])
        try:
            return resolve(saved, provider, home, progress)
        finally:
            progress.close()
    provider, target = resolve_with_choices(entry, ready, '',
        lambda reason, options: xbmcgui.Dialog().select(
            'The saved destination failed — open with' if failure is not None else 'Saved destination unavailable — open with',
            [p['name'] for p in options]), attempt)
    current_data = hub.load_view(profile)
    current = _saved(current_data, entry['key'], bucket)
    if (xbmc.Monitor().abortRequested() or not current or
            not hub.same_identity(identity, hub.entry_identity(current)) or _source_snapshot(current, current_data.get('sources', {})) != snapshot or
            original_target(current, current_data.get('sources', {})) != original):
        raise Cancelled('Navigation changed; the saved item was kept.')
    if failure is not None:
        failure_ticket(home, entry['key'], token, initial, identity, bucket)
    search.route(provider)
    pending = dict(schema=1, token=token, key=entry['key'], bucket=bucket, identity=identity,
        route=target, original=initial, provider=provider, source_snapshot=snapshot,
        epoch_ms=int(time.time()*1000))
    home.setProperty('Infinity.SavedNavigation.Pending', json.dumps(pending))
    home.clearProperty('Infinity.SavedNavigation.Success')
    request = dict(token=token, path=target)
    if failure is None:
        request.update(key=entry['key'], bucket=bucket, original=initial, folder=identity['kind'] in ('tvshow', 'season'), resume=resume_offset)
        home.setProperty('Infinity.SavedNavigation.Start', json.dumps(request))
    else:
        home.setProperty('Infinity.SavedNavigation.Next', json.dumps(request))
    _trace('saved_navigation_handoff', saved_key=entry['key'], provider=provider['id'],
           destination_sha256=_hash(target), media_identity=identity)
    if identity['kind'] in ('tvshow', 'season'):
        xbmc.executebuiltin('ActivateWindow(Videos,"' + target.replace('"', '%22') + '",return)' if
            xbmcgui.getCurrentWindowId() != 10025 else 'Container.Update("' + target.replace('"', '%22') + '")')
    else:
        if item_builder is None:
            raise Unavailable('The original playback item builder is unavailable.')
        _, item = item_builder(entry, data, bucket)
        item.setPath(target)
        try:
            offset = float(resume_offset)
        except (ValueError, TypeError):
            offset = 0
        if not 0 <= offset < 1e12:
            offset = 0
        item.setProperty('ResumeTime', str(offset))
        item.setProperty('StartOffset', str(offset))
        xbmc.Player().play(target, item)


def recover_saved(profile, key, token, original_target, bucket='later', item_builder=None, resume_offset=0):
    try:
        if xbmc.getSkinDir() != 'skin.infinity.diggz':
            raise Unavailable('Saved navigation is available only in Infinity.')
        data = hub.load_view(profile)
        entry = _saved(data, key, bucket)
        if entry is None:
            raise Unavailable('The saved item is no longer in this list.')
        home = xbmcgui.Window(10000)
        failure = _property(home, 'Failure', 8192) if token else None
        _choose_recovery(profile, entry, bucket, data, home, original_target, token, failure, item_builder, resume_offset)
    except Cancelled:
        _trace('saved_navigation_cancelled', saved_key=str(key)[:64])
    except (Unavailable, OSError, ValueError, RuntimeError, TypeError, KeyError,
            AttributeError, SyntaxError, ET.ParseError) as error:
        _trace('saved_navigation_failed', saved_key=str(key)[:64], error_type=type(error).__name__)
        xbmcgui.Dialog().ok('Infinity saved item', str(error))
