# SPDX-License-Identifier: GPL-2.0-or-later
"""Kodi context-item ingress into the existing local persistence participant.

Kodi supplies a selected ListItem copy. Titles, folder rows, untyped streams,
and unnamespaced IDs never authorize mutation. No provider code is replaced.
"""
from __future__ import annotations

import json
import sys
from urllib.parse import urlencode

import xbmc
import xbmcgui

from common import addon_profile, persistence_scope
from experience import stable_route, number
from persistence_participant import AdmissionClosed
import resume_hub as hub


def view_hub():
    xbmc.executebuiltin('ActivateWindow(Videos,plugin://script.infinity.commandcenter/?action=resume,return)')


def can_resume(entry, sources):
    if not entry or not hub.entry_identity(entry) or entry.get('synthetic_next'):
        return False
    preference = sources.get(entry['key'], {}) if isinstance(sources, dict) else {}
    if not isinstance(preference, dict):
        preference = {}
    route = stable_route(preference.get('route') or entry.get('stable_source') or entry.get('source'))
    if route and number(preference.get('failures')) < 2:
        host = route.split('/')[2] if route.startswith('plugin://') else ''
        if not host or xbmc.getCondVisibility('System.HasAddon(%s)' % host):
            return True
    tmdb = entry.get('tmdb') if entry.get('media') == 'movie' else (
        entry.get('show_tmdb') if entry.get('show_ids_verified') is True else '')
    return str(tmdb or '').isdigit() and xbmc.getCondVisibility('System.HasAddon(plugin.video.themoviedb.helper)')


def selected_entry(item):
    """Read only typed metadata from this selected copy; no global player fallback."""
    try:
        if item is None or item.isFolder():
            return None
        tag = item.getVideoInfoTag()
        kind = tag.getMediaType()
        if kind not in ('movie', 'episode'):
            return None
        ids = hub.verified_ids({name: tag.getUniqueID(name) for name in ('tmdb', 'tvdb', 'imdb')})
        season = tag.getSeason() if kind == 'episode' else -1
        episode = tag.getEpisode() if kind == 'episode' else -1
        media = 'tv' if kind == 'episode' else 'movie'
        identity = hub.media_identity(media, ids, season, episode)
        key = hub.identity_key(identity)
        if not key:
            return None
        title = str(tag.getTitle() or item.getLabel() or '').strip()[:512]
        show = str(tag.getTVShowTitle() or '').strip()[:512] if media == 'tv' else ''
        entry = dict(key=key, identity=identity, media=media, title=title, label=title,
                     showtitle=show, season=season, episode=episode, dbid=-1,
                     source=stable_route(item.getPath()),
                     stable_source=stable_route(item.getPath()),
                     poster=str(item.getArt('poster') or item.getArt('thumb') or '')[:2048],
                     fanart=str(item.getArt('fanart') or '')[:2048], **ids)
        dbid = tag.getDbId()
        if type(dbid) is int and dbid > 0:
            field = 'episodeid' if media == 'tv' else 'movieid'
            details_key = 'episodedetails' if media == 'tv' else 'moviedetails'
            properties = ['uniqueid'] + (['season', 'episode'] if media == 'tv' else [])
            raw = json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0', id=1,
                method='VideoLibrary.GetEpisodeDetails' if media == 'tv' else 'VideoLibrary.GetMovieDetails',
                params={field: dbid, 'properties': properties}))))
            details = raw.get('result', {}).get(details_key, {}) if isinstance(raw, dict) else {}
            actual = hub.media_identity(media, details.get('uniqueid'),
                                        details.get('season', -1), details.get('episode', -1))
            matched = ('error' not in raw and type(details.get(field)) is int and
                       details[field] == dbid and hub.same_identity(identity, actual))
            if matched:
                entry['dbid'] = dbid
            elif str(item.getPath()).startswith('videodb://'):
                return None  # A stale native library row cannot authorize changes.
        return entry
    except (AttributeError, TypeError, ValueError, KeyError, RuntimeError):
        return None


def publish_selected_state(item, entry, data):
    """Decorate only the selected copy, never claim all provider rows are decorated."""
    key = entry['key']
    item.setProperty('Infinity.ResumeHub.Key', key)
    item.setProperty('Infinity.ResumeHub.Watched', 'true' if key in data['watched'] else 'false')
    item.setProperty('Infinity.ResumeHub.InProgress', 'true' if key in data['items'] else 'false')
    item.setProperty('Infinity.ResumeHub.Revision', str(data['revision']))


