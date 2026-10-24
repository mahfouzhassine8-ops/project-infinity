# SPDX-License-Identifier: GPL-2.0-or-later
from __future__ import annotations

import re
import json
import sys
import time
from urllib.parse import parse_qs, urlencode

import xbmc
import xbmcgui
import xbmcplugin

from common import addon_profile, setting_bool, persistence_scope
from persistence_participant import AdmissionClosed
from experience import artwork, commands, stable_route, number, verified_source
import resume_hub as hub

HANDLE = int(sys.argv[1])
QUERY = sys.argv[2][1:] if len(sys.argv) > 2 and sys.argv[2].startswith('?') else ''
PARAMS = {key: values[-1] for key, values in parse_qs(QUERY).items()}
PROFILE = addon_profile()


def _url(**params):
    return 'plugin://script.infinity.commandcenter/?' + urlencode(params)


def _has_addon(addon_id, render=None):
    if render is None:
        return bool(xbmc.getCondVisibility('System.AddonIsEnabled(%s)' % addon_id))
    installed = render['installed']
    if addon_id not in installed:
        installed[addon_id] = bool(xbmc.getCondVisibility('System.AddonIsEnabled(%s)' % addon_id))
    return installed[addon_id]


def _has_tmdb_helper(render=None):
    try:
        return _has_addon('plugin.video.themoviedb.helper', render)
    except Exception:
        return False


def _target(entry, sources=None, render=None):
    source_memory = render['source_memory'] if render is not None else setting_bool('source_memory_enabled', True)
    if source_memory and not entry.get('synthetic_next'):
        preference = sources.get(entry.get('key'), {}) if isinstance(sources, dict) else {}
        if not isinstance(preference, dict):
            preference = {}
        # Movie and TV entries both retain an independent captured route.
        # A stale preference must not mask it. Do not retry the very same
        # failed preferred route after two recorded failures.
        preferred = preference.get('route')
        failed = number(preference.get('failures')) >= 2
        choices = ([] if failed else [preferred])
        captured = entry.get('stable_source')
        if captured != preferred or not failed:
            choices.append(captured)
        for saved in choices:
            route = verified_source(entry, saved)
            if not route:
                continue
            host = route.split('/')[2] if route.startswith('plugin://') else ''
            if not host or _has_addon(host, render):
                return route
    if entry.get('synthetic_next') and (entry.get('next_verified') is not True or
            entry.get('show_ids_verified') is not True or
            str(entry.get('show_tmdb') or '').strip() != str(entry.get('tmdb') or '').strip()):
        return ''
    media = entry.get('media')
    if (hub.entry_identity(entry) or {}).get('kind') in ('tvshow', 'season'):
        return ''  # Only an original verified provider/library directory may open a show.
    # An episode TMDb ID cannot authorize a show resolver. Original verified
    # episode routes remain usable; unknown series identity stays unavailable.
    tmdb = str((entry.get('show_tmdb') if media == 'tv' and entry.get('show_ids_verified') is True
                else entry.get('tmdb') if media == 'movie' else '') or '').strip()
    if media == 'tv' and not tmdb:
        # An already saved, validated SHOW-EPISODE identity is sufficient
        # evidence of a series TMDb ID. An EPISODE ID NEVER is. No provider
        # search, name-based guess, or mutation of saved history is allowed.
        identity = hub.entry_identity(entry)
        if identity and identity.get('scope') == 'show_episode':
            tmdb = str(identity.get('ids', {}).get('tmdb') or '')
    if tmdb.isdigit() and _has_tmdb_helper(render):
        if media == 'tv':
            season = hub.episode_number(entry.get('season'))
            episode = hub.episode_number(entry.get('episode'))
            if season < 0 or episode < 0:
                return ''
            season, episode = str(season), str(episode)
            return ('plugin://plugin.video.themoviedb.helper/?info=play&tmdb_type=tv&tmdb_id=' + tmdb +
                    '&season=' + season + '&episode=' + episode)
        return 'plugin://plugin.video.themoviedb.helper/?info=play&tmdb_type=movie&tmdb_id=' + tmdb
    if entry.get('synthetic_next'):
        return ''  # No verified resolver: display the existing unavailable action.
    source = str(entry.get('source') or '').strip()
    if source.startswith('plugin://') and not _has_addon(source.split('/')[2], render):
        return ''
    if source.startswith('plugin://'):
        return verified_source(entry, source)
    if stable_route(source) or time.time() - number(entry.get('updated')) < 21600:
        return source
    return ''


