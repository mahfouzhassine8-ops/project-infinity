"""Selected real API36 tracking probe on unchanged69 + normally installed ZIP.

No app/build/sign dispatch at import. Prerequisite or observer failures are
BLOCKED and unreached steps remain NOT_RUN. Only observed functional assertions
after the relevant genuine Infinity workflow report FAIL.
"""
import argparse
import codecs
import json
import os
from pathlib import Path
import socket
import re
import time
import traceback
from urllib.parse import parse_qs, urlencode, urlsplit

import qualify_android_baseline as base
from stage_tracking_android import selected_focus

HERE = Path(__file__).resolve().parent
QA = 'script.infinity.trackingqa'
QA_PROFILE = base.PROFILE + '/addon_data/' + QA
WNT = 'plugin.video.watchnixtoons2'
QUEEN_PARENT = '/anime/queen-s-blade?season=all&lang=dub'
QUEEN_E4 = '/queens-blade-episode-4-english-dubbed'
REZERO_PARENT = '/anime/re-zero-starting-life-in-another-world?season=all&lang=dub'


class ObserverBlocked(RuntimeError):
    pass


class FunctionalFailure(RuntimeError):
    pass


def functional(value, label):
    if not value:
        raise FunctionalFailure(label)


class FeatureDevice(base.Device):
    # Independent feature transport. The five-method baseline RPC is untouched.
    METHODS = frozenset(('JSONRPC.Ping', 'GUI.GetProperties', 'GUI.ActivateWindow',
        'XBMC.GetInfoLabels', 'Input.Home', 'Input.Right', 'Input.Left', 'Input.Up',
        'Input.Down', 'Input.Back', 'Input.Select', 'Input.ExecuteAction',
        'Addons.GetAddonDetails', 'Addons.ExecuteAddon', 'Player.GetActivePlayers',
        'Player.GetItem', 'Player.GetProperties', 'Player.Stop', 'Player.Seek'))

    def rpc(self, method, params=None, timeout=5):
        base.require(method in self.METHODS, 'EXACT_SELECTED_FEATURE_RPC_METHOD')
        if method == 'Input.ExecuteAction':
            base.require(params == {'action': 'firstpage'}, 'ONLY_NATIVE_LIST_FIRSTPAGE_ACTION')
        if method == 'Addons.ExecuteAddon':
            base.require(params in ({'addonid': QA}, {'addonid': base.CC, 'params': ['theme']}), 'ONLY_INSTALLED_OBSERVER_OR_EXISTING_THEME_UI')
        if method == 'Player.Seek':
            base.require(set(params) == {'playerid', 'value'} and params['value'] == {'percentage': 96}, 'ONLY_SELECTED_REAL_MOVIE_COMPLETION_THRESHOLD_SEEK')
        deadline = time.monotonic() + min(timeout, 15)
        def remaining():
            seconds = deadline - time.monotonic()
            if seconds <= 0:
                raise TimeoutError('Absolute feature RPC deadline: ' + method)
            return seconds
        request = dict(jsonrpc='2.0', id=469, method=method)
        if params is not None:
            request['params'] = params
        with socket.create_connection(('127.0.0.1', 19090), timeout=remaining()) as conn:
            conn.settimeout(remaining())
            conn.sendall(json.dumps(request).encode())
            utf8, decoder, pending, received = codecs.getincrementaldecoder('utf-8')(), json.JSONDecoder(), '', 0
            while received < 2 * 1024 * 1024:
                conn.settimeout(remaining())
                chunk = conn.recv(min(65536, 2 * 1024 * 1024 - received))
                if not chunk:
                    break
                received += len(chunk)
                pending += utf8.decode(chunk)
                while pending.strip():
                    remaining()
                    pending = pending.lstrip()
                    try:
                        reply, end = decoder.raw_decode(pending)
                    except ValueError:
                        break
                    pending = pending[end:]
                    if reply.get('id') != 469:
                        continue
                    base.require('error' not in reply and reply.get('jsonrpc') == '2.0', 'ACTUAL_FEATURE_RPC_ERROR:' + str(reply))
                    remaining()
                    return reply['result']
        raise ConnectionError('Incomplete bounded feature RPC reply: ' + method)


def until(device, fn, label, seconds=60):
    deadline, last = time.monotonic() + seconds, None
    while time.monotonic() < deadline:
        device.alive()
        last = fn()
        if last:
            return last
        time.sleep(.4)
    raise TimeoutError(label + '; last=' + repr(last)[:500])


def labels(device, values):
    return device.rpc('XBMC.GetInfoLabels', dict(labels=values))


def gui(device):
    return device.rpc('GUI.GetProperties', dict(properties=['currentwindow', 'currentcontrol', 'skin']))


def native_select_path(device, path, control, out, label, seconds=20):
    """Bootstrap only: focus already belongs to the native list; read every selection."""
    until(device, lambda: labels(device, ['System.CurrentControlId'])['System.CurrentControlId'] == str(control),
          'Actual filebrowser/list focus ' + str(control), seconds)
    device.rpc('Input.ExecuteAction', dict(action='firstpage'))
    observations = []
    for _ in range(1500):
        prefix = 'Container(%d).ListItem.' % control
        names = [prefix + 'FileNameAndPath', prefix + 'Label', 'System.CurrentControlId']
        actual = labels(device, names)
        observations.append(actual)
        base.require(actual['System.CurrentControlId'] == str(control), 'ACTUAL_NATIVE_LIST_STILL_FOCUSED')
        if actual[prefix + 'FileNameAndPath'].rstrip('/') == path.rstrip('/'):
            base.save(out / (label + '-native-selection.json'), dict(expected_path=path, live=actual, observations=observations))
            device.rpc('Input.Select')
            return
        device.rpc('Input.Down')
        time.sleep(.05)
        if len(observations) > 2 and actual == observations[0]:
            break
    base.save(out / (label + '-native-selection.json'), dict(expected_path=path, observations=observations))
    raise RuntimeError('Exact native selected path missing: ' + path)


def addon_details(device, addon):
    try:
        return device.rpc('Addons.GetAddonDetails', dict(addonid=addon, properties=['version', 'enabled']))['addon']
    except RuntimeError:
        return None


def native_paths(device, control):
    label = 'Container(%d).NumItems' % control
    count = int(labels(device, [label])[label] or 0)
    base.require(0 <= count <= 1500, 'BOUNDED_ACTUAL_NATIVE_DIRECTORY')
    names = ['Container(%d).ListItemAbsolute(%d).FileNameAndPath' % (control, i) for i in range(count + 1)]
    result = []
    for start in range(0, len(names), 100):
        result.extend(labels(device, names[start:start + 100]).values())
    return result


def install_zip(device, row, staged, out, label):
    before = addon_details(device, row['addon'])
    # Native AddonBrowser::OnClick exact addons://install/ -> InstallFromZip.
    device.rpc('Input.Home')
    device.rpc('GUI.ActivateWindow', dict(window='addonbrowser', parameters=['addons://']))
    native_select_path(device, 'addons://install/', 50, out, label + '-open')
    remote = staged['remote_zip_directory']
    until(device, lambda: labels(device, ['System.CurrentControlId'])['System.CurrentControlId'] == '450',
          'Actual normal ZIP filebrowser focus', 20)
    # Use the actual visible row paths; FolderPath belongs to media windows and
    # is not an authoritative filebrowser current-directory API.
    if remote + row['archive'] not in native_paths(device, 450):
        native_select_path(device, remote, 450, out, label + '-source')
    native_select_path(device, remote + row['archive'], 450, out, label + '-zip')
    detail = until(device, lambda: (d if (d := addon_details(device, row['addon'])) and
        d.get('version') == row['version'] and d.get('enabled') is True else None),
        'Normal Kodi installed/enabled ZIP ' + row['addon'], 120)
    base.save(out / (label + '-installed.json'), dict(before=before, after=detail,
        archive=row['archive'], sha256=row['sha256'], mechanism='Native AddonBrowser InstallFromZip; actual selected filebrowser450 path'))


