"""Observe Kodi's existing video; paint only skin-owned glass illumination.

The APK library shares Cobra's directional rendering arithmetic. RAM-backed PNGs
contain only the tiny blurred edge field, never screenshots or video previews.
No transport/resolver/provider calls. No permanent cache or additional add-on.
"""
import ctypes
import hashlib
import json
import os
import time
import uuid
import xbmc
import xbmcgui
import xbmcvfs

PREFIX = 'Infinity.NativeAmbient.'
CADENCE = 1.0 / 12.0
CAPTURE_WAIT_MS = 50
MAX_CAPTURE_MISSES = 12
MAX_SURFACES = 24
MAX_FRAME_AGE = 1.0
HOME = 10000


def ambient_eligible(lib, home):
    # Kodi's actual idle owner takes precedence over Home glass sampling.
    return (not xbmc.getCondVisibility('System.ScreenSaverActive') and
            lib.infinity_ambient_allowed() == 1 and
            xbmcgui.getCurrentWindowId() == HOME and
            home.getProperty('Infinity.AmbientHome.Mode').lower() == 'immersive' and
            xbmc.getCondVisibility('Player.HasVideo + Control.IsVisible(29900)'))


def native_library():
    # Main loads the APK's library. Resolve that exact mapped image rather than
    # loading a skin-supplied binary or inspecting any playback/provider data.
    paths = ['libinfinityambient.so']
    try:
        with open('/proc/self/maps', encoding='utf-8') as maps:
            for line in maps:
                path = line.rstrip().split(None, 5)[-1]
                if path.startswith('/') and path.endswith('/libinfinityambient.so'):
                    paths.insert(0, path)
                    break
    except OSError:
        pass
    for path in paths:
        try:
            lib = ctypes.CDLL(path)
            lib.infinity_ambient_create.restype = ctypes.c_void_p
            lib.infinity_ambient_destroy.argtypes = [ctypes.c_void_p]
            lib.infinity_ambient_reset.argtypes = [ctypes.c_void_p]
            lib.infinity_ambient_feed.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                                 ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
            lib.infinity_ambient_tile.argtypes = [ctypes.c_void_p] + [ctypes.c_float]*4 + [
                ctypes.c_int, ctypes.c_int, ctypes.c_float, ctypes.c_float,
                ctypes.POINTER(ctypes.c_void_p)]
            lib.infinity_ambient_surface_request.argtypes = [ctypes.c_int]
            lib.infinity_ambient_surface_request.restype = ctypes.c_uint64
            lib.infinity_ambient_surface_read.argtypes = [ctypes.c_uint64, ctypes.c_void_p,
                ctypes.c_int, ctypes.POINTER(ctypes.c_uint64),
                ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
            if lib.infinity_ambient_version() == 1 and lib.infinity_ambient_surface_version() == 1:
                return lib
        except (OSError, AttributeError):
            continue
    raise RuntimeError('APK 2103284 ambient surface bridge required')


class Observer(xbmc.Player):
    """Playback callbacks only invalidate colors; never control the player."""
    def __init__(self):
        super().__init__()
        self.epoch = 0

    def onAVStarted(self):
        self.epoch += 1

    def onPlayBackStarted(self):
        self.epoch += 1

    def onPlayBackSeek(self, time, seekOffset):
        self.epoch += 1

    def onPlayBackSeekChapter(self, chapter):
        self.epoch += 1

    def onPlayBackStopped(self):
        self.epoch += 1

    def onPlayBackEnded(self):
        self.epoch += 1

    def onPlayBackError(self):
        self.epoch += 1


class DialogMirror:
    """Render the same live palette at the dialog's OWN window-relative bounds.

    One additional three-fd material ring; no extra capture/decoder or provider.
    """
    glass = None
    dialog = None
    signature = None

    @classmethod
    def clear(cls):
        glass, cls.glass = cls.glass, None
        cls.dialog = cls.signature = None
        if glass is not None:
            glass.close()

    @classmethod
    def present(cls, session, sw, sh, appearance, changed, layout_key):
        dialog = xbmcgui.getCurrentWindowDialogId()
        if dialog not in (11198, 10111, 11191) or not session.ready:
            cls.clear()
            return
        if cls.dialog != dialog:
            cls.clear()
            try:
                cls.glass = Glass(xbmcgui.Window(dialog),
                    {'overlay':1198880,'parents':[1198888],
                     'probes':[1198888],'radius':24}, session.lib)
                cls.dialog = dialog
            except Exception:
                cls.clear()
                return
        try:
            # The active modal is an explicit owner. A global Control.IsVisible
            # lookup can resolve against Home instead of this modal window.
            owner = cls.glass.home.getControl(1198888)
            ox,oy = owner.getPosition()
            x,y = cls.glass.control.getPosition()
            bounds = (ox+x,oy+y,cls.glass.control.getWidth(),cls.glass.control.getHeight())
            if not bounds or sw <= 0 or sh <= 0:
                cls.clear()
                return
            signature = (dialog,layout_key,appearance,sw,sh,bounds)
            if not changed and cls.signature == signature:
                return
            x,y,w,h = bounds
            if w <= 0 or h <= 0:
                cls.clear()
                return
            scale = min(144.0/w,144.0/h,1.0)
            tw,th = max(2,round(w*scale)),max(2,round(h*scale))
            ptr = ctypes.c_void_p()
            count = session.lib.infinity_ambient_tile(session.handle,
                x/sw,y/sh,(x+w)/sw,(y+h)/sh,tw,th,
                24*scale,1.5*scale,ctypes.byref(ptr))
            if count <= 0 or count > 144*144*5:
                cls.clear()
                return
            cls.glass.present(ptr.value,count)
            cls.signature = signature
        except Exception:
            cls.clear()


class Glass:
    def __init__(self, home, spec, lib):
        self.home, self.spec, self.lib = home, spec, lib
        self.control = home.getControl(spec['overlay'])
        self.fds = []
        self.slot = 0
        self.presented = None
        self.texture_path = None

    def allocate(self):
        if self.fds:
            return
        try:
            for _ in range(3):
                fd = self.lib.infinity_ambient_memfd()
                if fd < 0:
                    raise RuntimeError('memory texture unavailable')
                self.fds.append(fd)
        except Exception:
            self.close()
            raise

    def bounds(self):
        if not all(xbmc.getCondVisibility('Control.IsVisible(%d)' % cid)
                   for cid in self.spec['probes']):
            return None
        x, y = self.control.getPosition()
        for cid in self.spec['parents']:
            px, py = self.home.getControl(cid).getPosition()
            x, y = x+px, y+py
        w, h = self.control.getWidth(), self.control.getHeight()
        return (x, y, w, h) if w > 0 and h > 0 else None

    def present(self, ptr, size):
        self.allocate()
        fd = self.fds[self.slot]
        self.slot = (self.slot+1) % len(self.fds)
        os.lseek(fd, 0, os.SEEK_SET)
        data = memoryview((ctypes.c_ubyte * size).from_address(ptr)).cast('B')
        written = 0
        while written < size:
            written += os.write(fd, data[written:])
        os.ftruncate(fd, size)
        # Alternate a bounded three-slot RAM ring and explicitly bypass Kodi's
        # texture cache. Reusing one filename would silently freeze CGUIImage.
        self.texture_path = '/proc/self/fd/%d' % fd
        self.control.setImage(self.texture_path, False)

    def close(self):
        self.texture_path = None
        try:
            self.control.setImage('', False)
        except Exception:
            pass
        for fd in self.fds:
            os.close(fd)
        self.fds = []


class SurfaceFrames:
    """Leased native mailbox; a request cannot outlive a dead/paused skin observer."""
    def __init__(self, lib):
        self.lib = lib
        self.buffer = (ctypes.c_ubyte * (144*144*4))()
        self.token = 0
        self.serial = 0
        self.changed_generation = False

    def release(self):
        self.lib.infinity_ambient_surface_request(0)
        self.token = self.serial = 0

    def poll(self):
        token = self.lib.infinity_ambient_surface_request(1)
        self.changed_generation = token != self.token
        if self.changed_generation:
            self.token, self.serial = token, 0
        if not token:
            return None
        serial, width, height = ctypes.c_uint64(), ctypes.c_int(), ctypes.c_int()
        size = self.lib.infinity_ambient_surface_read(token, self.buffer, len(self.buffer),
            ctypes.byref(serial), ctypes.byref(width), ctypes.byref(height))
        if size <= 0 or serial.value == self.serial:
            return None
        if width.value != 144 or not 48 <= height.value <= 144 or size != 144*height.value*4:
            raise RuntimeError('invalid video surface dimensions')
        self.serial = serial.value
        return bytearray(self.buffer[:size]), height.value


class Session:
    def __init__(self, lib):
        self.lib = lib
        self.handle = lib.infinity_ambient_create()
        if not self.handle:
            raise RuntimeError('ambient allocation unavailable')
        self.surface = SurfaceFrames(lib)
        self.capture = None
        self.source = None
        self.last_good = 0.0
        self.height = 0
        self.fresh = 0
        self.capture_misses = 0
        self.ready = False
        self.glass = []
        self.last_frame = None
        self.last_light = None
        self.presented = None

    def reset(self):
        DialogMirror.clear()
        self.lib.infinity_ambient_reset(self.handle)
        self.surface.release()
        self.source = None
        self.last_good = 0.0
        self.capture = None  # RenderCapture destructor releases the native capture.
        self.height = 0
        self.fresh = 0
        self.capture_misses = 0
        self.ready = False
        self.last_frame = None
        self.last_light = None
        self.presented = None
        for glass in self.glass:
            glass.close()
        self.glass = []

    def close(self):
        self.reset()
        self.lib.infinity_ambient_destroy(self.handle)
        self.handle = None


def light(home):
    return (home.getProperty('Infinity.SystemTheme') or
            home.getProperty('Infinity.NativeSystemTheme')).lower() == 'light'


def identity(observer):
    # Digest stays inside this observer. Never publish a source URL or token.
    title = '\x1f'.join(xbmc.getInfoLabel(k) for k in (
        'Player.FilenameAndPath', 'VideoPlayer.Title', 'VideoPlayer.TVShowTitle',
        'VideoPlayer.Season', 'VideoPlayer.Episode'))
    return (observer.epoch, hashlib.sha256(title.encode('utf-8')).digest())


def main():
    home = xbmcgui.Window(HOME)
    home.setProperty(PREFIX+'LayoutEpoch',uuid.uuid4().hex)
    # One process-wide advisory lock, released by the OS on interpreter exit.
    # A Home re-entry never starts a competing sampler.
    import fcntl
    lockpath = xbmcvfs.translatePath('special://temp/infinity-native-ambient.lock')
    lock = open(lockpath, 'a')
    try:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        lock.close()
        return
    monitor, observer = xbmc.Monitor(), Observer()
    session = None
    def clear(status):
        home.clearProperty(PREFIX+'Active')
        home.setProperty(PREFIX+'Status', status)
    try:
        clear('waiting')
        lib = native_library()
        session = Session(lib)
        with open(xbmcvfs.translatePath('special://skin/resources/lib/infinity_native_glass.json'), encoding='utf-8') as f:
            profiles = json.load(f)
        key = None
        layout_key = None
        cooldown = 0
        while not monitor.abortRequested():
            start = time.monotonic()
            eligible = ambient_eligible(lib, home)
            if not eligible:
                if key is not None:
                    clear('idle');session.reset();key = None;layout_key = None
                if monitor.waitForAbort(.25):
                    break
                continue
            current_key = identity(observer)
            if current_key != key:
                clear('waiting-frame');session.reset();key=current_key;layout_key=None
            try:
                # The declared GUI viewport comes from the actual selected skin
                # profile. Android/Kodi already map it to current window bounds.
                epoch=home.getProperty(PREFIX+'LayoutEpoch')
                if layout_key is None or epoch!=layout_key[1]:
                    home=xbmcgui.Window(HOME)
                viewport = home.getControl(39799)
                sw, sh = viewport.getWidth(), viewport.getHeight()
                profile_key = home.getProperty(PREFIX+'Profile')
                current_layout = (profile_key,epoch)
                if current_layout != layout_key:
                    for glass in session.glass:
                        glass.close()
                    session.glass = []
                    home = xbmcgui.Window(HOME)
                    for spec in profiles[profile_key]:
                        session.glass.append(Glass(home,spec,lib))
                    layout_key = current_layout
                    session.presented = None
                held = xbmc.getCondVisibility('Player.Paused | Player.Caching')
                appearance = light(home)
                changed = False
                if not held or not session.ready:
                    source = 'mediacodec-surface' if lib.infinity_ambient_surface_present() == 1 else 'kodi-rendercapture'
                    home.setProperty(PREFIX+'Source', source)
                    if source != session.source:
                        session.surface.release()
                        session.capture = None
                        session.fresh = 0
                        session.ready = False
                        session.last_good = 0.0
                        session.capture_misses = 0
                        session.last_frame = None
                        lib.infinity_ambient_reset(session.handle)
                        clear('waiting-frame')
                        session.source = source
                    frame = None
                    if source == 'mediacodec-surface':
                        result = session.surface.poll()
                        if session.surface.changed_generation:
                            session.fresh = 0
                            session.capture_misses = 0
                            session.ready = False
                            session.last_frame = None
                            session.last_good = 0.0
                            lib.infinity_ambient_reset(session.handle)
                            clear('waiting-video-surface')
                        if result is not None:
                            frame, session.height = result
                    else:
                        if session.capture is None:
                            session.capture = xbmc.RenderCapture()
                            aspect = float(session.capture.getAspectRatio())
                            if not .2 <= aspect <= 5:
                                raise RuntimeError('capture aspect unavailable')
                            session.height = max(48,min(144,round(144/aspect)))
                            session.capture.capture(144,session.height)
                            session.fresh = 0
                            if session.capture.getImageFormat() != 'BGRA':
                                raise RuntimeError('unsupported capture format')
                        try:
                            frame = session.capture.getImage(CAPTURE_WAIT_MS)
                        except RuntimeError:
                            frame = None
                    if identity(observer) != key:
                        raise RuntimeError('capture session changed')
                    if frame is None or len(frame) != 144*session.height*4:
                        session.capture_misses += 1
                        if session.ready and time.monotonic()-session.last_good <= MAX_FRAME_AGE:
                            home.setProperty(PREFIX+'Status','waiting-fresh-frame')
                        else:
                            if session.ready:
                                lib.infinity_ambient_reset(session.handle)
                                session.fresh = 0
                                session.last_frame = None
                            session.ready = False
                            error_code = lib.infinity_ambient_surface_error() if source == 'mediacodec-surface' else 0
                            home.setProperty(PREFIX+'CaptureError',str(error_code))
                            clear('video-surface-unavailable' if error_code else
                                  ('waiting-video-surface' if source == 'mediacodec-surface' else 'warming-frame'))
                        if source == 'kodi-rendercapture' and session.capture_misses >= MAX_CAPTURE_MISSES:
                            raise RuntimeError('capture warmup timed out')
                    else:
                        session.capture_misses = 0
                        home.clearProperty(PREFIX+'CaptureError')
                        home.clearProperty(PREFIX+'Error')
                        session.fresh += 1
                        if session.fresh > 2:
                            raw = (ctypes.c_ubyte * len(frame)).from_buffer(frame) if isinstance(frame,bytearray) else ctypes.create_string_buffer(frame)
                            session.ready = bool(lib.infinity_ambient_feed(session.handle,raw,len(frame),144,session.height,int(appearance)))
                            session.last_frame = frame
                            session.last_light = appearance
                            session.last_good = time.monotonic()
                            changed = session.ready
                elif appearance != session.last_light and session.last_frame is not None:
                    frame = session.last_frame
                    raw = (ctypes.c_ubyte * len(frame)).from_buffer(frame) if isinstance(frame,bytearray) else ctypes.create_string_buffer(frame)
                    session.ready = bool(lib.infinity_ambient_feed(session.handle,raw,len(frame),144,session.height,int(appearance)))
                    session.last_light = appearance
                    changed = True
                if held and session.ready:
                    session.capture = None
                    session.surface.release()
                if session.ready:
                    visible = 0
                    for glass in session.glass:
                        bounds = glass.bounds()
                        if not bounds:
                            continue
                        visible += 1
                        if visible > MAX_SURFACES:
                            raise RuntimeError('surface budget exceeded')
                        signature = (layout_key, appearance, sw, sh, bounds)
                        if not changed and glass.presented == signature:
                            continue
                        x,y,w,h = bounds
                        scale = min(144.0/w,144.0/h,1.0)
                        tw,th = max(2,round(w*scale)),max(2,round(h*scale))
                        ptr = ctypes.c_void_p()
                        count = lib.infinity_ambient_tile(session.handle,x/sw,y/sh,(x+w)/sw,(y+h)/sh,
                            tw,th,glass.spec['radius']*scale,1.5*scale,ctypes.byref(ptr))
                        if count <= 0 or count > 144*144*5:
                            raise RuntimeError('ambient rendering unavailable')
                        glass.present(ptr.value,count)
                        glass.presented = signature
                    session.presented = (layout_key, appearance, sw, sh)
                    if visible:
                        DialogMirror.present(session,sw,sh,appearance,changed,layout_key)
                        home.setProperty(PREFIX+'Active','true')
                        home.setProperty(PREFIX+'Status','held' if held else ('active' if changed else 'waiting-fresh-frame'))
                        home.setProperty(PREFIX+'Surfaces',str(visible))
                    else:
                        DialogMirror.clear()
                        clear('no-visible-materials')
                cooldown = 0
            except Exception as error:
                home.setProperty(PREFIX+'Error',type(error).__name__)
                clear('unavailable');session.reset();key=None;layout_key=None
                cooldown=min(3,cooldown+1)
                if monitor.waitForAbort(.5*cooldown):
                    break
                continue
            # Work time counts toward cadence. Slow capture/GUI naturally yields;
            # no queue, frame catch-up or work on Kodi's playback thread.
            delay=max(CADENCE-(time.monotonic()-start),.02)
            if held:
                delay=max(delay,.25)
            if monitor.waitForAbort(delay):
                break
    except Exception as error:
        home.setProperty(PREFIX+'Error',type(error).__name__)
        clear('native-update-required' if session is None else 'unavailable')
    finally:
        DialogMirror.clear()
        home.clearProperty(PREFIX+'Active')
        if session:
            session.close()
        lock.close()


if __name__ == '__main__':
    main()
