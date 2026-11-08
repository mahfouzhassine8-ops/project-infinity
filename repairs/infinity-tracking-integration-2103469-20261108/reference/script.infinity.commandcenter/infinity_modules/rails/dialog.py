"""On-demand Kodi-owned chooser: no XML path lookup or hidden custom windows."""


def choose(title, labels, subtitle=''):
    import xbmcgui
    caption = title if not subtitle else title + ' — ' + subtitle
    # Kodi Dialog.select returns zero-based index or -1 on dismissal.
    # Kodi owns focus/back/theme/scroll/geometry using the skin's DialogSelect.xml.
    return xbmcgui.Dialog().select(caption, list(labels))
