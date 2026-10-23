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
import os
import re
import time
import stat
import threading

import xbmc

from common import atomic_json, read_json, persistence_scope
import uuid
import hashlib

CONTINUE_FILE = 'continue-watching.json'
SCHEMA = 2
KEY_RE = re.compile(r'^[a-f0-9]{64}$')
BUCKET_LIMITS = {
    'items': 100,
    'watched': 600,
    'watchlist': 500,
    'collection': 1000,
    'later': 500,
}

def verified_ids(values):
    """Retain explicit namespaces; numeric IDs from different systems never alias."""
    result = {}
    for namespace, value in _dict(values).items():
        value = str(value or '').strip()
        if namespace in ('tmdb', 'tvdb') and re.fullmatch(r'[1-9][0-9]{0,19}', value):
            result[namespace] = value
        elif namespace == 'imdb' and re.fullmatch(r'tt[0-9]{5,12}', value):
            result[namespace] = value
    return result


def media_identity(media, ids, season=-1, episode=-1, show_ids=None):
    """Producer supplies a typed movie/episode, never just a title or folder."""
    ids = verified_ids(ids)
    if media == 'movie' and ids:
        return {'schema': 1, 'kind': 'movie', 'scope': 'movie', 'ids': ids}
    season, episode = episode_number(season), episode_number(episode)
    if media != 'tv' or season < 0 or episode < 0:
        return None
    series = verified_ids(show_ids)
    if series:
        return {'schema': 1, 'kind': 'episode', 'scope': 'show_episode', 'ids': series,
                'season': season, 'episode': episode}
    if ids:
        return {'schema': 1, 'kind': 'episode', 'scope': 'episode', 'ids': ids,
                'season': season, 'episode': episode}
    return None


def show_identity(kind, ids, season=-1):
    ids = verified_ids(ids)
    if not ids or kind not in ('tvshow', 'season'):
        return None
    identity = dict(schema=1, kind=kind, scope='show' if kind == 'tvshow' else 'show_season', ids=ids)
    if kind == 'season':
        season = episode_number(season)
        if season < 0:
            return None
        identity['season'] = season
    return identity


def entry_identity(entry):
    """Validate additive identity; legacy records remain readable without guessing."""
    value = _dict(_dict(entry).get('identity'))
    if type(value.get('schema')) is not int or value.get('schema') != 1:
        return None
    media = _dict(entry).get('media')
    if media == 'movie' and value.get('kind') == 'movie' and value.get('scope') == 'movie':
        return media_identity('movie', value.get('ids'))
    if media == 'tv' and value.get('kind') == 'episode' and value.get('scope') in ('episode', 'show_episode'):
        season, episode = episode_number(value.get('season')), episode_number(value.get('episode'))
        if (season, episode) != (episode_number(entry.get('season')), episode_number(entry.get('episode'))):
            return None
        return media_identity('tv', value.get('ids') if value['scope'] == 'episode' else {},
                              season, episode, value.get('ids') if value['scope'] == 'show_episode' else {})
    if media == 'tv' and value.get('kind') in ('tvshow', 'season'):
        kind = value['kind']
        if value.get('scope') != ('show' if kind == 'tvshow' else 'show_season'):
            return None
        if kind == 'season' and episode_number(value.get('season')) != episode_number(entry.get('season')):
            return None
        return show_identity(kind, value.get('ids'), value.get('season', -1))
    return None


def identity_key(identity):
    if not isinstance(identity, dict):
        return ''
    ids = verified_ids(identity.get('ids'))
    for namespace in ('tmdb', 'imdb', 'tvdb'):
        if namespace in ids:
            raw = identity['scope'] + '|' + namespace + ':' + ids[namespace]
            if identity['kind'] == 'episode':
                raw += '|%s|%s' % (identity['season'], identity['episode'])
            elif identity['kind'] == 'season':
                raw += '|%s' % identity['season']
            return hashlib.sha256(raw.encode('ascii')).hexdigest()
    return ''


def same_identity(left, right):
    if not left or not right or left.get('kind') != right.get('kind') or left.get('scope') != right.get('scope'):
        return False
    if left['kind'] == 'episode' and (left['season'], left['episode']) != (right['season'], right['episode']):
        return False
    if left['kind'] == 'season' and left['season'] != right['season']:
        return False
    common = set(left['ids']) & set(right['ids'])
    return bool(common) and all(left['ids'][namespace] == right['ids'][namespace] for namespace in common)


