"""Explicit D-pad/remote focus graph for Infinity Live Python windows."""


def _wire_live(window):
    labels = ["GUIDE", "FAVORITE", "FULL SCREEN", "MULTI-VIEW", "SOURCES", "REFRESH", "EXIT"]
    buttons = window.buttons
    window.groups.controlRight(window.channels)
    window.channels.controlLeft(window.groups)
    window.channels.controlRight(buttons["FULL SCREEN"])
    window.groups.controlDown(buttons["GUIDE"])
    window.channels.controlDown(buttons["FAVORITE"])
    for index, label in enumerate(labels):
        button = buttons[label]
        button.controlUp(window.channels)
        button.controlLeft(buttons[labels[index - 1]] if index > 0 else window.groups)
        button.controlRight(buttons[labels[index + 1]] if index + 1 < len(labels) else window.channels)


def _wire_guide(window):
    window.channels_list.controlRight(window.programs_list)
    window.programs_list.controlLeft(window.channels_list)


def _wrap_init(cls, marker, wire):
    if getattr(cls, marker, False):
        return
    original = cls.__init__

    def wrapped(self, *args, **kwargs):
        original(self, *args, **kwargs)
        wire(self)

    cls.__init__ = wrapped
    setattr(cls, marker, True)


def install_focus_contracts():
    from .guide import GuideWindow
    from .ui import InfinityLiveWindow

    _wrap_init(InfinityLiveWindow, "_infinity_focus_contract", _wire_live)
    _wrap_init(GuideWindow, "_infinity_focus_contract", _wire_guide)
