"""Disposable synthetic providers; never install into the user's application."""
import sys
from urllib.parse import parse_qs
import xbmc
import xbmcgui
import xbmcplugin

p = parse_qs(sys.argv[2].lstrip('?'))
page = int(p.get('page', ['1'])[0])
content = p.get('content', ['movies'])[0]
handle = int(sys.argv[1])
xbmcplugin.setContent(handle, content)
for i in range(1, 9):
    item = xbmcgui.ListItem(label='Fixture %s %02d' % (content, i))
    info = item.getVideoInfoTag()
    info.setTitle('Fixture %s %02d' % (content, i))
    info.setPlot('Synthetic browsing metadata. This description remains available across views; no real provider or private media is used. ' * 3)
    info.setYear(2026);info.setDuration(7200);info.setGenres(['Drama', 'Adventure'])
    info.setRating(8.1)
    info.setMediaType('tvshow' if content == 'tvshows' else 'episode' if content == 'episodes' else 'movie')
    item.setArt({'poster': '/tmp/kodi-ui-runtime-qa/poster.png', 'fanart': '/tmp/kodi-ui-runtime-qa/fanart.png'})
    xbmcplugin.addDirectoryItem(handle, '/tmp/kodi-ui-runtime-qa/not-a-playback-fixture.mp4', item, False)
next_url = sys.argv[0] + '?page=%s&content=%s' % (page + 1, content)
xbmcplugin.addDirectoryItem(handle, next_url, xbmcgui.ListItem(label='Next page'), True)
xbmcplugin.endOfDirectory(handle, succeeded=True, cacheToDisc=False)
# Reproduce a provider's explicit post-directory override without changing any
# production provider. This intentionally challenges the global preference.
xbmc.executebuiltin('Container.SetViewMode(500)')
