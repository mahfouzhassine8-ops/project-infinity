"""Selected immutable publisher functions in synthetic host fixtures only.

No provider import/initialization, real network, Kodi profile or device operation.
The prior 15 tests are reused, not inherited or rerun by this suite.
"""
import ast
import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import sqlite3
from types import SimpleNamespace
import unittest
from urllib.parse import quote_plus
import urllib.parse
import xml.etree.ElementTree as ET

import test_shipped_state as shipped

ROOT = Path(os.environ.get('SEARCH_REFERENCE_ROOT', '/tmp/infinity-search-provider-references'))
PINS = {
    'plugin.video.watchnixtoons2/lib/plugin.py': 'd8d395634eff8ada8c9d09138744997573035b7819fcac91985ff870bbfc2283',
    'plugin.video.watchnixtoons2/lib/network.py': '6cd59019db4fddeb86d83596cc163bd56176f181efcd3f21cf4313554b564d66',
    'script.module.thecrew/lib/resources/lib/modules/crewruntime.py': 'e45ba1dd3ef55f4287915613031bc3ebeb56ccb39a4dd38991a3ca782c08aed9',
    'script.module.thecrew/lib/resources/lib/indexers/tvshows.py': '0b41bb739b609ad068ea3b48f403ef422d40eb5fc61b66b0e30344f29892f00e',
}


def extracted(name, function, env, cls=None):
    raw = (ROOT / name).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PINS[name], 'REFERENCE_SOURCE_CHANGED'
    tree = ast.parse(raw)
    scope = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == cls).body if cls else tree.body
    node = next(n for n in scope if isinstance(n, ast.FunctionDef) and n.name == function)
    exec(compile(ast.Module(body=[node], type_ignores=[]), name, 'exec'), env)
    return env[function]


