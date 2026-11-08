# SPDX-License-Identifier: GPL-2.0-or-later
"""Kodi context-item ingress into the existing local persistence participant.

Kodi supplies a selected ListItem copy. Titles, folder rows, untyped streams,
and unnamespaced IDs never authorize mutation. No provider code is replaced.
"""
from __future__ import annotations

# INFINITY_AUTHENTICATED_MODULE_BOOTSTRAP_V1
import sys as _infinity_sys
import xbmcaddon as _infinity_addon
import xbmcvfs as _infinity_vfs
_infinity_cc = _infinity_addon.Addon('script.infinity.commandcenter')
_infinity_root = _infinity_vfs.translatePath(_infinity_cc.getAddonInfo('path')).rstrip('/')
_infinity_base = _infinity_root.rsplit('/', 1)[0] + '/'
_infinity_prefixes = tuple(_infinity_base + name for name in (
    'script.infinity.commandcenter', 'script.infinity.uirepair',
    'script.infinity.watchedbridge', 'script.infinity.rails'))
_infinity_paths = _infinity_sys.path[:]
try:
    # The trust helper's standard-library imports cannot be shadowed by an
    # unlisted source file in an owned component before its guard is active.
    _infinity_sys.path[:] = [p for p in _infinity_paths if p.startswith('/') and not any(
        p == root or p.startswith(root + '/') for root in _infinity_prefixes)]
    import hashlib as _infinity_hash
    import types as _infinity_types
    with open(_infinity_root + '/module_contract.py', 'rb') as _infinity_stream:
        _infinity_raw = _infinity_stream.read(4 * 1024 * 1024 + 1)
    if _infinity_hash.sha256(_infinity_raw).hexdigest() != '759e60439fae0b1bf0f8a2ff6895209ac848101b9544ac6c0e297b9c73df1267':
        raise RuntimeError('The trusted Infinity module bootstrap changed. Install the matching native package.')
    _infinity_contract_module = _infinity_sys.modules.get('module_contract')
    if _infinity_contract_module is None:
        _infinity_contract_module = _infinity_types.ModuleType('module_contract')
        _infinity_contract_module.__file__ = _infinity_root + '/module_contract.py'
        _infinity_sys.modules['module_contract'] = _infinity_contract_module
        exec(compile(_infinity_raw, _infinity_contract_module.__file__, 'exec', dont_inherit=True),
             _infinity_contract_module.__dict__)
finally:
    _infinity_sys.path[:] = _infinity_paths
_infinity_sys.path.insert(0, _infinity_root)
_infinity_contract = _infinity_contract_module.active_contract(
    _infinity_root, _infinity_cc.getAddonInfo('version'))
del _infinity_raw, _infinity_paths
# END_INFINITY_AUTHENTICATED_MODULE_BOOTSTRAP_V1


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


def _watchnixtoons_identity_slot(route):
    import hashlib
    if not isinstance(route, str) or not route.startswith('plugin://plugin.video.watchnixtoons2/') or len(route) > 8192:
        return ''
    return hashlib.sha256(route.encode('utf-8')).hexdigest()


def _watchnixtoons_verified_link(data, route, kind):
    """An opt-in link can be reused only for this exact provider URI and media kind."""
    slot = _watchnixtoons_identity_slot(route)
    links = data.get('nixtoons_verified_links', {})
    if not slot or not isinstance(links, dict):
        return None
    row = links.get(slot)
    if (not isinstance(row, dict) or row.get('source') != route or
            row.get('stable_source') != route or row.get('media') !=
            ('movie' if kind == 'movie' else 'tv')):
        return None
    identity = hub.entry_identity(row)
    if not identity or identity.get('kind') != kind or hub.identity_key(identity) != row.get('key'):
        return None
    return dict(row)


