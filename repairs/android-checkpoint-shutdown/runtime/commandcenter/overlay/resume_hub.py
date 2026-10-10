# SPDX-License-Identifier: GPL-2.0-or-later
"""Infinity Resume Hub local-first media state.

The existing continue-watching.json remains the single local store. Schema 2 extends
that file with watched history, watchlist, collection, ratings and custom lists while
preserving schema-1 progress/source data in place. Trakt is never required.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json
import re
import time
import stat
import threading

import xbmc

from common import atomic_json, read_json, persistence_scope
import uuid

CONTINUE_FILE = 'continue-watching.json'
SCHEMA = 2
KEY_RE = re.compile(r'^[a-f0-9]{64}$')
BUCKET_LIMITS = {
    'items': 100,
    'watched': 600,
    'watchlist': 500,
    'collection': 1000,
}


def _now() -> int:
    return int(time.time())


def _dict(value):
    return value if isinstance(value, dict) else {}


def _entry_copy(entry, key=''):
    result = deepcopy(entry) if isinstance(entry, dict) else {}
    if key and KEY_RE.fullmatch(str(key)):
        result['key'] = str(key)
    return result


def _stamp(entry, field='updated'):
    result = _entry_copy(entry)
    result[field] = _now()
    result['updated'] = _now()
    return result


def _ordered(bucket, limit):
    # Preserve legacy/foreign keys in stored buckets. New Resume Hub mutations still require
    # canonical 64-hex identities, but save() must never silently delete older progress entries.
    pairs = [(str(k), v) for k, v in _dict(bucket).items()
             if str(k) and isinstance(v, dict)]
    pairs.sort(key=lambda pair: int(pair[1].get('updated') or pair[1].get('watched_at') or
                                    pair[1].get('added_at') or 0), reverse=True)
    return dict(pairs[:limit])


def _normalize(data):
    if not isinstance(data, dict):
        data = {}
    data = dict(data)
    for name in ('items', 'sources', 'watched', 'watchlist', 'collection', 'ratings', 'lists'):
        data[name] = _dict(data.get(name))
    data['sources'] = {str(k): v for k, v in data['sources'].items()
                       if KEY_RE.fullmatch(str(k)) and isinstance(v, dict)}
    data['ratings'] = {str(k): v for k, v in data['ratings'].items()
                       if KEY_RE.fullmatch(str(k)) and isinstance(v, dict)}
    clean_lists = {}
    for name, bucket in data['lists'].items():
        label = str(name).strip()[:80]
        if not label or not isinstance(bucket, dict):
            continue
        clean_lists[label] = {str(k): v for k, v in bucket.items()
                              if KEY_RE.fullmatch(str(k)) and isinstance(v, dict)}
    data['lists'] = clean_lists
    data['schema'] = SCHEMA
    return data


def load(profile: Path):
    path = Path(profile) / CONTINUE_FILE
    data = read_json(path, {'schema': SCHEMA, 'revision': 0, 'items': {}})
    return _normalize(data)


_view_lock = threading.RLock()
_view_cache = None


def _view_signature(profile):
    """Observe atomic replacements and owner/journal changes without opening a writer gate."""
    signature = []
    for path in (profile / CONTINUE_FILE, profile / '.android-checkpoint' / 'participant.json',
                 profile / '.android-checkpoint' / 'engine.json'):
        try:
            value = path.lstat()
        except FileNotFoundError:
            signature.append(None)
            continue
        except OSError:
            return None
        if not stat.S_ISREG(value.st_mode):
            return None  # Symlinks/unknown types must use the original verified read.
        signature.append((value.st_dev, value.st_ino, value.st_size,
                          value.st_mtime_ns, value.st_ctime_ns))
    return tuple(signature)


def _view_data(profile: Path):
    """Internal read-only snapshot; never passed to mutations or checkpoint proof."""
    global _view_cache
    profile = Path(profile).resolve()
    before = _view_signature(profile)
    with _view_lock:
        if before is not None and _view_cache is not None and _view_cache[:2] == (profile, before):
            return _view_cache[2]
        _view_cache = None
    # Never hold a display lock while load() acquires the persistence gate:
    # admitted save() invalidates the cache while it already owns that gate.
    data = load(profile)
    after = _view_signature(profile)
    if before is not None and before == after:
        with _view_lock:
            _view_cache = (profile, after, data)
    return data


def load_view(profile: Path):
    """One bounded display snapshot, returned as a private copy.

    A cache miss uses load() and its participant digest/owner verification. The
    data file, participant journal and engine identity all invalidate the view,
    including same-sized atomic replacements. Authoritative reads stay fresh.
    """
    return deepcopy(_view_data(profile))


def poll_kodi_sync(profile):
    """Idle fast path only; real queued writes keep the fresh admitted RPC/readback path."""
    if not _view_data(profile).get('pending_kodi_sync'):
        return True
    return flush_kodi_sync(profile)


def counts(data):
    data = _normalize(data)
    def media_count(bucket, media):
        return sum(1 for v in _dict(data.get(bucket)).values()
                   if isinstance(v, dict) and v.get('media') == media)
    return {
        'continue_movies': media_count('items', 'movie'),
        'continue_tv': media_count('items', 'tv'),
        'watched_movies': media_count('watched', 'movie'),
        'watched_tv': media_count('watched', 'tv'),
        'watchlist_movies': media_count('watchlist', 'movie'),
        'watchlist_tv': media_count('watchlist', 'tv'),
        'collection_movies': media_count('collection', 'movie'),
        'collection_tv': media_count('collection', 'tv'),
    }


def save(profile: Path, data, publish=None):
    global _view_cache
    data = _normalize(data)
    for name, limit in BUCKET_LIMITS.items():
        data[name] = _ordered(data[name], limit)
    data['sources'] = _ordered(data['sources'], 150)
    data['ratings'] = _ordered(data['ratings'], 600)
    data['lists'] = {name: _ordered(bucket, 500) for name, bucket in data['lists'].items()}
    data['schema'] = SCHEMA
    # Millisecond revision gives every skin/plugin list a single refresh token.
    data['revision'] = int(time.time() * 1000)
    data['updated'] = _now()
    atomic_json(Path(profile) / CONTINUE_FILE, data)
    with _view_lock:
        _view_cache = None
    if publish:
        publish(data)
    return data


def find_entry(data, key):
    if not KEY_RE.fullmatch(str(key)):
        return None
    data = _normalize(data)
    for bucket in ('items', 'watched', 'watchlist', 'collection'):
        entry = data[bucket].get(key)
        if isinstance(entry, dict):
            return _entry_copy(entry, key)
    for bucket in data['lists'].values():
        entry = bucket.get(key)
        if isinstance(entry, dict):
            return _entry_copy(entry, key)
    return None


def is_watched(data, key):
    return str(key) in _dict(_normalize(data).get('watched'))


def mark_watched_data(data, key, entry=None, completed=False):
    data = _normalize(data)
    entry = _entry_copy(entry or find_entry(data, key), key)
    if not entry:
        return data, None
    prior = _dict(data['watched'].get(key))
    play_count = int(prior.get('play_count') or 0)
    if completed or not prior:
        play_count += 1
    duration = float(entry.get('duration') or prior.get('duration') or 0.0)
    entry.update({
        'watched': True,
        'watched_at': _now(),
        'updated': _now(),
        'play_count': max(1, play_count),
        'percentage': 100.0,
        'position': duration if duration > 0 else float(entry.get('position') or 0.0),
    })
    data['items'].pop(key, None)
    data['watched'][key] = entry
    return data, entry


def mark_unwatched_data(data, key):
    data = _normalize(data)
    entry = data['watched'].pop(str(key), None)
    if isinstance(entry, dict):
        entry = _entry_copy(entry, str(key))
        entry['watched'] = False
        entry['percentage'] = 0.0
        entry['position'] = 0.0
        entry['updated'] = _now()
    return data, entry


def reset_progress_data(data, key):
    data = _normalize(data)
    return data, data['items'].pop(str(key), None)


def remove_resume_data(data, key):
    return reset_progress_data(data, key)


def _toggle_bucket(data, key, bucket):
    data = _normalize(data)
    key = str(key)
    if key in data[bucket]:
        entry = data[bucket].pop(key)
        return data, False, entry
    entry = find_entry(data, key)
    if not entry:
        return data, False, None
    entry = _stamp(entry, 'added_at')
    data[bucket][key] = entry
    return data, True, entry


def toggle_watchlist_data(data, key):
    return _toggle_bucket(data, key, 'watchlist')


def toggle_collection_data(data, key):
    return _toggle_bucket(data, key, 'collection')


def set_rating_data(data, key, rating):
    data = _normalize(data)
    key = str(key)
    try:
        rating = int(rating)
    except (TypeError, ValueError):
        rating = 0
    if rating <= 0:
        return data, data['ratings'].pop(key, None)
    if rating > 10 or not find_entry(data, key):
        return data, None
    data['ratings'][key] = {'rating': rating, 'updated': _now()}
    return data, data['ratings'][key]


def add_to_list_data(data, key, list_name):
    data = _normalize(data)
    name = str(list_name).strip()[:80]
    entry = find_entry(data, str(key))
    if not name or not entry:
        return data, None
    bucket = data['lists'].setdefault(name, {})
    bucket[str(key)] = _stamp(entry, 'added_at')
    return data, bucket[str(key)]


def remove_from_list_data(data, key, list_name):
    data = _normalize(data)
    name = str(list_name).strip()[:80]
    bucket = data['lists'].get(name)
    if not isinstance(bucket, dict):
        return data, None
    removed = bucket.pop(str(key), None)
    if not bucket:
        data['lists'].pop(name, None)
    return data, removed


def entries(data, media='all', bucket='items', list_name=''):
    data = _normalize(data)
    if bucket == 'list':
        source = _dict(data['lists'].get(str(list_name)))
    elif bucket == 'ratings':
        values = []
        for key, rating in data['ratings'].items():
            entry = find_entry(data, key)
            if entry:
                entry['rating'] = int(rating.get('rating') or 0)
                entry['updated'] = int(rating.get('updated') or entry.get('updated') or 0)
                values.append(entry)
        source = {e['key']: e for e in values}
    else:
        source = _dict(data.get(bucket))
    values = [_entry_copy(value, key) for key, value in source.items()
              if isinstance(value, dict) and (media == 'all' or value.get('media') == media)]
    values.sort(key=lambda value: int(value.get('updated') or value.get('watched_at') or
                                      value.get('added_at') or 0), reverse=True)
    return values


def progress_shows(data):
    """Return the newest known episode per show, preferring in-progress episodes."""
    data = _normalize(data)
    chosen = {}
    for bucket, priority in (('watched', 0), ('items', 1)):
        for key, value in data[bucket].items():
            if not isinstance(value, dict) or value.get('media') != 'tv':
                continue
            show_key = str(value.get('tmdb') or value.get('tvdb') or value.get('imdb') or
                           value.get('showtitle') or value.get('title') or key).casefold()
            marker = (priority, int(value.get('season') or -1), int(value.get('episode') or -1),
                      int(value.get('updated') or value.get('watched_at') or 0))
            if show_key not in chosen or marker > chosen[show_key][0]:
                chosen[show_key] = (marker, _entry_copy(value, key))
    result = [value[1] for value in chosen.values()]
    result.sort(key=lambda e: int(e.get('updated') or e.get('watched_at') or 0), reverse=True)
    return result


def next_episodes(data):
    """Build conservative next-up candidates from locally observed TV state.

    An unfinished episode remains the next item. Once completed, a synthetic next episode is
    offered only when a TMDb/TVDb identity and concrete season/episode are known. The normal
    provider/TMDb Helper resolver validates playback; no guessed stream URL is stored.
    """
    data = _normalize(data)
    progress = {}
    for key, value in data['items'].items():
        if isinstance(value, dict) and value.get('media') == 'tv':
            show_key = str(value.get('tmdb') or value.get('tvdb') or value.get('imdb') or
                           value.get('showtitle') or value.get('title') or key).casefold()
            current = progress.get(show_key)
            marker = (int(value.get('season') or -1), int(value.get('episode') or -1), int(value.get('updated') or 0))
            if current is None or marker > current[0]:
                progress[show_key] = (marker, _entry_copy(value, key))
    result = [v[1] for v in progress.values()]

    watched_latest = {}
    for key, value in data['watched'].items():
        if not isinstance(value, dict) or value.get('media') != 'tv':
            continue
        show_key = str(value.get('tmdb') or value.get('tvdb') or value.get('imdb') or
                       value.get('showtitle') or value.get('title') or key).casefold()
        if show_key in progress:
            continue
        season = int(value.get('season') or -1)
        episode = int(value.get('episode') or -1)
        if season < 0 or episode < 0 or not (value.get('tmdb') or value.get('tvdb')):
            continue
        marker = (season, episode, int(value.get('watched_at') or value.get('updated') or 0))
        if show_key not in watched_latest or marker > watched_latest[show_key][0]:
            watched_latest[show_key] = (marker, _entry_copy(value, key))
    for marker, last in watched_latest.values():
        candidate = _entry_copy(last)
        candidate.pop('key', None)
        candidate['episode'] = marker[1] + 1
        candidate['position'] = 0.0
        candidate['percentage'] = 0.0
        candidate['watched'] = False
        candidate['synthetic_next'] = True
        candidate['source'] = ''
        candidate['updated'] = int(last.get('watched_at') or last.get('updated') or 0)
        show = str(candidate.get('showtitle') or candidate.get('title') or 'TV Show')
        candidate['label'] = f"{show} • S{marker[0]:02d}E{marker[1] + 1:02d}"
        # Key is intentionally deterministic but distinct from the completed episode.
        import hashlib
        raw = 'tv|' + str(candidate.get('tmdb') or candidate.get('tvdb') or show.casefold()) + f'|{marker[0]}|{marker[1] + 1}'
        candidate['key'] = hashlib.sha256(raw.encode('utf-8', errors='replace')).hexdigest()
        result.append(candidate)
    result.sort(key=lambda e: int(e.get('updated') or 0), reverse=True)
    return result


def sync_kodi_playcount(entry, watched, preserve_playcount=False):
    """Checked bridge for Kodi-library items; provider-only items remain local."""
    if not isinstance(entry, dict):
        return False
    try:
        dbid = int(entry.get('dbid'))
    except (TypeError, ValueError):
        return False
    if dbid < 0:
        return False
    method = 'VideoLibrary.SetEpisodeDetails' if entry.get('media') == 'tv' else 'VideoLibrary.SetMovieDetails'
    field = 'episodeid' if entry.get('media') == 'tv' else 'movieid'
    read_method = 'VideoLibrary.GetEpisodeDetails' if entry.get('media') == 'tv' else 'VideoLibrary.GetMovieDetails'
    detail_field = 'episodedetails' if entry.get('media') == 'tv' else 'moviedetails'
    query = {'jsonrpc': '2.0', 'id': 1, 'method': read_method,
             'params': {field: dbid, 'properties': ['playcount']}}
    if watched and preserve_playcount:
        # Native frozen-player persistence owns the actual watched increment.
        # Existing nonzero native counts are already the required watched state;
        # never overwrite a higher count with the inherited absolute SET(1).
        try:
            details = json.loads(xbmc.executeJSONRPC(json.dumps(query)))
            playcount = details.get('result', {}).get(detail_field, {}).get('playcount')
            if type(playcount) is not int or playcount < 0:
                return False
            if playcount > 0:
                return True
        except Exception:
            return False
    payload = {'jsonrpc': '2.0', 'id': 1, 'method': method,
               'params': {field: dbid, 'playcount': 1 if watched else 0}}
    try:
        response = json.loads(xbmc.executeJSONRPC(json.dumps(payload)))
        if not isinstance(response, dict) or 'error' in response or response.get('result') != 'OK':
            return False
        details = json.loads(xbmc.executeJSONRPC(json.dumps(query)))
        playcount = details.get('result', {}).get(detail_field, {}).get('playcount')
        expected = 1 if watched else 0
        return type(playcount) is int and (playcount > 0 if watched and preserve_playcount
                                          else playcount == expected)
    except Exception:
        return False


def queue_kodi_sync(data, entry, watched):
    """Persist required library mirroring before crossing into Kodi JSON-RPC."""
    try:
        dbid = int(entry.get('dbid'))
    except (TypeError, ValueError):
        return data
    if dbid < 0:
        return data
    key = ('episode:' if entry.get('media') == 'tv' else 'movie:') + str(dbid)
    data.setdefault('pending_kodi_sync', {})[key] = {
        'operation': uuid.uuid4().hex, 'entry': dict(entry), 'watched': bool(watched)}
    return data


def flush_kodi_sync(profile, preserve_playcount=False):
    """Keep each queued mutation, synchronous RPC/readback and ack in one lease.

    The audited VideoLibrary Get/SetMovie/EpisodeDetails path performs database
    work directly and queues notifications; it never waits for a Python callback
    or an interactive dialog. Releasing the gate before the RPC would allow an
    old client operation to overwrite a newer checkpointed watched state.
    """
    while True:
        with persistence_scope():
            pending = load(profile).get('pending_kodi_sync', {})
            if not pending:
                return True
            key, operation = next(iter(pending.items()))
            if not isinstance(operation, dict) or not sync_kodi_playcount(operation.get('entry'), operation.get('watched'), preserve_playcount):
                return False  # Keep the durable operation for retry/checkpoint failure.
            current = load(profile)
            if current.get('pending_kodi_sync', {}).get(key, {}).get('operation') == operation.get('operation'):
                current['pending_kodi_sync'].pop(key, None)
                save(profile, current)


def publish_home(data):
    """Publish only small counts/revision; never serialize title history into window properties."""
    try:
        import xbmcgui
        home = xbmcgui.Window(10000)
        state = counts(data)
        values = {
            'Infinity.ContinueWatchingRevision': data.get('revision', 0),
            'Infinity.ResumeHubRevision': data.get('revision', 0),
            'Infinity.ContinueWatchingMovies': state['continue_movies'],
            'Infinity.ContinueWatchingTV': state['continue_tv'],
            'Infinity.WatchedMovies': state['watched_movies'],
            'Infinity.WatchedTV': state['watched_tv'],
            'Infinity.WatchlistMovies': state['watchlist_movies'],
            'Infinity.WatchlistTV': state['watchlist_tv'],
            'Infinity.CollectionMovies': state['collection_movies'],
            'Infinity.CollectionTV': state['collection_tv'],
        }
        for key, value in values.items():
            text = str(value)
            if home.getProperty(key) != text:
                home.setProperty(key, text)
    except Exception:
        pass
