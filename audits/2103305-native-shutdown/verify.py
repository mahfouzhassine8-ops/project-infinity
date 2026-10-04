"""Read-only identity verification; not a native/device acceptance test."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST_SHA = 'b870052cc344b8d419ed8fb29eb5dbc019fdbc9a528219a576576dcc4332b82b'
ENGINE_SHA = '2b0897a286a7286e17109e8f5c7c2ec152c838dc91686ce349be3100eea69eac'
OWNERS = {
    'XBMCApp.cpp': '9feadf50fd1864815e819b598221cb2b20f78fea069aba7fb0a771b84ad95f49',
    'android_main.cpp': 'd70d38cef4471a74f70e3bc80ed0c100f6ae3dd8c54fc44f3bf482ccce263a32',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(manifest, engine, owner_directory=HERE):
    if digest(manifest) != MANIFEST_SHA:
        raise ValueError('Wrong native source manifest')
    proof = json.loads(manifest.read_text())
    for name, expected in OWNERS.items():
        rel = 'xbmc/platform/android/activity/' + name
        if proof['after'].get(rel) != expected or digest(owner_directory / name) != expected:
            raise ValueError('Wrong source owner: ' + name)
    if digest(engine) != ENGINE_SHA:
        raise ValueError('Wrong native library')
    return {'source_owners_verified': len(OWNERS), 'engine_sha256': ENGINE_SHA,
            'production_modified': False, 'installable_apk': False,
            'device_shutdown_verified': False, 'crash_owner_proven': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--engine', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.manifest, args.engine), indent=2))
