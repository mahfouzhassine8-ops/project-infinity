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
from pathlib import Path
import re
from urllib.parse import urlsplit

CONTROLS = {8101: 'movies', 8102: 'tvshows'}
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
            'PlayAvailable': 'true' if _media_path(self.path) else 'false',
            'TrailerAvailable': 'true' if _trailer_path(self.trailer) else 'false',
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


PENDING_FIELDS = ('Control', 'Index', 'Path', 'Label', 'Proof')


def read_native_hold(xbmcgui, args) -> NativeHold | None:
    """Require the exact C++ touch-hit item; never use stale Home focus alone."""
    if len(args) != 3 or args[0] not in ('8101', '8102'):
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
                not path.startswith('plugin://plugin.video.umbrella/') or
                len(path) > 4096 or not label or len(label) > 512):
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
        return None
    if xbmcgui.getCurrentWindowDialogId() not in (0, -1, 9999):
        return None
    home = xbmcgui.Window(10000)
    try:
        control = home.getFocusId()
        if control not in CONTROLS or (native is not None and control != native.control):
            return None
        section = _safe(xbmc.getInfoLabel('Container(9000).ListItem.Property(section)'), 50)
        if section != CONTROLS[control]:
            return None
        widget = home.getControl(control)
        # If Kodi's panel wrapper does not expose its selected index, do not
        # guess an adjacent poster or treat a stale focus as a touch hit.
        idx = widget.getSelectedPosition()
        if not isinstance(idx, int) or idx < 0 or (native is not None and idx != native.index):
            return None
        count = xbmc.getInfoLabel(f'Container({control}).NumItems')
        if not count.isdecimal() or idx >= int(count):
            return None
        prefix = f'Container({control}).ListItem.'
        def info(name: str, maxlen: int = MAX_METADATA_LENGTH) -> str:
            return _safe(xbmc.getInfoLabel(prefix + name), maxlen)
        observed_label = info('Label')
        title = info('Title') or observed_label
        path = info('FileNameAndPath',4096) or info('FolderPath',4096)
        if native is not None:
            # Native source is the hit-tested CFileItem, not an inferred stream.
            if observed_label and observed_label != native.label:
                return None
            if path and path != native.path:
                return None
            path = native.path
            if not title:
                title = native.label
        if not title or not _media_path(path):
            return None
        poster = info('Art(poster)',2048) or info('Thumb',2048)
        media_type = info('DBTYPE',40).casefold() or info('Property(MediaType)',40).casefold()
        season = info('Season',6)
        episode = info('Episode',6)
        if media_type != 'episode':
            season = episode = ''
        return Selection(control=control,index=idx,section=section,path=path,
                         title=title,poster=poster,year=info('Year',5),
                         media_type=media_type,season=season,episode=episode,
                         episode_title=info('EpisodeName',120) if media_type=='episode' else '',
                         certification=info('MPAA',40),runtime=info('Duration',40),
                         rating=info('Rating',40),genres=info('Genre',160),
                         synopsis=info('Plot',2300),trailer=info('Trailer',4096),
                         is_folder=bool(xbmc.getCondVisibility(
                             f'Container({control}).ListItem.IsFolder')))
    except (AttributeError, TypeError, ValueError, RuntimeError):
        return None


