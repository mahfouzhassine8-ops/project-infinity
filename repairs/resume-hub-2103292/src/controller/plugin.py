# SPDX-License-Identifier: GPL-2.0-or-later
from __future__ import annotations

import re
import sys
import time
from urllib.parse import parse_qs, urlencode

import xbmc
import xbmcgui
import xbmcplugin

from common import addon_profile, setting_bool
from experience import artwork, commands, stable_route, number
import resume_hub as hub

HANDLE = int(sys.argv[1])
QUERY = sys.argv[2][1:] if len(sys.argv) > 2 and sys.argv[2].startswith('?') else ''
PARAMS = {key: values[-1] for key, values in parse_qs(QUERY).items()}
PROFILE = addon_profile()


def _url(**params):
    return 'plugin://script.infinity.commandcenter/?' + urlencode(params)


def _has_tmdb_helper():
    try:
        return bool(xbmc.getCondVisibility('System.HasAddon(plugin.video.themoviedb.helper)'))
    except Exception:
        return False


def _target(entry, sources=None):
    if setting_bool('source_memory_enabled', True):
        preference = sources.get(entry.get('key'), {}) if isinstance(sources, dict) else {}
        if not isinstance(preference, dict):
            preference = {}
        route = stable_route(preference.get('route') or entry.get('stable_source', ''))
        if route and number(preference.get('failures')) < 2:
            host = route.split('/')[2] if route.startswith('plugin://') else ''
            if not host or xbmc.getCondVisibility('System.HasAddon(%s)' % host):
                return route
    tmdb = str(entry.get('tmdb') or '').strip()
    media = entry.get('media')
    if tmdb.isdigit() and _has_tmdb_helper():
        if media == 'tv':
            season = str(int(number(entry.get('season'))))
            episode = str(int(number(entry.get('episode'))))
            return ('plugin://plugin.video.themoviedb.helper/?info=play&tmdb_type=tv&tmdb_id=' + tmdb +
                    '&season=' + season + '&episode=' + episode)
        return 'plugin://plugin.video.themoviedb.helper/?info=play&tmdb_type=movie&tmdb_id=' + tmdb
    source = str(entry.get('source') or '').strip()
    if stable_route(source) or time.time() - number(entry.get('updated')) < 21600:
        return source
    return ''


def _mutate_url(op, key, list_name=''):
    params = {'action': 'mutate', 'op': op, 'key': key}
    if list_name:
        params['list'] = list_name
    return 'RunPlugin(' + _url(**params) + ')'


def _context(entry, data, bucket='', list_name=''):
    key = str(entry.get('key') or '')
    if not hub.KEY_RE.fullmatch(key) or entry.get('synthetic_next'):
        return []
    watched = key in data.get('watched', {})
    watchlisted = key in data.get('watchlist', {})
    collected = key in data.get('collection', {})
    rated = int((data.get('ratings', {}).get(key) or {}).get('rating') or 0)
    menu = [
        ('Mark Unwatched' if watched else 'Mark Watched',
         _mutate_url('mark-unwatched' if watched else 'mark-watched', key)),
        ('Reset Progress', _mutate_url('reset-progress', key)),
        ('Remove from Watchlist' if watchlisted else 'Add to Watchlist',
         _mutate_url('toggle-watchlist', key)),
        ('Remove from Collection' if collected else 'Add to Collection',
         _mutate_url('toggle-collection', key)),
        (('Change Rating • %d/10' % rated) if rated else 'Rate', _mutate_url('rate', key)),
        ('Add to Custom List', _mutate_url('add-list', key)),
    ]
    if key in data.get('items', {}):
        menu.append(('Remove from Continue Playing', _mutate_url('remove-resume', key)))
    if bucket == 'list' and list_name:
        menu.append(('Remove from ' + list_name, _mutate_url('remove-list', key, list_name)))
    return menu