def _watchnixtoons_owned_records(data, route):
    """Inspect every owned list, not only Resume Hub's five primary buckets."""
    for bucket in ('items', 'watched', 'watchlist', 'collection', 'later'):
        for record in data.get(bucket, {}).values():
            if isinstance(record, dict) and record.get('source') == route:
                yield record
    for values in data.get('lists', {}).values():
        if isinstance(values, dict):
            for record in values.values():
                if isinstance(record, dict) and record.get('source') == route:
                    yield record


def _watchnixtoons_store_verified_link(item, route, kind, entry):
    """Persist only the explicitly confirmed typed-ID association, not a tracking action.

    Fail closed on a conflicting route identity, unsupported schema or full map.
    The existing essential participant owns atomic writes and checkpoint proof.
    """
    slot = _watchnixtoons_identity_slot(route)
    identity = hub.entry_identity(entry)
    if (not slot or not identity or identity.get('kind') != kind or
            entry.get('source') != route or entry.get('stable_source') != route or
            entry.get('key') != hub.identity_key(identity) or
            item.getPath() != route or item.getVideoInfoTag().getMediaType() != kind):
        return False
    profile = addon_profile()
    with persistence_scope():
        data = hub.load(profile)
        links = data.get('nixtoons_verified_links', {})
        if not isinstance(links, dict):
            return False
        old = _watchnixtoons_verified_link(data, route, kind)
        if slot in links and not old:
            return False
        if old is not None and not hub.same_identity(hub.entry_identity(old), identity):
            return False
        for row in _watchnixtoons_owned_records(data, route):
            bound = hub.entry_identity(row)
            if bound is not None and not hub.same_identity(bound, identity):
                return False
        if old is not None:
            return True
        if len(links) >= 500:
            return False  # Never evict user-approved links as an implicit side effect.
        linked = {key: value for key, value in entry.items() if key != '_native_watched'}
        linked['source'] = route
        linked['stable_source'] = route
        updated = dict(links)
        updated[slot] = linked
        data['nixtoons_verified_links'] = updated
        hub.save(profile, data, hub.publish_home, retain_records=True)
    return True


def _watchnixtoons_exact_previous(item, route, kind):
    """Reuse ONLY a prior verified identity bound to this exact provider route.

    Never infer from a title, season label, poster or another add-on's route.
    Conflicting stored identities require fresh, user-confirmed verification.
    Read-only: neither this lookup nor holding the menu changes saved data.
    """
    data=hub.load_view(addon_profile())
    matches=[]
    media='movie' if kind=='movie' else 'tv'
    verified = _watchnixtoons_verified_link(data, route, kind)
    candidates = list(_watchnixtoons_owned_records(data, route))
    if verified is not None:
        candidates.append(verified)
    for row in candidates:
        if row.get('stable_source') != route:
            continue
        identity=hub.entry_identity(row)
        if not identity or row.get('media')!=media or identity['kind']!=kind:
            continue
        if kind in ('season','episode') and (hub.episode_number(row.get('season')) !=
                                              hub.episode_number(item.getVideoInfoTag().getSeason())):
            continue
        if kind=='episode' and (hub.episode_number(row.get('episode')) !=
                                hub.episode_number(item.getVideoInfoTag().getEpisode())):
            continue
        matches.append((row,identity))
    if not matches or not all(hub.same_identity(matches[0][1], ident) for _,ident in matches):
        return None
    row=dict(matches[0][0])
    row['key']=hub.identity_key(matches[0][1])
    row['title']=str(item.getVideoInfoTag().getTitle() or item.getLabel())
    row['label']=str(item.getLabel())
    row['poster']=item.getArt('poster') or item.getArt('thumb')
    row['fanart']=item.getArt('fanart')
    row['_native_watched']=item.getVideoInfoTag().getPlayCount()>0
    return row if hub.entry_identity(row) else None


