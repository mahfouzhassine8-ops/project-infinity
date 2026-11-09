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
BOOTSTRAP_PHASES = []
CANCELLED_CHOICE = None


def require(value, label):
    if not value:
        raise RuntimeError(label)


def phase(name):
    BOOTSTRAP_PHASES.append(dict(phase=name, monotonic=time.monotonic()))
    BOOTSTRAP_PHASES[:] = BOOTSTRAP_PHASES[-64:]


def authenticated_bootstrap(root, version):
    """Consume the original loaded-engine ABI before executing owned Python.

    The sole Python bootstrap is the installed, hash-verified module_contract
    source, loaded exactly as the original default.py bootstrap does. Its own
    ImportGuard remains responsible for every subsequent owned import.
    """
    expected = json.loads((Path(__file__).parent / 'expected.json').read_text())
    owned = ('script.infinity.commandcenter', 'script.infinity.uirepair',
             'script.infinity.watchedbridge', 'script.infinity.rails')
    prefixes = tuple(str(root.parent / name) for name in owned)
    previous = sys.path[:]
    phase('NATIVE_IDENTITY_BEGIN')
    try:
        sys.path[:] = [p for p in previous if p.startswith('/') and not any(
            p == prefix or p.startswith(prefix + '/') for prefix in prefixes)]
        import ctypes
        import types
        library_root = os.environ.get('KODI_ANDROID_LIBS', '')
        require(library_root.startswith('/') and '\0' not in library_root, 'RUNNING_ENGINE_LIBRARY_ROOT_REQUIRED')
        library = ctypes.CDLL(os.path.realpath(os.path.join(library_root, 'libkodi.so')),
                              mode=os.RTLD_NOLOAD | os.RTLD_NOW)
        native = library.InfinityCommandCenterIdentityV1
        native.argtypes = (ctypes.c_char_p, ctypes.POINTER(ctypes.c_char), ctypes.c_size_t,
                           ctypes.POINTER(ctypes.c_char), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint))
        native.restype = ctypes.c_int
        encoded = str(root).encode('utf-8')
        require(len(encoded) <= 4096 and b'\0' not in encoded, 'BOUNDED_INSTALLED_CC_ROOT_REQUIRED')
        actual_version, digest, protocol = ctypes.create_string_buffer(49), ctypes.create_string_buffer(65), ctypes.c_uint()
        require(native(encoded, actual_version, len(actual_version), digest, len(digest), ctypes.byref(protocol)) == 1,
                'NATIVE_ORIGINAL_RSA_FULL80_IDENTITY_REQUIRED')
        require(actual_version.value.decode('ascii') == version == expected['cc_version'] and protocol.value == 1 and
                digest.value.decode('ascii') == expected['manifest_sha256'], 'EXPECTED_NATIVE_VERSION_PROTOCOL_MANIFEST_REQUIRED')
        phase('NATIVE_FULL80_IDENTITY_ACCEPTED')
        with (root / 'INFINITY-MODULES.v1').open('rb') as stream:
            manifest = stream.read(128 * 1024 + 1)
        require(len(manifest) <= 128 * 1024 and hashlib.sha256(manifest).hexdigest() == expected['manifest_sha256'],
                'NATIVE_AUTHENTICATED_MANIFEST_BYTES_REQUIRED')
        rows = [line.split('\t') for line in manifest.decode('ascii').splitlines() if line.startswith('file\t')]
        require(len(rows) == 80 and all(len(row) == 3 for row in rows), 'EXACT80_MANIFEST_RECORDS_REQUIRED')
        files = {row[2]: row[1] for row in rows}
        require(len(files) == 80 and files == expected['module_sources'], 'EXACT_EXPECTED_AUTHENTICATED80_MAP_REQUIRED')
        for relative, wanted in files.items():
            path = root.parent / relative
            require(path.resolve().is_relative_to(root.parent.resolve()), 'OWNED_BOOTSTRAP_SOURCE_PATH_REQUIRED')
            require(hashlib.sha256(path.read_bytes()).hexdigest() == wanted, 'EXACT_BOOTSTRAP_FULL80_SOURCE_REQUIRED:' + relative)
        phase('EXPECTED_FULL80_SOURCE_MAP_ACCEPTED')
        bootstrap = root / 'module_contract.py'
        require(files[CC + '/module_contract.py'] == '759e60439fae0b1bf0f8a2ff6895209ac848101b9544ac6c0e297b9c73df1267',
                'ORIGINAL_IMMUTABLE_BOOTSTRAP_SOURCE_PIN_REQUIRED')
        with bootstrap.open('rb') as stream:
            raw = stream.read(4 * 1024 * 1024 + 1)
        require(len(raw) <= 4 * 1024 * 1024 and hashlib.sha256(raw).hexdigest() == files[CC + '/module_contract.py'],
                'AUTHENTICATED_INSTALLED_BOOTSTRAP_BYTES_REQUIRED')
        module = sys.modules.get('module_contract')
        if module is None:
            module = types.ModuleType('module_contract')
            module.__file__ = str(bootstrap)
            sys.modules['module_contract'] = module
            exec(compile(raw, str(bootstrap), 'exec', dont_inherit=True), module.__dict__)
            phase('INSTALLED_VERIFIED_BOOTSTRAP_SOURCE_EXECUTED')
        else:
            require(getattr(module, '__file__', None) == str(bootstrap), 'CONFLICTING_BOOTSTRAP_CACHE_PATH_REJECTED')
            guard_type = getattr(module, 'ImportGuard', None)
            require(isinstance(guard_type, type), 'CONFLICTING_BOOTSTRAP_CACHE_TYPE_REJECTED')
            guards = [guard for guard in sys.meta_path if isinstance(guard, guard_type)]
            require(len(guards) == 1 and guards[0].contract.root == root.parent and
                    guards[0].contract.identity.package_version == version and
                    guards[0].contract.identity.manifest_sha256 == expected['manifest_sha256'],
                    'UNOWNED_OR_CONFLICTING_BOOTSTRAP_CACHE_REJECTED')
            phase('EXISTING_AUTHENTICATED_BOOTSTRAP_GUARD_ACCEPTED')
        contract = module.active_contract(root, version)
        require(contract.identity.manifest_sha256 == expected['manifest_sha256'] and
                dict(contract.files) == files, 'ORIGINAL_ACTIVE_CONTRACT_REQUIRED')
        phase('ORIGINAL_IMPORT_GUARD_ACTIVE_BEFORE_CONTROLLER_IMPORT')
        return contract
    finally:
        sys.path[:] = previous


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
    addon = xbmcaddon.Addon(CC)
    root = Path(xbmcvfs.translatePath(addon.getAddonInfo('path'))).absolute()
    authenticated_bootstrap(root, addon.getAddonInfo('version'))
    for path in (root, root / 'infinity_modules/uirepair'):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    from controller_access import load
    phase('CONTROLLER_ACCESS_IMPORTED_THROUGH_ORIGINAL_GUARD')
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
            require(path.resolve().is_relative_to(root.parent.resolve()), 'OWNED_MODULE_PATH_REQUIRED')
            actual[fields[2]] = hashlib.sha256(path.read_bytes()).hexdigest()
    expected = json.loads((Path(__file__).parent / 'expected.json').read_text())
    require(native.manifest_sha256 == expected['manifest_sha256'], 'EXACT_NATIVE_FIXTURE_MANIFEST_REQUIRED')
    require(actual == expected['module_sources'] and len(actual) == 80, 'EXACT_AUTHENTICATED80_SOURCE_SET_REQUIRED')
    providers = {}
    for aid, hashes in expected['provider_sources'].items():
        addon = xbmcaddon.Addon(aid)
        source = Path(xbmcvfs.translatePath(addon.getAddonInfo('path')))
        observed = {name: hashlib.sha256((source / name).read_bytes()).hexdigest() for name in hashes}
        require(observed == hashes, 'UNMODIFIED_PUBLISHER_SOURCE_REQUIRED:' + aid)
        providers[aid] = dict(path=str(source), version=addon.getAddonInfo('version'), files=observed)
    return dict(pid=os.getpid(), cc_version=native.package_version,
                manifest_sha256=native.manifest_sha256, module_files=actual,
                module_count=len(actual), controller_path=str(root), loaded_plugin=str(plugin.__file__),
                provider_sources=providers, skin=xbmc.getSkinDir(), Python_optimization=sys.flags.optimize,
                bootstrap_phases=list(BOOTSTRAP_PHASES))


