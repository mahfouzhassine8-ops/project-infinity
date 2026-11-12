"""Read-only Cast clock adapter for the existing playback recorder.

No database, worker, provider request, player command or persistent setting.
Only the same process may supply a bounded clock for the actual playing item.
"""
import hashlib
import json
import math
import os
import re
import socket
import struct
import time

CHANNEL = re.compile(r'infinity-cast-([1-9][0-9]*)-([a-f0-9]{32})\Z')
OCCURRENCE = re.compile(r'[a-f0-9]{32}\Z')

def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()

def _unique_object(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError('Duplicate Cast field')
        result[name] = value
    return result

def _read(name, expected, occurrence):
    """One local connection, one total deadline, same PID and UID both ways."""
    deadline = time.monotonic() + .15
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(.15)
        client.connect('\0' + name)
        pid, uid, _ = struct.unpack('3i', client.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        if (pid, uid) != (os.getpid(), os.getuid()):
            raise ValueError('Cast peer owner mismatch')
        data = bytearray()
        while b'\n' not in data:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('Cast clock deadline')
            client.settimeout(remaining)
            part = client.recv(2049 - len(data))
            if not part:
                raise ValueError('Incomplete Cast clock')
            data.extend(part)
            if len(data) > 2048:
                raise ValueError('Cast clock size limit')
        if data.count(b'\n') != 1 or not data.endswith(b'\n'):
            raise ValueError('Cast clock framing')
        value = json.loads(data, object_pairs_hook=_unique_object)
        validate(value, expected, occurrence, time.monotonic() * 1000)
        ack = dict(session=expected['session'], file_sha256=expected['file_sha256'],
                   origin_sha256=expected['origin_sha256'], occurrence=occurrence)
        client.settimeout(max(.001, deadline - time.monotonic()))
        client.sendall((json.dumps(ack, separators=(',', ':')) + '\n').encode('utf-8'))
        return value

def validate(value, expected, occurrence, now_ms):
    if not isinstance(value, dict):
        raise ValueError('Cast clock object')
    if (type(value.get('schema')) is not int or value['schema'] != 1 or
            value.get('controller') != 'InfinityCastV1' or
            type(value.get('pid')) is not int or value['pid'] != os.getpid() or
            any(value.get(k) != v for k, v in expected.items()) or
            value.get('occurrence', '') not in ('', occurrence)):
        raise ValueError('Cast clock identity mismatch')
    stamp = value.get('at_ms')
    if type(stamp) not in (int, float) or not math.isfinite(stamp) or not 0 <= now_ms - stamp <= 2000:
        raise ValueError('Cast clock stale')
    for key in ('connected', 'owned', 'media_matches', 'ever_played', 'completed'):
        if type(value.get(key)) is not bool:
            raise ValueError('Cast clock boolean')
    for key in ('position', 'duration'):
        number = value.get(key)
        if type(number) not in (int, float) or not math.isfinite(number) or not 0 <= number <= 30 * 24 * 3600:
            raise ValueError('Cast clock range')
    if value['duration'] and value['position'] > value['duration'] + 1:
        raise ValueError('Cast clock position exceeds duration')
    if value['owned'] and value.get('occurrence') != occurrence:
        raise ValueError('Cast handoff not acknowledged for this playback')
    if value['completed'] and not value['ever_played']:
        raise ValueError('Cast completion before playback')
    return value

def register(name, clear, xbmc, xbmcgui):
    match = CHANNEL.fullmatch(str(name))
    if not match or int(match[1]) != os.getpid() or xbmc.getSkinDir() != 'skin.infinity.diggz':
        return False
    home = xbmcgui.Window(10000)
    if clear:
        if home.getProperty('Infinity.Cast.Channel') in ('', name):
            # An explicit release differs from Home properties disappearing
            # during a skin/display reload. It is RAM-only, never profile data.
            home.setProperty('Infinity.Cast.Channel', 'released:' + name)
            home.clearProperty('Infinity.Cast.Connected')
    else:
        home.setProperty('Infinity.Cast.Channel', name)
    return True

class Clock:
    def __init__(self, xbmc, xbmcgui):
        self.xbmc, self.gui, self.home = xbmc, xbmcgui, xbmcgui.Window(10000)
        self.binding = None
        self.owned = False
        self.next_poll = 0.0
        self.value = None

    def sample(self, player):
        try:
            return self._sample(player)
        except (OSError, ValueError, TypeError, RuntimeError, AttributeError):
            return dict(hold=True) if self.owned else None

    def _sample(self, player):
        self.home = self.gui.Window(10000)
        name = self.home.getProperty('Infinity.Cast.Channel')
        if name.startswith('released:'):
            if self.binding is None or name[9:] == self.binding[0]:
                self.binding = self.value = None
                self.owned = False
                self.home.clearProperty('Infinity.Cast.Channel')
                self.home.clearProperty('Infinity.Cast.Connected')
                return None
        if not name and self.owned and self.binding:
            name = self.binding[0]
        if not name or self.xbmc.getSkinDir() != 'skin.infinity.diggz':
            self.binding = self.value = None
            self.owned = False
            return None
        occurrence = player.cw_occurrence
        match = CHANNEL.fullmatch(name)
        if not match or int(match[1]) != os.getpid() or not OCCURRENCE.fullmatch(str(occurrence)):
            return None
        try:
            if not player.isPlayingVideo():
                # Do not replace a valid remote sample with a released phone
                # clock in the existing stopped/error callback.
                return dict(hold=True) if self.owned else None
            def actual():
                return player.getPlayingFile(), player.getPlayingItem().getProperty('Infinity.Resume.OriginalProvider')
            before = actual()
            expected = dict(session=match[2], file_sha256=digest(before[0]), origin_sha256=digest(before[1]))
            binding = (name, occurrence, expected['file_sha256'], expected['origin_sha256'])
            if binding != self.binding:
                self.binding, self.value, self.owned, self.next_poll = binding, None, False, 0.0
            now = time.monotonic()
            if now >= self.next_poll:
                self.next_poll = now + .5
                value = _read(name, expected, occurrence)
                if actual() != before or player.cw_occurrence != occurrence:
                    return None
                self.value = value
                self.owned = bool(value['owned'])
                if value['connected']:
                    self.home.setProperty('Infinity.Cast.Connected', 'true')
                else:
                    self.home.clearProperty('Infinity.Cast.Connected')
            value = self.value
            if not value or not self.owned:
                return None
            validate(value, expected, occurrence, time.monotonic() * 1000)
            if not (value['ever_played'] and value['duration'] > 0 and
                    (value['completed'] or (value['connected'] and value['media_matches']))):
                return dict(hold=True)
            return dict(position=value['position'], duration=value['duration'], completed=value['completed'], hold=False)
        except (OSError, ValueError, TypeError, RuntimeError, AttributeError):
            self.home.clearProperty('Infinity.Cast.Connected')
            return dict(hold=True) if self.owned else None