class Observer:
    def __init__(self, device, out):
        self.device, self.out, self.sequence = device, out, 0
        device.rpc('Addons.ExecuteAddon', dict(addonid=QA))
        def ready():
            text = device.shell('cat', QA_PROFILE + '/ready.json', check=False)
            try:
                data = json.loads(text)
            except ValueError:
                return None
            return data if data.get('pid') == device.pid and data.get('qa') == QA else None
        self.ready = until(device, ready, 'Observer ready for exact current native PID', 45)

    def call(self, action, **values):
        self.sequence += 1
        request = dict(pid=self.device.pid, sequence=self.sequence, action=action, **values)
        path = self.out / 'observer-request.json'
        base.save(path, request)
        self.device.adb('push', path, QA_PROFILE + '/request.pending')
        self.device.shell('mv', QA_PROFILE + '/request.pending', QA_PROFILE + '/request.json')
        def reply():
            raw = self.device.shell('head', '-c', '4194305', QA_PROFILE + '/reply.json', check=False)
            base.require(len(raw.encode()) <= 4 * 1024 * 1024, 'BOUNDED_ACTUAL_OBSERVER_REPLY')
            try:
                result = json.loads(raw)
            except ValueError:
                return None
            return result if result.get('pid') == self.device.pid and result.get('sequence') == self.sequence else None
        result = until(self.device, reply, 'Actual SDK observer ' + action, 45)
        base.save(self.out / ('observer-%03d-%s.json' % (self.sequence, action)), result)
        if result.get('passed') is not True:
            raise ObserverBlocked('OBSERVER_FAILED:' + repr(result))
        return result['result']


def route(parent):
    return 'plugin://' + WNT + '/?' + urlencode(dict(action='actionEpisodesMenu', url=parent))


def content_rows(snapshot, optional=False):
    """One actual visible source-declared Videos content view, never a title match."""
    base.require(snapshot['window'] == 10025 and snapshot['dialog'] in (0, -1, 9999), 'ACTUAL_UNOBSCURED_VIDEOS_CONTENT_REQUIRED')
    if optional and not any(snapshot['controls'].get(str(control)) for control in snapshot['primary_controls']):
        return []  # Observed empty initialization state: wait without selecting a view.
    controls = [control for control in snapshot['primary_controls'] if snapshot['visible_controls'].get(str(control))]
    base.require(len(controls) <= 1, 'AMBIGUOUS_VISIBLE_PRIMARY_CONTENT_CONTROLS_REJECTED')
    if not controls and optional:
        return []
    base.require(len(controls) == 1, 'ONE_VISIBLE_ORIGINAL_VIDEOS_CONTENT_CONTROL_REQUIRED')
    control = controls[0]
    return [dict(row, control=control) for row in snapshot['controls'].get(str(control), [])]


def open_directory(device, observer, destination):
    device.rpc('GUI.ActivateWindow', dict(window='videos', parameters=[destination, 'return']))
    def current():
        value = observer.call('snapshot')
        return value if value['window'] == 10025 and value['dialog'] in (0, -1, 9999) and value['folder'] == destination and content_rows(value, optional=True) else None
    return until(device, current, 'Actual populated original directory: ' + destination, 90)


def exact_episode_row(snapshot, page):
    matches = []
    for row in content_rows(snapshot):
        parsed = urlsplit(row['file'])
        query = parse_qs(parsed.query)
        if parsed.scheme == 'plugin' and parsed.netloc == WNT and query.get('action') == ['actionResolve']:
            raw = query.get('url', [''])[0]
            if raw == page or raw == 'https://www.wcostream.tv' + page:
                matches.append(dict(**{k: row[k] for k in ('control', 'index', 'file', 'label')}))
    base.require(len(matches) == 1, 'EXACT_PUBLISHER_EPISODE_PAGE_NATIVE_ROW_REQUIRED:' + page)
    return matches[0]


def menu_choose(device, observer, expected):
    opened_owned_menu = False
    def find():
        nonlocal opened_owned_menu
        snap = observer.call('snapshot')
        matches = [dict(control=int(control), index=row['index'], label=row['label'],
                        dialog=snap['dialog'], heading=snap['heading'])
            for control, rows in snap['controls'].items() if snap['visible_controls'].get(control)
            for row in rows if row['label'] == expected]
        buttons = [dict(kind='context-button', **button) for button in snap.get('context_buttons', []) if button['label'] == expected]
        if buttons:
            base.require(len(buttons) == 1 and not matches, 'UNIQUE_ACTUAL_NATIVE_CONTEXT_ACTION_REQUIRED')
            return buttons[0]
        if len(matches) == 1:
            return dict(kind='menu-select', **matches[0])
        if snap['dialog'] == 10106 and not opened_owned_menu and expected in ('Add to Watchlist', 'Resume', 'Play'):
            # Original addon.xml Infinity Tracked or the saved row's original
            # Title options command, never an external/provider auth action.
            bridges = [button for button in snap.get('context_buttons', []) if button['label'] in ('Infinity Tracked', 'Title options')]
            base.require(len(bridges) <= 1, 'UNIQUE_EXISTING_FIRSTPARTY_CONTEXT_HANDOFF_REQUIRED')
            if bridges:
                observer.call('context-button', **bridges[0])
                opened_owned_menu = True
        return None
    selection = until(device, find, 'Actual existing title menu label: ' + expected, 20)
    kind = selection.pop('kind')
    observer.call(kind, **selection)


def enter_saved_queen_parent(device, observer, before, passed):
    destination = 'plugin://' + WNT + '/?' + urlencode(dict(action='actionCatalogSection', path='/dubbed-anime-list', section='Q'))
    catalog = open_directory(device, observer, destination)
    matches = []
    for row in content_rows(catalog):
        parsed = urlsplit(row['file'])
        query = parse_qs(parsed.query)
        if parsed.netloc == WNT and query.get('action') == ['actionEpisodesMenu'] and query.get('url') in (
                [QUEEN_PARENT], ['https://www.wcostream.tv' + QUEEN_PARENT]):
            matches.append(row)
    base.require(len(matches) == 1, 'EXACT_ACTUAL_QUEEN_PARENT_CATALOG_ROW_REQUIRED')
    row = dict(**{key: matches[0][key] for key in ('control', 'index', 'file', 'label')})
    inspected = observer.call('inspect', **row)
    base.require(inspected['actual_gui_item']['media_type'] == 'tvshow', 'ACTUAL_TYPED_PARENT_SHOW_REQUIRED_NO_EPISODE_RELABEL')
    observer.call('context', **row)
    menu_choose(device, observer, 'Add to Watchlist')
    saved_state = until(device, lambda: (s if (s := observer.call('state')) and
        len(saved_source(s, row['file'])) == 1 else None), 'Existing typed parent show saved by actual menu', 25)
    base.require(progress_rows(before) == progress_rows(saved_state), 'SAVING_ACTUAL_PARENT_ALONE_CREATES_NO_HISTORY')
    saved = saved_source(saved_state, row['file'])[0]
    watchlist = open_directory(device, observer, 'plugin://script.infinity.commandcenter/?action=library&media=tv&bucket=watchlist')
    cards = [card for card in content_rows(watchlist) if card['key'] == saved['key']]
    base.require(len(cards) == 1, 'UNIQUE_ACTUAL_INFINITY_SAVED_PARENT_CARD_REQUIRED')
    selected = dict(**{key: cards[0][key] for key in ('control', 'index', 'file', 'label')})
    observer.call('click', **selected)
    def children():
        snapshot = observer.call('snapshot')
        return snapshot if snapshot['folder'] == row['file'] and snapshot['dialog'] in (0, -1, 9999) and content_rows(snapshot, optional=True) else None
    snapshot = until(device, children, 'Actual Infinity saved parent opens original provider children', 90)
    passed('actual_typed_parent_save_no_history_and_infinity_child_navigation', saved_key=saved['key'],
           selected_parent=inspected, native_saved_card=selected, provider_folder=row['file'])
    return snapshot, saved['key']


