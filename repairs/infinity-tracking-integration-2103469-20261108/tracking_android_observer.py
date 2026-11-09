"""Disposable SDK observer for selected tracking tests; never a progress writer.

Installed as a normal ZIP addon. Uses the installed original-key controller and
actual native GUI/player copies. No provider settings, identities or callbacks
are manufactured here.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

QA = 'script.infinity.trackingqa'
CC = 'script.infinity.commandcenter'
EVENTS = None


class ActualEvents(xbmc.Player):
    def __init__(self):
        super().__init__()
        self.events = []
        self.sequence = 0

    def record(self, name):
        self.sequence += 1
        self.events.append(dict(event=name, sequence=self.sequence, monotonic=time.monotonic()))
        self.events[:] = self.events[-96:]

    def onPlayBackStarted(self): self.record('Started')
    def onAVStarted(self): self.record('AVStarted')
    def onPlayBackStopped(self): self.record('Stopped')
    def onPlayBackEnded(self): self.record('Ended')
    def onPlayBackError(self): self.record('Error')


def controller():
    root = Path(xbmcvfs.translatePath(xbmcaddon.Addon(CC).getAddonInfo('path')))
    for path in (root, root / 'infinity_modules/uirepair'):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    from controller_access import load
    return load()


def identity():
    plugin = controller()  # Native RSA + full manifest source loader, before behavior.
    root = Path(xbmcvfs.translatePath(xbmcaddon.Addon(CC).getAddonInfo('path')))
    from module_contract import installed_identity
    native = installed_identity(root, xbmcaddon.Addon(CC).getAddonInfo('version'))
    actual = {}
    for line in (root / 'INFINITY-MODULES.v1').read_text().splitlines():
        fields = line.split('\t')
        if fields[0] == 'file':
            path = root.parent / fields[2]
            assert path.resolve().is_relative_to(root.parent.resolve())
            actual[fields[2]] = hashlib.sha256(path.read_bytes()).hexdigest()
    expected = json.loads((Path(__file__).parent / 'expected.json').read_text())
    assert native.manifest_sha256 == expected['manifest_sha256']
    assert actual == expected['module_sources'] and len(actual) == 80
    providers = {}
    for aid, hashes in expected['provider_sources'].items():
        addon = xbmcaddon.Addon(aid)
        source = Path(xbmcvfs.translatePath(addon.getAddonInfo('path')))
        observed = {name: hashlib.sha256((source / name).read_bytes()).hexdigest() for name in hashes}
        assert observed == hashes, 'UNMODIFIED_PUBLISHER_SOURCE_REQUIRED:' + aid
        providers[aid] = dict(path=str(source), version=addon.getAddonInfo('version'), files=observed)
    return dict(pid=os.getpid(), cc_version=native.package_version,
                manifest_sha256=native.manifest_sha256, module_files=actual,
                module_count=len(actual), controller_path=str(root), loaded_plugin=str(plugin.__file__),
                provider_sources=providers, skin=xbmc.getSkinDir())


def tag(item):
    info = item.getVideoInfoTag()
    return dict(path=item.getPath(), label=item.getLabel(), media_type=info.getMediaType(), season=info.getSeason(),
                episode=info.getEpisode(), ids={key: info.getUniqueID(key) for key in ('tmdb', 'tvdb', 'imdb')}, title=info.getTitle(),
                show_title=info.getTVShowTitle(), dbid=info.getDbId(),
                original_listitem_url=item.getProperty('original_listitem_url'),
                parent_path=item.getProperty('ParentPath'))


def snapshot():
    controls = {}
    for control in (50, 450, 451, 1000):
        count = int(xbmc.getInfoLabel('Container(%d).NumItems' % control) or 0)
        assert 0 <= count <= 1500
        if count:
            rows = []
            for i in range(count + 1):
                p = 'Container(%d).ListItemAbsolute(%d).' % (control, i)
                rows.append(dict(index=i, label=xbmc.getInfoLabel(p + 'Label'),
                    file=xbmc.getInfoLabel(p + 'FileNameAndPath'),
                    media_type=xbmc.getInfoLabel(p + 'DBTYPE'),
                    season=xbmc.getInfoLabel(p + 'Season'), episode=xbmc.getInfoLabel(p + 'Episode'),
                    key=xbmc.getInfoLabel(p + 'Property(Infinity.ResumeHub.Key)'),
                    selection=xbmc.getInfoLabel(p + 'Property(Infinity.Selection.Snapshot)')))
            controls[str(control)] = rows
    return dict(pid=os.getpid(), window=xbmcgui.getCurrentWindowId(),
                dialog=xbmcgui.getCurrentWindowDialogId(), controls=controls,
                folder=xbmc.getInfoLabel('Container.FolderPath'), skin=xbmc.getSkinDir(),
                heading=xbmc.getInfoLabel('Control.GetLabel(1)'), body=xbmc.getInfoLabel('Control.GetLabel(9)'),
                screen_width=xbmc.getInfoLabel('System.ScreenWidth'), screen_height=xbmc.getInfoLabel('System.ScreenHeight'),
                theme=xbmcaddon.Addon('service.infinity.compat').getSetting('theme_mode'),
                visual_mode=xbmc.getInfoLabel('Skin.String(Infinity.VisualMode)'),
                home_view=xbmc.getInfoLabel('Skin.String(Infinity.HomeView)'))


def selected(request):
    control, index = request['control'], request['index']
    assert control in (50, 450, 451, 1000) and type(index) is int and 0 <= index <= 1500
    xbmc.executebuiltin('SetFocus(%d,%d,absolute)' % (control, index), True)
    p = 'Container(%d).ListItem.' % control
    assert xbmc.getInfoLabel(p + 'FileNameAndPath') == request['file']
    assert xbmc.getInfoLabel(p + 'Label') == request['label']
    # A native ControlList Python wrapper has no Python-owned vecItems; its
    # getSelectedItem() would return None. Read the actual native GUI labels.
    # Only playing() below supplies an authoritative SDK CFileItem copy.
    season = xbmc.getInfoLabel(p + 'Season')
    episode = xbmc.getInfoLabel(p + 'Episode')
    return dict(live_native_file=request['file'], actual_gui_item=dict(
        path=request['file'], label=request['label'], media_type=xbmc.getInfoLabel(p + 'DBTYPE'),
        season_raw=season, episode_raw=episode,
        season=int(season) if season.isdigit() else -1,
        episode=int(episode) if episode.isdigit() else -1,
        ids={key: xbmc.getInfoLabel(p + 'UniqueID(' + key + ')') for key in ('tmdb', 'tvdb', 'imdb')}))


def action(request):
    kind = request['action']
    if kind == 'identity': return identity()
    if kind == 'snapshot': return snapshot()
    if kind == 'events': return EVENTS.events
    if kind == 'state':
        plugin = controller()
        data = plugin.hub.load_view(plugin.PROFILE)
        return dict(data=data, continue_entries=plugin.hub.entries(data),
                    progress_shows=plugin.hub.progress_shows(data), next_episodes=plugin.hub.next_episodes(data),
                    series_proof={key: plugin.hub.continue_series_ids(entry)
                                  for key, entry in data.get('items', {}).items() if entry.get('media') == 'tv'})
    if kind == 'playing':
        player = xbmc.Player()
        value = dict(playing=player.isPlayingVideo(), events=EVENTS.events)
        if value['playing']:
            value.update(item=tag(player.getPlayingItem()), file=player.getPlayingFile(),
                         time=player.getTime(), total=player.getTotalTime(), clock_monotonic=time.monotonic())
        return value
    if kind in ('inspect', 'click', 'context'):
        result = selected(request)
        if kind != 'inspect':
            # Native GUI selection/context, preserving the real selected item.
            method = 'Input.Select' if kind == 'click' else 'Input.ContextMenu'
            reply = json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0', id=1, method=method))))
            assert 'error' not in reply
        return result
    if kind == 'menu-select':
        control, index = request['control'], request['index']
        assert control in (50, 450, 1000) and type(index) is int and 0 <= index <= 100
        assert xbmcgui.getCurrentWindowDialogId() not in (0, -1, 9999)
        xbmc.executebuiltin('SetFocus(%d,%d,absolute)' % (control, index), True)
        assert xbmc.getInfoLabel('Container(%d).ListItem.Label' % control) == request['label']
        xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Input.Select"}')
        return dict(actual_selected_label=request['label'])
    raise ValueError('UNSELECTED_OBSERVER_ACTION:' + str(kind))


def serve():
    global EVENTS
    EVENTS = ActualEvents()
    root = Path(xbmcvfs.translatePath(xbmcaddon.Addon(QA).getAddonInfo('profile')))
    root.mkdir(parents=True, exist_ok=True)
    pid, last, monitor = os.getpid(), 0, xbmc.Monitor()
    (root / 'ready.json').write_text(json.dumps(dict(pid=pid, qa=QA)))
    while not monitor.waitForAbort(.15):
        try:
            raw = (root / 'request.json').read_text()
            assert len(raw.encode()) <= 65536
            request = json.loads(raw)
        except (OSError, ValueError, AssertionError):
            continue
        if request.get('pid') != pid or type(request.get('sequence')) is not int or request['sequence'] <= last:
            continue
        last = request['sequence']
        reply = dict(pid=pid, sequence=last, passed=False)
        try:
            reply.update(passed=True, result=action(request))
        except Exception as error:
            reply.update(error=repr(error), traceback=traceback.format_exc())
        payload = json.dumps(reply)
        if len(payload.encode()) > 4 * 1024 * 1024:
            payload = json.dumps(dict(pid=pid, sequence=last, passed=False, error='BOUNDED_REPLY_EXCEEDED'))
        pending = root / 'reply.pending'
        pending.write_text(payload)
        pending.replace(root / 'reply.json')


if __name__ == '__main__':
    serve()
