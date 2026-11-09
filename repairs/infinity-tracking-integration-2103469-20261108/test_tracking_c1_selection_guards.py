"""New C1 test-tool controls only; optimized host doubles are not Android proof."""
import ast
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from urllib.parse import parse_qs, urlsplit

HERE = Path(__file__).resolve().parent


def functions(path, names, namespace):
    tree = ast.parse(path.read_text(), filename=str(path))
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    if {node.name for node in nodes} != set(names):
        raise RuntimeError('Exact selected source functions required')
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec', optimize=1), namespace)


class Selection(unittest.TestCase):
    def setUp(self):
        self.ns = {}
        functions(HERE / 'verify_tracking_android.py', ('selected_playback_seconds', 'playback_domain', 'mode_ready', 'selected_overall_status'), self.ns)

    def test_existing_eligibility_target_without_repeating_five_minutes(self):
        target = self.ns['selected_playback_seconds']
        self.assertEqual(target('tv', 1424.423), 45)
        self.assertGreaterEqual(target('tv', 1424.423), max(30, .01 * 1424.423))
        self.assertEqual(target('movie', 5204.752), 90)
        self.assertEqual(target('tv', 10000), 105)

    def test_domain_ignores_bookkeeping_but_detects_playback_mutation(self):
        domain = self.ns['playback_domain']
        before = {'data': {'revision': 1, 'items': {'observed-key': {'identity': {'kind': 'movie'}, 'position': 94.4}}, 'watched': {}}}
        after = copy.deepcopy(before)
        after['data']['revision'] = 2
        after['data']['items']['observed-key']['updated'] = 123
        self.assertEqual(domain(before), domain(after))
        after['data']['items']['observed-key']['position'] += 1
        self.assertNotEqual(domain(before), domain(after))
        after = copy.deepcopy(before)
        after['data']['items']['observed-key']['identity'] = {'kind': 'episode'}
        self.assertNotEqual(domain(before), domain(after))

    def test_mode_needs_actual_publication_and_correct_pane(self):
        ready = self.ns['mode_ready']
        props = {'Infinity.ViewMode.Requested': 'twopane', 'Infinity.ViewMode.Effective': 'twopane',
                 'Infinity.EffectiveViewMode': 'twopane', 'Infinity.EffectivePaneMode': 'two-pane'}
        self.assertTrue(ready({'properties': props}, 'twopane'))
        self.assertFalse(ready({'properties': dict(props, **{'Infinity.EffectivePaneMode': 'single-pane'})}, 'twopane'))
        self.assertFalse(ready({'properties': props}, 'normal'))
        self.assertFalse(ready({'properties': {}}, 'normal'))
        props.update({'Infinity.ViewMode.Requested': 'auto'})
        self.assertTrue(ready({'properties': props}, 'auto'))

    def test_other_saved_origin_clock_does_not_assume_resume(self):
        ns = {}
        functions(HERE / 'verify_tracking_android.py', ('saved_entry_clock_ready',), ns)
        ready = ns['saved_entry_clock_ready']
        initial = dict(file='observed-stream', total=5204.752, time=0)
        self.assertFalse(ready(dict(playing=True, file='observed-stream', time=12), initial))
        self.assertFalse(ready(dict(playing=True, file='observed-stream', time=35), initial))
        self.assertTrue(ready(dict(playing=True, file='observed-stream', time=58), initial))
        resumed = dict(initial, time=94)
        self.assertFalse(ready(dict(playing=True, file='observed-stream', time=100), resumed))
        self.assertTrue(ready(dict(playing=True, file='observed-stream', time=106), resumed))
        self.assertFalse(ready(dict(playing=False), resumed))
        self.assertFalse(ready(dict(playing=True, file='changed-stream', time=106), resumed))

    def test_view_data_readiness_waits_empty_without_excusing_populated_wrong_rows(self):
        ns = dict(parse_qs=parse_qs, urlsplit=urlsplit)
        functions(HERE / 'verify_tracking_android.py', ('view_data_ready',), ns)
        ready = ns['view_data_ready']
        mapping = [dict(container_id=28103, route='plugin://script.infinity.commandcenter/?action=library&media=tv&bucket=next')]
        state = dict(data={}, next_episodes=[dict(media='tv', key='existing-observed-key')], progress_shows=[])
        self.assertFalse(ready(dict(rows={'28103': []}), 'tv', state, mapping))
        self.assertFalse(ready(dict(rows={'28103': [dict(label='Loading', key='', file='')]}), 'tv', state, mapping))
        # Readiness must not conceal wrong data; the subsequent equality guard rejects it.
        self.assertTrue(ready(dict(rows={'28103': [dict(key='wrong-key', file='actual-route')]}), 'tv', state, mapping))
        self.assertTrue(ready(dict(rows={'28103': [dict(key='existing-observed-key', file='actual-route')]}), 'tv', state, mapping))
        self.assertTrue(ready(dict(rows={}), 'tv', state, mapping))
        self.assertTrue(ready(dict(rows={'28103': []}), 'tv', dict(state, next_episodes=[]), mapping))

    def test_empty_projection_cannot_hide_unexpected_or_duplicate_cards(self):
        class ObservedFailure(RuntimeError): pass
        ns = dict(FunctionalFailure=ObservedFailure)
        functions(HERE / 'verify_tracking_android.py', ('functional', 'assert_view_keys'), ns)
        compare = ns['assert_view_keys']
        compare([], set())
        compare(['existing-key'], {'existing-key'})
        for actual, expected in ((['stale-card'], set()), (['existing-key', 'existing-key'], {'existing-key'}), ([], {'missing-key'})):
            with self.assertRaisesRegex(ObservedFailure, 'VISIBLE_MODE_DATA_KEYS_MUST_MATCH'):
                compare(actual, expected)

    def test_unexecuted_or_visual_pending_is_not_aggregate_pass(self):
        overall = self.ns['selected_overall_status']
        self.assertEqual(overall(['PASS', 'PASS'], ['PASS']), 'PASS_SELECTED_INFINITY_ORIGIN_TV_MOVIE')
        for status in ('NOT_RUN', 'NOT_RUN_BUDGET', 'BLOCKED_THEME_OWNER_UNAVAILABLE', 'CAPTURED_VISUAL_PENDING'):
            self.assertEqual(overall(['PASS', 'PASS'], [status]), 'PARTIAL_SELECTED_INFINITY_TRACKING_CORE_PASS')
        self.assertEqual(overall(['PASS', 'NOT_RUN'], ['PASS']), 'BLOCKED_INFINITY_ORIGIN_ACCEPTANCE')
        self.assertEqual(overall(['PASS', 'PASS'], ['FAIL']), 'FAIL_SELECTED_INFINITY_TRACKING_ASSERTION')


