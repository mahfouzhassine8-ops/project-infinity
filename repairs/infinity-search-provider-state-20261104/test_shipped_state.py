"""Read-only diagnosis of the actual signed453 Search; synthetic fixtures only.

No provider is executed, no Android acceptance claimed, no production edits.
"""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace, ModuleType
import unittest
from urllib.parse import urlencode, quote, parse_qs, urlsplit
from zipfile import ZipFile

APK = Path(os.environ.get('INFINITY_SEARCH_AUDIT_APK', '/tmp/kodi453-published-signed/Infinity-2103453-Combined-Original-Signer.apk'))
APK_SHA = '08ca19e9ff01e3830253980028dbcdbfb36056fd71b06a18cbfb922158ceaac8'
CC = 'script.infinity.commandcenter'
PREFIX = 'assets/addons/' + CC + '/'
with APK.open('rb') as stream:
    assert hashlib.file_digest(stream, 'sha256').hexdigest() == APK_SHA
with ZipFile(APK) as package:
    RAW = package.read(PREFIX + 'infinity_search.py')
    CAP = package.read(PREFIX + 'provider_capabilities.py')
    NAV = json.loads(package.read(PREFIX + 'NAVIGATION-CONTRACTS.json'))
TREE = ast.parse(RAW)
SELECT = {'route', '_query_file_stamp', '_query_signature', '_query_cache_entries',
          '_remember_query_answer', '_provider_result', '_VisibleCancellation'}
CODE = compile(ast.Module(body=[n for n in TREE.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in SELECT], type_ignores=[]), 'signed453/infinity_search.py', 'exec')


