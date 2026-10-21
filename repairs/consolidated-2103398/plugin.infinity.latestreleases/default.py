"""Infinity-owned feeds using Kodi's authorized directory API to Umbrella.

Umbrella remains installed and unmodified; its installed version owns upstream
requests, filters, sorting, pagination, artwork and metadata transformations.
"""
import json
import sys
from urllib.parse import parse_qs, urlsplit, urlencode
import xbmc
import xbmcgui
import xbmcplugin
from identity import BASE, FEEDS, decode, equivalent, wrap

FIELDS = ['title', 'originaltitle', 'year', 'genre', 'plot', 'plotoutline',
          'runtime', 'rating', 'mpaa', 'premiered', 'trailer', 'uniqueid',
          'imdbnumber', 'art', 'thumbnail', 'fanart', 'season', 'episode',
          'showtitle', 'playcount', 'lastplayed', 'resume', 'cast', 'director',
          'writer', 'studio', 'country', 'tagline']
INFO = {'originaltitle', 'title', 'year', 'genre', 'plot', 'plotoutline',
        'rating', 'mpaa', 'premiered', 'trailer', 'imdbnumber', 'season', 'episode',
        'playcount', 'lastplayed', 'director', 'writer', 'studio',
        'country', 'tagline'}


def rpc(method, params):
    reply = json.loads(xbmc.executeJSONRPC(json.dumps({'jsonrpc': '2.0', 'id': 1,
                                                     'method': method, 'params': params})))
    if 'error' in reply:
        raise RuntimeError('Kodi directory request failed')
    return reply.get('result', {})


def listing(route):
    rows = rpc('Files.GetDirectory', {'directory': route, 'media': 'video',
                                      'properties': FIELDS}).get('files', [])
    if not isinstance(rows, list) or len(rows) > 1000:
        raise RuntimeError('Unexpected provider listing')
    return rows


def item(row):
    path = row['file']
    li = xbmcgui.ListItem(label=row.get('label') or row.get('title') or '', path=path)
    art=dict(row.get('art') or {})
    if row.get('thumbnail'): art.setdefault('thumb',row['thumbnail'])
    if row.get('fanart'): art.setdefault('fanart',row['fanart'])
    li.setArt(art)
    info = {k: row[k] for k in INFO if row.get(k) not in (None, '', [])}
    if row.get('showtitle'): info['tvshowtitle']=row['showtitle']
    if row.get('runtime') is not None: info['duration']=row['runtime']
    kind = row.get('_infinity_kind') or row.get('type')
    if kind in ('movie', 'tvshow', 'season', 'episode'):
        info['mediatype'] = kind
    li.setInfo('video', info)
    if row.get('uniqueid'):
        li.setUniqueIDs({k: str(v) for k, v in row['uniqueid'].items()})
    if row.get('cast'):
        li.setCast(row['cast'])
    resume = row.get('resume') or {}
    if resume.get('position'):
        li.setProperty('ResumeTime', str(resume['position']))
        li.setProperty('TotalTime', str(resume.get('total', 0)))
    folder = kind in ('tvshow', 'season') or row.get('filetype') == 'directory'
    if path.startswith(BASE):
        verified = decode(path)
        li.setProperty('Infinity.LatestReleases.Identity', 'v1')
        li.setProperty('Infinity.LatestReleases.Kind', verified['kind'])
    if not folder:
        li.setProperty('IsPlayable', 'true')
    return path, li, folder


def run():
    handle = int(sys.argv[1])
    q = parse_qs(sys.argv[2].lstrip('?'), keep_blank_values=True)
    action = q.get('action', ['feed'])[0]
    if action == 'open':
        verified = decode(sys.argv[0] + sys.argv[2])
        if verified['kind'] == 'movie':
            xbmcplugin.setResolvedUrl(handle, True, xbmcgui.ListItem(path=verified['route']))
            return
        rows = listing(verified['route'])
        content = 'seasons' if 'action=seasons' in verified['route'] else 'episodes'
    elif action == 'feed':
        section = q.get('section', ['movies'])[0]
        if section not in FEEDS:
            raise ValueError('Unknown Latest Releases feed')
        route=FEEDS[section]
        if q.get('reload'):
            route+='&'+urlencode({'reload':q['reload'][0][:200]})
        before = listing(route)
        rows = []
        for row in before:
            # Preserve next-page/navigation entries exactly. Only genuine media
            # with real identifiers receive an Infinity media identity.
            try:
                rows.append(wrap(row, section))
            except (ValueError, KeyError):
                rows.append(dict(row))
        if not equivalent(before, rows):
            raise RuntimeError('Latest Releases output equivalence failed')
        xbmcgui.Window(10000).setProperty('Infinity.LatestReleases.Equivalent.' + section, 'true')
        content = section
    else:
        raise ValueError('Unknown Latest Releases action')
    xbmcplugin.setContent(handle, content)
    xbmcplugin.addDirectoryItems(handle, [item(row) for row in rows], len(rows))
    # SORT_METHOD_NONE preserves the provider's exact ordering and pagination.
    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(handle, cacheToDisc=False)


if __name__ == '__main__':
    try:
        run()
    except Exception:
        xbmc.log('[Infinity Latest Releases] listing or identity validation failed', xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Infinity Latest Releases', 'The existing provider listing is unavailable.')
        xbmcplugin.endOfDirectory(int(sys.argv[1]), succeeded=False, cacheToDisc=False)
