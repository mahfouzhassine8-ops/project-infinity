"""Infinity-owned Save for Later navigation. Saved records are read-only inputs.

Provider URLs are hints about provider preference, never media identity. Only a
fresh result from a reviewed installed API may supply a destination. Titles are
queries, not matching evidence. No provider imports, profile writes or database
migrations occur here. Continue Playing and Search keep their original paths.
"""
from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import parse_qs, unquote, urlencode, urlsplit
import xml.etree.ElementTree as ET

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

import infinity_search as search
import resume_hub as hub

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
        if not re.fullmatch(r'plugin\.video\.[A-Za-z0-9._-]{1,160}', aid):
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


def _directory(path, provider, query, home, progress):
    # Preserve the existing engine's bounded consumer protocol and Search limit.
    # Larger, unverified request envelopes remain explicit failures.
    if len(path.encode('utf-8')) + len('|infinity_search=') + 32 > 8192:
        raise Unavailable('Provider destination exceeds the supported navigation request limit.')
    _trace('saved_navigation_request', provider=provider['id'],
                     destination_sha256=hashlib.sha256(path.encode()).hexdigest())
    search.route(provider, query)  # Raw installed source and enabled-state recheck.
    status, answer = search._leased_directory(path, home, progress)
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
    if wanted == 'movie':
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


def open_saved(handle, profile, key):
    """Only the Save for Later action calls this. It never rewrites saved state."""
    folder = True
    try:
        if xbmc.getSkinDir() != 'skin.infinity.diggz':
            raise Unavailable('Save for Later navigation is available only in Infinity.')
        if not hub.KEY_RE.fullmatch(str(key)):
            raise Unavailable('The saved entry key is invalid.')
        data = hub.load_view(profile)
        entries = [e for e in hub.entries(data, 'all', 'later') if e['key'] == key]
        if len(entries) != 1:
            raise Unavailable('The saved entry is no longer in Save for Later.')
        entry = deepcopy(entries[0])
        identity = hub.entry_identity(entry)
        if not identity:
            raise Unavailable('The saved media identity is not verified.')
        folder = identity['kind'] in ('tvshow', 'season')
        _trace('saved_navigation_click', saved_key=key, media_identity=identity)
        ready, unsupported = available('movie' if identity['kind'] == 'movie' else 'tv')
        # The route is used ONLY to retain the original provider preference.
        try:
            sources = data.get('sources', {})
            preference = sources.get(key, {}) if isinstance(sources, dict) else {}
            if not isinstance(preference, dict):preference = {}
            try:failed = float(preference.get('failures') or 0) >= 2
            except (TypeError, ValueError):failed = False
            remembered = preference.get('route') if not failed else ''
            if not isinstance(remembered, str):remembered = ''
            preferred = urlsplit(remembered or entry.get('stable_source') or entry.get('source') or '').netloc
        except ValueError:
            preferred = ''
        home = xbmcgui.Window(10000)
        if home.getProperty('Infinity.Search.Protocol') != '1':
            search._leased_directory('plugin://' + CC + '/?action=search-probe', home)
        if home.getProperty('Infinity.Search.Protocol') != '1':
            raise Unavailable('The installed engine lacks the required bounded navigation protocol.')
        def attempt(saved, provider):
            progress = xbmcgui.DialogProgress()
            progress.create('Save for Later', 'Verifying saved identity with ' + provider['name'])
            try:
                return resolve(saved, provider, home, progress)
            finally:
                progress.close()
        provider, target = resolve_with_choices(entry, ready, preferred,
            lambda reason, options: xbmcgui.Dialog().select(reason, [p['name'] for p in options]), attempt)
        _trace('saved_navigation_handoff', saved_key=key, provider=provider['id'],
                         destination_sha256=hashlib.sha256(target.encode()).hexdigest(),
                         media_identity=identity)
        if folder:
            xbmcplugin.endOfDirectory(handle, succeeded=False, cacheToDisc=False)
            xbmc.executebuiltin('Container.Update("' + target.replace('"', '%22') + '")')
        else:
            xbmcplugin.setResolvedUrl(handle, True, xbmcgui.ListItem(path=target))
    except Cancelled:
        _trace('saved_navigation_cancelled', saved_key=str(key)[:64])
        if folder:
            xbmcplugin.endOfDirectory(handle, succeeded=False, cacheToDisc=False)
        else:
            xbmcplugin.setResolvedUrl(handle, False, xbmcgui.ListItem())
    except (Unavailable, OSError, ValueError, RuntimeError, TypeError, KeyError,
            AttributeError, SyntaxError, ET.ParseError) as error:
        _trace('saved_navigation_failed', saved_key=str(key)[:64], error_type=type(error).__name__)
        xbmcgui.Dialog().ok('Infinity Save for Later', str(error))
        if folder:
            xbmcplugin.endOfDirectory(handle, succeeded=False, cacheToDisc=False)
        else:
            xbmcplugin.setResolvedUrl(handle, False, xbmcgui.ListItem())
