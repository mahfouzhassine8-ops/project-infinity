"""Synthetic local-only directory; contains no user media or provider request."""
import json
from pathlib import Path
import sys
from urllib.parse import parse_qs, urlsplit
import xbmcgui
import xbmcplugin

base = Path(__file__).resolve().parents[1]
config = json.loads((base / 'config.json').read_text())
handle = int(sys.argv[1])
params = parse_qs(sys.argv[2].lstrip('?'))
if params.get('play') == ['1']:
    item = xbmcgui.ListItem(path=str(base / 'silent-test.mp4'))
    xbmcplugin.setResolvedUrl(handle, True, item)
else:
    kind = params.get('kind', ['movies'])[0]
    mediatype = {'movies': 'movie', 'tvshows': 'tvshow', 'episodes': 'episode'}[kind]
    xbmcplugin.setContent(handle, kind)
    xbmcplugin.setPluginCategory(handle, 'Synthetic browser provider')
    for index in range(1, 11):
        label = 'Media %02d — A longer title with readable words' % index
        item = xbmcgui.ListItem(label)
        item.setInfo('video', {'title': label, 'mediatype': mediatype, 'year':2024,
            'duration':5880, 'genre':'Drama / Adventure', 'rating':7.8, 'mpaa':'PG-13',
            'plot':('Synthetic metadata for selected item %02d. This is a local rendering fixture. ' % index) * 8,
            'trailer':str(base / 'silent-test.mp4') if index == 1 else ''})
        if index != 2:
            item.setArt({'poster': str(base / 'poster.png'), 'thumb':str(base / 'poster.png')})
        # A conspicuous directory icon must never become selected poster art.
        item.setArt({'icon':str(base / 'fanart.png')})
        item.setProperty('IsPlayable', 'true' if kind != 'tvshows' else 'false')
        url = 'plugin://plugin.video.infinitybrowserqa/?play=1' if kind != 'tvshows' else 'plugin://plugin.video.infinitybrowserqa/?kind=episodes'
        xbmcplugin.addDirectoryItem(handle, url, item, kind == 'tvshows')
    xbmcplugin.endOfDirectory(handle, succeeded=True, cacheToDisc=False)
