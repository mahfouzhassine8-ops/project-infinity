"""One-shot Home route refresh. Reads add-on code/data; writes only window properties."""
import os
import sys
import uuid

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

sys.path.insert(0, os.path.dirname(__file__))
from infinity_playlist_registry import PROVIDER, ROOT, resolve

PREFIX = 'Infinity.Playlist.'


def read_local(path, limit):
    translated = xbmcvfs.translatePath(path)
    if '://' in translated:
        raise ValueError('Provider files must be installed locally')
    with open(translated, 'rb') as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError('Provider registry exceeds inspection limit')
    return data.decode('utf-8-sig')


def main():
    if xbmc.getSkinDir() != 'skin.infinity.diggz':
        return
    home = xbmcgui.Window(10000)
    request = uuid.uuid4().hex
    home.setProperty(PREFIX + 'Request', request)
    for name in ('Ready', 'TVPath', 'SportsPath'):
        home.clearProperty(PREFIX + name)
    installed = xbmc.getCondVisibility('System.HasAddon(' + PROVIDER + ')')
    browse = ROOT if installed else 'addons://sources/video/'
    result = {'tv': '', 'sports': '', 'status': 'unavailable'}
    version = 'unavailable'
    try:
        if installed:
            addon = xbmcaddon.Addon(PROVIDER)
            version = addon.getAddonInfo('version')
            directory = addon.getAddonInfo('path')
            code = read_local(os.path.join(directory, 'main.py'), 1024 * 1024)
            data = read_local(os.path.join(directory, 'resources', 'baked_in.json'), 256 * 1024)
            result = resolve(code, data)
    except Exception as error:
        result['status'] = 'inspection-' + type(error).__name__
    if home.getProperty(PREFIX + 'Request') != request or xbmc.getSkinDir() != 'skin.infinity.diggz':
        return
    for name, value in [('TVPath', result['tv']), ('SportsPath', result['sports']),
                        ('TVBrowse', result['tv'] or browse), ('SportsBrowse', result['sports'] or browse),
                        ('Status', result['status']), ('Version', version)]:
        home.setProperty(PREFIX + name, value)
    # Publish readiness last so a half-written route set cannot load a widget.
    home.setProperty(PREFIX + 'Ready', 'v1')
    xbmc.log('Infinity playlist routes: version={} status={} tv={} sports={}'.format(
        version, result['status'], bool(result['tv']), bool(result['sports'])), xbmc.LOGINFO)


if __name__ == '__main__':
    main()
