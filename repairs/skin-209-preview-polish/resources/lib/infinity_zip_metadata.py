"""Bounded, read-only Kodi ZIP metadata. No extraction, imports or archive execution."""
from dataclasses import dataclass, field
import hashlib
import os
from pathlib import PurePosixPath
import re
import stat
import struct
import time
import unicodedata
import urllib.parse
import xml.etree.ElementTree as ET
import zlib

MAX_ENTRIES = 8192
MAX_DIRECTORY = 2 * 1024 * 1024
MAX_XML = 256 * 1024
MAX_ICON = 512 * 1024
MAX_READ = MAX_DIRECTORY + MAX_XML + MAX_ICON + 256 * 1024
MAX_PIXELS = 1024 * 1024
TIME_BUDGET = 4.0


class PreviewError(Exception):
    pass


def clean_text(value, limit=4096):
    text = ''.join(c for c in str(value or '') if c in '\n\t' or ord(c) >= 32)
    text = text.replace('\t', ' ').replace('[', '［').replace(']', '］')
    return text[:limit]


def display_location(path):
    try:
        parts = urllib.parse.urlsplit(path)
        if parts.scheme and parts.netloc:
            host = parts.hostname or ''
            if parts.port:
                host += ':' + str(parts.port)
            # Credentials, query tokens and fragments never become preview text.
            path = urllib.parse.urlunsplit((parts.scheme, host, parts.path, '', ''))
    except ValueError:
        path = 'Location unavailable'
    return clean_text(path, 512)


def safe_member(name):
    if (not name or len(name) > 4096 or '\\' in name or '\x00' in name or
            any(ord(c) < 32 for c in name) or name.startswith('/') or ':' in name):
        raise PreviewError('This ZIP contains unsafe archive paths.')
    parts = name.rstrip('/').split('/')
    if any(part in ('', '.', '..') for part in parts):
        raise PreviewError('This ZIP contains unsafe archive paths.')
    return unicodedata.normalize('NFC', name).casefold()


@dataclass
class Metadata:
    path: str
    file_name: str
    kind: str = 'File'
    name: str = ''
    addon_id: str = ''
    version: str = ''
    author: str = ''
    description: str = ''
    addon_type: str = ''
    size: int = None
    icon: str = ''
    compatible: bool = False
    status: str = ''
    fingerprint: tuple = field(default_factory=tuple)
    metadata_signature: str = ''
    bytes_read: int = 0
    entries_seen: int = 0


@dataclass(frozen=True)
class Entry:
    name: str
    flags: int
    method: int
    crc: int
    packed: int
    size: int
    offset: int


class Reader:
    def __init__(self, file, size, cancel=None):
        self.file = file
        self.size = size
        self.cancel = cancel or (lambda: False)
        self.deadline = time.monotonic() + TIME_BUDGET
        self.bytes_read = 0

    def check(self):
        if self.cancel():
            raise PreviewError('Preview cancelled.')
        if time.monotonic() > self.deadline:
            raise PreviewError('This archive took too long to preview.')

    def read(self, offset, size):
        self.check()
        if offset < 0 or size < 0 or offset + size > self.size or self.bytes_read + size > MAX_READ:
            raise PreviewError('This ZIP exceeds the metadata preview limits.')
        self.file.seek(offset)
        chunks = []
        remaining = size
        while remaining:
            self.check()
            chunk = self.file.read(min(remaining, 65536))
            if not chunk:
                raise PreviewError('This ZIP is incomplete.')
            chunks.append(chunk)
            remaining -= len(chunk)
            self.bytes_read += len(chunk)
        return b''.join(chunks)


