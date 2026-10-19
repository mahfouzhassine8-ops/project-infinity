#!/usr/bin/env python3
"""Group #1/task 02 exact 2103390 Command Center movie duplicate guard.

Only verified identical movie keys can share one display card / saved-progress
update key. This deliberately NEVER deletes or merges persistent user data and
never touches television identities, provider routes, or shutdown code.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

PREIMAGE_SHA256 = '7794e25ec63348d29f74c45948d81db3e2fa1ba780437c329277fcffb1888eff'

BEFORE_KEY = '''    matches = canonical or legacy
    return next(iter(matches)) if len(matches) == 1 else identity_key(identity)
'''
AFTER_KEY = '''    matches = canonical or legacy
    if len(matches) == 1:
        return next(iter(matches))
    # Existing duplicate movie records with fully verified, mutually agreeing
    # IDs should update the newest saved key, not mint a third progress record.
    # Never choose arbitrarily among ambiguous records or TV episodes.
    if identity.get('kind') == 'movie' and len(canonical) > 1:
        items = _dict(_dict(data).get('items'))
        group = [(key, _dict(items.get(key))) for key in canonical]
        verified = [entry_identity(value) for _, value in group]
        if (all(value and source for (_, value), source in zip(group, verified)) and
                all(same_identity(left, right) for n, left in enumerate(verified)
                    for right in verified[n + 1:])):
            return max(group, key=lambda item: (int(item[1].get('updated') or 0), item[0]))[0]
    return identity_key(identity)
'''

BEFORE_ENTRIES = '''    values.sort(key=lambda value: int(value.get('updated') or value.get('watched_at') or
                                      value.get('added_at') or 0), reverse=True)
    return values
'''
AFTER_ENTRIES = '''    values.sort(key=lambda value: int(value.get('updated') or value.get('watched_at') or
                                      value.get('added_at') or 0), reverse=True)
    if bucket == 'items' and media in ('movie', 'all'):
        # Presentation-only: never delete, modify, or merge a saved record.
        # Title/poster and untyped source links are NOT identity evidence.
        groups = {}
        for value in values:
            if value.get('media') != 'movie':
                continue
            token = identity_key(entry_identity(value))
            if token:
                groups.setdefault(token, []).append(value)
        hidden_keys = set()
        for group in groups.values():
            identities = [entry_identity(item) for item in group]
            if len(group) > 1 and all(identities) and all(
                    same_identity(left, right) for i, left in enumerate(identities)
                    for right in identities[i + 1:]):
                hidden_keys.update(item['key'] for item in group[1:])
        if hidden_keys:
            values = [item for item in values if item.get('key') not in hidden_keys]
    return values
'''


def patch_bytes(source: bytes) -> bytes:
    if hashlib.sha256(source).hexdigest() != PREIMAGE_SHA256:
        raise ValueError('Refusing to edit unknown Command Center Resume Hub source')
    text = source.decode('utf8')
    for original, corrected in ((BEFORE_KEY, AFTER_KEY), (BEFORE_ENTRIES, AFTER_ENTRIES)):
        if text.count(original) != 1:
            raise ValueError('Refusing ambiguous resume identity edit')
        text = text.replace(original, corrected, 1)
    return text.encode('utf8')


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('original', type=Path)
    parser.add_argument('staged', type=Path)
    args = parser.parse_args()
    if args.original.resolve() == args.staged.resolve():
        raise ValueError('Never overwrite the protected parent')
    patched = patch_bytes(args.original.read_bytes())
    args.staged.parent.mkdir(parents=True, exist_ok=True)
    args.staged.write_bytes(patched)
    print('Staged only the exact verified movie duplicate guard; no data writes')


if __name__ == '__main__':
    main()
