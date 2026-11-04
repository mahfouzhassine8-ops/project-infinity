"""One explicit media-view preference; observed by the existing UI resident.

No provider execution, file/database access, new thread, timer or setting writer.
The Videos selector owns the preference through native Skin.SetString. Native
SetViewMode retains Kodi's existing item/focus transfer and directory history.
"""
from uuid import uuid4

PREFERENCE = 'Infinity.MediaView.Default'
PROCESSED = 'Infinity.MediaView.Processed'
MEDIA = ('movies', 'tvshows', 'seasons', 'episodes', 'sets', 'musicvideos')
# Populated from the exact signed Videos registration and selector predicates.
REGISTERED = ()  # GENERATED_REGISTRATION
RULES = {}  # GENERATED_RULES


class MediaViewPreference:
    def __init__(self, xbmc, gui):
        self.xbmc = xbmc
        self.gui = gui
        self.pending = None
        self.nonce = uuid4().hex
        self.sequence = 0
        self.ticket = ''

    def _eligible(self):
        return (self.xbmc.getSkinDir() == 'skin.infinity.diggz'
                and self.gui.getCurrentWindowId() == 10025
                and self.gui.getCurrentWindowDialogId() in (0, 9999)
                and not self.xbmc.getCondVisibility('Container.IsUpdating'))

    def _supported(self, view):
        if view not in REGISTERED or view not in RULES:
            return False
        if not any(all(self.xbmc.getCondVisibility(c) for c in conditions)
                   for conditions in RULES[view]):
            return False
        try:
            # Disabled conditional includes can remove a registered control.
            self.gui.Window(10025).getControl(view)
        except (RuntimeError, TypeError):
            return False
        return True

    def tick(self):
        try:
            return self._observe()
        except Exception:
            # A changing window/control is not a reason to interrupt the resident
            # or expose provider paths. Retry only at its next ordinary UI tick.
            self.pending = None
            return 'unavailable'

    def _observe(self):
        if not self._eligible():
            self.pending = None
            return 'inactive'
        media = next((c for c in MEDIA if self.xbmc.getCondVisibility(
            'Container.Content(%s)' % c)), None)
        if media is None:
            self.pending = None
            return 'non-media'
        value = self.xbmc.getInfoLabel('Skin.String(%s)' % PREFERENCE)
        if not value.isdecimal() or int(value) not in REGISTERED:
            # No migration of previous per-path choices; no invalid command.
            self.pending = None
            return 'unset'
        preferred = int(value)
        target = preferred if self._supported(preferred) else 50
        if not self._supported(target):
            self.pending = None
            return 'unsupported'
        current = next((i for i in REGISTERED if self.xbmc.getCondVisibility(
            'Control.IsVisible(%s)' % i)), None)
        if current is None:
            self.pending = None
            return 'not-ready'
        if current == target:
            self.pending = None
            return 'matched' if target == preferred else 'fallback'
        # Keep only the current context in memory, never log/persist its path.
        context = (self.xbmc.getInfoLabel('Container.FolderPath'), media,
                   preferred, target, current)
        if (self.pending == context
                and self.gui.Window(10000).getProperty(PROCESSED) != self.ticket):
            return 'pending'
        # Recheck immediately before asynchronous dispatch. Never wait on Kodi's
        # GUI from the resident or change focus, directory, playback or refresh.
        if (not self._eligible()
                or self.xbmc.getInfoLabel('Skin.String(%s)' % PREFERENCE) != value
                or self.xbmc.getInfoLabel('Container.FolderPath') != context[0]):
            return 'changed'
        self.sequence += 1
        self.ticket = '%s:%s' % (self.nonce, self.sequence)
        self.xbmc.executebuiltin('Container.SetViewMode(%s)' % target)
        # Same FIFO GUI queue: acknowledges processing, not view success. A
        # provider may override the view before the next resident observation.
        # Never wait synchronously, or confuse an old acknowledgement with a
        # new request. This property is transient and contains no media data.
        self.xbmc.executebuiltin('SetProperty(%s,%s,Home)' % (PROCESSED, self.ticket))
        self.pending = context
        return 'requested' if target == preferred else 'requested-fallback'
