"""Selected real API36 tracking probe on unchanged69 + normally installed ZIP.

No app/build/sign dispatch at import. Run only in the selected feature workflow
after root reviews this harness. Missing actual metadata/playable media is FAIL,
and credential-dependent/unexecuted families remain NOT_RUN_BLOCKED.
"""
import argparse
import codecs
import json
import os
from pathlib import Path
import socket
import time
import traceback
from urllib.parse import parse_qs, urlencode, urlsplit

import qualify_android_baseline as base

HERE = Path(__file__).resolve().parent
QA = 'script.infinity.trackingqa'
QA_PROFILE = base.PROFILE + '/addon_data/' + QA
WNT = 'plugin.video.watchnixtoons2'
QUEEN_PARENT = '/anime/queen-s-blade?season=all&lang=dub'
QUEEN_E4 = '/queens-blade-episode-4-english-dubbed'
REZERO_PARENT = '/anime/re-zero-starting-life-in-another-world?season=all&lang=dub'


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
        base.require(result.get('passed') is True, 'OBSERVER_FAILED:' + repr(result))
        return result['result']


def route(parent):
    return 'plugin://' + WNT + '/?' + urlencode(dict(action='actionEpisodesMenu', url=parent))


def open_directory(device, observer, destination):
    device.rpc('GUI.ActivateWindow', dict(window='videos', parameters=[destination, 'return']))
    def current():
        value = observer.call('snapshot')
        return value if value['window'] == 10025 and value['dialog'] in (0, -1, 9999) and value['folder'] == destination and value['controls'].get('50') else None
    return until(device, current, 'Actual populated original directory: ' + destination, 90)


def exact_episode_row(snapshot, page):
    matches = []
    for row in snapshot['controls'].get('50', []):
        parsed = urlsplit(row['file'])
        query = parse_qs(parsed.query)
        if parsed.scheme == 'plugin' and parsed.netloc == WNT and query.get('action') == ['actionResolve']:
            raw = query.get('url', [''])[0]
            if raw == page or raw == 'https://www.wcostream.tv' + page:
                matches.append(dict(control=50, **{k: row[k] for k in ('index', 'file', 'label')}))
    base.require(len(matches) == 1, 'EXACT_PUBLISHER_EPISODE_PAGE_NATIVE_ROW_REQUIRED:' + page)
    return matches[0]


def menu_choose(device, observer, expected):
    def find():
        snap = observer.call('snapshot')
        matches = [dict(control=int(control), index=row['index'], label=row['label'])
            for control, rows in snap['controls'].items() for row in rows if row['label'] == expected]
        return matches[0] if len(matches) == 1 else None
    selection = until(device, find, 'Actual existing title menu label: ' + expected, 20)
    observer.call('menu-select', **selection)


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
    actual = [row['key'] for row in snapshot['controls'].get('50', []) if row['key']]
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
    for _ in range(3):
        current = gui(device)['currentwindow']['id']
        if current in (10000, 10025, 10040):
            break
        device.rpc('Input.Back')
        time.sleep(.25)
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
        if heading in ('Select Quality', 'Select Chapter'):
            rows = snap['controls'].get('450', [])
            candidates = [row for row in rows if row['label'] and row['label'] != '..']
            if candidates and (heading, snap['dialog']) not in choices:
                selected = candidates[0]
                observer.call('menu-select', control=450, index=selected['index'], label=selected['label'])
                choices.add((heading, snap['dialog']))
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
        matches = [r for r in snap['controls'].get('50', []) if r['key'] == saved_key]
        base.require(len(matches) == 1, 'ONE_EXACT_MOVIE_SAVED_ROW')
        row = dict(control=50, **{k: matches[0][k] for k in ('index', 'file', 'label')})
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
    matches = [r for r in snap['controls'].get('50', []) if r['key'] == saved_key]
    base.require(len(matches) == 1, 'ONE_ACTUAL_MOVIE_RESUME_ROW')
    row = dict(control=50, **{k: matches[0][k] for k in ('index', 'file', 'label')})
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
    matches = [r for r in snap['controls'].get('50', []) if r['key'] == saved_key]
    base.require(len(matches) == 1, 'EXACT_COMPLETED_SAVED_MOVIE_REPLAY_ROW')
    row = dict(control=50, **{k: matches[0][k] for k in ('index', 'file', 'label')})
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