def _watchnixtoons_confirmed_entry(item,route,kind,title):
    """Get typed ID from a pin-verified Search provider after explicit user consent.

    Only the same first-party Search inventory/route and native lease are used.
    One eligible provider at a time, never provider edits or title guessing.
    User selection + confirmation is mandatory. No mapping is saved here.
    """
    from infinity_search import providers, _provider_result, _Cancellation
    from infinity_settings import choose
    media='movie' if kind=='movie' else 'tv'
    search=xbmcgui.Dialog().input('Find the verified title for WatchNixtoons2',title[:160]).strip()
    if not search or len(search)>160 or any(ord(ch)<32 for ch in search):
        return None
    ready,_=providers(media,force=True)
    # Nixtoons itself supplies no trusted cross-provider unique IDs here.
    # Keep the published search capability and component hash/lease checks.
    ready=[p for p in ready if p.get('id')!='plugin.video.watchnixtoons2' and
           isinstance(p.get('id'),str) and isinstance(p.get('contract'),dict)]
    if not ready:
        xbmcgui.Dialog().ok('Infinity Trakt','No verified metadata provider is available. No tracking record was changed.')
        return None
    which=choose('Choose verified metadata provider',[p['name'] for p in ready])
    if not isinstance(which,int) or not 0<=which<len(ready):return None
    provider=ready[which]
    home=xbmcgui.Window(10000)
    progress=xbmcgui.DialogProgress()
    progress.create('Infinity Trakt','Checking verified media IDs')
    cancel=_Cancellation()
    try:
        found,status,result,_=_provider_result(provider,search,home,cancel)
    finally:
        cancel.cancel();progress.close()
    if found['id']!=provider['id'] or status!='completed' or 'error' in result:
        xbmcgui.Dialog().ok('Infinity Trakt','The metadata provider could not confirm a result. No records were changed.')
        return None
    rows=result.get('result',{}).get('files',[])
    if not isinstance(rows,list):return None
    candidates=[]
    for row in rows[:40]:
        if not isinstance(row,dict) or row.get('type')!=('movie' if media=='movie' else 'tvshow'):
            continue
        origin=row.get('file','')
        if not isinstance(origin,str) or not origin.startswith('plugin://'+provider['id']+'/'):
            continue
        ids=hub.verified_ids(row.get('uniqueid'))
        if not ids:continue
        if kind=='movie':identity=hub.media_identity('movie',ids)
        elif kind=='episode':identity=hub.media_identity('tv',{},item.getVideoInfoTag().getSeason(),
                              item.getVideoInfoTag().getEpisode(),show_ids=ids)
        else:identity=hub.show_identity(kind,ids,item.getVideoInfoTag().getSeason())
        if not identity or not hub.identity_key(identity):continue
        name=row.get('title') or row.get('label')
        if not isinstance(name,str) or not name.strip() or len(name)>512:continue
        year=row.get('year')
        year=str(year) if type(year) is int and 1900<=year<=2100 else 'Year unknown'
        idhint=', '.join(n.upper()+':'+v for n,v in ids.items())
        candidates.append((name,year,idhint,identity,ids))
    if not candidates:
        xbmcgui.Dialog().ok('Infinity Trakt','This provider returned no verified IDs for the selected media type. Saved records were not changed.')
        return None
    which=choose('Confirm the exact title',[
        name+' ('+year+') — '+idhint for name,year,idhint,_,_ in candidates])
    if not isinstance(which,int) or not 0<=which<len(candidates):return None
    name,year,idhint,identity,ids=candidates[which]
    # The user must explicitly confirm this source record. The provider title
    # need not match the source label (dub/localization/spin-offs differ).
    if not xbmcgui.Dialog().yesno('Verify WatchNixtoons2 identity',
            'Source: '+title[:150]+'\nVerified: '+name[:150]+' ('+year+')\n'+idhint[:150]+
            '\nUse this verified identity for the selected action?'):
        return None
    if item.getPath()!=route or item.getVideoInfoTag().getMediaType()!=kind:return None
    key=hub.identity_key(identity)
    tag=item.getVideoInfoTag()
    entry=dict(key=key,identity=identity,media=media,title=title,label=item.getLabel(),
        source=route,stable_source=route,season=hub.episode_number(tag.getSeason()) if kind in ('season','episode') else -1,
        episode=hub.episode_number(tag.getEpisode()) if kind=='episode' else -1,dbid=-1,
        poster=item.getArt('poster') or item.getArt('thumb'),fanart=item.getArt('fanart'),
        _native_watched=tag.getPlayCount()>0,**ids)
    if not hub.entry_identity(entry) or entry['key'] != hub.identity_key(hub.entry_identity(entry)):
        return None
    if not _watchnixtoons_store_verified_link(item, route, kind, entry):
        xbmcgui.Dialog().ok('Infinity Trakt', 'The verified link could not be saved safely. No tracking action was performed.')
        return None
    return entry