def compatible_key(data, entry):
    """Reuse one proven row; legacy identity is bound only on exact route replay."""
    identity = entry_identity(entry)
    if not identity:
        return ''
    canonical, legacy = set(), set()
    observed_ids = verified_ids({name: entry.get(name) for name in ('tmdb', 'tvdb', 'imdb')})
    source = str(entry.get('source') or '')
    for bucket in ('items', 'watched', 'watchlist', 'collection', 'later'):
        for key, old in _dict(_dict(data).get(bucket)).items():
            if not KEY_RE.fullmatch(str(key)) or not isinstance(old, dict):
                continue
            old_identity = entry_identity(old)
            if old_identity and same_identity(identity, old_identity):
                canonical.add(key)
            elif (not old_identity and identity['kind'] in ('movie', 'episode') and source.startswith('plugin://') and old.get('source') == source
                  and old.get('media') == entry.get('media')):
                ids = verified_ids({name: old.get(name) for name in ('tmdb', 'tvdb', 'imdb')})
                common = set(ids) & set(observed_ids)
                if (common and all(ids[name] == observed_ids[name] for name in common) and
                        (entry['media'] == 'movie' or
                         (episode_number(old.get('season')), episode_number(old.get('episode'))) ==
                         (identity['season'], identity['episode']))):
                    legacy.add(key)
    matches = canonical or legacy
    if len(matches) == 1:
        return next(iter(matches))
    # Existing duplicate movie records with fully verified, mutually agreeing
    # IDs should update the newest saved key, not mint a third progress record.
    # Never choose arbitrarily among ambiguous records or TV episodes.
    if identity.get('kind') == 'movie' and len(canonical) > 1:
        items = _dict(_dict(data).get('items'))
        group = [(key, _dict(items.get(key))) for key in canonical]
        verified = [entry_identity(value) for _, value in group]
        if (all(value and source for (_, value), source in zip(group, verified)) and
                all(same_identity(left, right) for n, left in enumerate(verified)
                    for right in verified[n + 1:])):
            return max(group, key=lambda item: (int(item[1].get('updated') or 0), item[0]))[0]
    return identity_key(identity)


def occurrence_completed(data, key, occurrence):
    return bool(occurrence and _dict(_dict(_dict(data).get('watched')).get(key)).get('completed_occurrence') == occurrence)


def episode_number(value):
    """Return an exact nonnegative identity number; zero is not missing."""
    if isinstance(value, bool):
        return -1
    text = str(value).strip() if value is not None else ''
    if not re.fullmatch(r'[0-9]{1,6}', text):
        return -1
    return int(text)


def trace_timing(stage, started=None, **fields):
    """Bounded numeric observations in Kodi's log, never a persistence receipt."""
    if stage not in ('service_start', 'saved_state_published', 'cache_validation', 'snapshot_load', 'plugin_start', 'saved_state_ready', 'filter_group', 'directory_items', 'plugin_complete', 'card_visible'):
        return
    now = time.monotonic()
    row = {'schema': 1, 'stage': stage, 'pid': os.getpid(), 'monotonic_ms': round(now * 1000, 3)}
    if started is not None:
        row['elapsed_ms'] = round(max(0.0, now - started) * 1000, 3)
    for key, value in fields.items():
        if ((key == 'request' and re.fullmatch(r'[np][0-9]{1,30}', str(value))) or
                (key == 'media' and value in ('tv', 'movie', 'all')) or
                (key == 'bucket' and value in ('continue', 'history', 'watched', 'list'))):
            row[key] = str(value)
        elif key in ('items', 'revision', 'cache_hit') and isinstance(value, (int, bool)):
            row[key] = int(value)
    try:
        xbmc.log('INFINITY_RESUME_TIMING ' + json.dumps(row, sort_keys=True, separators=(',', ':')), xbmc.LOGINFO)
    except Exception:
        pass  # Observation cannot change saving or list results.


_visible_requests = set()


def observe_visible_cards():
    """Observe existing controls; unknown installed layouts remain unmeasured."""
    if not xbmc.getCondVisibility('Window.IsActive(home)'):
        return
    for control in (8830, 8831):
        if not xbmc.getCondVisibility('Control.IsVisible(%d)' % control):
            continue
        request = xbmc.getInfoLabel('Container(%d).ListItem.Property(Infinity.ResumeHub.Request)' % control)
        if re.fullmatch(r'[np][0-9]{1,30}', request or '') and request not in _visible_requests:
            if len(_visible_requests) >= 128:
                _visible_requests.clear()
            _visible_requests.add(request)
            trace_timing('card_visible', request=request, media='movie' if control == 8830 else 'tv')


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
    for name in ('items', 'sources', 'watched', 'watchlist', 'collection', 'ratings', 'lists', 'later'):
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


