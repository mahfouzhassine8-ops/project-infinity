# SPDX-License-Identifier: GPL-2.0-or-later
"""Checked, one-way persistence barrier for the compatibility service only.

All legacy critical writes run synchronously on this service's main thread.
Once a native request is observed that thread is permanently parked, even if
the checkpoint fails. No receipt grants permission to terminate the engine.
"""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import stat
import tempfile

API = 1
ADDON_VERSION = '0.7.2'
PARTICIPANT = 'infinity-compat'
_dirty_files = set()
_dirty_directories = set()
_write_failures = []


@contextmanager
def critical_write(path):
    path = Path(path)
    # Persist the parent entries for directories this operation may create.
    parent = path.parent
    directories = {parent}
    while not parent.exists():
        parent = parent.parent
        directories.add(parent)
    try:
        yield
    except Exception as error:
        _write_failures.append(type(error).__name__ + ':' + path.name)
        raise
    else:
        _dirty_files.add(path)
        _dirty_directories.update(directories)


def _sync(path, directory=False):
    flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW
    if directory:
        flags |= os.O_DIRECTORY
    fd = os.open(str(path), flags)
    try:
        mode = os.fstat(fd).st_mode
        if not (stat.S_ISDIR(mode) if directory else stat.S_ISREG(mode)):
            raise OSError('unexpected checkpoint file type')
        os.fsync(fd)
    finally:
        os.close(fd)


def _publish_json(path, value):
    path = Path(path)
    fd, temporary = tempfile.mkstemp(prefix='.compat-', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, sort_keys=True)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        # Publication is the last fallible action. The receipt is transport,
        # not user state; all certified files/namespaces are already fsynced.
        # No later receipt-directory error may revoke a visible COMPLETE.
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _read(path):
    try:
        raw = Path(path).read_bytes()
    except FileNotFoundError:
        return None
    if len(raw) > 262144:
        raise ValueError('oversized checkpoint protocol')
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError('checkpoint protocol is not an object')
    return value


def _token(value):
    return isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9_-]{16,128}', value) is not None


class CompatCheckpoint:
    def __init__(self, profile, control):
        self.profile, self.control = Path(profile), Path(control)
        self.identity = None
        self.registered_owner = None
        self.parked = False
        self.error = None

    def _response(self, status, operations, error=None):
        result = dict(self.identity, participant=PARTICIPANT, status=status,
                      participant_api=API, addon_version=ADDON_VERSION,
                      global_safe_to_terminate=False, guard_frozen=True,
                      operations=operations)
        if error:
            result['error'] = str(error)[:240]
        _publish_json(self.control / 'compat-response.json', result)

    def poll(self):
        if self.parked:
            return True
        # An absent or old-process handshake is ordinary legacy operation.
        engine = _read(self.control / 'engine.json')
        if engine is None or type(engine.get('pid')) is not int or engine['pid'] != os.getpid():
            return False
        if type(engine.get('schema')) is not int or engine['schema'] != API or \
                type(engine.get('native_api')) is not int or engine['native_api'] != API or \
                not _token(engine.get('owner')):
            self.parked = True
            self.error = 'invalid native checkpoint identity'
            return True
        base = {'schema': API, 'pid': os.getpid(), 'owner': engine['owner']}
        if self.registered_owner != engine['owner']:
            if self.registered_owner is not None:
                self.parked = True
                self.error = 'native owner changed in same engine'
                return True
            _publish_json(self.control / 'compat-active.json', dict(base,
                participant=PARTICIPANT, status='ACTIVE', participant_api=API,
                addon_version=ADDON_VERSION, global_safe_to_terminate=False))
            self.registered_owner = engine['owner']
        request = _read(self.control / 'request.json')
        if request is None or any(request.get(k) != v for k, v in base.items()) or \
                type(request.get('schema')) is not int or type(request.get('pid')) is not int:
            return False
        self.parked = True  # Set before all fallible persistence work; never reopen.
        self.identity = dict(base, session=request.get('session'))
        operations = []
        try:
            if not _token(request.get('session')) or request.get('phase') not in ('PREPARE', 'FINALIZE'):
                raise ValueError('invalid compat checkpoint request')
            if _write_failures:
                raise OSError('prior critical compatibility write failed: ' + ';'.join(_write_failures))
            # History affects automatic safe-mode policy; health/theme/layout
            # snapshots are reconstructible diagnostics and are not flushed.
            history = self.profile / 'startup-history.json'
            value = _read(history)
            if value is None or not isinstance(value.get('unclean_starts'), list):
                raise ValueError('compatibility history is unavailable')
            marker = self.profile / 'startup-marker.json'
            for path in sorted(_dirty_files | {history}):
                if path != marker:
                    _sync(path)
            for path in sorted(_dirty_directories | {self.profile}):
                _sync(path, directory=True)
            operations.append({'name': 'critical_files', 'ok': True})
            # This marker describes this service, not whole-engine success.
            # The guard remains permanently parked after its marker is removed.
            try:
                marker.unlink()
            except FileNotFoundError:
                pass
            _sync(self.profile, directory=True)
            if marker.exists():
                raise OSError('compatibility clean marker remains')
            operations.append({'name': 'clean_marker', 'ok': True})
            self._response('PARTICIPANT_COMPLETE', operations)
        except Exception as error:
            self.error = str(error)
            operations.append({'name': 'compat_checkpoint', 'ok': False})
            try:
                self._response('CHECKPOINT_FAILED', operations, error)
            except Exception:
                pass  # No readable receipt is never a successful barrier.
        return True