def _watchnixtoons_source_entry(item, route, kind, title):
    """Direct local-only tracking from the selected, exact Nixtoons page URL.

    Never present a source digest as a TMDb/IMDb/TVDb ID or silently sync Trakt.
    The original plugin route remains the only playback/navigation destination.
    """
    tag = item.getVideoInfoTag()
    identity = hub.watchnixtoons_source_identity(route, kind, tag.getSeason(), tag.getEpisode())
    key = hub.identity_key(identity)
    if not key or item.getPath() != route or tag.getMediaType() != kind:
        return None
    return dict(key=key, identity=identity, media='movie' if kind=='movie' else 'tv',
                title=title, label=item.getLabel(), source=route, stable_source=route,
                season=hub.episode_number(tag.getSeason()) if kind in ('season','episode') else -1,
                episode=hub.episode_number(tag.getEpisode()) if kind=='episode' else -1,
                dbid=-1, poster=item.getArt('poster') or item.getArt('thumb'),
                fanart=item.getArt('fanart'), _native_watched=tag.getPlayCount()>0)


def _watchnixtoons_tracking(item,route,kind,title,label,op):
    # Identity stays independent of the Nixtoons provider URI; the original
    # URI is retained only for play/open after a user-verified typed-ID link.
    entry=_watchnixtoons_exact_previous(item,route,kind)
    if entry is None:entry=_watchnixtoons_source_entry(item,route,kind,title)
    if entry is None:
        # Refuse to guess when this provider does not expose a source URL.
        xbmcgui.Dialog().ok('Infinity Tracked','This item has no verifiable WatchNixtoons2 source location. Nothing was changed.')
        return False
    if item.getPath()!=route or item.getVideoInfoTag().getMediaType()!=kind:return False
    completed = _popup_module().show_item_menu(entry['key'],bucket='',incoming=entry,
                                         nixtoons_confirmed_row=(label,op,''))
    if completed and (hub.entry_identity(entry) or {}).get('scope') == 'watchnixtoons_local':
        # Trakt and third-party provider databases are not modified by local actions.
        try:
            xbmcgui.Dialog().notification('Infinity Tracked', 'Saved in Infinity locally • Trakt not synced', xbmcgui.NOTIFICATION_INFO, 2600)
        except Exception:
            pass
    return completed