def _view_data(profile: Path, timing=False, context=None):
    """Internal read-only snapshot; never passed to mutations or checkpoint proof."""
    global _view_cache
    profile = Path(profile).resolve()
    started = time.monotonic()
    context = context or {}
    before = _view_signature(profile)
    if timing:
        trace_timing('cache_validation', started, **context)
    with _view_lock:
        if before is not None and _view_cache is not None and _view_cache[:2] == (profile, before):
            if timing:
                trace_timing('snapshot_load', started, cache_hit=1, **context)
            return _view_cache[2]
        _view_cache = None
    # Never hold a display lock while load() acquires the persistence gate:
    # admitted save() invalidates the cache while it already owns that gate.
    data = load(profile)
    if timing:
        trace_timing('snapshot_load', started, cache_hit=0, **context)
    after = _view_signature(profile)
    if before is not None and before == after:
        with _view_lock:
            _view_cache = (profile, after, data)
    return data


def load_view(profile: Path, timing_context=None):
    """One bounded display snapshot, returned as a private copy.

    A cache miss uses load() and its participant digest/owner verification. The
    data file, participant journal and engine identity all invalidate the view,
    including same-sized atomic replacements. Authoritative reads stay fresh.
    """
    return deepcopy(_view_data(profile, timing=True, context=timing_context))


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


def save(profile: Path, data, publish=None, retain_records=False):
    global _view_cache
    data = _normalize(data)
    if not retain_records:
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
    for bucket in ('items', 'watched', 'watchlist', 'collection', 'later'):
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
    occurrence = str(entry.get('playback_occurrence') or '')
    occurrence = occurrence if re.fullmatch(r'[a-f0-9]{32}', occurrence) else ''
    if prior and (not completed or not occurrence or prior.get('completed_occurrence') == occurrence):
        return data, None
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
    if completed and occurrence:
        entry['completed_occurrence'] = occurrence
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


def _toggle_bucket(data, key, bucket, incoming=None):
    data = _normalize(data)
    key = str(key)
    if key in data[bucket]:
        entry = data[bucket].pop(key)
        return data, False, entry
    entry = find_entry(data, key) or incoming
    if not entry:
        return data, False, None
    entry = _stamp(entry, 'added_at')
    data[bucket][key] = entry
    return data, True, entry


def toggle_watchlist_data(data, key, incoming=None):
    return _toggle_bucket(data, key, 'watchlist', incoming)


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
    if bucket == 'items' and media in ('movie', 'all'):
        # Presentation-only: never delete, modify, or merge a saved record.
        # Title/poster and untyped source links are NOT identity evidence.
        groups = {}
        for value in values:
            if value.get('media') != 'movie':
                continue
            token = identity_key(entry_identity(value))
            if token:
                groups.setdefault(token, []).append(value)
        hidden_keys = set()
        for group in groups.values():
            identities = [entry_identity(item) for item in group]
            if len(group) > 1 and all(identities) and all(
                    same_identity(left, right) for i, left in enumerate(identities)
                    for right in identities[i + 1:]):
                hidden_keys.update(item['key'] for item in group[1:])
        if hidden_keys:
            values = [item for item in values if item.get('key') not in hidden_keys]
    if bucket == 'items' and media in ('tv', 'all'):
        # Home and the full Continue view share this read-only projection.
        # Keep the most recently updated episode (including deliberate rewatches),
        # retaining every underlying episode, watched record and source action.
        groups = []
        aliases = {}
        hidden = set()
        for value in values:
            series = continue_series_ids(value)
            if not series:
                continue
            candidates = set().union(*(aliases.get((n, uid), set()) for n, uid in series.items()))
            compatible = [i for i in candidates if all(
                all(series[n] == member[n] for n in set(series) & set(member)) and
                bool(set(series) & set(member)) for member in groups[i])]
            if len(compatible) == 1:
                index = compatible[0]
                groups[index].append(series)
                hidden.add(value['key'])
            else:
                index = len(groups)
                groups.append([series])
            for namespace, uid in series.items():
                aliases.setdefault((namespace, uid), set()).add(index)
        values = [value for value in values if value.get('key') not in hidden]
    return values


