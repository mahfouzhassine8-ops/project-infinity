"""New selected origin/refusal/report guards; no Android or production suite.

Source-extracted test functions compile with optimize=1. Controlled dictionaries
test acceptance boundaries only; they are never installed as IDs or progress.
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
from urllib.parse import urlsplit, parse_qs

from test_tracking_dialog_select_optimized import functions

HERE = Path(__file__).resolve().parent
CC = 'script.infinity.commandcenter'


class AcceptanceGuards(unittest.TestCase):
    def setUp(self):
        self.ns = dict(os=os, re=re, base=SimpleNamespace(CC=CC, PACKAGE='com.projectinfinity.kodi', APK_SHA='a' * 64), urlsplit=urlsplit, parse_qs=parse_qs)
        functions(HERE / 'verify_tracking_android.py', ('functional', 'route_matches', 'verify_origin',
            'validate_progress', 'initial_report', 'classify_scenario', 'final_apk_observation', 'observed_resume_lower_deadline'), self.ns)
        # The selected functions refer to the actual source exception classes.
        source = (HERE / 'verify_tracking_android.py').read_text()
        import ast
        classes = [node for node in ast.parse(source).body if isinstance(node, ast.ClassDef) and node.name in ('ObserverBlocked', 'FunctionalFailure')]
        exec(compile(ast.Module(body=classes, type_ignores=[]), 'actual-origin-exceptions', 'exec', optimize=1), self.ns)

    def trace(self, media='tv'):
        section = 'trakttv' if media == 'tv' else 'traktmovies'
        result = [dict(step='home', window=10000, native=dict(hubsource='infinity', section=section)),
            dict(step='root', folder='plugin://' + CC + '/?action=' + ('tv' if media == 'tv' else 'movies')),
            dict(step='section', folder='plugin://' + CC + '/?action=library&media=' + media + '&bucket=watchlist'),
            dict(step='saved', key='controlled-saved-key', source='exact-parent')]
        if media == 'tv': result.append(dict(step='child', folder='exact-parent'))
        result.append(dict(step='launch', native_click=True))
        return result

    def test_direct_provider_launch_cannot_count_as_infinity_origin(self):
        with self.assertRaises(self.ns['FunctionalFailure']):
            self.ns['verify_origin']([dict(step='launch', native_click=True)], 'tv')

    def test_live_home_regular_owner_cannot_be_declared_infinity(self):
        owner, calls = ['trakt'], []
        values = {'System.CurrentControlId': '9000', 'Container(9000).ListItem.Label': 'INFINITY TV',
                  'Container(9000).ListItem.Property(section)': 'trakttv'}
        xbmc = SimpleNamespace(getSkinDir=lambda: 'skin.infinity.diggz', getCondVisibility=lambda expression: True,
            executebuiltin=lambda *args: None,
            getInfoLabel=lambda name: owner[0] if name == 'Container(9000).ListItem.Property(hubsource)' else values.get(name, ''),
            executeJSONRPC=lambda raw: calls.append(json.loads(raw)['method']) or '{"result":"OK"}')
        ns = dict(os=os, time=time, json=json, xbmc=xbmc,
            xbmcgui=SimpleNamespace(getCurrentWindowId=lambda: 10000, getCurrentWindowDialogId=lambda: 9999))
        functions(HERE / 'tracking_android_observer.py', ('require', 'action'), ns)
        request = dict(action='home-select', index=1, label='INFINITY TV', section='trakttv', hubsource='infinity')
        with self.assertRaises(RuntimeError): ns['action'](request)
        self.assertEqual(calls, [])
        owner[0] = 'infinity'
        self.assertEqual(ns['action'](request)['hubsource'], 'infinity')
        self.assertEqual(calls, ['Input.Select'])

    def test_regular_trakt_wrong_media_and_missing_saved_chain_refuse(self):
        for mutation in ('trakt', 'wrong_media', 'missing_saved', 'wrong_parent'):
            trace = self.trace()
            if mutation == 'trakt': trace[0]['native']['hubsource'] = 'trakt'
            if mutation == 'wrong_media': trace[0]['native']['section'] = 'traktmovies'
            if mutation == 'missing_saved': trace.pop(3)
            if mutation == 'wrong_parent': trace[4]['folder'] = 'different-parent'
            with self.assertRaises(self.ns['FunctionalFailure']): self.ns['verify_origin'](trace, 'tv')

    def test_ordered_actual_origin_requires_av_when_requested(self):
        trace = self.trace()
        self.ns['verify_origin'](trace, 'tv')
        with self.assertRaises(self.ns['FunctionalFailure']): self.ns['verify_origin'](trace, 'tv', require_av=True)
        trace.append(dict(step='AVStarted', events=[dict(event='AVStarted')]))
        self.ns['verify_origin'](trace, 'tv', require_av=True)

    def test_fixture_blocked_and_observer_blocked_leave_steps_not_run(self):
        report = self.ns['initial_report']()
        scenario = report['scenarios']['tv']
        self.assertTrue(all(value['status'] == 'NOT_RUN' for value in scenario['steps'].values()))
        self.assertEqual(self.ns['classify_scenario'](RuntimeError('Unavailable save fixture'), dict(last_step='fixture_preparation')), 'BLOCKED_FIXTURE_PREPARATION')
        self.assertEqual(self.ns['classify_scenario'](self.ns['ObserverBlocked']('SDK unavailable'), scenario), 'BLOCKED_OBSERVER')
        self.assertEqual(self.ns['classify_scenario'](RuntimeError('AMBIGUOUS_VISIBLE_PRIMARY_CONTENT_CONTROLS_REJECTED'), scenario), 'BLOCKED_OBSERVER')
        self.assertEqual(self.ns['classify_scenario'](self.ns['FunctionalFailure']('record mismatch'), dict(integration_started=True)), 'FAIL')

    def test_observed_save_and_resume_assertions_fail_without_hiding_blockers(self):
        classify = self.ns['classify_scenario']
        self.assertEqual(classify(self.ns['FunctionalFailure']('SAVING_ALONE_CHANGED_PLAYBACK_HISTORY'),
                                 dict(last_step='fixture_preparation')), 'FAIL')
        scenario = dict(last_step='resume', integration_started=True)
        for label in ('RESUMED_ACTUAL_TYPED_ITEM_CONTINUITY:media_type', 'RESUMED_ACTUAL_TYPED_ID_CONTINUITY:tmdb',
                      'RESUMED_ACTUAL_SOURCE_URI_CONTINUITY', 'EXACT_RESUME_UPPER_OFFSET_BOUND_NO_LATE_OVERSHOOT'):
            self.assertEqual(classify(RuntimeError(label), scenario), 'FAIL')
        self.assertEqual(classify(self.ns['FunctionalFailure']('EXACT_RESUME_LOWER_OFFSET_DEADLINE'), scenario), 'FAIL')
        outer = TimeoutError('Existing same-source Infinity resume offset; last=None')
        self.assertTrue(self.ns['observed_resume_lower_deadline'](outer, True))
        self.assertFalse(self.ns['observed_resume_lower_deadline'](outer, False))
        transport = TimeoutError('Actual SDK observer playing; last=None')
        self.assertFalse(self.ns['observed_resume_lower_deadline'](transport, True))
        self.assertEqual(classify(transport, scenario), 'BLOCKED_RUNTIME_PREREQUISITE')
        self.assertEqual(classify(self.ns['ObserverBlocked']('SDK ambiguous'), scenario), 'BLOCKED_OBSERVER')
        self.assertEqual(classify(RuntimeError('UNAMBIGUOUS_ACTUAL_NATIVE_PROVIDER_SOURCE_URI_REQUIRED'), scenario), 'BLOCKED_RUNTIME_PREREQUISITE')

    def test_normal_local_bridge_identity_accepts_unknown_coordinates(self):
        identity = dict(kind='episode', scope='watchnixtoons_local', season=-1, episode=-1)
        stored = dict(key='controlled-progress-key', media='tv', source='exact-child', source_parent='exact-parent',
                      season=-1, episode=-1, label='Native label')
        state = dict(valid_identities=dict(items={stored['key']: identity}), series_proof={stored['key']: {'wnt2': 'validated-local-parent'}})
        result = self.ns['validate_progress'](state, stored, 'tv', dict(file='exact-child'), 'exact-parent')
        self.assertEqual(result, identity)  # Raw SDK movie is deliberately not a pre-gate/input.
        self.assertEqual((stored['season'], stored['episode']), (-1, -1))
        wrong = copy.deepcopy(stored); wrong['source_parent'] = 'another-parent'
        with self.assertRaises(self.ns['FunctionalFailure']): self.ns['validate_progress'](state, wrong, 'tv', dict(file='exact-child'), 'exact-parent')

    def test_final_hash_timeout_is_unverified_but_actual_different_digest_fails(self):
        device = SimpleNamespace(shell=lambda *args: (_ for _ in ()).throw(TimeoutError('bounded read')))
        self.assertEqual(self.ns['final_apk_observation'](device)['status'], 'UNVERIFIED_READ_ERROR')
        path = '/data/app/controlled/base.apk'
        device.shell = lambda *args: 'package:' + path if args[0] == 'pm' else 'b' * 64 + '  ' + path
        self.assertEqual(self.ns['final_apk_observation'](device)['status'], 'FAIL_MISMATCH')
        device.shell = lambda *args: 'package:' + path if args[0] == 'pm' else 'permission denied'
        self.assertEqual(self.ns['final_apk_observation'](device)['status'], 'UNVERIFIED_DIGEST_QUERY')


if __name__ == '__main__':
    for name in ('stage_tracking_android.py', 'tracking_android_observer.py', 'verify_tracking_android.py'):
        print(name, hashlib.sha256((HERE / name).read_bytes()).hexdigest(), flush=True)
    unittest.main(verbosity=2)
