"""Selected actual native and Infinity watched actions; engineering profile only."""
import json
import time

IMDB = 'tt1254207'


def run(rpc, observer, until, passed, record, alive, directory, filename):
    inputs = []
    def observed_input(value):
        inputs.append(value); record('watched_actual_input', value)
        return value
    def ui(): return observer('watched_ui')
    def state():
        value = observer('watched_state')
        return value if value.get('stable') else None
    def dialog(number):
        return until(lambda: (lambda value: value if value['dialog'] == number else None)(ui()),
                     'actual watched-probe dialog ' + str(number), 20)
    def choose_row(value, predicate, input_kind='select', menu_control=None, **extra):
        matches = [(int(control), row) for control, rows in value['containers'].items()
                   for row in rows if (menu_control is None or int(control) == menu_control) and predicate(row)]
        assert len(matches) == 1, ('UNIQUE_REAL_ROW_REQUIRED', matches)
        control, row = matches[0]
        return observed_input(observer('watched_select', control=control, index=row['index'], label=row['label'],
                        path=row['path'], window=value['window'], dialog=value['dialog'],
                        input=input_kind, **extra))
    def click_button(value, expected):
        matches = [int(control) for control, row in value['controls'].items()
                   if row['label'] == expected and (row['enabled'] is True or
                      (int(control) in (-180, -179) and row['visible'] and row['requires_native_focus_acceptance']))]
        assert len(matches) == 1, ('UNIQUE_REAL_BUTTON_REQUIRED', expected, matches)
        return observed_input(observer('watched_button', dialog=value['dialog'], control=matches[0], label=expected))
    def context_button(expected): click_button(dialog(10106), expected)
    # Let the existing Set content dialog enforce enabled-scraper admission.
    # Require actual local-provider selection/readback and NFO identity below;
    # the earlier generic addon-details assertion duplicated this admission.
    record('watched_scraper_selection', {'required': 'metadata.local',
           'configured_default': rpc('Settings.GetSettingValue', {'setting': 'scrapers.moviesdefault'})['value']})
    assert not ui()['playing']
    assert rpc('GUI.ActivateWindow', {'window': 'videos', 'parameters': ['sources://video/', 'return']}) == 'OK'
    source = until(lambda: (lambda value: value if value['window'] == 10025 and
                           any(row['path'].rstrip('/') == directory.rstrip('/') for rows in value['containers'].values() for row in rows)
                           else None)(ui()), 'normal configured movie source', 20)
    choose_row(source, lambda row: row['path'].rstrip('/') == directory.rstrip('/'), 'context')
    context_button('Set content')
    content = dialog(10132); click_button(content, 'This directory contains')
    choice = dialog(12000); assert choice['heading'] == 'This directory contains'
    choose_row(choice, lambda row: row['label'] == 'Movies', menu_control=3, heading='This directory contains')
    content = dialog(10132); click_button(content, 'Choose information provider')
    choice = dialog(12000); assert choice['heading'] == 'Movie information'
    choose_row(choice, lambda row: row['label'] == 'Local information only' and row['path'] == 'metadata.local',
               menu_control=6, heading='Movie information', scraper='metadata.local')
    content = until(lambda: (lambda value: value if value['dialog'] == 10132 and
                            value['controls'].get('-180', {}).get('value') == 'Movies' and
                            value['controls'].get('-179', {}).get('value') == 'Local information only'
                            else None)(ui()), 'actual returned Movies/local scraper settings', 15)
    record('watched_content_settings_readback', content['controls'])
    click_button(content, 'OK')
    refresh = dialog(10100); click_button(refresh, 'No')
    until(lambda: ui()['dialog'] in (0, -1, 9999), 'normal Set content completion', 15)
    assert not ui()['scan_running'], 'SCAN_ALREADY_RUNNING_NO_TOGGLE_RETRY'
    assert rpc('VideoLibrary.Scan', {'directory': directory, 'showdialogs': False}) == 'OK'

    def imported():
        rows = rpc('VideoLibrary.GetMovies', {'properties': ['file', 'uniqueid', 'playcount', 'resume']}).get('movies', [])
        matches = [row for row in rows if row.get('file') == filename and row.get('uniqueid', {}).get('imdb') == IMDB]
        assert len(matches) <= 1, 'DUPLICATE_FIXTURE_LIBRARY_ROWS'
        return matches[0] if len(matches) == 1 and not ui()['scan_running'] else None
    movie = until(imported, 'real local NFO movie scan and allocated identity', 60)
    movieid = movie['movieid']; assert type(movieid) is int and movieid > 0 and movie['playcount'] == 0
    assert movie.get('resume', {}).get('position', 0) == 0, 'FIXTURE_WAS_ALREADY_PLAYED'
    baseline = until(state, 'stable original disposable CC store', 20)
    for bucket in ('items', 'watched', 'watchlist', 'collection', 'later', 'infinity_watched_overrides', 'pending_kodi_sync'):
        assert baseline['selected'][bucket] == [], ('FIXTURE_ALREADY_RECORDED', bucket)
    passed('watched_fixture_normal_library_admission', movie=movie, original_store=baseline,
           data_scope='Fresh disposable profile; no owner store or fabricated history')

    def open_movie_context():
        assert not ui()['playing']
        assert rpc('GUI.ActivateWindow', {'window': 'videos', 'parameters': ['videodb://movies/titles/', 'return']}) == 'OK'
        value = until(lambda: (lambda value: value if value['window'] == 10025 and
                              any(row['dbid'] == str(movieid) and row['imdb'] == IMDB and row['media'] == 'movie'
                                  for rows in value['containers'].values() for row in rows) else None)(ui()),
                      'actual allocated movie row', 20)
        choose_row(value, lambda row: row['dbid'] == str(movieid) and row['imdb'] == IMDB and row['media'] == 'movie',
                   'context', movieid=movieid)

    def completed(playcount, watched, override):
        actual = rpc('VideoLibrary.GetMovieDetails', {'movieid': movieid, 'properties': ['file', 'uniqueid', 'playcount', 'resume']})['moviedetails']
        assert actual['movieid'] == movieid and actual['file'] == filename and actual['uniqueid']['imdb'] == IMDB
        assert type(actual['playcount']) is int
        saved = state()
        if saved is None: return None
        chosen = saved['selected']
        if actual['playcount'] != playcount or len(chosen['watched']) != watched or len(chosen['infinity_watched_overrides']) != override or chosen['pending_kodi_sync']:
            return None
        assert actual['resume']['position'] == 0
        if watched:
            assert chosen['watched'][0]['play_count'] == 1 and chosen['watched'][0]['watched'] is True
            assert chosen['watched'][0]['dbid'] == movieid and type(chosen['watched'][0]['dbid']) is int
        if override:
            assert chosen['infinity_watched_overrides'][0]['watched'] is False
            assert chosen['infinity_watched_overrides'][0]['dbid'] == movieid and type(chosen['infinity_watched_overrides'][0]['dbid']) is int
        assert chosen['items'] == [], 'MANUAL_MARK_CREATED_PLAYBACK_PROGRESS'
        for bucket in ('sources', 'ratings', 'lists', 'resume_hidden'):
            assert chosen[bucket] == baseline['selected'][bucket], ('UNRELATED_SELECTED_RECORD_CHANGED', bucket)
        assert saved['unrelated_bucket_hashes'] == baseline['unrelated_bucket_hashes'], 'UNRELATED_DISPOSABLE_RECORD_CHANGED'
        for bucket in ('watchlist', 'collection', 'later'):
            assert chosen[bucket] == [], ('WATCHED_ACTION_CREATED_LIST_MEMBERSHIP', bucket)
        alive()
        return {'library': actual, 'saved': saved}

    for name, native_label, infinity_label, expected in (
        ('native_mark', 'Mark as watched', None, (1, 0, 0)),
        ('native_unmark', 'Mark as unwatched', None, (0, 0, 0)),
        ('Infinity_mark', 'Infinity Trakt', 'Mark as Watched', (1, 1, 0)),
        ('Infinity_unmark', 'Infinity Trakt', 'Mark as Unwatched', (0, 0, 1)),
    ):
        first_input = len(inputs)
        open_movie_context(); context_button(native_label)
        if infinity_label:
            def menu():
                value = ui()
                return value if value['dialog'] not in (0, -1, 9999) and value['Infinity_popup'] == '1' and value['Infinity_title'] == 'Infinity Trakt' and any(
                    row['label'] == infinity_label for row in value['containers'].get('50', [])) else None
            value = until(menu, 'actual Infinity Trakt action menu', 20)
            choose_row(value, lambda row: row['label'] == infinity_label, menu_control=50, heading='Infinity Trakt')
        prior = None; since = None
        def quiescent_semantics():
            nonlocal prior, since
            result = completed(*expected)
            if result is None: prior = since = None; return None
            view = ui()
            if view['window'] != 10025 or view['dialog'] not in (0, -1, 9999):
                prior = since = None; return None
            rows = [row for rows in view['containers'].values() for row in rows
                    if row['dbid'] == str(movieid) and row['imdb'] == IMDB and row['media'] == 'movie']
            if len(rows) != 1 or rows[0]['playcount'] != (str(expected[0]) if expected[0] else ''):
                prior = since = None; return None
            semantic = json.dumps({'library': result['library'], 'selected': result['saved']['selected'],
                                   'unrelated': result['saved']['unrelated_bucket_hashes'], 'row': rows[0]}, sort_keys=True)
            now = time.monotonic()
            if semantic != prior: prior, since = semantic, now; return None
            if now - since < .75: return None
            return dict(result, returned_view=view, semantic_stability_seconds=now-since)
        result = until(quiescent_semantics, 'one actual ' + name + ' with UI return and two stable semantic reads', 20)
        passed('watched_' + name, action_clicked_once=True, input_receipts=inputs[first_input:], result=result)
    return {'status': 'PASS_SELECTED_WATCHED_ACTIONS', 'movieid': movieid,
            'original_incident_B': 'NOT_REPRODUCED_BY_THIS_CASE; absent original fault stack prevents attribution'}
