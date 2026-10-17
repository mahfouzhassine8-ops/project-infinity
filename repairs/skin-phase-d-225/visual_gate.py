"""Phase D PNG visibility gate: reject blank native GUI captures, no Pillow dependency.

This validates visual evidence only. It does not establish visual design parity,
physical Fold behavior, player correctness, shutdown safety or source fidelity.
"""
import json
import struct
import zlib
from pathlib import Path

SIGNATURE = b'\x89PNG\r\n\x1a\n'
PNG_HEADER = struct.Struct('>IIBBBBB')
MIN_VISIBLE = 0.001  # UI captures must contain at least some visible pixels.


def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    return a if pa <= pb and pa <= pc else b if pb <= pc else c


def inspect_png(path):
    """Measure visible RGB samples; fail closed on malformed/unsupported PNGs."""
    raw = Path(path).read_bytes()
    if not raw.startswith(SIGNATURE):
        raise ValueError('invalid PNG signature')
    offset = len(SIGNATURE)
    chunks = []
    shape = None
    saw_end = False
    while offset + 12 <= len(raw):
        size = struct.unpack_from('>I', raw, offset)[0]
        end = offset + 12 + size
        if end > len(raw):
            raise ValueError('truncated PNG chunk')
        kind = raw[offset + 4: offset + 8]
        data = raw[offset + 8: offset + 8 + size]
        expected = struct.unpack_from('>I', raw, offset + 8 + size)[0]
        if zlib.crc32(kind + data) & 0xffffffff != expected:
            raise ValueError('PNG chunk CRC mismatch')
        if kind == b'IHDR':
            if shape is not None or len(data) != 13:
                raise ValueError('invalid IHDR')
            shape = PNG_HEADER.unpack(data)
        elif kind == b'IDAT':
            chunks.append(data)
        elif kind == b'IEND':
            saw_end = True
            break
        offset = end
    if not saw_end or not chunks or shape is None:
        raise ValueError('incomplete PNG')
    width, height, depth, color, compression, filtering, interlace = shape
    if depth != 8 or color not in (2, 6) or compression or filtering or interlace:
        raise ValueError('unsupported PNG pixel encoding; cannot certify screenshot')
    if not 0 < width <= 8192 or not 0 < height <= 8192:
        raise ValueError('invalid screenshot dimensions')
    bpp = 4 if color == 6 else 3
    stride = width * bpp
    data = zlib.decompress(b''.join(chunks))
    if len(data) != height * (stride + 1):
        raise ValueError('PNG decompressed byte count mismatch')
    before = bytearray(stride)
    position = 0
    bright = total = 0
    for y in range(height):
        fil = data[position]
        row = bytearray(data[position + 1:position + 1 + stride])
        position += stride + 1
        if fil == 1:
            for i in range(bpp, stride):
                row[i] = (row[i] + row[i-bpp]) & 255
        elif fil == 2:
            for i in range(stride):
                row[i] = (row[i] + before[i]) & 255
        elif fil == 3:
            for i in range(stride):
                row[i] = (row[i] + ((row[i-bpp] if i >= bpp else 0) + before[i]) // 2) & 255
        elif fil == 4:
            for i in range(stride):
                row[i] = (row[i] + _paeth(row[i-bpp] if i >= bpp else 0, before[i], before[i-bpp] if i >= bpp else 0)) & 255
        elif fil != 0:
            raise ValueError('unsupported PNG row filter')
        if y % 12 == 0:
            for x in range(0, width, 12):
                i = x * bpp
                total += 1
                if row[i] > 24 or row[i+1] > 24 or row[i+2] > 24:
                    bright += 1
        before = row
    fraction = bright / total if total else 0
    return dict(width=width, height=height, nonblack_samples=bright,
                sampled_pixels=total, visible_fraction=round(fraction, 6),
                visibly_nonblank=fraction >= MIN_VISIBLE)


def inspect_session(directory, result):
    """Require all expected per-theme screens to have real nonblack pixels."""
    directory = Path(directory)
    screens = result.get('screens', [])
    expected = {theme + '-' + name for theme in ('light', 'dark', 'oled')
                for name in ('home', 'browse', 'settings', 'settings-category',
                             'command', 'health', 'system', 'navigation', 'audio',
                             'speed', 'display', 'palette', 'addons', 'select')}
    observed = [s.get('name') for s in screens]
    findings = []
    failures = []
    if set(observed) != expected or len(observed) != len(expected):
        failures.append('missing or duplicate theme/screen captures')
    for item in screens:
        name = item.get('name', '<unknown>')
        fname = item.get('screenshot')
        path = directory / str(fname)
        try:
            if not fname or Path(fname).name != fname or not path.is_file():
                raise ValueError('missing or invalid screenshot file')
            metric = inspect_png(path)
            if not metric['visibly_nonblank']:
                failures.append(name + ': fully blank or nearly blank PNG')
            findings.append(dict(name=name, screenshot=fname, **metric))
        except Exception as exc:
            failures.append(name + ': ' + str(exc))
            findings.append(dict(name=name, screenshot=fname, error=str(exc)))
    return dict(visual_evidence_passed=not failures, checked=len(findings),
                expected=len(expected), failures=failures, screenshots=findings,
                physical_fold=False, scope='pixel nonblank + completeness only; no visual design acceptance')
