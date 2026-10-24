"""Exact copied-selection host contract; native gestures need separate evidence."""
from copy import deepcopy
import json
import sys
import types
import unittest
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

from test_quick_actions import QuickActions, CC, HERE, Item, load


class Selection(QuickActions):
    def test_each_real_saved_projection_emits_one_versioned_contract(self):
        entry = self.movie()
        for bucket in ('continue', 'history', 'watched', 'watchlist', 'later', 'collection', 'ratings', 'progress'):
            _, item = self.plugin._list_item(entry, self.data, bucket)
            value = self.selection.read(item)
            self.assertEqual(value['bucket'], bucket)
            self.assertEqual(value['key'], entry['key'])
            self.assertEqual(value['identity'], entry['identity'])
            self.assertEqual(value['source'], entry['source'])
            self.assertEqual(value['owner'], 'script.infinity.commandcenter')
            command = self.plugin._context(entry, self.data, bucket)[0][1]
            params = parse_qs(urlsplit(command[len('RunPlugin('):-1]).query)
            self.assertEqual(params['selection'], [value['token']])
        self.assertEqual(self.writers, 0)

    def test_custom_list_name_and_route_survive_exact_copy_and_url_encoding(self):
        entry = self.movie(); name = 'Weekend, "choice" & more / TV'
        self.data['lists'][name] = {entry['key']: entry}; self.write()
        _, item = self.plugin._list_item(entry, self.data, 'list', name)
        value = self.selection.read(item)
        self.assertEqual(value['list'], name)
        self.assertEqual(item.getProperty('Infinity.ResumeHub.List'), name)
        command = self.plugin._context(entry, self.data, 'list', name)[0][1]
        params = parse_qs(urlsplit(command[len('RunPlugin('):-1]).query)
        self.assertEqual(params['list'], [name])
        self.choice = 'Save for Later'
        self.assertTrue(self.plugin.show_item_menu(entry['key'], 'list', name, expected_selection=value['token']))
        self.assertEqual(self.saved()['later'][entry['key']]['source'], entry['source'])

    def test_stale_source_or_identity_cannot_operate_after_card_replacement(self):
        original = self.movie(); self.data['watchlist'][original['key']] = original; self.write()
        _, item = self.plugin._list_item(original, self.data, 'watchlist')
        selection = self.selection.read(item)['token']
        for replacement in (dict(original, source='new-original-route'),
                            dict(original, identity=self.hub.media_identity('movie', {'tmdb': '604'}))):
            self.data['watchlist'][original['key']] = replacement; self.write()
            before = self.path.read_bytes(); self.choice = 'Save for Later'
            self.assertFalse(self.plugin.show_item_menu(original['key'], 'watchlist', expected_selection=selection))
            self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.writers, 0)

    def test_native_copied_capsule_enters_same_popup_without_global_focus(self):
        entry = self.movie(); name = 'Exact custom list'
        self.data['lists'][name] = {entry['key']: entry}; self.write()
        _, item = self.plugin._list_item(entry, self.data, 'list', name)
        calls = []
        bridge = types.SimpleNamespace(_bridge=lambda: (_ for _ in ()).throw(AssertionError('provider bridge not needed')),
                                       selected=lambda *a: None, notice=lambda *a: None)
        with patch.dict(sys.modules, {'infinity_trakt': bridge}):
            context = load('selection_context', CC / 'context.py')
            context._popup_module = lambda: types.SimpleNamespace(show_item_menu=lambda *a, **kw: calls.append((a, kw)) or True)
            self.assertTrue(context.title_popup(item))
        self.assertEqual(calls, [((entry['key'], 'list', name),
                                {'expected_selection': self.selection.token(entry, 'list', name)})])
        self.assertEqual(self.calls, [])

    def test_malformed_capsule_fails_closed_without_legacy_fallback(self):
        entry = self.movie(); item = Item(); self.selection.publish(item, entry, 'watchlist')
        self.assertIsNone(self.selection.snapshot(entry, []))
        self.assertIsNone(self.selection.snapshot(dict(entry, key=int('1' * 64)), 'watchlist'))
        original = json.loads(item.getProperty('Infinity.Selection.Snapshot'))
        for changed in (dict(original, bucket=[]), dict(original, list=[]),
                        dict(original, key=int('1' * 64)), dict(original, identity=[]),
                        dict(original, token='0' * 64), dict(original, owner='other')):
            item.setProperty('Infinity.Selection.Snapshot', json.dumps(changed))
            self.assertIsNone(self.selection.read(item))
        item.setProperty('Infinity.Selection.Snapshot', 'not JSON')
        with patch.dict(sys.modules, {'infinity_trakt': types.SimpleNamespace(
                _bridge=lambda: (_ for _ in ()).throw(AssertionError('unsafe fallback')),
                selected=lambda *a: None, notice=lambda *a: None)}):
            context = load('malformed_selection_context', CC / 'context.py')
            self.assertFalse(context.title_popup(item))

    def test_synthetic_next_keeps_open_route_without_creating_title_actions(self):
        entry = self.movie(synthetic_next=True)
        _, item = self.plugin._list_item(entry, self.data, 'next')
        self.assertEqual(item.path, entry['source'])
        self.assertEqual(item.getProperty('Infinity.Selection.Unsupported'), 'synthetic-next')
        self.assertIsNone(self.selection.read(item))
        with patch.dict(sys.modules, {'infinity_trakt': types.SimpleNamespace(
                _bridge=lambda: (_ for _ in ()).throw(AssertionError('synthetic title cannot become authoritative')),
                selected=lambda *a: None, notice=lambda *a: None)}):
            context = load('synthetic_selection_context', CC / 'context.py')
            self.assertFalse(context.title_popup(item))
        self.assertEqual(self.calls, []); self.assertEqual(self.writers, 0)

    def test_cancel_keeps_origin_records_selection_and_refresh_untouched(self):
        entry = self.movie(); self.data['watchlist'][entry['key']] = entry; self.write()
        _, item = self.plugin._list_item(entry, self.data, 'watchlist')
        snapshot = deepcopy(item.properties); before = self.path.read_bytes()
        self.assertFalse(self.plugin.show_item_menu(entry['key'], 'watchlist', expected_selection=self.selection.read(item)['token']))
        self.assertEqual(item.properties, snapshot); self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.calls, []); self.assertEqual(self.writers, 0)


if __name__ == '__main__':
    # Run only this correction's selected cases; inherited prior tests are selected
    # explicitly in their own existing runner rather than silently duplicated.
    cases = [name for name in Selection.__dict__ if name.startswith('test_')]
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(Selection(name) for name in cases))
    (HERE / 'SELECTION-HOST.json').write_text(json.dumps(dict(
        host='PASS' if result.wasSuccessful() else 'FAIL', tests=result.testsRun,
        scope='Actual selection/property/action Python with mocked Kodi APIs',
        native_gestures='NOT RUN IN THIS TEST', android17='NOT RUN',
        physical_fold='NOT RUN', shutdown='NOT RUN'), indent=2) + '\n')
    sys.exit(not result.wasSuccessful())
