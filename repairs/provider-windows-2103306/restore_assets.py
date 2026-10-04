#!/usr/bin/env python3
"""Recover original PNG timestamp bytes, never accept a different locked hash.

The inherited ImageMagick recipe emits wall-clock PNG metadata. Reconstructing
that metadata is safe only when the entire resulting file matches the original
SHA-256 in the authenticated locked-engine receipt. Pixel/compression chunks are
never decoded, re-encoded, replaced, or exempted from preservation.
"""
import argparse
from datetime import datetime, timedelta, timezone
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import struct
import zlib

HERE = Path(__file__).resolve().parent
RECEIPT_SHA = 'b870052cc344b8d419ed8fb29eb5dbc019fdbc9a528219a576576dcc4332b82b'
MAP_SHA = 'dc3cd4dce5abcfe7bb4b4a316a8b6a3ce9f69f308546ffe721e4d7b6787ebd1c'
# Original native run 37189319805: started 08:33:39Z; its recorded parent
# source snapshot existed by 08:36Z. This bounded range is not an acceptance
# exception: recovery succeeds only on an exact original full-file hash.
START = datetime(2026, 10, 4, 8, 33, tzinfo=timezone.utc)
SECONDS = 240
# ImageMagick records the canvas creation time in date:create/date:modify,
# while tIME is written after rendering. The captured splash PNGs differ by
# 5-6 seconds within a single file. Search only up to 60 seconds of render time;
# the complete original hash remains the sole acceptance condition.
RENDER_SECONDS = 60
SIGNATURE = b'\x89PNG\r\n\x1a\n'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def chunks(data):
    if not data.startswith(SIGNATURE):
        raise ValueError('Not a PNG')
    output = []
    offset = len(SIGNATURE)
    while offset < len(data):
        if len(data) - offset < 12:
            raise ValueError('Truncated PNG chunk')
        length = struct.unpack('>I', data[offset:offset + 4])[0]
        end = offset + length + 12
        if end > len(data):
            raise ValueError('Invalid PNG chunk length')
        kind = data[offset + 4:offset + 8]
        value = data[offset + 8:end - 4]
        crc = struct.unpack('>I', data[end - 4:end])[0]
        if zlib.crc32(kind + value) & 0xffffffff != crc:
            raise ValueError('Invalid PNG CRC')
        output.append((kind, value))
        offset = end
    if not output or output[0][0] != b'IHDR' or output[-1] != (b'IEND', b''):
        raise ValueError('Invalid PNG structure')
    return output


def timestamp_chunk(kind, value):
    return kind == b'tIME' or (kind == b'tEXt' and
        value.partition(b'\0')[0] in (b'date:create', b'date:modify'))


def fixed_chunks(data):
    return [(kind, value) for kind, value in chunks(data)
            if not timestamp_chunk(kind, value)]


def at_time(parts, moment, text_moment=None):
    output = bytearray(SIGNATURE)
    text_date = (text_moment or moment).isoformat(timespec='seconds').encode('ascii')
    for kind, value in parts:
        if kind == b'tIME':
            if len(value) != 7:
                raise ValueError('Invalid PNG timestamp')
            value = struct.pack('>H5B', moment.year, moment.month, moment.day,
                                moment.hour, moment.minute, moment.second)
        elif timestamp_chunk(kind, value):
            value = value.partition(b'\0')[0] + b'\0' + text_date
        output.extend(struct.pack('>I', len(value)) + kind + value +
                      struct.pack('>I', zlib.crc32(kind + value) & 0xffffffff))
    return bytes(output)


