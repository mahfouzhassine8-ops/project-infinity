"""New selected optimize=1 content-view/Stop/focus host controls only.

Explicit SDK doubles test observer refusal/coherency. No Android/provider PASS,
native callbacks, production modules, accounts, network, build or signing.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import time
from types import SimpleNamespace
import unittest

from test_tracking_dialog_select_optimized import SDK, functions

HERE = Path(__file__).resolve().parent
URI = 'plugin://plugin.video.watchnixtoons2/?action=actionEpisodesMenu&url=%2Fanime%2Fqueen-s-blade%3Fseason%3Dall%26lang%3Ddub'


class ContentSDK(SDK):
    def __init__(self):
        super().__init__()
        self.dialog, self.focus = 9999, 65051
        self.rows, self.visible = {65051: ["Queen's Blade"]}, {65051: True}

    def label(self, name):
        if name == 'Container.FolderPath': return 'actual-directory'
        match = re.fullmatch(r'Container\((\d+)\)\.ListItem(?:Absolute\((\d+)\))?\.(FileNameAndPath|DBTYPE|Property\(Infinity.ResumeHub.Key\))', name)
        if match:
            control, index, field = int(match[1]), int(match[2] or self.indices.get(int(match[1]), 0)), match[3]
            if index >= len(self.rows.get(control, [])): return ''
            return {'FileNameAndPath': URI, 'DBTYPE': 'tvshow', 'Property(Infinity.ResumeHub.Key)': 'actual-key'}[field]
        return super().label(name)


class ContentStopFocus(unittest.TestCase):
    def setUp(self):
        self.sdk = ContentSDK()
        self.player = SimpleNamespace(isPlayingVideo=lambda: False)
        xbmc = SimpleNamespace(getInfoLabel=self.sdk.label, getCondVisibility=self.sdk.condition,
            getSkinDir=lambda: 'skin.infinity.diggz', executebuiltin=self.sdk.builtin,
            executeJSONRPC=self.sdk.rpc, Player=lambda: self.player)
        self.ns = dict(os=os, json=json, time=time, xbmc=xbmc,
            xbmcgui=SimpleNamespace(getCurrentWindowId=lambda: 10025, getCurrentWindowDialogId=lambda: self.sdk.dialog),
            xbmcaddon=SimpleNamespace(Addon=self.sdk.addon), CANCELLED_CHOICE=None,
            EVENTS=SimpleNamespace(sequence=0, events=[]), tag=lambda item: dict(native_copy=item))
        functions(HERE / 'tracking_android_observer.py', ('require', 'snapshot', 'selected', 'action'), self.ns)
        self.driver = dict(base=SimpleNamespace(require=self.ns['require']))
        functions(HERE / 'verify_tracking_android.py', ('content_rows', 'assert_native_projection'), self.driver)

    def test_visible_65051_rows_keys_selection_and_projection(self):
        snapshot = self.ns['snapshot']()
        rows = self.driver['content_rows'](snapshot)
        self.assertEqual(len(rows), 2)  # Native optional out-of-range sentinel remains blank.
        self.assertEqual(rows[0]['control'], 65051)
        self.assertEqual(rows[0]['file'], URI)
        self.driver['assert_native_projection'](snapshot, [dict(key='actual-key')], 'actual-key')
        result = self.ns['action'](dict(action='click', control=65051, index=0, file=URI, label="Queen's Blade"))
        self.assertEqual(result['live_native_file'], URI)
        self.assertEqual(self.sdk.focus_calls, ['SetFocus(65051,0,absolute)'])
        self.assertEqual(self.sdk.rpc_calls, ['Input.Select'])

    def test_ambiguous_visible_views_refuse_without_synthesizing_cards(self):
        self.sdk.rows[50], self.sdk.visible[50] = ["Queen's Blade"], True
        snapshot = self.ns['snapshot']()
        with self.assertRaisesRegex(RuntimeError, 'AMBIGUOUS'):
            self.driver['content_rows'](snapshot)
        with self.assertRaises(RuntimeError):
            self.ns['action'](dict(action='click', control=65051, index=0, file=URI, label="Queen's Blade"))
        self.assertEqual(self.sdk.rpc_calls, [])

    def test_hidden_or_stale_content_read_refuses(self):
        for setup in ('hidden', 'stale_label', 'stale_file'):
            with self.subTest(setup=setup):
                self.setUp()
                request = dict(action='click', control=65051, index=0, file=URI, label="Queen's Blade")
                if setup == 'hidden': self.sdk.visible[65051] = False
                if setup == 'stale_label': request['label'] = 'Different show'
                if setup == 'stale_file': request['file'] = URI + '&stale=1'
                with self.assertRaises(RuntimeError): self.ns['action'](request)
                self.assertEqual(self.sdk.rpc_calls, [])

    def player_with(self, fault=None, message=None, after=False):
        states = iter((True, after))
        def getter(name, value):
            if name == fault: raise RuntimeError(message)
            return value
        self.player = SimpleNamespace(isPlayingVideo=lambda: next(states),
            getPlayingItem=lambda: getter('item', 'SDK copy'),
            getPlayingFile=lambda: getter('file', 'actual-file'),
            getTime=lambda: getter('time', 90.0), getTotalTime=lambda: getter('total', 1200.0))

    def test_exact_stop_transition_at_each_sdk_seam_has_no_partial_clock(self):
        messages = {'item': 'Kodi is not playing any item', 'file': 'Kodi is not playing any file',
                    'time': 'Kodi is not playing any media file', 'total': 'Kodi is not playing any media file'}
        for field, message in messages.items():
            with self.subTest(field=field):
                self.player_with(field, message)
                result = self.ns['action'](dict(action='playing'))
                self.assertFalse(result['playing'])
                self.assertEqual(result['observation'], 'stopped_during_sdk_snapshot')
                self.assertEqual(result['sdk_transition_error'], message)
                self.assertTrue({'item', 'file', 'time', 'total'}.isdisjoint(result))
                self.assertEqual(result['events'], [])

    def test_unrelated_sdk_error_is_never_hidden(self):
        self.player_with('total', 'Unrelated metadata failure')
        with self.assertRaisesRegex(RuntimeError, 'Unrelated metadata failure'):
            self.ns['action'](dict(action='playing'))

    def test_no_media_error_while_still_playing_is_never_hidden(self):
        self.player_with('total', 'Kodi is not playing any media file', after=True)
        with self.assertRaises(RuntimeError): self.ns['action'](dict(action='playing'))

    def test_stop_after_complete_reads_discards_tuple(self):
        self.player_with(after=False)
        result = self.ns['action'](dict(action='playing'))
        self.assertEqual(result['observation'], 'stopped_after_sdk_snapshot')
        self.assertFalse(result['playing'])
        self.assertNotIn('time', result)

    def test_stable_playing_tuple_keeps_actual_sdk_reads(self):
        self.player_with(after=True)
        result = self.ns['action'](dict(action='playing'))
        self.assertTrue(result['playing'])
        self.assertEqual((result['item'], result['file'], result['time'], result['total']),
                         (dict(native_copy='SDK copy'), 'actual-file', 90.0, 1200.0))

    def test_only_committed_independent_movie_focus_and_retained_failure(self):
        expected = dict(execution_focus='independent-movie', retained_actual_evidence=dict(run=42567028842,
            source='9b05d1b4bf2283b7adc92f7ef6db0aff3b9fede3', queens_blade_status='FAIL_ACTUAL_SDK_MOVIE_UNKNOWN_EPISODE',
            cross_entry_rezero_status='BLOCKED_UNVERIFIED_METADATA', replay_known_wrong_typed_tv=False))
        request = copy.deepcopy(expected)
        ns = dict(HERE=Path('/committed-task'), base=SimpleNamespace(load=lambda path: request,
                  sha=lambda path: 'bound-request-sha', require=self.ns['require']))
        functions(HERE / 'stage_tracking_android.py', ('selected_focus',), ns)
        result = ns['selected_focus']()
        self.assertEqual(result['execution_focus'], 'independent-movie')
        self.assertFalse(result['retained_actual_evidence']['replay_known_wrong_typed_tv'])
        for mutation in ('focus', 'run', 'status', 'replay'):
            request = copy.deepcopy(expected)
            if mutation == 'focus': request['execution_focus'] = 'all-providers'
            if mutation == 'run': request['retained_actual_evidence']['run'] += 1
            if mutation == 'status': request['retained_actual_evidence']['queens_blade_status'] = 'PASS'
            if mutation == 'replay': request['retained_actual_evidence']['replay_known_wrong_typed_tv'] = True
            with self.assertRaises(RuntimeError): ns['selected_focus']()


if __name__ == '__main__':
    for name in ('stage_tracking_android.py', 'tracking_android_observer.py', 'verify_tracking_android.py'):
        print(name, hashlib.sha256((HERE / name).read_bytes()).hexdigest(), flush=True)
    unittest.main(verbosity=2)
