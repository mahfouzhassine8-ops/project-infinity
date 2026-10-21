"""Lossless identities around Kodi's existing provider directory results.

No discovery API, credentials, metadata scraper, cache, or database. Provider
routes remain byte-for-byte inside a bounded, checksummed identity envelope.
"""
import base64
import hashlib
import json
import re
from urllib.parse import parse_qs, urlencode, urlsplit
import zlib

BASE = 'plugin://plugin.infinity.latestreleases/'
PROVIDER = 'plugin://plugin.video.umbrella/'
MAX_ROUTE = 65536
MAX_IDENTITY = 32768
MOVIES = ('plugin://plugin.video.umbrella/?action=movies&folderName=Latest+releases&url='
          'https%3A%2F%2Fapi.trakt.tv%2Fusers%2Fgarycrawfordgc%2Flists%2F5308818%2Fitems%2Fmovies%3Flimit%3D20%26page%3D1'
          '&folderName=Latest+releases+-+%5BCOLOR+FFFFFF33%5Dgarycrawfordgc%5B%2FCOLOR%5D')
TVSHOWS = ('plugin://plugin.video.umbrella/?action=tvshows&url=trakttrending_recent'
           '&folderName=Trending+Recently+Released+%28Trakt%29')
FEEDS = {'movies': MOVIES, 'tvshows': TVSHOWS}


def provider_route(route, kind):
    if not isinstance(route, str) or len(route.encode('utf-8')) > MAX_ROUTE:
        return False
    if any(ord(c) < 32 for c in route):
        return False
    p = urlsplit(route)
    if p.scheme != 'plugin' or p.netloc != 'plugin.video.umbrella' or p.path not in ('', '/'):
        return False
    q = parse_qs(p.query, keep_blank_values=True)
    return q.get('action', []) in ([('play' if kind == 'movie' else 'seasons')], ['episodes'] if kind == 'tvshow' else ['play'])


def encode(route, kind, ids):
    if kind not in ('movie', 'tvshow') or not provider_route(route, kind):
        raise ValueError('unverified provider item')
    ids = {k: str(v) for k, v in ids.items() if k in ('imdb', 'tmdb', 'tvdb') and v and str(v) != '0'}
    route_ids=parse_qs(urlsplit(route).query)
    if any(route_ids.get(k) and route_ids[k][0] != v for k,v in ids.items()):
        raise ValueError('provider identifier mismatch')
    if not ids or not all(re.fullmatch(r'tt[0-9]+', v) if k == 'imdb' else re.fullmatch(r'[0-9]+', v)
               for k, v in ids.items()):
        raise ValueError('media identifiers unavailable')
    raw = json.dumps({'v': 1, 'kind': kind, 'ids': ids, 'route': route},
                     ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    packed = base64.urlsafe_b64encode(zlib.compress(raw, 9)).decode().rstrip('=')
    path = BASE + '?' + urlencode({'action': 'open', 'data': packed,
                                  'sha256': hashlib.sha256(raw).hexdigest()})
    if len(path.encode()) > MAX_IDENTITY:
        raise ValueError('identity exceeds reviewed bound')
    return path


def _decode(path):
    if not isinstance(path, str) or len(path.encode()) > MAX_IDENTITY:
        raise ValueError('identity length')
    p = urlsplit(path)
    if p.scheme != 'plugin' or p.netloc != 'plugin.infinity.latestreleases' or p.path != '/':
        raise ValueError('identity owner')
    q = parse_qs(p.query, strict_parsing=True)
    if set(q) != {'action', 'data', 'sha256'} or any(len(v) != 1 for v in q.values()) or q['action'] != ['open']:
        raise ValueError('identity shape')
    if not re.fullmatch('[a-f0-9]{64}', q['sha256'][0]):
        raise ValueError('identity digest')
    data = q['data'][0]
    if not re.fullmatch('[a-zA-Z0-9_-]+', data):
        raise ValueError('identity encoding')
    decompressor = zlib.decompressobj()
    raw = decompressor.decompress(base64.urlsafe_b64decode(data + '=' * (-len(data) % 4)), MAX_ROUTE + 4096)
    if not decompressor.eof or decompressor.unused_data or decompressor.unconsumed_tail:
        raise ValueError('identity compression bound')
    if hashlib.sha256(raw).hexdigest() != q['sha256'][0]:
        raise ValueError('identity checksum')
    obj = json.loads(raw)
    if set(obj) != {'v', 'kind', 'ids', 'route'} or obj['v'] != 1 or obj['kind'] not in ('movie', 'tvshow'):
        raise ValueError('identity version')
    if encode(obj['route'], obj['kind'], obj['ids']) != path:
        raise ValueError('noncanonical media identity')
    return obj


def wrap(row, section):
    """Every metadata value stays from the exact Kodi-returned item."""
    result = dict(row)
    kind = {'movies': 'movie', 'tvshows': 'tvshow'}[section]
    q = parse_qs(urlsplit(row.get('file', '')).query)
    ids = dict(row.get('uniqueid') or {})
    for key in ('imdb', 'tmdb', 'tvdb'):
        if not ids.get(key) and q.get(key):
            ids[key] = q[key][0]
    result['file'] = encode(row['file'], kind, ids)
    result['_infinity_kind'] = kind
    return result


def equivalent(before, after):
    if len(before) != len(after):
        return False
    for a, b in zip(before, after):
        rebuilt = dict(b)
        rebuilt.pop('_infinity_kind', None)
        if b['file'].startswith(BASE):
            rebuilt['file'] = decode(b['file'])['route']
        if rebuilt != a:
            return False
    return True


def decode(path):
    try:
        return _decode(path)
    except (zlib.error, KeyError, TypeError) as error:
        raise ValueError('Invalid Infinity media identity') from error
