# SPDX-License-Identifier: GPL-2.0-or-later
from __future__ import annotations

import json
import os
from pathlib import Path
import time
import threading
from functools import wraps

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

from common import (ADDON_ID, addon_profile, atomic_json, jsonrpc, log, read_json,
                    semantic_playback_key, setting_bool, setting_int, setting_str, backup_ui_if_healthy,
                    ui_health, self_heal_ui, addon_set_setting, refresh_runtime_state, skin_baseline_integrity,
                    nonnegative_int)
from view_mode import resolve_effective_view_mode
from experience import ExperienceController
import resume_hub as hub
import skin_upgrade

HOME = xbmcgui.Window(10000)
COMMAND_ADDON = xbmcaddon.Addon()
COMMAND_ICON = xbmcvfs.translatePath(COMMAND_ADDON.getAddonInfo('icon')) if COMMAND_ADDON.getAddonInfo('icon') else xbmcgui.NOTIFICATION_INFO
PLAYBACK_FILE = 'playback-memory.json'
CONTINUE_FILE = hub.CONTINUE_FILE
GUARDIAN_FILE = 'guardian-state.json'
_integrity_cache = None
_integrity_signature = None
_integrity_checked_at = 0.0
PROGRESS_LOCK = threading.RLock()


def _serialized_progress(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        with PROGRESS_LOCK:
            return fn(*args, **kwargs)
    return wrapped


def _background_integrity():
    """Keep the one-second capability publisher free of repeated full-file hashing.

    Manual common.skin_baseline_integrity() calls remain immediate. A changed
    installed manifest or skin path invalidates the background cache at once.
    """
    global _integrity_cache, _integrity_signature, _integrity_checked_at
    root = Path(xbmcvfs.translatePath('special://skin'))
    try:
        stat = (root / 'Infinity-Protected-Manifest.json').stat()
        signature = (str(root), stat.st_mtime_ns, stat.st_size, stat.st_ino)
    except OSError:
        signature = (str(root), None)
    now = time.monotonic()
    if _integrity_cache is None or signature != _integrity_signature or now - _integrity_checked_at >= 30.0:
        _integrity_cache = skin_baseline_integrity()
        _integrity_signature = signature
        _integrity_checked_at = now
    return _integrity_cache


def _set(name, value):
    """Publish a Home property only when its value actually changed.

    Several runtime/capability publishers run on a short cadence. Avoiding
    identical setProperty() calls reduces GUI invalidation and accessibility /
    observer churn without changing any public Infinity property contract.
    """
    try:
        text = str(value)
        if HOME.getProperty(name) != text:
            HOME.setProperty(name, text)
    except Exception:
        pass


def _refresh_setting(key: str, default: str) -> str:
    try:
        value = xbmcaddon.Addon('service.infinity.refresh').getSetting(key)
        return value if value else default
    except Exception:
        return default


def publish_refresh_state():
    mode = _refresh_setting('mode', 'auto').strip().lower()
    cap = _refresh_setting('max_hz', 'auto').strip().lower()
    if mode not in ('auto','performance','balanced','system','off'):
        mode = 'auto'
    if cap not in ('auto','60','90','120','highest'):
        cap = 'auto'
    if mode == 'performance': cap = 'highest'
    elif mode == 'balanced' and cap in ('auto','highest'): cap = '90'
    _set('Infinity.RefreshUserMode', mode)
    _set('Infinity.RefreshMaxHz', cap)
    _set('Infinity.RefreshSelectionConfirmed', 'true')
    _set('Infinity.RefreshPending', 'false')
    if xbmc.getSkinDir() == 'skin.infinity.diggz':
        if _skin_string('Infinity.PerformanceMode') != mode:
            xbmc.executebuiltin('Skin.SetString(Infinity.PerformanceMode,' + mode + ')')
        if _skin_string('Infinity.RefreshCap') != cap:
            xbmc.executebuiltin('Skin.SetString(Infinity.RefreshCap,' + cap + ')')
    return mode, cap



def _skin_string(name: str, default: str = '') -> str:
    try:
        value = xbmc.getInfoLabel('Skin.String(' + name + ')')
        return value if value != '' else default
    except Exception:
        return default


def _first_prop(*names, default=''):
    for name in names:
        value = _prop(name, '')
        if value != '':
            return value
    return default


def _fmt_hz(value: str) -> str:
    try:
        hz = float(value)
        if hz <= 0:
            return '— Hz'
        return (str(int(round(hz))) if abs(hz - round(hz)) < 0.15 else ('%.1f' % hz)) + ' Hz'
    except Exception:
        return '— Hz'


def _effective_view_mode(layout: str, device: str, orientation: str, width_dp: str = '', height_dp: str = '', screen_w: str = '', screen_h: str = ''):
    visual = _skin_string('Infinity.VisualMode', '').strip().lower()
    selected = _skin_string('Infinity.HomeView', 'auto').strip().lower()
    # H3: explicit Normal is a stable local presentation. It is intentionally not
    # run through AUTO's device resolver; AUTO/follow-device remains adaptive.
    if visual == 'normal':
        return 'normal', 'explicit-normal-local'
    if visual in ('cinema', 'compact', 'twopane'):
        selected = visual
    elif visual in ('follow', 'adaptive'):
        selected = 'auto'
    return resolve_effective_view_mode(
        selected, layout, device, orientation, width_dp, height_dp, screen_w, screen_h
    )


def publish_runtime_capabilities():
    snap = refresh_runtime_state()
    runtime = snap.get('runtime', {})
    policy = snap.get('policy', {})

    # Refresh runtime proof. Owner settings remain published by publish_refresh_state().
    hook = runtime.get('hook_active', 'false').lower() == 'true'
    granted_raw = runtime.get('granted', '')
    granted = granted_raw.lower() == 'true' if granted_raw else False
    status = runtime.get('status') or ('awaiting-runtime' if not snap.get('runtime_file_present') else 'unknown')
    requested = runtime.get('requested_hz', '')
    active = runtime.get('active_hz', '')
    saver = runtime.get('battery_saver', 'false').lower() == 'true'
    thermal = runtime.get('thermal_limited', 'false').lower() == 'true'
    _set('Infinity.RefreshHookActive', 'true' if hook else 'false')
    _set('Infinity.RefreshRuntimePresent', 'true' if snap.get('runtime_file_present') else 'false')
    _set('Infinity.RefreshRuntimeMode', runtime.get('mode', policy.get('mode', '')))
    _set('Infinity.RefreshRequestedHz', requested)
    _set('Infinity.RefreshActiveHz', active)
    _set('Infinity.RefreshRequestedLabel', _fmt_hz(requested))
    _set('Infinity.RefreshActiveLabel', _fmt_hz(active))
    _set('Infinity.RefreshGranted', 'true' if granted else ('false' if granted_raw else 'unknown'))
    _set('Infinity.RefreshStatus', status)
    _set('Infinity.RefreshBatterySaver', 'true' if saver else 'false')
    _set('Infinity.RefreshThermalLimited', 'true' if thermal else 'false')
    _set('Infinity.RefreshRuntimeUpdatedMs', runtime.get('updated_ms', ''))
    if granted:
        refresh_summary = _fmt_hz(active) + ' ACTIVE'
    elif status == 'requested-not-active':
        refresh_summary = _fmt_hz(requested) + ' REQUESTED • ' + _fmt_hz(active) + ' ACTIVE'
    elif status in ('yield-to-kodi-video', 'video-system-control'):
        refresh_summary = 'VIDEO MATCH / KODI CONTROL'
    elif status == 'system-control':
        refresh_summary = 'SYSTEM CONTROL'
    elif not snap.get('runtime_file_present'):
        refresh_summary = 'RUNTIME PROOF PENDING'
    else:
        refresh_summary = status.replace('-', ' ').upper()
    _set('Infinity.RefreshSummary', refresh_summary)

    # Native responsive facts with compatibility fallbacks.
    device = _first_prop('Infinity.NativeDeviceMode', 'Infinity.DeviceMode', default='unknown').strip().lower()
    layout = _first_prop('Infinity.NativeLayout', 'Infinity.Layout', default='unknown').strip().lower()
    orientation = _first_prop('Infinity.NativeOrientation', 'Infinity.Orientation', default='unknown').strip().lower()
    width_dp = _first_prop('Infinity.NativeWidthDp', default='')
    height_dp = _first_prop('Infinity.NativeHeightDp', default='')
    fold_hint = _first_prop('Infinity.NativeFoldHint', default='false').strip().lower() == 'true'
    screen_w = _screen_label('System.ScreenWidth')
    screen_h = _screen_label('System.ScreenHeight')
    effective_view, view_reason = _effective_view_mode(layout, device, orientation, width_dp, height_dp, screen_w, screen_h)
    _set('Infinity.EffectiveDeviceMode', device)
    _set('Infinity.EffectiveLayout', layout)
    _set('Infinity.EffectiveOrientation', orientation)
    _set('Infinity.EffectiveWidthDp', width_dp)
    _set('Infinity.EffectiveHeightDp', height_dp)
    _set('Infinity.EffectiveViewMode', effective_view)
    _set('Infinity.EffectivePaneMode', 'two-pane' if effective_view == 'twopane' else 'single-pane')
    visual_mode = _skin_string('Infinity.VisualMode', '').strip().lower()
    requested_view = 'normal' if visual_mode == 'normal' else ('auto' if visual_mode in ('follow', 'adaptive') else (_skin_string('Infinity.HomeView', 'auto').strip().lower() or 'auto'))
    _set('Infinity.ViewMode.Requested', requested_view)
    _set('Infinity.ViewMode.Effective', effective_view)
    _set('Infinity.ViewMode.PolicyReason', view_reason)
    _set('Infinity.SafeAreaClass', 'fold-cover-safe' if device == 'cover/front' else ('fold-inner-safe' if fold_hint else 'standard'))
    _set('Infinity.RuntimeDisplayProfile', ' • '.join(x.upper() for x in (device, layout, orientation) if x and x != 'unknown') or 'UNKNOWN DISPLAY')

    # User motion preference + safety adaptation. This does not force display refresh.
    motion_user = setting_str('motion_mode', 'full').strip().lower()
    if motion_user not in ('full', 'reduced', 'off'):
        motion_user = 'full'
    if motion_user == 'off':
        motion_effective = 'off'
    elif motion_user == 'reduced' or saver or thermal or _prop('Infinity.StartupWatchdog.Status') == 'safe-mode':
        motion_effective = 'reduced'
    else:
        motion_effective = 'full'
    _set('Infinity.MotionModeUser', motion_user)
    _set('Infinity.MotionModeEffective', motion_effective)
    _set('Infinity.OptionalMotionAllowed', 'true' if motion_effective == 'full' else 'false')
    _set('Infinity.RuntimeBadgesVisible', 'true' if setting_bool('runtime_badges', True) else 'false')

    # Read-only baseline self-check. No automatic overwrite is performed here.
    integrity = _background_integrity()
    _set('Infinity.BaselineIntegrityStatus', integrity.get('status', 'unavailable'))
    _set('Infinity.BaselineCheckedFiles', integrity.get('checked', 0))
    mismatches = integrity.get('mismatches', [])
    _set('Infinity.BaselineMismatchCount', len(mismatches))
    _set('Infinity.BaselineMismatchFiles', ', '.join(mismatches[:8]))
    _set('Infinity.BaselineCandidate', integrity.get('candidate', ''))

    theme = _first_prop('Infinity.SystemTheme', 'Infinity.NativeSystemTheme', default='?').upper()
    view_label = effective_view.replace('twopane', 'two-pane').upper()
    perf = _prop('Infinity.RefreshUserMode', 'auto').upper()
    badge = 'VIEW ' + view_label + ' • PERF ' + perf + ' • ' + refresh_summary + ' • MOTION ' + motion_effective.upper() + ' • ' + theme
    _set('Infinity.RuntimeBadgeLine', badge)
    _set('Infinity.RuntimeCapabilitiesReady', 'true')
    return snap

def _compat_history():
    root = Path(xbmcvfs.translatePath('special://profile/addon_data/service.infinity.compat'))
    return read_json(root / 'startup-history.json', {})


def _addon_name(addon_id: str) -> str:
    try:
        return xbmcaddon.Addon(addon_id).getAddonInfo('name') or addon_id
    except Exception:
        return addon_id


def scan_guardian(profile: Path):
    if not setting_bool('guardian_enabled', True):
        _set('Infinity.Guardian.Status', 'disabled')
        return

    khc_bridge = Path(xbmcvfs.translatePath('special://profile/addon_data/script.kodihealthcenter/health-bridge.json'))
    health = read_json(khc_bridge, {})
    suspects = []
    source = 'infinity-fallback'
    unclean_count = 0
    if isinstance(health, dict) and health.get('correlated_changes') is not None:
        try:
            age = int(time.time()) - int(health.get('timestamp',0) or 0)
        except Exception:
            age = 999999
        changes = health.get('correlated_changes', [])
        if 0 <= age <= 900 and isinstance(changes, list):
            suspects = [item for item in changes if isinstance(item, dict)][:20]
            unclean_count = nonnegative_int(health.get('unclean_start_count', 0))
            source = 'kodi-health-center'

    if source == 'infinity-fallback':
        history = _compat_history()
        now = int(time.time())
        entries = history.get('unclean_starts', [])
        entries = entries if isinstance(entries, list) else []
        starts = [nonnegative_int(x, -1) for x in entries]
        starts = [x for x in starts if x >= 0 and 0 <= now - x <= 900]
        last_start = nonnegative_int(history.get('last_start'), now)
        unclean_count = len(starts)
        window = max(5, min(180, setting_int('suspect_window_minutes', 30))) * 60
        if unclean_count:
            addons_root = Path(xbmcvfs.translatePath('special://home/addons'))
            if addons_root.is_dir():
                for child in addons_root.iterdir():
                    if not child.is_dir() or child.name.startswith('repository.'):
                        continue
                    if child.name in (ADDON_ID, 'service.infinity.compat', 'script.kodihealthcenter'):
                        continue
                    try: modified = int(child.stat().st_mtime)
                    except OSError: continue
                    delta = last_start - modified
                    if 0 <= delta <= window:
                        suspects.append({'addon_id':child.name,'name':_addon_name(child.name),'modified':modified,
                                         'minutes_before_start':max(0,int(round(delta/60.0))), 'evidence':'addon-directory-mtime'})
        suspects.sort(key=lambda item:item.get('minutes_before_start',999999))

    state = {
        'schema':2, 'timestamp':int(time.time()), 'unclean_start_count':unclean_count,
        'suspects':suspects[:20], 'analysis_source':source,
        'evidence_note':'Recent change is correlation only, not proof of crash causation.'
    }
    atomic_json(profile / GUARDIAN_FILE, state)
    _set('Infinity.Guardian.Status', 'suspects' if suspects else 'clear')
    _set('Infinity.Guardian.AnalysisSource', source)
    _set('Infinity.Guardian.UncleanStarts', unclean_count)
    _set('Infinity.Guardian.SuspectCount', len(suspects))
    _set('Infinity.Guardian.Suspects', ','.join(item.get('addon_id','') for item in suspects[:10]))
    log('Guardian source=' + source + ' unclean=' + str(unclean_count) + ' suspects=' + str(len(suspects)))


def _active_video_player_id():
    result = jsonrpc('Player.GetActivePlayers')
    for item in result.get('result', []):
        if item.get('type') == 'video':
            return item.get('playerid')
    return None


def _player_props(player_id):
    result = jsonrpc('Player.GetProperties', {
        'playerid': player_id,
        'properties': ['audiostreams', 'currentaudiostream', 'subtitles', 'currentsubtitle', 'subtitleenabled', 'speed'],
    })
    return result.get('result', {}) if 'error' not in result else {}


def _stream_identity(stream):
    if not isinstance(stream, dict):
        return {}
    return {
        'index': stream.get('index'),
        'language': stream.get('language', ''),
        'name': stream.get('name', ''),
    }


def _best_stream_index(saved, available):
    if not isinstance(saved, dict) or not saved:
        return None
    available = [x for x in available if isinstance(x, dict)] if isinstance(available, list) else []
    language = str(saved.get('language') or '').lower()
    name = str(saved.get('name') or '').lower()
    for stream in available or []:
        if language and str(stream.get('language') or '').lower() == language and name and str(stream.get('name') or '').lower() == name:
            return stream.get('index')
    for stream in available or []:
        if language and str(stream.get('language') or '').lower() == language:
            return stream.get('index')
    wanted = saved.get('index')
    if isinstance(wanted, int) and any(stream.get('index') == wanted for stream in available or []):
        return wanted
    return None


def _load_playback(profile: Path):
    data = read_json(profile / PLAYBACK_FILE, {'schema': 1, 'titles': {}})
    titles = data.get('titles', {})
    data['titles'] = {k:v for k,v in titles.items() if isinstance(v, dict)} if isinstance(titles, dict) else {}
    return data


def _save_playback(profile: Path, data):
    data['schema'] = 1
    data['updated'] = int(time.time())
    titles = data.get('titles', {})
    if len(titles) > 500:
        ordered = sorted(titles.items(), key=lambda pair: nonnegative_int(pair[1].get('updated', 0)), reverse=True)[:500]
        data['titles'] = dict(ordered)
    atomic_json(profile / PLAYBACK_FILE, data)



def _continue_player_item(player_id):
    props = ['title', 'showtitle', 'season', 'episode', 'file', 'thumbnail', 'art', 'uniqueid']
    result = jsonrpc('Player.GetItem', {'playerid': player_id, 'properties': props})
    if 'error' in result:
        result = jsonrpc('Player.GetItem', {'playerid': player_id, 'properties': ['title', 'file', 'thumbnail']})
    item = result.get('result', {}).get('item', {}) if 'error' not in result else {}
    return item if isinstance(item, dict) else {}


def _continue_identity(item):
    item_type = str(item.get('type') or '').strip().lower()
    show = str(item.get('showtitle') or xbmc.getInfoLabel('VideoPlayer.TVShowTitle') or '').strip()
    title = str(item.get('title') or xbmc.getInfoLabel('VideoPlayer.Title') or '').strip()
    try:
        season = int(item.get('season')) if item.get('season') is not None else int(xbmc.getInfoLabel('VideoPlayer.Season') or -1)
    except Exception:
        season = -1
    try:
        episode = int(item.get('episode')) if item.get('episode') is not None else int(xbmc.getInfoLabel('VideoPlayer.Episode') or -1)
    except Exception:
        episode = -1
    unique = item.get('uniqueid') if isinstance(item.get('uniqueid'), dict) else {}
    tmdb = str(unique.get('tmdb') or xbmc.getInfoLabel('VideoPlayer.UniqueID(tmdb)') or '').strip()
    tvdb = str(unique.get('tvdb') or xbmc.getInfoLabel('VideoPlayer.UniqueID(tvdb)') or '').strip()
    imdb = str(unique.get('imdb') or xbmc.getInfoLabel('VideoPlayer.UniqueID(imdb)') or '').strip()
    source = str(item.get('file') or xbmc.getInfoLabel('Player.Filenameandpath') or '').strip()
    try:
        dbid = int(item.get('id')) if item.get('id') is not None else -1
    except Exception:
        dbid = -1

    is_episode = item_type == 'episode' or bool(show) or (season >= 0 and episode >= 0 and item_type != 'movie')
    if is_episode and (show or title):
        media = 'tv'
        show_label = show or title
        label = show_label
        if season >= 0 and episode >= 0:
            label = f'{show_label} • S{season:02d}E{episode:02d}'
        raw = 'tv|' + (tmdb or tvdb or imdb or show_label.lower()) + f'|{season}|{episode}'
    elif title:
        media = 'movie'
        label = title
        raw = 'movie|' + (tmdb or imdb or title.lower())
    else:
        return None

    import hashlib
    key = hashlib.sha256(raw.encode('utf-8', errors='replace')).hexdigest()
    art = item.get('art') if isinstance(item.get('art'), dict) else {}
    poster = str(art.get('poster') or item.get('thumbnail') or xbmc.getInfoLabel('VideoPlayer.Cover') or '')
    fanart = str(art.get('fanart') or xbmc.getInfoLabel('VideoPlayer.Fanart') or '')
    return {
        'key': key,
        'media': media,
        'label': label,
        'title': title,
        'showtitle': show,
        'season': season,
        'episode': episode,
        'tmdb': tmdb,
        'tvdb': tvdb,
        'imdb': imdb,
        'dbid': dbid,
        'source': source,
        'poster': poster,
        'fanart': fanart,
    }


def _load_continue(profile: Path):
    return hub.load(profile)


def _continue_counts(data):
    state = hub.counts(data)
    return state['continue_movies'], state['continue_tv']


def _publish_resume_hub(data):
    state = hub.counts(data)
    revision = data.get('revision', 0)
    _set('Infinity.ContinueWatchingRevision', revision)
    _set('Infinity.ResumeHubRevision', revision)
    _set('Infinity.ContinueWatchingMovies', state['continue_movies'])
    _set('Infinity.ContinueWatchingTV', state['continue_tv'])
    _set('Infinity.WatchedMovies', state['watched_movies'])
    _set('Infinity.WatchedTV', state['watched_tv'])
    _set('Infinity.WatchlistMovies', state['watchlist_movies'])
    _set('Infinity.WatchlistTV', state['watchlist_tv'])
    _set('Infinity.CollectionMovies', state['collection_movies'])
    _set('Infinity.CollectionTV', state['collection_tv'])


def _save_continue(profile: Path, data):
    return hub.save(profile, data, _publish_resume_hub)


def _publish_continue_state(profile: Path):
    _publish_resume_hub(_load_continue(profile))

def _widget_signature(sig):
    # Rebind dynamic widgets only for semantic display geometry changes. Native
    # revision counters may change while the same display is settling.
    return tuple(sig[index] for index in (2, 3, 4, 5, 6, 7, 8, 9, 10))


def _bump_widget_revision():
    _set('Infinity.WidgetReloadRevision', int(time.time() * 1000))


class InfinityPlayer(xbmc.Player):
    def __init__(self, profile: Path):
        super().__init__()
        self.profile = profile
        self.key = None
        self.readable = None
        self.last_props = None
        self.restore_pending = False
        self.cw_item = None
        self.cw_key = None
        self.cw_pending = False
        self.cw_last_save = 0.0
        self.experience = None

    def onAVStarted(self):
        self.cw_item = None
        self.cw_key = None
        if (setting_bool('continue_watching_enabled', True) or setting_bool('source_memory_enabled', True)
                or setting_str('playback_recovery', 'prompt') != 'off'):
            self.cw_pending = True
            self._arm_continue()
        if self.experience:
            self.experience.on_started()
        if not setting_bool('playback_memory_enabled', True):
            return
        self.key, self.readable = semantic_playback_key()
        self.restore_pending = True
        _set('Infinity.PlaybackMemory.TitleKey', self.readable)
        log('Playback memory armed for ' + self.readable)

    def onPlayBackStopped(self):
        self.persist_continue(completed=False, force=True)
        self.persist()

    def onPlayBackEnded(self):
        self.persist_continue(completed=True, force=True)
        self.persist()

    def onPlayBackError(self):
        if self.experience and setting_str('playback_recovery', 'prompt') != 'off':
            self.experience.on_error()
        self.persist_continue(completed=False, force=True)
        self.persist()

    def poll(self):
        if self.isPlayingVideo() and setting_bool('continue_watching_enabled', True):
            if self.cw_pending or not self.cw_item:
                self._arm_continue()
            self.persist_continue(completed=False, force=False)
        if not setting_bool('playback_memory_enabled', True) or not self.isPlayingVideo():
            return
        if not self.key:
            self.key, self.readable = semantic_playback_key()
        player_id = _active_video_player_id()
        if player_id is None:
            return
        props = _player_props(player_id)
        if props:
            self.last_props = props
        if self.restore_pending and props:
            self.restore_pending = False
            self.restore(player_id, props)

    def _arm_continue(self):
        player_id = _active_video_player_id()
        if player_id is None:
            return
        item = _continue_identity(_continue_player_item(player_id))
        if not item:
            return
        self.cw_item = item
        self.cw_key = item.get('key')
        self.cw_pending = False
        self.cw_last_save = 0.0
        log('Continue Watching armed for ' + item.get('label', 'video'))

    @_serialized_progress
    def persist_continue(self, completed=False, force=False):
        if not setting_bool('continue_watching_enabled', True):
            return
        if not self.cw_item or not self.cw_key:
            if completed:
                self.cw_pending = False
            return
        data = _load_continue(self.profile)
        items = data.setdefault('items', {})

        if completed:
            data, watched_entry = hub.mark_watched_data(data, self.cw_key, self.cw_item, completed=True)
            if watched_entry:
                _save_continue(self.profile, data)
                hub.sync_kodi_playcount(watched_entry, True)
            self.cw_item = None
            self.cw_key = None
            self.cw_pending = False
            return

        now = time.monotonic()
        if not force and now - self.cw_last_save < 8.0:
            return

        try:
            position = max(0.0, float(self.getTime()))
            duration = max(0.0, float(self.getTotalTime()))
        except Exception:
            position = 0.0
            duration = 0.0

        # onPlayBackStopped may fire after Kodi has already released the clock.
        # Periodic writes during playback are authoritative in that case.
        if duration <= 0.0:
            if force:
                self.cw_item = None
                self.cw_key = None
                self.cw_pending = False
            return

        percent = (position / duration) * 100.0 if duration else 0.0
        changed = False
        if percent >= 95.0:
            completed_entry = dict(self.cw_item)
            completed_entry.update({
                'position': round(position, 3),
                'duration': round(duration, 3),
                'percentage': 100.0,
                'updated': int(time.time()),
            })
            data, watched_entry = hub.mark_watched_data(data, self.cw_key, completed_entry, completed=True)
            items = data.setdefault('items', {})
            changed = watched_entry is not None
            if watched_entry:
                hub.sync_kodi_playcount(watched_entry, True)
        elif position >= 30.0 and duration >= 120.0 and percent >= 1.0:
            entry = dict(self.cw_item)
            entry.update({
                'position': round(position, 3),
                'duration': round(duration, 3),
                'percentage': round(percent, 2),
                'updated': int(time.time()),
            })
            prior = items.get(self.cw_key, {}) if isinstance(items.get(self.cw_key), dict) else {}
            if force or abs(float(prior.get('position', 0.0) or 0.0) - position) >= 5.0:
                items[self.cw_key] = entry
                changed = True

        self.cw_last_save = now
        if changed:
            _save_continue(self.profile, data)
        if force:
            self.cw_item = None
            self.cw_key = None
            self.cw_pending = False

    def restore(self, player_id, props):
        data = _load_playback(self.profile)
        saved = data.get('titles', {}).get(self.key)
        if not saved:
            return
        audio_index = _best_stream_index(saved.get('audio'), props.get('audiostreams'))
        if audio_index is not None:
            jsonrpc('Player.SetAudioStream', {'playerid': player_id, 'stream': audio_index})

        if not saved.get('subtitle_enabled', False):
            jsonrpc('Player.SetSubtitle', {'playerid': player_id, 'subtitle': 'off', 'enable': False})
        else:
            subtitle_index = _best_stream_index(saved.get('subtitle'), props.get('subtitles'))
            if subtitle_index is not None:
                jsonrpc('Player.SetSubtitle', {'playerid': player_id, 'subtitle': subtitle_index, 'enable': True})
        _set('Infinity.PlaybackMemory.Restored', self.readable or '')
        log('Restored audio/subtitle memory for ' + (self.readable or self.key))

    def persist(self):
        if not self.key or not self.last_props:
            self.key = None
            self.readable = None
            self.last_props = None
            return
        props = self.last_props
        data = _load_playback(self.profile)
        titles = data.setdefault('titles', {})
        titles[self.key] = {
            'readable': self.readable,
            'audio': _stream_identity(props.get('currentaudiostream')),
            'subtitle': _stream_identity(props.get('currentsubtitle')),
            'subtitle_enabled': bool(props.get('subtitleenabled', False)),
            'speed': props.get('speed', 1),
            'updated': int(time.time()),
        }
        _save_playback(self.profile, data)
        _set('Infinity.PlaybackMemory.LastSaved', self.readable or '')
        log('Saved audio/subtitle memory for ' + (self.readable or self.key))
        self.key = None
        self.readable = None
        self.last_props = None



BOOT_MARKER = 'boot-marker.json'
BOOT_HISTORY = 'boot-history.json'


def _prop(name, default=''):
    try:
        value = HOME.getProperty(name)
        return value if value != '' else default
    except Exception:
        return default


def _bool_prop(name):
    return _prop(name, '').strip().lower() == 'true'


NORMAL_RETURN_LATCH = 'Infinity.ViewMode.NormalReturnLatch'
NORMAL_RETURN_REASON = 'Infinity.ViewMode.NormalReturnReason'


def _norm_token(value: str) -> str:
    return (value or '').strip().lower().replace('_', '-').replace(' ', '-')


def _canon_device(value: str) -> str:
    value = _norm_token(value)
    if value in {'cover/front','front/cover','cover','front','cover-front','front-cover','fold-cover','outer','outer-screen','phone','handset'}:
        return 'cover'
    if value in {'inner','fold-inner','expanded','large','tablet'}:
        return 'inner'
    if value in {'tv','television','android-tv'}:
        return 'tv'
    return value


def _canon_layout(value: str) -> str:
    value = _norm_token(value)
    if value in {'compact','narrow','cover','front','phone','handset'}:
        return 'compact'
    if value in {'expanded','inner','large','tablet','wide','fold-inner'}:
        return 'expanded'
    return value


def _canon_orientation(value: str) -> str:
    value = _norm_token(value)
    if value.startswith('land'):
        return 'landscape'
    if value.startswith('port'):
        return 'portrait'
    if value == 'square':
        return 'square'
    return value


def _num_or_none(value):
    try:
        number = float(str(value).strip())
        return number if number > 0 else None
    except Exception:
        return None


def _normal_return_current_state():
    return {
        'device': _canon_device(_first_prop('Infinity.NativeDeviceMode', 'Infinity.DeviceMode', default='')),
        'layout': _canon_layout(_first_prop('Infinity.NativeLayout', 'Infinity.Layout', default='')),
        'orientation': _canon_orientation(_first_prop('Infinity.NativeOrientation', 'Infinity.Orientation', default='')),
        'width_dp': _first_prop('Infinity.NativeWidthDp', default='').strip(),
        'height_dp': _first_prop('Infinity.NativeHeightDp', default='').strip(),
        'screen_w': _screen_label('System.ScreenWidth').strip(),
        'screen_h': _screen_label('System.ScreenHeight').strip(),
    }


def _capture_normal_return_baseline(reason: str):
    state = _normal_return_current_state()
    _set(NORMAL_RETURN_LATCH, 'true')
    _set(NORMAL_RETURN_REASON, reason)
    _set('Infinity.ViewMode.NormalReturnBaselineDevice', state['device'])
    _set('Infinity.ViewMode.NormalReturnBaselineLayout', state['layout'])
    _set('Infinity.ViewMode.NormalReturnBaselineOrientation', state['orientation'])
    _set('Infinity.ViewMode.NormalReturnBaselineWidthDp', state['width_dp'])
    _set('Infinity.ViewMode.NormalReturnBaselineHeightDp', state['height_dp'])
    _set('Infinity.ViewMode.NormalReturnBaselineScreenWidth', state['screen_w'])
    _set('Infinity.ViewMode.NormalReturnBaselineScreenHeight', state['screen_h'])
    _set('Infinity.ViewMode.NormalReturnBaselineCaptured', 'true')


def _release_normal_return(reason: str):
    _set(NORMAL_RETURN_LATCH, 'false')
    _set(NORMAL_RETURN_REASON, reason)
    _set('Infinity.ViewMode.NormalReturnBaselineCaptured', 'false')


def _normal_return_semantic_display_changed() -> bool:
    """True only for a meaningful display/posture change.

    Do not use native revision counters or screen-mode strings here: they can change
    while the same physical display state is settling and were the source of the
    premature 0.3.5.7 latch release.
    """
    current = _normal_return_current_state()
    base = {
        'device': _prop('Infinity.ViewMode.NormalReturnBaselineDevice', ''),
        'layout': _prop('Infinity.ViewMode.NormalReturnBaselineLayout', ''),
        'orientation': _prop('Infinity.ViewMode.NormalReturnBaselineOrientation', ''),
        'width_dp': _prop('Infinity.ViewMode.NormalReturnBaselineWidthDp', ''),
        'height_dp': _prop('Infinity.ViewMode.NormalReturnBaselineHeightDp', ''),
        'screen_w': _prop('Infinity.ViewMode.NormalReturnBaselineScreenWidth', ''),
        'screen_h': _prop('Infinity.ViewMode.NormalReturnBaselineScreenHeight', ''),
    }
    for key in ('device', 'layout', 'orientation'):
        if base[key] and current[key] and base[key] != current[key]:
            return True

    # Large dimension changes are posture/window changes; ignore small settling noise.
    for a, b in (('width_dp', 'width_dp'), ('height_dp', 'height_dp')):
        old = _num_or_none(base[a]); new = _num_or_none(current[b])
        if old is not None and new is not None and abs(old - new) >= 160:
            return True

    # Kodi screen dimensions are a fallback only when native dp facts are unavailable.
    if not (_num_or_none(base['width_dp']) and _num_or_none(base['height_dp'])):
        for key in ('screen_w', 'screen_h'):
            old = _num_or_none(base[key]); new = _num_or_none(current[key])
            if old is not None and new is not None and abs(old - new) >= 160:
                return True
    return False


class NormalReturnController:
    """H3 compatibility cleaner for obsolete H1/H2 Normal latches.

    Explicit Normal is represented by Skin.String(Infinity.VisualMode)=normal and
    EffectiveViewMode=normal. No background manual->auto latch is needed.
    """
    def __init__(self):
        if _bool_prop(NORMAL_RETURN_LATCH):
            _release_normal_return('superseded-by-h3-explicit-normal-state')

    def tick(self):
        if _bool_prop(NORMAL_RETURN_LATCH):
            _release_normal_return('superseded-by-h3-explicit-normal-state')


class StabilityController:
    """Upper-layer startup staging, UI protection and 120 Hz-aware widget pacing.

    This does not select a display refresh rate itself. Infinity Refresh owns that policy.
    We consume its published Motion/Refresh/Power contract and pace optional UI work so
    high-refresh animation is not starved by add-on/widget startup bursts.
    """

    def __init__(self, profile: Path):
        self.profile = profile
        self.started = time.monotonic()
        self.stage = 'core'
        self.ready_marked = False
        self.primary_ready = False
        self.secondary_ready = False
        self.primary_timeout = False
        self.secondary_timeout = False
        self._last_policy = None
        self._register_start()
        self._publish_base()
        self._check_ui()

    def _history_path(self):
        return self.profile / BOOT_HISTORY

    def _marker_path(self):
        return self.profile / BOOT_MARKER

    def _register_start(self):
        now = int(time.time())
        prior = read_json(self._marker_path(), {})
        history = read_json(self._history_path(), {
            'schema': 1, 'incomplete_starts': 0, 'total_starts': 0,
            'auto_safe_activations': 0,
        })
        incomplete = nonnegative_int(history.get('incomplete_starts', 0))
        try:
            prior_age = now - int(prior.get('timestamp', 0) or 0)
        except Exception:
            prior_age = 999999
        if prior and 0 <= prior_age <= 24 * 60 * 60 and prior.get('stage') not in ('ready', 'clean-stop'):
            incomplete += 1
            history['last_incomplete_stage'] = prior.get('stage', 'unknown')
            history['last_incomplete_timestamp'] = int(prior.get('timestamp', 0) or 0)
        history['incomplete_starts'] = incomplete
        history['total_starts'] = nonnegative_int(history.get('total_starts', 0)) + 1
        history['last_start'] = now
        atomic_json(self._history_path(), history)
        atomic_json(self._marker_path(), {'schema': 1, 'timestamp': now, 'stage': 'core'})
        _set('Infinity.StartupWatchdog.IncompleteStarts', incomplete)
        if incomplete >= 2:
            _set('Infinity.StartupWatchdog.Status', 'warning')
        else:
            _set('Infinity.StartupWatchdog.Status', 'clear')
        if incomplete >= 3 and setting_bool('watchdog_safe_mode', True):
            current = read_json(self._history_path(), {})
            if not current.get('safe_mode_for_this_streak'):
                if addon_set_setting('service.infinity.compat', 'compat_mode', 'safe'):
                    current['safe_mode_for_this_streak'] = True
                    current['auto_safe_activations'] = nonnegative_int(current.get('auto_safe_activations', 0)) + 1
                    atomic_json(self._history_path(), current)
                    _set('Infinity.StartupWatchdog.Status', 'safe-mode')
                    log('Startup watchdog requested Infinity Safe Mode after repeated incomplete starts', xbmc.LOGWARNING)

    def _check_ui(self):
        state = ui_health()
        _set('Infinity.UIHealth.Status', 'healthy' if state.get('healthy') else 'problem')
        _set('Infinity.UIHealth.IssueCount', len(state.get('issues', [])))
        _set('Infinity.UIHealth.SkinVersion', state.get('skin_version', ''))
        _set('Infinity.UIHealth.ContractSchema', state.get('contract_schema', 0))
        if state.get('healthy'):
            _set('Infinity.UIHealth.PendingReason', '')
            try:
                backup_ui_if_healthy(force=False)
            except Exception:
                pass
            return
        if not setting_bool('auto_ui_self_heal', True):
            return
        # Never rewrite active player UI while Kodi is decoding/playing media.
        if xbmc.getCondVisibility('Player.HasMedia'):
            _set('Infinity.UIHealth.Status', 'deferred')
            _set('Infinity.UIHealth.PendingReason', 'active-playback')
            log('Automatic UI Self-Heal deferred during active playback', xbmc.LOGWARNING)
            return
        ok, message = self_heal_ui()
        if ok:
            _set('Infinity.UIHealth.Status', 'restored')
            _set('Infinity.UIHealth.PendingReload', 'true')
            _set('Infinity.UIHealth.PendingReason', 'same-version-selective-restore')
            log('Automatic UI Self-Heal selectively restored critical files: ' + message, xbmc.LOGWARNING)
            try:
                xbmcgui.Dialog().notification('Infinity', 'UI Self-Heal restored a same-version UI file', COMMAND_ICON, 4500)
            except Exception:
                pass
        else:
            _set('Infinity.UIHealth.Status', 'unresolved')
            _set('Infinity.UIHealth.PendingReason', 'stale-or-missing-backup')
            log('Automatic UI Self-Heal safely refused recovery: ' + message, xbmc.LOGERROR)

    def _policy(self):
        motion = _prop('Infinity.MotionModeEffective', 'full').strip().lower()
        granted = _prop('Infinity.RefreshGranted', 'unknown').strip().lower()
        try:
            active_hz = float(_prop('Infinity.RefreshActiveHz', '0') or 0)
        except Exception:
            active_hz = 0.0
        if motion == 'off':
            return 'still', 50.0, (1.2, 3.5, 9.0, 14.0, 26.0, 42.0)
        if motion == 'reduced' or _prop('Infinity.StartupWatchdog.Status') == 'safe-mode':
            return 'grace', 33.33, (1.0, 3.0, 8.0, 12.0, 22.0, 36.0)
        if granted == 'true' and active_hz >= 100.0:
            return 'performance', 8.33, (0.35, 0.9, 2.2, 5.0, 12.0, 22.0)
        return 'balanced', 16.67, (0.65, 1.6, 4.5, 8.0, 16.0, 28.0)

    def _publish_base(self):
        _set('Infinity.CommandCenter.Ready', 'true')
        _set('Infinity.CommandCenter.Version', COMMAND_ADDON.getAddonInfo('version') or '0.3.5.14')
        _set('Infinity.StabilityAPI', '0.4')
        _set('Infinity.BootStage', 'core')
        _set('Infinity.WidgetPrimaryReady', 'false')
        _set('Infinity.WidgetSecondaryReady', 'false')
        _set('Infinity.WidgetPrimaryTimeout', 'false')
        _set('Infinity.WidgetSecondaryTimeout', 'false')

    def _set_stage(self, stage):
        if self.stage == stage:
            return
        self.stage = stage
        _set('Infinity.BootStage', stage)
        marker = read_json(self._marker_path(), {})
        marker.update({'schema': 1, 'timestamp': int(time.time()), 'stage': stage})
        atomic_json(self._marker_path(), marker)
        log('Startup stage -> ' + stage)

    def tick(self):
        elapsed = time.monotonic() - self.started
        policy, frame_budget, times = self._policy()
        shell_t, primary_t, secondary_t, ready_t, primary_timeout_t, secondary_timeout_t = times
        if self._last_policy != policy:
            self._last_policy = policy
            _set('Infinity.WidgetLoadPolicy', policy)
            _set('Infinity.UIFrameBudgetMs', frame_budget)
            _set('Infinity.HighRefreshUI', 'true' if policy == 'performance' else 'false')
            _set('Infinity.StabilityMode', 'grace' if policy == 'grace' else 'normal')
            log('Widget scheduler policy=' + policy + ' frame_budget_ms=' + str(frame_budget))

        if elapsed >= shell_t and self.stage == 'core':
            self._set_stage('shell')
        if elapsed >= primary_t and not self.primary_ready:
            self.primary_ready = True
            _set('Infinity.WidgetPrimaryReady', 'true')
            self._set_stage('primary')
        if elapsed >= secondary_t and not self.secondary_ready:
            self.secondary_ready = True
            _set('Infinity.WidgetSecondaryReady', 'true')
            self._set_stage('secondary')
        if elapsed >= ready_t and not self.ready_marked:
            self.ready_marked = True
            self._set_stage('ready')
            history = read_json(self._history_path(), {})
            history['incomplete_starts'] = 0
            history['safe_mode_for_this_streak'] = False
            history['last_ready'] = int(time.time())
            atomic_json(self._history_path(), history)
            _set('Infinity.StartupWatchdog.Status', 'clear')
        if elapsed >= primary_timeout_t and not self.primary_timeout:
            self.primary_timeout = True
            _set('Infinity.WidgetPrimaryTimeout', 'true')
        if elapsed >= secondary_timeout_t and not self.secondary_timeout:
            self.secondary_timeout = True
            _set('Infinity.WidgetSecondaryTimeout', 'true')

    def clean_stop(self):
        history = read_json(self._history_path(), {})
        history['last_clean_stop'] = int(time.time())
        atomic_json(self._history_path(), history)
        try:
            self._marker_path().unlink()
        except FileNotFoundError:
            pass
        _set('Infinity.BootStage', 'stopped')



# ---------------------------------------------------------------------------
# Infinity live responsive reflow
# ---------------------------------------------------------------------------
DISPLAY_REFLOW_DEBOUNCE_SEC = 0.55
DISPLAY_REFLOW_COOLDOWN_SEC = 1.50


def _screen_label(name: str) -> str:
    try:
        return str(xbmc.getInfoLabel(name) or '').strip()
    except Exception:
        return ''


def _display_signature():
    native_ready = _prop('Infinity.NativeReady', '').strip().lower()
    revision = _prop('Infinity.NativeDisplayRevision', '').strip()
    device = _first_prop('Infinity.NativeDeviceMode', 'Infinity.DeviceMode', default='').strip().lower()
    layout = _first_prop('Infinity.NativeLayout', 'Infinity.Layout', default='').strip().lower()
    orientation = _first_prop('Infinity.NativeOrientation', 'Infinity.Orientation', default='').strip().lower()
    width_dp = _first_prop('Infinity.NativeWidthDp', default='').strip()
    height_dp = _first_prop('Infinity.NativeHeightDp', default='').strip()
    multi = _first_prop('Infinity.NativeMultiWindow', default='').strip().lower()
    pip = _first_prop('Infinity.NativePiP', default='').strip().lower()
    screen_w = _screen_label('System.ScreenWidth')
    screen_h = _screen_label('System.ScreenHeight')
    screen_mode = _screen_label('System.ScreenMode')
    return (
        native_ready, revision, device, layout, orientation,
        width_dp, height_dp, multi, pip, screen_w, screen_h, screen_mode
    )


def _display_signature_valid(sig) -> bool:
    return any(str(value).strip() for value in sig[1:])


def _display_signature_text(sig) -> str:
    keys = (
        'native', 'rev', 'device', 'layout', 'orientation',
        'wdp', 'hdp', 'multi', 'pip', 'sw', 'sh', 'mode'
    )
    return ';'.join(k + '=' + str(v) for k, v in zip(keys, sig))


class DisplayReflowController:
    def __init__(self):
        self.stable = None
        self.pending = None
        self.pending_since = 0.0
        self.last_apply = 0.0
        self.apply_count = 0
        self.preserved_view = ''
        self.widget_signature = None
        _set('Infinity.ResponsiveReflow.Enabled', 'true')
        _set('Infinity.ResponsiveReflow.Pending', 'false')
        _set('Infinity.ResponsiveReflow.State', 'initializing')

    def _publish_signature(self, prefix: str, sig):
        _set(prefix + '.Signature', _display_signature_text(sig))
        _set(prefix + '.Revision', sig[1])
        _set(prefix + '.DeviceMode', sig[2])
        _set(prefix + '.Layout', sig[3])
        _set(prefix + '.Orientation', sig[4])
        _set(prefix + '.WidthDp', sig[5])
        _set(prefix + '.HeightDp', sig[6])
        _set(prefix + '.ScreenWidth', sig[9])
        _set(prefix + '.ScreenHeight', sig[10])

    def _capture_view_mode(self):
        mode = _skin_string('Infinity.HomeView', 'auto').strip().lower()
        if mode not in ('auto', 'cinema', 'compact', 'twopane'):
            mode = 'auto'
        self.preserved_view = mode
        _set('Infinity.ResponsiveReflow.PreservedViewMode', mode)

    def _restore_view_mode_if_needed(self):
        if not self.preserved_view:
            return
        current = _skin_string('Infinity.HomeView', '').strip().lower()
        if current == '':
            xbmc.executebuiltin('Skin.SetString(Infinity.HomeView,' + self.preserved_view + ')')

    def _apply(self, now: float, sig):
        # NormalReturnController owns Normal-latch release. Reflow signatures include
        # revision/screen-mode noise and must not cancel an explicit Normal request.
        publish_runtime_capabilities()
        self._capture_view_mode()

        old = self.stable
        self.stable = sig
        self.pending = None
        self.pending_since = 0.0
        self.last_apply = now
        self.apply_count += 1

        _set('Infinity.ResponsiveReflow.Pending', 'false')
        _set('Infinity.ResponsiveReflow.State', 'applying')
        _set('Infinity.ResponsiveReflow.Count', self.apply_count)
        _set('Infinity.ResponsiveReflow.LastAppliedMs', int(time.time() * 1000))
        self._publish_signature('Infinity.ResponsiveReflow.Previous', old or tuple('' for _ in sig))
        self._publish_signature('Infinity.ResponsiveReflow.Current', sig)

        try:
            if xbmc.getCondVisibility('Window.IsActive(1198)'):
                xbmc.executebuiltin('Dialog.Close(1198)')
        except Exception:
            pass

        if xbmc.getSkinDir() == 'skin.infinity.diggz':
            log('Live responsive reflow: ' + _display_signature_text(sig))
            self.widget_signature = _widget_signature(sig)
            _bump_widget_revision()
            xbmc.executebuiltin('ReloadSkin()')
            _set('Infinity.ResponsiveReflow.State', 'reloaded')
        else:
            _set('Infinity.ResponsiveReflow.State', 'observed-non-infinity-skin')

    def tick(self, now: float):
        # Native/app ownership takes precedence. Infinity 1.0.9+ publishes
        # app-v1 from libkodi.so. When present, Command Center is observer-only
        # and must never schedule its Python ReloadSkin fallback.
        native_owner = _prop('Infinity.NativeReflowOwner', '').strip().lower()
        if native_owner.startswith('app-'):
            sig = _display_signature()
            if _display_signature_valid(sig):
                # Observer-only native signatures may change revision fields without a
                # physical posture change. Rebind widgets only when semantic geometry changes.
                semantic = _widget_signature(sig)
                if self.widget_signature is None:
                    self.widget_signature = semantic
                elif semantic != self.widget_signature:
                    self.widget_signature = semantic
                    _bump_widget_revision()
                self.stable = sig
                self.pending = None
                self.pending_since = 0.0
                self._publish_signature('Infinity.ResponsiveReflow.Current', sig)
            _set('Infinity.ResponsiveReflow.Enabled', 'false')
            _set('Infinity.ResponsiveReflow.Pending', 'false')
            _set('Infinity.ResponsiveReflow.State', 'native-owned')
            _set('Infinity.ResponsiveReflow.NativeOwner', native_owner)
            return

        # Older APK fallback: retain the already device-accepted 0.3.5.3
        # watcher/reload behavior below this ownership gate.
        _set('Infinity.ResponsiveReflow.Enabled', 'true')
        _set('Infinity.ResponsiveReflow.NativeOwner', '')
        self._restore_view_mode_if_needed()
        sig = _display_signature()
        if not _display_signature_valid(sig):
            return

        if self.stable is None:
            self.stable = sig
            self.widget_signature = _widget_signature(sig)
            self._publish_signature('Infinity.ResponsiveReflow.Current', sig)
            _set('Infinity.ResponsiveReflow.State', 'ready')
            return

        if sig == self.stable:
            if self.pending is not None:
                self.pending = None
                self.pending_since = 0.0
                _set('Infinity.ResponsiveReflow.Pending', 'false')
                _set('Infinity.ResponsiveReflow.State', 'ready')
            return

        if self.pending != sig:
            self.pending = sig
            self.pending_since = now
            _set('Infinity.ResponsiveReflow.Pending', 'true')
            _set('Infinity.ResponsiveReflow.State', 'settling')
            self._publish_signature('Infinity.ResponsiveReflow.PendingState', sig)
            return

        if now - self.pending_since < DISPLAY_REFLOW_DEBOUNCE_SEC:
            return
        if now - self.last_apply < DISPLAY_REFLOW_COOLDOWN_SEC:
            return

        self._apply(now, sig)

def main():
    profile = addon_profile()
    profile.mkdir(parents=True, exist_ok=True)
    skin_upgrade_status = skin_upgrade.apply_and_reload()
    _set('Infinity.ResumeHubSkinUpgrade', skin_upgrade_status)
    scan_guardian(profile)
    publish_refresh_state()
    publish_runtime_capabilities()
    _publish_continue_state(profile)
    if _prop('Infinity.WidgetReloadRevision', '') == '':
        _bump_widget_revision()
    stability = StabilityController(profile)
    player = InfinityPlayer(profile)
    experience = ExperienceController(profile, player, {
        'xbmc': xbmc, 'gui': xbmcgui, 'set': _set, 'read': read_json,
        'atomic': atomic_json, 'bool': setting_bool, 'str': setting_str,
        'rpc': jsonrpc, 'load_continue': _load_continue, 'save_continue': _save_continue,
        'progress_lock': PROGRESS_LOCK,
    })
    player.experience = experience
    normal_return = NormalReturnController()
    display_reflow = DisplayReflowController()
    monitor = xbmc.Monitor()
    last_guardian = time.monotonic()
    last_ui_check = time.monotonic()
    last_refresh_state = time.monotonic()
    while not monitor.abortRequested():
        player.poll()
        stability.tick()
        now = time.monotonic()
        try:
            experience.tick(now)
        except Exception as error:
            log('Experience observer deferred: ' + type(error).__name__)
        normal_return.tick()
        display_reflow.tick(now)
        if now - last_refresh_state >= 1.0:
            publish_refresh_state()
            publish_runtime_capabilities()
            last_refresh_state = now
        if now - last_guardian >= 300:
            scan_guardian(profile)
            last_guardian = now
        if now - last_ui_check >= 600:
            try:
                state = ui_health()
                _set('Infinity.UIHealth.Status', 'healthy' if state.get('healthy') else 'problem')
                _set('Infinity.UIHealth.IssueCount', len(state.get('issues', [])))
                _set('Infinity.UIHealth.SkinVersion', state.get('skin_version', ''))
                _set('Infinity.UIHealth.ContractSchema', state.get('contract_schema', 0))
                if state.get('healthy'):
                    backup_ui_if_healthy(force=False)
            except Exception:
                pass
            last_ui_check = now
        if monitor.waitForAbort(0.5):
            break
    player.persist_continue(force=True)
    player.persist()
    experience.shutdown()
    stability.clean_stop()


if __name__ == '__main__':
    main()