def continue_series_ids(value):
    """Only proven parent-series IDs; never episode IDs or similar show names."""
    if value.get('media') != 'tv':
        return {}
    identity = entry_identity(value)
    typed = identity['ids'] if identity and identity.get('scope') == 'show_episode' else {}
    parent = verified_ids({name: value.get('show_' + name) for name in ('tmdb', 'tvdb', 'imdb')}) \
        if value.get('show_ids_verified') is True else {}
    if any(typed[name] != parent[name] for name in set(typed) & set(parent)):
        return {}
    return dict(typed, **parent)


def _show_key(value, key):
    if value.get('show_ids_verified') is True:
        for namespace in ('tmdb', 'tvdb'):
            verified = str(value.get('show_' + namespace) or '')
            if verified.isdigit() and int(verified) > 0:
                return 'series:' + namespace + ':' + verified
    # Ambiguous legacy rows keep their own identities and are not title-merged.
    return 'legacy-record:' + str(key)


def progress_shows(data):
    """Return the newest known episode per show, preferring in-progress episodes."""
    data = _normalize(data)
    chosen = {}
    for bucket, priority in (('watched', 0), ('items', 1)):
        for key, value in data[bucket].items():
            if not isinstance(value, dict) or value.get('media') != 'tv':
                continue
            show_key = _show_key(value, key)
            marker = (priority, episode_number(value.get('season')), episode_number(value.get('episode')),
                      int(value.get('updated') or value.get('watched_at') or 0))
            if show_key not in chosen or marker > chosen[show_key][0]:
                chosen[show_key] = (marker, _entry_copy(value, key))
    result = [value[1] for value in chosen.values()]
    result.sort(key=lambda e: int(e.get('updated') or e.get('watched_at') or 0), reverse=True)
    return result


def next_episodes(data):
    """Build conservative next-up candidates from locally observed TV state.

    An unfinished episode remains the next item. Once completed, a synthetic next episode is
    offered from concrete local season/episode state. Only verified series IDs may
    authorize the existing TMDb Helper resolver; ambiguous legacy cards stay unavailable.
    Episode unique IDs are never promoted to series IDs; no guessed stream URL is stored.
    """
    data = _normalize(data)
    progress = {}
    for key, value in data['items'].items():
        if isinstance(value, dict) and value.get('media') == 'tv':
            show_key = _show_key(value, key)
            current = progress.get(show_key)
            marker = (episode_number(value.get('season')), episode_number(value.get('episode')), int(value.get('updated') or 0))
            if current is None or marker > current[0]:
                progress[show_key] = (marker, _entry_copy(value, key))
    result = [v[1] for v in progress.values()]

    watched_latest = {}
    for key, value in data['watched'].items():
        if not isinstance(value, dict) or value.get('media') != 'tv':
            continue
        show_key = _show_key(value, key)
        if show_key in progress:
            continue
        season = episode_number(value.get('season'))
        episode = episode_number(value.get('episode'))
        if season < 0 or episode < 0 or value.get('show_ids_verified') is not True:
            continue
        marker = (season, episode, int(value.get('watched_at') or value.get('updated') or 0))
        if show_key not in watched_latest or marker > watched_latest[show_key][0]:
            watched_latest[show_key] = (marker, _entry_copy(value, key))
    for marker, last in watched_latest.values():
        successor = _dict(last.get('verified_next'))
        # The catalogue's successor must match the completed episode and series.
        # Adding one to an episode number does not prove an episode exists.
        if (successor.get('verified') is not True or
                successor.get('after') != [marker[0], marker[1]] or
                str(successor.get('show_tmdb') or '') != str(last.get('show_tmdb') or '') or
                episode_number(successor.get('season')) < 0 or
                episode_number(successor.get('episode')) < 0):
            continue
        # A show preference is not an episode route. Copy only series identity;
        # old DB IDs, stream URLs, episode titles/durations/art and watched data
        # must never be attributed to this locally inferred successor.
        show = str(last.get('showtitle') or last.get('title') or 'TV Show')
        candidate = {
            'media': 'tv', 'showtitle': show, 'title': show,
            'tmdb': last.get('show_tmdb', '') if last.get('show_ids_verified') is True else '',
            'tvdb': last.get('show_tvdb', '') if last.get('show_ids_verified') is True else '',
            'show_tmdb': last.get('show_tmdb', '') if last.get('show_ids_verified') is True else '',
            'show_ids_verified': last.get('show_ids_verified') is True,
            'season': episode_number(successor['season']), 'episode': episode_number(successor['episode']),
            'position': 0.0, 'percentage': 0.0, 'watched': False,
            'synthetic_next': True,
            'next_verified': True,
            'updated': int(last.get('watched_at') or last.get('updated') or 0),
        }
        candidate['label'] = f"{show} • S{candidate['season']:02d}E{candidate['episode']:02d}"
        candidate['identity'] = media_identity('tv', {}, candidate['season'], candidate['episode'],
                                              {'tmdb': candidate['show_tmdb']})
        candidate['key'] = identity_key(candidate['identity'])
        if not candidate['key']:
            continue
        result.append(candidate)
    result.sort(key=lambda e: int(e.get('updated') or 0), reverse=True)
    return result


