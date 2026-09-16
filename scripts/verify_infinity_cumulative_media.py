#!/usr/bin/env python3
"""Static presence gate for a cumulative Infinity responsive-v5 + media APK.

Accepts an APK or an Actions ZIP containing exactly one APK. Does not install,
modify, sign or execute it. A pass is NOT Audio Eraser eligibility or runtime proof.
Uses only Python's standard library.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import struct
import sys
import zipfile

REQUIRED_CLASSES = {
    'platform_hook_api': 'Lcom/projectinfinity/kodi/InfinityPlatformHooks;',
    'system_media_hook': 'Lcom/projectinfinity/kodi/InfinitySystemMediaHook;',
    'kodi_media_session': 'Lcom/projectinfinity/kodi/XBMCMediaSession;',
}
REQUIRED_NATIVE = (
    'Infinity.NativeDeviceMode', 'Infinity.NativeWidthDp',
    'Infinity.NativeHeightDp', 'Infinity.NativeDisplayRevision',
)
MAX_APK = 512 * 1024 * 1024


def dex_classes(data: bytes) -> set[str]:
    """Read class definitions, not arbitrary class-name substrings."""
    if len(data) < 112 or data[:4] != b'dex\n':
        raise ValueError('Not a standard DEX file')
    if struct.unpack_from('<I', data, 32)[0] != len(data):
        raise ValueError('DEX file size mismatch')
    if struct.unpack_from('<I', data, 40)[0] != 0x12345678:
        raise ValueError('Unexpected DEX byte order')

    def u32(pos: int) -> int:
        if not 0 <= pos <= len(data) - 4:
            raise ValueError('DEX offset outside file')
        return struct.unpack_from('<I', data, pos)[0]

    def table(pos: int, stride: int) -> tuple[int, int]:
        count, off = u32(pos), u32(pos + 4)
        if off > len(data) or count > (len(data) - off) // stride:
            raise ValueError('DEX table outside file')
        return count, off

    ns, so = table(56, 4)
    nt, to = table(64, 4)
    nc, co = table(96, 32)

    def string(index: int) -> str:
        if index >= ns:
            raise ValueError('Invalid DEX string index')
        pos = u32(so + 4 * index)
        # Skip the UTF-16 length ULEB128. Class descriptors are ASCII here.
        for _ in range(5):
            if pos >= len(data):
                raise ValueError('Truncated DEX string length')
            b = data[pos]
            pos += 1
            if b & 128 == 0:
                break
        else:
            raise ValueError('Invalid DEX string length')
        end = data.find(b'\0', pos)
        if end < 0:
            raise ValueError('Unterminated DEX string')
        return data[pos:end].decode('utf-8', errors='replace')

    result: set[str] = set()
    for i in range(nc):
        ci = u32(co + 32 * i)
        if ci >= nt:
            raise ValueError('Invalid DEX class type')
        result.add(string(u32(to + 4 * ci)))
    return result


def inspect(path: Path) -> dict:
    if not path.is_file() or path.stat().st_size > MAX_APK:
        raise ValueError('Missing or oversized input')
    with zipfile.ZipFile(path) as outer:
        if 'AndroidManifest.xml' in outer.namelist():
            apk = path.read_bytes()
            member = path.name
        else:
            entries = [i for i in outer.infolist() if i.filename.endswith('.apk')]
            if len(entries) != 1 or entries[0].file_size > MAX_APK:
                raise ValueError('Expected exactly one reasonably sized APK in artifact')
            member = entries[0].filename
            apk = outer.read(member)
    checks: dict[str, bool] = {}
    with zipfile.ZipFile(io.BytesIO(apk)) as z:
        names = z.namelist()
        if len(names) != len(set(names)):
            raise ValueError('APK contains duplicate members')
        dex_parts = [z.read(n) for n in names if re.fullmatch(r'classes\d*\.dex', n)]
        if not dex_parts:
            raise ValueError('No DEX files')
        classes: set[str] = set()
        for part in dex_parts:
            classes |= dex_classes(part)
        for key, descriptor in REQUIRED_CLASSES.items():
            checks[key] = descriptor in classes
        checks['responsive_v5_java_marker'] = any(b'Published responsive v5' in d for d in dex_parts)
        checks['infinity_media_session_tag'] = any(b'Infinity_media' in d for d in dex_parts)
        checks['media_notification_channel'] = any(b'infinity_media_playback' in d for d in dex_parts)
        native = z.read('lib/arm64-v8a/libkodi.so')
        if not native.startswith(b'\x7fELF'):
            raise ValueError('Invalid native library')
        for prop in REQUIRED_NATIVE:
            checks[prop] = prop.encode('ascii') in native
        for name in ('theme_contract.py', 'layout_service.py'):
            checks[name] = 'assets/addons/service.infinity.compat/' + name in names
    return {
        'schema': 1,
        'input': path.name,
        'apk_member': member,
        'apk_sha256': hashlib.sha256(apk).hexdigest(),
        'libkodi_sha256': hashlib.sha256(native).hexdigest(),
        'checks': checks,
        'missing': [key for key, ok in checks.items() if not ok],
        'static_presence_gate_passed': all(checks.values()),
        'runtime_tested': False,
        'audio_track_policy_verified': False,
        'audio_eraser_eligibility': 'unknown',
        'note': 'Presence only. Verify signature, version, JNI compatibility, actual audio attributes and device behavior separately.',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apk_or_artifact', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    try:
        result = inspect(args.apk_or_artifact)
        text = json.dumps(result, indent=2, sort_keys=True) + '\n'
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(text, encoding='utf-8')
        sys.stdout.write(text)
        return 0 if result['static_presence_gate_passed'] else 2
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, struct.error) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