class PublicUI(unittest.TestCase):
    def setUp(self):
        self.window, self.dialog, self.heading = 10025, 10103, 'Add to custom list'
        self.rpc, self.commands = [], []
        def execute(raw):
            self.rpc.append(json.loads(raw))
            return '{"jsonrpc":"2.0","id":1,"result":"OK"}'
        self.ns = dict(json=json, controller=lambda: object(),
            xbmc=SimpleNamespace(getInfoLabel=lambda expression: self.heading if expression == 'Control.GetLabel(311)' else '',
                executeJSONRPC=execute, executebuiltin=lambda command: self.commands.append(command)),
            xbmcgui=SimpleNamespace(getCurrentWindowId=lambda: self.window, getCurrentWindowDialogId=lambda: self.dialog))
        functions(HERE / 'tracking_android_observer.py', ('require', 'action'), self.ns)

    def test_exact_original_custom_list_keyboard_fixed_name_only(self):
        self.ns['action']({'action': 'fill-custom-list-name', 'text': 'ignored-untrusted-input'})
        self.assertEqual(self.rpc[0]['method'], 'Input.SendText')
        self.assertEqual(self.rpc[0]['params'], {'text': 'Tracking QA', 'done': True})
        for dialog, heading in ((10103, 'Enter password'), (12000, 'Add to custom list')):
            self.dialog, self.heading = dialog, heading
            with self.assertRaisesRegex(RuntimeError, 'EXACT_EXISTING_CUSTOM_LIST_KEYBOARD_REQUIRED'):
                self.ns['action']({'action': 'fill-custom-list-name'})
        self.assertEqual(len(self.rpc), 1)

    def test_public_mode_only_unobscured_home_and_known_mode(self):
        self.window, self.dialog = 10000, 9999
        reply = self.ns['action']({'action': 'public-view-mode', 'mode': 'auto'})
        self.assertFalse(reply['selection_verified'])
        self.assertEqual(self.commands, ['RunScript(script.infinity.commandcenter,view-mode,auto)'])
        with self.assertRaisesRegex(RuntimeError, 'EXISTING_PUBLIC_MODE_REQUIRED'):
            self.ns['action']({'action': 'public-view-mode', 'mode': 'invented'})
        self.dialog = 10103
        with self.assertRaisesRegex(RuntimeError, 'UNOBSCURED_HOME_REQUIRED'):
            self.ns['action']({'action': 'public-theme'})
        self.assertEqual(len(self.commands), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
