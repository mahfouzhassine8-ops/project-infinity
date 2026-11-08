"""Watchlist-only launch and actual-item evidence; no player, writer or client."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import time
import uuid
import xml.etree.ElementTree as ET
from urllib.parse import parse_qs, urlsplit

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
import resume_hub as hub

# Source-reviewed current producers. Runtime bytes, not advertised version alone,
# authorize this narrowly scoped identity view. No provider code is imported.
PRODUCERS = {'plugin.video.pov': {'version': '6.11.02', 'files': {'addon.xml': 'd1183b5c1fbdf9aa692048a54e66b89bba4bfaa40d78aa615d00351cdf8ebf05', 'resources/lib/caches/__init__.py': 'f3448d8392d0d587c561d2d3444e6c97474b77c3d30a915a0da247e8d4364c2b', 'resources/lib/caches/meta_cache.py': '0cbb93769c9867a61d0faf31140510c19f3f8bbe6c1c0f312bd7cfd9e862de46', 'resources/lib/indexers/metadata.py': '66409de0d892b20e4e8c3b23cc7214727f2f8b40a643c49b228a758db74168be', 'resources/lib/indexers/tmdb_api.py': '26a844d69b4e76c55762ca091b098ee9ec3abce0f74f76fa49e5351f963b1303', 'resources/lib/menus/episodes.py': '407bc518143920f903df884b96ca661784e8d9840962f2109f1f68778a323911', 'resources/lib/menus/movies.py': '2328d24a4090396f3970fa329d48bbff92e86b7fcc5ee14fbaedfc1594263bef', 'resources/lib/menus/seasons.py': '1a29b118399825708302d090ff8d569ce831774e5fa23a26082a52352d9aa4a1', 'resources/lib/menus/tvshows.py': 'b13b2fbfb4f48def0ef81c2ef4dede92a11f04c85ff54c101dd4286e94639680', 'resources/lib/modules/entry.py': '0814bc3b11b377ce96ce3373936a4fd40fb683e5330daa25fc8a17f63c732b6f', 'resources/lib/modules/kodi_utils.py': 'a5d35a7c01502a09af379fe729e15a29aced3053c23e1a513cfa4a55bfffc238', 'resources/lib/modules/player.py': '5051f95b9989c5d1608e84c5562edc6795a7bef8e5cf9d14386e79471a1d2f9c', 'resources/lib/modules/sources.py': '530c6446e25c87088e4aab72526824513b14c1e9f5af575cc6e5d6f1e0e56f89', 'resources/lib/router.py': '9bab400e60cfcb7a3923f9584c5348efa068fc361c3ee5e7d97101b65dbb3534'}}, 'plugin.video.umbrella': {'version': '6.8.00', 'files': {'addon.xml': '879343065f8c9a515fa76dfabb8faa7c375047ca9b0ae179cbbaae2f0f771b5e', 'resources/lib/database/metacache.py': 'ffc7b769e0c354188cd7c285aa1c968d45591f4ef466f8b0c5bd5b41c17ab894', 'resources/lib/indexers/tmdb.py': '6bae13471d955a1560ea939125c9a831426ea976c745251173782bf3b700cff8', 'resources/lib/menus/episodes.py': '6a3564f70dab1ffe01325cf7fbcf3d000833af652525e7a5252e6b261e9c0ad9', 'resources/lib/menus/movies.py': 'e9ba284439ec2e126defeebf1b59cbad3a25f3a2fd0e75d004915171f0118291', 'resources/lib/menus/seasons.py': 'd4dd8c64a2a040f743b99f2d5b61e7a5f5668900aeaf1c2181e7ba5bf12e8af6', 'resources/lib/menus/tvshows.py': '15816f2daad65b15d08bd04a20792e3d0c80aab4e7ff9cf7053df2d472d9fcc1', 'resources/lib/modules/control.py': 'f0bf8b18d1019e6fc9c38bfb56eaeb37b7b0c2e90ebdcf33d42e12b7f548a29d', 'resources/lib/modules/playback_metadata.py': '1c991b60f63cd7a58f401024b68fa80377c4731853c8ab96012c2f5e7fd540c0', 'resources/lib/modules/player.py': '49d0bbed8175340669dd46c1dc6b691f9ec835650e1955fd101cc109972107fe', 'resources/lib/modules/router.py': 'c0cfecb068b0ee80f78e774791cad4205cdb269987888f858d4710627a1a51ea', 'resources/lib/modules/sources.py': 'f1a1a70784dfff702f2394932990d3f113e80069e9ba2e7798d7660636b7b997', 'umbrella.py': '8875307040fd671afae5d460085730419dff2b1f84857394ddee742e18daa980'}}}
_verified = {}


def profile_root():
    return xbmcvfs.translatePath('special://profile').rstrip('/\\')


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':'))


def _property(home, name):
    raw = home.getProperty('Infinity.Watchlist.' + name)
    if not isinstance(raw, str) or not raw or len(raw.encode('utf-8')) > 262144:
        return None
    try:
        value = json.loads(raw)
        return value if isinstance(value, dict) else None
    except (ValueError, TypeError):
        return None


def _recent(value, maximum=300000):
    epoch = value.get('epoch_ms')
    return type(epoch) is int and 0 <= int(time.time() * 1000) - epoch <= maximum


def _stamp(path):
    stat = path.lstat()
    if path.is_symlink() or not path.is_file() or stat.st_size > 2 * 1024 * 1024:
        raise ValueError('Unreviewed producer source')
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns


def verified_producer(provider):
    contract = PRODUCERS.get(provider)
    if not contract:
        return False
    try:
        addon = xbmcaddon.Addon(provider)
        raw = Path(xbmcvfs.translatePath(addon.getAddonInfo('path'))).absolute()
        root = raw.resolve()
        if root != raw or addon.getAddonInfo('id') != provider or addon.getAddonInfo('version') != contract['version']:
            return False
        paths = [(root / name, digest) for name, digest in contract['files'].items()]
        if any(not path.resolve().is_relative_to(root) for path, _ in paths):
            return False
        before = tuple(_stamp(path) for path, _ in paths)
        marker = (str(root), before)
        if _verified.get(provider) == marker:
            return True
        _verified.pop(provider, None)
        if any(hashlib.sha256(path.read_bytes()).hexdigest() != digest for path, digest in paths):
            return False
        manifest = ET.parse(root / 'addon.xml').getroot()
        if manifest.get('id') != provider or manifest.get('version') != contract['version']:
            return False
        if before != tuple(_stamp(path) for path, _ in paths):
            return False
        _verified[provider] = marker
        return True
    except (OSError, ValueError, RuntimeError, ET.ParseError):
        return False


def route_identity(route, kind, season=-1, episode=-1, verify=None):
    """Reviewed playing routes contain movie IDs or parent-show IDs plus S/E."""
    if not isinstance(route, str) or len(route.encode('utf-8')) > 65536 or any(ord(c) < 32 for c in route):
        return None
    try:
        parsed = urlsplit(route)
        if (parsed.scheme != 'plugin' or parsed.path not in ('', '/') or parsed.fragment or
                not (verify or verified_producer)(parsed.netloc)):
            return None
        parts = parse_qs(parsed.query, keep_blank_values=True, max_num_fields=100)
        if any(len(values) != 1 for values in parts.values()):
            return None
        if parsed.netloc == 'plugin.video.umbrella':
            if parts.get('action') not in (['play'], ['play_Item']):
                return None
            ids = hub.verified_ids({name: parts.get(name, [''])[0] for name in ('tmdb', 'tvdb', 'imdb')})
        elif parsed.netloc == 'plugin.video.pov':
            if parts.get('mode') != ['play_media'] or parts.get('mediatype') != [kind]:
                return None
            ids = hub.verified_ids({name: parts.get(name + '_id', [''])[0] for name in ('tmdb', 'tvdb', 'imdb')})
        else:
            return None
        if kind == 'movie':
            return hub.media_identity('movie', ids) if not {'season', 'episode'} & set(parts) else None
        coordinates = tuple(hub.episode_number(parts.get(name, [''])[0]) for name in ('season', 'episode'))
        if kind != 'episode' or coordinates != (hub.episode_number(season), hub.episode_number(episode)) or min(coordinates) < 0:
            return None
        return hub.media_identity('tv', {}, season, episode, ids)
    except (ValueError, TypeError):
        return None


def saved_identity(entry):
    """Temporary exact saved-episode scope view, independent of click authority."""
    identity = hub.entry_identity(entry)
    if not identity or identity.get('kind') != 'episode' or identity.get('scope') != 'episode':
        return identity
    for route in (entry.get('stable_source'), entry.get('source')):
        proved = route_identity(route, 'episode', entry.get('season'), entry.get('episode'))
        if proved and hub._agreeing_ids(proved['ids'], identity['ids']):
            return proved
    return identity


def supported_target(entry):
    """Preserve the saved current-producer route without expanding global trust."""
    identity = hub.entry_identity(entry)
    if not identity or identity.get('kind') not in ('movie', 'episode'):
        return ''
    for route in (entry.get('stable_source'), entry.get('source')):
        proved = route_identity(route, identity['kind'], entry.get('season'), entry.get('episode'))
        if proved and hub._agreeing_ids(proved['ids'], identity['ids']):
            return route
    return ''


def selected_matches(home, token, entry, destination):
    from selection_contract import snapshot
    selected = _property(home, 'Selected')
    return bool(selected and type(selected.get('schema')) is int and selected['schema'] == 1 and
                re.fullmatch(r'[a-f0-9]{32}', str(token)) and selected.get('token') == token and
                selected.get('profile') == profile_root() and selected.get('key') == entry.get('key') and
                selected.get('selection') == snapshot(entry, 'watchlist') and
                selected.get('destination') == destination and _recent(selected, 120000))


def launch(home, item, entry, destination, selected_token='', progress=None):
    """Only called after explicit first-party Play and a fresh selected-row read."""
    from selection_contract import snapshot
    selection = snapshot(entry, 'watchlist')
    if not selection or (selection['identity']['kind'] not in ('movie', 'episode')):
        return False
    if selected_token and not selected_matches(home, selected_token, entry, destination):
        return False
    value = dict(schema=1, token=uuid.uuid4().hex, key=entry['key'], profile=profile_root(),
                 selection=selection, destination=destination, epoch_ms=int(time.time() * 1000))
    value['resume'] = float(progress['position']) if progress else 0.0
    value['resume_revision'] = int(progress.get('resume_revision') or 0) if progress else 0
    if selected_token:
        value['selected_token'] = selected_token
    raw = _json(value)
    item.setProperty('Infinity.Watchlist.Launch', raw)
    home.setProperty('Infinity.Watchlist.Launch', raw)
    return True


def admit(profile, actual, entry):
    """Enrich only native-proven actual Watchlist playback; never write progress."""
    if not isinstance(entry, dict) or xbmc.getSkinDir() != 'skin.infinity.diggz':
        return entry
    origin = actual.get('infinity_watchlist_origin') if isinstance(actual, dict) else None
    if not isinstance(origin, dict):
        return entry
    from selection_contract import snapshot
    try:
        if (type(origin.get('schema')) is not int or origin['schema'] != 1 or
                not re.fullmatch(r'[a-f0-9]{32}', str(origin.get('token') or '')) or
                origin.get('profile') != profile_root() or not _recent(origin)):
            return entry
        saved = hub.load_view(profile).get('watchlist', {}).get(origin.get('key'))
        if not saved or origin.get('selection') != snapshot(dict(saved, key=origin['key']), 'watchlist'):
            return entry
        anchor = hub.entry_identity(saved)
        kind = actual.get('type')
        observed = hub.entry_identity(entry)
        if not anchor or not observed or kind not in ('movie', 'episode') or observed['kind'] != kind:
            return entry
        season, episode = (hub.episode_number(actual.get(name)) for name in ('season', 'episode'))
        if kind == 'episode' and (observed.get('season'), observed.get('episode')) != (season, episode):
            return entry
        proved = route_identity(origin.get('destination'), kind, season, episode)
        ids = hub.verified_ids(actual.get('uniqueid'))
        if not proved or not hub._agreeing_ids(proved['ids'], ids):
            return entry
        if anchor['kind'] == 'movie':
            if kind != 'movie' or not hub._agreeing_ids(anchor['ids'], proved['ids']):
                return entry
        else:
            if kind != 'episode' or not hub._agreeing_ids(saved_identity(saved)['ids'], proved['ids']):
                return entry
            if anchor['kind'] == 'episode' and (season, episode) != (anchor['season'], anchor['episode']):
                return entry
            if anchor['kind'] == 'season' and season != anchor['season']:
                return entry
        result = dict(entry)
        result['_watchlist_origin'] = dict(origin)
        # Preserve original raw progress IDs/key and all manual-action contracts.
        # The proven parent is a progress-only canonical view already supported
        # by the existing store/projections, not a global episode-ID relaxation.
        if kind == 'episode':
            result.update(show_ids_verified=True)
            result.update({'show_' + name: value for name, value in proved['ids'].items()})
        from common import setting_bool
        if setting_bool('source_memory_enabled', True):
            result['stable_source'] = origin['destination']
        return result
    except (OSError, ValueError, RuntimeError, TypeError, KeyError, AttributeError):
        return entry
