"""Bounded identity reads only. No Kodi imports, execution of target code or writes."""
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import struct
from zipfile import BadZipFile, ZipFile

CC = 'script.infinity.commandcenter'
TRAKT = 'script.module.tmdbhelper.sync.trakt'
OWNED = (CC, 'script.infinity.rails', 'script.infinity.uirepair', 'script.infinity.watchedbridge')
DENIED = {'userdata', 'addon_data', 'database', 'databases', 'profile', 'cache', '__pycache__'}
ROOT_DENIED = DENIED - {'cache', '__pycache__'}  # Kodi's authenticated APK assets live in its own cache/apk.


class Cancelled(Exception):
    pass


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def safe_relative(name):
    if not isinstance(name, str) or not name or '\\' in name or ':' in name:
        raise ValueError('Unrecognized source path')
    parts = name.split('/')
    if any(p in ('', '.', '..') or p.casefold() in DENIED for p in parts):
        raise ValueError('Non-source path refused')
    if PurePosixPath(name).is_absolute():
        raise ValueError('Absolute source path refused')
    return parts


def source_path(root, name):
    parts = safe_relative(name)
    root = Path(root)
    if not root.is_absolute() or any(p.casefold() in ROOT_DENIED for p in root.parts):
        raise ValueError('Active source path is unavailable or points to saved data')
    if root.is_symlink():
        raise ValueError('Symbolic add-on root refused')
    root = root.resolve(strict=True)
    target = root
    for part in parts:
        target = target / part
        if target.is_symlink():
            raise ValueError('Symbolic source path refused')
    if not target.resolve(strict=True).is_relative_to(root):
        raise ValueError('Source path escaped its active add-on')
    return target