def sections(device, observer, out, label):
    result = {}
    for name, params in [('continue', dict(action='resume')), ('progress', dict(action='library', media='tv', bucket='progress')),
                         ('next', dict(action='library', media='tv', bucket='next'))]:
        destination = 'plugin://script.infinity.commandcenter/?' + urlencode(params)
        device.rpc('GUI.ActivateWindow', dict(window='videos', parameters=[destination, 'return']))
        until(device, lambda: observer.call('snapshot')['folder'] == destination, 'Existing Infinity ' + name, 45)
        result[name] = observer.call('snapshot')
        device.screenshot(label + '-' + name)
    base.save(out / (label + '-actual-sections.json'), result)
    return result


def assert_native_projection(snapshot, projection, required_key=None):
    """Compare real existing-hub projection keys with real native GUI card keys."""
    expected = [entry['key'] for entry in projection]
    actual = [row['key'] for row in content_rows(snapshot) if row['key']]
    base.require(len(expected) == len(set(expected)) and len(actual) == len(set(actual)), 'ONE_NATIVE_CARD_PER_PROJECTED_KEY')
    base.require(set(actual) == set(expected), 'ACTUAL_NATIVE_CARDS_EQUAL_EXISTING_HUB_PROJECTION_KEYS')
    if required_key is not None:
        # This fresh scenario has exactly one source/episode record. Do not use
        # titles, neighboring episodes or an unverified alias to find its card.
        base.require(expected.count(required_key) == actual.count(required_key) == 1,
                     'EXACT_PLAYED_PROGRESS_KEY_PRESENT_ONCE_IN_PROJECTION_AND_NATIVE_GUI')


def movie_continue(device, observer, out, label, required_key=None):
    destination = 'plugin://script.infinity.commandcenter/?action=resume'
    device.rpc('GUI.ActivateWindow', dict(window='videos', parameters=[destination, 'return']))
    until(device, lambda: observer.call('snapshot')['folder'] == destination, 'Actual existing movie Continue', 45)
    state, snapshot = observer.call('state'), observer.call('snapshot')
    assert_native_projection(snapshot, state['continue_entries'], required_key)
    base.save(out / (label + '-actual-continue.json'), dict(snapshot=snapshot, projection=state['continue_entries']))
    device.screenshot(label + '-continue')
    return state


def progress_rows(state):
    data = state['data']
    return dict(items=data.get('items', {}), watched=data.get('watched', {}))


def matching_source_rows(state, page):
    return [row for row in state['data'].get('items', {}).values()
            if any(parse_qs(urlsplit(row.get(field, '')).query).get('url') in ([page], ['https://www.wcostream.tv' + page])
                   for field in ('source', 'stable_source'))]


def saved_source(state, source):
    return [dict(entry, key=key) for key, entry in state['data'].get('watchlist', {}).items()
            if entry.get('source') == source or entry.get('stable_source') == source]


def stop_video(device, observer):
    active = device.rpc('Player.GetActivePlayers')
    floor = event_sequence(observer)
    for player in active:
        base.require(player['type'] == 'video', 'NO_UNSELECTED_AUDIO_PLAYER_CONTROL')
        device.rpc('Player.Stop', dict(playerid=player['playerid']))
    until(device, lambda: not observer.call('playing')['playing'], 'Actual video stopped', 20)
    if active:
        until(device, lambda: any(event['event'] == 'Stopped' and event['sequence'] > floor
              for event in observer.call('events')), 'Genuine SDK Stopped for actual stop', 15)


def record_case_failure(device, observer, out, report, name, error):
    record = dict(case=name, status='FAIL', error=repr(error), traceback=traceback.format_exc())
    for action in ('snapshot', 'playing', 'events', 'state'):
        try:
            base.save(out / (name + '-failure-' + action + '.json'), observer.call(action))
        except Exception as capture_error:
            record['capture_' + action + '_error'] = repr(capture_error)
    report['cases'].append(record)
    base.save(out / 'ANDROID-VERIFICATION.json', report)
    # Preserve the real failure before ending only its actual video; no restart/retry.
    stop_video(device, observer)
    base.crash_free_alive(device)
    snap = observer.call('snapshot')
    if snap['dialog'] == 12000 and snap['heading'] in ('Select Quality', 'Select Chapter'):
        record['choice_cancel'] = observer.call('cancel-provider-choice', heading=snap['heading'])
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            acknowledged = observer.call('ack-cancelled-playback-failure')
            if acknowledged['acknowledged']:
                record['cancelled_failure_ack'] = acknowledged
                break
            time.sleep(.25)
        base.save(out / (name + '-recognized-cancel-cleanup.json'), record)
    # Other modals, including authentication/account dialogs, are retained.
    device.screenshot(name + '-failure')


def event_sequence(observer):
    return max((event['sequence'] for event in observer.call('events')), default=0)


def actual_av(device, observer, event_floor, seconds=120):
    choices = set()
    def playing():
        value = observer.call('playing')
        if value.get('playing') and any(event['event'] == 'AVStarted' and event['sequence'] > event_floor for event in value['events']):
            return value
        # Source-backed original WNT dialogs, using only actual visible options.
        snap = observer.call('snapshot')
        heading = snap['heading']
        if snap['dialog'] == 12000 and heading in ('Select Quality', 'Select Chapter'):
            controls = [control for control in ('3', '6') if snap['visible_controls'].get(control) and snap['controls'].get(control)]
            base.require(len(controls) <= 1, 'UNAMBIGUOUS_VISIBLE_ORIGINAL_SELECT_DIALOG_LIST_REQUIRED')
            if controls:
                control = controls[0]
                candidates = [row for row in snap['controls'][control] if row['label'] and row['label'] != '..']
                if candidates and (heading, snap['dialog'], control) not in choices:
                    selected = candidates[0]
                    observer.call('menu-select', control=int(control), index=selected['index'], label=selected['label'],
                                  dialog=snap['dialog'], heading=heading)
                    choices.add((heading, snap['dialog'], control))
        return None
    return until(device, playing, 'New genuine provider AVStarted/current player', seconds)


def exact_resume_observation(current, original, stored, event_floor):
    """Bound the real offset using the same device clock as the new AV event."""
    if not current.get('playing'):
        return None
    expected, actual = original['item'], current['item']
    for field in ('media_type', 'season', 'episode'):
        base.require(actual[field] == expected[field], 'RESUMED_ACTUAL_TYPED_ITEM_CONTINUITY:' + field)
    for namespace, identifier in expected['ids'].items():
        if identifier:
            base.require(actual['ids'].get(namespace) == identifier, 'RESUMED_ACTUAL_TYPED_ID_CONTINUITY:' + namespace)
    def native_source(item):
        routes = {item.get(field) for field in ('original_listitem_url', 'path')
                  if isinstance(item.get(field), str) and item[field].startswith('plugin://' + WNT + '/')}
        base.require(len(routes) == 1, 'UNAMBIGUOUS_ACTUAL_NATIVE_PROVIDER_SOURCE_URI_REQUIRED')
        return routes.pop()
    base.require(native_source(actual) == native_source(expected), 'RESUMED_ACTUAL_SOURCE_URI_CONTINUITY')
    events = [event for event in current['events'] if event['event'] == 'AVStarted' and event['sequence'] > event_floor]
    base.require(events, 'NEW_ACTUAL_AV_EVENT_REQUIRED_FOR_RESUME_BOUND')
    started = max(events, key=lambda event: event['sequence'])
    elapsed = max(0.0, current['clock_monotonic'] - started['monotonic'])
    position = float(stored['position'])
    base.require(current['time'] <= position + elapsed + 20, 'EXACT_RESUME_UPPER_OFFSET_BOUND_NO_LATE_OVERSHOOT')
    return current if current['time'] >= position - 20 else None


def observed_resume_lower_deadline(error, valid_current=False):
    # This is the outer position-wait deadline after actual same-source AV.
    # Observer/RPC/no-AV timeouts have other labels and remain prerequisites.
    return valid_current is True and isinstance(error, TimeoutError) and str(error).startswith('Existing same-source Infinity resume offset; last=')


