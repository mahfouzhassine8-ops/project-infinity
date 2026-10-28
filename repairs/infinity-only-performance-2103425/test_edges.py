"""Selected negative/race controls; never launches an app, provider or writer."""
import copy
import hashlib
import json
from pathlib import Path
import re
import tempfile
import threading
import time
import types
import unittest
import yaml

from verify import definitions, Home, load_hub, fixture

HERE = Path(__file__).resolve().parent
ROOT = HERE / 'overlay/script.infinity.commandcenter'


class QueryRaces(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='infinity-query-race-')
        self.addCleanup(self.temp.cleanup)
        self.profile = Path(self.temp.name)
        self.home = Home()
        profile = self.profile
        class Addon:
            def __init__(self, aid): self.aid = aid
            def getAddonInfo(self, key):
                return str(profile / 'addon_data' / self.aid) if key == 'profile' else '1'
        self.ns = dict(hashlib=hashlib, json=json, time=time, Path=Path, CC='script.infinity.commandcenter',
                       xbmcaddon=types.SimpleNamespace(Addon=Addon),
                       xbmcvfs=types.SimpleNamespace(translatePath=lambda v: str(profile) if v == 'special://profile' else v),
                       _VisibleCancellation=lambda c, p: c)
        names = ['_provider_result', '_query_cache_entries', '_remember_query_answer', '_query_signature', '_query_file_stamp']
        definitions(ROOT / 'infinity_search.py', names, self.ns)
        self.provider = dict(id='plugin.video.example', root=str(profile / 'provider'), contract={'pins': {}})
        self.route_calls = 0
        def route(*args):
            self.route_calls += 1
            return 'plugin://plugin.video.example/?query=exact'
        self.ns['route'] = route
        self.ns['_leased_directory'] = lambda *a: ('completed', {'result': {'files': []}})
        self.cancel = False
        self.cancellation = types.SimpleNamespace(iscanceled=lambda: self.cancel)

    def result(self):
        return self.ns['_provider_result'](self.provider, 'exact', self.home, self.cancellation)

    def test_cache_hit_still_verifies_before_and_after(self):
        self.result()
        self.assertEqual(self.route_calls, 2)
        self.ns['_leased_directory'] = lambda *a: self.fail('Valid hit should avoid native request')
        self.assertEqual(self.result()[1], 'completed')
        self.assertEqual(self.route_calls, 4)

    def test_cached_hit_race_is_not_published(self):
        self.result()
        old_route = self.ns['route']
        def route(*args):
            value = old_route(*args)
            if self.route_calls == 4:
                self.home.setProperty('Infinity.ProviderInventory.Revision', 'newer')
            return value
        self.ns['route'] = route
        self.assertEqual(self.result()[1:3], ('state_changed', {}))

    def test_cancelled_worker_does_not_cache(self):
        def native(*args):
            self.cancel = True
            return 'completed', {'result': {'files': []}}
        self.ns['_leased_directory'] = native
        self.assertEqual(self.result()[1], 'cancelled')
        self.assertEqual(self.home.values, {})

    def test_failed_and_busy_work_does_not_cache(self):
        for status in ('busy', 'cancelled', 'provider_failed'):
            with self.subTest(status=status):
                self.ns['_leased_directory'] = lambda *a: (status, {'error': {}})
                self.assertEqual(self.result()[1], status)
                self.assertEqual(self.home.values, {})

    def test_disabled_or_changed_source_after_worker_does_not_cache(self):
        original = self.ns['route']
        def route(*args):
            if self.route_calls:
                raise RuntimeError('Source changed')
            return original(*args)
        self.ns['route'] = route
        self.assertEqual(self.result()[1], 'unavailable')
        self.assertEqual(self.home.values, {})

    def test_unknown_or_linked_state_disables_reuse(self):
        path = self.profile / 'provider/addon.xml'
        path.parent.mkdir()
        path.symlink_to(self.profile / 'missing')
        self.assertEqual(self.result()[1], 'completed')
        self.assertEqual(self.home.values, {})

    def test_same_sized_atomic_settings_replacement_invalidates(self):
        path = self.profile / 'addon_data/plugin.video.example/settings.xml'
        path.parent.mkdir(parents=True)
        path.write_text('first')
        self.result()
        old = dict(self.home.values)
        temp = path.with_name('replacement')
        temp.write_text('other')
        temp.replace(path)
        self.result()
        self.assertNotEqual(self.home.values, old)

    def test_profile_and_presentation_revision_invalidate(self):
        self.result()
        original = dict(self.home.values)
        self.home.setProperty('Infinity.ResumeHub.PresentationSnapshot', 'new watched badges')
        self.result()
        self.assertNotEqual(self.home.getProperty('Infinity.Search.Cache.plugin.video.example'),
                            original['Infinity.Search.Cache.plugin.video.example'])
        self.ns['xbmcvfs'].translatePath = lambda v: str(self.profile / 'other-profile') if v == 'special://profile' else v
        self.assertEqual(self.result()[1], 'completed')
        cache = json.loads(self.home.getProperty('Infinity.Search.Cache.plugin.video.example'))
        self.assertEqual(len(cache['entries']), 3)