def bounded_read(path, limit):
    with open(path, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError('Regular files only')
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('Source metadata exceeds its read limit')
    return raw


def file_hash(path, limit, progress=None):
    with open(path, 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
            raise ValueError('File is not a bounded regular source file')
        digest, count = hashlib.sha256(), 0
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            count += len(chunk)
            if count > limit:
                raise ValueError('Read limit exceeded')
            digest.update(chunk)
            if progress:
                progress(count, before.st_size)
        after = os.fstat(stream.fileno())
    current = os.stat(path, follow_symlinks=False)
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)
    if identity(before) != identity(after) or identity(after) != identity(current) or count != after.st_size or not stat.S_ISREG(current.st_mode):
        raise ValueError('File changed while being read; hash refused')
    return dict(sha256=digest.hexdigest(), bytes=count)


def manifest_identity(raw):
    """Read only package/version fields from standard Android binary XML."""
    if len(raw) < 8:
        raise ValueError('Truncated Android manifest')
    kind, header, total = struct.unpack_from('<HHI', raw)
    if kind != 3 or header != 8 or total != len(raw) or total > 4 * 1024 * 1024:
        raise ValueError('Unsupported binary Android manifest')
    strings = None

    def length8(at):
        n = raw[at]
        return (((n & 127) << 8) | raw[at+1], at+2) if n & 128 else (n, at+1)

    def length16(at):
        n = struct.unpack_from('<H', raw, at)[0]
        return (((n & 32767) << 16) | struct.unpack_from('<H', raw, at+2)[0], at+4) if n & 32768 else (n, at+2)

    offset = header
    while offset + 8 <= total:
        kind, size_header, size = struct.unpack_from('<HHI', raw, offset)
        if size_header < 8 or size < size_header or offset + size > total:
            raise ValueError('Invalid Android XML chunk')
        if kind == 1:
            count, _, flags, start, _ = struct.unpack_from('<IIIII', raw, offset+8)
            if size_header < 28 or count > 100000 or size_header + count*4 > size:
                raise ValueError('Invalid Android string pool')
            strings = []
            for i in range(count):
                at = offset + start + struct.unpack_from('<I', raw, offset+size_header+i*4)[0]
                if flags & 256:
                    _, at = length8(at)
                    length, at = length8(at)
                    end = at + length
                    if end >= offset+size:
                        raise ValueError('Invalid Android string')
                    strings.append(raw[at:end].decode('utf-8'))
                else:
                    length, at = length16(at)
                    end = at + length*2
                    if end+1 >= offset+size:
                        raise ValueError('Invalid Android string')
                    strings.append(raw[at:end].decode('utf-16le'))
        if kind == 0x102:
            if strings is None or size_header != 16 or size < 36:
                raise ValueError('Invalid Android manifest element')
            name = struct.unpack_from('<I', raw, offset+20)[0]
            if strings[name] != 'manifest':
                raise ValueError('Android manifest root was not found')
            attr_start, attr_size, count = struct.unpack_from('<HHH', raw, offset+24)
            if attr_size < 20 or count > 256 or 16+attr_start+attr_size*count > size:
                raise ValueError('Invalid Android manifest attributes')
            result = {}
            for i in range(count):
                at = offset+16+attr_start+i*attr_size
                ns, name, text = struct.unpack_from('<III', raw, at)
                value_size, _, value_type, value = struct.unpack_from('<HBBI', raw, at+12)
                if value_size != 8:
                    raise ValueError('Unsupported Android attribute')
                name = strings[name]
                namespace = strings[ns] if ns != 0xffffffff else None
                if name == 'package' and namespace is None:
                    if text != 0xffffffff:
                        result['package'] = strings[text]
                    elif value_type == 3:
                        result['package'] = strings[value]
                if namespace == 'http://schemas.android.com/apk/res/android':
                    if name in ('versionCode', 'versionCodeMajor') and value_type in (16, 17):
                        result[name] = value
                    elif name == 'versionName' and (text != 0xffffffff or value_type == 3):
                        result[name] = strings[text if text != 0xffffffff else value]
            if 'package' not in result or 'versionCode' not in result:
                raise ValueError('APK package/version could not be read')
            result['long_version_code'] = (result.get('versionCodeMajor', 0) << 32) | result['versionCode']
            return result
        offset += size
    raise ValueError('Android manifest identity unavailable')


def apk_identity(path, pins, progress=None):
    result = dict(path_source='KODI_ANDROID_APK published by the existing Android engine', status='APK_UNREADABLE', signature_verified_on_device=False)
    if not path:
        result['limitation'] = 'Kodi did not expose its installed APK path. No APK hash was invented.'
        return result
    result['path'] = path
    try:
        if not os.path.isabs(path) or not path.endswith('.apk'):
            raise ValueError('Kodi APK path is not an absolute APK filename')
        result.update(file_hash(path, 3*1024*1024*1024, progress))
        result['status'] = 'APK_BYTES_READ'
        try:
            with ZipFile(path) as z:
                entry = z.getinfo('AndroidManifest.xml')
                if entry.file_size > 4*1024*1024:
                    raise ValueError('APK manifest exceeds read bound')
                result['manifest'] = manifest_identity(z.read(entry))
        except (OSError, ValueError, KeyError, IndexError, struct.error, BadZipFile, RuntimeError) as error:
            result['manifest_limitation'] = type(error).__name__ + ': ' + str(error)
        matches = [version for version, row in pins['apks'].items() if isinstance(row, dict) and row.get('sha256') == result['sha256']]
        result['known_verified_APK_reference'] = matches[0] if len(matches) == 1 else None
        if len(matches) == 1:
            result['original_signer_by_previously_verified_whole_APK_byte_identity'] = pins['certificate_sha256']
        else:
            result['signer_limitation'] = 'Unknown APK bytes. This collector does not perform APK signature verification.'
    except Cancelled:
        raise
    except (OSError, ValueError) as error:
        result['limitation'] = type(error).__name__ + ': ' + str(error) + '; no APK hash was invented.'
        result.pop('sha256', None)
        result.pop('bytes', None)
    return result


def metadata(addon_info, aid):
    value = addon_info(aid)
    if not isinstance(value, dict) or value.get('id') != aid:
        raise ValueError('Unexpected active add-on identity')
    root = value['path']
    if not os.path.isabs(root) or Path(root.rstrip('/')).name != aid:
        raise ValueError('Unsupported active source path; no alternate copy assumed')
    return {k: value[k] for k in ('id', 'version', 'path')}


def module_inventory(addon_info, pins):
    result = dict(status='MODULE_METADATA_UNREADABLE', components={}, files={}, known_verified_manifest_signature_reference=None)
    try:
        for aid in OWNED:
            try:
                result['components'][aid] = metadata(addon_info, aid)
            except (OSError, ValueError, RuntimeError) as error:
                result['components'][aid] = dict(status='UNREADABLE', limitation=repr(error))
        root = result['components'][CC]['path']
        manifest_path = source_path(root, 'INFINITY-MODULES.v1')
        signature_path = source_path(root, 'INFINITY-MODULES.v1.sig')
        manifest = bounded_read(manifest_path, 131072)
        signature = bounded_read(signature_path, 512)
        result.update(manifest_base64=base64.b64encode(manifest).decode('ascii'), signature_base64=base64.b64encode(signature).decode('ascii'), manifest_sha256=sha(manifest), signature_sha256=sha(signature))
        lines = manifest.decode('ascii').splitlines()
        if not lines or lines[0] != 'INFINITY-MODULES/1':
            raise ValueError('Unrecognized manifest format')
        records = []
        for line in lines[1:]:
            row = line.split('\t')
            if row[0] == 'package' and len(row) == 2:
                result['manifest_version'] = row[1]
            if row[0] != 'file':
                continue
            if len(row) != 3 or len(row[1]) != 64 or any(c not in '0123456789abcdef' for c in row[1]):
                raise ValueError('Malformed module record')
            records.append((row[2], row[1]))
        if not 1 <= len(records) <= 256 or len(set(n for n, _ in records)) != len(records):
            raise ValueError('Invalid module record count')
        allowed = set(pins['allowed_module_files'])
        for name, expected in records:
            record = dict(expected_sha256=expected)
            result['files'][name] = record
            try:
                parts = safe_relative(name)
                if name not in allowed or len(parts) < 2 or parts[0] not in OWNED:
                    raise ValueError('Unrecognized source path; file content was not read')
                root = result['components'][parts[0]]['path']
                record.update(file_hash(source_path(root, '/'.join(parts[1:])), 8*1024*1024))
                record['status'] = 'MATCH' if record['sha256'] == expected else 'MISMATCH'
            except (OSError, ValueError, KeyError) as error:
                record.update(status='UNREADABLE_OR_REFUSED', limitation=repr(error))
        result['additional_unlisted_known_sources'] = {}
        for name, expected in pins.get('known_unlisted_sources', {}).items():
            if name in result['files']:
                continue
            record = dict(expected_sha256=expected)
            result['additional_unlisted_known_sources'][name] = record
            try:
                parts = safe_relative(name)
                if name not in allowed or parts[0] not in OWNED:
                    raise ValueError('Unrecognized extra source path refused')
                root = result['components'][parts[0]]['path']
                record.update(file_hash(source_path(root, '/'.join(parts[1:])), 8*1024*1024))
                record['status'] = 'MATCH' if record['sha256'] == expected else 'MISMATCH'
            except FileNotFoundError:
                record['status'] = 'NOT_PRESENT'
            except (OSError, ValueError, KeyError) as error:
                record.update(status='UNREADABLE_OR_REFUSED', limitation=repr(error))
        for version, row in pins['modules'].items():
            if row['manifest_sha256'] == sha(manifest) and row['signature_sha256'] == sha(signature):
                result['known_verified_manifest_signature_reference'] = version
        result['signature_note'] = 'Exact reference-byte comparison only; raw manifest/signature included for original-public-key verification on the host.'
        if manifest != bounded_read(manifest_path, 131072) or signature != bounded_read(signature_path, 512):
            raise ValueError('Installed manifest/signature changed during collection')
        result['all_declared_files_match'] = all(r['status'] == 'MATCH' for r in result['files'].values())
        result['status'] = 'MODULE_METADATA_AND_HASHES_COLLECTED'
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        result['limitation'] = repr(error)
    return result


def trakt_inventory(addon_info, pins):
    result = dict(status='ACTIVE_TRAKT_UNREADABLE', files={}, unexpected_files=[], globally_atomic=False)
    try:
        identity = metadata(addon_info, TRAKT)
        result['identity'] = identity
        # Only the source-only receipt's145 names are opened, never saved data.
        baseline = pins['trakt']['1.2.8']
        expected = pins['trakt'].get(identity['version'], {})
        root = identity['path']
        source_path(root, 'addon.xml')  # Validate the active root before any enumeration.
        for name in sorted(baseline):
            record = {}
            result['files'][name] = record
            try:
                record.update(file_hash(source_path(root, name), 8*1024*1024))
                record['expected_sha256'] = expected.get(name)
                record['status'] = ('MATCH' if record['sha256'] == expected[name] else 'MISMATCH') if name in expected else 'UNKNOWN_GENERATION_HASH_COLLECTED'
            except (OSError, ValueError) as error:
                record.update(status='UNREADABLE_OR_REFUSED', limitation=repr(error))
        for parent, dirs, files in os.walk(root, followlinks=False):
            for directory in dirs:
                if Path(parent, directory).is_symlink():
                    result['unexpected_files'].append(Path(parent, directory).relative_to(root).as_posix() + '/ [symlink not followed]')
            dirs[:] = [d for d in dirs if d.casefold() not in DENIED and not Path(parent, d).is_symlink()]
            for name in files:
                if name.endswith(('.pyc', '.pyo')):
                    continue
                relative = Path(parent, name).relative_to(root).as_posix()
                if relative not in baseline:
                    result['unexpected_files'].append(relative)  # Names only; contents not read.
                if len(result['unexpected_files']) > 1000:
                    raise ValueError('Unexpected file count exceeds diagnostic bound')
        result['identity_after_collection'] = metadata(addon_info, TRAKT)
        result['identity_unchanged_during_collection'] = identity == result['identity_after_collection']
        result['all_reference_files_match'] = bool(expected) and all(r['status'] == 'MATCH' for r in result['files'].values())
        result['complete_known_tree_match'] = result['all_reference_files_match'] and not result['unexpected_files'] and result['identity_unchanged_during_collection']
        result['status'] = 'ACTIVE_TRAKT_SOURCE_HASHES_COLLECTED'
    except (OSError, ValueError, RuntimeError) as error:
        result['limitation'] = repr(error)
    return result


def collect(addon_info, pins, apk_path=None, progress=None):
    return dict(schema='INFINITY-READONLY-IDENTITY/1', diagnostic_version='1.0.0',
                status='READ_ONLY_COLLECTION_NOT_INSTALLATION_CLEARANCE',
                apk=apk_identity(apk_path, pins, progress),
                command_center=module_inventory(addon_info, pins),
                trakt=trakt_inventory(addon_info, pins),
                globally_atomic=False, account_settings_or_tokens_read=False,
                databases_opened=False, existing_addons_modified=False,
                permission_changes=False, APK_or_correction_installed=False,
                three_corrections_complete=False)