class StateDiagnosis(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='search-synthetic-')
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.profile = root / 'profile'; self.profile.mkdir()
        self.progress = root / 'cc'; self.progress.mkdir()
        self.root = root / 'provider'; self.root.mkdir()
        self.provider = dict(id='plugin.video.synthetic', root=str(self.root),
                             contract=dict(params={'action': 'search'}, query_key='q', pins={}))
        for name, content in [('addon.xml', '<addon id="plugin.video.synthetic"/>'), ('main.py', '# synthetic fixture\n')]:
            (self.root / name).write_text(content)
            self.provider['contract']['pins'][name] = hashlib.sha256(content.encode()).hexdigest()
        self.settings = self.profile / 'addon_data' / self.provider['id'] / 'settings.xml'
        self.settings.parent.mkdir(parents=True); self.settings.write_text('<settings/>')
        (self.progress / 'continue-watching.json').write_text('{"revision":1}')
        self.props = {}; self.enabled = True; self.canceled = False
        self.calls = 0; self.during = lambda: None; self.native_status = 'completed'
        self.answer = {'result': {'files': [{'label': 'Synthetic result', 'file': 'plugin://plugin.video.synthetic/?id=1'}]}}
        self.home = SimpleNamespace(getProperty=lambda k: self.props.get(k, ''), setProperty=lambda k, v: self.props.__setitem__(k, v))
        self.cancel = SimpleNamespace(iscanceled=lambda: self.canceled)
        caps = ModuleType('provider_capabilities'); exec(compile(CAP, 'signed453/provider_capabilities.py', 'exec'), caps.__dict__)
        self.deps = {}
        inventory = ModuleType('provider_inventory'); inventory._resolve_search_dependency = lambda identity: self.deps[identity]
        saved = ModuleType('saved_navigation'); saved._source = lambda root, name: (root / name).read_bytes()
        # Only external platform/read boundaries are fixtures. Actual route/pin,
        # dependency, state and result functions above execute unchanged.
        self.old = {name: sys.modules.get(name) for name in ('provider_capabilities', 'provider_inventory', 'saved_navigation')}
        sys.modules.update(provider_capabilities=caps, provider_inventory=inventory, saved_navigation=saved)
        self.addCleanup(self.restore_modules)
        self.env = dict(hashlib=hashlib, json=json, Path=Path, time=time, quote=quote, urlencode=urlencode, CC=CC,
                        xbmc=SimpleNamespace(getCondVisibility=lambda _: self.enabled),
                        xbmcaddon=SimpleNamespace(Addon=lambda _: SimpleNamespace(getAddonInfo=lambda field: {'profile': str(self.progress), 'version': 'test-constant'}[field])),
                        xbmcvfs=SimpleNamespace(translatePath=lambda path: str(self.profile) if path == 'special://profile' else path),
                        _leased_directory=self.lease)
        exec(CODE, self.env)

    def restore_modules(self):
        for name, value in self.old.items():
            if value is None: sys.modules.pop(name, None)
            else: sys.modules[name] = value

    def lease(self, path, home, cancel):
        self.calls += 1; self.during()
        return self.native_status, self.answer

    def query(self):
        return self.env['_provider_result'](self.provider, 'synthetic query', self.home, self.cancel)

    def touch(self, path):
        st = path.stat(); os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns + 1000000))

    def test_stable_result_and_cache_hit_keep_original_request_count(self):
        self.assertEqual(self.query()[1:3], ('completed', self.answer))
        self.assertEqual(self.query()[1:3], ('completed', self.answer))
        self.assertEqual(self.calls, 1)

    def test_identical_settings_content_new_timestamp_rejects_fresh_result(self):
        before = self.settings.read_bytes(); self.during = lambda: self.touch(self.settings)
        self.assertEqual(self.query()[1:3], ('state_changed', {}))
        self.assertEqual(self.settings.read_bytes(), before)
        self.assertFalse(any(k.startswith('Infinity.Search.Cache.') for k in self.props))

    def test_changed_settings_remains_rejected(self):
        self.during = lambda: self.settings.write_text('<settings><setting id="synthetic">changed</setting></settings>')
        self.assertEqual(self.query()[1], 'state_changed')

    def test_all_global_revision_properties_reject_without_route_or_result_change(self):
        for key in ('Infinity.ContinueWatchingRevision', 'Infinity.ProviderInventory.Revision',
                    'Infinity.ResumeHub.PresentationSnapshot', 'widgetreload', 'widgetreload2',
                    'widgetreload-movies', 'widgetreload-tvshows'):
            with self.subTest(property=key):
                self.props.clear(); self.during = lambda key=key: self.props.__setitem__(key, 'synthetic-new-revision')
                self.assertEqual(self.query()[1:3], ('state_changed', {}))

    def test_unrelated_progress_file_timestamp_also_rejects(self):
        self.during = lambda: self.touch(self.progress / 'continue-watching.json')
        self.assertEqual(self.query()[1], 'state_changed')

    def test_dependency_settings_timestamp_rejects_even_with_unchanged_source(self):
        identity = 'script.module.synthetic'; dep = Path(self.tmp.name) / 'dependency'; dep.mkdir()
        (dep / 'addon.xml').write_text('<addon/>'); self.deps[identity] = (dep, '1')
        self.provider['contract']['dependencies'] = [dict(id=identity, root=str(dep), version='1', pins={'addon.xml': hashlib.sha256(b'<addon/>').hexdigest()})]
        settings = self.profile / 'addon_data' / identity / 'settings.xml'; settings.parent.mkdir(parents=True); settings.write_text('<settings/>')
        self.during = lambda: self.touch(settings)
        self.assertEqual(self.query()[1], 'state_changed')

    def test_actual_source_pin_change_is_unavailable_not_state_changed(self):
        self.during = lambda: (self.root / 'main.py').write_text('# changed fixture\n')
        self.assertEqual(self.query()[1], 'unavailable')

    def test_disabled_provider_is_unavailable_not_state_changed(self):
        self.during = lambda: setattr(self, 'enabled', False)
        self.assertEqual(self.query()[1], 'unavailable')

    def test_profile_change_remains_rejected(self):
        other = Path(self.tmp.name) / 'other'; other.mkdir()
        self.during = lambda: setattr(self, 'profile', other)
        self.assertEqual(self.query()[1], 'state_changed')

    def test_user_cancellation_takes_priority_over_revision_rejection(self):
        def interrupt():
            self.props['widgetreload'] = 'changed'; self.canceled = True
        self.during = interrupt
        self.assertEqual(self.query()[1], 'cancelled')

    def test_native_failure_status_preserved_when_fingerprint_stable(self):
        self.answer = {'error': {'message': 'synthetic native refusal'}}
        for status in ('busy', 'timeout', 'cancelled'):
            with self.subTest(status=status):
                self.native_status = status
                self.assertEqual(self.query()[1], status)
        self.assertFalse(self.props)

    def test_revision_change_can_mask_native_failure_with_state_changed(self):
        self.native_status = 'timeout'; self.answer = {'error': {'message': 'synthetic timeout'}}
        self.during = lambda: self.props.__setitem__('widgetreload', 'changed')
        self.assertEqual(self.query()[1:3], ('state_changed', {}))

    def test_completed_empty_result_is_distinct_from_state_rejection(self):
        self.answer = {'result': {'files': []}}
        self.assertEqual(self.query()[1:3], ('completed', self.answer))

    def test_cached_answer_rechecks_actual_source_before_accepting(self):
        self.assertEqual(self.query()[1], 'completed')
        (self.root / 'main.py').write_text('# changed fixture\n')
        self.assertEqual(self.query()[1], 'unavailable'); self.assertEqual(self.calls, 1)

    def test_shipped_tv_routes_do_not_add_provider_replacement_or_genre_filter(self):
        cases = {'nixtoons-query-search-v1': ('searchType', 'series'),
                 'action-list-v1': ('action', 'tvSearchterm'),
                 'json-args-list-v1': ('action', 'showsSearch')}
        for family, (key, value) in cases.items():
            spec = next(s for s in NAV['contracts'] if s['family'] == family)
            self.provider['contract'].update(spec['search']['tv'])
            route = self.env['route'](self.provider, 'synthetic query')
            self.assertEqual(parse_qs(urlsplit(route).query)[key], [value])
        spec = next(s for s in NAV['contracts'] if s['family'] == 'otaku-path-search-v1')
        self.provider['contract'].update(spec['search']['tv'])
        self.assertTrue(self.env['route'](self.provider, 'synthetic query').endswith('/search_tv_show/synthetic%20query'))


if __name__ == '__main__':
    print('Source APK SHA256:', APK_SHA)
    print('Shipped Search SHA256:', hashlib.sha256(RAW).hexdigest())
    unittest.main(verbosity=2)