def _unverified_anime_menu(item):
    """Never invent a media identity. Provider paths remain exact."""
    import json
    from urllib.parse import urlsplit
    from title_metadata import capture
    from infinity_settings import choose
    route = item.getPath()
    if not isinstance(route, str) or len(route)>8192 or any(ord(c)<32 for c in route):
        return False
    parsed=urlsplit(route)
    sources={'plugin.video.otaku':'Otaku',
             'plugin.video.watchnixtoons2':'WatchNixtoons2'}
    if parsed.scheme!='plugin' or parsed.netloc not in sources or not route.startswith('plugin://'+parsed.netloc+'/'):
        return False
    tag=item.getVideoInfoTag()
    kind=tag.getMediaType()
    if kind not in ('movie','tvshow','episode','season'):
        return False
    title=str(tag.getTitle() or item.getLabel() or '').strip()
    if not title or len(title)>512 or any(ord(c)<32 for c in title):
        return False
    folder=bool(item.isFolder()) or kind in ('tvshow','season')
    spec={'title':title,'type':'window' if folder else 'media'}
    if folder: spec.update(window='videos',windowparameter=route)
    else: spec['path']=route
    art=item.getArt('poster') or item.getArt('thumb')
    if isinstance(art,str) and 0<len(art)<=2048: spec['thumbnail']=art

    def rpc(name,params):
        result=json.loads(xbmc.executeJSONRPC(json.dumps({
            'jsonrpc':'2.0','id':1,'method':name,'params':params})))
        if not isinstance(result,dict) or 'error' in result:
            raise RuntimeError('Kodi refused the selected original-item action')
        return result.get('result') or {}

    def existing_favourite():
        saved=rpc('Favourites.GetFavourites',
                  {'properties':['path','window','windowparameter','thumbnail']}).get('favourites',[])
        if not isinstance(saved,list): return None
        matches=[row for row in saved if isinstance(row,dict) and
                 row.get('type')==spec['type'] and
                 (row.get('windowparameter')==route and
                  str(row.get('window','')).lower() in ('videos','10025')
                  if folder else row.get('path')==route)]
        return bool(matches) if len(matches)<=1 else None

    try: favourite=existing_favourite()
    except (RuntimeError,ValueError,TypeError): favourite=None
    if parsed.netloc=='plugin.video.watchnixtoons2':
        # Exactly one exception to the otherwise frozen anime fallback:
        # show the SAME applicable tracking choices as the universal menu.
        # No identity-dependent action can run until verified explicitly.
        linked=_watchnixtoons_exact_previous(item,route,kind)
        if linked is not None:
            return _popup_module().show_item_menu(linked['key'],bucket='',incoming=linked)
        rows=[('Open in WatchNixtoons2','open'),('Mark Watched','track:mark-watched'),
              ('Add to Watchlist','track:toggle-watchlist')]
        if favourite is not None:
            rows.append(('Remove from Favourites' if favourite else 'Add to Favourites','favourite'))
        rows.extend([('Add to Collection','track:toggle-collection'),
                     ('Add to Custom List','track:add-list'),
                     ('Save for Later','track:save-later'),('Information','information')])
    else:
        rows=[('Open in '+sources[parsed.netloc],'open'),
              ('Information','information')]
        if favourite is not None:
            rows.append(('Remove from Favourites' if favourite else 'Add to Favourites','favourite'))
    selected=choose(title,[label for label,_ in rows])
    if not isinstance(selected,int) or not 0<=selected<len(rows):
        return False
    if item.getPath()!=route or item.getVideoInfoTag().getMediaType()!=kind:
        return False
    action=rows[selected][1]
    if parsed.netloc=='plugin.video.watchnixtoons2' and action.startswith('track:'):
        return _watchnixtoons_tracking(item,route,kind,title,rows[selected][0],action[6:])
    if action=='information':
        from information import show_information
        record={'title':title,'label':title,
                'poster':art if isinstance(art,str) else '',
                'information':capture(item)}
        show_information(item,record,play_available=False)
        return True
    if action=='favourite':
        if existing_favourite()!=favourite: return False
        rpc('Favourites.AddFavourite',spec)
        return True
    if folder:
        rpc('GUI.ActivateWindow',{'window':'videos','parameters':[route,'return']})
    else:
        xbmc.Player().play(route,item)
    return True


