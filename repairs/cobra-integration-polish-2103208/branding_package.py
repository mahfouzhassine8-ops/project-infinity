"""Retain the source-built Java/native contract; replace only reviewed icon PNGs.

This module does not relax the parent packager. It supplies an independently
tested exact-delta check for the user-authorized PNG changes; all other payloads,
the resource table, IDs, manifest rules, native ABI and signer gates still apply.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import re
import struct
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent
DEX = re.compile(r'classes\d*\.dex$')
SIGNATURE = re.compile(r'META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))$', re.I)

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def png_size(data):
    require(data[:8] == b'\x89PNG\r\n\x1a\n' and data[12:16] == b'IHDR', 'Not an approved PNG')
    return list(struct.unpack('>II', data[16:24]))

def resource_slots(text):
    result = {}
    current = None
    for line in text.splitlines():
        found = re.match(r'\s*resource\s+0x7f[0-9a-fA-F]{6}\s+(\S+)', line)
        if found:
            current = found.group(1).split(':')[-1]
        found = re.match(r'\s*\(([^)]*)\)\s+\(file\)\s+(res/\S+)', line)
        if found and current:
            key = (current, found.group(1))
            require(key not in result, 'Ambiguous resource configuration: ' + repr(key))
            result[key] = found.group(2)
    require(result, 'Empty AAPT resource payload map')
    return result

def validate_rows(rows):
    from contract import ICON_SLOTS
    require(bool(rows), 'No approved branding payloads')
    sources, entries = set(), set()
    for row in rows:
        path, entry = row['source'], row['entry']
        require(path in ICON_SLOTS, 'Unapproved branding source: ' + path)
        require(tuple(row['slot']) == ICON_SLOTS[path], 'Wrong named icon slot: ' + path)
        require(re.fullmatch(r'res/[^/]+\.png', entry) is not None, 'Invalid PNG payload target')
        require(path not in sources and entry not in entries, 'Duplicate approved replacement')
        sources.add(path)
        entries.add(entry)
        for key in ('before', 'after'):
            require(re.fullmatch(r'[0-9a-f]{64}', row[key]) is not None, 'Invalid reviewed digest')
        require(row['before'] != row['after'], 'Unchanged payload must not be exempted')
    return {row['entry']: row for row in rows}

def replace_reviewed_pngs(archive_path, source, rows, resource_report):
    approved = validate_rows(rows)
    slots = resource_slots(Path(resource_report).read_text())
    for row in rows:
        require(slots.get(tuple(row['slot'])) == row['entry'], 'Parent resource mapping drift: ' + row['source'])
    replacement = {}
    with zipfile.ZipFile(archive_path) as original:
        require(len(original.namelist()) == len(set(original.namelist())), 'Duplicate base APK members')
        for entry, row in approved.items():
            before = original.read(entry)
            after = (Path(source) / row['source']).read_bytes()
            require(digest(before) == row['before'], 'Parent icon drift: ' + entry)
            require(digest(after) == row['after'], 'Unreviewed icon bytes: ' + entry)
            require(png_size(before) == row['dimensions'] == png_size(after), 'Icon dimensions drift: ' + entry)
            replacement[entry] = after
        with tempfile.NamedTemporaryFile(prefix='cobra208-icons-', suffix='.apk', dir=Path(archive_path).parent) as temp:
            with zipfile.ZipFile(temp.name, 'w') as target:
                for info in original.infolist():
                    target.writestr(info, replacement.get(info.filename, original.read(info.filename)))
            # Archive replacement occurs only after all targeted bytes validate.
            Path(archive_path).write_bytes(Path(temp.name).read_bytes())

def verify_exact_payload_delta(base, final, rows):
    approved = validate_rows(rows)
    with zipfile.ZipFile(base) as before, zipfile.ZipFile(final) as after:
        an, bn = set(before.namelist()), set(after.namelist())
        require(len(an) == len(before.namelist()) and len(bn) == len(after.namelist()), 'Duplicate APK members')
        require(before.testzip() is None and after.testzip() is None, 'APK CRC failure')
        kept = {name for name in an if name != 'AndroidManifest.xml' and not DEX.fullmatch(name) and not SIGNATURE.fullmatch(name)}
        expected = kept | {'AndroidManifest.xml'} | {name for name in bn if DEX.fullmatch(name) or SIGNATURE.fullmatch(name)}
        require(bn == expected, 'Unexpected APK inventory delta')
        require(set(approved) <= kept, 'Approved icon missing from protected payload')
        changes = []
        for name in sorted(kept):
            old, new = before.read(name), after.read(name)
            if name in approved:
                row = approved[name]
                require(digest(old) == row['before'], 'Parent approved PNG drift: ' + name)
                require(digest(new) == row['after'], 'Candidate approved PNG drift: ' + name)
                require(png_size(old) == row['dimensions'] == png_size(new), 'Candidate PNG dimensions drift')
                changes.append(name)
            else:
                require(old == new, 'Protected APK payload changed: ' + name)
        require(before.read('resources.arsc') == after.read('resources.arsc'), 'Resource table changed')
        return {
            'native_files_byte_identical': sum(name.startswith('lib/') and not name.endswith('/') for name in kept),
            'asset_files_byte_identical': sum(name.startswith('assets/') and not name.endswith('/') for name in kept),
            'android_resources_byte_identical': False,
            'resource_table_byte_identical': True,
            'unrelated_resources_byte_identical': True,
            'approved_branding_resource_entries': changes,
            'other_payload_entries_preserved': len(kept) - len(changes),
        }

# Preserve the current parent contract after its background-control bridge
# upgrade, not the obsolete pre-bridge display-copy sentinel.
RUNTIME_TOKENS = (
    b'InfinityExtendedBackgroundService', b'InfinityBackgroundControlActivity',
    b'BACKGROUND_MODE_NORMAL', b'BACKGROUND_MODE_EXTENDED', b'InfinityCoreBridge',
    b'InfinityCobraDeviceBridge', b'getPlayWhenReady', b'Turn off',
)

def verify_runtime_tokens(joined):
    for token in RUNTIME_TOKENS:
        require(token in joined, 'Missing source-built runtime: ' + repr(token))

def main():
    # Resolve the same existing shell packager from the CI reconstruction. Its
    # manifest/JNI/resource ID/signature checks remain executed by its main().
    sys.path.insert(0, str(Path('scripts').resolve()))
    spec = importlib.util.spec_from_file_location('package208_parent', Path('scripts/package_background_resume.py'))
    package = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(package)
    rows = json.loads((ROOT / 'approved-resources.json').read_text())
    original_merge = package.merge
    def merge(base, donor, output):
        result = original_merge(base, donor, output)
        replace_reviewed_pngs(output, Path('kodi'), rows, Path(output).parent / 'base-resources.txt')
        return result
    def verify_bytes(base, final):
        result = verify_exact_payload_delta(base, final, rows)
        with zipfile.ZipFile(base) as original, zipfile.ZipFile(final) as candidate:
            require(digest(candidate.read('lib/arm64-v8a/libkodi.so')) == package.BASE_ENGINE_SHA256, 'Native engine changed')
            require(package.dex_contract(original)[0] == package.dex_contract(candidate)[0], 'Final JNI contract changed')
            joined = b''.join(candidate.read(name) for name in candidate.namelist() if DEX.fullmatch(name))
            verify_runtime_tokens(joined)
        return result
    package.merge = merge
    package.verify_bytes = verify_bytes
    package.main()

if __name__ == '__main__':
    main()