def directory(reader):
    if reader.size < 22:
        raise PreviewError('This is not a readable ZIP archive.')
    tail_offset = max(0, reader.size - 65557)
    tail = reader.read(tail_offset, reader.size - tail_offset)
    index = len(tail)
    record = None
    while True:
        index = tail.rfind(b'PK\x05\x06', 0, index)
        if index < 0:
            break
        if index + 22 <= len(tail):
            fields = struct.unpack_from('<4s4H2IH', tail, index)
            if index + 22 + fields[-1] == len(tail):
                record = fields
                break
    if record is None:
        raise PreviewError('This is not a readable ZIP archive.')
    _, disk, directory_disk, on_disk, count, length, offset, _ = record
    if disk or directory_disk or on_disk != count or count == 65535 or length == 0xffffffff or offset == 0xffffffff:
        raise PreviewError('Split and ZIP64 archives are not supported by metadata preview.')
    if count > MAX_ENTRIES or length > MAX_DIRECTORY:
        raise PreviewError('This ZIP exceeds the metadata preview limits.')
    end = tail_offset + index
    if offset + length != end:
        raise PreviewError('This ZIP has an invalid directory.')
    data = reader.read(offset, length)
    entries = []
    names = set()
    position = 0
    for _ in range(count):
        reader.check()
        if position + 46 > len(data) or data[position:position + 4] != b'PK\x01\x02':
            raise PreviewError('This ZIP has an invalid directory.')
        values = struct.unpack_from('<4s6H3I5H2I', data, position)
        _, made, _, flags, method, _, _, crc, packed, size, name_len, extra_len, comment_len, entry_disk, _, attr, local = values
        finish = position + 46 + name_len + extra_len + comment_len
        if finish > len(data) or entry_disk or local == 0xffffffff or packed == 0xffffffff or size == 0xffffffff:
            raise PreviewError('This ZIP has invalid or unsupported entries.')
        raw = data[position + 46:position + 46 + name_len]
        try:
            name = raw.decode('utf-8' if flags & 0x800 else 'cp437')
        except UnicodeDecodeError:
            raise PreviewError('This ZIP has invalid archive names.') from None
        normalized = safe_member(name)
        if normalized in names:
            raise PreviewError('This ZIP contains ambiguous duplicate paths.')
        names.add(normalized)
        if flags & 1 or stat.S_ISLNK(attr >> 16):
            raise PreviewError('Encrypted or linked archive entries cannot be previewed.')
        if local + 30 > offset:
            raise PreviewError('This ZIP has invalid entry offsets.')
        entries.append(Entry(name, flags, method, crc, packed, size, local))
        position = finish
    if position != len(data):
        raise PreviewError('This ZIP has an invalid directory.')
    return entries, offset, hashlib.sha256(data).hexdigest()


def member_bytes(reader, entry, directory_offset, limit):
    if entry.size > limit or entry.packed > limit or entry.method not in (0, 8):
        raise PreviewError('This metadata entry exceeds the preview limits.')
    header = reader.read(entry.offset, 30)
    fields = struct.unpack('<4s5H3I2H', header)
    if fields[0] != b'PK\x03\x04' or fields[2] != entry.flags or fields[3] != entry.method:
        raise PreviewError('This ZIP has inconsistent metadata headers.')
    if not entry.flags & 8 and fields[6:9] != (entry.crc, entry.packed, entry.size):
        raise PreviewError('This ZIP has inconsistent metadata sizes.')
    name_len, extra_len = fields[-2:]
    raw_name = reader.read(entry.offset + 30, name_len)
    encoding = 'utf-8' if entry.flags & 0x800 else 'cp437'
    if raw_name.decode(encoding) != entry.name:
        raise PreviewError('This ZIP has inconsistent metadata names.')
    offset = entry.offset + 30 + name_len + extra_len
    if offset + entry.packed > directory_offset:
        raise PreviewError('This ZIP has overlapping metadata.')
    packed = reader.read(offset, entry.packed)
    if entry.method == 0:
        data = packed
    else:
        decoder = zlib.decompressobj(-15)
        try:
            data = decoder.decompress(packed, limit + 1)
        except zlib.error:
            raise PreviewError('This ZIP has damaged metadata.') from None
        if not decoder.eof or decoder.unconsumed_tail or decoder.unused_data:
            raise PreviewError('This ZIP has oversized or damaged metadata.')
    if len(data) != entry.size or len(data) > limit or zlib.crc32(data) & 0xffffffff != entry.crc:
        raise PreviewError('This ZIP has damaged metadata.')
    return data