def run_public_movie(device, observer, out, passed):
    page = '/fantastic-mr-fox'
    destination = 'plugin://' + WNT + '/?' + urlencode(dict(action='actionCatalogSection', path='/movie-list', section='F'))
    before = observer.call('state')
    snap = open_directory(device, observer, destination)
    row = exact_episode_row(snap, page)
    inspected = observer.call('inspect', **row)
    base.save(out / 'public-movie-actual-gui-sdk.json', inspected)
    base.require(progress_rows(before) == progress_rows(observer.call('state')), 'ACTUAL_MOVIE_BROWSE_NO_HISTORY')
    if inspected['actual_gui_item']['media_type'] == 'movie':
        observer.call('context', **row)
        menu_choose(device, observer, 'Add to Watchlist')
        saved_state = until(device, lambda: (s if (s := observer.call('state')) and
            len(saved_source(s, row['file'])) == 1 else None), 'Existing movie menu save completed', 20)
        base.require(progress_rows(before) == progress_rows(saved_state), 'ACTUAL_MOVIE_SAVE_NO_HISTORY')
        saved = saved_source(saved_state, row['file'])
        base.require(len(saved) == 1, 'ACTUAL_MOVIE_SAVED_KEY')
        saved_key = saved[0]['key']
        snap = open_directory(device, observer, 'plugin://script.infinity.commandcenter/?action=library&media=movie&bucket=watchlist')
        matches = [r for r in content_rows(snap) if r['key'] == saved_key]
        base.require(len(matches) == 1, 'ONE_EXACT_MOVIE_SAVED_ROW')
        row = dict(**{k: matches[0][k] for k in ('control', 'index', 'file', 'label')})
        passed('actual_public_movie_save_only_no_history', key=saved_key)
    else:
        saved_key = None  # Capture final actual classification; never assign it.
    floor = event_sequence(observer)
    observer.call('click', **row)
    actual = actual_av(device, observer, floor)
    base.save(out / 'public-movie-actual-av.json', actual)
    base.require(actual['item']['media_type'] == 'movie' and actual['item']['episode'] < 0,
                 'ACTUAL_PUBLIC_MOVIE_FINAL_TYPED_IDENTITY')
    base.require(actual['total'] >= 300 and actual['time'] < 30, 'ACTUAL_MOVIE_DURATION_AND_BEGINNING')
    samples, began = [actual], time.monotonic()
    while samples[-1]['time'] - actual['time'] < 90:
        base.require(time.monotonic() - began < 180, 'ACTUAL_MOVIE_90_SECOND_MEDIA_CLOCK_BUFFERING_DEADLINE')
        time.sleep(10)
        current = observer.call('playing')
        base.require(current.get('playing') and current['file'] == actual['file'] and
                     current['time'] >= samples[-1]['time'], 'ACTUAL_MOVIE_CLOCK_NEVER_REGRESSES_NO_SEEK')
        samples.append(current)
        base.save(out / 'public-movie-partial-clock.json', samples)
    base.require(samples[-1]['time'] - samples[0]['time'] >= 90, 'AT_LEAST_90_SECONDS_ACTUAL_MOVIE_MEDIA_CLOCK')
    stop_video(device, observer)
    state = until(device, lambda: (s if (s := observer.call('state')) and
        len(matching_source_rows(s, page)) == 1 else None), 'Actual public movie existing progress writer', 35)
    stored = matching_source_rows(state, page)[0]
    base.require(stored.get('media') == 'movie' and float(stored.get('position') or 0) >= 60, 'ACCURATE_MOVIE_PARTIAL_POSITION')
    base.require(float(stored['position']) <= samples[-1]['time'] + 15, 'ACTUAL_MOVIE_STORED_POSITION_MATCHES_OBSERVED_CLOCK')
    movie_continue(device, observer, out, 'movie-partial', stored['key'])
    passed('actual_public_movie_partial_native_clock_and_stop', stored=stored)
    base.require(saved_key is not None, 'ACTUAL_MOVIE_SAVE_MENU_AVAILABLE_NO_SYNTHETIC_METADATA')
    snap = open_directory(device, observer, 'plugin://script.infinity.commandcenter/?action=library&media=movie&bucket=watchlist')
    matches = [r for r in content_rows(snap) if r['key'] == saved_key]
    base.require(len(matches) == 1, 'ONE_ACTUAL_MOVIE_RESUME_ROW')
    row = dict(**{k: matches[0][k] for k in ('control', 'index', 'file', 'label')})
    observer.call('context', **row)
    floor = event_sequence(observer)
    menu_choose(device, observer, 'Resume')
    resumed = actual_av(device, observer, floor)
    exact_resume_observation(resumed, actual, stored, floor)
    resumed = until(device, lambda: exact_resume_observation(observer.call('playing'), actual, stored, floor),
                    'Existing exact movie offset settles within actual AV elapsed bound', 20)
    base.require(resumed['item']['media_type'] == 'movie' and resumed['time'] >= float(stored['position']) - 20,
                 'ACTUAL_MOVIE_EXISTING_RESUME_NO_HARNESS_SEEK')
    resumed_state = observer.call('state')
    exact = matching_source_rows(resumed_state, page)
    base.require(len(exact) == 1 and exact[0]['key'] == stored['key'] and
                 float(exact[0]['position']) >= float(stored['position']) - 15, 'EXACT_MOVIE_PROGRESS_KEY_POSITION_RETAINED_ON_RESUME')
    passed('actual_public_movie_existing_resume', actual=resumed)
    active = device.rpc('Player.GetActivePlayers')
    base.require(len(active) == 1 and active[0]['type'] == 'video', 'EXACT_ACTUAL_MOVIE_PLAYER')
    # Explicitly selected real player seek exercises existing95% threshold;
    # this is not a simulated callback or a seek used to claim resume/five minutes.
    seek = device.rpc('Player.Seek', dict(playerid=active[0]['playerid'], value=dict(percentage=96)))
    after_seek = until(device, lambda: (p if (p := observer.call('playing')).get('playing') and
        p['file'] == resumed['file'] and p['time'] / p['total'] >= .95 else None), 'Real movie clock past original completion threshold', 25)
    watched = until(device, lambda: (s if (s := observer.call('state')) and stored['key'] in s['data'].get('watched', {}) else None),
        'Original completion writer actual watched row', 25)
    completed = watched['data']['watched'][stored['key']]
    base.require(completed.get('media') == 'movie' and completed.get('identity') == stored.get('identity') and
                 completed.get('source') == stored.get('source'), 'ACTUAL_WATCHED_RECORD_EXACT_PLAYED_MOVIE_IDENTITY_AND_ROUTE')
    base.require(stored['key'] not in {entry['key'] for entry in watched['continue_entries']}, 'COMPLETED_MOVIE_NOT_UNFINISHED_CONTINUE')
    passed('actual_public_movie_existing_95_percent_completion', seek=seek, actual_clock=after_seek,
           completion_mode='Actual player seek96% plus real service observation; natural Ended not claimed')
    stop_video(device, observer)
    completed_view = movie_continue(device, observer, out, 'movie-completed')
    base.require(stored['key'] not in {entry['key'] for entry in completed_view['continue_entries']},
                 'COMPLETED_MOVIE_ABSENT_FROM_ACTUAL_NATIVE_AND_PROJECTED_CONTINUE_AFTER_STOP')
    snap = open_directory(device, observer, 'plugin://script.infinity.commandcenter/?action=library&media=movie&bucket=watchlist')
    matches = [r for r in content_rows(snap) if r['key'] == saved_key]
    base.require(len(matches) == 1, 'EXACT_COMPLETED_SAVED_MOVIE_REPLAY_ROW')
    row = dict(**{k: matches[0][k] for k in ('control', 'index', 'file', 'label')})
    observer.call('context', **row)
    floor = event_sequence(observer)
    menu_choose(device, observer, 'Play')
    replay = actual_av(device, observer, floor)
    base.require(replay['item']['media_type'] == 'movie' and replay['time'] < 30, 'REAL_REPLAY_STARTS_AT_BEGINNING_NO_HARNESS_SEEK')
    stop_video(device, observer)
    final = observer.call('state')
    base.require(len(matching_source_rows(final, page)) <= 1, 'NO_DUPLICATE_EXACT_MOVIE_PROGRESS_ON_REPLAY')
    passed('actual_public_movie_replay_beginning_no_duplicate', actual=replay)