def apply_action(profile, entry, action):
    """One writer gate covers reloading, identity comparison, mutation and save."""
    if not hub.entry_identity(entry) or entry['key'] != hub.identity_key(entry['identity']):
        return False
    with persistence_scope():
        data = hub.load(profile)
        key = hub.compatible_key(data, entry)
        saved = hub.find_entry(data, key)
        if saved and not hub.same_identity(hub.entry_identity(saved), entry['identity']):
            return False  # Legacy/ambiguous state stays untouched.
        admitted = dict(saved or entry, key=key)
        changed = None
        if action == 'mark-watched':
            data, changed = hub.mark_watched_data(data, key, admitted, completed=False)
            if changed:
                hub.queue_kodi_sync(data, changed, True)
        elif action == 'mark-unwatched':
            data, changed = hub.mark_unwatched_data(data, key)
            if changed:
                hub.queue_kodi_sync(data, changed, False)
        elif action == 'toggle-watchlist':
            data, _, changed = hub.toggle_watchlist_data(data, key, admitted)
        elif action == 'remove-resume':
            data, changed = hub.remove_resume_data(data, key)
        if changed is None:
            return False
        hub.save(profile, data, hub.publish_home)
    # Failed native synchronization remains durably queued and checkpoint-blocking.
    hub.flush_kodi_sync(profile)
    return True


def _popup_module():
    # Import the already verified owner, with no global focus lookup.
    import importlib.util
    from pathlib import Path
    previous = sys.argv
    try:
        sys.argv = ['plugin://script.infinity.commandcenter/', '-1', '']
        spec = importlib.util.spec_from_file_location('_infinity_title_popup', Path(__file__).with_name('plugin.py'))
        menu = importlib.util.module_from_spec(spec); spec.loader.exec_module(menu)
        return menu
    finally:
        sys.argv = previous


def title_popup(item):
    """Native exact-item handoff for Infinity's Movie/TV title holds only."""
    if xbmc.getSkinDir() != 'skin.infinity.diggz' or item is None:
        return False
    from infinity_trakt import _bridge, selected, notice
    try:
        if getattr(item, 'getProperty', lambda name: '')('Infinity.Selection.Unsupported'):
            return False  # Synthetic next-up candidates do not authorize title mutations.
        from selection_contract import read
        selection = read(item)
        if selection is not None:
            return _popup_module().show_item_menu(selection['key'], selection['bucket'], selection['list'],
                                                 expected_selection=selection['token'])
        if getattr(item, 'getProperty', lambda name: '')('Infinity.Selection.Contract'):
            return False  # Never fall back from a malformed owned selection.
        bridge, modules = _bridge()
        if item.getVideoInfoTag().getMediaType() not in ('movie', 'tvshow', 'episode', 'season'):
            return False
        candidate = item
        if item.getPath().startswith('plugin://plugin.infinity.latestreleases/'):
            # Reuse the unchanged, pinned lossless wrapper decoder. Its exact
            # original provider route and IDs must agree with this item copy.
            import hashlib
            import importlib.util
            from pathlib import Path
            import xbmcaddon
            import xbmcvfs
            root = Path(xbmcvfs.translatePath(xbmcaddon.Addon('script.infinity.uirepair').getAddonInfo('path')))
            path = root / 'latest_identity.py'
            if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != '225ac23336701db63715583ca8b6716afa96bb9b738b4b99750d9a5bbd8ab223':
                raise RuntimeError('The media identity component differs from the verified release.')
            spec = importlib.util.spec_from_file_location('_infinity_title_identity', path)
            decoder = importlib.util.module_from_spec(spec); spec.loader.exec_module(decoder)
            value = decoder.decode(item.getPath())
            tag = item.getVideoInfoTag()
            ids = hub.verified_ids({n: tag.getUniqueID(n) for n in ('tmdb','imdb','tvdb')})
            verified_ids = hub.verified_ids(value['ids'])
            if (value['kind'] != tag.getMediaType() or not verified_ids or
                    any(verified_ids.get(name) != identifier for name, identifier in ids.items())):
                raise RuntimeError('The selected title identity does not match its provider destination.')
            class OriginalTag:
                def __getattr__(self, name): return getattr(tag, name)
                def getUniqueID(self, name): return verified_ids.get(name, '')
            class OriginalTitle:
                def __getattr__(self, name): return getattr(item, name)
                def getPath(self): return value['route']
                def getVideoInfoTag(self): return OriginalTag()
                def isFolder(self): return False if value['kind'] == 'movie' else item.isFolder()
            candidate = OriginalTitle()
        entry = selected(candidate, bridge, modules)
        if not entry:
            notice('This title has no supported verified media identity. Its records were retained.')
            return False
        # The verified selected copy owns the metadata. Do not consult a later
        # global selection, generate a synopsis, or truncate the original text.
        from title_metadata import capture
        entry['information'] = capture(candidate)
        entry['_native_watched'] = item.getVideoInfoTag().getPlayCount() > 0
        return _popup_module().show_item_menu(entry['key'], bucket='', incoming=entry)
    except (OSError, ValueError, RuntimeError, AttributeError) as error:
        notice(str(error), 'Title options')
        return False


def main():
    if len(sys.argv) == 2 and sys.argv[1] == 'infinity-item-menu-v1':
        return title_popup(getattr(sys, 'listitem', None))
    from infinity_trakt import main as local_tracking
    local_tracking(getattr(sys, 'listitem', None))

if __name__ == '__main__':
    main()
