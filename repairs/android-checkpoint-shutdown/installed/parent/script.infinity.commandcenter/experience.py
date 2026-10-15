# SPDX-License-Identifier: GPL-2.0-or-later
"""Shared Infinity experience policy. One observer, one existing progress store.

Artwork preloading warms Kodi's texture cache only; it never opens a player or
asks a provider for streams. Provider routes are remembered only after AV starts.
"""
from __future__ import annotations
import re
import time
from contextlib import nullcontext
from urllib.parse import urlsplit

COMMANDS = (
    ('resume-hub', 'Resume Hub', 'Continue, watched history, Watchlist, Collection and local lists'),
    ('restore-session', 'Restore session', 'Return to your last browsing position'),
    ('retry-playback', 'Recover playback', 'Retry the failed source at your saved position'),
    ('forget-source', 'Forget source preference', 'Use the normal resolver for this title'),
    ('ambient-home', 'Ambient Home', 'Off, Subtle or Immersive artwork atmosphere'),
    ('health-center', 'Health Center', 'Open existing diagnostics and recovery'),
    ('runtime', 'Runtime inspector', 'Display, motion, power and stability'),
    ('view-normal', 'View: Normal', 'Preserve the original Normal presentation'),
    ('view-auto', 'View: Adaptive', 'Follow the active display'),
    ('view-cinema', 'View: Cinema', 'Cinema Home presentation'),
    ('view-compact', 'View: Compact', 'Compact Home presentation'),
    ('view-twopane', 'View: Two Pane', 'Two Pane Home presentation'),
    ('settings', 'Experience settings', 'Motion, artwork, recovery and resume preferences'),
    ('support-exporter', 'Export diagnostics', 'Use the existing support exporter'),
    ('create-restore', 'Create restore point', 'Snapshot the existing setup'),
    ('restore-menu', 'Restore point', 'Choose a saved setup'),
    ('mark-good', 'Mark known good', 'Save the working setup'),
    ('restore-good', 'Restore known good', 'Use the existing recovery system'),
    ('performance', 'Performance mode', 'Use existing performance controls'),
    ('adaptive-refresh', 'Adaptive refresh', 'Use existing refresh ownership'),
    ('crash-recovery', 'Crash recovery', 'Review existing guardian suggestions'),
)


def commands(query=''):
    terms = str(query).casefold().split()
    return [row for row in COMMANDS if all(t in ' '.join(row).casefold() for t in terms)]


def stable_route(route):
    """Expiring HTTP streams, PVR and opaque builtins are never source memory."""
    if not isinstance(route, str) or not route or any(c in route for c in '\r\n\x00'):
        return ''
    try:
        parsed = urlsplit(route)
    except ValueError:
        return ''
    if parsed.scheme == 'plugin' and re.fullmatch(r'[\w.-]+', parsed.netloc or ''):
        return route
    if parsed.scheme in ('file', 'smb', 'nfs', 'special'):
        return route
    if route.startswith('/'):
        return route
    return ''


def browsing_route(route):
    if not isinstance(route, str) or any(c in route for c in '\r\n\x00"'):
        return ''
    try:
        return stable_route(route) or (route if urlsplit(route).scheme in ('videodb', 'musicdb', 'sources', 'library') else '')
    except ValueError:
        return ''


def number(value, default=0.0):
    try:
        n = float(value)
        return n if n >= 0 and n < 1e12 else default
    except (ValueError, TypeError, OverflowError):
        return default


def artwork_tier(free_mb, width, playing=False, constrained=False):
    # Unknown RAM is conservative, never treated as a measurement of abundance.
    if playing or constrained or 0 < number(free_mb) < 650:
        return 'safe'
    if number(free_mb) >= 1800 and number(width) >= 1600:
        return 'high'
    return 'standard'


def memory_mb(value):
    match = re.match(r'^\s*([\d.]+)\s*(GB|MB|KB)?', str(value), re.I)
    if not match:
        return 0.0
    unit = (match[2] or 'MB').upper()
    return number(match[1]) * {'GB': 1024, 'MB': 1, 'KB': 1 / 1024}[unit]


def artwork(url, tier='standard', fanart=False):
    if not isinstance(url, str):
        return ''
    # Only TMDb's documented size routes. Tokens, Kodi image:// wrappers, local
    # paths, provider headers and unrelated artwork servers pass through intact.
    size = {'safe': ('w342', 'w780'), 'standard': ('w500', 'w1280'),
            'high': ('w780', 'w1280')}.get(tier, ('w500', 'w1280'))[bool(fanart)]
    return re.sub(r'^(https://image\.tmdb\.org/t/p/)(?:original|w\d+)(/[^?|]+)$',
                  lambda m: m[1] + size + m[2], url)


