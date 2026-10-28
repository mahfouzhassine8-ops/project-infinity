"""Focused host checks against actual APK sources. No Android/shutdown runner.

Kodi transports are substituted explicitly. Production functions are compiled
from the selected source, without executing the native-authenticated bootstrap
on the host. Signature/inventory verification is a separate staging check.
"""
import argparse
import ast
import contextlib
import copy
import hashlib
import json
from pathlib import Path
import statistics
import sys
import tempfile
import time
import tracemalloc
import types
from unittest.mock import patch

HERE = Path(__file__).resolve().parent


def definitions(path, names, namespace):
    tree = ast.parse(path.read_text())
    nodes = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in names]
    if {n.name for n in nodes} != set(names):
        raise AssertionError('Missing production definitions: ' + str(names))
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace


class Home:
    def __init__(self):
        self.values = {}

    def getProperty(self, key):
        return self.values.get(key, '')

    def setProperty(self, key, value):
        self.values[key] = value


def load_hub(root):
    xbmc = types.ModuleType('xbmc')
    xbmc.LOGINFO = 1
    xbmc.log = lambda *a: None
    common = types.ModuleType('common')
    common.atomic_json = lambda *a: (_ for _ in ()).throw(AssertionError('No host writes'))
    common.read_json = lambda *a: {}
    common.persistence_scope = contextlib.nullcontext
    with patch.dict(sys.modules, xbmc=xbmc, common=common):
        module = types.ModuleType('resume_hub')
        exec(compile((root / 'resume_hub.py').read_text(), str(root / 'resume_hub.py'), 'exec'), module.__dict__)
    return module


def fixture(hub, count=600):
    data = dict(schema=2, revision=123, items={}, watched={}, watchlist={}, collection={}, later={}, lists={}, sources={})
    for i in range(count):
        media = 'tv' if i % 2 else 'movie'
        ids = {'tmdb': str(i + 100)}
        identity = hub.media_identity(media, ids, 1, i, ids if media == 'tv' else None)
        key = hub.identity_key(identity)
        entry = dict(media=media, identity=identity, tmdb=str(i + 100), season=1, episode=i,
                     title='Saved ' + str(i), label='Saved ' + str(i), updated=i,
                     position=31.25, duration=100, percentage=31.25,
                     source='/media/' + str(i) + '.mkv',
                     metadata={'cast': [{'name': str(j), 'role': 'Role'} for j in range(40)]})
        data['items'][key] = entry
        data['watched'][key] = copy.deepcopy(entry)
        data['later'][key] = copy.deepcopy(entry)
    data['lists']['Saved'] = copy.deepcopy(data['later'])
    keys = list(data['items'])
    data['resume_hidden'] = {keys[-1]: {'occurrence': 'a' * 32}}
    return data


def projection_checks(root, baseline_root, phase):
    hub, original = load_hub(root), load_hub(baseline_root)
    data = fixture(original)
    unchanged = copy.deepcopy(data)
    count = 0
    for media in ('movie', 'tv', 'all'):
        for bucket in ('items', 'watched', 'later', 'list'):
            expected = original.entries(data, media, bucket, 'Saved')
            if phase == 'baseline':
                actual = hub.entries(data, media, bucket, 'Saved')[:20]
            else:
                actual = hub.entries(data, media, bucket, 'Saved', limit=20)
                assert hub.entries(data, media, bucket, 'Saved') == expected
                assert hub.entries(data, media, bucket, 'Saved', limit=0) == []
            assert actual == expected[:20]
            if actual:
                actual[0]['metadata']['cast'][0]['role'] = 'private copy'
                assert data == unchanged
            count += 1
    # Conflicting ID components and different episodes must keep the exact
    # existing grouping/order; limiting happens after the full identity pass.
    values = list(data['items'].values())[:4]
    for i, value in enumerate(values):
        value['identity']['ids'] = {'tmdb': '777', 'imdb': 'tt00000' + str(i)}
    expected = original.entries(data)
    actual = hub.entries(data) if phase == 'baseline' else hub.entries(data, limit=20)
    assert actual[:20] == expected[:20]
    measured = fixture(original, 1000)
    read_count = 0
    real_copy = hub._entry_copy
    def counted(*args):
        nonlocal read_count
        read_count += 1
        return real_copy(*args)
    hub._entry_copy = counted
    def run():
        if phase == 'baseline':
            return hub.entries(measured, 'all', 'items')[:20]
        return hub.entries(measured, 'all', 'items', limit=20)
    run()
    copies_per_view = read_count
    hub._entry_copy = real_copy
    samples = []
    for _ in range(9):
        start = time.perf_counter()
        run()
        samples.append((time.perf_counter() - start) * 1000)
    tracemalloc.start()
    run()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return dict(equivalent_projection_cases=count, copies_per_20_card_view=copies_per_view,
                samples_ms=samples, median_ms=statistics.median(samples),
                peak_traced_bytes=peak, fixture_rows=1000,
                conditions='CPython host, local in-memory saved metadata; no Android/native latency')


