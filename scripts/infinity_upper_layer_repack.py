#!/usr/bin/env python3
"""Repack an existing Infinity APK with current upper-layer services only.

Keeps the compiled Kodi/Infinity engine untouched, removes old APK signatures,
replaces selected assets/addons trees, and emits a new unsigned APK for signing.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ADDONS = ('service.infinity.compat', 'service.infinity.refresh', 'script.infinity.audiopolicy')
SIGNING = re.compile(r'META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))', re.I)


def replacement_files() -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for addon_id in ADDONS:
        root = ROOT / 'addons' / addon_id
        if not root.is_dir():
            raise FileNotFoundError(root)
        for path in sorted(root.rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                out[f'assets/addons/{addon_id}/' + path.relative_to(root).as_posix()] = path.read_bytes()
    return out


def build(source: Path, output: Path) -> None:
    if source.resolve() == output.resolve():
        raise ValueError('input and output must differ')
    repl = replacement_files()
    prefixes = tuple(f'assets/addons/{a}/' for a in ADDONS)
    with zipfile.ZipFile(source, 'r') as zin:
        names = zin.namelist()
        if len(names) != len(set(names)):
            raise ValueError('input APK has duplicate members')
        with zipfile.ZipFile(output, 'w', allowZip64=True) as zout:
            for item in zin.infolist():
                if SIGNING.fullmatch(item.filename):
                    continue
                if item.filename.startswith(prefixes):
                    continue
                zout.writestr(item, zin.read(item.filename))
            for name, data in repl.items():
                zout.writestr(name, data, compress_type=zipfile.ZIP_DEFLATED)
    with zipfile.ZipFile(output, 'r') as z:
        for name, data in repl.items():
            if z.read(name) != data:
                raise ValueError('replacement mismatch: ' + name)
    print('Upper-layer repack complete; compiled engine members were not rebuilt.')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    build(a.source, a.output)
