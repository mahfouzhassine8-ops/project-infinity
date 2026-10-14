"""One-shot .215 -> .216 skin delta with guarded backup, readback and rollback.

The update ships no skin binaries or fonts. Only the authorized XML/metadata
changes are applied to the user's exact installed .215; unrelated files are
never rewritten. Nothing executes automatically on installation or startup.
"""
import hashlib
import json
from pathlib import Path, PurePosixPath
from lib.store import RailError, atomic_bytes, locked, sync_dir


def digest(data):
    return hashlib.sha256(data).hexdigest()


class Installer:
    def __init__(self, skin, profile, payload, abort=lambda: False):
        self.skin = Path(skin).resolve()
        self.payload = Path(payload)
        self.profile = Path(profile) / 'skin216'
        self.abort = abort
        raw = (self.payload / 'manifest.json').read_bytes()
        self.manifest_hash = digest(raw)
        self.manifest = json.loads(raw)
        if self.manifest.get('base_version') != '1.0.5.215' or self.manifest.get('version') != '1.0.5.216':
            raise RailError('The update package has unexpected version metadata.')
        self.entries = self.manifest['files']
        if not isinstance(self.entries, dict) or not 1 <= len(self.entries) <= 100:
            raise RailError('Invalid update manifest.')
        self.journal = self.profile / 'transaction.json'

    def target(self, name):
        rel = PurePosixPath(name)
        if rel.is_absolute() or not rel.parts or any(p in ('..','.') for p in rel.parts) or '\\' in name:
            raise RailError('Unsafe skin update path.')
        target = self.skin.joinpath(*rel.parts)
        if self.skin not in target.resolve().parents or target.is_symlink():
            raise RailError('Skin update path is outside the installed skin.')
        if target.suffix.lower() not in ('.xml', '.json'):
            raise RailError('Only the authorized skin XML and metadata can be updated.')
        return target

    def read_hash(self, path):
        return digest(path.read_bytes()) if path.is_file() else None

    def status(self):
        originals = candidates = 0
        for name, row in self.entries.items():
            current = self.read_hash(self.target(name))
            if current == row['after']:
                candidates += 1
            elif current == row['before']:
                originals += 1
            else:
                return 'unknown', name
        if originals == len(self.entries):
            return 'parent', ''
        if candidates == len(self.entries):
            return 'candidate', ''
        return 'mixed', ''

    def _original_path(self, sha):
        if not isinstance(sha, str) or len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
            raise RailError('Invalid update backup identity.')
        return self.profile / 'originals' / sha

    def _check_journal(self):
        data = json.loads(self.journal.read_text('utf-8'))
        if data.get('manifest_sha256') != self.manifest_hash:
            raise RailError('A different skin update owns the saved rollback. No files were changed.')
        return data

    def _backup_complete(self):
        self._check_journal()
        for row in self.entries.values():
            if row['before'] is not None:
                path = self._original_path(row['before'])
                if self.read_hash(path) != row['before']:
                    raise RailError('The exact .215 rollback is missing or damaged. No files were changed.')

    def _payload_bytes(self, row):
        data = (self.payload / 'objects' / row['after']).read_bytes()
        if digest(data) != row['after']:
            raise RailError('The skin update payload failed its checksum.')
        return data

    def apply(self):
        with locked(self.profile, self.abort):
            status, name = self.status()
            if status == 'unknown':
                raise RailError('NOT UPDATED: the installed .215 files differ at ' + name + '. No skin files were changed.')
            if status == 'candidate':
                return 'already_applied'
            # Stage and checksum everything before touching the skin.
            staged = {name: self._payload_bytes(row) for name, row in self.entries.items()}
            if self.journal.exists():
                self._backup_complete()
            else:
                if status != 'parent':
                    raise RailError('A partial update has no matching recovery record. No skin files were changed.')
                for name, row in self.entries.items():
                    if row['before'] is not None:
                        atomic_bytes(self._original_path(row['before']), self.target(name).read_bytes())
                self._record('prepared')
                self._backup_complete()
            if self.abort():
                raise RailError('Infinity is closing. The update was not started.')
            try:
                order = [n for n in self.entries if n != 'addon.xml'] + ['addon.xml']
                for name in order:
                    row = self.entries[name]
                    if self.abort():
                        raise RailError('Infinity started closing; the skin update is being rolled back.')
                    target = self.target(name)
                    # Check again immediately before each replacement, including new-file collisions.
                    if self.read_hash(target) not in (row['before'], row['after']):
                        raise RailError('Another update changed ' + name + '; stopped to protect it.')
                    atomic_bytes(target, staged[name])
                    if self.read_hash(target) != row['after']:
                        raise RailError('Skin update readback failed at ' + name)
                if self.status()[0] != 'candidate':
                    raise RailError('The skin did not pass final verification.')
                self._record('applied')
            except Exception:
                # Best effort rollback changes belonging to this transaction only.
                self._restore_known()
                raise
            return 'applied'

    def _record(self, status):
        record = {'schema': 1, 'manifest_sha256': self.manifest_hash,
                  'base_version': '1.0.5.215', 'version': '1.0.5.216', 'status': status}
        atomic_bytes(self.journal, (json.dumps(record, sort_keys=True, indent=2)+'\n').encode())

    def _restore_known(self):
        self._backup_complete()
        unknown = []
        # Restore addon.xml last so metadata is never ahead of an incomplete rollback.
        order = [n for n in self.entries if n != 'addon.xml'] + ['addon.xml']
        for name in order:
            row = self.entries[name]
            target = self.target(name)
            current = self.read_hash(target)
            if current == row['before']:
                continue
            if current != row['after']:
                unknown.append(name)
                continue
            if row['before'] is None:
                target.unlink()
                sync_dir(target.parent)
            else:
                atomic_bytes(target, self._original_path(row['before']).read_bytes())
        self._record('recovery_required' if unknown else 'restored')
        if unknown:
            raise RailError('Unrecognized files were left untouched. The .215 rollback is retained: ' + ', '.join(unknown))

    def rollback(self):
        with locked(self.profile, self.abort):
            self._backup_complete()
            status, name = self.status()
            if status == 'unknown':
                raise RailError('NOT RESTORED: a later or different update changed ' + name + '. No skin files were changed.')
            if status == 'parent':
                return 'already_restored'
            self._restore_known()
            if self.status()[0] != 'parent':
                raise RailError('Rollback needs verification. Your exact original files remain saved.')
            return 'restored'
