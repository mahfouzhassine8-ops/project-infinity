"""Selected host controls for actual-source DialogSelect interaction only.

Compiles the unchanged selected observer/driver functions with optimize=1.
SDK doubles are negative/interaction controls, never Android/provider evidence.
No first-party production module, app, account or playback callback is loaded.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import time
from types import SimpleNamespace
import unittest

HERE = Path(__file__).resolve().parent


def functions(path, names, namespace):
    tree = ast.parse(path.read_text(), filename=str(path))
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    if {node.name for node in selected} != set(names):
        raise RuntimeError('Exact selected source functions required')
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), 'exec', optimize=1), namespace)


class SDK:
    def __init__(self):
        self.dialog, self.heading, self.body, self.focus = 12000, 'Select Quality', '', 3
        self.rows = {3: ['SD', 'HD'], 6: []}
        self.visible = {3: True, 6: False}
        self.buttons, self.on_select = {}, None
        self.indices, self.rpc_calls, self.focus_calls = {}, [], []

    def label(self, name):
        known = {'Control.GetLabel(1)': self.heading, 'Control.GetLabel(9)': self.body,
                 'System.CurrentControlId': str(self.focus)}
        if name in known:
            return known[name]
        button = re.fullmatch(r'Control.GetLabel\((\d+)\)', name)
        if button:
            return self.buttons.get(int(button[1]), '')
        match = re.fullmatch(r'Container\((\d+)\)\.NumItems', name)
        if match:
            return str(len(self.rows.get(int(match[1]), [])))
        match = re.fullmatch(r'Container\((\d+)\)\.ListItemAbsolute\((\d+)\)\.Label', name)
        if match:
            rows = self.rows.get(int(match[1]), [])
            return rows[int(match[2])] if int(match[2]) < len(rows) else ''
        match = re.fullmatch(r'Container\((\d+)\)\.ListItem.Label', name)
        if match:
            return self.rows[int(match[1])][self.indices.get(int(match[1]), 0)]
        return ''

    def condition(self, expression):
        match = re.fullmatch(r'Control.IsVisible\((\d+)\)', expression)
        return self.visible.get(int(match[1]), False) if match else False

    def builtin(self, expression, wait):
        self.focus_calls.append(expression)
        match = re.fullmatch(r'SetFocus\((\d+)(?:,(\d+),absolute)?\)', expression)
        if not match:
            raise RuntimeError('Unselected host builtin')
        self.focus = int(match[1])
        if match[2] is not None:
            self.indices[self.focus] = int(match[2])

    def rpc(self, raw):
        method = json.loads(raw)['method']
        self.rpc_calls.append(method)
        if method == 'Input.Select' and self.on_select:
            self.on_select()
        return '{"jsonrpc":"2.0","id":1,"result":"OK"}'

    def addon(self, aid):
        raise RuntimeError("Unknown addon id '" + aid + "'.")


class DialogControls(unittest.TestCase):
    def setUp(self):
        self.sdk = SDK()
        xbmc = SimpleNamespace(getInfoLabel=self.sdk.label, getCondVisibility=self.sdk.condition,
            getSkinDir=lambda: 'skin.infinity.diggz', executebuiltin=self.sdk.builtin,
            executeJSONRPC=self.sdk.rpc, Player=lambda: SimpleNamespace(isPlayingVideo=lambda: False))
        self.ns = dict(os=os, json=json, time=time, xbmc=xbmc,
            xbmcgui=SimpleNamespace(getCurrentWindowId=lambda: 10025, getCurrentWindowDialogId=lambda: self.sdk.dialog),
            xbmcaddon=SimpleNamespace(Addon=self.sdk.addon), CANCELLED_CHOICE=None,
            EVENTS=SimpleNamespace(sequence=0, events=[]))
        functions(HERE / 'tracking_android_observer.py', ('require', 'snapshot', 'action'), self.ns)

    def select(self, **changes):
        request = dict(action='menu-select', control=3, index=1, label='HD', dialog=12000, heading='Select Quality')
        request.update(changes)
        return self.ns['action'](request)

    def test_snapshot_records_real_simple_and_detailed_control_labels(self):
        self.sdk.rows[6] = ['Detailed hidden']
        snap = self.ns['snapshot']()
        self.assertEqual([row['label'] for row in snap['controls']['3'] if row['label']], ['SD', 'HD'])
        self.assertEqual(snap['controls']['6'][0]['label'], 'Detailed hidden')
        self.assertTrue(snap['visible_controls']['3'])
        self.assertFalse(snap['visible_controls']['6'])
        self.assertFalse(snap['theme_available'])

    def test_optimized_simple_and_detailed_selection(self):
        self.select()
        self.assertEqual(self.sdk.rpc_calls, ['Input.Select'])
        self.sdk.rows[6], self.sdk.visible[3], self.sdk.visible[6] = ['480p'], False, True
        self.select(control=6, index=0, label='480p')
        self.assertEqual(self.sdk.rpc_calls, ['Input.Select', 'Input.Select'])

    def test_changed_label_refuses_before_select(self):
        with self.assertRaisesRegex(RuntimeError, 'LIVE_NATIVE_MENU_LABEL'):
            self.select(label='Stale HD')
        self.assertEqual(self.sdk.rpc_calls, [])

    def test_hidden_empty_or_wrong_dialog_choice_refuses(self):
        for setup in ('hidden', 'empty', 'auth', 'wrong_window'):
            with self.subTest(setup=setup):
                self.setUp()
                if setup == 'hidden': self.sdk.visible[3] = False
                if setup == 'empty': self.sdk.rows[3] = []
                if setup == 'auth': self.sdk.heading = 'Authenticate'
                if setup == 'wrong_window': self.sdk.dialog = 12002
                with self.assertRaises(RuntimeError): self.select()
                self.assertEqual(self.sdk.rpc_calls, [])

    def test_driver_selects_only_visible_original_quality_list(self):
        ns = dict(base=SimpleNamespace(require=self.ns['require']), until=lambda device, fn, label, seconds: fn())
        functions(HERE / 'verify_tracking_android.py', ('actual_av', 'menu_choose'), ns)
        observer = SimpleNamespace(call=lambda action, **values: self.ns['action'](dict(action=action, **values)))
        self.assertIsNone(ns['actual_av'](None, observer, 0))
        self.assertEqual(self.sdk.rpc_calls, ['Input.Select'])
        self.sdk.rpc_calls.clear()
        ns['menu_choose'](None, observer, 'HD')
        self.assertEqual(self.sdk.rpc_calls, ['Input.Select'])

    def test_empty_quality_options_never_guess_selection(self):
        self.sdk.rows[3] = []
        ns = dict(base=SimpleNamespace(require=self.ns['require']), until=lambda device, fn, label, seconds: fn())
        functions(HERE / 'verify_tracking_android.py', ('actual_av',), ns)
        observer = SimpleNamespace(call=lambda action, **values: self.ns['action'](dict(action=action, **values)))
        self.assertIsNone(ns['actual_av'](None, observer, 0))
        self.assertEqual(self.sdk.rpc_calls, [])

    def test_cancel_then_exact_stale_failure_ack_is_one_use(self):
        self.ns['action'](dict(action='cancel-provider-choice', heading='Select Quality'))
        self.sdk.dialog, self.sdk.heading = 12002, 'Playback failed'
        self.sdk.body = 'One or more items failed to play. Check the log for more information about this message.'
        self.assertTrue(self.ns['action'](dict(action='ack-cancelled-playback-failure'))['acknowledged'])
        with self.assertRaises(RuntimeError): self.ns['action'](dict(action='ack-cancelled-playback-failure'))
        self.assertEqual(self.sdk.rpc_calls, ['Input.Back', 'Input.Select'])

    def test_unknown_auth_and_unrelated_failure_are_never_dismissed(self):
        self.sdk.heading = 'Authenticate'
        with self.assertRaises(RuntimeError): self.ns['action'](dict(action='cancel-provider-choice', heading='Authenticate'))
        self.sdk.dialog, self.sdk.heading = 12002, 'Playback failed'
        with self.assertRaises(RuntimeError): self.ns['action'](dict(action='ack-cancelled-playback-failure'))
        self.assertEqual(self.sdk.rpc_calls, [])

    def test_only_exact_existing_parent_identity_refusal_is_acknowledged(self):
        self.sdk.dialog, self.sdk.heading = 12002, 'Infinity Tracked'
        self.sdk.body = 'This item has no verifiable WatchNixtoons2 source location. Nothing was changed.'
        self.assertTrue(self.ns['action'](dict(action='ack-parent-identity-refusal'))['acknowledged'])
        self.sdk.body = 'Sign in to continue'
        with self.assertRaises(RuntimeError): self.ns['action'](dict(action='ack-parent-identity-refusal'))
        self.assertEqual(self.sdk.rpc_calls, ['Input.Select'])

    def test_actual_context_buttons_handoff_to_owned_menu(self):
        self.sdk.dialog, self.sdk.heading = 10106, ''
        self.sdk.rows, self.sdk.visible = {}, {1001: True, 1002: True}
        self.sdk.buttons = {1001: 'Play Chapters', 1002: 'Infinity Tracked'}
        snap = self.ns['snapshot']()
        self.assertEqual(snap['context_buttons'], [dict(control=1001, label='Play Chapters'), dict(control=1002, label='Infinity Tracked')])
        def opened():
            self.sdk.dialog, self.sdk.focus = 13000, 50
            self.sdk.rows, self.sdk.visible = {50: ['Play', 'Add to Watchlist']}, {50: True}
        self.sdk.on_select = opened
        def polling(device, fn, label, seconds):
            for _ in range(3):
                value = fn()
                if value: return value
            raise RuntimeError('Host selected menu did not appear')
        ns = dict(base=SimpleNamespace(require=self.ns['require']), until=polling)
        functions(HERE / 'verify_tracking_android.py', ('menu_choose',), ns)
        observer = SimpleNamespace(call=lambda action, **values: self.ns['action'](dict(action=action, **values)))
        ns['menu_choose'](None, observer, 'Add to Watchlist')
        self.assertEqual(self.sdk.focus_calls, ['SetFocus(1002)', 'SetFocus(50,1,absolute)'])
        self.assertEqual(self.sdk.rpc_calls, ['Input.Select', 'Input.Select'])

    def test_context_button_stale_hidden_template_or_wrong_dialog_refuses(self):
        for setup in ('stale', 'hidden', 'template', 'wrong_dialog'):
            with self.subTest(setup=setup):
                self.setUp()
                self.sdk.dialog, self.sdk.buttons, self.sdk.visible = 10106, {1001: 'Infinity Tracked'}, {1001: True}
                control = 1001
                if setup == 'stale': self.sdk.buttons[1001] = 'Authenticate'
                if setup == 'hidden': self.sdk.visible[1001] = False
                if setup == 'template': control = 1000
                if setup == 'wrong_dialog': self.sdk.dialog = 12000
                with self.assertRaises(RuntimeError):
                    self.ns['action'](dict(action='context-button', control=control, label='Infinity Tracked'))
                self.assertEqual(self.sdk.rpc_calls, [])


if __name__ == '__main__':
    for name in ('tracking_android_observer.py', 'verify_tracking_android.py'):
        print(name, hashlib.sha256((HERE / name).read_bytes()).hexdigest(), flush=True)
    unittest.main(verbosity=2)