def listing_checks(root, baseline_root, phase):
    hub = load_hub(root)
    data = fixture(hub, 25)
    rows = []
    calls = []
    class Native:
        def setPluginCategory(self, *args): pass
        def setContent(self, *args): pass
        def endOfDirectory(self, *args, **kwargs):
            assert kwargs == dict(succeeded=True, updateListing=False, cacheToDisc=False)
        def addDirectoryItem(self, handle, target, item, isFolder=False):
            calls.append('one')
            rows.append((target, item, isFolder))
        def addDirectoryItems(self, handle, items, totalItems=0):
            calls.append('batch')
            rows.extend(items)
            assert totalItems == len(items)
            return True
    hub.load_view = lambda *args, **kwargs: copy.deepcopy(data)
    ns = dict(hub=hub, time=time, re=__import__('re'), HANDLE=7, PARAMS={'home': '1'},
              PROFILE=Path('/host'), xbmcplugin=Native(),
              xbmcgui=types.SimpleNamespace(Window=lambda _: Home()), setting_bool=lambda *a: True,
              _category=lambda *a: 'Movies', prepare_render=lambda d, v, r: r,
              _list_item=lambda entry, *args: (entry['source'], copy.deepcopy(entry)))
    definitions(root / 'plugin.py', ('listing', '_values_for'), ns)
    ns['listing']('all', 'continue')
    expected = load_hub(baseline_root).entries(data)[:20]
    assert rows == [(entry['source'], entry, False) for entry in expected]
    assert calls == (['one'] * 20 if phase == 'baseline' else ['batch'])
    return dict(exact_submitted_rows=len(rows), native_submission_calls=len(calls),
                card_builder='transport sentinel; actual card-builder source must remain exact')