def recover(data, expected, start=START, seconds=SECONDS):
    if sha(data) == expected:
        return data, None
    parts = chunks(data)
    if not any(timestamp_chunk(kind, value) for kind, value in parts):
        raise ValueError('Different PNG without recoverable timestamp metadata')
    for second in range(seconds):
        moment = start + timedelta(seconds=second)
        candidate = at_time(parts, moment)
        if sha(candidate) == expected:
            if fixed_chunks(data) != fixed_chunks(candidate):
                raise ValueError('Non-timestamp bytes changed')
            return candidate, moment.isoformat()
    # Avoid hashing the large, identical IDAT payload for every possible text
    # timestamp. Hash the prefix once per tIME value, then copy its digest state
    # for each short metadata suffix. No chunk is omitted from the final hash.
    text_index = next((i for i, (kind, value) in enumerate(parts)
                       if kind == b'tEXt' and timestamp_chunk(kind, value)), None)
    if text_index is not None and any(kind == b'tIME' for kind, _ in parts):
        for second in range(seconds):
            moment = start + timedelta(seconds=second)
            prefix = at_time(parts[:text_index], moment)
            prefix_hash = hashlib.sha256(prefix)
            for offset in range(1, min(RENDER_SECONDS, second) + 1):
                created = moment - timedelta(seconds=offset)
                suffix = at_time(parts[text_index:], moment, created)[len(SIGNATURE):]
                digest = prefix_hash.copy()
                digest.update(suffix)
                if digest.hexdigest() == expected:
                    candidate = prefix + suffix
                    if sha(candidate) != expected or fixed_chunks(data) != fixed_chunks(candidate):
                        raise ValueError('Exact timestamp-only verification failed')
                    return candidate, {'tIME': moment.isoformat(),
                                       'text': created.isoformat()}
    raise ValueError('No exact locked PNG hash match; no replacement accepted')


def locked_map(receipt):
    payload = receipt.read_bytes()
    if receipt.suffix == '.gz':
        payload = gzip.decompress(payload)
    if sha(payload) != RECEIPT_SHA:
        raise ValueError('Unauthenticated locked native receipt')
    mapping = json.loads(payload)['after']
    encoded = json.dumps(mapping, sort_keys=True, separators=(',', ':')).encode()
    if len(mapping) != 9372 or sha(encoded) != MAP_SHA:
        raise ValueError('Unauthenticated complete locked source map')
    return mapping


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--receipt', type=Path,
                        default=HERE / 'fixtures/locked-3305-source-manifest.json.gz')
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    mapping = locked_map(args.receipt)
    args.evidence.mkdir(parents=True, exist_ok=True)
    changes, diagnostics, errors = {}, [], []
    for name, expected in sorted(mapping.items()):
        if not name.endswith('.png'):
            continue
        file = args.source / name
        if not file.is_file():
            errors.append({'file': name, 'error': 'Missing locked PNG'})
            continue
        data = file.read_bytes()
        if sha(data) == expected:
            continue
        entry = {'file': name, 'before': sha(data), 'expected': expected}
        try:
            entry['chunks'] = [(kind.decode('ascii'), len(value))
                               for kind, value in chunks(data)]
            replacement, moment = recover(data, expected)
            entry.update(recovered_at=moment, after=sha(replacement),
                         non_timestamp_bytes_identical=True)
            changes[file] = replacement
        except ValueError as error:
            entry['error'] = str(error)
            errors.append(entry)
            saved = args.evidence / 'unmatched-assets' / name
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(file, saved)
        diagnostics.append(entry)
    report = {'locked_receipt_sha256': RECEIPT_SHA, 'locked_map_sha256': MAP_SHA,
              'complete_source_guard_unchanged': True,
              'recovered_files': len(changes), 'errors': errors, 'files': diagnostics}
    (args.evidence / 'png-recovery.json').write_text(json.dumps(report, indent=2) + '\n')
    if errors:
        raise ValueError('PNG recovery refused before any write: ' +
                         json.dumps([e['file'] for e in errors]))
    # Validate the entire recovery batch before touching any inherited file.
    for file, replacement in changes.items():
        file.write_bytes(replacement)
    for name, expected in mapping.items():
        if name.endswith('.png') and sha((args.source / name).read_bytes()) != expected:
            raise ValueError('Locked PNG readback failed: ' + name)
    print('PASS exact locked PNG recovery:', len(changes),
          'files; complete 9372-file guard remains unchanged')


if __name__ == '__main__':
    main()
