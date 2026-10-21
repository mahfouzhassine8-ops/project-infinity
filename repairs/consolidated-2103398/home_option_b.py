"""Group #3 only: Option B movie/TV top-rail details, on demand, fail closed.

This module has NO default/event/keymap registration. It cannot intercept a
long-press by itself; the exact per-poster native context dispatch must first
be proven without changing Cobra or another Home control.

Never import a provider, seek streams, scrape metadata or mutate playback on
focus. Only an explicit action within the approved modal can do anything.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import hmac
import json
import os
import time
import threading
from pathlib import Path
import re
from urllib.parse import urlsplit

from latest_identity import BASE as LATEST_BASE, MAX_IDENTITY, decode as decode_latest

CONTROLS = {8101: 'movies', 8102: 'tvshows', 8801: 'movies', 8802: 'tvshows'}
ACTIONS = {101: 'play', 102: 'trailer', 103: 'favorite', 104: 'more-info'}
APPROVED_ORDER = ('Play', 'Trailer', 'Favorite', 'More Info')
CANCEL_ACTION_IDS = (10, 92, 110)
MAX_METADATA_LENGTH = 2400


def _safe(value: str, limit: int = MAX_METADATA_LENGTH) -> str:
    if not isinstance(value, str):
        return ''
    return ''.join(c for c in value if c >= ' ' or c in '\n\t')[:limit].strip()


def _media_path(path: str) -> bool:
    """Do not construct, rewrite or evaluate dynamic Kodi actions or paths."""
    path = _safe(path, 4096)
    if not path or any(c in path for c in '\r\n\x00'):
        return False
    return path.startswith(('plugin://', 'videodb://', 'smb://', 'nfs://', 'special://', 'file://', '/'))


def _trailer_path(path: str) -> bool:
    path = _safe(path, 4096)
    if not path or any(c in path for c in '\r\n\x00'):
        return False
    # This is an already returned ListItem.Trailer URL, never a fabricated link.
    if path.startswith('plugin://'):
        parsed = urlsplit(path)
        return bool(re.fullmatch(r'[a-zA-Z0-9._-]+', parsed.netloc))
    return path.startswith('https://')


@dataclass(frozen=True)
class Selection:
    control: int
    index: int
    section: str
    path: str
    title: str
    poster: str = ''
    year: str = ''
    media_type: str = ''
    season: str = ''
    episode: str = ''
    episode_title: str = ''
    certification: str = ''
    runtime: str = ''
    rating: str = ''
    genres: str = ''
    synopsis: str = ''
    trailer: str = ''
    is_folder: bool = False
    release_date: str = ''
    credits: str = ''

    def identity(self) -> tuple:
        # Full identity, not just title or screenshot position. Same movie titles
        # with different paths are distinct. Never invent TMDb/season metadata.
        return (self.control, self.index, self.section, self.path, self.title,
                self.year, self.media_type, self.season, self.episode,
                self.is_folder, self.trailer)

    def properties(self) -> dict:
        verified_episode = (self.section == 'tvshows' and self.media_type == 'episode' and
                            self.season.isdigit() and self.episode.isdigit())
        more = 'S%s E%s' % (self.season, self.episode) if verified_episode else ''
        if verified_episode and self.episode_title:
            more += '  •  ' + self.episode_title
        label = self.year if self.year.isdigit() else ''
        if more:
            label = (label + '   •   ' + more).strip(' •')
        return {
            'Title': self.title,
            'Poster': self.poster,
            'YearAndEpisode': label,
            'Certification': self.certification,
            'Runtime': self.runtime,
            'Rating': self.rating,
            'Genres': self.genres,
            'Synopsis': self.synopsis,
            'ReleaseDate': self.release_date,
            'Credits': self.credits,
            'PlayAvailable': 'true' if _media_path(self.path) else 'false',
            'TrailerAvailable': 'true',
            'FavoriteAvailable': 'true' if _media_path(self.path) else 'false',
            'InfoAvailable': 'true' if _media_path(self.path) else 'false',
        }



@dataclass(frozen=True)
class NativeHold:
    control: int
    index: int
    path: str
    label: str
    proof: str


def _trace(xbmc, stage, outcome, control=-1, index=-1):
    # Event-triggered bounded facts only. No titles, item URLs or private paths.
    try:
        xbmc.log('[InfinityTouch] ' + json.dumps(dict(event='touch.option_b',
            phase=stage, outcome=outcome, control=control, index=index,
            pid=os.getpid(), tid=threading.get_native_id(), epoch_ns=time.time_ns(),
            monotonic_ns=time.monotonic_ns())), xbmc.LOGINFO)
    except (AttributeError, TypeError, RuntimeError):
        pass


PENDING_FIELDS = ('Control', 'Index', 'Path', 'Label', 'Proof')


def read_native_hold(xbmcgui, args) -> NativeHold | None:
    """Require the exact C++ touch-hit item; never use stale Home focus alone."""
    if len(args) != 3 or args[0] not in tuple(str(value) for value in CONTROLS):
        return None
    if not isinstance(args[1], str) or not re.fullmatch(r'\d{1,3}', args[1]):
        return None
    if not isinstance(args[2], str) or not re.fullmatch(r'[a-f0-9]{64}', args[2]):
        return None
    try:
        home = xbmcgui.Window(10000)
        fields = {field: home.getProperty('Infinity.HomeOptionB.Pending' + field)
                  for field in PENDING_FIELDS}
        control = int(args[0])
        index = int(args[1])
        if control not in CONTROLS or index < 0 or index > 200:
            return None
        path, label = fields['Path'], fields['Label']
        if (fields['Control'] != args[0] or fields['Index'] != args[1] or
                fields['Proof'] != args[2] or not _media_path(path) or
                not path.startswith(('plugin://plugin.video.umbrella/', LATEST_BASE)) or
                len(path.encode('utf-8')) > (MAX_IDENTITY if path.startswith(LATEST_BASE) else 4096) or not label or len(label) > 512):
            return None
        if path.startswith(LATEST_BASE):
            verified = decode_latest(path)
            if verified['kind'] != ('movie' if CONTROLS[control] == 'movies' else 'tvshow'):
                return None
        message = f'{control}\n{index}\n{path}\n{label}'
        actual = hashlib.sha256(message.encode('utf-8')).hexdigest()
        if not hmac.compare_digest(actual, args[2]):
            return None
        return NativeHold(control, index, path, label, actual)
    except (AttributeError, TypeError, ValueError, RuntimeError):
        return None


def clear_native_hold(xbmcgui, native: NativeHold):
    """Only consume the matching one-shot hold; never clear unrelated Home state."""
    try:
        home = xbmcgui.Window(10000)
        prefix = 'Infinity.HomeOptionB.Pending'
        if hmac.compare_digest(home.getProperty(prefix + 'Proof'), native.proof):
            for field in PENDING_FIELDS:
                home.clearProperty(prefix + field)
    except (AttributeError, RuntimeError):
        pass


def capture(xbmc, xbmcgui, native: NativeHold | None = None) -> Selection | None:
    """Read only the actually focused top poster, with its native list index."""
    if xbmcgui.getCurrentWindowId() != 10000:
        _trace(xbmc, 'python.window', 'not_home')
        return None
    if xbmcgui.getCurrentWindowDialogId() not in (0, -1, 9999):
        _trace(xbmc, 'python.window', 'modal_active')
        return None
    home = xbmcgui.Window(10000)
    try:
        control = home.getFocusId()
        if control not in CONTROLS or (native is not None and control != native.control):
            _trace(xbmc, 'python.focus', 'mismatch', control)
            return None
        section = _safe(xbmc.getInfoLabel('Container(9000).ListItem.Property(section)'), 50)
        if section != CONTROLS[control]:
            _trace(xbmc, 'python.section', 'mismatch', control)
            return None
        # ControlList.getSelectedPosition reads its Python vecItems. An XML
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
        prefix = f'Container({control}).ListItem.'
        def info(name: str, maxlen: int = MAX_METADATA_LENGTH) -> str:
            return _safe(xbmc.getInfoLabel(prefix + name), maxlen)
        observed_label = info('Label')
        title = info('Title') or observed_label
        path = info('FileNameAndPath',MAX_IDENTITY) or info('FolderPath',MAX_IDENTITY)
        if native is not None:
            # Native source is the hit-tested CFileItem, not an inferred stream.
            if observed_label and observed_label != native.label:
                _trace(xbmc, 'python.label', 'mismatch', control, idx)
                return None
            if path and path != native.path:
                _trace(xbmc, 'python.path', 'mismatch', control, idx)
                return None
            path = native.path
            if not title:
                title = native.label
        if not title or not _media_path(path):
            _trace(xbmc, 'python.metadata', 'missing', control, idx)
            return None
        poster = info('Art(poster)',2048) or info('Thumb',2048)
        media_type = info('DBTYPE',40).casefold() or info('Property(MediaType)',40).casefold()
        season = info('Season',6)
        episode = info('Episode',6)
        if media_type != 'episode':
            season = episode = ''
        if path.startswith(LATEST_BASE):
            verified = decode_latest(path)
            if verified['kind'] != media_type or info('Property(Infinity.LatestReleases.Identity)',8) != 'v1':
                return None
        return Selection(control=control,index=idx,section=section,path=path,
                         title=title,poster=poster,year=info('Year',5),
                         media_type=media_type,season=season,episode=episode,
                         episode_title=info('EpisodeName',120) if media_type=='episode' else '',
                         certification=info('MPAA',40),runtime=info('Duration',40),
                         rating=info('Rating',40),genres=info('Genre',160),
                         synopsis=info('Plot',65536),trailer=info('Trailer',4096),
                         release_date=info('Premiered',40),
                         credits=' • '.join(v for v in (info('Director',1200), info('Studio',600)) if v),
                         is_folder=bool(xbmc.getCondVisibility(
                             f'Container({control}).ListItem.IsFolder')))
    except (AttributeError, TypeError, ValueError, RuntimeError):
        return None


def geometry(width, height, physical_width='', physical_height='', expanded=False):
    """Keep the reference card's horizontal structure; give cover text real room."""
    width, height = max(1, int(width)), max(1, int(height))
    try:
        pw, ph = int(physical_width), int(physical_height)
        if min(pw, ph) < 200: raise ValueError()
    except (TypeError, ValueError):
        pw, ph = width, height
    ratio = (height * pw) / (width * ph)
    available_h = height / ratio
    landscape = pw > ph * 1.45
    cw = min(width * (.60 if landscape else .94), available_h * 2.8)
    ch = min(cw * (.78 if expanded else (.36 if landscape else .50)), available_h * .86)
    pad, gap = cw * .024, cw * .018
    close, bh = cw * .055, max(cw * .072, width * (.108 if not landscape else .054))
    poster_h = min(ch - 2*pad, cw*.40)
    poster_w = poster_h * 2/3
    tx, tw = pad+poster_w+gap, cw-(pad+poster_w+gap)-pad
    ay = ch-pad-bh
    bw = (tw-3*gap)/4
    def rect(x,y,w,h): return tuple(round(v) for v in (x,y*ratio,w,h*ratio))
    my, mh = pad+cw*.064, cw*.047
    sy = my+mh+gap
    details = {
        'poster':rect(pad,pad,poster_w,poster_h),
        'title':rect(tx,pad,tw-close-gap,cw*.060),
        'year':rect(tx,my,tw*.16,mh),
        'certification':rect(tx+tw*.17,my,tw*.15,mh),
        'runtime':rect(tx+tw*.33,my,tw*.20,mh),
        'rating':rect(tx+tw*.54,my,tw*.12,mh),
        'genres':rect(tx+tw*.67,my,tw*.33,mh),
        'synopsis':rect(tx,sy,tw,ay-gap-sy),
    }
    return dict(x=round((width-cw)/2), y=round((height-ch*ratio)/2),
        width=round(cw), height=round(ch*ratio), compact=False,
        details=details,surface=rect(0,0,cw,ch),close=rect(cw-pad-close,pad,close,close),
        buttons=[rect(tx+i*(bw+gap),ay,bw,bh) for i in range(4)])


