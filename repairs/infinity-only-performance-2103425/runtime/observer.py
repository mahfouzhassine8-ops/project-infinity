"""Bounded disposable-emulator observer. Never part of the production APK."""
import hashlib
import json
import os
from pathlib import Path
import time

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

ADDON = 'service.infinity.performanceqa'
ACTIONS = ('snapshot', 'movie-tab', 'tv-tab', 'movie-focus', 'search', 'finish')
MAX_REQUESTS = 24


def accept(value, pid, sequence):
    return (isinstance(value, dict) and set(value) == {'pid', 'sequence', 'action'} and
            type(value['pid']) is int and value['pid'] == pid and
            type(value['sequence']) is int and value['sequence'] == sequence and
            1 <= sequence <= MAX_REQUESTS and value['action'] in ACTIONS)


def snapshot():
    labels = ['Container(9000).NumItems', 'Container(9000).ListItem.Property(section)',
              'Container.FolderPath', 'Window(Home).Property(Infinity.ContinueWatchingRevision)',
              'Window(Home).Property(Infinity.EffectiveViewMode)',
              'Window(Home).Property(Infinity.Home.FirstViewportReady)']
    flags = ['Window.IsActive(home)', 'Player.HasMedia']
    for control in (8830, 8831):
        labels.append('Container(%d).NumItems' % control)
        labels.extend('Container(%d).ListItem.%s' % (control, field) for field in (
            'Label', 'PercentPlayed', 'Property(Infinity.Selection.Snapshot)',
            'Property(Infinity.ResumeHub.Watched)', 'Property(Infinity.ResumeHub.Revision)',
            'Art(poster)', 'Season', 'Episode'))
        flags.append('Control.IsVisible(%d)' % control)
    return dict(pid=os.getpid(), monotonic=time.monotonic(), window=xbmcgui.getCurrentWindowId(),
                labels={name: xbmc.getInfoLabel(name) for name in labels},
                flags={name: bool(xbmc.getCondVisibility(name)) for name in flags})


def select_tab(media):
    """Choose the exact static tab, then observe its real settled selection."""
    if xbmcgui.getCurrentWindowId() != 10000:
        raise RuntimeError('Actual Home required before selecting its tab')
    wanted = 'movies' if media == 'movie' else 'tvshows'
    count = int(xbmc.getInfoLabel('Container(9000).NumItems') or 0)
    if not 1 <= count <= 50:
        raise RuntimeError('Bounded actual Home tabs unavailable')
    matches = [index for index in range(count) if xbmc.getInfoLabel(
        'Container(9000).ListItemAbsolute(%d).Property(section)' % index) == wanted]
    if len(matches) != 1:
        raise RuntimeError('Exact actual Home tab not uniquely identified: ' + wanted)
    xbmc.executebuiltin('SetFocus(9000,%d,absolute)' % matches[0], True)
    monitor = xbmc.Monitor()
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and not monitor.abortRequested():
        if xbmc.getInfoLabel('Container(9000).ListItem.Property(section)') == wanted:
            return
        monitor.waitForAbort(.05)
    raise RuntimeError('Actual Home tab did not settle on ' + wanted)


def serve():
    root = Path(xbmcvfs.translatePath(xbmcaddon.Addon(ADDON).getAddonInfo('profile')))
    root.mkdir(parents=True, exist_ok=True)
    if root.is_symlink():
        raise RuntimeError('Linked observer profile refused')
    pid = os.getpid()
    def output(name, value):
        path = root / name
        if path.is_symlink(): raise RuntimeError('Linked observer response refused')
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(value, sort_keys=True))
        temporary.replace(path)
    output('ready.json', dict(pid=pid, source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                             max_requests=MAX_REQUESTS, production_changes=False))
    sequence = 1
    monitor = xbmc.Monitor()
    deadline = time.monotonic() + 600
    while sequence <= MAX_REQUESTS and time.monotonic() < deadline and not monitor.abortRequested():
        request = root / 'request.json'
        if request.exists():
            if request.is_symlink() or request.stat().st_size > 4096:
                raise RuntimeError('Invalid observer request')
            try: value = json.loads(request.read_text())
            except ValueError: value = None
            if accept(value, pid, sequence):
                action = value['action']
                result = dict(pid=pid, sequence=sequence, action=action)
                try:
                    if action == 'movie-tab': select_tab('movie')
                    elif action == 'tv-tab': select_tab('tv')
                    elif action == 'movie-focus':
                        if not xbmc.getCondVisibility('Control.IsVisible(8830)'):
                            raise RuntimeError('Actual movie Continue rail must be visible')
                        xbmc.executebuiltin('SetFocus(8830,0,absolute)', True)
                    elif action == 'search':
                        xbmc.executebuiltin('RunScript(script.infinity.commandcenter,universal-search,movie)')
                    result['observed'] = snapshot()
                except Exception as error:
                    result['failure'] = type(error).__name__ + ': ' + str(error)
                    result['observed'] = snapshot()
                output('response.json', result)
                sequence += 1
                if action == 'finish': return
        monitor.waitForAbort(.1)


if __name__ == '__main__':
    serve()
