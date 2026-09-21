"""Restore exact locked source PNG bytes after proving timestamp-only drift.

This is not a PNG/pixel/source hash exemption. Replayed ImageMagick outputs have
wall-clock metadata; every other encoded chunk must remain byte-identical. Only
the 35 observed legacy paths are eligible, and the full SHA-pinned source export
provides replacement bytes. The normal 226-file and protected-member gates still
run after restoration. No APK resource payload is changed by this operation.
"""
from pathlib import Path
import datetime
import hashlib
import json
import re
import struct
import zipfile
import zlib

PARENT_SOURCE = '82546500a4e3b54a0df69ada48c313a7ac4d164798b7d60323e7aa43992b5c95'
TIMESTAMP_PNG_PATHS = frozenset('''
media/applaunch_screen.png
media/banner.png
media/icon120x120.png
media/icon16x16.png
media/icon256x256.png
media/icon32x32.png
media/icon48x48.png
media/icon80x80.png
media/infinity_launch_dark.png
media/vendor_icon.png
media/vendor_logo.png
tools/android/packaging/media/drawable-hdpi/ic_launcher.png
tools/android/packaging/media/drawable-ldpi/ic_launcher.png
tools/android/packaging/media/drawable-mdpi/ic_launcher.png
tools/android/packaging/media/drawable-xhdpi/banner.png
tools/android/packaging/media/drawable-xhdpi/ic_launcher.png
tools/android/packaging/media/drawable-xxhdpi/ic_launcher.png
tools/android/packaging/media/drawable-xxxhdpi/ic_launcher.png
tools/android/packaging/xbmc/res/drawable/notif_icon.png
tools/android/packaging/xbmc/res/drawable-night/applaunch_screen.png
tools/android/packaging/xbmc/res/drawable-night-xxxhdpi/applaunch_screen.png
tools/android/packaging/xbmc/res/drawable-nodpi/infinity_icon_background_bitmap.png
tools/android/packaging/xbmc/res/drawable-nodpi/infinity_icon_foreground.png
tools/android/packaging/xbmc/res/drawable-nodpi/infinity_icon_monochrome.png
tools/android/packaging/xbmc/res/drawable-nodpi/infinity_splash_icon.png
tools/android/packaging/xbmc/res/mipmap-hdpi/ic_launcher.png
tools/android/packaging/xbmc/res/mipmap-hdpi/ic_launcher_round.png
tools/android/packaging/xbmc/res/mipmap-mdpi/ic_launcher.png
tools/android/packaging/xbmc/res/mipmap-mdpi/ic_launcher_round.png
tools/android/packaging/xbmc/res/mipmap-xhdpi/ic_launcher.png
tools/android/packaging/xbmc/res/mipmap-xhdpi/ic_launcher_round.png
tools/android/packaging/xbmc/res/mipmap-xxhdpi/ic_launcher.png
tools/android/packaging/xbmc/res/mipmap-xxhdpi/ic_launcher_round.png
tools/android/packaging/xbmc/res/mipmap-xxxhdpi/ic_launcher.png
tools/android/packaging/xbmc/res/mipmap-xxxhdpi/ic_launcher_round.png
'''.split())

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def png_chunks(data):
    require(data.startswith(b'\x89PNG\r\n\x1a\n'), 'Invalid PNG signature')
    offset, result = 8, []
    while offset < len(data):
        require(offset + 12 <= len(data), 'Truncated PNG chunk')
        size = struct.unpack('>I', data[offset:offset + 4])[0]
        end = offset + size + 12
        require(end <= len(data), 'Truncated PNG payload')
        kind = data[offset + 4:offset + 8]
        value = data[offset + 8:end - 4]
        crc = struct.unpack('>I', data[end - 4:end])[0]
        require(zlib.crc32(kind + value) & 0xffffffff == crc, 'PNG CRC mismatch')
        result.append((kind, value, data[offset:end]))
        offset = end
        if kind == b'IEND':
            require(size == 0 and offset == len(data), 'PNG trailing data')
            break
    require(result and result[0][0] == b'IHDR' and len(result[0][1]) == 13, 'Invalid PNG IHDR')
    require(result[-1][0] == b'IEND', 'Missing PNG IEND')
    require(sum(kind == b'IHDR' for kind, _, _ in result) == 1, 'Duplicate PNG IHDR')
    return result

