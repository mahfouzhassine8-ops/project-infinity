"""Infinity Live implementation package."""

# Kodi's Python-created controls do not inherit the skin XML focus graph.
# Install the explicit TV-remote navigation contract only inside Kodi; keeping
# this guarded lets parser/provider unit tests run in plain CPython as well.
try:
    import xbmcgui as _xbmcgui  # noqa: F401
except (ImportError, ModuleNotFoundError):
    pass
else:
    from .focus import install_focus_contracts

    install_focus_contracts()
