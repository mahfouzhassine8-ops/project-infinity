"""Scoped UI adapter changes from the exact signed 2103393 components."""
from __future__ import annotations
import ast
from native94 import once, require


def home_option_b(raw):
    old=b'''        widget = home.getControl(control)
        # If Kodi's panel wrapper does not expose its selected index, do not
        # guess an adjacent poster or treat a stale focus as a touch hit.
        idx = widget.getSelectedPosition()
        if not isinstance(idx, int) or idx < 0 or (native is not None and idx != native.index):
            return None
        count = xbmc.getInfoLabel(f'Container({control}).NumItems')
        if not count.isdecimal() or idx >= int(count):
            return None
'''
    new=b'''        # ControlList.getSelectedPosition reads its Python vecItems. An XML
        # DirectoryProvider panel has no Python-added items, so that API returns
        # -1 even with a real selected poster. Use the actual native labels.
        # CurrentItem is 1-based except when the first row is the parent folder;
        # NumAllItems-NumItems supplies precisely that documented native offset.
        current = xbmc.getInfoLabel(f'Container({control}).CurrentItem')
        count = xbmc.getInfoLabel(f'Container({control}).NumItems')
        total = xbmc.getInfoLabel(f'Container({control}).NumAllItems')
        if not all(value.isdecimal() for value in (current, count, total)):
            _trace(xbmc, 'python.index', 'native_labels_unavailable', control)
            return None
        parent = int(total) - int(count)
        idx = int(current) - 1 + parent
        if parent not in (0, 1) or idx < parent or idx >= int(total) or (native is not None and idx != native.index):
            _trace(xbmc, 'python.index', 'native_index_mismatch', control, idx)
            return None
        _trace(xbmc, 'python.index', 'accepted', control, idx)
'''
    raw=once(raw,old,new)
    anchor=b'PENDING_FIELDS = '
    trace=b'''def _trace(xbmc, stage, outcome, control=-1, index=-1):
    # Event-triggered bounded facts only. No titles, item URLs or private paths.
    try:
        xbmc.log('[InfinityTouch] ' + json.dumps(dict(event='touch.option_b',
            phase=stage, outcome=outcome, control=control, index=index)), xbmc.LOGINFO)
    except (AttributeError, TypeError, RuntimeError):
        pass


'''
    raw=once(raw,anchor,trace+anchor)
    raw=once(raw,b'    snapshot = capture(xbmc, xbmcgui, native)\n    if snapshot is None:\n        return False',
        b"    snapshot = capture(xbmc, xbmcgui, native)\n    if snapshot is None:\n        _trace(xbmc, 'python.capture', 'rejected', native.control, native.index)\n        return False\n    _trace(xbmc, 'python.capture', 'accepted', native.control, native.index)")
    raw=once(raw,b'            self.ready=True',
        b"            self.ready=True\n            _trace(xbmc, 'popup.shown', 'accepted', native.control, native.index)")
    raw=once(raw,b'        window.doModal()',
        b"        _trace(xbmc, 'popup.create', 'requested', native.control, native.index)\n        window.doModal()")
    # The metadata and action revalidation remain unchanged.
    ast.parse(raw.decode())
    return raw


def runtime_trace(raw):
    return once(raw,b'    home = xbmcgui.Window(10000)\n    if home.getProperty(\'Infinity.UI.MenuActive\'):',
        b'''    home = xbmcgui.Window(10000)
    if args and args[0] == 'option-b':
        from home_option_b import _trace
        _trace(xbmc, 'python.entry', 'received')
    if home.getProperty('Infinity.UI.MenuActive'):''')


def settings_entry(raw):
    anchor=b"    action = argv[1].strip().lower()\n"
    return once(raw,anchor,anchor+b'''    if action in ('appearance', 'theme', 'dark-appearance', 'motion-settings', 'ambient-home'):
        from infinity_settings import open_settings
        open_settings(action)
        return True
''')


def tracking_menu(raw):
    anchor=b'    hub = plugin.hub\n    with plugin.persistence_scope():'
    return once(raw,anchor,b"    hub = plugin.hub\n    if op == 'trakt':\n        from infinity_trakt import show_saved\n        return show_saved(key)\n    with plugin.persistence_scope():")
