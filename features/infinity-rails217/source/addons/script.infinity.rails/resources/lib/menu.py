"""One foreground modal. Native gesture detection; no startup hook or service."""
from contextlib import contextmanager
from pathlib import Path
import threading
import time

from .menu_geometry import layout
from .store import RailError

BACK = (9, 10, 92, 101)


@contextmanager
def menu_lock(profile, name='rails-menu.lock'):
    """Ignore duplicate long presses without leaving a stale lock after process death."""
    import fcntl
    Path(profile).mkdir(parents=True, exist_ok=True)
    with open(Path(profile) / name, 'a+b') as handle:
        acquired = False
        try:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
            except BlockingIOError:
                pass
            yield acquired
        finally:
            if acquired:
                fcntl.flock(handle, fcntl.LOCK_UN)


def select(gui, xbmc, root, heading, subtitle, choices, icon='', initial=0):
    """Return an action key, or None for Back/X/Cancel/configuration change.

    XML comes from the current Infinity skin, with a helper fallback. The bounded
    foreground observer watches only published window facts while THIS modal is
    open. It dismisses on resize/shutdown; it never refreshes widgets or artwork.
    No observer survives dismissal. Native touch/long-press rules remain intact.
    """
    class RailsDialog(gui.WindowXMLDialog):
        def __init__(self, *args, **kwargs):
            self.result = None
            self.done = threading.Event()
            self.observer = None
            self.page = 0
            self.mapping = {}
            self.initial = max(0, min(initial, len(choices) - 1))
            self.metrics = None
            self.opened = time.perf_counter()

        def facts(self):
            home = gui.Window(10000)
            rev = home.getProperty('Infinity.NativeDisplayRevision')
            if home.getProperty('Infinity.NativeReady') == 'false':
                return None
            facts = (self.getWidth(), self.getHeight(),
                     home.getProperty('Infinity.NativeWidthDp'),
                     home.getProperty('Infinity.NativeHeightDp'), rev)
            if home.getProperty('Infinity.NativeReady') == 'false' or home.getProperty('Infinity.NativeDisplayRevision') != rev:
                return None
            return facts

        def onInit(self):
            try:
                self.metrics = self.facts()
                if self.metrics is None:
                    self.close()
                    return
                self.shape = layout(*self.metrics[:4], count=len(choices))
                self.capacity = self.shape['capacity']
                self.page = self.initial // self.capacity
                self.getControl(1).setAnimations(self.shape['animations'])
                self.getControl(2).setHeight(self.shape['design_height'])
                self.setProperty('Rails.Title', heading)
                self.setProperty('Rails.Subtitle', subtitle)
                self.getControl(5).setImage(icon or 'DefaultAddonVideo.png')
                self.render_page(self.initial % self.capacity)
                self.setProperty('Rails.LayoutReady', 'true')
                xbmc.log('Infinity Rails: menu initialized in {:.2f} ms; verified dp={}'.format(
                    (time.perf_counter() - self.opened) * 1000, self.shape['dp_verified']), xbmc.LOGDEBUG)
                if self.observer is None or not self.observer.is_alive():
                    self.observer = threading.Thread(target=self.observe, name='InfinityRailsModalBounds', daemon=True)
                    self.observer.start()
            except Exception:
                self.close()
                raise

        def render_page(self, focus=0):
            self.mapping = {}
            start = self.page * self.capacity
            for i in range(5):
                button = self.getControl(200 + i)
                present = i < self.capacity and start + i < len(choices)
                button.setVisible(present)
                if present:
                    key, label = choices[start + i]
                    button.setLabel(label)
                    self.mapping[200 + i] = key
            paged = self.shape['paged']
            y = 160 + self.shape['rows'] * 100
            for cid in (210, 211, 212):
                self.getControl(cid).setVisible(paged)
                self.getControl(cid).setPosition({210:24, 211:556, 212:208}[cid], y)
            self.getControl(210).setEnabled(self.page > 0)
            self.getControl(211).setEnabled(start + self.capacity < len(choices))
            self.getControl(212).setLabel('{} / {}'.format(self.page + 1, (len(choices) + self.capacity - 1) // self.capacity))
            ids = list(self.mapping) + ([210, 211] if paged else []) + [9]
            ids = [i for i in ids if i != 210 or self.page > 0]
            ids = [i for i in ids if i != 211 or (self.page + 1) * self.capacity < len(choices)]
            for i, cid in enumerate(ids):
                control = self.getControl(cid)
                control.setNavigation(self.getControl(ids[i - 1]), self.getControl(ids[(i + 1) % len(ids)]),
                                      self.getControl(9 if cid != 9 else 200), self.getControl(9 if cid != 9 else 200))
            self.setFocusId(200 + min(focus, max(0, len(self.mapping) - 1)))

        def current(self):
            facts = self.facts()
            return facts is not None and facts == self.metrics

        def observe(self):
            monitor = xbmc.Monitor()
            try:
                while not self.done.wait(.2):
                    if monitor.abortRequested() or not self.current():
                        self.close()
                        return
            except Exception:
                self.close()

        def onClick(self, cid):
            if not self.current():
                self.close()
            elif cid == 9:
                self.close()
            elif cid in (210, 211):
                new_page = self.page + (-1 if cid == 210 else 1)
                if 0 <= new_page <= (len(choices) - 1) // self.capacity:
                    self.page = new_page
                    self.render_page()
            elif cid in self.mapping:
                self.result = self.mapping[cid]
                self.close()

        def onAction(self, action):
            if action.getId() in BACK or not self.current():
                self.close()

        def close(self):
            self.done.set()
            super().close()

    if not choices:
        return None
    dialog = RailsDialog('DialogInfinityRails.xml', str(root), 'Default', '1080i')
    try:
        dialog.doModal()
        return dialog.result
    finally:
        dialog.done.set()
        if dialog.observer is not None:
            dialog.observer.join(timeout=.5)
        dialog.close()
        del dialog