def capture_rezero_metadata(device, observer, out, passed):
    snap = open_directory(device, observer, route(REZERO_PARENT))
    observed = {}
    for episode in (3, 4):
        page = '/re-zero-starting-life-in-another-world-episode-%d-english-dubbed' % episode
        row = exact_episode_row(snap, page)
        observed[str(episode)] = observer.call('inspect', **row)
    base.save(out / 'rezero-actual-native-e3-e4-sdk.json', observed)
    valid = all(value['actual_gui_item']['media_type'] == 'episode' and
                value['actual_gui_item']['episode'] == int(number) for number, value in observed.items())
    base.require(valid, 'REZERO_ACTUAL_E3_E4_SDK_REQUIRED_NO_SLUG_NUMBER_INFERENCE')
    passed('actual_rezero_native_e3_e4_metadata_only', observed=observed,
           cross_provider_playback='NOT_RUN_REAL_REGULAR_SOURCE_AND_VERIFIED_PARENT_LINK_REQUIRED')


def capture_ui(device, observer, out):
    stop_video(device, observer)
    result = dict(status='CAPTURED_SELECTED_VIEWPORT_THEME_EVIDENCE_VISUAL_ACCEPTANCE_PENDING', samples=[],
                  all_view_modes='NOT_RUN', physical_Fold='NOT_RUN')
    original = observer.call('snapshot')
    try:
        for width, height, name in ((904, 2316, 'front-portrait'), (2316, 904, 'front-landscape'),
                                     (1812, 2176, 'inner-portrait'), (2176, 1812, 'inner-landscape')):
            device.shell('wm', 'size', str(width) + 'x' + str(height))
            time.sleep(2)
            device.rpc('Input.Home')
            snap = observer.call('snapshot')
            base.require(snap['skin'] == 'skin.infinity.diggz', 'ORIGINAL_INFINITY_SKIN_ON_VIEWPORT')
            device.screenshot('ui-' + name)
            result['samples'].append(dict(viewport=name, requested=[width, height], actual=snap, gui=gui(device)))
        device.shell('wm', 'size', 'reset')
        time.sleep(2)
        if not original.get('theme_available'):
            result.update(status='VIEWPORT_CAPTURED_THEME_UNVERIFIED_OWNER_UNAVAILABLE',
                          theme_status='UNVERIFIED', theme_error=original.get('theme_error'),
                          published_theme=original.get('published_theme'))
            base.save(out / 'independent-viewport-theme-captures.json', result)
            raise RuntimeError('THEME_UNVERIFIED_OWNER_UNAVAILABLE:' + str(original.get('theme_error')))
        for label, value in (('Light Pearl', 'light'), ('Dark', 'dark')):
            device.rpc('Addons.ExecuteAddon', dict(addonid=base.CC, params=['theme']))
            menu_choose(device, observer, label)
            snap = until(device, lambda: (s if (s := observer.call('snapshot'))['theme'] == value else None), 'Existing theme owner ' + value, 20)
            device.screenshot('ui-theme-' + value)
            result['samples'].append(dict(theme=value, actual=snap))
    finally:
        device.shell('wm', 'size', 'reset')
        if original.get('theme_available') and original['theme'] in ('system', 'light', 'dark'):
            device.rpc('Addons.ExecuteAddon', dict(addonid=base.CC, params=['theme']))
            menu_choose(device, observer, {'system': 'Follow System', 'light': 'Light Pearl', 'dark': 'Dark'}[original['theme']])
    base.save(out / 'independent-viewport-theme-captures.json', result)
    return result


def row_request(row):
    return {key: row[key] for key in ('control', 'index', 'file', 'label')}


def route_matches(route_value, **wanted):
    parsed = urlsplit(route_value)
    query = parse_qs(parsed.query)
    return parsed.scheme == 'plugin' and parsed.netloc == base.CC and all(query.get(key) == [value] for key, value in wanted.items())


def breadcrumb(trace, name, **observed):
    trace.append(dict(step=name, observed_epoch=time.time(), **observed))


def infinity_section(device, observer, media, bucket, trace, known_history=()):
    """Native Home9000 -> existing first-party root -> real section row."""
    device.rpc('Input.Home')
    section = 'trakttv' if media == 'tv' else 'traktmovies'
    def home():
        snap = observer.call('snapshot')
        if snap['window'] != 10000 or snap['dialog'] not in (0, -1, 9999): return None
        rows = [row for row in snap['controls'].get('9000', []) if row['section'] == section and row['hubsource'] == 'infinity']
        base.require(len(rows) <= 1, 'UNIQUE_ACTUAL_INFINITY_HOME_OWNER_REQUIRED')
        return (snap, rows[0]) if rows else None
    snap, row = until(device, home, 'Actual visible first-party Infinity Home selection', 45)
    observed = observer.call('home-select', index=row['index'], label=row['label'], section=section, hubsource='infinity')
    breadcrumb(trace, 'home', native=observed, window=snap['window'])
    history_back = []
    trace[-1]['native_history_back'] = history_back
    returned_from = set()
    action = 'tv' if media == 'tv' else 'movies'
    def root():
        current = observer.call('snapshot')
        if history_back and 'observed_to' not in history_back[-1] and current['folder'] != history_back[-1]['observed_from']:
            history_back[-1]['observed_to'] = current['folder']
        if current['window'] != 10025 or current['dialog'] not in (0, -1, 9999): return None
        rows = content_rows(current, optional=True)
        if route_matches(current['folder'], action=action) and rows: return current
        # Original Home onclick uses ActivateWindow(...,return), which may
        # restore the observed saved child/section. Follow only that real history.
        if (rows and current['folder'] in known_history and current['folder'] not in returned_from and
                len(history_back) < 3):
            returned_from.add(current['folder'])
            history_back.append(dict(observed_from=current['folder'], window=current['window'],
                dialog=current['dialog'], focused_control=current['focused_control'], action='Input.Back'))
            device.rpc('Input.Back')
        return None
    root_snapshot = until(device, root, 'Actual first-party Infinity root', 60)
    breadcrumb(trace, 'root', folder=root_snapshot['folder'], window=root_snapshot['window'])
    matches = [row for row in content_rows(root_snapshot) if route_matches(row['file'], action='library', media=media, bucket=bucket)]
    base.require(len(matches) == 1, 'UNIQUE_ACTUAL_INFINITY_SECTION_ROW_REQUIRED:' + bucket)
    selected = matches[0]
    observed = observer.call('click', **row_request(selected))
    def directory():
        current = observer.call('snapshot')
        return current if current['window'] == 10025 and current['dialog'] in (0, -1, 9999) and route_matches(current['folder'], action='library', media=media, bucket=bucket) and content_rows(current, optional=True) else None
    current = until(device, directory, 'Actual Infinity section directory ' + bucket, 60)
    breadcrumb(trace, 'section', bucket=bucket, media=media, folder=current['folder'], selected=row_request(selected), native=observed)
    return current


