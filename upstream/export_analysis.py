#!/usr/bin/env python3
"""Create a compact, shareable ZIP from Kodi smart-analysis evidence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import zipfile

TOP_LEVEL = {
    'SMART-ANALYSIS.md',
    'smart-analysis.json',
    'system-tray-status.json',
    'port-report.json',
    'ownership-manifest.json',
    'patch-series.json',
    'fast-java-status.json',
    'SHA256SUMS.json',
}
DIRS = {'replay', 'reconstruction', 'receipts'}
MAX_FILE_BYTES = 5 * 1024 * 1024


def collect(evidence: Path):
    included, skipped = [], []
    for path in sorted(evidence.rglob('*')):
        if not path.is_file():
            continue
        rel = path.relative_to(evidence)
        allowed = rel.as_posix() in TOP_LEVEL or (rel.parts and rel.parts[0] in DIRS)
        if not allowed:
            continue
        if path.stat().st_size > MAX_FILE_BYTES:
            skipped.append({'path': rel.as_posix(), 'reason': 'over_5mb'})
            continue
        included.append(path)
    return included, skipped


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()

    evidence = args.evidence.resolve()
    if not evidence.is_dir():
        raise SystemExit('Evidence directory does not exist')
    args.output.parent.mkdir(parents=True, exist_ok=True)

    included, skipped = collect(evidence)
    if not included:
        raise SystemExit('No portable analysis files found')

    manifest = {
        'schema': 1,
        'purpose': 'Portable Infinity Kodi analysis bundle for user-selected save/share.',
        'included': [p.relative_to(evidence).as_posix() for p in included],
        'skipped': skipped,
        'contains_apk': False,
        'contains_signing_keys': False,
        'contains_candidate_source_archive': False,
    }

    with zipfile.ZipFile(args.output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in included:
            zf.write(path, path.relative_to(evidence).as_posix())
        zf.writestr('EXPORT-MANIFEST.json', json.dumps(manifest, indent=2) + '\n')

    print(args.output)


if __name__ == '__main__':
    main()