def text(element, limit=4096):
    return clean_text(''.join(element.itertext()) if element is not None else '', limit)


def localized(elements):
    items = list(elements)
    for language in ('en_GB', 'en_US', 'en', None):
        for item in items:
            if item.get('lang') == language:
                return item
    return items[0] if items else None


def image_dimensions(data):
    if data.startswith(b'\x89PNG\r\n\x1a\n') and len(data) >= 33 and data[12:16] == b'IHDR':
        position = 8
        idat = False
        dimensions = struct.unpack('>II', data[16:24])
        while position + 12 <= len(data):
            length = struct.unpack_from('>I', data, position)[0]
            end = position + 12 + length
            if end > len(data):
                return 0, 0
            kind = data[position + 4:position + 8]
            crc = struct.unpack_from('>I', data, end - 4)[0]
            if zlib.crc32(data[position + 4:end - 4]) & 0xffffffff != crc:
                return 0, 0
            if position == 8 and length != 13:
                return 0, 0
            if kind == b'IDAT' and length:
                idat = True
            if kind == b'IEND':
                return dimensions if idat and length == 0 and end == len(data) else (0, 0)
            position = end
        return 0, 0
    if not data.startswith(b'\xff\xd8'):
        return 0, 0
    if not data.endswith(b'\xff\xd9'):
        return 0, 0
    position = 2
    while position + 4 <= len(data):
        if data[position] != 0xff:
            return 0, 0
        while position < len(data) and data[position] == 0xff:
            position += 1
        if position >= len(data):
            break
        marker = data[position]
        position += 1
        if marker in (0xd9, 0xda):
            break
        if marker == 0x01 or 0xd0 <= marker <= 0xd7:
            continue
        if position + 2 > len(data):
            break
        length = struct.unpack_from('>H', data, position)[0]
        if length < 2 or position + length > len(data):
            break
        if marker in (0xc0, 0xc1, 0xc2) and length >= 7:
            height, width = struct.unpack_from('>HH', data, position + 3)
            return width, height
        position += length
    return 0, 0


def local_path(path):
    parsed = urllib.parse.urlsplit(path)
    if not parsed.scheme:
        return path
    if parsed.scheme == 'file' and parsed.netloc in ('', 'localhost'):
        return urllib.parse.unquote(parsed.path)
    return None


