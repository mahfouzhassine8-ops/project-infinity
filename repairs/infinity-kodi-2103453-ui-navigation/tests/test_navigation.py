import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('navigation', Path(__file__).resolve().parents[1] / 'navigation.py')
nav = importlib.util.module_from_spec(spec);spec.loader.exec_module(nav)


class API:
    def __init__(self):
        self.requests = [];self.dialogs = [];self.folder = '';self.yes = False
        self.ready = 'v1';self.sports = 'plugin://plugin.video.playlistbrowser/?section=sports'
        self.enabled = True;self.android = True;self.directory = {'files': [], 'limits': {'total': 0}}
        self.accept = True
    def executeJSONRPC(self, raw):
        req = json.loads(raw);self.requests.append(req)
        if req['method'] == 'Files.GetDirectory':value = self.directory
        elif req['method'] == 'GUI.ActivateWindow':value = 'OK' if self.accept else None
        else:raise AssertionError('Unexpected mutation/API: ' + req['method'])
        return json.dumps({'error': {'code': -1}} if value is None else {'result': value})
    def getCondVisibility(self, name):
        if name == 'System.Platform.Android':return self.android
        if name == 'System.AddonIsEnabled(plugin.video.playlistbrowser)':return self.enabled
        raise AssertionError(name)
    def Dialog(self):return self
    def Window(self, wid):
        assert wid == 10000
        return self
    def getProperty(self, name):
        return {'Infinity.Playlist.SportsPath': self.sports, 'Infinity.Playlist.Ready': self.ready}[name]
    def ok(self, *args):self.dialogs.append(('ok', args))
    def yesno(self, *args, **kwargs):self.dialogs.append(('yesno', args, kwargs));return self.yes
    def browseSingle(self, *args):self.dialogs.append(('browse', args));return self.folder


class Navigation(unittest.TestCase):
    def test_configured_sports_uses_exact_existing_route_once(self):
        a = API();self.assertTrue(nav.run('sports', a, a))
        self.assertEqual(len(a.requests), 1)
        self.assertEqual(a.requests[0]['params']['parameters'], [a.sports, 'return'])
    def test_missing_sports_never_substitutes_provider(self):
        for prop, value in [('enabled', False), ('ready', ''), ('sports', ''),
                            ('sports', 'plugin://other.provider/'), ('sports', 'file:///private')]:
            a = API();setattr(a, prop, value)
            self.assertFalse(nav.run('sports', a, a));self.assertEqual(a.requests, [])
            self.assertEqual(a.dialogs[0][0], 'ok')
    def test_browse_cancel_has_no_side_effect(self):
        a = API();self.assertFalse(nav.run('browse', a, a));self.assertEqual(a.requests, [])
        self.assertEqual(a.dialogs[0], ('browse', (0, 'Browse Files', 'video')))
    def test_folder_name_is_data_not_builtin(self):
        a = API();a.folder = '/storage/self/primary/Movies, "Family" (2026)/'
        self.assertTrue(nav.run('browse', a, a))
        self.assertEqual(a.requests[0]['params'], {'window': 'videos', 'parameters': [a.folder, 'return']})
    def test_downloads_empty_is_success_and_uses_current_android_user(self):
        a = API();self.assertTrue(nav.run('downloads', a, a, {}))
        self.assertEqual(a.requests[0]['params']['directory'], '/storage/self/primary/Download/')
        self.assertEqual(a.requests[1]['params']['parameters'][0], '/storage/self/primary/Download/')
        self.assertEqual(a.dialogs, [])
    def test_downloads_respects_environment_storage_location(self):
        a = API();self.assertTrue(nav.run('downloads', a, a, {'EXTERNAL_STORAGE': '/storage/emulated/10/'}))
        self.assertEqual(a.requests[0]['params']['directory'], '/storage/emulated/10/Download/')
    def test_denied_access_cancel_does_not_navigate_or_request_permissions(self):
        a = API();a.directory = None
        self.assertFalse(nav.run('downloads', a, a, {}))
        self.assertEqual([r['method'] for r in a.requests], ['Files.GetDirectory'])
        self.assertEqual(a.dialogs[0][0], 'yesno')
        self.assertIn('permission', a.dialogs[0][1][1])
    def test_denied_access_can_browse_already_accessible_location(self):
        a = API();a.directory = None;a.yes = True;a.folder = '/storage/authorized/'
        self.assertTrue(nav.run('downloads', a, a, {}))
        self.assertEqual(a.requests[-1]['params']['parameters'], [a.folder, 'return'])
    def test_failed_window_request_is_not_reported_as_navigation_success(self):
        a = API();a.accept = False
        self.assertFalse(nav.run('sports', a, a));self.assertEqual(a.dialogs[-1][0], 'ok')
    def test_non_android_downloads_asks_for_folder_without_guessing(self):
        a = API();a.android = False
        self.assertFalse(nav.run('downloads', a, a));self.assertEqual(a.requests, [])
        self.assertEqual([d[0] for d in a.dialogs], ['ok', 'browse'])
    def test_unknown_action_is_noop(self):
        a = API();self.assertFalse(nav.run('shutdown', a, a))
        self.assertEqual(a.requests, []);self.assertEqual(a.dialogs, [])


if __name__ == '__main__':unittest.main()