def timestamp_key(kind, value):
    if kind == b'tIME':
        require(len(value) == 7, 'Invalid PNG timestamp')
        year, month, day, hour, minute, second = struct.unpack('>HBBBBB', value)
        try:
            datetime.datetime(year, month, day, hour, minute, min(second, 59))
        except ValueError as error:
            raise RuntimeError('Invalid PNG timestamp') from error
        require(second <= 60, 'Invalid PNG timestamp second')
        return 'tIME'
    if kind == b'tEXt' and b'\0' in value:
        key, text = value.split(b'\0', 1)
        if key in (b'date:create', b'date:modify'):
            require(re.fullmatch(rb'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})', text) is not None,
                    'Invalid PNG date text')
            try:
                datetime.datetime.fromisoformat(text.decode().replace('Z', '+00:00'))
            except ValueError as error:
                raise RuntimeError('Invalid PNG date text') from error
            return key.decode()
    return None

def prove_timestamp_only(path, current, canonical):
    require(path in TIMESTAMP_PNG_PATHS, 'Unapproved timestamp source: ' + path)
    left, right = png_chunks(current), png_chunks(canonical)
    require(len(left) == len(right), 'PNG chunk inventory changed: ' + path)
    changes = []
    for (ka, va, rawa), (kb, vb, rawb) in zip(left, right):
        require(ka == kb, 'PNG chunk order/type changed: ' + path)
        if rawa == rawb:
            continue
        ta, tb = timestamp_key(ka, va), timestamp_key(kb, vb)
        require(ta is not None and ta == tb, 'PNG non-timestamp bytes changed: ' + path)
        changes.append(ta)
    require(changes or current == canonical, 'Unexplained PNG drift: ' + path)
    return changes

def canonicalize(source, export, inventory, receipt, report):
    source, export, receipt, report = map(Path, (source, export, receipt, report))
    require(digest(export.read_bytes()) == PARENT_SOURCE, 'Wrong locked source archive')
    require(len(TIMESTAMP_PNG_PATHS) == 35, 'Timestamp path allowlist drift')
    data = json.loads(receipt.read_text())
    require(set(data['files']) <= set(inventory), 'Receipt contains unreviewed source identity')
    planned, rows = [], []
    with zipfile.ZipFile(export) as archive:
        require(len(archive.namelist()) == len(set(archive.namelist())), 'Duplicate source archive member')
        require(set(archive.namelist()) == set(inventory), 'Locked source inventory differs')
        # Validate EVERY source/receipt first. A later unapproved mismatch must
        # never leave an earlier source restored in a partially changed tree.
        for name, expected in inventory.items():
            target = source / name
            require(not target.is_symlink() and target.is_file(), 'Source path missing/symlink: ' + name)
            require(Path(name).as_posix() == name and '..' not in Path(name).parts and not Path(name).is_absolute(),
                    'Unsafe source identity: ' + name)
            require(target.resolve().is_relative_to(source.resolve()), 'Source path escapes tree: ' + name)
            canonical, current = archive.read(name), target.read_bytes()
            require(digest(canonical) == expected, 'Canonical source hash differs: ' + name)
            before = digest(current)
            if name in data['files']:
                require(data['files'][name]['after'] == before, 'Original source receipt drift: ' + name)
            if before == expected:
                continue
            changes = prove_timestamp_only(name, current, canonical)
            planned.append((target, canonical))
            row = dict(path=name, before_sha256=before, after_sha256=expected, timestamp_fields=changes,
                       remaining_chunks_byte_identical=True, receipt_updated=name in data['files'])
            rows.append(row)
        for target, canonical in planned:
            target.write_bytes(canonical)
        for row in rows:
            if row['receipt_updated']:
                data['files'][row['path']]['after'] = row['after_sha256']
        if any(row['receipt_updated'] for row in rows):
            receipt.write_text(json.dumps(data, indent=2) + '\n')
    for name, expected in inventory.items():
        require(digest((source / name).read_bytes()) == expected, 'Canonical parent source drift: ' + name)
    for name, row in data['files'].items():
        require(digest((source / name).read_bytes()) == row['after'], 'Restored source receipt drift: ' + name)
    report.write_text(json.dumps(dict(parent_source_sha256=PARENT_SOURCE,
        normalization='Restore pinned member bytes only after CRC and timestamp-only chunk proof',
        canonical_source_files_verified=len(inventory), restored=rows,
        original_receipt_changed=any(row['receipt_updated'] for row in rows)), indent=2) + '\n')
    return rows