def inspect(path, folder=False, label='', size_hint=None, cancel=None):
    file_name = label or os.path.basename(path.rstrip('/')) or path
    result = Metadata(path=display_location(path), file_name=clean_text(file_name, 256), name=clean_text(file_name, 256))
    result.kind = 'Folder' if folder else ('ZIP archive' if path.lower().endswith('.zip') else 'File')
    result.size = size_hint if isinstance(size_hint, int) and size_hint >= 0 and not folder else None
    local = local_path(path)
    if local is None:
        result.status = 'Metadata preview is unavailable for this location. Normal browsing remains available.'
        return result
    reader = None
    try:
        info = os.stat(local)
        result.fingerprint = (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)
        if folder or stat.S_ISDIR(info.st_mode):
            result.kind = 'Folder'
            result.size = None
            result.status = 'Open this folder with a single tap in the file picker.'
            return result
        if not stat.S_ISREG(info.st_mode):
            result.status = 'This location does not support file preview.'
            return result
        result.size = info.st_size
        if result.kind != 'ZIP archive':
            result.status = 'File information only. This file is not a Kodi add-on ZIP.'
            return result
        with open(local, 'rb') as file:
            opened = os.fstat(file.fileno())
            if (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) != result.fingerprint:
                raise PreviewError('This file changed. Open the preview again.')
            reader = Reader(file, info.st_size, cancel)
            entries, directory_offset, directory_digest = directory(reader)
            result.entries_seen = len(entries)
            descriptors = [item for item in entries if len(PurePosixPath(item.name).parts) == 2 and
                           PurePosixPath(item.name).name == 'addon.xml' and not item.name.endswith('/')]
            if len(descriptors) != 1:
                raise PreviewError('This ZIP is not a single compatible Kodi add-on.')
            descriptor = descriptors[0]
            data = member_bytes(reader, descriptor, directory_offset, MAX_XML)
            if b'\x00' in data or b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
                raise PreviewError('This ZIP has unsupported XML metadata.')
            try:
                addon = ET.fromstring(data)
            except (ET.ParseError, ValueError):
                raise PreviewError('This ZIP has invalid add-on metadata.') from None
            addon_id = addon.get('id', '')
            version = addon.get('version', '')
            root = descriptor.name.split('/')[0]
            if (addon.tag != 'addon' or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}', addon_id) or
                    root != addon_id or not version or len(version) > 128 or not addon.get('name') or
                    not addon.findall('extension')):
                raise PreviewError('This ZIP has incompatible add-on metadata.')
            if any(item.name.rstrip('/') != root and not item.name.startswith(root + '/') for item in entries):
                raise PreviewError('This ZIP contains files outside its add-on folder.')
            result.name = clean_text(addon.get('name'), 256)
            result.addon_id = addon_id
            result.version = clean_text(version, 128)
            result.author = clean_text(addon.get('provider-name', ''), 256)
            extensions = addon.findall('extension')
            points = [element.get('point', '') for element in extensions if element.get('point') != 'xbmc.addon.metadata']
            types = {'xbmc.gui.skin': 'Skin', 'xbmc.python.script': 'Script', 'xbmc.python.pluginsource': 'Provider / plugin',
                     'xbmc.service': 'Service', 'xbmc.python.module': 'Python module', 'xbmc.addon.repository': 'Repository',
                     'kodi.pvrclient': 'PVR client', 'kodi.resource': 'Resource', 'xbmc.ui.screensaver': 'Screensaver'}
            result.addon_type = clean_text(', '.join(dict.fromkeys(types.get(point, point) for point in points)) or 'Add-on', 256)
            metadata = next((element for element in extensions if element.get('point') == 'xbmc.addon.metadata'), None)
            if metadata is not None:
                result.description = text(localized(metadata.findall('description')), 12000) or text(localized(metadata.findall('summary')), 12000)
                icon_name = text(metadata.find('assets/icon'), 4096) or text(metadata.find('icon'), 4096) or 'icon.png'
            else:
                icon_name = 'icon.png'
            try:
                safe_member(icon_name)
                icon_entry = next((item for item in entries if item.name == root + '/' + icon_name), None)
                if icon_entry is not None:
                    icon = member_bytes(reader, icon_entry, directory_offset, MAX_ICON)
                    width, height = image_dimensions(icon)
                    if width > 0 and height > 0 and width <= 1024 and height <= 1024 and width * height <= MAX_PIXELS:
                        # Kodi reads this one validated, bounded entry directly; nothing is extracted.
                        result.icon = 'zip://' + urllib.parse.quote(os.path.abspath(local), safe='') + '/' + urllib.parse.quote(icon_entry.name, safe='/')
            except (PreviewError, UnicodeError):
                result.icon = ''
            current = os.fstat(file.fileno())
            if (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns) != result.fingerprint:
                raise PreviewError('This file changed. Open the preview again.')
            result.metadata_signature = hashlib.sha256(directory_digest.encode() + data).hexdigest()
            result.compatible = True
            result.status = 'Preview only. Choose Install to continue through Kodi.'
    except PreviewError as error:
        result.compatible = False
        result.status = str(error)
    except (OSError, UnicodeError, ValueError, struct.error, OverflowError):
        result.compatible = False
        result.status = 'This file could not be previewed safely. Normal browsing remains available.'
    finally:
        result.bytes_read = reader.bytes_read if reader is not None else 0
    return result


def same_metadata(original, current):
    return (original.compatible and current.compatible and bool(original.metadata_signature) and
            original.fingerprint == current.fingerprint and original.metadata_signature == current.metadata_signature)
