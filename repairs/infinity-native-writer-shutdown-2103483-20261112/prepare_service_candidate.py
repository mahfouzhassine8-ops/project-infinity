#!/usr/bin/env python3
"""Prepare an unshipped, hash-bound Core source patch. Never installs it.

Path correction must not be activated until native completion is verified.
The reporting correction deliberately creates no durability receipt.
"""
import argparse
import difflib
import hashlib
import json
from pathlib import Path

SOURCE_SHA = '2e1b79adc352129696ccfa48a3b5b16f85ebf812026fdd26c3e55d67f34b43b3'


def candidate(raw):
    assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA, 'Unknown installed service source'
    source = raw.decode('utf-8')
    old = '                    pkg_name = cf.read().split(b"\\x00")[0].decode("utf-8", "ignore").strip()'
    new = old + '''
                    # Infinity's engine process suffix is not part of its
                    # Android package/private directory identity.
                    if pkg_name == "com.projectinfinity.kodi:kodi":
                        pkg_name = "com.projectinfinity.kodi"'''
    assert source.count(old) == 1
    source = source.replace(old, new, 1)
    old = '''    # Clean shutdown
    if loaded_lib is not None:
        try:
            loaded_lib.stop_core_service()
        except Exception:
            pass'''
    new = '''    # Python service retirement is not a native durability receipt.
    if loaded_lib is not None:
        try:
            result = loaded_lib.stop_core_service()
            _log(f"Native stop requested (result={result}); completion is unverified",
                 xbmc.LOGWARNING if xbmc else None)
        except Exception as exc:
            _log(f"Native stop failed ({type(exc).__name__}); completion is unverified",
                 xbmc.LOGWARNING if xbmc else None)'''
    assert source.count(old) == 1
    source = source.replace(old, new, 1)
    old = '    _log("Service stopped cleanly.")'
    new = '    _log("Python service stopped; native completion remains unverified.")'
    assert source.count(old) == 1
    return source.replace(old, new, 1).encode('utf-8')


def prepare(source, out):
    assert out.name.endswith('UNSHIPPED'), 'Research output must be explicitly unshipped'
    raw = source.read_bytes()
    changed = candidate(raw)
    out.mkdir(parents=True, exist_ok=False)
    (out/'service.py').write_bytes(changed)
    patch = ''.join(difflib.unified_diff(raw.decode().splitlines(True), changed.decode().splitlines(True),
                                      fromfile='installed-1.0.2/service.py', tofile='unshipped/service.py', n=0))
    (out/'SERVICE-CANDIDATE.patch').write_text(patch)
    result = dict(status='UNSHIPPED_SOURCE_CORRECTIONS_ONLY_NATIVE_CONTRACT_BLOCKED',
                  installed_source_sha256=SOURCE_SHA, candidate_sha256=hashlib.sha256(changed).hexdigest(),
                  activation_allowed=False, native_completion_proven=False,
                  installed_library_sha256='c4a8a8d1e046cab6a42934b8fba31246efb21a002a90beb2bffa555623a383a9',
                  scope=['Exact Infinity process/private-package identity correction',
                         'Truthful native stop outcome reporting; no success or durability granted'],
                  actual_Core_executed=False, deployed=False)
    (out/'CANDIDATE.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.out), indent=2))