def _rpc(xbmc, method: str, params: dict) -> dict:
    response = json.loads(xbmc.executeJSONRPC(json.dumps(
        {'jsonrpc':'2.0','id':1,'method':method,'params':params})))
    if 'error' in response:
        raise RuntimeError('Kodi did not complete '+method)
    return response.get('result',{})


def _perform(xbmc, gui, selected: Selection, action: str, native: NativeHold | None = None) -> bool:
    """Only a verified, explicit button press may dispatch; never on focus."""
    if native is not None and read_native_hold(gui, (str(native.control), str(native.index), native.proof)) != native:
        return False
    active = capture(xbmc, gui, native)
    if active is None or active.identity()!=selected.identity():
        return False
    if action == 'play':
        # Preserves original provider CDirectoryProvider::OnClick path/chooser,
        # instead of synthesizing an Umbrella source/episode or autoplaying.
        xbmc.executebuiltin('Action(Select)')
        return True
    if action == 'favorite' and _media_path(selected.path):
        # Kodi's own Favourites JSON-RPC; no Infinity/trakt/watched database.
        kind = 'window' if selected.is_folder else 'media'
        target = decode_latest(selected.path)['route'] if selected.path.startswith(LATEST_BASE) else selected.path
        params = {'title':selected.title,'type':kind,'thumbnail':selected.poster}
        if kind == 'window':
            params.update(window='Videos',windowparameter=target)
        else:
            params['path'] = target
        # Kodi's AddFavourite calls AddOrRemove; repeating toggles this exact route.
        _rpc(xbmc,'Favourites.AddFavourite',params)
        return True
    if action == 'trailer' and not _trailer_path(selected.trailer):
        gui.Dialog().ok('Infinity Trailer', 'No trailer is available for this title.')
        return True
    if action == 'trailer' and _trailer_path(selected.trailer):
        # Only a provider-supplied ListItem.Trailer, after explicit selection.
        xbmc.Player().play(selected.trailer)
        return True
    return False


