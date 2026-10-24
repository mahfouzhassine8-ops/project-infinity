"""Infinity Live implementation package."""

# Kodi's Python-created controls do not inherit the skin XML focus graph.
# Install Infinity-owned runtime integrations only inside Kodi; keeping this
# guarded lets parser/provider unit tests run in plain CPython as well.
try:
    import xbmcgui as _xbmcgui  # noqa: F401
except (ImportError, ModuleNotFoundError):
    pass
else:
    from .multiview import install_multiview_hooks
    from .focus import install_focus_contracts

    # Multi-View decorates the Live window first so the focus wrapper sees the
    # seventh action button when each window instance finishes constructing.
    install_multiview_hooks()
    install_focus_contracts()
