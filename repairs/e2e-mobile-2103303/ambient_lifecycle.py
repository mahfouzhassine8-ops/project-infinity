"""Constrain the existing glass sampler without changing playback ownership."""
from native_controls import once


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