def prepare_saved_title(device, observer, media):
    """Find a real saved entry, or use its existing native context Save action."""
    page = QUEEN_PARENT if media == 'tv' else '/fantastic-mr-fox'
    expected_action = 'actionEpisodesMenu' if media == 'tv' else 'actionResolve'
    def matches(state):
        found = []
        for key, entry in state['data'].get('watchlist', {}).items():
            parsed = urlsplit(entry.get('source', ''))
            query = parse_qs(parsed.query)
            if parsed.scheme == 'plugin' and parsed.netloc == WNT and query.get('action') == [expected_action] and query.get('url') in ([page], ['https://www.wcostream.tv' + page]):
                found.append(dict(entry, key=key))
        base.require(len(found) <= 1, 'UNIQUE_EXISTING_SAVED_SOURCE_REQUIRED')
        return found
    before = observer.call('state')
    existing = matches(before)
    if not existing:
        # Provider directory access is preparation only, never play-origin proof.
        path, letter = ('/dubbed-anime-list', 'Q') if media == 'tv' else ('/movie-list', 'F')
        directory = open_directory(device, observer, 'plugin://' + WNT + '/?' + urlencode(dict(action='actionCatalogSection', path=path, section=letter)))
        rows = []
        for row in content_rows(directory):
            parsed = urlsplit(row['file']); query = parse_qs(parsed.query)
            if parsed.scheme == 'plugin' and parsed.netloc == WNT and query.get('action') == [expected_action] and query.get('url') in ([page], ['https://www.wcostream.tv' + page]): rows.append(row)
        base.require(len(rows) == 1, 'ACTUAL_CATALOG_TITLE_REQUIRED_FOR_LEGITIMATE_SAVE')
        selected = observer.call('inspect', **row_request(rows[0]))
        base.require(selected['actual_gui_item']['media_type'] == ('tvshow' if media == 'tv' else 'movie'), 'ACTUAL_SAVE_METADATA_PREREQUISITE')
        observer.call('context', **row_request(rows[0]))
        menu_choose(device, observer, 'Add to Watchlist')
        after = until(device, lambda: (state if matches(state := observer.call('state')) else None), 'Existing supported save completed', 25)
        functional(progress_rows(before) == progress_rows(after), 'SAVING_ALONE_CHANGED_PLAYBACK_HISTORY')
        existing = matches(after)
    else:
        after = before
    entry = existing[0]
    identity = after['valid_identities']['watchlist'].get(entry['key'])
    base.require(identity and identity['kind'] == ('tvshow' if media == 'tv' else 'movie'), 'VALID_EXISTING_SAVED_IDENTITY_REQUIRED')
    return entry


def verify_origin(trace, media, require_av=False):
    names = [event['step'] for event in trace]
    required = ['home', 'root', 'section', 'saved'] + (['child'] if media == 'tv' else []) + ['launch'] + (['AVStarted'] if require_av else [])
    functional(names == required, 'COMPLETE_ORDERED_INFINITY_ORIGIN_REQUIRED_NO_PROVIDER_FALLBACK')
    expected_section = 'trakttv' if media == 'tv' else 'traktmovies'
    functional(trace[0]['window'] == 10000 and trace[0]['native']['hubsource'] == 'infinity' and
               trace[0]['native']['section'] == expected_section, 'ACTUAL_FIRSTPARTY_HOME_OWNER_REQUIRED')
    functional(route_matches(trace[1]['folder'], action='tv' if media == 'tv' else 'movies') and
               route_matches(trace[2]['folder'], action='library', media=media, bucket='watchlist'), 'ACTUAL_INFINITY_ROOT_WATCHLIST_CHAIN_REQUIRED')
    functional(bool(trace[3]['key']) and bool(trace[3]['source']), 'ACTUAL_SAVED_KEY_SOURCE_REQUIRED')
    if media == 'tv':
        functional(trace[4]['folder'] == trace[3]['source'], 'CHILD_MUST_COME_FROM_CLICKED_SAVED_PARENT')
    launch = trace[-2] if require_av else trace[-1]
    functional(launch['native_click'] is True, 'ACTUAL_SELECTED_NATIVE_LAUNCH_REQUIRED')
    if require_av:
        functional(any(event['event'] == 'AVStarted' for event in trace[-1]['events']), 'GENUINE_AV_CALLBACK_REQUIRED_AFTER_ORIGIN')


def validate_progress(state, stored, media, selected, parent_source=None):
    """Trust the existing hub's validated identity; raw SDK tags stay diagnostic."""
    identity = state['valid_identities']['items'].get(stored['key'])
    functional(stored['media'] == media and identity and identity['kind'] == ('episode' if media == 'tv' else 'movie'), 'EXISTING_HUB_EXACT_VALID_MEDIA_IDENTITY_REQUIRED')
    functional(stored.get('source') == selected['file'] or stored.get('stable_source') == selected['file'], 'EXACT_PLAYED_SOURCE_RECORD_REQUIRED')
    if media == 'tv':
        functional(stored.get('source_parent') == parent_source and state['series_proof'].get(stored['key']), 'EXACT_PROVED_PARENT_REQUIRED')
        functional(identity.get('season') == stored.get('season') and identity.get('episode') == stored.get('episode'), 'STORED_COORDINATES_MUST_REMAIN_VALID_AND_UNKNOWN_WHEN_UNKNOWN')
    functional(bool(stored.get('label')), 'RETAINED_NATIVE_LABEL_REQUIRED')
    return identity


