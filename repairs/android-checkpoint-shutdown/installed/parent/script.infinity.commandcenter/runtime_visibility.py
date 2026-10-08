# SPDX-License-Identifier: GPL-2.0-or-later
"""Read the existing activity-owned atomic gate, without JNI or a player API."""
class ForegroundGate:
    def __init__(self, xbmc):
        self.android = xbmc.getCondVisibility('System.Platform.Android')
        self.allowed = None
        if self.android:
            try:
                import ctypes
                self.library = ctypes.CDLL('libinfinityambient.so')
                self.allowed = self.library.infinity_ambient_allowed
                self.allowed.restype = ctypes.c_int
            except (OSError, AttributeError):
                pass
    def visible(self):
        if not self.android:
            return True
        return self.allowed is not None and self.allowed() == 1
