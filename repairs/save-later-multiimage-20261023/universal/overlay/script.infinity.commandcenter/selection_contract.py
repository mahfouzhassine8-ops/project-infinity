# SPDX-License-Identifier: GPL-2.0-or-later
"""Versioned exact-title selection for Infinity-owned saved projections.

The native ingress supplies a copied ListItem. This capsule binds its key,
owning list, typed identity and original routes; coordinates and later global
focus never authorize an action. It is presentation state, not a new store.
"""
from __future__ import annotations

import hashlib
import json
import re

import resume_hub as hub

OWNER = 'script.infinity.commandcenter'
VERSION = '1'
BUCKETS = frozenset(('continue', 'history', 'watched', 'watchlist', 'later',
                     'collection', 'list', 'ratings', 'progress', 'next'))
FIELDS = frozenset(('schema', 'owner', 'key', 'bucket', 'list', 'identity',
                    'source', 'stable_source'))


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':'))


def _digest(value):
    return hashlib.sha256(_json(value).encode('utf-8')).hexdigest()


def snapshot(entry, bucket, list_name=''):
    identity = hub.entry_identity(entry)
    key = entry.get('key')
    if (not identity or not isinstance(key, str) or not hub.KEY_RE.fullmatch(key) or
            not isinstance(bucket, str) or bucket not in BUCKETS or
            entry.get('synthetic_next') or not isinstance(list_name, str) or
            (bucket == 'list' and not list_name)):
        return None
    value = dict(schema=1, owner=OWNER, key=key, bucket=bucket,
                 list=list_name if bucket == 'list' else '', identity=identity,
                 source=entry.get('source') if isinstance(entry.get('source'), str) else '',
                 stable_source=entry.get('stable_source') if isinstance(entry.get('stable_source'), str) else '')
    value['token'] = _digest(value)
    return value


def token(entry, bucket, list_name=''):
    value = snapshot(entry, bucket, list_name)
    return value['token'] if value else ''


def publish(item, entry, bucket, list_name=''):
    value = snapshot(entry, bucket, list_name)
    if value is None:
        return False
    item.setProperty('Infinity.Selection.Contract', VERSION)
    item.setProperty('Infinity.Selection.Snapshot', _json(value))
    return True


def read(item):
    """Untrusted capsule parsing; the action owner must compare its token again."""
    try:
        if item.getProperty('Infinity.Selection.Contract') != VERSION:
            return None
        raw = item.getProperty('Infinity.Selection.Snapshot')
        if not isinstance(raw, str) or len(raw) > 256 * 1024:
            return None
        value = json.loads(raw)
    except (AttributeError, TypeError, ValueError, RuntimeError):
        return None
    if not isinstance(value, dict) or set(value) != FIELDS | {'token'}:
        return None
    if (type(value['schema']) is not int or value['schema'] != 1 or value['owner'] != OWNER or
            not isinstance(value['bucket'], str) or value['bucket'] not in BUCKETS or
            not isinstance(value['key'], str) or not hub.KEY_RE.fullmatch(value['key']) or
            not isinstance(value['identity'], dict) or
            not isinstance(value['list'], str) or (value['bucket'] == 'list' and not value['list']) or
            not all(isinstance(value[field], str) for field in ('source', 'stable_source')) or
            not re.fullmatch(r'[0-9a-f]{64}', str(value['token']))):
        return None
    expected = _digest({name: value[name] for name in FIELDS})
    return value if value['token'] == expected else None


def matches(expected_token, entry, bucket, list_name=''):
    return (isinstance(expected_token, str) and bool(re.fullmatch(r'[0-9a-f]{64}', expected_token))
            and token(entry, bucket, list_name) == expected_token)