def run_origin_scenario(device, observer, out, media, scenario, persist):
    trace = scenario['origin_trace']
    scenario['last_step'] = 'fixture_preparation'; persist()
    saved = prepare_saved_title(device, observer, media)
    before_launch_history = progress_rows(observer.call('state'))
    scenario['steps']['fixture_preparation'] = dict(status='PASS', key=saved['key'], source=saved['source'])
    scenario['last_step'] = 'infinity_origin'; persist()
    watchlist = infinity_section(device, observer, media, 'watchlist', trace)
    known_history = [watchlist['folder']]
    cards = [row for row in content_rows(watchlist) if row['key'] == saved['key']]
    base.require(len(cards) == 1, 'ACTUAL_SAVED_WATCHLIST_CARD_REQUIRED')
    selected = cards[0]
    observer.call('inspect', **row_request(selected))
    breadcrumb(trace, 'saved', key=saved['key'], source=saved['source'], row=row_request(selected), folder=watchlist['folder'])
    if media == 'tv':
        observer.call('click', **row_request(selected))
        def children():
            snap = observer.call('snapshot')
            return snap if snap['window'] == 10025 and snap['dialog'] in (0, -1, 9999) and snap['folder'] == saved['source'] and content_rows(snap, optional=True) else None
        child_snapshot = until(device, children, 'Actual saved Queen parent episode list', 90)
        known_history.append(child_snapshot['folder'])
        selected = exact_episode_row(child_snapshot, QUEEN_E4)
        breadcrumb(trace, 'child', folder=child_snapshot['folder'], selected=selected)
    floor = event_sequence(observer)
    scenario['last_step'] = 'saving_browsing_no_history'
    functional(progress_rows(observer.call('state')) == before_launch_history, 'INFINITY_BROWSING_BEFORE_AV_CREATED_HISTORY')
    scenario['steps']['saving_browsing_no_history'] = dict(status='PASS')
    scenario['last_step'] = 'infinity_origin'
    observer.call('click', **row_request(selected))
    breadcrumb(trace, 'launch', selected=row_request(selected), native_click=True)
    verify_origin(trace, media)
    scenario['steps']['infinity_origin'] = dict(status='PASS', trace=trace)
    scenario['last_step'] = 'actual_av'; persist()
    actual = actual_av(device, observer, floor)
    breadcrumb(trace, 'AVStarted', events=actual['events'], native_item=actual['item'])
    verify_origin(trace, media, require_av=True)
    scenario['raw_sdk_diagnostic'] = actual
    scenario['steps']['actual_av'] = dict(status='PASS', events=actual['events'])
    scenario['integration_started'] = True
    scenario['last_step'] = 'eligible_playback'; persist()
    functional(actual['total'] >= 120 and 0 <= actual['time'] < 30, 'ACTUAL_DURATION_AND_INITIAL_CLOCK_REQUIRED')
    expected_source = selected['file'] if media == 'tv' else saved['source']
    functional(expected_source in (actual['item']['path'], actual['item']['original_listitem_url']), 'ACTUAL_PLAYING_NATIVE_SOURCE_MUST_MATCH_INFINITY_SELECTED_CONTENT')
    target = 300 if media == 'tv' else max(90, actual['total'] * .01 + 5)
    began, samples = time.monotonic(), [actual]
    while samples[-1]['time'] - actual['time'] < target:
        base.require(time.monotonic() - began < target + 120, 'BLOCKED_ACTUAL_MEDIA_BUFFERING_DEADLINE')
        time.sleep(10)
        current = observer.call('playing')
        functional(current.get('playing') and current['file'] == actual['file'] and current['time'] >= samples[-1]['time'], 'SAME_ACTUAL_PLAYBACK_CLOCK_REQUIRED')
        samples.append(current)
        base.save(out / (media + '-actual-clock.json'), samples)
    stop_video(device, observer)
    scenario['steps']['eligible_playback'] = dict(status='PASS', actual_clock_delta=samples[-1]['time'] - actual['time'])
    scenario['steps']['stop'] = dict(status='PASS', callbacks=observer.call('events'))
    scenario['last_step'] = 'record'; persist()
    source_page = QUEEN_E4 if media == 'tv' else '/fantastic-mr-fox'
    try:
        state = until(device, lambda: (state if len(matching_source_rows(state := observer.call('state'), source_page)) == 1 else None), 'One actual eligible progress record', 35)
    except TimeoutError as error:
        raise FunctionalFailure('NO_EXACT_ELIGIBLE_PROGRESS_AFTER_GENUINE_INFINITY_PLAYBACK') from error
    stored = matching_source_rows(state, source_page)[0]
    identity = validate_progress(state, stored, media, selected, saved['source'] if media == 'tv' else None)
    functional(samples[-1]['time'] - 20 <= float(stored.get('position') or 0) <= samples[-1]['time'] + 15, 'PERSISTED_POSITION_MATCHES_ACTUAL_CLOCK')
    functional(stored['label'] == actual['item']['label'], 'NATIVE_LABEL_PRESERVED_WITHOUT_INVENTED_EPISODE_NUMBER')
    scenario['steps']['record'] = dict(status='PASS', stored=stored, validated_identity=identity)
    scenario['last_step'] = 'tracking_sections'; persist()
    for bucket, field in ([('progress', 'progress_shows'), ('next', 'next_episodes'), ('continue', 'continue_entries')] if media == 'tv' else [('continue', 'continue_entries')]):
        section_trace = []
        scenario.setdefault('tracking_navigation', []).append(section_trace)
        cards = infinity_section(device, observer, media, bucket, section_trace, known_history=known_history)
        known_history.append(cards['folder'])
        current_state = observer.call('state')
        projection = [entry for entry in current_state[field] if entry.get('media') == media]
        try:
            assert_native_projection(cards, projection, stored['key'])
        except RuntimeError as error:
            if str(error) in ('AMBIGUOUS_VISIBLE_PRIMARY_CONTENT_CONTROLS_REJECTED',
                              'ONE_VISIBLE_ORIGINAL_VIDEOS_CONTENT_CONTROL_REQUIRED', 'ACTUAL_UNOBSCURED_VIDEOS_CONTENT_REQUIRED'):
                raise ObserverBlocked(str(error)) from error
            raise FunctionalFailure('ACTUAL_TRACKING_CARD_PROJECTION_ASSERTION:' + str(error)) from error
        scenario['steps'][bucket] = dict(status='PASS', trace=section_trace, key=stored['key'])
        base.save(out / (media + '-' + bucket + '-actual-gui.json'), cards)
        device.screenshot(media + '-' + bucket)
    scenario['successor'] = 'NOT_ASSERTED_WITHOUT_EXISTING_VERIFIED_ORDERING; unfinished current source required'
    scenario['last_step'] = 'resume'; persist()
    resume_trace = []
    scenario['resume_navigation'] = resume_trace
    cards = infinity_section(device, observer, media, 'continue', resume_trace, known_history=known_history)
    matches = [row for row in content_rows(cards) if row['key'] == stored['key']]
    functional(len(matches) == 1, 'ONE_EXACT_REAL_INFINITY_CONTINUE_CARD_REQUIRED')
    observer.call('context', **row_request(matches[0]))
    floor = event_sequence(observer)
    menu_choose(device, observer, 'Resume')
    resumed = actual_av(device, observer, floor)
    exact_resume_observation(resumed, actual, stored, floor)
    resume_sample = dict(valid_current=False)
    def observed_offset():
        current = observer.call('playing')
        result = exact_resume_observation(current, actual, stored, floor)
        resume_sample['valid_current'] = current.get('playing') is True
        return result
    try:
        resumed = until(device, observed_offset, 'Existing same-source Infinity resume offset', 20)
    except TimeoutError as error:
        if observed_resume_lower_deadline(error, resume_sample['valid_current']):
            raise FunctionalFailure('EXACT_RESUME_LOWER_OFFSET_DEADLINE') from error
        raise
    stop_video(device, observer)
    scenario['steps']['resume'] = dict(status='PASS', observed=resumed, harness_seek=False)
    scenario['status'] = 'PASS'; persist()


def initial_report():
    names = ('fixture_preparation', 'infinity_origin', 'saving_browsing_no_history', 'actual_av', 'eligible_playback', 'stop',
             'record', 'progress', 'next', 'continue', 'resume')
    return dict(status='NOT_RUN', APK_sha256=base.APK_SHA, release_acceptance=False, Fold='NOT_RUN',
        shutdown='NOT_SELECTED', source=os.environ.get('GITHUB_SHA'),
        scenarios={media: dict(status='NOT_RUN', steps={name: dict(status='NOT_RUN') for name in names},
                               origin_trace=[], integration_started=False) for media in ('tv', 'movie')},
        other_entry_points={name: 'NOT_RUN' for name in ('Collection', 'Save For Later', 'Custom Lists', 'Other playable sections')},
        shared_record_view_coverage='NOT_RUN', completion96='NOT_RUN', direct_provider_diagnostics='NOT_ACCEPTANCE')


def classify_scenario(error, scenario):
    if isinstance(error, ObserverBlocked) or str(error) in ('AMBIGUOUS_VISIBLE_PRIMARY_CONTENT_CONTROLS_REJECTED',
            'ONE_VISIBLE_ORIGINAL_VIDEOS_CONTENT_CONTROL_REQUIRED', 'ACTUAL_UNOBSCURED_VIDEOS_CONTENT_REQUIRED'):
        return 'BLOCKED_OBSERVER'
    if isinstance(error, FunctionalFailure) and str(error) == 'SAVING_ALONE_CHANGED_PLAYBACK_HISTORY':
        return 'FAIL'
    if scenario.get('integration_started') and scenario.get('last_step') == 'resume' and (
            str(error).startswith(('RESUMED_ACTUAL_TYPED_ITEM_CONTINUITY:', 'RESUMED_ACTUAL_TYPED_ID_CONTINUITY:')) or
            str(error) in ('RESUMED_ACTUAL_SOURCE_URI_CONTINUITY', 'EXACT_RESUME_UPPER_OFFSET_BOUND_NO_LATE_OVERSHOOT')):
        return 'FAIL'
    if isinstance(error, FunctionalFailure) and (scenario.get('integration_started') or scenario.get('last_step') == 'saving_browsing_no_history'): return 'FAIL'
    if scenario.get('last_step') == 'fixture_preparation': return 'BLOCKED_FIXTURE_PREPARATION'
    if scenario.get('last_step') == 'infinity_origin': return 'BLOCKED_ORIGIN_PREREQUISITE'
    return 'BLOCKED_RUNTIME_PREREQUISITE'


def final_apk_observation(device):
    try:
        paths = device.shell('pm', 'path', base.PACKAGE).splitlines()
        if len(paths) != 1 or not paths[0].startswith('package:/data/app/') or not paths[0].endswith('/base.apk'):
            return dict(status='UNVERIFIED_PACKAGE_QUERY')
        path = paths[0].removeprefix('package:')
        parts = device.shell('sha256sum', path).strip().split()
        if len(parts) != 2 or not re.fullmatch('[0-9a-f]{64}', parts[0]) or parts[1] != path:
            return dict(status='UNVERIFIED_DIGEST_QUERY')
        return dict(status='PASS_EXACT_ORIGINAL69' if parts[0] == base.APK_SHA else 'FAIL_MISMATCH', observed_sha256=parts[0])
    except Exception as error:
        return dict(status='UNVERIFIED_READ_ERROR', error=repr(error))


