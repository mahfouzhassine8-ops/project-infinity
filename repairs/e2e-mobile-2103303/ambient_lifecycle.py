"""Constrain the existing glass sampler without changing playback ownership."""
from native_controls import once


def repair_continuity(text):
    text=once(text,'        monitor = continuity_monitor()', '''        # Reuse the Android activity's existing atomic visibility owner. Keep
        # the bounded monitor queue alive, but suspend optional GUI observation
        # and trace polling while the activity is backgrounded.
        foreground = lambda: True
        if xbmc.getCondVisibility('System.Platform.Android'):
            foreground = lambda: False
            try:
                import ctypes
                foreground_library = ctypes.CDLL('libinfinityambient.so')
                foreground = foreground_library.infinity_ambient_allowed
                foreground.restype = ctypes.c_int
            except (OSError, AttributeError):
                pass
        monitor = continuity_monitor()''')
    return once(text,'''        while not monitor.abortRequested():
            if xbmc.getSkinDir()''','''        while not monitor.abortRequested():
            if not foreground():
                if monitor.waitForAbort(1.0):
                    break
                continue
            if xbmc.getSkinDir()''')


def repair(text):
    text=once(text,'CADENCE = 1.0 / 12.0','CADENCE = 1.0 / 6.0')
    text=once(text,'    def close(self):\n        self.texture_path = None',
              '    def close(self):\n        self.presented = None\n        self.texture_path = None')
    text=once(text,'''    def close(self):
        self.reset()
        self.lib.infinity_ambient_destroy(self.handle)
        self.handle = None''','''    def close(self):
        if self.handle is None:
            return
        self.reset()
        self.lib.infinity_ambient_destroy(self.handle)
        self.handle = None''')
    text=once(text,'        session = Session(lib)\n','')
    text=once(text,'''        while not monitor.abortRequested():
            start = time.monotonic()''','''        while not monitor.abortRequested():
            if xbmc.getSkinDir() != 'skin.infinity.diggz':
                break
            start = time.monotonic()''')
    text=once(text,'''                if key is not None:
                    clear('idle');session.reset();key = None;layout_key = None
                if monitor.waitForAbort(.25):''','''                if session is not None:
                    clear('idle');session.close();session = None;key = None;layout_key = None
                if monitor.waitForAbort(1.0):''')
    text=once(text,'            current_key = identity(observer)','''            if session is None:
                session = Session(lib)
            current_key = identity(observer)''')
    text=once(text,'                current_layout = (profile_key,epoch)','''                # Window-size changes can retain the same profile and epoch.
                # Release the old sampling lease and materials before repainting.
                current_layout = (profile_key,epoch,sw,sh)''')
    text=once(text,'''                if current_layout != layout_key:
                    for glass in session.glass:
                        glass.close()
                    session.glass = []''','''                if current_layout != layout_key:
                    session.reset()''')
    text=once(text,'''                        if not bounds:
                            continue''','''                        if not bounds:
                            if glass.fds or glass.presented is not None:
                                glass.close()
                            continue''')
    return text