def tag(item):
    info = item.getVideoInfoTag()
    return dict(path=item.getPath(), label=item.getLabel(), media_type=info.getMediaType(), season=info.getSeason(),
                episode=info.getEpisode(), ids={key: info.getUniqueID(key) for key in ('tmdb', 'tvdb', 'imdb')}, title=info.getTitle(),
                show_title=info.getTVShowTitle(), dbid=info.getDbId(),
                original_listitem_url=item.getProperty('original_listitem_url'),
                parent_path=item.getProperty('ParentPath'))


def snapshot():
    # Exact original69 unified/MyVideoNav.xml <views>; owned popup50 is kept.
    primary_controls = (50, 65050, 65051, 65052, 51, 52, 53, 55, 56, 57, 58, 59,
                        500, 501, 502, 503, 504, 505, 506, 507, 509, 591, 592, 602, 609)
    observed_controls = tuple(dict.fromkeys((3, 6, 50, 450, 451, 1000) + primary_controls))
    visible = {str(control): xbmc.getCondVisibility('Control.IsVisible(%d)' % control) for control in observed_controls}
    controls = {}
    for control in observed_controls:
        if control in primary_controls and control != 50 and not visible[str(control)]:
            continue
        count = int(xbmc.getInfoLabel('Container(%d).NumItems' % control) or 0)
        require(0 <= count <= 1500, 'BOUNDED_ACTUAL_DIRECTORY_REQUIRED')
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
    # Theme telemetry is independent of native directory/player observation.
    # An APK asset is not proof that its historical addon owner is registered.
    theme, theme_error = None, None
    try:
        theme = xbmcaddon.Addon('service.infinity.compat').getSetting('theme_mode')
        require(theme in ('system', 'light', 'dark'), 'THEME_OWNER_POLICY_UNAVAILABLE')
    except Exception as error:
        theme, theme_error = None, repr(error)
    buttons = []
    if xbmcgui.getCurrentWindowDialogId() == 10106:
        for control in range(1001, 1101):
            label = xbmc.getInfoLabel('Control.GetLabel(%d)' % control)
            if label and xbmc.getCondVisibility('Control.IsVisible(%d)' % control):
                buttons.append(dict(control=control, label=label))
    return dict(pid=os.getpid(), window=xbmcgui.getCurrentWindowId(),
                dialog=xbmcgui.getCurrentWindowDialogId(), controls=controls,
                context_buttons=buttons,
                primary_controls=list(primary_controls),
                folder=xbmc.getInfoLabel('Container.FolderPath'), skin=xbmc.getSkinDir(),
                heading=xbmc.getInfoLabel('Control.GetLabel(1)'), body=xbmc.getInfoLabel('Control.GetLabel(9)'),
                screen_width=xbmc.getInfoLabel('System.ScreenWidth'), screen_height=xbmc.getInfoLabel('System.ScreenHeight'),
                theme=theme, theme_available=theme is not None, theme_error=theme_error,
                published_theme=xbmc.getInfoLabel('Window(Home).Property(Infinity.Theme)'),
                visible_controls=visible,
                focused_control=xbmc.getInfoLabel('System.CurrentControlId'),
                visual_mode=xbmc.getInfoLabel('Skin.String(Infinity.VisualMode)'),
                home_view=xbmc.getInfoLabel('Skin.String(Infinity.HomeView)'))


