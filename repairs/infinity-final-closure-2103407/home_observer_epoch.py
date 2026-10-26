def _consume_home_observer_epoch():
    """Refresh the original helper tokens without two duplicate interpreters."""
    if (xbmc.getSkinDir() != 'skin.infinity.diggz' or
            xbmcgui.getCurrentWindowId() != 10000):
        return False
    continuity = HOME.getProperty('Infinity.Home.Continuity.Pending') == 'true'
    ambient = HOME.getProperty('Infinity.Home.Ambient.Pending') == 'true'
    if not continuity and not ambient:
        return False
    try:
        from module_contract import require_current
        require_current()
        if continuity:
            HOME.setProperty('Infinity.Continuity.HomeLoad', uuid.uuid4().hex)
            HOME.clearProperty('Infinity.Home.Continuity.Pending')
        if ambient:
            HOME.setProperty('Infinity.NativeAmbient.LayoutEpoch', uuid.uuid4().hex)
            HOME.clearProperty('Infinity.Home.Ambient.Pending')
        return True
    except Exception as error:
        # Keep the request pending; never import an unsigned skin helper into
        # the authenticated resident or create a second writer/sampler.
        log('Home observer refresh deferred: ' + type(error).__name__)
        return False