def _apply_identity(li, entry):
    ids = {name: str(entry.get(name)) for name in ('tmdb', 'tvdb', 'imdb') if str(entry.get(name) or '').strip()}
    if ids and hasattr(li, 'setUniqueIDs'):
        try:
            li.setUniqueIDs(ids)
        except Exception:
            pass
    for name, value in ids.items():
        li.setProperty('Infinity.UniqueID.' + name, value)


def _list_item(entry, data, bucket='', list_name=''):
    key = str(entry.get('key') or '')
    target = _target(entry, data.get('sources', {}))
    if not target:
        target = _url(action='unavailable')
    kind = entry.get('media')
    label = str(entry.get('label') or entry.get('title') or 'Resume Hub')
    rating = int((data.get('ratings', {}).get(key) or {}).get('rating') or entry.get('rating') or 0)
    label2 = ('★ %d/10' % rating) if rating else ''
    li = xbmcgui.ListItem(label=label, label2=label2, path=target)
    watched = key in data.get('watched', {})
    in_progress = key in data.get('items', {}) and number(entry.get('position')) > 0
    info = {
        'title': str(entry.get('title') or label),
        'mediatype': 'episode' if kind == 'tv' else 'movie',
        'playcount': 1 if watched else 0,
        # Kodi's standard watched overlay value. The skin also keys off PlayCount/Overlay.
        'overlay': 6 if watched else 0,
    }
    if kind == 'tv':
        info.update({
            'tvshowtitle': str(entry.get('showtitle') or ''),
            'season': int(number(entry.get('season'))),
            'episode': int(number(entry.get('episode'))),
        })
    li.setInfo('video', info)
    _apply_identity(li, entry)
    art = {}
    tier = xbmcgui.Window(10000).getProperty('Infinity.Artwork.Quality') or 'standard'
    if entry.get('poster'):
        art.update({'poster': artwork(entry['poster'], tier), 'thumb': artwork(entry['poster'], tier)})
    if entry.get('fanart'):
        art['fanart'] = artwork(entry['fanart'], tier, True)
    if art:
        li.setArt(art)
    li.setProperty('IsPlayable', 'true')
    li.setProperty('Infinity.ResumeHub.Key', key)
    li.setProperty('Infinity.ResumeHub.Watched', 'true' if watched else 'false')
    li.setProperty('Infinity.ResumeHub.InProgress', 'true' if in_progress else 'false')
    li.setProperty('Infinity.ResumeHub.State', 'in-progress' if in_progress else ('watched' if watched else 'unwatched'))
    li.setProperty('Infinity.ResumeHub.Revision', str(data.get('revision', 0) or 0))
    # Publish both the dedicated Resume Hub state and Kodi-compatible fallbacks. Existing Infinity
    # watched overlays already consume Kodi playcount/overlay state; these properties let shared
    # skin includes consume the same state without inventing a second watched database.
    li.setProperty('Watched', 'true' if watched else 'false')
    li.setProperty('PlayCount', '1' if watched else '0')
    li.setProperty('Overlay', '6' if watched else '0')
    li.setProperty('Infinity.ResumeHub.Bucket', bucket)
    if rating:
        li.setProperty('Rating', str(rating))
    if in_progress:
        position = number(entry.get('position'))
        duration = number(entry.get('duration'))
        li.setProperty('ResumeTime', str(position))
        li.setProperty('TotalTime', str(duration))
        li.setProperty('StartOffset', str(position))
        li.setProperty('PercentPlayed', str(entry.get('percentage', 0) or 0))
    else:
        # A watched title started again must begin from zero, not its prior completion point.
        li.setProperty('ResumeTime', '0')
        li.setProperty('StartOffset', '0')
    context = _context(entry, data, bucket, list_name)
    if context:
        li.addContextMenuItems(context)
    return target, li


