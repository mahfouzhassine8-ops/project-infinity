"""Profile-local, bounded, crash-safe rail preferences. No Kodi imports or service."""
from contextlib import contextmanager
from copy import deepcopy
import json
import os
from pathlib import Path
import re
import tempfile
import time

SCHEMA = 1
SECTIONS = ('movies', 'tvshows')
LIMIT = 256
MAX_BYTES = 262144
ID_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,199}$')
TOKEN_RE = re.compile(r'^(?:b:[0-9a-f]{16}|c:[A-Za-z0-9][A-Za-z0-9_.-]{0,199})$')

class RailError(Exception):
    pass

class CorruptStore(RailError):
    pass


def valid_id(value):
    return isinstance(value, str) and bool(ID_RE.fullmatch(value))


def empty_state():
    return {'schema': SCHEMA, 'revision': 0, 'rails': {
        section: {'custom': [], 'order': []} for section in SECTIONS}}


def validate(data):
    if not isinstance(data, dict) or type(data.get('schema')) is not int or data.get('schema') != SCHEMA:
        raise CorruptStore('Unrecognized rail preferences. The original file was not changed.')
    if type(data.get('revision')) is not int or not 0 <= data['revision'] < 2**63:
        raise CorruptStore('Invalid rail revision.')
    rails = data.get('rails')
    if not isinstance(rails, dict) or set(rails) != set(SECTIONS):
        raise CorruptStore('Invalid rail sections.')
    for section in SECTIONS:
        part = rails[section]
        if not isinstance(part, dict):
            raise CorruptStore('Invalid rail record.')
        for key, limit, validator in [('custom', LIMIT, valid_id),
                                      ('order', LIMIT + 64, lambda v: isinstance(v, str) and bool(TOKEN_RE.fullmatch(v)))]:
            seq = part.get(key)
            if not isinstance(seq, list) or len(seq) > limit or not all(validator(v) for v in seq):
                raise CorruptStore('Invalid rail entries.')
            if len(seq) != len(set(seq)):
                raise CorruptStore('Duplicate rail entries.')
    return deepcopy(data)


def read_json(path):
    with open(path, 'rb') as src:
        raw = src.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise CorruptStore('Rail preferences exceed the safety limit.')
    try:
        return validate(json.loads(raw))
    except (UnicodeError, ValueError, TypeError) as exc:
        raise CorruptStore('Rail preferences cannot be read; no file was changed.') from exc


def sync_dir(path):
    # Android, Linux and macOS allow syncing the directory containing a rename.
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_bytes(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '.', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'wb') as out:
            out.write(content)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temporary, str(path))
        sync_dir(path.parent)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def locked(profile, abort=lambda: False, timeout=1.0):
    """OS advisory lock is released on interpreter/process death, never a stale flag."""
    import fcntl
    profile = Path(profile)
    profile.mkdir(parents=True, exist_ok=True)
    with open(profile / 'rails.lock', 'a+b') as lockfile:
        deadline = time.monotonic() + timeout
        while True:
            if abort():
                raise RailError('Infinity is closing; no new rail changes were started.')
            try:
                fcntl.flock(lockfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise RailError('Another rail update is finishing. Please try again.')
                time.sleep(0.025)
        try:
            yield
        finally:
            fcntl.flock(lockfile.fileno(), fcntl.LOCK_UN)


class Store:
    def __init__(self, profile, abort=lambda: False):
        self.profile = Path(profile)
        self.path = self.profile / 'rails.json'
        self.backup = self.profile / 'rails.json.bak'
        self.abort = abort

    def load(self):
        """Read primary; recover last valid snapshot in memory. Never rewrite on read."""
        if not self.path.exists():
            return empty_state(), ''
        try:
            return read_json(self.path), ''
        except (OSError, CorruptStore) as exc:
            try:
                return read_json(self.backup), 'Using the last good rail backup. The damaged original was retained.'
            except (OSError, CorruptStore):
                return empty_state(), str(exc)

    def change(self, mutate):
        with locked(self.profile, self.abort):
            # Unlike the display path, writes never silently replace damaged state.
            old = read_json(self.path) if self.path.exists() else empty_state()
            new = deepcopy(old)
            result = mutate(new)
            validate(new)
            if new == old:
                return result, old['revision']
            if self.abort():
                raise RailError('Infinity is closing; your existing rail preferences were kept.')
            new['revision'] = old['revision'] + 1
            encoded = (json.dumps(new, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')
            if len(encoded) > MAX_BYTES:
                raise RailError('Rail preferences exceed the safety limit.')
            if self.path.exists():
                atomic_bytes(self.backup, self.path.read_bytes())
            atomic_bytes(self.path, encoded)
            return result, new['revision']

    def add(self, addon_id, sections, builtin_ids):
        if not valid_id(addon_id) or not sections or not set(sections) <= set(SECTIONS):
            raise RailError('Invalid add-on or rail destination.')
        def apply(data):
            added = []
            for section in sections:
                part = data['rails'][section]
                if addon_id in builtin_ids.get(section, ()) or addon_id in part['custom']:
                    continue
                if len(part['custom']) >= LIMIT:
                    raise RailError('This rail already contains the maximum of 256 custom cards.')
                part['custom'].append(addon_id)
                part['order'].append('c:' + addon_id)
                added.append(section)
            return added
        return self.change(apply)

    def remove(self, section, addon_id):
        if section not in SECTIONS or not valid_id(addon_id):
            raise RailError('Invalid custom card.')
        def apply(data):
            part = data['rails'][section]
            existed = addon_id in part['custom']
            part['custom'] = [i for i in part['custom'] if i != addon_id]
            part['order'] = [i for i in part['order'] if i != 'c:' + addon_id]
            return existed
        return self.change(apply)

    def move(self, section, token, before, default_tokens):
        if section not in SECTIONS:
            raise RailError('Invalid rail destination.')
        def apply(data):
            part = data['rails'][section]
            tokens = ordered_tokens(default_tokens, part)
            if token not in tokens or (before is not None and before not in tokens):
                raise RailError('The rail changed while this menu was open. Please reopen it.')
            if token == before:
                return False
            tokens.remove(token)
            tokens.insert(len(tokens) if before is None else tokens.index(before), token)
            part['order'] = tokens
            return True
        return self.change(apply)


def ordered_tokens(default_tokens, part):
    # Missing/disabled custom IDs are retained so their positions return on reinstall.
    allowed = list(default_tokens) + ['c:' + a for a in part['custom']]
    permitted = set(allowed)
    ordered = [t for t in part['order'] if t in permitted]
    # Until an explicit move, new customs belong after all default cards.
    if not any(t.startswith('b:') for t in ordered):
        ordered = list(default_tokens) + ordered
    seen = set(ordered)
    return ordered + [t for t in allowed if t not in seen]