def navigation_target(entry, data, bucket='continue', render=None):
    if bucket in ('later', 'watchlist', 'continue') and data.get('navigation_recovery'):
        from saved_navigation import remembered, navigation_target as select_target
        record = remembered(data, hub.entry_identity(entry))
        if record and record.get('success_verified') is True and record.get('route'):
            # A verified preference supersedes the failed old route. Do not
            # inspect the old provider or construct another resolver first.
            return select_target(entry, data, '', bucket, render)
    original = _target(entry, data.get('sources', {}), render)
    if bucket not in ('later', 'watchlist', 'continue'):
        return original
    # Keep untouched working records on the exact old path, with no discovery.
    if original and not data.get('navigation_recovery'):
        return original
    from saved_navigation import navigation_target as select_target
    return select_target(entry, data, original, bucket, render)


def recover_entry(key, bucket='later', token='', resume_offset=0):
    from saved_navigation import recover_saved
    return recover_saved(PROFILE, key, token, _target, bucket,
                         item_builder=_list_item, resume_offset=resume_offset)


def _mutate_url(op, key, list_name=''):
    params = {'action': 'mutate', 'op': op, 'key': key}
    if list_name:
        params['list'] = list_name
    return 'RunPlugin(' + _url(**params) + ')'


def _legacy_management_context(entry, data, bucket='', list_name=''):
    key = str(entry.get('key') or '')
    if not hub.KEY_RE.fullmatch(key) or entry.get('synthetic_next'):
        return []
    watched = hub.is_watched(data, key)
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



def _context(entry, data, bucket='', list_name=''):
    # Defer state/favourite discovery until one selected item's popup opens.
    # Never issue one JSON-RPC call per card while a rail is being rendered.
    key = str(entry.get('key') or '')
    if not hub.KEY_RE.fullmatch(key) or entry.get('synthetic_next'):
        return []
    return [('Title options', 'RunPlugin(' + _url(action='item-menu', key=key,
                                                 bucket=bucket, list=list_name) + ')')]