def health(ui, guardian, watchdog):
    if ui in ('problem', 'unresolved') or watchdog == 'safe-mode':
        return 'attention', 'FFFF665F', 'Health needs attention'
    if guardian == 'suspects' or watchdog == 'warning' or ui in ('deferred', 'restored'):
        return 'review', 'FFFFBF60', 'Health review available'
    if ui == 'healthy' and guardian in ('clear', 'disabled') and watchdog == 'clear':
        return 'ready', 'FF4ADDCB', 'Health checks ready'
    return 'unknown', 'FF91A4BC', 'Health status pending'


class ExperienceController:
    def __init__(self, profile, player, api):
        self.profile, self.player, self.api = profile, player, api
        self.xbmc, self.gui = api['xbmc'], api['gui']
        self.home = self.gui.Window(10000)
        self.last_tick = self.last_save = 0.0
        self.highlight = None
        self.highlight_at = 0.0
        self.origin = None
        self.recovery = None
        self.retry_count = 0
        self.retry_key = ''
        self.seek_pending = None
        self.session = api['read'](profile / 'session.json', {})
        self.boot_restore = False
        self.focus_pending = None
        self.recovery_notice = False

    def progress_lock(self):
        return self.api.get('progress_lock') or nullcontext()

    def save_source(self, key, route):
        with self.progress_lock():
            data = self.api['load_continue'](self.profile)
            sources = data.setdefault('sources', {})
            sources[key] = {'route': route, 'updated': int(time.time()), 'failures': 0}
            data['sources'] = dict(sorted(sources.items(),
                key=lambda pair: number(pair[1].get('updated')), reverse=True)[:100])
            self.api['save_continue'](self.profile, data)

    def remove_progress(self, key, collection):
        with self.progress_lock():
            data = self.api['load_continue'](self.profile)
            data.get(collection, {}).pop(key, None)
            self.api['save_continue'](self.profile, data)

    def prop(self, key):
        return self.home.getProperty('Infinity.' + key)

    def publish(self, key, value):
        self.api['set']('Infinity.' + key, value)

    def label(self, key):
        return str(self.xbmc.getInfoLabel(key) or '')

    def clear_art(self):
        for name in ('AmbientHome.Art', 'Preload.One', 'Preload.Two'):
            self.publish(name, '')

    def on_started(self):
        item = self.player.cw_item
        if not item:
            return
        if self.xbmc.getCondVisibility('Pvr.IsPlayingTV | Pvr.IsPlayingRadio'):
            return
        if self.retry_key != item['key']:
            self.retry_count = 0
        self.retry_key = item['key']
        route = stable_route(item.get('source', ''))
        # A recently highlighted provider route is accepted only when the
        # semantic title matches the actual playing item, not merely its time.
        if self.origin and time.monotonic() - self.origin['at'] < 20:
            title = item.get('showtitle') or item.get('title') or ''
            matched = title.casefold() == self.origin['title'].casefold()
            if matched and item.get('media') == 'tv':
                matched = (str(item.get('season')) == self.origin['season'] and
                           str(item.get('episode')) == self.origin['episode'])
            if matched:
                route = self.origin['route'] or route
        if route and self.api['bool']('source_memory_enabled', True):
            self.save_source(item['key'], route)
            item['stable_source'] = route
            self.publish('SourceMemory.Status', 'remembered')
        if self.seek_pending:
            if self.seek_pending['key'] == item['key']:
                self.seek_pending['ready'] = True
            else:
                self.seek_pending = None
        self.publish('Recovery.Status', 'playing')
        self.publish('Recovery.Available', 'false')
        self.recovery = None
        self.recovery_notice = False

    def on_error(self):
        # Callback only arms recovery; it never runs a dialog on Kodi's player
        # callback thread and never changes a healthy/paused/live player.
        item = dict(self.player.cw_item or {})
        if self.xbmc.getCondVisibility('Pvr.IsPlayingTV | Pvr.IsPlayingRadio'):
            self.publish('Recovery.Status', 'unavailable')
            return
        if not item or not item.get('key'):
            self.publish('Recovery.Status', 'unavailable')
            return
        self.seek_pending = None
        with self.progress_lock():
            data = self.api['load_continue'](self.profile)
            saved = data.get('items', {}).get(item['key'], {})
            source = data.get('sources', {}).get(item['key'], {})
            if source:
                source['failures'] = min(2, int(number(source.get('failures'))) + 1)
                self.api['save_continue'](self.profile, data)
        route = stable_route(source.get('route') or item.get('stable_source') or item.get('source', ''))
        if not route or item.get('media') not in ('movie', 'tv'):
            self.publish('Recovery.Status', 'unavailable')
            return
        if self.retry_key != item['key']:
            self.retry_count = 0
        self.retry_key = item['key']
        self.recovery = {'key': item['key'], 'route': route,
                         'position': number(saved.get('position')), 'at': time.monotonic()}
        self.publish('Recovery.Status', 'available' if self.retry_count < 2 else 'exhausted')
        self.publish('Recovery.Available', 'true' if self.retry_count < 2 else 'false')
        if self.retry_count < 2 and self.api['str']('playback_recovery', 'prompt') == 'prompt':
            self.recovery_notice = True

    def retry(self):
        if not self.recovery or self.retry_count >= 2 or self.player.isPlaying():
            return False
        if time.monotonic() - self.recovery['at'] > 300:
            self.recovery = None
            self.publish('Recovery.Available', 'false')
            return False
        record = self.recovery
        self.retry_count += 1
        self.publish('Recovery.Status', 'retrying')
        self.publish('Recovery.Available', 'false')
        self.seek_pending = dict(record, ready=False, started=time.monotonic())
        result = self.api['rpc']('Player.Open', {'item': {'file': record['route']}})
        if 'error' in result:
            self.seek_pending = None
            self.publish('Recovery.Status', 'failed')
            self.publish('Recovery.Available', 'true' if self.retry_count < 2 else 'false')
            return False
        return True

    def capture_session(self):
        window = self.gui.getCurrentWindowId()
        if window not in (10000, 10025, 10500, 10002, 10001) or self.gui.getCurrentWindowDialogId() != 9999:
            return
        try:
            focus = self.gui.Window(window).getFocusId()
        except Exception:
            focus = 0
        record = {'schema': 1, 'updated': int(time.time()), 'window': window,
                  'focus': max(0, int(focus)), 'position': int(number(self.label('Container(%d).CurrentItem' % focus))),
                  'path': browsing_route(self.label('Container.FolderPath')),
                  'view': self.label('Skin.String(Infinity.VisualMode)'),
                  'label': self.label('ListItem.Label')}
        self.api['atomic'](self.profile / 'session.json', record)
        self.session = record
        self.publish('Session.Status', 'saved')

    def restore_session(self, manual=False):
        if self.player.isPlaying() or not self.api['bool']('session_restore_enabled', True):
            return False
        saved = self.session
        names = {10000: 'home', 10025: 'videos', 10500: 'music', 10002: 'pictures', 10001: 'programs'}
        win = saved.get('window')
        if win not in names or time.time() - number(saved.get('updated')) > 604800:
            self.publish('Session.Status', 'unavailable')
            return False
        path = browsing_route(saved.get('path', ''))
        if win != 10000 and not path:
            self.publish('Session.Status', 'unavailable')
            return False
        params = {'window': names[win]}
        if path:
            params['parameters'] = [path]
        result = self.api['rpc']('GUI.ActivateWindow', params)
        if 'error' in result:
            self.publish('Session.Status', 'unavailable')
            return False
        if manual:
            view = {'normal': 'normal', 'follow': 'auto', 'adaptive': 'auto',
                    'cinema': 'cinema', 'compact': 'compact', 'twopane': 'twopane'}.get(saved.get('view'))
            if view:
                self.xbmc.executebuiltin('RunScript(script.infinity.commandcenter,view-mode,%s)' % view)
        self.focus_pending = dict(saved, due=time.monotonic() + 1.5, expires=time.monotonic() + 12)
        self.publish('Session.Status', 'restoring')
        return True

    def background_tick(self, now):
        self.clear_art()
        # Completing an already requested resume seek remains essential work.
        self.continue_pending_seek(now)

    def continue_pending_seek(self, now):
        if self.seek_pending:
            pending = self.seek_pending
            if now - pending['started'] > 30:
                self.seek_pending = None
                self.publish('Recovery.Status', 'failed')
            elif pending.get('ready') and self.player.isPlayingVideo():
                try:
                    total = self.player.getTotalTime()
                    if total > 0:
                        if 0 < pending['position'] < total * .95:
                            self.player.seekTime(pending['position'])
                        self.seek_pending = None
                except Exception:
                    pass

    def tick(self, now):
        if now - self.last_tick < 0.4:
            return
        self.last_tick = now
        if self.recovery_notice:
            self.recovery_notice = False
            self.gui.Dialog().notification('Infinity playback recovery',
                'Retry is available in the Infinity Command Palette.', self.gui.NOTIFICATION_INFO, 5000)
        playing = self.player.isPlaying()
        mode = self.prop('MotionModeEffective')
        tier = artwork_tier(memory_mb(self.label('System.Memory(free)')), self.label('System.ScreenWidth'),
                            playing, mode in ('off', 'reduced') or self.prop('RefreshThermalLimited') == 'true')
        self.publish('Artwork.Quality', tier)
        state, color, text = health(self.prop('UIHealth.Status'), self.prop('Guardian.Status'),
                                   self.prop('StartupWatchdog.Status'))
        self.publish('HealthOrb.State', state)
        self.publish('HealthOrb.Color', color)
        self.publish('HealthOrb.Label', text)
        ambient = self.api['str']('ambient_home', 'subtle')
        if ambient not in ('off', 'subtle', 'immersive'):
            ambient = 'subtle'
        self.publish('AmbientHome.Mode', ambient)
        ready = self.prop('BootStage') == 'ready'
        window = self.gui.getCurrentWindowId()
        if playing or not ready or window != 10000:
            self.clear_art()
        else:
            try:
                focus = self.gui.Window(window).getFocusId()
            except Exception:
                focus = 0
            route = self.label('ListItem.FileNameAndPath')
            title = self.label('ListItem.TVShowTitle') or self.label('ListItem.Title') or self.label('ListItem.Label')
            sig = (focus, route, title, self.label('ListItem.Art(fanart)'), tier, ambient)
            if sig != self.highlight:
                self.highlight = sig
                self.highlight_at = now
                self.origin = {'route': stable_route(route), 'title': title, 'at': now,
                               'season': self.label('ListItem.Season'), 'episode': self.label('ListItem.Episode')}
            elif now - self.highlight_at >= 0.45:
                self.publish('AmbientHome.Art', artwork(sig[3], tier, True) if ambient != 'off' else '')
                enabled = self.api['bool']('highlight_preload_enabled', True)
                for offset, name in ((1, 'One'), (2, 'Two')):
                    value = self.label('Container(%d).ListItem(%d).Art(poster)' % (focus, offset))
                    # Keep at most two textures, one under pressure. No wrapping
                    # duplicates, no bulk catalogue or video prefetch.
                    self.publish('Preload.' + name, artwork(value, tier) if enabled and (offset == 1 or tier != 'safe') else '')
        command = self.prop('Experience.Command')
        if command:
            self.home.clearProperty('Infinity.Experience.Command')
            if command == 'retry-playback':
                self.retry()
            elif command == 'restore-session':
                self.restore_session(manual=True)
            elif command == 'forget-source' and self.retry_key:
                self.remove_progress(self.retry_key, 'sources')
                self.publish('SourceMemory.Status', 'cleared')
            elif command.startswith('remove:') and re.fullmatch(r'remove:[a-f0-9]{64}', command):
                self.remove_progress(command[7:], 'items')
        if self.recovery and not playing and self.api['str']('playback_recovery', 'prompt') == 'auto':
            if now - self.recovery['at'] >= 2 and self.retry_count == 0:
                self.retry()
        self.continue_pending_seek(now)
        if ready and not self.boot_restore:
            self.boot_restore = True
            if window == 10000 and not playing:
                self.restore_session()
        if self.focus_pending:
            saved = self.focus_pending
            if now > saved['expires'] or playing:
                self.focus_pending = None
            elif now >= saved['due'] and window == saved['window']:
                if window == 10000 or self.label('Container.FolderPath') == saved.get('path'):
                    focus = int(number(saved.get('focus')))
                    pos = max(0, int(number(saved.get('position'))) - 1)
                    if focus:
                        self.xbmc.executebuiltin('Control.SetFocus(%d,%d,absolute)' % (focus, pos))
                    self.focus_pending = None
                    self.publish('Session.Status', 'restored')
        if ready and self.boot_restore and not self.focus_pending and not playing and now - self.last_save > 12:
            self.capture_session()
            self.last_save = now

    def shutdown(self):
        # Never overwrite a browsing snapshot with the full-screen player.
        if self.boot_restore and not self.player.isPlaying():
            self.capture_session()
        self.clear_art()