def run(staged_path, sdk, out):
    base.require(not out.exists(), 'FRESH_SELECTED_ANDROID_EVIDENCE')
    out.mkdir(parents=True)
    staged = base.load(staged_path / 'STAGED.json')
    base.require(staged['status'] == 'ADMITTED_INPUTS_ONLY_NOT_ANDROID_PASS' and
                 staged['baseline']['apk_sha256'] == base.APK_SHA and
                 staged['observer_sha256'] == base.sha(HERE / 'tracking_android_observer.py') and
                 staged['stage_source_sha256'] == base.sha(HERE / 'stage_tracking_android.py'), 'EXACT_SOURCE_BOUND_STAGING')
    base.require(os.environ.get('GITHUB_ACTIONS') == 'true' and
                 os.environ.get('GITHUB_REPOSITORY') == 'mahfouzhassine8-ops/project-infinity' and
                 os.environ.get('GITHUB_REF') == 'refs/heads/work/infinity-tracking-integration-20261108', 'SELECTED_DISPOSABLE_FEATURE_WORKFLOW_ONLY')
    for row in [staged['qa'], *staged['dependencies'], *staged['fixture_packages']]:
        base.require(base.sha(staged_path / 'zips' / row['archive']) == row['sha256'], 'STAGED_ZIP_REVALIDATED')
    base.require(base.sha(Path(staged['APK_path'])) == base.APK_SHA, 'UNCHANGED69_APK_REVALIDATED')
    report = dict(status='RUNNING_SELECTED_TRACKING_ANDROID', cases=[], APK_sha256=base.APK_SHA,
        fixture=staged['fixture'], source=os.environ['GITHUB_SHA'],
        harness_sha256=base.sha(__file__), stage_sha256=staged['stage_source_sha256'], observer_sha256=staged['observer_sha256'],
        premium_families={name: 'NOT_RUN_BLOCKED_REAL_TEST_CREDENTIALS_OR_PLAYABLE_SOURCE_REQUIRED'
                          for name in ('Umbrella', 'POV', 'Seren', 'Otaku', 'The Crew')},
        movie='NOT_RUN_BLOCKED_REAL_MOVIE_SOURCE_NOT_SELECTED', cross_entry_rezero='NOT_RUN',
        view_theme_matrix='NOT_RUN', module_recovery='NOT_RUN', full_twelve_checks='NOT_RUN',
        shutdown='NOT_SELECTED', Fold='NOT_RUN', release_acceptance=False,
        mandatory_owner_gates=dict(all_supported_families='NOT_RUN_BLOCKED_REAL_AUTH_AND_SOURCES',
            cross_provider_rezero='NOT_RUN_BLOCKED_REAL_REGULAR_SOURCE_AND_EXPLICIT_PARENT_LINK',
            natural_Ended='NOT_RUN', verified_completed_episode_successor='NOT_RUN_NO_CATALOGUE_PROOF',
            all_view_modes='NOT_RUN', physical_Fold='NOT_RUN', forward_APK_install_recovery='NOT_RUN_MODULE_FIXTURE_ONLY'))
    device, reader, disposer, observer, code = None, None, None, None, 1
    def passed(name, **evidence):
        report['cases'].append(dict(case=name, status='PASS', **evidence))
        base.save(out / 'ANDROID-VERIFICATION.json', report)
    try:
        device = FeatureDevice(out, sdk)
        disposer, report['retained_host_disposal'] = base.retained_disposal(out)
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
        report['initial_start'] = base.start_once(device, 'feature-initial', out)
        base.crash_free_alive(device)
        base.save(out / 'original69-installed80.json', base.installed_hashes(device, staged['baseline']))
        install_zip(device, staged['qa'], staged, out, 'install-observer')
        for i, row in enumerate(staged['dependencies']):
            install_zip(device, row, staged, out, 'install-dependency-%02d' % i)
        candidate = next(row for row in staged['fixture_packages'] if not row['recovery'])
        install_zip(device, candidate, staged, out, 'install-authenticated-cc68')
        # Explicit selected restart loads updated service/source; no Close journey.
        previous = dict(pid=device.pid, process_start=device.start_time)
        device.shell('am', 'force-stop', base.PACKAGE)
        base.require(not device.pids(), 'SELECTED_MODULE_ACTIVATION_PROCESS_STOPPED')
        report['module_activation_restart'] = dict(previous=previous, start=base.start_once(device, 'module-activation', out), data_cleared=False)
        observer = Observer(device, out)
        auth = observer.call('identity')
        base.require(auth['module_files'] == staged['expected']['module_sources'] and auth['module_count'] == 80 and
                     auth['manifest_sha256'] == staged['expected']['manifest_sha256'] and auth['cc_version'] == '0.3.5.68', 'DYNAMIC_ORIGINAL_NATIVE_FULL80_CONTROLLER_AUTH')
        passed('normal_zip_install_and_dynamic_original_full80_auth', identity=auth)
        base.crash_free_alive(device)
        try:
            saved_key = None
            before = observer.call('state')
            snap = open_directory(device, observer, route(QUEEN_PARENT))
            row = exact_episode_row(snap, QUEEN_E4)
            inspected = observer.call('inspect', **row)
            base.save(out / 'queens-blade-e4-actual-gui-sdk.json', inspected)
            after_browse = observer.call('state')
            base.require(progress_rows(before) == progress_rows(after_browse), 'BROWSING_ALONE_CREATES_NO_PROGRESS')
            passed('real_wnt_catalog_browse_no_history', exact_page=QUEEN_E4, actual_gui_item=inspected['actual_gui_item'])
            gui_item = inspected['actual_gui_item']
            valid_episode = gui_item.get('media_type') == 'episode' and gui_item.get('episode') == 4
            if valid_episode:
                observer.call('context', **row)
                menu_choose(device, observer, 'Add to Watchlist')
                after_save = until(device, lambda: (s if (s := observer.call('state')) and
                    len(saved_source(s, row['file'])) == 1 else None), 'Existing episode menu save completed', 20)
                base.require(progress_rows(before) == progress_rows(after_save), 'SAVING_ALONE_CREATES_NO_PROGRESS')
                saved = saved_source(after_save, row['file'])
                base.require(len(saved) == 1, 'EXACT_ACTUAL_ROW_SAVED_BY_EXISTING_MENU')
                saved_key = saved[0]['key']
                passed('existing_actual_title_save_no_history', key=saved_key)
                watchlist = open_directory(device, observer, 'plugin://script.infinity.commandcenter/?action=library&media=tv&bucket=watchlist')
                selected = [r for r in watchlist['controls'].get('50', []) if r['key'] == saved_key]
                base.require(len(selected) == 1, 'ACTUAL_SAVED_ROW_KEY_UNIQUE')
                row = dict(control=50, **{k: selected[0][k] for k in ('index', 'file', 'label')})
            floor = event_sequence(observer)
            observer.call('click', **row)
            # Real source chooser, DRM/site errors or missing playable media remain failures;
            # no fake account/server or substituted clip is supplied.
            actual = actual_av(device, observer, floor)
            base.save(out / 'queens-blade-e4-actual-av.json', actual)
            base.require(actual['item']['media_type'] == 'episode' and actual['item']['episode'] == 4,
                         'ACTUAL_PUBLISHER_SDK_EPISODE_METADATA_REQUIRED_NO_INFERRED_SEASON_OR_EPISODE')
            sdk_item = actual['item']
            base.require(actual['total'] >= 420 and actual['time'] < 30, 'ACTUAL_LONG_ENOUGH_SOURCE_STARTS_BEFORE_30_SECONDS')
            samples, began, initial = [actual], time.monotonic(), actual['time']
            while samples[-1]['time'] - initial < 300:
                base.require(time.monotonic() - began < 420, 'ACTUAL_TV_300_SECOND_MEDIA_CLOCK_BUFFERING_DEADLINE')
                time.sleep(10)
                current = observer.call('playing')
                base.require(current.get('playing') and current['file'] == actual['file'] and
                             current['item']['episode'] == 4 and current['time'] >= samples[-1]['time'], 'SAME_REAL_MEDIA_CLOCK_NEVER_REGRESSES_WITHOUT_SEEK')
                samples.append(current)
                base.save(out / 'queens-blade-e4-real-clock.json', samples)
            base.require(samples[-1]['time'] - initial >= 300, 'FIVE_MINUTES_ACTUAL_PLAYBACK_CLOCK')
            active = device.rpc('Player.GetActivePlayers')
            base.require(len(active) == 1 and active[0]['type'] == 'video', 'ONE_ACTUAL_VIDEO_PLAYER')
            device.rpc('Player.Stop', dict(playerid=active[0]['playerid']))
            until(device, lambda: not observer.call('playing')['playing'] and
                  any(e['event'] == 'Stopped' for e in observer.call('events')), 'Genuine native Stopped callback', 30)
            state = until(device, lambda: (s if (s := observer.call('state')) and
                len(matching_source_rows(s, QUEEN_E4)) == 1 else None), 'Existing recorder exact WNT progress', 35)
            stored = matching_source_rows(state, QUEEN_E4)[0]
            base.require(stored.get('episode') == 4 and stored.get('season') == sdk_item['season'] and
                         290 <= float(stored.get('position') or 0) <= samples[-1]['time'] + 15,
                         'EXACT_ACTUAL_EPISODE_POSITION_NO_METADATA_GUESS')
            passed('real_wnt_infinity_e4_300_second_clock_stop_progress', stored=stored, callbacks=observer.call('events'))
            cards = sections(device, observer, out, 'after-wnt-stop')
            current_state = observer.call('state')
            for section, field in (('continue', 'continue_entries'), ('progress', 'progress_shows'), ('next', 'next_episodes')):
                assert_native_projection(cards[section], current_state[field], stored['key'])
            base.require(current_state['series_proof'].get(stored['key']),
                         'LIMITATION_ACTUAL_TV_PARENT_SERIES_PROOF_MISSING_NO_INVENTED_SHOW_GROUP')
            # Unknown/unproved successors must be withheld; do not assert E+1.
            candidates = state['next_episodes']
            for entry in candidates:
                if entry.get('synthetic_next'):
                    base.require(entry.get('next_verified') is True, 'NO_UNPROVED_SYNTHETIC_SUCCESSOR')
            passed('actual_existing_unfinished_tv_cards_present_once_no_invented_successor', next_entries=candidates,
                   key=stored['key'], series_proof=current_state['series_proof'][stored['key']])
            before_restart = observer.call('state')
            device.shell('am', 'force-stop', base.PACKAGE)
            base.require(not device.pids(), 'EXPLICIT_SELECTED_PERSISTENCE_RESTART_STOPPED')
            report['persistence_restart'] = base.start_once(device, 'progress-persistence', out)
            observer = Observer(device, out)
            observer.call('identity')
            after_restart = observer.call('state')
            base.require(progress_rows(after_restart) == progress_rows(before_restart) and
                         after_restart['data'].get('watchlist') == before_restart['data'].get('watchlist'), 'EXISTING_STORE_RELOAD_RETAINS_PROGRESS_AND_SAVED_MEMBERSHIP')
            passed('explicit_restart_exact_progress_and_membership_persistence')
            # Resume is an independent actual existing menu path; never seek or add AV restore.
            base.require(saved_key is not None, 'ACTUAL_GUI_SAVE_METADATA_UNAVAILABLE_NO_INVENTED_SAVED_IDENTITY')
            watchlist = open_directory(device, observer, 'plugin://script.infinity.commandcenter/?action=library&media=tv&bucket=watchlist')
            selected = [r for r in watchlist['controls'].get('50', []) if r['key'] == saved_key]
            base.require(len(selected) == 1, 'EXACT_SAVED_RESUME_ROW')
            row = dict(control=50, **{k: selected[0][k] for k in ('index', 'file', 'label')})
            observer.call('context', **row)
            floor = event_sequence(observer)
            menu_choose(device, observer, 'Resume')
            resumed = actual_av(device, observer, floor)
            exact_resume_observation(resumed, actual, stored, floor)
            resumed = until(device, lambda: exact_resume_observation(observer.call('playing'), actual, stored, floor),
                            'Existing exact episode offset settles within actual AV elapsed bound', 20)
            base.require(resumed['time'] >= stored['position'] - 20, 'EXISTING_EXACT_EPISODE_RESUME_POSITION')
            base.require(resumed['item']['episode'] == 4 and resumed['item']['season'] == sdk_item['season'], 'NO_OTHER_EPISODE_OFFSET')
            exact = matching_source_rows(observer.call('state'), QUEEN_E4)
            base.require(len(exact) == 1 and exact[0]['key'] == stored['key'] and
                         exact[0]['season'] == sdk_item['season'] and exact[0]['episode'] == 4 and
                         float(exact[0]['position']) >= float(stored['position']) - 15,
                         'EXACT_EPISODE_PROGRESS_KEY_POSITION_RETAINED_ON_RESUME')
            passed('existing_saved_exact_episode_resume_no_harness_seek', actual=resumed)
            stop_video(device, observer)
        except Exception as error:
            record_case_failure(device, observer, out, report, 'queens_blade_e4', error)
        base.crash_free_alive(device)
        try:
            run_public_movie(device, observer, out, passed)
            report['movie'] = 'PASS_SELECTED_REAL_PUBLIC_WNT_MOVIE_CASES'
        except Exception as error:
            report['movie'] = 'FAIL_ACTUAL_PUBLIC_WNT_MOVIE'
            record_case_failure(device, observer, out, report, 'public_movie', error)
        base.crash_free_alive(device)
        try:
            persisted = observer.call('state')
            base.require(any(progress_rows(persisted).values()), 'ACTUAL_RECORDED_PROGRESS_REQUIRED_FOR_PERSISTENCE_CASE')
            stop_video(device, observer)
            device.shell('am', 'force-stop', base.PACKAGE)
            base.require(not device.pids(), 'SELECTED_RECORDED_STATE_RESTART_STOPPED')
            report['independent_progress_restart'] = base.start_once(device, 'recorded-state-persistence', out)
            observer = Observer(device, out)
            observer.call('identity')
            reloaded = observer.call('state')
            base.require(progress_rows(persisted) == progress_rows(reloaded) and
                         persisted['data'].get('watchlist') == reloaded['data'].get('watchlist'), 'ACTUAL_RECORDED_STATE_RELOAD_NO_LOSS')
            passed('independent_actual_recorded_state_restart_persistence')
        except Exception as error:
            record_case_failure(device, observer, out, report, 'independent_recorded_state_persistence', error)
        base.crash_free_alive(device)
        try:
            capture_rezero_metadata(device, observer, out, passed)
        except Exception as error:
            record_case_failure(device, observer, out, report, 'rezero_actual_metadata', error)
        try:
            report['view_theme_matrix'] = capture_ui(device, observer, out)
        except Exception as error:
            record_case_failure(device, observer, out, report, 'independent_ui_capture', error)
        base.crash_free_alive(device)
        failed = any(case['status'] == 'FAIL' for case in report['cases'])
        report['status'] = ('FAIL_SELECTED_REAL_TRACKING_ANDROID' if failed else
                            'PASS_SELECTED_REAL_WNT_TRACKING_CASES_OTHER_REQUIREMENTS_NOT_RUN')
        # This is deliberately not an all-family/release PASS.
        code = 1 if failed else 0
    except Exception as error:
        report.update(status='FAIL_SELECTED_REAL_TRACKING_ANDROID', error=repr(error), traceback=traceback.format_exc())
        if observer:
            for name in ('snapshot', 'playing', 'events', 'state'):
                try:
                    base.save(out / ('failure-actual-' + name + '.json'), observer.call(name))
                except Exception as capture_error:
                    report['capture_' + name + '_error'] = repr(capture_error)
        if device:
            base.capture_failure(device, out)
    finally:
        if device:
            report['measured_UI_actions'] = device.actions
            try:
                base.installed_apk(device)
                report['installed_APK_still_original69'] = True
            except Exception as error:
                report['installed_APK_check_error'] = repr(error)
                report['installed_APK_still_original69'] = False
                report['status_before_final_integrity_check'] = report['status']
                report['status'] = 'FAIL_SELECTED_REAL_TRACKING_ANDROID_INSTALLED_APK_INTEGRITY'
                code = 1
        if reader:
            report['lifecycle_capture'] = base.stop_lifecycle_log(reader, out)
        base.save(out / 'ANDROID-VERIFICATION.json', report)
        if device and disposer:
            disposer['arm_host_disposal'](device, out)
    return code


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('staged', 'sdk', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.staged, args.sdk, args.out))
