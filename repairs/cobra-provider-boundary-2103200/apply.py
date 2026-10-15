#!/usr/bin/env python3
"""Guarded Java-only resource publication boundary for exact Cobra 2103199."""
from pathlib import Path
import argparse, hashlib, json, shutil, zipfile

ROOT = Path(__file__).resolve().parent
PROVIDER = 'tools/android/packaging/xbmc/src/content/XBMCFileContentProvider.java.in'
JSONRPC = 'tools/android/packaging/xbmc/src/XBMCJsonRPC.java.in'
PREIMAGES = {
    PROVIDER: 'b154fc43903c2b5dfa03199c4fa1872434af98a410c95ba649ebdb1638c00da5',
    JSONRPC: '7ca8fa099091847a82c148b5dc7251ae0f417a84314f04eb1f475baa7ac3a35c',
}

def require(value, message):
    if not value:
        raise RuntimeError(message)

def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()

def transform_provider(source):
    require(digest(source) == PREIMAGES[PROVIDER], 'Provider preimage mismatch')
    return (ROOT/'XBMCFileContentProvider.java.in').read_text()

def transform_jsonrpc(source):
    require(digest(source) == PREIMAGES[JSONRPC], 'JSON-RPC preimage mismatch')
    # Generic URIs in same-UID bitmap loading and directory listing are not public.
    require(source.count('XBMCFileContentProvider.buildUri(') == 15, 'Unexpected URI construction sites')
    source = source.replace('XBMCFileContentProvider.buildUri(', 'XBMCFileContentProvider.buildPublishedUri(')
    source = source.replace('resolver.openInputStream(XBMCFileContentProvider.buildPublishedUri(src))',
                            'resolver.openInputStream(XBMCFileContentProvider.buildUri(src))')
    source = source.replace('XBMCFileContentProvider.buildPublishedUri(uri.toString()).toString()',
                            'XBMCFileContentProvider.buildUri(uri.toString()).toString()')
    require(source.count('XBMCFileContentProvider.buildPublishedUri(') == 13, 'Publication-site mismatch')
    anchor = '  public Cursor getSuggestions(String query, int limit)\n  {\n'
    require(source.count(anchor) == 1, 'Search boundary anchor mismatch')
    source = source.replace(anchor, anchor +
        '    // The external search term remains one JSON string value in all six fixed requests.\n'
        '    String quotedQuery = new com.google.gson.JsonPrimitive(query == null ? "" : query).toString();\n'
        '    query = quotedQuery.substring(1, quotedQuery.length() - 1);\n', 1)
    return source

def apply(source, receipt, out):
    data = json.loads(receipt.read_text())
    require(data['version_code'] == 2103199, 'Requires verified 2103199 source')
    for name, row in data['files'].items():
        require(hashlib.sha256((source/name).read_bytes()).hexdigest() == row['after'], 'Receipt mismatch: '+name)
    # Calculate every exact-preimage transform before writing any input.
    transformed = {PROVIDER: transform_provider((source/PROVIDER).read_text()),
                   JSONRPC: transform_jsonrpc((source/JSONRPC).read_text())}
    out.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(out/'pre-change-android-source.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for folder in ('tools/android/packaging', 'media'):
            for path in sorted((source/folder).rglob('*')):
                if path.is_file():
                    archive.write(path, str(path.relative_to(source)))
        archive.write(source/'cmake/scripts/android/Install.cmake', 'cmake/scripts/android/Install.cmake')
    shutil.copy2(receipt, out/'pre-change-source-receipt.json')
    files = {}
    for name, value in transformed.items():
        files[name] = {'before': PREIMAGES[name], 'after': digest(value)}
        (source/name).write_text(value)
    for name, row in data['files'].items():
        if name not in files:
            require(hashlib.sha256((source/name).read_bytes()).hexdigest() == row['after'], 'Unrelated input changed: '+name)
    (out/'patch.json').write_text(json.dumps({'parent_build':2103199, 'files':files,
        'native_engine_recompiled':False, 'manifest_changed':False, 'new_controls':False,
        'physical_device_verified':False}, indent=2)+'\n')
    print('PASS: exact two-file Java boundary applied; other inputs preserved')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    apply(args.source, args.receipt, args.out)
