"""Infinity-owned Kodi HTTP preferences; independent provider sockets are unchanged."""
from __future__ import annotations

OWNER = 'script.infinity.commandcenter'
KEY = 'network_family'
MODES = ('auto', 'ipv4', 'ipv6')
LABELS = ('Automatic (Default)', 'IPv4 Only', 'IPv6 Only')
COVERAGE = (
    'Applies to new Kodi HTTP connections, including artwork and playback that '
    'uses Kodi HTTP/VFS. Active playback keeps its current connection mode.\n\n'
    'Providers that manage their own Python connections, direct FFmpeg inputs, '
    'and independent inputstream networking may use their own IP selection. '
    'Cobra networking and Android network settings are independent.\n\n'
    'IPv6 Only requires a usable IPv6 route. A proxy may resolve the destination '
    'itself; this setting then controls the connection to the proxy.'
)


def normalized(value):
    return value if value in MODES else 'auto'


def open_connections():
    import xbmc
    import xbmcaddon
    import xbmcgui
    from common import addon_set_setting
    from infinity_settings import choose

    if xbmc.getSkinDir() != 'skin.infinity.diggz':
        return
    current = normalized(xbmcaddon.Addon(OWNER).getSetting(KEY))
    selected = choose('Network Connections', LABELS + ('Supported connections',),
                      MODES.index(current))
    if selected == len(MODES):
        xbmcgui.Dialog().textviewer('Network Connections — Supported connections', COVERAGE)
        return
    if not 0 <= selected < len(MODES):
        return
    if (not addon_set_setting(OWNER, KEY, MODES[selected]) or
            xbmcaddon.Addon(OWNER).getSetting(KEY) != MODES[selected]):
        xbmcgui.Dialog().ok('Network Connections',
                            'The selection could not be saved. Reopen this screen to check it.')
        return
    xbmcgui.Dialog().notification('Network Connections',
                                 LABELS[selected] + ' — applies to new Kodi HTTP connections')