def run(staged_path, sdk, out):
    base.require(not out.exists(), 'FRESH_SELECTED_ANDROID_EVIDENCE')
    out.mkdir(parents=True)
    report = initial_report()
    device, reader, disposer, observer, phase = None, None, None, None, 'fixture_authentication'
    def persist(): base.save(out / 'ANDROID-VERIFICATION.json', report)
    persist()
    try:
        staged = base.load(staged_path / 'STAGED.json')
        selection = selected_focus()
        base.require(staged.get('selection') == selection and selection['execution_focus'] == 'infinity-origin-acceptance', 'COMMITTED_ORIGIN_ONLY_SELECTION_REQUIRED')
        base.require(staged['status'] == 'ADMITTED_INPUTS_ONLY_NOT_ANDROID_PASS' and staged['baseline']['apk_sha256'] == base.APK_SHA and
            staged['observer_sha256'] == base.sha(HERE / 'tracking_android_observer.py') and
            staged['stage_source_sha256'] == base.sha(HERE / 'stage_tracking_android.py'), 'EXACT_SOURCE_BOUND_STAGING')
        base.require(os.environ.get('GITHUB_ACTIONS') == 'true' and
            os.environ.get('GITHUB_REPOSITORY') == 'mahfouzhassine8-ops/project-infinity' and
            os.environ.get('GITHUB_REF') == 'refs/heads/work/infinity-tracking-integration-20261108', 'SELECTED_DISPOSABLE_FEATURE_WORKFLOW_ONLY')
        for row in [staged['qa'], *staged['dependencies'], *staged['fixture_packages']]:
            base.require(base.sha(staged_path / 'zips' / row['archive']) == row['sha256'], 'STAGED_ZIP_REVALIDATED')
        base.require(base.sha(Path(staged['APK_path'])) == base.APK_SHA, 'UNCHANGED69_APK_REVALIDATED')
        report.update(status='RUNNING_ORIGIN_ACCEPTANCE', selection=selection, fixture=staged['fixture'],
            candidate_version=staged['expected']['cc_version'], harness_sha256=base.sha(__file__),
            observer_sha256=staged['observer_sha256'], stage_sha256=staged['stage_source_sha256'])
        phase = 'environment'
        device = FeatureDevice(out, sdk)
        disposer, report['host_disposal'] = base.retained_disposal(out)
        report['environment'] = base.environment(device, out)
        base.require(not device.shell('pm', 'list', 'packages', base.PACKAGE).strip(), 'FRESH_VM_NO_DATA_RESET')
        report['root_handshake'] = base.root_reconnect(device, out)
        device.adb('install', '--no-streaming', staged['APK_path'], timeout=300)
        base.installed_apk(device)
        device.shell('mkdir', '-p', base.PROFILE, staged['remote_zip_directory'])
        for name in ('guisettings.xml', 'sources.xml'):
            device.adb('push', staged_path / name, base.PROFILE + '/' + name)
        device.adb('push', str(staged_path / 'zips') + '/.', staged['remote_zip_directory'], timeout=180)
        uid = device.shell('stat', '-c', '%u', '/data/user/0/' + base.PACKAGE).strip()
        base.require(uid.isdigit() and int(uid) >= 10000, 'NORMAL_APPLICATION_UID')
        device.shell('chown', '-R', uid + ':' + uid, '/data/media/0/Android/data/' + base.PACKAGE)
        device.shell('restorecon', '-RF', '/data/media/0/Android/data/' + base.PACKAGE)
        device.adb('forward', 'tcp:19090', 'tcp:9090')
        reader = base.start_lifecycle_log(device, out)
        report['initial_start'] = base.start_once(device, 'origin-initial', out)
        base.crash_free_alive(device)
        phase = 'fixture_installation'
        install_zip(device, staged['qa'], staged, out, 'install-observer')
        for i, row in enumerate(staged['dependencies']): install_zip(device, row, staged, out, 'install-dependency-%02d' % i)
        candidate = next(row for row in staged['fixture_packages'] if not row['recovery'])
        install_zip(device, candidate, staged, out, 'install-approved-candidate')
        device.shell('am', 'force-stop', base.PACKAGE)
        base.require(not device.pids(), 'SELECTED_MODULE_ACTIVATION_PROCESS_STOPPED')
        report['module_activation_restart'] = base.start_once(device, 'origin-module-activation', out)
        phase = 'observer_authentication'
        observer = Observer(device, out)
        auth = observer.call('identity')
        base.require(auth['module_files'] == staged['expected']['module_sources'] and auth['module_count'] == 80 and
            auth['manifest_sha256'] == staged['expected']['manifest_sha256'] and auth['cc_version'] == candidate['version'], 'DYNAMIC_E410_NATIVE_FULL80_AUTH_REQUIRED')
        report['authentication'] = dict(status='PASS', identity=auth)
        phase = 'scenarios'
        for media in ('tv', 'movie'):
            scenario = report['scenarios'][media]
            try:
                scenario['status'] = 'RUNNING'; persist()
                run_origin_scenario(device, observer, out, media, scenario, persist)
            except Exception as error:
                scenario.update(status=classify_scenario(error, scenario), blocker_or_failure=repr(error), traceback=traceback.format_exc())
                for action in ('snapshot', 'playing', 'events', 'state'):
                    try: base.save(out / (media + '-outcome-' + action + '.json'), observer.call(action))
                    except Exception as capture_error: scenario['capture_' + action + '_error'] = repr(capture_error)
                persist()
                # Stop only an actual selected video; preserve unknown modals.
                stop_video(device, observer)
                snap = observer.call('snapshot')
                if snap['dialog'] == 12002 and snap['heading'] == 'Infinity Tracked':
                    observer.call('ack-parent-identity-refusal')
                elif snap['dialog'] == 12000 and snap['heading'] in ('Select Quality', 'Select Chapter'):
                    observer.call('cancel-provider-choice', heading=snap['heading'])
                    deadline = time.monotonic() + 8
                    while time.monotonic() < deadline:
                        if observer.call('ack-cancelled-playback-failure')['acknowledged']: break
                        time.sleep(.25)
            base.crash_free_alive(device)
            persist()
        statuses = [case['status'] for case in report['scenarios'].values()]
        report['status'] = ('PASS_SELECTED_INFINITY_ORIGIN_TV_MOVIE' if statuses == ['PASS', 'PASS'] else
                            'FAIL_INFINITY_ORIGIN_ASSERTION' if 'FAIL' in statuses else 'BLOCKED_INFINITY_ORIGIN_ACCEPTANCE')
    except Exception as error:
        report.update(status=('BLOCKED_ENVIRONMENT' if phase == 'environment' else
            'BLOCKED_OBSERVER' if phase == 'observer_authentication' or isinstance(error, ObserverBlocked) else
            'BLOCKED_FIXTURE_PREPARATION' if phase.startswith('fixture') else 'BLOCKED_RUNTIME_PREREQUISITE'),
            setup_phase=phase, blocker=repr(error), traceback=traceback.format_exc())
        if phase == 'scenarios' and str(error) in ('NATIVE_ENGINE_DIED_OR_RESTARTED', 'NATIVE_PID_REUSED', 'BASELINE_PACKAGE_OR_CHILD_CRASH_NO_RETRY'):
            report['status'] = 'FAIL_NATIVE_RUNTIME_DURING_SELECTED_SCENARIO'
        if device:
            try: base.capture_failure(device, out)
            except Exception as capture_error: report['failure_capture_error'] = repr(capture_error)
    finally:
        if device:
            report['measured_UI_actions'] = device.actions
            integrity = final_apk_observation(device)
            report['final_APK_integrity'] = integrity
            if integrity['status'] != 'PASS_EXACT_ORIGINAL69':
                report['status_before_final_integrity'] = report['status']
                if integrity['status'] == 'FAIL_MISMATCH': report['status'] = 'FAIL_INSTALLED_APK_INTEGRITY'
                elif report['status'].startswith('PASS'): report['status'] = 'BLOCKED_FINAL_APK_INTEGRITY_UNVERIFIED'
        if reader:
            try: report['lifecycle_capture'] = base.stop_lifecycle_log(reader, out)
            except Exception as error: report['lifecycle_capture_error'] = repr(error)
        persist()
        if device and disposer: disposer['arm_host_disposal'](device, out)
    return 0 if report['status'] == 'PASS_SELECTED_INFINITY_ORIGIN_TV_MOVIE' else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('staged', 'sdk', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.staged, args.sdk, args.out))