class SideEffectDiagnosis(unittest.TestCase):
    def setUp(self):
        self.b = shipped.StateDiagnosis()
        self.b.setUp()
        self.addCleanup(self.b.doCleanups)
        self.values = {}
        self.writes = []
        self.addon = SimpleNamespace(getSetting=lambda key: self.values.get(key, ''), setSetting=self.save)

    def save(self, key, value):
        self.values[key] = value; self.writes.append(key)
        root = ET.Element('settings')
        for key, val in self.values.items():
            ET.SubElement(root, 'setting', id=key).text = str(val)
        self.b.settings.write_bytes(ET.tostring(root))
        self.b.touch(self.b.settings)

    def nixtoons(self):
        b = self.b
        spec = next(s for s in shipped.NAV['contracts'] if s['family'] == 'nixtoons-query-search-v1')
        root = ROOT / 'plugin.video.watchnixtoons2'
        for name, pin in spec['exact_sources'].items():
            self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), pin)
        pins = dict(spec['exact_sources'], **{'addon.xml': '9dc68f15ce6d7e80ff31443eff8fcf43afe80d8fcdd88a5e8fc592f9fa31318c'})
        b.provider = dict(id='plugin.video.watchnixtoons2', root=str(root), contract=dict(copy.deepcopy(spec['search']['tv']), pins=pins))
        b.settings = b.profile / 'addon_data/plugin.video.watchnixtoons2/settings.xml'
        b.settings.parent.mkdir(parents=True); b.settings.write_text('<settings/>')
        catalog_calls = []
        fn = extracted('plugin.video.watchnixtoons2/lib/plugin.py', 'actionSearchMenu',
                       dict(ADDON=self.addon, actionCatalogSection=lambda p: catalog_calls.append(dict(p))))
        return fn, catalog_calls

    def test_nixtoons_fresh_explicit_query_writes_history_then_rejects_own_result(self):
        fn, calls = self.nixtoons()
        self.b.during = lambda: fn(dict(searchType='series', query='synthetic query', path='/search'))
        self.assertEqual(self.b.query()[1:3], ('state_changed', {}))
        self.assertEqual(self.writes, ['searchHistory'])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]['section'], 'ALL')
        self.assertEqual(calls[0]['query'], 'synthetic query')
        self.assertEqual(self.b.calls, 1)

    def test_nixtoons_retry_same_query_writes_again_instead_of_stabilizing(self):
        fn, calls = self.nixtoons()
        self.b.during = lambda: fn(dict(searchType='series', query='synthetic query', path='/search'))
        self.assertEqual(self.b.query()[1], 'state_changed')
        self.assertEqual(self.b.query()[1], 'state_changed')
        self.assertEqual(self.writes, ['searchHistory', 'searchHistory'])
        self.assertEqual(len(calls), 2)
        self.assertEqual(self.b.calls, 2)
        self.assertFalse(any(k.startswith('Infinity.Search.Cache.') for k in self.b.props))

    def test_nixtoons_request_timing_write_independently_invalidates(self):
        self.nixtoons()
        calls = []
        response = SimpleNamespace(status_code=200, cookies=None)
        def request(*args, **kwargs):
            calls.append(1); return response
        fn = extracted('plugin.video.watchnixtoons2/lib/network.py', 'request_helper',
                       dict(ADDON=self.addon, json=json, urllib_parse=urllib.parse,
                            time=lambda: 100.0, sleep=lambda _: self.fail('unexpected sleep'),
                            rqs=SimpleNamespace(get=request, post=request), WNT2_USER_AGENT='synthetic',
                            getRawWindowProperty=lambda _: '', PROPERTY_SESSION_COOKIE='fixture',
                            setRawWindowProperty=lambda *args: self.fail('unexpected cookie'), tls_adapters=[]))
        self.b.during = lambda: fn('https://example.invalid/search')
        self.assertEqual(self.b.query()[1], 'state_changed')
        self.assertEqual(self.writes, ['requestTimes']); self.assertEqual(calls, [1])

    def crew_orion(self, installed, failed=False):
        def user():
            if failed: raise RuntimeError('synthetic lookup failure')
            return {'username': 'synthetic', 'subscription': {'package': {'name': 'fixture'}, 'time': {'expiration': 2000000000}}}
        state = SimpleNamespace(is_orion_installed=lambda: installed,
                                Orion=lambda _: SimpleNamespace(user=user),
                                set_setting=self.save, log=lambda *args: None)
        fn = extracted('script.module.thecrew/lib/resources/lib/modules/crewruntime.py', 'check_orion',
                       dict(keys=SimpleNamespace(orion_key='synthetic'), datetime=datetime), cls='CrewRuntime')
        self.b.during = lambda: fn(state)

    def test_crew_orion_absent_does_not_write_settings(self):
        self.crew_orion(False)
        self.assertEqual(self.b.query()[1], 'completed')
        self.assertEqual(self.writes, [])

    def test_crew_orion_present_metadata_writes_invalidate_result(self):
        self.crew_orion(True)
        self.assertEqual(self.b.query()[1], 'state_changed')
        self.assertEqual(self.writes, ['orion.installed', 'orion.boolinstalled', 'orion.username', 'orion.package', 'orion.expiration'])

    def test_crew_orion_failure_status_writes_can_also_invalidate(self):
        self.crew_orion(True, failed=True)
        self.assertEqual(self.b.query()[1], 'state_changed')
        self.assertEqual(self.writes, ['orion.installed', 'orion.boolinstalled'])

    def test_crew_history_database_write_alone_does_not_change_fingerprint(self):
        db = Path(self.b.tmp.name) / 'synthetic-history.db'
        with sqlite3.connect(db) as conn:
            conn.execute('CREATE TABLE tvshow (ID INTEGER, term TEXT)')
        calls = []
        def connect():
            conn = sqlite3.connect(db); return conn, conn.cursor()
        state = SimpleNamespace(create_db_connection=connect, close_db_connection=lambda conn, cursor: conn.close(),
                                search_link='https://example.invalid/search?q=%s', get=lambda _: calls.append(1))
        fn = extracted('script.module.thecrew/lib/resources/lib/indexers/tvshows.py', 'search_term',
                       dict(utils=SimpleNamespace(title_key=lambda q: q), quote_plus=quote_plus,
                            c=SimpleNamespace(log=lambda *args: None)), cls='TVShows')
        self.b.during = lambda: fn(state, 'synthetic query')
        self.assertEqual(self.b.query()[1], 'completed')
        with sqlite3.connect(db) as conn:
            self.assertEqual(conn.execute('SELECT count(*) FROM tvshow').fetchone()[0], 1)
        self.assertEqual(calls, [1]); self.assertEqual(self.writes, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
