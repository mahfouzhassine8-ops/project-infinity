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
REGISTERED = (50, 51, 52, 53, 55, 56, 57, 58, 59, 500, 501, 502, 503, 504, 505, 506, 507, 509, 591, 592, 602, 609)
RULES = {50: [()], 506: [('Window.IsActive(videos)', '[Container.Content(movies) | Container.Content(sets) | Container.Content(tvshows) | Container.Content(seasons) | Container.Content(episodes) | Container.Content(artists)] + !Skin.HasSetting(Disable.RightListView)'), ('Window.IsActive(music)', '!Skin.HasSetting(Disable.RightListView)')], 602: [('Window.IsActive(videos)', '[Container.Content(movies) | Container.Content(sets) | Container.Content(tvshows) | Container.Content(seasons) | Container.Content(episodes)] + !Skin.HasSetting(Disable.FanartListView)')], 501: [('Window.IsActive(videos)', '[Container.Content(movies) | Container.Content(sets) | Container.Content(tvshows) | Container.Content(seasons) | Container.Content(episodes)] + !Skin.HasSetting(Disable.LowListView)'), ('Window.IsActive(music)', '[Container.Content(albums) | Container.Content(artists) | Container.Content(songs) | Container.Content(files)] + !Skin.HasSetting(Disable.LowListView)'), ('Window.IsActive(programs)', 'String.Contains(Container.FolderPath,plugin.program.advanced.launcher) + !Skin.HasSetting(Disable.LowListView)')], 507: [('Window.IsActive(videos)', '[Container.Content(movies) | Container.Content(tvshows) | Container.Content(episodes)] + !Skin.HasSetting(Disable.BigListView)'), ('Window.IsActive(music)', '[Container.Content(albums) | Container.Content(artists)] + !Skin.HasSetting(Disable.BigListView)')], 59: [('Window.IsActive(videos) | Window.IsActive(music)', '!Skin.HasSetting(Disable.LogoView)', '[Container.Content(movies) | Container.Content(sets) | Container.Content(tvshows) | Container.Content(artists)]')], 502: [('Window.IsActive(videos)', 'Container.Content(episodes) + !Skin.HasSetting(Disable.EpisodeView)')], 53: [('Window.IsActive(videos)', '[Container.Content(movies) | Container.Content(tvshows) | Container.Content(musicvideos) | Container.Content(seasons) | Container.Content(genres) | Container.Content(sets)] + !Skin.HasSetting(Disable.ShowCaseView)')], 57: [('[Container.Content(movies) | Container.Content(tvshows) | Container.Content(musicvideos) | Container.Content(seasons) | Container.Content(genres) | Container.Content(sets) | Container.Content(addons) | Container.Content(songs) | Container.Content(artists) | Container.Content(albums) | Container.Content(genres)] + !Skin.HasSetting(Disable.ShiftView)',), ('Window.IsActive(programs)', 'String.Contains(Container.FolderPath,plugin.program.advanced.launcher) + !Skin.HasSetting(Disable.LowListView)')], 56: [('Window.IsActive(videos)', '[Container.Content(genres) | Container.Content(tvshows) | Container.Content(movies) | Container.Content(sets) | Container.Content(seasons) | Container.Content(musicvideos)] + !Skin.HasSetting(Disable.PostersView)')], 509: [('Window.IsActive(videos)', '[Container.Content(movies) | Container.Content(sets) | Container.Content(tvshows) | Container.Content(seasons) | Container.Content(episodes)] + !Skin.HasSetting(Disable.MyFlixView)')], 55: [('Window.IsActive(videos)', '[Container.Content(movies) | Container.Content(tvshows) | Container.Content(seasons) | Container.Content(episodes) | Container.Content(sets)] + !Skin.HasSetting(Disable.TriPanelView)'), ('[Window.IsActive(music) | Window.IsActive(addonbrowser)]', '[Container.Content(albums) | Container.Content(artists) | Container.Content(songs) | Container.Content(addons) | Window.IsActive(music) + Container.Content(files)] + !Skin.HasSetting(Disable.TriPanelView)'), ('Window.IsActive(programs)', 'String.Contains(Container.FolderPath,plugin.program.advanced.launcher) + !Skin.HasSetting(Disable.TriPanelView)')], 500: [('!Skin.HasSetting(Disable.IconsView)', '![Window.IsActive(FavouritesBrowser) | Window.IsActive(tvchannels) | Window.IsActive(tvrecordings) | Window.IsActive(tvguide) | Window.IsActive(tvtimers) | Window.IsActive(tvsearch) | Window.IsActive(musicplaylist) | Window.IsActive(radiochannels) | Window.IsActive(radiorecordings) | Window.IsActive(radioguide) | Window.IsActive(radiotimers) | Window.IsActive(radiosearch) | [Window.IsActive(pictures) + Container.Content(addons)]]')], 503: [('Window.IsActive(videos) | Window.IsActive(programs)', '[Container.Content(movies) | Container.Content(sets) | Container.Content(tvshows) | Container.Content(seasons) | Container.Content(addons) | Container.Content(files)] + !Skin.HasSetting(Disable.WallView)'), ('Window.IsActive(music)', '[Container.Content(artists) | Container.Content(albums) | Container.Content(genres) | Container.Content(files) + !Skin.HasSetting(Disable.WallView)]')], 609: [('Window.IsActive(videos)', '[Container.Content(movies) | Container.Content(tvshows) | Container.Content(sets)] + !Skin.HasSetting(Disable.FullscreenWallView)'), ('Window.IsActive(music)', '[Container.Content(artists) | Container.Content(albums)] | [Window.IsActive(music) + Container.Content(files)] + !Skin.HasSetting(Disable.FullscreenWallView)')], 51: [('Window.IsActive(videos)', '[Container.Content(tvshows) | Container.Content(movies)] + !Skin.HasSetting(Disable.InfoWallView)'), ('Window.IsActive(music) | Window.IsActive(addonbrowser) | Window.IsActive(programs)', '[Container.Content(albums) | Container.Content(artists) | Container.Content(addons)]', '!Skin.HasSetting(Disable.InfoWallView)')], 58: [('Window.IsActive(videos)', '[Container.Content(movies) | Container.Content(tvshows)] + !Skin.HasSetting(Disable.BannerWallView)')], 52: [('[Container.Content(movies) | Container.Content(tvshows) | Container.Content(episodes) | Container.Content(artists) | Container.Content(sets)] + !Skin.HasSetting(Disable.LandscapeView)',)], 591: [('[Container.Content(movies) | Container.Content(sets) | Container.Content(tvshows) | Container.Content(seasons)] + !Skin.HasSetting(Disable.BigFanView)',)], 504: [('[Container.Content(movies) | Container.Content(tvshows) | Container.Content(sets) | Window.IsActive(pictures)] + !Skin.HasSetting(Disable.GalleryView)', '![Window.IsActive(pictures) + Container.Content(addons)]')], 505: [('[Container.Content(movies) | Container.Content(tvshows) | Container.Content(episodes)] + !Skin.HasSetting(Disable.PanelView)',)]}


