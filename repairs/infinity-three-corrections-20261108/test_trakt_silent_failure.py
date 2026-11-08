"""Focused tests of pinned real Trakt methods; SDK/HTTP boundaries are synthetic.

No account, network, database, Kodi app, build or signer is accessed.
"""
import ast
from contextlib import contextmanager
from functools import cached_property
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
TRAKT = HERE / 'trakt'
API = Path('resources/lib/tmdbhelper_sync_trakt/api')
MESSAGE = ('Trakt authorization could not be completed. Automatic authorization attempts are paused for five minutes. '
           'You can try signing in again from the Trakt account settings.')


def module(name, **attributes):
    value = types.ModuleType(name)
    value.__dict__.update(attributes)
    return value


@contextmanager
def environment(candidate=True, silent=True, skin='skin.infinity.diggz', query_error=False):
    state = types.SimpleNamespace(now=1000, silent=silent, skin=skin, dialogs=[], logs=[],
                                  properties={'TraktIsAuth': 'previous'}, http_calls=0,
                                  login_calls=[], configured=0, silent_queries=0, query_error=query_error)
    authorization = dict(access_token='synthetic-access', refresh_token='synthetic-refresh',
                         created_at=0, expires_in=1)
    api = types.SimpleNamespace(user_token=types.SimpleNamespace(value=json.dumps(authorization)),
                                login_if_required=False)
    def get_property(name, value=None, set_property=None, clear_property=False, is_type=None):
        if clear_property:
            state.properties.pop(name, None)
            return ''
        if set_property is not None:
            value = set_property
        if value is not None:
            state.properties[name] = value
        result = state.properties.get(name, '')
        return is_type(result or 0) if is_type else result
    def get_skin():
        if state.query_error:
            raise RuntimeError('synthetic unavailable GUI query')
        return state.skin
    def get_condition(value):
        assert value == 'Skin.HasSetting(Infinity.SilentMode)'
        state.silent_queries += 1
        return state.silent
    class Dialog:
        def ok(self, title, text):
            state.dialogs.append((title, text))
    class KeyGetter:
        def __init__(self, data):
            self.data = data
        def get_key(self, key):
            return (self.data or {}).get(key)
    def localized(key):
        return {32103: 'Trakt Authentication', 32111: MESSAGE}.get(key, str(key))
    stubs = {
        'xbmc': module('xbmc', getSkinDir=get_skin, getCondVisibility=get_condition),
        'xbmcgui': module('xbmcgui', Dialog=Dialog, DialogProgress=object, DLG_YESNO_YES_BTN=1),
        'jurialmunkey.parser': module('parser', boolean=lambda v: str(v).lower() == 'true'),
        'jurialmunkey.window': module('window', get_property=get_property),
        'jurialmunkey.ftools': module('ftools', cached_property=cached_property),
        'tmdbhelper.lib.files.locker': module('locker', mutexlock=lambda fn: fn),
        'tmdbhelper.lib.files.futils': module('futils', json_loads=lambda s: json.loads(s) if s else None, json_dumps=json.dumps),
        'tmdbhelper.lib.addon.plugin': module('plugin', KeyGetter=KeyGetter, get_localized=localized),
        'tmdbhelper.lib.addon.logger': module('logger', kodi_log=lambda *args: state.logs.append(args)),
        'tmdbhelper.lib.addon.tmdate': module('tmdate', get_timestamp=lambda t: t > state.now,
                                           set_timestamp=lambda seconds: state.now + seconds),
        'tmdbhelper_sync_trakt.localization': module('localization', get_localized=localized),
    }
    def load(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        value = importlib.util.module_from_spec(spec)
        sys.modules[name] = value
        spec.loader.exec_module(value)
        return value
    namespace = 'tmdbhelper_sync_trakt.api.'
    with patch.dict(sys.modules, stubs):
        recovery = load(namespace + 'recovery', TRAKT / 'reference' / API / 'recovery.py')
        source = TRAKT / ('candidate' if candidate else 'reference')
        token = load(namespace + 'token', source / API / 'token.py')
        auth = load(namespace + 'authenticator', source / API / 'authenticator.py')
        api.authenticator = auth.TraktAuthenticator(api)
        def no_response(refresh):
            assert refresh == 'synthetic-refresh'
            state.http_calls += 1
            return None
        api.set_authorisation_token = no_response
        def no_login(prompt=True):
            state.login_calls.append(prompt)
            return None
        api.authenticator.get_login_authorization = no_login
        def configure():
            state.configured += 1
        api.authenticator.configure_provider = configure
        state.api, state.token, state.auth, state.result = api, token, auth, recovery.TraktAuthorizationResult
        state.stored = token.TraktStoredAccessToken(api)
        yield state


class TraktSilentFailure(unittest.TestCase):
    def test_exact_screenshot_producer(self):
        text = (TRAKT / 'reference/resources/language/resource.language.en_gb/strings.po').read_text()
        self.assertIn('msgctxt "#32103"\nmsgid "Trakt Authentication"', text)
        self.assertIn('msgctxt "#32111"\nmsgid "' + MESSAGE + '"', text)
        body = (TRAKT / 'reference' / API / 'authenticator.py').read_text()
        self.assertIn('Dialog().ok(get_localized(32103), get_localized(32111))', body)

    def test_original_automatic_failure_reproduces_interrupt_in_silent_mode(self):
        with environment(candidate=False) as state:
            self.assertIsNone(state.stored.get_authorization())
            self.assertEqual(state.dialogs, [('Trakt Authentication', MESSAGE)])
            self.assertEqual(state.properties['TraktRefreshTimeStamp'], 1300)

    def test_automatic_silent_on_keeps_error_record_and_cooldown_without_dialog(self):
        with environment() as state:
            original_account = state.api.user_token.value
            self.assertIsNone(state.stored.get_authorization())
            self.assertEqual(state.dialogs, [])
            self.assertEqual(state.http_calls, 1)
            self.assertEqual(state.properties['TraktRefreshTimeStamp'], 1300)
            self.assertNotIn('TraktIsAuth', state.properties)
            self.assertEqual(state.logs, [('Trakt authentication failed: no response from token endpoint. Suppressing retries for 300s.', 1)])
            self.assertEqual(state.api.user_token.value, original_account)

    def test_cooldown_still_blocks_until_300_seconds_then_retries(self):
        with environment() as state:
            state.stored.get_authorization()
            state.now = 1299
            self.assertIsNone(state.stored.get_authorization())
            self.assertIsNone(state.stored.recover())
            self.assertEqual(state.http_calls, 1)
            self.assertEqual(len(state.logs), 1)
            state.now = 1300
            self.assertIsNone(state.stored.get_authorization())
            self.assertEqual(state.http_calls, 2)
            self.assertEqual(len(state.logs), 2)
            self.assertEqual(state.properties['TraktRefreshTimeStamp'], 1600)
            self.assertEqual(state.dialogs, [])

    def test_silent_off_and_other_skins_keep_existing_dialog(self):
        for options in [dict(silent=False), dict(skin='skin.cobra.test'), dict(skin='skin.estuary')]:
            with self.subTest(options=options), environment(**options) as state:
                state.stored.get_authorization()
                self.assertEqual(state.dialogs, [('Trakt Authentication', MESSAGE)])
                self.assertEqual(state.properties['TraktRefreshTimeStamp'], 1300)
                if options.get('skin'):
                    self.assertEqual(state.silent_queries, 0)

    def test_manual_login_keeps_failure_dialog_and_bypasses_active_automatic_cooldown(self):
        for candidate in (False, True):
            with self.subTest(candidate=candidate), environment(candidate=candidate) as state:
                state.properties['TraktRefreshTimeStamp'] = 1299
                original_account = state.api.user_token.value
                self.assertIsNone(state.api.authenticator.login())
                self.assertEqual(state.login_calls, [False])
                self.assertEqual(state.dialogs, [('Trakt Authentication', MESSAGE)])
                self.assertEqual(state.http_calls, 0)
                self.assertEqual(state.properties['TraktRefreshTimeStamp'], 1300)
                self.assertEqual(state.api.user_token.value, original_account)
                self.assertEqual(state.silent_queries, 0)

    def test_manual_path_does_not_query_silent_setting(self):
        with environment(query_error=True) as state:
            state.api.authenticator.login()
            self.assertEqual(state.dialogs, [('Trakt Authentication', MESSAGE)])

    def test_failed_presentation_query_falls_back_to_existing_dialog(self):
        with environment(query_error=True) as state:
            state.stored.get_authorization()
            self.assertEqual(state.dialogs, [('Trakt Authentication', MESSAGE)])

    def test_second_401_rejection_path_is_silent_but_records_failure(self):
        with environment() as state:
            original_account = state.api.user_token.value
            state.stored.reject_authorization('synthetic-access')
            self.assertEqual(state.dialogs, [])
            self.assertEqual(state.properties['TraktRefreshTimeStamp'], 1300)
            self.assertEqual(state.logs, [('Trakt authentication failed: request remained unauthorized after recovery. Suppressing retries for 300s.', 1)])
            self.assertEqual(state.api.user_token.value, original_account)

    def test_stale_401_does_not_notify_or_change_cooldown(self):
        with environment() as state:
            state.stored.reject_authorization('different-synthetic-token')
            self.assertEqual(state.dialogs, [])
            self.assertEqual(state.logs, [])
            self.assertNotIn('TraktRefreshTimeStamp', state.properties)

    def test_no_recovery_result_keeps_no_notification(self):
        with environment() as state:
            state.stored.get_refreshed_token = lambda **kwargs: None
            self.assertIsNone(state.stored.recover())
            self.assertEqual(state.dialogs, [])
            self.assertEqual(state.logs, [])

    def test_successful_refresh_preserves_existing_token_rotation(self):
        results = []
        for candidate in (False, True):
            with environment(candidate=candidate) as state:
                replacement = dict(access_token='synthetic-new', refresh_token='synthetic-new-refresh', created_at=1000, expires_in=3600)
                class Response:
                    status_code = 200
                    closed = False
                    def json(self):
                        return replacement
                    def close(self):
                        self.closed = True
                response = Response()
                state.api.set_authorisation_token = lambda refresh: response
                self.assertEqual(state.stored.get_authorization(), replacement)
                self.assertTrue(response.closed)
                results.append((state.api.user_token.value, state.logs, state.properties, state.dialogs))
        self.assertEqual(results[0], results[1])

    def test_source_delta_does_not_change_cooldown_authentication_or_manual_prompt_methods(self):
        pins = json.loads((TRAKT / 'SOURCE-PINS.json').read_text())
        for name, change in pins['changed'].items():
            before = (TRAKT / 'reference' / name).read_text()
            after = (TRAKT / 'candidate' / name).read_text()
            self.assertEqual(hashlib.sha256(before.encode()).hexdigest(), change['before_sha256'])
            self.assertEqual(hashlib.sha256(after.encode()).hexdigest(), change['after_sha256'])
            def methods(text):
                lines = text.splitlines(keepends=True)
                return {n.name: ''.join(lines[n.lineno-1:n.end_lineno]) for n in ast.walk(ast.parse(text)) if isinstance(n, ast.FunctionDef)}
            old, new = methods(before), methods(after)
            expected = {'notify_failure'} if name.endswith('authenticator.py') else {'recover'}
            self.assertEqual({n for n in old if old[n] != new[n]}, expected)
            if name.endswith('token.py'):
                self.assertEqual(new['recover'].replace('notify_failure(manual=force_login)', 'notify_failure()'), old['recover'])


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TraktSilentFailure)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = dict(status='PASS_FOCUSED_TRAKT_NOTIFICATION_SOURCE_CHECKS' if result.wasSuccessful() else 'FAIL',
                  tests_run=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                  source_commit='fff6d9b38820d2e64e0b00cb2b469c72ff3fbe2b', upstream_version='1.2.8',
                  real_Kodi_or_Fold_execution=False, real_accounts_or_network_access=False,
                  original_cooldown_seconds=300, build_or_signing=False)
    (HERE / 'evidence/TRAKT-SILENT-FAILURE.json').write_text(json.dumps(report, indent=2) + '\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