def geometry(width: int, height: int) -> dict:
    """Centered compact panel in Kodi coordinates; return nonoverlapping actions."""
    width, height = max(1, int(width)), max(1, int(height))
    card_w = min(920, max(280, int(width * .88)), max(1,width - 32))
    compact = card_w < 740
    card_h = min(max(1,height-32), max(280, int(height * (.90 if compact else .74))))
    card_h = min(card_h, 700 if compact else 580)
    x = max(0,(width-card_w)//2)
    y = max(0,(height-card_h)//2)
    if compact:
        poster_w = min(170,max(90,int(card_w*.29)))
        poster_h = min(185, max(105, int(card_h*.29)))
        text_x = 28+poster_w+18
        text_w = max(36,card_w-text_x-20)
        meta_top = min(300, 91+poster_h+15)
        synopsis_top = meta_top+82
        buttons_top = card_h-173
        synopsis_height = max(0, buttons_top-synopsis_top-12)
        bw = (card_w-60)//2
        buttons = [(20+(i%2)*(bw+20), buttons_top+(i//2)*78, bw,68)
                   for i in range(4)]
        details = {'poster':(28,91,poster_w,poster_h),
                   'title':(text_x,87,text_w,78),
                   'year':(text_x,165,text_w,46),
                   'certification':(24,meta_top,95,32),
                   'runtime':(122,meta_top,100,32),
                   'rating':(max(24,card_w-126),meta_top,104,32),
                   'genres':(24,meta_top+36,card_w-48,42),
                   'synopsis':(24,synopsis_top,card_w-48,synopsis_height)}
    else:
        bw = (card_w-48-3*14)//4
        buttons = [(24+i*(bw+14),card_h-95,bw,74) for i in range(4)]
        details = {'poster':(28,91,228,354),
                   'title':(288,87,card_w-390,64),
                   'year':(288,153,card_w-322,40),
                   'certification':(288,203,95,34),
                   'runtime':(385,203,110,34),
                   'rating':(498,203,110,34),
                   'genres':(288,248,card_w-322,58),
                   'synopsis':(288,318,card_w-322,max(0,card_h-438))}
    return dict(x=x,y=y,width=card_w,height=card_h,compact=compact,
                details=details,buttons=buttons)


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
    if action == 'more-info':
        xbmc.executebuiltin('Action(Info)')
        return True
    if action == 'favorite' and _media_path(selected.path):
        # Kodi's own Favourites JSON-RPC; no Infinity/trakt/watched database.
        kind = 'window' if selected.is_folder else 'media'
        params = {'title':selected.title,'type':kind,'thumbnail':selected.poster}
        if kind == 'window':
            params.update(window='Videos',windowparameter=selected.path)
        else:
            params['path'] = selected.path
        current = _rpc(xbmc,'Favourites.GetFavourites',{'properties':['path','window','windowparameter']})
        for fav in current.get('favourites',[]):
            if (fav.get('type') == kind and (fav.get('path') if kind=='media'
                    else fav.get('windowparameter'))) == selected.path:
                return True
        _rpc(xbmc,'Favourites.AddFavourite',params)
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
        return False
    try:
        return _show_verified_hold(xbmc, xbmcaddon, xbmcgui, xbmcvfs, native)
    finally:
        clear_native_hold(xbmcgui, native)


def _show_verified_hold(xbmc, xbmcaddon, xbmcgui, xbmcvfs, native: NativeHold) -> bool:
    snapshot = capture(xbmc, xbmcgui, native)
    if snapshot is None:
        return False
    props = snapshot.properties()
    root = Path(xbmcvfs.translatePath(xbmcaddon.Addon('script.infinity.uirepair').getAddonInfo('path')))
    class OptionB(xbmcgui.WindowXMLDialog):
        selected_action = None
        ready = False
        def onInit(self):
            for name,value in props.items():
                self.setProperty('Infinity.HomeOptionB.'+name,value)
            # backdrop is the true Kodi window; reflow on each open/fold.
            background=self.getControl(2)
            bounds=geometry(background.getWidth(),background.getHeight())
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
            for ident,coords in zip((101,102,103,104),bounds['buttons']):
                ctrl=self.getControl(ident)
                ctrl.setPosition(coords[0],coords[1])
                ctrl.setWidth(coords[2]);ctrl.setHeight(coords[3])
            self.setFocusId(101 if props['PlayAvailable']=='true' else 9)
            self.ready=True
        def onClick(self,control_id):
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
        window.doModal()
        if not window.ready:
            return False
        choice=window.selected_action
    finally:
        window.close();del window
    # Close never moves Home focus; canceled/back/outside click is inert.
    return bool(choice and _perform(xbmc,xbmcgui,snapshot,choice,native))