def search_checks(root, phase):
    with tempfile.TemporaryDirectory(prefix='infinity-query-') as directory:
        profile = Path(directory)
        home = Home()
        cc_profile = profile / 'addon_data/script.infinity.commandcenter'
        cc_profile.mkdir(parents=True)
        class Addon:
            def __init__(self, aid): self.aid = aid
            def getAddonInfo(self, key):
                if key == 'profile': return str(profile / 'addon_data' / self.aid)
                if key == 'path': return str(profile / 'addons' / self.aid)
                if key == 'version': return '1.0'
                return ''
        ns = dict(hashlib=hashlib, json=json, time=time, Path=Path, CC='script.infinity.commandcenter',
                  xbmcaddon=types.SimpleNamespace(Addon=Addon),
                  xbmcvfs=types.SimpleNamespace(translatePath=lambda value: str(profile) if value == 'special://profile' else value),
                  _VisibleCancellation=lambda cancel, progress: cancel)
        names = ['_provider_result', '_query_cache_entries', '_remember_query_answer']
        if phase != 'baseline': names += ['_query_signature', '_query_file_stamp']
        definitions(root / 'infinity_search.py', names, ns)
        cancel = types.SimpleNamespace(iscanceled=lambda: False)
        provider = dict(id='plugin.video.example', root=str(profile / 'addons/example'),
                        contract={'pins': {'router.py': 'a' * 64}, 'dependencies': []})
        ns['route'] = lambda p, q: 'plugin://plugin.video.example/?query=' + q
        native_calls = []
        def native(*args):
            native_calls.append(1)
            return 'completed', {'result': {'files': [{'file': 'plugin://plugin.video.example/play', 'playcount': len(native_calls)}]}}
        ns['_leased_directory'] = native
        def result(): return ns['_provider_result'](provider, 'query', home, cancel)
        assert result()[1] == 'completed'
        assert result()[1] == 'completed' and len(native_calls) == 1
        home.setProperty('Infinity.ContinueWatchingRevision', '456')
        result()
        after_progress = len(native_calls)
        provider['contract']['dependencies'] = [{'id': 'script.module.example', 'root': '/deps', 'version': '2', 'pins': {'entry.py': 'b' * 64}}]
        result()
        after_dependency = len(native_calls)
        provider['root'] += '-reinstalled'
        result()
        after_root = len(native_calls)
        settings = profile / 'addon_data' / provider['id'] / 'settings.xml'
        settings.parent.mkdir(parents=True)
        settings.write_text('<settings/>')
        result()
        after_settings = len(native_calls)
        (cc_profile / 'continue-watching.json').write_text('{"revision": 987}')
        result()
        after_file = len(native_calls)
        expected = (1, 1, 1, 1, 1) if phase == 'baseline' else (2, 3, 4, 5, 6)
        observed = (after_progress, after_dependency, after_root, after_settings, after_file)
        assert observed == expected, (observed, expected, result())
        # In-flight state changes must not be published or made reusable.
        home.values.clear()
        def raced(*args):
            home.setProperty('Infinity.ContinueWatchingRevision', 'newer')
            return 'completed', {'result': {'files': [{'playcount': 0}]}}
        ns['_leased_directory'] = raced
        outcome = result()
        assert outcome[1] == ('completed' if phase == 'baseline' else 'state_changed')
        if phase != 'baseline':
            assert not home.getProperty('Infinity.Search.Cache.' + provider['id'])
        return dict(native_calls_after_progress_dependency_root_settings_file=[after_progress, after_dependency, after_root, after_settings, after_file],
                    stale_inflight_status=outcome[1], transport='Host RPC substitute; not provider/device execution')


def inventory_checks(root, phase):
    home = Home()
    seen = []
    ns = dict(threading=__import__('threading'), time=time, deepcopy=copy.deepcopy,
              re=__import__('re'), _cached=None, _checked_at=-1, _verified={}, _generation=0,
              _monitor=object(), _event_revision='', _scan_lock=__import__('threading').Lock(),
              _lock=__import__('threading').RLock(), INVENTORY_TTL=2, API_VERSION=1,
              xbmcgui=types.SimpleNamespace(Window=lambda _: home), InventoryMonitor=lambda: object())
    rows = [dict(addonid='plugin.video.' + name) for name in ('umbrella', 'seren', 'otaku', 'pov')]
    ns['_rpc'] = lambda *a: {'addons': rows}
    ns['_contracts'] = lambda: ([], 'digest')
    def scan(rows, *args):
        seen.extend(row['addonid'] for row in rows)
        return rows, {}
    ns['_scan'] = scan
    definitions(root / 'provider_inventory.py', ('snapshot',), ns)
    ns['snapshot'](force=True, **({} if phase == 'baseline' else {'provider_id': 'plugin.video.seren'}))
    assert len(seen) == (4 if phase == 'baseline' else 1)
    if phase != 'baseline':
        assert ns['_cached'] is None and ns['_verified'] == {}
        seen.clear()
        ns['snapshot'](force=True)
        assert len(seen) == 4
    return dict(verified_providers_for_selected_search=4 if phase == 'baseline' else 1,
                all_provider_metadata_rows=4, Search_All='all four still scanned',
                transport='Four-row host inventory; no provider recognition timings')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--baseline-root', type=Path, required=True)
    p.add_argument('--phase', choices=('baseline', 'candidate'), required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    report = dict(phase=a.phase, projection=projection_checks(a.root, a.baseline_root, a.phase),
                  listing=listing_checks(a.root, a.baseline_root, a.phase),
                  search=search_checks(a.root, a.phase), inventory=inventory_checks(a.root, a.phase),
                  shutdown='NOT_RUN', Android='NOT_RUN', physical_Fold='NOT_RUN')
    a.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