def title_popup(item, requested_action=None):
    """Native exact-item handoff for Infinity's Movie/TV title holds only."""
    if xbmc.getSkinDir() != 'skin.infinity.diggz' or item is None:
        return False
    if requested_action not in (None, 'mark-watched', 'mark-unwatched'):
        return False
    from infinity_trakt import _bridge, selected, notice
    try:
        if getattr(item, 'getProperty', lambda name: '')('Infinity.Selection.Unsupported'):
            return False  # Synthetic next-up candidates do not authorize title mutations.
        from selection_contract import read
        selection = read(item)
        if selection is not None:
            return _popup_module().show_item_menu(selection['key'], selection['bucket'], selection['list'],
                                                 expected_selection=selection['token'], requested_action=requested_action)
        if getattr(item, 'getProperty', lambda name: '')('Infinity.Selection.Contract'):
            return False  # Never fall back from a malformed owned selection.
        if item.getVideoInfoTag().getMediaType() not in ('movie', 'tvshow', 'episode', 'season'):
            return False
        path = item.getPath()
        anime = isinstance(path,str) and path.startswith(
            ('plugin://plugin.video.otaku/','plugin://plugin.video.watchnixtoons2/'))
        if anime:
            tag = item.getVideoInfoTag()
            ids=hub.verified_ids({n:tag.getUniqueID(n) for n in ('tmdb','imdb','tvdb')})
            if not ids:
                if requested_action is not None:
                    if not path.startswith('plugin://plugin.video.watchnixtoons2/'):
                        return False
                    title = str(tag.getTitle() or item.getLabel() or '').strip()
                    if not title or len(title) > 512 or any(ord(c) < 32 for c in title):
                        return False
                    return _watchnixtoons_tracking(item, path, tag.getMediaType(), title,
                        'Mark Watched' if requested_action == 'mark-watched' else 'Mark Unwatched', requested_action)
                return _unverified_anime_menu(item)
        bridge, modules = _bridge()
        candidate = item
        if item.getPath().startswith('plugin://plugin.infinity.latestreleases/'):
            # Reuse the unchanged, pinned lossless wrapper decoder. Its exact
            # original provider route and IDs must agree with this item copy.
            import hashlib
            import importlib.util
            from pathlib import Path
            import xbmcaddon
            import xbmcvfs
            from module_contract import source_module
            relative = 'script.infinity.commandcenter/infinity_modules/uirepair/latest_identity.py'
            if _infinity_contract.files.get(relative) != '225ac23336701db63715583ca8b6716afa96bb9b738b4b99750d9a5bbd8ab223':
                raise RuntimeError('The media identity component differs from the verified release.')
            decoder = source_module(_infinity_contract, '_infinity_title_identity', relative)
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
            if requested_action is not None:
                notice('This title has no supported verified media identity. Its records were retained.')
                return False
            if anime:
                return _unverified_anime_menu(item)
            notice('This title has no supported verified media identity. Its records were retained.')
            return False
        # The verified selected copy owns the metadata. Do not consult a later
        # global selection, generate a synopsis, or truncate the original text.
        from title_metadata import capture
        entry['information'] = capture(candidate)
        entry['_native_watched'] = item.getVideoInfoTag().getPlayCount() > 0
        return _popup_module().show_item_menu(entry['key'], bucket='', incoming=entry, requested_action=requested_action)
    except (OSError, ValueError, RuntimeError, AttributeError) as error:
        notice(str(error), 'Title options')
        return False


def main():
    if len(sys.argv) == 2 and sys.argv[1] in ('infinity-mark-watched-v1', 'infinity-mark-unwatched-v1'):
        return title_popup(getattr(sys, 'listitem', None),
            'mark-watched' if sys.argv[1] == 'infinity-mark-watched-v1' else 'mark-unwatched')
    if len(sys.argv) == 2 and sys.argv[1] == 'infinity-item-menu-v1':
        return title_popup(getattr(sys, 'listitem', None))
    from infinity_trakt import main as local_tracking
    local_tracking(getattr(sys, 'listitem', None))

if __name__ == '__main__':
    main()