def _values_for(data, media, bucket, list_name=''):
    if bucket == 'continue':
        return hub.entries(data, media, 'items')
    if bucket in ('history', 'watched'):
        return hub.entries(data, media, 'watched')
    if bucket == 'progress':
        values = hub.progress_shows(data)
        return [v for v in values if media == 'all' or v.get('media') == media]
    if bucket == 'next':
        values = hub.next_episodes(data)
        return [v for v in values if media == 'all' or v.get('media') == media]
    if bucket in ('watchlist', 'collection', 'ratings'):
        return hub.entries(data, media, bucket)
    if bucket == 'list':
        return hub.entries(data, media, 'list', list_name)
    return []


def listing(media='all', bucket='continue', list_name=''):
    data = hub.load(PROFILE)
    values = _values_for(data, media, bucket, list_name)
    xbmcplugin.setContent(HANDLE, 'episodes' if media == 'tv' else ('movies' if media == 'movie' else 'videos'))
    for entry in values[:100]:
        target, li = _list_item(entry, data, bucket, list_name)
        xbmcplugin.addDirectoryItem(HANDLE, target, li, isFolder=False)
    xbmcplugin.endOfDirectory(HANDLE, succeeded=True, updateListing=False, cacheToDisc=False)


def _directory(label, url, label2=''):
    li = xbmcgui.ListItem(label=label, label2=label2)
    li.setProperty('IsPlayable', 'false')
    xbmcplugin.addDirectoryItem(HANDLE, url, li, isFolder=True)


def navigator(media):
    title = 'Infinity Movies' if media == 'movie' else 'Infinity TV'
    if media == 'movie':
        rows = (
            ('Continue Playing', 'continue', 'Local unfinished movies'),
            ('Watchlist', 'watchlist', 'Movies you want to watch'),
            ('Collection', 'collection', 'Movies you keep'),
            ('Watched History', 'history', 'Completed movies'),
            ('Ratings', 'ratings', 'Your local ratings'),
        )
    else:
        rows = (
            ('Next Episodes', 'next', 'Local next-up candidates'),
            ('Progress Shows', 'progress', 'Latest known episode per show'),
            ('Continue Playing', 'continue', 'Unfinished episodes'),
            ('Watchlist', 'watchlist', 'Shows and episodes you want to watch'),
            ('Collection', 'collection', 'TV you keep'),
            ('Watched History', 'history', 'Completed episodes'),
            ('Ratings', 'ratings', 'Your local ratings'),
        )
    xbmcplugin.setPluginCategory(HANDLE, title)
    for label, bucket, description in rows:
        _directory(label, _url(action='library', media=media, bucket=bucket), description)
    _directory('Custom Lists', _url(action='custom-lists', media=media), 'Your Resume Hub lists')
    xbmcplugin.endOfDirectory(HANDLE, succeeded=True, cacheToDisc=False)


def custom_lists(media):
    data = hub.load(PROFILE)
    xbmcplugin.setPluginCategory(HANDLE, 'Infinity Custom Lists')
    for name in sorted(data.get('lists', {}), key=str.casefold):
        count = len([v for v in data['lists'][name].values()
                     if isinstance(v, dict) and (media == 'all' or v.get('media') == media)])
        if count:
            _directory(name, _url(action='library', media=media, bucket='list', list=name), '%d items' % count)
    xbmcplugin.endOfDirectory(HANDLE, succeeded=True, cacheToDisc=False)


