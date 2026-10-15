# SPDX-License-Identifier: GPL-2.0-or-later
"""Checkpoint for the exact 0.8.2 property/theme-cache coordinator.

This version has no user-state writer or crash marker. Its generated theme
cache is reconstructible. Park the main loop and every monitor callback under
one lock before acknowledging that ownership; no engine authorization is given.
"""
import json
import os
from pathlib import Path
import re
import tempfile
import threading


def _read(path):
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        return None
    if len(data) > 262144:
        raise ValueError('oversized compatibility protocol')
    value = json.loads(data)
    if not isinstance(value, dict):
        raise ValueError('invalid compatibility protocol')
    return value


def _publish(path, value):
    fd, temporary = tempfile.mkstemp(prefix='.compat-', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _token(value):
    return isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9_-]{16,128}', value) is not None


class CompatCheckpoint:
    def __init__(self, control):
        self.control = Path(control)
        self.lock = threading.RLock()
        self.parked = False
        self.owner = None

    def poll(self):
        with self.lock:
            if self.parked:
                return True
            engine = _read(self.control / 'engine.json')
            if engine is None or type(engine.get('pid')) is not int or engine['pid'] != os.getpid():
                return False
            if type(engine.get('schema')) is not int or engine['schema'] != 1 or \
                    type(engine.get('native_api')) is not int or engine['native_api'] != 1 or \
                    not _token(engine.get('owner')):
                self.parked = True
                raise ValueError('invalid native compatibility owner')
            if self.owner is not None and self.owner != engine['owner']:
                self.parked = True
                raise ValueError('native compatibility owner changed in one process')
            base = dict(schema=1, pid=os.getpid(), owner=engine['owner'],
                        participant='infinity-compat', participant_api=1,
                        addon_version='0.8.2', global_safe_to_terminate=False)
            if self.owner is None:
                _publish(self.control / 'compat-active.json', dict(base, status='ACTIVE'))
                self.owner = engine['owner']
            request = _read(self.control / 'request.json')
            if request is None or any(request.get(k) != base[k] for k in ('schema', 'pid', 'owner')) or \
                    type(request.get('schema')) is not int or type(request.get('pid')) is not int:
                return False
            self.parked = True
            if not _token(request.get('session')) or request.get('phase') not in ('PREPARE', 'FINALIZE'):
                raise ValueError('invalid compatibility checkpoint request')
            _publish(self.control / 'compat-response.json', dict(base,
                session=request['session'], status='PARTICIPANT_COMPLETE', guard_frozen=True,
                operations=[{'name': 'critical_files', 'ok': True,
                             'result': 'NO_REQUIRED_USER_STATE_WRITES_IN_0.8.2'},
                            {'name': 'clean_marker', 'ok': True,
                             'result': 'NO_CRASH_MARKER_PRODUCED_IN_0.8.2'}]))
            return True
