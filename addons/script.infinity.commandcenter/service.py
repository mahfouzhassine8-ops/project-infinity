# SPDX-License-Identifier: GPL-2.0-or-later
from __future__ import annotations

from pathlib import Path
import time

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

from common import (ADDON_ID, addon_profile, atomic_json, jsonrpc, log, read_json,
                    semantic_playback_key, setting_bool, setting_int)

HOME = xbmcgui.Window(10000)
PLAYBACK_FILE = 'playback-memory.json'
GUARDIAN_FILE = 'guardian-state.json'


def _set(name, value):
    try:
        HOME.setProperty(name, str(value))
    except Exception:
        pass


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

    history = _compat_history()
    starts = [int(x) for x in history.get('unclean_starts', []) if str(x).isdigit()]
    last_start = int(history.get('last_start', int(time.time())))
    unclean_count = len(starts)
    window = max(5, min(180, setting_int('suspect_window_minutes', 30))) * 60
    suspects = []

    if unclean_count:
        addons_root = Path(xbmcvfs.translatePath('special://home/addons'))
        if addons_root.is_dir():
            for child in addons_root.iterdir():
                if not child.is_dir() or child.name.startswith('repository.'):
                    continue
                if child.name in (ADDON_ID, 'service.infinity.compat'):
                    continue
                try:
                    modified = int(child.stat().st_mtime)
                except OSError:
                    continue
                delta = last_start - modified
                if 0 <= delta <= window:
                    suspects.append({
                        'addon_id': child.name,
                        'name': _addon_name(child.name),
                        'modified': modified,
                        'minutes_before_start': max(0, int(round(delta / 60.0))),
                    })

    suspects.sort(key=lambda item: item['minutes_before_start'])
    state = {
        'schema': 1,
        'timestamp': int(time.time()),
        'unclean_start_count': unclean_count,
        'last_start': last_start,
        'correlation_window_minutes': int(window / 60),
        'suspects': suspects[:20],
        'evidence_note': 'Recent modification is correlation only, not proof of crash causation.',
    }
    atomic_json(profile / GUARDIAN_FILE, state)
    _set('Infinity.Guardian.Status', 'suspects' if suspects else 'clear')
    _set('Infinity.Guardian.UncleanStarts', unclean_count)
    _set('Infinity.Guardian.SuspectCount', len(suspects))
    _set('Infinity.Guardian.Suspects', ','.join(item['addon_id'] for item in suspects[:10]))
    log('Guardian: unclean=' + str(unclean_count) + ' suspects=' + str(len(suspects)))


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
    if not saved:
        return None
    language = (saved.get('language') or '').lower()
    name = (saved.get('name') or '').lower()
    for stream in available or []:
        if language and (stream.get('language') or '').lower() == language and name and (stream.get('name') or '').lower() == name:
            return stream.get('index')
    for stream in available or []:
        if language and (stream.get('language') or '').lower() == language:
            return stream.get('index')
    wanted = saved.get('index')
    if isinstance(wanted, int) and any(stream.get('index') == wanted for stream in available or []):
        return wanted
    return None


def _load_playback(profile: Path):
    return read_json(profile / PLAYBACK_FILE, {'schema': 1, 'titles': {}})


def _save_playback(profile: Path, data):
    data['schema'] = 1
    data['updated'] = int(time.time())
    titles = data.get('titles', {})
    if len(titles) > 500:
        ordered = sorted(titles.items(), key=lambda pair: pair[1].get('updated', 0), reverse=True)[:500]
        data['titles'] = dict(ordered)
    atomic_json(profile / PLAYBACK_FILE, data)


class InfinityPlayer(xbmc.Player):
    def __init__(self, profile: Path):
        super().__init__()
        self.profile = profile
        self.key = None
        self.readable = None
        self.last_props = None
        self.restore_pending = False

    def onAVStarted(self):
        if not setting_bool('playback_memory_enabled', True):
            return
        self.key, self.readable = semantic_playback_key()
        self.restore_pending = True
        _set('Infinity.PlaybackMemory.TitleKey', self.readable)
        log('Playback memory armed for ' + self.readable)

    def onPlayBackStopped(self):
        self.persist()

    def onPlayBackEnded(self):
        self.persist()

    def poll(self):
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
        if self.restore_pending:
            self.restore_pending = False
            self.restore(player_id, props)

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


def main():
    profile = addon_profile()
    profile.mkdir(parents=True, exist_ok=True)
    scan_guardian(profile)
    player = InfinityPlayer(profile)
    monitor = xbmc.Monitor()
    _set('Infinity.CommandCenter.Ready', 'true')
    _set('Infinity.CommandCenter.Version', '0.1.0')
    last_guardian = time.monotonic()
    while not monitor.abortRequested():
        player.poll()
        now = time.monotonic()
        if now - last_guardian >= 300:
            scan_guardian(profile)
            last_guardian = now
        if monitor.waitForAbort(2.0):
            break
    player.persist()


if __name__ == '__main__':
    main()