class InventoryRaces(unittest.TestCase):
    def setUp(self):
        home = Home()
        self.ns = dict(threading=threading, time=time, re=re, deepcopy=copy.deepcopy,
                       _cached=None, _checked_at=-1, _verified={}, _generation=0,
                       _monitor=object(), _event_revision='', _scan_lock=threading.Lock(),
                       _lock=threading.RLock(), INVENTORY_TTL=2, API_VERSION=1,
                       xbmcgui=types.SimpleNamespace(Window=lambda _: home), InventoryMonitor=lambda: object())
        self.rows = [dict(addonid='plugin.video.umbrella'), dict(addonid='plugin.video.seren')]
        self.ns['_rpc'] = lambda *a: {'addons': self.rows}
        self.ns['_contracts'] = lambda: ([], 'digest')
        self.ns['_scan'] = lambda rows, *args: (rows, {})
        definitions(ROOT / 'provider_inventory.py', ('snapshot',), self.ns)

    def test_selected_snapshot_preserves_full_cached_inventory(self):
        original = self.ns['snapshot'](force=True)
        selected = self.ns['snapshot'](force=True, provider_id='plugin.video.seren')
        self.assertEqual(len(selected['entries']), 1)
        self.assertEqual(self.ns['_cached'], original)
        self.assertEqual(len(self.ns['snapshot']()['entries']), 2)

    def test_absent_selected_provider_does_not_substitute_another(self):
        self.assertEqual(self.ns['snapshot'](force=True, provider_id='plugin.video.absent')['entries'], [])

    def test_invalid_provider_id_is_rejected(self):
        for value in ('all', '../example', 'plugin.video.a) | true', False, ''):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.ns['snapshot'](provider_id=value)

    def test_repeated_inventory_change_rejects_stale_scan(self):
        def scan(rows, *args):
            self.ns['_generation'] += 1
            return rows, {}
        self.ns['_scan'] = scan
        with self.assertRaisesRegex(RuntimeError, 'Providers changed'):
            self.ns['snapshot'](force=True, provider_id='plugin.video.seren')
        self.assertIsNone(self.ns['_cached'])


class ScopeControls(unittest.TestCase):
    def test_projection_bounds_and_private_full_results(self):
        hub = load_hub(ROOT)
        data = fixture(hub, 30)
        original = copy.deepcopy(data)
        for limit in (-1, 101, True, 1.5, '20'):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                hub.entries(data, limit=limit)
        values = hub.entries(data)
        values[0]['metadata']['cast'][0]['role'] = 'changed'
        self.assertEqual(data, original)

    def test_only_selected_host_job_can_run_for_host_choice(self):
        repository = HERE.parents[1]
        workflow = yaml.load((repository / '.github/workflows/infinity-saved-navigation-android.yml').read_text(), Loader=yaml.BaseLoader)
        host = workflow['jobs']['performance-host']
        self.assertIn("github.event_name == 'workflow_dispatch'", host['if'])
        self.assertIn("inputs.feature == 'infinity-performance-host'", host['if'])
        self.assertEqual(workflow['jobs']['android17']['if'], "inputs.feature != 'infinity-performance-host' && inputs.feature != 'infinity-performance-android'")
        self.assertNotIn('needs', host)
        commands = '\n'.join(step.get('run', '') for step in host['steps'])
        for forbidden in ('adb ', 'emulator', 'INFINITY_KEYSTORE_B64', 'assemble.py sign', 'pytest', 'unittest discover'):
            self.assertNotIn(forbidden, commands)
        self.assertNotIn('continue-on-error', json.dumps(host))


if __name__ == '__main__':
    unittest.main(verbosity=2)