def selected(request):
    control, index = request['control'], request['index']
    primary = (50, 65050, 65051, 65052, 51, 52, 53, 55, 56, 57, 58, 59,
               500, 501, 502, 503, 504, 505, 506, 507, 509, 591, 592, 602, 609)
    require(control in primary + (450, 451, 1000)
            and type(index) is int and 0 <= index <= 1500,
            'EXACT_SELECTED_NATIVE_CONTROL_AND_INDEX_REQUIRED')
    require(xbmc.getCondVisibility('Control.IsVisible(%d)' % control), 'VISIBLE_ACTUAL_SELECTED_CONTAINER_REQUIRED')
    if control in primary:
        require(xbmcgui.getCurrentWindowId() == 10025 and xbmcgui.getCurrentWindowDialogId() in (0, -1, 9999) and
                [candidate for candidate in primary if xbmc.getCondVisibility('Control.IsVisible(%d)' % candidate)] == [control],
                'ONE_UNOBSCURED_ACTUAL_PRIMARY_DIRECTORY_VIEW_REQUIRED')
    xbmc.executebuiltin('SetFocus(%d,%d,absolute)' % (control, index), True)
    p = 'Container(%d).ListItem.' % control
    require(xbmc.getInfoLabel(p + 'FileNameAndPath') == request['file'], 'LIVE_NATIVE_SELECTED_PATH_REQUIRED')
    require(xbmc.getInfoLabel(p + 'Label') == request['label'], 'LIVE_NATIVE_SELECTED_LABEL_REQUIRED')
    require(xbmc.getInfoLabel('System.CurrentControlId') == str(control), 'ACTUAL_SELECTED_DIRECTORY_FOCUS_REQUIRED')
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
    global CANCELLED_CHOICE
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
        value = dict(playing=player.isPlayingVideo(), events=list(EVENTS.events))
        if value['playing']:
            try:
                observed = dict(item=tag(player.getPlayingItem()), file=player.getPlayingFile(),
                                time=player.getTime(), total=player.getTotalTime(), clock_monotonic=time.monotonic())
            except RuntimeError as error:
                if str(error) not in ('Kodi is not playing any item', 'Kodi is not playing any file',
                                      'Kodi is not playing any media file') or player.isPlayingVideo():
                    raise
                return dict(playing=False, observation='stopped_during_sdk_snapshot', sdk_transition_error=str(error),
                            events=list(EVENTS.events), observed_monotonic=time.monotonic())
            if not player.isPlayingVideo():
                return dict(playing=False, observation='stopped_after_sdk_snapshot', events=list(EVENTS.events),
                            observed_monotonic=time.monotonic())
            value.update(observed)
        return value
    if kind in ('inspect', 'click', 'context'):
        result = selected(request)
        if kind != 'inspect':
            # Native GUI selection/context, preserving the real selected item.
            method = 'Input.Select' if kind == 'click' else 'Input.ContextMenu'
            reply = json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0', id=1, method=method))))
            require('error' not in reply, 'ACTUAL_NATIVE_INPUT_RPC_REQUIRED')
        return result
    if kind == 'menu-select':
        control, index = request['control'], request['index']
        require(control in (3, 6, 50, 450, 1000) and type(index) is int and 0 <= index <= 100,
                'EXACT_NATIVE_MENU_CONTROL_AND_INDEX_REQUIRED')
        require(xbmcgui.getCurrentWindowDialogId() not in (0, -1, 9999), 'ACTUAL_NATIVE_MENU_DIALOG_REQUIRED')
        if control in (3, 6):
            require(xbmcgui.getCurrentWindowDialogId() == request.get('dialog') == 12000 and
                    xbmc.getInfoLabel('Control.GetLabel(1)') == request.get('heading') and
                    request.get('heading') in ('Select Quality', 'Select Chapter'), 'RECOGNIZED_ACTUAL_PROVIDER_CHOICE_REQUIRED')
            require(xbmc.getCondVisibility('Control.IsVisible(%d)' % control), 'VISIBLE_NATIVE_CHOICE_LIST_REQUIRED')
            count = int(xbmc.getInfoLabel('Container(%d).NumItems' % control) or 0)
            require(index < count <= 100, 'ACTUAL_NATIVE_CHOICE_INDEX_REQUIRED')
        xbmc.executebuiltin('SetFocus(%d,%d,absolute)' % (control, index), True)
        require(xbmc.getInfoLabel('System.CurrentControlId') == str(control), 'ACTUAL_NATIVE_MENU_FOCUS_REQUIRED')
        require(xbmc.getInfoLabel('Container(%d).ListItem.Label' % control) == request['label'],
                'LIVE_NATIVE_MENU_LABEL_REQUIRED')
        reply = json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Input.Select"}'))
        require('error' not in reply, 'ACTUAL_NATIVE_MENU_SELECT_RPC_REQUIRED')
        return dict(actual_selected_label=request['label'])
    if kind == 'context-button':
        control = request['control']
        require(type(control) is int and 1001 <= control <= 1100 and
                xbmcgui.getCurrentWindowDialogId() == 10106, 'ACTUAL_BOUNDED_NATIVE_CONTEXT_BUTTON_REQUIRED')
        require(xbmc.getCondVisibility('Control.IsVisible(%d)' % control) and
                xbmc.getInfoLabel('Control.GetLabel(%d)' % control) == request['label'], 'LIVE_VISIBLE_NATIVE_CONTEXT_LABEL_REQUIRED')
        xbmc.executebuiltin('SetFocus(%d)' % control, True)
        require(xbmc.getInfoLabel('System.CurrentControlId') == str(control) and
                xbmc.getInfoLabel('Control.GetLabel(%d)' % control) == request['label'], 'LIVE_NATIVE_CONTEXT_FOCUS_AND_LABEL_REQUIRED')
        reply = json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Input.Select"}'))
        require('error' not in reply, 'ACTUAL_NATIVE_CONTEXT_SELECT_RPC_REQUIRED')
        return dict(actual_context_button=control, actual_selected_label=request['label'])
    if kind == 'cancel-provider-choice':
        heading = xbmc.getInfoLabel('Control.GetLabel(1)')
        require(xbmcgui.getCurrentWindowDialogId() == 12000 and heading in ('Select Quality', 'Select Chapter') and
                heading == request.get('heading'), 'ONLY_RECOGNIZED_PROVIDER_CHOICE_CANCEL_ALLOWED')
        reply = json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Input.Back"}'))
        require('error' not in reply, 'ACTUAL_NATIVE_CHOICE_CANCEL_RPC_REQUIRED')
        CANCELLED_CHOICE = dict(heading=heading, monotonic=time.monotonic(), event_sequence=EVENTS.sequence)
        return dict(deliberate_cancel=dict(CANCELLED_CHOICE))
    if kind == 'ack-cancelled-playback-failure':
        require(CANCELLED_CHOICE is not None and time.monotonic() - CANCELLED_CHOICE['monotonic'] <= 15,
                'RECENT_OBSERVED_DELIBERATE_CHOICE_CANCEL_REQUIRED')
        require(not xbmc.Player().isPlayingVideo() and not any(event['event'] == 'AVStarted' and
                event['sequence'] > CANCELLED_CHOICE['event_sequence'] for event in EVENTS.events),
                'NO_NEW_AV_AFTER_CANCEL_REQUIRED')
        if xbmcgui.getCurrentWindowDialogId() != 12002:
            return dict(acknowledged=False, dialog=xbmcgui.getCurrentWindowDialogId())
        require(xbmc.getInfoLabel('Control.GetLabel(1)') == 'Playback failed' and
                xbmc.getInfoLabel('Control.GetLabel(9)') ==
                'One or more items failed to play. Check the log for more information about this message.',
                'ONLY_EXACT_STALE_CANCELLED_PLAYBACK_FAILURE_ALLOWED')
        xbmc.executebuiltin('SetFocus(11)', True)
        require(xbmc.getInfoLabel('System.CurrentControlId') == '11', 'ACTUAL_PLAYBACK_FAILURE_OK_FOCUS_REQUIRED')
        reply = json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Input.Select"}'))
        require('error' not in reply, 'ACTUAL_CANCELLED_FAILURE_ACK_RPC_REQUIRED')
        CANCELLED_CHOICE = None
        return dict(acknowledged=True, exact_cancelled_playback_failure=True)
    if kind == 'ack-parent-identity-refusal':
        require(xbmcgui.getCurrentWindowDialogId() == 12002 and
                xbmc.getInfoLabel('Control.GetLabel(1)') == 'Infinity Tracked' and
                xbmc.getInfoLabel('Control.GetLabel(9)') ==
                'This item has no verifiable WatchNixtoons2 source location. Nothing was changed.',
                'ONLY_EXACT_EXISTING_INFINITY_PARENT_IDENTITY_REFUSAL_ALLOWED')
        xbmc.executebuiltin('SetFocus(11)', True)
        require(xbmc.getInfoLabel('System.CurrentControlId') == '11', 'ACTUAL_IDENTITY_REFUSAL_OK_FOCUS_REQUIRED')
        reply = json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Input.Select"}'))
        require('error' not in reply, 'ACTUAL_EXISTING_IDENTITY_REFUSAL_ACK_RPC_REQUIRED')
        return dict(acknowledged=True, exact_existing_identity_refusal=True)
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
            require(len(raw.encode()) <= 65536, 'BOUNDED_QA_REQUEST_REQUIRED')
            request = json.loads(raw)
        except (OSError, ValueError, RuntimeError):
            continue
        if request.get('pid') != pid or type(request.get('sequence')) is not int or request['sequence'] <= last:
            continue
        last = request['sequence']
        reply = dict(pid=pid, sequence=last, passed=False)
        try:
            reply.update(passed=True, result=action(request))
        except Exception as error:
            reply.update(error=repr(error), traceback=traceback.format_exc())
        reply['bootstrap_phases'] = list(BOOTSTRAP_PHASES)
        payload = json.dumps(reply)
        if len(payload.encode()) > 4 * 1024 * 1024:
            payload = json.dumps(dict(pid=pid, sequence=last, passed=False, error='BOUNDED_REPLY_EXCEEDED'))
        pending = root / 'reply.pending'
        pending.write_text(payload)
        pending.replace(root / 'reply.json')


if __name__ == '__main__':
    serve()