def publish_browser_genres(xbmc, gui):
    """Transient selected-item styling only, on the existing resident tick.

    Kodi's genre label uses its existing human-readable separator. If a source
    supplies another separator or more than four tags, the skin keeps its full
    native genre text. No provider/settings/file access or action dispatch.
    """
    if (xbmc.getSkinDir() != 'skin.infinity.diggz'
            or gui.getCurrentWindowId() != 10025
            or gui.getCurrentWindowDialogId() not in (0, 9999)
            or not xbmc.getCondVisibility('Control.IsVisible(50)')
            or xbmc.getCondVisibility('Container.IsUpdating')):
        return 'inactive'
    source = xbmc.getInfoLabel('Container(50).ListItem.Genre')
    window = gui.Window(10025)
    key = 'Infinity.MediaBrowser.GenreSource'
    if window.getProperty(key) == source:
        return 'unchanged'
    tags = [s.strip() for s in source.split(' / ') if s.strip()]
    # The complete native label remains visible as fallback, never silently cut.
    usable = bool(tags) and len(tags) <= 4
    window.setProperty('Infinity.MediaBrowser.GenreCount', '0')
    window.clearProperty(key)
    for i in range(4):
        window.setProperty('Infinity.MediaBrowser.Genre%s' % (i + 1),
                           tags[i] if usable and i < len(tags) else '')
    if (gui.getCurrentWindowId() != 10025
            or xbmc.getCondVisibility('Container.IsUpdating')
            or xbmc.getInfoLabel('Container(50).ListItem.Genre') != source):
        return 'changed'
    # Publish last: the skin compares this exact native label before using tags.
    window.setProperty(key, source)
    window.setProperty('Infinity.MediaBrowser.GenreCount', str(len(tags) if usable else 0))
    return 'published'


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
            result = self._observe()
        except Exception:
            # A changing window/control is not a reason to interrupt the resident
            # or expose provider paths. Retry only at its next ordinary UI tick.
            self.pending = None
            result = 'unavailable'
        try:
            publish_browser_genres(self.xbmc, self.gui)
        except Exception:
            # Presentation cannot change preference ordering/result or pending work.
            pass
        return result

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