def mutate():
    op = PARAMS.get('op', '')
    key = PARAMS.get('key', '')
    list_name = PARAMS.get('list', '')
    if not hub.KEY_RE.fullmatch(key):
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False, cacheToDisc=False)
        return
    data = hub.load(PROFILE)
    entry = hub.find_entry(data, key)
    changed = False
    notice = ''
    if op == 'mark-watched' and entry:
        data, changed_entry = hub.mark_watched_data(data, key, entry, completed=False)
        changed = changed_entry is not None
        if changed_entry:
            hub.sync_kodi_playcount(changed_entry, True)
        notice = 'Marked watched'
    elif op == 'mark-unwatched':
        data, changed_entry = hub.mark_unwatched_data(data, key)
        changed = changed_entry is not None
        if changed_entry:
            hub.sync_kodi_playcount(changed_entry, False)
        notice = 'Marked unwatched'
    elif op in ('reset-progress', 'remove-resume'):
        data, removed = hub.reset_progress_data(data, key)
        changed = removed is not None
        notice = 'Progress reset' if op == 'reset-progress' else 'Removed from Continue Playing'
    elif op == 'toggle-watchlist' and entry:
        data, added, changed_entry = hub.toggle_watchlist_data(data, key)
        changed = changed_entry is not None
        notice = 'Added to Watchlist' if added else 'Removed from Watchlist'
    elif op == 'toggle-collection' and entry:
        data, added, changed_entry = hub.toggle_collection_data(data, key)
        changed = changed_entry is not None
        notice = 'Added to Collection' if added else 'Removed from Collection'
    elif op == 'rate' and entry:
        current = int((data.get('ratings', {}).get(key) or {}).get('rating') or 0)
        options = ['Remove rating'] + ['%d / 10' % i for i in range(1, 11)]
        choice = xbmcgui.Dialog().select('Rate • ' + str(entry.get('label') or entry.get('title') or 'Title'),
                                         options, preselect=current)
        if choice >= 0:
            data, result = hub.set_rating_data(data, key, choice)
            changed = True
            notice = 'Rating removed' if choice == 0 else 'Rated %d/10' % choice
    elif op == 'add-list' and entry:
        name = xbmcgui.Dialog().input('Add to custom list').strip()[:80]
        if name:
            data, result = hub.add_to_list_data(data, key, name)
            changed = result is not None
            notice = 'Added to ' + name
    elif op == 'remove-list' and list_name:
        data, removed = hub.remove_from_list_data(data, key, list_name)
        changed = removed is not None
        notice = 'Removed from ' + list_name
    if changed:
        data = hub.save(PROFILE, data, hub.publish_home)
        try:
            xbmcgui.Dialog().notification('Infinity Resume Hub', notice, xbmcgui.NOTIFICATION_INFO, 2200)
        except Exception:
            pass
        xbmc.executebuiltin('Container.Refresh')
    xbmcplugin.endOfDirectory(HANDLE, succeeded=True, cacheToDisc=False)


def main():
    action = PARAMS.get('action', 'continue')
    if action == 'commands':
        query = xbmcgui.Window(10000).getProperty('Infinity.Palette.Query')
        for key, label, description in commands(query):
            li = xbmcgui.ListItem(label=label, label2=description)
            li.setProperty('Infinity.Action', key)
            xbmcplugin.addDirectoryItem(HANDLE, _url(action='command', command=key), li, isFolder=False)
        xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=False)
        return
    if action == 'unavailable':
        xbmcgui.Dialog().ok('Infinity Resume Hub',
            'This source is unavailable or has expired. Open the title in your provider to resolve a fresh source. Resume Hub kept your local state.')
        xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
        return
    if action == 'mutate':
        mutate(); return
    if action in ('movies', 'movie-navigator'):
        navigator('movie'); return
    if action in ('tv', 'tv-navigator'):
        navigator('tv'); return
    if action == 'custom-lists':
        custom_lists(PARAMS.get('media', 'all')); return
    if action == 'library':
        listing(PARAMS.get('media', 'all'), PARAMS.get('bucket', 'continue'), PARAMS.get('list', '')); return
    if action in ('continue', 'resume'):
        listing('all' if action == 'resume' else ('tv' if PARAMS.get('media') == 'tv' else 'movie'), 'continue'); return
    xbmcplugin.endOfDirectory(HANDLE, succeeded=False, cacheToDisc=False)


if __name__ == '__main__':
    main()