def sync_kodi_playcount(entry, watched, preserve_playcount=False):
    """Checked bridge for Kodi-library items; provider-only items remain local."""
    if not isinstance(entry, dict):
        return False
    identity = entry_identity(entry)
    dbid = entry.get('dbid')
    if not identity or type(dbid) is not int or dbid <= 0:
        return False
    method = 'VideoLibrary.SetEpisodeDetails' if entry.get('media') == 'tv' else 'VideoLibrary.SetMovieDetails'
    field = 'episodeid' if entry.get('media') == 'tv' else 'movieid'
    read_method = 'VideoLibrary.GetEpisodeDetails' if entry.get('media') == 'tv' else 'VideoLibrary.GetMovieDetails'
    detail_field = 'episodedetails' if entry.get('media') == 'tv' else 'moviedetails'
    query = {'jsonrpc': '2.0', 'id': 1, 'method': read_method,
             'params': {field: dbid, 'properties': (['playcount', 'uniqueid', 'season', 'episode', 'tvshowid']
                                                   if entry['media'] == 'tv' else ['playcount', 'uniqueid'])}}
    def checked_details():
        response = json.loads(xbmc.executeJSONRPC(json.dumps(query)))
        details = _dict(_dict(response.get('result')).get(detail_field))
        if 'error' in response or type(details.get(field)) is not int or details[field] != dbid:
            return None
        if entry['media'] == 'tv':
            if (episode_number(details.get('season')), episode_number(details.get('episode'))) != (identity['season'], identity['episode']):
                return None
            ids = details.get('uniqueid')
            if identity['scope'] == 'show_episode':
                show_id = details.get('tvshowid')
                if type(show_id) is not int or show_id <= 0:
                    return None
                show = json.loads(xbmc.executeJSONRPC(json.dumps({
                    'jsonrpc': '2.0', 'id': 1, 'method': 'VideoLibrary.GetTVShowDetails',
                    'params': {'tvshowid': show_id, 'properties': ['uniqueid']}})))
                series = _dict(_dict(show.get('result')).get('tvshowdetails'))
                if 'error' in show or type(series.get('tvshowid')) is not int or series['tvshowid'] != show_id:
                    return None
                ids = series.get('uniqueid')
            actual = media_identity('tv', ids if identity['scope'] == 'episode' else {},
                                    details['season'], details['episode'],
                                    ids if identity['scope'] == 'show_episode' else {})
        else:
            actual = media_identity('movie', details.get('uniqueid'))
        return details if same_identity(identity, actual) else None
    try:
        details = checked_details()
        playcount = details.get('playcount') if details else None
        if type(playcount) is not int or playcount < 0:
            return False
        # Preserve native replay counts during ordinary synchronization too.
        if (watched and playcount > 0) or (not watched and playcount == 0):
            return True
    except Exception:
        return False
    payload = {'jsonrpc': '2.0', 'id': 1, 'method': method,
               'params': {field: dbid, 'playcount': 1 if watched else 0}}
    try:
        response = json.loads(xbmc.executeJSONRPC(json.dumps(payload)))
        if not isinstance(response, dict) or 'error' in response or response.get('result') != 'OK':
            return False
        details = checked_details()
        playcount = details.get('playcount') if details else None
        expected = 1 if watched else 0
        return type(playcount) is int and (playcount > 0 if watched else playcount == expected)
    except Exception:
        return False


def queue_kodi_sync(data, entry, watched):
    """Persist required library mirroring before crossing into Kodi JSON-RPC."""
    dbid = entry.get('dbid')
    if type(dbid) is not int or dbid <= 0:
        return data
    key = ('episode:' if entry.get('media') == 'tv' else 'movie:') + str(dbid)
    data.setdefault('pending_kodi_sync', {})[key] = {
        'operation': uuid.uuid4().hex, 'entry': dict(entry), 'watched': bool(watched)}
    return data


def flush_kodi_sync(profile, preserve_playcount=False, retain_records=False):
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
                save(profile, current, retain_records=retain_records)


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