def show_for_focused_top_poster(native_args) -> bool:
    """Called ONLY by a token-verified native one-pointer top-poster hold."""
    import xbmc
    import xbmcaddon
    import xbmcgui
    import xbmcvfs
    native = read_native_hold(xbmcgui, native_args)
    if native is None:
        _trace(xbmc, 'python.proof', 'rejected')
        return False
    _trace(xbmc, 'python.proof', 'accepted', native.control, native.index)
    try:
        return _show_verified_hold(xbmc, xbmcaddon, xbmcgui, xbmcvfs, native)
    finally:
        clear_native_hold(xbmcgui, native)


def _show_verified_hold(xbmc, xbmcaddon, xbmcgui, xbmcvfs, native: NativeHold) -> bool:
    snapshot = capture(xbmc, xbmcgui, native)
    if snapshot is None:
        _trace(xbmc, 'python.capture', 'rejected', native.control, native.index)
        return False
    _trace(xbmc, 'python.capture', 'accepted', native.control, native.index)
    props = snapshot.properties()
    root = Path(xbmcvfs.translatePath(xbmcaddon.Addon('script.infinity.uirepair').getAddonInfo('path')))
    class OptionB(xbmcgui.WindowXMLDialog):
        selected_action = None
        ready = False
        expanded = False
        def onInit(self):
            for name,value in props.items():
                self.setProperty('Infinity.HomeOptionB.'+name,value)
            # backdrop is the true Kodi window; reflow on each open/fold.
            background=self.getControl(2)
            bounds=geometry(background.getWidth(),background.getHeight(),
                xbmc.getInfoLabel('System.ScreenWidth'), xbmc.getInfoLabel('System.ScreenHeight'), self.expanded)
            card=self.getControl(100)
            card.setPosition(bounds['x'],bounds['y'])
            card.setWidth(bounds['width'])
            card.setHeight(bounds['height'])
            for ident,key in ((112,'poster'),(120,'title'),(121,'year'),
                              (122,'certification'),(123,'runtime'),
                              (124,'rating'),(125,'genres'),(126,'synopsis')):
                ctrl=self.getControl(ident)
                xx,yy,ww,hh=bounds['details'][key]
                ctrl.setPosition(xx,yy)
                ctrl.setWidth(ww);ctrl.setHeight(hh)
            for ident,key in ((110,'surface'),(111,'surface'),(9,'close')):
                ctrl=self.getControl(ident)
                xx,yy,ww,hh=bounds[key]
                ctrl.setPosition(xx,yy);ctrl.setWidth(ww);ctrl.setHeight(hh)
            for ident,coords in zip((101,102,103,104),bounds['buttons']):
                ctrl=self.getControl(ident)
                ctrl.setPosition(coords[0],coords[1])
                ctrl.setWidth(coords[2]);ctrl.setHeight(coords[3])
            if self.expanded:
                extra = ' • '.join(v for v in (snapshot.release_date, snapshot.credits) if v)
                self.setProperty('Infinity.HomeOptionB.Synopsis', (extra+'\n\n' if extra else '')+snapshot.synopsis)
                for ident in (101,102,103): self.getControl(ident).setVisible(False)
                self.getControl(104).setLabel('Back')
                self.setFocusId(126)
            else:
                self.setFocusId(101 if props['PlayAvailable']=='true' else 9)
            self.ready=True
            _trace(xbmc, 'popup.shown', 'accepted', native.control, native.index)
        def onClick(self,control_id):
            if self.expanded and control_id == 104:
                self.close();return
            if control_id == 104 and not self.expanded:
                details=OptionB('InfinityHomeOptionB.xml',str(root),'Default','1080i')
                details.expanded=True
                try: details.doModal()
                finally: details.close();del details
                return
            if control_id in (2,9):
                self.close();return
            action=ACTIONS.get(control_id)
            if action and props.get({102:'TrailerAvailable',103:'FavoriteAvailable',
                                     104:'InfoAvailable',101:'PlayAvailable'}[control_id])=='true':
                self.selected_action=action
                self.close()
        def onAction(self,action):
            if action.getId() in CANCEL_ACTION_IDS:
                self.close()
    window=OptionB('InfinityHomeOptionB.xml',str(root),'Default','1080i')
    try:
        _trace(xbmc, 'popup.create', 'requested', native.control, native.index)
        window.doModal()
        if not window.ready:
            return False
        choice=window.selected_action
        _trace(xbmc, 'popup.closed', choice or 'cancelled', native.control, native.index)
    finally:
        window.close();del window
    # Close never moves Home focus; canceled/back/outside click is inert.
    return bool(choice and _perform(xbmc,xbmcgui,snapshot,choice,native))