def _rpc(method, params):
    reply = json.loads(xbmc.executeJSONRPC(json.dumps(
        {'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})))
    if 'error' in reply:
        raise RuntimeError('Kodi could not complete the selected action')
    return reply.get('result')


def _favourite(entry, data, bucket):
    # This reads the existing Kodi favourites through its public API; it never
    # rewrites favourites.xml or changes the verified Umbrella destination.
    target = navigation_target(entry, data, bucket)
    if not target or target.startswith('plugin://script.infinity.commandcenter/'):
        return None, None
    folder = (hub.entry_identity(entry) or {}).get('kind') in ('tvshow', 'season')
    spec = dict(title=str(entry.get('label') or entry.get('title') or 'Title'),
                type='window' if folder else 'media')
    if folder:
        spec.update(window='videos', windowparameter=target)
    else:
        spec['path'] = target
    if entry.get('poster'):
        spec['thumbnail'] = str(entry['poster'])
    favourites = _rpc('Favourites.GetFavourites', {'properties': ['path', 'window', 'windowparameter', 'thumbnail']})
    matches = [value for value in (favourites or {}).get('favourites', [])
               if value.get('type') == spec['type'] and
               (value.get('windowparameter') == target and str(value.get('window')).lower() in ('videos', '10025')
                if folder else value.get('path') == target)]
    if len(matches) > 1:
        return None, None
    if matches:
        # AddFavourite is Kodi's AddOrRemove operation. Use the exact existing
        # entry on removal, including title, artwork and window destination.
        spec = {name: value for name, value in matches[0].items()
                if name in ('title', 'type', 'path', 'window', 'windowparameter', 'thumbnail')}
    return spec, bool(matches)


def _menu_resume(entry, data):
    return next((row for row in hub.entries(data)
                 if row['key'] == entry['key'] or hub.resume_matches(entry, row)), None)


def _menu_progress_state(entry, data):
    return sorted((key, old.get('position'), old.get('playback_occurrence'))
                  for key, old in data.get('items', {}).items()
                  if isinstance(old, dict) and (key == entry['key'] or hub.resume_matches(entry, old)))


def _menu_rows(entry, data, favourite_state=None, list_name='', bucket=''):
    key = entry['key']
    identity = hub.entry_identity(entry)
    rows = []
    if entry.get('source') or entry.get('stable_source') or identity:
        progress = _menu_resume(entry, data)
        resume = progress is not None and number(progress.get('position')) > 0
        rows.append(('Resume' if resume else 'Play', 'play', ''))
    if identity:
        watched = hub.is_watched(data, key) or (entry.get('_native_watched') is True and
                  key not in data.get('infinity_watched_overrides', {}))
        rows.append(('Mark Unwatched' if watched else 'Mark Watched',
                     'mark-unwatched' if watched else 'mark-watched', ''))
    rows.append(('Remove from Watchlist' if hub.bucket_has(data, 'watchlist', entry) else 'Add to Watchlist',
                 'toggle-watchlist', ''))
    if favourite_state is not None:
        rows.append(('Remove from Favorites' if favourite_state else 'Add to Favorites', 'favourite', ''))
    rows.append(('Remove from Collection' if hub.bucket_has(data, 'collection', entry) else 'Add to Collection',
                 'toggle-collection', ''))
    rows.append(('Add to Custom List', 'add-list', ''))
    for name, values in sorted(data.get('lists', {}).items()):
        if key in values:
            rows.append(('Remove from ' + name, 'remove-list', name))
    if bucket == 'later' and key in data.get('later', {}):
        rows.append(('Remove from Save for Later', 'remove-later', ''))
    rows.append(('Information', 'information', ''))
    if any(hub.resume_visible(data, old_key) and (old_key == key or hub.resume_matches(entry, old))
           for old_key, old in data.get('items', {}).items() if isinstance(old, dict)):
        rows.append(('Remove from Continue Watching', 'remove-resume', ''))
    return rows


def _selected_menu_entry(data, key, bucket, list_name=''):
    storage = {'continue': 'items', 'history': 'watched', 'watched': 'watched',
               'later': 'later', 'watchlist': 'watchlist', 'collection': 'collection'}.get(bucket)
    if storage:
        value = data.get(storage, {}).get(key)
        return dict(value, key=key) if isinstance(value, dict) else None
    if bucket == 'list' and list_name:
        value = data.get('lists', {}).get(list_name, {}).get(key)
        return dict(value, key=key) if isinstance(value, dict) else None
    return hub.find_entry(data, key)


def show_item_menu(key, bucket='continue', list_name='', incoming=None):
    if not hub.KEY_RE.fullmatch(str(key)):
        return False
    data = hub.load_view(PROFILE)
    if incoming is not None:
        if not hub.entry_identity(incoming) or incoming.get('key') != key:
            return False
        key = hub.compatible_key(data, incoming)
        incoming = dict(incoming, key=key)
    original = incoming or _selected_menu_entry(data, key, bucket, list_name)
    if not original or original.get('synthetic_next'):
        return False
    try:
        favourite, favourite_state = _favourite(original, data, bucket)
    except (ValueError, RuntimeError, TypeError):
        favourite, favourite_state = None, None
    rows = _menu_rows(original, data, favourite_state, list_name, bucket)
    from infinity_settings import choose
    selected = choose(str(original.get('label') or original.get('title') or 'Title'), [r[0] for r in rows])
    if not 0 <= selected < len(rows):
        return False  # cancellation does not refresh/rebind the underlying view
    label, op, selected_list = rows[selected]
    name = xbmcgui.Dialog().input('Add to custom list').strip()[:80] if op == 'add-list' else ''
    if op == 'add-list' and not name:
        return False
    with persistence_scope():
        current_data = hub.load(PROFILE)
        current = incoming or _selected_menu_entry(current_data, key, bucket, list_name)
        if not current:
            return False
        original_id, current_id = hub.entry_identity(original), hub.entry_identity(current)
        if (original_id or current_id):
            if not hub.same_identity(original_id, current_id):
                return False
        elif original != current:
            return False
        if (label, op, selected_list) not in _menu_rows(current, current_data, favourite_state, list_name, bucket):
            return False
        # A newer playback must never be removed/marked by a stale popup.
        if op in ('remove-resume', 'mark-watched', 'mark-unwatched') and (
                _menu_progress_state(original, data) != _menu_progress_state(current, current_data)):
            return False
        if op not in ('play', 'information', 'favourite'):
            changed, notice = _mutate_locked(op, key, selected_list, name=name, incoming=incoming)
        else:
            changed = False
    # Navigation, dialogs and favourites RPC never hold the progress writer.
    if op == 'play':
        if incoming is not None:
            progress = _menu_resume(current, current_data)
            if progress is not None:
                current, key, bucket = progress, progress['key'], 'continue'
        target, item = _list_item(current, current_data, bucket, list_name)
        if target.startswith('plugin://script.infinity.commandcenter/?action=saved-recovery&'):
            recover_entry(key, bucket, resume_offset=max(0.0, number(current.get('position')))
                          if hub.resume_visible(current_data, key) else 0)
        elif (hub.entry_identity(current) or {}).get('kind') in ('tvshow', 'season'):
            _rpc('GUI.ActivateWindow', {'window': 'videos', 'parameters': [target, 'return']})
        elif target:
            xbmc.Player().play(target, item)
        return bool(target)
    if op == 'information':
        _, item = _list_item(current, current_data, bucket, list_name)
        xbmcgui.Dialog().info(item)
        return True
    if op == 'favourite':
        current_favourite, current_state = _favourite(current, current_data, bucket)
        if current_favourite != favourite or current_state != favourite_state:
            return False
        _rpc('Favourites.AddFavourite', current_favourite)
        return True
    if changed:
        hub.flush_kodi_sync(PROFILE, retain_records=True)
        # Home observes the existing revision; only refresh this same CC list.
        if (xbmcgui.getCurrentWindowId() == 10025 and
                xbmc.getInfoLabel('Container.FolderPath').startswith('plugin://script.infinity.commandcenter/')):
            xbmc.executebuiltin('Container.Refresh')
    return changed


def _apply_identity(li, entry):
    ids = {name: str(entry.get(name)) for name in ('tmdb', 'tvdb', 'imdb') if str(entry.get(name) or '').strip()}
    if ids and hasattr(li, 'setUniqueIDs'):
        try:
            li.setUniqueIDs(ids)
        except Exception:
            pass
    for name, value in ids.items():
        li.setProperty('Infinity.UniqueID.' + name, value)


def _list_item(entry, data, bucket='', list_name='', render=None):
    key = str(entry.get('key') or '')
    target = navigation_target(entry, data, bucket, render)
    if not target:
        target = _url(action='unavailable')
    kind = entry.get('media')
    label = str(entry.get('label') or entry.get('title') or 'Resume Hub')
    rating = int((data.get('ratings', {}).get(key) or {}).get('rating') or entry.get('rating') or 0)
    label2 = ('★ %d/10' % rating) if rating else ''
    li = xbmcgui.ListItem(label=label, label2=label2, path=target, offscreen=True)
    watched = hub.is_watched(data, key)
    in_progress = hub.resume_visible(data, key) and number(entry.get('position')) > 0
    info = {
        'title': str(entry.get('title') or label),
        'mediatype': (hub.entry_identity(entry) or {}).get('kind') or ('episode' if kind == 'tv' else 'movie'),
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
    tier = render['tier'] if render is not None else (xbmcgui.Window(10000).getProperty('Infinity.Artwork.Quality') or 'standard')
    if entry.get('poster'):
        poster = artwork(entry['poster'], tier)
        art.update({'poster': poster, 'thumb': poster})
    if entry.get('fanart'):
        art['fanart'] = artwork(entry['fanart'], tier, True)
    if art:
        li.setArt(art)
    li.setProperty('IsPlayable', 'false' if (hub.entry_identity(entry) or {}).get('kind') in ('tvshow', 'season') else 'true')
    li.setProperty('Infinity.ResumeHub.Key', key)
    if render is not None and render.get('request'):
        li.setProperty('Infinity.ResumeHub.Request', render['request'])
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
    if bucket in ('later', 'watchlist', 'continue'):
        li.setProperty('Infinity.SavedNavigation.Listing', _url(action='library', media=kind, bucket=bucket))
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
    if bucket in ('watchlist', 'collection', 'ratings', 'later'):
        return hub.entries(data, media, bucket)
    if bucket == 'list':
        return hub.entries(data, media, 'list', list_name)
    return []


def _category(media, bucket='', list_name=''):
    title = 'Movies' if media == 'movie' else ('TV Shows' if media == 'tv' else 'Resume Hub')
    names = {'continue': 'Continue Playing', 'next': 'Next Episodes',
             'progress': 'Progress Shows', 'watchlist': 'Watchlist',
             'collection': 'Collection', 'later': 'Save For Later', 'history': 'Watched History',
             'watched': 'Watched History', 'ratings': 'Ratings',
             'custom-lists': 'Custom Lists', 'list': list_name or 'Custom List'}
    return title + ' — ' + names[bucket] if bucket in names else 'Infinity ' + title


def listing(media='all', bucket='continue', list_name=''):
    xbmcplugin.setPluginCategory(HANDLE, _category(media, bucket, list_name))
    started = time.monotonic()
    request = PARAMS.get('infinity_trace', '')
    if not re.fullmatch(r'[np][0-9]{1,30}', request):
        request = 'p' + str(time.monotonic_ns())
    timing = dict(request=request, media=media, bucket=bucket)
    hub.trace_timing('plugin_start', **timing)
    data = hub.load_view(PROFILE, timing_context=timing)
    hub.trace_timing('saved_state_ready', started, revision=int(data.get('revision') or 0), **timing)
    filtered = time.monotonic()
    values = _values_for(data, media, bucket, list_name)
    hub.trace_timing('filter_group', filtered, items=len(values), **timing)
    render = {'source_memory': setting_bool('source_memory_enabled', True),
              'tier': xbmcgui.Window(10000).getProperty('Infinity.Artwork.Quality') or 'standard',
              'installed': {}, 'request': request}
    xbmcplugin.setContent(HANDLE, 'episodes' if media == 'tv' else ('movies' if media == 'movie' else 'videos'))
    rendered = time.monotonic()
    for entry in values[:100]:
        target, li = _list_item(entry, data, bucket, list_name, render)
        xbmcplugin.addDirectoryItem(HANDLE, target, li, isFolder=(hub.entry_identity(entry) or {}).get('kind') in ('tvshow', 'season'))
    hub.trace_timing('directory_items', rendered, items=min(len(values), 100), revision=int(data.get("revision") or 0), **timing)
    xbmcplugin.endOfDirectory(HANDLE, succeeded=True, updateListing=False, cacheToDisc=False)
    hub.trace_timing('plugin_complete', started, items=min(len(values), 100), revision=int(data.get("revision") or 0), **timing)


def _directory(label, url, label2=''):
    li = xbmcgui.ListItem(label=label, label2=label2)
    li.setProperty('IsPlayable', 'false')
    xbmcplugin.addDirectoryItem(HANDLE, url, li, isFolder=True)


def navigator(media):
    title = _category(media)
    if media == 'movie':
        rows = (
            ('Continue Playing', 'continue', 'Local unfinished movies'),
            ('Watchlist', 'watchlist', 'Movies you want to watch'),
            ('Save For Later', 'later', 'Your separate local saved list'),
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
            ('Save For Later', 'later', 'Your separate local saved list'),
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
    xbmcplugin.setPluginCategory(HANDLE, _category(media, 'custom-lists'))
    for name in sorted(data.get('lists', {}), key=str.casefold):
        count = len([v for v in data['lists'][name].values()
                     if isinstance(v, dict) and (media == 'all' or v.get('media') == media)])
        if count:
            _directory(name, _url(action='library', media=media, bucket='list', list=name), '%d items' % count)
    xbmcplugin.endOfDirectory(HANDLE, succeeded=True, cacheToDisc=False)


def mutate():
    op = PARAMS.get('op', '')
    key = PARAMS.get('key', '')
    if op == 'trakt':
        from infinity_trakt import show_saved
        show_saved(key)
        xbmcplugin.endOfDirectory(HANDLE, succeeded=True, cacheToDisc=False)
        return
    list_name = PARAMS.get('list', '')
    if not hub.KEY_RE.fullmatch(key):
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False, cacheToDisc=False)
        return
    choice, name = None, ''
    # Dialogs never hold the cross-interpreter writer gate. Reload after input
    # so the resident playback observer's intervening progress is preserved.
    if op in ('rate', 'add-list'):
        preview = hub.load(PROFILE)
        entry = hub.find_entry(preview, key)
        if entry and op == 'rate':
            current = int((preview.get('ratings', {}).get(key) or {}).get('rating') or 0)
            options = ['Remove rating'] + ['%d / 10' % i for i in range(1, 11)]
            choice = xbmcgui.Dialog().select('Rate • ' + str(entry.get('label') or entry.get('title') or 'Title'),
                                             options, preselect=current)
        elif entry:
            name = xbmcgui.Dialog().input('Add to custom list').strip()[:80]
    try:
        with persistence_scope():
            changed, notice = _mutate_locked(op, key, list_name, choice, name)
        if changed:
            hub.flush_kodi_sync(PROFILE)
            try:
                xbmcgui.Dialog().notification('Infinity Resume Hub', notice, xbmcgui.NOTIFICATION_INFO, 2200)
            except Exception:
                pass
            xbmc.executebuiltin('Container.Refresh')
    except AdmissionClosed:
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False, cacheToDisc=False)
        return
    xbmcplugin.endOfDirectory(HANDLE, succeeded=True, cacheToDisc=False)


def _mutate_locked(op, key, list_name, choice=None, name='', incoming=None):
    data = hub.load(PROFILE)
    entry = hub.find_entry(data, key) or incoming
    if incoming is not None and (not hub.entry_identity(incoming) or not entry or
            not hub.same_identity(hub.entry_identity(entry), hub.entry_identity(incoming))):
        return False, ''
    native_watched = incoming is not None and incoming.get('_native_watched') is True
    if incoming is not None:
        incoming = {name: value for name, value in incoming.items() if name != '_native_watched'}
        entry = {name: value for name, value in entry.items() if name != '_native_watched'}
    changed = False
    notice = ''
    if op == 'mark-watched' and entry:
        data, changed_entry = hub.mark_watched_data(data, key, entry, completed=False)
        changed = changed_entry is not None
        if changed_entry:
            hub.queue_kodi_sync(data, changed_entry, True)
        notice = 'Marked watched'
    elif op == 'mark-unwatched':
        data, changed_entry = hub.mark_unwatched_data(data, key)
        if not changed_entry and native_watched:
            changed_entry = dict(entry)
        changed = changed_entry is not None
        if changed_entry:
            hub.queue_kodi_sync(data, changed_entry, False)
        notice = 'Marked unwatched'
    elif op in ('reset-progress', 'remove-resume'):
        data, removed = (hub.remove_resume_data(data, key, incoming) if op == 'remove-resume'
                         else hub.reset_progress_data(data, key))
        changed = removed is not None
        notice = 'Progress reset' if op == 'reset-progress' else 'Removed from Continue Playing'
    elif op == 'remove-later' and key in data.get('later', {}):
        data['later'].pop(key)
        changed = True
        notice = 'Removed from Save for Later'
    elif op == 'toggle-watchlist' and entry:
        data, added, changed_entry = hub.toggle_watchlist_data(data, key, incoming)
        changed = changed_entry is not None
        notice = 'Added to Watchlist' if added else 'Removed from Watchlist'
    elif op == 'toggle-collection' and entry:
        data, added, changed_entry = hub.toggle_collection_data(data, key, incoming)
        changed = changed_entry is not None
        notice = 'Added to Collection' if added else 'Removed from Collection'
    elif op == 'rate' and entry:
        if choice is not None and choice >= 0:
            data, result = hub.set_rating_data(data, key, choice)
            changed = True
            notice = 'Rating removed' if choice == 0 else 'Rated %d/10' % choice
    elif op == 'add-list' and entry:
        if name:
            data, result = hub.add_to_list_data(data, key, name, incoming)
            changed = result is not None
            notice = 'Added to ' + name
    elif op == 'remove-list' and list_name:
        data, removed = hub.remove_from_list_data(data, key, list_name)
        changed = removed is not None
        notice = 'Removed from ' + list_name
    if changed:
        if op in ('mark-watched', 'mark-unwatched'):
            overrides = data.setdefault('infinity_watched_overrides', {})
            if not isinstance(overrides, dict):
                raise RuntimeError('Unsupported watched override state')
            if op == 'mark-watched':
                overrides.pop(key, None)
            elif changed_entry:
                overrides[key] = dict(changed_entry, watched=False, updated=hub._now())
        data = hub.save(PROFILE, data, hub.publish_home, retain_records=True)
    return changed, notice


def play_saved(key):
    if hub.KEY_RE.fullmatch(key):
        data = hub.load_view(PROFILE)
        entry = data.get('items', {}).get(key)
        if entry and hub.entry_identity(entry) and not entry.get('synthetic_next'):
            target = navigation_target(entry, data, 'continue')
            if target.startswith('plugin://script.infinity.commandcenter/?action=saved-recovery&'):
                xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
                recover_entry(key, 'continue', resume_offset=max(0.0, number(entry.get('position'))))
                return
            if target:
                _, item = _list_item(entry, data, 'continue')
                xbmcplugin.setResolvedUrl(HANDLE, True, item)
                return
    xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())


def main():
    action = PARAMS.get('action', 'continue')
    if action == 'item-menu':
        show_item_menu(PARAMS.get('key', ''), PARAMS.get('bucket', 'continue'), PARAMS.get('list', '')); return
    if action == 'search-probe':
        xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=False)
        return
    if action == 'search-all':
        from infinity_search import search_all
        try:
            search_all(HANDLE, PARAMS.get('media', 'movie'), PARAMS.get('query', ''))
        finally:
            xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=False)
        return
    if action == 'search':
        from infinity_search import open_search
        open_search(PARAMS.get('media', 'movie'))
        xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=False)
        return
    if action in ('saved-fallback', 'saved-recovery'):
        recover_entry(PARAMS.get('key', ''), PARAMS.get('bucket', 'later'),
                      PARAMS.get('token', ''), number(PARAMS.get('resume', '0'))); return
    if action == 'saved-confirm':
        from saved_navigation import confirm_saved
        confirm_saved(PROFILE, PARAMS.get('key', ''), PARAMS.get('token', '')); return
    if action == 'play-saved':
        play_saved(PARAMS.get('key', '')); return
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
