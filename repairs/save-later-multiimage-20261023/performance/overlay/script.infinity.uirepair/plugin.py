"""Original Resume items and a reversible, view-local Video Sources filter."""
import sys
from urllib.parse import parse_qs
import xbmc
import xbmcgui
import xbmcplugin
from runtime import addons, hidden, destination

def optin(item, kind, token):
    item.setProperty('Infinity.UI.Version', '1')
    item.setProperty('Infinity.UI.Kind', kind)
    item.setProperty('Infinity.UI.Token', token)

def main():
    handle = int(sys.argv[1])
    params = parse_qs(sys.argv[2].lstrip('?'))
    action = params.get('action', ['sources'])[0]
    try:
        if action == 'sources':
            xbmcplugin.setContent(handle, 'addons')
            for row in addons():
                aid = row['addonid']
                if hidden(aid): continue
                route = destination(aid)
                if not route: continue
                kind, target = route
                path = target if kind == 'plugin' else 'script://' + aid
                item = xbmcgui.ListItem(row.get('name', aid), path=path, offscreen=True)
                item.setArt(dict(thumb=row.get('thumbnail', ''), icon=row.get('thumbnail', '')))
                item.setProperty('Addon.ID', aid)
                item.setProperty('Addon.IsInstalled', 'true')
                optin(item, 'addon', aid)
                xbmcplugin.addDirectoryItem(handle, path, item, isFolder=(kind == 'plugin'))
        elif action == 'continue':
            from controller_access import load
            plugin = load()
            media = 'tv' if params.get('media') == ['tv'] else 'movie'
            data = plugin.hub.load_view(plugin.PROFILE)
            render = dict(source_memory=plugin.setting_bool('source_memory_enabled', True),
                          tier=xbmcgui.Window(10000).getProperty('Infinity.Artwork.Quality') or 'standard', installed={})
            xbmcplugin.setContent(handle, 'episodes' if media == 'tv' else 'movies')
            values = plugin._values_for(data, media, 'continue')[:100]
            render = plugin.prepare_render(data, values, render)
            for entry in values:
                target, item = plugin._list_item(entry, data, 'continue', render=render)
                key = str(entry.get('key') or '')
                if plugin.hub.KEY_RE.fullmatch(key) and not entry.get('synthetic_next'):
                    optin(item, 'resume', key)
                xbmcplugin.addDirectoryItem(handle, target, item, isFolder=False)
        else:
            raise ValueError('Unknown directory')
        xbmcplugin.endOfDirectory(handle, succeeded=True, cacheToDisc=False)
    except Exception as exc:
        xbmc.log('Infinity item directory unavailable: ' + str(exc), xbmc.LOGWARNING)
        xbmcplugin.endOfDirectory(handle, succeeded=False, cacheToDisc=False)

if __name__ == '__main__':
    main()
