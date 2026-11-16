"""Read-only observations and guarded real GUI input in a fresh engineering profile.

No controller imports, synthetic CFileItems, database edits, or progress writes.
Actual selected native/Infinity menu actions remain the sole watched-state writers.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

IMDB = 'tt1254207'
PRIMARY = (50, 65050, 65051, 65052, 51, 52, 53, 55, 56, 57, 58, 59,
           500, 501, 502, 503, 504, 505, 506, 507, 509, 591, 592, 602, 609)
LISTS = PRIMARY + (3, 6, 450, 1000)


def label(control):
    if control in (-180, -179):
        assert xbmcgui.getCurrentWindowDialogId() == 10132
        return xbmcgui.Window(10132).getControl(control).getLabel()
    return xbmc.getInfoLabel('Control.GetLabel(%d)' % control)


def visible(control):
    if control in (-180, -179):
        if xbmcgui.getCurrentWindowDialogId() != 10132: return False
        try: return xbmcgui.Window(10132).getControl(control).isVisible()
        except RuntimeError: return False
    return bool(xbmc.getCondVisibility('Control.IsVisible(%d)' % control))


def rpc(method):
    assert method in ('Input.Select', 'Input.ContextMenu')
    reply = json.loads(xbmc.executeJSONRPC(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method})))
    assert 'error' not in reply, reply


def ui():
    containers = {}
    for control in LISTS:
        if not visible(control):
            continue
        count = int(xbmc.getInfoLabel('Container(%d).NumItems' % control) or 0)
        assert 0 <= count <= 250, 'BOUNDED_FRESH_PROFILE_LIST'
        rows = []
        for index in range(count):
            prefix = 'Container(%d).ListItemAbsolute(%d).' % (control, index)
            rows.append({'index': index, 'label': xbmc.getInfoLabel(prefix + 'Label'),
                         'path': xbmc.getInfoLabel(prefix + 'FileNameAndPath'),
                         'imdb': xbmc.getInfoLabel(prefix + 'UniqueID(imdb)'),
                         'dbid': xbmc.getInfoLabel(prefix + 'DBID'),
                         'playcount': xbmc.getInfoLabel(prefix + 'PlayCount'),
                         'media': xbmc.getInfoLabel(prefix + 'DBTYPE')})
        containers[str(control)] = rows
    controls = {}
    for control in (-180, -179, 2, 9, 10, 11, 28, *range(1001, 1101)):
        if visible(control):
            controls[str(control)] = {'label': label(control),
                                     'visible': True,
                                     'enabled': None if control < 0 else bool(xbmc.getCondVisibility('Control.IsEnabled(%d)' % control)),
                                     'requires_native_focus_acceptance': control < 0}
    dialog = xbmcgui.getCurrentWindowDialogId()
    if dialog == 10132:
        for control in (-180, -179):
            if str(control) in controls:
                try: controls[str(control)]['value'] = xbmcgui.Window(10132).getControl(control).getLabel2()
                except RuntimeError as error: controls[str(control)]['value_observation_error'] = str(error)
    return {'pid': os.getpid(), 'window': xbmcgui.getCurrentWindowId(),
            'dialog': dialog, 'heading': label(1),
            'Infinity_popup': xbmc.getInfoLabel('Window(%d).Property(Infinity.UI.Popup)' % dialog),
            'Infinity_title': xbmc.getInfoLabel('Window(%d).Property(Infinity.UI.Title)' % dialog),
            'setting_heading': label(2), 'body': label(9), 'containers': containers,
            'controls': controls, 'folder': xbmc.getInfoLabel('Container.FolderPath'),
            'scan_running': bool(xbmc.getCondVisibility('Library.IsScanningVideo')),
            'playing': xbmc.Player().isPlayingVideo()}


def select(request):
    control, index = request['control'], request['index']
    assert control in LISTS and type(index) is int and 0 <= index <= 250
    assert xbmcgui.getCurrentWindowId() == request['window']
    assert xbmcgui.getCurrentWindowDialogId() == request['dialog'] and visible(control)
    if request['dialog'] in (0, -1, 9999):
        assert request['window'] == 10025 and control in PRIMARY
        assert [n for n in PRIMARY if visible(n)] == [control]
    else:
        assert request['dialog'] == 12000 or control == 50
        assert request.get('heading') in ('This directory contains', 'Movie information', 'Infinity Trakt')
        if request['dialog'] == 12000:
            assert label(1) == request['heading']
        else:
            assert xbmc.getInfoLabel('Window(%d).Property(Infinity.UI.Popup)' % request['dialog']) == '1'
            assert xbmc.getInfoLabel('Window(%d).Property(Infinity.UI.Title)' % request['dialog']) == 'Infinity Trakt'
    xbmc.executebuiltin('SetFocus(%d,%d,absolute)' % (control, index), True)
    prefix = 'Container(%d).ListItem.' % control
    assert xbmc.getInfoLabel('System.CurrentControlId') == str(control)
    assert xbmc.getInfoLabel(prefix + 'Label') == request['label']
    assert xbmc.getInfoLabel(prefix + 'FileNameAndPath') == request['path']
    if request.get('movieid'):
        assert xbmc.getInfoLabel(prefix + 'DBTYPE') == 'movie'
        assert xbmc.getInfoLabel(prefix + 'DBID') == str(request['movieid'])
        assert xbmc.getInfoLabel(prefix + 'UniqueID(imdb)') == IMDB
    if request.get('scraper'):
        assert request['path'] == request['scraper'] == 'metadata.local'
    kind = request['input']
    assert kind in ('inspect', 'select', 'context')
    if kind != 'inspect':
        rpc('Input.ContextMenu' if kind == 'context' else 'Input.Select')
    return {'pid': os.getpid(), 'verified_selected': request['label'], 'path': request['path'],
            'control': control, 'index': index, 'dialog': request['dialog'],
            'movieid': request.get('movieid'), 'input': kind}


def button(request):
    dialog, control = request['dialog'], request['control']
    allowed = {10132: {-180, -179, 28}, 10100: {10}, 10106: set(range(1001, 1101))}
    assert dialog in allowed and control in allowed[dialog]
    assert xbmcgui.getCurrentWindowDialogId() == dialog and visible(control)
    if control >= 0: assert xbmc.getCondVisibility('Control.IsEnabled(%d)' % control)
    assert label(control) == request['label']
    if dialog == 10132:
        assert label(2) == 'Set content'
        assert request['label'] == {-180: 'This directory contains', -179: 'Choose information provider', 28: 'OK'}[control]
    elif dialog == 10100:
        assert label(1) == 'Change content' and label(9) == 'Do you want to refresh information for all items within this path?'
        assert request['label'] == 'No'
    else:
        assert request['label'] in ('Set content', 'Mark as watched', 'Mark as unwatched', 'Infinity Trakt')
    if control < 0:
        # GUIInfo masks negative IDs; use the actual native control. Moving
        # away first means a stale focused-ID cannot stand in for CanFocus.
        assert visible(28) and label(28) == 'OK' and xbmc.getCondVisibility('Control.IsEnabled(28)')
        xbmc.executebuiltin('SetFocus(28)', True)
        assert xbmcgui.Window(10132).getFocusId() == 28
        xbmc.executebuiltin('SetFocus(%d)' % control, True)
        assert xbmcgui.getCurrentWindowDialogId() == 10132
        assert xbmcgui.Window(10132).getFocusId() == control and visible(control) and label(control) == request['label']
    else:
        xbmc.executebuiltin('SetFocus(%d)' % control, True)
        assert xbmc.getInfoLabel('System.CurrentControlId') == str(control) and label(control) == request['label']
    rpc('Input.Select')
    return {'pid': os.getpid(), 'actual_button': control, 'actual_label': request['label'], 'dialog': dialog,
            'negative_control_enabled_proof': 'NATIVE_CANFOCUS_AFTER_OK28_DETOUR' if control < 0 else None}


def bounded(path):
    if not path.exists():
        return None
    assert path.is_file() and not path.is_symlink() and path.stat().st_size <= 8 * 1024 * 1024
    value = path.read_bytes()
    assert len(value) <= 8 * 1024 * 1024
    return value


def state():
    root = Path(xbmcvfs.translatePath(xbmcaddon.Addon('script.infinity.commandcenter').getAddonInfo('profile')))
    journal = root / '.android-checkpoint/participant.json'
    engine = root / '.android-checkpoint/engine.json'
    before, engine_before = bounded(journal), bounded(engine)
    raw = bounded(root / 'continue-watching.json')
    after, engine_after = bounded(journal), bounded(engine)
    if before != after or engine_before != engine_after:
        return {'stable': False, 'reason': 'CONCURRENT_RECEIPT_CHANGE'}
    if before is None or engine_before is None:
        return {'stable': False, 'reason': 'ENGINE_OR_PARTICIPANT_NOT_READY'}
    receipt = json.loads(before)
    engine_identity = json.loads(engine_before)
    assert type(engine_identity.get('schema')) is int and engine_identity['schema'] == 1
    assert type(engine_identity.get('native_api')) is int and engine_identity['native_api'] == 1
    assert type(engine_identity.get('pid')) is int and engine_identity['pid'] == os.getpid()
    assert isinstance(engine_identity.get('owner'), str) and re.fullmatch(r'[A-Za-z0-9_-]{16,128}', engine_identity['owner'])
    assert type(receipt.get('schema')) is int and receipt['schema'] == 1
    assert receipt['owner'] == {'pid': os.getpid(), 'token': engine_identity['owner']}, 'PARTICIPANT_ENGINE_OWNER_MISMATCH'
    assert type(receipt['owner']['pid']) is int
    assert type(receipt['generation']) is int and type(receipt['committed_generation']) is int
    assert 0 <= receipt['committed_generation'] <= receipt['generation']
    digest = hashlib.sha256(raw).hexdigest() if raw is not None else None
    if (receipt['pending'] is not None or receipt['generation'] != receipt['committed_generation'] or
            receipt['proofs']['continue-watching.json'] != digest):
        return {'stable': False, 'reason': 'PENDING_OR_NOT_YET_ACKNOWLEDGED_BYTES'}
    assert receipt['phase'] == 'ACTIVE' and receipt['session'] is None and receipt['stages'] == [], 'WRITER_NOT_IN_ACTIVE_PHASE'
    data = json.loads(raw) if raw is not None else {}
    assert isinstance(data, dict)
    selected, unrelated = {}, {}
    for bucket in ('items', 'sources', 'watched', 'watchlist', 'collection', 'ratings', 'lists', 'later',
                   'infinity_watched_overrides', 'pending_kodi_sync', 'resume_hidden'):
        values = data.get(bucket, {})
        assert isinstance(values, dict), bucket
        selected[bucket], rest = [], {}
        for key, value in values.items():
            entry = value.get('entry', {}) if bucket == 'pending_kodi_sync' and isinstance(value, dict) else value
            identity = entry.get('identity', {}) if isinstance(entry, dict) else {}
            if (isinstance(entry, dict) and entry.get('imdb') == IMDB) or identity.get('ids', {}).get('imdb') == IMDB:
                assert type(identity.get('schema')) is int and identity['schema'] == 1
                assert identity.get('kind') == 'movie' and identity.get('scope') == 'movie'
                assert identity.get('ids', {}).get('imdb') == IMDB and entry.get('media') == 'movie'
                selected[bucket].append({'key': key, 'identity': identity, 'dbid': entry.get('dbid'),
                                         'media': entry['media'], 'play_count': entry.get('play_count'), 'watched': value.get('watched'),
                                         'record_sha256': hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()})
            else:
                rest[key] = value
        unrelated[bucket] = hashlib.sha256(json.dumps(rest, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'stable': True, 'pid': os.getpid(), 'raw_sha256': digest, 'file_absent': raw is None,
            'revision': data.get('revision'), 'generation': receipt['generation'], 'pending': None,
            'engine_owner_matches_current_pid': True,
            'proof_sha256': receipt['proofs']['continue-watching.json'], 'selected': selected,
            'unrelated_bucket_hashes': unrelated, 'engine_receipt_sha256': hashlib.sha256(engine_before).hexdigest() if engine_before else None}


def action(request):
    assert not xbmc.Player().isPlayingVideo(), 'WATCHED_PROBE_REQUIRES_INACTIVE_PLAYBACK'
    kind = request['action']
    if kind == 'watched_ui': return ui()
    if kind == 'watched_select': return select(request)
    if kind == 'watched_button': return button(request)
    if kind == 'watched_state': return state()
    raise RuntimeError('UNSELECTED_WATCHED_PROBE_ACTION')
