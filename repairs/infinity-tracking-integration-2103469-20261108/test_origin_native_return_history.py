"""Only new bounded Back/history host guards; no actual app/record simulation."""
from pathlib import Path
import time
from types import SimpleNamespace
import unittest
from urllib.parse import urlsplit, parse_qs

from test_tracking_dialog_select_optimized import functions

HERE = Path(__file__).resolve().parent
CC = 'script.infinity.commandcenter'
ROOT = 'plugin://' + CC + '/?action=tv'
WATCHLIST = 'plugin://' + CC + '/?action=library&media=tv&bucket=watchlist'
PROGRESS = 'plugin://' + CC + '/?action=library&media=tv&bucket=progress'
PARENT = 'plugin://plugin.video.watchnixtoons2/?action=actionEpisodesMenu&url=%2Fanime%2Fqueen-s-blade%3Fseason%3Dall%26lang%3Ddub'


def require(value, label):
    if not value: raise RuntimeError(label)


class NativeHistory(unittest.TestCase):
    def call(self, restored, known, modal=9999):
        route_index, mode, calls, trace = [0], ['home'], [], []
        def snapshot():
            if mode[0] == 'home':
                return dict(window=10000, dialog=9999, controls={'9000': [dict(index=9, label='INFINITY TV', section='trakttv', hubsource='infinity')]})
            route = PROGRESS if mode[0] == 'section' else restored[route_index[0]]
            row = dict(index=0, label='Progress Shows', file=PROGRESS, key='')
            return dict(window=10025, dialog=modal, folder=route, focused_control='65051',
                        primary_controls=[50, 65051], visible_controls={'50': False, '65051': True}, controls={'65051': [row]})
        def observe(action, **request):
            if action == 'snapshot': return snapshot()
            if action == 'home-select':
                mode[0] = 'restored'
                return dict(label=request['label'], section=request['section'], hubsource=request['hubsource'])
            if action == 'click':
                self.assertEqual(request['file'], PROGRESS)
                mode[0] = 'section'
                return dict(live_native_file=PROGRESS)
            raise RuntimeError('Unselected host action')
        def rpc(method, params=None):
            calls.append(method)
            if method == 'Input.Home': mode[0] = 'home'
            elif method == 'Input.Back': route_index[0] = min(route_index[0] + 1, len(restored) - 1)
            else: raise RuntimeError('Raw route activation is not allowed')
        def wait(device, function, label, seconds):
            for _ in range(10):
                value = function()
                if value: return value
            raise TimeoutError(label)
        namespace = dict(base=SimpleNamespace(CC=CC, require=require), time=time, urlsplit=urlsplit, parse_qs=parse_qs, until=wait)
        functions(HERE / 'verify_tracking_android.py', ('row_request', 'route_matches', 'breadcrumb', 'content_rows', 'infinity_section'), namespace)
        try:
            result = namespace['infinity_section'](SimpleNamespace(rpc=rpc), SimpleNamespace(call=observe), 'tv', 'progress', trace, known_history=known)
            return result, calls, trace
        except Exception as error:
            return error, calls, trace

    def test_known_saved_child_and_section_follow_native_history_to_root(self):
        result, calls, trace = self.call([PARENT, WATCHLIST, ROOT], [PARENT, WATCHLIST])
        self.assertEqual(result['folder'], PROGRESS)
        self.assertEqual(calls, ['Input.Home', 'Input.Back', 'Input.Back'])
        back = trace[0]['native_history_back']
        self.assertEqual([(item['observed_from'], item['observed_to']) for item in back], [(PARENT, WATCHLIST), (WATCHLIST, ROOT)])
        self.assertEqual([item['step'] for item in trace], ['home', 'root', 'section'])

    def test_unknown_route_and_modal_never_receive_back(self):
        for restored, modal in ((['plugin://unrelated/'], 9999), ([PARENT], 13000)):
            with self.subTest(restored=restored, modal=modal):
                result, calls, trace = self.call(restored, [PARENT], modal)
                self.assertIsInstance(result, TimeoutError)
                self.assertEqual(calls, ['Input.Home'])
                self.assertEqual(trace[0]['native_history_back'], [])

    def test_cycle_is_not_retried_and_back_is_bounded(self):
        result, calls, _ = self.call([PARENT], [PARENT])
        self.assertIsInstance(result, TimeoutError)
        self.assertEqual(calls.count('Input.Back'), 1)
        paths = [PARENT, WATCHLIST, PROGRESS, 'known-fourth-section']
        result, calls, _ = self.call(paths, paths)
        self.assertIsInstance(result, TimeoutError)
        self.assertEqual(calls.count('Input.Back'), 3)


if __name__ == '__main__':
    unittest.main(verbosity=2)
